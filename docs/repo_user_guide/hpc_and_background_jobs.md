---
provenance:
  - AGENTS.md
  - .agent/README.md
  - tools/agent/background_compute_helper.py
tags: [repo-user-guide, hpc, background-compute, slurm]
related:
  - docs/repo_user_guide/agent_workflow.md
  - operational_notes/maps/agent-operations.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# HPC and Background Jobs

The safest default is read-only local inspection. Scheduler actions require
explicit board scope.

## Which Tool to Use

| Need | Tool |
| --- | --- |
| Durable long or overnight work | `sbatch` from a login node |
| Compute work inside an allocation | `srun` |
| Keep an interactive launcher/session alive | `tmux` |
| Monitor scheduler state | `squeue`, `sacct`, package logs |

`tmux` does not allocate resources. If it owns an `srun --jobid=...` launcher,
killing the session or allocation may kill the step.

## Login Node Rule

Do not run expensive OpenFOAM solvers, rendering, full-case extraction, or
convergence-driven loops on login nodes. Prepare scripts and submit them through
Slurm when the board row allows scheduler action.

Use this helper before launch planning:

```bash
python3.11 tools/agent/background_compute_helper.py --duration long --openfoam --persistent
```

## Principal and Monitor Pattern

For long-running work:

- The principal row owns the scientific task, writes the launch package, submits
  the job, and documents the command and expected outputs.
- A monitor row owns read-only checks of `squeue`, `sacct`, logs, process state,
  and expected output files.
- The monitor must not submit duplicates, cancel, requeue, harvest, admit, fit,
  or score unless the row explicitly allows it.

## Required Handoff Fields

Every background handoff should name:

- task ID;
- Slurm job/step ID or tmux session name;
- node and allocation context;
- exact command;
- stdout, stderr, and package log paths;
- expected runtime and heartbeat interval;
- completion criteria and terminal states that matter;
- safe kill/cancel/requeue rules;
- downstream row to claim after terminal completion.

## Safe Scheduler Discovery

Read-only:

```bash
squeue -u "$USER"
sacct -j <jobid> --format=JobID,JobName%40,State,ExitCode,Elapsed,NodeList%30
```

Mutating:

```bash
sbatch <script.sbatch>
scancel <jobid>
```

Only run mutating scheduler commands when the board row explicitly grants that
action.
