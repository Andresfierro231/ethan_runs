---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness/summary.json
tags: [pressure, f6, low-recirculation, scheduler-readiness, no-admission]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-F6-LOW-RECIRC-SOURCE-READINESS-2026-07-21.md
  - imports/2026-07-21_pressure_f6_low_recirc_source_readiness.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness/README.md
task: TODO-PRESSURE-F6-LOW-RECIRC-SOURCE-READINESS-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: journal
status: complete
---
# Pressure/F6 Low-Recirculation Source Readiness

## Attempted

I implemented the F6 readiness phase of the planned next-step sequence. The
goal was to determine whether any existing low-recirculation source family can
justify a later staged-copy F6 endpoint sampler and same-QOI UQ pass.

The planned S13 same-window UQ design phase was already completed in the active
board state before this implementation started, so I treated it as read-only
context and included its status in the F6 handoff rather than overwriting it.

## Observed

The prior low-recirculation anchor package preferred `CAND-001`, the Salt4
high-heat/no-recirculation probe family, but had zero terminal-ready cases.
Read-only scheduler/accounting refresh changed the detail but not the decision:
job `3299610` for `salt4_q3x_probe` is `TIMEOUT`, and job `3299620` for
`salt4_heat_pack` is still `RUNNING`.

All `CAND-001` endpoint fields remain blocked pending terminal staged-copy
sampling. Current F6 endpoint evidence still has `0/10` ordinary candidate
pairs. Existing pressure-corner rows remain section-effective diagnostics and
are not ordinary F6 anchors.

The completed S13 UQ design reports `0` S11-reviewable candidates, no UQ
release, and no sampler or harvest allowance. That keeps S13 useful as parallel
infrastructure but not as an F6 admission shortcut.

## Inferred

No F6 sampler should run yet. The next scientific gate is still source readiness:
the high-heat family must either land terminal-successfully or fail closed. Only
after a terminal source exists should a separate staged-copy endpoint sampler
be claimed.

The publication claim freeze remains unchanged: pressure rise around corners is
hydrostatic/recovery/section-effective/diagnostic evidence, and F6 is
diagnostic-only under current evidence.

## What Worked

The readiness refresh converted the vague "refresh scheduler state" blocker
into concrete evidence: one cited high-heat job timed out and one remains
running. The package now gives the next agent a precise no-go decision and the
conditions required to reopen sampler work.

## What Did Not Work

The source family still does not provide a terminal ordinary-flow anchor. No
endpoint fields, RAF/RMF/SVF rows, same-QOI UQ, or F3 comparison can be produced
from this task without violating guardrails.

## Caveats

This task did not inspect native solver fields or mutate staged/source cases.
The scheduler observations are read-only snapshots from `squeue`/`sacct`; a
later monitor/source-readiness task must refresh them before any sampler launch
decision.

## Next Useful Actions

Monitor `3299620` to terminal state and separately review `3299610` timeout
disposition. If a source family becomes terminal-successful and endpoint fields
are available, claim a new staged-copy F6 endpoint sampler/UQ row. Otherwise,
fail-close `CAND-001` and evaluate whether `CAND-002` has become terminal
admitted.
