---
provenance:
  - AGENTS.md
  - .agent/BOARD.md
  - .agent/BOARD_ARCHIVE.md
  - tools/agent/board_archive.py
  - tools/agent/board_summary.py
  - tools/git/
tags: [agent-operations, board-hygiene, git-hygiene, token-efficiency]
related:
  - .agent/status/2026-07-22_TODO-TOKEN-EFFICIENT-BOARD-ARCHIVE-AND-GIT-SUMMARY-TOOLS-2026-07-22.md
  - imports/2026-07-22_token_efficient_board_archive_and_git_summary_tools.json
task: TODO-TOKEN-EFFICIENT-BOARD-ARCHIVE-AND-GIT-SUMMARY-TOOLS-2026-07-22
date: 2026-07-22
role: Coordinator/Cleaner/Implementer/Tester/Writer
type: journal
status: complete
---
# Token-Efficient Board Archive And Git Summary Tools

Task: TODO-TOKEN-EFFICIENT-BOARD-ARCHIVE-AND-GIT-SUMMARY-TOOLS-2026-07-22

## Attempted

Implemented a live-board/archive split and bounded command helpers to reduce
future agent token use during board scans, dirty-worktree reviews, and staging
audits.

## Observed

- Before applying the archive split, `board_archive.py` found `65` archived
  level-two sections embedded in `.agent/BOARD.md`.
- After applying the split, `.agent/BOARD.md` has only `## Active`,
  `## Planned / Unclaimed`, `## Blocked`, `## Archive`, and `## Board Rules`.
- `board_summary.py --limit 10` reports `48` live parsed rows instead of the
  previous `880+` row scan.
- `board_summary.py --include-archive --limit 3` still sees the historical row
  universe and reported `881` rows.
- The git summary helper bounded a dirty tree with `300` status entries and
  `265` untracked entries to counts, top directories, and examples.

## Inferred

The main token failure mode was not the coordination policy itself, but using
full raw board/status/path outputs where a bounded summary was enough. Keeping
archive rows parser-readable in `.agent/BOARD_ARCHIVE.md` preserves historical
closeout checks while making startup and board hygiene cheaper.

## Caveats

- Several unrelated active/concurrent rows had already modified or created
  files. This task did not stage, revert, or clean those files.
- Ten completed rows remain in the live Active section. They should be
  archived in a follow-up board-cleanup pass after validation, not silently
  moved as part of this tooling implementation.
- Generated docs index files were already dirty before this task; this task will
  refresh them only during closeout.

## Next Useful Actions

- For routine board hygiene, run `python3.11 tools/agent/board_summary.py --limit 30`.
- After validating completed active rows, move them through
  `python3.11 tools/agent/board_archive.py --apply` and verify with `--check`.
- Before any future git push with many artifacts, run:
  - `python3.11 tools/git/clean_status_summary.py --untracked all --limit 30`
  - `python3.11 tools/git/staged_audit.py --limit 20`
  - `python3.11 tools/git/diff_check_filtered.py --max-output-lines 80`
