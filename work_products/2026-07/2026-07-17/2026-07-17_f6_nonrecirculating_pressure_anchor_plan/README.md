---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_candidate_inventory.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_recorrection_resolution_plan/f6_row_gate_matrix.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/anchor_gate_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/named_pressure_readiness.csv
tags: [f6, pressure-anchor, recirculation, hydraulics]
related:
  - .agent/status/2026-07-17_TODO-F6-NONRECIRC-PRESSURE-ANCHOR-PLAN.md
  - .agent/journal/2026-07-17/f6-nonrecirculating-pressure-anchor-plan.md
task: TODO-F6-NONRECIRC-PRESSURE-ANCHOR-PLAN
date: 2026-07-17
role: Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Non-Recirculating Pressure Anchor Plan

## Decision

No F6 or pressure coefficient is fitted here. Current PM5 rows remain recirculation diagnostics. Pending PM10/high-heat rows are ordinary-anchor candidates only after terminal harvest and low-reverse, same-window pressure gates pass.

## Results

- Current PM5 rows reviewed: `12`.
- Current legitimate ordinary F6 anchors: `0`.
- Current recirculation diagnostic rows: `12`.
- Pending ordinary-anchor candidate rows: `8`.
- Named pressure slots reviewed: `33`.
- Fitting performed: `False`.

## Outputs

- `f6_pressure_anchor_plan.csv`: row-level current and pending anchor classification.
- `named_pressure_anchor_slots.csv`: branch/straight/component pressure-row roles for future F6 use.
- `ordinary_anchor_gate_contract.csv`: exact gates required before ordinary F6 evidence exists.
- `next_action_plan.csv`: non-fitting sequence for attacking `f6-friction-re-correction`.
- `runtime_request_audit.csv`: no-fit/no-launch/no-mutation audit.

## Scientific Guardrail

A pressure row is not a legitimate ordinary F6 anchor unless reverse flow is negligible, pressure and velocity are same-window and geometry-normalized, straight/development/component losses are separated, and mesh/time uncertainty is reported. Until then, rows remain diagnostic.
