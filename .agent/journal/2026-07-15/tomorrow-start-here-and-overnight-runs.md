# Journal: Tomorrow Start Here And Overnight Runs

Date: 2026-07-15
Task: AGENT-437

## Work Performed

Read the current board and blocker state, inspected live scheduler status for
the Box upload and corrected-Q continuation/harvest jobs, and consolidated the
July 15 work products into a handoff note for the next agent.

The handoff emphasizes that the next progress is executable analysis, not more
generic summary text:

- convert the mdot/temperature audit into setup-only predictive scorecards;
- implement the `M3+TS` test-section heat-loss successor rather than deleting
  the test section;
- preserve the current training/testing split, including Salt2/Salt4 +/-10Q
  rows as closest-to-postprocessing but still blocked on terminal harvest;
- freeze segment-resolved coupled pressure/thermal equations;
- advance closure-QOI, mesh/GCI, raw pressure, and recirculation gates through
  admission packages;
- keep recirculating upcomer rows out of ordinary single-stream `Nu`, `f_D`,
  and `K` fits.
- preserve the current hydraulic evidence classification: AGENT-373 stage
  rerun rows, AGENT-409 raw two-tap rows, AGENT-406 PM5 matched-plane rows, and
  AGENT-414 downstream review rows are diagnostic/onset evidence until an
  admission package explicitly promotes them.

## Live Jobs Checked

- `squeue -j 3297384`: running Box upload on `c318-011`.
- `squeue -j 3293924,3295438`: corrected-Q continuation running on `c318-016`;
  dependent harvest pending.
- `squeue -u andresfierro231`: also showed pre-existing `3295120` on
  NuclearEnergy-dev; it was not touched.
- `sacct -j 3295492`: nominal upcomer matched-plane compute completed
  successfully and should be harvested/parsed before relaunch.
- `sacct -j 3295901,3295968,3295989,3295990,3295991`: PM5/hydraulic
  dependency-chain jobs were cancelled before running; tomorrow should use the
  landed diagnostic AGENT-404/406/409/421/425 packages instead of waiting on
  those job IDs.
- Box upload sampled stdout: about `441 GiB / 603 GiB` copied (`73%`) with
  retryable rclone errors still present.

## Hydraulic Context Added At Closeout

- AGENT-421 reran the AGENT-373 chain locally into scratch: raw two-tap
  preflight `3` rows, F6 gate `4` rows, reset-K sweep `128` rows.
- AGENT-409 raw two-tap staged-copy diagnostics landed `3` Salt2/Salt3/Salt4
  rows with lower-minus-upper `p_rgh` values of `16.30560313 Pa`,
  `13.12073641 Pa`, and `11.8397775 Pa`.
- AGENT-406 PM5 matched-plane evidence has `12/12` wallHeatFlux rows.
- AGENT-414/425 review status remains F6 fit candidates `0`, internal-Nu fit
  candidates `0`, final hydraulic residual `blocked_not_final`, and final
  forward-v1 `blocked_no_go_final_forward_v1_not_admitted`.

No new sbatch jobs were launched. The overnight job list is a recommendation
matrix with launch conditions for a future claimed scheduler row.

## Files Created

- `operational_notes/07-26/15/2026-07-15_TOMORROW_START_HERE.md`
- `.agent/status/2026-07-15_AGENT-437.md`
- `.agent/journal/2026-07-15/tomorrow-start-here-and-overnight-runs.md`
- `imports/2026-07-15_tomorrow_start_here_and_overnight_runs.json`

## Guardrails

Native CFD outputs, registry/admission state, generated indexes, scheduler job
state, and external `../cfd-modeling-tools/**` were not mutated.
