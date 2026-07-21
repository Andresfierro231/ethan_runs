#!/bin/bash
#SBATCH -p normal
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH -n 128
#SBATCH -t 48:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/slurm-%x-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/slurm-%x-%j.err

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAMPAIGN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALL_LIBDIR="${RCWALLBC_LIBDIR:-$CAMPAIGN_ROOT/runtime_libs}"
CASE_DIR_1="${CASE_DIR_1:-}"
CASE_DIR_2="${CASE_DIR_2:-}"
CASE_LABEL_1="${CASE_LABEL_1:-case_1}"
CASE_LABEL_2="${CASE_LABEL_2:-case_2}"

validate_case() {
    local case_dir="$1"
    local case_label="$2"
    if [[ -z "$case_dir" || -z "$case_label" ]]; then
        echo "Each packed slot requires CASE_DIR_n and CASE_LABEL_n." >&2
        exit 1
    fi
    if [[ ! -d "$case_dir/0" || ! -d "$case_dir/constant" || ! -d "$case_dir/system" || ! -r "$case_dir/system/controlDict" ]]; then
        echo "[$case_label] staged case is incomplete: $case_dir" >&2
        exit 1
    fi
}

latest_restart_time() {
    local case_dir="$1"
    find "$case_dir/processors64" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | awk '/^[0-9.]+$/ {print}' | sort -g | tail -1
}

launch_case() {
    local case_dir="$1"
    local case_label="$2"
    local latest_time="$3"
    mkdir -p "$case_dir/logs"
    printf "\n--- normal packed job %s start (%s, restart %s) ---\n" "$SLURM_JOB_ID" "$case_label" "$latest_time" >> "$case_dir/logs/log.foamRun_continuation"
    srun \
        --exclusive \
        --exact \
        --nodes=1 \
        --ntasks=64 \
        --cpu-bind=cores \
        --distribution=block:block \
        --chdir="$case_dir" \
        --mpi=pmi2 \
        "$FOAMRUN_BIN" -parallel >> "$case_dir/logs/log.foamRun_continuation" 2>&1 &
}

if [[ ! -r "$OPENFOAM_ENV_SH" ]]; then
    echo "OpenFOAM env script not readable: $OPENFOAM_ENV_SH" >&2
    exit 1
fi
if [[ ! -r "$RCWALL_LIBDIR/libRCWallBC.so" ]]; then
    echo "Missing libRCWallBC.so under: $RCWALL_LIBDIR" >&2
    exit 1
fi

set +eu
source "$OPENFOAM_ENV_SH"
source_status=$?
set -eu
if [[ $source_status -ne 0 ]]; then
    echo "Failed to source $OPENFOAM_ENV_SH" >&2
    exit "$source_status"
fi

unset FOAM_SIGFPE
export OMP_NUM_THREADS=1
export LD_LIBRARY_PATH="$RCWALL_LIBDIR:${LD_LIBRARY_PATH:-}"
export I_MPI_PMI_LIBRARY="${I_MPI_PMI_LIBRARY:-/usr/lib64/libpmi2.so}"
if [[ ! -r "$I_MPI_PMI_LIBRARY" ]]; then
    echo "I_MPI_PMI_LIBRARY not readable: $I_MPI_PMI_LIBRARY" >&2
    exit 1
fi

FOAMRUN_BIN="$(command -v foamRun || true)"
if [[ -z "$FOAMRUN_BIN" || ! -x "$FOAMRUN_BIN" ]]; then
    echo "foamRun not found after sourcing runtime" >&2
    exit 1
fi

ensure_processors64() {
    local case_dir="$1"
    local case_label="$2"
    if [[ -d "$case_dir/processors64" ]]; then
        return
    fi
    if [[ ! -r "$case_dir/SOURCE_PROCESSORS64.txt" ]]; then
        echo "[$case_label] missing processors64/ and SOURCE_PROCESSORS64.txt: $case_dir" >&2
        exit 1
    fi
    local source_processors
    source_processors="$(tr -d '
' < "$case_dir/SOURCE_PROCESSORS64.txt")"
    if [[ ! -d "$source_processors" ]]; then
        echo "[$case_label] source processors64 dir not found: $source_processors" >&2
        exit 1
    fi
    echo "[$case_label] populating processors64 from $source_processors"
    cp -a "$source_processors" "$case_dir/processors64"
}

validate_case "$CASE_DIR_1" "$CASE_LABEL_1"
validate_case "$CASE_DIR_2" "$CASE_LABEL_2"
ensure_processors64 "$CASE_DIR_1" "$CASE_LABEL_1"
ensure_processors64 "$CASE_DIR_2" "$CASE_LABEL_2"
LATEST_1="$(latest_restart_time "$CASE_DIR_1")"
LATEST_2="$(latest_restart_time "$CASE_DIR_2")"
if [[ -z "$LATEST_1" || -z "$LATEST_2" ]]; then
    echo "At least one packed case is missing a numeric restart time under processors64/" >&2
    exit 1
fi

echo "Packed two-case normal job: $SLURM_JOB_ID"
echo "Using foamRun: $FOAMRUN_BIN"
echo "Using RCWallBC libdir: $RCWALL_LIBDIR"
echo "Using cases: $CASE_LABEL_1, $CASE_LABEL_2"

launch_case "$CASE_DIR_1" "$CASE_LABEL_1" "$LATEST_1"
launch_case "$CASE_DIR_2" "$CASE_LABEL_2" "$LATEST_2"

wait
