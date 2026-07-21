---
provenance:
  - AGENTS.md
  - .agent/README.md
  - operational_notes/START_HERE_FOR_AGENTS.md
  - operational_notes/maps/agent-operations.md
  - tools/agent/README.md
  - tools/agent/background_compute_helper.py
tags: [journal, background-compute, monitor-agent, tmux, srun, sbatch]
related:
  - .agent/status/2026-07-17_AGENT-528.md
  - imports/2026-07-17_background_terminal_monitor_agent_policy.json
task: AGENT-528
date: 2026-07-17
role: Coordinator/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Background Terminal Monitor-Agent Policy

Task: AGENT-528

## Context

The user wants to keep communicating with the main/principal agent while long
compute work runs in a background terminal and another agent observes
convergence. Existing docs distinguished `sbatch`, `srun`, and `tmux`, but did
not make the principal-agent plus monitor-agent operating model explicit enough.

## Changes Made

- Added the principal/monitor pattern to `AGENTS.md`.
- Added the same policy to `.agent/README.md`,
  `operational_notes/START_HERE_FOR_AGENTS.md`,
  `operational_notes/maps/agent-operations.md`, and `tools/agent/README.md`.
- Updated `tools/agent/background_compute_helper.py` output to list principal
  and monitor handoff fields, monitor prohibitions, and the user-availability
  rule.

## Job 3300966

Read-only Slurm/accounting result:

- Job: `3300966`
- Name: `ag511_hsrc`
- Node: `c318-009`
- State: `COMPLETED`
- Exit code: `0:0`
- Runtime: `00:36:50`
- Start: `2026-07-17T15:46:27`
- End: `2026-07-17T16:23:17`

The stdout log `logs/2026-07-17/heater_source_redistribution_coupled_score.out`
reports `27` completed coupled rows, selected Salt2 heater lambda `0`, and no
admitted candidates; the related blocker decision remains `keep_open` for
`predictive-wall-test-section-submodels`.

## Policy Summary

- Principal agent owns the science, launches the job, writes the running
  handoff, and remains available to the user.
- Monitor agent owns a separate read-only board row and periodically checks
  scheduler state, logs, process state, and expected outputs.
- `tmux` is useful for a background terminal but does not allocate resources; it
  should wrap or preserve `srun`/launcher state, not replace Slurm accounting.
- Monitor agents must not submit duplicates, cancel, requeue, harvest, admit, or
  fit unless the board row explicitly grants that authority.

## Validation

- `sacct -j 3300966 --format=JobID,JobName,Partition,Account,State,ExitCode,Elapsed,Start,End,NodeList%30`
- `tail -80 logs/2026-07-17/heater_source_redistribution_coupled_score.out`
- `python3.11 -m pytest tools/agent`
- `python3.11 -m py_compile tools/agent/background_compute_helper.py`
- `python3.11 tools/agent/background_compute_helper.py --duration long --openfoam --persistent --host-kind compute`
- `python3.11 tools/agent/finish_task.py --task-id AGENT-528 --json`

## Guardrails

- No native CFD outputs, registry state, admission state, scheduler state,
  external Fluid code, or generated index files were mutated.
- The `3300966` inspection was read-only; no cancellation, requeue, dependency
  mutation, harvest, or admission action was performed.
