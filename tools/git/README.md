---
provenance:
  - AGENTS.md
  - tools/README.md
  - tools/agent/README.md
tags: [git, token-efficiency, tooling]
related:
  - tools/git/clean_status_summary.py
  - tools/git/staged_audit.py
  - tools/git/diff_check_filtered.py
  - tools/git/diff_summary.py
task: TODO-TOKEN-EFFICIENT-BOARD-ARCHIVE-AND-GIT-SUMMARY-TOOLS-2026-07-22
date: 2026-07-22
role: Coordinator/Implementer/Tester/Writer
type: operational_note
status: complete
---
# Git Helper Tools

Use these helpers when the worktree has many generated files or staged outputs.
They bound command output so agents do not spend context on thousands of paths.

## Commands

```bash
python3.11 tools/git/clean_status_summary.py --untracked all --limit 30
python3.11 tools/git/staged_audit.py --limit 20
python3.11 tools/git/diff_check_filtered.py --max-output-lines 80
python3.11 tools/git/diff_summary.py --mode unstaged --limit 40 -- tools/agent tools/git
```

`clean_status_summary.py` replaces broad `git status --short --untracked-files=all`
when only counts, top directories, and examples are needed.

`staged_audit.py` reports staged byte totals, largest files, extension counts,
known generated-heavy hits, optional forbidden-prefix hits, and overlaps with
open Active row edit paths.

`diff_check_filtered.py` runs `git diff --cached --check` on staged paths while
skipping generated catalog/work-product outputs by default.

`diff_summary.py` summarizes unstaged, staged, or HEAD-relative diffs for an
optional path scope. It prints counts, top directories, and bounded `--stat`
output by default, and it includes bounded untracked-file examples for the same
path scope; use `--names` for a bounded name-status list. It does not print
hunks unless an agent intentionally runs raw `git diff` afterward.

These scripts do not stage, commit, push, delete, or rewrite files.
