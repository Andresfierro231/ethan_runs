"""Unit tests for the 2026-06-30 action-item tools (AGENT-156).

Covers the pure/deterministic helpers so the science logic is regression-guarded
without needing an OpenFOAM runtime or large case data. Run with:
    python -m pytest tools/analyze/test_claude_action_items.py -q
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(mod_name: str, rel: str):
    spec = importlib.util.spec_from_file_location(mod_name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

conv = _load("assess_time_convergence", "tools/analyze/assess_time_convergence.py")
rep = _load("represent_closures_per_case", "tools/analyze/represent_closures_per_case.py")
seg = _load("validate_segment_map", "tools/analyze/validate_segment_map.py")
veldiag = _load("diagnose_section_velocity", "tools/analyze/diagnose_section_velocity.py")
recon = _load("reconcile_freeze_windows", "tools/analyze/reconcile_freeze_windows.py")


# ---- convergence: stationarity verdicts ----
class _Args:
    window_frac = 0.5
    stationary_drift = 0.01
    stationary_amp = 0.02
    quasi_drift = 0.05
    quasi_amp = 0.10


def test_constant_series_is_stationary():
    series = [{"time": float(t), "value": 5.0} for t in range(40)]
    out = conv.assess_series("flat", series, _Args())
    assert out["verdict"] == "stationary"
    assert abs(out["drift_frac_of_mean"]) < 1e-9


def test_strong_trend_is_drifting():
    series = [{"time": float(t), "value": 1.0 + 0.1 * t} for t in range(40)]
    out = conv.assess_series("ramp", series, _Args())
    assert out["verdict"] == "drifting_or_oscillatory"


def test_norm_scale_overrides_own_mean():
    # near-zero-mean residual: own-mean normalization is unusable (mean->0, frac
    # explodes/NaN); a physical scale yields a small, finite, meaningful fraction.
    import math

    series = [{"time": float(t), "value": 0.01 * (1 if t % 2 else -1)} for t in range(40)]
    own = conv.assess_series("resid", series, _Args())
    scaled = conv.assess_series("resid", series, _Args(), norm_scale=100.0)
    assert scaled["norm_basis"] == "physical_scale"
    assert own["norm_basis"] == "own_mean"
    # physical-scale fraction is finite and tiny (|value|<=0.01 over scale 100)
    assert math.isfinite(scaled["amp_frac_of_mean"]) and scaled["amp_frac_of_mean"] < 0.01
    # own-mean fraction is NOT a usable finite small number (mean ~ 0)
    assert (not math.isfinite(own["amp_frac_of_mean"])) or own["amp_frac_of_mean"] > 1.0


def test_wallheatflux_duty_split(tmp_path):
    dat = tmp_path / "wallHeatFlux.dat"
    dat.write_text(
        "# Wall heat-flux\n"
        "# Time\tpatch\tmin\tmax\tQ\tq\n"
        "1\theater\t0\t0\t100.0\t0\n"
        "1\tcooler\t0\t0\t-60.0\t0\n"
        "1\tstub\t0\t0\t0.0\t0\n"
    )
    duty = conv.parse_wallheatflux_duty(dat)
    assert duty["gross"][0]["value"] == 160.0
    assert duty["heat_in"][0]["value"] == 100.0
    assert duty["heat_out"][0]["value"] == -60.0
    assert abs(duty["net"][0]["value"] - 40.0) < 1e-9


# ---- closure representation ----
def test_power_law_fit_recovers_exponent():
    re_vals = [80.0, 120.0, 170.0]
    y_vals = [64.0 / r for r in re_vals]  # exact f = 64/Re -> b = -1
    fit = rep.power_law_fit(re_vals, y_vals)
    assert fit["status"] == "fit"
    assert abs(fit["b"] - (-1.0)) < 1e-6
    assert abs(fit["a"] - 64.0) < 1e-3


def test_overfit_flag_for_two_points():
    fit = rep.power_law_fit([100.0, 150.0], [0.6, 0.4])
    assert fit["dof"] == 0
    assert "interpolation" in fit["overfit_flag"]


def test_physical_vs_property_axis():
    assert rep.physical_case("Salt 4 Kirst") == "Salt 4"
    assert rep.property_model("Salt 4 Kirst", "x_kirst_y") == "kirst"
    assert rep.property_model("Salt 2 Jin", "x_jin_y") == "jin"


def test_pr_collinearity_detected():
    # construct Re and Pr perfectly anti-correlated (both driven by 1/mu)
    per_case = []
    for mu in (1.0, 1.5, 2.0):
        re = 100.0 / mu
        pr = 20.0 * mu
        per_case.append({"re_effective": re, "pr_effective": pr, "nu_effective": 0.1 * re**0.9})
    out = rep.assess_pr_relevance(per_case)
    assert out["status"] == "assessed"
    assert abs(out["logRe_logPr_correlation"]) > 0.99


# ---- segment map ----
def test_segment_map_owner_confirmed():
    assert seg.resolve("test_section")["maps_to"] == "test_section_span"
    assert seg.resolve("test_section")["status"] == "resolved"
    # owner-confirmed 2026-06-30
    assert seg.resolve("heated_incline")["maps_to"] == "lower_leg"
    assert seg.resolve("heated_incline")["status"] == "resolved"
    # upcomer is a confirmed composite of the three riser sections
    assert seg.resolve("upcomer")["maps_to"] == ["left_lower_leg", "test_section_span", "left_upper_leg"]
    assert seg.resolve("upcomer")["status"] == "resolved"
    assert seg.resolve("downcomer")["maps_to"] == "right_leg"
    # genuinely unknown tokens still fail loudly
    assert seg.resolve("totally_unknown_token")["status"] == "UNRESOLVED"


# ---- velocity diagnostic: the multi-leg cancellation root cause ----
def test_velocity_stats_counterflow_cancels_but_single_leg_coherent():
    # Synthetic two-leg plane: 100 faces flowing +y, 100 faces flowing -y, both
    # along the plane normal. Full plane cancels; one leg alone is coherent.
    n = np.array([0.0, 1.0, 0.0])
    up = np.tile([0.0, 0.02, 0.0], (100, 1))
    down = np.tile([0.0, -0.02, 0.0], (100, 1))
    full = veldiag._stats(np.vstack([up, down]), n)
    one_leg = veldiag._stats(up, n)
    # full plane: healthy speed, but mean vector ~0 -> alignment ~0
    assert abs(full["mean_speed_mag_U"] - 0.02) < 1e-9
    assert full["flow_alignment_meanvec_over_speed"] < 0.05
    # single leg: alignment ~1
    assert one_leg["flow_alignment_meanvec_over_speed"] > 0.99


# ---- reconcile: continuation candidate names + multi-root index ----
def test_reconcile_candidates_include_continuation():
    cands = recon.candidate_case_names("salt2_cont")
    assert "viscosity_screening_salt_test_2_jin_coarse_mesh_continuation" in cands
    # continuation variant is offered before the parent-warmup name
    assert cands.index("viscosity_screening_salt_test_2_jin_coarse_mesh_continuation") < \
           cands.index("viscosity_screening_salt_test_2_jin_coarse_mesh")
