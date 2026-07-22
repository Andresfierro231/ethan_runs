---
provenance:
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/RUNNING.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/run_medium_fine_exact_label_sampler.sbatch
tags: [s13, upcomer-exchange, exact-label-sampler, medium-fine, slurm]
related:
  - .agent/journal/2026-07-22/s13-upcomer-exchange-medium-fine-exact-label-sampler.md
  - imports/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler.json
task: TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-EXACT-LABEL-SAMPLER-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer/Scheduler
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-EXACT-LABEL-SAMPLER-2026-07-22

## Objective

Generate exact-label medium/fine rows for the four S13 QOIs using the completed
contract tables. Only after those rows exist should terminal-window
equivalence and mesh/GCI disposition be evaluated.

## Outcome

Complete, fail-closed but useful. Slurm job `3310179` was submitted through
`login3` at approximately `2026-07-22 09:48`, ran on `c318-019`, and completed
successfully at the scheduler level with state `COMPLETED` and exit code `0:0`
at `2026-07-22T10:40:19`.

The scientific sampling result is fail-closed:

- `source_contract_rows=6`
- `source_preflight_ready_rows=6`
- `mesh_geometry_rows=6`
- `terminal_window_reduction_rows=0`
- `exact_label_qoi_rows=0`
- `sampling_error_rows=6`
- `same_label_mesh_gci_ready=false`
- `production_harvest_allowed=false`
- `admission_allowed=false`

The generated geometry contracts are useful downstream: trusted-wall faces,
exchange-interface faces, cap faces, and recirculation-CV cell masks exist for
Salt2/Salt3/Salt4 medium/fine. Exact-label QOI rows do not exist because each
medium/fine reduction failed with missing face area vectors.

Submitted command:

```bash
ssh login3 sbatch /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/run_medium_fine_exact_label_sampler.sbatch
```

Task-owned Slurm wrapper:
`work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/run_medium_fine_exact_label_sampler.sbatch`

Log paths:

- `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/logs/slurm-3310179.out`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/logs/slurm-3310179.err`

## Changes Made

- Verified and used the task-owned reducer
  `tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py`.
- Updated the task-owned tests for the current reducer interface.
- Confirmed the Slurm wrapper runs the reducer with `--execute --job-id`.
- Submitted job `3310179` through the login node after direct `sbatch` reported
  compute-node submission is unavailable.
- Wrote `RUNNING.md` with the monitor and forbidden-action handoff.
- Killed an accidental duplicate local `srun` wrapper in allocation step
  `3307325.2`; it targeted the same package path without the Slurm batch
  provenance and could have overwritten the real batch results. The intended
  batch job `3310179` was not cancelled.
- Inspected completed outputs and closed the row fail-closed rather than
  promoting geometry-only evidence into medium/fine same-label QOI evidence.

## Validation

- `python3.11 -m pytest tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py`:
  passed, `4` tests.
- `sacct -j 3310179 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList`:
  job `3310179` and batch step `COMPLETED` with exit code `0:0`; elapsed
  `00:52:15`; node `c318-019`.
- `ssh c318-019 ps -f -p 410604`: confirmed the batch Python process was
  running with `--execute --job-id 3310179`.
- `python3.11 -m json.tool work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/summary.json`:
  passed.
- `head -20 .../sampling_error_log.csv`: confirmed six fail-closed sampling
  errors, one per Salt2/Salt3/Salt4 medium/fine case, all caused by missing
  face area vectors.
- `head -20 .../mesh_gci_readiness_gate.csv`: confirmed all four QOI labels are
  `blocked_not_executed_or_no_sampled_rows`.

## Unresolved

The immediate unblock is a new repair row for generated face-area-vector
provenance. The sampler currently writes interface/trusted-wall face identities
and area magnitudes, but downstream exact-label reductions require face area
vector components. Do not run mesh/GCI, production harvest, Qwall release, or
admission until exact-label medium/fine rows exist.

## Guardrails

Native solver outputs are read-only. No registry/admission mutation, solver
run, OpenFOAM postProcess mutation, production harvest, source/property or
Qwall admission/release, coefficient admission, final score, S11/S12/S13/S15/S6
trigger, blocker-register change, generated-index refresh, external/Fluid
mutation, or proxy substitution was performed.
