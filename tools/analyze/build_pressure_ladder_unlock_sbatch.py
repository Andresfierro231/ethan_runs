#!/usr/bin/env python3
"""Prepare and harvest AGENT-445 pressure-ladder unlock sbatch job."""

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
TASK = "AGENT-445"
DATE = "2026-07-15"
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch"
TMP = ROOT / "tmp/2026-07-15_pressure_ladder_unlock_sbatch"
MESH_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
OF_ENV = ROOT / "tools/ofenv/of13_env.sh"

CASES = [
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
    return TMP / "pressure_ladder" / case["case_key"] / "postProcessing/agent445PressureLadderSurfaces" / case["time_s"] / f"plane_{label}.xy"


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
  agent445PressureLadderSurfaces {{
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
    runner = scripts / "run_pressure_ladder.sh"
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
    mv "$case_dir/system/functions" "$case_dir/system/functions.agent445_disabled.$(date +%s)"
  fi
  python3.11 tools/analyze/build_pressure_ladder_unlock_sbatch.py --write-control "$case_dir" --source-id "$source_id"
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
  log "AGENT-445 pressure ladder preflight-only complete"
  exit 0
fi
python3.11 tools/analyze/build_pressure_ladder_unlock_sbatch.py --harvest --record-job-id "${{SLURM_JOB_ID:-local}}"
log "AGENT-445 pressure ladder runner complete"
""",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    sbatch = scripts / "submit_pressure_ladder.sbatch"
    sbatch.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J press_ladder
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 08:00:00
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
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
        {"script_id": "runner", "path": rel(runner), "purpose": "preflight/stage/reconstruct/sample/harvest all station planes"},
        {"script_id": "sbatch", "path": rel(sbatch), "purpose": "submit pressure ladder extraction to Slurm"},
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
        f"""# Pressure-Ladder Unlock Plan And sbatch

Task: AGENT-445
Generated: {DATE}

## Why This Exists

AGENT-440 successfully produced two-tap pressure diagnostics, but it did not
unlock final hydraulic residual attribution because two isolated taps cannot
establish pressure orientation, adjacent straight-loss subtraction, branch-local
development behavior, or recirculation masks. This package launches the next
overnight postprocessing step: sample all 30 mesh-centerline station planes for
Salt2/Salt3/Salt4 and harvest station plus adjacent-pair pressure deltas.

## Tomorrow Unlock Plan

1. Check job `{summary.get('submitted_job_id', '')}` with `sacct`.
2. If terminal, run `python3.11 tools/analyze/build_pressure_ladder_unlock_sbatch.py --harvest --record-job-id {summary.get('submitted_job_id', '')}`.
3. Open `station_pressure_ladder.csv` and `adjacent_pressure_ladder.csv`.
4. Build an orientation table by branch using adjacent `p` and `p_rgh` trends.
5. Use branch-specific adjacent pairs to estimate straight/distributed pressure gradients before computing any local/component K.
6. Mask rows with material reverse-area fractions before any true `f_D` or `K` fit.
7. Keep all rows diagnostic until mesh/GCI, pressure definition, tap orientation, straight-loss subtraction, and recirculation gates explicitly admit them.

## Current Status

- Preflight rows: `{summary['preflight_rows']}`
- Preflight failures: `{summary['preflight_failures']}`
- Station planes targeted per case: `30`
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
    write_csv(OUT / "source_manifest.csv", [{"path": c["source_case"], "role": c["case_key"], "exists": str((ROOT / c["source_case"]).exists()).lower()} for c in CASES] + [{"path": rel(OF_ENV), "role": "OpenFOAM 13 env", "exists": str(OF_ENV.exists()).lower()}])
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "preflight_rows": len(rows),
        "preflight_failures": sum(1 for r in rows if r["preflight_status"] != "pass"),
        "submitted_job_id": submitted.get("job_id", ""),
        "submitted_job_state": submitted.get("state", submitted.get("initial_squeue_state", "")),
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
    payload = {"job_id": job_id, "job_name": "press_ladder", "state": state, "submitted_at": utc_now()}
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
