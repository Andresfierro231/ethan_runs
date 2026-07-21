---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/summary.json
  - tools/analyze/build_val_salt2_external_score_and_unlock_progress.py
tags: [val-salt2, external-score, junction-heat, pressure-k, pm10, handoff]
related:
  - .agent/status/2026-07-17_AGENT-500.md
  - imports/2026-07-17_val_salt2_external_score_and_unlock_progress.json
task: AGENT-500
date: 2026-07-17
role: cfd-pp/Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# val_salt2 External Score and Unlock Progress

## Why This Exists

The prior AGENT-496 package made `val_salt2` target-ready but not evidence-ready:
numeric targets existed, while frozen model predictions and admissible coefficient
lanes did not. This task created the next reusable package so tomorrow's work can
start from explicit join contracts, residual status, and unlock gates.

## Files To Open First

1. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/val_salt2_prediction_join_contract.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/summary.json`
4. `tools/analyze/build_val_salt2_external_score_and_unlock_progress.py`

## Observed Output

- `61` external-score targets were emitted.
- Target split: `30` pressure map, `14` thermal section/junction, `17` sensor.
- `15` sensors are score-allowed after TP2/TW10 exclusion.
- `0` prediction rows were joined; the residual scorecard marks usable targets
  as `prediction_missing`.
- `16` junction heat-readiness rows were emitted, with `0` coefficient-admitted.
- `12` corner-K rows were emitted, with `0` fit-admitted.
- `4` PM10 rows remain monitor-only.
- `4` SVG figures were generated from existing data.

## Inference

`val_salt2` should now be treated as blind external-test target evidence with a
complete scoring surface, not as a training input. The current blocker is not
target quality; it is the absence of an admitted corrected-split frozen
prediction artifact.

Junction/stub heat-loss trends remain physically useful diagnostics. Salt2/3/4
mainline rows now expose h-proxy values from realized loss, area, and local
temperature drive, but these are not coefficient-fit rows. `val_salt2` lacks the
same area and drive metadata, so it cannot validate a transferable junction
coefficient yet.

Corner-K remains diagnostic. The current negative local centerline K values are
treated as a failed extraction/gating signal, not as physical negative minor
loss coefficients.

## Contradictions Or Caveats

- Some legacy coupled candidates are named "frozen", but current gate outputs
  mark them blocked or diagnostic-only. This package therefore does not use them
  as prediction evidence.
- PM10 has steady-window context in the readiness package, but terminal
  admission remains blocked because the solver/harvest jobs are still recorded
  as running/pending there.
- The generated pressure loop plot is an external target map, not a pressure
  closure fit.

## Next Useful Actions

1. Produce or identify a corrected-split frozen prediction artifact that is not
   trained or selected on `val_salt2`.
2. Join that artifact to `val_salt2_prediction_join_contract.csv` and regenerate
   the residual scorecard.
3. Add comparable area and temperature-drive metadata for `val_salt2` and
   perturbation junction buckets before any junction heat coefficient review.
4. Rebuild corner pressure extraction with branch orientation, straight-run
   subtraction, recirculation mask, component isolation, and mesh/GCI evidence.
5. Revisit PM10 terminal admission only after the recorded jobs are terminal and
   harvested.

## Do Not Do

- Do not tune, fit, select, or reclassify using `val_salt2` residuals.
- Do not submit duplicate pressure, PM5, or PM10 jobs from this package.
- Do not edit native OpenFOAM outputs, registry/admission state, or external
  Fluid source.
- Do not use current corner-K rows for pressure-K fitting.
