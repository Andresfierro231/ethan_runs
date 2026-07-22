---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/target_plus_qoi_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/same_qoi_neighbor_triplet_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/job_terminal_status.csv
tags: [s13, upcomer-exchange, target-plus, same-qoi-uq]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-SAME-QOI-HARVEST-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/README.md
task: TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-SAME-QOI-HARVEST-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Target-Plus Same-QOI Harvest

Decision: `target_plus_same_qoi_rows_harvested_triplets_ready_uq_not_executed`.

This package harvested the staged target-plus windows and joined them to the
existing target-minus/target S13 evidence. It does not execute UQ or production
harvest.

- target-plus QOI rows: `12`
- joined triplet rows: `12`
- same-QOI triplet-ready labels: `4`
- same-QOI UQ executed: `false`
- production harvest allowed: `false`

Next action: claim a separate same-QOI neighbor UQ execution row using the
complete triplet table. Mesh/GCI UQ and production harvest remain closed until
that row passes.
