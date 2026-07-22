---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger/val_salt2_external_pressure_thermal_sensor_targets.csv
  - work_products/2026-07/2026-07-17/2026-07-17_external_score_junction_corner_progress/val_salt2_sensor_numeric_join.csv
  - work_products/2026-07/2026-07-17/2026-07-17_external_score_junction_corner_progress/junction_stub_cross_case_audit.csv
  - work_products/2026-07/2026-07-17/2026-07-17_external_score_junction_corner_progress/pressure_corner_k_unlock_contract.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_coupled_segment_m3ts_scorecard/coupled_candidate_gate_scorecard.csv
  - work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/pm10_case_readiness.csv
tags: [val-salt2, external-score, junction-heat, pressure-k, pm10, next-studies]
related:
  - .agent/status/2026-07-17_AGENT-500.md
  - .agent/journal/2026-07-17/val-salt2-external-score-and-unlock-progress.md
task: AGENT-500
date: 2026-07-17
role: cfd-pp/Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 External Score and Unlock Progress

This package converts the current `val_salt2` target-ready state into a
decision-ready external-score contract and unlock-study ledger. It uses existing
postprocessed artifacts only.

## Observed Output

- External score targets emitted: `61`.
- Policy-allowed scored sensor targets after TP2/TW10 exclusion: `15`.
- Frozen prediction rows joined: `0`.
- Residual rows marked `prediction_missing`: `59`.
- Junction coefficient-ready rows admitted: `0`.
- Corner-K fit-admitted rows: `0`.
- PM10 rows allowed for terminal admission now: `0`.

## Interpretation

`val_salt2` is ready as blind external-test target evidence, but not as training,
fitting, model-selection, or runtime input. No admitted frozen prediction artifact
is available in this package, so residuals are deliberately left as
`prediction_missing` instead of being inferred from diagnostic legacy candidates.

Junction/stub heat remains a stable named-loss diagnostic. The coefficient lane
is still blocked because comparable area and local temperature-drive metadata are
not available for every required validation/perturbation bucket.

Corner-K remains diagnostic. Current rows still fail the pressure basis,
straight-loss subtraction, recirculation mask, component isolation, and mesh/GCI
gates.

## Continue Here

Open `val_salt2_prediction_join_contract.csv` before running any external score.
The next legitimate scoring step is to join a corrected-split frozen prediction
artifact to these targets without changing model parameters or split policy.

Do not submit PM10 duplicate jobs, do not rerun pressure ladders from this task,
and do not edit Fluid or native OpenFOAM outputs from this package.
