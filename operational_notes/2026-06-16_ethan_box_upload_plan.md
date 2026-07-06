# Ethan Box Upload Plan

Date: `2026-06-16`
Task: `AGENT-082`

## Goal

Upload the Ethan workspace to Box in a form that is practical to download and
open locally in ParaView, without writing anything into the raw-data Box tree.

## Chosen destination

Recommended Box root:

- Box folder ID: `385169164073`
- Earlier API-facing label:
  `All Files/Andres_Obsidian_Notes_Box/tamu_flow_loop/analyzing_operational_data`
- Actual `rclone`-visible path:
  `box:Andres_Obsidian_Notes_Box/tamu_flow_loop/a_tacc_analyzing_operational_data`

Chosen remote subfolders:

- primary mirror: `ethans runs`
- symlink follow-up payload: `ethans runs openfoam symlink targets`

Recommended resulting remote paths:

```text
box:
  / Andres_Obsidian_Notes_Box
    / tamu_flow_loop
      / a_tacc_analyzing_operational_data
        / ethans runs
        / ethans runs openfoam symlink targets
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
- A separate symlink-target folder is safer than rerunning the main upload with
  `--copy-links`, because it avoids expanding unrelated symlinked trees such as
  `staging/render_inputs/**`.

## Local prerequisites

Expected local root:

- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

Required user-local tools and config:

- `~/bin/rclone`
- `~/.config/rclone/rclone.conf`

Current verified state:

- `~/bin/rclone` exists and runs.
- `rclone listremotes` shows `box:`.
- `rclone lsd box:` succeeds.
- `rclone lsd "box:Andres_Obsidian_Notes_Box/tamu_flow_loop"` succeeds.
- A compute-node probe upload succeeded into a temporary Box folder.

## Setup and auth procedure

Use `rclone`, not the older Python Box SDK helper, as the active upload path.

Install `rclone` in user space:

```bash
mkdir -p "$HOME/software" "$HOME/bin"
cd "$HOME/software"
curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip
unzip rclone-current-linux-amd64.zip
cp rclone-*-linux-amd64/rclone "$HOME/bin/"
chmod +x "$HOME/bin/rclone"
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
"$HOME/bin/rclone" version
```

Configure Box from TACC:

```bash
"$HOME/bin/rclone" config
```

Recommended choices:

- remote name: `box`
- storage: `box`
- `client_id`: Enter
- `client_secret`: Enter
- `box_sub_type`: `user`
- auto browser auth: `n`

Because TACC is headless, complete the authorization on a machine with a
browser:

```bash
rclone authorize "box"
```

Paste the returned token blob back into the TACC `rclone config` session.

If Box auth later expires:

```bash
"$HOME/bin/rclone" config reconnect box:
```

## Verification checklist

On the login node:

```bash
"$HOME/bin/rclone" listremotes
"$HOME/bin/rclone" lsd box:
"$HOME/bin/rclone" lsd "box:Andres_Obsidian_Notes_Box"
"$HOME/bin/rclone" lsd "box:Andres_Obsidian_Notes_Box/tamu_flow_loop"
```

Expected collaborator-output branch:

- `a_tacc_analyzing_operational_data`

Compute-node smoke test:

```bash
mkdir -p tmp/2026-06-16_ethan_box_upload_probe/probe_src
date --iso-8601=seconds \
  > tmp/2026-06-16_ethan_box_upload_probe/probe_src/probe.txt
bash tmp/2026-06-16_ethan_box_upload_probe/2026-06-17_rclone_box_probe.sbatch
```

Probe verification:

```bash
"$HOME/bin/rclone" ls \
  "box:Andres_Obsidian_Notes_Box/tamu_flow_loop/a_tacc_analyzing_operational_data/ethans runs probe 2026-06-17"
```

## Primary mirror scope

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
  is required internally by `rclone`.
- The transfer should run under Slurm or from an existing compute allocation,
  not from the login node.

## Primary upload command

Use `rclone copy`, not `rclone sync`, for the default mirror:

```bash
bash staging/upload_jobs/2026-06-16_ethan_runs_box_upload.sbatch
```

That wrapper uploads:

- source: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`
- destination:
  `box:Andres_Obsidian_Notes_Box/tamu_flow_loop/a_tacc_analyzing_operational_data/ethans runs`

Current monitoring file:

- `tmp/2026-06-16_ethan_box_upload_probe/rclone_full_upload.log`

Useful monitor command:

```bash
tail -f tmp/2026-06-16_ethan_box_upload_probe/rclone_full_upload.log
```

## Known skipped content in the primary mirror

The main `rclone copy` deliberately does not follow symlinks.

Observed skipped categories:

- many symlinked convenience trees under `staging/render_inputs/**`
- generated OpenFOAM dynamic-code helper links under
  `dynamicCode/*/lnInclude/*`

The render-input symlinks are intentionally left alone in the primary mirror.
They are local convenience links, not authoritative payload.

## OpenFOAM symlink follow-up

Reason for a separate follow-up:

- The skipped OpenFOAM symlink files are small but potentially useful for full
  case reproducibility.
- Running the whole tree with `--copy-links` would be unsafe because it would
  dereference unrelated symlinked directories and multiply the upload scope.

Bounded follow-up policy:

- upload only symlinked files matching
  `staging/**/dynamicCode/*/lnInclude/*` and
  `jadyn_runs/**/dynamicCode/*/lnInclude/*`
- preserve their root-relative paths
- upload into sibling Box folder `ethans runs openfoam symlink targets`
- include the manifest and target map used to drive the copy

Current manifest artifacts:

- path list:
  `tmp/2026-06-16_ethan_box_upload_probe/openfoam_dynamiccode_symlink_manifest.txt`
- symlink-to-target map:
  `tmp/2026-06-16_ethan_box_upload_probe/openfoam_dynamiccode_symlink_targets.txt`

Current bounded inventory:

- `119` OpenFOAM `lnInclude` symlink files

Follow-up job entrypoint:

```bash
bash tmp/2026-06-16_ethan_box_upload_probe/2026-06-17_rclone_openfoam_symlink_followup.sbatch
```

If a real queued batch submission is preferred from a compute node:

```bash
ssh login1 \
  'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && \
   sbatch --parsable tmp/2026-06-16_ethan_box_upload_probe/2026-06-17_rclone_openfoam_symlink_followup.sbatch'
```

## Operator guidance

- Use `copy` first; do not switch to `sync` unless deletes on Box are intended.
- Keep the primary mirror and the symlink-target payload separate.
- Re-run `rclone config reconnect box:` if token refresh fails.
- Prefer storing provenance notes and manifests alongside the upload plan so the
  Box tree remains reproducible later.
