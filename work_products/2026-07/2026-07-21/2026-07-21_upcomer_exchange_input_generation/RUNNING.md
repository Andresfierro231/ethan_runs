---
task: TODO-UPCOMER-EXCHANGE-INPUT-GENERATION-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Writer
type: operational_note
status: active
tags: [upcomer, exchange-cell, cell-volume, scheduler]
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/submission_record.csv
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/README.md
---
# Running Cell-Volume Export

- task ID: `TODO-UPCOMER-EXCHANGE-INPUT-GENERATION-2026-07-21`
- job ID: `3308363`
- submitted from node: unknown from package; check `squeue -j 3308363` while queued/running
- exact submit command: `ssh login3 cd-and-sbatch submit_cell_volume_exports.sbatch`
- runner: `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/scripts/run_cell_volume_exports.sh`
- sbatch script: `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/scripts/submit_cell_volume_exports.sbatch`
- stdout log pattern: `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/logs/slurm-%j.out`
- stderr log pattern: `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/logs/slurm-%j.err`

Expected outputs:

- `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/cell_volumes/salt_2_cell_volumes.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/cell_volumes/salt_3_cell_volumes.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/cell_volumes/salt_4_cell_volumes.csv`

Terminal condition: all expected CSV and summary JSON files exist, or Slurm
reports a terminal failure. Killing/cancelling the job is safe for native CFD
outputs because it writes only under this work-product package, but do not
resubmit without a new board row or explicit operator decision.
