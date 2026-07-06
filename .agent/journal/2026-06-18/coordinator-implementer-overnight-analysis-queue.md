# AGENT-088 Raw Journal — Overnight Analysis Queue

## 2026-06-22 Reconstruction

- The task was still listed in `Active`, but the claimed status file was
  missing and the raw journal path did not exist.
- I reconstructed the durable record from the queue outputs that are still
  present under:
  - `tmp/2026-06-18_overnight_analysis_queue/`

## Observable queue products

- `15` case-analysis package roots exist under:
  - `tmp/2026-06-18_overnight_analysis_queue/case_analysis/`
- Each completed package preserves:
  - `README.md`
  - `analysis_manifest.json`
  - `summary.json`
- The package contents show that the queue was not a minimal hydraulic rerun
  only. It carried the full June 18 per-case additive stack:
  - matched streamwise thermal reductions
  - branch thermal summaries and support QC
  - azimuthal wall transport
  - grouped streamwise heat-loss reductions
  - boundary-layer landmarks
  - retained-time feature minor-loss summaries

## Proven submitted jobs

- Historical accounting confirms `15` completed standard Slurm jobs on
  `2026-06-19`:
  - `3245941` `casepkg_val_salt_test_2_coarse_mesh_laminar_window12`
  - `3245942` `casepkg_viscosity_screening_salt_test_1_jin_coarse_mesh`
  - `3245943` `casepkg_viscosity_screening_salt_test_1_kirst_coarse_mesh`
  - `3245944` `casepkg_viscosity_screening_salt_test_2_jin_coarse_mesh`
  - `3245945` `casepkg_viscosity_screening_salt_test_2_kirst_coarse_mesh`
  - `3245946` `casepkg_viscosity_screening_salt_test_3_jin_coarse_mesh`
  - `3245947` `casepkg_viscosity_screening_salt_test_3_kirst_coarse_mesh`
  - `3245948` `casepkg_viscosity_screening_salt_test_4_jin_coarse_mesh`
  - `3245949` `casepkg_viscosity_screening_salt_test_4_kirst_coarse_mesh`
  - `3245950` `casepkg_val_water_test_1_coarse_mesh_laminar_window12`
  - `3245951` `casepkg_val_water_test_2_coarse_mesh_laminar_window12`
  - `3245952` `casepkg_val_water_test_3_coarse_mesh_laminar_window12`
  - `3245953` `casepkg_val_water_test_4_coarse_mesh_laminar_window12`
  - `3246140` `casepkg_val_salt_test_2_coarse_mesh_laminar_window20`
  - `3246141` `casepkg_val_water_test_1_coarse_mesh_laminar_window20`
- The saved `slurm-*.out/.err` files match those `15` jobs.

## Dense-friction boundary

- Three dense-friction Slurm launchers exist under:
  - `tmp/2026-06-18_overnight_analysis_queue/dense_slurm/`
- Those launchers target:
  - `val_salt_test_2_coarse_mesh_laminar_window12`
  - `viscosity_screening_salt_test_2_jin_coarse_mesh_window12`
  - `viscosity_screening_salt_test_4_jin_coarse_mesh_window12`
- I did not find matching dense-job `slurm-*.out/.err` artifacts in the queue
  root, so the scientifically honest statement is:
  - dense-friction jobs were staged
  - standard case-analysis jobs were proven submitted and completed

## Interpretation boundary

- This queue materially improved retained-time evidence coverage for later Salt
  and Water closure-hardening work.
- The queue itself is not a new closure package and should not be described as
  if it independently defended a new `f`, `Nu`, or `K_eff` law.
- The strongest direct queue outcome is reproducible, richer per-case evidence
  in a preserved task-local tree.
