#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  submit_ethan_case_analysis_package_sbatch.sh [slurm options] --source-id SOURCE_ID --output-dir OUTPUT_DIR [builder options]

Purpose:
  Submit the reusable Ethan case-analysis package builder through Slurm so
  long hydraulic/thermal extraction runs do not depend on an interactive shell.

Slurm options:
  --job-name NAME            Slurm job name. Default: derived from SOURCE_ID.
  --job-dir PATH             Directory for emitted sbatch script and logs.
  --partition NAME           Slurm partition. Default: NuclearEnergy
  --account NAME             Slurm account. Default: ASC23046
  --time HH:MM:SS            Walltime. Default: 12:00:00
  --ntasks N                 Slurm task count. Default: 1
  --cpus-per-task N          Slurm CPUs per task. Default: 1
  --python-bin PATH          Python executable to run inside the job. Default: python
  --openfoam-env-sh PATH     OpenFOAM env script to source before running.
  --dry-run                  Emit the sbatch script path and resolved command without submitting.
  --help, -h                 Show this help text.

Builder passthrough:
  All unrecognized arguments are forwarded to
  tools/analyze/build_ethan_case_analysis_package.py. Common examples:
    --last-n-times 5
    --time-selector 3276,3277,3278,3279
    --raw-extraction-dir PATH
    --target-ds-m 0.01
    --skip-extraction

Examples:
  bash tools/analyze/submit_ethan_case_analysis_package_sbatch.sh \
    --source-id viscosity_screening_salt_test_1_kirst_coarse_mesh \
    --output-dir tmp/2026-06-11_salt1_kirst_case_analysis_package_window4 \
    --time-selector 3276,3277,3278,3279

  bash tools/analyze/submit_ethan_case_analysis_package_sbatch.sh \
    --source-id val_salt_test_2_coarse_mesh_laminar \
    --output-dir tmp/2026-06-11_case_analysis_raw_reuse_smoke_v5 \
    --raw-extraction-dir reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction \
    --dry-run
EOF
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_PATH="$ROOT/tools/analyze/build_ethan_case_analysis_package.py"
OPENFOAM_ENV_SH_DEFAULT="${OPENFOAM13_ENV_SH:-$ROOT/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"

JOB_NAME=""
JOB_DIR=""
PARTITION="NuclearEnergy"
ACCOUNT="ASC23046"
WALLTIME="12:00:00"
NTASKS="1"
CPUS_PER_TASK="1"
PYTHON_BIN="${PYTHON_BIN:-}"
OPENFOAM_ENV_SH="$OPENFOAM_ENV_SH_DEFAULT"
DRY_RUN=0
SOURCE_ID=""
OUTPUT_DIR=""
BUILDER_ARGS=()

if [[ -z "$PYTHON_BIN" ]]; then
    if [[ -x "/usr/bin/python" ]]; then
        PYTHON_BIN="/usr/bin/python"
    else
        PYTHON_BIN="python"
    fi
fi

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
        --ntasks)
            NTASKS="$2"
            shift 2
            ;;
        --cpus-per-task)
            CPUS_PER_TASK="$2"
            shift 2
            ;;
        --python-bin)
            PYTHON_BIN="$2"
            shift 2
            ;;
        --openfoam-env-sh)
            OPENFOAM_ENV_SH="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        --source-id)
            SOURCE_ID="$2"
            BUILDER_ARGS+=("$1" "$2")
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            BUILDER_ARGS+=("$1" "$2")
            shift 2
            ;;
        *)
            BUILDER_ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ -z "$SOURCE_ID" ]]; then
    echo "Missing required builder argument: --source-id" >&2
    exit 1
fi
if [[ -z "$OUTPUT_DIR" ]]; then
    echo "Missing required builder argument: --output-dir" >&2
    exit 1
fi
if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo "Builder script not found: $SCRIPT_PATH" >&2
    exit 1
fi
if [[ ! -r "$OPENFOAM_ENV_SH" ]]; then
    echo "OpenFOAM env script not readable: $OPENFOAM_ENV_SH" >&2
    exit 1
fi

safe_source_id="${SOURCE_ID//[^A-Za-z0-9_-]/_}"
timestamp="$(date +%Y%m%dT%H%M%S)"
if [[ -z "$JOB_NAME" ]]; then
    JOB_NAME="casepkg_${safe_source_id}"
fi
if [[ -z "$JOB_DIR" ]]; then
    JOB_DIR="$ROOT/tmp/slurm_case_analysis_jobs/${timestamp}_${safe_source_id}"
fi
mkdir -p "$JOB_DIR"

SBATCH_SCRIPT="$JOB_DIR/${JOB_NAME}.sbatch"
STDOUT_PATH="$JOB_DIR/slurm-%j.out"
STDERR_PATH="$JOB_DIR/slurm-%j.err"
MPLCONFIGDIR_PATH="$ROOT/tmp/mplconfig"

command_string=""
printf -v command_string '%q ' "$PYTHON_BIN" "$SCRIPT_PATH" "${BUILDER_ARGS[@]}"
command_string="${command_string% }"

printf -v root_q '%q' "$ROOT"
printf -v env_q '%q' "$OPENFOAM_ENV_SH"
printf -v mpl_q '%q' "$MPLCONFIGDIR_PATH"

cat > "$SBATCH_SCRIPT" <<EOF
#!/bin/bash
#SBATCH -J $JOB_NAME
#SBATCH -p $PARTITION
#SBATCH -A $ACCOUNT
#SBATCH -N 1
#SBATCH -n $NTASKS
#SBATCH -c $CPUS_PER_TASK
#SBATCH -t $WALLTIME
#SBATCH -o $STDOUT_PATH
#SBATCH -e $STDERR_PATH

set -euo pipefail

cd $root_q
mkdir -p $mpl_q

export MPLCONFIGDIR=$mpl_q
export PYTHONUNBUFFERED=1
export OPENFOAM_ENV_SH=$env_q

echo "Running in: $ROOT"
echo "Using OpenFOAM env: $OPENFOAM_ENV_SH"
echo "Executing: $command_string"

$command_string
EOF

if [[ $DRY_RUN -eq 1 ]]; then
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
