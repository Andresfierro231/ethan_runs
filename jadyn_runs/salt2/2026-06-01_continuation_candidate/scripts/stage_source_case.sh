#!/bin/bash
set -euo pipefail

SOURCE_CASE="/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar"
TARGET_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage"
TARGET_CASE="$TARGET_ROOT/val_salt_test_2_coarse_mesh_laminar_continuation"

mkdir -p "$TARGET_ROOT"

if [ -e "$TARGET_CASE" ]; then
    echo "Target already exists: $TARGET_CASE" >&2
    exit 1
fi

rsync -a "$SOURCE_CASE/" "$TARGET_CASE/"

echo "Staged writable continuation copy at: $TARGET_CASE"
echo "Next: edit only the staged copy, not the imported source."
