---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_runbook/setup_legal_variation_matrix.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/case_runtime_inputs_forward_v0.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/runtime_input_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/conservative_equation_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/sensor_projection_operator_table.csv
tags: [predictive-1d, setup-uq, train-only, smoke, no-release]
related:
  - .agent/status/2026-07-22_TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22.md
  - .agent/journal/2026-07-22/1d-train-only-setup-uq-smoke-execution.md
  - imports/2026-07-22_1d_train_only_setup_uq_smoke_execution.json
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22
date: 2026-07-22
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: work_product
status: active
---
# 1D Train-Only Setup-UQ Smoke Execution

Generated: `2026-07-22T16:41:34+00:00`

Decision: `train_only_setup_uq_smoke_executed_no_release_no_score`.

Smoke status: `smoke_complete`.

This package is the execution surface for the train-only setup-UQ smoke. It
freezes the runtime manifest and scenario matrix locally. The full Fluid
`solve_case` matrix must run on a compute node because a single Salt2
`solve_case` probe exceeded one minute on the login-node foreground path.

## Guardrails

No protected validation, holdout, or external-test row may tune, fit, select, or
score this smoke. No source/property release, candidate freeze, F6/component-K,
internal-Nu, exchange coefficient, final score, native-output mutation,
registry mutation, or external Fluid edit is authorized.

## Compute Handoff

Task-owned command:

```bash
sbatch work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/scripts/run_train_only_setup_uq_smoke.sbatch
```

The run script first executes the Fluid-backed smoke and then runs the package
validator. It writes logs under `work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/logs`.
