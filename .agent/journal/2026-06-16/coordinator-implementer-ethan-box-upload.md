# AGENT-082 Journal

Date: `2026-06-16T16:30:00-05:00`
Role: `Coordinator / Implementer`
Task: `AGENT-082`

## Intent

Set up a reproducible Box upload path for the Ethan workspace so the staged CFD
cases can be downloaded and opened locally in ParaView without manually rsyncing
from LS6 each time.

## Observed state at start

- The workspace already had an established Box convention in the sibling
  `dmdc-analysis` repo: collaborator-facing outputs go under Box folder
  `385169164073`
  (`All Files/Andres_Obsidian_Notes_Box/tamu_flow_loop/analyzing_operational_data`),
  while raw TAMU data stays isolated in raw-data folder `246873664013`.
- The Ethan workspace contains the actual case-bearing trees needed for local
  ParaView work, especially:
  - `staging/modern_runs/2026-06-01_full_extractable_batch/` at about `56G`
  - `jadyn_runs/` at about `36G`
  - `reports/` at about `1.1G`
- The file count is high enough that a naive uploader would be risky:
  `staging/modern_runs/...` plus `jadyn_runs/` already account for roughly
  `344k` files, and many individual files exceed `50 MB`.
- The official Node-based Box CLI is not available in this environment, and no
  `node` or `npm` module is present.
- The existing Box OAuth cache in `~/.box/oauth_token_cache.json` is expired, so
  any real upload must refresh or re-authenticate first.

## Planned action

- Reuse the proven collaborator-facing Box root `385169164073`, but create a
  dedicated subfolder named `ethans runs` instead of writing into the raw-data
  tree.
- Add a Python uploader under `tools/publish/` that:
  - mirrors a selected local tree into Box
  - handles both small uploads and chunked uploads for large OpenFOAM files
  - skips Box-irrelevant local state by default (`.git`, `.agent`, `cache`,
    `tmp`, `linked_cases`, and similar scratch/control folders)
  - defaults to dry-run semantics unless `--execute` is requested
- Add a Slurm wrapper under `staging/upload_jobs/` that bootstraps a
  job-local virtualenv and runs the uploader on a compute allocation instead of
  on the login node.

## Outcome

- Claimed `AGENT-082` for the bounded Box-upload scope.
- Added a dated operational note documenting the chosen remote destination, the
  size/risk profile, and the remaining auth boundary.
- Added a repo-local uploader designed around Box’s current Python SDK package
  layout and chunked-upload path.
- Added a dated Slurm wrapper that prepares a local virtualenv and launches the
  uploader against the chosen remote subfolder.
- Fixed the job bootstrap package list so the wrapper now installs
  `box-sdk-gen`, matching the uploader’s `box_sdk_gen` imports.
- Tightened the default upload scope to exclude generated `figures/` and
  `figures_rendered/` trees unless explicitly re-included.
- Verified the uploader locally in `--inventory-only` mode. The full default
  mirror scope under the current exclusions is:
  - `345,514` files
  - `107.4 GiB`
  - dominant top-level payloads:
    - `staging`: `219,125` files, `71.0 GiB`
    - `jadyn_runs`: `125,962` files, `35.5 GiB`
    - `reports`: `173` files, `922.8 MiB`
    - `tools`: `56` files, `1.2 MiB`
- Verified the live remote path cannot run yet. A one-file Box probe through
  the prepared virtualenv fails during OAuth refresh with:
  - Box API `400`
  - `error = invalid_grant`
  - `error_description = Refresh token has expired`
- Preserved the main unresolved blocker explicitly: the cached Box OAuth state
  is stale, so a live upload requires a fresh Box login or equivalent token
  refresh before `--execute` can succeed.
