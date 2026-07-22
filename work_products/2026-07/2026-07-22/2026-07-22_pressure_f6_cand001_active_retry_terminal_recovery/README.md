---
provenance:
  generated_by: tools/analyze/build_pressure_f6_cand001_active_retry_terminal_recovery.py
  task_id: TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22
  generated_at_utc: 2026-07-22T13:07:54.140688+00:00
task: TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22
tags:
  - pressure
  - F6
  - CAND001
  - scheduler
  - terminal-source-recovery
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_steady_relaunch_manifest.csv
---

# CAND001 active retry terminal recovery

## Decision

CAND001 remains scientifically worth monitoring as terminal-source recovery, but
only through the already-running Salt4 high-heat relaunch job `3308712`.
This task did not submit, cancel, requeue, sample, harvest, or score anything.

The reason to continue is narrow: previous CAND001 evidence failed by scheduler
timeout, not by a physics contradiction, and the active relaunch has four source
cases with explicit restart times and a common target end time. If those cases
finish, they may provide the first terminal source evidence needed before an
endpoint-field readiness row.

## Why this is not F6 evidence

The current state is still missing terminal success, endpoint fields, ordinary
flow evidence, and same-QOI mesh/time UQ. Therefore this package explicitly
keeps `F6_scoring_now=false`, `component_K=false`, `cluster_K=false`, and
`S11/S15/S6 trigger=false`.

## What worked

- The S10/S14 gate produced a scheduler-safe runbook that separated terminal
  source recovery from F6 scoring.
- The high-heat relaunch package already created the appropriate scheduler
  attempt for CAND001, so the pressure path can avoid a duplicate submission.

## What did not work

- Prior jobs `3299610` and `3299620` timed out before terminal success.
- No endpoint pressure/F6 field package exists yet.
- No ordinary-flow or same-QOI UQ gate has passed.

## Next post-terminal action

After `3308712` reaches a terminal scheduler state, claim a separate
terminal-disposition/readiness row. That row may read logs and terminal fields,
but it still must not score F6 unless a later endpoint-field, ordinary-flow, F3,
and same-QOI UQ gate passes.
