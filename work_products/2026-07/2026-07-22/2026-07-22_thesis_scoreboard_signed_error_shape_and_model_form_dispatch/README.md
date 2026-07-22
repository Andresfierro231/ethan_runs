---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_error_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/recommended_model_forms_to_try.csv
tags: [thesis, model-form-scoreboard, signed-error-shape, no-admission]
related:
  - .agent/status/2026-07-22_TODO-THESIS-SCOREBOARD-SIGNED-ERROR-SHAPE-AND-MODEL-FORM-DISPATCH-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-scoreboard-signed-error-shape-and-model-form-dispatch.md
task: TODO-THESIS-SCOREBOARD-SIGNED-ERROR-SHAPE-AND-MODEL-FORM-DISPATCH-2026-07-22
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer / Coordinator
type: work_product
status: complete
---
# Thesis Scoreboard Signed-Error Shape And Model-Form Dispatch

Decision: `signed_error_shape_executed_model_form_dispatch_updated_no_scoring_or_admission`.

This package performs the signed-error shape study requested from the thesis
master model-form scoreboard. It also records the current gate status for M0,
S13, passive wall/test-section residual ownership, and pressure/mdot coupling.

## Outputs

- `signed_error_shape_metrics.csv`
- `signed_error_shape_by_sensor.csv`
- `signed_error_local_shape_outliers.csv`
- `model_form_level_error_summary.csv`
- `model_form_error_reduction_targets.csv`
- `m0_setup_baseline_gap_contract.csv`
- `study_enrichment_status.csv`
- `model_form_board_dispatch_matrix.csv`
- `figures/svg/signed_error_shape_by_sensor.svg`
- `figures/svg/bias_vs_shape_residual.svg`
- `summary.json`

## Result

- shape metric rows: `24`
- finite sensor rows: `180`
- model-level rows: `4`
- board dispatch rows: `5`

No new prediction scoring, fitting, model selection, source/property release,
coefficient admission, S11/S12/S13/S15/S6 trigger, solver/sampler/harvest/UQ
launch, Fluid/external edit, thesis edit, or native-output mutation was
performed.
