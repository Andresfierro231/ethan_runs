---
provenance:
  - tools/extract/openfoam_cell_volumes.py
  - tools/extract/test_openfoam_cell_volumes.py
  - tools/extract/sample_upcomer_exchange_cell.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser/mesh_volume_parser_readiness.csv
tags: [journal, upcomer, recirculation, exchange-cell, cell-volume, parser]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-CELL-VOLUME-PARSER-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_cell_volume_parser.json
task: TODO-UPCOMER-EXCHANGE-CELL-VOLUME-PARSER-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Cell-Volume Parser

## Attempted

Implemented the missing cell-volume basis for the upcomer exchange-cell sampler.
The approach was a pure Python parser for OpenFOAM ASCII `polyMesh` files plus a
sampler fallback that reads a `cell_id,cellVolume_m3` CSV when the sampled VTK
does not carry `cellVolume`.

## Observed

The Salt2/Salt3/Salt4 source cases all expose `constant/polyMesh` with
`points`, `faces`, `owner`, and `neighbour`. The header note reports
`2268735` points, `2166996` cells, `6598756` faces, and `6403220` internal
faces for each queued production mesh. Those meshes are large enough that full
volume export should be run under scheduler control rather than as a login-node
side effect.

## Inferred

The previous `cellVolume` blocker is now a tooling blocker rather than a method
blocker: the parser and sampler fallback exist and pass synthetic geometry
tests. The next scheduler-authorized row can generate production volume CSVs,
sample real exchange-cell VTK, and assemble rows with `volume_basis` recorded.

## Contradictions Or Caveats

The parser is validated against synthetic cube meshes, including an internal
owner/neighbour face. It has not yet been run over the full production meshes in
this row. That is intentional because the row had no scheduler scope and full
production parsing is multi-million-cell work.

## Next Useful Actions

1. Claim a scheduler-authorized cell-volume export row.
2. Run `openfoam_cell_volumes.py --poly-mesh <case>/constant/polyMesh` for each
   Salt2/Salt3/Salt4 source case on a compute node and write volume CSVs under
   a task-owned package or scratch tree.
3. Update the exchange sampler compute scaffold to pass `--volume-csv` with the
   matching case CSV.
4. Launch real cell/interface/wall VTK extraction only after the volume CSVs
   exist and row-count checks pass.
