---
provenance:
  - .agent/status/2026-07-15_AGENT-446.md
  - imports/2026-07-15_switch_m3ts_val_jobs_to_nuclearenergy.json
tags: [journal, AGENT-446, scheduler, partition-switch]
task: AGENT-446
date: 2026-07-15
type: journal
status: complete
---
# Switch M3TS / val_salt2 Jobs to NuclearEnergy

The user requested that the AGENT-439 jobs still queued on `development` be
switched to `NuclearEnergy`.

## Action

Used `scontrol update` through `login3` to modify the original pending job IDs:

- `3297842` / `val_s2_ext`: `development` -> `NuclearEnergy`.
- `3297844` / `m3ts_score`: `development` -> `NuclearEnergy`.

The PM5/onset job `3297843` was already running on `NuclearEnergy`.

## Verification

`squeue` and `sacct` showed all three AGENT-439 jobs on `NuclearEnergy` after
the update. `3297842` and `3297844` remain pending for priority with no
dependency; `3297843` remains running.

No resubmission or cancellation was performed.
