# AGENT-154 Raw Notes

Date: `2026-06-30`
Role: `Coordinator / Implementer`
Task ID: `AGENT-154`

## Scope

- `.agent/BOARD.md`
- `.agent/status/2026-06-30_AGENT-154.md`
- `.agent/journal/2026-06-30/coordinator-implementer-resubmit-unmet-dependency-chain.md`
- `journals/2026-06/2026-06-30_ethan_runs.md`

## Starting point

- Dead dependency jobs in queue at open:
  - `3265892` `lw_promote`
  - `3265893` `lw_promote`
  - `3265894` `lw_bakeoff`
  - `3265895` `lw_1d_val`
  - `3265896` `lw_discrep`
- Existing tracked wrappers to reuse:
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/latest_window_finalize_from_parallel_full.sbatch`
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/latest_window_promote_parallel_full.sbatch`
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/latest_window_validation_latest_window.sbatch`
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/latest_window_bakeoff_latest_window.sbatch`
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/latest_window_discrepancy_latest_window.sbatch`

## Immediate caveat

- The earlier `3265734` finalize job timed out after real Salt 4 extractor /
  OpenFOAM retained-time failures. The first replacement chain was therefore
  premature and had to be withdrawn once the upstream fault was confirmed.

## Actions taken

- Confirmed the tracked wrappers all pass `bash -n`.
- Canceled the stale dependency-held jobs:
  - `3265892`
  - `3265893`
  - `3265894`
  - `3265895`
  - `3265896`
- Submitted an initial replacement chain:
  - `3267252` `lw_finalize`
  - `3267253` `lw_promote` dependent on `3267252`
  - `3267254` `lw_1d_val` dependent on `3267253`
  - `3267255` `lw_bakeoff` dependent on `3267253`
  - `3267256` `lw_discrep` dependent on `3267254:3267255`
- The first remote submit attempt also left an extra standalone finalize job
  `3267251`; canceled it.
- After AGENT-155 fixed the Salt 4 sanitization/cache fault, canceled the
  premature `3267251-3267256` set so the queue would not continue from broken
  upstream data.
- Submitted the repaired full-to-publish chain:
  - `3267436` `lw_s234_full`
  - `3267437` `lw_finalize` dependent on `3267436`
  - `3267438` `lw_promote` dependent on `3267437`
  - `3267439` `lw_1d_val` dependent on `3267438`
  - `3267440` `lw_bakeoff` dependent on `3267438`
  - `3267441` `lw_discrep` dependent on `3267439:3267440`
- `squeue --start` then estimated `3267436` would not begin until
  `2026-07-01T08:21:51-05:00`, roughly 21 hours out.
- Confirmed this Codex session is already inside active allocation `3267228`
  on compute node `c318-008` (`NuclearEnergy-dev`) with more than four days of
  walltime remaining, so waiting on the queued `NuclearEnergy` slot was not
  necessary.
- Canceled the queued repaired chain `3267436-3267441`.
- Found the earlier local Salt 4 rebuild was still legitimately running on the
  current compute node.
- Started detached `tmux` continuation session
  `lw_local_chain_20260630T113922` to wait for that Salt 4 rebuild and then
  run:
  - `latest_window_finalize_from_parallel_full.sbatch`
  - `latest_window_promote_parallel_full.sbatch`
  - `latest_window_validation_latest_window.sbatch`
  - `latest_window_bakeoff_latest_window.sbatch`
  - `latest_window_discrepancy_latest_window.sbatch`
- Continuation log:
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/logs/local_post_salt4_chain_20260630T113922.out`

## Queue state after cleanup

- Active repaired chain:
  - queued replacement path `3267436-3267441`: canceled intentionally
  - active local path:
    - Salt 4 rebuild already running on `c318-008`
    - detached `tmux` continuation `lw_local_chain_20260630T113922`
- Confirmed `3267251-3267256` are gone from `squeue`.
- Confirmed the old dead-dependency jobs `3265892-3265896` are gone from
  `squeue`.
