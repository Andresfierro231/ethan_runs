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
JOB_STAGE_ROOT="$CAMPAIGN_ROOT/job_staged_runs/$SLURM_JOB_ID"

stage_case() {
    local case_key="$1"
    local source_case="$2"
    local target_case="$3"
    local target_outer_m="$4"

    if [[ ! -d "$source_case" ]]; then
        echo "[$case_key] missing source case: $source_case" >&2
        exit 1
    fi
    if [[ -e "$target_case" ]]; then
        echo "[$case_key] target already exists: $target_case" >&2
        exit 1
    fi

    mkdir -p "$(dirname "$target_case")"
    cp -a "$source_case" "$target_case"

    if [[ ! -d "$target_case/0" || ! -d "$target_case/constant" || ! -d "$target_case/system" || ! -d "$target_case/processors64" ]]; then
        echo "[$case_key] staged target missing required restart directories: $target_case" >&2
        exit 1
    fi

    perl -0pi -e "s/0\\.035559999999999994/${target_outer_m}/g" "$target_case/0/T"

    if grep -Fq "0.035559999999999994" "$target_case/0/T"; then
        echo "[$case_key] baseline outer insulation remains in $target_case/0/T" >&2
        exit 1
    fi
    if ! grep -Fq "$target_outer_m" "$target_case/0/T"; then
        echo "[$case_key] target outer insulation value missing in $target_case/0/T" >&2
        exit 1
    fi

    echo "[$case_key] staged target: $target_case"
}

validate_case() {
    local case_dir="$1"
    local case_label="$2"

    if [[ ! -d "$case_dir/0" || ! -d "$case_dir/constant" || ! -d "$case_dir/system" || ! -d "$case_dir/processors64" ]]; then
        echo "[$case_label] missing required case directories after staging: $case_dir" >&2
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

mkdir -p "$JOB_STAGE_ROOT"

SOURCE_1="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation"
SOURCE_2="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh"
SOURCE_3="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_3_jin_coarse_mesh"
SOURCE_4="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"

CASE_DIR_1="$JOB_STAGE_ROOT/salt1_jin_optins/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation"
CASE_DIR_2="$JOB_STAGE_ROOT/salt2_jin_optins/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh"
CASE_DIR_3="$JOB_STAGE_ROOT/salt3_jin_optins/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh"
CASE_DIR_4="$JOB_STAGE_ROOT/salt4_jin_optins/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"

stage_case "salt1_jin_optins" "$SOURCE_1" "$CASE_DIR_1" "0.060960000000"
stage_case "salt2_jin_optins" "$SOURCE_2" "$CASE_DIR_2" "0.043919140000"
stage_case "salt3_jin_optins" "$SOURCE_3" "$CASE_DIR_3" "0.042407840000"
stage_case "salt4_jin_optins" "$SOURCE_4" "$CASE_DIR_4" "0.046423580000"

validate_case "$CASE_DIR_1" "salt1_jin_optins"
validate_case "$CASE_DIR_2" "salt2_jin_optins"
validate_case "$CASE_DIR_3" "salt3_jin_optins"
validate_case "$CASE_DIR_4" "salt4_jin_optins"

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

LATEST_1="$(latest_restart_time "$CASE_DIR_1")"
LATEST_2="$(latest_restart_time "$CASE_DIR_2")"
LATEST_3="$(latest_restart_time "$CASE_DIR_3")"
LATEST_4="$(latest_restart_time "$CASE_DIR_4")"

if [[ -z "$LATEST_1" || -z "$LATEST_2" || -z "$LATEST_3" || -z "$LATEST_4" ]]; then
    echo "At least one case is missing a numeric restart time under processors64/" >&2
    exit 1
fi

echo "Packed Salt optimum self-staging wave job: $SLURM_JOB_ID"
echo "Job stage root: $JOB_STAGE_ROOT"
echo "Using foamRun: $FOAMRUN_BIN"
echo "Using I_MPI_PMI_LIBRARY: $I_MPI_PMI_LIBRARY"
echo "Using RCWallBC libdir: $RCWALL_LIBDIR"

launch_case "$CASE_DIR_1" "salt1_jin_optins" "$LATEST_1"
launch_case "$CASE_DIR_2" "salt2_jin_optins" "$LATEST_2"
launch_case "$CASE_DIR_3" "salt3_jin_optins" "$LATEST_3"
launch_case "$CASE_DIR_4" "salt4_jin_optins" "$LATEST_4"

wait
