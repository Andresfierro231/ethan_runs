---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_case_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/same_qoi_neighbor_window_rows.csv
tags: [s13, upcomer-exchange, same-qoi-uq, temporal-uq]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-SAME-QOI-NEIGHBOR-UQ-AFTER-TARGET-PLUS-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix/README.md
task: TODO-S13-UPCOMER-EXCHANGE-SAME-QOI-NEIGHBOR-UQ-AFTER-TARGET-PLUS-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Same-QOI Neighbor UQ After Target-Plus

Decision: `same_qoi_neighbor_temporal_uq_executed_mesh_gci_ready_to_claim`.

This package executes temporal neighbor-window UQ from the complete
target-minus/target/target-plus table. It does not execute mesh/GCI UQ or
production harvest.

- case-level temporal UQ rows: `12`
- QOI-level UQ summaries: `4`
- temporal-UQ executed QOI labels: `4`
- mesh/GCI gate input ready: `true`
- heat-flow match diagnostic rows: `3`
- heat-flow match ready rows: `0`
- production harvest allowed: `false`

The heat-flow match diagnostic compares direct `Q_wall_W` against the
source-side static heat-flow fallback and the current exchange
`mdot_exchange * DeltaT_wall_core` scale. It intentionally does not tune a
coefficient. Current rows show that forcing these heat lanes to agree through
the present exchange scale would require unphysical heat-capacity-scale values;
the next scientific step is a same-mask production energy residual with
released property basis and harvested `T_recirc`/core enthalpy terms.

Next action: claim the S13 Qwall/exchange mesh/GCI UQ gate. That row must use a
same-label mesh family or fail closed; it must not borrow unrelated GCI.
