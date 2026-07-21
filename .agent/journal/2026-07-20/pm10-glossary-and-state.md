---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification/pm10_terminal_drift.csv
  - work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification/pm10_terminal_admission_rows.csv
  - work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification/pm10_split_decisions.csv
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
tags: [pm10, split-policy, terminal-admission, holdout, current-state]
related:
  - .agent/status/2026-07-20_AGENT-555.md
  - imports/2026-07-20_pm10_glossary_and_state.json
task: AGENT-555
date: 2026-07-20
role: Coordinator/Writer
type: journal
status: complete
---
# PM10 Glossary And State

Task: AGENT-555

## Attempted

Answered whether the PM10 cases reached steady state and added a glossary-style
expansion for PM10 in the canonical final split policy note.

## Observed

The PM10 classification package covers four corrected-Q perturbation rows:
`salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and `salt4_hi10q`.

All four rows have `terminal_drift_status=pass`, `plateau_like=True`,
`moved_enough=True`, `mdot_direction_ok=True`, `preflight_overall_ok=True`,
`strict_log_status=pass`, and `strict_fatal_count=0`. The late-window mdot
drift percentages are small: `0.00790594`, `0.101131805`, `0.052102218`, and
`-0.486409185`.

The same admission table records
`terminal_scheduler_context=solver_timeout_harvest_completed` and
`terminal_holdout_classification=admitted_for_future_holdout_scoring_after_final_freeze`
for each row. It also records `pressure_upcomer_status` as
`diagnostic_blocked_pending_pm10_matched_plane_extraction`.

## Inferred

The best short answer is: the PM10 rows are at accepted terminal steady state
for the current heat/mass-flow admission gate, despite the solver walltime stop.
They are score-ready as future/frozen-model holdout rows after final freeze.
They are not fit-admitted, model-selection-admitted, or runtime-input-admitted,
and they do not yet unblock pressure/upcomer closure use.

## Contradictions Or Caveats

The terminal evidence is not the same as a full closure package. The current
policy explicitly forbids training or model selection on PM10 rows. Pressure and
upcomer diagnostics remain blocked until PM10 matched-plane extraction lands.

## Next Useful Actions

If PM10 needs to move beyond terminal holdout scoring, claim a separate
postprocessing/admission row to extract the matched-plane pressure/upcomer
diagnostics and publish a closure-use decision. Do not reuse PM10 rows for
fitting or tuning without a new dated policy change.
