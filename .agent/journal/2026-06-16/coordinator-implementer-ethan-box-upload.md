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

## 2026-06-17 rclone recovery

- The user established a working `rclone` install at `~/bin/rclone` and a
  working `box:` remote in `~/.config/rclone/rclone.conf`.
- Live login-side checks succeeded:
  - `rclone lsd box:`
  - `rclone lsd "box:Andres_Obsidian_Notes_Box"`
  - `rclone lsd "box:Andres_Obsidian_Notes_Box/tamu_flow_loop"`
- Those checks exposed the real rclone-visible collaborator-output path:
  - `box:Andres_Obsidian_Notes_Box/tamu_flow_loop/a_tacc_analyzing_operational_data`
  rather than the earlier inferred `analyzing_operational_data` leaf name from
  the API-facing Box notes.
- Reworked the full upload wrapper to use `rclone copy` directly instead of the
  Python Box SDK helper.
- Added a one-file compute-node probe script:
  `tmp/2026-06-16_ethan_box_upload_probe/2026-06-17_rclone_box_probe.sbatch`
- The current shell is already inside interactive Slurm job `3233156` on
  `c318-008`, so `sbatch` is disabled from this session. To validate
  compute-node reachability, ran the probe directly on the current allocation.
- Probe result: success. The file `probe.txt` landed at:
  `box:Andres_Obsidian_Notes_Box/tamu_flow_loop/a_tacc_analyzing_operational_data/ethans runs probe 2026-06-17`
- After the probe cleared, launched the full transfer live from the same
  compute allocation with:
  `bash staging/upload_jobs/2026-06-16_ethan_runs_box_upload.sbatch`
- Early live-transfer observations:
  - traversal reached the expected `~105 GiB` mirror scope immediately
  - files began copying into `ethans runs` right away
  - one warning appeared for an OpenFOAM symlink under
    `dynamicCode/totalQ/lnInclude/...`: `Can't follow symlink without -L/--copy-links`
  - that warning is acceptable for now because Box cannot preserve Unix
    symlinks directly and the skipped path is a generated helper include, not a
    primary ParaView target
- Active runtime log:
  `tmp/2026-06-16_ethan_box_upload_probe/rclone_full_upload.log`

## 2026-06-17 symlink follow-up and operator docs

- Extended `operational_notes/2026-06-16_ethan_box_upload_plan.md` into a
  reproducible `rclone` runbook covering install, Box auth, reconnect,
  verification, probe upload, primary mirror launch, monitoring, and the
  bounded symlink follow-up workflow.
- Confirmed the main mirror skipped heterogeneous symlinks, but separated them
  into two operational classes:
  - broad convenience trees under `staging/render_inputs/**`
  - OpenFOAM-generated helper files under `dynamicCode/*/lnInclude/*`
- Chose not to rerun the whole workspace with `--copy-links`, because that
  would dereference unrelated render-input trees and inflate the payload.
- Generated a bounded manifest of the skipped OpenFOAM helper links:
  - `tmp/2026-06-16_ethan_box_upload_probe/openfoam_dynamiccode_symlink_manifest.txt`
  - `tmp/2026-06-16_ethan_box_upload_probe/openfoam_dynamiccode_symlink_targets.txt`
- Counted `119` manifest entries, all rooted under `staging/**/dynamicCode` or
  `jadyn_runs/**/dynamicCode`.
- Added a dedicated follow-up wrapper:
  `tmp/2026-06-16_ethan_box_upload_probe/2026-06-17_rclone_openfoam_symlink_followup.sbatch`
- The wrapper uses:
  - `rclone copy --copy-links --files-from <manifest>` to upload only the
    listed symlink targets
  - sibling destination
    `box:Andres_Obsidian_Notes_Box/tamu_flow_loop/a_tacc_analyzing_operational_data/ethans runs openfoam symlink targets`
  - `rclone copyto` to place the manifest and target map alongside the payload
- Verified the wrapper syntax locally with:
  `bash -n tmp/2026-06-16_ethan_box_upload_probe/2026-06-17_rclone_openfoam_symlink_followup.sbatch`
- Submitted the follow-up as a real queued batch job from the login node, since
  `sbatch` is disabled from the current compute shell:
  - submission command:
    `ssh login1 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch --parsable tmp/2026-06-16_ethan_box_upload_probe/2026-06-17_rclone_openfoam_symlink_followup.sbatch'`
  - returned job id: `3241193`
- Immediate queue-state check:
  - `ssh login1 'squeue -j 3241193'`
  - state: running on `c318-009` in `NuclearEnergy-dev`
