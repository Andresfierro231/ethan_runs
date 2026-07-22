---
provenance:
  generated_by: codex
  generated_at: 2026-07-22
tags:
  - board-cleanup
  - worktree-hygiene
  - staging
related:
  - .agent/BOARD.md
  - .gitignore
  - imports/2026-07-22_worktree_board_stage_for_push.json
---

# TODO-WORKTREE-BOARD-STAGE-FOR-PUSH-2026-07-22

## Objective

Clean stale completed board locks and prepare a reviewable git index for a later push without deleting, reverting, committing, pushing, or staging heavy local/generated runtime payloads.

## Outcome

Completed. Six validated completed Active rows were archived:

- `TODO-THERMAL-PASSIVE-H2-RADIATION-RUNTIME-BASIS-RECONCILIATION-2026-07-22`
- `TODO-THESIS-PAPER-OUTLINE-EVIDENCE-TRANSFER-GAP-REQUEST-2026-07-22`
- `TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22`
- `TODO-S13-MEDIUM-FINE-MESH-GCI-DISPOSITION-2026-07-22`
- `TODO-S13-COARSE-EQUIVALENCE-OPEN-CV-HEATFLOW-CONTRACT-2026-07-22`
- `TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22`

The D2 row had a stray priority cell in Active; its archived parser-readable copy was normalized back to the standard five-column board schema after `finish_task.py --json` passed.

## Changes Made

- Added this cleanup/staging row and closeout artifacts.
- Archived validated completed locks from `.agent/BOARD.md`.
- Added targeted `.gitignore` rules for the local S13 target-plus staging mirror and very large regenerated CSV row dumps:
  - `staging/s13_target_plus_window_generation_2026-07-22/**`
  - `work_products/**/trusted_wall_Q_wall_detail_rows.csv`
  - `work_products/**/salt14_postprocessing_tidy.csv`
- Rebuilt the generated documentation index after board cleanup.
- Prepared the git index from non-ignored durable docs/code/evidence files only.

## Validation

- `python3.11 tools/agent/finish_task.py --task-id <archived-task> --json` passed for each archived completed row.
- `python3.11 tools/docs/build_repo_index.py` completed after cleanup.
- `python3.11 tools/agent/finish_task.py --task-id TODO-WORKTREE-BOARD-STAGE-FOR-PUSH-2026-07-22 --json` passed before final staging.
- Pre-stage visible status after targeted ignores: `8045` changed/untracked non-ignored files, `253.96 MiB` total, largest visible file about `5.15 MiB`.

## Guardrails

- No native CFD/OpenFOAM outputs were mutated.
- No registry/admission state was mutated.
- No scheduler action was taken.
- No Fluid or external repository was edited.
- No thesis body/LaTeX file was edited by this row.
- No files were deleted or reverted.
- No commit or push was performed.

## Remaining Notes

The staged set intentionally depends on `.gitignore` to keep heavyweight local staging and large regenerated row dumps out of the repository. Any remaining unstaged files after final staging should be treated as ignored/heavy/local scratch unless reported otherwise in the final status.
