---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_sampler_monitor/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/slurm-3308082.err
tags: [f6, endpoint-sampler, monitor, raw-face]
related:
  - .agent/status/2026-07-21_TODO-F6-STAGE-A-SAMPLER-MONITOR.md
  - imports/2026-07-21_f6_stage_a_sampler_monitor.json
task: TODO-F6-STAGE-A-SAMPLER-MONITOR
date: 2026-07-21
role: Scheduler Monitor / Writer
type: journal
status: complete
---

# F6 Stage A Sampler Monitor

## Attempted

I performed the narrow monitor closeout for job `3308082`. The monitor checks
were limited to scheduler state, Slurm progress logs, and expected VTK output
paths.

## Observed

`sacct` reports the job and batch step as `COMPLETED` with exit code `0:0`.
The job ran on `c318-012` from `2026-07-21T12:44:35` to
`2026-07-21T12:57:32`. The progress log records sampling `salt_2_medium`,
sampling `salt_2_fine`, and final endpoint raw-face sampling completion.

Eight expected VTK plane files are present under the staged reconstructed
medium/fine trees.

## Inferred

The scheduler execution blocker is closed. The next unresolved question is not
whether the job ran; it is whether the harvested raw rows are scientifically
usable after face, orientation, pressure-basis, and recirculation QA.

## Contradictions Or Caveats

This monitor task did not perform harvest QA. It intentionally does not change
F6, component-K, or pressure-corner admission state.

## Next Useful Actions

Use `TODO-F6-STAGE-A-HARVEST-QA` to classify the eight harvested endpoint faces
and decide whether the raw rows are ordinary candidates, recirculation
diagnostics, orientation failures, or sample failures.
