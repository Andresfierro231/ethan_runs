---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/same_qoi_neighbor_window_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/same_qoi_uq_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels/README.md
tags: [thesis, n2, s13, upcomer-exchange, qwall, panels, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-REFRESH-AFTER-NEIGHBOR-SAMPLING-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/README.md
task: TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-REFRESH-AFTER-NEIGHBOR-SAMPLING-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Figures / Tester / Writer / Reviewer
type: work_product
status: complete
---
# N2 Qwall/UQ Panel Refresh After Neighbor Sampling

Decision: `n2_refresh_ready_diagnostic_only_target_plus_missing`.

This addendum updates the N2 thesis/paper panel package with the new
target-minus sampling result. It preserves the diagnostic-only claim
boundary because target-plus rows are still absent.

- target rows ready: `12`
- target-minus rows sampled: `12`
- target-plus rows sampled: `0`
- same-QOI UQ-ready labels: `0`
- production harvest allowed: `false`

Qwall adjacent-window drift rows:

| case | target-minus s | target s | Qwall delta W | relative delta |
| --- | ---: | ---: | ---: | ---: |
| salt_2 | 7914 | 7915 | 6.64561000008e-05 | 2.87487912869e-06 |
| salt_3 | 7617 | 7618 | 1.41790000008e-05 | 5.59405546735e-07 |
| salt_4 | 9999 | 10000 | 0.0010252426 | 3.64554244946e-05 |

Use this package as a paper/thesis blocker panel, not as admission
evidence. Same-QOI UQ still requires target-minus / target /
target-plus triplets for each requested label.
