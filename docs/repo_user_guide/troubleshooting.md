---
provenance:
  - AGENTS.md
  - .agent/README.md
  - tools/agent/README.md
  - .agent/BLOCKERS.md
tags: [repo-user-guide, troubleshooting, guardrails]
related:
  - docs/repo_user_guide/quickstart.md
  - docs/repo_user_guide/hpc_and_background_jobs.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Troubleshooting

## `preflight_task.py` Reports a Conflict

Stop and inspect the active row that owns the overlapping path. Do not edit
around it. Either choose a different row or wait for closeout.

## `finish_task.py` Fails

Common causes:

- board row does not say complete or blocked;
- status file is missing;
- journal entry is missing;
- import manifest is missing;
- manifest lacks `changed_files`, `read_only_context`, or mutation flags;
- a listed changed file does not exist;
- generated blocker index check fails.

Fix the durable docs and rerun:

```bash
python3.11 tools/agent/finish_task.py --task-id <TASK_ID> --json
```

## `pytest` Is Not Installed

Use unittest for repo-local lightweight checks:

```bash
python3.11 -m unittest discover tools/agent
python3.11 -m unittest tools.docs.test_repo_tool_inventory
```

## A Source Case Path Is Missing

Do not invent a replacement path or use `linked_cases/` as provenance. Check
the registry and manifests:

```bash
rg -n "<source_id>|<case_name>" registry imports operational_notes work_products
```

If the source originates elsewhere, require local staging before analysis.

## A Solver/Postprocessing Command Looks Quick

Treat it as heavy until proven otherwise. Use `background_compute_helper.py`,
read the local instructions, and submit through Slurm only when a board row
allows it.

## A Predictive Result Looks Good

Do not promote it unless source/property labels, runtime-input audits,
split-role permissions, UQ/mesh/time gates, and candidate-freeze rules pass.
Validation, holdout, and external rows cannot be used for fitting or model
selection.

## Current State Disagrees With an Old Note

Trust generated state first:

```bash
sed -n '1,220p' .agent/STATE.md
sed -n '1,220p' .agent/BLOCKERS.md
```

Then follow the topic map for that research thread.

## Need to Clean Scratch Files

Claim a Cleaner row first. Do a dry-run inventory. Classify candidates as safe
generated artifact, duplicate output, misplaced file, stale but potentially
useful, or unknown/do not touch. Ask before deletion or irreversible cleanup.
