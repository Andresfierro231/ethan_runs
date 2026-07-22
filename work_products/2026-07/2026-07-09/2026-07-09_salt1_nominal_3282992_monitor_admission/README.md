# Salt1 Nominal 3282992 Live Monitor And Admission Memo

Date: `2026-07-09`
Checked at: `2026-07-09T16:30:41-05:00`
Task: `AGENT-242`
Role: Coordinator / Reviewer / Writer

## Verdict

Salt1 nominal job `3282992` is **not usable yet** and remains **excluded from
closure fits**.

This is not a failure verdict. The live evidence says the run is currently
healthy and advancing, but it is still running and therefore lacks terminal
gate evidence. Do not use Salt1 nominal as the low-Re endpoint until the job
exits and the post-run admission checks pass.

Machine-readable verdict:

- `admission_verdict.csv`

## Evidence Snapshot

Scheduler/accounting snapshot:

- `3282992` / `salt1_nom_cont` is `RUNNING` on `NuclearEnergy`.
- Job start: `2026-07-08T13:21:42`.
- `foamRun` step start: `2026-07-08T13:29:18`.
- Elapsed at check: `1-03:08:59`.
- Time limit: `5-00:00:00`.
- Node: `c318-016`.
- Current accounting exit code fields are `0:0`, but the job is still running,
  so this is not a completed-run verdict.

Machine-readable scheduler snapshot:

- `scheduler_snapshot.csv`

Case and control evidence:

- Campaign README and manifest identify this as
  `salt1_jin_nominal_continuation_corrected`, staged from the June 25
  `salt1_jin_basecont` candidate at source restart time `4026.15625 s`.
- `system/controlDict` uses `startFrom latestTime`, `stopAt endTime`, and
  `endTime 10000`.
- The corrected convergence monitor is diagnostic-only: it logs the criterion
  and continues to configured `endTime`.

Live OpenFOAM evidence:

- Case log inspected:
  `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/logs/log.foamRun_salt1_nominal_continuation`
- Log lines at snapshot: `3,416,795`.
- Latest solver time at snapshot: `Time = 4996.6625s`.
- Latest execution line: `ExecutionTime = 96335.2216 s  ClockTime = 97291 s`.
- Latest Courant line: `Courant Number mean: 0.0799473205 max: 0.999294798`.
- Fatal/cancel marker counts were zero for `FOAM FATAL`, `Fatal`, `fatal`,
  `FOAM exiting`, `Segmentation`, `Floating point`, `MPI_ABORT`, `SIGSEGV`,
  `SIGFPE`, `CANCELLED`, and `cancelled`.

Monitor evidence:

- The diagnostic convergence criterion fired at iteration `662700` with
  `dTmean=1.67129068e-05`, `dTsigma=9.76646245e-05`,
  `dUmean=2.333543e-05`, and `tol=0.0001`.
- The following live log message then confirms the intended policy:
  `convergenceMonitor: continuing to configured endTime; Salt1 nominal continuation qualification is handled by post-run operating-point and time-window gates`.
- This is useful evidence that the earlier premature monitor-stop failure mode
  was avoided, but it is not terminal admission evidence.

PostProcessing evidence:

- `postProcessing/total_Q.dat`: `970` data rows, first time `4027.0`, latest
  time `4996.0`.
- `postProcessing/velocity_profiles`: `971` numeric time directories, through
  `4996.0`.
- `postProcessing/wallHeatFlux` and `postProcessing/yPlus`: one visible
  directory each at `4027.0` in this live snapshot.
- `processors64`: retained numeric write/restart directories through `4996.0`;
  `purgeWrite 21` means absence of all intermediate write directories is not
  itself suspicious.

Machine-readable evidence inventory:

- `live_evidence_inventory.csv`

## Admission Rule For Salt1

Salt1 nominal can only become usable after a terminal audit establishes all of
the following:

1. `sacct` reports a terminal non-failure state for `3282992`, including the
   `foamRun` step.
2. The Slurm stdout/stderr and case log have no fatal, cancel, MPI abort,
   floating-point, segmentation, or failed boundary-condition markers.
3. The solver either reaches configured `endTime 10000` or leaves a defensible
   final written/sampled terminal window that satisfies the same operating-point
   rigor used for Salt2/3/4.
4. Final postProcessing samples exist for the required operating-point and heat
   diagnostics; do not rely only on the diagnostic convergenceMonitor trigger.
5. A post-run gate/memo explicitly admits Salt1 nominal before any F5/Ri, F6,
   or nominal-band closure fit uses it.

## Required Exit Harvest

When `3282992` exits, run the terminal harvest before changing any fit set:

```bash
squeue -j 3282992 -o '%i|%j|%T|%P|%M|%l|%D|%R'
sacct -j 3282992 --format=JobIDRaw,JobID,JobName%34,State,ExitCode,Submit,Start,End,Elapsed,Timelimit,NNodes,AllocCPUS -P
tail -120 jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/slurm-salt1_nom_cont-3282992.out
tail -120 jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/slurm-salt1_nom_cont-3282992.err
tail -160 jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/logs/log.foamRun_salt1_nominal_continuation
rg -n 'FOAM FATAL|Fatal|fatal|FOAM exiting|Segmentation|Floating point|MPI_ABORT|SIGSEGV|SIGFPE|CANCELLED|cancelled' jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/logs/log.foamRun_salt1_nominal_continuation
```

Then build a terminal admission memo that cites final log time, final
postProcessing horizons, and the actual operating-point gate outcome.

## Boundary

No native solver output was edited, deleted, copied over, or promoted into a
closure fit during this live monitor pass.
