---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/phase_f_thermal_residual_decomposition/dominant_thermal_residual_owners.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/phase_j_train_repair_decision/repair_candidate_manifest.csv
tags: [journal, fluid, external-bc, train-support, diagnostics, no-admission]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-FJ-PARALLEL-DIAGNOSTICS-2026-07-21.md
  - imports/2026-07-21_fluid_extbc_fj_parallel_diagnostics.json
task: TODO-FLUID-EXTBC-FJ-PARALLEL-DIAGNOSTICS-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Fluid External-BC F-J Parallel Diagnostics

## Attempted

Validated the completed F-J train/support diagnostics package. The package
recomputes or loads the Phase E Salt2 baseline, decomposes thermal residuals by
segment/source role, audits external-BC dictionary coverage, evaluates bounded
heat-loss sensitivities, checks runtime source/sink admissibility, and decides
whether a one-change train repair can be run.

## Observed

The train/support baseline remains finite but thermally poor: all-probe RMSE is
about `83.36 K`. The largest residual owner is `heated_incline`, with a maximum
absolute residual of about `109.09 K`. The dictionary audit has no unit/sign
failures, but Salt1 expected rows are still absent. Phase H ran only diagnostic
sensitivity rows; most sensitivity rows are blocked by policy. Phase I admits
no runtime source/sink rows. Phase J therefore correctly stops at
`blocked_no_repair_candidate` and does not run a repair solve.

## Inferred

The next predictive-model work should target the heated-incline wall/test
section residual owner with train/support diagnostics. The current evidence
does not justify candidate freeze, final scoring, validation/holdout/external
evaluation, or a hidden residual repair term.

## Contradictions Or Caveats

The package is useful for residual ownership and runtime legality, not for
model selection. It intentionally consumes no validation, holdout, or external
test rows.

## Next Useful Actions

1. Open a narrow train/support diagnostic row for heated-incline TW5/TW6,
   axial-mixing, or upcomer-stratification mechanisms.
2. Keep source/sink runtime inputs denied unless a future source/property row
   explicitly admits them.
3. Defer freeze/admission and final predictive scoring until source/property,
   uncertainty, and split-role gates pass.
