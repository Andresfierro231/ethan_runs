---
task: TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Scheduler / Implementer / Tester / Writer
type: completed_handoff
status: complete
tags: [upcomer, recirculation, exchange-cell, cell-volume, sbatch]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch/expected_outputs.csv
---
# Running Handoff

## Command

`sbatch work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch/scripts/submit_upcomer_exchange_cell_volume_export.sbatch`

Submitted unchanged via `login3` because direct `sbatch` from the current
compute-node shell reported that submission is unavailable from compute nodes.

- job id: `3308290`
- job name: `upx_vols`
- partition: `NuclearEnergy`
- allocation: `ASC23046`
- terminal state: `COMPLETED`
- exit code: `0:0`
- initial node: `c318-014`
- submitted at: `2026-07-21T14:50:49-05:00`
- completed after: `00:02:32`

## Expected Completion

The job is complete when all three CSVs and JSON summaries under
`cell_volumes/` exist and each CSV has header plus `2166996` data rows.

Completion check passed:

- Salt2 CSV lines including header: `2166997`
- Salt3 CSV lines including header: `2166997`
- Salt4 CSV lines including header: `2166997`
- each JSON summary reports `2166996` cells;
- each JSON summary reports `0` negative-volume cells;
- each JSON summary reports `0` zero-or-negative-volume cells.

## Monitor Instructions

Use `squeue -j <job_id>` while running and `sacct -j <job_id>` after terminal
state. Do not resubmit, cancel, harvest into exchange rows, or launch OpenFOAM
without a new board row.

Key logs:

- `logs/slurm-3308290.err`
- `logs/slurm-3308290.out`
- `logs/salt_2_cell_volume_export.stderr`
- `logs/salt_2_cell_volume_export.stdout`
- `logs/salt_3_cell_volume_export.stderr`
- `logs/salt_3_cell_volume_export.stdout`
- `logs/salt_4_cell_volume_export.stderr`
- `logs/salt_4_cell_volume_export.stdout`
