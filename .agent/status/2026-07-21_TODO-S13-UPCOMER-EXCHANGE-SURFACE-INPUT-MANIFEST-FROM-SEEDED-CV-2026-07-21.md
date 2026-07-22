---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/case_preflight_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/seeded_surface_input_inventory.csv
tags: [s13, upcomer-exchange, seeded-cv, surface-input-manifest, preflight]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-surface-input-manifest-from-seeded-cv.md
  - imports/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed/summary.json
task: TODO-S13-UPCOMER-EXCHANGE-SURFACE-INPUT-MANIFEST-FROM-SEEDED-CV-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-SURFACE-INPUT-MANIFEST-FROM-SEEDED-CV-2026-07-21

## Objective

Build a read-only seeded-CV surface/input manifest from the released S13 seeded
mask/interface/wall CSVs, existing cell VTKs, volume CSVs, source/sink summary,
and normal convention.

## Outcome

Complete. The package at
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/`
contains:

- `seeded_surface_input_inventory.csv`
- `seeded_surface_input_manifest.csv`
- `input_file_existence_checks.csv`
- `downstream_gate.csv`
- `case_preflight_matrix.csv`
- `surface_input_decision.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`
- `README.md`
- per-case split inputs under `masks/`, `faces/`, and `bands/`

Key result: Salt2/Salt3/Salt4 are `3/3` ready for a later
scheduler-authorized seeded surface-extraction task. Each case has `38880`
seeded CV cells, `38880` seeded internal interface faces, `38880` trusted wall
faces, released seeded wall/core band, released normal convention, existing cell
VTK, existing cell-volume CSV, and static source/sink summary context.

The result is not sampler or admission readiness. Sampler-manifest-ready rows
remain `0/3` because raw sampled interface/wall VTK outputs, `Q_wall_W`, and
same-window sampler outputs are still absent.

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv.py`.
- Added `tools/extract/test_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv.py`.
- Generated the task-owned work-product package with inventory, case matrix,
  decision table, guardrails, manifest, summary, and README.
- Added this status file, the matching journal entry, and the import manifest.
- Updated only the task-owned board row to report completion.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv.py tools/extract/test_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv.py`
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv`
  passed: 6 tests.

## Unresolved Blockers

- Raw same-window interface and wall sampled VTK/face-field outputs have not
  been generated from the seeded face lists.
- `Q_wall_W` remains unreleased for the seeded wall/core band.
- Same-window sampler outputs and same-QOI UQ are not present.
- S13 production harvest, coefficient review, S11/S12/S13/S15/S6 triggers, and
  exchange-cell admission remain blocked.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
sampler/harvest state, Fluid source tree, external repository, blocker register,
or generated documentation index was changed. No OpenFOAM solver/postprocessing,
surface extraction, sampler, harvest, UQ execution, fitting, model selection,
coefficient admission, S11/S12/S13/S15/S6 trigger, or residual absorption into
internal `Nu` was performed.
