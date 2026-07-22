---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_b_exact_file_preflight/segment_mapping_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_c_implementation/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/summary.json
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/external_boundary.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
tags: [forward-model, predictive-1d, thermal-boundary, runtime-leakage]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-E-TRAIN-FULL-SOLVE-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-external-bc-phase-e-train-full-solve.md
  - imports/2026-07-21_fluid_external_bc_phase_e_train_full_solve.json
task: TODO-FLUID-EXTERNAL-BC-PHASE-E-TRAIN-FULL-SOLVE-2026-07-21
date: 2026-07-21
role: Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Fluid External BC Phase E Train Full Solve

This package runs the local Fluid 1D nonlinear `solve_case` path using the
Phase C/D external-boundary dictionary mechanism. It consumes only train/support
rows from the repo-local external BC dictionary and keeps validation, holdout,
and external-test rows out of runtime and scoring.

## Outputs

- `phase_e_train_external_boundary_dictionary.csv`: package-local filtered
  train/support dictionary.
- `role_row_ledger.csv`: predictive passive external-boundary rows converted
  into Fluid solver role rows.
- `train_solve_summary.csv`: one-row Fluid solve summary when the solve returns.
- `segment_states.csv`: Fluid segment states from the solve.
- `heat_path_ledger.csv`: segment heat-path ownership and external role-row
  mapping.
- `pressure_residual_attribution.csv`: pressure-root and residual attribution.
- `thermal_residual_attribution.csv`: train reference TP/TW/mdot residuals
  joined after the solve only.
- `runtime_leakage_audit.csv`: forbidden-runtime input and split checks.
- `split_claim_matrix.csv`: train/support, validation, holdout, and
  external-test claim separation.
- `failure_matrix.csv`: pass/fail/not-run execution gates.

## Claim Boundary

This is train execution evidence only. It is not a freeze decision, not model
selection, not validation scoring, not holdout scoring, not external-test
scoring, and not a final predictive admission. Salt 2 reference measurements are
joined only after the solve for residual attribution and are not runtime inputs.
