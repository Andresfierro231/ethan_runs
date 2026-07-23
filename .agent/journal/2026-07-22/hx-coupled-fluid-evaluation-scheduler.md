---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/source_property_preflight.csv
  - work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/coupled_qoi_review.csv
  - work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/coupled_fluid_output/coupled_scorecard.csv
tags: [journal, hx, cooler, coupled-fluid, source-property, scheduler]
related:
  - .agent/status/2026-07-22_TODO-HX-COUPLED-FLUID-EVALUATION-SCHEDULER-2026-07-22.md
  - imports/2026-07-22_hx_coupled_fluid_evaluation_scheduler.json
task: TODO-HX-COUPLED-FLUID-EVALUATION-SCHEDULER-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Monitor
type: journal
status: complete
---
# HX Coupled Fluid Evaluation Scheduler

## Attempted

Claimed a separate scheduler-owned HX row, preserved the source/property gate as
fail-closed, added a run-specific output directory to the cooler builder, and
ran the actual coupled Fluid path under `srun` inside Slurm allocation
`3307325`.

## Observed

`sbatch` was unavailable from the current compute node (`c318-008`), so the
run used scheduler-accounted `srun` in the existing allocation. The Fluid
evaluation completed `12/12` rows with accepted roots and wrote the new package
under `work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/coupled_fluid_output/`.

The source/property preflight still reports release-ready rows `0`, strict
source-envelope pass rows `0`, and source/property release `false`. The coupled
QOI review reports large errors for every cooler candidate; the selected
`HX_LUMPED_UA_NTU` row has mean all-probe RMSE `114.1543299 K`, max absolute
mdot error `37.48196928%`, and mean all-probe RMSE delta `97.57853845 K` worse
than `M3TS_R0`.

## Inferred

The compute blocker is closed for this HX/cooler pass: the Fluid path can run
and produce coupled QOI rows. The scientific blocker is not closed. The HX
candidate cannot be admitted because both the source/property gate and the
coupled QOI review fail. Cooler segmentation from `N4` to `N16` does not change
the conclusion; the segmented rows are nearly identical to the lumped row in
coupled QOI space.

## Caveats

The run is diagnostic because the user explicitly requested compute after
maximum preflight progress. It is not a source/property release, final score,
candidate freeze, or protected/admission score. Fixed-mdot segmented duty rows
remain pending; they were not reconstructed from coupled totals.

## Next Useful Actions

Move HX/cooler work down in priority for admission. The more productive path is
now source/property repair and a physical source/heat-path model that affects
the large mdot and TP/TW errors rather than refining HX segmentation.
