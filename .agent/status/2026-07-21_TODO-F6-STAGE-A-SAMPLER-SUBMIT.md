---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/RUNNING.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/slurm-3308082.err
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/slurm-3308082.out
tags: [f6, endpoint-sampler, scheduler-handoff, raw-face]
related:
  - .agent/journal/2026-07-21/f6-stage-a-sampler-submit.md
  - imports/2026-07-21_f6_stage_a_sampler_submit.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/README.md
task: TODO-F6-STAGE-A-SAMPLER-SUBMIT
date: 2026-07-21
role: Scheduler / cfd-pp / Tester / Writer
type: status
status: complete
---
# TODO-F6-STAGE-A-SAMPLER-SUBMIT Status

## Objective

Submit the existing Stage A F6 endpoint raw-face sampler sbatch and leave a
durable handoff for monitor and harvest work.

## Outcome

Complete. The direct local `sbatch` attempt from compute node `c318-008` did not
submit a job because `sbatch` is unavailable on compute nodes. The job was then
submitted through `login3.ls6.tacc.utexas.edu` with the same absolute sbatch
script.

Submitted job: `3308082` (`f6_face_sA`). Initial scheduler state was `RUNNING`
on `c318-012` at `2026-07-21T12:44:35-05:00`.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-STAGE-A-SAMPLER-SUBMIT.md`
- `.agent/journal/2026-07-21/f6-stage-a-sampler-submit.md`
- `imports/2026-07-21_f6_stage_a_sampler_submit.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/RUNNING.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/slurm-3308082.err`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/slurm-3308082.out`

## Validation

- `bash -n work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/submit_stage_a_f6_endpoint_sampler.sbatch` passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/run_stage_a_f6_endpoint_sampler.sh` passed.
- `squeue -u andresfierro231` showed no existing `f6_face_sA` job before submission.
- Local `sbatch ...submit_stage_a_f6_endpoint_sampler.sbatch` printed compute-node refusal and did not report a job ID.
- `ssh login3.ls6.tacc.utexas.edu sbatch /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/submit_stage_a_f6_endpoint_sampler.sbatch` submitted batch job `3308082`.
- `squeue -j 3308082` showed `RUNNING` on `c318-012`.
- `sacct -j 3308082 --format=JobID,JobName%24,State,ExitCode,Elapsed,NodeList%20,Start,End` showed job and batch step `RUNNING`.

## Guardrails

Native CFD/OpenFOAM source outputs were not mutated by this submit task. The
job operates through staged copies under the repo `tmp/` tree. Registry/admission
state was not mutated. No cancel/requeue/dependency mutation, harvest QA, parser
edit, Fluid edit, external edit, fitting/tuning/model selection, F6 fit,
component-K admission, clipped K, hidden global multiplier, blocker-register
change, or generated-index refresh was performed.

Continuing monitoring belongs to `TODO-F6-STAGE-A-SAMPLER-MONITOR`. Harvest and
scientific QA belong to `TODO-F6-STAGE-A-HARVEST-QA` after successful terminal
completion.
