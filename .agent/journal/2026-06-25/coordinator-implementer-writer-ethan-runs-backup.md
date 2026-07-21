# AGENT-129 Raw Journal

Date: `2026-06-25`
Role: `Coordinator / Implementer / Writer`
Task: `AGENT-129`

## Scope

- `.agent/BOARD.md`
- `.agent/status/2026-06-25_AGENT-129.md`
- `.agent/journal/2026-06-25/coordinator-implementer-writer-ethan-runs-backup.md`
- `imports/2026-06-25_ethan_runs_backup_inventory.json`
- `operational_notes/06-26/25/2026-06-25_ethan_runs_backup_plan.md`
- `tools/publish/rsync_ethan_runs_backup.sh`
- `tools/publish/submit_ethan_runs_backup_sbatch.sh`

## Observed output

- The requested backup destination root
  `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs`
  exists and was empty at the time of inspection.
- The current default backup payload is dominated by:
  - `jadyn_runs`: about `497G`
  - `tmp_extract`: about `163G`
  - `staging`: about `72G`
  - `reports`: about `1.3G`
  - `figures`: about `1.8G`
- The excluded-by-default `tmp/` tree is itself large at about `166G`.
- The measured default-scope payload is about `786,074,703,912` bytes
  (`732.1 GiB`) with an estimated `1,197,130` files.

## Interpretation

- A direct first backup pass is large enough that it should be treated as a
  real data-movement job, not a casual login-node copy.
- Defaulting to additive `rsync` without deletes is the safer backup contract:
  it moves only new or changed files while avoiding accidental cleanup of older
  backup-side content.
- A manifest-producing dry-run is sufficient to answer the user’s “what is new
  and what still needs to move” requirement without inventing a custom diff
  database.

## Contradictions and caveats

- `tmp/` may contain useful one-off scratch state for some investigations, but
  it is not included in the default backup because of its size and lower
  provenance value. The helper scripts keep `--include-tmp` available when that
  tradeoff changes.
- The current workspace already has active overlapping ownership in `reports/`
  and the main June 25 curated journal, so this task deliberately kept its
  durable documentation in `operational_notes/` plus `.agent/` records instead
  of opening another `reports/` package.

## Actions taken

- Claimed `AGENT-129` on the board with a narrow scope.
- Added `tools/publish/rsync_ethan_runs_backup.sh`.
- Added `tools/publish/submit_ethan_runs_backup_sbatch.sh`.
- Wrote the backup inventory JSON and the dated operational note.
- Validated both scripts locally with shell syntax checks and a small `/tmp`
  smoke tree.
- Created the real external backup skeleton under
  `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup`.
- Submitted the first real sync as Slurm job `3259225` on `NuclearEnergy`
  through `login3` because `sbatch` is not available from the current compute
  shell. Initial observed state: `PENDING (Resources)`.

## Suggested next actions

- The external backup root and README/manifests skeleton now exist under
  `/home1/.../cfd_runs/ethan_runs_backup/`.
- Monitor `3259225`, then review:
  - the Slurm stdout/stderr in
    `tmp/slurm_ethan_runs_backup_jobs/20260625T125336_sync/`
  - the final backup manifest at
    `/home1/.../cfd_runs/ethan_runs_backup/manifests/latest/summary.txt`

## 2026-06-29T12:56:19-05:00

## Observed output

- The backup mirror is no longer empty; representative top-level files now
  exist under:
  `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup/mirror/ethan_runs/`
- The backup root has history-manifest directories for at least two real sync
  attempts after the original submission:
  - `manifests/history/20260625T150303/`
  - `manifests/history/20260626T200016/`
- Those two runs wrote large sync logs:
  - `20260625T150303/rsync_sync.log`: `874123` lines
  - `20260626T200016/rsync_sync.log`: `709036` lines
- `manifests/latest/` still contains only `backup_scope.txt`; it does not yet
  have the expected final `summary.txt`, `new_files.txt`, `changed_files.txt`,
  or `rsync_plan.log`.
- Slurm/job evidence reviewed:
  - `3259225`: first sync launcher ran the backup script
  - `3259614`: later sync attempt timed out
  - `3261333`: later sync attempt continued deep into the tree but ended with
    rsync warning code `24` because live case files vanished during transfer

## Interpretation

- The backup workflow itself is built and the backup mirror has progressed, but
  the lane is not cleanly closed.
- The remaining problem is no longer “does the sync launch”; it is “how do we
  produce a clean latest-manifest state while the source tree is still moving.”

## Suggested next actions

- Rerun a narrower incremental sync or plan pass that refreshes
  `manifests/latest/` explicitly.
- Decide whether actively mutating run directories need temporary exclusions or
  whether rsync warning code `24` is acceptable for the backup contract as long
  as a later incremental pass stabilizes the mirror.

## 2026-06-29T13:30:52-05:00

## Observed output

- Updated `tools/publish/rsync_ethan_runs_backup.sh` so live-tree backup passes
  can run as one rsync per top-level included directory via
  `--top-level-pass`.
- Updated the same helper so it records `rsync_status.txt` and treats rsync
  exit code `24` as a non-fatal vanished-file warning.
- Updated `tools/publish/submit_ethan_runs_backup_sbatch.sh` to accept
  `--begin` and forward `--top-level-pass`.
- Dry-run submission generated the expected `#SBATCH --begin=2026-06-29T20:00:00`
  and `#SBATCH -t 11:30:00` directives.
- Submitted a new overnight incremental sync on `login3`:
  - job id: `3265388`
  - scheduled start: `2026-06-29T20:00:00` CDT
  - walltime: `11:30:00`
  - expected end window: `2026-06-30T07:30:00` CDT
  - script:
    `tmp/slurm_ethan_runs_backup_jobs/20260629T133052_sync/ethan_backup_sync.sbatch`
- Queue check showed:
  - state: `PENDING`
  - reason: `BeginTime`

## Interpretation

- The new approach does not make changing files stop changing, but it prevents
  one volatile subtree from aborting the whole workspace copy.
- The overnight rerun is now aligned with the requested quiet window and should
  preserve useful progress across stable top-level trees even if active case
  directories continue mutating.
