---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_smoke_scenario/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_forward_blocker_unlock_runbook/next_agent_contracts.csv
  - work_products/2026-07/2026-07-20/2026-07-20_final_scorecard_source_property_refresh/README.md
tags: [forward-model, tswfc2, bounded-scorecard, wall-test-section]
related:
  - .agent/status/2026-07-20_AGENT-557.md
  - .agent/journal/2026-07-20/tswfc2-bounded-nominal-scorecard.md
task: AGENT-557
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer/Tester
type: work_product
status: complete
---
# TSWFC2 Bounded Nominal Scorecard

Decision: `not_admitted_no_grid_expansion`.

This package runs the single predeclared AGENT-553 four-node TSWFC2 candidate
against Salt1-4 nominal cases. It is not a broad grid, fit, model-selection
run, blocker-register update, or scientific admission change.

## Outputs

- `case_split_contract.csv`
- `candidate_definitions.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `root_status_by_case.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `candidate_admission_review.csv`
- `source_property_gate_report.csv`
- `case_outputs/*/summary.csv`
- `case_outputs/*/segment_states.csv`
- `summary.json`

## Result

- Root gate all pass: `True`.
- Source/property gate all pass: `False`.
- Numerical coupled gate all pass: `False`.
- Admission decision: `not_admitted`.
- Blocking reasons: `source_property_gate_blocked;numerical_coupled_gate_failed_or_missing_m3`.

Validation records are used only after `solve_case` returns, for scoring. They
are not runtime inputs to the forward model.
