---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/seeded_surface_input_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/sampled_field_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock/source_basis_audit.csv
tags: [s13, upcomer-exchange, pressure, wallHeatFlux, q-wall]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21.md
task: TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_input_release
---
# S13 Exact Pressure and Trusted-Wall Q Wall Compute

This package releases exact target-window pressure reductions and trusted-wall
`Q_wall_W` from read-only native OpenFOAM collated fields.

- cases processed: `3`
- pressure rows released: `3`
- `Q_wall_W` rows released: `3`
- detailed pressure sample rows: `233280`
- detailed trusted-wall heat-flux rows: `116640`
- native outputs mutated: `False`
- sampler/harvest/UQ/admission launched: `false`

`Q_wall_W` is positive into the seeded recirculation fluid. The native
OpenFOAM wallHeatFlux integral is retained separately as
`wallHeatFlux_integral_native_outward_W`; `Q_wall_W = -native_integral`.

This release does not put any missing heat residual into internal `Nu`.
Sampler refresh, production harvest, and same-QOI UQ are eligible for later
review only; they are not executed here.
