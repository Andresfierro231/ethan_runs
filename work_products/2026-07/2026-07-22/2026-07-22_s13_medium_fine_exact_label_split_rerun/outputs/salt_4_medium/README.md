---
provenance:
  generated_by: TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-EXACT-LABEL-SAMPLER-2026-07-22
  generated_at: 2026-07-22T11:59:50-05:00
tags: [s13, upcomer-exchange, medium-fine, exact-label-sampler, mesh-gci]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute
---

# S13 medium/fine exact-label sampler

This package rebuilds mesh-level S13 trusted-wall, exchange-interface, cap, and
recirculation-CV masks for Salt2/Salt3/Salt4 medium and fine source cases. In
execution mode it samples terminal candidate windows from read-only collated
OpenFOAM processor fields for `Q_wall_W`,
`mdot_exchange_positive_outward_proxy_kg_s`, `tau_recirc_proxy_s`, and
`wall_core_bulk_temperature_contrast_K`.

Decision: `terminal_exact_label_rows_sampled_mesh_gci_fail_closed_time_equivalence_missing`.

The source fields are not production-harvested or admitted here. The strict
coarse-contract physical windows are absent from the medium/fine cases, so the
same-label mesh/GCI gate remains fail-closed unless a later task supplies a
trusted terminal-window equivalence basis or exact same-time mesh-family rows.

## Key Outputs

- `source_preflight.csv`: source/run/path readiness.
- `mesh_level_geometry_summary.csv`: mesh-level CV and face-mask release
  status.
- `medium_fine_terminal_window_reductions.csv`: one row per sampled
  case/mesh/window when `--execute` is used.
- `medium_fine_exact_label_qoi_rows.csv`: long-form QOI rows for downstream
  same-QOI review.
- `mesh_gci_readiness_gate.csv`: fail-closed mesh/GCI disposition.
- `masks/` and `faces/`: generated geometry contracts by case/mesh.

## Guardrails

Native solver outputs were read only. No solver, OpenFOAM post-processing,
production harvest, registry mutation, coefficient admission, S11/S12/S13/S15
trigger, or proxy substitution is performed. Execution mode used here:
`true`.
