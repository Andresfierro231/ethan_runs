---
provenance:
  - .agent/status/2026-07-15_AGENT-412.md
  - work_products/2026-07/2026-07-15/2026-07-15_hydraulic_duplicate_slurm_tail_cancel/README.md
tags: [journal, scheduler, hydraulics, cleanup]
related:
  - .agent/status/2026-07-15_AGENT-405.md
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run/README.md
task: AGENT-412
date: 2026-07-15
role: Coordinator/Hydraulics/Scheduler/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Hydraulic Duplicate Slurm Tail Cancel

The user asked whether pending hydraulic jobs could be removed from the dependency Slurm queue because the safe stages had already been run.

I confirmed:

- `3295989`, `3295990`, and `3295991` were still pending with reason `Dependency`.
- `sacct` showed elapsed `00:00:00` and no assigned node for all three.
- AGENT-405 had already run the safe local equivalents on `c318-008`.

I cancelled only those three jobs with `scancel 3295989 3295990 3295991`.

Afterward:

- `squeue -j 3295989,3295990,3295991` returned no job rows.
- `sacct` reports all three as `CANCELLED by 890970`.

No solver outputs were changed and no new jobs were submitted.
