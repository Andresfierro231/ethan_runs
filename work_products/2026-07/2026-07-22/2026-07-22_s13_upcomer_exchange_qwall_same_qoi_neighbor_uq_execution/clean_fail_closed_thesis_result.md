---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/target_qoi_evidence.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/neighbor_window_inventory.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/same_qoi_uq_matrix.csv
tags: [s13, upcomer-exchange, same-qoi-uq, fail-closed, thesis-result]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-QWALL-SAME-QOI-NEIGHBOR-UQ-EXECUTION-2026-07-22.md
task: TODO-S13-UPCOMER-EXCHANGE-QWALL-SAME-QOI-NEIGHBOR-UQ-EXECUTION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Writer / Reviewer
type: work_product
status: complete
---
# S13 Same-QOI Neighbor-Window Fail-Closed Result

Decision: `fail_closed_neighbor_window_uq_missing`.

Target-window evidence is present for the requested S13 QOI labels across
Salt2, Salt3, and Salt4, including the direct trusted-wall `Q_wall_W` rows.
However, exact same-label target-minus and target-plus neighboring windows are
missing for all four requested QOI labels:

- `Q_wall_W`
- `mdot_exchange_positive_outward_proxy_kg_s`
- `tau_recirc_proxy_s`
- `wall_core_bulk_temperature_contrast_K`

This is a clean negative uncertainty result. It supports thesis language that
S13 has diagnostic target-window exchange and heat-flow evidence, but it does
not support production harvest, coefficient admission, model fitting, validation
scoring, or any S11/S12/S13/S15/S6 trigger.

Next scientific unlock: generate or locate exact same-label target-minus and
target-plus rows for the four QOI labels above. Only after that should a
separate mesh/GCI UQ gate run.
