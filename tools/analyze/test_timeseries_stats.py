"""Tests for timeseries_stats.py (AGENT-244)."""

from __future__ import annotations

import math

import timeseries_stats as ts


def test_linfit_exact_line() -> None:
    t = list(range(10))
    y = [2.0 * ti + 3.0 for ti in t]
    fit = ts.linfit(t, y)
    assert abs(fit.slope - 2.0) < 1e-9
    assert abs(fit.intercept - 3.0) < 1e-9
    assert abs(fit.r2 - 1.0) < 1e-9


def test_linfit_flat_series() -> None:
    t = list(range(20))
    y = [5.0] * 20
    fit = ts.linfit(t, y)
    assert abs(fit.slope) < 1e-12
    assert abs(fit.intercept - 5.0) < 1e-9


def test_oscillation_std_and_variance() -> None:
    t = list(range(100))
    y = [5.0 + (1.0 if i % 2 == 0 else -1.0) for i in range(100)]  # ±1 about 5
    fit = ts.linfit(t, y)
    osc = ts.oscillation(t, y, fit)
    assert abs(osc.mean - 5.0) < 1e-9
    assert abs(osc.rmse_about_mean - 1.0) < 1e-9      # RMS fluctuation = 1
    assert abs(osc.var_about_mean - 1.0) < 1e-9
    assert abs(osc.peak_to_peak - 2.0) < 1e-9
    assert abs(osc.cov - 0.2) < 1e-9                  # 1/5


def test_rmse_about_trend_removes_drift() -> None:
    # pure linear drift → zero oscillation about the trend
    t = list(range(50))
    y = [0.01 * ti + 2.0 for ti in t]
    fit = ts.linfit(t, y)
    osc = ts.oscillation(t, y, fit)
    assert osc.rmse_about_mean > 0.1          # spread about mean is nonzero (drift)
    assert osc.rmse_about_trend < 1e-9        # but zero about the trend


def test_autocorr_time_constant_is_one() -> None:
    tau, _ = ts.integrated_autocorr_time([3.0] * 50)
    assert tau == 1.0


def test_autocorr_time_white_is_near_one() -> None:
    resid = [1.0 if i % 2 == 0 else -1.0 for i in range(200)]  # anti-correlated
    tau, _ = ts.integrated_autocorr_time(resid)
    assert tau <= 1.001                        # first rho<0 → truncates immediately


def test_autocorr_time_smooth_is_large() -> None:
    resid = [math.sin(i * 0.05) for i in range(600)]  # slowly varying → correlated
    tau, used = ts.integrated_autocorr_time(resid)
    assert tau > 2.0
    assert used > 1


def test_uncertainty_naive_vs_corrected() -> None:
    osc = ts.Oscillation(mean=10.0, minimum=9, maximum=11, peak_to_peak=2,
                         rmse_about_mean=2.0, var_about_mean=4.0,
                         rmse_about_trend=2.0, var_about_trend=4.0, cov=0.2)
    unc = ts.uncertainty(osc, n=100, tau_int=4.0)
    assert abs(unc.sem_naive - 0.2) < 1e-9          # 2/sqrt(100)
    assert abs(unc.n_eff - 25.0) < 1e-9             # 100/4
    assert abs(unc.sem_corrected - 0.4) < 1e-9      # 2/sqrt(25)
    assert unc.sem_corrected > unc.sem_naive        # correlation inflates uncertainty
    assert abs(unc.rel_sem_corrected - 0.04) < 1e-9  # 0.4/10


def test_window_selects_tail() -> None:
    t = [float(i) for i in range(1000)]
    y = [float(i) for i in range(1000)]
    tw, yw = ts.window(t, y, 300.0)
    assert tw[0] >= 699.0
    assert tw[-1] == 999.0
    assert len(tw) == 301


def test_running_sem_decreases() -> None:
    t = [float(i) for i in range(400)]
    y = [5.0 + (1.0 if i % 2 == 0 else -1.0) for i in range(400)]
    pts = ts.running_sem(t, y)
    assert len(pts) >= 5
    assert pts[-1]["sem_naive"] < pts[0]["sem_naive"]     # shrinks with more samples
    assert all(p["sem_reference"] > 0 for p in pts)


def test_steady_verdict_flat_vs_drifting() -> None:
    t = list(range(300))
    flat = [10.0 + (0.001 if i % 2 else -0.001) for i in range(300)]
    fit = ts.linfit(t, flat)
    osc = ts.oscillation(t, flat, fit)
    verdict, rel_drift, drift_ratio, near_zero, resolved = ts.steady_verdict(fit, osc, 300.0)
    assert verdict == "steady"
    assert near_zero is False

    drift = [10.0 + 0.02 * i for i in range(300)]   # +6 over window on mean ~13 → huge
    fit2 = ts.linfit(t, drift)
    osc2 = ts.oscillation(t, drift, fit2)
    verdict2, rel_drift2, dr2, nz2, resolved2 = ts.steady_verdict(fit2, osc2, 300.0)
    assert verdict2 == "not steady (drifting)"
    assert dr2 > drift_ratio
    assert resolved2 is True


def test_steady_verdict_near_zero_mean_not_falsely_drifting() -> None:
    """A small bounded oscillation about ~0 with tiny drift must NOT read 'drifting'.

    This is the net-heat (total_Q) case: mean ≈ 0 so relative-to-mean drift is
    meaningless; the scale-free drift_ratio keeps the verdict honest.
    """
    t = list(range(300))
    # mean ~0.05, oscillation amplitude ~0.03, drift ~0.01 over window (< noise)
    y = [0.05 + 0.03 * math.sin(i * 0.4) + 3e-5 * i for i in range(300)]
    fit = ts.linfit(t, y)
    osc = ts.oscillation(t, y, fit)
    verdict, rel_drift, drift_ratio, near_zero, resolved = ts.steady_verdict(fit, osc, 300.0)
    assert near_zero is True
    assert math.isnan(rel_drift)              # mean not separated from zero
    assert drift_ratio < ts.DRIFT_RATIO_DRIFT
    assert verdict != "not steady (drifting)"  # the bug we fixed


def test_analyze_end_to_end() -> None:
    t = [float(i) for i in range(2000)]
    y = [7.0 + 0.5 * math.sin(i * 0.3) for i in range(2000)]
    a = ts.analyze(t, y, 300.0)
    assert a is not None
    assert a.n_window == 301
    assert abs(a.oscillation.mean - 7.0) < 0.05
    assert a.uncertainty.sem_corrected >= a.uncertainty.sem_naive
    assert a.verdict in {"steady", "quasi-steady (bounded drift/oscillation)",
                         "not steady (drifting)"}
