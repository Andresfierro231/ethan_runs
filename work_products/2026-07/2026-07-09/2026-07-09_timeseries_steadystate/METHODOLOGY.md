# Methodology — statistics & steady-state criteria (AGENT-244)

All statistics are computed on the **analysis window**: the samples whose
simulated time is within the last 300 s of the run
(`t ≥ t_end − 300`). Implementation: `tools/analyze/timeseries_stats.py`
(pure Python; auditable).

## Linear trend (OLS)
Fit `y = a·t + b` by ordinary least squares.
- slope `a`, intercept `b`.
- `R² = 1 − SS_res/SS_tot`.
- slope standard error `se_a = sqrt( (SS_res/(n−2)) / Σ(t−t̄)² )`.
- slope t-statistic `t = a / se_a` (|t| > 3.0 → a statistically
  resolved trend; note the autocorrelation caveat below makes this optimistic).

## Oscillation / RMSE / variance
- `mean` = time-average over the window.
- **RMSE about the mean** = `sqrt( mean( (y−ȳ)² ) )` = the population standard
  deviation = RMS fluctuation amplitude. Its square is the **variance about the
  mean**.
- **RMSE about the trend** = `sqrt( mean( (y − (a·t+b))² ) )` = the *detrended*
  oscillation amplitude (removes any linear drift). Its square is the variance
  about the trend. Comparing the two RMSEs separates drift from oscillation.
- peak-to-peak = max − min; coefficient of variation `CoV = std/|mean|`.

## Autocorrelation & effective sample size
CFD samples are correlated in time, so naive statistics overstate confidence.
- Integrated autocorrelation time `τ_int = 1 + 2 Σ_k ρ_k`, summing the
  autocorrelation of the detrended residuals until the first non-positive ρ_k
  (initial-positive-sequence truncation).
- Effective independent samples `N_eff = N / τ_int`.

## Uncertainty of the mean (Central Limit Theorem)
- **Naive** standard error of the mean `SEM = σ/√N` — the textbook CLT result
  assuming independent samples; scales as 1/√N ∝ 1/√t at fixed sample rate.
- **Autocorrelation-corrected** `SEM = σ/√N_eff = σ·√(τ_int/N)` — the honest
  uncertainty for correlated CFD data.
- **Relative SEM** = SEM/|mean| compares the uncertainty to the average value.
- The `mdot_sem_convergence.svg` figure plots the running `σ(window)/√N` against
  averaging duration on log-log axes with a `σ_full/√t` reference line; a slope
  of −1/2 confirms CLT scaling.

## Steady-state verdict (advisory thresholds)
The verdict uses a **scale-free** primary metric so it stays valid when the mean
is near zero (e.g. net heat oscillating about ~0, where relative-to-mean drift
would explode):

- `drift_ratio = |a·W| / (RMSE about trend)` — the trend's total change across the
  window W = 300 s, measured in units of the oscillation amplitude.
- `rel_drift = |a·W| / |mean|` — used only when the mean is well separated from
  zero (`|mean| > 3·std`); otherwise reported as NaN and the row is
  flagged `near_zero_mean`.

Decision — two branches:

*When the mean is well separated from zero* (`|mean| > 3·std`,
the usual case for mdot, temperature, and non-zero heat) judge drift by physical
significance relative to the mean:
- **not steady**: `rel_drift > 0.02`.
- **steady**: `rel_drift < 0.005` and `CoV < 0.01`.
- **quasi-steady**: in between.

*When the mean is near zero* (`near_zero_mean`, e.g. net heat about ~0, where
relative-to-mean drift is meaningless) judge by the scale-free `drift_ratio`:
- **not steady**: `drift_ratio > 3`.
- **steady**: `drift_ratio < 1`.
- **quasi-steady**: in between.

`trend_resolved` (= `drift_ratio > 3`) marks a drift that
stands clear of the oscillation band — note a drift can be statistically resolved
yet physically tiny (small vs a large mean), which correctly reads "quasi-steady".
Thresholds are explicit constants in `timeseries_stats.py`; the verdict is a
screening aid, not a physical certification.
