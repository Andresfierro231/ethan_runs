---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/seeded_surface_input_manifest.csv
tags: [s13, upcomer-exchange, diagnostic-average, thermal-reduction]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-AVERAGE-FIELD-THERMAL-REDUCTION-2026-07-21.md
task: TODO-S13-UPCOMER-EXCHANGE-AVERAGE-FIELD-THERMAL-REDUCTION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Diagnostic Average Field Thermal Reduction

This package computes diagnostic average reductions from existing whole-mesh
cell VTK `cellID`, `U`, `T`, and `rho` fields over the released seeded CV and
seed/core interface. It also reads OpenFOAM face area vectors to produce a
signed outward interface mass-flux proxy under the seeded-CV outward convention.
It is not a production sampler harvest.

Result: `diagnostic_average_proxy_complete_sampler_harvest_blocked`.

- cases reduced: `3`
- diagnostic metric rows: `3`
- average-field rows: `3`
- interface-proxy rows: `3`
- thermal-proxy rows: `3`
- sampler-ready rows: `0`
- admission-ready rows: `0`

The result supports continued S13/S12 diagnostic reasoning, but sampler
refresh, production harvest, same-QOI UQ, and coefficient admission remain
blocked.
