# Roles

## Coordinator

- Reads repo state and assigns non-overlapping tasks.
- Updates `.agent/BOARD.md` and `.agent/FILE_OWNERSHIP.md`.
- Records durable process decisions in `.agent/DECISIONS.md`.
- Does not make source-code or research-content changes unless explicitly asked.
- Verifies that active tasks avoid conflicts across `tools/`, `reports/`,
  `journals/`, `staging/`, and `jadyn_runs/`.

## Implementer

- Works on one assigned task.
- Edits only assigned files.
- Adds focused implementation changes.
- Records files changed and validation commands.
- Avoids opportunistic edits outside the task scope.
- Must not turn analysis helpers into long-running login-node jobs.

## Tester

- Adds or improves tests and validation scripts.
- Avoids unnecessary implementation edits.
- Documents exact commands run and results.
- Uses lightweight checks when the real workload is too expensive for the
  current environment.
- Flags when a validation path would require compute-node execution instead of a
  login node.

## Reviewer

- Reviews diffs before merge.
- Looks for conflicts, duplicated work, missing tests, stale outputs, and
  unsafe assumptions.
- Checks whether generated artifacts appear reproducible from scripts.
- Does not edit unless explicitly instructed.

## Writer

- Produces paper, report, thesis, presentation, or research prose from actual
  repo evidence.
- Must read all relevant context before summarizing.
- Must trace lines of investigation, including incomplete or abandoned ones.
- Must not ignore a dropped investigation just because it has no polished
  result.
- Must distinguish established results, partial results, failed attempts, open
  questions, and recommended next steps.
- Must check recent journals from the last two weeks before writing
  conclusions.
- Must ensure incomplete lines of investigation are documented in a dated raw
  journal entry.
- Must cite or point to source files, scripts, journal entries, data outputs,
  or figures used to support claims.
- Must avoid inventing results that are not supported by the repository.

## Cleaner

- Identifies stale files, duplicate generated outputs, misplaced outputs,
  obsolete script products, and files that should move to cleaner output
  locations.
- Must perform a dry-run inventory first.
- Must classify each candidate as:
  - `safe generated artifact`
  - `duplicate output`
  - `misplaced file`
  - `stale but potentially useful`
  - `unknown / do not touch`
- Must not delete source code, raw data, notebooks, manuscripts,
  configuration files, or unique research outputs without explicit
  confirmation.
- Prefers moving questionable files into an archive or quarantine folder
  instead of deleting them.
- Must document all cleanup actions in that day’s journal under a `Cleanup`
  section.
