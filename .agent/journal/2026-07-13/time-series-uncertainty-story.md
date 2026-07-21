# Time-Series Uncertainty Story

Date: `2026-07-13`
Task: `AGENT-272`
Role: Coordinator / Implementer / Tester / Writer

## Prompt

The user identified the AGENT-244 `steady_state_summary.csv` as useful for the
paper uncertainty story and requested use of:

- `osc_mean`
- `osc_rmse_about_trend`
- `fit_slope`
- `unc_sem_corrected`
- `unc_rel_sem_corrected`
- `verdict`

## Implementation

Added `tools/analyze/build_time_series_uncertainty_story.py`.

The builder consumes:

- `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv`

It writes:

- `uncertainty_components_steady_or_quasi.csv`
- `mainline_salt234_uncertainty_components.csv`
- `paper_uncertainty_bounds_salt234.csv`
- `screened_out_not_steady_or_live.csv`
- `summary.json`
- `README.md`

Rows are uncertainty-usable only when they are not live/active and their verdict
is `steady` or starts with `quasi-steady`. Rows with `not steady...` verdicts
are kept in the screened table.

## Uncertainty Contract

- `osc_mean`: best estimate.
- `unc_sem_corrected`: autocorrelation-corrected SEM of the mean.
- `unc_rel_sem_corrected`: relative SEM from AGENT-244.
- `osc_rmse_about_trend`: oscillation component after removing linear drift.
- `fit_slope`: residual drift rate.
- `drift_over_window`: derived `fit_slope * (t_end - t_start)`.
- `paper_envelope_abs`: conservative display bound,
  `1.96*unc_sem_corrected + osc_rmse_about_trend + 0.5*abs(drift_over_window)`.

The display envelope is not a formal confidence interval; methods prose should
report the components separately.

## Results

- Input rows: `415`
- Uncertainty-usable rows: `345`
- Screened rows: `70`
- Mainline Salt2/3/4 component rows: `25`
- Compact Salt2/3/4 case rows: `3`

Mainline Salt2 and Salt3 `total_Q` rows are screened as not steady. Salt4
mainline `total_Q` passes the steady screen. Because `total_Q` is a near-zero
net residual, absolute W components are the only sensible paper-facing values
when it is used.

## Validation

- `python3.11 -m py_compile tools/analyze/build_time_series_uncertainty_story.py tools/analyze/test_time_series_uncertainty_story.py`
- `python3.11 tools/analyze/test_time_series_uncertainty_story.py`
- `python3.11 tools/analyze/build_time_series_uncertainty_story.py`

`pytest` was unavailable in the current environment, so the test module was run
directly with `unittest`.

## Boundaries

No solver outputs, registry files, scheduler state, or external Fluid files were
modified.
