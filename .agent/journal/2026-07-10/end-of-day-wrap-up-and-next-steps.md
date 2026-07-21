# End-of-Day Wrap-Up and Next Steps

Date: 2026-07-10
Role: Coordinator / Writer
Latest scheduler refresh: `2026-07-10T17:23:00-0500`

## Observed State

This wrap-up used scheduler snapshots plus existing AGENT-248, AGENT-249, and
AGENT-250 products. It did not mutate native solver outputs and did not submit
new work.

Live jobs at wrap-up:

| Job | Name | State | Interpretation |
| --- | --- | --- | --- |
| `3282992` | `salt1_nom_cont` | RUNNING on `c318-016`, elapsed `2-04:01:18` | Salt1 nominal is still advancing. Keep it excluded from closure fits until it exits and passes the same terminal admission gate used for Salt2/3/4. |
| `3288671` | `saltq_sel_cont` | RUNNING on `c318-017`, elapsed `05:03:37` | Packed selected corrected-Q job is partially healthy. Salt1 -10Q and Salt1 +10Q steps are running; Salt4 +10Q step failed. |
| `3288637` | `agent248_salt2_pressure` | CANCELLED before node assignment | Correctly canceled as duplicate after immediate Salt2 medium/fine pressure-only extraction completed. No monitoring required. |

The `3288671.2` failed step is `salt4_jin_hi10q_corrected`. The case log reports
OpenFOAM maximum time precision at current time name `11536.488262910847`. Treat
this as a launch/controlDict precision repair, not physical non-convergence and
not a reason to bulk-resubmit other corrected-Q rows.

## Completed Today

- Salt2 refined medium/fine pressure-only extraction was smoke-tested and then
  completed immediately on a compute node. It produced section/friction/momentum
  outputs and avoids the reconstructed-`T` blocker. Thermal closure remains
  blocked.
- Selected corrected-Q continuation job `3288671` was submitted for three rows
  only: Salt1 -10Q, Salt1 +10Q, Salt4 +10Q. These rows remain sensitivity /
  correlation-support, not nominal baselines.
- Registry-driven corrected-Q table generator was added and all 14 corrected-Q
  manifest rows were registered with strict-clean coverage.

## What Not To Submit Tonight

- Do not bulk-resubmit all corrected-Q rows.
- Do not resubmit Salt2 pressure extraction; the immediate rerun completed and
  the scheduled duplicate was canceled.
- Do not submit Salt4 +10Q corrected blindly. First repair the time-precision /
  restart-name issue and preflight the exact restart directory.
- Do not launch closure refits using corrected-Q perturbation rows unless a
  post-continuation gate explicitly admits terminal windows.

## Candidate Submissions After Checks

1. Let `3282992` continue to exit or walltime, then harvest Salt1 nominal logs,
   postProcessing, final writes, and terminal gate diagnostics. Only then decide
   whether Salt1 nominal is usable.
2. Let the surviving `3288671` Salt1 corrected-Q steps continue. When they exit,
   run the same admission diagnostics as the completed corrected-Q gate.
3. Prepare a targeted Salt4 +10Q corrected repair-only resubmit after resolving
   the time precision failure. The expected fix is a controlDict/start-time
   precision/restart naming repair, followed by a single-row preflight and
   single-row continuation.
4. Start a pressure-only mesh-family comparison/sign review from the completed
   Salt2 refined pressure outputs. This is analysis work, not another extraction
   job.

## TODO For Tomorrow

- Monitor `3282992` and `3288671` with `squeue`/`sacct`.
- For `3288671`, explicitly record that Salt4 +10Q failed while the two Salt1
  corrected-Q steps continued.
- Harvest final logs and postProcessing only after job exit; do not infer
  admission from a running log tail.
- Repair Salt4 +10Q corrected time precision before any resubmit.
- Run/adapt the corrected-Q admission table generator after terminal evidence is
  available so the status table reflects post-continuation outcomes.
- Build the Salt2 refined pressure-only comparison and review rows marked
  `negative_f_pressure_recovery_or_noise` before fit/GCI admission.
- Keep all perturbation rows labeled as sensitivity/correlation-support.

## Key References

- `work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/`
- `work_products/2026-07/2026-07-10/2026-07-10_corrected_salt_selected_q_steadiness_packed_resubmit/`
- `work_products/2026-07/2026-07-10/2026-07-10_registry_corrected_q_status_table/`
- `.agent/status/2026-07-10_AGENT-248.md`
- `.agent/status/2026-07-10_AGENT-249.md`
- `.agent/status/2026-07-10_AGENT-250.md`
