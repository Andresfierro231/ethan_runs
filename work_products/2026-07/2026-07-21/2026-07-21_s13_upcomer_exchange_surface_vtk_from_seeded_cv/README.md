---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed/seeded_exchange_interface_faces.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed/seeded_trusted_wall_faces.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/summary.json
tags: [s13, upcomer-exchange, seeded-cv, surface-vtk, geometry-only]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-FROM-SEEDED-CV-2026-07-21.md
task: TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-FROM-SEEDED-CV-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_geometry_surface_vtk
---
# S13 Seeded-CV Geometry Surface VTK

This package writes geometry-only VTK surfaces from released seeded face IDs
and read-only OpenFOAM `constant/polyMesh` topology. It emits one seeded
exchange-interface VTK and one trusted-wall VTK for each of Salt2, Salt3, and
Salt4.

Decision: `geometry_only_surface_vtk_released`.

- cases processed: `3`
- VTK surface rows: `6`
- validated VTK surface rows: `6`
- sampled CFD fields present: `false`
- `Q_wall_W` released: `false`
- sampler/harvest allowed: `false`
- same-QOI UQ ready: `false`
- S11/S12/S15/S6 trigger: `false`

These VTKs are suitable as trusted geometry inputs for the next field-sampling
or sampler-manifest design row. They are not production harvest outputs and do
not admit an exchange-cell coefficient.
