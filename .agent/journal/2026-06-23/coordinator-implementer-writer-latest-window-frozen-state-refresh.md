# AGENT-121 Raw Journal — Latest-Window Frozen-State Refresh

- date: `2026-06-23`
- role: `Coordinator / Implementer / Writer`
- task ID: `AGENT-121`
- purpose:
  - rebuild the nominal Salt Jin case-analysis roots from the June 23 CFD
    checkpoint windows
  - promote those refreshed roots into a clearly dated frozen-state package
  - remove ambiguity with the older June 15 live-analysis package roots
- questions accumulating:
  - Should the presentation-facing narrative continue to cite the old June 23
    bakeoff package as a bounded surrogate until the latest-window retarget
    lands, or should that package be explicitly superseded in the report text?
  - Is the intended physical interpretation that all representative Salt Jin
    cases should be treated as globally `1.4 in` insulation, or only that the
    current best surrogate does not yet match the likely physical setup?
- progress notes:
  - The exact-time freeze path could not safely use
    `freeze_case_windows.csv` alone because `salt1_jin` rounds
    `3617.6625 -> 3617.66` and `3756.33125 -> 3756.33`. The orchestration
    builder now uses `representative_timesteps.csv` for exact processor labels
    and reserves `freeze_case_windows.csv` for window metadata only.
  - On `2026-06-26`, the builder defaults were corrected to the nested
    `reports/2026-06/2026-06-23/...` publication tree, and the import manifest
    path writer was fixed to record the actual `--checkpoint-root` argument
    instead of the stale default constant.
  - On `2026-06-29`, the nested case-analysis refresh path was patched to
    probe for a Python interpreter that can import `matplotlib` before
    launching `build_ethan_case_analysis_package.py`. This avoided the
    immediate `/usr/bin/python3.11` import failure on the current compute
    node, where plain `python` has the required plotting stack but
    `python3.11` does not.
  - The live refresh cleared `salt1_jin` and advanced into `salt2_cont`.
  - To avoid waiting on one serial lane, a packed parallel follow-on was
    staged under
    `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/`
    with two tracked sbatch files:
    - `latest_window_salt234_parallel_smoke.sbatch`
    - `latest_window_salt234_parallel_full.sbatch`
  - Important concurrency detail:
    - the packed jobs do not point directly at
      `tmp/2026-06-23_salt_last20_checkpoint/salt{2,3,4}_cont`
    - instead they use unique runtime-root symlink aliases under
      `parallel_jobs/runtime_aliases/`
    - this forces distinct snapshot keys so the packed jobs can coexist with
      the still-running serial builder without clobbering the same
      `tmp_extract/ethan_case_analysis_snapshots/**` roots
  - First smoke submission:
    - `3265678` on `NuclearEnergy-dev`
    - scheduler launch worked, but all three packed `srun` lanes failed
      immediately
    - root cause: sourcing `of13-env.sh` before the driver Python changed
      `python` to a broken interpreter that could not load
      `libpython3.9.so.1.0`
  - Fix:
    - packed sbatch scripts now launch the driver with `/usr/bin/python`
      without sourcing `of13-env.sh` first
    - this is safe because the case-analysis extractors already source the
      OpenFOAM 13 environment internally when they invoke `reconstructPar` and
      related utilities
  - Corrected smoke submission:
    - `3265684` on `NuclearEnergy-dev`
    - three packed case lanes started on one node `c318-009`
    - per-case logs showed real OpenFOAM reconstruction output instead of
      immediate launcher failure
    - final accounting:
      - `3265684|lw_s234_smoke|COMPLETED|00:10:55`
      - `3265684.0|bash|COMPLETED|00:10:53`
      - `3265684.1|bash|COMPLETED|00:10:53`
      - `3265684.2|bash|COMPLETED|00:10:52`
    - all three smoke roots wrote full one-time package outputs, including:
      - `parallel_jobs/outputs/smoke/salt2_cont/{summary.json,major_loss_summary.csv,branch_thermal_summary.csv,...}`
      - `parallel_jobs/outputs/smoke/salt3_cont/{summary.json,major_loss_summary.csv,branch_thermal_summary.csv,...}`
      - `parallel_jobs/outputs/smoke/salt4_cont/{summary.json,major_loss_summary.csv,branch_thermal_summary.csv,...}`
  - Overnight production submission:
    - stale broken `NuclearEnergy` submission `3265676` was removed from the
      live queue
    - first corrected overnight submission `3265688` was also canceled after
      the user changed the desired production window from midnight to `20:00`
    - current heavy overnight job:
      - `3265733` on `NuclearEnergy`
      - `BeginTime=2026-06-29T20:00:00`
      - walltime `12:00:00`
      - packed full `salt2/3/4` refresh on one node
    - current dependent finalize job:
      - `3265734` on `normal`
      - dependency `afterok:3265733`
      - runs `build_ethan_latest_window_frozen_state_stack.py --skip-case-refresh`
        against an assembled aggregate case root under
        `parallel_jobs/aggregate_case_analysis_root/`
      - writes the scheduled result bundle under
        `tmp/2026-06-23_ethan_frozen_state_results_latest_window_parallel_scheduled`
  - Chained post-processing submission:
    - added four follow-on sbatch launchers under
      `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/parallel_jobs/`:
      - `latest_window_promote_parallel_full.sbatch`
      - `latest_window_validation_latest_window.sbatch`
      - `latest_window_bakeoff_latest_window.sbatch`
      - `latest_window_discrepancy_latest_window.sbatch`
    - all four scripts pass `bash -n`
    - queued follow-on chain:
      - `3265893` on `normal`, dependency `afterok:3265734`
      - `3265895` on `normal`, dependency `afterok:3265893`
      - `3265894` on `normal`, dependency `afterok:3265893`
      - `3265896` on `normal`, dependency `afterok:3265895:3265894`
    - intent:
      - `3265893` promotes the scheduled tmp frozen-state output into the
        canonical latest-window report and import-manifest paths
      - `3265895` and `3265894` publish the latest-window local 1D validation
        and bakeoff surfaces in parallel
      - `3265896` publishes the latest-window discrepancy explainer after both
        local 1D packages land
