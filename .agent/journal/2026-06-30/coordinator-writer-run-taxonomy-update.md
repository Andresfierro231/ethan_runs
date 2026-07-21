# AGENT-157 Raw Notes

Date: `2026-06-30`
Role: `Coordinator / Writer`
Task ID: `AGENT-157`

## Scope

- `.agent/BOARD.md`
- `.agent/status/2026-06-30_AGENT-157.md`
- `.agent/journal/2026-06-30/coordinator-writer-run-taxonomy-update.md`
- `AGENTS.md`
- `README.md`
- `operational_notes/06-26/30/2026-06-30_run_classification_policy.md`

## Observed starting point

- Root `AGENTS.md` and `README.md` did not yet state a repo-level rule for how
  to classify continuation runs versus perturbations.
- Older notes still left room for Kirst usage or Jin-vs-Kirst framing:
  - `operational_notes/06-26/01/2026-06-01_modern_runs_first_batch_extraction_summary.md`
  - `operational_notes/06-26/01/2026-06-01_publish_handoff_gate.md`
  - `operational_notes/06-26/01/2026-06-01_todo.md`
  - `operational_notes/06-26/02/2026-06-02_todo.md`
- `README.md` was already claimed by active `AGENT-127`, so the board needed a
  narrow coordinator-approved overlap before editing the root documentation.

## Actions taken

- Opened `AGENT-157` on the board with an explicit note that the overlap with
  `AGENT-127` is limited to the root `README.md` run-taxonomy correction.
- Updated `AGENTS.md` so repo instructions now state:
  - continuations are the current mainline family when present
  - Kirst runs are excluded from current mainline use
  - perturbations stay in a separate correlation-support group
- Updated `README.md` to surface the same policy from the main repo
  documentation.
- Added `operational_notes/06-26/30/2026-06-30_run_classification_policy.md` as a
  dated override note that supersedes the older Kirst framing.

## Current handoff state

- Repo-level instructions now align with the current policy the user asked for.
- Older campaign or report notes that still mention Kirst as a usable main
  comparison path should be treated as historical unless they are updated by a
  later dated note.
