---
provenance:
  generated_by: build_s13_upcomer_exchange_same_window_uq_design.py
  generated_at: 2026-07-21T17:18:18-05:00
tags:
  - s13
  - upcomer-exchange
  - same-qoi-uq
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_c_admission_table/same_qoi_uq_admission_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/downstream_surface_vtk_inputs.csv
---

# S13 Upcomer Exchange Same-Window UQ Design

This package defines the UQ gate for S13 exchange-cell QOIs before any
production harvest can be used in an S11 candidate review.

Result: fail-closed. The retained-time evidence is not enough: each target QOI
still needs same-label neighboring windows, accepted same-QOI mesh/GCI evidence,
and trusted interface/wall/source geometry. No sampler, postprocessing, solver,
fit, score, or admission step was launched.

Primary outputs:

- `uq_acceptance_contract.csv`
- `neighbor_window_requirements.csv`
- `mesh_gci_requirements.csv`
- `qoi_release_decision.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

The next useful action is to keep this design as the gate for S13 and proceed
only to sampler manifest preflight after the surface/geometry inputs are either
released or explicitly fail-closed.
