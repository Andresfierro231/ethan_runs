---
provenance:
  - tools/extract/build_upcomer_exchange_geometry_release.py
  - tools/extract/test_build_upcomer_exchange_geometry_release.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/summary.json
tags: [upcomer, exchange-cell, geometry-release, cell-vtk, no-solver, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-geometry-release.md
  - imports/2026-07-21_upcomer_exchange_geometry_release.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/README.md
task: TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21

## Objective

Implement the geometry-release phase for upcomer exchange blockers: release the
whole-mesh cell VTK policy if defensible, audit existing exchange-interface and
wall/core candidates from trusted mesh/topology context, reject proxy planes,
and publish exact release conditions for the next scheduler extraction row.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/`.

Key results:

- case rows: `3`;
- whole-mesh cell VTK releases: `3/3`;
- VTK cell-count target per case: `2166996`;
- faceZone/proxy candidates audited: `15`;
- released exchange-interface rows: `0`;
- wall/core candidates audited: `18`;
- released wall/core rows: `0`;
- planned next extraction command rows: `3`;
- scheduler action: `false`;
- OpenFOAM launch: `false`;
- fit/admission/score release: `false`.

The cell VTK blocker is now sufficiently unlocked for a separate scheduler row:
the next row may stage the Salt2/Salt3/Salt4 continuation cases and extract
whole-mesh `U`, `T`, and `rho` cell VTKs, provided it verifies VTK cell count
and ordering against the existing volume CSVs.

The exchange-interface and wall/core lanes remain blocked. Existing
`mdot_pipeleg_*` faceZones are loop mass-flow planes, and the prior
`upcomer_outlet_proxy` is explicitly rejected as a substitute for a conservative
main/recirculation exchange interface. Wall patches are known, but no approved
recirculation cell region or wall/core band exists yet. No heat residual was
absorbed into internal `Nu`.

## Changes Made

- Added `tools/extract/build_upcomer_exchange_geometry_release.py`.
- Added `tools/extract/test_build_upcomer_exchange_geometry_release.py`.
- Generated `geometry_release_decision.csv`, `cell_vtk_contract.csv`,
  `facezone_candidate_audit.csv`, `wall_core_candidate_audit.csv`,
  `planned_extraction_commands.csv`, `no_mutation_guardrails.csv`,
  `next_agent_handoff.csv`, `source_manifest.csv`, `summary.json`, and
  `README.md` under the package.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_upcomer_exchange_geometry_release.py tools/extract/test_build_upcomer_exchange_geometry_release.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_build_upcomer_exchange_geometry_release`:
  passed, `3` tests.
- `python3.11 tools/extract/build_upcomer_exchange_geometry_release.py`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21.md .agent/journal/2026-07-21/upcomer-exchange-geometry-release.md imports/2026-07-21_upcomer_exchange_geometry_release.json`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21.md .agent/journal/2026-07-21/upcomer-exchange-geometry-release.md imports/2026-07-21_upcomer_exchange_geometry_release.json`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21`:
  passed.

## Unresolved Blockers

- `exchange_interface_vtk`: requires a trusted conservative
  main/recirculation interface with point, normal, area/sign convention, and
  source path.
- `wall_vtk` and `Q_wall_W`: require a recirculation cell region and wall/core
  band before wallHeatFlux integration can be owned.
- Sampler execution remains blocked until cell VTK, exchange-interface VTK,
  wall/core VTK, and wall heat terms exist.
- Same-QOI UQ, Phase 4B rescore, Phase 5, S6, fitting, scoring, and admission
  remain blocked.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- OpenFOAM solver/surface/postprocessing launch: no.
- Sampler/harvest execution launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
