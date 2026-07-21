#!/usr/bin/env python3
"""Tests for sample_span_endpoint_temperatures.

RUN WITH SYSTEM PYTHON (do NOT source any OpenFOAM env):
    python -m pytest tools/extract/test_sample_span_endpoint_temperatures.py -q

Covers:
  * rho inversion: T = (2293.6 - rho) / 0.7497
  * mass-flux-weighted bulk T computation from synthetic 8-col XY data
  * downcomer flow direction convention (s04→s00)
  * file-not-found and degenerate edge cases
  * sanity check on real Salt 2 XY files (when present)
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.extract.sample_span_endpoint_temperatures as m  # noqa: E402

REAL_SECMEAN = (
    ROOT / "tmp" / "2026-06-30_claude_action_items"
    / "recon_salt2_of13" / "postProcessing" / "secmeanSurfaces" / "7915"
)

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def make_xy_data(u_x: float, rho: float, n: int = 30, leg_radius: float = 0.015) -> np.ndarray:
    """Synthetic 8-column XY cut plane: face_x face_y face_z Ux Uy Uz p_rgh rho.

    Faces uniformly distributed in a disc of the given radius centred at origin.
    Velocity is purely in the x-direction (u_x).
    """
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = leg_radius * np.sqrt(np.random.default_rng(42).uniform(0, 1, n))
    xs = np.zeros(n)
    ys = r * np.cos(theta)
    zs = r * np.sin(theta)
    Ux = np.full(n, u_x)
    Uy = np.zeros(n)
    Uz = np.zeros(n)
    p_rgh = np.zeros(n)
    rhos = np.full(n, rho)
    return np.column_stack([xs, ys, zs, Ux, Uy, Uz, p_rgh, rhos])


def write_xy_file(data: np.ndarray, path: Path) -> None:
    header = "# face_x face_y face_z U_x U_y U_z p_rgh rho"
    np.savetxt(path, data, header=header)


# -------------------------------------------------------------------------
# Unit: rho inversion
# -------------------------------------------------------------------------

def test_t_from_rho_at_reference():
    """At TRef = 447 K, rho = 2293.6 - 0.7497*447 = 1958.48"""
    rho = 2293.6 - 0.7497 * 447.0
    T = m.t_from_rho(np.array([rho]))[0]
    assert abs(T - 447.0) < 0.01


def test_t_from_rho_hot_cell():
    """Hot side ~483 K → rho ~ 1931.5 kg/m3"""
    T_expected = 483.0
    rho = 2293.6 - 0.7497 * T_expected
    T = m.t_from_rho(np.array([rho]))[0]
    assert abs(T - T_expected) < 0.01


def test_t_from_rho_cold_cell():
    """Cold side ~438 K → rho ~ 1965.2 kg/m3"""
    T_expected = 438.0
    rho = 2293.6 - 0.7497 * T_expected
    T = m.t_from_rho(np.array([rho]))[0]
    assert abs(T - T_expected) < 0.01


# -------------------------------------------------------------------------
# Unit: bulk_t_from_xy
# -------------------------------------------------------------------------

def test_bulk_t_uniform_flow(tmp_path):
    """Uniform T, uniform u_n → T_bulk = T_cell."""
    T_cell = 460.0
    rho = 2293.6 - 0.7497 * T_cell  # ~1948.5 kg/m3
    data = make_xy_data(u_x=0.05, rho=rho, n=40)
    xy = tmp_path / "test.xy"
    write_xy_file(data, xy)
    result = m.bulk_t_from_xy(xy, leg_radius_m=0.018)
    assert result["status"] == "ok"
    assert abs(result["T_bulk_k"] - T_cell) < 0.1
    assert abs(result["T_simple_k"] - T_cell) < 0.1


def test_bulk_t_hot_cold_halves(tmp_path):
    """Half faces at T_hot, half at T_cold with equal velocity → T_bulk = mean."""
    T_hot, T_cold = 480.0, 440.0
    rho_hot = 2293.6 - 0.7497 * T_hot
    rho_cold = 2293.6 - 0.7497 * T_cold
    n_each = 25

    data_hot = make_xy_data(u_x=0.05, rho=rho_hot, n=n_each, leg_radius=0.007)
    data_cold = make_xy_data(u_x=0.05, rho=rho_cold, n=n_each, leg_radius=0.007)
    # offset cold half so centroid stays near origin
    data_cold[:, 1] += 0.001
    data = np.vstack([data_hot, data_cold])

    xy = tmp_path / "test.xy"
    write_xy_file(data, xy)
    result = m.bulk_t_from_xy(xy, leg_radius_m=0.015)
    assert result["status"] == "ok"
    # Mass-flux-weighted: slightly biased toward cold (denser, heavier) - within 2 K of arithmetic mean
    T_expected = (T_hot + T_cold) / 2
    assert abs(result["T_bulk_k"] - T_expected) < 2.0


def test_bulk_t_file_not_found(tmp_path):
    result = m.bulk_t_from_xy(tmp_path / "nonexistent.xy")
    assert result["status"].startswith("unreadable")


def test_bulk_t_too_few_faces(tmp_path):
    """A cut plane with only 3 faces should return a 'too_few_faces' status."""
    T_cell = 455.0
    rho = 2293.6 - 0.7497 * T_cell
    data = make_xy_data(u_x=0.05, rho=rho, n=3)
    xy = tmp_path / "tiny.xy"
    write_xy_file(data, xy)
    result = m.bulk_t_from_xy(xy, leg_radius_m=0.015)
    assert result["status"] == "too_few_faces"


def test_bulk_t_zero_velocity(tmp_path):
    """Zero velocity everywhere → zero_mean_velocity or zero_mass_flux status."""
    T_cell = 455.0
    rho = 2293.6 - 0.7497 * T_cell
    data = make_xy_data(u_x=0.0, rho=rho, n=40)
    xy = tmp_path / "stagnant.xy"
    write_xy_file(data, xy)
    result = m.bulk_t_from_xy(xy, leg_radius_m=0.015)
    assert result["status"] in ("zero_mean_velocity", "zero_mass_flux")


# -------------------------------------------------------------------------
# Unit: flow direction convention
# -------------------------------------------------------------------------

def test_flow_direction_keys():
    """All SPANS have a FLOW_DIRECTION entry."""
    for span in m.SPANS:
        assert span in m.FLOW_DIRECTION, f"Missing FLOW_DIRECTION for {span}"


def test_right_leg_reversed():
    """Downcomer (right_leg) should flow s04→s00 (direction = -1)."""
    assert m.FLOW_DIRECTION["right_leg"] == -1


def test_other_spans_forward():
    """Heater (lower_leg) and downcomer (right_leg) flow s04→s00; upcomer/cooler flow s00→s04."""
    assert m.FLOW_DIRECTION["lower_leg"] == -1, "lower_leg flows s04→s00 (heater: downcomer→upcomer)"
    for span in ["left_lower_leg", "test_section_span", "left_upper_leg", "upper_leg"]:
        assert m.FLOW_DIRECTION[span] == 1, f"{span} should flow s00→s04 (forward), got {m.FLOW_DIRECTION[span]}"


# -------------------------------------------------------------------------
# Integration: process_case on synthetic data
# -------------------------------------------------------------------------

def _make_fake_secmean_dir(base: Path, spans: list[str], T_s00: float, T_s04: float) -> Path:
    """Build a minimal fake secmeanSurfaces/{time} directory."""
    time_dir = base / "postProcessing" / "secmeanSurfaces" / "1234"
    time_dir.mkdir(parents=True)
    rho_s00 = 2293.6 - 0.7497 * T_s00
    rho_s04 = 2293.6 - 0.7497 * T_s04
    for span in spans:
        for idx, rho in [(0, rho_s00), (2, (rho_s00 + rho_s04) / 2), (4, rho_s04)]:
            data = make_xy_data(u_x=0.05, rho=rho, n=40)
            write_xy_file(data, time_dir / f"plane_{span}__s{idx:02d}.xy")
    return time_dir


def test_process_case_basic(tmp_path):
    """process_case should produce one record per span with finite T values."""
    spans = ["lower_leg", "left_lower_leg", "test_section_span",
             "left_upper_leg", "upper_leg", "right_leg"]
    T_s00 = 450.0
    T_s04 = 460.0
    _make_fake_secmean_dir(tmp_path, spans, T_s00, T_s04)

    records = m.process_case(tmp_path, "test_case", "test_source")
    assert len(records) == len(spans)
    for r in records:
        assert r["status_s00"] == "ok"
        assert r["status_s04"] == "ok"
        assert math.isfinite(r["T_s00_bulk_k"])
        assert math.isfinite(r["T_s04_bulk_k"])
        assert abs(r["T_s00_bulk_k"] - T_s00) < 0.5
        assert abs(r["T_s04_bulk_k"] - T_s04) < 0.5


def test_process_case_right_leg_inlet_outlet_swapped(tmp_path):
    """For right_leg (downcomer), T_in = T_s04, T_out = T_s00."""
    T_s00 = 465.0  # top of downcomer (outlet) — cooler
    T_s04 = 445.0  # bottom of downcomer (inlet? no — convention: s00 is one end, s04 the other)
    _make_fake_secmean_dir(tmp_path, ["right_leg"], T_s00, T_s04)

    records = m.process_case(tmp_path, "test_case", "test_source")
    rl = next(r for r in records if r["span"] == "right_leg")
    assert rl["flow_dir"] == "s04_to_s00"
    # For right_leg: T_in = T_s04, T_out = T_s00
    assert abs(rl["T_in_bulk_k"] - T_s04) < 0.5
    assert abs(rl["T_out_bulk_k"] - T_s00) < 0.5


def test_process_case_delta_t_sign_heater(tmp_path):
    """Heater span (lower_leg, FLOW_DIRECTION=-1): T_in=T_s04, T_out=T_s00, delta_T = T_s00 - T_s04 > 0."""
    T_s00, T_s04 = 462.0, 448.0  # lower_leg flows s04→s00; s04 is heater inlet (cooler)
    _make_fake_secmean_dir(tmp_path, ["lower_leg"], T_s00, T_s04)
    records = m.process_case(tmp_path, "test_case", "test_source")
    ll = next(r for r in records if r["span"] == "lower_leg")
    assert ll["flow_dir"] == "s04_to_s00"
    assert ll["delta_T_flow_dir_k"] > 0
    assert abs(ll["delta_T_flow_dir_k"] - (T_s00 - T_s04)) < 0.5


def test_process_case_delta_t_sign_upcomer(tmp_path):
    """Upcomer span (left_upper_leg, FLOW_DIRECTION=+1): T_in=T_s00, T_out=T_s04, delta_T > 0 for heating."""
    T_s00, T_s04 = 448.0, 462.0  # fluid heated as it travels s00→s04
    _make_fake_secmean_dir(tmp_path, ["left_upper_leg"], T_s00, T_s04)
    records = m.process_case(tmp_path, "test_case", "test_source")
    lu = next(r for r in records if r["span"] == "left_upper_leg")
    assert lu["flow_dir"] == "s00_to_s04"
    assert lu["delta_T_flow_dir_k"] > 0
    assert abs(lu["delta_T_flow_dir_k"] - (T_s04 - T_s00)) < 0.5


# -------------------------------------------------------------------------
# Sanity check on real Salt 2 data (skip if not present)
# -------------------------------------------------------------------------

@pytest.mark.skipif(not REAL_SECMEAN.is_dir(), reason="real secmeanSurfaces not on this machine")
def test_real_salt2_lower_leg_temperature_range():
    """lower_leg bulk T at s00 and s04 should be in [430, 500] K."""
    xy_s00 = REAL_SECMEAN / "plane_lower_leg__s00.xy"
    xy_s04 = REAL_SECMEAN / "plane_lower_leg__s04.xy"
    r00 = m.bulk_t_from_xy(xy_s00)
    r04 = m.bulk_t_from_xy(xy_s04)
    assert r00["status"] == "ok", f"s00 status: {r00['status']}"
    assert r04["status"] == "ok", f"s04 status: {r04['status']}"
    assert 430 < r00["T_bulk_k"] < 500, f"T_s00 = {r00['T_bulk_k']:.1f} K out of range"
    assert 430 < r04["T_bulk_k"] < 500, f"T_s04 = {r04['T_bulk_k']:.1f} K out of range"


@pytest.mark.skipif(not REAL_SECMEAN.is_dir(), reason="real secmeanSurfaces not on this machine")
def test_real_salt2_all_spans_readable():
    """All 6 SPANS should return ok status for s00 and s04 in the real Salt 2 case.

    Uses T_fwd_bulk_k for range check — mixing-cup T is allowed to be outside physical
    range at high-recirculation cut planes (e.g. left_lower_leg s00 ~90% recirc).
    """
    for span in m.SPANS:
        for idx in [0, 4]:
            xy = REAL_SECMEAN / f"plane_{span}__s{idx:02d}.xy"
            if not xy.is_file():
                pytest.skip(f"File not found: {xy}")
            r = m.bulk_t_from_xy(xy)
            assert r.get("status") == "ok", (
                f"span={span}, s{idx:02d}: status={r.get('status')}"
            )
            # Forward-bulk T should always be in the physical operating range
            t_fwd = r["T_fwd_bulk_k"]
            assert 420 < t_fwd < 520, (
                f"span={span}, s{idx:02d}: T_fwd_bulk={t_fwd:.1f} K out of range"
            )
            # Print recirculation info for documentation
            rc = r.get("recirculation_ratio", 0)
            if rc > 0.5:
                print(f"  High recirculation: span={span}, s{idx:02d}: "
                      f"recirc={rc:.1%}, T_bulk={r['T_bulk_k']:.1f} K (mixing-cup), "
                      f"T_fwd={t_fwd:.1f} K")
