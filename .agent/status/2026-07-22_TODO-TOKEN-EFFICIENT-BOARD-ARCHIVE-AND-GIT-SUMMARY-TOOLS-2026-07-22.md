---
provenance:
  - AGENTS.md
  - .agent/BOARD.md
  - .agent/BOARD_ARCHIVE.md
  - tools/agent/README.md
  - tools/git/README.md
tags: [agent-operations, board-hygiene, token-efficiency, git-hygiene]
related:
  - .agent/journal/2026-07-22/token-efficient-board-archive-and-git-summary-tools.md
  - imports/2026-07-22_token_efficient_board_archive_and_git_summary_tools.json
task: TODO-TOKEN-EFFICIENT-BOARD-ARCHIVE-AND-GIT-SUMMARY-TOOLS-2026-07-22
date: 2026-07-22
role: Coordinator/Cleaner/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TOKEN-EFFICIENT-BOARD-ARCHIVE-AND-GIT-SUMMARY-TOOLS-2026-07-22 Status

## Changes Made

- Split historical `## Archived ...` sections out of `.agent/BOARD.md` into `.agent/BOARD_ARCHIVE.md`.
- Added `tools/agent/board_archive.py` for dry-run/apply/check archive maintenance.
- Added `board_archive.py --archive-task <TASK_ID> --apply` for archiving a
  single validated completed/blocked live row.
- Added `tools/agent/board_summary.py` for bounded board scans.
- Made `tools/agent/finish_task.py` archive-aware through `parse_board(include_archive=True)`.
- Added bounded git helpers under `tools/git/`:
  - `clean_status_summary.py`
  - `staged_audit.py`
  - `diff_check_filtered.py`
- Updated `AGENTS.md`, `.agent/README.md`, `.agent/FILE_OWNERSHIP.md`, `tools/README.md`, and `tools/agent/README.md` so agents use the archive and summary tools in routine board/worktree contexts.
- Added tests for board archive movement and section-aware board summary parsing.

## Validation

- `python3.11 -m py_compile tools/agent/common.py tools/agent/finish_task.py tools/agent/board_archive.py tools/agent/board_summary.py tools/git/clean_status_summary.py tools/git/staged_audit.py tools/git/diff_check_filtered.py` passed.
- `python3.11 -m pytest tools/agent/test_agent_tools.py` passed: `15 passed`.
- `python3.11 tools/agent/board_archive.py --check` passed.
- `python3.11 tools/agent/board_summary.py --limit 10` passed and reported a live-board bounded scan: `rows=48`, `active_open=6`, `complete_still_in_active=10`.
- `python3.11 tools/agent/board_summary.py --include-archive --limit 3` passed and reported archive-aware historical rows: `rows=881`.
- `python3.11 tools/git/clean_status_summary.py --untracked all --limit 12` passed and bounded a dirty worktree to counts/examples.
- `python3.11 tools/git/staged_audit.py --limit 8` passed with `staged_files=0`.
- `python3.11 tools/git/diff_check_filtered.py --max-output-lines 20` passed with `diff_check: OK`.
- `python3.11 tools/agent/finish_task.py --task-id TODO-PREDICTIVE-1D-STRONGEST-DIRECTION-RUNTIME-CONTRACT-2026-07-22 --json` passed, confirming archive-aware closeout lookup.
- `python3.11 tools/agent/board_archive.py --archive-task TODO-TOKEN-EFFICIENT-BOARD-ARCHIVE-AND-GIT-SUMMARY-TOOLS-2026-07-22 --apply` archived this completed row after validation.
- `python3.11 tools/docs/build_repo_index.py` passed after final archive movement: `indexed 3165 docs; 16 board rows; 15 blockers`.

## Guardrails

- Native CFD/OpenFOAM outputs were not mutated.
- Registry/admission state was not mutated.
- Scheduler state was not changed.
- Fluid/external repositories were not edited.
- Thesis body/LaTeX content was not edited.
- No scientific admission, coefficient release, source/property release, Qwall release, protected scoring, candidate freeze, or final score claim was made.
- No files were deleted.
- No git staging, commit, or push was performed.
- Unrelated dirty/untracked files from active/concurrent rows were left in place.

## Remaining Notes

- Ten completed rows still sit in the live Active section. The new
  `board_summary.py` exposes them clearly; a separate board-cleanup row should
  archive those after each row passes closeout validation.
