#!/bin/bash
set -euo pipefail

STAGE_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch"
WORKSPACE_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs"
REGISTER="$WORKSPACE_ROOT/tools/intake/register_case.py"
MANIFEST="$WORKSPACE_ROOT/tools/intake/build_import_manifest.py"

CASES=(
  "salt/viscosity_screening_salt_test_1_jin_coarse_mesh"
  "salt/viscosity_screening_salt_test_1_kirst_coarse_mesh"
  "salt/viscosity_screening_salt_test_2_jin_coarse_mesh"
  "salt/viscosity_screening_salt_test_2_kirst_coarse_mesh"
  "salt/viscosity_screening_salt_test_3_jin_coarse_mesh"
  "salt/viscosity_screening_salt_test_3_kirst_coarse_mesh"
  "salt/viscosity_screening_salt_test_4_jin_coarse_mesh"
  "salt/viscosity_screening_salt_test_4_kirst_coarse_mesh"
  "water/val_water_test_1_coarse_mesh_laminar"
  "water/val_water_test_2_coarse_mesh_laminar"
  "water/val_water_test_3_coarse_mesh_laminar"
  "water/val_water_test_4_coarse_mesh_laminar"
)

for rel in "${CASES[@]}"; do
  path="$STAGE_ROOT/$rel"
  if [ ! -d "$path" ]; then
    echo "Missing staged case: $path" >&2
    exit 1
  fi
  echo "Registering $rel"
  python "$REGISTER"     --source-path "$path"     --source-owner "ethan_modern_runs_staged"
  source_id="$(basename "$path")"
  python "$MANIFEST"     --source-id "$source_id"     --provenance-note "Local staged copy for modern_runs intake. External origin is documented in jadyn_runs/modern_runs/2026-06-01_source_inventory/batch_manifests/first_batch_source_to_stage_map.json."
done
