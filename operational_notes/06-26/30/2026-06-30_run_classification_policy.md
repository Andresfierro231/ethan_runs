# 2026-06-30 Run Classification Policy

## Observed

- Earlier notes left the workspace with mixed signals about whether Kirst runs
  were part of the usable comparison set:
  - `operational_notes/06-26/01/2026-06-01_modern_runs_first_batch_extraction_summary.md`
  - `operational_notes/06-26/01/2026-06-01_publish_handoff_gate.md`
  - `operational_notes/06-26/01/2026-06-01_todo.md`
  - `operational_notes/06-26/02/2026-06-02_todo.md`
- The active latest-window and continuation refresh work is centered on the
  continuation-derived Jin family rather than on Kirst parents:
  - `.agent/status/2026-06-22_AGENT-104.md`
  - `.agent/status/2026-06-23_AGENT-121.md`
  - `.agent/status/2026-06-23_AGENT-122.md`
  - `.agent/status/2026-06-23_AGENT-123.md`

## Inferred Interpretation

- Continuation runs are the current mainline Ethan run family whenever a case
  has a continuation artifact. Main documentation should surface the
  continuation package as the primary run.
- Perturbation runs remain valuable, but only as a separate
  sensitivity/correlation-support lane. They can inform correlations, trend
  checks, and robustness arguments without being promoted into the main-run
  set.

## Contradictions And Overrides

- Kirst runs are wrong for current mainline use and should not be treated as
  primary, nominal, or defended main-run inputs.
- Any older note that frames Kirst runs as part of the current main comparable
  set is superseded by this dated policy unless a later dated note explicitly
  restores a bounded Kirst use case.
- Perturbations should not be grouped into the same bucket as the main
  continuation runs even when they share downstream analysis products.

## Next Suggested Actions

- When campaign READMEs or report packages are next touched, label run groups
  explicitly as `mainline_continuation`, `perturbation_correlation_support`,
  or `historical_excluded_kirst` where relevant.
- Keep continuation artifacts visible from repo-entry documentation and future
  summary notes so the default reader path lands on the defended main runs
  first.
