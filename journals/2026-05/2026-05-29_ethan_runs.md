# 2026-05-29 ethan_runs

## Checkpoint

- Workspace scaffold is in place for intake, extraction, rendering, join, and publish.
- `val_salt_test_2_coarse_mesh_laminar` is registered and has a manifest-backed local record.
- The canonical publish target for this pass is `cross_model_comparison/campaigns/2026-05-29_ethan_salt_test_2_v1`.
- The native OpenFOAM case has already been run and produced `processors64/`, `logs/log.foamRun`, and `postProcessing/` outputs.
- The `.foam` file created under `ethan_runs/staging/render_inputs/...` is only a ParaView reader entrypoint for visualization, not a solver execution artifact.

## Status

- Inventory extraction is complete for `salt_test_2`.
- QoI extraction is complete from actual `postProcessing/` outputs and `logs/log.foamRun`.
- The Ethan 2D case is joined against the canonical 1D reference row for `salt_test_2`.
- A reusable Slurm render retry path exists at `staging/render_jobs/val_salt_test_2_coarse_mesh_laminar_render.sbatch`.
- Local rendering still skips because the current case is processor-decomposed and the current runtime does not produce a renderable representation directly.
- Only one accessible Ethan case was found under the readable project scratch tree today, so the workflow is batch-ready in code but not yet validated across multiple cases.

## TODO

- Submit the staged render job if field figures are needed for this case.
- Decide whether decomposed-case visualization should standardize on MPI-enabled ParaView rendering or reconstructed staging copies.
- Register the next accessible Ethan case and rerun `python tools/run_registered_pipeline.py --all-registered`.
- Compare the Ethan-derived 2D mdot and heat-loss outputs against the trusted 2D baseline envelope before using them in paper-facing interpretation.
- Keep the joined contract mapping in sync if `cross_model_comparison` changes its canonical schema.
- Confirm whether the source run stopping with signal `15` should be treated as an expected walltime stop or an incomplete analysis state.
- Compare the observed final time `1724` against the configured `endTime 10000` and document whether restart or continuation is needed.
- Decide whether downstream reports should label this case as a completed validation sample or a partial run with usable diagnostics.

## Handoff To cross_model_comparison

- Canonical campaign already published:
  `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-05-29_ethan_salt_test_2_v1`
- Key handoff items for downstream comparison:
  - import manifest and provenance index
  - joined cross-model contract row for `salt_test_2`
  - derived 2D metrics from four mdot monitors, wall heat, PIV slab averages, and terminal temperature probes
  - solver termination context from job `3139458`
  - explicit note that the native case was already run and the staged `.foam` file is only for visualization intake
  - render blocker state and staged render retry path
- Important limitation to preserve in downstream notes:
  this is a single-case intake milestone, not yet a multi-case Ethan batch.
