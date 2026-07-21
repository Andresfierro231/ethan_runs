#!/usr/bin/env python3
"""Generate AGENT-248 Salt2 refined pressure-only smoke and 8pm batch package."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch"
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
    run_lines = "\n".join(
        f"run_case {q(level)} {q(path)} {q(time)} {q(proc)}" for level, path, time, proc in CASES
    )
    preflight_lines = "\n".join(
        f"preflight_case {q(level)} {q(path)} {q(time)} {q(proc)}" for level, path, time, proc in CASES
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
  bash -lc "cd '$ROOT' && source '$OF_ENV' >/dev/null 2>&1 && of13_assert_ready && foamPostProcess -help >/dev/null"
}}

preflight_case() {{
  local level="$1" case_dir="$2" time="$3" proc="$4"
  log "$level preflight source=$case_dir time=$time proc=$proc"
  [[ -d "$case_dir/$proc" ]] || die "$level missing processor dir $case_dir/$proc"
  for field in U p_rgh rho wallShearStress yPlus; do
    [[ -f "$case_dir/$proc/$time/$field" ]] || die "$level missing $field at $proc/$time"
  done
  [[ -f "$case_dir/$proc/$time/T" ]] || die "$level source T missing for diagnostic at $proc/$time"
}}

prepare_recon() {{
  local level="$1" case_dir="$2" proc="$3" recon="$4"
  mkdir -p "$recon"
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
notes=Pressure-only extraction; T deliberately not reconstructed or sampled.
EOF
}}

diagnose_source_t() {{
  local level="$1" case_dir="$2" time="$3" proc="$4" out="$5"
  python3 - "$case_dir/$proc/$time/T" "$out/t_diagnostic_${{level}}.json" "$level" <<'PY'
import json, math, re, sys
src, out, level = sys.argv[1:4]
numeric = re.compile(r"^[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?$")
total = finite = plausible = nonfinite = 0
examples = []
with open(src, encoding="utf-8", errors="replace") as f:
    for line in f:
        s = line.strip()
        if not numeric.match(s) and s.lower() not in ("nan", "-nan", "inf", "-inf"):
            continue
        total += 1
        try:
            value = float(s)
        except ValueError:
            nonfinite += 1
            if len(examples) < 5:
                examples.append(s)
            continue
        if math.isfinite(value):
            finite += 1
            if 250.0 <= value <= 1500.0:
                plausible += 1
        else:
            nonfinite += 1
            if len(examples) < 5:
                examples.append(s)
payload = {{
    "level": level,
    "source_T": src,
    "numeric_token_count": total,
    "finite_count": finite,
    "plausible_250_1500K_count": plausible,
    "nonfinite_count": nonfinite,
    "nonfinite_examples": examples,
    "thermal_status": "blocked_reconstructed_T_path_not_used_in_pressure_lane",
}}
if finite == 0 or plausible == 0:
    raise SystemExit(f"source T diagnostic failed: {{payload}}")
json.dump(payload, open(out, "w", encoding="utf-8"), indent=2)
print(json.dumps(payload, sort_keys=True))
PY
}}

reconstruct_pressure_fields() {{
  local level="$1" recon="$2" time="$3" log_path="$4"
  if [[ -d "$recon/$time" && -f "$recon/$time/U" && -f "$recon/$time/p_rgh" && -f "$recon/$time/rho" ]]; then
    log "$level reusing reconstructed pressure time $time"
    return 0
  fi
  log "$level reconstructPar pressure fields t=$time"
  bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$recon' -time '$time' -fields '(p_rgh U rho wallShearStress yPlus)'" > "$log_path" 2>&1
}}

assert_sampled_sections() {{
  local level="$1" out="$2"
  local foam_log="$out/foampostprocess_${{PROFILE}}.log"
  local json_path="$out/section_mean_pressure_${{PROFILE}}.json"
  grep -Eq 'Version:[[:space:]]*13' "$foam_log" || die "$level section foamPostProcess was not OF13"
  ! grep -q 'FOAM FATAL' "$foam_log" || die "$level section foamPostProcess had FOAM FATAL"
  python3 - "$json_path" "$level" <<'PY'
import json, sys
from collections import Counter
p, level = sys.argv[1:3]
data = json.load(open(p))
rows = data.get("stations") or data.get("rows") or []
sampled = [r for r in rows if r.get("status") == "sampled"]
by_span = Counter(r.get("span") for r in sampled)
required = ["lower_leg", "right_leg", "left_lower_leg", "test_section_span", "left_upper_leg", "upper_leg"]
missing = [span for span in required if by_span[span] < 2]
if missing:
    raise SystemExit(f"{{level}} missing sampled rows by span: {{missing}} counts={{dict(by_span)}}")
print(f"{{level}} sampled_section_rows={{len(sampled)}} by_span={{dict(by_span)}}")
PY
}}

assert_csv_has_data() {{
  local path="$1" label="$2"
  [[ -f "$path" ]] || die "$label missing: $path"
  local lines
  lines=$(wc -l < "$path")
  [[ "$lines" -gt 1 ]] || die "$label has no data rows: $path"
}}

run_case() {{
  local level="$1" case_dir="$2" time="$3" proc="$4"
  local recon="$PKG/recon/$level"
  local out="$PKG/outputs/$level"
  mkdir -p "$out" "$PKG/logs"
  preflight_case "$level" "$case_dir" "$time" "$proc"
  prepare_recon "$level" "$case_dir" "$proc" "$recon"
  diagnose_source_t "$level" "$case_dir" "$time" "$proc" "$out"
  reconstruct_pressure_fields "$level" "$recon" "$time" "$PKG/logs/reconstruct_${{level}}.log"

  rm -rf "$recon/postProcessing"
  mkdir -p "$recon/postProcessing"
  log "$level section sampling without T"
  python3 "$ROOT/tools/extract/sample_section_mean_pressure.py" \\
    --case-dir "$recon" --time "$time" --source-id "$PROFILE" --output-dir "$out" \\
    --of-env-script tools/ofenv/of13_env.sh --centerline-source mesh \\
    --mesh-stations "$MESH_STATIONS" > "$PKG/logs/section_${{level}}.log" 2>&1
  assert_sampled_sections "$level" "$out"

  log "$level friction and momentum reductions"
  python3 "$ROOT/tools/analyze/derive_segment_friction.py" \\
    --input-dir "$out" --auto-mu-jin --drop-fitting-ends --output-dir "$out" > "$PKG/logs/friction_${{level}}.log" 2>&1
  assert_csv_has_data "$out/segment_friction.csv" "$level segment_friction"
  python3 "$ROOT/tools/analyze/derive_streamwise_momentum_budget.py" \\
    --input-dir "$out" --output-dir "$out" > "$PKG/logs/momentum_${{level}}.log" 2>&1
  assert_csv_has_data "$out/momentum_budget.csv" "$level momentum_budget"
  cat > "$out/run_provenance.json" <<EOF
{{"level":"$level","source_case_root":"$case_dir","time_s":"$time","processor_dir":"$proc","profile_source_id":"$PROFILE","mesh_stations":"$MESH_STATIONS","thermal_status":"blocked_reconstructed_T_path_not_used","completed_at":"$(date +%Y-%m-%dT%H:%M:%S%z)"}}
EOF
  log "$level complete"
}}

main() {{
  local mode="${{1:-smoke}}"
  mkdir -p "$PKG/logs" "$PKG/outputs" "$PKG/recon"
  [[ -f "$MESH_STATIONS" ]] || die "missing mesh stations: $MESH_STATIONS"
  assert_of13
  case "$mode" in
    preflight)
{preflight_lines}
      ;;
    smoke|batch)
{run_lines}
      ;;
    *)
      die "unknown mode $mode"
      ;;
  esac
  log "mode $mode complete"
}}

main "$@"
"""


def sbatch_text() -> str:
    return f"""#!/usr/bin/env bash
#SBATCH -J agent248_salt2_pressure
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 128
#SBATCH -t 08:00:00
#SBATCH --begin=2026-07-10T20:00:00
#SBATCH -o {PKG}/logs/sbatch_%j.out
#SBATCH -e {PKG}/logs/sbatch_%j.err

set -euo pipefail
cd {q(ROOT)}
mkdir -p {q(LOGS)}
echo "started_at=$(date +%Y-%m-%dT%H:%M:%S%z) job=${{SLURM_JOB_ID:-unset}} host=$(hostname)" > {q(LOGS)}/sbatch_${{SLURM_JOB_ID:-nojob}}_provenance.env
bash {q(SCRIPTS / "run_pressure_extraction.sh")} batch > {q(LOGS)}/sbatch_${{SLURM_JOB_ID:-nojob}}_pressure.log 2>&1
echo "completed_at=$(date +%Y-%m-%dT%H:%M:%S%z)" >> {q(LOGS)}/sbatch_${{SLURM_JOB_ID:-nojob}}_provenance.env
"""


def main() -> int:
    for path in (SCRIPTS, LOGS, RECON, OUTPUTS):
        path.mkdir(parents=True, exist_ok=True)
    write(SCRIPTS / "run_pressure_extraction.sh", runner_text(), executable=True)
    write(SCRIPTS / "sbatch_pressure_extraction_8pm.sh", sbatch_text(), executable=True)
    payload = {
        "generated_at": now(),
        "task_id": "AGENT-248",
        "purpose": "Salt2 refined pressure-only smoke tests and 8pm batch submission",
        "profile_source_id": PROFILE,
        "mesh_stations": str(MESH_STATIONS),
        "cases": [
            {"level": level, "source_case_root": str(path), "time_s": time, "processor_dir": proc}
            for level, path, time, proc in CASES
        ],
        "thermal_policy": "blocked until reconstructed T path is repaired; no --dump-temperature in pressure lane",
        "source_cases_read_only": True,
        "closure_observations_updated": False,
        "batch_script": str(SCRIPTS / "sbatch_pressure_extraction_8pm.sh"),
        "scheduled_start": "2026-07-10T20:00:00",
    }
    write(PKG / "summary.json", json.dumps(payload, indent=2) + "\n")
    write(
        PKG / "README.md",
        f"""# Salt2 Refined Pressure Smoke And 8pm Batch

Generated: `{now()}`

This package is the pressure-only repair path after AGENT-245 failed on
reconstructed `T`. It deliberately avoids `--dump-temperature`, extracts
section pressure from `U p_rgh rho`, and keeps thermal UA/HTC/Nu blocked until
the `T` reconstruction path is repaired.

## Run Smoke

```bash
srun -N1 -n1 -c128 bash {SCRIPTS / "run_pressure_extraction.sh"} smoke
```

## Submit 8pm Batch

Only submit after smoke passes:

```bash
ssh login3 'cd {ROOT} && sbatch {SCRIPTS / "sbatch_pressure_extraction_8pm.sh"}'
```

## Acceptance Gates

- OF13 ready and used by `foamPostProcess`.
- At least two sampled section rows per major span for medium and fine.
- Non-empty `segment_friction.csv` and `momentum_budget.csv` for medium and fine.
- `t_diagnostic_<level>.json` records source decomposed T as finite/plausible,
  while thermal closure remains blocked.
""",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
