#!/bin/bash
set -euo pipefail

SOURCE_ROOT="/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs"
TARGET_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch"

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

mkdir -p "$TARGET_ROOT"

for rel in "${CASES[@]}"; do
  src="$SOURCE_ROOT/$rel"
  dst="$TARGET_ROOT/$rel"
  tmp="$dst.__partial"
  marker="$dst/.stage_complete"
  mkdir -p "$(dirname "$dst")"

  if [ -f "$marker" ]; then
    echo "Skipping complete target: $dst"
    continue
  fi

  rm -rf "$tmp"
  if [ -d "$dst" ]; then
    echo "Removing incomplete target: $dst"
    rm -rf "$dst"
  fi

  echo "Staging $rel"
  rsync -a "$src/" "$tmp/"
  mkdir -p "$tmp"
  touch "$tmp/.stage_complete"
  mv "$tmp" "$dst"
done

echo "Staged first modern_runs batch under: $TARGET_ROOT"
