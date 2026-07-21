# 2026-06-30 Board Cleanup Proposal

## Purpose

This is a proposal only. It does not move active board rows. The goal is to
reduce stale active-task noise after Claude's current lane and the local
latest-window chain finish.

## Retire Candidates

- `AGENT-153`: beginning-of-day job recap is complete. Remaining work was
  handed to `AGENT-154` / `AGENT-155`.
- `AGENT-157`: repo-level run taxonomy update is complete. Future package
  propagation should be separate task-specific work.
- `AGENT-147`: paper case inventory package is complete and has no blockers.
- `AGENT-148`: reduction-contract audit package is complete; later refresh is
  conditional on latest-window package publication.
- `AGENT-149`: status explicitly says `completed`.
- `AGENT-150`: closure-status gate package is complete; later refresh is
  conditional on latest-window changes.
- `AGENT-152`: launcher correction is complete; live job monitoring should be
  a separate operations task, not this implementation row.

## Keep Active For Now

- `AGENT-156`: Claude is actively working this lane.
- `AGENT-154`: local latest-window chain remains active via
  `tmux` session `lw_local_chain_20260630T113922`.
- `AGENT-155`: code fix is complete, but remaining status still points at
  monitoring the repaired rebuild path. It should be closed after the local
  chain confirms or supersedes Salt 4 completion.
- `AGENT-151`: status says `in_progress` even though a package exists. Needs a
  status reconciliation before retirement.
- `AGENT-129`: backup lane needs follow-up because the status still describes
  post-job inspection of `manifests/latest`.
- `AGENT-127`: broad cleanup/commit curation remains active and owns many
  report paths.
- `AGENT-102`, `AGENT-121`, `AGENT-122`, `AGENT-123`: latest-window and Fluid
  replay lanes remain active until the refreshed continuation packages and
  external readable replay are reconciled.

## Recommended Follow-On Tasks

- Open a narrow operations-monitor task for `3265969-3265972`, `3267228`, and
  `lw_local_chain_20260630T113922`.
- Open a backup-follow-up task to inspect latest backup manifests and decide
  whether rsync code `24` is acceptable routine noise.
- Open a package-specific presentation refresh task for
  `reports/2026-06/2026-06-23/2026-06-23_presentation/**` after the latest
  continuation chain finishes.
- Open a board-retirement task once Claude and the local chain finish, moving
  the retire candidates out of Active in one controlled patch.

## Do Not Retire Automatically

Do not remove rows just because their package exists on disk. Retire only after
the status file says complete/completed or after a coordinator note records how
remaining work was handed to another active task.
