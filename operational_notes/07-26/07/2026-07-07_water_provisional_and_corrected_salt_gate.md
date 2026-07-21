# Water Provisional And Corrected Salt Gate

Date: `2026-07-07`
Task: `AGENT-181`

## Decision

Use July 6 Water outputs only as provisional monitor-status evidence. Keep the
timeout/frozen-window caveat attached to every Water claim.

Do not admit any corrected Salt perturbation to closure or ROM fitting until
the replacement gate job finishes and the operating-point gate reports
`requalified`.

## Actions

- Built reusable read-only checker:
  `tools/analyze/check_corrected_salt_preflight.py`.
- Built reusable live corrected-Salt sanity monitor:
  `tools/analyze/monitor_live_corrected_salt.py`.
- Audited all 14 corrected Salt cases:
  `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/corrected_salt_preflight_audit.csv`.
- Wrote live monitor CSV/JSON/README:
  `work_products/2026-07-07_corrected_salt_live_monitor/`.
- Wrote Water provisional language audit:
  `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/water_provisional_language_audit.csv`.
- Created report package:
  `reports/2026-07/2026-07-07/2026-07-07_water_provisional_and_corrected_salt_gate/`.
- Submitted replacement Salt gate:
  `3279646` `saltq_gate_0707`, dependency
  `afterany:3275448:3275449:3275560`.

## Current Queue

- `3275448`, `3275449`, `3275560`: still running.
- `3275450`: canceled Salt 3 high-Q group; `salt3_jin_hi5q_corrected` advanced only about `21.5 s` past restart and `salt3_jin_hi10q_corrected` only about `19.9 s`.
- `3278453`: canceled old gate job.
- `3279646`: pending on dependency.

## Special Scrutiny

The live monitor currently flags four rows with
`needs_special_gate_scrutiny=True`:

- `salt1_jin_lo10q_corrected`: missing nominal Salt 1 mdot reference.
- `salt1_jin_hi10q_corrected`: missing nominal Salt 1 mdot reference and solver `End` after `254.259 s` past restart, only `4.24%` of target extension.
- `salt3_jin_hi5q_corrected`: job `3275450` canceled, fatal/error markers in the log, only `21.476 s` past restart.
- `salt3_jin_hi10q_corrected`: job `3275450` canceled, fatal/error markers in the log, only `19.876 s` past restart.

## Morning / Post-Finish Pickup

When `3279646` exits, inspect:

- `tmp/2026-07-07_corrected_salt_gate/slurm-saltq_gate_0707-3279646.out`
- `tmp/2026-07-07_corrected_salt_gate/slurm-saltq_gate_0707-3279646.err`
- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/corrected_salt_gate_after_3275448_3275449_3275560/run_status/run_status_inventory.csv`

Only rows with `operating_point_verdict=requalified` and
`closure_fit_admissible=yes` may feed closure fitting or ROM correlations, and
no row with `needs_special_gate_scrutiny=True` may be admitted without
coordinator review.

## Evening Supersession

The `3279646` pending-gate state above is superseded. A dependency-gated
continuation submission for `corr_saltq_g1` after `3275448` was attempted from
`login3`, but Slurm rejected the submission because project `ASC23046` had
`4633` SUs remaining and `4688` SUs already requested by running/waiting jobs.
No continuation job ID was created. Since the existing gates would have run
after the original live jobs rather than after the desired extensions, jobs
`3279638` and `3279646` were canceled; `sacct` reports both as
`CANCELLED by 890970` with no start time.

Coordinator review of `salt1_jin_hi10q_corrected` found that the case stopped
cleanly via the coded global `convergenceMonitor`, not by crash or by reaching
`endTime`. The log reports convergence at iteration `640600` and
`Time = 4010.590361446s`, only `254.259 s` past the corrected restart. The
case `controlDict` still targeted `endTime 9756.33125`, and the coded monitor
uses `rtol = 0.0001` on global `Tmean`, `Tsigma`, and `Umean` changes before
calling `stopAt(writeNow)`.

Salt 1 corrected-Q rows remain held for coordinator review and are not
closure-fit admissible. Next action is to wait for allocation capacity or an
approved alternate allocation, then submit continuation/rerun jobs with the
convergence monitor disabled or non-terminating and gate Salt 1 on
operating-point movement plus quasi-steady time-window UQ.
