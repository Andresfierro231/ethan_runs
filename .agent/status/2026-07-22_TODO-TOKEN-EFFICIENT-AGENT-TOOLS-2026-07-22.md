---
provenance:
  - tools/agent/README.md
  - operational_notes/START_HERE_FOR_AGENTS.md
  - AGENTS.md
  - CLAUDE.md
tags: [status, agent-operations, token-budget, tooling]
related:
  - .agent/journal/2026-07-22/token-efficient-agent-tools.md
  - imports/2026-07-22_token_efficient_agent_tools.json
task: TODO-TOKEN-EFFICIENT-AGENT-TOOLS-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TOKEN-EFFICIENT-AGENT-TOOLS-2026-07-22

## Objective

Add repo-local scripts and instructions that reduce token waste from broad
board reads, repo-wide searches, full dirty-worktree status, full CSV dumps, and
full JSON manifest pretty-printing.

## Outcome

Added bounded inspection helpers under `tools/agent/` and updated the standard
agent instructions so future agents know to use them.

## Changes Made

- Added `tools/agent/safe_rg.py`.
- Added `tools/agent/status_scope.py`.
- Added `tools/agent/preview_csv.py`.
- Added `tools/agent/manifest_check.py`.
- Added `tools/agent/link_report.py`.
- Extended `tools/agent/board_summary.py` with task, owner, status, section, and
  Active-section filters.
- Updated `tools/agent/test_agent_tools.py`.
- Updated `tools/agent/README.md`.
- Updated `AGENTS.md`, `operational_notes/START_HERE_FOR_AGENTS.md`, and
  `operational_notes/maps/agent-operations.md`.
- Updated `CLAUDE.md` so Claude-based agents see the same low-output helper
  workflow during bootstrap.

## Validation

- `python3.11 -m py_compile tools/agent/safe_rg.py tools/agent/status_scope.py tools/agent/preview_csv.py tools/agent/manifest_check.py tools/agent/link_report.py tools/agent/board_summary.py`
- `python3.11 tools/agent/safe_rg.py AGENTS AGENTS.md --max-lines 5`
- `python3.11 tools/agent/safe_rg.py AGENTS .` returned the expected broad-search refusal.
- `python3.11 tools/agent/status_scope.py tools/agent/safe_rg.py tools/agent/status_scope.py`
- `python3.11 tools/agent/preview_csv.py /tmp/token_tools_preview.csv --cols id,status --rows 1`
- `python3.11 tools/agent/manifest_check.py imports/2026-07-22_token_efficient_agent_tools.json --check-paths`
- `python3.11 -m pytest tools/agent/test_agent_tools.py`
- `python3.11 tools/docs/build_repo_index.py --check`
- `git diff --check -- <task paths>`
- `python3.11 tools/agent/status_scope.py <task paths>`

## Unresolved Blockers

No blocker was opened. `link_report.py` is intentionally simple and should be
reviewed after use; it gives a default link insertion rather than perfect
topic-specific prose.

## Guardrails

No native CFD/OpenFOAM outputs, registry rows, scheduler state, model
coefficients, source evidence, external repos, or thesis LaTeX were mutated.
Generated index files were not regenerated.
