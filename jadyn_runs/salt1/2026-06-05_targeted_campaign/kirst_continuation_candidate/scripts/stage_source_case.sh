#!/bin/bash
set -euo pipefail

SOURCE_CASE="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_1_kirst_coarse_mesh"
TARGET_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt1/2026-06-05_targeted_campaign/kirst_continuation_candidate/case_stage"
TARGET_CASE="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt1/2026-06-05_targeted_campaign/kirst_continuation_candidate/case_stage/viscosity_screening_salt_test_1_kirst_coarse_mesh_continuation"

mkdir -p "$TARGET_ROOT"

if [ -e "$TARGET_CASE" ]; then
    echo "Target already exists: $TARGET_CASE" >&2
    exit 1
fi

cp -a "$SOURCE_CASE" "$TARGET_CASE"

echo "Staged writable continuation copy at: $TARGET_CASE"
echo "Next: edit only the staged copy, not the imported source."
