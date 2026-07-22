---
provenance:
  - README.md
  - tools/agent/README.md
  - tools/docs/build_repo_tool_inventory.py
tags: [repo-user-guide, workflows, tooling]
related:
  - docs/repo_user_guide/quickstart.md
  - docs/repo_user_guide/tool_index.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Common Tasks

These workflows are templates. Always follow the active board row and local
instructions over generic examples.

## Inspect the Board

```bash
python3.11 tools/agent/board_dashboard.py --limit 20
rg -n "TODO-.*open|active|trigger-gated" .agent/BOARD.md
```

Use this to find open work and active conflicts. Do not claim trigger-gated rows
until the trigger exists.

## Claim a Task

1. Read the row and confirm allowed edit paths.
2. Update only that row in `.agent/BOARD.md`.
3. Run:

```bash
python3.11 tools/agent/preflight_task.py --task-id <TASK_ID>
```

## Finish a Task

```bash
python3.11 tools/agent/finish_task.py --task-id <TASK_ID>
```

If it fails, fix the missing status, journal, manifest, mutation flags, or index
check before marking complete.

## Locate Latest Reports

```bash
find work_products/2026-07 -maxdepth 3 -name README.md | sort | tail -40
find reports/2026-07 -maxdepth 3 -name README.md | sort | tail -40
```

For topic-based lookup, start with:

```bash
sed -n '1,220p' operational_notes/maps/README.md
```

## Find Case Provenance

```bash
head -20 registry/case_registry.csv
rg -n "\"changed_files\"|\"read_only_context\"|native_solver_outputs_mutated" imports
```

Use manifests and registry rows, not symlink paths, for provenance.

## Validate Docs and Tooling

```bash
python3.11 tools/docs/build_repo_tool_inventory.py
python3.11 -m unittest tools.docs.test_repo_tool_inventory
python3.11 tools/docs/build_repo_index.py --check
python3.11 -m pytest tools/agent
```

## Run Lightweight Tests

Most package builders have paired tests:

```bash
python3.11 -m unittest tools.analyze.test_<name>
python3.11 -m unittest tools.extract.test_<name>
```

Prefer targeted tests over broad test discovery when the repo has many
long-lived analysis scripts.

## Prepare Heavy CFD Work Without Launching It

1. Claim a scheduler-capable row.
2. Read local instructions under `jadyn_runs/`, `staging/`, or `tools/`.
3. Build a task-scoped script or sbatch file.
4. Run shell syntax checks where possible:

```bash
bash -n <script.sh>
```

5. Write a `RUNNING.md` or package README section with handoff fields.
6. Submit only after the row allows it:

```bash
sbatch <script.sbatch>
```

## Refresh the Tool Inventory

```bash
python3.11 tools/docs/build_repo_tool_inventory.py
```

This updates:

- `docs/repo_user_guide/tool_inventory.csv`;
- `docs/repo_user_guide/tool_index.md`.
