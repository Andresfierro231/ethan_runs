---
provenance:
  - .agent/status/2026-07-17_AGENT-519.md
  - .agent/journal/2026-07-17/post-terminal-cfd-harvest-watch.md
tags: [work-product, scheduler, cfd-pp, harvest-watch, admission]
related:
  - imports/2026-07-17_post_terminal_cfd_harvest_watch.json
task: AGENT-519
date: 2026-07-17
role: Coordinator/Scheduler/cfd-pp/Writer
type: work_product
status: active
---
# Post-Terminal CFD Harvest Watch

This package assigns an active read-only monitor for CFD and dependent harvest
jobs that can unlock later terminal-admission packages. It is not a harvest
package and it is not an admission package.

## Current Decision

Keep monitoring. Do not submit duplicates.

The corrected-Q parent job `3293924` is still running, and the dependent
selected Salt2/Salt4 harvester `3295438` remains pending on dependency. The
high-heat Salt4 jobs `3299610` and `3299620` are also running. None of these
rows are harvest-ready at this snapshot.

## Watchlist

- Corrected-Q terminal chain: `3293924` -> `3295438`.
- High-heat/no-recirculation anchor chain: `3299610`, `3299620`.
- Context-only active job: `3300966` from AGENT-511. AGENT-519 does not own it.

## Terminal Trigger Rule

Only a terminal successful watched chain should trigger a new claimed
cfd-pp/admission row. This monitor may record the terminal state and source
paths, but it must not run the harvest itself.

For corrected-Q, the trigger is not simply `3293924` exiting. The dependent
harvest job `3295438` also needs to run, finish, and provide usable harvest
evidence before admission processing can start.

For high-heat jobs, the trigger is terminal success for `3299610` or `3299620`
plus readable staged outputs/logs. Recirculating rows remain onset/diagnostic
evidence unless a later admission package passes its gates.

## Forbidden Actions

- No `sbatch`.
- No `scancel`.
- No `scontrol update`, dependency edit, requeue, or partition change.
- No OpenFOAM or solver launch.
- No harvest/postprocessing scripts.
- No registry/admission mutation.
- No native CFD/OpenFOAM output mutation.
- No duplicate submissions for corrected-Q, high-heat, pressure, PM5, PM10, or
  future holdout/new-CFD rows.

## Read-Only Commands For Next Monitor Pass

```bash
squeue -u $(whoami)
sacct -j 3293924,3295438,3299610,3299620 --format=JobID,JobName%30,State,Elapsed,ExitCode
```

If those show a terminal-success trigger, claim a separate row before running
any harvest/admission work.

## 2026-07-21 Refresh

Read-only checks at `2026-07-21T17:19:14-0500` show no terminal-success
trigger:

- `3299610` / `salt4_q3x_probe`: `RUNNING`, elapsed `4-23:39:53`, node
  `c318-017`.
- `3299620` / `salt4_heat_pack`: `RUNNING`, elapsed `4-23:25:04`, node
  `c318-018`.
- `3307441` / `saltq_sel36_cont`: `RUNNING`, elapsed `08:21:05`, node
  `c318-020`.

If either high-heat job lands successfully, a separate S10/F6 pressure-anchor
harvest/preflight row is required before any parsing or admission work. If
`3307441` lands successfully, a separate S9/S13 corrected-Q source-family
harvest/preflight row is required.

## 2026-07-21 18:25 Refresh

Read-only scheduler/accounting refresh shows `3299610` and `3299620` are now
`TIMEOUT`, not successful terminal states. They do not trigger harvest or
admission. Corrected-Q continuation `3307441` remains `RUNNING` on `c318-020`
with four active `foamRun` steps.

Next monitor action is corrected-Q only: keep checking `3307441` until terminal
state. High-heat timeout disposition or recovery requires a separate claimed
row before any inspection-driven harvest, resubmission, or admission work.

## 2026-07-22 12:52 Refresh

Read-only accounting refresh at `2026-07-22T12:52:05-0500` shows no
terminal-success trigger:

- `3307441` / `saltq_sel36_cont`: `RUNNING`, elapsed `1-03:53:43`, node
  `c318-020`; batch plus four `foamRun` steps remain running.
- `3308712` / `salt4_heat2_pack`: `RUNNING`, elapsed `18:46:40`, node
  `c318-017`; batch plus four `foamRun` steps remain running.

Current action: keep `AGENT-519` active for read-only monitoring. Do not
harvest, parse, submit duplicates, cancel, requeue, mutate registry/admission
state, or open source/property/admission work until a separate row is claimed
after terminal success.
