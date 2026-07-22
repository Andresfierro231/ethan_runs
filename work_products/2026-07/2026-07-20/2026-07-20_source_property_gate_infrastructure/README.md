---
provenance:
  - tools/agent/source_property_gate.py
  - tools/agent/finish_task.py
  - work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/
tags: [source-property-gate, agent-tooling, scorecard-enforcement]
related:
  - operational_notes/maps/agent-operations.md
  - operational_notes/maps/literature-synthesis-and-gates.md
task: AGENT-554
date: 2026-07-20
role: Implementer/Tester
type: work_product
status: complete
---
# Source/Property Gate Infrastructure

AGENT-554 promoted the AGENT-546 source/property gate policy into reusable
repo tooling:

- `tools/agent/source_property_gate.py` audits scorecard-like CSVs for
  fit/admission candidate rows and reports source/property failure modes.
- `tools/agent/finish_task.py` now emits warning-mode
  `SOURCE_PROPERTY_GATE_WARNING` messages for changed scorecard-like CSVs
  unless a task manifest declares `no_scorecard_outputs: true`.
- `tools/agent/test_agent_tools.py` covers complete labels, missing labels,
  blocked label content, warning behavior, and warning suppression.

## Current TODO Ledger

`final_scorecard_source_property_todo.csv` is the durable follow-up ledger
generated from the current final predictive scorecard shell.

Observed warning result:

- Candidate rows: `22`
- Rows with source/property findings: `22`
- Failure modes:
  - `candidate_allowed_but_source_property_blocked`: `22`
  - `diagnostic_or_no_fit_source_use`: `22`
  - `outside_or_mixed_source_envelope`: `21`
  - `refresh_required_label_content`: `1`
  - `source_property_gate_blocked`: `1`

## Guardrails

This task changed tooling and documentation only. It did not rewrite historical
scorecards, mutate native CFD/OpenFOAM outputs, change registry/admission
state, act on the scheduler, edit Fluid, fit/tune/select a model, or make a
scientific admission change.
