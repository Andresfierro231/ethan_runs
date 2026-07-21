---
provenance:
  - tools/extract/build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py
  - tools/extract/test_build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/validation_report.csv
tags: [upcomer, exchange-cell, cell-vtk, salt3, salt4, scheduler, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-cell-vtk-salt3-salt4-matrix.md
  - imports/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/README.md
task: TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21

## Objective

Replicate the repaired Salt2 whole-mesh `cell_vtk` extraction path for Salt3
and Salt4, validate `U`, `T`, and `rho` against the existing cell-volume
contracts, and keep interface/wall/`Q_wall_W`/harvest/admission lanes blocked.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/`.

Key results:

- Salt3 target time: `7618`; VTK validation `pass`; observed cells `2166996`;
  fields `T;U;cellID;rho`.
- Salt4 target time: `10000`; VTK validation `pass`; observed cells
  `2166996`; fields `T;U;cellID;rho`.
- Outputs:
  `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/vtk/salt_3_cell_fields.vtk`
  and
  `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/vtk/salt_4_cell_fields.vtk`.
- Scheduler job `3308527` completed on `c318-016` with exit code `0:0` and
  elapsed time `00:01:05`.
- Native output mutation: `false`.

Important implementation note: Salt3 had four non-finite tokens in the
task-local reconstructed `T` boundaryField. The runner verifies there are no
non-finite internal-cell `T` tokens, replaces only task-local boundary
non-finite tokens so OpenFOAM can read the field, and exports the whole-mesh
internal VTK. This does not alter native case data and does not release wall or
boundary thermal evidence.

## Changes Made

- Updated `tools/extract/build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py`
  to use task-local boundary-field sanitization and patch-excluded internal VTK
  export.
- Updated `tools/extract/test_build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py`
  with regression checks for sanitizer and `foamToVTK` flags.
- Generated Salt3/Salt4 package ledgers, scripts, logs, scheduler handoff, and
  validated cell VTKs under the work-product package.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py tools/extract/test_build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py tools/extract/build_s13_upcomer_exchange_geometry_contract.py tools/extract/test_s13_upcomer_exchange_geometry_contract.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_build_upcomer_exchange_cell_vtk_salt3_salt4_matrix tools.extract.test_s13_upcomer_exchange_geometry_contract`:
  passed, `8` tests.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/scripts/run_salt3_salt4_cell_vtk_matrix.sh`:
  passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/scripts/submit_salt3_salt4_cell_vtk_matrix.sbatch`:
  passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/scripts/validate_salt3_salt4_cell_vtk.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py ...`:
  passed.
- `python3.11 tools/agent/source_property_gate.py ... --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py ...`:
  passed.

## Unresolved Blockers

- Cell VTKs are now complete for Salt2/Salt3/Salt4.
- `exchange_interface_vtk` remains blocked until a trusted conservative
  main/recirculation interface is defined.
- `wall_vtk` and `Q_wall_W` remain blocked until an approved recirculation
  volume is linked to a wall/core band and heat-flow convention.
- The exchange-cell harvest remains blocked by geometry, not by missing
  whole-mesh cell VTK.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: yes, task-owned Salt3/Salt4 cell-VTK extraction only.
- OpenFOAM postprocessing launched: yes, task-owned staged cases only.
- Interface/wall/sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
