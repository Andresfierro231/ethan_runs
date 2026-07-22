# Time-Series Uncertainty Story

Task: `AGENT-272`  
Presentation table addendum: `AGENT-273`  
Documentation polish: `AGENT-275`  
Source: `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv`

This package turns the AGENT-244 steady-state time-series metrics into
paper-facing uncertainty components for considered steady/quasi-steady CFD
solutions.

## Start Here

For the next presentation, start with:

- `presentation_salt234_timeseries_uncertainty.md` for a slide-readable table.
- `presentation_salt234_timeseries_uncertainty.csv` for spreadsheet cleanup or
  plotting.

For paper methods and uncertainty provenance, start with:

- `uncertainty_components_steady_or_quasi.csv` for the full steady/quasi
  component table.
- `screened_out_not_steady_or_live.csv` for rows intentionally excluded from
  uncertainty use.
- `summary.json` for counts, source path, and policy metadata.

## Recommended Use

- `osc_mean`: best estimate of the steady-window mean.
- `unc_sem_corrected`: autocorrelation-corrected standard error of that mean.
- `unc_rel_sem_corrected`: relative SEM from the source package.
- `osc_rmse_about_trend`: detrended oscillation amplitude; use as the
  persistent time-variation component after drift removal.
- `fit_slope`: residual drift rate. This package also reports
  `drift_over_window = fit_slope * (t_end - t_start)`.
- `verdict`: screen. Use `steady` directly and use `quasi-steady...` with a
  caveat. Rows with `not steady...` or live/active slugs are screened out.

The derived `paper_envelope_abs` is a conservative display bound:

```text
1.96 * unc_sem_corrected + osc_rmse_about_trend + 0.5 * abs(drift_over_window)
```

It is not a formal confidence interval; the paper methods should report the
components separately when precision matters.

## Reusable Script

Primary script:

```bash
python3.11 tools/analyze/build_time_series_uncertainty_story.py
```

Useful variants:

```bash
# Regenerate this package from the default AGENT-244 source.
python3.11 tools/analyze/build_time_series_uncertainty_story.py

# Smoke-test into /tmp without touching the dated package.
python3.11 tools/analyze/build_time_series_uncertainty_story.py \
  --output-dir /tmp/time_series_uncertainty_story_smoke

# Reuse against a refreshed steady-state summary.
python3.11 tools/analyze/build_time_series_uncertainty_story.py \
  --input path/to/steady_state_summary.csv \
  --output-dir work_products/2026-07/2026-07-XX/your_package_name
```

Validation:

```bash
python3.11 -m py_compile \
  tools/analyze/build_time_series_uncertainty_story.py \
  tools/analyze/test_time_series_uncertainty_story.py
python3.11 tools/analyze/test_time_series_uncertainty_story.py
```

## Input Contract

The input CSV must contain AGENT-244-style columns including:

- identity: `case_slug`, `fluid`, `group`, `series`, `unit`
- window: `n_window`, `t_start`, `t_end`
- screen: `verdict`, `near_zero_mean`, `trend_resolved`
- values: `osc_mean`, `osc_rmse_about_trend`, `fit_slope`,
  `unc_sem_corrected`, `unc_rel_sem_corrected`

The script does not read native OpenFOAM fields or mutate solver outputs.

## Output Contract

The generated tables are:

- full component rows: `uncertainty_components_steady_or_quasi.csv`
- screened rows: `screened_out_not_steady_or_live.csv`
- mainline component rows: `mainline_salt234_uncertainty_components.csv`
- compact paper bounds: `paper_uncertainty_bounds_salt234.csv`
- presentation table: `presentation_salt234_timeseries_uncertainty.csv`
- presentation Markdown: `presentation_salt234_timeseries_uncertainty.md`

## Outputs

- `uncertainty_components_steady_or_quasi.csv`: all terminal/non-live rows whose
  verdict is steady or quasi-steady, preserving the requested AGENT-244 metric
  names plus derived bound columns.
- `mainline_salt234_uncertainty_components.csv`: steady/quasi component rows
  for the current mainline Salt2/3/4 Jin continuations.
- `paper_uncertainty_bounds_salt234.csv`: compact case-level table for Salt2/3/4.
- `presentation_salt234_timeseries_uncertainty.csv`: compact presentation rows
  for admitted Salt2/3/4 mdot, six temperature probes, wall temperature, and
  total_Q residual.
- `presentation_salt234_timeseries_uncertainty.md`: Markdown rendering of the
  same presentation table.
- `screened_out_not_steady_or_live.csv`: rows excluded from uncertainty use and
  the reason.
- `summary.json`: counts and provenance.

## Counts

- input rows: `415`
- uncertainty-usable rows: `345`
- screened rows: `70`
- mainline Salt2/3/4 component rows: `25`
- compact Salt2/3/4 case rows: `3`
- Salt2/3/4 presentation rows: `27`

For `total_Q`, use absolute W components only when the row passes the verdict
screen; it is a near-zero net residual, so relative uncertainty can look large
even when the absolute residual is physically small.
