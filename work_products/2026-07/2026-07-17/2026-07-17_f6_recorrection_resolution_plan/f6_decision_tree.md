---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_candidate_inventory.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_admission_contract.md
tags: [f6, friction, recirculation, decision-tree]
related:
  - .agent/status/2026-07-17_AGENT-501.md
task: AGENT-501
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Re-Correction Decision Tree

Generated: `2026-07-17T20:04:44+00:00`

## Gate 1: Ordinary F6

A row can enter ordinary single-stream F6 only when `RAF < 0.01` and
`RMF < 0.01`, and when same-window pressure loss, Re/Ri/properties, and
split-safe validation/holdout scoring exist. Any material reverse flow blocks
ordinary `f_D`, ordinary F6, and component `K` fitting.

Current PM5 result: fail. The PM5 inventory has 12 rows and all 12 have
material reverse flow, so ordinary F6 has 0 scoreable rows.

## Gate 2: Recirculation-Modeled Lane

Material-recirculation rows may support a named section-effective loss,
mixing penalty, or onset/transition diagnostic. They cannot be reported as
ordinary friction. Promotion requires same-window RAF/RMF/SVF, wall-core or
wall-bulk Delta T, Gz, pressure residual movement, mesh/time uncertainty, and
validation/holdout improvement over `F3_shah_apparent` without a hidden global
multiplier.

Current PM5 result: diagnostic only. PM5 has RAF/RMF/SVF evidence, but it does
not have the full pressure, thermal, uncertainty, and split-score package.

## Gate 3: Follow-On Evidence

PM10 and high-heat runs should be harvested only after terminal completion.
If they produce low-reverse anchors, ordinary F6 can be revisited. If they
remain recirculating, use them only in the named recirculation/onset lane and
score against `F3_shah_apparent`.

## Current Production Decision

Keep `F3_shah_apparent` as production. Do not promote F6 or a recirculation
hybrid until one of the explicit lanes passes its full gate.
