#!/bin/bash
#SBATCH -J ethan_box_upload
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -t 24:00:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/upload_jobs/slurm-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/upload_jobs/slurm-%j.err

set -euo pipefail

ROOT=/scratch/09748/andresfierro231/projects_scratch/ethan_runs
RCLONE_BIN=${RCLONE_BIN:-$HOME/bin/rclone}
REMOTE_ROOT='box:Andres_Obsidian_Notes_Box/tamu_flow_loop/a_tacc_analyzing_operational_data/ethans runs'
LOG_PATH="$ROOT/tmp/2026-06-16_ethan_box_upload_probe/rclone_full_upload.log"

cd "$ROOT"

echo "[ethan-box-upload] root: $ROOT"
echo "[ethan-box-upload] remote: $REMOTE_ROOT"
echo "[ethan-box-upload] log: $LOG_PATH"

test -x "$RCLONE_BIN"
test -f "$HOME/.config/rclone/rclone.conf"

"$RCLONE_BIN" copy "$ROOT" "$REMOTE_ROOT" \
  --progress \
  --log-file "$LOG_PATH" \
  --log-level INFO \
  --checkers 16 \
  --transfers 8 \
  --exclude '.git/**' \
  --exclude '.agent/**' \
  --exclude '.agents/**' \
  --exclude '.codex/**' \
  --exclude 'cache/**' \
  --exclude 'figures/**' \
  --exclude 'figures_rendered/**' \
  --exclude 'linked_cases/**' \
  --exclude 'tmp/**' \
  --exclude 'tmp_extract/**' \
  --exclude '__pycache__/**' \
  --exclude '.pytest_cache/**'
