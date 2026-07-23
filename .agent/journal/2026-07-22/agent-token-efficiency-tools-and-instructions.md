---
provenance:
  - AGENTS.md
  - .agent/BOARD.md
  - tools/agent/README.md
  - tools/agent/test_agent_tools.py
tags: [agent-operations, token-efficiency, tooling]
related:
  - .agent/status/2026-07-22_TODO-AGENT-TOKEN-EFFICIENCY-TOOLS-AND-INSTRUCTIONS-2026-07-22.md
task: TODO-AGENT-TOKEN-EFFICIENCY-TOOLS-AND-INSTRUCTIONS-2026-07-22
date: 2026-07-22
role: Coordinator/Implementer/Tester/Writer/Reviewer
type: journal
status: complete
---
# Agent Token Efficiency Tools And Instructions

Task: TODO-AGENT-TOKEN-EFFICIENCY-TOOLS-AND-INSTRUCTIONS-2026-07-22

## Attempted

- Claimed a scoped board row for agent token-efficiency tools and instruction
  updates.
- Added bounded-output helpers for board slices, task context, package briefs,
  state briefs, and closeout stubs.
- Extended the existing agent tool tests and updated root/agent/tooling
  documentation to prefer these helpers over broad board, state, CSV, or
  package dumps.

## Observed

- A simple `head -10 .agent/BOARD.md` still produced thousands of tokens
  because active rows contain long scope and guardrail text.
- The first `state_brief.py --active --blockers` implementation was still too
  verbose because it included generated blocker notes; the script was corrected
  to use the open-blocker table by default.
- The generated `.agent/STATE.md` was stale during validation and reported zero
  active board tasks, while the live board had active rows.
- Tests passed after the blocker-table tightening.

## Inferred

- Most avoidable token use comes from broad coordination/evidence reads: long
  board rows, generated state/blocker notes, full CSV/JSON dumps, recursive
  package listing, and unscoped task startup.
- Exact-row and package-summary commands can materially reduce churn while
  preserving scientific rigor because they show counts, headers, provenance,
  and guardrails first, then let agents open only the files that matter.

## Caveats

- The helpers are text parsers and summaries, not permission systems. Board
  ownership and AGENTS.md still define authority.
- Live board concurrency can still invalidate a patch context. Agents should
  re-run `board_slice.py --task-id <TASK>` before patching a frequently edited
  coordination file.
- `package_brief.py` samples CSV rows for orientation only; detailed scientific
  review still requires opening specific evidence rows when the brief indicates
  they are relevant.

## Next Actions

- Prefer the new startup sequence for known tasks:
  `board_slice.py --task-id`, `task_context.py --task-id`, then
  `state_brief.py --active --blockers`.
- Use `package_brief.py` before broad reads of `work_products/`, `reports/`,
  or package CSV/JSON trees.
- Use `closeout_stub.py` in dry-run mode when preparing standard status,
  journal, and import-manifest paths.

## Validation Notes

- `python3.11 -m py_compile tools/agent/board_slice.py tools/agent/task_context.py tools/agent/package_brief.py tools/agent/closeout_stub.py tools/docs/state_brief.py`: pass.
- `python3.11 -m pytest tools/agent/test_agent_tools.py`: `22 passed`.
- Live helper smoke checks passed for this board row, generated state/blockers,
  a recent S13 work-product package, and closeout-stub dry-run paths.
