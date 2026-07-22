---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/role_row_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/phase_f_thermal_residual_decomposition/sensor_segment_residuals.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/summary.json
tags: [forward-model, external-bc, heat-loss-sensitivity, train-only]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-PHASE-H-COMPUTE-SAFE-SENSITIVITY-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-extbc-phase-h-compute-safe-sensitivity.md
  - imports/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity.json
task: TODO-FLUID-EXTBC-PHASE-H-COMPUTE-SAFE-SENSITIVITY-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Phase H Compute-Safe Sensitivity

This package runs the six predeclared train-only external-BC heat-loss
perturbations as isolated subprocesses with hard timeouts and partial CSV
flushing. It is diagnostic only: no fitting, model selection, repair run,
freeze, admission, validation scoring, holdout scoring, or external-test
scoring is performed.

## Outputs

- `sensitivity_status.csv`: subprocess disposition for each perturbation.
- `sensitivity_metrics.csv`: mdot, pressure residual, heat totals, and TP/TW/all residual metrics for completed rows.
- `sensor_delta.csv`: per-sensor residual delta versus Phase E/F-J baseline.
- `owner_delta.csv`: heated-incline/TW5 response classification for each sensitivity.
- `worker_results/`: per-row worker JSON and captured stdout/stderr logs.

## Result

Completed sensitivities: `6` of `6`.
Timeouts: `0`. Failures: `0`.
Owner response counts: `{'improves': 3, 'worsens': 3}`.

All rows remain train-only diagnostics and cannot be used as fitted evidence or
as a final predictive temperature claim.
