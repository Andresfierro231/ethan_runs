#!/usr/bin/env python3
"""Prepare and harvest AGENT-447 expanded Salt pressure-ladder sbatch job."""

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
TASK = "AGENT-447"
DATE = "2026-07-15"
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch"
TMP = ROOT / "tmp/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch"
MESH_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
OF_ENV = ROOT / "tools/ofenv/of13_env.sh"

CASES = [
    {
        "case_id": "salt_1",
        "case_key": "salt1_nominal",
        "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "time_s": "7884",
        "source_case": "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "split_role": "training",
        "time_window_s": "7284-7884",
        "admission_caveat": "Salt1 training candidate; pressure ladder diagnostic until mesh/GCI and pressure gates admit",
    },
    {
        "case_id": "salt_1",
        "case_key": "salt1_lo10q",
        "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "time_s": "8016",
        "source_case": "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "split_role": "training_perturbation",
        "time_window_s": "7416-8016",
        "admission_caveat": "Salt1 -10%Q training candidate; pressure ladder diagnostic until mesh/GCI and pressure gates admit",
    },
    {
        "case_id": "salt_1",
        "case_key": "salt1_hi10q",
        "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "time_s": "5587",
        "source_case": "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "split_role": "training_perturbation",
        "time_window_s": "4987-5587",
        "admission_caveat": "Salt1 +10%Q training candidate with documented conflict-resolution caveat; pressure ladder diagnostic until gates admit",
    },
    {
        "case_id": "salt_2",
        "case_key": "salt2_lo5q",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "time_s": "10275",
        "source_case": "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_lo5q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
        "split_role": "holdout_perturbation",
        "time_window_s": "9975-10275",
        "admission_caveat": "Salt2 -5%Q holdout only; do not use for training/model selection",
    },
    {
        "case_id": "salt_2",
        "case_key": "salt2_hi5q",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "time_s": "9780",
        "source_case": "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_hi5q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
        "split_role": "holdout_perturbation",
        "time_window_s": "9480-9780",
        "admission_caveat": "Salt2 +5%Q holdout only; do not use for training/model selection",
    },
    {
        "case_id": "salt_4",
        "case_key": "salt4_lo5q",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "time_s": "11695",
        "source_case": "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_lo5q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "split_role": "training_perturbation",
        "time_window_s": "11395-11695",
        "admission_caveat": "Salt4 -5%Q training perturbation; pressure ladder diagnostic until gates admit",
    },
    {
        "case_id": "salt_4",
        "case_key": "salt4_hi5q",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "time_s": "11399",
        "source_case": "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_hi5q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "split_role": "training_perturbation",
        "time_window_s": "11099-11399",
        "admission_caveat": "Salt4 +5%Q training perturbation; pressure ladder diagnostic until gates admit",
    },
    {
        "case_id": "val_salt_2",
        "case_key": "val_salt2",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "time_s": "8602",
        "source_case": "jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation",
        "split_role": "external_validation",
        "time_window_s": "8302-8602",
        "admission_caveat": "external validation coarse case; pressure ladder diagnostic until gates admit",
    },
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


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str] | None = None) -> int:
    data = list(rows)
    if fields is None:
        fields = list(data[0].keys()) if data else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({field: row.get(field, "") for field in fields})
    return len(data)


def stations(source_id: str) -> list[dict[str, Any]]:
    return read_json(MESH_ROOT / source_id / "mesh_stations.json").get("stations", [])


def fmt(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{number:.10g}" if math.isfinite(number) else ""


def plane_file(case: dict[str, str], label: str) -> Path:
    return TMP / "pressure_ladder" / case["case_key"] / "postProcessing/agent447PressureLadderSurfaces" / case["time_s"] / f"plane_{label}.xy"


def parse_plane(path: Path, normal: tuple[float, float, float]) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": rel(path)}
    count = reverse = 0
    sum_un = sum_p = sum_prgh = sum_rho = 0.0
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            ux, uy, uz = float(parts[3]), float(parts[4]), float(parts[5])
            p, prgh = float(parts[6]), float(parts[7])
            rho = float(parts[8]) if len(parts) >= 9 else float("nan")
            un = ux * normal[0] + uy * normal[1] + uz * normal[2]
            count += 1
            reverse += int(un < 0.0)
            sum_un += un
            sum_p += p
            sum_prgh += prgh
            if math.isfinite(rho):
                sum_rho += rho
    if count == 0:
        return {"status": "empty", "path": rel(path)}
    return {
        "status": "parsed_area_proxy",
        "path": rel(path),
        "face_count": count,
        "mean_un_m_s": sum_un / count,
        "mean_p_Pa": sum_p / count,
        "mean_p_rgh_Pa": sum_prgh / count,
        "mean_rho_kg_m3": sum_rho / count if sum_rho else "",
        "reverse_area_fraction_proxy": reverse / count,
    }


def preflight_rows() -> list[dict[str, Any]]:
    rows = []
    for case in CASES:
        source = ROOT / case["source_case"]
        mesh = MESH_ROOT / case["source_id"] / "mesh_stations.json"
        rows.append({
            **case,
            "source_case_exists": str(source.exists()).lower(),
            "processor_time_exists": str((source / "processors64" / case["time_s"]).exists()).lower(),
            "mesh_stations_exists": str(mesh.exists()).lower(),
            "station_count": len(stations(case["source_id"])) if mesh.exists() else 0,
            "of13_env_exists": str(OF_ENV.exists()).lower(),
            "preflight_status": "pass" if source.exists() and (source / "processors64" / case["time_s"]).exists() and mesh.exists() and OF_ENV.exists() else "fail",
            "staged_case_dir": rel(TMP / "pressure_ladder" / case["case_key"]),
            "native_solver_outputs_mutated": "false",
        })
    return rows


def control_dict_text(source_id: str) -> str:
    surface_blocks = []
    for row in stations(source_id):
        label = row["label"]
        surface_blocks.append(
            f"""      plane_{label} {{
        type cuttingPlane; planeType pointAndNormal;
        pointAndNormalDict {{ point ({float(row['x']):.12g} {float(row['y']):.12g} {float(row['z']):.12g}); normal ({float(row['nx']):.12g} {float(row['ny']):.12g} {float(row['nz']):.12g}); }}
      }}"""
        )
    surfaces = "\n".join(surface_blocks)
    return f"""FoamFile {{ version 2.0; format ascii; class dictionary; object controlDict; }}
application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;
writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;
writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;
functions {{
  agent447PressureLadderSurfaces {{
    type            surfaces;
    libs            ("libsampling.so");
    writeControl    writeTime;
    surfaceFormat   raw;
    interpolate     false;
    interpolationScheme cell;
    fields          (U p p_rgh rho);
    surfaces (
{surfaces}
    );
  }}
}}
"""


def write_control(case_dir: Path, source_id: str) -> None:
    system = case_dir / "system"
    system.mkdir(parents=True, exist_ok=True)
    (system / "controlDict").write_text(control_dict_text(source_id), encoding="utf-8")


def write_scripts() -> list[dict[str, Any]]:
    scripts = OUT / "scripts"
    logs = OUT / "logs"
    scripts.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    case_lines = "\n".join(f"{c['case_key']}|{c['source_case']}|{c['time_s']}|{c['source_id']}" for c in CASES)
    runner = scripts / "run_expanded_pressure_ladder.sh"
    runner.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
ROOT={ROOT}
OUT="$ROOT/{rel(OUT)}"
TMP="$ROOT/{rel(TMP)}"
OF_ENV="$ROOT/{rel(OF_ENV)}"
LOG_DIR="$OUT/logs"
PRECHECK_ONLY=0
[[ "${{1:-}}" == "--preflight-only" ]] && PRECHECK_ONLY=1
mkdir -p "$LOG_DIR" "$TMP/pressure_ladder"
cd "$ROOT"
log() {{ printf '[%s] %s\\n' "$(date --iso-8601=seconds)" "$*" >&2; }}
run_one() {{
  local case_key="$1" source_case="$2" time_s="$3" source_id="$4"
  local source_abs="$ROOT/$source_case"
  local case_dir="$TMP/pressure_ladder/$case_key"
  [[ -d "$source_abs/processors64/$time_s" ]] || {{ log "missing $source_abs/processors64/$time_s"; exit 1; }}
  [[ -f "$OF_ENV" ]] || {{ log "missing $OF_ENV"; exit 1; }}
  for name in constant system 0; do [[ -e "$source_abs/$name" ]] || {{ log "missing $source_abs/$name"; exit 1; }}; done
  log "preflight ok: $case_key time $time_s"
  [[ "$PRECHECK_ONLY" == "0" ]] || return 0
  mkdir -p "$case_dir"
  for name in constant system 0; do [[ -e "$case_dir/$name" ]] || cp -a "$source_abs/$name" "$case_dir/$name"; done
  ln -sfn "$source_abs/processors64" "$case_dir/processors64"
  if [[ -e "$case_dir/system/functions" || -L "$case_dir/system/functions" ]]; then
    mv "$case_dir/system/functions" "$case_dir/system/functions.agent447_disabled.$(date +%s)"
  fi
  python3.11 tools/analyze/build_expanded_salt_pressure_ladder_8pm_sbatch.py --write-control "$case_dir" --source-id "$source_id"
  if [[ ! -d "$case_dir/$time_s" ]]; then
    timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$case_dir' -time '$time_s' -fields '(U p p_rgh rho)'" > "$LOG_DIR/reconstruct_${{case_key}}.log" 2>&1
  fi
  timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && foamPostProcess -case '$case_dir' -time '$time_s'" > "$LOG_DIR/pressure_ladder_${{case_key}}.log" 2>&1
}}
while IFS='|' read -r case_key source_case time_s source_id; do
  [[ -n "$case_key" ]] || continue
  run_one "$case_key" "$source_case" "$time_s" "$source_id"
done <<'CASES'
{case_lines}
CASES
if [[ "$PRECHECK_ONLY" == "1" ]]; then
  log "AGENT-447 expanded Salt pressure ladder preflight-only complete"
  exit 0
fi
python3.11 tools/analyze/build_expanded_salt_pressure_ladder_8pm_sbatch.py --harvest --record-job-id "${{SLURM_JOB_ID:-local}}"
log "AGENT-447 expanded Salt pressure ladder runner complete"
""",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    sbatch = scripts / "submit_expanded_pressure_ladder_8pm.sbatch"
    sbatch.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J press_lad2
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 14:00:00
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH --begin=2026-07-15T20:00:00
#SBATCH -o {OUT}/logs/slurm-%j.out
#SBATCH -e {OUT}/logs/slurm-%j.err

set -euo pipefail
cd {ROOT}
{rel(runner)}
""",
        encoding="utf-8",
    )
    sbatch.chmod(sbatch.stat().st_mode | stat.S_IXUSR)
    return [
        {"script_id": "runner", "path": rel(runner), "purpose": "preflight/stage/reconstruct/sample/harvest all expanded Salt station planes"},
        {"script_id": "sbatch", "path": rel(sbatch), "purpose": "submit expanded Salt pressure ladder extraction to Slurm beginning at 2026-07-15 20:00 CDT"},
    ]


def harvest_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    station_rows: list[dict[str, Any]] = []
    adjacent_rows: list[dict[str, Any]] = []
    for case in CASES:
        parsed_by_label: dict[str, dict[str, Any]] = {}
        station_meta = stations(case["source_id"])
        for index, meta in enumerate(station_meta):
            label = meta["label"]
            parsed = parse_plane(plane_file(case, label), (float(meta["nx"]), float(meta["ny"]), float(meta["nz"])))
            parsed_by_label[label] = parsed
            station_rows.append({
                "case_id": case["case_id"],
                "case_key": case["case_key"],
                "split_role": case.get("split_role", ""),
                "time_window_s": case.get("time_window_s", ""),
                "admission_caveat": case.get("admission_caveat", ""),
                "source_id": case["source_id"],
                "time_s": case["time_s"],
                "station_index": index,
                "station_label": label,
                "branch": label.rsplit("__", 1)[0],
                "status": parsed["status"],
                "face_count": parsed.get("face_count", ""),
                "mean_p_Pa": fmt(parsed.get("mean_p_Pa")),
                "mean_p_rgh_Pa": fmt(parsed.get("mean_p_rgh_Pa")),
                "mean_un_m_s": fmt(parsed.get("mean_un_m_s")),
                "mean_rho_kg_m3": fmt(parsed.get("mean_rho_kg_m3")),
                "reverse_area_fraction_proxy": fmt(parsed.get("reverse_area_fraction_proxy")),
                "plane_file": parsed.get("path", ""),
                "admission_status": "diagnostic_station_pressure_ladder_not_fit_admitted" if parsed["status"] == "parsed_area_proxy" else "missing_or_failed_plane",
                "fit_eligible": "no",
                "blockers": "coarse_only_no_mesh_gci;orientation_straight_loss_recirc_admission_pending",
            })
        for left, right in zip(station_meta, station_meta[1:]):
            if left["label"].rsplit("__", 1)[0] != right["label"].rsplit("__", 1)[0]:
                continue
            a = parsed_by_label[left["label"]]
            b = parsed_by_label[right["label"]]
            ok = a["status"] == "parsed_area_proxy" and b["status"] == "parsed_area_proxy"
            adjacent_rows.append({
                "case_id": case["case_id"],
                "case_key": case["case_key"],
                "split_role": case.get("split_role", ""),
                "time_window_s": case.get("time_window_s", ""),
                "admission_caveat": case.get("admission_caveat", ""),
                "branch": left["label"].rsplit("__", 1)[0],
                "from_station": left["label"],
                "to_station": right["label"],
                "delta_p_to_minus_from_Pa": fmt(float(b["mean_p_Pa"]) - float(a["mean_p_Pa"])) if ok else "",
                "delta_p_rgh_to_minus_from_Pa": fmt(float(b["mean_p_rgh_Pa"]) - float(a["mean_p_rgh_Pa"])) if ok else "",
                "from_reverse_area_fraction_proxy": fmt(a.get("reverse_area_fraction_proxy")),
                "to_reverse_area_fraction_proxy": fmt(b.get("reverse_area_fraction_proxy")),
                "status": "diagnostic_adjacent_pressure_delta" if ok else "missing_or_failed_pair",
                "next_use": "orientation_and_straight_loss_subtraction_screen_only",
            })
    return station_rows, adjacent_rows


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        f"""# Expanded Salt Pressure-Ladder 8 PM sbatch

Task: AGENT-447
Generated: {DATE}

## Why This Exists

AGENT-445 already queued the nominal Salt2/Salt3/Salt4 pressure ladder. This
package expands the overnight postprocessing queue to the Salt1 training
candidate rows, Salt2 +/-5Q holdout rows, Salt4 +/-5Q training perturbation
rows, and the val_salt2 external-validation row. The goal is to make hydraulic
and closure-QOI pressure evidence available for training/validation studies
without reusing realized pressure information as a predictive-model input.

All rows here remain diagnostic until a later admission gate explicitly admits
pressure definition, mesh/GCI, branch orientation, straight-loss subtraction,
and recirculation masks.

## Included Cases

- `salt1_nominal`: Salt1 training candidate, terminal window `7284-7884`, sampled at `7884`.
- `salt1_lo10q`: Salt1 -10%Q training perturbation, terminal window `7416-8016`, sampled at `8016`.
- `salt1_hi10q`: Salt1 +10%Q training perturbation, terminal window `4987-5587`, sampled at `5587`; preserve documented conflict-resolution caveat.
- `salt2_lo5q`: Salt2 -5%Q holdout, terminal window `9975-10275`, sampled at `10275`; do not use for training/model selection.
- `salt2_hi5q`: Salt2 +5%Q holdout, terminal window `9480-9780`, sampled at `9780`; do not use for training/model selection.
- `salt4_lo5q`: Salt4 -5%Q training perturbation, terminal window `11395-11695`, sampled at `11695`.
- `salt4_hi5q`: Salt4 +5%Q training perturbation, terminal window `11099-11399`, sampled at `11399`.
- `val_salt2`: external validation coarse case, terminal window `8302-8602`, sampled at `8602`.

## Deliberate Non-Duplication

- Salt2/Salt3/Salt4 nominal pressure ladders are already covered by AGENT-445 job `{summary.get('related_agent445_job_id', '3297860')}`.
- Salt2/Salt4 +/-10Q remain in the corrected-Q chain and are not duplicated here.
- Legacy Salt4 `balq`/`hiins` and Salt3 low/high perturbations are not promoted into this job.

## Tomorrow Unlock Plan

1. Check job `{summary.get('submitted_job_id', '')}` with `sacct`.
2. If terminal, run `python3.11 tools/analyze/build_expanded_salt_pressure_ladder_8pm_sbatch.py --harvest --record-job-id {summary.get('submitted_job_id', '')}`.
3. Open `station_pressure_ladder.csv` and `adjacent_pressure_ladder.csv`.
4. Build an orientation table by branch using adjacent `p` and `p_rgh` trends.
5. Use branch-specific adjacent pairs to estimate straight/distributed pressure gradients before computing any local/component K.
6. Mask rows with material reverse-area fractions before any true `f_D` or `K` fit.
7. Keep all rows diagnostic until mesh/GCI, pressure definition, tap orientation, straight-loss subtraction, and recirculation gates explicitly admit them.

## Current Status

- Preflight rows: `{summary['preflight_rows']}`
- Preflight failures: `{summary['preflight_failures']}`
- Station planes targeted per case: `30`
- Submitted begin time: `2026-07-15T20:00:00`
- Submitted job id: `{summary.get('submitted_job_id', '')}`
- Latest submitted state: `{summary.get('submitted_job_state', '')}`
- Harvested station row slots: `{summary.get('harvested_station_rows', 0)}`
- Harvested parsed station rows: `{summary.get('harvested_station_parsed_rows', 0)}`
- Harvested adjacent row slots: `{summary.get('harvested_adjacent_rows', 0)}`
- Harvested parsed adjacent rows: `{summary.get('harvested_adjacent_parsed_rows', 0)}`

## Guardrails

Native CFD outputs are read-only. The sbatch job writes only under
`{rel(TMP)}` and this work-product package. Outputs are diagnostic until an
admission gate promotes them.
""",
        encoding="utf-8",
    )


def build_package() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    rows = preflight_rows()
    scripts = write_scripts()
    submitted = read_json(OUT / "submitted_job.json")
    write_csv(OUT / "pressure_ladder_preflight.csv", rows)
    write_csv(OUT / "scripts_manifest.csv", scripts)
    write_csv(
        OUT / "source_manifest.csv",
        [
            {
                "path": c["source_case"],
                "case_key": c["case_key"],
                "split_role": c.get("split_role", ""),
                "time_s": c["time_s"],
                "time_window_s": c.get("time_window_s", ""),
                "exists": str((ROOT / c["source_case"]).exists()).lower(),
            }
            for c in CASES
        ]
        + [{"path": rel(OF_ENV), "case_key": "OpenFOAM 13 env", "split_role": "runtime", "time_s": "", "time_window_s": "", "exists": str(OF_ENV.exists()).lower()}],
    )
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "preflight_rows": len(rows),
        "preflight_failures": sum(1 for r in rows if r["preflight_status"] != "pass"),
        "submitted_job_id": submitted.get("job_id", ""),
        "submitted_job_state": submitted.get("state", submitted.get("initial_squeue_state", "")),
        "submitted_begin_time": "2026-07-15T20:00:00",
        "related_agent445_job_id": "3297860",
        "harvested_station_rows": 0,
        "harvested_station_parsed_rows": 0,
        "harvested_adjacent_rows": 0,
        "harvested_adjacent_parsed_rows": 0,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def harvest(record_job_id: str = "") -> dict[str, Any]:
    station_rows, adjacent_rows = harvest_rows()
    write_csv(OUT / "station_pressure_ladder.csv", station_rows)
    write_csv(OUT / "adjacent_pressure_ladder.csv", adjacent_rows)
    summary = read_json(OUT / "summary.json") or build_package()
    summary.update({
        "last_harvest_at": utc_now(),
        "last_harvest_job_id": record_job_id,
        "harvested_station_rows": len(station_rows),
        "harvested_station_parsed_rows": sum(1 for row in station_rows if row.get("status") == "parsed_area_proxy"),
        "harvested_adjacent_rows": len(adjacent_rows),
        "harvested_adjacent_parsed_rows": sum(1 for row in adjacent_rows if row.get("status") == "diagnostic_adjacent_pressure_delta"),
    })
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def record_submission(job_id: str, state: str = "SUBMITTED") -> dict[str, Any]:
    payload = {"job_id": job_id, "job_name": "press_lad2", "state": state, "begin_time": "2026-07-15T20:00:00", "submitted_at": utc_now()}
    write_json(OUT / "submitted_job.json", payload)
    summary = read_json(OUT / "summary.json") or build_package()
    summary.update({"submitted_job_id": job_id, "submitted_job_state": state})
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-control", type=Path)
    parser.add_argument("--source-id", default="")
    parser.add_argument("--harvest", action="store_true")
    parser.add_argument("--record-job-id", default="")
    parser.add_argument("--record-submission", default="")
    parser.add_argument("--state", default="SUBMITTED")
    args = parser.parse_args()
    if args.write_control:
        if not args.source_id:
            raise SystemExit("--source-id is required with --write-control")
        write_control(args.write_control, args.source_id)
    elif args.harvest:
        harvest(args.record_job_id)
    elif args.record_submission:
        record_submission(args.record_submission, args.state)
    else:
        build_package()


if __name__ == "__main__":
    main()
