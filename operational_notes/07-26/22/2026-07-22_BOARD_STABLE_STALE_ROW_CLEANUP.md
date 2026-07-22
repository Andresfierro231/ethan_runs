---
provenance:
  - .agent/BOARD.md
tags: [coordination, board-cleanup]
related:
  - .agent/status/2026-07-22_TODO-BOARD-STABLE-STALE-ROW-CLEANUP-2026-07-22.md
  - .agent/journal/2026-07-22/board-stable-stale-row-cleanup.md
  - imports/2026-07-22_board_stable_stale_row_cleanup.json
task: TODO-BOARD-STABLE-STALE-ROW-CLEANUP-2026-07-22
date: 2026-07-22
role: Coordinator/Cleaner/Reviewer/Writer
type: operational_note
status: complete
---
# Board Stable Stale Row Cleanup

Task: `TODO-BOARD-STABLE-STALE-ROW-CLEANUP-2026-07-22`

## Cleanup Summary

The live board had another completed-row wave in both `## Active` and `## Planned / Unclaimed`.

- Archived `24` completed rows from `## Active`.
- Archived `20` completed rows from `## Planned / Unclaimed`.
- The initial validator pass found `21` completed Active rows and `17` completed Planned rows before archival, all passing `finish_task.py --json`; additional rows completed during cleanup and were handled before closeout.
- Marked `TODO-MF16-SOURCE-PROPERTY-EXACT-FIELDS-RELEASE-CANDIDATE-2026-07-22` as `closeout-fix-needed` because its validator failed due missing manifest mutation keys and a non-existent changed-file glob.
- Final live `## Active` has `14` rows, `0` stale complete rows, and `1` explicit closeout-fix row.
- Final live `## Planned / Unclaimed` has `17` rows and `0` stale complete rows.

## Guardrails

This was board hygiene only. No native CFD/OpenFOAM outputs, registry/admission state, scheduler jobs, solver/postprocessing/sampler/harvest/UQ, Fluid/external repos, thesis body/LaTeX, fitting/model selection, source/property/Qwall release, blocker-register source, staging, commit, or push were touched.

## Next Useful Actions

- Leave active solver/sampler monitor rows alone unless their owner closes them.
- If another row self-reports complete, validate with `python3.11 tools/agent/finish_task.py --task-id <TASK> --json` before archiving.
- Planned now reads like an open queue again; avoid adding broad duplicate research rows until the current open lanes are claimed or retired.
