---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/README.md
tags: [predictive-1d, setup-uq, train-only, runbook, no-execution]
related:
  - .agent/status/2026-07-22_TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-RUNBOOK-2026-07-22.md
  - .agent/journal/2026-07-22/1d-train-only-setup-uq-smoke-runbook.md
  - imports/2026-07-22_1d_train_only_setup_uq_smoke_runbook.json
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-RUNBOOK-2026-07-22
date: 2026-07-22
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Tester / Writer
type: work_product
status: complete
---
# 1D Train-Only Setup-UQ Smoke Runbook

Generated: `2026-07-22T15:33:48.489036+00:00`

Decision: `train_only_setup_uq_smoke_runbook_ready_no_execution`.

This package defines the next executable science row for the 1D model. It does
not launch the execution. A future worker must claim a separate execution row
before running Fluid, scheduler jobs, or UQ sweeps.

## What The Future Execution May Vary

Only setup-legal inputs: heater source fraction, setup cooler/HX strength,
ambient temperature, declared external hA, predictive radiation fields if the
capability exists, labeled property modes, existing baseline pressure-loss
terms, and post-solve sensor projection class audits.

## What It Must Report

`mdot_model`, root status, TP/TW projections, heat-path terms, segment residual
`R_s`, residual-owner labels, runtime-input lint status, and skip reasons for
unsupported variants.

## Files

- `setup_legal_variation_matrix.csv`: 9 variants.
- `executable_runbook.csv`: 7 ordered execution steps.
- `qoi_output_contract.csv`: 10 required outputs.
- `split_and_runtime_guardrails.csv`: 11 split/runtime guardrails.
- `stop_rules.csv`: 6 stop/abort conditions.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`.

## Guardrails

No protected validation/holdout/external tuning, source/property release,
candidate freeze, final score, fit/model selection, coefficient admission,
solver execution, scheduler launch, Fluid edit, native-output mutation, registry
mutation, or external repository edit was performed.
