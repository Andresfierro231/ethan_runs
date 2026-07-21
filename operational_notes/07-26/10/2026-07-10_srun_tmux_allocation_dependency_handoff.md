# 2026-07-10 `srun` / `tmux` Allocation Dependency Handoff

## Short Answer

Yes: Slurm owns the corrected-Q allocation on `c318-017`, but the attached
Salt4 `srun` launcher depends on the current interactive node/session on
`c318-008`.

## Current Jobs

- `3285548` / `idv43192`: interactive allocation on `c318-008`.
- `3288671` / `saltq_sel_cont`: corrected-Q allocation on `c318-017`.
- `3288671.0`, `.1`, and `.5`: running `foamRun` steps on `c318-017` at the
  time of this note.
- `salt4_attach_3288671`: tmux session on the interactive node.

## What This Means

The OpenFOAM compute work runs under Slurm on `c318-017`. However, the repaired
Salt4 attached step was launched from `c318-008` with an `srun --jobid=3288671`
command. That launcher is associated with the `salt4_attach_3288671` tmux
session.

So:

- Detaching from tmux is OK.
- Closing a local terminal is OK if tmux and the interactive allocation remain
  alive.
- Canceling `3285548`, killing the tmux session, or killing the `srun` launcher
  can crash the attached Salt4 step.
- Canceling `3288671` kills the Slurm-owned corrected-Q job itself.

## Do Not Do Until `3288671.5` Is Terminal

- Do not `scancel 3285548`.
- Do not kill `salt4_attach_3288671`.
- Do not kill any `srun --jobid=3288671` launcher.
- Do not clean up the interactive allocation just because the heavy compute is
  on `c318-017`.

## Check Before Cleanup

```bash
sacct -j 3288671 --format=JobID,JobName%32,State,ExitCode,Elapsed,NodeList%20 -P
tmux ls
```

Only after the attached step is terminal should a fresh coordinator decide
whether the tmux session and interactive allocation can be cleaned up.
