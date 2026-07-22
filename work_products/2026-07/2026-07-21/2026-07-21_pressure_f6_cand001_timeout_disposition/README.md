---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness/source_case_readiness_refresh.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/anchor_decision.csv
tags: [pressure, f6, cand001, timeout-disposition, no-admission]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-F6-CAND001-TIMEOUT-DISPOSITION-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness/README.md
task: TODO-PRESSURE-F6-CAND001-TIMEOUT-DISPOSITION-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Scheduler / Tester / Writer
type: work_product
status: complete
---
# Pressure/F6 CAND-001 Timeout Disposition

## Decision

`CAND-001` current attempts are fail-closed as F6 evidence. The candidate itself
is classified `retry_needed_with_scheduler_plan`, because the observed failure
mode is Slurm walltime timeout rather than a clean terminal source failure or an
ordinary-flow physics rejection.

No F6 sampler, F6 coefficient review, component `K`, cluster `K`, clipped `K`,
or hidden multiplier is released.

## Evidence

Both high-heat scheduler jobs timed out:

- `3299610` / `salt4_q3x_probe`: `TIMEOUT`, elapsed `5-00:00:25`.
- `3299620` / `salt4_heat_pack`: `TIMEOUT`, elapsed `5-00:00:08`.

The logs end with time-limit cancellation messages. Processor-local time
directories exist, but the root cases do not contain reconstructed terminal
fields beyond `0`, and no endpoint harvest exists. These partial outputs are
therefore scheduler/runtime diagnostics only.

## Open First

1. `summary.json`
2. `candidate_disposition.csv`
3. `scheduler_disposition.csv`
4. `partial_output_inventory.csv`
5. `endpoint_gate_after_timeout.csv`
6. `next_task_queue.csv`
