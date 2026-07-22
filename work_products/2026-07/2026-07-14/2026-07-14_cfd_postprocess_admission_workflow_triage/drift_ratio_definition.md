---
provenance:
  - work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/METHODOLOGY.md
tags: [cfd-pp, steady-state, drift-ratio]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_steady_state_table.csv
task: AGENT-347
date: 2026-07-14
role: cfd-pp / Writer
type: work_product
status: complete
---
# Drift Ratio Definition

`ratio` in the drift-severity context refers to:

```text
drift_ratio = |a * W| / RMSE_about_trend
```

where `a` is the ordinary-least-squares slope over the analysis window, `W` is
the window duration, and `RMSE_about_trend` is the detrended oscillation
amplitude.

Interpretation: it measures how much the fitted trend changes across the window
in units of the case's own oscillation amplitude. The detector uses it mainly
when the mean is near zero and relative drift against the mean would be
misleading. In the July 9 methodology, `drift_ratio < 1` is steady,
`drift_ratio > 3` is not steady, and intermediate values are quasi-steady for
near-zero-mean series.
