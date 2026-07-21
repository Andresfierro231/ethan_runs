---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/case_log_disposition.csv
tags: [pressure, f6, cand001, timeout, scheduler-readiness]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-F6-CAND001-TIMEOUT-DISPOSITION-2026-07-21.md
  - imports/2026-07-21_pressure_f6_cand001_timeout_disposition.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/README.md
task: TODO-PRESSURE-F6-CAND001-TIMEOUT-DISPOSITION-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Scheduler / Tester / Writer
type: journal
status: complete
---
# Pressure/F6 CAND-001 Timeout Disposition

## Attempted

I converted the prior "monitor `3299620` and review `3299610` timeout" handoff
into a disposition package. The task was intentionally read-only: refresh
scheduler/accounting state, inspect cited logs and file availability, and make
a go/no-go decision for F6 readiness.

## Observed

Both CAND-001 scheduler jobs timed out. `3299610` ended as `TIMEOUT` for
`salt4_q3x_probe`; `3299620` ended as `TIMEOUT` for the three-case
`salt4_heat_pack`. The log tails show Slurm time-limit cancellation for each
`foamRun` step.

The staged case roots have only root `0` plus processor-local time directories.
Processor-local latest times are about `11658`, `11031`, `11395`, and `10795`
seconds for the four source cases. These are not reconstructed terminal fields,
and no endpoint harvest exists.

## Inferred

The current CAND-001 attempts must fail closed as F6 evidence. Partial
processor-local writes can document runtime progress and timeout behavior, but
they cannot be used as endpoint pressure/velocity evidence, ordinary-flow
evidence, same-QOI UQ, F3 comparison, or coefficient support.

The candidate source family is not scientifically disproven, because the
failure mode observed here is scheduler walltime timeout, not a documented
reverse-flow gate failure or bad pressure-basis result. The right disposition
is therefore `retry_needed_with_scheduler_plan`, not sampler release.

## What Worked

The timeout disposition narrowed the blocker. We no longer have a live/unknown
high-heat source state for CAND-001: both cited jobs are terminal timeouts, and
the current attempts are closed as evidence.

## What Did Not Work

No terminal-successful source case was found. No endpoint fields became ready,
and no RAF/RMF/SVF rows can be computed under this task's guardrails.

## Caveats

This package did not launch, reconstruct, sample, or harvest anything. It did
not inspect full native field values or infer convergence from processor-local
partial data. Any retry must be planned in a separate scheduler row with exact
cases, continuation safety, walltime/resource estimate, and duplicate-job guard.

## Next Useful Actions

Choose between a CAND-001 retry scheduler plan and a CAND-002 fallback
terminal-readiness audit. If a future retry lands terminal-successfully, then a
separate staged-copy endpoint sampler can be claimed; only after finite endpoint
fields, ordinary RAF/RMF pass, same-QOI UQ, and F3 comparison should F6 or
component-K review reopen.
