#!/usr/bin/env python3
"""Upcomer convection-cell / recirculation characterization for correlation fitting.

WHY THIS EXISTS  (user direction 2026-06-30)
--------------------------------------------
The upcomer shows a REAL buoyancy-driven recirculation (convection cell), not a
clean through-flow: a single apparent friction factor is meaningless there (it
even comes out negative). The plan is to model the upcomer with a convection-cell
+ natural-circulation closure and to FIT a correlation that captures the onset
and limits of the recirculation as more CFD is run. This tool produces the
correlation-ready dataset: a recirculation METRIC (dependent variable) paired
with the governing NONDIMENSIONAL GROUPS (independent variables) per upcomer
section per case.

LITERATURE BASIS  (papers/LitRev-start-.../chapters/14 + 05)
-----------------------------------------------------------
- Natural-convection cell scaling (LeFrancois et al.): Nu(Ra,Pr) = C*Ra^n*Pr^m,
  Ra = beta*g*(Th-Tc)*Lc^3/(nu*alpha); molten-salt cells change scaling regime and
  large-scale circulation structure across ~2e7 < Ra < 2e9 (cavity study -> use as
  cell evidence, not a pipe HTC correlation).
- Mixed convection in vertical tubes (Jackson, Cotton & Axcell): use Ri = Gr/Re^2
  as the buoyancy screen; buoyancy assisting vs opposing the mean flow enhances or
  IMPAIRS transport and can drive reversed/recirculating flow. Upcomer and
  downcomer must NOT share a closure (branch-direction policy flag).
- Thermal development coordinate: Gz (Graetz). Report local quantities, not
  length-based development assumptions.

So the candidate independent groups for the recirculation correlation are
Ri = Gr/Re^2 (primary buoyancy screen), Ra (cell scaling), Gr, Re, Pr. The solver
already wrote Gr, Ra, Ri, Re, Pr as volume fields, which we sample directly.

RECIRCULATION METRIC (dependent variable; defined here, justified)
-----------------------------------------------------------------
On each upcomer cross-section (single-leg masked), with the net-flow direction n
(= unit mean velocity) and per-face normal velocity u_n = U.n:
  * backflow_area_fraction = fraction of section faces with u_n < 0  (0 = clean
    through-flow; ->0.5 = a fully developed counter-rotating cell).
  * recirculation_intensity = (sum |u_n| over backflow faces) / (sum |u_n| over
    forward faces)  -- magnitude of reverse vs forward volumetric flux.
  * flow_alignment = |mean(U)| / mean(|U|)  (1 = coherent; ->0 = cell-dominated).
These are robust, dimensionless, and trend monotonically with Re/Ri (verified:
backflow falls as forced flow rises Salt2->4), i.e. they capture onset/limits.

CONFIDENCE BOUNDARIES
  * Coarse mesh, laminar, single time per case (mainline continuation). The
    correlation is a FRAMEWORK to be populated as more CFD (onset/limit sweep)
    arrives -- treat current points as seed data, not a fitted law.
  * Solver-written Ra/Ri/Gr definitions (Lc, reference Delta T) are taken as-is;
    their exact definition should be page-audited against the case setup before a
    published correlation (flagged NEEDS-AUDIT in output).
  * Section-mean nondim groups are cross-section means over the masked leg.

USAGE  (needs an OF13 reconstruction with U + Ra Ri Gr Re Pr fields)
  source tools/ofenv/of13_env.sh   # not required for --skip-run parsing
  python tools/extract/sample_upcomer_convection_cell.py \
      --case-dir tmp/.../recon_salt2_of13 --time 7915 \
      --source-id viscosity_screening_salt_test_2_jin_coarse_mesh
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump,
    relative_to_workspace, safe_float,
)
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "sample_section_mean_pressure", ROOT / "tools" / "extract" / "sample_section_mean_pressure.py")
_secmean = importlib.util.module_from_spec(_spec); assert _spec and _spec.loader
_spec.loader.exec_module(_secmean)

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_upcomer_convection_cell"
# Upcomer = left_lower_leg + test_section_span + left_upper_leg (owner-locked map).
UPCOMER_SPANS = {"left_lower_leg", "test_section_span", "left_upper_leg"}
NONDIM_FIELDS = ["Ra", "Ri", "Gr", "Re", "Pr"]
FO = "convcellSurfaces"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case-dir", required=True)
    p.add_argument("--time", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--leg-radius-m", type=float, default=0.04)
    p.add_argument("--of-env-script", default="tools/ofenv/of13_env.sh")
    p.add_argument("--skip-run", action="store_true")
    p.add_argument("--spans", choices=["upcomer", "all"], default="upcomer",
                   help="'upcomer' (default) = the 3 upcomer spans; 'all' = every leg "
                        "(T5: Ri/Ra/recirc for downcomer etc. to quantify reversal margin).")
    p.add_argument("--centerline-source", choices=["profile", "mesh"], default="mesh",
                   help="'mesh' (default, T1): mesh-true centerlines from build_mesh_centerlines.py. "
                        "'profile': legacy schematic probe CSV (mis-oriented).")
    p.add_argument("--mesh-stations", default=None,
                   help="Path to mesh_stations.json; default = standard work_products location.")
    return p.parse_args()


def write_controldict(case_dir: Path, stations: list[dict[str, Any]]) -> None:
    lines = [
        "FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }",
        "application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;",
        "writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;",
        "writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;",
        "functions {", f"  {FO} {{", "    type surfaces;", '    libs ("libsampling.so");',
        "    writeControl writeTime; surfaceFormat raw; interpolate false; interpolationScheme cell;",
        f"    fields (U {' '.join(NONDIM_FIELDS)});", "    surfaces (",
    ]
    for st in stations:
        lines += [f"      plane_{st['label']} {{", "        type cuttingPlane; planeType pointAndNormal;",
                  f"        pointAndNormalDict {{ point ({st['x']} {st['y']} {st['z']}); normal ({st['nx']} {st['ny']} {st['nz']}); }}",
                  "      }"]
    lines += ["    );", "  }", "}"]
    (case_dir / "system" / "controlDict").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_fpp(case_dir: Path, t: str, log: Path, env_rel: str) -> int:
    env = ROOT / env_rel
    inner = f"source '{env}' >/dev/null 2>&1 && foamPostProcess -case '{case_dir}' -time '{t}'"
    with log.open("w") as fh:
        return subprocess.run(["bash", "-lc", inner], cwd=str(case_dir), stdout=fh, stderr=subprocess.STDOUT).returncode


def analyze_station(case_dir: Path, st: dict[str, Any], leg_radius: float) -> dict[str, Any]:
    base = case_dir / "postProcessing" / FO
    hits = list(base.rglob(f"plane_{st['label']}.xy")) if base.exists() else []
    out: dict[str, Any] = {"label": st["label"], "span": st["span"]}
    if not hits:
        out["status"] = "no_output"; return out
    data = np.loadtxt(hits[0])
    if data.ndim == 1:
        data = data.reshape(1, -1)
    # columns: x y z Ux Uy Uz Ra Ri Gr Re Pr
    if data.shape[1] < 3 + 3 + len(NONDIM_FIELDS):
        out["status"] = f"unexpected_cols_{data.shape[1]}"; return out
    pts, U = data[:, :3], data[:, 3:6]
    nd = {name: data[:, 6 + i] for i, name in enumerate(NONDIM_FIELDS)}
    center = np.array([st["x"], st["y"], st["z"]])
    mask = np.linalg.norm(pts - center, axis=1) < leg_radius
    if mask.sum() < 8:
        out["status"] = "too_few_masked_faces"; out["n_masked"] = int(mask.sum()); return out
    Um = U[mask]
    meanvec = Um.mean(axis=0)
    n = meanvec / (np.linalg.norm(meanvec) or 1.0)
    un = Um @ n
    fwd = un[un > 0].sum()
    back = -un[un < 0].sum()
    # INCLINATION (mesh/gravity frame; g=(0,-9.81,0)). The leg axis tangent is
    # (nx,ny,nz); cos(theta_g)=|axis . g_hat|=|ny|. Buoyancy projects into a
    # STREAMWISE part (g*cos -> assist/oppose -> flow reversal/cell, the vertical-
    # leg regime) and a TRANSVERSE part (g*sin -> stratification/secondary flow,
    # the horizontal-leg regime). Carrying this lets one correlation span legs of
    # different inclination instead of an orientation-agnostic Ri. (User question
    # 2026-06-30: inclination was NOT previously in the closures.)
    axis = np.array([st["nx"], st["ny"], st["nz"]], dtype=float)
    cos_g = abs(float(axis[1]))  # |axis . (0,-1,0)|
    incl_from_vertical_deg = math.degrees(math.acos(min(1.0, cos_g)))
    out.update({
        "inclination_from_vertical_deg": incl_from_vertical_deg,
        "buoyancy_streamwise_frac_cos": cos_g,           # 1=vertical (streamwise), 0=horizontal
        "buoyancy_transverse_frac_sin": math.sqrt(max(0.0, 1.0 - cos_g * cos_g)),
    })
    out.update({
        "status": "analyzed", "n_masked": int(mask.sum()),
        # recirculation metric (dependent variables)
        "backflow_area_fraction": float(np.mean(un < 0)),
        "recirculation_intensity": float(back / fwd) if fwd > 0 else float("nan"),
        "flow_alignment": float(np.linalg.norm(meanvec) / np.linalg.norm(Um, axis=1).mean()),
        "u_bulk_m_s": float(np.linalg.norm(meanvec)),
        # governing nondimensional groups (independent variables; section means)
        **{f"{name}_section_mean": float(np.mean(nd[name][mask])) for name in NONDIM_FIELDS},
        **{f"{name}_section_median": float(np.median(nd[name][mask])) for name in NONDIM_FIELDS},
    })
    # Orientation-resolved buoyancy parameter. Per the Route-B audit, the section
    # MEDIAN Ri (~O(1)) is the characteristic group, NOT the mean (low-U-dominated).
    ri_char = out["Ri_section_median"]
    out["Ri_streamwise_median"] = float(ri_char * cos_g)          # drives flow reversal/cell
    out["Ri_transverse_median"] = float(ri_char * out["buoyancy_transverse_frac_sin"])
    return out


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).resolve()
    out_dir = Path(args.output_dir); ensure_dir(out_dir)
    if args.centerline_source == "mesh":
        ms = Path(args.mesh_stations) if args.mesh_stations else _secmean.default_mesh_stations_path(args.source_id)
        if not ms.exists():
            print(f"ERROR: --centerline-source mesh but {relative_to_workspace(ms)} missing. "
                  f"Run tools/extract/build_mesh_centerlines.py first.", file=sys.stderr)
            return 2
        all_st = _secmean.load_mesh_stations(ms)
        print(f"Using MESH-true centerlines (T1): {relative_to_workspace(ms)}")
    else:
        all_st = _secmean.build_loop_polyline(args.source_id)
    stations = all_st if args.spans == "all" else [s for s in all_st if s["span"] in UPCOMER_SPANS]
    if not args.skip_run:
        write_controldict(case_dir, stations)
        log = out_dir / f"fpp_{args.source_id}.log"
        print(f"Running foamPostProcess (OF13)... {relative_to_workspace(log)}")
        rc = run_fpp(case_dir, args.time, log, args.of_env_script)
        if rc != 0:
            print(f"WARNING rc={rc}")
    rows = [analyze_station(case_dir, st, args.leg_radius_m) for st in stations]
    payload = {
        "generated_at": iso_timestamp(), "source_id": args.source_id,
        "case_dir": relative_to_workspace(case_dir), "time": args.time,
        "centerline_source": args.centerline_source, "spans_mode": args.spans,
        "model_basis": "convection-cell (LeFrancois Nu(Ra,Pr)) + mixed-convection screen (Ri=Gr/Re^2, Jackson-Cotton-Axcell); upcomer-only branch.",
        "recirculation_metric_def": "backflow_area_fraction, recirculation_intensity, flow_alignment on single-leg-masked cross sections.",
        "independent_groups": NONDIM_FIELDS,
        "needs_audit": "Solver Ra/Ri/Gr definitions (Lc, ref Delta T) must be page-audited vs case setup before a published correlation.",
        "confidence": "coarse mesh, laminar, single time per case (mainline continuation); SEED data for a correlation to be fit as onset/limit CFD arrives.",
        "stations": rows,
    }
    json_dump(out_dir / f"upcomer_convection_cell_{args.source_id}.json", payload)
    good = [r for r in rows if r.get("status") == "analyzed"]
    if good:
        keys = sorted({k for r in good for k in r.keys()})
        csv_dump(out_dir / f"upcomer_convection_cell_{args.source_id}.csv", keys, [{k: r.get(k, "") for k in keys} for r in good])
    print(f"\n# Upcomer convection-cell metrics  {args.source_id}  t={args.time}")
    print(f"{'label':22s} {'span':18s} {'backflow':>8s} {'recirc':>7s} {'align':>6s} {'Ri':>10s} {'Ra':>11s} {'Re':>8s}")
    for r in rows:
        if r.get("status") == "analyzed":
            print(f"{r['label']:22s} {r['span']:18s} {r['backflow_area_fraction']:8.2f} {r['recirculation_intensity']:7.2f} "
                  f"{r['flow_alignment']:6.2f} {r['Ri_section_mean']:10.3g} {r['Ra_section_mean']:11.3g} {r['Re_section_mean']:8.1f}")
        else:
            print(f"{r['label']:22s} {r['span']:18s}  {r.get('status')}")
    print(f"\nWrote {relative_to_workspace(out_dir / ('upcomer_convection_cell_' + args.source_id + '.json'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
