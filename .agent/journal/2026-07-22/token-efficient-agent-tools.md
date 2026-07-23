---
provenance:
  - tools/agent/README.md
  - operational_notes/START_HERE_FOR_AGENTS.md
  - AGENTS.md
  - CLAUDE.md
tags: [journal, agent-operations, token-budget, tooling]
related:
  - .agent/status/2026-07-22_TODO-TOKEN-EFFICIENT-AGENT-TOOLS-2026-07-22.md
  - imports/2026-07-22_token_efficient_agent_tools.json
task: TODO-TOKEN-EFFICIENT-AGENT-TOOLS-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Token-Efficient Agent Tools

## What Was Attempted

Added helper scripts and instructions to prevent repeated high-token inspection
patterns: broad `rg`, full `.agent/BOARD.md` reads, full dirty `git status`,
full CSV dumps, and full JSON manifest pretty-printing.

## Observed

The repo already had board summary/dashboard and source-property tooling, so the
change extended `board_summary.py` instead of adding a duplicate board
summarizer. The new tools are small stdlib-only wrappers intended for agent
coordination, not scientific data reduction.

## Inferred

Most future token savings should come from changing default behavior in the
startup instructions. The scripts help only if agents see them early, so the
root `AGENTS.md`, `CLAUDE.md`, start-here note, agent operations map, and tools
README were updated.

## Caveats

`link_report.py` inserts generic discoverability text. Agents should still
review and improve the wording when a report needs a more precise handoff.

## Next Useful Actions

Use the new helpers in future work and add package-specific wrappers only when a
recurring workflow still produces noisy output after these defaults.
