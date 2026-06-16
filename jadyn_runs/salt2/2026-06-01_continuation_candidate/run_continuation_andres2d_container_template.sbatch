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
OF_IMAGE="/corral-secure/utexas/ASC23046/Images/openfoam-default_latest.sif"
OF_BASHRC="/openfoam/bash.rc"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data}"
APPTAINER_BIN="/opt/apps/tacc-apptainer/1.3.3/bin/apptainer"

if [[ ! -x "$APPTAINER_BIN" ]]; then
    echo "Apptainer binary missing: $APPTAINER_BIN" >&2
    exit 1
fi
if [[ ! -r "$OF_IMAGE" ]]; then
    echo "OpenFOAM image missing: $OF_IMAGE" >&2
    exit 1
fi
if [[ ! -d "$CASE_DIR/processors64" ]]; then
    echo "Expected decomposed restart state missing under: $CASE_DIR/processors64" >&2
    exit 1
fi
if [[ ! -r "$RCWALLBC_LIBDIR/libRCWallBC.so" ]]; then
    echo "Missing libRCWallBC.so under: $RCWALLBC_LIBDIR" >&2
    exit 1
fi

cd "$CASE_DIR"
mkdir -p logs

latest_time=$(find processors64 -mindepth 1 -maxdepth 1 -type d | xargs -n1 basename | awk '/^[0-9.]+$/ {print}' | sort -g | tail -1)
echo "Restarting from latest processor time: ${latest_time:-unknown}"
echo "Using andres_2d container image: $OF_IMAGE"
echo "Binding RCWallBC libdir: $RCWALLBC_LIBDIR"

export SINGULARITY_BIND="$CASE_DIR:$CASE_DIR,$RCWALLBC_LIBDIR:$RCWALLBC_LIBDIR"
export APPTAINER_BIND="$SINGULARITY_BIND"

srun "$APPTAINER_BIN" exec --cleanenv \
    --bind "$CASE_DIR:$CASE_DIR" \
    --bind "$RCWALLBC_LIBDIR:$RCWALLBC_LIBDIR" \
    "$OF_IMAGE" \
    /bin/bash --noprofile --norc -c "source '$OF_BASHRC' && \
set -eo pipefail && \
export LD_LIBRARY_PATH='$RCWALLBC_LIBDIR':\${LD_LIBRARY_PATH:-} && \
command -v foamRun && \
cd '$CASE_DIR' && \
foamRun -parallel >> logs/log.foamRun_continuation 2>&1"
