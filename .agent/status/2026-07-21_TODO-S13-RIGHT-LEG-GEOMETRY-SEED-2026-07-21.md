---
provenance:
  - tools/extract/build_s13_right_leg_geometry_seed.py
  - tools/extract/test_s13_right_leg_geometry_seed.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed/geometry_seed_case_summary.csv
tags: [s13, upcomer, right-leg, geometry-seed, s12, status]
related:
  - .agent/journal/2026-07-21/s13-right-leg-geometry-seed.md
  - imports/2026-07-21_s13_right_leg_geometry_seed.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition
task: TODO-S13-RIGHT-LEG-GEOMETRY-SEED-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-RIGHT-LEG-GEOMETRY-SEED-2026-07-21

## Objective

Build a predeclared geometry-backed right-leg/upcomer seed from trusted wall
patches `pipeleg_right_01_lower`, `pipeleg_right_02_middle`, and
`pipeleg_right_03_upper`, then decide whether the seed is ready for a later
source-bounded CV rerun.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed/`.

Key results:

- Decision: `released_geometry_seed_ready_for_source_bounded_rerun`.
- Geometry seed ready cases: `3/3`.
- Salt2/Salt3/Salt4 seed cells: `38880/38880/38880`.
- Seed volume: `1.19084663056e-05 m3` for each case.
- Trusted wall faces: `38880` per case; trusted wall area:
  `0.063435001093 m2` per case.
- Internal interface faces: `38880` per case; internal interface area:
  `0.0623473180949 m2` per case.
- Classified cap faces: `96` per case; escape faces: `0`.
- Reverse-flow occupancy is diagnostic only:
  Salt2 `0`, Salt3 `6`, Salt4 `15` seed cells.

This unlocks only a new source-bounded CV rerun row. Surface extraction,
sampler refresh, harvest, same-QOI UQ, S12-HIAX1 implementation, S11/S15/S6,
and any admission remain blocked.

## Changes Made

- Added `tools/extract/build_s13_right_leg_geometry_seed.py`.
- Added `tools/extract/test_s13_right_leg_geometry_seed.py`.
- Generated:
  - `geometry_seed_case_summary.csv`
  - `geometry_seed_cells.csv`
  - `geometry_seed_face_lanes.csv`
  - `geometry_seed_patch_classification.csv`
  - `geometry_seed_surface_contract.csv`
  - `downstream_release_gate.csv`
  - `reverse_flow_occupancy_diagnostics.csv`
  - `reverse_occupancy_diagnostics.csv`
  - `source_bounded_rerun_readiness.csv`
  - `s12_unlock_impact.csv`
  - `masks/*_right_leg_geometry_seed_cells.csv`
  - `summary.json`, `source_manifest.csv`, `no_mutation_guardrails.csv`, and
    `README.md`
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_right_leg_geometry_seed.py tools/extract/test_s13_right_leg_geometry_seed.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_right_leg_geometry_seed`:
  passed, `5` tests.
- `python3.11 tools/extract/build_s13_right_leg_geometry_seed.py`:
  passed, emitted `geometry_seed_ready_case_count=3` and
  `geometry_seed_ready_for_source_bounded_rerun=true`.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed --strict`:
  passed, `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed`:
  passed.

## Unresolved Blockers

- Source-bounded CV release must be rerun in a new row using this seed.
- Surface VTK extraction, sampler refresh, wall/source `Q_wall_W`, harvest,
  same-QOI UQ, S12-HIAX1 implementation, S11/S15/S6, and candidate admission
  remain blocked until the source-bounded rerun releases the needed lanes.
- Reverse-flow occupancy remains diagnostic-only and has no selection authority.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- OpenFOAM solver/postprocessing launched: no.
- Surface VTK extraction launched: no.
- Sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, threshold relaxation, exchange-cell
  coefficient admission, S11/S12/S13/S15/S6 trigger, or closure admission
  changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
