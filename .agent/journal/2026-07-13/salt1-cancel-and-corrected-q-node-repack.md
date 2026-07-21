# Salt1 Cancel And Corrected-Q Node Repack

Date: `2026-07-13`
Task: `AGENT-268`
Role: Coordinator / Writer

## User Decision

The user stated that normal Salt1 is done and requested:

- end normal Salt1,
- stop Salt1 -10Q,
- keep Salt4 +10Q running,
- assess other Salt runs worth using on the node for the remaining allocation
  time.

## Actions

Executed:

```bash
scancel 3282992
scancel 3288671.0
```

No broad allocation cancellation was run. In particular, `scancel 3288671` was
not run because that would also kill Salt4 +10Q.

## Scheduler Evidence

Snapshot time: `2026-07-13T11:09:18-05:00`.

`squeue -u $USER` showed:

- `3288671` `saltq_sel_cont` running on `c318-017`, elapsed `2-22:51:06`,
  time limit `5-00:00:00`.
- `3292998` interactive job running on `c318-008`.

`sacct -j 3282992,3288671` showed:

- `3282992` `CANCELLED by 890970`, allocation `c318-016`.
- `3282992.0` `CANCELLED`, exit `0:15`.
- `3288671` `RUNNING`, allocation `c318-017`.
- `3288671.0` `CANCELLED by 890970`.
- `3288671.1` `RUNNING`.
- `3288671.5` `RUNNING`.
- `3288671.2`, `.3`, and `.4` are historical failed attempts.

Step audit showed live corrected-Q steps:

- `3288671.1` `foamRun`, elapsed about `2-22:49:39`.
- `3288671.5` `foamRun`, elapsed about `2-17:32:30`.
- `3288671.batch` still running.

## Interpretation

Observed:

- Normal Salt1 and Salt1 -10Q have been stopped as requested.
- Salt4 +10Q remains live.
- Salt1 +10Q remains live because the user did not request cancelling it.
- The corrected-Q allocation is a 256-CPU node with two live 64-rank steps, so
  there should be roughly two 64-rank step slots available if the launcher is
  still healthy.

Inferred:

- If using the freed capacity now, the lowest-risk, highest-value add is the
  Salt2 symmetric +/-10Q pair.
- Salt1 +10Q can be considered for cancellation if a third slot is needed. A
  latest 600 s read-only check found flat heat and mdot traces, but this note
  does not authorize or perform that cancellation.

## Candidate Ranking

Recommended first:

- `salt2_jin_lo10q_corrected`
- `salt2_jin_hi10q_corrected`

Rationale:

- July 9 minimal continuation plan names only these two rows as the minimal
  first wave.
- July 13 latest-time refresh still classifies them as first-wave continuation
  candidates.
- They provide the smallest useful symmetric bracket around one nominal Salt2
  case.
- They avoid Salt1 reference-policy ambiguity and Salt3 high-Q investigation
  debt.

Second wave only if the first pair is launched cleanly and the node still has
capacity:

- Salt2 +/-5Q for midpoint/linearity support.
- Salt4 -10Q only after the current Salt4 +10Q is closer to steady or after
  Salt2 proves the continuation settings.

Avoid for now:

- Salt3 +5Q and Salt3 +10Q until their cancelled/superseded attempts are
  diagnosed.
- Bulk corrected-Q resubmission.

## Gate Warning

The July 9 gate notes warn that the formal operating-point gate uses
`tau_thermal=5000 s` and `min_tau_advance=3`, implying roughly `15000 s`
post-restart advance. A short continuation can still fail as `too_short`.
Before launching the Salt2 pair, the next implementer should either set the
target high enough for that gate or document a reviewed gate-policy change.

## Files Consulted

- `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_gate_3280969_review/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_corrected_q_latest_time_refresh/corrected_q_latest_timesteps.csv`

