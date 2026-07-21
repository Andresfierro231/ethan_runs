#!/usr/bin/env python3
"""Unit tests for the pure-function core of derive_segment_friction.

Run from the repo root with the SYSTEM python (do NOT source OpenFOAM env):
    python -m pytest tools/analyze/test_derive_segment_friction.py -q
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.derive_segment_friction import (  # noqa: E402
    apparent_darcy_friction,
    arc_length_along,
    laminar_darcy_reference,
    reynolds_number,
    segment_pressure_gradient,
)


# --------------------------------------------------------------------------- #
# arc length                                                                   #
# --------------------------------------------------------------------------- #
def test_arc_length_axis_aligned():
    coords = [(0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (3.0, 4.0, 0.0)]
    s = arc_length_along(coords)
    # +3 along x, then +4 along y
    assert s == pytest.approx([0.0, 3.0, 7.0])


def test_arc_length_single_point_is_zero():
    assert arc_length_along([(1.0, 2.0, 3.0)]) == [0.0]


def test_arc_length_3d_diagonal():
    coords = [(0.0, 0.0, 0.0), (1.0, 2.0, 2.0)]
    s = arc_length_along(coords)
    assert s[-1] == pytest.approx(3.0)  # sqrt(1+4+4)


# --------------------------------------------------------------------------- #
# pressure gradient                                                            #
# --------------------------------------------------------------------------- #
def test_segment_pressure_gradient_linear():
    arc = [0.0, 1.0, 2.0]
    p = [10.0, 8.0, 6.0]  # falls 2 Pa/m
    assert segment_pressure_gradient(arc, p) == pytest.approx(-2.0)


def test_segment_pressure_gradient_zero_length_is_nan():
    assert math.isnan(segment_pressure_gradient([0.0, 0.0], [5.0, 3.0]))


def test_segment_pressure_gradient_too_few_points():
    assert math.isnan(segment_pressure_gradient([0.0], [5.0]))


# --------------------------------------------------------------------------- #
# Darcy friction formula                                                       #
# --------------------------------------------------------------------------- #
def test_apparent_darcy_friction_known_values():
    # Synthetic linear p(s): static gradient -100 Pa/m over the segment, so the
    # loss gradient dp_loss/ds = +100 Pa/m.
    # D_h = 0.02 m, rho = 1800 kg/m3, u = 0.05 m/s.
    # f = 2 * D_h * dp_loss_ds / (rho * u^2)
    #   = 2 * 0.02 * 100 / (1800 * 0.0025)
    #   = 4.0 / 4.5 = 0.888888...
    f = apparent_darcy_friction(100.0, 0.02, 1800.0, 0.05)
    assert f == pytest.approx(4.0 / 4.5)


def test_apparent_darcy_friction_from_linear_profile_endtoend():
    # Build a linear total-pressure profile and confirm the chained pure functions
    # reproduce the closed-form f.
    arc = [0.0, 0.5, 1.0]
    p = [200.0, 150.0, 100.0]  # -100 Pa/m
    grad = segment_pressure_gradient(arc, p)
    dp_loss_ds = -grad
    assert dp_loss_ds == pytest.approx(100.0)
    f = apparent_darcy_friction(dp_loss_ds, 0.02, 1800.0, 0.05)
    assert f == pytest.approx(4.0 / 4.5)


def test_apparent_darcy_friction_zero_velocity_is_nan():
    assert math.isnan(apparent_darcy_friction(100.0, 0.02, 1800.0, 0.0))


def test_apparent_darcy_friction_zero_dh_is_nan():
    assert math.isnan(apparent_darcy_friction(100.0, 0.0, 1800.0, 0.05))


def test_apparent_darcy_friction_negative_loss_gives_negative_f():
    # pressure rising downstream -> negative loss gradient -> negative f (flagged
    # downstream, not clamped in the formula)
    f = apparent_darcy_friction(-100.0, 0.02, 1800.0, 0.05)
    assert f < 0


# --------------------------------------------------------------------------- #
# Reynolds + laminar reference                                                 #
# --------------------------------------------------------------------------- #
def test_reynolds_number_known():
    # Re = rho u Dh / mu = 1800 * 0.05 * 0.02 / 0.003 = 1.8/0.003 = 600
    assert reynolds_number(1800.0, 0.05, 0.02, 0.003) == pytest.approx(600.0)


def test_reynolds_number_no_mu_is_nan():
    assert math.isnan(reynolds_number(1800.0, 0.05, 0.02, None))


def test_reynolds_number_zero_mu_is_nan():
    assert math.isnan(reynolds_number(1800.0, 0.05, 0.02, 0.0))


def test_laminar_darcy_reference():
    assert laminar_darcy_reference(600.0) == pytest.approx(64.0 / 600.0)


def test_laminar_darcy_reference_invalid_re_is_nan():
    assert math.isnan(laminar_darcy_reference(float("nan")))
    assert math.isnan(laminar_darcy_reference(0.0))
