---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_c_implementation/summary.json
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/external_boundary.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
tags: [forward-model, predictive-1d, thermal-boundary, runtime-leakage]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-D-SMOKE-SCORECARD-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-external-bc-phase-d-smoke-scorecard.md
  - imports/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard.json
task: TODO-FLUID-EXTERNAL-BC-PHASE-D-SMOKE-SCORECARD-2026-07-21
date: 2026-07-21
role: Forward-pred/Tester/Writer
type: work_product
status: complete
---
# Fluid External BC Phase D Smoke Scorecard

This package proves the runtime-legal external thermal input path at smoke
scale. It filters the repo-local external-boundary dictionary to one
`salt_2` train/support predictive ambient-wall row, maps `upcomer:ambient_wall`
to `left_upper_vertical`, loads that row through the external Fluid parser,
converts it to solver role rows, validates the solver contract, and computes
one setup-only heat-path accounting value from a synthetic trial state.

## Outputs

- `smoke_scorecard.csv`: parser, role-row, solver-contract, and heat-accounting
  status for the single train/support smoke row.
- `heat_path_ledger.csv`: external `h`, area, ambient/surroundings temperature,
  emissivity, drive selector, and computed heat loss for the smoke path.
- `runtime_leakage_audit.csv`: train-only consumption and forbidden-runtime
  checks.
- `failure_matrix.csv`: pass/fail/not-run status for each execution gate.
- `split_claim_matrix.csv`: explicit train, validation, holdout, and
  external-test claim boundaries.
- `source_manifest.csv`: source and mutation provenance.

## Claim Boundary

This is not a Salt2 predictive solve, not a scorecard, not a fit, not model
selection, and not an admission. Validation, holdout, and external-test rows
were not consumed. The synthetic `T_bulk=650 K` and `mdot=0.02 kg/s` values
exercise heat accounting only; they are not CFD values and do not support a
temperature prediction claim.
