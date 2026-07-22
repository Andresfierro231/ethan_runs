---
provenance:
  generated_by: build_s13_upcomer_exchange_surface_vtk_disposition.py
  generated_at: 2026-07-21T17:18:18-05:00
tags:
  - s13
  - upcomer-exchange
  - surface-vtk
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/downstream_surface_vtk_inputs.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/interface_geometry_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/wall_core_band_contract.csv
---

# S13 Upcomer Exchange Surface VTK Disposition

This package applies the completed S13 geometry contract to the surface VTK
lane. Salt2, Salt3, and Salt4 have whole-mesh cell VTK inputs ready, but no
trusted exchange-interface surface, wall/core band surface, or same-window
`Q_wall_W` measurement is released.

Result: fail-closed. No scheduler job, surface extraction, sampler, harvest, or
native-output mutation occurred. The downstream manifest fragment keeps the
cell VTK paths visible while marking interface and wall inputs as missing.
