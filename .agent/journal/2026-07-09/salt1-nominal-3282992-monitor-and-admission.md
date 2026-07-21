# Salt1 Nominal 3282992 Monitor And Admission

Date: `2026-07-09`
Task ID: `AGENT-242`
Role: Coordinator / Reviewer / Writer

## Request

Monitor Salt1 nominal continuation job `3282992`, harvest logs,
postProcessing, and admission diagnostics, and decide whether Salt1 nominal
becomes usable or remains excluded.

## Observed Output

- `squeue` at `2026-07-09T16:30:41-05:00` showed
  `3282992|salt1_nom_cont|RUNNING|NuclearEnergy|1-03:08:59|5-00:00:00|1|c318-016`.
- `sacct` showed the parent job, batch step, and `foamRun` step all still
  running with current accounting `ExitCode 0:0`.
- The case log had advanced to `Time = 4996.6625s`, with
  `ExecutionTime = 96335.2216 s  ClockTime = 97291 s`.
- Targeted fatal/cancel marker counts were zero in the case log.
- The diagnostic convergence monitor fired at iteration `662700` and then
  logged that it was continuing to configured `endTime`; this confirms the
  corrected monitor is not doing the old early `stopAt(writeNow)` behavior.
- `postProcessing/total_Q.dat` had `970` data rows through time `4996.0`.
- `postProcessing/velocity_profiles` had `971` numeric time directories through
  time `4996.0`.

## Interpretation

Salt1 nominal is healthy in progress but not admitted. Because `3282992` is
still running, the run lacks terminal job accounting, final write/sample
availability, and a post-run operating-point/time-window gate verdict. The
diagnostic convergence monitor trigger is helpful progress evidence only; it
must not be substituted for the same rigor bar used for Salt2/3/4.

## Decision

Salt1 nominal remains excluded from closure fits until a terminal audit admits
it explicitly.

Do not use Salt1 nominal in F5/Ri, F6, or nominal-band closure fitting yet.

## Artifacts

- `work_products/2026-07/2026-07-09/2026-07-09_salt1_nominal_3282992_monitor_admission/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_salt1_nominal_3282992_monitor_admission/scheduler_snapshot.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_salt1_nominal_3282992_monitor_admission/live_evidence_inventory.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_salt1_nominal_3282992_monitor_admission/admission_verdict.csv`

## Next Terminal Check

After job exit, rerun `squeue`, `sacct`, Slurm stdout/stderr tails, full
fatal-marker scan, final solver-log tail, and final postProcessing horizon
inventory. Then write a terminal admission memo before moving Salt1 anywhere
near closure fits.

No native solver output was modified.
