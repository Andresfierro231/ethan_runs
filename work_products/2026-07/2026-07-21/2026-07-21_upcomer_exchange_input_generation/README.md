---
task: TODO-UPCOMER-EXCHANGE-INPUT-GENERATION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, input-generation, cell-volume, scheduler]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution
---
# Upcomer Exchange Input Generation

This package bridges the next input-generation state after the cell-volume
parser and export sbatch. It records the completed Salt2 `7915`, Salt3 `7618`,
and Salt4 `10000` cell-volume CSVs from the dedicated export package, prepares
task-owned export scripts, records the completed task-owned validation export,
and records why the other production sampler inputs remain blocked.

## Decision

- case windows: `3`
- input ledger rows: `18`
- task-owned cell-volume CSVs ready: `3/3`
- external corroborating cell-volume CSVs ready: `3/3`
- cell-volume export submitted by this row: `true`
- scheduler action: `true`
- OpenFOAM surface/postprocessing launch: `false`
- fit/admission/score allowed now: `false`

Cell-volume export was completed under this row and matches the earlier
`TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21` outputs. The
task-owned CSVs are the primary ready inputs for the next row. Cell/interface/
wall VTK generation and source/sink ledger extraction remain explicit blockers
for a later row.

## Outputs

- `input_generation_ledger.csv`: per-case input status.
- `cell_volume_export_validation.csv`: external volume output readiness.
- `cell_volume_export_commands.csv`: exact parser commands and output paths.
- `surface_and_ledger_blockers.csv`: blockers for VTK and source/sink inputs.
- `submission_record.csv`: scheduler submission state.
- `scripts/`: runner and sbatch wrapper for cell-volume export.
- `RUNNING.md`: written when a scheduler job id is recorded.
- `source_manifest.csv`: provenance and mutation flags.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, Fluid source, external
repository, blocker register, generated docs index, fit, model selection,
exchange-cell admission, Phase 4B rescore, Phase 5/S6 trigger, or internal-Nu
residual absorption is changed by this package.
