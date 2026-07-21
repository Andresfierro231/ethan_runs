#!/usr/bin/env python3
"""Sample SECTION-MEAN pressure + dynamic head along the loop (action items #1, #4).

WHY THIS EXISTS
---------------
The legacy hydraulic path takes pressure on the WALL (boundary-face p_rgh) and
forms Delta p from static p_rgh only, omitting the kinetic-energy term. For a 1D
mechanical-energy balance the correct quantities are the CROSS-SECTION-MEAN
static pressure and the TOTAL pressure  p0 = <p_rgh> + 0.5*rho*U_bulk^2. This
tool computes those plus the measured cross-section area (action #4).

METHOD (and the bug it fixes — AGENT-156 phase 2)
-------------------------------------------------
We cut a plane perpendicular to the loop centerline at each station and dump the
RAW per-face fields (`surfaces` FO, `.xy`). We then isolate a SINGLE pipe leg by
keeping only faces within `--leg-radius-m` of the station point, IN PYTHON.

This replaces the earlier approach that relied on the `cuttingPlane` `bounds`
keyword to limit the plane extent. That keyword is an ESI/foam-extend feature
that OpenFOAM **Foundation** silently ignores, so every plane spanned the whole
domain and averaged TWO counter-flowing legs together -> the area came out ~2.2x
a single bore and the area-averaged velocity cancelled to ~0 (the "velocity
anomaly"). Single-leg radius masking removes both artifacts (verified: post-mask
flow alignment |meanU|/<|U|> ~ 1.0).

QUANTITIES (per station, over the masked single leg)
  * section_mean_p_rgh_pa  = face-mean p_rgh   (static, hydrostatic-removed)
  * section_mean_rho       = face-mean rho
  * u_bulk_m_s             = |face-mean U| (valid because, post-mask, the flow is
                             coherent; flow_alignment reports how coherent)
  * dynamic_head_pa        = 0.5 * rho * u_bulk^2
  * section_mean_total_pressure_pa = section_mean_p_rgh + dynamic_head
  * section_area_m2         = total plane area * (n_masked / n_total_plane)
  * u_bulk_from_mdot_m_s   = mdot_monitor / (rho * section_area)  [cross-check]

CONFIDENCE BOUNDARIES
  * Face means approximate AREA means: cutting-plane faces are near-uniform in
    size on this mesh, so the unweighted mean ~ area mean. Exact area weighting
    needs per-face areas (not in the .xy); documented as a minor approximation.
  * flow_alignment < 0.8 flags a station where the mask still mixes directions
    (e.g. a bend) -> section mean unreliable there.
  * Reconstructed from staged data; run on the mainline CONTINUATION reconstruction
    for closure-grade numbers (see operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md).

USAGE
  python tools/extract/sample_section_mean_pressure.py \
      --case-dir tmp/.../recon_salt2_jin --time 2431 \
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
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    parse_scalar_series,
    relative_to_workspace,
    safe_float,
)
from tools.case_analysis_profiles import (  # noqa: E402  (read-only import)
    get_case_analysis_profile,
    load_station_centers_from_file,
)

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_section_mean_pressure"
# Half the minimum leg-to-leg spacing (~0.2 m) bounds the mask radius; 0.04 m
# captures one bore (radius ~0.016 m) with margin while excluding neighbouring legs.
DEFAULT_LEG_RADIUS_M = 0.04
FLOW_ALIGNMENT_GATE = 0.8  # |meanU|/<|U|> below this => mask still mixes directions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--time", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--leg-radius-m", type=float, default=DEFAULT_LEG_RADIUS_M)
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--of-env-script", default="tools/ofenv/of12_env.sh",
                        help="OpenFOAM env to source for foamPostProcess. Use tools/ofenv/of13_env.sh for "
                             "cases reconstructed under OF13 (e.g. when T is present, since T's custom BC "
                             "segfaults under OF12).")
    parser.add_argument("--dump-temperature", action="store_true",
                        help="Also dump T in the raw cut-plane (adds a 9th column) for downstream bulk-T / "
                             "thermal extraction. Requires the case to have a reconstructed T field (OF13).")
    parser.add_argument("--centerline-source", choices=["profile", "mesh"], default="mesh",
                        help="Where station coords + local tangent come from. 'mesh' (default, T1): "
                             "mesh-true centerlines from build_mesh_centerlines.py (heater cut "
                             "perpendicular to its ~21 deg axis; lower/right not swapped). 'profile': "
                             "legacy schematic tp_tw_probe_locations.csv (mis-oriented; kept for comparison).")
    parser.add_argument("--mesh-stations", default=None,
                        help="Path to mesh_stations.json (from build_mesh_centerlines.py). Required when "
                             "--centerline-source mesh. Default: the standard work_products location for "
                             "this source-id.")
    return parser.parse_args()


def load_mesh_stations(path: Path) -> list[dict[str, Any]]:
    """Load mesh-true stations (T1) into the same dict shape build_loop_polyline emits."""
    import json
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    for s in payload.get("stations", []):
        out.append({"label": s["label"], "span": s.get("span", ""),
                    "x": float(s["x"]), "y": float(s["y"]), "z": float(s["z"]),
                    "nx": float(s["nx"]), "ny": float(s["ny"]), "nz": float(s["nz"]),
                    "bore_m": float(s.get("bore_m", float("nan"))),
                    "is_fitting_end": bool(s.get("is_fitting_end", False))})
    return out


def default_mesh_stations_path(source_id: str) -> Path:
    return (WORKSPACE_ROOT / "work_products" / "2026-07-01_claude_mesh_centerlines"
            / source_id / "mesh_stations.json")


def build_loop_polyline(source_id: str) -> list[dict[str, Any]]:
    """Ordered stations along the full loop with coords + local tangent (plane normal)."""
    profile = get_case_analysis_profile(source_id)
    centers = load_station_centers_from_file(profile.tp_tw_locations)
    ordered: list[str] = []
    seen: set[str] = set()
    for span in profile.major_span_order:
        for lab in profile.major_spans[span]["centerline_labels"]:
            # dedupe globally by label (the loop closes back to TP1; a duplicate
            # surface name crashes the OpenFOAM `surfaces` FO).
            if lab not in seen:
                ordered.append(lab)
                seen.add(lab)
    label_span: dict[str, str] = {}
    for span in profile.major_span_order:
        for lab in profile.major_spans[span]["centerline_labels"]:
            label_span.setdefault(lab, span)
    pts = [np.array(centers[lab], dtype=float) for lab in ordered]
    n = len(pts)
    out: list[dict[str, Any]] = []
    for i, lab in enumerate(ordered):
        prev_p = pts[i - 1] if i > 0 else pts[i]
        next_p = pts[i + 1] if i < n - 1 else pts[i]
        tangent = next_p - prev_p
        norm = float(np.linalg.norm(tangent)) or 1.0
        tangent = tangent / norm
        out.append({"label": lab, "span": label_span.get(lab, ""),
                    "x": float(pts[i][0]), "y": float(pts[i][1]), "z": float(pts[i][2]),
                    "nx": float(tangent[0]), "ny": float(tangent[1]), "nz": float(tangent[2])})
    return out


def write_controldict(case_dir: Path, stations: list[dict[str, Any]], dump_temperature: bool = False) -> None:
    """controlDict with a single `surfaces` FO (raw) dumping every station plane.

    No `bounds` (Foundation ignores it); we mask to a single leg in Python.
    """
    lines = [
        "FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }",
        "application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;",
        "writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;",
        "writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;",
        "functions {",
        "  secmeanSurfaces {",
        "    type            surfaces;",
        '    libs            ("libsampling.so");',
        "    writeControl    writeTime;",
        "    surfaceFormat   raw;",
        "    interpolate     false;",
        "    interpolationScheme cell;",
        f"    fields          (U p_rgh rho{' T' if dump_temperature else ''});",
        "    surfaces (",
    ]
    for st in stations:
        lines += [
            f"      plane_{st['label']} {{",
            "        type        cuttingPlane;",
            "        planeType   pointAndNormal;",
            f"        pointAndNormalDict {{ point ({st['x']} {st['y']} {st['z']}); normal ({st['nx']} {st['ny']} {st['nz']}); }}",
            "      }",
        ]
    lines += ["    );", "  }", "}"]
    (case_dir / "system" / "controlDict").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_foampostprocess(case_dir: Path, time_name: str, log_path: Path, env_script_rel: str = "tools/ofenv/of12_env.sh") -> int:
    env_script = ROOT / env_script_rel
    inner = f"source '{env_script}' >/dev/null 2>&1 && foamPostProcess -case '{case_dir}' -time '{time_name}'"
    with log_path.open("w", encoding="utf-8") as log:
        return subprocess.run(["bash", "-lc", inner], cwd=str(case_dir), stdout=log, stderr=subprocess.STDOUT).returncode


def lookup_monitor_mdot(case_dir: Path) -> float:
    candidates = [case_dir]
    proc = case_dir / "processors64"
    if proc.is_symlink():
        candidates.append(proc.resolve().parent)
    for base in candidates:
        for mon in ("mdot_pipeleg_left_04_test_section", "mdot_pipeleg_lower_05_straight"):
            d = base / "postProcessing" / mon
            if d.exists():
                for dat in d.rglob("surfaceFieldValue.dat"):
                    series = parse_scalar_series(dat)
                    if series:
                        return float(series[-1]["value"])
    return float("nan")


def measured_area_and_dh(masked_pts: np.ndarray, normal: np.ndarray) -> tuple[float, float, float]:
    """Measured cross-section area, wetted perimeter, and D_h from masked faces.

    Projects the masked face centers onto the cut plane (drop the normal
    component), builds a 2D convex hull, and reports area, perimeter, and
    D_h = 4*A/P. This gives a GEOMETRY-MEASURED hydraulic diameter for the single
    isolated leg, replacing the legacy idealized-circle assumption (action #4).

    Confidence: the hull of face CENTERS slightly under-estimates the true bore
    (centers sit ~half a cell inside the boundary); on this fine cut the bias is
    small. Returned values are a tight lower bound on the true bore; documented.
    Returns (area_m2, perimeter_m, d_h_m); NaNs if scipy/hull unavailable.
    """
    try:
        from scipy.spatial import ConvexHull  # local import; scipy is available
    except Exception:
        return (float("nan"), float("nan"), float("nan"))
    if masked_pts.shape[0] < 3:
        return (float("nan"), float("nan"), float("nan"))
    n = normal / (np.linalg.norm(normal) or 1.0)
    # build an in-plane orthonormal basis (e1, e2) perpendicular to n
    ref = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = ref - np.dot(ref, n) * n
    e1 = e1 / (np.linalg.norm(e1) or 1.0)
    e2 = np.cross(n, e1)
    proj = np.column_stack([masked_pts @ e1, masked_pts @ e2])
    try:
        hull = ConvexHull(proj)
    except Exception:
        return (float("nan"), float("nan"), float("nan"))
    # ConvexHull.volume is the 2D area; .area is the 2D perimeter
    area = float(hull.volume)
    perim = float(hull.area)
    d_h = 4.0 * area / perim if perim > 0 else float("nan")
    return (area, perim, d_h)


def find_plane_xy(case_dir: Path, label: str) -> Path | None:
    base = case_dir / "postProcessing" / "secmeanSurfaces"
    if not base.exists():
        return None
    hits = list(base.rglob(f"plane_{label}.xy")) + list(base.rglob(f"*plane_{label}*.xy"))
    return hits[0] if hits else None


def sample_station(case_dir: Path, st: dict[str, Any], leg_radius: float, monitor_mdot: float) -> dict[str, Any]:
    out: dict[str, Any] = {**st}
    xy = find_plane_xy(case_dir, st["label"])
    if xy is None:
        out["status"] = "no_output"
        return out
    try:
        data = np.loadtxt(xy)
    except Exception:
        out["status"] = "unreadable"
        return out
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.size == 0 or data.shape[1] < 8:
        out["status"] = "empty"
        return out
    pts = data[:, :3]
    U = data[:, 3:6]
    p_rgh = data[:, 6]
    rho = data[:, 7]
    center = np.array([st["x"], st["y"], st["z"]], dtype=float)
    dist = np.linalg.norm(pts - center, axis=1)
    mask = dist < leg_radius
    n_total = int(data.shape[0])
    n_masked = int(mask.sum())
    if n_masked < 8:
        out.update({"status": "too_few_masked_faces", "n_total_plane": n_total, "n_masked": n_masked})
        return out
    Um = U[mask]
    speed = np.linalg.norm(Um, axis=1)
    mean_vec = Um.mean(axis=0)
    u_bulk = float(np.linalg.norm(mean_vec))
    alignment = float(u_bulk / speed.mean()) if speed.mean() > 0 else float("nan")
    # Signed projection of the mean velocity onto the station tangent (= cut-plane
    # normal). Its SIGN gives the flow direction relative to loop-order s, which
    # the momentum-budget tool (T1b) needs to orient the streamwise balance
    # per leg (loop-order is NOT always the flow direction).
    n_unit = np.array([st["nx"], st["ny"], st["nz"]], dtype=float)
    n_unit = n_unit / (np.linalg.norm(n_unit) or 1.0)
    u_along_tangent = float(mean_vec @ n_unit)
    rho_mean = float(rho[mask].mean())
    p_mean = float(p_rgh[mask].mean())
    # measured geometry (action #4): absolute area + hydraulic diameter
    plane_normal = np.array([st["nx"], st["ny"], st["nz"]], dtype=float)
    area_m2, perim_m, d_h_m = measured_area_and_dh(pts[mask], plane_normal)
    # bulk velocity cross-check from the monitor mdot and measured area
    u_bulk_from_mdot = (abs(monitor_mdot) / (rho_mean * area_m2)
                        if (math.isfinite(monitor_mdot) and math.isfinite(area_m2) and area_m2 > 0) else float("nan"))
    q_dyn = 0.5 * rho_mean * u_bulk * u_bulk
    p_total = p_mean + q_dyn
    out.update({
        "status": "sampled",
        "n_total_plane": n_total,
        "n_masked": n_masked,
        "section_mean_p_rgh_pa": p_mean,
        "section_mean_rho_kg_m3": rho_mean,
        "u_bulk_m_s": u_bulk,
        "u_along_tangent_m_s": u_along_tangent,
        "flow_alignment": alignment,
        "section_area_m2": area_m2,
        "wetted_perimeter_m": perim_m,
        "hydraulic_diameter_m": d_h_m,
        "u_bulk_from_mdot_m_s": u_bulk_from_mdot,
        "dynamic_head_pa": q_dyn,
        "section_mean_total_pressure_pa": p_total,
        "monitor_mdot_kg_s": monitor_mdot,
    })
    gate = "ok"
    if math.isfinite(alignment) and alignment < FLOW_ALIGNMENT_GATE:
        gate = "low_flow_alignment_mask_mixes_directions_(bend?)"
    out["gate"] = gate
    return out


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).resolve()
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)
    if args.centerline_source == "mesh":
        ms_path = Path(args.mesh_stations) if args.mesh_stations else default_mesh_stations_path(args.source_id)
        if not ms_path.exists():
            print(f"ERROR: --centerline-source mesh but {relative_to_workspace(ms_path)} missing. "
                  f"Run tools/extract/build_mesh_centerlines.py first.", file=sys.stderr)
            return 2
        stations = load_mesh_stations(ms_path)
        print(f"Using MESH-true centerlines (T1): {relative_to_workspace(ms_path)} ({len(stations)} stations)")
    else:
        stations = build_loop_polyline(args.source_id)
        print(f"Using PROFILE (schematic probe-CSV) centerlines: {len(stations)} stations")

    if not args.skip_run:
        write_controldict(case_dir, stations, dump_temperature=args.dump_temperature)
        log = output_dir / f"foampostprocess_{args.source_id}.log"
        print(f"Running foamPostProcess (raw plane dump; mesh re-stitch 1-2 min)... {relative_to_workspace(log)}")
        rc = run_foampostprocess(case_dir, args.time, log, env_script_rel=args.of_env_script)
        if rc != 0:
            print(f"WARNING: foamPostProcess rc={rc}; parsing whatever exists.")

    monitor_mdot = lookup_monitor_mdot(case_dir)
    rows = [sample_station(case_dir, st, args.leg_radius_m, monitor_mdot) for st in stations]

    # measured median bore area: estimate single-leg area for sampled stations from
    # the masked-face fraction is not available without total plane area; instead we
    # report the masked face count and leave absolute area to a later area-weighted
    # pass. u_bulk_from_mdot cross-check uses the section mean rho when available.
    payload = {
        "generated_at": iso_timestamp(),
        "source_id": args.source_id,
        "case_dir": relative_to_workspace(case_dir),
        "time": args.time,
        "method": "raw cuttingPlane dump + single-leg radius mask; face-mean p_rgh/rho/U; u_bulk=|meanU|; p0=<p_rgh>+0.5 rho u_bulk^2",
        "centerline_source": args.centerline_source,
        "mesh_stations_path": (relative_to_workspace(Path(args.mesh_stations) if args.mesh_stations
                               else default_mesh_stations_path(args.source_id))
                               if args.centerline_source == "mesh" else None),
        "leg_radius_m": args.leg_radius_m,
        "monitor_mdot_kg_s": monitor_mdot,
        "window_caveat": (
            "Run on the mainline CONTINUATION reconstruction for closure-grade numbers; "
            "staged parent-warmup is a method demonstration."
        ),
        "fix_note": (
            "Supersedes the earlier surfaceFieldValue/bounds approach: Foundation ignores "
            "cuttingPlane 'bounds', so prior planes averaged two counter-flowing legs "
            "(velocity ~0, area ~2.2x bore). Single-leg masking resolves both."
        ),
        "stations": rows,
    }
    json_dump(output_dir / f"section_mean_pressure_{args.source_id}.json", payload)
    if rows:
        keys = sorted({k for r in rows for k in r.keys()})
        csv_dump(output_dir / f"section_mean_pressure_{args.source_id}.csv", keys, [{k: r.get(k, "") for k in keys} for r in rows])

    print(f"\n# Section-mean pressure  {args.source_id}  t={args.time}  (monitor mdot={monitor_mdot})")
    print(f"{'label':22s} {'span':18s} {'nmask':>5s} {'p_rgh':>10s} {'u_bulk':>8s} {'Dh_mm':>6s} {'align':>6s} {'q_dyn':>8s} {'p_total':>10s}  gate")
    for r in rows:
        if r.get("status") == "sampled":
            dh_mm = r.get("hydraulic_diameter_m", float("nan")) * 1000.0
            print(f"{r['label']:22s} {r['span']:18s} {r['n_masked']:5d} {r['section_mean_p_rgh_pa']:10.3f} "
                  f"{r['u_bulk_m_s']:8.4f} {dh_mm:6.1f} {r['flow_alignment']:6.2f} {r['dynamic_head_pa']:8.4f} "
                  f"{r['section_mean_total_pressure_pa']:10.3f}  {r['gate']}")
        else:
            print(f"{r['label']:22s} {r['span']:18s}   {r.get('status')}")
    print(f"\nWrote {relative_to_workspace(output_dir / ('section_mean_pressure_' + args.source_id + '.json'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
