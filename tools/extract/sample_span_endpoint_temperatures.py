"""Sample mass-flux-weighted bulk temperature at span endpoints from existing XY cut files.

Approach
--------
The existing secmeanSurfaces foamPostProcess output contains 8-column cut-plane files:
  face_x  face_y  face_z  U_x  U_y  U_z  p_rgh  rho

Since the density equation of state is linear: rho = 2293.6 - 0.7497*T (Salt Jin),
temperature can be recovered exactly via inversion: T = (2293.6 - rho) / 0.7497.

With cp constant (cp = 1423.47 J/kg/K for Salt Jin), the enthalpy-flux-weighted bulk T
simplifies to the mass-flux-weighted mean:
  T_bulk = sum(rho * u_n * T_face) / sum(rho * u_n)

This avoids re-running foamPostProcess — the existing XY files are sufficient.

Span stations
-------------
Each span has 5 cut planes: s00 (inlet end), s01, s02 (midpoint), s03, s04 (outlet end).
This script extracts T_bulk at s00, s02, and s04 for each span.
delta_T = T_s04 - T_s00 (positive = temperature increases from s00 to s04).

Flow direction note (based on nominal loop circulation):
  lower_leg     : flow s00→s04 (up the heater incline)
  left_lower_leg: flow s00→s04 (up the upcomer bottom)
  test_section_span: flow s00→s04 (up through test section)
  left_upper_leg: flow s00→s04 (up the upcomer top)
  upper_leg     : flow s00→s04 (across the cooler)
  right_leg     : flow s04→s00 (down the downcomer — REVERSED convention)

Energy balance check
--------------------
For each span: enthalpy_change_W = mdot * cp * delta_T_kgrams_direction
where delta_T_mass_dir > 0 means the fluid gained heat traversing the span.

An implied mdot is estimated from: mdot_implied = Q_wall / (cp * |delta_T|)
This can be cross-checked against the convergence-monitor mdot if available.

Property coefficients (Salt Jin, all three mainline cases)
----------------------------------------------------------
rho = 2293.6 - 0.7497 * T          [kg/m3], T in K
Cp  = 1423.47                       [J/kg/K] (constant)
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Property coefficients (Salt Jin — same across S2/S3/S4)
# ---------------------------------------------------------------------------
RHO_C0 = 2293.6        # kg/m3
RHO_C1 = -0.7497       # kg/m3/K  (rho = RHO_C0 + RHO_C1 * T)
CP_J_KG_K = 1423.47    # J/kg/K (constant)

# Minimum faces for a valid bulk-T estimate at a cut plane
MIN_FACES = 8

# Span ordering for output
SPANS = [
    "lower_leg",
    "left_lower_leg",
    "test_section_span",
    "left_upper_leg",
    "upper_leg",
    "right_leg",
]

# Station indices to sample: 0=inlet end, 2=mid, 4=outlet end
STATION_INDICES = [0, 2, 4]

# Flow-traversal direction:
# +1 => fluid traverses from s00 → s04 (positive delta_T means heat gained)
# -1 => fluid traverses from s04 → s00 (downcomer flows downward, reversed in label order)
FLOW_DIRECTION: dict[str, int] = {
    "lower_leg": -1,       # fluid flows s04 (downcomer junction, x≈0.8) → s00 (upcomer junction, x≈0.1)
    "left_lower_leg": 1,
    "test_section_span": 1,
    "left_upper_leg": 1,
    "upper_leg": 1,        # fluid flows s00 (upcomer top, left) → s04 (downcomer top, right)
    "right_leg": -1,       # fluid flows s04 (upper, y≈0.6) → s00 (lower, y≈−0.1)
}


def t_from_rho(rho: np.ndarray) -> np.ndarray:
    """Recover T [K] from density using linear EOS: rho = RHO_C0 + RHO_C1*T."""
    return (rho - RHO_C0) / RHO_C1


def bulk_t_from_xy(xy_path: Path, leg_radius_m: float = 0.015) -> dict[str, Any]:
    """Compute mass-flux-weighted bulk T from an 8-column XY cut-plane file.

    Columns: face_x face_y face_z U_x U_y U_z p_rgh rho  (header starts with #)

    Returns dict with:
        T_bulk_k         : mixing-cup T = Σ(ρ·u_n·T)/Σ(ρ·u_n). Correct for energy balance
                           but unphysical when recirculation_ratio > 0.5.
        T_fwd_bulk_k     : forward-only mass-flux-weighted T. Best estimate of actual fluid
                           temperature at the cut plane. Equal to T_bulk_k when no backflow.
        T_simple_k       : simple face-mean T [K] (diagnostic).
        recirculation_ratio : bwd_flux / fwd_flux. > 0.5 means mixing-cup T is unreliable.
        mdot_proxy       : Σ(ρ·u_n) — proportional to net mass flow rate.
        n_faces          : total faces read.
        n_masked         : faces inside the leg radius mask.
        status           : 'ok' or error string.
    """
    out: dict[str, Any] = {"status": "ok"}
    try:
        data = np.loadtxt(xy_path, comments="#")
    except Exception as exc:
        return {"status": f"unreadable: {exc}"}

    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.size == 0 or data.shape[1] < 8:
        return {"status": f"insufficient_columns: {data.shape[1] if data.size > 0 else 0}"}

    pts = data[:, :3]      # x, y, z of face centres
    U = data[:, 3:6]       # velocity vector
    rho = data[:, 7]       # density kg/m3
    n_faces = len(pts)

    umag_all = np.linalg.norm(U, axis=1)
    # Pipe-centre estimate: centroid of the high-velocity faces (top 20%).
    # For cut planes that cross multiple pipes or are diagonal, the centroid of
    # ALL faces is far from the pipe axis. The high-velocity faces are inside the
    # pipe core and cluster around the true pipe centre.
    u_thresh = np.percentile(umag_all, 80)
    active_mask = umag_all >= u_thresh
    if active_mask.sum() >= MIN_FACES:
        pipe_centre = pts[active_mask].mean(axis=0)
    else:
        pipe_centre = pts.mean(axis=0)

    # Mask: faces within leg_radius of the pipe centre estimate
    dist = np.linalg.norm(pts - pipe_centre, axis=1)
    mask = dist < leg_radius_m
    n_masked = int(mask.sum())

    if n_masked < MIN_FACES:
        # Fallback: try using all faces (already a compact cross-section)
        n_masked = n_faces
        mask = np.ones(n_faces, dtype=bool)
        if n_masked < MIN_FACES:
            return {"status": "too_few_faces", "n_faces": n_faces, "n_masked": n_masked}

    Um = U[mask]
    rhom = rho[mask]
    Tm = t_from_rho(rhom)

    # Normal direction: use the mean velocity direction as the cut-plane normal
    mean_U = Um.mean(axis=0)
    umag = np.linalg.norm(mean_U)
    if umag < 1e-15:
        return {"status": "zero_mean_velocity", "n_masked": n_masked}

    normal = mean_U / umag
    u_n = Um @ normal    # signed normal velocity component

    weight = rhom * u_n  # mass-flux weight (signed)
    denom = float(weight.sum())

    if not math.isfinite(denom) or abs(denom) < 1e-30:
        return {"status": "zero_mass_flux", "n_masked": n_masked}

    t_bulk = float((weight * Tm).sum() / denom)
    t_simple = float(Tm.mean())

    # Forward-only bulk T and recirculation ratio (robust to recirculation zones)
    fwd = u_n > 0
    if fwd.any():
        fwd_flux = float((rhom * u_n)[fwd].sum())
        bwd_flux = float(abs((rhom * u_n)[~fwd].sum())) if (~fwd).any() else 0.0
        t_fwd_bulk = float(((rhom * u_n * Tm)[fwd]).sum() / fwd_flux) if fwd_flux > 1e-30 else t_simple
        recirculation_ratio = bwd_flux / fwd_flux if fwd_flux > 1e-30 else 0.0
    else:
        t_fwd_bulk = t_simple
        recirculation_ratio = 0.0

    out.update({
        "T_bulk_k": t_bulk,
        "T_fwd_bulk_k": t_fwd_bulk,
        "T_simple_k": t_simple,
        "recirculation_ratio": recirculation_ratio,
        "mdot_proxy": denom,   # sum(rho*u_n); scale by face area and leg section for true mdot
        "n_faces": n_faces,
        "n_masked": n_masked,
    })
    return out


def find_secmean_dir(recon_case_dir: Path) -> Path | None:
    """Find the secmeanSurfaces postProcessing directory within a reconstructed case."""
    pp = recon_case_dir / "postProcessing" / "secmeanSurfaces"
    if pp.is_dir():
        # Find the time subdirectory
        time_dirs = sorted([d for d in pp.iterdir() if d.is_dir()])
        if time_dirs:
            return time_dirs[-1]  # latest
    return None


def load_xy_for_station(secmean_dir: Path, span: str, station_idx: int) -> Path | None:
    """Return the XY file path for plane_{span}__s{station_idx:02d}.xy."""
    fname = f"plane_{span}__s{station_idx:02d}.xy"
    p = secmean_dir / fname
    return p if p.is_file() else None


def process_case(
    recon_case_dir: Path,
    case_id: str,
    source_id: str,
    heat_ledger_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Extract span endpoint temperatures for one reconstructed case.

    Returns a list of per-span records.
    """
    secmean_dir = find_secmean_dir(recon_case_dir)
    if secmean_dir is None:
        print(f"  WARNING: no secmeanSurfaces found in {recon_case_dir}")
        return []

    # Load heat ledger Q_wall per span if available (for mdot_implied)
    q_wall_by_span: dict[str, float] = {}
    if heat_ledger_path and heat_ledger_path.is_file():
        import csv
        with open(heat_ledger_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("source_id") == source_id or row.get("case_id") == source_id:
                    span = row.get("span") or row.get("segment")
                    if span and "net_heat_flux_w" in row:
                        try:
                            q_wall_by_span[span] = float(row["net_heat_flux_w"])
                        except (ValueError, TypeError):
                            pass

    records = []
    for span in SPANS:
        rec: dict[str, Any] = {
            "case_id": case_id,
            "source_id": source_id,
            "span": span,
            "flow_dir": "s00_to_s04" if FLOW_DIRECTION[span] == 1 else "s04_to_s00",
        }

        station_results: dict[int, dict[str, Any]] = {}
        for idx in STATION_INDICES:
            xy_path = load_xy_for_station(secmean_dir, span, idx)
            if xy_path is None:
                station_results[idx] = {"status": "file_not_found"}
                continue
            station_results[idx] = bulk_t_from_xy(xy_path)

        r_s00 = station_results.get(0, {})
        r_s02 = station_results.get(2, {})
        r_s04 = station_results.get(4, {})

        rec["T_s00_bulk_k"] = r_s00.get("T_bulk_k", float("nan"))
        rec["T_s00_fwd_bulk_k"] = r_s00.get("T_fwd_bulk_k", float("nan"))
        rec["T_s00_recirc_ratio"] = r_s00.get("recirculation_ratio", float("nan"))
        rec["T_s02_bulk_k"] = r_s02.get("T_bulk_k", float("nan"))
        rec["T_s04_bulk_k"] = r_s04.get("T_bulk_k", float("nan"))
        rec["T_s04_fwd_bulk_k"] = r_s04.get("T_fwd_bulk_k", float("nan"))
        rec["T_s04_recirc_ratio"] = r_s04.get("recirculation_ratio", float("nan"))
        rec["n_masked_s00"] = r_s00.get("n_masked", 0)
        rec["n_masked_s04"] = r_s04.get("n_masked", 0)
        rec["status_s00"] = r_s00.get("status", "missing")
        rec["status_s04"] = r_s04.get("status", "missing")

        # Use forward-bulk T when recirculation is heavy (> 0.5), else mixing-cup T
        def _best_t(res: dict[str, Any]) -> float:
            rc = res.get("recirculation_ratio", 0.0)
            if not math.isfinite(rc):
                rc = 0.0
            if rc > 0.5:
                return res.get("T_fwd_bulk_k", float("nan"))
            return res.get("T_bulk_k", float("nan"))

        # delta_T in the flow direction (inlet → outlet)
        t_in = _best_t(r_s00) if FLOW_DIRECTION[span] == 1 else _best_t(r_s04)
        t_out = _best_t(r_s04) if FLOW_DIRECTION[span] == 1 else _best_t(r_s00)
        rec["T_in_bulk_k"] = t_in
        rec["T_out_bulk_k"] = t_out

        if math.isfinite(t_in) and math.isfinite(t_out):
            delta_t = t_out - t_in
            rec["delta_T_flow_dir_k"] = delta_t
            # Enthalpy change: positive = fluid gained heat traversing the span
            # mdot_implied from Q_wall energy balance: mdot = Q / (cp * delta_T)
            q_wall = q_wall_by_span.get(span, float("nan"))
            rec["q_wall_w"] = q_wall
            if math.isfinite(q_wall) and abs(delta_t) > 0.01:
                rec["mdot_implied_kgs"] = q_wall / (CP_J_KG_K * delta_t)
                rec["enthalpy_change_w"] = q_wall  # = mdot * cp * delta_T by construction
            else:
                rec["mdot_implied_kgs"] = float("nan")
                rec["enthalpy_change_w"] = float("nan")
        else:
            rec["delta_T_flow_dir_k"] = float("nan")
            rec["q_wall_w"] = q_wall_by_span.get(span, float("nan"))
            rec["mdot_implied_kgs"] = float("nan")
            rec["enthalpy_change_w"] = float("nan")

        records.append(rec)

    return records


def write_csv(records: list[dict[str, Any]], out_path: Path) -> None:
    import csv
    if not records:
        return
    fieldnames = list(records[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)


def write_summary_json(records: list[dict[str, Any]], meta: dict[str, Any], out_path: Path) -> None:
    ok_records = [r for r in records if r.get("status_s00") == "ok" and r.get("status_s04") == "ok"]
    finite_dt = [r for r in ok_records if math.isfinite(r.get("delta_T_flow_dir_k", float("nan")))]

    summary = {
        **meta,
        "counts": {
            "total_rows": len(records),
            "ok_endpoint_pairs": len(ok_records),
            "finite_delta_T": len(finite_dt),
        },
        "limitations": [
            "T derived from rho inversion (T=(2293.6-rho)/0.7497); exact for linear EOS but assumes correct rho_coeffs",
            "mass-flux-weighted T_bulk uses mean-U as cut-plane normal — exact if flow is unidirectional at each cut",
            "mdot_implied requires Q_wall from heat ledger; enthalpy_change_w is not independently extracted",
            "right_leg (downcomer) flow convention: s04_to_s00; inlet/outlet labels adjusted accordingly",
            "test_section_span Ri bias ~5.7% from global D = 22.098 mm vs actual bore 20.9 mm (see ri_length_scale_audit.md)",
        ],
    }
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract mass-flux-weighted bulk T at span endpoints from existing XY cut files."
    )
    parser.add_argument("--recon-root", required=True,
                        help="Root dir containing recon_salt2_of13, recon_salt3_of13, recon_salt4_of13.")
    parser.add_argument("--heat-ledger", default=None,
                        help="Path to heat_source_sink_ledger.csv for Q_wall lookup.")
    parser.add_argument("--output-dir", required=True,
                        help="Output directory for CSV and JSON.")
    args = parser.parse_args()

    recon_root = Path(args.recon_root)
    heat_ledger = Path(args.heat_ledger) if args.heat_ledger else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        ("salt_2_jin", "viscosity_screening_salt_test_2_jin_coarse_mesh", "recon_salt2_of13"),
        ("salt_3_jin", "viscosity_screening_salt_test_3_jin_coarse_mesh", "recon_salt3_of13"),
        ("salt_4_jin", "viscosity_screening_salt_test_4_jin_coarse_mesh", "recon_salt4_of13"),
    ]

    all_records: list[dict[str, Any]] = []
    for case_id, source_id, recon_dir_name in cases:
        recon_dir = recon_root / recon_dir_name
        if not recon_dir.is_dir():
            print(f"  SKIP {case_id}: {recon_dir} not found")
            continue
        print(f"Processing {case_id} from {recon_dir} ...")
        recs = process_case(recon_dir, case_id, source_id, heat_ledger)
        all_records.extend(recs)
        for r in recs:
            t_in = r.get("T_in_bulk_k", float("nan"))
            t_out = r.get("T_out_bulk_k", float("nan"))
            dt = r.get("delta_T_flow_dir_k", float("nan"))
            print(f"  {r['span']:<25}  T_in={t_in:.1f} K  T_out={t_out:.1f} K  dT={dt:+.2f} K  "
                  f"status_s00={r.get('status_s00')} status_s04={r.get('status_s04')}")

    csv_path = output_dir / "span_endpoint_temperatures.csv"
    write_csv(all_records, csv_path)
    print(f"\nWrote {len(all_records)} rows to {csv_path}")

    meta = {
        "generated_at": "2026-07-08",
        "task": "AGENT-203",
        "inputs": {
            "recon_root": str(recon_root),
            "heat_ledger": str(heat_ledger) if heat_ledger else None,
        },
        "outputs": {
            "span_endpoint_temperatures_csv": str(csv_path),
        },
        "method": (
            "8-column XY cut files from secmeanSurfaces foamPostProcess output. "
            "T derived from rho inversion: T=(2293.6-rho)/0.7497. "
            "T_bulk = sum(rho*u_n*T)/sum(rho*u_n) (mass-flux-weighted, constant cp). "
            "Normal direction from mean velocity vector at each cut plane."
        ),
    }
    summary_path = output_dir / "summary.json"
    write_summary_json(all_records, meta, summary_path)
    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
