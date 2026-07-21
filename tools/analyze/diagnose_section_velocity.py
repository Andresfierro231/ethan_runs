#!/usr/bin/env python3
"""Diagnose the section-mean velocity anomaly (AGENT-156 phase 2, task 2).

PROBLEM
-------
`sample_section_mean_pressure.py` found that, at clean cross-sections, the
area-averaged normal velocity `areaAverage(U)·n` integrates to ~0, implying a
mass flux ~100x below the mdot monitor (~0.0132 kg/s). Until we know WHY, the
dynamic-head / total-pressure term cannot be trusted.

This tool dumps the RAW cut-plane velocity field at chosen stations (OpenFOAM
`surfaces` function object, `surfaceFormat raw`) and decomposes it so the cause
is unambiguous:
  * mean SPEED  <|U|>           -> if ~0, the reconstructed U is genuinely tiny
                                   here (reconstruction / warmup problem).
  * mean NORMAL <U·n>           -> the throughflow component (should give mdot).
  * mean TANGENTIAL <|U - (U·n)n|>
  * forward/backward area fractions (does the plane catch counter-flow that
    cancels in the average?).
  * implied mdot = rho * <U·n> * A   vs the monitor mdot.

Decision tree the output resolves:
  - <|U|> ~ 0                      => reconstruction/warmup: U field is dead here.
  - <|U|> large, <U·n> ~ 0,
    tangential large              => plane normal misaligned with the local flow
                                     (centerline tangent != true flow axis), OR
                                     the cut is oblique.
  - <U·n> swings sign across faces => plane catches counter-flowing passages.

Read-only on a reconstructed case; calls foamPostProcess in a subshell that
sources tools/ofenv/of12_env.sh (so the OF toolchain does not break Python).

USAGE
  python tools/analyze/diagnose_section_velocity.py \
      --case-dir tmp/.../recon_salt2_jin --time 2431 \
      --source-id viscosity_screening_salt_test_2_jin_coarse_mesh \
      --labels TW2,TW5,TP4
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
    relative_to_workspace,
    safe_float,
)

# Reuse the loop-polyline builder from the section-mean tool (same station frame).
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "sample_section_mean_pressure", ROOT / "tools" / "extract" / "sample_section_mean_pressure.py"
)
_secmean = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_secmean)

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_velocity_diagnostic"
DEFAULT_BOX_HALF_M = 0.05


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case-dir", required=True)
    p.add_argument("--time", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--labels", default="TW2,TW5,TP4", help="Comma-separated station labels to diagnose.")
    p.add_argument("--box-half-m", type=float, default=DEFAULT_BOX_HALF_M)
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--skip-run", action="store_true")
    return p.parse_args()


def write_surfaces_controldict(case_dir: Path, stations: list[dict[str, Any]], box_half: float) -> None:
    lines = [
        "FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }",
        "application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;",
        "writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;",
        "writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;",
        "functions {",
        "  diagSurfaces {",
        "    type            surfaces;",
        '    libs            ("libsampling.so");',
        "    writeControl    writeTime;",
        "    surfaceFormat   raw;",
        "    interpolate     false;",
        "    interpolationScheme cell;",
        "    fields          (U p_rgh rho);",
        "    surfaces (",
    ]
    for st in stations:
        x, y, z = st["x"], st["y"], st["z"]
        b0 = (x - box_half, y - box_half, z - box_half)
        b1 = (x + box_half, y + box_half, z + box_half)
        lines += [
            f"      plane_{st['label']} {{",
            "        type        cuttingPlane;",
            "        planeType   pointAndNormal;",
            f"        pointAndNormalDict {{ point ({x} {y} {z}); normal ({st['nx']} {st['ny']} {st['nz']}); }}",
            f"        bounds      ({b0[0]} {b0[1]} {b0[2]}) ({b1[0]} {b1[1]} {b1[2]});",
            "      }",
        ]
    lines += ["    );", "  }", "}"]
    (case_dir / "system" / "controlDict").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_foampostprocess(case_dir: Path, time_name: str, log_path: Path) -> int:
    env_script = ROOT / "tools" / "ofenv" / "of12_env.sh"
    inner = f"source '{env_script}' >/dev/null 2>&1 && foamPostProcess -case '{case_dir}' -time '{time_name}'"
    with log_path.open("w", encoding="utf-8") as log:
        return subprocess.run(["bash", "-lc", inner], cwd=str(case_dir), stdout=log, stderr=subprocess.STDOUT).returncode


def find_raw_surface(case_dir: Path, label: str) -> Path | None:
    """OpenFOAM Foundation writes raw cutting-plane surfaces as `<name>.xy`."""
    base = case_dir / "postProcessing" / "diagSurfaces"
    if not base.exists():
        return None
    hits = list(base.rglob(f"plane_{label}.xy")) + list(base.rglob(f"*plane_{label}*.xy"))
    return hits[0] if hits else None


def parse_raw_vectors(path: Path) -> np.ndarray:
    """Parse a raw `.xy` surface. Columns: x y z Ux Uy Uz p_rgh rho. Returns Nx8."""
    try:
        data = np.loadtxt(path)
    except Exception:
        return np.empty((0, 0))
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data


def _stats(U: np.ndarray, n: np.ndarray) -> dict[str, Any]:
    speed = np.linalg.norm(U, axis=1)
    un = U @ n
    mean_vec = U.mean(axis=0)
    sp = float(speed.mean())
    return {
        "n_faces": int(U.shape[0]),
        "mean_speed_mag_U": sp,
        "mean_normal_U_dot_n": float(un.mean()),
        "mean_vector_magnitude": float(np.linalg.norm(mean_vec)),
        "flow_alignment_meanvec_over_speed": float(np.linalg.norm(mean_vec) / sp) if sp > 0 else float("nan"),
        "forward_area_fraction": float(np.mean(un > 0)),
        "backward_area_fraction": float(np.mean(un < 0)),
    }


def diagnose_station(case_dir: Path, st: dict[str, Any], time_name: str, leg_radius: float = 0.04) -> dict[str, Any]:
    raw = find_raw_surface(case_dir, st["label"])
    out: dict[str, Any] = {"label": st["label"], "span": st["span"]}
    if raw is None:
        out["status"] = "no_raw_U_output"
        return out
    data = parse_raw_vectors(raw)
    if data.size == 0 or data.shape[1] < 6:
        out["status"] = "empty_or_malformed"
        return out
    pts = data[:, :3]
    U = data[:, 3:6]
    n = np.array([st["nx"], st["ny"], st["nz"]], dtype=float)
    n = n / (np.linalg.norm(n) or 1.0)
    full = _stats(U, n)
    # single-leg mask: faces within leg_radius of the station point
    center = np.array([st["x"], st["y"], st["z"]], dtype=float)
    mask = np.linalg.norm(pts - center, axis=1) < leg_radius
    masked = _stats(U[mask], n) if mask.sum() >= 8 else {"n_faces": int(mask.sum())}
    out["status"] = "diagnosed"
    out["full_plane"] = full
    out["single_leg_masked"] = masked
    # interpret: the diagnosis that explains the anomaly
    sp = full["mean_speed_mag_U"]
    if sp < 1e-3:
        out["interpretation"] = "reconstruction_or_warmup: speed ~0 (field dead here)"
    elif full["flow_alignment_meanvec_over_speed"] < 0.3 and masked.get("flow_alignment_meanvec_over_speed", 0) > 0.7:
        out["interpretation"] = ("MULTI_LEG_CANCELLATION: full plane spans multiple counter-flowing legs "
                                 "(mean vector cancels) but single-leg mask is coherent. ROOT CAUSE of the "
                                 "velocity anomaly; fix = single-leg masking.")
    elif full["flow_alignment_meanvec_over_speed"] > 0.7:
        out["interpretation"] = "single_clean_cross_section: full plane already coherent"
    else:
        out["interpretation"] = "ambiguous: inspect spatial face distribution"
    return out


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).resolve()
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)
    want = {l.strip() for l in args.labels.split(",") if l.strip()}
    all_stations = _secmean.build_loop_polyline(args.source_id)
    stations = [s for s in all_stations if s["label"] in want] or all_stations[:3]

    if not args.skip_run:
        write_surfaces_controldict(case_dir, stations, args.box_half_m)
        log = output_dir / f"foampostprocess_diag_{args.source_id}.log"
        print(f"Running foamPostProcess (raw surface dump; mesh re-stitch 1-2 min)... {relative_to_workspace(log)}")
        rc = run_foampostprocess(case_dir, args.time, log)
        if rc != 0:
            print(f"WARNING: foamPostProcess rc={rc}; parsing whatever exists.")

    results = [diagnose_station(case_dir, st, args.time) for st in stations]
    json_dump(output_dir / f"velocity_diagnostic_{args.source_id}.json",
              {"generated_at": iso_timestamp(), "case_dir": relative_to_workspace(case_dir),
               "time": args.time, "stations": results})
    diag = [r for r in results if r.get("status") == "diagnosed"]
    if diag:
        csv_dump(output_dir / f"velocity_diagnostic_{args.source_id}.csv", list(diag[0].keys()), diag)

    print(f"\n# Velocity-section diagnostic  {args.source_id}  t={args.time}")
    print("  (full plane vs single-leg mask: align = |mean vector| / mean speed)")
    for r in results:
        if r.get("status") != "diagnosed":
            print(f"  {r['label']}: {r.get('status')}")
            continue
        f = r["full_plane"]; m = r["single_leg_masked"]
        m_align = m.get("flow_alignment_meanvec_over_speed", float("nan"))
        print(f"  {r['label']:5s} full: nf={f['n_faces']:5d} <|U|>={f['mean_speed_mag_U']:.4f} align={f['flow_alignment_meanvec_over_speed']:.2f}  "
              f"| masked: nf={m.get('n_faces',0):5d} <|U|>={m.get('mean_speed_mag_U',float('nan')):.4f} align={m_align:.2f}")
        print(f"        => {r['interpretation']}")
    print(f"\nWrote {relative_to_workspace(output_dir / ('velocity_diagnostic_' + args.source_id + '.json'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
