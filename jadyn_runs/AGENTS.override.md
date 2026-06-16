# Jadyn Runs Override

Read this after the repo-root `AGENTS.md` when working anywhere under
`jadyn_runs/`.

## Scope

`jadyn_runs/` holds staged continuation candidates, targeted campaigns,
runtime-recovery notes, campaign TODOs, and lightweight helper scripts.

## Local rules

- Preserve non-destructive staging. Do not mutate imported native source trees.
- Read the local `README.md` and `TODO.md` in the specific campaign directory
  before editing anything below it.
- Treat `case_stage/` contents as restart-sensitive. Touch them only when the
  assigned task is specifically about staged runtime preparation or repair.
- Prefer editing the campaign README, TODO, sbatch wrapper, or helper script
  over making broad case-tree changes.
- When a continuation outcome changes interpretation, record it in a dated raw
  journal entry and update the relevant report package or operational note.
- Runtime/bootstrap experiments belong in scripts, sbatch wrappers, and
  documentation first; do not improvise one-off shell edits inside staged case
  trees.

## Current high-risk areas

- `salt2/2026-06-02_runtime_recovery/`: canonical repaired OpenFOAM 13 runtime
  path and bootstrap notes
- `salt1/2026-06-05_targeted_campaign/`: Salt 1 targeted retry coordination
- `salt4/2026-06-04_jin_continuation_candidate/`: staged Salt 4 Jin retry path
- `modern_runs/2026-06-01_source_inventory/`: campaign-level intake snapshot
