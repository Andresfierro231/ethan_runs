---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_smoke_duplicate_3311113_monitor/summary.json
tags: [journal, s13, scheduler-monitor, duplicate-smoke]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-SMOKE-DUPLICATE-3311113-MONITOR-2026-07-22.md
  - imports/2026-07-22_s13_medium_fine_smoke_duplicate_3311113_monitor.json
task: TODO-S13-MEDIUM-FINE-SMOKE-DUPLICATE-3311113-MONITOR-2026-07-22
date: 2026-07-22
role: Scheduler Monitor / cfd-pp / Reviewer / Writer
type: journal
status: complete
---
# S13 Medium/Fine Smoke Duplicate 3311113 Monitor

## Attempted

Claimed a narrow monitor/cancel row after Slurm accounting showed two
`s13_mf_smoke` jobs: canonical job `3311109` and unexpected duplicate job
`3311113`.

## Observed

Job `3311109` completed and wrote the canonical smoke output tree with nonempty
exact-label QOI rows. Job `3311113` was still running into a separate
`salt2_medium_one_window_smoke` output tree that had only header/pre-reduction
files at inspection time.

## Inferred

The duplicate did not need to continue because the canonical smoke already
answered the repair-gate question. The duplicate's partial files should not be
used for science or admission.

## Next Useful Actions

Use the canonical `3311109` smoke package to close the S13 face-area repair
row. If broader medium/fine evidence is needed, claim a separate full six-case
rerun row after explicitly preserving the smoke result and mesh/time-equivalence
gate.
