# Workspace Status

Date: `2026-05-29`

## Completed

- Registered `val_salt_test_2_coarse_mesh_laminar` by manifest and local symlink.
- Extracted inventory, QoI, solver-log status, and postProcessing-derived validation metrics.
- Joined the Ethan 2D case against the canonical `salt_test_2` 1D reference contract row.
- Published the canonical campaign package into `cross_model_comparison`.
- Staged a reusable Slurm render job for the decomposed OpenFOAM case.

## Current blocker

- Only one accessible Ethan case was found under the readable project scratch tree.
- Direct field rendering still skips in the local runtime because the source case is processor-decomposed.

## Action path

- Submit `staging/render_jobs/val_salt_test_2_coarse_mesh_laminar_render.sbatch` when field figures are required.
- Register the next accessible Ethan case and rerun `python tools/run_registered_pipeline.py --all-registered`.
