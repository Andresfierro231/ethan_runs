#!/usr/bin/env python3
"""Build Salt2 refined-mesh closure-QOI smoke/overnight runners.

The generated runners keep Ethan's source cases read-only. They stage a local
reconstruction directory under this work product, symlink decomposed processor
data from the source, run OpenFOAM under ``srun``/OF13, and write derived closure
products only under the package output tree.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_salt2_fine_closure_qoi_smoke_and_overnight"
SCRIPTS = PACKAGE / "scripts"
LOGS = PACKAGE / "logs"
OUTPUTS = PACKAGE / "outputs"
RECON = PACKAGE / "recon"

PROFILE_SOURCE_ID = "viscosity_screening_salt_test_2_jin_coarse_mesh"
MESH_STATIONS = (
    ROOT
    / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
    / PROFILE_SOURCE_ID
    / "mesh_stations.json"
)

SOURCE_BASE = Path(
    "/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt"
)

CASES = [
    {
        "mesh_level": "medium",
        "source_case_id": "viscosity_screening_salt_test_2_jin_medium_mesh",
        "source_case_root": SOURCE_BASE
        / "medium/viscosity_screening_salt_test_2_jin_medium_mesh",
        "latest_time_s": "518",
        "processor_dir": "processors64",
        "role": "smoke_full_pipeline_before_fine",
    },
    {
        "mesh_level": "fine",
        "source_case_id": "viscosity_screening_salt_test_2_jin_fine_mesh",
        "source_case_root": SOURCE_BASE / "fine/viscosity_screening_salt_test_2_jin_fine_mesh",
        "latest_time_s": "399",
        "processor_dir": "processors128",
        "role": "overnight_target",
    },
]


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def q(path: Path | str) -> str:
    return "'" + str(path).replace("'", "'\"'\"'") + "'"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_runner() -> str:
    medium = CASES[0]
    fine = CASES[1]
    return f"""#!/usr/bin/env bash
set -euo pipefail

ROOT={q(ROOT)}
PACKAGE={q(PACKAGE)}
PROFILE_SOURCE_ID={q(PROFILE_SOURCE_ID)}
MESH_STATIONS={q(MESH_STATIONS)}
OF_ENV_SCRIPT="tools/ofenv/of13_env.sh"

log() {{
  echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] $*"
}}

die() {{
  echo "ERROR: $*" >&2
  exit 1
}}

run_cmd() {{
  log "CMD: $*"
  "$@"
}}

assert_ready() {{
  cd "$ROOT"
  [[ -f "$MESH_STATIONS" ]] || die "mesh stations missing: $MESH_STATIONS"
  bash -lc "cd '$ROOT' && source '$ROOT/$OF_ENV_SCRIPT' >/dev/null 2>&1 && of13_assert_ready"
  python3 - <<'PY'
import scipy, numpy
print(f"python scipy={{scipy.__version__}} numpy={{numpy.__version__}}")
PY
}}

prepare_recon_dir() {{
  local mesh_level="$1"
  local case_dir="$2"
  local proc_dir="$3"
  local recon_dir="$4"

  mkdir -p "$recon_dir"
  if [[ ! -d "$recon_dir/constant" ]]; then
    cp -a "$case_dir/constant" "$recon_dir/constant"
    cp -a "$case_dir/system" "$recon_dir/system"
    cp -a "$case_dir/0" "$recon_dir/0"
    cp -a "$case_dir/case_config.yaml" "$recon_dir/case_config.yaml"
  fi
  # The source controlDict includes "functions". Use an empty include-compatible
  # file during reconstructPar, then sample_section_mean_pressure.py overwrites
  # controlDict for the sampling stage.
  : > "$recon_dir/system/functions"
  if [[ ! -e "$recon_dir/$proc_dir" ]]; then
    ln -s "$case_dir/$proc_dir" "$recon_dir/$proc_dir"
  fi

  mkdir -p "$recon_dir/postProcessing"
  for family in wallHeatFlux temperature_probes wall_temperature_probes mdot_pipeleg_left_04_test_section mdot_pipeleg_lower_05_straight mdot_pipeleg_right_02_middle mdot_pipeleg_upper_05_cooler; do
    if [[ -e "$case_dir/postProcessing/$family" && ! -e "$recon_dir/postProcessing/$family" ]]; then
      ln -s "$case_dir/postProcessing/$family" "$recon_dir/postProcessing/$family"
    fi
  done

  cat > "$recon_dir/PROVENANCE.txt" <<EOF
mesh_level=$mesh_level
source_case_root=$case_dir
profile_source_id=$PROFILE_SOURCE_ID
mesh_stations=$MESH_STATIONS
created_at=$(date +%Y-%m-%dT%H:%M:%S%z)
notes=Local reconstruction mirror; source processors and monitor folders are symlinked read-only by policy.
EOF
}}

preflight_case() {{
  local mesh_level="$1"
  local case_dir="$2"
  local time_val="$3"
  local proc_dir="$4"
  log "Preflight $mesh_level: $case_dir at t=$time_val"
  [[ -d "$case_dir" ]] || die "$mesh_level case missing: $case_dir"
  [[ -d "$case_dir/$proc_dir" ]] || die "$mesh_level processor dir missing: $case_dir/$proc_dir"
  for field in T U p_rgh rho wallHeatFlux wallShearStress yPlus; do
    [[ -f "$case_dir/$proc_dir/$time_val/$field" ]] || die "$mesh_level missing $field at $proc_dir/$time_val"
  done
  [[ -f "$case_dir/postProcessing/wallHeatFlux/0/wallHeatFlux.dat" || -n "$(find "$case_dir/postProcessing/wallHeatFlux" -name wallHeatFlux.dat -print -quit)" ]] || die "$mesh_level wallHeatFlux monitor missing"
}}

run_case() {{
  local mesh_level="$1"
  local case_dir="$2"
  local time_val="$3"
  local proc_dir="$4"
  local out_dir="$PACKAGE/outputs/$mesh_level"
  local recon_dir="$PACKAGE/recon/$mesh_level"
  local recon_log="$PACKAGE/logs/reconstruct_$mesh_level.log"
  local thermal_log="$PACKAGE/logs/thermal_$mesh_level.log"
  local section_log="$PACKAGE/logs/section_$mesh_level.log"
  local friction_log="$PACKAGE/logs/friction_$mesh_level.log"
  local momentum_log="$PACKAGE/logs/momentum_$mesh_level.log"

  mkdir -p "$out_dir" "$PACKAGE/logs" "$PACKAGE/recon"
  preflight_case "$mesh_level" "$case_dir" "$time_val" "$proc_dir"
  prepare_recon_dir "$mesh_level" "$case_dir" "$proc_dir" "$recon_dir"

  if [[ ! -d "$recon_dir/$time_val" ]]; then
    log "Reconstructing $mesh_level fields at t=$time_val"
    bash -lc "source '$ROOT/$OF_ENV_SCRIPT' >/dev/null 2>&1 && reconstructPar -case '$recon_dir' -time '$time_val' -fields '(T p_rgh U rho wallHeatFlux wallShearStress yPlus)'" > "$recon_log" 2>&1
  else
    log "Reusing existing reconstruction: $recon_dir/$time_val"
  fi

  : > "$recon_dir/system/functions"

  log "Sampling section means for $mesh_level"
  python3 "$ROOT/tools/extract/sample_section_mean_pressure.py" \\
    --case-dir "$recon_dir" \\
    --time "$time_val" \\
    --source-id "$PROFILE_SOURCE_ID" \\
    --output-dir "$out_dir" \\
    --of-env-script "$OF_ENV_SCRIPT" \\
    --centerline-source mesh \\
    --mesh-stations "$MESH_STATIONS" \\
    --dump-temperature > "$section_log" 2>&1

  log "Deriving segment friction for $mesh_level"
  python3 "$ROOT/tools/analyze/derive_segment_friction.py" \\
    --input-dir "$out_dir" \\
    --auto-mu-jin \\
    --drop-fitting-ends \\
    --output-dir "$out_dir" > "$friction_log" 2>&1

  log "Deriving streamwise momentum budget for $mesh_level"
  python3 "$ROOT/tools/analyze/derive_streamwise_momentum_budget.py" \\
    --input-dir "$out_dir" \\
    --output-dir "$out_dir" > "$momentum_log" 2>&1

  log "Running thermal closure extractor for $mesh_level"
  python3 "$ROOT/tools/extract/sample_segment_htc_uaprime.py" \\
    --case-dir "$recon_dir" \\
    --time "$time_val" \\
    --source-id "$PROFILE_SOURCE_ID" \\
    --output-dir "$out_dir" \\
    --mesh-length \\
    --mesh-stations "$MESH_STATIONS" > "$thermal_log" 2>&1

  cat > "$out_dir/run_provenance.json" <<EOF
{{
  "mesh_level": "$mesh_level",
  "source_case_root": "$case_dir",
  "profile_source_id": "$PROFILE_SOURCE_ID",
  "mesh_stations": "$MESH_STATIONS",
  "time_s": "$time_val",
  "processor_dir": "$proc_dir",
  "recon_dir": "$recon_dir",
  "completed_at": "$(date +%Y-%m-%dT%H:%M:%S%z)"
}}
EOF
  log "Completed $mesh_level; outputs: $out_dir"
}}

main() {{
  local mode="${{1:-smoke_then_overnight}}"
  mkdir -p "$PACKAGE/logs" "$PACKAGE/outputs" "$PACKAGE/recon"
  log "Salt2 refined closure-QOI runner mode=$mode"
  assert_ready

  case "$mode" in
    preflight)
      preflight_case medium {q(medium["source_case_root"])} {q(medium["latest_time_s"])} {q(medium["processor_dir"])}
      preflight_case fine {q(fine["source_case_root"])} {q(fine["latest_time_s"])} {q(fine["processor_dir"])}
      ;;
    smoke)
      run_case medium {q(medium["source_case_root"])} {q(medium["latest_time_s"])} {q(medium["processor_dir"])}
      ;;
    overnight)
      run_case fine {q(fine["source_case_root"])} {q(fine["latest_time_s"])} {q(fine["processor_dir"])}
      ;;
    smoke_then_overnight)
      run_case medium {q(medium["source_case_root"])} {q(medium["latest_time_s"])} {q(medium["processor_dir"])}
      run_case fine {q(fine["source_case_root"])} {q(fine["latest_time_s"])} {q(fine["processor_dir"])}
      ;;
    *)
      die "unknown mode: $mode"
      ;;
  esac
  log "Runner complete mode=$mode"
}}

main "$@"
"""


def make_launchers() -> tuple[str, str, str]:
    driver = SCRIPTS / "run_refined_closure_qoi.sh"
    smoke = f"""#!/usr/bin/env bash
set -euo pipefail
cd {q(ROOT)}
mkdir -p {q(LOGS)}
srun -N1 -n1 -c64 bash {q(driver)} smoke > {q(LOGS / "srun_smoke.log")} 2>&1
"""
    overnight = f"""#!/usr/bin/env bash
set -euo pipefail
cd {q(ROOT)}
mkdir -p {q(LOGS)}
srun -N1 -n1 -c128 bash {q(driver)} overnight > {q(LOGS / "srun_overnight.log")} 2>&1
"""
    chain = f"""#!/usr/bin/env bash
set -euo pipefail
cd {q(ROOT)}
mkdir -p {q(LOGS)}
srun -N1 -n1 -c128 bash {q(driver)} smoke_then_overnight > {q(LOGS / "srun_smoke_then_overnight.log")} 2>&1
"""
    return smoke, overnight, chain


def main() -> int:
    for path in (SCRIPTS, LOGS, OUTPUTS, RECON):
        path.mkdir(parents=True, exist_ok=True)

    runner = make_runner()
    runner_path = SCRIPTS / "run_refined_closure_qoi.sh"
    write(runner_path, runner)
    smoke, overnight, chain = make_launchers()
    write(SCRIPTS / "launch_smoke_srun.sh", smoke)
    write(SCRIPTS / "launch_overnight_srun.sh", overnight)
    write(SCRIPTS / "launch_smoke_then_overnight_srun.sh", chain)
    for script in SCRIPTS.glob("*.sh"):
        script.chmod(0o755)

    summary = {
        "generated_at": iso_now(),
        "task": "AGENT-239",
        "profile_source_id": PROFILE_SOURCE_ID,
        "mesh_stations": str(MESH_STATIONS),
        "source_cases": [
            {
                **case,
                "source_case_root": str(case["source_case_root"]),
                "exists": Path(case["source_case_root"]).exists(),
            }
            for case in CASES
        ],
        "policy": {
            "source_cases_read_only": True,
            "closure_observations_updated": False,
            "registry_updated": False,
            "runner_requires_compute_node": True,
        },
        "entrypoints": {
            "driver": str(runner_path),
            "smoke": str(SCRIPTS / "launch_smoke_srun.sh"),
            "overnight": str(SCRIPTS / "launch_overnight_srun.sh"),
            "smoke_then_overnight": str(SCRIPTS / "launch_smoke_then_overnight_srun.sh"),
        },
    }
    write(PACKAGE / "summary.json", json.dumps(summary, indent=2) + "\n")

    rows = [
        "mesh_level,role,source_case_id,source_case_root,latest_time_s,processor_dir,profile_source_id,planned_output_dir",
    ]
    for case in CASES:
        rows.append(
            ",".join(
                [
                    case["mesh_level"],
                    case["role"],
                    case["source_case_id"],
                    str(case["source_case_root"]),
                    case["latest_time_s"],
                    case["processor_dir"],
                    PROFILE_SOURCE_ID,
                    str(OUTPUTS / case["mesh_level"]),
                ]
            )
        )
    write(PACKAGE / "sampling_targets.csv", "\n".join(rows) + "\n")

    readme = f"""# Salt2 Fine Closure-QOI Smoke And Overnight

Generated: `{iso_now()}`

This package launches compute-node processing for Salt2 refined-mesh closure
QoIs while keeping the imported Ethan case folders read-only.

## Execution Contract

- Smoke test: run the Salt2 Jin medium mesh through reconstruction, section-mean
  pressure sampling, segment friction, momentum budget, and thermal closure
  extraction.
- Overnight target: run the same pipeline on the Salt2 Jin fine mesh only after
  the smoke step succeeds.
- Provenance: the physical source case is medium/fine; the station and segment
  contract uses `{PROFILE_SOURCE_ID}` because refined-mesh source IDs are not
  registered in `tools.case_analysis_profiles`.

## Entrypoints

- `scripts/launch_smoke_srun.sh`
- `scripts/launch_overnight_srun.sh`
- `scripts/launch_smoke_then_overnight_srun.sh`
- Direct driver: `scripts/run_refined_closure_qoi.sh [preflight|smoke|overnight|smoke_then_overnight]`

## Expected Outputs

Each mesh level writes under `outputs/<mesh_level>/`:

- `section_mean_pressure_{PROFILE_SOURCE_ID}.json/.csv`
- `segment_friction.json/.csv`
- `momentum_budget.json/.csv`
- thermal closure outputs from `sample_segment_htc_uaprime.py`
- `run_provenance.json`

Logs write under `logs/`; staged reconstructions write under `recon/`.

## Interpretation Boundary

These outputs are extraction products, not closure-table admissions. Do not
update `closure_observations.csv` until the medium/fine rows are reviewed,
compared with the aligned mainline coarse baseline, and converted into explicit
closure-QOI mesh-UQ/GCI rows.
"""
    write(PACKAGE / "README.md", readme)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
