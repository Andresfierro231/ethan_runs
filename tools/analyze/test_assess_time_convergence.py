#!/usr/bin/env python3
"""Tests for assess_time_convergence.py, focused on the T3 operating-point gate.

The gate distinguishes a genuinely re-equilibrated perturbation run (mdot moved
from nominal by ~the Q^(1/3) expectation AND re-plateaued) from a FALSE-STEADY run
(flat but pinned at the nominal fixed point). We build tiny synthetic postProcessing
trees and assert the verdicts.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.analyze.assess_time_convergence as atc  # noqa: E402


def _args(**over) -> argparse.Namespace:
    ns = argparse.Namespace(
        window_frac=0.25, stationary_drift=0.01, stationary_amp=0.02,
        quasi_drift=0.05, quasi_amp=0.10, require_moved_from=None,
        expected_q_ratio=None, expected_move_frac=None, move_tolerance=0.5,
        tau_thermal=None, min_tau_advance=3.0, source_id="test",
    )
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


def _write_mdot(pp: Path, restart: float, t_end: float, value: float,
                extra_zero_seg: bool = False) -> None:
    """Write a flat mdot monitor with one (or two) restart segments."""
    for mon in atc.MDOT_MONITOR_DIRS:
        base = pp / mon
        if extra_zero_seg:
            _seg(base / "0", 0.0, restart, value)
        _seg(base / str(restart), restart, t_end, value)


def _seg(seg_dir: Path, t0: float, t1: float, value: float) -> None:
    seg_dir.mkdir(parents=True, exist_ok=True)
    times = np.arange(t0, t1 + 1.0, 1.0)
    lines = ["# faceZone", "# Time\tsum(phi)"]
    for t in times:
        # tiny bounded oscillation so it reads as stationary, not perfectly constant
        v = value * (1.0 + 1e-4 * np.sin(t))
        lines.append(f"{t:.6g}\t{v:.9e}")
    (seg_dir / "surfaceFieldValue.dat").write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# expected_move_frac / Q^(1/3) scaling
# ---------------------------------------------------------------------------

def test_expected_move_frac_q_cube_root():
    # +10% Q -> ~3.23% expected mdot move
    assert abs(atc.expected_move_frac(_args(expected_q_ratio=1.10)) - 0.03228) < 1e-4
    # -10% Q -> ~3.45%
    assert abs(atc.expected_move_frac(_args(expected_q_ratio=0.90)) - 0.03451) < 1e-4
    # explicit override wins
    assert atc.expected_move_frac(_args(expected_move_frac=0.02, expected_q_ratio=1.1)) == 0.02
    # nothing supplied
    assert atc.expected_move_frac(_args()) is None


# ---------------------------------------------------------------------------
# restart-time detection
# ---------------------------------------------------------------------------

def test_restart_time_single_segment(tmp_path):
    pp = tmp_path / "postProcessing"
    _write_mdot(pp, restart=2431.0, t_end=2600.0, value=-0.0132)
    rt = atc.restart_time_from_segments(pp / atc.MDOT_MONITOR_DIRS[0])
    assert rt == 2431.0


def test_restart_time_skips_inherited_zero_segment(tmp_path):
    pp = tmp_path / "postProcessing"
    _write_mdot(pp, restart=2514.0, t_end=2700.0, value=-0.015, extra_zero_seg=True)
    rt = atc.restart_time_from_segments(pp / atc.MDOT_MONITOR_DIRS[0])
    assert rt == 2514.0  # not 0.0


# ---------------------------------------------------------------------------
# gate verdicts
# ---------------------------------------------------------------------------

def test_false_steady_pinned_at_nominal(tmp_path):
    """+10% Q but mdot pinned at nominal -> false_steady (the real perturbation bug)."""
    pp = tmp_path / "postProcessing"
    nominal = -0.0132
    _write_mdot(pp, restart=2431.0, t_end=8000.0, value=nominal)  # did NOT move
    res = atc.assess_case("false", tmp_path,
                          _args(require_moved_from=nominal, expected_q_ratio=1.10))
    op = res["operating_point"]
    assert op["verdict"] == "false_steady"
    assert op["usable_for_correlation"] is False
    assert abs(op["pct_moved"]) < 0.005


def test_requalified_when_moved_and_plateaued(tmp_path):
    """+10% Q and mdot moved ~+3.2% and flat -> requalified (usable)."""
    pp = tmp_path / "postProcessing"
    nominal = -0.0132
    moved = nominal * 1.032  # +3.2%, matches Q^(1/3)
    _write_mdot(pp, restart=2431.0, t_end=8000.0, value=moved)
    res = atc.assess_case("good", tmp_path,
                          _args(require_moved_from=nominal, expected_q_ratio=1.10))
    op = res["operating_point"]
    assert op["verdict"] == "requalified"
    assert op["usable_for_correlation"] is True


def test_too_short_flag_with_tau(tmp_path):
    """Moved + plateaued but advance << min_tau_advance*tau -> too_short."""
    pp = tmp_path / "postProcessing"
    nominal = -0.0132
    moved = nominal * 1.032
    _write_mdot(pp, restart=2431.0, t_end=2600.0, value=moved)  # advance ~169 s
    res = atc.assess_case("short", tmp_path,
                          _args(require_moved_from=nominal, expected_q_ratio=1.10,
                                tau_thermal=1000.0, min_tau_advance=3.0))
    op = res["operating_point"]
    assert op["too_short"] is True
    assert op["verdict"] == "too_short"


def test_gate_not_applied_without_flag(tmp_path):
    pp = tmp_path / "postProcessing"
    _write_mdot(pp, restart=2431.0, t_end=8000.0, value=-0.0132)
    res = atc.assess_case("noflag", tmp_path, _args())
    assert "operating_point" not in res
