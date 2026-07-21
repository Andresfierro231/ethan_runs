# 2026-06-30 Backup Follow-Up

## Observed

- Latest backup manifest stamp: `20260629T200027`
- Mode: `sync`
- Source root:
  `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`
- Backup root:
  `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup`
- Mirror root:
  `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup/mirror/ethan_runs`
- `include_tmp = 0`
- `top_level_pass = 1`

Latest summary counts:

- `new_files = 184439`
- `changed_files = 694`
- `created_dirs = 58611`
- `symlink_updates = 66`

Latest manifest files present:

- `backup_scope.txt`
- `changed_files.txt`
- `created_dirs.txt`
- `latest_stamp.txt`
- `new_files.txt`
- `rsync_command.txt`
- `rsync_status.txt`
- `rsync_sync.log`
- `summary.txt`
- `symlink_updates.txt`

## Root Status

- `staging`: `ok`
- `jadyn_runs`: `ok_with_vanished_files`, rsync code `24`
- `tmp_extract`: `ok`
- `reports`: `ok`
- `figures`: `ok`
- `work_products`: `ok`
- `imports`: `ok`
- `registry`: `ok`
- `config`: `ok`
- `tools`: `ok`
- `journals`: `ok`
- `operational_notes`: `ok`

## Interpretation

The backup lane is usable. The only nonzero rsync status is `jadyn_runs` with
code `24`, which is consistent with live-tree churn while CFD case directories
are being written or cleaned during active operations. The top-level pass
otherwise wrote the latest manifest set and every other tracked root completed
normally.

## Decision

- Accept rsync code `24` for `jadyn_runs` as routine live-tree vanished-file
  noise for this backup pass.
- Retire `AGENT-129` from Active; future backup refreshes should be opened as
  new routine operations tasks.
- Do not resubmit a backup job immediately. A cleaner rerun is only needed if a
  future user-facing transfer requires a quiet `jadyn_runs` snapshot.

## Validation Commands

- `sed -n '1,180p' /home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup/manifests/latest/summary.txt`
- `sed -n '1,160p' /home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup/manifests/latest/rsync_status.txt`
- `find /home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup/manifests/latest -maxdepth 1 -type f -printf '%f\n' | sort`
- `tail -40 tmp/slurm_ethan_runs_backup_jobs/20260629T133052_sync/slurm-3265388.out`
