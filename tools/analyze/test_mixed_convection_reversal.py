#!/usr/bin/env python3
"""Tests for tools/analyze/mixed_convection_reversal.py (system python, no OF)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import mixed_convection_reversal as m  # noqa: E402


def test_beta_salt():
    # rho ~ 1955 kg/m^3 at ~452 K (rho=2293.6-0.7497*452); beta = 0.7497/rho
    rho = 2293.6 - 0.7497 * 452.0
    assert math.isclose(m.beta_salt(rho), 0.7497 / rho, rel_tol=1e-12)
    # plausible magnitude ~ 3.8e-4 / K
    assert 3.0e-4 < m.beta_salt(rho) < 4.5e-4


def test_grashof_and_richardson_consistency():
    # Ri = Gr/Re^2 should reduce to g*beta*dT*Lc/U^2 independent of nu.
    beta, dT, Lc, nu, U, g = 3.8e-4, 5.0, 0.0218, 1e-6, 0.016, 9.81
    Gr = m.grashof_dt(beta, dT, Lc, nu, g)
    Re = U * Lc / nu
    Ri = m.richardson(Gr, Re)
    assert math.isclose(Ri, g * beta * dT * Lc / U ** 2, rel_tol=1e-9)


def test_re_crit_from_ri():
    Gr = 1.0e6
    assert math.isclose(m.re_crit_from_ri(Gr, 1.0), 1000.0, rel_tol=1e-9)
    assert math.isclose(m.re_crit_from_ri(Gr, 4.0), 500.0, rel_tol=1e-9)


def test_re_crit_from_gr_over_re():
    assert math.isclose(m.re_crit_from_gr_over_re(20000.0, 100.0), 200.0, rel_tol=1e-9)


def test_reynolds_roundtrip():
    rho, U, Lc, mu = 1955.0, 0.016, 0.0218, 0.0073
    Re = m.reynolds(rho, U, Lc, mu)
    assert math.isclose(Re, rho * U * Lc / mu, rel_tol=1e-12)
    assert 80.0 < Re < 100.0  # sanity: laminar upcomer band


def test_nan_guards():
    assert math.isnan(m.beta_salt(float("nan")))
    assert math.isnan(m.beta_salt(-1.0))
    assert math.isnan(m.grashof_dt(1, 1, 1, 0.0))
    assert math.isnan(m.richardson(1.0, 0.0))
    assert math.isnan(m.re_crit_from_ri(1.0, 0.0))
    assert math.isnan(m.re_crit_from_gr_over_re(1.0, 0.0))
    assert math.isnan(m.reynolds(1, 1, 1, 0.0))


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
