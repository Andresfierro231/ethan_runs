#!/bin/bash
# launch_variant.sh — start ONE staged insulation-perturbation variant as a
# background parallel OF13 solve on the current interactive node (idev / NuclearEnergy-dev).
#
# T2 (AGENT-164). Restarts from latestTime under processors64 (collated).
# Uses the campaign Intel-MPI OF13 runtime (the runtime that produced these fields),
# pinned to a core offset so two variants can share the node.
#
# Usage: launch_variant.sh <case_dir> <ncores> <core_offset>
set -euo pipefail

CASE_DIR="$1"; NCORES="${2:-64}"; OFFSET="${3:-0}"
ENV_SH=/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh
RCWALL_LIBDIR=/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data

cd "$CASE_DIR"
mkdir -p logs

set +eu
source "$ENV_SH"
set -eu
unset FOAM_SIGFPE || true
export LD_LIBRARY_PATH="$RCWALL_LIBDIR:${LD_LIBRARY_PATH:-}"

latest_time="$(find processors64 -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \
  | awk '/^[0-9.]+$/{print}' | sort -g | tail -1)"

echo "=== $(date) launching $(basename "$CASE_DIR") ===" >> logs/log.foamRun_insulation
echo "restart latestTime=$latest_time ncores=$NCORES offset=$OFFSET" >> logs/log.foamRun_insulation
echo "foamRun=$(command -v foamRun)" >> logs/log.foamRun_insulation

# ibrun -o <offset> -n <ncores> pins this MPI job to a core range so two variants coexist.
ibrun -o "$OFFSET" -n "$NCORES" foamRun -parallel >> logs/log.foamRun_insulation 2>&1
echo "=== $(date) foamRun exited rc=$? ===" >> logs/log.foamRun_insulation
