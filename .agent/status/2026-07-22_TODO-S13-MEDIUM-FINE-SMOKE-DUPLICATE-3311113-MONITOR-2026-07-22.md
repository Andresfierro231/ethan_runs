---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_smoke_duplicate_3311113_monitor/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_smoke_duplicate_3311113_monitor/scheduler_adjudication.csv
tags: [status, s13, scheduler-monitor, duplicate-smoke]
related:
  - .agent/journal/2026-07-22/s13-medium-fine-smoke-duplicate-3311113-monitor.md
  - imports/2026-07-22_s13_medium_fine_smoke_duplicate_3311113_monitor.json
task: TODO-S13-MEDIUM-FINE-SMOKE-DUPLICATE-3311113-MONITOR-2026-07-22
date: 2026-07-22
role: Scheduler Monitor / cfd-pp / Reviewer / Writer
type: status
status: complete
---
# TODO-S13-MEDIUM-FINE-SMOKE-DUPLICATE-3311113-MONITOR-2026-07-22

## Objective

Adjudicate unexpected duplicate S13 one-case/window smoke job `3311113`
without launching new sampler work or changing scientific admission state.

## Outcome

Complete. Slurm job `3311109` is the canonical smoke result:
`COMPLETED 0:0`, elapsed `00:04:51`, node `c318-018`. It produced four
exact-label QOI rows and zero sampling-error rows.

Duplicate job `3311113` was still running after `3311109` completed, so this
row cancelled only `3311113`. Accounting then reported
`CANCELLED by 890970`, batch exit `0:15`, elapsed `00:02:39`, node `c318-014`.

## Changes Made

- Added
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_smoke_duplicate_3311113_monitor/`.
- Added this status, journal, and import manifest.
- Updated `.agent/BOARD.md` duplicate-monitor row to complete.
- Updated the parent S13 repair row status phrase through its own closeout.

## Validation

- `sacct -j 3311109,3311113 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList -P`
  showed `3311109` complete and `3311113` cancelled.
- `summary.json` and CSV files in the monitor package were parsed.
- `slurm-3311113.err` records cancellation at `2026-07-22T11:51:36`.

## Guardrails

No new scheduler submission, requeue, dependency mutation, native-output
mutation, registry/admission mutation, solver/postprocessing launch, full
medium/fine rerun, production harvest, source/property release, Qwall release,
coefficient admission, final score, S11/S12/S13/S15/S6 trigger, generated-index
refresh, or proxy substitution occurred.
