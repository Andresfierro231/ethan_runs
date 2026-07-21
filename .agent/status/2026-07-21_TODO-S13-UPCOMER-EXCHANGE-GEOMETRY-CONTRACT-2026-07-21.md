---
provenance:
  - tools/extract/build_s13_upcomer_exchange_geometry_contract.py
  - tools/extract/test_s13_upcomer_exchange_geometry_contract.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/downstream_surface_vtk_inputs.csv
tags: [upcomer, exchange-cell, geometry-contract, fail-closed, status]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-geometry-contract.md
  - imports/2026-07-21_s13_upcomer_exchange_geometry_contract.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/README.md
task: TODO-S13-UPCOMER-EXCHANGE-GEOMETRY-CONTRACT-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-UPCOMER-EXCHANGE-GEOMETRY-CONTRACT-2026-07-21

## Objective

Define or fail-close the trusted exchange-interface and wall/core
recirculation-band geometry contract needed before surface VTK extraction,
`Q_wall_W`, or exchange-cell harvest.

## Outcome

Complete as fail-closed. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/`.

Key results:

- geometry source ledger rows: `33`;
- released exchange-interface rows: `0`;
- released wall/core rows: `0`;
- released `Q_wall_W` rows: `0`;
- harvest-ready rows: `0`;
- surface VTK extraction allowed: `false`;
- exchange-cell harvest allowed: `false`.

The normal-vector convention is defined for future use only: positive
`mdot_exchange` must point from the recirculation cell toward the main
throughflow once a trusted interface exists. No current source supplies that
interface. Right-leg/upcomer wall patches are identified as plausible support
context, but no approved recirculation cell volume links them to a wall/core
band or area-weighting convention.

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_geometry_contract.py`.
- Added `tools/extract/test_s13_upcomer_exchange_geometry_contract.py`.
- Generated `geometry_source_ledger.csv`,
  `interface_geometry_contract.csv`, `wall_core_band_contract.csv`, and
  `downstream_surface_vtk_inputs.csv`.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile ...`:
  passed.
- `python3.11 -m unittest tools.extract.test_build_upcomer_exchange_cell_vtk_salt3_salt4_matrix tools.extract.test_s13_upcomer_exchange_geometry_contract`:
  passed, `8` tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_geometry_contract.py`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py ...`:
  passed.
- `python3.11 tools/agent/source_property_gate.py ... --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py ...`:
  passed.

## Unresolved Blockers

- `exchange_interface_vtk` remains blocked because audited faceZones are loop
  mass-flow planes or representative proxies, not conservative exchange
  interfaces.
- `wall_vtk` and `Q_wall_W` remain blocked because wall patches are not tied to
  an approved recirculation cell region.
- Exchange-cell harvest for `V_recirc`, `mdot_exchange`, `T_recirc`, pressure
  residual, and energy residual was not run because the required geometry
  lanes are not released.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/surface extraction/sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
