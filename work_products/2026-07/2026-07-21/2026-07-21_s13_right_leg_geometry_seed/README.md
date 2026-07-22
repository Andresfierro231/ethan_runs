---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/release_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/recirc_segmentation_case_summary.csv
tags: [s13, upcomer-exchange, geometry-seed, right-leg, s12]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/s12_unlock_gate.csv
task: TODO-S13-RIGHT-LEG-GEOMETRY-SEED-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Right-Leg Geometry Seed

This package builds a predeclared geometry-backed right-leg/upcomer seed from
trusted wall patches `pipeleg_right_01_lower`, `pipeleg_right_02_middle`, and
`pipeleg_right_03_upper`. The seed is the conservative wall-adjacent owner-cell
set for those patches; internal faces from those cells are classified as the
candidate interface lane for the next source-bounded CV rerun.

Decision: `released_geometry_seed_ready_for_source_bounded_rerun`.

Reverse-flow occupancy is diagnostic only. It is reported to compare the new
geometry seed with prior velocity masks, but it does not select, release, or
fit the seed.

This package does not run surface extraction, sampler refresh, harvest,
same-QOI UQ, Fluid/S12 implementation, S11/S15/S6 trigger, fitting, model
selection, registry/admission mutation, scheduler action, native-output
mutation, or residual absorption into internal Nu.
