---
provenance:
  generated_by: tools/analyze/build_pressure_f6_cand001_active_retry_terminal_recovery.py
  task_id: TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22
  generated_at_utc: 2026-07-22T13:07:54.140688+00:00
task: TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22
tags:
  - status
  - pressure
  - CAND001
related:
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery
---

# TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22

## Objective

Claim and close a separate pressure-owned scheduler retry follow-up row for
CAND001 that only recovers terminal source evidence and cannot score F6.

## Outcome

Decision: `continue_existing_cand001_retry_monitor_only_no_duplicate_submit`.
The active relaunch job is `3308712` with `4`
CAND001 source cases in the relaunch manifest. CAND001 is still worth monitoring
because prior failures were timeouts rather than physics rejections, but no new
job was submitted and no sampler/F6 work was authorized.

## Changes Made

- Wrote `work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery/README.md`.
- Wrote `work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery/scientific_worth_assessment.md`.
- Wrote scheduler/source/guardrail CSVs and summary JSON under
  `work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery`.
- Wrote this status, a journal entry, and an import manifest.

## Validation

- `python3.11 -m py_compile tools/analyze/build_pressure_f6_cand001_active_retry_terminal_recovery.py tools/analyze/test_pressure_f6_cand001_active_retry_terminal_recovery.py`: passed.
- `python3.11 tools/analyze/test_pressure_f6_cand001_active_retry_terminal_recovery.py`: passed with Slurm read access.
- Scheduler snapshot at `2026-07-22T13:07:54.140688+00:00`: job `3308712` was `RUNNING` on `c318-017` with four running `foamRun` steps; prior jobs `3299610` and `3299620` remained `TIMEOUT`.
- `python3 tools/docs/build_repo_index.py --check`: passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22`: passed.

## Guardrails

- Native-output mutation: false.
- Registry/admission mutation: false.
- Scheduler submission/cancel/requeue: false.
- Solver/postprocessing/sampler/harvest launch: false.
- F6 fit/scoring, component-K, cluster-K, clipped-K, hidden/global multiplier:
  false.
- S11/S15/S6 trigger: false.
- Fluid/external edit: false.
