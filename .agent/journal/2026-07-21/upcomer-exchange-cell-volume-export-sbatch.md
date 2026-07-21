---
provenance:
  - tools/extract/openfoam_cell_volumes.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch/RUNNING.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch/expected_outputs.csv
tags: [journal, upcomer, recirculation, exchange-cell, cell-volume, sbatch]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_cell_volume_export_sbatch.json
task: TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Scheduler/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Cell-Volume Export Sbatch

## Attempted

Advanced from tested parser to production export. Before submission, changed
the parser production path to stream faces, owner, and neighbour entries instead
of materializing the full face list, and changed CSV writing to emit rows
incrementally.

## Observed

The focused parser tests pass, including a synthetic two-cell owner/neighbour
mesh that verifies streaming and in-memory results match. The first direct
`sbatch` attempt from host `c318-008.ls6.tacc.utexas.edu` reported that `sbatch`
is unavailable on compute nodes. The unchanged sbatch file was then submitted
through `ssh login3`, yielding job `3308290`. `squeue -j 3308290` showed state
`R` and then `CG` on `c318-014`; `sacct` then reported `COMPLETED`, exit
`0:0`, elapsed `00:02:32`.

The output checks passed. Each Salt CSV has `2166997` lines including the
header. Each summary JSON reports `2166996` cells, `0` negative-volume cells,
and `0` zero-or-negative-volume cells.

## Inferred

The cell-volume evidence path is now complete enough for the next exchange-cell
sampler row to consume these package-local CSVs through `--volume-csv`. The next
action is exchange-cell VTK extraction and row assembly, not duplicate
cell-volume submission.

## Contradictions Or Caveats

The volume CSVs are production support diagnostics, not model coefficients. No
exchange-cell row, coefficient, pressure residual claim, energy residual claim,
or scorecard admission is made by this export.

## Next Useful Actions

1. Claim the exchange-cell sampler launch/harvest row and pass
   the matching `--volume-csv` paths to `sample_upcomer_exchange_cell.py`.
2. Generate/supply the real cell/interface/wall VTK inputs for Salt2/Salt3/Salt4.
3. Assemble diagnostic exchange rows and then run same-QOI UQ before any Phase
   4B/5/S6 claim.
