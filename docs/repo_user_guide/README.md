---
provenance:
  - README.md
  - docs/repo_user_guide/quickstart.md
  - docs/repo_user_guide/tool_index.md
  - tools/docs/build_repo_tool_inventory.py
tags: [repo-user-guide, documentation, tooling]
related:
  - docs/repo_user_guide/repo_organization.md
  - docs/repo_user_guide/data_and_provenance.md
  - docs/repo_user_guide/agent_workflow.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Repo User Guide

This directory is the public-facing user guide for `ethan_runs/`. It explains
safe first steps, repository organization, provenance expectations, board
workflow, HPC/background-job rules, common tasks, troubleshooting, and glossary
terms.

## Contents

| File | Purpose |
| --- | --- |
| `quickstart.md` | Safe first-hour walkthrough and beginner commands. |
| `repo_organization.md` | Directory map and local-instruction rules. |
| `data_and_provenance.md` | Native outputs, manifests, registry, work products, and runtime-input discipline. |
| `agent_workflow.md` | Board claiming, editing, and closeout contract. |
| `hpc_and_background_jobs.md` | Slurm, `srun`, `tmux`, principal/monitor handoffs. |
| `common_tasks.md` | Concrete workflows for board inspection, task closeout, report lookup, and safe preparation. |
| `troubleshooting.md` | Common failure modes and safe checks. |
| `glossary.md` | Repo and research terminology. |
| `tool_index.md` | Generated Markdown inventory of every helper under `tools/`. |
| `tool_inventory.csv` | Machine-readable inventory generated from the same script. |

## Regeneration

Regenerate the tool inventory after adding, removing, or renaming helpers:

```bash
python3.11 tools/docs/build_repo_tool_inventory.py
```

Validate the inventory builder:

```bash
python3.11 -m unittest tools.docs.test_repo_tool_inventory
```

## Guardrails

This documentation did not mutate native CFD/OpenFOAM outputs, registry or
admission state, scheduler state, Fluid/external repositories, blocker source,
or generated repo index files.
