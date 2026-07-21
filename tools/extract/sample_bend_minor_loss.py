#!/usr/bin/env python3
r"""Bend / junction / connector minor-loss K factors from the CFD (T7).

WHY (master TODO 2026-07-01, motivated by the T1b loop-closure):
-----------------------------------------------------------------
The loop-closure check (T1b) showed the straight legs dissipate only ~57-70% of
the buoyancy driving head; the remaining ~30-43% (~12-19 Pa) is lost across the
bends, junctions, and the test-section connector. Those are MINOR LOSSES (K
factors), not friction factors -- a first-order part of the loop resistance that
the 1D model must carry explicitly.

METHOD
------
Each feature in the profile `feature_budgets` (4 corners + the test-section
connector/expansion-contraction) is bounded by two non-conformal-couple interface
patches (`start_patch`, `end_patch`). We dump each patch's face values of
(U, p_rgh, rho) with a raw `surfaces` FO (type patch) -- the same mechanism the
geometry/section tools use -- and compute the area-mean total (stagnation)
pressure on each face:

    P0 = <p_rgh> + 1/2 <rho> |<U>|^2            [Pa]

The minor loss across the feature is the drop in total pressure in the flow
direction; K references it to the dynamic head:

    K = |P0_in - P0_out| / (1/2 rho_ref u_ref^2)

For a bend (equal bore) u_ref is the mean of the two faces. For the
expansion/contraction connector, K is referenced to the HIGHER dynamic head
(smaller bore) and that choice is recorded.

CONFIDENCE / LIMITS
-------------------
  * Buoyancy over the feature: p_rgh removes only the REFERENCE-density
    hydrostatic, so a feature spanning an elevation change with rho != rho_ref
    carries a small residual buoyancy term (gh*Delta rho). Features are short, so
    this is O(a few percent of a Pa); reported dz so the reader can judge.
  * Straight friction over the (short) feature length is neglected (the feature
    is dominated by the turning/area-change loss); documented.
  * ncc interface patches can have <1 coverage (patchToPatch); area-mean of face
    values is robust to that. Coarse mesh (GCI pending, T6).
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
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    relative_to_workspace,
)
from tools.case_analysis_profiles import get_case_analysis_profile  # noqa: E402

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-07-01_claude_bend_minor_loss"
FO_NAME = "bendMinorLossPatches"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case-dir", required=True)
    p.add_argument("--time", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--skip-run", action="store_true",
                   help="Reuse existing patch dumps (skip foamPostProcess).")
    p.add_argument("--of-env-script", default="tools/ofenv/of13_env.sh")
    return p.parse_args()


def features(profile: Any) -> dict[str, dict[str, Any]]:
    """Corner / connector features with both interface patches present."""
    out: dict[str, dict[str, Any]] = {}
    for name, defn in profile.feature_budgets.items():
        if not isinstance(defn, dict):
            continue
        sp, ep = defn.get("start_patch"), defn.get("end_patch")
        if sp and ep:
            out[name] = defn
    return out


def write_controldict(case_dir: Path, patches: list[str]) -> None:
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
        "    fields          (U p_rgh rho);",
        "    surfaces (",
    ]
    for patch in patches:
        lines += [f"      {patch} {{", "        type        patch;",
                  f"        patches     ({patch});", "      }"]
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


def patch_face_state(case_dir: Path, patch: str) -> dict[str, Any] | None:
    """Area-mean p_rgh, rho, mean-U vector, total pressure, mean position for a patch.

    Raw patch surface columns: x y z Ux Uy Uz p_rgh rho.
    """
    xy = find_patch_xy(case_dir, patch)
    if xy is None:
        return None
    try:
        data = np.loadtxt(xy)
    except Exception:
        return None
    if data.size == 0:
        return None
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.shape[1] < 8:
        return None
    pos = data[:, :3]
    U = data[:, 3:6]
    p_rgh = data[:, 6]
    rho = data[:, 7]
    mean_U = U.mean(axis=0)
    u_mag = float(np.linalg.norm(mean_U))
    rho_m = float(rho.mean())
    p_m = float(p_rgh.mean())
    y_m = float(pos[:, 1].mean())
    q_dyn = 0.5 * rho_m * u_mag * u_mag
    return {
        "patch": patch, "n_faces": int(data.shape[0]),
        "p_rgh_pa": p_m, "rho_kg_m3": rho_m, "u_bulk_m_s": u_mag,
        "dynamic_head_pa": q_dyn, "y_mean_m": y_m,
    }


def minor_loss_for_feature(name: str, defn: dict[str, Any], case_dir: Path) -> dict[str, Any]:
    sp, ep = defn["start_patch"], defn["end_patch"]
    a = patch_face_state(case_dir, sp)
    b = patch_face_state(case_dir, ep)
    rec: dict[str, Any] = {
        "feature": name, "kind": defn.get("kind", ""),
        "start_patch": sp, "end_patch": ep,
        "adjacent_major_spans": "+".join(defn.get("adjacent_major_spans", []) or []),
    }
    if a is None or b is None:
        rec["status"] = "missing_patch_output"
        return rec
    rec.update(compute_minor_loss(a, b, defn.get("kind", "")))
    return rec


# Guard: features in the upcomer recirculation zone have near-zero mean face
# velocity, so a dynamic-head-referenced K is ill-defined (report the loss only).
Q_MIN_PA = 1e-3


def compute_minor_loss(a: dict[str, Any], b: dict[str, Any], kind: str) -> dict[str, Any]:
    """Dissipative minor loss + K from two interface-patch states (pure/testable).

    loss = -(Delta p_rgh + gh*Delta rho + Delta q_dyn): the drop in mechanical head
    with the REVERSIBLE buoyancy source gh*Delta rho subtracted (same decomposition
    as the T1b momentum budget) so the recoverable elevation/hydrostatic head is
    removed and only dissipation remains. gh = g.x = -9.81*y at feature-mean y.
    K references the loss to the dynamic head (throat-max for area changes).
    """
    dp_rgh = b["p_rgh_pa"] - a["p_rgh_pa"]
    drho = b["rho_kg_m3"] - a["rho_kg_m3"]
    dq = b["dynamic_head_pa"] - a["dynamic_head_pa"]
    gh_mean = -9.81 * 0.5 * (a["y_mean_m"] + b["y_mean_m"])
    buoy = gh_mean * drho
    loss = -(dp_rgh + buoy + dq)
    q_ref = max(a["dynamic_head_pa"], b["dynamic_head_pa"]) if kind == "connector_expansion_contraction" \
        else 0.5 * (a["dynamic_head_pa"] + b["dynamic_head_pa"])
    K = abs(loss) / q_ref if q_ref > Q_MIN_PA else float("nan")
    status = "computed" if q_ref > Q_MIN_PA else "K_undefined_reference_velocity_near_zero_recirc_zone"
    return {
        "status": status,
        "p_rgh_start_pa": a["p_rgh_pa"], "p_rgh_end_pa": b["p_rgh_pa"],
        "delta_p_rgh_pa": dp_rgh, "buoyancy_term_pa": buoy, "delta_q_dyn_pa": dq,
        "abs_loss_pa": abs(loss), "signed_loss_pa": loss,
        "q_ref_pa": q_ref, "q_ref_basis": ("throat_max" if kind == "connector_expansion_contraction" else "mean"),
        "K_minor_loss": K,
        "u_start_m_s": a["u_bulk_m_s"], "u_end_m_s": b["u_bulk_m_s"],
        "rho_ref_kg_m3": 0.5 * (a["rho_kg_m3"] + b["rho_kg_m3"]),
        "dz_across_feature_m": b["y_mean_m"] - a["y_mean_m"],
        "n_faces_start": a["n_faces"], "n_faces_end": b["n_faces"],
    }


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).resolve()
    profile = get_case_analysis_profile(args.source_id)
    feats = features(profile)
    all_patches = sorted({defn["start_patch"] for defn in feats.values()} |
                         {defn["end_patch"] for defn in feats.values()})
    out_dir = Path(args.output_dir)
    ensure_dir(out_dir)

    if not args.skip_run:
        write_controldict(case_dir, all_patches)
        log = out_dir / f"foampostprocess_{args.source_id}.log"
        print(f"Running foamPostProcess (feature patch dump)... {relative_to_workspace(log)}")
        rc = run_foampostprocess(case_dir, args.time, log, args.of_env_script)
        if rc != 0:
            print(f"WARNING: foamPostProcess rc={rc}; parsing whatever exists.")

    rows = [minor_loss_for_feature(name, defn, case_dir) for name, defn in feats.items()]
    payload = {
        "tool": "sample_bend_minor_loss.py",
        "generated_at": iso_timestamp(),
        "source_id": args.source_id,
        "case_dir": str(relative_to_workspace(case_dir)),
        "time": args.time,
        "method": ("K = |Delta P0| / q_ref across each feature's two interface patches; "
                   "P0 = <p_rgh> + 1/2 <rho>|<U>|^2; q_ref = throat-max for area-change "
                   "features, mean otherwise. Straight friction over the (short) feature "
                   "neglected; residual buoyancy small (see dz)."),
        "features": rows,
    }
    json_dump(out_dir / f"bend_minor_loss_{args.source_id}.json", payload)
    good = [r for r in rows if r.get("status") == "computed"]
    if good:
        keys = sorted({k for r in good for k in r.keys()})
        csv_dump(out_dir / f"bend_minor_loss_{args.source_id}.csv", keys,
                 [{k: r.get(k, "") for k in keys} for r in good])

    print(f"\n# Bend / junction minor-loss K  {args.source_id}  t={args.time}")
    print(f"{'feature':22s} {'kind':30s} {'loss[Pa]':>9s} {'q_ref':>8s} {'K':>7s} {'dz[m]':>7s}")
    for r in rows:
        if r.get("status") == "computed":
            print(f"{r['feature']:22s} {r['kind']:30s} {r['abs_loss_pa']:9.3f} "
                  f"{r['q_ref_pa']:8.4f} {r['K_minor_loss']:7.2f} {r['dz_across_feature_m']:7.3f}")
        else:
            print(f"{r['feature']:22s} {r.get('status')}")
    print(f"\nWrote {relative_to_workspace(out_dir / ('bend_minor_loss_' + args.source_id + '.json'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
