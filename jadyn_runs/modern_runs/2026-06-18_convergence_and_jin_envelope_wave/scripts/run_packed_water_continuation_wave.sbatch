#!/bin/bash
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -J ethan_water_contpilot
#SBATCH -N 1
#SBATCH -n 256
#SBATCH -t 72:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/slurm-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/slurm-%j.err

set -euo pipefail

OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALL_LIBDIR="${RCWALLBC_LIBDIR:-/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data}"
CAMPAIGN_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave"
RUNS_ROOT="$CAMPAIGN_ROOT/runs"

validate_case() {
    local case_dir="$1"
    local case_label="$2"

    if [[ ! -d "$case_dir" ]]; then
        echo "[$case_label] missing case dir: $case_dir" >&2
        exit 1
    fi
    if [[ ! -d "$case_dir/0" ]]; then
        echo "[$case_label] missing 0/: $case_dir" >&2
        exit 1
    fi
    if [[ ! -d "$case_dir/constant" ]]; then
        echo "[$case_label] missing constant/: $case_dir" >&2
        exit 1
    fi
    if [[ ! -d "$case_dir/system" ]]; then
        echo "[$case_label] missing system/: $case_dir" >&2
        exit 1
    fi
    if [[ ! -r "$case_dir/system/controlDict" ]]; then
        echo "[$case_label] missing readable system/controlDict: $case_dir" >&2
        exit 1
    fi
    if [[ ! -d "$case_dir/processors64" ]]; then
        echo "[$case_label] missing processors64/: $case_dir" >&2
        exit 1
    fi
}

latest_restart_time() {
    local case_dir="$1"
    find "$case_dir/processors64" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \
        | awk '/^[0-9.]+$/ {print}' \
        | sort -g \
        | tail -1
}

launch_case() {
    local case_dir="$1"
    local case_label="$2"
    local latest_time="$3"

    mkdir -p "$case_dir/logs"

    echo "Launching $case_label from $case_dir at restart time $latest_time"
    printf "\n--- packed pilot job %s start (%s, restart %s) ---\n" \
        "$SLURM_JOB_ID" "$case_label" "$latest_time" >> "$case_dir/logs/log.foamRun_continuation"

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

CASE_DIR_1="$RUNS_ROOT/water1/case_stage/val_water_test_1_coarse_mesh_laminar_continuation"
CASE_DIR_2="$RUNS_ROOT/water2/case_stage/val_water_test_2_coarse_mesh_laminar_continuation"
CASE_DIR_3="$RUNS_ROOT/water3/case_stage/val_water_test_3_coarse_mesh_laminar_continuation"
CASE_DIR_4="$RUNS_ROOT/water4/case_stage/val_water_test_4_coarse_mesh_laminar_continuation"

validate_case "$CASE_DIR_1" "water1"
validate_case "$CASE_DIR_2" "water2"
validate_case "$CASE_DIR_3" "water3"
validate_case "$CASE_DIR_4" "water4"

LATEST_1="$(latest_restart_time "$CASE_DIR_1")"
LATEST_2="$(latest_restart_time "$CASE_DIR_2")"
LATEST_3="$(latest_restart_time "$CASE_DIR_3")"
LATEST_4="$(latest_restart_time "$CASE_DIR_4")"

if [[ -z "$LATEST_1" || -z "$LATEST_2" || -z "$LATEST_3" || -z "$LATEST_4" ]]; then
    echo "At least one Water continuation case is missing a numeric restart time under processors64/" >&2
    exit 1
fi

echo "Packed Water continuation pilot job: $SLURM_JOB_ID"
echo "Using foamRun: $FOAMRUN_BIN"
echo "Using I_MPI_PMI_LIBRARY: $I_MPI_PMI_LIBRARY"
echo "Using RCWallBC libdir: $RCWALL_LIBDIR"
echo "This is the requested 4-per-node Water continuation pilot."

launch_case "$CASE_DIR_1" "water1" "$LATEST_1"
launch_case "$CASE_DIR_2" "water2" "$LATEST_2"
launch_case "$CASE_DIR_3" "water3" "$LATEST_3"
launch_case "$CASE_DIR_4" "water4" "$LATEST_4"

wait
