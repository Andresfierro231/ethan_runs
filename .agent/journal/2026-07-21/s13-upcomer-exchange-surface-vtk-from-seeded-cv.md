---
provenance:
  - tools/extract/build_s13_upcomer_exchange_surface_vtk_from_seeded_cv.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv/released_surface_vtk_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv/surface_vtk_validation.csv
tags: [s13, upcomer-exchange, seeded-cv, surface-vtk, geometry-only, journal]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-FROM-SEEDED-CV-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv.json
task: TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-FROM-SEEDED-CV-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13 Surface VTK From Seeded CV

## Attempted

Generated geometry-only VTK surfaces from the released seeded source-bounded
face lists. The builder reads seeded exchange-interface and trusted-wall face
IDs, maps them to read-only OpenFOAM `polyMesh` points/faces, and writes
task-owned POLYDATA VTKs.

## Observed

- Six VTK files were generated: exchange-interface and trusted-wall surfaces
  for Salt2, Salt3, and Salt4.
- Every surface has `38880` polygons and `38928` points.
- Exchange-interface area is `0.0623473180949 m2` for each case.
- Trusted-wall area is `0.063435001093 m2` for each case.
- Count and area validation passed for `6/6` rows.
- The VTKs contain only geometry plus face metadata; no sampled CFD fields or
  `Q_wall_W` are present.

## Inferred

The seeded geometry is now usable as a trusted surface-geometry input for a
later sampled-field or sampler-manifest design row. It is not yet a production
exchange-QOI harvest path because the field sampling, wallHeatFlux integration,
same-window UQ, and sampler-ready manifest remain absent.

## Contradictions and Caveats

- Surface VTK readiness does not imply sampler readiness.
- `Q_wall_W` remains blocked because no wallHeatFlux integration was run or
released.
- No scheduler or OpenFOAM postprocessing action occurred; the VTKs were built
from existing mesh topology and released face IDs.

## Next Useful Actions

1. Claim a separate sampled-field extraction or sampler-manifest refresh row.
2. Decide how sampled `U`, `T`, `rho`, pressure, and wallHeatFlux/`Q_wall_W`
   should be produced from these geometry surfaces.
3. Keep production harvest, same-QOI UQ, S11/S12/S15/S6, fitting, and
   exchange-cell coefficient admission blocked until sampled-field and UQ gates
   release.
