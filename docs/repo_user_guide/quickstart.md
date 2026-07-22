---
provenance:
  - README.md
  - AGENTS.md
  - operational_notes/START_HERE_FOR_AGENTS.md
  - .agent/README.md
tags: [repo-user-guide, quickstart, start-here]
related:
  - docs/repo_user_guide/repo_organization.md
  - docs/repo_user_guide/agent_workflow.md
  - docs/repo_user_guide/tool_index.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Quickstart

This page is the safe first path through `ethan_runs/`. It favors read-only
commands until you have a board row and know which files are allowed.

## 1. Confirm Where You Are

```bash
pwd
rg --files | head -80
```

If you are not in the repo root, move there before running repo tools.

## 2. Read the Operating Contract

```bash
sed -n '1,220p' AGENTS.md
sed -n '1,220p' .agent/README.md
sed -n '1,220p' operational_notes/START_HERE_FOR_AGENTS.md
```

The short version:

- claim a board row before editing;
- touch only paths allowed by that row;
- do not mutate native solver outputs;
- do not run heavy work on login nodes;
- close with status, journal, import manifest, and `finish_task.py`.

## 3. Inspect Live Work

```bash
python3.11 tools/agent/board_dashboard.py --limit 20
sed -n '1,220p' .agent/STATE.md
sed -n '1,220p' .agent/BLOCKERS.md
```

`STATE.md` and `BLOCKERS.md` are generated. Trust them over older prose if they
disagree.

## 4. Check the Tooling

```bash
python3.11 -m pytest tools/agent
python3.11 -m unittest tools.docs.test_repo_tool_inventory
python3.11 tools/docs/build_repo_tool_inventory.py
python3.11 tools/docs/build_repo_index.py --check
```

If `pytest` is not installed:

```bash
python3.11 -m unittest discover tools/agent
```

These commands are meant to be lightweight. Do not substitute a solver,
postprocessing, or Slurm launch command unless a board row says so.

## 5. Before Editing

Find or claim a board row. Then run:

```bash
python3.11 tools/agent/preflight_task.py --task-id <TASK_ID>
```

Stop if it reports path overlap with another active row.

## 6. Before Finishing

Write the required durable context:

- `.agent/status/<date>_<TASK_ID>.md`
- `.agent/journal/<date>/<slug>.md`
- `imports/<date>_<slug>.json`
- a package README or operational note for durable outputs

Then run:

```bash
python3.11 tools/agent/finish_task.py --task-id <TASK_ID>
```

Do not mark the row complete until another agent can continue from files alone.

## Safe Beginner Commands

Read-only:

```bash
rg -n "TODO-" .agent/BOARD.md
rg --files work_products | head -80
find work_products/2026-07/2026-07-22 -maxdepth 2 -name README.md
sed -n '1,180p' reference/geometry_reference.md
python3.11 tools/agent/background_compute_helper.py --duration long --openfoam --persistent
```

Mutating or heavy, only under explicit task scope:

```bash
sbatch <script.sbatch>
srun -N1 <command>
python3.11 tools/intake/register_case.py --source-path <case-dir>
python3.11 tools/extract/render_field_figures.py --source-id <source-id> --backend auto
python3.11 tools/run_registered_pipeline.py --source-id <source-id>
```
