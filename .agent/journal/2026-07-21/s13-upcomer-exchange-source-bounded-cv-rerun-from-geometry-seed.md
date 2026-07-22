---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed/seed_cv_release_decision.csv
tags: [journal, s13, upcomer-exchange, geometry-seed, source-bounded-cv]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.json
task: TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---
# S13 Source-Bounded CV Rerun From Geometry Seed

Observed: the right-leg geometry seed releases `3/3` geometry rows with
positive trusted wall and internal interface area and no unclassified escapes.

Observed: reverse-flow overlap within that seed is only `0`, `6`, and `15`
cells for Salt2/Salt3/Salt4. The seed is therefore geometry support, not an
admitted recirculating exchange state.

Inferred: S13 should remain fail-closed for production exchange-cell harvest.
The geometry blocker is narrowed, but surface extraction, source/sink ledgers,
wall `Q_wall_W`, and same-QOI UQ remain downstream prerequisites.

Caveat: no surface extraction, sampler, harvest, UQ, coefficient admission, or
S11/S12/S13/S15/S6 trigger was run.

Caveat: a concurrent Codex session generated and closed the final package while
a duplicate local builder run was still scanning topology. The duplicate run
was interrupted before it wrote an alternate output set; the validated package
is the one under the task work-product directory.

Next useful action: propose an exchange-state criterion that can use the
geometry seed without pretending tiny reverse overlap is a production
recirculation CV.
