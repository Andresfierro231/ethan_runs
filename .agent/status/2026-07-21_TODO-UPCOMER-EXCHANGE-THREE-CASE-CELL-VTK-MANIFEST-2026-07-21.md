---
provenance:
  - tools/extract/build_upcomer_exchange_three_case_cell_vtk_manifest.py
  - tools/extract/test_build_upcomer_exchange_three_case_cell_vtk_manifest.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest/three_case_cell_vtk_manifest.csv
tags: [upcomer, exchange-cell, cell-vtk, manifest, sampler-blocked, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-three-case-cell-vtk-manifest.md
  - imports/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix
task: TODO-UPCOMER-EXCHANGE-THREE-CASE-CELL-VTK-MANIFEST-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-THREE-CASE-CELL-VTK-MANIFEST-2026-07-21

## Objective

Publish a three-case cell-lane manifest that joins the validated Salt2,
Salt3, and Salt4 whole-mesh `cell_vtk` paths into the reusable exchange
sampler template while preserving all non-cell heat-loss blockers.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest/`.

Key results:

- Salt2/Salt3/Salt4 cell VTK rows: `3`.
- Cell VTK pass rows: `3/3`.
- Observed cells per case: `2166996`.
- Observed fields per case: `T;U;cellID;rho`.
- Sampler-ready rows: `0`.
- Remaining blocker rows: `12`.

The package updates only a task-owned manifest copy:
`case_vtk_input_manifest.cells_populated.csv`. The reusable scaffold template
was not edited. The populated manifest still contains
`MISSING_EXCHANGE_INTERFACE_VTK`, `MISSING_WALL_VTK`, blank normals, and blank
`cp_J_kg_K`, so it remains invalid for sampler execution by design.

## Changes Made

- Added `tools/extract/build_upcomer_exchange_three_case_cell_vtk_manifest.py`.
- Added `tools/extract/test_build_upcomer_exchange_three_case_cell_vtk_manifest.py`.
- Generated:
  - `three_case_cell_vtk_manifest.csv`
  - `case_vtk_input_manifest.cells_populated.csv`
  - `three_case_cell_vtk_validation_join.csv`
  - `source_sink_wall_loss_readiness.csv`
  - `remaining_sampler_blockers.csv`
  - `summary.json`, `source_manifest.csv`, `no_mutation_guardrails.csv`, and
    `README.md`
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_upcomer_exchange_three_case_cell_vtk_manifest.py tools/extract/test_build_upcomer_exchange_three_case_cell_vtk_manifest.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_build_upcomer_exchange_three_case_cell_vtk_manifest`:
  passed, `4` tests.
- `python3.11 tools/extract/build_upcomer_exchange_three_case_cell_vtk_manifest.py`:
  passed, emitted `cell_vtk_pass_rows=3`, `sampler_ready_rows=0`.
- `python3.11 tools/agent/runtime_input_lint.py ...`:
  passed.
- `python3.11 tools/agent/source_property_gate.py ... --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py ...`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-UPCOMER-EXCHANGE-THREE-CASE-CELL-VTK-MANIFEST-2026-07-21`:
  passed.

## Unresolved Blockers

- `exchange_interface_vtk` remains blocked until a trusted conservative
  main/recirculation interface and normal sign convention are published.
- `wall_vtk` remains blocked until a wall/core surface definition is published.
- `Q_wall_W` remains blocked until task-owned wallHeatFlux integration,
  wall/core band ownership, and heat-flow sign convention are published.
- The parsed static source/sink rows are context only; they do not release the
  full source/sink ledger needed for sampler execution.
- Exchange-cell sampler harvest, scoring, and admission remain blocked.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- OpenFOAM solver/postprocessing launched: no.
- Interface/wall/sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
