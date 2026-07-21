#!/usr/bin/env python3
r"""Streamwise bulk momentum budget per leg -> friction WITHOUT embedded buoyancy.

WHY (T1b, master TODO 2026-07-01):
-----------------------------------
`derive_segment_friction.py` reads a single leg's streamwise `p_rgh` gradient and
calls it friction. On the ISOTHERMAL upcomer legs that is fine, but on the
HEATED / COOLED legs (heater `lower_leg`, cooler `upper_leg`, plus the still
thermally-stratified downcomer `right_leg` and `test_section_span`) it returns a
NEGATIVE apparent Darcy f. That is not noise: in a buoyancy-driven loop, `p_rgh`
has only the hydrostatic of the ACTUAL density field removed
(`p = p_rgh + rho*gh`, `gh = g . x = -9.81*y`), so the streamwise momentum
balance carries a BUOYANCY SOURCE term that `p_rgh` does not contain, and on a
non-isothermal leg that term dominates and flips the sign.

Steady bulk streamwise momentum (per unit volume), projecting the OpenFOAM
buoyant momentum equation onto the flow direction s_hat:

    d/ds(rho u^2)  =  -d(p_rgh)/ds  -  gh * d(rho)/ds  +  [viscous . s_hat]
    \_____________/     \__________/    \____________/     \_______________/
      inertial (I)      p_rgh grad      buoyancy src B      wall friction

    => the pressure gradient that the WALL FRICTION actually balances is the
       COMBINED gradient  G_fric = d(p_rgh)/ds + gh*d(rho)/ds  (minus inertia).
    On an isothermal leg d(rho)/ds ~ 0 so G_fric -> d(p_rgh)/ds and this reduces
    EXACTLY to the legacy friction (a built-in consistency check).

This tool consumes the section-mean JSON from `sample_section_mean_pressure.py`
(mesh-centerline geometry, T1), computes the full budget per leg, and reports BOTH
the legacy buoyancy-embedded f (f_raw) and the de-buoyed f (f_corr), plus the
budget terms so the buoyancy source is CONSISTENTLY REPORTED.

CONFIDENCE / LIMITS:
  * Bulk 1D reduction: section-mean p_rgh/rho/u per station; endpoint gradients
    over interior stations (fitting ends dropped). Captures the leading balance,
    not the full 3D stress. The residual friction still carries the coarse-mesh
    discretization error (T6, unquantified).
  * `gh = -9.81*y` uses g=(0,-9.81,0) (verified in constant/g). gh is evaluated at
    the leg-mean y; the second-order rho*d(gh)/ds term is absorbed into p_rgh and
    is not double-counted.
  * Inertial term is O(rho*u^2/L) ~ tiny at these Re; reported and optionally
    removed (f_corr_ni) so the reader can see it is negligible.
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
from tools.analyze.derive_segment_friction import (  # noqa: E402
    apparent_darcy_friction,
    laminar_darcy_reference,
    reynolds_number,
)
from tools.analyze.salt_properties import jin_mu, temperature_from_rho  # noqa: E402

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-07-01_claude_momentum_budget"
G_MAG = 9.81  # m/s^2; g = (0, -9.81, 0) verified in constant/g
NAN = float("nan")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--section-json", action="append", default=[],
                   help="section_mean_pressure_<id>.json (repeatable).")
    p.add_argument("--input-dir", default=None,
                   help="Directory to glob section_mean_pressure_*.json from.")
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--keep-fitting-ends", action="store_true",
                   help="Include is_fitting_end stations (default drops them; their "
                        "minor-loss jumps contaminate the straight gradient).")
    return p.parse_args()


def collect_section_jsons(args: argparse.Namespace) -> list[Path]:
    paths = [Path(p) for p in args.section_json]
    if args.input_dir:
        paths.extend(sorted(Path(args.input_dir).glob("section_mean_pressure_*.json")))
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return out


def _endpoint_slope(s: list[float], v: list[float]) -> float:
    """Signed endpoint gradient d(v)/ds over the ordered stations (Pa/m etc.)."""
    if len(s) < 2 or len(v) < 2 or len(s) != len(v):
        return NAN
    ds = s[-1] - s[0]
    if ds == 0:
        return NAN
    return (v[-1] - v[0]) / ds


def _arc_length(coords: list[tuple[float, float, float]]) -> list[float]:
    s = [0.0]
    for i in range(1, len(coords)):
        a, b = coords[i - 1], coords[i]
        s.append(s[-1] + math.dist(a, b))
    return s


def _mean(vals: list[float]) -> float:
    clean = [v for v in vals if v is not None and math.isfinite(v)]
    return sum(clean) / len(clean) if clean else NAN


def budget_for_leg(span: str, stations: list[dict[str, Any]]) -> dict[str, Any]:
    coords = [(safe_float(st["x"]), safe_float(st["y"]), safe_float(st["z"])) for st in stations]
    s = _arc_length(coords)
    p_rgh = [safe_float(st.get("section_mean_p_rgh_pa")) for st in stations]
    rho = [safe_float(st.get("section_mean_rho_kg_m3")) for st in stations]
    u = [safe_float(st.get("u_bulk_m_s")) for st in stations]
    y = [c[1] for c in coords]
    u_along = [safe_float(st.get("u_along_tangent_m_s")) for st in stations]
    d_h = _mean([safe_float(st.get("hydraulic_diameter_m")) for st in stations])
    rho_m = _mean(rho)
    u_m = _mean(u)
    gh_mean = -G_MAG * _mean(y)  # gh = g . x = -9.81 * y

    # Flow orientation relative to loop-order s: sigma = sign(mean U . tangent).
    # The tangent (from build_mesh_centerlines) points along +s, so sigma=-1 means
    # the flow runs against loop-order (true for the heater + downcomer here). The
    # legacy friction tool assumed sigma=+1 for EVERY leg, which mis-orients those.
    u_along_mean = _mean(u_along)
    sigma = 1.0 if (math.isfinite(u_along_mean) and u_along_mean >= 0) else -1.0

    dP = _endpoint_slope(s, p_rgh)            # d(p_rgh)/ds  [Pa/m]  (loop-order s)
    dR = _endpoint_slope(s, rho)              # d(rho)/ds    [kg/m^4]
    dU = _endpoint_slope(s, u)                # d(u)/ds      [1/s]

    buoy_grad = gh_mean * dR                  # gh * d(rho)/ds  [Pa/m]
    inert_grad = rho_m * u_m * dU             # rho u du/ds     [Pa/m]

    # Rigorous streamwise balance (flow coordinate xi = sigma*s):
    #   friction_loss_per_vol = -dp_rgh/dxi - gh*drho/dxi - rho u du/dxi
    #                         = -sigma*(dP + buoy_grad + inert_grad).
    # f_raw_oriented removes only the orientation error (buoyancy still embedded);
    # f_corr additionally removes the buoyancy source; f_corr_ni also removes inertia.
    g_raw = -sigma * dP                       # flow-oriented, buoyancy still embedded
    g_corr = -sigma * (dP + buoy_grad)        # de-buoyed
    g_corr_ni = -sigma * (dP + buoy_grad + inert_grad)  # de-buoyed and de-inertia

    f_raw = apparent_darcy_friction(g_raw, d_h, rho_m, u_m)
    f_corr = apparent_darcy_friction(g_corr, d_h, rho_m, u_m)
    f_corr_ni = apparent_darcy_friction(g_corr_ni, d_h, rho_m, u_m)

    t_k = temperature_from_rho(rho_m) if math.isfinite(rho_m) else NAN
    mu = jin_mu(t_k) if math.isfinite(t_k) else None
    re = reynolds_number(rho_m, u_m, d_h, mu)
    f_lam = laminar_darcy_reference(re)

    return {
        "span": span,
        "n_stations_used": len(stations),
        "d_h_m": d_h,
        "rho_mean_kg_m3": rho_m,
        "u_bulk_mean_m_s": u_m,
        "bulk_T_K": t_k,
        "bulk_T_C": (t_k - 273.15) if math.isfinite(t_k) else NAN,
        "gh_mean_m2_s2": gh_mean,
        "u_along_tangent_mean_m_s": u_along_mean,
        "flow_orientation_sigma": sigma,
        "grad_p_rgh_pa_m": dP,
        "grad_rho_kg_m4": dR,
        "grad_u_per_s": dU,
        "buoyancy_source_grad_pa_m": buoy_grad,
        "inertial_grad_pa_m": inert_grad,
        "friction_grad_raw_pa_m": g_raw,
        "friction_grad_corrected_pa_m": g_corr,
        "friction_grad_corrected_noinertia_pa_m": g_corr_ni,
        "f_raw_buoyancy_embedded": f_raw,
        "f_corrected": f_corr,
        "f_corrected_noinertia": f_corr_ni,
        "Re": re,
        "f_lam_64_re": f_lam,
        "f_corrected_over_flam": (f_corr / f_lam) if (math.isfinite(f_corr) and math.isfinite(f_lam) and f_lam != 0) else NAN,
        "buoyancy_fraction_of_raw_grad": (abs(buoy_grad) / abs(dP)) if (math.isfinite(dP) and dP != 0) else NAN,
    }


def process_case(path: Path, keep_fitting_ends: bool) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    source_id = payload.get("source_id", path.stem)
    stations = payload.get("stations", [])
    by_span: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for st in stations:
        if st.get("status") != "sampled":
            continue
        if not keep_fitting_ends and bool(st.get("is_fitting_end", False)):
            continue
        span = st.get("span", "") or "(unlabeled)"
        by_span.setdefault(span, [])
        if span not in order:
            order.append(span)
        by_span[span].append(st)
    legs = []
    for span in order:
        sts = by_span[span]
        if len(sts) < 2:
            legs.append({"span": span, "n_stations_used": len(sts), "status": "too_few_stations"})
            continue
        row = budget_for_leg(span, sts)
        row["source_id"] = source_id
        legs.append(row)
    return {"source_id": source_id, "section_json": str(relative_to_workspace(path)), "legs": legs}


def main() -> int:
    args = parse_args()
    paths = collect_section_jsons(args)
    if not paths:
        print("No section JSONs given (use --section-json or --input-dir).", file=sys.stderr)
        return 2
    out_dir = Path(args.output_dir)
    ensure_dir(out_dir)
    cases = [process_case(p, args.keep_fitting_ends) for p in paths]
    payload = {
        "tool": "derive_streamwise_momentum_budget.py",
        "generated_at": iso_timestamp(),
        "method": (
            "bulk streamwise momentum budget from section-mean p_rgh/rho/u; "
            "friction driver = d(p_rgh)/ds + gh*d(rho)/ds (- inertia); "
            "gh = g.x = -9.81*y (g verified in constant/g). Isothermal legs reduce "
            "to legacy d(p_rgh)/ds friction (consistency check)."
        ),
        "cases": cases,
    }
    json_dump(out_dir / "momentum_budget.json", payload)
    flat = [leg for c in cases for leg in c["legs"] if leg.get("status") != "too_few_stations"]
    if flat:
        keys = sorted({k for r in flat for k in r.keys()})
        csv_dump(out_dir / "momentum_budget.csv", keys, [{k: r.get(k, "") for k in keys} for r in flat])

    print(f"\n# Streamwise momentum budget -> de-buoyed friction")
    hdr = (f"{'source':10s} {'leg':18s} {'Re':>6s} {'sig':>4s} {'dP/ds':>9s} {'buoy':>9s} {'inert':>8s} "
           f"{'f_raw':>7s} {'f_corr':>7s} {'f/flam':>7s} {'buoy/dP':>7s}")
    print(hdr)
    for c in cases:
        sid = c["source_id"].replace("viscosity_screening_", "").replace("_coarse_mesh", "")[:10]
        for leg in c["legs"]:
            if leg.get("status") == "too_few_stations":
                print(f"{sid:10s} {leg['span']:18s}  too_few_stations")
                continue
            print(f"{sid:10s} {leg['span']:18s} {leg['Re']:6.0f} {leg['flow_orientation_sigma']:+4.0f} "
                  f"{leg['grad_p_rgh_pa_m']:9.3f} "
                  f"{leg['buoyancy_source_grad_pa_m']:9.3f} {leg['inertial_grad_pa_m']:8.4f} "
                  f"{leg['f_raw_buoyancy_embedded']:7.2f} {leg['f_corrected']:7.2f} "
                  f"{leg['f_corrected_over_flam']:7.2f} {leg['buoyancy_fraction_of_raw_grad']:7.2f}")
    print(f"\nWrote {relative_to_workspace(out_dir / 'momentum_budget.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
