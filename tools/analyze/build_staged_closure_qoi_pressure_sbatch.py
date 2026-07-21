#!/usr/bin/env python3
"""Prepare and harvest AGENT-440 staged closure-QOI/raw-pressure sbatch job."""

from __future__ import annotations

import argparse
import csv
import json
import math
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-440"
DATE = "2026-07-15"
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch"
TMP = ROOT / "tmp/2026-07-15_staged_closure_qoi_pressure_sbatch"
MESH_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
OF_ENV = ROOT / "tools/ofenv/of13_env.sh"
AG409 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess"
AG421 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification"
AG425 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock"

RAW_CASES = [
    {
        "case_id": "salt_2",
        "case_key": "salt2_mainline",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "time_s": "7915",
        "source_case": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    },
    {
        "case_id": "salt_3",
        "case_key": "salt3_mainline",
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "time_s": "7618",
        "source_case": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    },
    {
        "case_id": "salt_4",
        "case_key": "salt4_mainline",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "time_s": "10000",
        "source_case": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
    },
]

SURFACE_FUNCTION_CANDIDATES = [
    "agent440RawPressureSurfaces",
    "agent440ClosurePressureSurfaces",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> int:
    data = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({field: row.get(field, "") for field in fields})
    return len(data)


def as_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any) -> str:
    number = as_float(value)
    return "" if number is None else f"{number:.10g}"


def station_normal(source_id: str, label: str) -> tuple[float, float, float]:
    stations = read_json(MESH_ROOT / source_id / "mesh_stations.json").get("stations", [])
    for row in stations:
        if row.get("label") == label:
            return float(row["nx"]), float(row["ny"]), float(row["nz"])
    raise KeyError(f"missing station {source_id}:{label}")


def preflight_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in RAW_CASES:
        source = ROOT / case["source_case"]
        proc_time = source / "processors64" / case["time_s"]
        mesh = MESH_ROOT / case["source_id"] / "mesh_stations.json"
        ok = source.exists() and proc_time.exists() and mesh.exists() and OF_ENV.exists()
        rows.append(
            {
                **case,
                "source_case_exists": str(source.exists()).lower(),
                "processor_time_exists": str(proc_time.exists()).lower(),
                "mesh_stations_exists": str(mesh.exists()).lower(),
                "of13_env_exists": str(OF_ENV.exists()).lower(),
                "preflight_status": "pass" if ok else "fail",
                "staged_case_dir": rel(TMP / "raw_pressure" / case["case_key"]),
                "native_solver_outputs_mutated": "false",
            }
        )
    return rows


def control_dict_text() -> str:
    return """FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }
application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;
writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;
writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;
functions {
  agent440RawPressureSurfaces {
    type            surfaces;
    libs            ("libsampling.so");
    writeControl    writeTime;
    surfaceFormat   raw;
    interpolate     false;
    interpolationScheme cell;
    fields          (U p p_rgh rho);
    surfaces (
      plane_left_lower_leg__s00 {
        type cuttingPlane; planeType pointAndNormal;
        pointAndNormalDict { point (1.85606127216e-13 0.0486021944432 0); normal (-1.19827685174e-12 1 0); }
      }
      plane_left_upper_leg__s04 {
        type cuttingPlane; planeType pointAndNormal;
        pointAndNormalDict { point (-1.04166497973e-13 0.895903471523 0); normal (6.93310699107e-14 1 0); }
      }
    );
  }
}
"""


def write_control_dict(case_dir: Path) -> None:
    system = case_dir / "system"
    system.mkdir(parents=True, exist_ok=True)
    (system / "controlDict").write_text(control_dict_text(), encoding="utf-8")


def write_scripts() -> list[dict[str, Any]]:
    scripts = OUT / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    logs = OUT / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    case_lines = "\n".join(
        f'{case["case_key"]}|{case["source_case"]}|{case["time_s"]}' for case in RAW_CASES
    )
    runner = scripts / "run_staged_closure_qoi_raw_pressure.sh"
    runner.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
ROOT={ROOT}
OUT="$ROOT/{rel(OUT)}"
TMP="$ROOT/{rel(TMP)}"
OF_ENV="$ROOT/{rel(OF_ENV)}"
LOG_DIR="$OUT/logs"
mkdir -p "$LOG_DIR" "$TMP/raw_pressure"
cd "$ROOT"
run_one() {{
  local case_key="$1" source_case="$2" time_s="$3"
  local source_abs="$ROOT/$source_case"
  local case_dir="$TMP/raw_pressure/$case_key"
  [[ -d "$source_abs/processors64/$time_s" ]] || {{ echo "missing $source_abs/processors64/$time_s" >&2; exit 1; }}
  mkdir -p "$case_dir"
  for name in constant system 0; do
    [[ -e "$source_abs/$name" ]] || {{ echo "missing $source_abs/$name" >&2; exit 1; }}
    [[ -e "$case_dir/$name" ]] || cp -a "$source_abs/$name" "$case_dir/$name"
  done
  ln -sfn "$source_abs/processors64" "$case_dir/processors64"
  if [[ -e "$case_dir/system/functions" || -L "$case_dir/system/functions" ]]; then
    mv "$case_dir/system/functions" "$case_dir/system/functions.agent440_disabled.$(date +%s)"
  fi
  python3.11 tools/analyze/build_staged_closure_qoi_pressure_sbatch.py --write-control "$case_dir"
  if [[ ! -d "$case_dir/$time_s" ]]; then
    timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$case_dir' -time '$time_s' -fields '(U p p_rgh rho)'" > "$LOG_DIR/reconstruct_${{case_key}}.log" 2>&1
  fi
  timeout 60m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && foamPostProcess -case '$case_dir' -time '$time_s'" > "$LOG_DIR/raw_pressure_${{case_key}}.log" 2>&1
}}
while IFS='|' read -r case_key source_case time_s; do
  [[ -n "$case_key" ]] || continue
  run_one "$case_key" "$source_case" "$time_s"
done <<'CASES'
{case_lines}
CASES
python3.11 tools/analyze/build_staged_closure_qoi_pressure_sbatch.py --harvest --record-job-id "${{SLURM_JOB_ID:-local}}"
""",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)

    sbatch = scripts / "submit_staged_closure_qoi_raw_pressure.sbatch"
    sbatch.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J closure_qoi_p
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 04:00:00
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -o {rel(OUT / 'logs' / 'closure_qoi_pressure-%j.out')}
#SBATCH -e {rel(OUT / 'logs' / 'closure_qoi_pressure-%j.err')}

set -euo pipefail
cd {ROOT}
bash {rel(runner)}
""",
        encoding="utf-8",
    )
    sbatch.chmod(sbatch.stat().st_mode | stat.S_IXUSR)
    return [
        {
            "script_id": "runner",
            "path": rel(runner),
            "purpose": "stage copies and run reconstructPar/foamPostProcess raw pressure surfaces",
        },
        {
            "script_id": "sbatch",
            "path": rel(sbatch),
            "job_name": "closure_qoi_p",
            "partition": "NuclearEnergy",
            "time_limit": "04:00:00",
        },
    ]


def parse_plane(path: Path, normal: tuple[float, float, float]) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": rel(path)}
    count = reverse = 0
    sum_prgh = sum_p = sum_un = 0.0
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.split()
            if not parts or line.startswith("#") or len(parts) < 8:
                continue
            ux, uy, uz = float(parts[3]), float(parts[4]), float(parts[5])
            p = float(parts[6])
            prgh = float(parts[7])
            un = ux * normal[0] + uy * normal[1] + uz * normal[2]
            count += 1
            reverse += int(un < 0.0)
            sum_un += un
            sum_p += p
            sum_prgh += prgh
    if count == 0:
        return {"status": "empty", "path": rel(path)}
    return {
        "status": "parsed",
        "path": rel(path),
        "face_count": count,
        "mean_p_Pa": sum_p / count,
        "mean_p_rgh_Pa": sum_prgh / count,
        "mean_normal_velocity_m_s": sum_un / count,
        "reverse_area_fraction_equal_face_proxy": reverse / count,
    }


def harvest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lower_label = "left_lower_leg__s00"
    upper_label = "left_upper_leg__s04"
    for case in RAW_CASES:
        post_root = TMP / "raw_pressure" / case["case_key"] / "postProcessing"
        base = post_root / SURFACE_FUNCTION_CANDIDATES[0] / case["time_s"]
        surface_function = SURFACE_FUNCTION_CANDIDATES[0]
        for candidate in SURFACE_FUNCTION_CANDIDATES:
            candidate_base = post_root / candidate / case["time_s"]
            if (candidate_base / f"plane_{lower_label}.xy").exists() or (candidate_base / f"plane_{upper_label}.xy").exists():
                base = candidate_base
                surface_function = candidate
                break
        lower = parse_plane(base / f"plane_{lower_label}.xy", station_normal(case["source_id"], lower_label))
        upper = parse_plane(base / f"plane_{upper_label}.xy", station_normal(case["source_id"], upper_label))
        parsed = lower["status"] == "parsed" and upper["status"] == "parsed"
        lower_prgh = as_float(lower.get("mean_p_rgh_Pa"))
        upper_prgh = as_float(upper.get("mean_p_rgh_Pa"))
        lower_p = as_float(lower.get("mean_p_Pa"))
        upper_p = as_float(upper.get("mean_p_Pa"))
        rows.append(
            {
                **case,
                "mesh_level": "coarse",
                "surface_function": surface_function,
                "tap_lower_label": lower_label,
                "tap_upper_label": upper_label,
                "lower_mean_p_Pa": fmt(lower_p),
                "upper_mean_p_Pa": fmt(upper_p),
                "delta_p_upper_minus_lower_Pa": fmt((upper_p or 0.0) - (lower_p or 0.0)) if parsed else "",
                "lower_mean_p_rgh_Pa": fmt(lower_prgh),
                "upper_mean_p_rgh_Pa": fmt(upper_prgh),
                "delta_p_rgh_upper_minus_lower_Pa": fmt((upper_prgh or 0.0) - (lower_prgh or 0.0)) if parsed else "",
                "lower_reverse_area_fraction_proxy": fmt(lower.get("reverse_area_fraction_equal_face_proxy")),
                "upper_reverse_area_fraction_proxy": fmt(upper.get("reverse_area_fraction_equal_face_proxy")),
                "lower_face_count": lower.get("face_count", ""),
                "upper_face_count": upper.get("face_count", ""),
                "lower_plane_file": lower.get("path", ""),
                "upper_plane_file": upper.get("path", ""),
                "admission_status": "diagnostic_staged_copy_raw_pressure_not_fit_admitted" if parsed else "blocked_missing_sbatch_output",
                "fit_eligible": "no",
                "blockers": "coarse_only_no_mesh_gci;tap_orientation_and_straight_loss_subtraction_pending;recirculation_policy_pending",
                "native_solver_outputs_mutated": "false",
            }
        )
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        f"""# Staged Closure-QOI / Raw-Pressure sbatch

Task: {TASK}
Generated: {DATE}

This package stages nominal Salt2/Salt3/Salt4 raw-pressure two-tap
postprocessing onto copied/symlinked scratch cases and submits one compute-node
sbatch job. Native CFD solver outputs remain read-only.

## Current Status

- Preflight rows: `{summary['preflight_rows']}`
- Preflight failures: `{summary['preflight_failures']}`
- submitted sbatch script: `{summary.get('submitted_sbatch_script', 'scripts/submit_staged_closure_qoi_raw_pressure.sbatch')}`
- prepared fallback sbatch script: `scripts/submit_staged_closure_qoi_raw_pressure.sbatch`
- submitted job id: `{summary.get('submitted_job_id', '')}`
- submitted job name: `{summary.get('submitted_job_name', '')}`
- latest checked state: `{summary.get('submitted_job_state', '')}`
- harvested rows: `{summary.get('harvested_rows', 0)}`

Outputs are diagnostic until admission gates handle pressure definition,
orientation, straight-loss subtraction, mesh/GCI, and recirculation policy.
""",
        encoding="utf-8",
    )


def build_package() -> dict[str, Any]:
    rows = preflight_rows()
    scripts = write_scripts()
    failures = [row for row in rows if row["preflight_status"] != "pass"]
    submitted = read_json(OUT / "submitted_job.json")
    write_csv(
        OUT / "raw_pressure_preflight.csv",
        rows,
        [
            "case_id",
            "case_key",
            "source_id",
            "time_s",
            "source_case",
            "source_case_exists",
            "processor_time_exists",
            "mesh_stations_exists",
            "of13_env_exists",
            "preflight_status",
            "staged_case_dir",
            "native_solver_outputs_mutated",
        ],
    )
    write_csv(OUT / "sbatch_scripts.csv", scripts, ["script_id", "path", "purpose", "job_name", "partition", "time_limit"])
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"path": rel(AG409 / "README.md"), "role": "completed diagnostic precedent", "exists": str((AG409 / "README.md").exists()).lower()},
            {"path": rel(AG421 / "README.md"), "role": "hydraulic chain verification", "exists": str((AG421 / "README.md").exists()).lower()},
            {"path": rel(AG425 / "README.md"), "role": "F6/internal-Nu admission review", "exists": str((AG425 / "README.md").exists()).lower()},
            {"path": rel(OF_ENV), "role": "OpenFOAM 13 environment", "exists": str(OF_ENV.exists()).lower()},
        ],
        ["path", "role", "exists"],
    )
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "preflight_rows": len(rows),
        "preflight_failures": len(failures),
        "sbatch_scripts": len(scripts),
        "submitted_job_id": submitted.get("job_id", ""),
        "submitted_job_name": submitted.get("job_name", ""),
        "submitted_job_state": submitted.get("initial_squeue_state", ""),
        "harvested_rows": 0,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def harvest(record_job_id: str = "") -> dict[str, Any]:
    rows = harvest_rows()
    write_csv(
        OUT / "raw_pressure_two_tap_harvest.csv",
        rows,
        [
            "case_id",
            "case_key",
            "source_id",
            "time_s",
            "mesh_level",
            "surface_function",
            "tap_lower_label",
            "tap_upper_label",
            "lower_mean_p_Pa",
            "upper_mean_p_Pa",
            "delta_p_upper_minus_lower_Pa",
            "lower_mean_p_rgh_Pa",
            "upper_mean_p_rgh_Pa",
            "delta_p_rgh_upper_minus_lower_Pa",
            "lower_reverse_area_fraction_proxy",
            "upper_reverse_area_fraction_proxy",
            "lower_face_count",
            "upper_face_count",
            "lower_plane_file",
            "upper_plane_file",
            "admission_status",
            "fit_eligible",
            "blockers",
            "native_solver_outputs_mutated",
        ],
    )
    summary = read_json(OUT / "summary.json") or build_package()
    summary.update({"harvested_rows": len(rows), "last_harvest_job_id": record_job_id, "last_harvest_at": utc_now()})
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def record_submission(job_id: str) -> dict[str, Any]:
    summary = read_json(OUT / "summary.json") or build_package()
    summary.update({"submitted_job_id": job_id, "submitted_at": utc_now()})
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_csv(
        OUT / "sbatch_submission_status.csv",
        [{"job_id": job_id, "job_name": "closure_qoi_p", "state_at_submission": "SUBMITTED", "submitted_at": summary["submitted_at"]}],
        ["job_id", "job_name", "state_at_submission", "submitted_at"],
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-control", type=Path)
    parser.add_argument("--harvest", action="store_true")
    parser.add_argument("--record-job-id", default="")
    parser.add_argument("--record-submission", default="")
    args = parser.parse_args()
    if args.write_control:
        write_control_dict(args.write_control)
    elif args.harvest:
        harvest(args.record_job_id)
    elif args.record_submission:
        record_submission(args.record_submission)
    else:
        build_package()


if __name__ == "__main__":
    main()
