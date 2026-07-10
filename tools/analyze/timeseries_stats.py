#!/usr/bin/env python3
"""timeseries_stats.py — steady-state / oscillation / CLT statistics (stdlib only).

Rigorous, dependency-free statistics for CFD postprocessor time series. Given a
time window (the "last N seconds" of simulated time), it computes:

  - Linear trend: OLS slope, intercept, R², slope standard error, t-statistic.
  - Oscillation: mean, RMS fluctuation about the mean (= population std), variance
    about the mean, RMSE about the linear trend (detrended), variance about the
    trend, peak-to-peak, coefficient of variation.
  - Autocorrelation: integrated autocorrelation time τ_int of the detrended
    residuals (initial-positive-sequence truncation).
  - Uncertainty of the mean (CLT): standard error of the mean, both the naive
    σ/√N (independent-sample CLT) and the autocorrelation-corrected σ/√N_eff with
    N_eff = N/τ_int; plus relative SEM (SEM/|mean|).
  - Running SEM vs averaging duration for the 1/√t convergence plot.
  - A steady-state verdict from explicit, documented thresholds.

Why both SEM forms: CFD time series are autocorrelated, so the naive σ/√N
under-estimates the true uncertainty of the time-average. τ_int quantifies the
inflation; N_eff = N/τ_int is the effective number of independent samples.

Everything is plain arithmetic on Python lists so it runs in a minimal shell.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

# Steady-state thresholds (explicit + documented; advisory, not a hard gate).
DRIFT_STEADY = 0.005     # |trend change over window| / |mean| below this → steady
DRIFT_QUASI = 0.02       # ... below this (but above STEADY) → quasi-steady
COV_STEADY = 0.01        # coefficient of variation below this supports "steady"
TSTAT_SIGNIF = 3.0       # |slope t-stat| above this → statistically resolved trend
# Scale-free drift criterion (robust when the mean is near zero — e.g. net heat
# oscillating about ~0, where relative-to-mean metrics blow up):
DRIFT_RATIO_STEADY = 1.0  # |trend change| < 1 oscillation amplitude → drift unresolved
DRIFT_RATIO_DRIFT = 3.0   # |trend change| > 3 oscillation amplitudes → clear drift
SNR_MEAN = 3.0            # mean is "well separated from zero" if |mean| > 3·std
MIN_WINDOW_POINTS = 5


@dataclass
class Fit:
    n: int
    slope: float
    intercept: float
    r2: float
    slope_se: float
    t_stat: float


@dataclass
class Oscillation:
    mean: float
    minimum: float
    maximum: float
    peak_to_peak: float
    rmse_about_mean: float     # == population std (RMS fluctuation about the mean)
    var_about_mean: float
    rmse_about_trend: float    # detrended RMS oscillation
    var_about_trend: float
    cov: float                 # std / |mean|


@dataclass
class Uncertainty:
    tau_int: float             # integrated autocorrelation time (samples)
    n_eff: float               # effective independent samples = n / tau_int
    sem_naive: float           # sigma / sqrt(n)   (independent-sample CLT)
    sem_corrected: float       # sigma / sqrt(n_eff) (autocorrelation-corrected)
    rel_sem_naive: float       # sem_naive / |mean|
    rel_sem_corrected: float   # sem_corrected / |mean|


@dataclass
class SeriesAnalysis:
    n_window: int
    t_start: float
    t_end: float
    dt_median: float
    window_seconds: float
    fit: Fit
    oscillation: Oscillation
    uncertainty: Uncertainty
    verdict: str
    rel_drift_over_window: float   # |trend change|/|mean| (NaN if mean≈0)
    drift_ratio: float             # |trend change|/oscillation amplitude (scale-free)
    near_zero_mean: bool           # |mean| not separated from zero → rel metrics unreliable
    trend_resolved: bool

    def flat(self) -> dict:
        d = {
            "n_window": self.n_window, "t_start": self.t_start, "t_end": self.t_end,
            "dt_median": self.dt_median, "window_seconds": self.window_seconds,
            "verdict": self.verdict,
            "rel_drift_over_window": self.rel_drift_over_window,
            "drift_ratio": self.drift_ratio,
            "near_zero_mean": self.near_zero_mean,
            "trend_resolved": self.trend_resolved,
        }
        d.update({f"fit_{k}": v for k, v in asdict(self.fit).items()})
        d.update({f"osc_{k}": v for k, v in asdict(self.oscillation).items()})
        d.update({f"unc_{k}": v for k, v in asdict(self.uncertainty).items()})
        return d


# ---------------------------------------------------------------------------
def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def window(t: list[float], y: list[float], window_seconds: float) -> tuple[list[float], list[float]]:
    """Return the sub-series with time >= t_end - window_seconds."""
    if not t:
        return [], []
    cutoff = t[-1] - window_seconds
    tt, yy = [], []
    for ti, yi in zip(t, y):
        if ti >= cutoff:
            tt.append(ti)
            yy.append(yi)
    return tt, yy


def linfit(t: list[float], y: list[float]) -> Fit:
    n = len(t)
    if n < 2:
        return Fit(n, 0.0, y[0] if y else 0.0, 1.0, 0.0, 0.0)
    mt, my = _mean(t), _mean(y)
    sxx = sum((ti - mt) ** 2 for ti in t)
    sxy = sum((ti - mt) * (yi - my) for ti, yi in zip(t, y))
    slope = sxy / sxx if sxx > 0 else 0.0
    intercept = my - slope * mt
    ss_res = sum((yi - (slope * ti + intercept)) ** 2 for ti, yi in zip(t, y))
    ss_tot = sum((yi - my) ** 2 for yi in y)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    dof = n - 2
    slope_se = math.sqrt((ss_res / dof) / sxx) if (dof > 0 and sxx > 0) else 0.0
    t_stat = slope / slope_se if slope_se > 0 else 0.0
    return Fit(n, slope, intercept, r2, slope_se, t_stat)


def oscillation(t: list[float], y: list[float], fit: Fit) -> Oscillation:
    n = len(y)
    my = _mean(y)
    var_mean = sum((yi - my) ** 2 for yi in y) / n if n else 0.0
    resid = [yi - (fit.slope * ti + fit.intercept) for ti, yi in zip(t, y)]
    var_trend = sum(r * r for r in resid) / n if n else 0.0
    lo, hi = (min(y), max(y)) if y else (0.0, 0.0)
    cov = math.sqrt(var_mean) / abs(my) if my != 0 else float("inf")
    return Oscillation(
        mean=my, minimum=lo, maximum=hi, peak_to_peak=hi - lo,
        rmse_about_mean=math.sqrt(var_mean), var_about_mean=var_mean,
        rmse_about_trend=math.sqrt(var_trend), var_about_trend=var_trend, cov=cov)


def integrated_autocorr_time(resid: list[float], max_lag: int | None = None) -> tuple[float, int]:
    """τ_int = 1 + 2 Σ ρ_k, truncated at the first non-positive ρ_k (Sokal-style)."""
    n = len(resid)
    if n < 4:
        return 1.0, 0
    mu = _mean(resid)
    denom = sum((r - mu) ** 2 for r in resid)
    if denom <= 0:
        return 1.0, 0
    if max_lag is None:
        max_lag = min(n // 2, 1000)
    tau = 1.0
    used = 0
    for k in range(1, max_lag + 1):
        cov_k = sum((resid[i] - mu) * (resid[i + k] - mu) for i in range(n - k))
        rho = cov_k / denom
        if rho <= 0.0:
            break
        tau += 2.0 * rho
        used = k
    return max(tau, 1.0), used


def uncertainty(osc: Oscillation, n: int, tau_int: float) -> Uncertainty:
    sigma = osc.rmse_about_mean
    sem_naive = sigma / math.sqrt(n) if n > 0 else 0.0
    n_eff = n / tau_int if tau_int > 0 else float(n)
    sem_corr = sigma / math.sqrt(n_eff) if n_eff > 0 else 0.0
    am = abs(osc.mean) if osc.mean != 0 else float("inf")
    return Uncertainty(
        tau_int=tau_int, n_eff=n_eff, sem_naive=sem_naive, sem_corrected=sem_corr,
        rel_sem_naive=sem_naive / am, rel_sem_corrected=sem_corr / am)


def running_sem(t: list[float], y: list[float], n_points: int = 40) -> list[dict]:
    """SEM(σ/√k) as the averaging window grows — for the 1/√t convergence plot.

    Returns points {avg_seconds, n, sem_naive, sem_reference} where the reference
    is σ_full/√k (ideal CLT scaling). x is averaging duration from the window start.
    """
    n = len(y)
    if n < MIN_WINDOW_POINTS:
        return []
    my = _mean(y)
    sigma_full = math.sqrt(sum((yi - my) ** 2 for yi in y) / n)
    out: list[dict] = []
    ks = sorted(set(int(round(x)) for x in _logspace(MIN_WINDOW_POINTS, n, n_points)))
    for k in ks:
        if k < 2:
            continue
        sub = y[:k]
        m = _mean(sub)
        s = math.sqrt(sum((v - m) ** 2 for v in sub) / k)
        out.append({
            "avg_seconds": t[k - 1] - t[0],
            "n": k,
            "sem_naive": s / math.sqrt(k),
            "sem_reference": sigma_full / math.sqrt(k),
        })
    return out


def _logspace(lo: float, hi: float, count: int) -> list[float]:
    if hi <= lo:
        return [lo]
    a, b = math.log(lo), math.log(hi)
    return [math.exp(a + (b - a) * i / (count - 1)) for i in range(count)]


def steady_verdict(fit: Fit, osc: Oscillation,
                   window_seconds: float) -> tuple[str, float, float, bool, bool]:
    """Robust steady-state verdict.

    Returns (verdict, rel_drift, drift_ratio, near_zero_mean, trend_resolved).

    The primary metric is *scale-free*: drift_ratio = |trend change over window| /
    oscillation amplitude (RMSE about the trend). This avoids the near-zero-mean
    trap where |mean| ≈ 0 makes relative-to-mean drift explode (e.g. net heat
    oscillating about zero). The relative-to-mean drift is used as a refinement
    only when the mean is well separated from zero (|mean| > SNR·std).
    """
    change = abs(fit.slope * window_seconds)
    std = osc.rmse_about_mean
    osc_amp = osc.rmse_about_trend if osc.rmse_about_trend > 0 else std
    drift_ratio = (change / osc_amp) if osc_amp > 0 else (0.0 if change == 0 else float("inf"))
    mean_well_defined = abs(osc.mean) > SNR_MEAN * std and osc.mean != 0
    near_zero_mean = not mean_well_defined
    # a statistically resolved drift is one that stands clear of the oscillation band
    resolved = drift_ratio > DRIFT_RATIO_DRIFT

    if mean_well_defined:
        # Mean is meaningful → judge drift RELATIVE TO THE MEAN (physical significance).
        rel_drift = change / abs(osc.mean)
        if rel_drift > DRIFT_QUASI:
            verdict = "not steady (drifting)"
        elif rel_drift < DRIFT_STEADY and osc.cov < COV_STEADY:
            verdict = "steady"
        else:
            verdict = "quasi-steady (bounded drift/oscillation)"
    else:
        # Mean ≈ 0 → relative-to-mean is meaningless; use the scale-free ratio.
        rel_drift = float("nan")
        if drift_ratio > DRIFT_RATIO_DRIFT:
            verdict = "not steady (drifting)"
        elif drift_ratio < DRIFT_RATIO_STEADY:
            verdict = "steady"
        else:
            verdict = "quasi-steady (bounded drift/oscillation)"
    return verdict, rel_drift, drift_ratio, near_zero_mean, resolved


def analyze(t: list[float], y: list[float], window_seconds: float) -> SeriesAnalysis | None:
    tw, yw = window(t, y, window_seconds)
    if len(tw) < MIN_WINDOW_POINTS:
        return None
    dts = sorted(tw[i + 1] - tw[i] for i in range(len(tw) - 1))
    dt_med = dts[len(dts) // 2] if dts else 0.0
    fit = linfit(tw, yw)
    osc = oscillation(tw, yw, fit)
    resid = [yi - (fit.slope * ti + fit.intercept) for ti, yi in zip(tw, yw)]
    tau, _ = integrated_autocorr_time(resid)
    unc = uncertainty(osc, len(yw), tau)
    verdict, rel_drift, drift_ratio, near_zero, resolved = steady_verdict(fit, osc, window_seconds)
    return SeriesAnalysis(
        n_window=len(yw), t_start=tw[0], t_end=tw[-1], dt_median=dt_med,
        window_seconds=window_seconds, fit=fit, oscillation=osc, uncertainty=unc,
        verdict=verdict, rel_drift_over_window=rel_drift, drift_ratio=drift_ratio,
        near_zero_mean=near_zero, trend_resolved=resolved)
