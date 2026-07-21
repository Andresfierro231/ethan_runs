---
provenance:
  - tools/extract/build_upcomer_exchange_surface_source_generation.py
  - tools/extract/test_build_upcomer_exchange_surface_source_generation.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/summary.json
tags: [upcomer, exchange-cell, surface-generation, source-ledger, no-solver, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-surface-source-generation.md
  - imports/2026-07-21_upcomer_exchange_surface_source_generation.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/README.md
task: TODO-UPCOMER-EXCHANGE-SURFACE-SOURCE-GENERATION-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-SURFACE-SOURCE-GENERATION-2026-07-21

## Objective

Advance the next upcomer exchange input lanes after cell-volume readiness:
inspect the same-window surface/source requirements, emit source/sink and
surface contracts, prepare scheduler-safe scripts, and run only if geometry and
source preflight are unambiguous.

## Outcome

Complete as a fail-closed generation package. Published
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/`.

Key results:

- case windows: `3`;
- surface/input contract rows: `15`;
- blocked surface rows: `9`;
- static source/sink ledger rows: `21`;
- per-case static source/sink summaries ready: `3/3`;
- Salt2 static `Q_source=302.7 W`, `Q_sink=136.350739906 W`;
- Salt3 static `Q_source=334.5 W`, `Q_sink=150.769638674 W`;
- Salt4 static `Q_source=374.599999999 W`, `Q_sink=169.226815037 W`;
- scheduler action: `false`;
- OpenFOAM launch: `false`;
- fit/admission/score release: `false`.

The package moves the `source_sink_ledger` lane from undocumented blocker to
explicit static boundary-condition accounting. It does not release energy
residual evaluation because `Q_wall_W`, cell VTK, exchange-interface VTK, and
wall/core VTK are still blocked.

## Changes Made

- Added `tools/extract/build_upcomer_exchange_surface_source_generation.py`.
- Added `tools/extract/test_build_upcomer_exchange_surface_source_generation.py`.
- Generated `surface_extraction_contract.csv`, `source_sink_static_ledger.csv`,
  `source_sink_summary.csv`, `submission_decision.csv`, scripts, guardrails,
  handoff, source manifest, summary, and README under the package.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_upcomer_exchange_surface_source_generation.py tools/extract/test_build_upcomer_exchange_surface_source_generation.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_build_upcomer_exchange_surface_source_generation`:
  passed, `3` tests.
- `python3.11 tools/extract/build_upcomer_exchange_surface_source_generation.py`:
  passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/scripts/run_surface_source_generation.sh`:
  passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/scripts/submit_surface_source_generation.sbatch`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-UPCOMER-EXCHANGE-SURFACE-SOURCE-GENERATION-2026-07-21`:
  passed.

## Unresolved Blockers

- `cell_vtk`: choose whole-mesh cell VTK or approved upcomer cellSet and verify
  `cellId` aligns with the cell-volume CSV.
- `exchange_interface_vtk`: approve conservative main/recirculation interface
  point, normal, area basis, and sign convention.
- `wall_vtk`: approve wall/core surface or band tied to the recirculation cell
  region.
- `Q_wall_W`: requires task-owned wallHeatFlux integration before energy
  residual rows can be computed.
- Diagnostic sampler execution, same-QOI UQ, Phase 4B rescore, Phase 5, and S6
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
