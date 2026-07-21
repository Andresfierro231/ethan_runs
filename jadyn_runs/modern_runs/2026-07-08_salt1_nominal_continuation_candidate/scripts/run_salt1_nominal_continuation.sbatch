#!/bin/bash
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH -n 64
#SBATCH -t 120:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/slurm-%x-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/slurm-%x-%j.err

set -euo pipefail

ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs"
CAMPAIGN="$ROOT/jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate"
CASE_DIR="${CASE_DIR:-$CAMPAIGN/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation}"
CASE_LABEL="${CASE_LABEL:-salt1_jin_nominal_continuation_corrected}"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-$ROOT/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-$ROOT/jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runtime_libs}"

if [[ ! -r "$OPENFOAM_ENV_SH" ]]; then
    echo "OpenFOAM env script not readable: $OPENFOAM_ENV_SH" >&2
    exit 1
fi
if [[ ! -r "$RCWALLBC_LIBDIR/libRCWallBC.so" ]]; then
    echo "Missing libRCWallBC.so under: $RCWALLBC_LIBDIR" >&2
    exit 1
fi
if [[ ! -d "$CASE_DIR/0" || ! -d "$CASE_DIR/constant" || ! -d "$CASE_DIR/system" ]]; then
    echo "Staged case is incomplete: $CASE_DIR" >&2
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
export LD_LIBRARY_PATH="$RCWALLBC_LIBDIR:${LD_LIBRARY_PATH:-}"
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
    if [[ -d "$CASE_DIR/processors64" ]]; then
        return
    fi
    if [[ ! -r "$CASE_DIR/SOURCE_PROCESSORS64.txt" ]]; then
        echo "Missing processors64/ and SOURCE_PROCESSORS64.txt: $CASE_DIR" >&2
        exit 1
    fi
    local source_processors
    source_processors="$(tr -d '\n' < "$CASE_DIR/SOURCE_PROCESSORS64.txt")"
    if [[ ! -d "$source_processors" ]]; then
        echo "Source processors64 dir not found: $source_processors" >&2
        exit 1
    fi
    cp -a "$source_processors" "$CASE_DIR/processors64"
}

latest_restart_time() {
    find "$CASE_DIR/processors64" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | awk '/^[0-9.]+$/ {print}' | sort -g | tail -1
}

ensure_processors64
LATEST="$(latest_restart_time)"
if [[ -z "$LATEST" ]]; then
    echo "No numeric restart time found under $CASE_DIR/processors64" >&2
    exit 1
fi

mkdir -p "$CASE_DIR/logs"
{
    echo
    echo "--- Salt1 nominal continuation job ${SLURM_JOB_ID} start (${CASE_LABEL}, restart ${LATEST}) ---"
    echo "Using foamRun: $FOAMRUN_BIN"
    echo "Using RCWallBC libdir: $RCWALLBC_LIBDIR"
} >> "$CASE_DIR/logs/log.foamRun_salt1_nominal_continuation"

srun --exclusive --exact --nodes=1 --ntasks=64 --cpu-bind=cores --distribution=block:block --chdir="$CASE_DIR" --mpi=pmi2 \
    "$FOAMRUN_BIN" -parallel >> "$CASE_DIR/logs/log.foamRun_salt1_nominal_continuation" 2>&1
