---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
tags: [forward-model, heater-source, validation-split, salt3-holdout]
related:
  - predictive-wall-test-section-submodels
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
task: AGENT-529
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Source Leave-Salt3-Out Score

This package reruns the heater-source redistribution screen with the corrected
split: Salt1/Salt2/Salt4 are the only fit/model-selection rows, Salt3 is the
nominal holdout, and Salt2 +/-5Q plus `val_salt2` remain blind score-only rows.

Decision for `predictive-wall-test-section-submodels`: `keep_open`.

Reason: This package corrects the train/holdout split for the heater-source redistribution screen. The predictive-wall-test-section-submodels blocker remains open until blind PM5Q/val_salt2 adapters exist and the PB2/Salt1 boundary contract is repaired.

Selected lambda: `1`.
Selection status: `diagnostic_selected_from_salt1_salt2_salt4_finite_rows_with_root_rejections`.
Coupled status counts: `{"completed": 67}`.

## Important Limits

The executable lane uses the current Fluid default predictive wall/outer setup
with the frozen constant-UA cooler from AGENT-482. The PB2 wall-distribution lane
is intentionally blocked here because the available external-boundary role table
has Salt2/Salt3/Salt4 rows but no Salt1 rows. Blind PM5Q and `val_salt2` rows are
not fit/model-selection inputs and remain blocked until an executable Fluid
adapter can produce frozen predictions for those cases.

## Files

- `case_split_contract.csv`
- `case_contract_readiness.csv`
- `candidate_definitions.csv`
- `heater_source_lambda_grid.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `training_objective_by_lambda.csv`
- `selected_heater_source_weights.csv`
- `nominal_coupled_scorecard.csv`
- `salt3_holdout_delta_vs_m3.csv`
- `blind_perturbation_external_scorecard.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `ag529_heater_source_loso.sbatch`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
