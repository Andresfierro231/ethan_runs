#!/usr/bin/env python3
"""Generate the Salt2 refined closure-QOI repair batch package.

The package reruns medium/fine extraction in fresh staged mirrors and hard-fails
on the exact AGENT-239 failure modes: missing section surfaces, zero sampled
stations, empty segment-friction rows, and thermal rows with no cut-plane data.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_salt2_refined_closure_qoi_repair_batch"
SCRIPTS = PKG / "scripts"
LOGS = PKG / "logs"
RECON = PKG / "recon"
OUTPUTS = PKG / "outputs"

PROFILE = "viscosity_screening_salt_test_2_jin_coarse_mesh"
MESH_STATIONS = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines" / PROFILE / "mesh_stations.json"
BASE = Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt")

CASES = [
    ("medium", BASE / "medium/viscosity_screening_salt_test_2_jin_medium_mesh", "518", "processors64"),
    ("fine", BASE / "fine/viscosity_screening_salt_test_2_jin_fine_mesh", "399", "processors128"),
]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def q(value: object) -> str:
    return "'" + str(value).replace("'", "'\"'\"'") + "'"


def write(path: Path, text: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def runner_text() -> str:
    case_lines = "\n".join(
        f"run_case {q(level)} {q(path)} {q(time)} {q(proc)}" for level, path, time, proc in CASES
    )
    return f"""#!/usr/bin/env bash
set -euo pipefail

ROOT={q(ROOT)}
PKG={q(PKG)}
PROFILE={q(PROFILE)}
MESH_STATIONS={q(MESH_STATIONS)}
OF_ENV="${{ROOT}}/tools/ofenv/of13_env.sh"

log() {{ echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] $*"; }}
die() {{ echo "ERROR: $*" >&2; exit 1; }}

assert_of13() {{
  bash -lc "cd '$ROOT' && source '$OF_ENV' >/dev/null 2>&1 && of13_assert_ready && test \\"\\$(foamPostProcess -help 2>&1 | head -20 | grep -c 'Usage: foamPostProcess')\\" -gt 0"
}}

prepare_recon() {{
  local level="$1" case_dir="$2" proc="$3" recon="$4"
  mkdir -p "$recon"
  [[ -d "$case_dir/$proc" ]] || die "$level missing $proc"
  [[ -f "$case_dir/case_config.yaml" ]] || die "$level missing case_config.yaml"
  if [[ ! -d "$recon/constant" ]]; then
    cp -a "$case_dir/constant" "$recon/constant"
    cp -a "$case_dir/system" "$recon/system"
    cp -a "$case_dir/0" "$recon/0"
    cp -a "$case_dir/case_config.yaml" "$recon/case_config.yaml"
  fi
  : > "$recon/system/functions"
  if [[ ! -e "$recon/$proc" ]]; then
    ln -s "$case_dir/$proc" "$recon/$proc"
  fi
  rm -rf "$recon/postProcessing"
  mkdir -p "$recon/postProcessing"
  cat > "$recon/PROVENANCE.txt" <<EOF
level=$level
source_case_root=$case_dir
profile_source_id=$PROFILE
mesh_stations=$MESH_STATIONS
created_at=$(date +%Y-%m-%dT%H:%M:%S%z)
EOF
}}

reconstruct_fields() {{
  local level="$1" recon="$2" time="$3" log_path="$4"
  if [[ -d "$recon/$time" ]]; then
    log "$level reusing reconstructed time $time"
    return 0
  fi
  log "$level reconstructPar t=$time"
  bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$recon' -time '$time' -fields '(T p_rgh U rho wallHeatFlux wallShearStress yPlus)'" > "$log_path" 2>&1
}}

assert_sampled_sections() {{
  local level="$1" out="$2" log_path="$3"
  local json_path="$out/section_mean_pressure_${{PROFILE}}.json"
  grep -q 'Version: 13' "$out/foampostprocess_${{PROFILE}}.log" || die "$level section foamPostProcess did not run under OF13"
  [[ -d "$out/../.." ]] || true
  python3 - "$json_path" <<'PY'
import json, sys
p=sys.argv[1]
data=json.load(open(p))
rows=data.get("stations") or data.get("rows") or []
sampled=[r for r in rows if r.get("status")=="sampled"]
if not sampled:
    raise SystemExit(f"no sampled section rows in {{p}}")
print(f"sampled_section_rows={{len(sampled)}} total_rows={{len(rows)}}")
PY
}}

assert_csv_has_data() {{
  local path="$1" label="$2"
  [[ -f "$path" ]] || die "$label missing: $path"
  local lines
  lines=$(wc -l < "$path")
  [[ "$lines" -gt 1 ]] || die "$label has no data rows: $path"
}}

assert_thermal_has_cutplane() {{
  local path="$1" label="$2"
  python3 - "$path" "$label" <<'PY'
import csv, sys
p,label=sys.argv[1],sys.argv[2]
rows=list(csv.DictReader(open(p)))
ok=[r for r in rows if r.get("status") not in ("no_cutplane_output", "thermally_blocked_segment_right_leg")]
if not ok:
    raise SystemExit(f"{{label}} has no non-blocked cutplane thermal rows: {{p}}")
print(f"thermal_cutplane_rows={{len(ok)}} total_rows={{len(rows)}}")
PY
}}

run_case() {{
  local level="$1" case_dir="$2" time="$3" proc="$4"
  local recon="$PKG/recon/$level"
  local out="$PKG/outputs/$level"
  mkdir -p "$out" "$PKG/logs"
  log "$level start source=$case_dir time=$time"
  prepare_recon "$level" "$case_dir" "$proc" "$recon"
  reconstruct_fields "$level" "$recon" "$time" "$PKG/logs/reconstruct_${{level}}.log"

  rm -rf "$recon/postProcessing"
  mkdir -p "$recon/postProcessing"
  log "$level section sampling"
  python3 "$ROOT/tools/extract/sample_section_mean_pressure.py" \\
    --case-dir "$recon" --time "$time" --source-id "$PROFILE" --output-dir "$out" \\
    --of-env-script tools/ofenv/of13_env.sh --centerline-source mesh \\
    --mesh-stations "$MESH_STATIONS" --dump-temperature > "$PKG/logs/section_${{level}}.log" 2>&1
  assert_sampled_sections "$level" "$out" "$PKG/logs/section_${{level}}.log"

  log "$level friction and momentum reductions"
  python3 "$ROOT/tools/analyze/derive_segment_friction.py" --input-dir "$out" --auto-mu-jin --drop-fitting-ends --output-dir "$out" > "$PKG/logs/friction_${{level}}.log" 2>&1
  assert_csv_has_data "$out/segment_friction.csv" "$level segment_friction"
  python3 "$ROOT/tools/analyze/derive_streamwise_momentum_budget.py" --input-dir "$out" --output-dir "$out" > "$PKG/logs/momentum_${{level}}.log" 2>&1
  assert_csv_has_data "$out/momentum_budget.csv" "$level momentum_budget"

  log "$level thermal extraction"
  ln -sfn "$case_dir/postProcessing/wallHeatFlux" "$recon/postProcessing/wallHeatFlux"
  python3 "$ROOT/tools/extract/sample_segment_htc_uaprime.py" \\
    --case-dir "$recon" --time "$time" --source-id "$PROFILE" --output-dir "$out" \\
    --mesh-length --mesh-stations "$MESH_STATIONS" > "$PKG/logs/thermal_${{level}}.log" 2>&1
  assert_thermal_has_cutplane "$out/segment_htc_uaprime_${{PROFILE}}.csv" "$level thermal"

  cat > "$out/run_provenance.json" <<EOF
{{"level":"$level","source_case_root":"$case_dir","time_s":"$time","processor_dir":"$proc","profile_source_id":"$PROFILE","mesh_stations":"$MESH_STATIONS","completed_at":"$(date +%Y-%m-%dT%H:%M:%S%z)"}}
EOF
  log "$level complete"
}}

main() {{
  mkdir -p "$PKG/logs" "$PKG/outputs" "$PKG/recon"
  [[ -f "$MESH_STATIONS" ]] || die "missing mesh stations: $MESH_STATIONS"
  assert_of13
{case_lines}
  log "all requested cases complete"
}}

main "$@"
"""


def sbatch_text() -> str:
    return f"""#!/usr/bin/env bash
#SBATCH -J agent245_salt2_qoi
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 128
#SBATCH -t 08:00:00
#SBATCH --begin=2026-07-09T21:00:00
#SBATCH -o {PKG}/logs/sbatch_%j.out
#SBATCH -e {PKG}/logs/sbatch_%j.err

set -euo pipefail
cd {q(ROOT)}
mkdir -p {q(LOGS)}
echo "started_at=$(date +%Y-%m-%dT%H:%M:%S%z) job=${{SLURM_JOB_ID:-unset}} host=$(hostname)" > {q(LOGS)}/sbatch_${{SLURM_JOB_ID:-nojob}}_provenance.env
bash {q(SCRIPTS / "run_repair_extraction.sh")} > {q(LOGS)}/sbatch_${{SLURM_JOB_ID:-nojob}}_repair.log 2>&1
echo "completed_at=$(date +%Y-%m-%dT%H:%M:%S%z)" >> {q(LOGS)}/sbatch_${{SLURM_JOB_ID:-nojob}}_provenance.env
"""


def main() -> int:
    for path in (SCRIPTS, LOGS, RECON, OUTPUTS):
        path.mkdir(parents=True, exist_ok=True)
    write(SCRIPTS / "run_repair_extraction.sh", runner_text(), executable=True)
    write(SCRIPTS / "sbatch_repair_extraction_9pm.sh", sbatch_text(), executable=True)
    summary = {
        "generated_at": now(),
        "task_id": "AGENT-245",
        "purpose": "9pm batch rerun of Salt2 refined closure-QOI extraction with hard gates",
        "profile_source_id": PROFILE,
        "mesh_stations": str(MESH_STATIONS),
        "cases": [
            {"level": level, "source_case_root": str(path), "time_s": time, "processor_dir": proc}
            for level, path, time, proc in CASES
        ],
        "expected_batch_script": str(SCRIPTS / "sbatch_repair_extraction_9pm.sh"),
        "source_cases_read_only": True,
        "closure_observations_updated": False,
    }
    write(PKG / "summary.json", json.dumps(summary, indent=2) + "\n")
    write(
        PKG / "README.md",
        f"""# Salt2 Refined Closure-QOI Repair Batch

Generated: `{now()}`

This package is the corrected follow-on to AGENT-239. AGENT-239 reconstructed
medium/fine fields but section sampling produced `no_output` rows and empty
segment-friction tables. This package reruns extraction in fresh staged mirrors
and hard-fails if pressure or thermal cut-plane outputs are missing.

## Submit

```bash
ssh login3 'cd {ROOT} && sbatch {SCRIPTS / "sbatch_repair_extraction_9pm.sh"}'
```

The batch is configured to start at `2026-07-09T21:00:00` on `NuclearEnergy`.

## Fresh-Agent Continuation

1. Check `squeue -j <jobid>` and then `sacct -j <jobid>` after completion.
2. Inspect `logs/sbatch_<jobid>_repair.log`.
3. Confirm `outputs/medium/segment_friction.csv` and
   `outputs/fine/segment_friction.csv` have data rows.
4. Confirm thermal CSVs have at least one non-`no_cutplane_output` row.
5. Only then assemble mainline-coarse/medium/fine closure-QOI mesh-UQ tables.
""",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
