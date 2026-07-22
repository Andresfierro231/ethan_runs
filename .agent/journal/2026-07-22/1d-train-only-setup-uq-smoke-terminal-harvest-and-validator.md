---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator/README.md
tags: [journal, predictive-1d, setup-uq, terminal-harvest, no-score]
related:
  - .agent/status/2026-07-22_TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-TERMINAL-HARVEST-AND-VALIDATOR-2026-07-22.md
  - imports/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator.json
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-TERMINAL-HARVEST-AND-VALIDATOR-2026-07-22
date: 2026-07-22
role: Scheduler Monitor / Forward-pred / Tester / Writer / Reviewer
type: journal
status: complete
---
# 1D train-only setup-UQ smoke terminal harvest

## Attempted

Claimed the terminal harvest row after Slurm job `3310985` reached terminal
state. Queried Slurm accounting, read the run provenance and logs, reran the
post-smoke validator, and summarized the baseline, variant, sensitivity, and
decision-gate outputs into a compact package.

## Observed

The job completed successfully with exit code `0:0` after `00:38:40` on
`c318-011`. The execution summary decision is
`train_only_setup_uq_smoke_executed_no_release_no_score`.

All three Salt2/Salt3/Salt4 baseline roots were accepted. All 33 one-at-a-time
setup-legal variant roots were accepted. The pressure-loss family produced the
largest mdot sensitivity in this smoke, while cooler-HX strength produced the
largest sensor-projection sensitivity. Residual-owner rows remain diagnostic
only because they report `diagnostic_missing_cp`.

## Inferred

The 1D smoke has done its job: it proves the train-only solve path and produces
useful setup-sensitivity rankings. It still cannot unlock admission, protected
scoring, or candidate freeze because source/property, residual-owner, and split
freeze gates remain separate.

## Caveats

The sensitivity values are smoke diagnostics, not model scores. The largest
sensor response should guide the next train-only analysis, but it cannot be
used to tune against validation, holdout, or external-test temperatures.

## Next Useful Actions

Use the smoke package to design a follow-on train-only review row that compares
pressure-loss, external-convection, cooler-HX, and heater-source placement
families against the residual-owner and source/property gates. Keep final score
values at `0` until a frozen runtime-legal candidate exists.
