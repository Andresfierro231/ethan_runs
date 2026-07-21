#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  submit_ethan_runs_backup_sbatch.sh [slurm options] [backup options]

Purpose:
  Submit the Ethan workspace backup prepare/plan/sync workflow through Slurm on
  a compute node so large rsync passes do not depend on a login shell.

Slurm options:
  --mode ACTION             Backup action: prepare, plan, or sync. Default: plan
  --job-name NAME           Slurm job name. Default: ethan_backup_<mode>
  --job-dir PATH            Directory for emitted sbatch script and logs
  --partition NAME          Slurm partition. Default: NuclearEnergy
  --account NAME            Slurm account. Default: ASC23046
  --time HH:MM:SS           Walltime. Default: 02:00:00 for plan, 10:00:00 for sync
  --begin SPEC              Slurm deferred start time passed to sbatch --begin
  --ntasks N                Slurm task count. Default: 1
  --cpus-per-task N         Slurm CPUs per task. Default: 1
  --rsync-bin PATH          rsync executable. Default: rsync
  --dry-run                 Emit the sbatch script without submitting
  --help, -h                Show this help text

Backup options:
  --source-root PATH        Source workspace root. Default: repo root
  --backup-root PATH        Backup root under /home1/.../cfd_runs
  --mirror-name NAME        Mirror subdirectory name. Default: ethan_runs
  --checksum                Compare by checksum instead of size+mtime
  --include-tmp             Include tmp/ in the backup scope
  --top-level-pass          Run one rsync pass per top-level included path

Examples:
  bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode plan --dry-run
  bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode sync --time 10:00:00
  bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode sync --include-tmp --time 12:00:00
  bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode sync --top-level-pass --begin tomorrowT20:00:00
EOF
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_PATH="$ROOT/tools/publish/rsync_ethan_runs_backup.sh"
DEFAULT_BACKUP_ROOT="/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup"

MODE="plan"
JOB_NAME=""
JOB_DIR=""
PARTITION="NuclearEnergy"
ACCOUNT="ASC23046"
WALLTIME=""
BEGIN_TIME=""
NTASKS="1"
CPUS_PER_TASK="1"
RSYNC_BIN="${RSYNC_BIN:-rsync}"
DRY_RUN=0
SOURCE_ROOT="$ROOT"
BACKUP_ROOT="$DEFAULT_BACKUP_ROOT"
MIRROR_NAME="ethan_runs"
USE_CHECKSUM=0
INCLUDE_TMP=0
TOP_LEVEL_PASS=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"
            shift 2
            ;;
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
        --begin)
            BEGIN_TIME="$2"
            shift 2
            ;;
        --ntasks)
            NTASKS="$2"
            shift 2
            ;;
        --cpus-per-task)
            CPUS_PER_TASK="$2"
            shift 2
            ;;
        --rsync-bin)
            RSYNC_BIN="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --source-root)
            SOURCE_ROOT="$2"
            shift 2
            ;;
        --backup-root)
            BACKUP_ROOT="$2"
            shift 2
            ;;
        --mirror-name)
            MIRROR_NAME="$2"
            shift 2
            ;;
        --checksum)
            USE_CHECKSUM=1
            shift
            ;;
        --include-tmp)
            INCLUDE_TMP=1
            shift
            ;;
        --top-level-pass)
            TOP_LEVEL_PASS=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

case "$MODE" in
    prepare|plan|sync)
        ;;
    *)
        echo "Unsupported mode: $MODE" >&2
        exit 1
        ;;
esac

if [[ -z "$WALLTIME" ]]; then
    if [[ "$MODE" == "sync" ]]; then
        WALLTIME="10:00:00"
    else
        WALLTIME="02:00:00"
    fi
fi

timestamp="$(date +%Y%m%dT%H%M%S)"
if [[ -z "$JOB_NAME" ]]; then
    JOB_NAME="ethan_backup_${MODE}"
fi
if [[ -z "$JOB_DIR" ]]; then
    JOB_DIR="$ROOT/tmp/slurm_ethan_runs_backup_jobs/${timestamp}_${MODE}"
fi

if [[ ! -x "$SCRIPT_PATH" && ! -f "$SCRIPT_PATH" ]]; then
    echo "Backup script not found: $SCRIPT_PATH" >&2
    exit 1
fi

mkdir -p "$JOB_DIR"

SBATCH_SCRIPT="$JOB_DIR/${JOB_NAME}.sbatch"
STDOUT_PATH="$JOB_DIR/slurm-%j.out"
STDERR_PATH="$JOB_DIR/slurm-%j.err"

COMMAND_ARGS=(
    "$SCRIPT_PATH"
    "$MODE"
    "--source-root" "$SOURCE_ROOT"
    "--backup-root" "$BACKUP_ROOT"
    "--mirror-name" "$MIRROR_NAME"
    "--rsync-bin" "$RSYNC_BIN"
)
if [[ "$USE_CHECKSUM" -eq 1 ]]; then
    COMMAND_ARGS+=("--checksum")
fi
if [[ "$INCLUDE_TMP" -eq 1 ]]; then
    COMMAND_ARGS+=("--include-tmp")
fi
if [[ "$TOP_LEVEL_PASS" -eq 1 ]]; then
    COMMAND_ARGS+=("--top-level-pass")
fi

command_string=""
printf -v command_string '%q ' "${COMMAND_ARGS[@]}"
command_string="${command_string% }"

printf -v root_q '%q' "$ROOT"
printf -v rsync_q '%q' "$RSYNC_BIN"

BEGIN_DIRECTIVE=""
if [[ -n "$BEGIN_TIME" ]]; then
    BEGIN_DIRECTIVE="#SBATCH --begin=$BEGIN_TIME"
fi

cat > "$SBATCH_SCRIPT" <<EOF
#!/bin/bash
#SBATCH -J $JOB_NAME
#SBATCH -p $PARTITION
#SBATCH -A $ACCOUNT
#SBATCH -N 1
#SBATCH -n $NTASKS
#SBATCH -c $CPUS_PER_TASK
#SBATCH -t $WALLTIME
#SBATCH -D $ROOT
#SBATCH -o $STDOUT_PATH
#SBATCH -e $STDERR_PATH
$BEGIN_DIRECTIVE

set -euo pipefail

cd $root_q

echo "Running in: $ROOT"
echo "Using rsync: $RSYNC_BIN"
echo "Executing: $command_string"

command -v $rsync_q >/dev/null 2>&1
$command_string
EOF

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "sbatch script: $SBATCH_SCRIPT"
    echo "command: $command_string"
    exit 0
fi

submit_output=""
if ! submit_output="$(sbatch --parsable "$SBATCH_SCRIPT" 2>&1)"; then
    echo "sbatch submission failed for $SBATCH_SCRIPT" >&2
    echo "$submit_output" >&2
    exit 1
fi
job_id="$(printf '%s\n' "$submit_output" | tail -n 1 | tr -d '[:space:]')"
if [[ -z "$job_id" || ! "$job_id" =~ ^[0-9]+$ ]]; then
    echo "sbatch did not return a usable numeric job id for $SBATCH_SCRIPT" >&2
    echo "$submit_output" >&2
    exit 1
fi

echo "job_id: $job_id"
echo "sbatch_script: $SBATCH_SCRIPT"
echo "stdout: $STDOUT_PATH"
echo "stderr: $STDERR_PATH"
