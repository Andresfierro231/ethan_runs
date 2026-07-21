---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/heat_path_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/split_claim_matrix.csv
tags: [forward-model, predictive-1d, thermal-boundary, runtime-leakage]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-D-SMOKE-SCORECARD-2026-07-21.md
  - imports/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/README.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-D-SMOKE-SCORECARD-2026-07-21
date: 2026-07-21
role: Forward-pred/Tester/Writer
type: journal
status: complete
---
# Fluid External BC Phase D Smoke Scorecard

## Attempted

I validated that Phase C closeout passed `finish_task`, then claimed Phase D and
built a package-local smoke scorecard. The smoke intentionally filtered the
repo-local external-boundary dictionary to a single `salt_2` train row so that
validation and holdout rows remained unconsumed.

The package imports the external Fluid parser and solver contract functions
read-only. It creates one filtered CSV, loads it through
`load_external_boundary_dictionary`, converts it to one solver role row, and
validates a `ScenarioConfig` with `outer_closure_mode=external_boundary_table`.
It then calls `ambient_loss_for_segment` for `left_upper_vertical` using a
synthetic setup trial state to exercise heat accounting.

## Observed

- Source dictionary rows: 24.
- Filtered smoke rows: 1.
- Records loaded: 1.
- Solver role rows created: 1.
- Solver contract validation: pass.
- Computed smoke heat loss: `65.37489732389939 W`.
- Validation rows consumed: 0.
- Holdout rows consumed: 0.
- External-test rows consumed: 0.

## Inferred

The file-facing external thermal boundary path is now runtime-addressable for a
minimal train/support case: dictionary row -> parser record -> solver role row
-> external-boundary contract -> heat-path accounting. This is enough to support
thesis wording that the runtime-legal external thermal input mechanism exists
and has a smoke-level heat ledger.

It is not enough to claim a predictive temperature model. The smoke did not run
the nonlinear solve, did not score TP/TW targets, did not use validation or
holdout rows, and did not test full-loop residual attribution.

## Caveats

The smoke uses synthetic `T_bulk=650 K` and `mdot=0.02 kg/s` as execution inputs
only. These are not CFD state values and should not appear in thesis text as a
Salt2 prediction. The row also covers only the upcomer ambient-wall lane; source
and sink roles remain document-only or separately blocked.

## Next Useful Actions

1. Publish the thesis-readiness integration package that routes Phase C/D,
   same-QOI Phase C, S8, S9, and S10 into Chapters 5-7 without overclaiming.
2. Claim a later Fluid scorecard row for a full setup-only scenario solve once
   source/property gates and current Fluid row conflicts permit it.
3. Keep validation, holdout, and external-test scoring separated until a frozen
   candidate and final scorecard row explicitly authorize those claims.
