---
provenance:
  - tools/extract/build_s13_upcomer_exchange_surface_vtk_from_seeded_cv.py
  - tools/extract/test_s13_upcomer_exchange_surface_vtk_from_seeded_cv.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv/released_surface_vtk_manifest.csv
tags: [s13, upcomer-exchange, seeded-cv, surface-vtk, geometry-only, status]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-surface-vtk-from-seeded-cv.md
  - imports/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/summary.json
task: TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-FROM-SEEDED-CV-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-FROM-SEEDED-CV-2026-07-21

## Objective

Generate task-owned geometry-only VTK surfaces for the seeded exchange interface
and trusted wall/core band from released seeded face IDs and read-only OpenFOAM
`constant/polyMesh` topology.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv/`.

Key results:

- Geometry-only surface VTK rows released: `6/6`.
- Salt2/Salt3/Salt4 each have:
  - `exchange_interface` VTK with `38880` polygons, `38928` points, and
    `0.0623473180949 m2` area.
  - `trusted_wall` VTK with `38880` polygons, `38928` points, and
    `0.063435001093 m2` area.
- VTK cell data include `face_id`, `owner`, `neighbour`, and `area_m2`.
- Counts and areas match the seeded face-list sources.

This releases geometry VTK only. No sampled CFD fields, `Q_wall_W`, sampler
manifest, harvest, same-QOI UQ, fitting, exchange-cell coefficient admission,
or S11/S12/S13/S15/S6 trigger is released.

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_surface_vtk_from_seeded_cv.py`.
- Added `tools/extract/test_s13_upcomer_exchange_surface_vtk_from_seeded_cv.py`.
- Generated six geometry-only VTK files under the task-owned package.
- Generated released surface VTK manifest, validation table, downstream gate,
  guardrails, source manifest, README, and summary.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_surface_vtk_from_seeded_cv.py tools/extract/test_s13_upcomer_exchange_surface_vtk_from_seeded_cv.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_surface_vtk_from_seeded_cv`:
  passed, `5` tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_surface_vtk_from_seeded_cv.py`:
  passed, emitted `validated_surface_vtk_rows=6/6`.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv --strict`:
  passed, `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv`:
  passed.

## Unresolved Blockers

- These VTKs are geometry-only and do not include sampled `U`, `T`, `rho`,
  pressure, or wallHeatFlux fields.
- `Q_wall_W`, sampler/harvest, same-QOI UQ, S11/S12/S15/S6, fitting, and
  exchange-cell coefficient admission remain blocked.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- OpenFOAM solver/postprocessing launched: no.
- Sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, exchange-cell admission, or closure admission
  changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
