# 2026-07-13 Live-Job Heartbeat And Cleanup Call

Task: `AGENT-259`
Role: Coordinator / Writer
Snapshot time: `2026-07-13T10:19:15-05:00`
Host: `c318-008.ls6.tacc.utexas.edu`

## Summary

Both carry-over CFD jobs from the July 10 handoff are still running. Salt1
nominal `3282992` is live on `c318-016`. Selected corrected-Q job `3288671` is
live on `c318-017`, including the repaired Salt4 +10Q attached step
`3288671.5`.

No cleanup is currently safe for the corrected-Q launch context. In particular,
do not cancel `3288671`, do not kill any still-existing `srun --jobid=3288671`
launcher from a host-side shell, and do not clean up the active interactive
allocation on `c318-008` merely because the heavy compute is on `c318-017`.

## `squeue -u $USER`

```text
JOBID    PARTITION          NAME            ST TIME       NODES NODELIST
3282992  NuclearEnergy      salt1_nom_cont  R  4-20:57:33 1     c318-016
3288671  NuclearEnergy      saltq_sel_cont  R  2-21:59:52 1     c318-017
3292998  NuclearEnergy-dev  idv01713        R  0:08:09    1     c318-008
```

The live interactive allocation visible at this heartbeat is `3292998`
(`idv01713`) on `c318-008`. This differs from the older July 10 handoff note,
which named interactive allocation `3285548`. Treat the older allocation ID as
stale unless separately confirmed by accounting.

## `sacct` Detail

Salt1 nominal:

```text
3282992        salt1_nom_cont  RUNNING  0:0  4-20:57:33  256  c318-016
3282992.batch  batch           RUNNING  0:0  4-20:57:33  256  c318-016
3282992.0      foamRun         RUNNING  0:0  4-20:49:57   64  c318-016
```

Selected corrected-Q:

```text
3288671        saltq_sel_cont  RUNNING  0:0  2-21:59:52  256  c318-017
3288671.batch  batch           RUNNING  0:0  2-21:59:52  256  c318-017
3288671.0      foamRun         RUNNING  0:0  2-21:59:36   64  c318-017
3288671.1      foamRun         RUNNING  0:0  2-21:59:36   64  c318-017
3288671.2      foamRun         FAILED   1:0  00:02:33     64  c318-017
3288671.3      foamRun         FAILED   1:0  00:00:13     64  c318-017
3288671.4      foamRun         FAILED   1:0  00:02:02     64  c318-017
3288671.5      foamRun         RUNNING  0:0  2-16:42:27   64  c318-017
```

`squeue -s -j 3288671` confirms live steps `.0`, `.1`, `.5`, and the batch step.

## Log-Tail Evidence

Salt1 nominal `3282992.0` is actively advancing:

- log: `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/logs/log.foamRun_salt1_nominal_continuation`
- latest tail time observed: `7863.0375 s`
- latest written decomposed directory observed by `ls -lt processors64`: `7863`
- current label remains pending terminal admission evidence, not admitted

Corrected-Q Salt1 -10Q `3288671.0` is actively advancing:

- log: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q`
- latest tail time observed: `8002.1363636363703 s`
- `processors64` modified at snapshot time

Corrected-Q Salt1 +10Q `3288671.1` is actively advancing:

- log: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q`
- latest tail time observed: `5538.5481927711007 s`
- `processors64` modified at snapshot time

Corrected-Q Salt4 +10Q repaired attach `3288671.5` is actively advancing:

- log: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_salt4_hi10q_weekend_attach`
- latest tail time observed: `11540.098131 s`
- this is beyond the prior repaired-launch check at about `11537.723 s`
- `processors64` modified at snapshot time

## Tmux / Attach Audit

`tmux ls` from this Codex session on `c318-008` showed only:

```text
work: 3 windows (created Mon Jul 13 10:11:15 2026) [341x37] (attached)
```

The earlier July 10 `salt4_attach_3288671` tmux session is not visible from
this session's `tmux ls`. This does not make cleanup safe: Slurm still reports
attached step `3288671.5` as `RUNNING`, and the Salt4 attach log is advancing.

Interpretation:

- The July 10 handoff's specific tmux/allocation names are partly stale.
- The live Slurm step is authoritative for the cleanup decision.
- A host-side process/session audit should be repeated before terminating any
  interactive allocation, tmux session, or `srun --jobid=3288671` launcher.

## Safe / Unsafe Cleanup Call

Safe now:

- Detach from the visible `work` tmux session if needed.
- Run read-only `squeue`, `sacct`, `squeue -s`, and log-tail checks.
- Prepare follow-on post-exit gate tasks without launching them.

Unsafe now:

- Do not `scancel 3282992` or `3288671`.
- Do not cancel the current `c318-008` interactive allocation `3292998` as a
  cleanup action while `3288671.5` is live.
- Do not kill any host-side `srun --jobid=3288671` launcher if one is found.
- Do not delete or move live run logs, `processors64`, `postProcessing`, or
  staged case directories.
- Do not admit Salt1 nominal or corrected-Q rows into closure fits before
  terminal gate evidence.

Trigger for revisiting cleanup:

1. `sacct -j 3288671` shows `3288671.5` terminal.
2. `squeue -s -j 3288671` no longer lists `.5`.
3. A fresh host-side `tmux ls` / process audit finds no dependent launcher that
   still needs the interactive allocation.
4. A new coordinator writes the terminal-state cleanup/admission handoff.

## Next Commands

```bash
squeue -u "$USER"
sacct -j 3282992 --format=JobID,JobName%32,State,ExitCode,Elapsed,AllocCPUS,NTasks,NNodes,NodeList%20
sacct -j 3288671 --format=JobID,JobName%32,State,ExitCode,Elapsed,AllocCPUS,NTasks,NNodes,NodeList%20
squeue -s -j 3288671
tmux ls
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_salt4_hi10q_weekend_attach
```

## Boundaries

This heartbeat performed read-only scheduler/session/log checks only. No jobs
were submitted, canceled, attached, detached, or cleaned up, and no native
solver outputs were mutated.
