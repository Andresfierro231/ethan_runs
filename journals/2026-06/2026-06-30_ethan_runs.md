# 2026-06-30 Ethan Runs

## beginning-of-day

Checkpoint taken at `2026-06-30T10:00:00-05:00` from `sacct`, `squeue`,
`operational_notes/06-26/26/2026-06-26_nuclearenergy_repack_followon.md`,
`.agent/status/2026-06-25_AGENT-129.md`,
`.agent/status/2026-06-29_AGENT-152.md`,
`.agent/journal/2026-06-23/coordinator-implementer-writer-latest-window-frozen-state-refresh.md`,
the backup manifest under
`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup/manifests/latest/`,
and the emitted latest-window / backup Slurm logs.

### Observed output

- Completed successfully:
  - `3265388` `ethan_backup_sync`
    - finished `2026-06-30T00:30:30-05:00`
    - wrote `manifests/latest/summary.txt`, `rsync_status.txt`,
      `new_files.txt`, and `changed_files.txt`
    - latest manifest counts: `184439` new files, `694` changed files,
      `58611` created directories, `66` symlink updates
    - per-top-level status is clean except `jadyn_runs`, which is recorded as
      `ok_with_vanished_files` with rsync warning code `24`
  - `3265684` `lw_s234_smoke`
    - corrected smoke refresh for `salt2_cont`, `salt3_cont`, and
      `salt4_cont`
    - raw note reports all three smoke outputs landed cleanly

- Ran and are still active:
  - `3265969` `ethan_s34mid_ne5d`
  - `3265970` `ethan_w1234_ne5d`
  - `3265971` `ethan_s41lo2mid_ne5d`
  - `3265972` `ethan_s123hi_ne5d`
    - all four are the corrected June 29 single-node replacements for the
      older two-node mispacked jobs `3261320-3261323`
    - live `squeue` now shows each on `1` node

- Ran but failed or only partially succeeded:
  - `3265678` `lw_s234_smoke`
    - first smoke attempt
    - campaign note says all three packed lanes failed immediately because
      sourcing `of13-env.sh` switched `python` to a broken interpreter missing
      `libpython3.9.so.1.0`
    - no action needed now because `3265684` already replaced it successfully
  - `3265733` `lw_s234_full`
    - Slurm state is `COMPLETED`, but the payload is only partially good
    - `salt2_cont` and `salt3_cont` wrote full output sets
    - `salt4_cont` only left `analysis_manifest.json` plus partial raw
      extraction
    - Salt 4 logs show:
      - OpenFOAM fatal IO while reading retained `T` fields under
        `tmp_extract/ethan_streamwise_friction/...`
      - missing boundary-layer landmark outputs for
        `left_lower_leg_anchor_TW7` at retained time `8120`
  - `3265734` `lw_finalize`
    - timed out at `2026-06-29T23:10:46-05:00`
    - the log still shows repeated Salt 4 OpenFOAM fatal IO while reading
      retained `T` fields, so this was not just a pure queue-walltime issue

- Pending this morning:
  - `3265892` `lw_promote`: `DependencyNeverSatisfied`
  - `3265893` `lw_promote`: `DependencyNeverSatisfied`
  - `3265894` `lw_bakeoff`: `Dependency`
  - `3265895` `lw_1d_val`: `Dependency`
  - `3265896` `lw_discrep`: `Dependency`

### Inferred interpretation

- The backup lane is no longer the main operational blocker. It completed its
  overnight pass and produced the missing latest-manifest files, with only the
  expected live-tree rsync code `24` noise in `jadyn_runs`.
- The main beginning-of-day problem is the latest-window chain. The scheduler
  alone makes it look healthier than it is because `3265733` says
  `COMPLETED`, but Salt 4 failed badly enough that `3265734` never had a clean
  aggregate to finish from.
- The corrected single-node `NuclearEnergy` continuation packs are the main
  live CFD jobs this morning and do not currently need another resubmission.

### Contradictions / caveats

- `3265678` appears as `COMPLETED` in Slurm accounting, but the campaign raw
  note documents it as a failed smoke attempt. This recap follows the emitted
  job-note interpretation rather than the bare Slurm state.
- `3265734` is classified by Slurm as `TIMEOUT`, but the logs show upstream
  Salt 4 data/extractor failures as the real reason the finalize stage was not
  converging cleanly.

### Jobs that need resubmission

- No immediate resubmission is needed for the backup lane or the corrected
  running `NuclearEnergy` packs `3265969-3265972`.
- The latest-window finalize/publish chain does need a targeted resubmission,
  but only after the Salt 4 retained-time failure is repaired or explicitly
  bypassed:
  - rerun the finalize step that failed as `3265734`
  - then replace the stale dependency-held downstream jobs
    `3265892-3265896` with a clean new chain

### Follow-up at `2026-06-30T10:00:00-05:00`

- Cleaned the stale latest-window jobs whose dependencies were never going to
  clear:
  - canceled `3265892-3265896`
- Resubmitted the chain from the tracked sbatch wrappers on `login3`:
  - `3267252` `lw_finalize`
  - `3267253` `lw_promote`
  - `3267254` `lw_1d_val`
  - `3267255` `lw_bakeoff`
  - `3267256` `lw_discrep`
- One duplicate standalone finalize submit (`3267251`) was created during the
  first noisy remote submission attempt and was then canceled.
- Current queue state:
  - `3267252` is now waiting on ordinary queue `Priority`
  - `3267253-3267256` are waiting on the expected new dependencies
- Caveat remains unchanged: this queue cleanup/resubmission does not fix the
  underlying Salt 4 retained-time failure that showed up in the earlier
  `3265733/3265734` path.

### Follow-up at `2026-06-30T11:15:00-05:00`

- Fixed the Salt 4 retained-time root cause in
  `tools/extract/sample_leg_centerline_major_loss.py`:
  - the extractor had been reusing a stale
    `thermal_sanitization_summary.json` and skipping a fresh scan of retained
    reconstructed `T` fields
  - the fix now always rescans the selected retained times and rewrites the
    sanitization summary
- Quarantined the stale Salt 4 streamwise-friction cache root:
  - moved
    `tmp_extract/ethan_streamwise_friction/viscosity_screening_salt_test_4_jin_coarse_mesh/ad9ca25a2259410c`
    to
    `tmp_extract/ethan_streamwise_friction/viscosity_screening_salt_test_4_jin_coarse_mesh/ad9ca25a2259410c_stale_20260630T100000`
- Partial local validation confirmed the repaired `foamPostProcess` path
  advanced through retained times `8104-8106` without reproducing the earlier
  fatal Salt 4 `T`-field read. That local run was then stopped so the repaired
  queued rebuild could reuse the same cache path without collision.
- Canceled the premature replacement chain `3267251-3267256`.
- Submitted the repaired full latest-window chain:
  - `3267436` `lw_s234_full`
  - `3267437` `lw_finalize`
  - `3267438` `lw_promote`
  - `3267439` `lw_1d_val`
  - `3267440` `lw_bakeoff`
  - `3267441` `lw_discrep`
- Queue state immediately after submit:
  - `3267436`: `PENDING (Priority)` on `NuclearEnergy`
  - `3267437-3267441`: `PENDING (Dependency)` on the repaired upstream chain

### Follow-up at `2026-06-30T11:40:00-05:00`

- `squeue --start` projected queued job `3267436` would not start until
  `2026-07-01T08:21:51-05:00`, about 21 hours out.
- Verified this session is already inside active allocation `3267228` on
  compute node `c318-008` in `NuclearEnergy-dev`, with about 4 days of
  walltime remaining. That made a local compute-node continuation viable.
- Canceled the queued repaired chain `3267436-3267441`.
- Found the earlier local Salt 4 rebuild was still actively running on
  `c318-008`, so did not launch a duplicate Salt 4 worker.
- Started detached `tmux` session `lw_local_chain_20260630T113922` to wait for
  the live Salt 4 rebuild and then run the rest of the chain locally:
  - finalize
  - promote
  - validation and bakeoff in parallel
  - discrepancy
- Local continuation log:
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/logs/local_post_salt4_chain_20260630T113922.out`

### Follow-up at `2026-07-01T10:25:00-05:00`

- The older local continuation did not complete after allocation `3267228`
  ended; its log remained at `waiting_for_salt4_local_build`.
- A new active `NuclearEnergy-dev` allocation exists as `3269598` on
  `c318-008`, so the latest-window chain was restarted locally instead of
  waiting for a queued full-chain allocation.
- Added and launched:
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/run_local_latest_window_chain_20260701.sh`
- The new tmux-backed runner first reruns only the missing `salt4_cont` full
  package, then continues through finalize, promote, 1D validation, closure
  bakeoff, and discrepancy if Salt 4 succeeds.
- Main live log:
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/logs/local_latest_window_chain_20260701T102500.out`
- Salt 4 rerun logs:
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/logs/salt4_cont_full_local_20260701T102500.out`
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/logs/salt4_cont_full_local_20260701T102500.err`

### Follow-up at `2026-07-01T10:35:00-05:00`

- Postponed the OpenFOAM scaling study to preserve capacity for production CFD
  and ROM publication:
  - `3268028` `of_s2_scale`: canceled before start at
    `2026-07-01T10:29:57-05:00`
  - `3268024` `of_s2_opt`: canceled before start at
    `2026-07-01T10:29:57-05:00`
  - no scaling matrix completed; `results/job_3267228/*.csv` are header-only
    canceled-allocation artifacts
- Live production CFD packs still running:
  - `3265969` `ethan_s34mid_ne5d`
  - `3265970` `ethan_w1234_ne5d`
  - `3265971` `ethan_s41lo2mid_ne5d`
  - `3265972` `ethan_s123hi_ne5d`
- Lightweight monitor convergence checks were run read-only into
  `/tmp/ethan_convergence_check_20260701/`.
  - Salt cases checked stationary hydraulically and thermally.
  - Water 1/2/3 checked quasi-stationary hydraulically, stationary thermally.
  - Water 4 checked drifting/oscillatory hydraulically, stationary thermally.
- The local ROM latest-window chain is still active under allocation `3269598`;
  Salt 4 full-package rebuild is reducing cross-section thermal surfaces with
  no stderr at this checkpoint.
