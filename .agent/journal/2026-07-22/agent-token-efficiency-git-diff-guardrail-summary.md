---
provenance:
  - tools/git/diff_summary.py
  - tools/agent/guardrail_summary.py
tags: [journal, agent-tooling, token-efficiency]
related:
  - .agent/status/2026-07-22_TODO-AGENT-TOKEN-EFFICIENCY-GIT-DIFF-GUARDRAIL-SUMMARY-2026-07-22.md
  - imports/2026-07-22_agent_token_efficiency_git_diff_guardrail_summary.json
task: TODO-AGENT-TOKEN-EFFICIENCY-GIT-DIFF-GUARDRAIL-SUMMARY-2026-07-22
date: 2026-07-22
role: Coordinator / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Agent Token Efficiency Git Diff / Guardrail Summary

## Attempted

Checked which token-efficiency helpers already existed. The previous tooling
wave had already added board slicing, task context, package briefs, CSV preview,
manifest checks, safe ripgrep, status scoping, board archive support, and staged
diff-check filtering. The remaining practical gaps were path-scoped diff
summaries for ordinary unstaged/staged review and quiet summaries for verbose
guardrail/lint commands.

## Observed

Raw `git diff` and broad `git status` can still be expensive in this worktree
because many unrelated generated/tooling files are dirty or untracked. Validation
commands such as thesis guardrail scripts can also print long claim-boundary
review lists even when they pass.

## Implemented

Added `tools/git/diff_summary.py` and `tools/agent/guardrail_summary.py`, then
documented both in agent references and global instructions. `diff_summary.py`
also reports bounded untracked examples so newly created files do not disappear
from the summary.

## Inferred

Future agents should now be able to answer "what changed?" and "did the
guardrail pass?" without printing giant diffs or full validator logs. Raw hunks
and full guardrail output remain available for exact failures or final review,
but they should no longer be the default first command.

## Caveats

The worktree already had unrelated board/archive and tool changes. This task did
not revert them and only used the new scoped summaries to make the concurrency
visible.

## Next Useful Actions

If token use remains high, the next improvement should be a hard wrapper around
terminal commands that truncates output by default and writes full logs to a file
for later inspection. That should be a separate board row because it affects
agent execution conventions more broadly.
