# Time-Window Quasi-Steady Contract

Date: `2026-07-07`  
Task: `AGENT-190`  
Role: Coordinator / Writer

## Objective

Make the use of time-dependent CFD data scientifically conservative: time
samples become curated quasi-steady observations with temporal uncertainty, not
unvetted independent closure-training rows.

## Contract Added

- Window states: `stationary`, `quasi_stationary`, `moving_not_plateaued`,
  `oscillatory_not_steady`, `short_or_early_terminated`,
  `transient_model_only`.
- Required uncertainty components: autocorrelation/random uncertainty,
  oscillation envelope or block-to-block variability, and drift uncertainty.
- Required independence guard: multiple windows from one relaxation path share
  an `independence_group_id` and cannot be treated as independent fit rows.
- Explicit pass-through guard: reaching a target value while relaxing is not a
  new equilibrium unless the run has moved and re-plateaued.

## Board Follow-Up

`TODO-TIME-QUASI-STEADY-UQ` is now on `.agent/BOARD.md`. The implementation task
should build a read-only tool and dated work-product package with CSV/JSON/README
and tests.

## Exact Next Action

Implement the curation tool as a separate task. Start from
`tools/analyze/assess_time_convergence.py`, then add block means, oscillation
period/envelope diagnostics, total temporal uncertainty, and window-level
admission fields.
