---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv
  - jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/0/T
  - jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/postProcessing/wallHeatFlux/4027/wallHeatFlux.dat
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/case_partition_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/freeze_readiness_matrix.csv
tags: [forward-model, external-boundary, salt1, train-only, freeze-gate]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_train_only_external_bc_attribution_freeze_gate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/README.md
task: TODO-SALT1-TRAIN-EXTERNAL-BC-RECOVERY-FREEZE-GATE-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Salt1 Train External BC Recovery Freeze Gate

## Decision

This package recovers the four missing Salt1 canonical-train ambient-wall
external-BC rows from Salt1 setup metadata and publishes a task-owned augmented
Fluid runtime dictionary. It does not edit Fluid, mutate native CFD outputs,
fit/tune coefficients, admit a candidate, freeze a model, or score validation,
holdout, or external-test rows.

Freeze remains fail-closed: `no_candidate_frozen`.

## Results

- Salt1 recovered ambient-wall rows: `4`.
- Augmented runtime dictionary rows: `28`.
- Canonical train ambient-wall coverage: `16/16`.
- Parser failures: `0`.
- Full Fluid train solves run: `0`.
- Validation/holdout/external-test rows consumed: `0/0/0`.

## Outputs

- `salt1_external_bc_recovery_rows.csv`
- `augmented_fluid_external_boundary_runtime_dictionary.csv`
- `segment_heat_path_coverage.csv`
- `document_only_source_sink_rows.csv`
- `train_fluid_solve_runtime_audit.csv`
- `source_property_release_gate.csv`
- `train_residual_owner_scorecard.csv`
- `candidate_freeze_gate.csv`
- `validation_only_score_gate.csv`
- `holdout_external_test_release_gate.csv`
- `runtime_leakage_audit.csv`
- `fluid_state_snapshot.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Salt1 `wallHeatFlux.dat` is used only to recover/check grouped geometry and
diagnostic heat-path provenance; realized heat-flux values are not present in
the runtime dictionary. Heater, cooler, and test-section rows remain
document-only. Salt3/Salt4 legacy split labels are normalized only inside this
train-only gate. Residuals remain attribution evidence and cannot be absorbed
into F6, hidden K/global multipliers, external BC fields, or internal `Nu`.
