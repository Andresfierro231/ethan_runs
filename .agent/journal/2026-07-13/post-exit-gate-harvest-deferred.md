# Post-Exit Gate Harvest Deferred

Task: `AGENT-266`
Role: Coordinator / Reviewer / Writer

## Context

The requested AGENT-266 work is explicitly conditional: harvest terminal gate
evidence for Salt1 nominal `3282992` and corrected-Q `3288671` only after Slurm
says the jobs are terminal.

## Scheduler Check

Fresh read-only Slurm checks on 2026-07-13 showed both carry-over jobs are still
running:

```text
3282992|salt1_nom_cont|RUNNING|NuclearEnergy|4-21:01:37|5-00:00:00|1|c318-016
3288671|saltq_sel_cont|RUNNING|NuclearEnergy|2-22:03:56|5-00:00:00|1|c318-017
```

Accounting detail also showed:

- `3282992`, `3282992.batch`, and `3282992.0` are `RUNNING`;
- `3288671`, `3288671.batch`, `3288671.0`, `3288671.1`, and repaired attached
  step `3288671.5` are `RUNNING`;
- older corrected-Q failed steps `.2`, `.3`, and `.4` remain failed history,
  not terminal evidence for the whole job.

## Decision

The post-exit harvest was not launched. Salt1 nominal and selected corrected-Q
rows remain excluded from admission or interpretation until a future check shows
terminal top-level jobs and terminal relevant steps.

## Boundaries

This task performed scheduler/accounting checks only. No live job was canceled,
no terminal gate was harvested, no outputs were interpreted, and no solver
outputs were mutated.
