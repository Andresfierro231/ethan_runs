---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger/val_salt2_external_pressure_thermal_sensor_targets.csv
  - reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/cfd_sensor_reference.csv
  - work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/junction_split_heat_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_junction_split_heat_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/pressure_corner_k_admission_table.csv
tags: [external-score, val-salt2, junction-heat, pressure-k, next-studies]
related:
  - .agent/status/2026-07-17_AGENT-496.md
  - .agent/journal/2026-07-17/external-score-junction-corner-progress.md
task: AGENT-496
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# External Score, Junction Heat, and Corner-K Progress

This package implements the non-overlapping parts of the requested next-front
plan from existing evidence only. Active AGENT-495 owns the upcomer-onset /
recirculation classifier lane, so this package records that dependency without
duplicating its work.

## Result

- `val_salt2` external score targets are ready as targets, not model inputs.
- Numeric `val_salt2` TP/TW sensor targets joined: `17` of `17`.
- Cross-case junction/stub rows audited: `16`.
- Corner-K rows reviewed: `12`, fit-admitted rows `0`.
- Runtime/holdout leakage audit rows: `7`.

## Scientific Interpretation

`val_salt2` can now be externally scored once a frozen model produces pressure,
thermal, and sensor predictions. The score must remain blind: no tuning, model
selection, or training reclassification happens here.

The junction/stub losses are cross-case stable enough to justify a named-loss
diagnostic lane, especially the repeated upper-right dominance, but not enough
to fit a runtime coefficient. `val_salt2` still lacks the area and temperature
drive metadata present in Salt2/3/4 mainline junction rows.

Corner K remains diagnostic. Existing centerline straight-loss subtraction
produces negative local K rows, with recirculation and pressure-definition gates
still failing. The unlock contract is a new extraction, not reuse of current
negative rows.
