#!/usr/bin/env python3
"""Derive apparent Darcy friction factor per straight segment FROM section-mean
pressure profiles (the geometry-measured way), as a cross-check on the legacy
wall-based extractor (action L1/A3).

WHY THIS EXISTS
---------------
The legacy hydraulic path forms a per-segment friction factor from WALL pressure
(boundary-face p_rgh) and ignores the kinetic-energy term. The newer, physically
correct route uses CROSS-SECTION-MEAN quantities produced by
`tools/extract/sample_section_mean_pressure.py`:

  * section_mean_p_rgh_pa            -- static, hydrostatic-removed pressure
  * section_mean_total_pressure_pa   -- p0 = <p_rgh> + 1/2 rho u_bulk^2
  * u_bulk_m_s, section_mean_rho_kg_m3, hydraulic_diameter_m  -- MEASURED
  * x, y, z                          -- station coordinates (for arc length)
  * span, label, flow_alignment, gate

This tool consumes that JSON and derives, per STRAIGHT SEGMENT (grouped by span),
the apparent Darcy friction factor two ways and reports both with explicit
confidence columns. The NEW (total-pressure-gradient) method is the DEFAULT
because it is the physically correct mechanical-energy loss; the static-gradient
method is reported alongside so the difference (the reversible kinetic / area
change term) is visible.

CONVENTIONS (stated explicitly)
-------------------------------
* DARCY, not Fanning. We report the Darcy-Weisbach friction factor f_D, defined by
      dp_loss/ds = f_D * (1 / D_h) * (1/2 * rho * u_bulk^2)
  so that f_D = 2 * D_h * (dp_loss/ds) / (rho * u_bulk^2).
  The Fanning factor is f_F = f_D / 4; we DO NOT report Fanning here. The laminar
  reference we compare against is the Darcy value 64/Re (Fanning would be 16/Re).

* SIGN of dp/ds. In a real flow the loss term makes pressure DECREASE downstream,
  so the raw streamwise derivative d(p)/ds is NEGATIVE. The friction factor must be
  positive for a forward-flowing segment, so we use the LOSS gradient
      dp_loss/ds = -(p_downstream - p_upstream) / (s_downstream - s_upstream)
  i.e. we negate the signed streamwise gradient. We always order stations by
  increasing arc length along the segment using the station coordinates, and we
  take the average gradient across the segment endpoints (least sensitive to a
  single noisy interior station). A NEGATIVE derived f (pressure RISING downstream)
  is reported as-is (not clamped) and flagged, because it indicates either a
  pressure-recovery / area-change region or noise dominating a tiny gradient.

* STATIC vs TOTAL. The static p_rgh gradient includes REVERSIBLE pressure changes
  from cross-sectional area change (Bernoulli: where the bore narrows, static p
  drops even with zero loss). The TOTAL-pressure gradient d(p0)/ds removes that
  reversible term and is the true irreversible mechanical-energy loss per unit
  length; THIS is the physically correct quantity for a friction factor. We
  therefore DEFAULT to the total-pressure method and carry the static method as a
  diagnostic of how much reversible area-change pressure is present.

CONFIDENCE BOUNDARIES (disclosed)
---------------------------------
* This rests on SECTION-MEAN values. On these cases the dynamic-head term
  (1/2 rho u_bulk^2) is SMALL -- order ~0.18 Pa -- compared with the p_rgh swings
  along the loop, so the difference between the static and total methods is at the
  edge of the section-mean resolution. Treat the static-vs-total split as
  indicative, not closure-grade, until a finer mesh / area-weighted means exist.
* COARSE mesh only (project blocker B2): no mesh-independence bound on f.
* LAMINAR cases: the 64/Re reference is the right baseline, but the apparent f
  lumps entrance / development / curvature / form losses and is NOT pure wall
  friction. We report f/f_lam (excess-loss factor) to make that explicit.
* FEW stations per segment: a segment with only 2 clean stations gives a single
  two-point gradient with no redundancy. n_stations_used is reported so the reader
  can judge.
* Re requires the dynamic viscosity mu, which is NOT in the section JSON. We do
  NOT fabricate it: pass --mu-pa-s to get Re (and f/f_lam); otherwise Re, f_lam,
  and the excess factor are left NaN and flagged.

PURE-FUNCTION CORE
------------------
`arc_length_along`, `segment_pressure_gradient`, `apparent_darcy_friction`,
`reynolds_number`, and `laminar_darcy_reference` are side-effect-free and
unit-tested in `test_derive_segment_friction.py`. All divides guard against zero
by returning NaN rather than raising.

USAGE
  python tools/analyze/derive_segment_friction.py \
      --section-json work_products/.../section_mean_pressure_<id>.json [--section-json ...]
  python tools/analyze/derive_segment_friction.py --input-dir work_products/2026-06-30_claude_section_mean_pressure
  # add --mu-pa-s 0.0034 to also report Re and f/f_lam
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

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_segment_friction"

# Fully-developed laminar circular-pipe DARCY friction constant (f_D = 64/Re).
# The canonical reference for a fully-developed laminar duct; apparent f far above
# this is dominated by non-fully-developed / form / curvature effects.
LAMINAR_DARCY_CONST = 64.0

# Flow-alignment gate: |meanU|/<|U|> below this means the section mask still mixes
# directions (e.g. at a bend) so the section mean is unreliable. Mirrors the gate
# in sample_section_mean_pressure.py (FLOW_ALIGNMENT_GATE = 0.8).
FLOW_ALIGNMENT_GATE = 0.8

METHOD_TOTAL = "section_mean_total_pressure_gradient"
METHOD_STATIC = "section_mean_static_gradient"

NAN = float("nan")


# --------------------------------------------------------------------------- #
# Pure-function core (unit-tested; no I/O; NaN-guarded)                        #
# --------------------------------------------------------------------------- #
def arc_length_along(coords: list[tuple[float, float, float]]) -> list[float]:
    """Cumulative streamwise arc length (m) along an ordered list of 3D points.

    s[0] = 0; s[i] = s[i-1] + |p[i] - p[i-1]|. The points must already be ordered
    along the segment (this function does NOT reorder them). Returns one arc length
    per input point.
    """
    s: list[float] = []
    total = 0.0
    prev: tuple[float, float, float] | None = None
    for p in coords:
        if prev is not None:
            dx = p[0] - prev[0]
            dy = p[1] - prev[1]
            dz = p[2] - prev[2]
            total += math.sqrt(dx * dx + dy * dy + dz * dz)
        s.append(total)
        prev = p
    return s


def segment_pressure_gradient(arc_s: list[float], pressures: list[float]) -> float:
    """Mean streamwise pressure gradient d(p)/ds (Pa/m) across a segment.

    Uses the SEGMENT ENDPOINTS (first vs last clean station): this is the average
    gradient over the segment and is far less sensitive to a single noisy interior
    station than a finite-difference between adjacent stations. The returned value
    is the SIGNED derivative d(p)/ds (negative when pressure falls downstream).
    Callers negate it to obtain the positive loss gradient (see module docstring).

    Returns NaN if fewer than 2 points or if the span has zero arc length.
    """
    if len(arc_s) < 2 or len(pressures) < 2 or len(arc_s) != len(pressures):
        return NAN
    ds = arc_s[-1] - arc_s[0]
    if ds == 0:
        return NAN
    return (pressures[-1] - pressures[0]) / ds


def apparent_darcy_friction(
    dp_loss_ds: float, d_h: float, rho: float, u_bulk: float
) -> float:
    """Apparent Darcy-Weisbach friction factor.

        f_D = 2 * D_h * (dp_loss/ds) / (rho * u_bulk^2)

    `dp_loss_ds` is the POSITIVE loss gradient (Pa/m) -- i.e. the negated signed
    streamwise gradient (see module docstring on sign convention). With a positive
    loss gradient and forward flow this yields a positive Darcy factor.

    Divide-by-zero guarded: returns NaN if rho or u_bulk or D_h is non-positive /
    non-finite.
    """
    denom = rho * u_bulk * u_bulk
    if not math.isfinite(dp_loss_ds) or not math.isfinite(d_h):
        return NAN
    if not math.isfinite(denom) or denom <= 0 or d_h <= 0:
        return NAN
    return 2.0 * d_h * dp_loss_ds / denom


def reynolds_number(rho: float, u_bulk: float, d_h: float, mu: float | None) -> float:
    """Re = rho * u_bulk * D_h / mu.

    `mu` (dynamic viscosity, Pa*s) is NOT available in the section-mean JSON. If it
    is None or non-positive, we return NaN rather than fabricating a value.
    """
    if mu is None:
        return NAN
    if not all(math.isfinite(v) for v in (rho, u_bulk, d_h, mu)):
        return NAN
    if mu <= 0:
        return NAN
    return rho * u_bulk * d_h / mu


def laminar_darcy_reference(re: float) -> float:
    """Fully-developed laminar Darcy reference f_lam = 64/Re. NaN if Re invalid."""
    if not math.isfinite(re) or re <= 0:
        return NAN
    return LAMINAR_DARCY_CONST / re


def _mean(values: list[float]) -> float:
    clean = [v for v in values if v is not None and math.isfinite(v)]
    if not clean:
        return NAN
    return sum(clean) / len(clean)


# --------------------------------------------------------------------------- #
# I/O + orchestration                                                         #
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--section-json",
        action="append",
        default=[],
        help="Path to a section_mean_pressure_<id>.json file (repeatable).",
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Directory to glob section_mean_pressure_*.json from.",
    )
    parser.add_argument(
        "--mu-pa-s",
        type=float,
        default=None,
        help="Dynamic viscosity (Pa*s). If omitted, Re / f_lam / excess factor are "
        "left NaN and flagged (we do NOT fabricate Re).",
    )
    parser.add_argument(
        "--auto-mu-jin",
        action="store_true",
        help="Infer segment bulk T from the section-mean rho via the salt EoS "
        "(T = (2293.6 - rho)/0.7497) and evaluate the Jin viscosity correlation "
        "(tools/analyze/salt_properties.jin_mu) to populate Re / f_lam / excess. "
        "Overrides --mu-pa-s. Off by default, so legacy behaviour is unchanged.",
    )
    parser.add_argument(
        "--alignment-gate",
        type=float,
        default=FLOW_ALIGNMENT_GATE,
        help="Minimum flow_alignment for a station to be used (default 0.8).",
    )
    parser.add_argument(
        "--drop-fitting-ends",
        action="store_true",
        help="Drop stations flagged is_fitting_end (leg-end fitting/bend/junction "
        "stations from build_mesh_centerlines). Their minor-loss pressure jumps "
        "and one-sided tangents contaminate the STRAIGHT-friction gradient. "
        "Recommended for mesh-centerline (T1) inputs.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def collect_section_jsons(args: argparse.Namespace) -> list[Path]:
    paths: list[Path] = [Path(p) for p in args.section_json]
    if args.input_dir:
        paths.extend(sorted(Path(args.input_dir).glob("section_mean_pressure_*.json")))
    # de-duplicate while preserving order
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return out


def clean_stations(stations: list[dict[str, Any]], alignment_gate: float,
                   drop_fitting_ends: bool = False) -> list[dict[str, Any]]:
    """Keep only 'ok'-gated, well-aligned, sampled stations.

    If drop_fitting_ends, also drop stations flagged is_fitting_end (leg-end
    fitting/bend/junction stations that carry minor-loss pressure jumps).
    """
    kept: list[dict[str, Any]] = []
    for st in stations:
        if st.get("status") != "sampled":
            continue
        if st.get("gate") != "ok":
            continue
        if drop_fitting_ends and bool(st.get("is_fitting_end", False)):
            continue
        align = safe_float(st.get("flow_alignment"))
        if align is None or align < alignment_gate:
            continue
        kept.append(st)
    return kept


def order_segment_stations(stations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order stations within a segment by cumulative arc length from the first one.

    The section JSON stations are emitted in loop order, so they are already
    ordered along the segment. We compute arc length in that order and attach it.
    """
    coords = [
        (
            safe_float(st.get("x"), 0.0) or 0.0,
            safe_float(st.get("y"), 0.0) or 0.0,
            safe_float(st.get("z"), 0.0) or 0.0,
        )
        for st in stations
    ]
    arc = arc_length_along(coords)
    ordered: list[dict[str, Any]] = []
    for st, s in zip(stations, arc):
        merged = dict(st)
        merged["_arc_s_m"] = s
        ordered.append(merged)
    return ordered


def derive_segment(
    span: str,
    stations: list[dict[str, Any]],
    mu: float | None,
    auto_mu_jin: bool = False,
) -> list[dict[str, Any]]:
    """Return one row per method (total, static) for a single straight segment.

    If `auto_mu_jin` is True, the segment dynamic viscosity is computed from the
    segment-mean density via the salt EoS (T = temperature_from_rho(rho)) evaluated
    through the Jin viscosity correlation (tools/analyze/salt_properties.py). This
    overrides any explicit `mu`. When False (the default) the legacy behaviour is
    preserved exactly: Re uses the supplied `mu` (or NaN if mu is None).
    """
    ordered = order_segment_stations(stations)
    arc_s = [st["_arc_s_m"] for st in ordered]

    p_rgh = [safe_float(st.get("section_mean_p_rgh_pa")) for st in ordered]
    p_tot = [safe_float(st.get("section_mean_total_pressure_pa")) for st in ordered]

    # segment-averaged geometry / flow properties (the closure inputs)
    d_h = _mean([safe_float(st.get("hydraulic_diameter_m")) for st in ordered])
    rho = _mean([safe_float(st.get("section_mean_rho_kg_m3")) for st in ordered])
    u_bulk = _mean([safe_float(st.get("u_bulk_m_s")) for st in ordered])
    aligns = [safe_float(st.get("flow_alignment")) for st in ordered]
    align_min = min((a for a in aligns if a is not None and math.isfinite(a)), default=NAN)

    # Optionally derive mu(T) from the segment-mean rho via the Jin correlation.
    seg_temp_k = NAN
    mu_used = mu
    if auto_mu_jin:
        from tools.analyze.salt_properties import jin_mu, temperature_from_rho

        seg_temp_k = temperature_from_rho(rho) if math.isfinite(rho) else NAN
        mu_used = jin_mu(seg_temp_k) if math.isfinite(seg_temp_k) else None

    re = reynolds_number(rho, u_bulk, d_h, mu_used)
    f_lam = laminar_darcy_reference(re)
    arc_len = arc_s[-1] - arc_s[0] if len(arc_s) >= 2 else NAN

    rows: list[dict[str, Any]] = []
    for method, pressures in ((METHOD_TOTAL, p_tot), (METHOD_STATIC, p_rgh)):
        grad_signed = segment_pressure_gradient(arc_s, [p if p is not None else NAN for p in pressures])
        # Loss gradient is the NEGATED signed streamwise gradient (pressure falls
        # downstream in a forward-flowing loss region -> positive loss).
        dp_loss_ds = -grad_signed if math.isfinite(grad_signed) else NAN
        f_app = apparent_darcy_friction(dp_loss_ds, d_h, rho, u_bulk)
        excess = (f_app / f_lam) if (math.isfinite(f_app) and math.isfinite(f_lam) and f_lam > 0) else NAN

        flags: list[str] = []
        if mu_used is None or not math.isfinite(re):
            flags.append("Re_NaN_no_mu_provided")
        if auto_mu_jin:
            flags.append("mu_from_jin_corr_T_from_rho_eos")
        if math.isfinite(f_app) and f_app < 0:
            flags.append("negative_f_pressure_recovery_or_noise")
        if len(ordered) < 3:
            flags.append("few_stations_two_point_gradient_only")

        rows.append(
            {
                "method": method,
                "span": span,
                "n_stations_used": len(ordered),
                "segment_arc_length_m": arc_len,
                "dp_signed_ds_pa_per_m": grad_signed,
                "dp_loss_ds_pa_per_m": dp_loss_ds,
                "hydraulic_diameter_m": d_h,
                "section_mean_rho_kg_m3": rho,
                "u_bulk_m_s": u_bulk,
                "segment_temperature_k": seg_temp_k,
                "mu_pa_s_used": mu_used if mu_used is not None else NAN,
                "apparent_darcy_f": f_app,
                "reynolds_number": re,
                "laminar_ref_darcy_f_64_over_Re": f_lam,
                "excess_loss_factor_fapp_over_flam": excess,
                "flow_alignment_min": align_min,
                "flags": ";".join(flags),
            }
        )
    return rows


def process_case(
    path: Path, mu: float | None, alignment_gate: float, auto_mu_jin: bool = False,
    drop_fitting_ends: bool = False,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    source_id = payload.get("source_id", path.stem)
    stations = payload.get("stations", [])
    kept = clean_stations(stations, alignment_gate, drop_fitting_ends)

    # group clean stations by span/segment, preserving loop order
    by_span: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for st in kept:
        span = st.get("span", "") or "(unlabeled)"
        if span not in by_span:
            by_span[span] = []
            order.append(span)
        by_span[span].append(st)

    seg_rows: list[dict[str, Any]] = []
    for span in order:
        sts = by_span[span]
        if len(sts) < 2:
            # cannot form a gradient with <2 clean stations; record a skip row
            seg_rows.append(
                {
                    "method": "n/a",
                    "span": span,
                    "n_stations_used": len(sts),
                    "segment_arc_length_m": NAN,
                    "dp_signed_ds_pa_per_m": NAN,
                    "dp_loss_ds_pa_per_m": NAN,
                    "hydraulic_diameter_m": NAN,
                    "section_mean_rho_kg_m3": NAN,
                    "u_bulk_m_s": NAN,
                    "apparent_darcy_f": NAN,
                    "reynolds_number": NAN,
                    "laminar_ref_darcy_f_64_over_Re": NAN,
                    "excess_loss_factor_fapp_over_flam": NAN,
                    "flow_alignment_min": NAN,
                    "flags": "skipped_fewer_than_2_clean_stations",
                }
            )
            continue
        seg_rows.extend(derive_segment(span, sts, mu, auto_mu_jin))

    for row in seg_rows:
        row["source_id"] = source_id

    return {"source_id": source_id, "section_json": relative_to_workspace(path), "segments": seg_rows}


CSV_FIELDS = [
    "source_id",
    "span",
    "method",
    "n_stations_used",
    "segment_arc_length_m",
    "dp_signed_ds_pa_per_m",
    "dp_loss_ds_pa_per_m",
    "hydraulic_diameter_m",
    "section_mean_rho_kg_m3",
    "u_bulk_m_s",
    "segment_temperature_k",
    "mu_pa_s_used",
    "apparent_darcy_f",
    "reynolds_number",
    "laminar_ref_darcy_f_64_over_Re",
    "excess_loss_factor_fapp_over_flam",
    "flow_alignment_min",
    "flags",
]


def _fmt(value: Any, spec: str) -> str:
    v = safe_float(value)
    if v is None or not math.isfinite(v):
        return "nan"
    return format(v, spec)


def main() -> int:
    args = parse_args()
    paths = collect_section_jsons(args)
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    if not paths:
        print("No section-mean JSON files supplied. Use --section-json or --input-dir.")
        return 1

    cases = [
        process_case(p, args.mu_pa_s, args.alignment_gate, args.auto_mu_jin,
                     args.drop_fitting_ends)
        for p in paths
    ]

    all_rows: list[dict[str, Any]] = []
    for case in cases:
        all_rows.extend(case["segments"])

    payload = {
        "generated_at": iso_timestamp(),
        "default_method": METHOD_TOTAL,
        "friction_convention": "Darcy-Weisbach (f_D); Fanning would be f_D/4. Laminar ref is 64/Re (Darcy).",
        "sign_convention": "dp_loss/ds = -(p_down - p_up)/(s_down - s_up); positive = loss; negative f flagged.",
        "method_note": (
            "TOTAL-pressure gradient (default) is the irreversible mechanical-energy "
            "loss; STATIC p_rgh gradient additionally includes reversible area-change "
            "(Bernoulli) pressure, so the two differ by the reversible kinetic term."
        ),
        "mu_pa_s": args.mu_pa_s,
        "mu_source": (
            "jin_correlation_from_section_mean_rho_eos" if args.auto_mu_jin
            else ("explicit_mu_pa_s" if args.mu_pa_s is not None else "none_Re_NaN")
        ),
        "reynolds_note": (
            "mu is not in the section-mean JSON; Re/f_lam/excess are NaN unless --mu-pa-s "
            "is given or --auto-mu-jin is set. With --auto-mu-jin, per-segment T is "
            "inferred from section-mean rho via the linear salt EoS and mu(T) from the "
            "Jin viscosity correlation (tools/analyze/salt_properties.py); these inherit "
            "the section-mean / coarse-mesh caveats and are indicative, not closure-grade. "
            "Re is NOT fabricated."
        ),
        "confidence_boundaries": (
            "Section-mean values; dynamic head term ~0.18 Pa is small vs p_rgh swings so "
            "the static-vs-total split is indicative not closure-grade; coarse mesh "
            "(no mesh-independence bound); laminar; few stations per segment (n reported)."
        ),
        "alignment_gate": args.alignment_gate,
        "cases": cases,
    }
    json_dump(output_dir / "segment_friction.json", payload)
    csv_dump(
        output_dir / "segment_friction.csv",
        CSV_FIELDS,
        [{k: r.get(k, "") for k in CSV_FIELDS} for r in all_rows],
    )

    # ---- console table ----
    print(f"# Apparent Darcy friction per straight segment  ({iso_timestamp()})")
    print(f"# default method = {METHOD_TOTAL}; mu={'(none -> Re NaN)' if args.mu_pa_s is None else args.mu_pa_s}")
    header = (
        f"{'source_id':28s} {'span':20s} {'method':14s} {'n':>2s} {'Dh_mm':>6s} "
        f"{'u_bulk':>7s} {'dpL/ds':>9s} {'f_app':>9s} {'Re':>7s} {'f/f_lam':>8s} {'align':>5s}  flags"
    )
    print(header)
    for r in all_rows:
        method_short = {METHOD_TOTAL: "total", METHOD_STATIC: "static"}.get(r["method"], r["method"])
        dh_mm = (safe_float(r.get("hydraulic_diameter_m")) or NAN) * 1000.0
        print(
            f"{str(r.get('source_id',''))[:28]:28s} {str(r.get('span',''))[:20]:20s} "
            f"{method_short:14s} {r.get('n_stations_used',''):>2} {_fmt(dh_mm,'6.1f'):>6s} "
            f"{_fmt(r.get('u_bulk_m_s'),'7.4f'):>7s} {_fmt(r.get('dp_loss_ds_pa_per_m'),'9.3f'):>9s} "
            f"{_fmt(r.get('apparent_darcy_f'),'9.3f'):>9s} {_fmt(r.get('reynolds_number'),'7.1f'):>7s} "
            f"{_fmt(r.get('excess_loss_factor_fapp_over_flam'),'8.2f'):>8s} "
            f"{_fmt(r.get('flow_alignment_min'),'5.2f'):>5s}  {r.get('flags','')}"
        )
    print(f"\nWrote {relative_to_workspace(output_dir / 'segment_friction.json')}")
    print(f"Wrote {relative_to_workspace(output_dir / 'segment_friction.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
