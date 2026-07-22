---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/role_row_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/summary.json
tags: [forward-model, external-bc, heat-loss-sensitivity]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/README.md
task: TODO-FLUID-EXTBC-FJ-PARALLEL-DIAGNOSTICS-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Tester
type: work_product
status: complete
---
# Phase H Heat-Loss Network Sensitivity

The sensitivity matrix is diagnostic and train-only. It does not choose a fitted
multiplier and does not release a repair candidate by score behavior.

Best diagnostic row by all-probe MAE in this bounded run: `baseline_phase_e_recomputed`.
This is not a selected model; Phase J may only use deterministic corrections
released by Phase G or Phase I.
