---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch/RUNNING.md
tags: [upcomer, exchange-cell, input-generation, cell-volume]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-INPUT-GENERATION-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_input_generation.json
task: TODO-UPCOMER-EXCHANGE-INPUT-GENERATION-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Input Generation

## Attempted

Built the first input-generation package for upcomer exchange sampling after
the cell-volume parser. The package records per-case input readiness, validates
cell-volume exports, emits scheduler-safe fallback commands, and lists blockers
for cell/interface/wall VTK plus source/sink ledgers.

## Observed

The dedicated cell-volume export package completed as Slurm job `3308290` with
`COMPLETED 0:0`. During this row, the task-owned validation export job `3308363`
also completed with `COMPLETED 0:0` in `00:02:35`. Salt2, Salt3, and Salt4 each
have `2166997` CSV lines including header in both output locations. Summary
JSON files report `2166996` cells and `0` negative or zero-volume cells.

## Inferred

Cell-volume input is no longer the blocker for the exchange-cell sampler. The
remaining blockers are the physical field/source inputs: cell VTK, exchange
interface VTK, wall/core VTK, and source/sink ledger. The ready cell-volume
rows are diagnostic support only and do not justify exchange-cell admission,
fit, score, Phase 4B rescore, Phase 5, or S6 trigger.

## Caveats

The package has two valid cell-volume copies because the export package
completed first and this row also completed a task-owned validation export. The
input-generation ledger treats the dedicated export package as corroborating
evidence and the task-owned copy as ready for the next task; neither copy is a
native solver-output mutation.

## Next Useful Actions

Create a separate scheduler-authorized row for same-window cell/interface/wall
field generation and source/sink ledger extraction. Only after those inputs are
present should a sampler execution row run `sample_upcomer_exchange_cell.py`;
that row must remain diagnostic unless later UQ/source gates pass.
