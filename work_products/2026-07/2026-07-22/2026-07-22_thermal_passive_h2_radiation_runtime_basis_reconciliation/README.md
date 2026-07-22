---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_one_train_repair_preflight/passive_operator_term_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table/source_backed_passive_h2_basis_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/sensor_projection_predictions.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/baseline_root_and_qoi_smoke.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/one_at_a_time_setup_uq_smoke.csv
tags: [thermal, passive-h2, radiation, runtime-basis, same-qoi, no-release]
related:
  - .agent/status/2026-07-22_TODO-THERMAL-PASSIVE-H2-RADIATION-RUNTIME-BASIS-RECONCILIATION-2026-07-22.md
  - .agent/journal/2026-07-22/thermal-passive-h2-radiation-runtime-basis-reconciliation.md
  - imports/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation.json
task: TODO-THERMAL-PASSIVE-H2-RADIATION-RUNTIME-BASIS-RECONCILIATION-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Radiation Runtime-Basis Reconciliation

Decision: `passive_h2_radiation_basis_resolved_outer_insulation_surface_same_qoi_gate_diagnostic_no_release`.

The prior PASSIVE-H2 smoke reproduced a direct radiation term of
`656.493 W`. That value was large because
the diagnostic operator treated model-predicted wall/pipe-state temperatures as
the radiating surface. That is not the physically appropriate runtime basis for
an insulated external boundary.

This package treats the projected wall state as the inner boundary of the
source-backed layer stack, solves a conduction plus exterior convection and
radiation balance, and radiates from the outer insulation surface. Under that
basis the nominal corrected radiation term is
`22.215 W`; corrected convection is
`16.341 W`; corrected total
external passive operator is `38.557
W`.

## Scientific Interpretation

- The direct `~656 W` radiation result is a basis error for release purposes,
  not evidence that H2 requires a huge radiation correction.
- The existing train-only `radiation_on` Fluid/model variant still has zero
  mdot, heat-ledger, and temperature-output movement, so it is not admitted as
  an implemented H2 radiation switch.
- Radiation semantics are resolved enough to define a separately tested
  source-backed operator: inner model state -> source layer resistance -> outer
  insulation surface -> convection/radiation to `Ta/Tsur`.
- H2 remains diagnostic only here. No numeric q-loss release, source/property
  release, Qwall release, candidate freeze, coefficient admission, protected
  score, or final score is made.

## Files

- `radiation_runtime_basis_reconciliation.csv`
- `corrected_outer_surface_passive_operator_family.csv`
- `train_only_same_qoi_h2_gate.csv`
- `radiation_runtime_decision.csv`
- `runtime_input_audit.csv`
- `source_manifest.csv`
- `summary.json`
