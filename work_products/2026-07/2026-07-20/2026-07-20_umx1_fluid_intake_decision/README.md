# AGENT-558 UMX1 Fluid Intake Decision

Task: `AGENT-558`

This package ingests the completed external Fluid UMX1 follow-up row
`impl-2026-07-20-fluid-umx1-tswfc2-smoke-followup` without editing Fluid,
launching solvers, touching native CFD outputs, mutating registry/admission
state, or running a score grid.

## Decision

`blocked_not_scorecard_ready_no_grid`

The important change is that the UMX1 Salt3/Salt4 root-handling blocker is now
cleared at smoke level: `umx1_bracket_smoke_v1` completed `12` rows with `12`
accepted and `0` rejected. Upcomer reservoir energy residuals are zero across
the reviewed segment ledgers.

That does not make UMX1 scorecard-ready. The best exchange variant is still
worse than the radiation-on baseline:

- Baseline radiation-on: all-sensor RMSE `69.693542 K`.
- Exchange low, radiation-on: all-sensor RMSE `70.242831 K`.
- Exchange mid, radiation-on: all-sensor RMSE `71.040740 K`.
- Combined UMX1 plus TSWFC2 smoke: all-sensor RMSE `97.990763 K`.

AGENT-557 also closed the bounded TSWFC2 nominal candidate as
`not_admitted_no_grid_expansion`, so TSWFC2 does not supersede UMX1. The current
state is: roots are unlocked, but the candidate physics and source/property
release gates are not.

## Files

- `source_manifest.csv` lists the read-only Fluid and repo evidence consumed.
- `root_and_ledger_audit.csv` records accepted roots and ledger residual checks.
- `scenario_score_intake.csv` preserves the scenario-level smoke metrics used
  for the decision.
- `decision_matrix.csv` gives the direct blocker/readiness conclusions.
- `summary.json` is the machine-readable closeout summary.

## Next Step

Do not run a UMX1 grid from the current exchange variants. The next useful work
is a new physical candidate or release-gate package: richer setup-only
stratification/onset evidence, source/property envelope closure, or a revised
wall/test-section/passive-boundary model. The accepted-root UMX1 Fluid API can
then be reused as the execution substrate for a bounded smoke, not a broad grid.
