# `srun` / `tmux` Allocation Dependency Handoff

Date: `2026-07-10`
Task: `AGENT-258`
Role: Coordinator / Writer

## Prompt

The user asked whether the `srun` is on this node, whether closing the node
would crash it, and then asked to document the answer.

## Observed State

Commands checked:

```bash
squeue -j 3285548,3288671 -o '%i|%j|%T|%M|%l|%D|%R'
sacct -j 3288671 --format=JobID,JobName%32,State,ExitCode,Elapsed,Start,End,NodeList%20 -P
tmux ls
```

Observed:

- `3285548` / `idv43192`: interactive allocation, `RUNNING` on `c318-008`.
- `3288671` / `saltq_sel_cont`: corrected-Q allocation, `RUNNING` on
  `c318-017`.
- `3288671.0` and `3288671.1`: original selected corrected-Q `foamRun` steps,
  still `RUNNING`.
- `3288671.5`: attached repaired Salt4 `foamRun` step, `RUNNING`.
- `salt4_attach_3288671`: tmux session exists on the interactive node.

## Interpretation

Mental model:

- Slurm owns allocation/job `3288671` on `c318-017`.
- The OpenFOAM ranks for the corrected-Q steps run on `c318-017`.
- The attached Salt4 retry step was launched through an
  `srun --jobid=3288671 ...` command started from the interactive node
  `c318-008`.
- That launcher lives under the `salt4_attach_3288671` tmux session, so the
  launcher side depends on the interactive allocation/node remaining alive
  unless the step has already finished.

## Safe Actions

Safe / low-risk:

- Detach from tmux.
- Close a local terminal window if the remote tmux session remains alive.
- Leave `3285548`, `3288671`, and `salt4_attach_3288671` alone.

## Unsafe Actions

Potentially step-killing:

- `scancel 3285548`.
- Killing the `salt4_attach_3288671` tmux session.
- Killing the `srun --jobid=3288671` launcher process.
- Logging out or closing the environment in a way that kills user processes in
  the interactive allocation.
- `scancel 3288671`, which would cancel the corrected-Q allocation itself.

## Recommended Handoff

Before closing or cleaning up the interactive node, check:

```bash
sacct -j 3288671 --format=JobID,JobName%32,State,ExitCode,Elapsed,NodeList%20 -P
tmux ls
```

If `3288671.5` is still `RUNNING`, keep `3285548` and
`salt4_attach_3288671` alive. Once `3288671.5` reaches a terminal state, a
fresh agent can decide whether the tmux session is disposable after checking
logs.
