---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/phase_f_thermal_residual_decomposition/dominant_thermal_residual_owners.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/phase_h_heatloss_network_sensitivity/sensitivity_matrix.csv
tags: [forward-model, external-bc, thermal-residual, runtime-leakage]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-FJ-PARALLEL-DIAGNOSTICS-2026-07-21.md
  - imports/2026-07-21_fluid_extbc_fj_parallel_diagnostics.json
task: TODO-FLUID-EXTBC-FJ-PARALLEL-DIAGNOSTICS-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Fluid External-BC F-J Parallel Diagnostics

## Attempted

Claimed a single non-overlapping F-J task row and implemented a task-local
builder/checker under
`work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/`.
The builder uses completed Phase E as the baseline, recomputed a local
validation-provenance table for segment-level attribution, and wrote F/G/H/I/J
subpackages.

The original Phase H implementation attempted the full foreground sensitivity
matrix. The first non-baseline perturbation exceeded practical foreground
runtime and had to be interrupted. A signal-based timeout guard also did not
interrupt the Fluid call promptly. The final implementation therefore records
non-baseline sensitivity rows as blocked for a separate compute-safe row rather
than leaving the agent in an unbounded login-node solve.

## Observed

Phase E baseline remains executable and pressure-balanced:
`mdot=0.006265675 kg/s`, pressure residual `-1.301687e-06 Pa`, and accepted
root. Temperature residuals remain large: all-probe MAE `81.582 K`, TP MAE
`80.249 K`, TW MAE `82.187 K`, max absolute error `109.094 K`.

The dominant residual owner is `heated_incline` with dominant sensor `TW5`.
The lower-leg ambient-wall source-family row has the same top residual
ownership. Downcomer/right-vertical and cooling/junction top-exit rows are the
next major owners.

Phase G confirms Salt1 is missing from the current external-BC dictionary
(`8` expected rows missing), while Salt2/Salt3/Salt4 dictionary rows exist.
Document-only source/sink rows are present (`9`) but not runtime-admitted.
Unit/sign checks on present rows pass.

Phase I admits no source/sink runtime input. The current heater/cooler/test
section rows trace to diagnostic CFD wallHeatFlux paths and remain forbidden.

## Inferred

The Phase E result is useful as a train-only diagnostic baseline, but it is not
a predictive temperature candidate. The evidence points first to heated-incline
thermal ownership and source/sink admissibility, not to a final scorecard.

Because Phase H perturbation solves did not complete safely in foreground, the
next rigorous sensitivity step should be a separately claimed compute-safe row
that runs each predeclared perturbation in an isolated subprocess or scheduler
job with hard wall-clock limits and partial-result flushing.

## Caveats

The Phase F provenance table uses a recomputed Phase E-style local Fluid
baseline generated before the interrupted sensitivity attempts. This is a
post-solve train reference join and is not a validation/holdout/external score.

The Phase H matrix is a disposition matrix, not a completed sensitivity
scorecard. It records exactly which perturbations should run next and why they
were not completed in this foreground package.

## Next Useful Actions

Claim a compute-safe Phase H follow-up row that runs one sensitivity at a time
with subprocess timeout, per-row output flushing, and no branch-on-score
selection. Prioritize `lower_leg_hA_scale_0.5/2.0`, then global hA scale, then
ambient drive perturbations. Do not run Phase J repair until Phase G releases a
deterministic mapping/unit/sign correction or Phase I releases one setup-known
source/sink field.
