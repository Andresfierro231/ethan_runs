#!/bin/bash
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH -n 64

set -euo pipefail

CASE_DIR="${CASE_DIR:-}"
CASE_LABEL="${CASE_LABEL:-unnamed_case}"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALL_LIBDIR="${RCWALLBC_LIBDIR:-/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data}"

if [[ -z "$CASE_DIR" ]]; then
    echo "Set CASE_DIR to the continuation case root before submitting." >&2
    exit 1
fi
if [[ ! -d "$CASE_DIR" ]]; then
    echo "CASE_DIR does not exist: $CASE_DIR" >&2
    exit 1
fi
if [[ ! -d "$CASE_DIR/0" ]]; then
    echo "Expected 0/ directory missing under: $CASE_DIR" >&2
    exit 1
fi
if [[ ! -d "$CASE_DIR/constant" ]]; then
    echo "Expected constant/ directory missing under: $CASE_DIR" >&2
    exit 1
fi
if [[ ! -d "$CASE_DIR/system" ]]; then
    echo "Expected system/ directory missing under: $CASE_DIR" >&2
    exit 1
fi
if [[ ! -r "$CASE_DIR/system/controlDict" ]]; then
    echo "Expected readable system/controlDict missing under: $CASE_DIR" >&2
    exit 1
fi
if [[ ! -r "$OPENFOAM_ENV_SH" ]]; then
    echo "OpenFOAM env script not readable: $OPENFOAM_ENV_SH" >&2
    exit 1
fi
if [[ ! -r "$RCWALL_LIBDIR/libRCWallBC.so" ]]; then
    echo "Missing libRCWallBC.so under: $RCWALL_LIBDIR" >&2
    exit 1
fi
if [[ ! -d "$CASE_DIR/processors64" ]]; then
    echo "Expected decomposed restart state missing under: $CASE_DIR/processors64" >&2
    exit 1
fi

cd "$CASE_DIR"
mkdir -p logs

latest_time="$(
    find processors64 -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \
    | awk '/^[0-9.]+$/ {print}' \
    | sort -g \
    | tail -1
)"
if [[ -z "$latest_time" ]]; then
    echo "No numeric latest restart time found under: $CASE_DIR/processors64" >&2
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

echo "Case label: $CASE_LABEL"
echo "Case dir: $CASE_DIR"
echo "Restarting from latest processor time: $latest_time"
echo "Using env script: $OPENFOAM_ENV_SH"
echo "Using I_MPI_PMI_LIBRARY: $I_MPI_PMI_LIBRARY"
echo "Using foamRun: $FOAMRUN_BIN"
echo "Using RCWallBC libdir: $RCWALL_LIBDIR"

printf "\n--- job %s start (%s) ---\n" "$SLURM_JOB_ID" "$CASE_LABEL" >> logs/log.foamRun_continuation
srun --mpi=pmi2 "$FOAMRUN_BIN" -parallel >> logs/log.foamRun_continuation 2>&1
