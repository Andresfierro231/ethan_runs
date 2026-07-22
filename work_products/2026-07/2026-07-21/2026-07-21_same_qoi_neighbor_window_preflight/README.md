---
task: TODO-SAME-QOI-NEIGHBOR-WINDOW-PREFLIGHT-2026-07-21
date: 2026-07-21
role: cfd-pp / Mesh-GCI / Tester / Writer
type: work_product
status: complete
tags: [same-qoi-uq, neighboring-window, mesh-gci, no-admission]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_a_retained_window_inventory
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_c_admission_table
---
# Same-QOI Neighboring-Window Preflight

This package converts the Phase C same-QOI admission table into an executable
next-task queue. It does not search native case directories, launch samplers,
compute drift, invent GCI, or change admission state.

## Results

- QOI rows reviewed: `12`
- accepted after preflight: `0`
- compute-needed rows: `12`
- P1 pressure/F6 rows: `4`
- P2 recirculation/upcomer rows: `4`
- scheduler action: `false`
- admission change: `false`

## Outputs

- `neighbor_window_preflight.csv`
- `compute_needed_queue.csv`
- `admission_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Thesis-Safe Claim

No same-QOI uncertainty row is admitted. The next useful work is to handle P1
pressure/F6 rows first, then exchange/terminal-harvest rows after their inputs
exist. Thermal and heat-loss candidate rows remain policy/candidate gated.
