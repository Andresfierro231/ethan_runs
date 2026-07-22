---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/split_legal_case_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/candidate_freeze_manifest.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/val_salt2_external_score_targets.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/pm10_holdout_admission_watch.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_final_scorecard_source_envelope_resolution/scorecard_source_property_resolution_policy.csv
tags: [forward-model, final-scorecard, corrected-split, holdout-policy]
related:
  - .agent/status/2026-07-18_TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS.md
  - final-predictive-split-policy
  - val-salt2-external-test
  - salt2-pm5q-holdout
  - predictive-wall-test-section-submodels
task: AGENT-509
updated_by: TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS
date: 2026-07-17
role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Final Predictive Scorecard Shell

## Purpose

This package prepares the final scorecard shell without running a model or
computing final scores. It fixes the corrected split in a machine-readable
contract:

- Train/freeze: Salt1 nominal, Salt2 nominal, Salt3 nominal, Salt4 nominal.
- Current blind tests: Salt2 +/-5Q and `val_salt2`, released only after a
  corrected final freeze exists.
- Future tests: Salt2/Salt4 +/-10Q and new CFD, released only after terminal or
  run/admission gates and a corrected final freeze.

## Current State

Final scores are not available. The shell is blocked by the absence of an
admitted Salt1-4 nominal final freeze and by the current wall/test-section
candidate blockers. Existing PB1+cooler/distribution rows remain diagnostic, not
final model evidence.

## Outputs

- `case_partition_contract.csv` is the authoritative row-level split contract.
- `model_freeze_contract.csv` defines `FINAL_FREEZE_TBD` and documents why old
  candidates are not final freezes.
- `metric_contract.csv` defines score lanes and required prediction fields.
- `prediction_join_shell.csv` is the placeholder table that a future frozen
  prediction join should fill.
- `source_property_label_gate_audit.csv` verifies that partition and prediction
  rows carry source/property labels and apply the July 20 source-envelope
  resolution policy before any fit/admission language.
- `holdout_release_gates.csv` records when blind/current/future tests may be
  released.
- `admission_gate_shell.csv` records the gates that still block final scoring.
- `assumption_ledger.csv` lists assumptions and verification paths.
- `runtime_input_audit.csv` verifies no leakage is encoded in this shell.
- `scorecard_summary.csv`, `source_manifest.csv`, and `summary.json` summarize
  the generated package.

## Counts

- Training cases: `4`.
- Current blind holdout/external cases: `3`.
- Future test cases: `5`.
- Prediction placeholder rows: `79`.
- Source/property gate failures: `0`.
- Fit-enabled rows after source/property policy: `0`.
- Model-selection-enabled rows after source/property policy: `0`.
- Runtime audit failures: `0`.

## How To Use This Later

After a candidate is admitted, a separate task should produce a frozen
prediction artifact with `prediction_model_id` and the metric-specific fields
listed in `metric_contract.csv`. Join that artifact into
`prediction_join_shell.csv`; then compute residuals only for released rows.
Salt2 +/-5Q, `val_salt2`, PM10, and new CFD rows must remain unavailable to
fitting and model selection.
