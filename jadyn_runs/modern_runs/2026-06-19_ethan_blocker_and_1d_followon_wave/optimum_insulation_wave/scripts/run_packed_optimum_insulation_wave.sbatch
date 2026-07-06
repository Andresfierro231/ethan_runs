#!/bin/bash
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -J ethan_salt_optpack
#SBATCH -N 1
#SBATCH -n 256
#SBATCH -t 120:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/optimum_insulation_wave/slurm-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/optimum_insulation_wave/slurm-%j.err

set -euo pipefail

OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALL_LIBDIR="${RCWALLBC_LIBDIR:-/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data}"
CAMPAIGN_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/optimum_insulation_wave"
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
    printf "\n--- packed job %s start (%s, restart %s) ---\n" \
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

CASE_DIR_1="$RUNS_ROOT/salt1_jin_optins/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation"
CASE_DIR_2="$RUNS_ROOT/salt2_jin_optins/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh"
CASE_DIR_3="$RUNS_ROOT/salt3_jin_optins/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh"
CASE_DIR_4="$RUNS_ROOT/salt4_jin_optins/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"

validate_case "$CASE_DIR_1" "salt1_jin_optins"
validate_case "$CASE_DIR_2" "salt2_jin_optins"
validate_case "$CASE_DIR_3" "salt3_jin_optins"
validate_case "$CASE_DIR_4" "salt4_jin_optins"

LATEST_1="$(latest_restart_time "$CASE_DIR_1")"
LATEST_2="$(latest_restart_time "$CASE_DIR_2")"
LATEST_3="$(latest_restart_time "$CASE_DIR_3")"
LATEST_4="$(latest_restart_time "$CASE_DIR_4")"

if [[ -z "$LATEST_1" || -z "$LATEST_2" || -z "$LATEST_3" || -z "$LATEST_4" ]]; then
    echo "At least one case is missing a numeric restart time under processors64/" >&2
    exit 1
fi

echo "Packed Salt optimum wave job: $SLURM_JOB_ID"
echo "Using foamRun: $FOAMRUN_BIN"
echo "Using I_MPI_PMI_LIBRARY: $I_MPI_PMI_LIBRARY"
echo "Using RCWallBC libdir: $RCWALL_LIBDIR"

launch_case "$CASE_DIR_1" "salt1_jin_optins" "$LATEST_1"
launch_case "$CASE_DIR_2" "salt2_jin_optins" "$LATEST_2"
launch_case "$CASE_DIR_3" "salt3_jin_optins" "$LATEST_3"
launch_case "$CASE_DIR_4" "salt4_jin_optins" "$LATEST_4"

wait
