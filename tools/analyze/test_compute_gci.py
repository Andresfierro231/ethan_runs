#!/usr/bin/env python3
"""Unit tests for tools/analyze/compute_gci.py (Lane L5 GCI calculator).

Strategy: build an ANALYTIC convergent series with a KNOWN exact value f_exact and
order p, namely f(h) = f_exact + C * h^p, sampled at h = 1, 2, 4 (so r = 2). The
calculator must recover p and f_exact to tolerance, produce a positive GCI on the
fine grid, and an asymptotic-range ratio ~1. Also test the convergence verdict
classifier for monotonic vs oscillatory triplets, and the degenerate guards.

Run from the repo root with SYSTEM python (do NOT source any OpenFOAM env):
    python -m pytest tools/analyze/test_compute_gci.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.compute_gci import (  # noqa: E402
    classify_convergence,
    compute_gci,
    convergence_ratio,
    richardson_extrapolate,
    solve_observed_order,
)


def _analytic_triplet(f_exact: float, c: float, p: float, r: float = 2.0):
    """f(h) = f_exact + C*h^p at h1=1 (fine), h2=r (medium), h3=r^2 (coarse).

    Returns (coarse=f3, medium=f2, fine=f1, r21=r, r32=r).
    """
    h1, h2, h3 = 1.0, r, r * r
    f1 = f_exact + c * h1 ** p
    f2 = f_exact + c * h2 ** p
    f3 = f_exact + c * h3 ** p
    return f3, f2, f1, r, r


@pytest.mark.parametrize(
    "f_exact, c, p",
    [
        (10.0, 0.5, 2.0),   # canonical second-order
        (-3.25, 1.7, 1.0),  # first-order, negative exact, decreasing not required
        (100.0, -2.0, 2.0), # negative coefficient (solutions approach from above)
        (0.041, 0.01, 1.8), # mdot-like magnitude, fractional order
    ],
)
def test_recovers_known_order_and_exact(f_exact, c, p):
    f3, f2, f1, r21, r32 = _analytic_triplet(f_exact, c, p)
    res = compute_gci(f3, f2, f1, r21, r32)

    assert res["order_status"] == "ok"
    assert res["observed_order_p"] == pytest.approx(p, abs=1e-6)
    assert res["f_exact_richardson"] == pytest.approx(f_exact, abs=1e-6)
    assert res["verdict"] == "monotonic_convergence"

    # GCI on the fine grid must be a positive error band.
    assert res["gci_fine_pct"] is not None and res["gci_fine_pct"] > 0.0
    assert res["gci_coarse_pct"] > 0.0

    # Asymptotic-range ratio is reported and finite & positive. For an analytic
    # series it equals f1/f2 (the GCI normalizes by the grid solution, not the
    # difference), so it -> 1 as f_exact dominates C*h^p; see dedicated test.
    assert res["asymptotic_range_ratio"] is not None
    assert res["asymptotic_range_ratio"] > 0.0


def test_asymptotic_ratio_approaches_one_when_fexact_dominates():
    # Large exact value relative to error term -> f1 ~= f2 -> asym ratio ~= 1 and
    # the result is flagged trustworthy.
    f3, f2, f1, r21, r32 = _analytic_triplet(1.0e4, 0.5, 2.0, r=2.0)
    res = compute_gci(f3, f2, f1, r21, r32)
    assert res["observed_order_p"] == pytest.approx(2.0, abs=1e-6)
    assert res["asymptotic_range_ratio"] == pytest.approx(1.0, abs=5e-3)
    assert res["gci_trustworthy"] is True


def test_nonconstant_ratio_fixed_point():
    """Non-constant refinement ratios: r21 != r32 should still recover p, f_exact
    via the transcendental fixed-point solver."""
    f_exact, c, p = 5.0, 0.8, 2.0
    h1, h2, h3 = 1.0, 1.5, 1.5 * 1.9  # r21=1.5, r32=1.9 (non-constant)
    f1 = f_exact + c * h1 ** p
    f2 = f_exact + c * h2 ** p
    f3 = f_exact + c * h3 ** p
    order = solve_observed_order(f3, f2, f1, 1.5, 1.9)
    assert order["status"] == "ok"
    assert order["iters"] > 0  # used iteration, not the closed form
    assert order["p"] == pytest.approx(p, abs=1e-4)

    res = compute_gci(f3, f2, f1, 1.5, 1.9)
    assert res["f_exact_richardson"] == pytest.approx(f_exact, abs=1e-4)
    assert res["gci_fine_pct"] > 0.0


def test_richardson_pure_function():
    # f1 + (f1-f2)/(r^p - 1); for f1=10.5, f2=12, r=2, p=2 -> 10.5 + (-1.5)/3 = 10.0
    assert richardson_extrapolate(10.5, 12.0, 2.0, 2.0) == pytest.approx(10.0)


def test_verdict_monotonic_vs_oscillatory():
    # Monotonic convergence: differences same sign, shrinking. f3>f2>f1.
    assert classify_convergence(convergence_ratio(12.0, 10.5, 10.125)) == "monotonic_convergence"
    # Oscillatory: f2-f1 and f3-f2 have opposite signs -> R < 0.
    assert classify_convergence(convergence_ratio(11.0, 9.0, 10.0)) == "oscillatory"
    # Divergent: differences grow -> R > 1.
    assert classify_convergence(convergence_ratio(10.125, 10.5, 12.0)) == "monotonic_divergence"


def test_oscillatory_does_not_crash_and_flagged():
    # f1=10, f2=9, f3=11 -> e21=-1, e32=+2, opposite signs -> oscillatory.
    res = compute_gci(11.0, 9.0, 10.0, 2.0, 2.0)
    assert res["verdict"] == "oscillatory"
    assert res["gci_trustworthy"] is False
    # Must not raise; if order ill-defined GCI fields are None, otherwise flagged.


def test_equal_values_undefined_order():
    # f1==f2 -> e21=0 -> p undefined, no crash, GCI not formed.
    res = compute_gci(12.0, 10.0, 10.0, 2.0, 2.0)
    assert res["order_status"] == "undefined_equal_values"
    assert res["observed_order_p"] is None
    assert res["gci_fine_pct"] is None
    assert res["gci_trustworthy"] is False


def test_bad_ratio_guard():
    res = compute_gci(12.0, 10.5, 10.125, 1.0, 1.0)  # r==1 invalid
    assert res["order_status"] == "undefined_nonpositive_ratio"
    assert res["gci_fine_pct"] is None


def test_constant_ratio_uses_closed_form():
    f3, f2, f1, r21, r32 = _analytic_triplet(2.0, 0.3, 2.0, r=2.0)
    order = solve_observed_order(f3, f2, f1, r21, r32)
    assert order["status"] == "ok"
    assert order["iters"] == 0  # closed form, no iteration
    assert order["p"] == pytest.approx(2.0, abs=1e-9)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
