#!/usr/bin/env python3
"""Grid Convergence Index (GCI) calculator for 3-mesh studies (Lane L5, action #5).

WHY THIS EXISTS
---------------
Every TAMU-loop training case is `*_coarse_mesh`, yet both 1D READMEs state coarse
mesh is diagnostic/regression-only and medium/fine resolution is required for any
publishable thermal-closure / wall-temperature interpretation. So the apparent-`f`
(3.5-70x laminar) and Nu/UA'/HTC closures currently carry NO discretization-error
bound. The mesh-independence protocol
(`operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md`) calls for a 3-level
study so a Grid Convergence Index and an observed order of accuracy can be
computed. This module is the calculator that ingests the per-level QoI table
(3 values -> p, Richardson extrapolation, GCI bands). It is the headline-number
producer; running the meshes themselves is blocked on OF13 runtime recovery (B1).

METHOD (Roache 1994/1998; ASME V&V20-2009)
------------------------------------------
For a quantity of interest (QoI) `f` solved on three systematically refined grids:

    f1  = solution on the FINE grid   (cell size h1, smallest h)
    f2  = solution on the MEDIUM grid (cell size h2)
    f3  = solution on the COARSE grid (cell size h3, largest h)

with grid refinement ratios

    r21 = h2 / h1  >= 1   (medium-to-fine)
    r32 = h3 / h2  >= 1   (coarse-to-medium)

We compute, following ASME V&V20-2009 §7.5 (which codifies Roache's GCI):

1. OBSERVED ORDER OF ACCURACY `p`.
   Define the solution differences
       e21 = f2 - f1
       e32 = f3 - f2
   and the sign s = sign(e32 / e21).
   For GENERAL (possibly non-constant) refinement ratios, `p` solves the
   transcendental equation (ASME V&V20 Eq. set; Roache 1998):
       p = (1 / ln(r21)) * | ln| e32 / e21 |  +  q(p) |
       q(p) = ln( (r21^p - s) / (r32^p - s) )
   We solve this by fixed-point iteration on `p` (q(p)=0 when r21==r32, giving the
   familiar closed form). Fixed-point iteration is the method recommended in the
   ASME guide and is robust for r in [1.1, 2] with monotone data.
   For the CONSTANT-ratio case (r21 == r32 == r) this collapses to the closed form
       p = ln| e32 / e21 | / ln(r).

2. RICHARDSON-EXTRAPOLATED ("exact") VALUE.
   Using the fine and medium solutions and the observed order:
       f_exact = f1 + (f1 - f2) / (r21^p - 1)
   This is the generalized Richardson extrapolation (Roache 1998, Eq. 5.4.1);
   it is a formally (p+1)-order estimate of the zero-grid-spacing solution.

3. APPROXIMATE RELATIVE ERROR (fine pair):
       e_a21 = |(f1 - f2) / f1|
   and coarse pair  e_a32 = |(f2 - f3) / f2|.

4. GRID CONVERGENCE INDEX with safety factor Fs:
       GCI_fine21   = Fs * e_a21 / (r21^p - 1)
       GCI_coarse32 = Fs * e_a32 / (r32^p - 1)
   GCI is reported as a fraction (multiply by 100 for %). It is an error BAND, not
   a signed error: the true value is expected to lie within +/- GCI*|f| of the
   reported grid solution with ~95% confidence (Roache's calibrated interpretation
   of Fs=1.25).

   SAFETY FACTOR Fs = 1.25 -- JUSTIFICATION.
   Roache (1994, 1998) recommends Fs = 1.25 when the observed order is supported by
   a THREE-grid study (so `p` is computed from the data, not assumed); Fs = 3.0 is
   the conservative value for a two-grid study where `p` must be assumed. ASME
   V&V20-2009 adopts Fs = 1.25 for three or more grids. Because this protocol
   mandates three levels and computes `p` from the triplet, Fs = 1.25 is the
   defensible choice and is the module default. It is exposed as a CLI flag so a
   reviewer can stress-test with Fs = 3.0.

5. ASYMPTOTIC-RANGE CHECK.
   GCI is only valid if the solutions are in the asymptotic range (monotone,
   order-p convergence with h). The standard check (Roache 1998, Eq. 5.10.7):
       asymptotic_ratio = GCI_coarse32 / (r21^p * GCI_fine21)
   should be ~= 1.0 when the grids are in the asymptotic range. We REPORT this
   ratio and do not silently assume it; the user judges whether |ratio - 1| is
   small enough (a common rule of thumb is within ~10-15%).

6. CONVERGENCE VERDICT from the convergence ratio R = e21 / e32 = (f2-f1)/(f3-f2):
       0 < R < 1   -> monotonic convergence   (GCI is meaningful)
       R < 0       -> oscillatory convergence  (GCI of limited meaning; report
                       bounding behaviour, p may be complex / ill-defined)
       R > 1       -> monotonic divergence     (no convergence; GCI meaningless)
   (ASME V&V20-2009 §7.5; Stern et al. 2001 verification taxonomy.)

DISCLOSURE / CONFIDENCE BOUNDARY
--------------------------------
The GCI assumes the three solutions lie in the asymptotic range; that assumption
is NOT verifiable from three points alone. We therefore always emit the
asymptotic-range ratio and the convergence verdict so the consumer can judge
whether the headline GCI band is trustworthy. For oscillatory or divergent
triplets the numeric GCI is still computed where defined but flagged as
not-meaningful in `gci_trustworthy`.

The core routines (`solve_observed_order`, `richardson_extrapolate`,
`compute_gci`) are PURE functions (no I/O) so they are unit-testable; see
`test_compute_gci.py`.

USAGE
  # Single QoI via flags (constant or non-constant ratio):
  python tools/analyze/compute_gci.py \
      --qoi mdot_loop --coarse 0.041 --medium 0.0405 --fine 0.0403 \
      --r21 2 --r32 2

  # Table of QoIs from CSV (columns: qoi_name,coarse,medium,fine,r21,r32):
  python tools/analyze/compute_gci.py --input qois.csv --output-dir <dir>

  # ... or JSON (list of objects with the same keys):
  python tools/analyze/compute_gci.py --input qois.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    relative_to_workspace,
    safe_float,
)

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_gci_study"

# Safety factor for a THREE-grid study (Roache 1994/1998; ASME V&V20-2009).
# See module docstring for the justification of 1.25 vs the two-grid value 3.0.
DEFAULT_SAFETY_FACTOR = 1.25

# Numerical tolerances for the fixed-point order solver.
_ORDER_TOL = 1.0e-10
_ORDER_MAX_ITER = 1000
# Two ratios are treated as equal (closed-form branch) within this tolerance.
_RATIO_EQUAL_TOL = 1.0e-9


def convergence_ratio(f3: float, f2: float, f1: float) -> float | None:
    """R = (f2 - f1) / (f3 - f2): the convergence ratio.

    f1=fine, f2=medium, f3=coarse. Returns None if the coarse pair difference is
    zero (verdict undefined; would divide by zero).
    """
    e32 = f3 - f2
    if e32 == 0.0:
        return None
    return (f2 - f1) / e32


def classify_convergence(ratio: float | None) -> str:
    """Verdict from the convergence ratio R (see module docstring §6)."""
    if ratio is None:
        return "undefined_equal_coarse_pair"
    if ratio < 0.0:
        return "oscillatory"
    if ratio < 1.0:
        return "monotonic_convergence"
    if ratio == 1.0:
        return "neutral_no_reduction"
    return "monotonic_divergence"


def solve_observed_order(
    f3: float,
    f2: float,
    f1: float,
    r21: float,
    r32: float,
) -> dict[str, Any]:
    """Observed order of accuracy `p` for a 3-grid triplet.

    f1=fine, f2=medium, f3=coarse; r21=h2/h1, r32=h3/h2 (both >= 1).

    For constant r (r21==r32) uses the closed form p = ln|e32/e21| / ln(r).
    For general r solves the transcendental equation by fixed-point iteration
    (Roache 1998 / ASME V&V20-2009):
        p = | ln|e32/e21| + q(p) | / ln(r21),  q(p)=ln((r21^p - s)/(r32^p - s)).

    Returns a dict with keys:
        status: "ok" | "undefined_equal_values" | "undefined_nonpositive_ratio"
                | "nonconverged_iteration"
        p:      observed order (float) or None
        sign:   s = sign(e32/e21)
        iters:  fixed-point iterations used (0 for closed form)
    Never raises on bad input; reports status instead.
    """
    if r21 <= 1.0 or r32 <= 1.0:
        return {"status": "undefined_nonpositive_ratio", "p": None, "sign": None, "iters": 0}

    e21 = f2 - f1
    e32 = f3 - f2
    # p is undefined when either difference is zero (equal solutions -> ratio 0 or
    # infinity in the logs). Roache: GCI requires distinct, monotone solutions.
    if e21 == 0.0 or e32 == 0.0:
        return {"status": "undefined_equal_values", "p": None, "sign": None, "iters": 0}

    ratio = e32 / e21
    s = math.copysign(1.0, ratio)
    abs_log = math.log(abs(ratio))

    # Constant-ratio closed form.
    if abs(r21 - r32) <= _RATIO_EQUAL_TOL:
        # q(p) == 0 identically, so p = ln|e32/e21| / ln(r).
        p = abs_log / math.log(r21)
        return {"status": "ok", "p": p, "sign": s, "iters": 0}

    # General non-constant ratio: fixed-point iteration.
    ln_r21 = math.log(r21)
    p = abs_log / ln_r21  # initial guess: constant-r estimate using r21
    if p <= 0.0:
        p = 1.0  # keep the iteration in a sane region for the powers below
    for it in range(1, _ORDER_MAX_ITER + 1):
        denom_a = (r21 ** p) - s
        denom_b = (r32 ** p) - s
        if denom_a == 0.0 or denom_b == 0.0 or (denom_a / denom_b) <= 0.0:
            return {"status": "nonconverged_iteration", "p": None, "sign": s, "iters": it}
        q = math.log(denom_a / denom_b)
        p_new = abs(abs_log + q) / ln_r21
        if not math.isfinite(p_new):
            return {"status": "nonconverged_iteration", "p": None, "sign": s, "iters": it}
        if abs(p_new - p) < _ORDER_TOL:
            return {"status": "ok", "p": p_new, "sign": s, "iters": it}
        p = p_new
    return {"status": "nonconverged_iteration", "p": p, "sign": s, "iters": _ORDER_MAX_ITER}


def richardson_extrapolate(f1: float, f2: float, r21: float, p: float) -> float:
    """Generalized Richardson extrapolation to zero grid spacing (Roache 1998).

    f1=fine, f2=medium; r21=h2/h1; p=observed order.
        f_exact = f1 + (f1 - f2) / (r21^p - 1)
    Raises ZeroDivisionError only if r21^p == 1 (r21==1 or p==0); callers guard
    this via solve_observed_order returning a valid p with r21 > 1.
    """
    denom = (r21 ** p) - 1.0
    return f1 + (f1 - f2) / denom


def _gci(safety_factor: float, e_a: float, r: float, p: float) -> float:
    """GCI = Fs * e_a / (r^p - 1).  e_a is the approximate relative error (fraction)."""
    return safety_factor * abs(e_a) / ((r ** p) - 1.0)


def compute_gci(
    coarse: float,
    medium: float,
    fine: float,
    r21: float,
    r32: float,
    safety_factor: float = DEFAULT_SAFETY_FACTOR,
) -> dict[str, Any]:
    """Full GCI analysis for one QoI from a 3-grid triplet.  PURE function.

    Arguments use the user-facing names: coarse=f3, medium=f2, fine=f1.
    r21=h2/h1, r32=h3/h2.

    Returns a dict carrying every reported quantity plus a verdict and the
    asymptotic-range ratio. Never raises on degenerate input; sets `status` and
    leaves order/extrapolation fields None where undefined.
    """
    f3, f2, f1 = float(coarse), float(medium), float(fine)
    result: dict[str, Any] = {
        "coarse_f3": f3,
        "medium_f2": f2,
        "fine_f1": f1,
        "r21": float(r21),
        "r32": float(r32),
        "safety_factor": float(safety_factor),
    }

    ratio = convergence_ratio(f3, f2, f1)
    verdict = classify_convergence(ratio)
    result["convergence_ratio_R"] = ratio
    result["verdict"] = verdict

    order = solve_observed_order(f3, f2, f1, r21, r32)
    result["order_status"] = order["status"]
    result["observed_order_p"] = order["p"]
    result["order_iterations"] = order["iters"]
    result["difference_sign_s"] = order["sign"]

    p = order["p"]
    if order["status"] != "ok" or p is None or p <= 0.0:
        # Cannot form a defensible GCI band without a valid positive order.
        result["f_exact_richardson"] = None
        result["e_approx_fine_e_a21"] = None
        result["e_approx_coarse_e_a32"] = None
        result["gci_fine_pct"] = None
        result["gci_coarse_pct"] = None
        result["asymptotic_range_ratio"] = None
        result["gci_trustworthy"] = False
        result["gci_note"] = (
            "Observed order undefined or non-positive (%s); GCI not formed. "
            "Verdict: %s." % (order["status"], verdict)
        )
        return result

    # Richardson extrapolation (fine/medium pair).
    try:
        f_exact = richardson_extrapolate(f1, f2, r21, p)
    except ZeroDivisionError:
        f_exact = None
    result["f_exact_richardson"] = f_exact

    # Approximate relative errors.
    e_a21 = abs((f1 - f2) / f1) if f1 != 0.0 else float("inf")
    e_a32 = abs((f2 - f3) / f2) if f2 != 0.0 else float("inf")
    result["e_approx_fine_e_a21"] = e_a21
    result["e_approx_coarse_e_a32"] = e_a32

    gci_fine = _gci(safety_factor, e_a21, r21, p)
    gci_coarse = _gci(safety_factor, e_a32, r32, p)
    result["gci_fine_pct"] = 100.0 * gci_fine
    result["gci_coarse_pct"] = 100.0 * gci_coarse

    # Asymptotic-range check: GCI_coarse / (r21^p * GCI_fine) ~= 1.
    denom = (r21 ** p) * gci_fine
    asym = gci_coarse / denom if denom != 0.0 else None
    result["asymptotic_range_ratio"] = asym

    in_asym = asym is not None and abs(asym - 1.0) <= 0.15
    trustworthy = verdict == "monotonic_convergence" and in_asym
    result["gci_trustworthy"] = bool(trustworthy)
    result["gci_note"] = (
        "GCI assumes solutions are in the asymptotic range; asymptotic_range_ratio "
        "(=%s, want ~1.0) and verdict (=%s) disclose whether that holds."
        % (("%.3f" % asym) if asym is not None else "n/a", verdict)
    )
    return result


# ---------------------------------------------------------------------------
# I/O glue (impure)
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = ("coarse", "medium", "fine", "r21", "r32")


def _read_table(path: Path) -> list[dict[str, Any]]:
    """Read a QoI table from CSV or JSON. Returns list of raw dict rows."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("qois", [data])
        return list(data)
    import csv

    return list(csv.DictReader(text.splitlines()))


def _coerce_row(row: dict[str, Any]) -> dict[str, Any] | None:
    """Parse one raw table row into typed inputs; return None if unparseable."""
    name = str(row.get("qoi_name") or row.get("qoi") or "qoi").strip()
    vals: dict[str, float] = {}
    for key in _REQUIRED_KEYS:
        v = safe_float(row.get(key))
        if v is None:
            return None
        vals[key] = v
    return {"qoi_name": name, **vals}


def analyze_row(parsed: dict[str, Any], safety_factor: float) -> dict[str, Any]:
    res = compute_gci(
        parsed["coarse"],
        parsed["medium"],
        parsed["fine"],
        parsed["r21"],
        parsed["r32"],
        safety_factor=safety_factor,
    )
    return {"qoi_name": parsed["qoi_name"], **res}


def _fmt(value: Any, spec: str) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "n/a"
    return format(value, spec)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--input", help="CSV or JSON table of QoIs (qoi_name,coarse,medium,fine,r21,r32).")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--safety-factor",
        type=float,
        default=DEFAULT_SAFETY_FACTOR,
        help="GCI safety factor Fs (default 1.25 for 3-grid studies; 3.0 is the conservative 2-grid value).",
    )
    # Single-QoI direct flags.
    parser.add_argument("--qoi", help="Name for a single-QoI run.")
    parser.add_argument("--coarse", type=float, help="Coarse-grid value f3.")
    parser.add_argument("--medium", type=float, help="Medium-grid value f2.")
    parser.add_argument("--fine", type=float, help="Fine-grid value f1.")
    parser.add_argument("--r21", type=float, help="Refinement ratio h2/h1.")
    parser.add_argument("--r32", type=float, help="Refinement ratio h3/h2.")
    args = parser.parse_args(argv)

    parsed_rows: list[dict[str, Any]] = []
    if args.input:
        for raw in _read_table(Path(args.input)):
            row = _coerce_row(raw)
            if row is not None:
                parsed_rows.append(row)
        if not parsed_rows:
            parser.error("no parseable rows in --input (need qoi_name,coarse,medium,fine,r21,r32)")
    else:
        if None in (args.coarse, args.medium, args.fine, args.r21, args.r32):
            parser.error("provide --input OR all of --coarse --medium --fine --r21 --r32")
        parsed_rows.append(
            {
                "qoi_name": args.qoi or "qoi",
                "coarse": args.coarse,
                "medium": args.medium,
                "fine": args.fine,
                "r21": args.r21,
                "r32": args.r32,
            }
        )

    results = [analyze_row(r, args.safety_factor) for r in parsed_rows]

    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)
    payload = {
        "generated_at": iso_timestamp(),
        "method": "Roache GCI (1994/1998); ASME V&V20-2009 §7.5; 3-grid study.",
        "safety_factor": args.safety_factor,
        "disclosure": (
            "GCI assumes the three solutions are in the asymptotic range. "
            "asymptotic_range_ratio (~1.0 wanted) and verdict are reported so the "
            "user can judge whether that assumption holds."
        ),
        "results": results,
    }
    json_dump(output_dir / "gci_results.json", payload)
    if results:
        csv_dump(output_dir / "gci_results.csv", list(results[0].keys()), results)

    # Console table.
    print(f"# Grid Convergence Index  ({iso_timestamp()})   Fs={args.safety_factor}")
    hdr = f"{'qoi':18s} {'p':>7s} {'f_exact':>12s} {'GCI_fine%':>10s} {'GCI_coarse%':>11s} {'asym~1':>8s}  verdict"
    print(hdr)
    print("-" * len(hdr))
    for r in results:
        print(
            f"{r['qoi_name'][:18]:18s} "
            f"{_fmt(r['observed_order_p'], '7.3f')} "
            f"{_fmt(r['f_exact_richardson'], '12.5g')} "
            f"{_fmt(r['gci_fine_pct'], '10.3f')} "
            f"{_fmt(r['gci_coarse_pct'], '11.3f')} "
            f"{_fmt(r['asymptotic_range_ratio'], '8.3f')}  "
            f"{r['verdict']}{'' if r['gci_trustworthy'] else '  [check disclosure]'}"
        )
    print(f"\nWrote {relative_to_workspace(output_dir / 'gci_results.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
