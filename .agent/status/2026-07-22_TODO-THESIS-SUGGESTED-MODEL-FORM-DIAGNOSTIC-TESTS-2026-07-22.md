---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch/model_form_error_reduction_targets.csv
tags: [thesis, model-form-scoreboard, diagnostic-tests, signed-errors]
related:
  - .agent/journal/2026-07-22/thesis-suggested-model-form-diagnostic-tests.md
  - imports/2026-07-22_thesis_suggested_model_form_diagnostic_tests.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/README.md
task: TODO-THESIS-SUGGESTED-MODEL-FORM-DIAGNOSTIC-TESTS-2026-07-22
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status: Suggested Model-Form Diagnostic Tests

Task: `TODO-THESIS-SUGGESTED-MODEL-FORM-DIAGNOSTIC-TESTS-2026-07-22`

## Objective

Carefully test selected suggested TP/TW model-form variants and place the
results in a thesis-facing scoreboard addendum with auditable construction,
assumptions, per-sensor signed errors, and runtime logging.

## Outcome

Built `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/`.

The package tests six forms:

- `M2_as_is`
- `M3_as_is`
- `D1_M3_global_bias_offset_train`
- `D2_M3_sensor_kind_offsets_train`
- `D3_M3_wall_linear_shape_train`
- `D4_M3_segment_offsets_min2_train`

All fitted diagnostic forms use only Salt2 `train_candidate` residuals from
`signed_sensor_errors.csv`. Salt3 and Salt4 are reported as transfer
diagnostics only. No fitted form is admitted.

Key result:

- M3 transfer RMSE: `17.364529309579673 K`
- Best diagnostic transfer form: `D4_M3_segment_offsets_min2_train`
- Best diagnostic transfer RMSE: `7.940403491512912 K`
- Transfer RMSE reduction versus M3: `54.2722791389897 %`
- Best diagnostic transfer mean signed error: `+3.486151191637737 K`
- Final audited builder runtime: `0.16839051799615845 s`

Interpretation: the best empirical signal is segment/local-source placement,
followed by wall-index thermal-shape correction. This supports prioritizing
source-bounded passive wall/test-section and S12 thermal-shape work, but it does
not admit any residual-trained correction.

## Changes Made

- `tools/analyze/build_thesis_suggested_model_form_diagnostic_tests.py`
- `tools/analyze/test_thesis_suggested_model_form_diagnostic_tests.py`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_scoreboard.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_sensor_errors.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/construction_assumptions.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/model_form_scoreboard_append.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/runtime_audit.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/source_manifest.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/no_mutation_guardrails.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/summary.json`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/figures/svg/tested_model_form_transfer_rmse.svg`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/figures/svg/transfer_signed_sensor_errors_best_vs_m3.svg`
- `.agent/BOARD.md`
- `.agent/status/2026-07-22_TODO-THESIS-SUGGESTED-MODEL-FORM-DIAGNOSTIC-TESTS-2026-07-22.md`
- `.agent/journal/2026-07-22/thesis-suggested-model-form-diagnostic-tests.md`
- `imports/2026-07-22_thesis_suggested_model_form_diagnostic_tests.json`

## Validation

- `python3.11 tools/analyze/build_thesis_suggested_model_form_diagnostic_tests.py` passed.
- `python3.11 tools/analyze/test_thesis_suggested_model_form_diagnostic_tests.py` passed.

The validator reruns the builder and checks:

- input rows: `204`
- finite input rows: `180`
- tested forms: `6`
- scored sensor rows: `270`
- train rows per M3-derived fitted form: `15`
- transfer rows per M3-derived fitted form: `30`
- no transfer targets used for fitting
- all outputs labelled `diagnostic_not_admitted`
- runtime audit and SVG figures exist

## Unresolved Blockers

- M0 setup-only baseline remains unbuilt, so improvement over the minimum
  runtime-legal setup model is still unknown.
- The empirical segment-offset and wall-shape forms need independent
  source-bounded construction before they can become candidate model forms.
- Same-QOI UQ is still required before S12/S13 exchange-cell evidence can move
  beyond diagnostic use.
- Pressure/mdot coupling remains separate; this package does not change mdot,
  pressure loss, or hydraulic K terms.

## Guardrails

- Native CFD/OpenFOAM outputs: read-only, no mutation.
- Registry/admission state: no mutation.
- Scheduler/solver/sampler/UQ: no launch.
- Fluid and external repositories: no mutation.
- Thesis current/LaTeX files: no mutation.
- Master scoreboard package: read-only; this task created an addendum package
  instead of editing the canonical scoreboard in place.
- Validation/holdout targets: not used for fitting or tuning; reported only as
  transfer diagnostics.
