---
provenance:
  - .agent/status/2026-07-17_AGENT-519.md
  - work_products/2026-07/2026-07-17/2026-07-17_post_terminal_cfd_harvest_watch/README.md
tags: [journal, scheduler, cfd-pp, harvest-watch, admission]
related:
  - imports/2026-07-17_post_terminal_cfd_harvest_watch.json
task: AGENT-519
date: 2026-07-17
role: Coordinator/Scheduler/cfd-pp/Writer
type: journal
status: active
---
# Post-Terminal CFD Harvest Watch

The user requested a post-terminal CFD harvest watch: assign a scheduler
read-only monitor for live/future jobs and terminal-admission readiness, with
no duplicate submissions.

I claimed `AGENT-519` as an active monitor row rather than a harvest row. The
row is intentionally read-only: it can inspect `squeue`/`sacct` state and write
handoff documentation, but it cannot submit, cancel, requeue, edit Slurm
dependencies, launch solvers, run postprocessing, mutate native outputs, or
change admission state.

The current scheduler snapshot shows the corrected-Q parent `3293924` still
running and the selected Salt2/Salt4 harvester `3295438` still dependency-held.
That means the correct action is to continue monitoring, not to duplicate the
harvester. High-heat jobs `3299610` and `3299620` are also running and should
only trigger a later harvest/admission row after terminal success.

The package under
`work_products/2026-07/2026-07-17/2026-07-17_post_terminal_cfd_harvest_watch/`
records the watchlist, trigger matrix, source manifest, and duplicate
submission guardrails so tomorrow's agent can continue without relying on chat
context.

## 2026-07-21 Refresh

I refreshed the monitor from read-only scheduler/accounting state at
`2026-07-21T17:19:14-0500`. The watched jobs are still running: `3299610` at
`4-23:39:53` on `c318-017`, `3299620` at `4-23:25:04` on `c318-018`, and
corrected-Q continuation `3307441` at `08:21:05` on `c318-020` with four
active `foamRun` steps.

There is no terminal-success trigger yet. The monitor should keep doing only
read-only checks. A successful `3299610` or `3299620` should trigger a separate
S10/F6 pressure-anchor harvest/preflight row. A successful `3307441` should
trigger a separate S9/S13 corrected-Q source-family harvest/preflight row.
