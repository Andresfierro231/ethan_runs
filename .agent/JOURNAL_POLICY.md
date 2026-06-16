# Journal Policy

Use a hybrid journal system.

## Locations

- `JOURNAL.md` at repo root is the curated consolidated journal.
- `.agent/journal/YYYY-MM-DD/<agent-or-task>.md` contains raw append-only
  entries from individual agents.

## Required raw entry fields

Each raw journal entry must be dated and include:

- date
- agent role
- task ID
- branch or worktree
- files inspected
- files changed
- commands run
- results or observations
- incomplete lines of investigation
- next steps

## Consolidation rules

- The Writer agent is responsible for consolidating relevant recent entries
  into `JOURNAL.md`.
- If the Writer finds an incomplete or dropped line of investigation, it must
  either:
  - document it in today’s raw journal entry
  - or add it to `JOURNAL.md` with date and source references
- Recent means within the last two weeks unless otherwise specified.

## Repo-specific guidance

- Use existing `journals/YYYY-MM/*.md` and `operational_notes/*.md` as source
  context for curated updates.
- Keep raw entries append-only. If a correction is needed, add a dated note
  instead of silently rewriting history.
- Writers should cross-check report package READMEs, summaries, and dated TODOs
  before closing out a line of investigation.
