---
provenance:
  - tools/extract/openfoam_cell_volumes.py
  - tools/extract/test_openfoam_cell_volumes.py
  - tools/extract/sample_upcomer_exchange_cell.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser/README.md
tags: [upcomer, recirculation, exchange-cell, cell-volume, parser, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-cell-volume-parser.md
  - imports/2026-07-21_upcomer_exchange_cell_volume_parser.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/README.md
task: TODO-UPCOMER-EXCHANGE-CELL-VOLUME-PARSER-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-CELL-VOLUME-PARSER-2026-07-21

## Objective

Resolve the blocking `cellVolume` path identified by the upcomer exchange-cell
compute-execution gate. The task was to implement a tested OpenFOAM polyMesh
cell-volume parser, wire the dry exchange-cell sampler to accept a volume CSV
fallback, and publish a no-admission validation package.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser/`.

Key results:

- parser implemented: `tools/extract/openfoam_cell_volumes.py`;
- parser tests: `5`;
- combined parser plus exchange-cell sampler tests: `14`;
- queued production mesh metadata rows: `3`;
- production full-mesh volume export run: `false`;
- scheduler action: `false`;
- fit/admission changed: `false`.

The parser computes cell volumes from ASCII OpenFOAM `constant/polyMesh` files
using oriented owner/neighbour face contributions. The exchange-cell sampler now
uses VTK `cellVolume` when present, or a supplied CSV fallback by `cellId` /
`cellID` / `origCellId` / `cell_id`, with ordered fallback only when the CSV has
one row per VTK cell. Persisted extraction rows now include `volume_basis`.

## Changes Made

- Added `tools/extract/openfoam_cell_volumes.py`.
- Added `tools/extract/test_openfoam_cell_volumes.py`.
- Updated `tools/extract/sample_upcomer_exchange_cell.py` with a volume CSV
  fallback and CLI `--volume-csv`.
- Updated `tools/extract/test_sample_upcomer_exchange_cell.py`.
- Generated the cell-volume parser work product.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/openfoam_cell_volumes.py tools/extract/test_openfoam_cell_volumes.py tools/extract/sample_upcomer_exchange_cell.py tools/extract/test_sample_upcomer_exchange_cell.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_openfoam_cell_volumes`:
  passed, `5` tests.
- `python3.11 -m unittest tools.extract.test_openfoam_cell_volumes tools.extract.test_sample_upcomer_exchange_cell`:
  passed, `14` tests.
- `python3.11 tools/extract/openfoam_cell_volumes.py --package`:
  passed; generated `3` mesh metadata rows and `3` validation rows.
- `python3.11 tools/extract/sample_upcomer_exchange_cell.py --output-dir /tmp/upcomer_exchange_cell_cli_smoke`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser`:
  passed.

## Unresolved Blockers

- Full production cell-volume CSVs for Salt2/Salt3/Salt4 still need to be
  generated on a compute node or in a scheduler-authorized row.
- The exchange-cell sampler still needs real cell/interface/wall VTK extraction
  before `V_recirc`, `mdot_exchange`, `tau_recirc`, pressure residual, or energy
  residual rows can be harvested.
- Same-QOI UQ, Phase 4B rescore, Phase 5, and S6 remain blocked.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/sampler execution launched: no.
- Full production mesh parsing on login node: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
