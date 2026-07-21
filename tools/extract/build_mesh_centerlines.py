#!/usr/bin/env python3
"""Build MESH-TRUE per-leg centerlines, tangents, and bores from wall patches.

WHY (T1, master TODO 2026-07-01):
-----------------------------------
The hydraulic extractors (`sample_section_mean_pressure.py`,
`derive_segment_friction.py`, `sample_upcomer_convection_cell.py`) place their
cut planes at station points taken from `tp_tw_probe_locations.csv`. That CSV is
a SCHEMATIC: it does not match the mesh geometry. Two concrete failures follow:

  1. The heater leg (mesh `pipeleg_lower_*`, ~21 deg from horizontal) is cut with
     a near-VERTICAL normal from the schematic, so the "cut plane" is not
     perpendicular to the true flow axis -> area, D_h, and dynamic head are wrong.
  2. The schematic frame SWAPS `lower_leg` <-> `right_leg` spatially, so friction
     and recirculation reported "by probe label" are attributed to the wrong
     physical leg.

The mesh `wall_patches` for each span, in contrast, are UNAMBIGUOUS
(`pipeleg_lower_*` is physically the heater). This tool derives geometry from
those patches instead of from the schematic CSV:

  * For each major span, dump the face centers of its wall patches (raw
    `surfaces` FO, `type patch`), the same mechanism the cut-plane tools use.
  * PCA / arc-length order those face centers to get an ordered centerline.
  * Place N stations along the arc length; local tangent = smoothed finite
    difference of consecutive station centroids (robust across bends); bore =
    2 * median radial distance of the local bin points from the station center
    in the plane perpendicular to the local tangent.

OUTPUT: a `mesh_stations.json` with, per station: {label, span, x, y, z,
nx, ny, nz (unit local tangent = cut-plane normal), bore_m, n_faces}. This file
is consumed by the extractors via `--centerline-source mesh --mesh-stations`.

CONFIDENCE / LIMITS:
  * Face CENTERS sit ~half a cell inside the wall, so the radial-distance bore is
    a slight over-estimate of the true bore radius relative to the wall, but a
    slight under-estimate of the flow bore; on the coarse mesh the bias is O(cell).
    Reported bores should be compared to the design bores (test section 20.9 mm,
    others ~22.0 mm) as the primary sanity gate, not treated as exact.
  * Local tangent from station finite differences assumes stations are dense
    enough to resolve bends; with the default N per span a single sharp bend can
    smear one station's normal. Bends are handled better by keeping straights and
    bends in separate spans (they already are in the profile patch naming).
"""
from __future__ import annotations

import argparse
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
    ensure_dir,
    iso_timestamp,
    json_dump,
    relative_to_workspace,
)
from tools.case_analysis_profiles import (  # noqa: E402  (read-only import)
    get_case_analysis_profile,
)

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-07-01_claude_mesh_centerlines"
DEFAULT_STATIONS_PER_SPAN = 5
FO_NAME = "meshCenterlinePatches"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--case-dir", required=True)
    p.add_argument("--time", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--stations-per-span", type=int, default=DEFAULT_STATIONS_PER_SPAN)
    p.add_argument("--skip-run", action="store_true",
                   help="Reuse existing patch surface dumps in the case (skip foamPostProcess).")
    p.add_argument("--of-env-script", default="tools/ofenv/of13_env.sh",
                   help="OpenFOAM env sourced for foamPostProcess. of13 for OF13 recons.")
    return p.parse_args()


def spans_with_wall_patches(profile: Any) -> list[tuple[str, list[str]]]:
    """Ordered (span, wall_patches) for every major span that has wall patches."""
    out: list[tuple[str, list[str]]] = []
    for span in profile.major_span_order:
        defn = profile.major_spans.get(span, {})
        patches = list(defn.get("wall_patches", []) or [])
        if patches:
            out.append((span, patches))
    return out


def write_controldict(case_dir: Path, patches: list[str]) -> None:
    """controlDict with one raw `patch` surface per wall patch, dumping p_rgh.

    Raw patch surfaces write `x y z <field>` per face; we only use x y z. p_rgh
    is guaranteed present in these reconstructions and makes the surface valid.
    """
    lines = [
        "FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }",
        "application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;",
        "writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;",
        "writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;",
        "functions {",
        f"  {FO_NAME} {{",
        "    type            surfaces;",
        '    libs            ("libsampling.so");',
        "    writeControl    writeTime;",
        "    surfaceFormat   raw;",
        "    interpolate     false;",
        "    interpolationScheme cell;",
        "    fields          (p_rgh);",
        "    surfaces (",
    ]
    for patch in patches:
        lines += [
            f"      {patch} {{",
            "        type        patch;",
            f"        patches     ({patch});",
            "      }",
        ]
    lines += ["    );", "  }", "}"]
    (case_dir / "system" / "controlDict").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_foampostprocess(case_dir: Path, time_name: str, log_path: Path, env_script_rel: str) -> int:
    env_script = ROOT / env_script_rel
    inner = f"source '{env_script}' >/dev/null 2>&1 && foamPostProcess -case '{case_dir}' -time '{time_name}'"
    with log_path.open("w", encoding="utf-8") as log:
        return subprocess.call(["bash", "-lc", inner], stdout=log, stderr=subprocess.STDOUT)


def find_patch_xy(case_dir: Path, patch: str) -> Path | None:
    base = case_dir / "postProcessing" / FO_NAME
    if not base.exists():
        return None
    hits = list(base.rglob(f"{patch}.xy")) + list(base.rglob(f"*{patch}*.xy"))
    return hits[0] if hits else None


def load_patch_face_centers(case_dir: Path, patches: list[str]) -> np.ndarray:
    """Concatenated face-center coordinates (Nx3) for a span's wall patches."""
    chunks: list[np.ndarray] = []
    for patch in patches:
        xy = find_patch_xy(case_dir, patch)
        if xy is None:
            continue
        try:
            data = np.loadtxt(xy)
        except Exception:
            continue
        if data.size == 0:
            continue
        if data.ndim == 1:
            data = data.reshape(1, -1)
        chunks.append(data[:, :3])
    if not chunks:
        return np.zeros((0, 3), dtype=float)
    return np.vstack(chunks)


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def stations_from_points(pts: np.ndarray, n_stations: int) -> list[dict[str, Any]]:
    """Arc-length-ordered stations with local tangent and bore from a point cloud.

    Method:
      1. PCA (SVD): principal axis = direction of maximum variance = leg axis.
      2. Project onto the axis -> scalar arc coordinate s; sort by s.
      3. Split s into n_stations equal bins; each station center = mean of its
         bin points (this rides the true curved centerline, not the straight PCA
         axis, so bends are followed).
      4. Local tangent = normalized finite difference of neighbouring station
         centers (endpoints one-sided).
      5. Bore = 2 * median radial distance of the bin points from the station
         center, measured in the plane perpendicular to the local tangent.
    """
    if pts.shape[0] < n_stations * 2:
        return []
    centroid = pts.mean(axis=0)
    centered = pts - centroid
    # PCA via SVD; first right-singular vector is the principal (axis) direction.
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    axis = _unit(vt[0])
    s = centered @ axis
    order = np.argsort(s)
    s_sorted = s[order]
    pts_sorted = pts[order]
    edges = np.linspace(s_sorted[0], s_sorted[-1], n_stations + 1)
    centers: list[np.ndarray] = []
    bins: list[np.ndarray] = []
    for i in range(n_stations):
        lo, hi = edges[i], edges[i + 1]
        if i == n_stations - 1:
            m = (s_sorted >= lo) & (s_sorted <= hi)
        else:
            m = (s_sorted >= lo) & (s_sorted < hi)
        if m.sum() < 3:
            continue
        binpts = pts_sorted[m]
        centers.append(binpts.mean(axis=0))
        bins.append(binpts)
    out: list[dict[str, Any]] = []
    ncen = len(centers)
    for i in range(ncen):
        prev_c = centers[i - 1] if i > 0 else centers[i]
        next_c = centers[i + 1] if i < ncen - 1 else centers[i]
        tangent = _unit(next_c - prev_c)
        if float(np.linalg.norm(tangent)) == 0.0:
            tangent = axis
        # radial distance in the plane perpendicular to the local tangent
        rel = bins[i] - centers[i]
        along = rel @ tangent
        radial = rel - np.outer(along, tangent)
        r = np.linalg.norm(radial, axis=1)
        bore = 2.0 * float(np.median(r)) if r.size else float("nan")
        out.append({
            "x": float(centers[i][0]), "y": float(centers[i][1]), "z": float(centers[i][2]),
            "nx": float(tangent[0]), "ny": float(tangent[1]), "nz": float(tangent[2]),
            "bore_m": bore,
            "n_faces": int(bins[i].shape[0]),
        })
    return out


def inclination_from_horizontal_deg(tangent: np.ndarray) -> float:
    """Angle of the tangent above the horizontal (x-z) plane; g = (0,-9.81,0).

    y is vertical, so |tangent_y| = sin(theta). Returns degrees in [0, 90].
    """
    ty = abs(float(tangent[1]))
    ty = min(1.0, max(0.0, ty))
    return float(np.degrees(np.arcsin(ty)))


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).resolve()
    profile = get_case_analysis_profile(args.source_id)
    span_patches = spans_with_wall_patches(profile)
    all_patches = [p for _, patches in span_patches for p in patches]

    out_dir = Path(args.output_dir) / args.source_id
    ensure_dir(out_dir)

    if not args.skip_run:
        write_controldict(case_dir, all_patches)
        log_path = out_dir / "foampostprocess.log"
        print(f"Running foamPostProcess (patch surfaces)... {relative_to_workspace(log_path)}")
        rc = run_foampostprocess(case_dir, args.time, log_path, args.of_env_script)
        if rc != 0:
            print(f"foamPostProcess exited {rc}; see {relative_to_workspace(log_path)}", file=sys.stderr)
            # continue anyway: partial dumps may still be usable, but flag it.

    stations: list[dict[str, Any]] = []
    span_diag: list[dict[str, Any]] = []
    for span, patches in span_patches:
        pts = load_patch_face_centers(case_dir, patches)
        if pts.shape[0] == 0:
            span_diag.append({"span": span, "status": "no_patch_output", "n_patch_faces": 0})
            continue
        sts = stations_from_points(pts, args.stations_per_span)
        if not sts:
            span_diag.append({"span": span, "status": "too_few_points", "n_patch_faces": int(pts.shape[0])})
            continue
        tangents = np.array([[s["nx"], s["ny"], s["nz"]] for s in sts])
        mean_tan = _unit(tangents.mean(axis=0))
        bores = [s["bore_m"] for s in sts if np.isfinite(s["bore_m"])]
        span_diag.append({
            "span": span,
            "status": "ok",
            "n_patch_faces": int(pts.shape[0]),
            "n_stations": len(sts),
            "mean_inclination_from_horizontal_deg": inclination_from_horizontal_deg(mean_tan),
            "median_bore_m": float(np.median(bores)) if bores else float("nan"),
            "wall_patches": patches,
        })
        # The first/last station of each span land on the fitting/bend/junction
        # terminations: their finite-diff tangent is one-sided and the fittings
        # widen the bore (see journal T1 notes). They carry minor-loss pressure
        # jumps and must be excluded from STRAIGHT-friction fits. Flag them so
        # downstream tools (derive_segment_friction --drop-fitting-ends) can drop.
        last = len(sts) - 1
        for j, s in enumerate(sts):
            s["is_fitting_end"] = bool(j == 0 or j == last)
            stations.append({"label": f"{span}__s{j:02d}", "span": span, **s})

    payload = {
        "tool": "build_mesh_centerlines.py",
        "generated_at": iso_timestamp(),
        "source_id": args.source_id,
        "case_dir": str(relative_to_workspace(case_dir)),
        "time": args.time,
        "stations_per_span": args.stations_per_span,
        "method": (
            "per-span PCA/arc-length of wall-patch face centers; local tangent = "
            "finite-diff of station centroids; bore = 2*median radial distance. "
            "Replaces schematic tp_tw_probe_locations.csv geometry (T1)."
        ),
        "n_stations": len(stations),
        "span_diagnostics": span_diag,
        "stations": stations,
    }
    out_json = out_dir / "mesh_stations.json"
    json_dump(out_json, payload)
    print(f"Wrote {len(stations)} mesh stations across {len(span_patches)} spans -> {relative_to_workspace(out_json)}")
    for d in span_diag:
        if d.get("status") == "ok":
            print(f"  {d['span']:>16}: {d['n_stations']} stn, "
                  f"incl {d['mean_inclination_from_horizontal_deg']:.1f} deg, "
                  f"bore {1000*d['median_bore_m']:.1f} mm, {d['n_patch_faces']} faces")
        else:
            print(f"  {d['span']:>16}: {d['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
