# Ethan Box Upload Plan

Date: `2026-06-16`
Task: `AGENT-082`

## Goal

Upload the Ethan workspace to Box in a form that is practical to download and
open locally in ParaView, without writing anything into the raw-data Box tree.

## Chosen destination

Recommended Box root:

- Box folder ID: `385169164073`
- Box path:
  `All Files/Andres_Obsidian_Notes_Box/tamu_flow_loop/analyzing_operational_data`

Chosen remote subfolder:

- `ethans runs`

Recommended resulting remote path:

```text
All Files
  / Andres_Obsidian_Notes_Box
    / tamu_flow_loop
      / analyzing_operational_data
        / ethans runs
```

This keeps the Ethan share-out aligned with the existing collaborator-facing
Box convention already used by the sibling `dmdc-analysis` repo and avoids the
forbidden raw-data Box folder `246873664013`.

## Why this destination

- It is already the established outbound/share-out Box area, not the pull-only
  raw-data area.
- The Ethan workspace content is analysis-side material, not TAMU source data.
- A dedicated `ethans runs` subfolder makes it easy to keep the upload bounded
  and recognizable without mixing it into existing TAMU loop artifacts.

## Upload scope

Default local source root:

- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

Mirror strategy:

- Preserve the local relative directory structure under `ethans runs`.
- Include the run-bearing trees needed for local ParaView use, especially
  `staging/modern_runs/**` and `jadyn_runs/**`.
- Keep notes, manifests, scripts, and reports available alongside the runs.
- Exclude Box-irrelevant or scratch-only local state by default:
  - `.git`
  - `.agent`
  - `.agents`
  - `.codex`
  - `cache`
  - `figures`
  - `figures_rendered`
  - `tmp`
  - `tmp_extract`
  - `linked_cases`
  - `__pycache__`
  - `.pytest_cache`

These defaults keep the Box mirror useful as a transferable workspace snapshot
without uploading local control state or convenience symlinks.

## Current size and runtime implications

Observed large subtrees:

- `staging/modern_runs/2026-06-01_full_extractable_batch`: about `56G`
- `jadyn_runs`: about `36G`
- `reports`: about `1.1G`

Observed default mirror totals from full local inventory:

- `345,514` eligible files
- `107.4 GiB` eligible bytes
- top-level breakdown:
  - `staging`: `219,125` files, `71.0 GiB`
  - `jadyn_runs`: `125,962` files, `35.5 GiB`
  - `reports`: `173` files, `922.8 MiB`
  - `tools`: `56` files, `1.2 MiB`

Observed high file count:

- `staging/modern_runs/...` plus `jadyn_runs/`: about `344,454` files

Implications:

- A direct Box mirror is feasible but heavy.
- Many individual OpenFOAM files exceed `50 MB`, so Box’s chunked-upload path
  is required.
- The transfer should run under Slurm, not from the login node.

## Auth/tooling boundary

- No Node-based Box CLI is installed locally, and no `node`/`npm` module is
  available.
- The current Box OAuth cache under `~/.box/oauth_token_cache.json` is expired.
- The uploader therefore uses the Box Python SDK package installed into a
  virtualenv at run time, reading the same `~/.box/box_environments.json` and
  `~/.box/oauth_token_cache.json` credentials when they are valid.

Live upload boundary:

- `--execute` requires a fresh Box login or refreshable token cache.
- The live one-file Box probe already fails with `invalid_grant`, confirming
  the current refresh token is expired.
- Until that happens, the safe validation path is local inventory mode and
  script syntax checks.
