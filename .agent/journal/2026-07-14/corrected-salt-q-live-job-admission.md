---
provenance:
  - .agent/status/2026-07-14_AGENT-313.md
  - operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/README.md
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/TODO.md
tags: [salt-q-perturbation, admission, scheduler-handoff, live-job]
related:
  - imports/2026-07-14_corrected_salt_q_live_job_admission.json
  - operational_notes/maps/cfd-runs-and-admission.md
task: AGENT-313
date: 2026-07-14
role: Coordinator/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Corrected Salt-Q Live Job Admission

I claimed `AGENT-313` to monitor corrected Salt-Q job `3293924` without
mutating solver outputs. I read the July 13 live-job handoff, the corrected
Salt-Q campaign README/TODO, the CFD admission map, and the AGENT-290 repair
status before inspecting scheduler/log state.

Observed facts:

- `sacct` showed `3293924`, `3293924.batch`, and all four `foamRun` steps
  `3293924.0`-`.3` still `RUNNING` on `c318-016`.
- Top-level elapsed time was `18:09:31`; each solver step had elapsed
  `18:09:08`.
- The batch stdout tail preserved the current repair contract:
  explicit four-case launch, `TIME_FORMAT=general`, `TIME_PRECISION=6`, and
  `Audited 4 corrected Salt cases; failures=0`.
- The current solver-log tails showed all four cases advancing past the
  selected integer restarts.
- Latest live `Time =` lines seen were:
  `salt2_lo10q` `10633.766871 s`, `salt2_hi10q` `10004.348066 s`,
  `salt4_lo10q` `11942.703125 s`, and `salt4_hi10q` `12877.584112 s`.
- The selected staged `system/controlDict` files still show `startFrom
  startTime`, the expected integer `startTime`s, `stopAt endTime`,
  `endTime 30000`, `timeFormat general`, and `timePrecision 6`.
- The sbatch script has a `120:00:00` wall time.

Interpretation:

The corrected selected Salt-Q continuation is live and progressing. None of the
four selected rows has terminal admission evidence yet. Because the job is
still running, each row is blocked from downstream analysis pending the terminal
harvest and operating-point convergence gate. No row is admitted, failed, or
diagnostic-classified from this heartbeat alone.

Caution:

The full solver logs contain historical appended fatal blocks from previous
failed attempts, so an unconstrained `rg` over the whole log is not a valid
live-failure detector. Use scheduler state and current log tails while the job
is running; after exit, use terminal line ranges/tails and the documented gate.

Next action:

Monitor `3293924` until Slurm reports a terminal state for the top-level job and
all four steps. Then run the terminal harvest sequence from
`operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md`.
Do not launch duplicate corrected-Q work while this job remains live.

No native CFD solver outputs were modified.
