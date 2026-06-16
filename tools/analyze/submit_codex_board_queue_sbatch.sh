#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  submit_codex_board_queue_sbatch.sh [options]

Purpose:
  Submit one bounded Codex batch task that resumes only the currently
  half-finished Ethan board work and then completes one additional queued
  analysis row before exiting.

Typical usage:
  1. Dry run from a login node:
     bash tools/analyze/submit_codex_board_queue_sbatch.sh --dry-run
  2. Inspect the emitted prompt and sbatch script under tmp/slurm_codex_board_jobs/
  3. Submit for real:
     bash tools/analyze/submit_codex_board_queue_sbatch.sh
  4. Monitor with:
     squeue -j <jobid>
     sacct -j <jobid>

Options:
  --job-name NAME            Slurm job name. Default: codex_ethan_queue_resume
  --job-dir PATH             Directory for emitted sbatch script, prompt, and logs
  --partition NAME           Slurm partition. Default: NuclearEnergy
  --account NAME             Slurm account. Default: ASC23046
  --time HH:MM:SS            Walltime. Default: 06:00:00
  --cpus-per-task N          CPU count. Default: 2
  --codex-bin PATH           Codex executable path
  --model MODEL              Optional Codex model override
  --sandbox MODE             Codex sandbox mode. Default: workspace-write
  --cross-model-root PATH    Writable sibling tree to add to Codex. Default: ../cfd-modeling-tools
  --allow-stale-board        Skip the pre-submit board-state assertion
  --dry-run                  Emit the sbatch script and prompt without submitting
  --help, -h                 Show this help text

Bounded work slice:
  1. Close the half-finished Salt 4 Jin reviewer/cleanup pass (AGENT-067)
  2. Finish plotting row 5 for viscosity_screening_salt_test_1_jin_coarse_mesh
  3. Finish analysis row 2 for val_water_test_2_coarse_mesh_laminar
  4. Finish one additional queued analysis row: row 3 for val_water_test_3_coarse_mesh_laminar
  5. Exit naturally after recording results
USAGE
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BOARD_PATH="$ROOT/.agent/BOARD.md"
CODEX_BIN_DEFAULT="/home1/09748/andresfierro231/.local/bin/codex"
CROSS_MODEL_ROOT_DEFAULT="$(cd "$ROOT/../cfd-modeling-tools" 2>/dev/null && pwd || true)"

JOB_NAME="codex_ethan_queue_resume"
JOB_DIR=""
PARTITION="NuclearEnergy"
ACCOUNT="ASC23046"
WALLTIME="06:00:00"
CPUS_PER_TASK="2"
CODEX_BIN="$CODEX_BIN_DEFAULT"
CODEX_MODEL=""
CODEX_SANDBOX="workspace-write"
CROSS_MODEL_ROOT="$CROSS_MODEL_ROOT_DEFAULT"
ALLOW_STALE_BOARD=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --job-name)
            JOB_NAME="$2"
            shift 2
            ;;
        --job-dir)
            JOB_DIR="$2"
            shift 2
            ;;
        --partition)
            PARTITION="$2"
            shift 2
            ;;
        --account)
            ACCOUNT="$2"
            shift 2
            ;;
        --time)
            WALLTIME="$2"
            shift 2
            ;;
        --cpus-per-task)
            CPUS_PER_TASK="$2"
            shift 2
            ;;
        --codex-bin)
            CODEX_BIN="$2"
            shift 2
            ;;
        --model)
            CODEX_MODEL="$2"
            shift 2
            ;;
        --sandbox)
            CODEX_SANDBOX="$2"
            shift 2
            ;;
        --cross-model-root)
            CROSS_MODEL_ROOT="$2"
            shift 2
            ;;
        --allow-stale-board)
            ALLOW_STALE_BOARD=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ ! -f "$BOARD_PATH" ]]; then
    echo "Board file not found: $BOARD_PATH" >&2
    exit 1
fi
if [[ ! -x "$CODEX_BIN" ]]; then
    echo "Codex executable not found or not executable: $CODEX_BIN" >&2
    exit 1
fi
if [[ -z "$CROSS_MODEL_ROOT" || ! -d "$CROSS_MODEL_ROOT" ]]; then
    echo "Cross-model root not found: $CROSS_MODEL_ROOT" >&2
    exit 1
fi

if [[ -z "$JOB_DIR" ]]; then
    timestamp="$(date +%Y%m%dT%H%M%S)"
    JOB_DIR="$ROOT/tmp/slurm_codex_board_jobs/${timestamp}_${JOB_NAME}"
fi
mkdir -p "$JOB_DIR"

PROMPT_PATH="$JOB_DIR/prompt.md"
SBATCH_SCRIPT="$JOB_DIR/${JOB_NAME}.sbatch"
STDOUT_PATH="$JOB_DIR/slurm-%j.out"
STDERR_PATH="$JOB_DIR/slurm-%j.err"
EVENTS_PATH="$JOB_DIR/codex-events.jsonl"
LAST_MESSAGE_PATH="$JOB_DIR/codex-last-message.txt"
ENV_PATH="$JOB_DIR/environment.txt"
BOARD_SNAPSHOT_PATH="$JOB_DIR/board-snapshot.txt"
ASSERTION_PATH="$JOB_DIR/board-assertion.txt"

python3.11 - "$BOARD_PATH" "$ALLOW_STALE_BOARD" "$ASSERTION_PATH" "$BOARD_SNAPSHOT_PATH" <<'PY_ASSERT'
from pathlib import Path
import sys

board_path = Path(sys.argv[1])
allow_stale = sys.argv[2] == "1"
assertion_path = Path(sys.argv[3])
snapshot_path = Path(sys.argv[4])
text = board_path.read_text(encoding="utf-8")
snapshot_path.write_text(text, encoding="utf-8")

rows = {}
for line in text.splitlines():
    if not line.startswith("| "):
        continue
    parts = [part.strip() for part in line.strip().strip("|").split("|")]
    if len(parts) != 9:
        continue
    priority, source_id, plotting, plotter, analysis, analyst, review, reviewer, notes = parts
    if not priority.isdigit():
        continue
    rows[source_id.strip("`")] = {
        "priority": priority,
        "plotting": plotting.strip("`"),
        "plotter": plotter.strip("`"),
        "analysis": analysis.strip("`"),
        "analyst": analyst.strip("`"),
        "review": review.strip("`"),
        "reviewer": reviewer.strip("`"),
    }

checks = [
    (
        "viscosity_screening_salt_test_1_jin_coarse_mesh",
        {"plotting": "running", "plotter": "AGENT-058", "analysis": "waiting-on-plotting"},
    ),
    (
        "val_water_test_2_coarse_mesh_laminar",
        {"analysis": "running", "analyst": "AGENT-059", "plotting": "done"},
    ),
    (
        "val_water_test_3_coarse_mesh_laminar",
        {"analysis": "queued", "plotting": "done"},
    ),
    (
        "campaign_synthesis",
        {"plotting": "waiting-on-all-runs-reviewed"},
    ),
]
errors = []
for source_id, expected in checks:
    row = rows.get(source_id)
    if row is None:
        errors.append(f"missing row for {source_id}")
        continue
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append(f"{source_id} expected {key}={value!r} but found {row.get(key)!r}")

message = "Board assertion passed for bounded Codex queue resume slice.\n"
if errors:
    message = "Board assertion failed:\n- " + "\n- ".join(errors) + "\n"
assertion_path.write_text(message, encoding="utf-8")
if errors and not allow_stale:
    print(message, file=sys.stderr)
    sys.exit(1)
PY_ASSERT

cat > "$PROMPT_PATH" <<PROMPT_EOF
You are a bounded Codex recovery run for Ethan queue cleanup on $(date --iso-8601=seconds).

Workspace roots available:
- Primary workspace: $ROOT
- Additional writable sibling tree: $CROSS_MODEL_ROOT

Your task is intentionally narrow. Complete only this slice, in order, and then stop:

1. Finish the half-finished Salt 4 Jin reviewer/cleanup pass for AGENT-067.
   Allowed local files:
   - $ROOT/.agent/BOARD.md
   - $ROOT/.agent/status/2026-06-12_AGENT-067.md
   - $ROOT/.agent/journal/2026-06-12/coordinator-implementer-salt4-jin-rollout.md
   - $ROOT/tmp/2026-06-12_salt4_jin_case_analysis_package_window4/**
   Review the completed package rigorously. If it clears the same caveated rollout standard as the prior Salt-family cases, record that outcome durably and close the stale "build running" state honestly. If it does not clear, record a blocker and stop without touching the Ethan postprocessing queue.

2. Finish the half-finished plotting row 5 for source_id viscosity_screening_salt_test_1_jin_coarse_mesh under AGENT-058.
   Allowed queue/control files:
   - $ROOT/.agent/BOARD.md
   - $ROOT/.agent/status/2026-06-12_AGENT-058.md
   - $ROOT/.agent/journal/2026-06-12/implementer-ethan-postprocessing-plot-queue.md
   Allowed package subtree:
   - $CROSS_MODEL_ROOT/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/runs/viscosity_screening_salt_test_1_jin_coarse_mesh/**
   Existing smoke-build evidence:
   - $ROOT/tmp/2026-06-12_ethan_postprocessing_plot_smoke_5/**
   Verify rigorously whether the smoke build justifies releasing row 5 to Plotting=done and Analysis=queued. If more regeneration or comparison is needed, do it rigorously. Do not touch any other plotting row.

3. Finish the half-finished analysis row 2 for source_id val_water_test_2_coarse_mesh_laminar under AGENT-059.
   Allowed queue/control files:
   - $ROOT/.agent/BOARD.md
   - $ROOT/.agent/status/2026-06-12_AGENT-059.md
   - $ROOT/.agent/journal/2026-06-12/writer-ethan-postprocessing-analysis-queue.md
   Allowed report files:
   - $CROSS_MODEL_ROOT/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/runs/val_water_test_2_coarse_mesh_laminar/reports/executive_summary.md
   - $CROSS_MODEL_ROOT/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/runs/val_water_test_2_coarse_mesh_laminar/reports/technical_analysis.md
   Complete the analysis row rigorously from repo evidence and update the board from Analysis=running to Analysis=done and Review=queued if justified.

4. After row 2 is fully complete, claim and finish exactly one additional queued analysis row: row 3 for source_id val_water_test_3_coarse_mesh_laminar.
   Allowed report files:
   - $CROSS_MODEL_ROOT/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/runs/val_water_test_3_coarse_mesh_laminar/reports/executive_summary.md
   - $CROSS_MODEL_ROOT/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/runs/val_water_test_3_coarse_mesh_laminar/reports/technical_analysis.md
   Do not continue to row 4. Stop after row 3 is durably updated.

Required operating rules:
- Start by reading $ROOT/AGENTS.md, $ROOT/.agent/BOARD.md, $ROOT/.agent/FILE_OWNERSHIP.md, and $ROOT/.agent/ROLES.md.
- Before editing inside the sibling cross_model_comparison tree, read:
  - $CROSS_MODEL_ROOT/cross_model_comparison/AGENTS.md
  - $CROSS_MODEL_ROOT/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/TODO.md
- Keep changes small and reviewable.
- Do not touch campaign_synthesis.
- Do not touch any review row in the Ethan postprocessing queue.
- Do not touch any analysis row other than rows 2 and 3.
- Do not touch any plotting row other than row 5.
- Do not edit unrelated task files.
- If you find a real blocker, record it durably in the owned status/journal/board note and stop cleanly.
- At the end, provide a concise final summary and then exit naturally. Do not wait for more input.
PROMPT_EOF

printf 'ROOT=%s\n' "$ROOT" > "$ENV_PATH"
printf 'BOARD_PATH=%s\n' "$BOARD_PATH" >> "$ENV_PATH"
printf 'CROSS_MODEL_ROOT=%s\n' "$CROSS_MODEL_ROOT" >> "$ENV_PATH"
printf 'CODEX_BIN=%s\n' "$CODEX_BIN" >> "$ENV_PATH"
printf 'CODEX_MODEL=%s\n' "$CODEX_MODEL" >> "$ENV_PATH"
printf 'CODEX_SANDBOX=%s\n' "$CODEX_SANDBOX" >> "$ENV_PATH"
printf 'JOB_DIR=%s\n' "$JOB_DIR" >> "$ENV_PATH"

codex_cmd=("$CODEX_BIN" exec --sandbox "$CODEX_SANDBOX" -C "$ROOT" --add-dir "$CROSS_MODEL_ROOT" --output-last-message "$LAST_MESSAGE_PATH" --json)
if [[ -n "$CODEX_MODEL" ]]; then
    codex_cmd+=(--model "$CODEX_MODEL")
fi
codex_cmd+=(-)
printf -v codex_cmd_str '%q ' "${codex_cmd[@]}"
codex_cmd_str="${codex_cmd_str% }"

cat > "$SBATCH_SCRIPT" <<SBATCH_EOF
#!/bin/bash
#SBATCH -J $JOB_NAME
#SBATCH -p $PARTITION
#SBATCH -A $ACCOUNT
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c $CPUS_PER_TASK
#SBATCH -t $WALLTIME
#SBATCH -o $STDOUT_PATH
#SBATCH -e $STDERR_PATH

set -euo pipefail
cd $(printf '%q' "$ROOT")
export TMPDIR=/tmp
export PYTHONUNBUFFERED=1

echo "Running Codex bounded board resume in: $ROOT"
echo "Additional writable tree: $CROSS_MODEL_ROOT"
echo "Codex command: $codex_cmd_str"

$codex_cmd_str < $(printf '%q' "$PROMPT_PATH") | tee $(printf '%q' "$EVENTS_PATH")
SBATCH_EOF

chmod +x "$SBATCH_SCRIPT"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "board_assertion: $ASSERTION_PATH"
    echo "prompt: $PROMPT_PATH"
    echo "sbatch_script: $SBATCH_SCRIPT"
    echo "stdout: $STDOUT_PATH"
    echo "stderr: $STDERR_PATH"
    echo "events: $EVENTS_PATH"
    echo "last_message: $LAST_MESSAGE_PATH"
    exit 0
fi

submit_output="$(sbatch --parsable "$SBATCH_SCRIPT" 2>&1)" || {
    echo "sbatch submission failed for $SBATCH_SCRIPT" >&2
    echo "$submit_output" >&2
    exit 1
}
job_id="$(printf '%s\n' "$submit_output" | tail -n 1 | tr -d '[:space:]')"
if [[ -z "$job_id" || ! "$job_id" =~ ^[0-9]+$ ]]; then
    echo "sbatch did not return a usable numeric job id for $SBATCH_SCRIPT" >&2
    echo "$submit_output" >&2
    exit 1
fi

echo "job_id: $job_id"
echo "board_assertion: $ASSERTION_PATH"
echo "prompt: $PROMPT_PATH"
echo "sbatch_script: $SBATCH_SCRIPT"
echo "stdout: $STDOUT_PATH"
echo "stderr: $STDERR_PATH"
echo "events: $EVENTS_PATH"
echo "last_message: $LAST_MESSAGE_PATH"
