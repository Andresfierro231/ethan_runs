---
provenance:
  - README.md
  - docs/repo_user_guide/README.md
  - docs/repo_user_guide/tool_index.md
  - tools/docs/build_repo_tool_inventory.py
tags: [journal, repo-user-guide, documentation, tooling]
related:
  - .agent/status/2026-07-22_TODO-REPO-USER-GUIDE-README-TOOLING.md
  - imports/2026-07-22_repo_user_guide_readme_tooling.json
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer / Reviewer / Implementer / Tester / Coordinator
type: journal
status: complete
---
# Repo user guide README/tooling

## Attempted

Claimed the open repo-user-guide row because active scientific rows and
scheduler-gated harvest rows were not safe to advance. Read the startup
protocol, board, ownership rules, roles, start-here note, agent tooling README,
generated state/blocker docs, topic maps, geometry reference, and representative
manifest/status patterns.

Built a user-facing documentation package and a reproducible tool inventory
instead of hand-listing the large `tools/` tree.

## Observed

The repo already had strong internal agent instructions, but the root README was
too short for a new external user. The tool tree is large and changes often, so
the only durable way to inventory every helper is generated CSV/Markdown.

Current live scheduler and board state also showed several active scientific
rows, so this documentation row avoided scheduler, native-output, registry,
Fluid, and generated-index mutation.

## Inferred

This row improves operational throughput: new users can now start with the root
README and `docs/repo_user_guide/`, while agents can use the same guide to find
board workflow, provenance, HPC, and closeout rules without relying on chat
history.

The generated tool inventory should reduce stale documentation risk because
helpers are discovered directly from `tools/`.

## Caveats

The inventory purpose field comes from docstrings, leading comments, or file
names, so it is a practical index, not a scientific review of each helper. It
intentionally warns users to inspect source and board scope before running
mutating or HPC-capable tools.

The full worktree remains dirty from unrelated concurrent work and generated
index changes. This row validated only its owned paths for whitespace.

## Next Useful Actions

Keep the guide current when workflows change. In particular, rerun
`python3.11 tools/docs/build_repo_tool_inventory.py` after adding or renaming
tools, and update `docs/repo_user_guide/hpc_and_background_jobs.md` if scheduler
or monitor-agent policy changes.
