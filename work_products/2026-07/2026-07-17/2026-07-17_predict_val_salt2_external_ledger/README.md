---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_patch_heat_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_section_reconciliation.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_junction_split_heat_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_pressure_map.csv
  - work_products/2026-07/2026-07-15/2026-07-15_forward_v1_hydraulic_unblock_plan_execution/sensor_map_policy_refresh.csv
tags: [val_salt2, external-test, ledger, heat-audit, pressure-map, sensors]
related:
  - tools/analyze/build_val_salt2_external_test_ledger.py
task: AGENT-486
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 External-Test Ledger

This package normalizes AGENT-483 `val_salt2` heat and pressure evidence into a
single external-test ledger. It also carries AGENT-393 sensor policy rows so
TP/TW targets are visible to downstream scorecards without treating sensor
temperatures as runtime inputs.

## Result

- Patch heat rows: `69`.
- Section heat rows: `10`.
- Junction split rows: `4`.
- Pressure target rows: `30`.
- Sensor policy target rows: `17`.
- Fit-admitted rows: `0`.
- Runtime heat-input rows admitted: `0`.

`val_salt2` is main external-test evidence and a training-quality audit artifact.
It is not a training, fitting, model-selection, or runtime wall-heat input.
Sensor rows are policy targets only here; this package does not claim a
case-specific val_salt2 numeric sensor-temperature join.

## Files

- `val_salt2_external_patch_heat_ledger.csv`
- `val_salt2_external_section_heat_ledger.csv`
- `val_salt2_external_junction_split.csv`
- `val_salt2_external_pressure_thermal_sensor_targets.csv`
- `val_salt2_external_runtime_input_audit.csv`
- `val_salt2_external_admission_decision.csv`
- `source_manifest.csv`
- `summary.json`
