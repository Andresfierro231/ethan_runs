---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregated_exact_label_qoi_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregated_terminal_window_reductions.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_summary.csv
tags: [work-product, s13, recirculation, exchange-cell, mesh-gci, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-MESH-GCI-DISPOSITION-2026-07-22.md
  - .agent/journal/2026-07-22/s13-medium-fine-mesh-gci-disposition.md
task: TODO-S13-MEDIUM-FINE-MESH-GCI-DISPOSITION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Medium/Fine Mesh-GCI Disposition

This package consumes the completed S13 exact-label split rerun and reports
medium/fine mesh sensitivity for the four exchange-cell QOIs. It does not run a
formal Grid Convergence Index because this evidence family has no strict
same-label coarse member.

## Decision

`medium_fine_mesh_disposition_complete_formal_gci_fail_closed_no_admission`

## What Is Defensible

- `case_qoi_medium_fine_spread.csv` quantifies Salt2/Salt3/Salt4 medium/fine
  spread for `Q_wall_W`, `mdot_exchange_positive_outward_proxy_kg_s`,
  `tau_recirc_proxy_s`, and `wall_core_bulk_temperature_contrast_K`.
- `qoi_mesh_disposition_summary.csv` separates low diagnostic spread from
  large fail-closed spread.
- `formal_gci_blocker_table.csv` records why formal Richardson/GCI remains
  blocked.

## Guardrails

No native solver output, registry/admission state, scheduler state, Fluid source,
external repo, thesis body, source/property release, Qwall release, coefficient
fit, validation/holdout/external score, production harvest, or generated docs
index was mutated.
