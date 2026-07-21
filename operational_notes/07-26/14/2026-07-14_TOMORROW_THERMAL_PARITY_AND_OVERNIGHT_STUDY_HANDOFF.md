---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/section_heat_loss_comparison.csv
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/thermal_profile_drive_comparison.csv
  - operational_notes/07-26/14/2026-07-14_TOMORROW_HYDRAULICS_AND_OVERNIGHT_COMPUTE_HANDOFF.md
tags: [thermal-parity, external-boundary, heat-loss, overnight, handoff]
related:
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/forward-predictive-model.md
  - reports/thesis_dossier/README.md
task: AGENT-370
date: 2026-07-14
role: Coordinator/Writer
type: operational_note
status: complete
---
# Tomorrow Thermal Parity And Overnight Study Handoff

## Workspace

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
```

Current compute context observed by AGENT-370:

- Node: `c318-008.ls6.tacc.utexas.edu`.
- Interactive job: `3295120` running on `c318-008`.
- Corrected-Q continuation: `3293924` `saltq_sel_cont` running on `c318-016`.
- Dependency harvester: `3295438` `saltq_s24_sel_harv` pending dependency.
- Matched +/-5Q upcomer jobs `3295901` and `3295968` show `CANCELLED by 890970`
  before starting. Do not assume the +/-5Q matched-plane job is still pending.

## What Landed In The Thermal/External-BC Lane

AGENT-365 built:

`work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/`

Key outputs:

- `external_bc_patch_contract.csv`: 207 patch-level CFD boundary/source rows.
- `external_bc_segment_equivalents.csv`: 24 segment-equivalent 1D boundary rows.
- `source_sink_parity_contract.csv`: 12 heater/cooler/test-section/junction
  source/sink contract rows.
- `section_heat_loss_comparison.csv`: 15 Salt2/3/4 leg-level discrepancy rows.
- `thermal_profile_drive_comparison.csv`: 15 wall/bulk drive diagnostic rows.
- `admission_decision_table.csv`: 5 guardrail decisions.
- `presentation_brief.md`, `methodology_and_assumptions.md`,
  `equations_and_sign_conventions.md`, `repeatability_and_refinement_guide.md`,
  and `thesis_reuse_index.md`.

Focused validation passed:

```bash
python3.11 -m py_compile tools/analyze/build_external_bc_thermal_profile_parity_study.py tools/analyze/test_external_bc_thermal_profile_parity_study.py
python3.11 -m unittest tools.analyze.test_external_bc_thermal_profile_parity_study
```

## Current Scientific State

Observed:

- CFD `rcExternalTemperature` includes emissivity/Tsur radiation effects.
- Realized CFD `wallHeatFlux` is total heat flux; radiation is inseparable and
  must not be added again in 1D realized-flux replay.
- Fluid has external-boundary table support documented by AGENT-318, but
  AGENT-365 did not rerun Fluid.
- The current best executable predictive-style model is `F1_heater_only`.
  It still consumes imposed cooler duty, so it is not final predictive-HX
  validation.
- The best current model over-loses heat in pipe legs and under-loses heat in
  junction/stub connector regions. Aggregate heat balance is close by
  cancellation.
- Wall/shell drive diagnostics suggest upcomer and downcomer over-loss is
  plausibly tied to using bulk temperature as the external-loss drive in
  stratified/developing flow.

Inferred:

- The next thermal model should not use one global heat-loss multiplier.
- Separate lanes are required for:
  - external h/Ta/Tsur/emissivity/layer boundary contract;
  - active cooler/HX sink;
  - heater realization fraction;
  - test-section source/loss;
  - passive pipe-wall losses;
  - junction/stub/horizontal connector losses;
  - wall-adjacent or mixed thermal drive.

## Open First Tomorrow

1. `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/README.md`
2. `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/presentation_brief.md`
3. `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/section_heat_loss_comparison.csv`
4. `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/thermal_profile_drive_comparison.csv`
5. `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv`
6. `work_products/2026-07/2026-07-14/2026-07-14_tomorrow_thermal_parity_and_overnight_study_handoff/overnight_study_queue.csv`
7. `operational_notes/07-26/14/2026-07-14_TOMORROW_HYDRAULICS_AND_OVERNIGHT_COMPUTE_HANDOFF.md`
8. `.agent/BOARD.md`

## Recommended Overnight Studies

Best posture tonight: do not duplicate the existing corrected-Q continuation or
dependency harvester. Use the current compute node only for lightweight 1D or
repo-local analysis unless a new board row explicitly claims a Slurm/OpenFOAM
postprocessing launch.

Recommended queue is in:

`work_products/2026-07/2026-07-14/2026-07-14_tomorrow_thermal_parity_and_overnight_study_handoff/overnight_study_queue.csv`

Highest-value lightweight studies:

1. External-boundary table Fluid rerun comparing bulk drive, wall-shell drive,
   and a Salt2-trained mixing factor. This directly tests the user's core
   developing/stratified thermal-profile hypothesis.
2. Setup-only cooler/HX replacement for imposed cooler duty. This removes the
   biggest non-predictive shortcut from `F1_heater_only`.
3. Heater realization fraction model. This separates heater efficiency from
   lower-leg wall loss.
4. Junction/stub geometry-loss audit. This targets the largest under-loss lane.

Higher-risk Slurm/OpenFOAM work:

1. Review why `3295901` and `3295968` were cancelled, then resubmit the matched
   pressure/upcomer +/-5Q extraction only under a new board row if cancellation
   was administrative.
2. Let `3293924` finish and allow/inspect dependency harvester `3295438`; do
   not submit duplicate corrected-Q solver jobs.

## Exact Monitoring Commands

```bash
squeue -u andresfierro231
sacct -j 3293924 --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,NodeList -P
sacct -j 3295438 --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,NodeList -P
sacct -j 3295901 --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,NodeList -P
sacct -j 3295968 --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,NodeList -P
```

## Do Not Do

- Do not mutate native CFD solver outputs.
- Do not run heavy OpenFOAM on a login node.
- Do not use realized CFD `wallHeatFlux`, CFD `mdot`, or validation
  temperatures as predictive runtime inputs.
- Do not add a separate radiation term on top of realized CFD `wallHeatFlux`.
- Do not call radiation-off replay CFD parity.
- Do not call imposed cooler duty final predictive HX.
- Do not hide junction, heater, cooler, or wall-drive errors in one global
  ambient multiplier.
- Do not promote wall-adjacent drive diagnostics to an admitted internal Nu
  closure without Salt2 train / Salt3 validation / Salt4 holdout scoring.

## Tomorrow Pickup Order

1. Check scheduler state and resolve whether matched +/-5Q upcomer extraction
   should be resubmitted.
2. If staying in thermal/1D, claim a new board row for THERM-1: external-boundary
   table Fluid rerun with bulk vs wall-shell/mixing drive.
3. Use AGENT-365 tables as the source contract; do not recalculate assumptions
   from chat.
4. Score by leg, not only by aggregate heat balance.
5. Keep the presentation claim narrow: current result is a diagnostic that tells
   us exactly what to fix, not the final predictive thermal model.
