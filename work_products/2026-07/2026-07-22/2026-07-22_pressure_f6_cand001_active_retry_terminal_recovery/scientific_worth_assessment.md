---
provenance:
  generated_by: tools/analyze/build_pressure_f6_cand001_active_retry_terminal_recovery.py
  task_id: TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22
  generated_at_utc: 2026-07-22T13:07:54.140688+00:00
task: TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22
tags:
  - pressure
  - CAND001
  - scientific-worth
  - retry-gate
related:
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery/worth_trying_decision.csv
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery/post_terminal_decision_tree.csv
---

# Scientific worth assessment

## Finding

Continue CAND001 only as an active monitor of job `3308712`. Do not
launch a duplicate scheduler job. Do not score F6.

## Analysis

The retry is still scientifically defensible because the negative evidence so
far is operational: jobs `3299610` and `3299620` timed out. Timeout means the
source family has not yet produced terminal fields; it is not evidence that the
pressure decomposition is physically wrong.

The expected value is limited but real. A successful terminal run would provide
a low-recirculation/high-heat Salt4 source family that can be checked for
steady-state drift, endpoint field availability, and RAF/RMF/SVF ordinary-flow
status. Only after those checks could a separate endpoint harvest row be
considered.

The work should stop or pivot if `3308712` times out again, finishes
with unacceptable drift, or remains strongly recirculating at the target
sections. In those cases CAND001 should remain diagnostic/blocked and CAND002
or another lower-recirculation source family should be considered.
