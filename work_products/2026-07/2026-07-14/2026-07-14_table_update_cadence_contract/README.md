---
provenance:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_math_theory_assumptions_results_register/README.md
tags: [table-cadence, coordination, blocker-register, admission, scorecard, thesis-source]
related:
  - .agent/journal/2026-07-14/table-update-cadence-contract.md
  - imports/2026-07-14_table_update_cadence_contract.json
task: AGENT-325
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Table Update Cadence Contract

This package implements the daily plus gate-triggered update cadence requested
for the CFD-to-1D closure workflow. It is infrastructure, not a scientific
result: it tells each active lane which tables to refresh when results arrive.

## Cadence

- Daily: run the checklist and record either updates or a no-gate-change note.
- Gate-triggered: update same day when blocker state, admission class,
  scorecard, boundary/API model, terminal CFD harvest, or thesis story changes.

## Outputs

- `table_update_contract.csv`: 8 table contracts.
- `gate_trigger_matrix.csv`: 6 trigger events.
- `daily_refresh_checklist.csv`: 5 daily steps.
- `active_result_watchlist.csv`: 18 board-derived watch rows.
- `summary.json`: machine-readable metadata.

## Guardrails

- Do not edit active-agent scopes to refresh tables.
- Do not resolve blockers from smoke or diagnostic evidence alone.
- Do not mix predictive, calibrated, diagnostic, reference-only, rejected, and
  blocked evidence in one result row.
- Do not regenerate generated index files unless the board row explicitly claims
  them.
