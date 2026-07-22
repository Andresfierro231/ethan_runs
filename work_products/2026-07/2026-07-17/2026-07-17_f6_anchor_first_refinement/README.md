---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_recorrection_resolution_plan/f6_row_gate_matrix.csv
  - work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/pm10_case_readiness.csv
  - work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/harvest_readiness_queue.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/proposed_cfd_run_matrix.csv
tags: [f6, friction, recirculation, anchor-first]
related:
  - .agent/status/2026-07-17_AGENT-505.md
  - .agent/journal/2026-07-17/f6-anchor-first-refinement.md
task: AGENT-505
date: 2026-07-17
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Anchor-First Refinement

Generated: `2026-07-17T20:25:16+00:00`

## Decision

This package keeps the F6 avenue open but does not promote a new closure.
The next research move is anchor-first: terminal high-heat and PM10 evidence
must be harvested and gated before ordinary F6 or a named recirculation closure
can be scored.

## Current Counts

- PM5 rows reviewed: `12`.
- PM5 ordinary anchor rows: `0`.
- PM5 recirculation diagnostic rows: `12`.
- PM10/high-heat blocked rows: `8`.
- Recommended Salt3 CFD rows if evidence remains insufficient: `11`.
- Production closure: `F3_shah_apparent`.
- Promotion allowed now: `no`.

## Outputs

- `terminal_status_refresh.csv`
- `anchor_gate_table.csv`
- `f6_lane_decision.csv`
- `pressure_residual_scorecard.csv`
- `recommended_next_cfd_runs.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external
Fluid files, blocker register, generated index files, or active-agent scopes
were mutated. Optional live scheduler checks are read-only and do not replace a
separately claimed terminal harvest task.
