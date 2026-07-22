---
provenance:
  - .agent/BOARD.md
  - .gitignore
  - imports/2026-07-22_worktree_trim_stage_commit_push.json
tags: [status, coordination, cleanup, git, board-hygiene]
related:
  - .agent/journal/2026-07-22/worktree-trim-stage-commit-push.md
  - .agent/STATE.md
  - .agent/BLOCKERS.md
task: TODO-WORKTREE-TRIM-STAGE-COMMIT-PUSH-2026-07-22
date: 2026-07-22
role: Coordinator / Cleaner / Reviewer
type: status
status: complete
---
# TODO-WORKTREE-TRIM-STAGE-COMMIT-PUSH-2026-07-22

## Objective

Trim the staged push set by unstaging user-approved bulky generated figure,
image, and deck packages; add scoped ignore rules that keep those artifacts
local while preserving useful docs/tables; stage the remaining non-junk
evidence and coordination files; clean validated stale board rows; and prepare
the result for commit/push.

## Outcome

Completed the requested index cleanup. The staged set was reduced from the
previously observed `8111` files and about `252.07 MiB` to `7652` files and
about `63.54 MiB` before closeout docs/index refresh.

The agreed bulky packages now stage only docs/tables:

- `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/`: `100`
  staged files, `6.00 MiB`, `0` SVG/PNG/PDF/PPTX.
- `work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_expanded_case_set/`:
  `9` staged files, `0.49 MiB`, `0` SVG/PNG/PDF/PPTX.
- `work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope/`:
  `9` staged files, `0.49 MiB`, `0` SVG/PNG/PDF/PPTX.
- `work_products/2026-07/2026-07-15/2026-07-15_salt_training_testing_oscillation_steady_state/`:
  `8` staged files, `0.33 MiB`, `0` SVG/PNG/PDF/PPTX.
- `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/`:
  `6` staged files, `0.06 MiB`, `0` SVG/PNG/PDF/PPTX.
- `work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/`:
  `3` staged files, `0.01 MiB`, `0` SVG/PNG/PDF/PPTX.

Archived `12` validated completed Active rows. The fig/table D2/H2 extension
self-reports complete but remains live because closeout validation failed.

## Changes Made

- Added scoped `.gitignore` rules for the agreed bulky generated
  timeseries/oscillation/velocity/deck exports.
- Unstaged the agreed packages and re-added package docs/tables only under the
  new ignore policy.
- Archived validated completed rows from `.agent/BOARD.md`.
- Excluded currently active task scopes and invalid-closeout fig/table outputs
  from the staged set.
- Wrote this status, journal, and import manifest.

## Validation

- `python3.11 tools/agent/finish_task.py --task-id <completed-row> --json`:
  passed for the `12` rows archived during this task.
- `python3.11 tools/agent/finish_task.py --task-id TODO-PREDICTIVE-1D-STRONGEST-DIRECTION-RUNTIME-CONTRACT-2026-07-22 --json`:
  failed; task not found on board and status lacks `## Changes Made`. Left out
  of the staged set.
- `python3.11 tools/agent/finish_task.py --task-id TODO-THESIS-FIGTABLE-D2-H2-DIAGNOSTIC-FIGURE-EXTENSION-2026-07-22 --json`:
  failed; missing import manifest and status lacks `## Changes Made`. Left out
  of the staged set.

## Remaining Blockers

- Active task outputs remain local for:
  `TODO-S13-THROUGHFLOW-ENTHALPY-ENDPOINT-PREFLIGHT-2026-07-22`,
  `TODO-THESIS-LATEX-EVIDENCE-BATCH-TRANSFER-2026-07-22`, and
  `TODO-THESIS-FIGURES-DIAGRAMS`.
- The D2/H2 fig/table extension needs its owning agent to add the missing
  import manifest and repair the status-file shape before archive/stage.
- The predictive strongest-direction runtime contract needs a board row and
  status-file shape repair before archive/stage.

## Guardrails

No files were deleted. No native CFD/OpenFOAM outputs, registry/admission
state, scheduler state, Fluid/external repos, thesis body/LaTeX files,
source/property or Qwall releases, coefficient admissions, final scores, or
S11/S12/S13/S15/S6 triggers were changed.
