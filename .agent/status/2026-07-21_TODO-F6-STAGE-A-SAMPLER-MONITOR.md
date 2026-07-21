---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_sampler_monitor/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_sampler_monitor/expected_surface_inventory.csv
tags: [f6, endpoint-sampler, monitor, raw-face]
related:
  - .agent/journal/2026-07-21/f6-stage-a-sampler-monitor.md
  - imports/2026-07-21_f6_stage_a_sampler_monitor.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/RUNNING.md
task: TODO-F6-STAGE-A-SAMPLER-MONITOR
date: 2026-07-21
role: Scheduler Monitor / Writer
type: status
status: complete
---
# TODO-F6-STAGE-A-SAMPLER-MONITOR Status

## Objective

Monitor Stage A F6 sampler job `3308082`, report terminal state, and hand off
to harvest QA without submitting, cancelling, requeueing, harvesting, or
admitting coefficients.

## Outcome

Complete. `sacct` reports job `3308082` and its batch step `COMPLETED` with
exit code `0:0`, elapsed `00:12:57`, on `c318-012`. The Slurm progress log ends
with `F6 Stage A endpoint raw-face sampling complete`. All eight expected VTK
surfaces are present.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-STAGE-A-SAMPLER-MONITOR.md`
- `.agent/journal/2026-07-21/f6-stage-a-sampler-monitor.md`
- `imports/2026-07-21_f6_stage_a_sampler_monitor.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_sampler_monitor/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_sampler_monitor/summary.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_sampler_monitor/expected_surface_inventory.csv`

## Validation

- `sacct -j 3308082 --format=JobID,JobName%24,State,ExitCode,Elapsed,NodeList%20,Start,End` showed `COMPLETED 0:0`.
- `tail -80 work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/slurm-3308082.err` showed both case sampling lines and final completion.
- `find tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed -name 'plane_*.vtk'` found eight VTK files.

## Guardrails

No scheduler submit/cancel/requeue/dependency mutation was performed by this
monitor task. No harvest, parser edit, native-output mutation, registry/admission
mutation, solver/postprocessing launch, Fluid/external edit, fitting/tuning/model
selection, F6 fit, component-K admission, clipped K, hidden global multiplier,
blocker-register change, or generated-index refresh was performed.
