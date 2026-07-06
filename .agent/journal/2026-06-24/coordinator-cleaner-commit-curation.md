# AGENT-127 Raw Journal — Commit Curation

Date: `2026-06-24`
Task ID: `AGENT-127`
Owner: `codex`
Role: `Coordinator / Cleaner`

## Intent

Prepare a push-safe commit from the current mixed workspace without broad
staging. The user asked for a git-only cleanup that excludes figures and other
bulky not-useful artifacts from the commit while keeping text and Python
scripts locally and in the pushed snapshot where appropriate.

## Inputs Confirmed

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `README.md`
- `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/README.md`
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/README.md`
- `git status --short`
- `git diff --stat`

## Observed Workspace State

- The index initially contained only a staged `.agent/BOARD.md` update.
- The working tree also contained a large unstaged June report reorganization
  plus new text/code/provenance files and a smaller amount of generated figure
  output.
- `reports/2026-06/**` contained hundreds of `png` / `pdf` / `svg` files.
- `figures_rendered/**` contained rendered overview outputs that are not needed
  for the requested commit.

## Git Cleanup Rule Used

- Keep text-like provenance, notes, manifests, reports, CSV/JSON tables, and
  Python/script sources where they are not oversized dump artifacts.
- Exclude generated figure/image artifacts from the commit:
  - `png`
  - `pdf`
  - `svg`
  - other raster image formats if present
- Exclude oversized report payloads that are not needed for the requested
  text/code push.
- Leave excluded files on disk.

## Next Actions

- Stage the curated text/code/provenance tree explicitly.
- Review the staged diff for junk.
- Commit with a cleanup-oriented message.
- Push `main` to `upstream`.
