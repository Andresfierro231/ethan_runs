---
provenance:
  - tools/extract/openfoam_cell_volumes.py
  - tools/extract/test_openfoam_cell_volumes.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch/RUNNING.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch/sbatch_submission_status.csv
tags: [upcomer, recirculation, exchange-cell, cell-volume, sbatch, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-cell-volume-export-sbatch.md
  - imports/2026-07-21_upcomer_exchange_cell_volume_export_sbatch.json
task: TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Scheduler/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21

## Objective

Make the cell-volume parser production-safe and submit a compute-node job to
export Salt2/Salt3/Salt4 cell-volume CSVs into a task-owned package.

## Outcome

Complete. The production export job completed under Slurm:

- job id: `3308290`;
- job name: `upx_vols`;
- partition/account: `NuclearEnergy` / `ASC23046`;
- terminal state/exit: `COMPLETED` / `0:0`;
- elapsed/node: `00:02:32` on `c318-014`;
- package: `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch/`.

Direct `sbatch` from this shell reported that submission is unavailable from
compute nodes, so the same sbatch script was submitted unchanged through
`ssh login3`. The output checks passed: all three CSVs have `2166997` lines
including the header, and all three summaries report `2166996` cells with `0`
negative and `0` zero-or-negative volume cells.

## Changes Made

- Updated `tools/extract/openfoam_cell_volumes.py` so the production CLI uses
  streaming face/owner/neighbour parsing and row-by-row CSV writing.
- Updated `tools/extract/test_openfoam_cell_volumes.py` with a streaming
  equivalence test.
- Created run and sbatch scripts, expected-output ledger, source manifest,
  summary, README, and RUNNING handoff.
- Submitted Slurm job `3308290`.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/openfoam_cell_volumes.py tools/extract/test_openfoam_cell_volumes.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_openfoam_cell_volumes`:
  passed, `6` tests.
- `python3.11 -m unittest tools.extract.test_openfoam_cell_volumes tools.extract.test_sample_upcomer_exchange_cell`:
  passed, `15` tests.
- `bash -n` on run script and sbatch script: passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch`:
  passed.
- `squeue -j 3308290`: observed `R`, then `CG`, on `c318-014`.
- `sacct -j 3308290 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList`:
  `COMPLETED`, `0:0`, `00:02:32`, `c318-014`.
- `wc -l` for Salt2/Salt3/Salt4 CSVs: `2166997` each.
- JSON summary checks: `2166996` cells, `0` negative-volume cells, and `0`
  zero-or-negative-volume cells for all three cases.

## Unresolved Blockers

- Exchange-cell VTK extraction, exchange-row harvest, same-QOI UQ, Phase 4B
  rescore, Phase 5, and S6 remain separate rows.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: yes, submitted only job `3308290`.
- Solver/OpenFOAM/postprocessing/sampler launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
