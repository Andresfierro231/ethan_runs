---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/thermal_residual_attribution.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/heat_path_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/role_row_ledger.csv
tags: [forward-model, external-bc, thermal-residual, train-only]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/README.md
task: TODO-FLUID-EXTBC-FJ-PARALLEL-DIAGNOSTICS-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Writer
type: work_product
status: complete
---
# Phase F Thermal Residual Decomposition

This package decomposes the completed Phase E Salt2 train-only residuals by
Fluid prediction segment, external-BC source family, and heat-path role.

Phase E remains diagnostic: the baseline TP/TW residuals are large and are not
a freeze, admission, validation score, holdout score, or external-test score.
