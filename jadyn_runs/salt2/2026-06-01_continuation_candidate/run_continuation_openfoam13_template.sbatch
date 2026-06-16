#!/bin/bash
#SBATCH -J jadyn_salt2_cont
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH -n 64
#SBATCH -t 120:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/slurm-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/slurm-%j.err

set -euo pipefail

CASE_DIR="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALL_LIBDIR="${RCWALLBC_LIBDIR:-}"

if [[ -z "$OPENFOAM_ENV_SH" ]]; then
    echo "Set OPENFOAM13_ENV_SH to a readable OpenFOAM 13 env script before submitting." >&2
    exit 1
fi
if [[ ! -r "$OPENFOAM_ENV_SH" ]]; then
    echo "OpenFOAM env script not readable: $OPENFOAM_ENV_SH" >&2
    exit 1
fi
if [[ -z "$RCWALL_LIBDIR" ]]; then
    echo "Set RCWALLBC_LIBDIR to the directory containing libRCWallBC.so before submitting." >&2
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

latest_time=$(find processors64 -mindepth 1 -maxdepth 1 -type d | xargs -n1 basename | awk '/^[0-9.]+$/ {print}' | sort -g | tail -1)
echo "Restarting from latest processor time: ${latest_time:-unknown}"
echo "Using env script: $OPENFOAM_ENV_SH"
echo "Using MPI_ROOT: $MPI_ROOT"
echo "Using I_MPI_PMI_LIBRARY: $I_MPI_PMI_LIBRARY"
echo "Using foamRun: $FOAMRUN_BIN"
echo "Using RCWallBC libdir: $RCWALL_LIBDIR"

srun --mpi=pmi2 "$FOAMRUN_BIN" -parallel >> logs/log.foamRun_continuation 2>&1
