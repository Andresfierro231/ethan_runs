---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv
  - tools/analyze/build_thesis_suggested_model_form_diagnostic_tests.py
tags: [thesis, model-form-scoreboard, diagnostic-tests, signed-errors]
related:
  - .agent/status/2026-07-22_TODO-THESIS-SUGGESTED-MODEL-FORM-DIAGNOSTIC-TESTS-2026-07-22.md
  - imports/2026-07-22_thesis_suggested_model_form_diagnostic_tests.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/README.md
task: TODO-THESIS-SUGGESTED-MODEL-FORM-DIAGNOSTIC-TESTS-2026-07-22
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Journal: Suggested Model-Form Diagnostic Tests

## Attempted

Created a new scoreboard addendum rather than mutating the canonical master
scoreboard. The builder reads the existing master `signed_sensor_errors.csv`,
constructs six predeclared model-form rows, scores every finite TP/TW sensor
prediction, writes construction assumptions, and records phase runtime.

The fitted forms are deliberately narrow:

- one global M3 residual offset from Salt2 train rows
- TP/TW-specific residual offsets from Salt2 train rows
- wall-index linear residual shape from Salt2 TW train rows with TP mean offset
- segment-label offsets from Salt2 train rows when at least two sensors support
  the segment, with global fallback

## Observed

The existing M3 comparator has Salt3/Salt4 transfer RMSE
`17.364529309579673 K` and transfer mean signed error `-14.0651310596 K`.

All Salt2-trained diagnostic corrections improve transfer RMSE:

- `D1_M3_global_bias_offset_train`: `10.5420700958 K`
- `D2_M3_sensor_kind_offsets_train`: `10.5253939442 K`
- `D3_M3_wall_linear_shape_train`: `8.38846755024 K`
- `D4_M3_segment_offsets_min2_train`: `7.94040349151 K`

The best diagnostic row, `D4_M3_segment_offsets_min2_train`, changes the
transfer mean signed error to `+3.48615119164 K`, meaning it removes most of
the global cold bias but leaves local signed shape. The final audited builder
runtime was `0.16839051799615845 s` for this small CSV input.

## Inferred

The residual structure is not just a uniform global cold offset. The global
offset helps substantially, but wall-index shape and segment-local offsets help
more. The next rigorous model-form work should therefore focus on independent,
source-bounded local heat-path ownership rather than simply admitting a fitted
temperature bias.

The strongest follow-on rows are:

- passive wall/test-section source-bounded repair gate, because the segment
  offsets point to local source placement
- S12 thermal-shape/upcomer exchange work, because the wall-index correction
  transfers better than a pure global offset
- M0 setup-only baseline, because this diagnostic package still cannot quantify
  improvement over the minimum legal model

## Caveats

These are empirical residual tests, not admitted model forms. They do not
release Q_wall/source/property terms, do not run samplers or same-QOI UQ, do
not mutate Fluid, and do not adjust pressure/mdot. Salt3 and Salt4 target
values are used only for transparent transfer reporting, not fitting or tuning.

## Next Useful Actions

1. Claim and execute the M0 setup-only baseline scorecard row.
2. Claim the passive wall/test-section source-bounded repair gate and test
   whether the segment-local residual can be explained by independent source
   terms.
3. After active S12/S13 rows close, use the wall-index result to prioritize a
   source-bounded thermal-shape or wall/core exchange candidate with same-QOI
   UQ.
4. Keep the pressure/mdot coupling diagnostic separate; this task did not test
   hydraulic coupling.
