---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger/val_salt2_external_pressure_thermal_sensor_targets.csv
  - reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/cfd_sensor_reference.csv
  - work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/junction_split_heat_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_junction_split_heat_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/pressure_corner_k_admission_table.csv
tags: [external-score, val-salt2, junction-heat, pressure-k, next-studies]
related:
  - .agent/status/2026-07-17_AGENT-496.md
  - imports/2026-07-17_external_score_junction_corner_progress.json
task: AGENT-496
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# External Score, Junction Heat, and Corner-K Progress

## Why this exists

The user asked to implement the next plan for making progress after the
`val_salt2` external ledger and Salt2 +/-5Q PM5 repair landed. A new AGENT-495
row already owns the upcomer-onset/recirculation classifier lane, so this task
implemented the remaining non-overlapping fronts from existing evidence only.

## Observed output

The package joined all `17` `val_salt2` TP/TW numeric targets from the July 1
CFD sensor reference. TP2 and TW10 remain blocked by sensor policy for aggregate
score use, but their numeric target values are now visible for future explicit
policy decisions.

External scoring is now target-ready but prediction-join pending for three
lanes:

- pressure streamwise map
- section and junction/stub heat
- sensor temperatures

The junction/stub audit combines the Salt2/Salt3/Salt4 mainline split ledger and
the `val_salt2` external split ledger. The bucket fractions are stable:

- lower-left mean fraction `0.198946679026`
- lower-right mean fraction `0.194804709834`
- upper-left mean fraction `0.244631289268`
- upper-right mean fraction `0.361617321872`

Upper-right is again the dominant bucket. This is useful evidence for a named
loss term, but not enough for coefficient admission because `val_salt2` lacks
the area and temperature-drive metadata already present for Salt2/3/4 mainline.

The pressure corner-K unlock contract reviewed `12` rows. All remain
diagnostic: `0` fit-admitted, all fail straight-loss subtraction because
centerline-subtracted K is negative, and recirculation/pressure-definition gates
also fail.

## Interpretation

We can now make a clean external score once a frozen model produces predictions.
The evidence side is no longer the blocker for `val_salt2` pressure, heat, or
sensor target values. The blocker is model-side: predictions must be generated
without spending `val_salt2` for tuning.

The junction/stub heat-loss story is scientifically coherent but still
diagnostic. The repeated upper-right dominance is real enough to motivate a
named junction/stub loss lane. It should not be hidden inside ordinary pipe
internal-Nu or wallHeatFlux-derived runtime coefficients.

Corner K needs a repaired extraction, not reinterpretation of existing negative
rows. The next corner-K attempt must use an admitted pressure basis, local taps
outside recirculation, a physically local straight reference, component
isolation, and same-QOI mesh/GCI.

## Next task sequence

1. Freeze the predictive model, then join model predictions to this package's
   `external_score_readiness.csv` and `val_salt2_sensor_numeric_join.csv`.
2. Complete `val_salt2` junction geometry/area/temperature-drive metadata before
   any named-loss coefficient fit.
3. Design repaired corner-K extraction around local taps and local straight
   reference; do not use current negative K rows for tuning.
4. Wait for PM10 jobs to become terminal before terminal holdout admission.
5. Consume AGENT-495 when it completes the recirculation/onset classifier; do
   not duplicate that active scope.

## Commands

- `python3.11 -m py_compile tools/analyze/build_external_score_junction_corner_progress.py tools/analyze/test_external_score_junction_corner_progress.py`
- `python3.11 -m unittest tools.analyze.test_external_score_junction_corner_progress`
- `python3.11 tools/analyze/build_external_score_junction_corner_progress.py`

## Do-not-do guardrails

- Do not fit/tune/select model form on `val_salt2`, Salt2 +/-5Q, or PM10.
- Do not use realized `wallHeatFlux`, section heat, pressure, or TP/TW targets
  as runtime predictors.
- Do not relaunch pressure, PM5, or PM10 jobs from this lane.
- Do not overlap active AGENT-495 recirculation/onset files.
