---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/outputs
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_summary.csv
tags: [s13, upcomer-exchange, mesh-gci, thesis-evidence, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-S13-MESH-GCI-UPCOMER-EXCHANGE-EVIDENCE-PACKET-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-s13-mesh-gci-upcomer-exchange-evidence-packet.md
task: TODO-THESIS-S13-MESH-GCI-UPCOMER-EXCHANGE-EVIDENCE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Uncertainty / Writer / Reviewer / Tester
type: work_product
status: complete
---
# Thesis S13 Mesh/GCI Upcomer-Exchange Evidence Packet

Decision: `s13_medium_fine_exact_label_evidence_ready_gci_fail_closed_no_release`.

The repaired split rerun produced exact-label medium/fine rows for all three
Salt cases and all four S13 QOIs. This is useful thesis evidence because it
quantifies the mesh sensitivity of the exchange-cell observables. It is not a
GCI release: the coarse same-time same-label member is unavailable for these
terminal windows, so the packet remains fail-closed for production harvest,
source/property release, coefficient admission, candidate freeze, and scoring.

Key counts:

- exact-label QOI rows: `72`
- terminal QOI rows: `24`
- medium/fine comparison rows: `12`
- QOI gate rows: `4`
- accepted same-label GCI QOIs: `0`
- production harvest allowed: `false`

Open first:

- `mesh_level_terminal_qoi_table.csv`
- `medium_fine_delta_table.csv`
- `temporal_vs_mesh_uncertainty_table.csv`
- `gci_disposition_table.csv`
- `s13_predictive_path_status.csv`
