# Case Run State Checkpoint

Date: `2026-05-29`
Case: `val_salt_test_2_coarse_mesh_laminar`

## Checkpoint

- The native OpenFOAM case under `/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar` has already been executed.
- Evidence of prior execution includes `processors64/`, `logs/log.foamRun`, and populated `postProcessing/` outputs.
- `logs/log.foamRun` shows TACC job `3139458` running `foamRun -parallel` on `May 02 2026`.
- The staged `.foam` file under `ethan_runs/staging/render_inputs/...` is a ParaView/OpenFOAM reader entrypoint only. It is not a solver run, restart, or mutation of the native case.

## Implication

- Current `ethan_runs` work is intake, extraction, join, and visualization staging on top of an existing run.
- Any future solver action should be treated explicitly as a new continuation or restart decision, not assumed from the presence of the staged `.foam` file.

## Follow-up

- Decide whether the source run ending with signal `15` indicates a normal scheduled stop or an incomplete run state.
- Decide whether a continuation to later simulation time is needed for comparison-quality reporting.
