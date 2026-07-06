# Weekly Status Update — 2026-06-01

## Scope

This package summarizes the Ethan-run intake and analysis work completed during the current week, with focus on `val_salt_test_2_coarse_mesh_laminar` (`salt_test_2`) and the new `modern_runs` source campaign.

## Executive Status

- The intake and comparison workflow is now proven on one imported Ethan case end-to-end: intake, manifesting, extraction, cross-model join, and publication scaffolding are in place.
- `salt_test_2` is useful as a diagnostic case, but it is not yet defensible as a converged validation-grade CFD sample.
- The continuation path for `salt_test_2` has now been operationalized and submitted as Slurm job `3200407`.
- The multi-case campaign has advanced from one-case intake to real batch staging: the first `modern_runs` staging job `3200181` is running, and dependent registration job `3200186` is queued.

## What Was Accomplished This Week

- Registered and documented the imported `salt_test_2` case and published its first canonical comparison package.
- Confirmed the staged `.foam` artifact is only a visualization entrypoint, not a solver product.
- Extracted mdot, wall-heat, PIV-slab, and probe QoIs from real `postProcessing/` output and joined them against the trusted cross-model reference row.
- Determined that the source run stopped early at about simulation time `1724.714285714 s` despite `endTime 10000`.
- Performed a convergence-specific reassessment using the case's own coded stop logic and showed that the heat-loss-related behavior is still drifting.
- Built a detailed setup dossier for geometry, mesh, numerics, boundary conditions, TP/TW measurement locations, and comparison hooks needed for later 1D-vs-3D mapping.
- Investigated ParaView rendering and narrowed the current visualization blocker to decomposed-case/runtime behavior rather than missing scheduler access.
- Inventoried the external `modern_runs` tree and separated it into immediately extractable salt/water-laminar cases versus setup-only water `kOmegaSSTLM` cases.
- Submitted the first multi-case staging workflow for 8 salt and 4 water-laminar cases.
- Located the previously missing runtime dependency `libRCWallBC.so` and used it to submit the next salt2 continuation chunk.

## Current Results

### Salt2 numerical state

- Current imported source endpoint: `t = 1724.714285714 s`
- File-level target end time: `10000 s`
- Mean absolute mdot across 4 monitor planes: `0.01361622898 kg/s`
- Final derived total wall heat: `0.660044 W`
- Final PIV-slab mean velocity magnitude: `0.02426224071 m/s`
- Final PIV-slab temperature: `456.34893 K`
- Final six-probe mean temperature: `452.58333 K`

### Steady-state gap

- The active limiter is still `dTsigma`, not `dTmean` or `dUmean`.
- Current `dTsigma = 7.73823203e-3` versus target `1.0e-4`.
- That means the current stop metric is still `77.4x` above the case-defined tolerance.
- Exponential fit to the late-run convergence monitor gives about `7.95` additional wall-clock days to reach the `1e-4` threshold if the current decay trend holds.
- At the observed throughput (`23.28 simulated seconds/hour`), reaching `endTime 10000` would take about `14.81` more days from the current endpoint if no earlier convergence stop occurs.
- A single `120 h` continuation chunk is projected to reduce `dTsigma` only to about `5.03e-4`, which is still about `5x` above the target.

## Figures

- Convergence monitor history: [salt2_convergence_monitor.png](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-01_weekly_status/figures/salt2_convergence_monitor.png)
- QoI trend summary: [salt2_qoi_trends.png](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-01_weekly_status/figures/salt2_qoi_trends.png)
- Final temperature snapshot: [salt2_temperature_snapshot.png](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-01_weekly_status/figures/salt2_temperature_snapshot.png)
- Machine-readable summary used for these figures: [salt2_weekly_status_summary.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-01_weekly_status/salt2_weekly_status_summary.json)

## Job Status

- `3200407` (`jadyn_salt2_cont`): `PENDING`, reason currently resources
- `3200181` (`modern_stage1`): `RUNNING`
- `3200186` (`modern_reg1`): `PENDING`, dependency on `3200181`

## Risks / Limits

- `salt_test_2` should still be presented as an in-progress continuation case, not as a converged validation result.
- The low derived external heat-loss result should not yet be interpreted physically because it is tied to the still-drifting late-run state.
- Headless figure rendering for the decomposed 3D case is still unresolved; the figures in this package are diagnostic plots, not geometry/field screenshots.
- The `water kOmegaSSTLM` cases in `modern_runs` still appear setup-only and should stay outside cross-case result tables until actual runtime outputs exist.

## Recommended Talk Track

- This week established the workflow and provenance discipline needed to intake Ethan CFD runs reproducibly.
- We now know `salt_test_2` is close enough to be diagnostically useful, but not close enough to call converged.
- The remaining steady-state gap is quantifiable: about `8` more wall-clock days to satisfy the coded convergence criterion, and about `15` more days to run all the way to `endTime` at current throughput.
- The continuation is already in the queue, and the batch intake path for the broader Ethan run set is now active in parallel.

## Immediate Next Steps

- Monitor `3200407` and reassess the first continuation checkpoint as soon as it lands.
- Let `3200181` complete and then allow `3200186` to register the new staged batch.
- Run extraction on the staged `modern_runs` batch and build first cross-case tables.
- Revisit field/geometry screenshots after either interactive ParaView inspection or a reconstruction-based export path is defined.
