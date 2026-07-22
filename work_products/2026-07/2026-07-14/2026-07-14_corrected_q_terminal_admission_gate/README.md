---
provenance:
  - .agent/status/2026-07-14_AGENT-320.md
  - .agent/journal/2026-07-14/corrected-q-terminal-admission-gate.md
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.out
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.err
tags: [salt-q-perturbation, admission, live-job, scheduler-handoff]
related:
  - operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md
  - operational_notes/maps/cfd-runs-and-admission.md
task: AGENT-320
date: 2026-07-14
role: Coordinator/Writer
type: work_product
status: complete
---
# Corrected-Q Terminal Admission Gate

Checked at `2026-07-14T11:47:34-05:00`.

## Decision

Corrected Salt-Q job `3293924` is not terminal. No corrected-Q rows are
admitted, validation-ready, or fit-ready from this gate.

## Scheduler State

`sacct` reports the top-level job, batch step, and all four `foamRun` steps as
`RUNNING` on `c318-016`:

- top-level elapsed: `18:43:38`
- each `foamRun` step elapsed: `18:43:15`
- exit code fields still report `0:0` because the job is live, not complete
- Slurm `End` is `Unknown`

Batch stdout confirms the repaired launch contract: four selected cases,
explicit restart patching, `TIME_FORMAT=general`, `TIME_PRECISION=6`, and
`Audited 4 corrected Salt cases; failures=0`.

## Case Rows

| row | Slurm step | latest live solver time seen | classification |
| --- | --- | ---: | --- |
| `salt2_lo10q` | `3293924.0` | `10644.337423 s` | blocked_pending_terminal_gate |
| `salt2_hi10q` | `3293924.1` | `10014.348066 s` | blocked_pending_terminal_gate |
| `salt4_lo10q` | `3293924.2` | `11951.598958 s` | blocked_pending_terminal_gate |
| `salt4_hi10q` | `3293924.3` | `12885.023364 s` | blocked_pending_terminal_gate |

## Next Gate

Re-run the terminal harvest only after `sacct` shows a terminal state for
`3293924`, `3293924.batch`, and `3293924.0`-`.3`. Slurm completion alone is not
admission; each row still needs terminal solver evidence, convergence/steadiness
metrics, boundary-condition labels, and provenance.
