---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - work_products/2026-07/2026-07-16/2026-07-16_salt1_durable_test_data_and_thesis_story/salt1_primary_closure_cases.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/salt1_terminal_patch_bc_role_table.csv
  - work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/all_streamwise_pressure_1d_map.csv
tags: [salt1, schema-promotion, forward-predictive-model, final-training, admission]
related:
  - .agent/status/2026-07-17_TODO-PREDICT-SALT1-SCHEMA-PROMOTION.md
  - .agent/journal/2026-07-17/predict-salt1-schema-promotion.md
task: TODO-PREDICT-SALT1-SCHEMA-PROMOTION
date: 2026-07-17
role: cfd-pp/Forward-pred/Thermal-modeling/Hydraulics/Sensor-map/Implementer/Tester/Writer
type: work_product
status: complete
---
# Salt1 Schema Promotion

## Decision

Salt1 is now schema-promoted for future final predictive training. The promoted rows cover `salt1_nominal`, `salt1_lo10q`, and `salt1_hi10q` with final split labels, source/sink role ledgers, pressure targets, thermal score rows, sensor target rows, and runtime-input audits.

Use status:

- `salt1_nominal`: final-training evidence.
- `salt1_lo10q` and `salt1_hi10q`: training-support evidence with q-ratio labels preserved.
- Pressure and TP/TW rows are target/diagnostic rows, not runtime inputs.
- Realized Salt1 `wallHeatFlux` is not used as a predictive runtime input.
- The rows retain operational stop/cancel provenance and are not clean endTime completions.

## Outputs

- `salt1_bc_source_material_contract.csv`
- `salt1_patchwise_heat_source_sink_ledger.csv`
- `salt1_pressure_streamwise_rows.csv`
- `salt1_pressure_branch_score_rows.csv`
- `salt1_thermal_score_rows.csv`
- `salt1_sensor_target_rows.csv`
- `runtime_input_audit.csv`
- `salt1_split_ready_manifest.csv`
- `source_manifest.csv`
- `summary.json`

## Observed Facts

- Promoted cases: `3`.
- BC/source/material contract rows: `21`.
- Heat ledger rows: `18`.
- Streamwise pressure rows: `90`.
- Branch pressure rows: `18`.
- Sensor target rows: `51`.

## Interpretation

This closes the schema gap that prevented admitted Salt1 evidence from being consumed consistently with Salt2-4 in future final-training workflows. It does not admit new pressure coefficients, ordinary upcomer coefficients, or realized-wall-heat runtime inputs.

## Blockers And Next Action

Remaining physical-model blockers still live in `.agent/BLOCKERS.md`, especially the wall/test-section submodel, upcomer onset sparsity, and F6 friction correction. The next scorecard should consume `salt1_split_ready_manifest.csv` and reject any attempt to use CFD mdot, realized wallHeatFlux, imposed cooler duty, or TP/TW validation temperatures as runtime inputs.
