# AGENT-153 Raw Notes

Date: `2026-06-30`
Role: `Coordinator / Writer`
Task ID: `AGENT-153`

## Scope

- `.agent/BOARD.md`
- `.agent/status/2026-06-30_AGENT-153.md`
- `.agent/journal/2026-06-30/coordinator-writer-beginning-of-day-job-recap.md`
- `journals/2026-06/2026-06-30_ethan_runs.md`

## Sources used

- `operational_notes/06-26/26/2026-06-26_nuclearenergy_repack_followon.md`
- `.agent/status/2026-06-25_AGENT-129.md`
- `.agent/status/2026-06-29_AGENT-152.md`
- `.agent/journal/2026-06-23/coordinator-implementer-writer-latest-window-frozen-state-refresh.md`
- `journals/2026-06/2026-06-29_ethan_runs.md`
- `tmp/slurm_ethan_runs_backup_jobs/20260629T133052_sync/slurm-3265388.{out,err}`
- `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/logs/lw_finalize-3265734.{out,err}`
- `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/logs/salt4_cont_full_3265733.{out,err}`
- `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup/manifests/latest/{summary.txt,rsync_status.txt}`
- `sacct` and `squeue` snapshots collected on `2026-06-30T10:00:00-05:00`

## Observed output

- June 29 scheduler history relevant to current campaign operations:
  - `3265388` `ethan_backup_sync`: `COMPLETED`
  - `3265678` `lw_s234_smoke`: Slurm `COMPLETED`, but this first smoke launch
    is documented as a broken interpreter run
  - `3265684` `lw_s234_smoke`: `COMPLETED`
  - `3265733` `lw_s234_full`: `COMPLETED`
  - `3265734` `lw_finalize`: `TIMEOUT`
  - `3265969-3265972` corrected `NuclearEnergy` packs: started on
    `2026-06-29T17:18:26-05:00` and are still `RUNNING`
- The backup follow-up is no longer blocked on missing latest manifests:
  `manifests/latest/summary.txt`, `rsync_status.txt`, `new_files.txt`,
  `changed_files.txt`, and `rsync_sync.log` all exist after `3265388`.
- Backup summary counts from the latest manifest:
  - `184439` new files
  - `694` changed files
  - `58611` created directories
  - `66` symlink updates
  - top-level status is `ok` for every tracked tree except `jadyn_runs`,
    which is `ok_with_vanished_files` with rsync code `24`
- The latest-window smoke path has one failed and one fixed launch:
  - `3265678` failed immediately after `of13-env.sh` changed `python` to a
    broken interpreter missing `libpython3.9.so.1.0`
  - `3265684` then ran successfully and wrote full smoke outputs for
    `salt2_cont`, `salt3_cont`, and `salt4_cont`
- The latest-window full refresh `3265733` is only partially good:
  - `salt2_cont`: `22` top-level output files
  - `salt3_cont`: `22` top-level output files
  - `salt4_cont`: only `analysis_manifest.json` plus `raw_extraction/`
- The Salt 4 full-refresh logs show two concrete failure signatures:
  - OpenFOAM fatal IO while reading retained `T` files under
    `tmp_extract/ethan_streamwise_friction/.../8110-8123/T`
  - missing boundary-layer landmark outputs for
    `left_lower_leg_anchor_TW7` at retained time `8120`
- `3265734` then timed out after one hour. Its log still shows repeated Salt 4
  OpenFOAM fatal IO while reading retained `T` fields.
- The downstream normal-queue jobs are stuck behind the failed finalize step:
  - `3265892` `lw_promote`: `PENDING (DependencyNeverSatisfied)`
  - `3265893` `lw_promote`: `PENDING (DependencyNeverSatisfied)`
  - `3265894` `lw_bakeoff`: `PENDING (Dependency)`
  - `3265895` `lw_1d_val`: `PENDING (Dependency)`
  - `3265896` `lw_discrep`: `PENDING (Dependency)`
- The June 26 mispacked `NuclearEnergy` jobs `3261320-3261323` were already
  canceled on June 29 and replaced by single-node jobs `3265969-3265972`.

## Inferred interpretation

- The backup lane is now operationally healthy enough for beginning-of-day
  purposes. It still sees live-tree churn in `jadyn_runs`, but it no longer
  needs an immediate resubmission just to produce the latest manifest set.
- The latest-window lane is the main blocker. The scheduler-only view is
  misleading because `3265733` says `COMPLETED` even though the Salt 4 branch
  failed badly enough to poison the downstream finalize/publish chain.
- The four corrected single-node continuation packs are the main live CFD
  workload this morning; they do not currently need resubmission.

## Contradictions / caveats

- `3265678` appears as `COMPLETED` in Slurm accounting even though the raw note
  documents it as a failed smoke attempt. The classification here follows the
  emitted campaign note rather than the bare Slurm state.
- `3265734` is recorded by Slurm as a timeout, but the logs show real upstream
  Salt 4 data/extractor failures in addition to the walltime limit.
- Two promote jobs exist in the queue (`3265892` and `3265893`). The campaign
  note only documented `3265893`; both are currently dead dependency holders.

## Recommended next actions

- Keep the running corrected `NuclearEnergy` jobs `3265969-3265972` in place
  and recheck solver health later rather than resubmitting them again now.
- Treat the latest-window chain as needing a targeted repair plus rerun:
  repair or bypass the Salt 4 retained-time extractor/input failure, rerun the
  finalize step, then submit a clean replacement for `3265892-3265896`.
- Leave the backup lane alone unless a cleaner `jadyn_runs` pass is needed.
  The latest manifest now exists, and rsync code `24` is already accounted for
  in the recorded status file.
