---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/RUNNING.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/submit_stage_a_f6_endpoint_sampler.sbatch
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/stage_a_endpoint_face_matrix.csv
tags: [f6, endpoint-sampler, scheduler-handoff, raw-face]
related:
  - .agent/status/2026-07-21_TODO-F6-STAGE-A-SAMPLER-SUBMIT.md
  - imports/2026-07-21_f6_stage_a_sampler_submit.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/README.md
task: TODO-F6-STAGE-A-SAMPLER-SUBMIT
date: 2026-07-21
role: Scheduler / cfd-pp / Tester / Writer
type: journal
status: complete
---

# F6 Stage A Sampler Submit

## Attempted

I implemented the first executable phase of the F6 raw-face plan. I added
follow-on board rows for submit, monitor, harvest QA, coarse-path repair, and
same-QOI/admission review, then claimed only the submit row.

Before submission I ran syntax checks on the generated sbatch and runner,
checked the queue for duplicate `f6_face_sA` jobs, created the package log
directory, and tried the generated sbatch command.

## Observed

The local shell is on compute node `c318-008`, where `sbatch` is a wrapper
function that only prints that submission must happen from a login node. That
local attempt did not report a job ID and is treated as not submitted.

Submission through `login3.ls6.tacc.utexas.edu` succeeded and returned job
`3308082`. Initial `squeue`/`sacct` evidence showed the job running on
`c318-012`. Early Slurm stderr showed the first case starting:
`sampling salt_2_medium at 518`.

## Inferred

The missing F6 raw sampler evidence is now in the scheduler execution state.
The correct next action is not duplicate submission; it is read-only monitoring
until job `3308082` reaches a terminal state, then a separate harvest/QA row.

## Contradictions Or Caveats

This task submitted work but did not verify the scientific raw outputs. It also
did not run harvest manually. The job script itself is expected to run harvest
at the end, but the scientific QA row must still validate the eight expected VTK
surfaces and the parsed CSV before any F6 or component-K language changes.

## Next Useful Actions

Claim `TODO-F6-STAGE-A-SAMPLER-MONITOR`, watch job `3308082` with `squeue`,
`sacct`, logs, and expected VTK paths, and report terminal state. If successful,
claim `TODO-F6-STAGE-A-HARVEST-QA` to validate raw metrics and labels. If failed,
the harvest row should preserve explicit sample-failure rows rather than
inventing missing pressure or flux data.
