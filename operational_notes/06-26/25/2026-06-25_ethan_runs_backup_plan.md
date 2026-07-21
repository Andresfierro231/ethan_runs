# Ethan Runs Backup Plan

Date: `2026-06-25`
Task: `AGENT-129`

## Goal

Create a durable, readable backup of the current local
`/scratch/09748/andresfierro231/projects_scratch/ethan_runs` workspace under:

`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs`

The backup needs to:

- preserve the large run-bearing trees and their surrounding documentation
- make it obvious where the mirrored data lives
- make it cheap to identify only the new or changed files before each refresh
- run the actual copy through a `NuclearEnergy` Slurm job instead of a login node

## Chosen destination layout

Recommended backup root:

`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup`

Recommended internal structure:

```text
ethan_runs_backup/
  README.md
  manifests/
    latest/
    history/<timestamp>/
  mirror/
    ethan_runs/
```

Meaning:

- `README.md`
  Human-facing explanation of what the backup contains, what is excluded by
  default, and which commands regenerate the manifests.
- `manifests/latest/`
  The most recent rsync dry-run or sync outputs. This is the fast place to
  inspect what would move next.
- `manifests/history/<timestamp>/`
  A retained per-run record of the exact rsync command plus the generated file
  lists for that run.
- `mirror/ethan_runs/`
  The actual additive workspace backup.

This keeps the backup self-contained and readable without mixing the copied
workspace directly into the root of `cfd_runs/`.

## Current observed source size

Observed on `2026-06-25` before the final `prepare` action:

- destination `cfd_runs/` existed but had no backup substructure yet
- included backup scope: about `786,074,703,912` bytes (`732.1 GiB`)
- included file count estimate: about `1,197,130` files

Dominant included trees:

- `jadyn_runs`: about `497G`
- `tmp_extract`: about `163G`
- `staging`: about `72G`
- `figures`: about `1.8G`
- `reports`: about `1.3G`

Large excluded-by-default tree:

- `tmp`: about `166G`

## Default backup scope

Included by default:

- `staging/**`
- `jadyn_runs/**`
- `tmp_extract/**`
- `reports/**`
- `figures/**`
- `work_products/**`
- `imports/**`
- `registry/**`
- `config/**`
- `tools/**`
- `journals/**`
- `operational_notes/**`

Excluded by default:

- `.git/**`
- `.agent/**`
- `.agents/**`
- `.codex/**`
- `cache/**`
- `tmp/**`
- `linked_cases/**`
- `__pycache__/**`
- `.pytest_cache/**`
- `.DS_Store`

Reasoning:

- the included trees carry the run state, extracted data, figures, reports,
  scripts, manifests, and provenance needed to interpret the workspace later
- the excluded trees are control-state, convenience links, or large scratch
  state that is not part of the default backup contract

If `tmp/` needs to be preserved for a particular handoff, use `--include-tmp`
and increase the walltime request accordingly.

## Incremental diff workflow

Primary dry-run command:

```bash
bash tools/publish/rsync_ethan_runs_backup.sh plan
```

This writes:

- `manifests/latest/summary.txt`
- `manifests/latest/new_files.txt`
- `manifests/latest/changed_files.txt`
- `manifests/latest/rsync_plan.log`

Interpretation:

- `new_files.txt`
  Files not yet present in the backup mirror.
- `changed_files.txt`
  Existing files whose size or mtime changed relative to the mirror.
- `summary.txt`
  Short count summary plus the exact source and mirror roots.

The default copy mode is additive and does not delete anything already present
in the backup. That is safer for backup use than a strict mirror-delete policy.

If a deeper audit is needed, the same dry-run can use checksums:

```bash
bash tools/publish/rsync_ethan_runs_backup.sh plan --checksum
```

## Compute-node copy path

Preferred direct wrapper:

```bash
bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode sync --time 10:00:00
```

Default partition and account:

- partition: `NuclearEnergy`
- account: `ASC23046`

The wrapper emits an `sbatch` script under:

`tmp/slurm_ethan_runs_backup_jobs/<timestamp>_<mode>/`

That keeps the actual transfer reproducible and avoids running the large rsync
pass from an interactive login shell.

## Walltime estimate

Recommended requests:

- first full additive mirror, default scope: `10:00:00`
- recurring dry-run or incremental sync, default scope: `02:00:00`
- recurring checksum audit: `04:00:00`
- first sync with `tmp/` included: `12:00:00`

Basis:

- payload size is about `732.1 GiB` before `tmp/`
- the tree is metadata-heavy at about `1.2M` files
- even if effective sustained transfer were only `30-40 MiB/s`, the raw data
  motion is still in the `5-7` hour range, so a `10 h` request leaves
  reasonable headroom for file-list generation, metadata churn, and shared
  filesystem variability

## New helper scripts

- `tools/publish/rsync_ethan_runs_backup.sh`
  Creates the backup directory skeleton, writes the backup README, produces a
  dry-run delta manifest, and runs the actual additive rsync copy.
- `tools/publish/submit_ethan_runs_backup_sbatch.sh`
  Wraps the backup script in an `sbatch` launcher for `NuclearEnergy`.

## Validation done locally

- `bash -n tools/publish/rsync_ethan_runs_backup.sh`
- `bash -n tools/publish/submit_ethan_runs_backup_sbatch.sh`
- smoke-tested the backup script against a tiny throwaway tree under `/tmp`
- dry-ran the Slurm wrapper to confirm it emits a valid `sbatch` script and
  resolved command without submitting

## External layout status

The external backup skeleton now exists at:

`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup`

Created contents confirmed:

- `README.md`
- `manifests/latest/backup_scope.txt`
- `manifests/history/<timestamp>/backup_scope.txt`
- `mirror/ethan_runs/`

The next external action is the first real compute-node sync:

```bash
bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode sync --time 10:00:00
```

## 2026-06-29 backup-state addendum

Observed on `2026-06-29`:

- the backup mirror is no longer empty; files are present under
  `mirror/ethan_runs/`
- history sync artifacts now exist at:
  - `manifests/history/20260625T150303/`
  - `manifests/history/20260626T200016/`
- `manifests/latest/` still contains only `backup_scope.txt`
- sync attempt `3259614` hit the walltime limit
- sync attempt `3261333` ended with rsync warning code `24` because files
  vanished while live run directories were changing

Current interpretation:

- the helper scripts and destination layout remain valid
- the remaining open issue is manifest/finalization hygiene on a live,
  mutating source tree rather than basic launch failure
- this lane should stay live until a clean incremental rerun writes a fresh
  `manifests/latest/summary.txt` and companion delta files

Mitigation adopted on `2026-06-29`:

- add `--top-level-pass` so backup syncs run one rsync pass per top-level
  included directory
- keep rsync warning code `24` as non-fatal backup noise when files vanish
  during transfer
- record per-run pass results in `rsync_status.txt`
- support scheduled overnight starts with `submit_ethan_runs_backup_sbatch.sh
  --begin ...`

Overnight follow-up submitted:

- job id: `3265388`
- begin: `2026-06-29T20:00:00` CDT
- walltime: `11:30:00`
- expected end window: `2026-06-30T07:30:00` CDT
- script:
  `tmp/slurm_ethan_runs_backup_jobs/20260629T133052_sync/ethan_backup_sync.sbatch`
