---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_corrected_operator_predictive_train_packet/candidate_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke/case_corrected_radiation_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/model_form_summary.csv
tags: [thesis, figures, d2, passive-h2, diagnostic-only, operator-only]
related:
  - .agent/status/2026-07-22_TODO-THESIS-FIGTABLE-D2-H2-DIAGNOSTIC-FIGURE-EXTENSION-2026-07-22.md
  - imports/2026-07-22_thesis_figtable_d2_h2_diagnostic_figure_extension.json
task: TODO-THESIS-FIGTABLE-D2-H2-DIAGNOSTIC-FIGURE-EXTENSION-2026-07-22
date: 2026-07-22
role: Figures / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Journal

## Attempted

Extended the thesis model-form figure package to include the most useful
non-master-scoreboard diagnostic/model-form evidence: D2 and PASSIVE-H2.

## Observed

D2 has finite per-sensor diagnostic adjusted predictions for Salt2/Salt3/Salt4
except TP2 and TW10. It can therefore use the same TP/TW elevation and
signed-error visual contract as M1/M1b/M2/M3. Against experimental TP/TW
targets, D2 has RMSE `8.10959406187 K`, better than M3's `19.5676078164 K`.

PASSIVE-H2 does not emit per-sensor TP/TW predictions in the completed packets.
Its current evidence is heat-path/operator evidence: corrected outer-surface
convection/radiation, segment-family decomposition, and a global-patch rejection
projection. The corrected operator total is `38.6073163603066` to
`44.677058690827764 W`.

## Inferred

D2 is the better-looking curve, but it is not the predictive model because it
uses Salt2-trained empirical TP/TW offsets and remains diagnostic only. Its
thesis value is to show that a TP/TW projection or wall/core split matters.

PASSIVE-H2 should not be forced into TP/TW elevation plots until a runtime
operator produces legal per-sensor predictions. Its thesis value is to show why
the passive-boundary path is physically plausible and why direct global
qambient replacement/addition is rejected.

## Changed

The builder now normalizes D2 diagnostic sensor rows into the existing
TP/TW-panel data contract and emits model-form folders for D2. The builder also
emits PASSIVE-H2 operator panels and an operator-only README. The test now
asserts the expanded counts, output paths, D2 diagnostic disposition, and
PASSIVE-H2 operator-only disposition.

## Validation

`python3.11 -m py_compile tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
passed.

`python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
passed.

## Next Useful Actions

Use D2 figures as diagnostic evidence for projection/wall-core residual
ownership, not as final prediction. Use PASSIVE-H2 figures as the passive
external-boundary implementation motivation. Continue the actual predictive
path through source/property, Qwall/UQ, and freeze gates before any protected
score is computed.
