#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  run_openfoam_case.sh --case-dir CASE_DIR [options] [--] [command...]

Purpose:
  Source a selected OpenFOAM runtime, validate a staged case layout,
  and execute an OpenFOAM command from the case directory.

Defaults:
  command         foamRun -parallel
  log-path        CASE_DIR/logs/log.foamRun_continuation
  mpi-mode        pmi2
  decomp-dir      processors64
  env script      $OPENFOAM13_ENV_SH or Ethan's OF13 wrapper
  rcwall libdir   $RCWALLBC_LIBDIR or Ethan's shared wall-BC path
  log mode        append
  launch mode     srun

Options:
  --case-dir PATH         Case directory to run from.
  --decomp-dir PATH       Decomposed restart directory relative to CASE_DIR or absolute.
  --log-path PATH         Log file to append or truncate before the run.
  --mpi-mode MODE         MPI mode passed to srun.
  --openfoam-env-sh PATH  OpenFOAM env script to source.
  --rcwall-libdir PATH    Directory containing libRCWallBC.so.
  --extra-ld-library PATH Extra library directory prepended after rcwall libdir. Repeatable.
  --no-srun               Run the command directly instead of through srun.
  --truncate-log          Truncate the log before writing instead of appending.
  --skip-rcwall-check     Skip the libRCWallBC.so readability check.
  --dry-run               Print the resolved launch configuration and exit.
  --help, -h              Show this help text.

Examples:
  run_openfoam_case.sh --case-dir /path/to/case
  run_openfoam_case.sh --case-dir /path/to/case --no-srun -- foamRun -parallel
  run_openfoam_case.sh --case-dir /path/to/case --decomp-dir processors128 --openfoam-env-sh /path/to/env.sh
EOF
}

CASE_DIR=""
DECOMP_DIR="processors64"
LOG_PATH=""
MPI_MODE="pmi2"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALL_LIBDIR="${RCWALLBC_LIBDIR:-/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data}"
USE_SRUN=1
TRUNCATE_LOG=0
SKIP_RCWALL_CHECK=0
DRY_RUN=0
EXTRA_LD_LIBS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --case-dir)
            CASE_DIR=$2
            shift 2
            ;;
        --decomp-dir)
            DECOMP_DIR=$2
            shift 2
            ;;
        --log-path)
            LOG_PATH=$2
            shift 2
            ;;
        --mpi-mode)
            MPI_MODE=$2
            shift 2
            ;;
        --openfoam-env-sh)
            OPENFOAM_ENV_SH=$2
            shift 2
            ;;
        --rcwall-libdir)
            RCWALL_LIBDIR=$2
            shift 2
            ;;
        --extra-ld-library)
            EXTRA_LD_LIBS+=("$2")
            shift 2
            ;;
        --no-srun)
            USE_SRUN=0
            shift
            ;;
        --truncate-log)
            TRUNCATE_LOG=1
            shift
            ;;
        --skip-rcwall-check)
            SKIP_RCWALL_CHECK=1
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
        --)
            shift
            break
            ;;
        *)
            break
            ;;
    esac
done

if [[ -z "$CASE_DIR" ]]; then
    usage >&2
    exit 1
fi

if [[ $# -eq 0 ]]; then
    set -- foamRun -parallel
fi

if [[ ! -d "$CASE_DIR" ]]; then
    echo "Case directory not found: $CASE_DIR" >&2
    exit 1
fi
if [[ ! -r "$OPENFOAM_ENV_SH" ]]; then
    echo "OpenFOAM env script not readable: $OPENFOAM_ENV_SH" >&2
    exit 1
fi
if [[ $SKIP_RCWALL_CHECK -eq 0 && ! -r "$RCWALL_LIBDIR/libRCWallBC.so" ]]; then
    echo "Missing libRCWallBC.so under: $RCWALL_LIBDIR" >&2
    exit 1
fi

if [[ "$DECOMP_DIR" != /* ]]; then
    DECOMP_PATH="$CASE_DIR/$DECOMP_DIR"
else
    DECOMP_PATH="$DECOMP_DIR"
fi
if [[ ! -d "$DECOMP_PATH" ]]; then
    echo "Expected decomposed restart state missing under: $DECOMP_PATH" >&2
    exit 1
fi

if [[ -z "$LOG_PATH" ]]; then
    LOG_PATH="$CASE_DIR/logs/log.$1"
fi
mkdir -p "$(dirname "$LOG_PATH")"

cd "$CASE_DIR"
set +eu
source "$OPENFOAM_ENV_SH"
source_status=$?
set -eu
if [[ $source_status -ne 0 ]]; then
    echo "Failed to source $OPENFOAM_ENV_SH" >&2
    exit "$source_status"
fi

unset FOAM_SIGFPE
LD_PATH_COMPONENTS=()
if [[ $SKIP_RCWALL_CHECK -eq 0 ]]; then
    LD_PATH_COMPONENTS+=("$RCWALL_LIBDIR")
fi
for extra_path in "${EXTRA_LD_LIBS[@]}"; do
    LD_PATH_COMPONENTS+=("$extra_path")
done
if [[ ${#LD_PATH_COMPONENTS[@]} -gt 0 ]]; then
    export LD_LIBRARY_PATH="$(IFS=:; echo "${LD_PATH_COMPONENTS[*]}"):${LD_LIBRARY_PATH:-}"
fi
export I_MPI_PMI_LIBRARY="${I_MPI_PMI_LIBRARY:-/usr/lib64/libpmi2.so}"
if [[ $USE_SRUN -eq 1 && ! -r "$I_MPI_PMI_LIBRARY" ]]; then
    echo "I_MPI_PMI_LIBRARY not readable: $I_MPI_PMI_LIBRARY" >&2
    exit 1
fi

APP_BIN="$(command -v "$1" || true)"
if [[ -z "$APP_BIN" || ! -x "$APP_BIN" ]]; then
    echo "Application not found after sourcing runtime: $1" >&2
    exit 1
fi

latest_time=$(find "$DECOMP_PATH" -mindepth 1 -maxdepth 1 -type d | xargs -n1 basename | awk '/^[0-9.]+$/ {print}' | sort -g | tail -1)
launcher="direct"
if [[ $USE_SRUN -eq 1 ]]; then
    launcher="srun --mpi=$MPI_MODE"
fi

echo "Case directory: $CASE_DIR"
echo "Decomposed directory: $DECOMP_PATH"
echo "Restarting from latest processor time: ${latest_time:-unknown}"
echo "Using env script: $OPENFOAM_ENV_SH"
echo "Using launcher: $launcher"
echo "Using application: $APP_BIN ${*:2}"
echo "Using log path: $LOG_PATH"
echo "Using RCWallBC libdir: ${RCWALL_LIBDIR:-skipped}"

if [[ $DRY_RUN -eq 1 ]]; then
    exit 0
fi

if [[ $TRUNCATE_LOG -eq 1 ]]; then
    : > "$LOG_PATH"
fi
printf "
--- job %s start ---
" "${SLURM_JOB_ID:-manual}" >> "$LOG_PATH"
if [[ $USE_SRUN -eq 1 ]]; then
    srun --mpi="$MPI_MODE" "$APP_BIN" "${@:2}" >> "$LOG_PATH" 2>&1
else
    "$APP_BIN" "${@:2}" >> "$LOG_PATH" 2>&1
fi
