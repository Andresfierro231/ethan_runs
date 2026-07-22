---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/recommended_model_forms_to_try.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch/model_form_error_reduction_targets.csv
tags: [thesis, model-form-scoreboard, diagnostic-tests, signed-errors]
related:
  - .agent/status/2026-07-22_TODO-THESIS-SUGGESTED-MODEL-FORM-DIAGNOSTIC-TESTS-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-suggested-model-form-diagnostic-tests.md
task: TODO-THESIS-SUGGESTED-MODEL-FORM-DIAGNOSTIC-TESTS-2026-07-22
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# Suggested Model-Form Diagnostic Tests

This package tests selected suggested model forms as a scoreboard addendum. It
does not modify the canonical master scoreboard in place. All fitted diagnostic
forms use only Salt2 `train_candidate` residuals from the master
`signed_sensor_errors.csv`; Salt3 and Salt4 are reported as transfer diagnostics
only.

## Terms

- MF: model form, meaning a proposed 1D closure or correction family.
- M2: current legacy numeric model form after the major thermal-boundary and
  segment-model improvement.
- M3: current best legacy numeric comparator in the master scoreboard.
- TP: fluid thermocouple or bulk-temperature probe row.
- TW: wall thermocouple row.
- Salt2: train-candidate case used here to construct empirical diagnostics.
- Salt3/Salt4: transfer rows used only to report whether a diagnostic shape
  transfers; no fitting uses these targets.
- Signed error: `predicted_K - target_K`. Negative means the model is cold.
- RMSE: root mean square signed error magnitude in K.
- MAE: mean absolute error in K.
- Bias: mean signed error. Local shape RMSE removes that mean first.
- Source-bounded: a candidate has an independent physical/source envelope,
  not just an empirical residual correction.
- Admission: permission to use a model form as accepted evidence. Every fitted
  row here is `diagnostic_not_admitted`.

## Tested Forms

- `M2_as_is`: existing M2 finite TP/TW predictions.
- `M3_as_is`: existing M3 finite TP/TW predictions.
- `D1_M3_global_bias_offset_train`: one Salt2-trained global temperature offset.
- `D2_M3_sensor_kind_offsets_train`: separate Salt2-trained TP and TW offsets.
- `D3_M3_wall_linear_shape_train`: Salt2-trained TW sensor-index line plus TP
  mean offset.
- `D4_M3_segment_offsets_min2_train`: Salt2-trained segment offsets where at
  least two finite train sensors support the segment, with global fallback.

## Result

- tested forms: `6`
- scored sensor rows: `270`
- best transfer diagnostic: `D4_M3_segment_offsets_min2_train`
- best transfer RMSE: `7.9404 K`
- M3 as-is transfer RMSE: `17.3645 K`
- total runtime: `0.168391 s`

The best empirical transfer test is useful as a research-priority signal only.
It is not a source-bounded repair and should not be admitted or used for final
protected scoring.

## Outputs

- `tested_model_form_scoreboard.csv`
- `tested_model_form_sensor_errors.csv`
- `construction_assumptions.csv`
- `model_form_scoreboard_append.csv`
- `runtime_audit.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
- `figures/svg/tested_model_form_transfer_rmse.svg`
- `figures/svg/transfer_signed_sensor_errors_best_vs_m3.svg`
