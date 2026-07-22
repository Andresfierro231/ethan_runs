---
provenance:
  - tools/AGENTS.override.md
  - tools/agent/README.md
  - docs/repo_user_guide/tool_index.md
tags: [tooling, repo-user-guide, start-here]
related:
  - docs/repo_user_guide/tool_index.md
  - docs/repo_user_guide/common_tasks.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Tools

`tools/` contains reusable helpers for coordination, intake, extraction,
analysis, publishing, OpenFOAM launch wrappers, and documentation generation.

Read `tools/AGENTS.override.md` before editing this subtree. Many helpers are
package-specific and should not be run as generic maintenance commands.

## Main Subtrees

| Path | Use |
| --- | --- |
| `tools/agent/` | Board preflight, closeout validation, lints, dashboard, background-compute helper. |
| `tools/analyze/` | Analysis and work-product builders, usually paired with tests and package READMEs. |
| `tools/extract/` | CFD sampling, OpenFOAM/VTK parsing, rendering, and staged extraction helpers. |
| `tools/intake/` | Case registration and import manifest helpers. |
| `tools/publish/` | Publication, backup, transfer, and laptop download helpers. |
| `tools/docs/` | Repo index and repo-user-guide inventory generation. |
| `tools/ofenv/` | OpenFOAM environment setup snippets. |

## Generated Inventory

Regenerate the complete table of helpers with:

```bash
python3.11 tools/docs/build_repo_tool_inventory.py
```

Outputs:

- `docs/repo_user_guide/tool_inventory.csv`
- `docs/repo_user_guide/tool_index.md`

## Safe Defaults

Prefer `--help`, targeted tests, and read-only lints before running a builder:

```bash
python3.11 tools/agent/board_dashboard.py --limit 20
python3.11 tools/agent/preflight_task.py --task-id <TASK_ID>
python3.11 -m unittest tools.docs.test_repo_tool_inventory
```

Do not run solver, renderer, full extraction, scheduler, publish, upload, or
registry-mutating helpers unless your board row explicitly allows it.
