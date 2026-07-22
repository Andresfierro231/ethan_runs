---
provenance:
  - AGENTS.md
  - .agent/README.md
  - .agent/FILE_OWNERSHIP.md
  - .agent/ROLES.md
  - tools/agent/README.md
tags: [repo-user-guide, agent-operations, board-workflow]
related:
  - docs/repo_user_guide/quickstart.md
  - docs/repo_user_guide/hpc_and_background_jobs.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Agent Workflow

Agents and humans share one board and one documentation corpus. A task is not
done just because code ran; it is done when the next person can continue from
durable files.

## Roles

- Coordinator: assigns non-overlapping work and updates shared board state.
- Implementer: edits focused code or package files.
- Tester: validates behavior and records exact commands.
- Reviewer: checks risks, conflicts, missing tests, and stale assumptions.
- Writer: writes evidence-backed docs and reports.
- Cleaner: inventories and safely removes or archives stale artifacts.

## Claiming a Task

1. Read `AGENTS.md`, `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`,
   `.agent/ROLES.md`, and relevant local instructions.
2. Choose an open row whose gates are satisfied.
3. Update only that row in `.agent/BOARD.md` to show active ownership and dated
   artifact paths.
4. Run:

```bash
python3.11 tools/agent/preflight_task.py --task-id <TASK_ID>
```

If the row overlaps another active row, stop.

## Editing Rules

- Touch only paths named by your row.
- Treat all other paths as read-only context.
- Do not mutate native CFD outputs.
- Do not mutate registry, scheduler, generated indexes, Fluid/external repos,
  thesis body, or blocker source unless explicitly scoped.
- Keep changes reviewable and task-scoped.

## Closeout Contract

Before marking a row complete or blocked, write:

- `.agent/status/<date>_<TASK_ID>.md`;
- `.agent/journal/<date>/<slug>.md`;
- `imports/<date>_<slug>.json`;
- a package README or operational note if the work produced durable context.

Then run:

```bash
python3.11 tools/agent/finish_task.py --task-id <TASK_ID>
```

The status file should include objective, outcome, changes made, validation,
guardrails, blockers, and next useful actions. The journal should separate what
was attempted, observed, inferred, caveats, and next actions.

## Board Hygiene

Completed rows should not remain in the active section unless they are awaiting
validated closeout. Gated rows should not be claimed until their trigger exists,
such as a terminal Slurm job, a single named candidate, or a released source
basis.

## Generated Index

`tools/docs/build_repo_index.py` writes `.agent/STATE.md`,
`.agent/BLOCKERS.md`, `.agent/catalog.json`, and `.agent/catalog.csv`. Run
`--check` freely. Rebuild only when your row owns generated index files or no
active row blocks regeneration.
