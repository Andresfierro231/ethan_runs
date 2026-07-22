---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_duplicate_job_monitor/summary.json
tags: [status, s13, sampler-monitor, duplicate-job]
related:
  - .agent/journal/2026-07-22/s13-medium-fine-sampler-duplicate-job-monitor.md
  - imports/2026-07-22_s13_medium_fine_sampler_duplicate_job_monitor.json
task: TODO-S13-MEDIUM-FINE-SAMPLER-DUPLICATE-JOB-MONITOR-2026-07-22
date: 2026-07-22
role: Scheduler / cfd-pp / Reviewer / Writer
type: status
status: complete
---
# TODO-S13-MEDIUM-FINE-SAMPLER-DUPLICATE-JOB-MONITOR-2026-07-22

## Objective

Monitor duplicate S13 medium/fine sampler jobs `3310176` and `3310179`, decide
whether cancellation is needed, and adjudicate whether completed outputs are
usable.

## Outcome

Decision:
`duplicate_jobs_completed_no_cancellation_needed_sampler_fail_closed_no_terminal_qoi_rows`.

Both jobs reached `COMPLETED` with exit code `0:0`; no running duplicate
remained to cancel. The sampler output is fail-closed:

- geometry rows: `6`
- terminal window reduction rows: `0`
- exact-label QOI rows: `0`
- sampling error rows: `6`
- usable terminal output: `false`

## Changes Made

- Published monitor package
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_duplicate_job_monitor/`.
- Wrote job-state ledger, output-usable gate, error disposition, duplicate-risk
  decision, repair recommendation, source manifest, README, status, journal, and
  import manifest.
- Updated the S13 sampler board status phrase from running to completed
  fail-closed.

## Validation

- `squeue -j 3310176,3310179` showed no running jobs.
- `sacct -j 3310176,3310179` showed both jobs `COMPLETED` with exit code `0:0`.
- Inspected sampler `summary.json`, `sampling_error_log.csv`, geometry summary,
  and both stdout/stderr logs.

## Unresolved Blockers

The sampler needs a repair row before rerun. Generated exchange-interface rows
lack face area vector components required by `interface_reduction`, causing
every medium/fine case-mesh to fail before terminal QOI sampling.

## Guardrails

No new job was submitted. No job was cancelled because both were already
terminal. No native-output mutation, registry/admission mutation,
solver/postprocessing/sampler/harvest/UQ launch, source/property release, Qwall
release, production harvest, coefficient admission, final score, S11/S12/S13/S15
trigger, or proxy substitution occurred.
