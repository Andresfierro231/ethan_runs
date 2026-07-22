---
task: TODO-S13-NEXT-GATE-CHECKLIST-AND-BLOCKER-UNLOCKS-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Reviewer / Writer / Tester
type: work_product
status: complete
tags: [s13, upcomer-exchange, heat-loss-alignment, next-gate, blockers]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight
---
# S13 Next-Gate Checklist and Blocker Unlocks

This package is a read-only next-gate checklist for S13 after the geometry seed
and seeded source-bounded rerun evidence. It separates geometry readiness from
production heat-path and admission readiness.

## Decision

- cases reviewed: `3`
- geometry seed ready rows: `3`
- seeded surface-preflight ready rows: `3`
- production source-bounded CV rows released: `0`
- sampler-ready rows released: `0`
- same-QOI release rows allowed now: `0`
- scheduler action: `false`
- native-output mutation: `false`

The next useful S13 work package is a separately claimed seeded surface/input
preflight. It should consume the materialized seeded face lists and either
release or fail-close interface/wall VTK surfaces, normals, `Q_wall_W` or a
source-side equivalent, same-window thermal fields, and the source/sink
sign/cp ledger.

## Outputs

- `next_gate_checklist.csv`
- `s13_geometry_evidence_summary.csv`
- `blocker_unlock_queue.csv`
- `heat_path_alignment_guardrails.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Do Not Do

Do not launch surface extraction, sampler, harvest, UQ, fitting, admission, or
S11/S12/S15/S6 from this package. Do not hide a heat residual in internal `Nu`.
Keep internal convection, wall conduction, insulation/quartz, external
convection, radiation, jacket/cooler/source, storage, and residual lanes
separate until explicit source-backed terms exist.
