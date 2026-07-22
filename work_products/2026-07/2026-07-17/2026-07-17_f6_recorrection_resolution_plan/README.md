---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_candidate_inventory.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_admission_contract.md
  - work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/pm10_case_readiness.csv
  - work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/harvest_readiness_queue.csv
tags: [f6, friction, recirculation, blocker]
related:
  - .agent/status/2026-07-17_AGENT-501.md
  - .agent/journal/2026-07-17/f6-recorrection-resolution-plan.md
task: AGENT-501
date: 2026-07-17
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Re-Correction Resolution Plan

Generated: `2026-07-17T20:04:44+00:00`

## Answer

PM5 rows classify as recirculation diagnostics because all PM5 candidate rows
fail the low-reverse-flow gate for ordinary F6. The gate is `RAF < 0.01` and
`RMF < 0.01`; the current PM5 rows have material reverse flow, so they cannot
be used as ordinary single-stream `f_D`, F6, or component `K` rows.

## Current Counts

- PM5 rows reviewed: `12`.
- Ordinary F6 scoreable rows: `0`.
- Recirculation diagnostic rows: `12`.
- Hybrid/recirculation scoreable rows: `0`.
- Production closure: `F3_shah_apparent`.
- Promotion allowed now: `no`.

## Outputs

- `f6_row_gate_matrix.csv`
- `f6_decision_tree.md`
- `f6_resolution_scorecard.csv`
- `f6_next_action_queue.csv`
- `recommended_further_studies.md`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external
Fluid files, blocker register, generated index files, or active-agent scopes
were mutated. This package performs no terminal harvest and makes no
scientific admission change.
