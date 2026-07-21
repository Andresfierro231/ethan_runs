---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/failure_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/runtime_leakage_audit.csv
tags: [forward-model, predictive-1d, thermal-boundary, runtime-leakage]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-E-TRAIN-FULL-SOLVE-2026-07-21.md
  - imports/2026-07-21_fluid_external_bc_phase_e_train_full_solve.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/README.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-E-TRAIN-FULL-SOLVE-2026-07-21
date: 2026-07-21
role: Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Fluid External BC Phase E Train Full Solve

## Attempted

I claimed a narrow Phase E row because an existing active attribution/freeze
row overlapped the topic but forbade solver launch. This row used separate
package-local paths and allowed only a local Fluid 1D `solve_case` run.

The builder filtered the external-boundary dictionary to current train/support
rows for `salt_2`, converted only predictive passive rows into Fluid role rows,
and kept heater, cooler, and test-section source/sink rows document-only. It
then ran `Salt 2` through `ScenarioConfig(outer_closure_mode="external_boundary_table")`.

## Observed

The solve completed and accepted the numerical roots:

- selected train/support rows: 8
- predictive role rows: 12
- document-only selected rows: 3
- `mdot_kg_s = 0.00626567502343775`
- `pressure_residual_Pa = -1.3016870923365786e-06`
- `temperature_periodicity_error_K = 4.201831416139612e-08`
- validation/holdout/external-test rows consumed: `0/0/0`

Post-solve train residuals are large: mdot residual is
`-0.010534324976562249 kg/s`, TP MAE is `80.24939106239617 K`, TW MAE is
`82.18702596558934 K`, and max absolute temperature residual is
`109.09380824932663 K`.

## Inferred

The external-boundary runtime path has moved from smoke to full local Fluid
execution. The accepted root is useful because it proves the numerical path can
run with all current `salt_2` train passive external-boundary rows. The residuals
are also useful because they show that external passive boundary setup alone is
not a credible frozen predictive candidate.

This supports the next scientific move: attribution/freeze work should focus on
why the train solution over-loses heat and under-predicts mdot/temperatures
before any validation or holdout score is released.

## Caveats

Salt 2 reference mdot and temperatures were joined only after the solve for
train residual attribution. They were not passed into `solve_case`, and this row
does not claim validation scoring. The result is not a model freeze, not a
closure admission, and not a final predictive score.

## Next Useful Actions

1. The active attribution-freeze row can consume this package as read-only
   evidence and decide whether to fail closed or request a new physical change.
2. A follow-up should separate whether the large negative TP/TW residuals arise
   from passive external-loss overcoverage, missing source/sink physics, pressure
   underprediction, or current default Fluid closure assumptions.
3. Validation, holdout, and external-test scoring should remain blocked until a
   candidate is frozen before looking at protected rows.
