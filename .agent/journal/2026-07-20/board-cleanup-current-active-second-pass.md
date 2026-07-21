---
provenance:
  - .agent/BOARD.md
  - .agent/status/2026-07-20_AGENT-566.md
  - imports/2026-07-20_board_cleanup_current_active_second_pass.json
tags: [board-cleanup, coordination, agent-operations, current-state]
related:
  - .agent/status/2026-07-20_AGENT-566.md
  - imports/2026-07-20_board_cleanup_current_active_second_pass.json
task: AGENT-566
date: 2026-07-20
role: Coordinator/Cleaner/Writer
type: journal
status: complete
---
# Board Cleanup Current Active Second Pass

Task: AGENT-566

## Attempted

Performed a second board cleanup after the user asked to clean the board again.
The cleanup target was limited to rows in `## Active` whose goal already stated
`STATUS: COMPLETE` and whose closeout artifacts passed the repo validator.

## Observed

Before cleanup, the active table still contained 21 completed rows mixed with
live/open work. All 21 initial candidate rows passed
`python3.11 tools/agent/finish_task.py --task-id <TASK>`. During cleanup, a new
`AGENT-567` in-progress row appeared; it was not a candidate and was preserved.
The older `AGENT-519` monitor row also remained active and was preserved. A
late-arriving `TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS` row then
appeared in `## Active` already marked complete; it passed `finish_task.py` and
was archived as the 22nd row in this pass.

## Inferred

The board was stale mainly because completed July 20 rows had not been archived
after their own closeout. Archiving them improves dispatch clarity without
changing any research, admission, scheduler, registry, or blocker state.

## Caveats

`tools/agent/board_dashboard.py` does not currently classify `STATUS: IN
PROGRESS` as an active/live status, so it undercounts `AGENT-567`. Manual
inspection of the `## Active` table should be used until that status-token
mismatch is fixed by a separate tooling row.

## Cleanup

Moved these validated completed rows out of `## Active`:
`TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS`, `AGENT-565`,
`AGENT-563`, `AGENT-564`, `TODO-FINAL-SCORECARD-POLICY-INTEGRATION`,
`AGENT-562`, `AGENT-561`, `AGENT-560`, `AGENT-559`, `AGENT-558`,
`TODO-FINAL-SCORECARD-SOURCE-ENVELOPE-RESOLUTION`, `AGENT-557`,
`TODO-FINAL-SCORECARD-SOURCE-PROPERTY-REFRESH`, `AGENT-556`, `AGENT-555`,
`TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN`,
`TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL`,
`TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER`,
`TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS`, `AGENT-554`, `AGENT-553`, and
`AGENT-552`.

## Next Useful Actions

Keep `AGENT-567` and `AGENT-519` visible until they close or are superseded.
Future board work should distinguish real open TODO priority decisions from
simple completed-row cleanup.
