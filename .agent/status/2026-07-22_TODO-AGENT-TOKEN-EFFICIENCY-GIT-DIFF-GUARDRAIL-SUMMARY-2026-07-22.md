---
provenance:
  - AGENTS.md
  - .agent/README.md
  - tools/agent/README.md
  - tools/git/README.md
tags: [status, agent-tooling, token-efficiency, git, guardrails]
related:
  - .agent/journal/2026-07-22/agent-token-efficiency-git-diff-guardrail-summary.md
  - imports/2026-07-22_agent_token_efficiency_git_diff_guardrail_summary.json
task: TODO-AGENT-TOKEN-EFFICIENCY-GIT-DIFF-GUARDRAIL-SUMMARY-2026-07-22
date: 2026-07-22
role: Coordinator / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-AGENT-TOKEN-EFFICIENCY-GIT-DIFF-GUARDRAIL-SUMMARY-2026-07-22

## Objective

Implement the remaining low-token helper gaps after the prior token-efficiency
tooling wave: path-scoped git diff summaries and quiet guardrail/lint command
summaries.

## Outcome

Completed.

- Added `tools/git/diff_summary.py`, a read-only helper for unstaged, staged, or
  `HEAD`-relative diffs. It prints changed-file counts, bounded top directories,
  bounded `--stat`, and bounded untracked examples for the same path scope. It
  does not print hunks.
- Added `tools/agent/guardrail_summary.py`, a read-only wrapper for noisy
  validation commands. It prints command, exit code, output-line count, and
  bounded `PASS`/`FAIL`/`NOTE`/`ERROR`/heading lines.
- Updated `AGENTS.md`, `.agent/README.md`, `tools/agent/README.md`, and
  `tools/git/README.md` with usage instructions.
- Added focused tests to `tools/agent/test_agent_tools.py`.

## Changes Made

- Added `tools/git/diff_summary.py`.
- Added `tools/agent/guardrail_summary.py`.
- Updated token-efficiency instructions in `AGENTS.md`, `.agent/README.md`,
  `tools/agent/README.md`, and `tools/git/README.md`.
- Added tests in `tools/agent/test_agent_tools.py`.
- Added board row, status, journal, and import manifests for this task.

## Validation

- `python3.11 -m pytest tools/agent/test_agent_tools.py -q` passed:
  `24 passed`.
- `python3.11 tools/git/diff_summary.py --mode unstaged --limit 12 -- tools/git tools/agent AGENTS.md .agent/README.md` passed and printed bounded changed/untracked/stat summaries.
- `python3.11 tools/agent/guardrail_summary.py --limit 12 -- python3.11 -c "print('== Demo =='); print('PASS: ok'); print('ordinary detail'); print('NOTE: bounded')"` passed and selected only heading/PASS/NOTE lines.
- `python3.11 tools/agent/guardrail_summary.py --limit 20 -- python3.11 tools/docs/build_repo_index.py --check` passed and summarized `blocker register OK (15 entries)`.
- `python3.11 tools/agent/finish_task.py --task-id TODO-AGENT-TOKEN-EFFICIENCY-GIT-DIFF-GUARDRAIL-SUMMARY-2026-07-22 --json`
  passed with `ok: true`, no errors, and no warnings.

## Concurrency Notes

The scoped diff helper showed large unrelated `.agent/BOARD.md` changes already
present in the dirty worktree, likely from board archive/hygiene work. This task
intentionally edited only its own new board row in `.agent/BOARD.md`; unrelated
board changes were not reverted.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, science/admission/source-property
or Qwall release, Fluid/external edit, thesis edit, blocker-register source
change, generated-index rewrite, deletion, staging, commit, push, or
runtime-leakage relaxation.
