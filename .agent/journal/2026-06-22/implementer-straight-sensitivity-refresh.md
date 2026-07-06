# AGENT-104 Raw Journal — Straight Sensitivity Refresh

## 2026-06-22

- Confirmed the original `AGENT-104` dependency is no longer "wait for jobs to
  finish" in the literal sense. The packed Salt continuation node
  `3250777` is still live, but the continuation roots already preserve full
  `21`-time tails, which is enough to freeze the current latest state and treat
  it as pseudo-steady for the straight refresh.
- Read:
  - `reports/2026-06-22_ethan_corrected_continuation_relaunch/README.md`
  - `reports/2026-06-22_ethan_packed_continuation_and_salt_wave/README.md`
  - `reports/2026-06-19_ethan_salt_straight_hydraulic_sensitivity/README.md`
  - `tools/analyze/build_ethan_case_analysis_package.py`
  - `tools/analyze/build_ethan_case_heat_summary.py`
  - `tools/analyze/build_ethan_salt_straight_hydraulic_sensitivity.py`
  - `tools/analyze/ethan_salt_hardening_common.py`
- Measured current retained tails from the packed Salt continuation roots:
  - Salt 2 Jin continuation: `5008-5028 s`
  - Salt 3 Jin continuation: `4927-4947 s`
  - Salt 4 Jin continuation: `7794-7814 s`
- Added the minimum code needed to consume continuation-frozen state without
  mutating the old package registry:
  - runtime-root override in the case-analysis and heat-summary builders
  - package-root override support in the straight-sensitivity builder
- Validation after the code patch:
  - `python -m py_compile tools/analyze/build_ethan_case_heat_summary.py tools/analyze/build_ethan_case_analysis_package.py tools/analyze/ethan_salt_hardening_common.py tools/analyze/build_ethan_salt_straight_hydraulic_sensitivity.py tools/analyze/test_ethan_closure_modeling_v3.py`
  - `python -m unittest tools.analyze.test_ethan_closure_modeling_v3 -q`
- Started the first continuation-based package rebuild:
  - `python -m tools.analyze.build_ethan_case_analysis_package --source-id viscosity_screening_salt_test_2_jin_coarse_mesh --runtime-root jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation --last-n-times 21 --output-dir tmp/2026-06-22_salt_continuation_case_analysis_refresh/viscosity_screening_salt_test_2_jin_coarse_mesh`
- Also launched the parallel Salt 3 and Salt 4 refreshes with the same
  `--last-n-times 21` pattern under the same dated temp root.
- Added and launched a watcher/orchestrator:
  - `tools/analyze/run_ethan_straight_sensitivity_refresh_from_continuations.py`
  - active command:
    `python -m tools.analyze.run_ethan_straight_sensitivity_refresh_from_continuations`
  - purpose:
    wait until the three refreshed package roots emit
    `major_loss_cumulative_timeseries.csv` plus
    `leg_centerline_station_definitions.csv`, then run the scoped
    straight-sensitivity refresh automatically with source IDs limited to
    `salt2_jin`, `salt3_jin`, and `salt4_jin`.
- Question retained for the results report:
  - If the late-window rebuild changes only the blocker status and not the
    defended row set, the report should say that explicitly rather than implying
    the friction closure itself moved.

## 2026-06-23 closeout

- The late-window rebuild did change the defended straight subset.
- Preserved retained windows now used in the refresh package:
  - Salt 2 Jin: `5009-5029 s`
  - Salt 3 Jin: `4931-4951 s`
  - Salt 4 Jin: `7797-7817 s`
- Final straight refresh result:
  - case-mean defended rows: `5`
  - late-window defended rows: `4`
  - dropped relative to case-mean defended set:
    `Salt 3 Jin / lower_leg`
  - exclusion reason:
    `support_fraction_below_floor`
- The straight refresh report root now has package-level `README.md` and
  `summary.json`, and the frozen-state package now points at this June 22
  refresh instead of the older June 19 straight package.
