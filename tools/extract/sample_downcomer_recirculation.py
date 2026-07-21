#!/usr/bin/env python3
"""Downcomer (CFD span `right_leg`) recirculation characterization.

WHY THIS EXISTS  (user direction 2026-06-30)
--------------------------------------------
The upcomer was shown to host a real buoyancy-driven convection cell (15-33%
backflow area; negative apparent friction). The LitRev policy says the upcomer
and downcomer must NOT share a closure (branch-direction flag: buoyancy assists
in the heated upcomer, opposes in the cooled descending downcomer). Before we
assign the downcomer an ordinary f(Re)+Nu straight-pipe closure, we must check
whether the cooled descending return leg ALSO recirculates.

This is a PURE-PYTHON parser: it reads the already-reconstructed secmean cut-plane
dumps for the right_leg stations (TW4, TW5, TW6) and computes the SAME
recirculation metric as the upcomer tool. It does NOT run OpenFOAM.

DATA LIMITATION (recorded, important)
-------------------------------------
The convcell function object (which writes Ra/Ri/Gr/Re/Pr volume fields to cut
planes) was only configured for the UPCOMER spans (TW7/TW8/TP4/5/6). The
right_leg stations are present ONLY in secmeanSurfaces, whose columns are
  x y z Ux Uy Uz p_rgh rho T
i.e. NO nondimensional groups. We can therefore compute the velocity-based
recirculation metric (backflow_area_fraction, recirculation_intensity,
flow_alignment) on the downcomer, but NOT Ri/Ra/Re per cross-section. To get the
downcomer buoyancy screen (Ri=Gr/Re^2) directly, the convcell tool must be
re-run with right_leg stations added (do NOT do that here).

The recirculation metric definitions are IDENTICAL to
tools/extract/sample_upcomer_convection_cell.py so the two branches are
directly comparable:
  * backflow_area_fraction = fraction of masked faces with u_n < 0 (n = unit mean U)
  * recirculation_intensity = sum|u_n|_back / sum|u_n|_fwd
  * flow_alignment = |mean(U)| / mean(|U|)

USAGE
  python tools/extract/sample_downcomer_recirculation.py
(scans the three recon_salt{2,3,4}_of13 cases by default; --case-dir/--time/
--source-id to override a single case)
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump,
    relative_to_workspace,
)

_spec = importlib.util.spec_from_file_location(
    "sample_section_mean_pressure", ROOT / "tools" / "extract" / "sample_section_mean_pressure.py")
_secmean = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_secmean)

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_downcomer_recirculation"
# Downcomer = right_leg (owner-locked segment map). Corners TP2/TP3 sampled for context.
DOWNCOMER_LABELS = {"TW4", "TW5", "TW6"}
CONTEXT_LABELS = {"TP2", "TP3"}
FO = "secmeanSurfaces"

# Three reconstructed cases (already on disk; no OF run).
DEFAULT_CASES = [
    ("tmp/2026-06-30_claude_action_items/recon_salt2_of13", "7915",
     "viscosity_screening_salt_test_2_jin_coarse_mesh"),
    ("tmp/2026-06-30_claude_action_items/recon_salt3_of13", "7618",
     "viscosity_screening_salt_test_3_jin_coarse_mesh"),
    ("tmp/2026-06-30_claude_action_items/recon_salt4_of13", "10000",
     "viscosity_screening_salt_test_4_jin_coarse_mesh"),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case-dir")
    p.add_argument("--time")
    p.add_argument("--source-id")
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--leg-radius-m", type=float, default=0.04)
    return p.parse_args()


def analyze_station(case_dir: Path, st: dict[str, Any], leg_radius: float) -> dict[str, Any]:
    base = case_dir / "postProcessing" / FO
    hits = list(base.rglob(f"plane_{st['label']}.xy")) if base.exists() else []
    out: dict[str, Any] = {"label": st["label"], "span": st["span"]}
    if not hits:
        out["status"] = "no_output"
        return out
    data = np.loadtxt(hits[0])
    if data.ndim == 1:
        data = data.reshape(1, -1)
    # columns: x y z Ux Uy Uz p_rgh rho T
    if data.shape[1] < 9:
        out["status"] = f"unexpected_cols_{data.shape[1]}"
        return out
    pts, U = data[:, :3], data[:, 3:6]
    rho, T = data[:, 7], data[:, 8]
    center = np.array([st["x"], st["y"], st["z"]])
    mask = np.linalg.norm(pts - center, axis=1) < leg_radius
    if mask.sum() < 8:
        out["status"] = "too_few_masked_faces"
        out["n_masked"] = int(mask.sum())
        return out
    Um = U[mask]
    meanvec = Um.mean(axis=0)
    n = meanvec / (np.linalg.norm(meanvec) or 1.0)
    un = Um @ n
    fwd = un[un > 0].sum()
    back = -un[un < 0].sum()
    out.update({
        "status": "analyzed", "n_masked": int(mask.sum()),
        "backflow_area_fraction": float(np.mean(un < 0)),
        "recirculation_intensity": float(back / fwd) if fwd > 0 else float("nan"),
        "flow_alignment": float(np.linalg.norm(meanvec) / np.linalg.norm(Um, axis=1).mean()),
        "u_bulk_m_s": float(np.linalg.norm(meanvec)),
        "rho_section_mean_kg_m3": float(np.mean(rho[mask])),
        "T_section_mean_k": float(np.mean(T[mask])),
        # NO Ra/Ri/Re here: convcell FO did not cover right_leg (see module docstring).
        "nondim_available": False,
    })
    return out


def run_case(case_dir: Path, time: str, source_id: str, leg_radius: float) -> dict[str, Any]:
    all_st = _secmean.build_loop_polyline(source_id)
    wanted = DOWNCOMER_LABELS | CONTEXT_LABELS
    stations = [s for s in all_st if s["label"] in wanted]
    rows = [analyze_station(case_dir, st, leg_radius) for st in stations]
    return {
        "source_id": source_id, "case_dir": relative_to_workspace(case_dir), "time": time,
        "downcomer_labels": sorted(DOWNCOMER_LABELS), "context_labels": sorted(CONTEXT_LABELS),
        "stations": rows,
    }


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    ensure_dir(out_dir)
    if args.case_dir:
        cases = [(args.case_dir, args.time, args.source_id)]
    else:
        cases = DEFAULT_CASES
    payload = {
        "generated_at": iso_timestamp(),
        "metric_def": "backflow_area_fraction, recirculation_intensity, flow_alignment on "
                      "single-leg-masked (r<leg_radius) right_leg cross sections; identical defs "
                      "to sample_upcomer_convection_cell.py for direct branch comparison.",
        "nondim_note": "convcell FO covered only upcomer spans; right_leg has no per-section "
                       "Ra/Ri/Re. Re-run convcell with right_leg added for the buoyancy screen.",
        "confidence": "coarse mesh, laminar, single time per case; section-mean / velocity-field "
                      "metric only; SEED evidence for closure-TYPE decision, not a fitted law.",
        "cases": [],
    }
    print(f"{'case':6s} {'label':5s} {'span':12s} {'back':>5s} {'recirc':>7s} {'align':>6s} {'ubulk':>8s} {'T':>7s}")
    for cd, t, sid in cases:
        case_dir = (WORKSPACE_ROOT / cd).resolve() if not Path(cd).is_absolute() else Path(cd)
        cres = run_case(case_dir, t, sid, args.leg_radius_m)
        payload["cases"].append(cres)
        tag = sid.split("salt_test_")[-1].split("_")[0]
        for r in cres["stations"]:
            if r.get("status") == "analyzed":
                print(f"S{tag:5s} {r['label']:5s} {r['span']:12s} {r['backflow_area_fraction']:5.2f} "
                      f"{r['recirculation_intensity']:7.3f} {r['flow_alignment']:6.2f} "
                      f"{r['u_bulk_m_s']:8.4f} {r['T_section_mean_k']:7.1f}")
            else:
                print(f"S{tag:5s} {r['label']:5s} {r['span']:12s}  {r.get('status')}")
    json_dump(out_dir / "downcomer_recirculation.json", payload)
    flat = []
    for c in payload["cases"]:
        for r in c["stations"]:
            if r.get("status") == "analyzed":
                flat.append({"source_id": c["source_id"], **r})
    if flat:
        keys = sorted({k for r in flat for k in r.keys()})
        csv_dump(out_dir / "downcomer_recirculation.csv", keys,
                 [{k: r.get(k, "") for k in keys} for r in flat])
    print(f"\nWrote {relative_to_workspace(out_dir / 'downcomer_recirculation.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
