---
provenance:
  - AGENTS.md
  - .agent/README.md
  - operational_notes/START_HERE_FOR_AGENTS.md
  - tools/agent/
tags: [agent-operations, coordination, tooling, start-here]
related:
  - operational_notes/maps/README.md
  - .agent/DOC_FRONTMATTER_SCHEMA.md
task: AGENT-489
date: 2026-07-17
role: Coordinator/Writer
type: map
status: reference
---
# Agent Operations — Map of Content

Tags: #agent-operations #coordination #tooling #start-here

## What this covers

How agents and new users operate efficiently in `ethan_runs/`: startup,
board-task claiming, file ownership, background compute choices, handoff
requirements, and read-only lint tools.

## Current Status

AGENT-489 added the first consolidated agent/user efficiency platform:

- canonical start-here note: `operational_notes/START_HERE_FOR_AGENTS.md`
- background compute-agent policy in `AGENTS.md` and `.agent/README.md`
- `tools/agent/` preflight, finish, lint, dashboard, and compute-helper tools
- CFD-to-1D schema contract in `operational_notes/maps/cfd-runs-and-admission.md`

AGENT-554 added source/property scorecard gate tooling:

- `tools/agent/source_property_gate.py` audits scorecard-like CSVs for
  fit/admission rows with missing, blank, refresh-required, outside-envelope, or
  diagnostic/no-fit source/property labels.
- `finish_task.py` emits warning-mode `SOURCE_PROPERTY_GATE_WARNING` messages
  for changed scorecard-like CSVs unless a task manifest declares
  `no_scorecard_outputs: true`.
- Current follow-up ledger:
  `work_products/2026-07/2026-07-20/2026-07-20_source_property_gate_infrastructure/final_scorecard_source_property_todo.csv`

Generated index refresh was deferred during AGENT-489 because active AGENT-482
owned `.agent/STATE.md`, `.agent/BLOCKERS.md`, `.agent/catalog.json`, and
`.agent/catalog.csv`.

## Trusted Entry Points

- Startup and common commands: `operational_notes/START_HERE_FOR_AGENTS.md`
- Coordination rules: `AGENTS.md`
- Board and ownership: `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`
- Generated current state: `.agent/STATE.md`, `.agent/BLOCKERS.md`
- Topic maps: `operational_notes/maps/README.md`
- Agent tools: `tools/agent/`

## Tool Contracts

- `preflight_task.py`: read-only board scope and conflict check.
- `finish_task.py`: handoff validation and optional generated-index rebuild.
- `new_task.py`: dry-run or explicit-write task scaffolding.
- `split_policy_lint.py`: stale split-language guard.
- `runtime_input_lint.py`: predictive runtime-input leakage guard.
- `case_schema_lint.py`: CFD-to-1D schema coverage guard.
- `background_compute_helper.py`: `sbatch` / `srun` / `tmux` recommendation.
- `board_dashboard.py`: compact active/TODO board view.
- `source_property_gate.py`: source/property label and gate audit for
  scorecard-like fit/admission rows.

## Principal / Monitor Pattern

For long or convergence-driven runs, split responsibility instead of blocking
the main agent conversation:

- Principal agent:
  - owns the scientific task and board row;
  - prepares the command and package-local log paths;
  - launches with `sbatch`, `srun`, or `tmux+srun`;
  - writes a durable `RUNNING.md`, README section, or status note before moving
    on;
  - remains available to the user while the job runs.
- Monitor agent:
  - claims a separate narrow read-only board row;
  - periodically checks `squeue`, `sacct`, logs, process state, and expected
    output files;
  - reports progress, terminal state, and readiness for a later harvest or
    admission row;
  - does not submit duplicates, cancel, requeue, harvest, or admit unless the
    row explicitly grants that authority.

Required running-job handoff fields:

- principal task ID and monitor task ID;
- Slurm job ID, step ID, or tmux session name;
- node and allocation context;
- exact command;
- stdout/stderr/log paths;
- expected runtime and heartbeat interval;
- completion criteria and terminal states that matter;
- safe-kill/cancel/requeue rules;
- downstream package to claim after terminal completion.

## Guardrails

- Do not mutate native solver outputs.
- Do not edit active agents' paths.
- Do not refresh generated index files while another active row owns them.
- Do not run heavy work on login nodes.
- Do not promote diagnostic CFD evidence to predictive runtime input.
