---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/target_qoi_evidence.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/seeded_surface_input_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/same_qoi_neighbor_window_rows.csv
tags: [s13, upcomer-exchange, qwall, neighbor-window, same-qoi-uq]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-QWALL-NEIGHBOR-WINDOW-SAMPLING-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/README.md
task: TODO-S13-UPCOMER-EXCHANGE-QWALL-NEIGHBOR-WINDOW-SAMPLING-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Qwall Neighbor-Window Sampling

Decision: `target_minus_sampled_target_plus_missing_fail_closed`.

This package samples immediately preceding native time directories from
read-only `processors64` fields and joins them to the existing target-window
S13 QOI rows.

- cases: `3`
- QOI labels: `4`
- target rows: `12`
- target-minus rows sampled: `12`
- target-plus rows sampled: `0`
- same-QOI neighbor UQ-ready labels: `0`
- production harvest allowed: `false`

The new useful result is that target-minus values now exist for all requested
case/QOI rows. The remaining blocker is target-plus: Salt2/Salt3/Salt4 retained
targets are already the latest stored native time directories, so no later
same-label window is available from the existing source tree.

Do not move to mesh/GCI UQ or production harvest from this package. First
generate or locate later target-plus windows with the same QOI labels, formulas,
sign conventions, and geometry basis.
