---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_summary.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/summary.json
tags: [mf09, upcomer, recirculation, model-form, diagnostic-only]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/forward-predictive-model.md
---
# MF09 Recirculating-Upcomer Thermal Model Alternatives

MF09 compares the current upcomer alternatives without forcing the recirculating
upcomer into an ordinary single-stream pipe closure. It uses completed evidence
only and does not run CFD, harvest production samples, fit coefficients, release
source properties, or admit a candidate.

Decision: `blocked_missing_mesh_gci_source_basis`.

The best next science lane is
`MF09b_throughflow_plus_recirculation_exchange_cell_with_signed_wall_heat`, but
it is not smoke-ready: same-label mesh/GCI is missing for 4/4 S13 exchange QOIs,
source/property and `cp_J_kg_K` are not released, and production same-window
energy/pressure residual support is still blocked. Ordinary upcomer `Nu`,
`f_D`, and component `K` remain disabled.

Outputs:

- `variant_comparison_table.csv`
- `qoi_availability_and_uq_status.csv`
- `ordinary_upcomer_disabled_reasons.csv`
- `production_and_admission_gate.csv`
- `heat_flow_match_case_diagnostics.csv`
- `energy_residual_bridge_contract.csv`
- `next_work_package_queue.csv`
- `heat_path_guardrail_snapshot.csv`
- `onset_and_source_gap_snapshot.csv`
- `source_manifest.csv`
- `summary.json`

Guardrails:

- Do not relabel source-side static heat as direct `Q_wall_W`.
- Do not hide any heat/energy residual in internal Nu.
- Do not trigger S11/S12/S13/S15/S6 from this diagnostic gate.
