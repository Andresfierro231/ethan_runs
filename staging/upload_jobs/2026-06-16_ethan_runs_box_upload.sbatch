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
VENV_ROOT=${SLURM_TMPDIR:-/tmp}/${USER}_box_cli_env
MANIFEST_PATH="$ROOT/tmp/2026-06-16_ethan_box_upload_probe/execute_manifest.json"
PYTHON_BIN=${PYTHON_BIN:-python3.11}

cd "$ROOT"

echo "[ethan-box-upload] root: $ROOT"
echo "[ethan-box-upload] venv: $VENV_ROOT"
echo "[ethan-box-upload] manifest: $MANIFEST_PATH"

if [[ ! -x "$VENV_ROOT/bin/python" ]]; then
  echo "[ethan-box-upload] creating virtualenv"
  "$PYTHON_BIN" -m venv "$VENV_ROOT"
  "$VENV_ROOT/bin/pip" install --upgrade pip
  "$VENV_ROOT/bin/pip" install box-sdk-gen requests pyjwt
else
  echo "[ethan-box-upload] reusing existing virtualenv"
fi

"$VENV_ROOT/bin/python" tools/publish/upload_ethan_runs_to_box.py \
  --execute \
  --overwrite-changed \
  --source-root "$ROOT" \
  --box-folder-id 385169164073 \
  --remote-subfolder "ethans runs" \
  --manifest-path "$MANIFEST_PATH"
