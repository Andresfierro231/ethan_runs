---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/conservative_equation_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/sensor_projection_operator_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/uncertainty_source_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_source_property_release_atlas/runtime_legality_audit.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_runbook/summary.json
tags: [journal, predictive-1d, setup-uq, train-only, runtime-legality]
related:
  - .agent/status/2026-07-22_TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-RUNBOOK-2026-07-22.md
  - imports/2026-07-22_1d_train_only_setup_uq_smoke_runbook.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_runbook
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-RUNBOOK-2026-07-22
date: 2026-07-22
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Tester / Writer
type: journal
status: complete
---

# 1D train-only setup-UQ smoke runbook

## Attempted

Confirmed the two requested thesis evidence packets first. The source-property
release atlas and final-figure import ledger were already complete, their
`finish_task.py` closeouts passed, and there was no live builder process
holding those packet locks. I therefore did not rewrite their artifacts.

Claimed the next executable science-definition row and built a dry runbook from
the conservative thermal ledger, sensor projection operator, setup-only BC UQ
contract, regime-map eligibility context, source/property release atlas, and
thermal-pressure root stability audit.

## Observed

The source packets agree on one practical path: execute only train rows first,
vary only setup-legal inputs, and emit sensitivity tables rather than scoring
or freezing a candidate. The setup-only UQ contract gives the legal input
families: heater source fraction, cooler/HX strength, ambient temperature,
external convection hA, radiation capability inputs, wall/material labels,
fluid property mode, pressure-loss terms, and sensor projection class.

The conservative thermal ledger requires `R_s = sum(Q_known_s) -
mdot*cp*(T_out_s - T_in_s)` to remain an output and blocker pointer, not a
runtime closure. The release atlas blocks CFD `mdot`, realized wall heat flux,
imposed cooler duty, validation/holdout temperatures, external-test
temperatures, realized test-section heat, and score-selected global
multipliers.

## Inferred

The highest-value next compute is a smoke test, not a fit. A useful execution
must first prove the baseline train root is finite and bracketed, then run
one-at-a-time setup perturbations and report sensitivity of `mdot`, TP/TW
projections, heat-path terms, and residual-owner labels. This can expose which
setup families dominate the 1D model behavior without using protected rows or
admitting coefficients.

Pressure terms can be varied only as existing baseline setup pressure terms.
F6/component-K, clipped K, pressure-recovery coefficient, internal-Nu, and
exchange-cell coefficients stay disabled because their admission requirements
belong to separate evidence rows.

## What Worked

The dry package cleanly joins the four relevant 1D packets into one execution
contract. Tests confirmed the critical invariants: train-only scope, zero
protected scoring rows, zero source/property release rows, zero coefficient
admission rows, required QOI outputs present, and all forbidden runtime fields
blocked.

## What Did Not Work

No numerical Fluid or root-solve evidence was produced by this row. That was
intentional because the task was to define a scheduler-safe execution row, not
to launch it. The package also cannot decide whether radiation or material
variants are executable until the future execution row checks the actual model
capabilities and emits skip reasons for unsupported variants.

## Next Useful Actions

Claim a separate execution row to run `S00` through `S06` on train rows only.
That row should write a runtime-input manifest before execution, abort if a
forbidden field appears, run the baseline before variants, and close with a
sensitivity ranking plus explicit no-release/no-score status. Validation,
holdout, external-test, source/property release, candidate freeze, fit/model
selection, and coefficient admission should remain locked behind later rows.
