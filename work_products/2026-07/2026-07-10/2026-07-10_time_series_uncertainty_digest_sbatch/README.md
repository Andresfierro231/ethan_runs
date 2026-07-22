# Time-Series Uncertainty Digest

This package condenses the AGENT-244 time-series steady-state statistics into
presentation-usable uncertainty tables. It excludes currently live or active
case keys: Salt1 nominal continuation and selected corrected-Q continuation
rows under jobs `3282992` and `3288671`.

## Outputs

- `uncertainty_digest_all_terminal_cases.csv`: all non-live series rows.
- `uncertainty_digest_admitted_mainline_salt234.csv`: Salt2/3/4 mainline rows.
- `presentation_uncertainty_summary_salt234.csv`: one compact row per admitted mainline Salt case.
- `excluded_live_or_active_cases.csv`: rows intentionally excluded because they are live/active.
- `summary.json`: row counts and verdict summaries.

Use autocorrelation-corrected SEM for uncertainty bounds. For `total_Q`, use
absolute W values because it is a near-zero net heat residual.
