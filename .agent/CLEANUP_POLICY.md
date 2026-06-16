# Cleanup Policy

Cleaner tasks are safety-critical in this repo because generated artifacts,
staged cases, and report packages can be large, valuable, and hard to rebuild
quickly.

## Required workflow

1. Run in dry-run mode first.
2. Build a candidate table before acting.
3. Wait for confirmation on destructive or ambiguous actions.
4. Record every move or delete with the command or rationale used.

## Candidate classification

Each cleanup candidate must be classified as one of:

- `safe generated artifact`
- `duplicate output`
- `misplaced file`
- `stale but potentially useful`
- `unknown / do not touch`

## Required proposal table

Use a table like this before acting:

| Path | Classification | Why it is a candidate | Proposed action | Reproducible from script? | Needs confirmation? |
| --- | --- | --- | --- | --- | --- |

## Hard rules

- Cleaner must never broad-delete.
- Cleaner must never delete source code, raw data, notebooks, manuscripts,
  configuration files, native imported solver outputs, or unique research
  outputs without explicit confirmation.
- Prefer moving generated artifacts to a clean output directory or archive.
- Prefer archiving questionable files over deleting them.
- Delete only clearly reproducible generated clutter.
- Document actions in `.agent/journal/YYYY-MM-DD/cleaner.md` or the appropriate
  daily cleanup file.

## Repo-specific hotspots

- `tmp/`
- `tmp_extract/`
- `cache/`
- `reports/**/figures/`
- `figures_rendered/`
- old or duplicate status JSON under `figures/`

These areas still require dry-run classification first.
