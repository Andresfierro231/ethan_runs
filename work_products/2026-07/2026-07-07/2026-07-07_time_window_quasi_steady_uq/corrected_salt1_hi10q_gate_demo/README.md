# Time-Window Quasi-Steady UQ

Generated: `2026-07-07T17:43:57-05:00`

## Objective

Curate time-dependent CFD monitor histories into quasi-steady observations with explicit uncertainty, window-state labels, fit-use controls, and independence groups. Raw transient samples are not independent closure training rows.

## Method

- Candidate trailing windows are evaluated for each QOI.
- Drift is measured by a linear fit over the window.
- Random uncertainty uses an autocorrelation-corrected effective sample size.
- Block means and a robust oscillation envelope are reported separately.
- The total temporal uncertainty is conservative: random, drift, and the larger of block or oscillation components are combined by root-sum-square.
- Persistent oscillation is treated as a non-shrinking uncertainty floor.
- Multiple windows from the same relaxation path share one `independence_group_id`.
- Corrected Salt / special-gate rows are not closure-fit admissible until coordinator review.

## Outputs

- `quasi_steady_observations.csv`: primary window per case/QOI.
- `window_diagnostics.csv`: all evaluated candidate windows.
- `excluded_or_provisional_windows.csv`: non-admitted primary rows.
- `run_window_summary.json`: machine-readable summary and recommendation.

## Recommendation

hold/investigate: coordinator review required for special-gate rows

## Raw Observations vs Interpretation

Raw observations are the computed window statistics in the CSV/JSON outputs. Interpretation is limited to the explicit `window_state`, `fit_use_status`, `needs_special_gate_scrutiny`, and recommendation fields. Passing through a target while drifting is not treated as equilibrium evidence.
