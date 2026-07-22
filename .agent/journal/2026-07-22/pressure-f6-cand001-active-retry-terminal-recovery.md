---
provenance:
  generated_by: tools/analyze/build_pressure_f6_cand001_active_retry_terminal_recovery.py
  task_id: TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22
  generated_at_utc: 2026-07-22T13:07:54.140688+00:00
task: TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22
tags:
  - journal
  - pressure
  - CAND001
related:
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery
---

# CAND001 active retry terminal recovery

## Attempted

Claimed a pressure-owned active retry row, read the prior S10/S14 retry/UQ gate,
the CAND001 timeout disposition, the low-recirculation source readiness table,
and the high-heat steady relaunch manifest. Queried scheduler/accounting state
for `3308712` and prior timeout jobs using read-only commands.

## Observed

The previous CAND001 jobs timed out before terminal source evidence. The current
active relaunch package contains four CAND001 Salt4 high-heat/no-recirculation
source cases targeted to `22000 s`. The scheduler snapshot recorded state
`RUNNING` for `3308712` at `2026-07-22T13:07:54.140688+00:00`.

## Inferred

CAND001 is worth continuing only as monitor-only terminal source recovery. The
scientific basis is that timeout is not a physics rejection and terminal fields
could still unlock a later readiness decision. It remains non-evidence for F6
until terminal success, steady-state review, endpoint fields, ordinary-flow
screening, F3 comparison, and same-QOI UQ all pass under future rows.

## Contradictions or Caveats

The relaunch can become worthless for pressure admission if it times out again,
if drift remains large, or if endpoint sections remain nonordinary. This package
does not inspect native fields or make any flow-quality finding.

## Next Useful Actions

After `3308712` reaches terminal scheduler state, claim a terminal
disposition/readiness row. If successful, document terminal times, drift,
endpoint-field availability, and RAF/RMF/SVF screening. If failed, classify the
failure and decide whether CAND002 or another source family is a better use of
compute.
