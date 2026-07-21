#!/usr/bin/env python3
"""Unit tests for tools/analyze/salt_properties.py (pure functions).

Run from the repo root with the SYSTEM python (do NOT source OpenFOAM env):
    python -m pytest tools/analyze/test_salt_properties.py -q
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.salt_properties import (  # noqa: E402
    jin_mu,
    kirst_mu,
    salt_cp,
    salt_k,
    salt_rho,
    temperature_from_rho,
)


def test_jin_mu_reference_value():
    # Direct evaluation of 0.001149*exp(-810.896/T + 780600/T^2) at T=900 K.
    expected = 0.001149 * math.exp(-810.896 / 900.0 + 780600.0 / 900.0**2)
    assert jin_mu(900.0) == pytest.approx(expected, rel=1e-12)


def test_jin_mu_positive_and_reasonable():
    mu = jin_mu(900.0)
    assert math.isfinite(mu)
    # FLiNaK-class molten salts: mu is a small fraction of a Pa*s near 900 K.
    assert 1e-4 < mu < 1e-2


def test_jin_mu_decreases_with_temperature():
    # Viscosity must fall as temperature rises over the operating range.
    temps = [700.0, 800.0, 900.0, 1000.0]
    mus = [jin_mu(t) for t in temps]
    assert all(mus[i] > mus[i + 1] for i in range(len(mus) - 1))


def test_kirst_mu_reference_value():
    expected = 6.757e-05 * math.exp(2247.11 / 900.0)
    assert kirst_mu(900.0) == pytest.approx(expected, rel=1e-12)


def test_kirst_mu_decreases_with_temperature():
    mus = [kirst_mu(t) for t in (700.0, 800.0, 900.0, 1000.0)]
    assert all(mus[i] > mus[i + 1] for i in range(len(mus) - 1))


def test_salt_rho_reference_and_trend():
    assert salt_rho(900.0) == pytest.approx(2293.6 - 0.7497 * 900.0)
    # rho decreases with temperature (negative linear coefficient).
    assert salt_rho(800.0) > salt_rho(1000.0)


def test_salt_cp_constant():
    assert salt_cp(700.0) == pytest.approx(1423.47)
    assert salt_cp(1000.0) == pytest.approx(1423.47)


def test_salt_k_reference():
    assert salt_k(900.0) == pytest.approx(0.78 - 0.00125 * 900.0 + 1.6e-06 * 900.0**2)


def test_temperature_from_rho_roundtrip():
    for t in (600.0, 750.0, 900.0, 1050.0):
        assert temperature_from_rho(salt_rho(t)) == pytest.approx(t, rel=1e-9)


def test_nan_guards():
    assert math.isnan(jin_mu(float("nan")))
    assert math.isnan(jin_mu(0.0))
    assert math.isnan(kirst_mu(float("inf")))
    assert math.isnan(salt_rho(float("nan")))
    assert math.isnan(temperature_from_rho(float("nan")))
