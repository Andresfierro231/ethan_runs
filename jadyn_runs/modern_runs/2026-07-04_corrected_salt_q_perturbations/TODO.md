- [x] Document why the previous Salt perturbation roots are invalid.
- [x] Stage corrected Salt Q perturbation roots from nominal continuations.
- [x] Patch root `0/T` for every intended heater/cooler patch.
- [x] Add launch-time patching for copied `processors64/<latest>/T`.
- [x] Run local BC patch/audit smoke checks.
- [x] Fix strict-mode OpenFOAM bootstrap failure observed in jobs `3275388`-`3275391`.
- [x] Fix comma-splitting Slurm export bug observed in jobs `3275392`-`3275395`.
- [x] Fix broken post-OpenFOAM `python` resolution and enforce patcher failure before `foamRun`.
- [x] Fix binary/collated `decomposedBlockData` restart patching and verify processor block framing.
- [x] Stage parent `dynamicCode/` to avoid fresh parallel coded-function compilation failures.
- [ ] Verify current submitted jobs pass launch preflight for every group.
- [x] Monday: build a reusable automated preflight checker that fails a case
      unless `case_config.yaml`, root `0/T`, and
      `processors64/<latest>/T` agree for every target thermal patch. It must
      validate all target patch counts, preserve/verify collated
      `decomposedBlockData` frames, and write a documented audit artifact.
- [x] Extend the corrected-Salt preflight to reject unsafe large-time adaptive
      continuation controls for explicit integer restart repairs: wrong restart
      directory, `latestTime` instead of the selected `startTime`, fixed-format
      restart attempts, or higher general-format precision.
- [x] Monitor selected continuation job `3293924` through the initial startup
      window; all four `foamRun` steps were still `RUNNING` after about 2.5 min
      with explicit integer `startTime`, `timeFormat general`, and
      `timePrecision 6`.
- [x] Document tomorrow pickup for live job `3293924`:
      `operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md`.
- [ ] Re-run operating-point convergence gate after the jobs produce late windows.
- [x] 2026-07-21: submitted selected Salt2/Salt4 corrected-Q latest-restart
      continuation `3307441` (`saltq_sel36_cont`) for 36 hours from retained
      integer restarts `12382`, `11668`, `13421`, and `14017`; in-job preflight
      passed and all four `foamRun` steps advanced past startup on `c318-020`.
- [ ] Monitor `3307441` through terminal state, then re-run mdot plus thermal
      stationarity checks before any admission/harvest decision. Do not submit a
      duplicate selected harvester while this continuation is running.
- [ ] Admit only `requalified` rows to closure fitting.
- [ ] Before any Salt 1 corrected-Q rerun/continuation is submitted, verify the
      included `system/functions` `convergenceMonitor` is diagnostic-only and
      cannot call `stopAt(writeNow)`; then gate the result on operating-point
      movement plus quasi-steady time-window UQ.
- [ ] 2026-07-08 pickup: retry Slurm SU/accounting check and submit
      dependency-gated continuation jobs only if allocation capacity allows:
      `corr_saltq_g1` after `3275448`, `corr_saltq_g2` after `3275449`, and
      `corr_saltq_salt4_all` after `3275560`; submit the formal gate only
      after those continuation job IDs exist.
