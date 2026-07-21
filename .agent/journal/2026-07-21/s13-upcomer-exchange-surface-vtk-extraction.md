---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - surface-vtk
  - journal
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-EXTRACTION-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_extraction/surface_input_disposition.csv
---

# S13 Upcomer Exchange Surface VTK Extraction Journal

Task: `TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-EXTRACTION-2026-07-21`

Observed: the geometry contract marks Salt2, Salt3, and Salt4 whole-mesh cell VTKs as ready. The same contract blocks exchange-interface VTK, wall/core VTK, `Q_wall_W`, and the exchange-cell harvest lane for all three cases.

Observed: interface geometry rows define only the future sign convention: positive `mdot_exchange` must point from recirculation cell toward main throughflow once a trusted interface exists. No numeric normal vector or interface path is released.

Inferred: there is no legal surface extraction to launch from this row. Launching now would invent a geometry/interface definition and would violate the fail-closed source policy.

Contradiction/caveat: older reusable scaffold templates still show missing cell VTK placeholders, but the newer S13 geometry contract supersedes that for the cell VTK lane only.

Next useful actions: pass the fail-closed downstream fragment to sampler manifest preflight. Reopen surface extraction only when a trusted exchange-interface source and wall/core band source are released.
