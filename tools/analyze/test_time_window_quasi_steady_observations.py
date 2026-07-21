#!/usr/bin/env python3
"""Synthetic tests for quasi-steady time-window curation."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.analyze.build_time_window_quasi_steady_observations as tq  # noqa: E402


def _series(times: np.ndarray, values: np.ndarray) -> list[dict[str, float]]:
    return [{"time": float(t), "value": float(v)} for t, v in zip(times, values)]


def _spec(values: np.ndarray, times: np.ndarray | None = None) -> tq.SeriesSpec:
    if times is None:
        times = np.arange(values.size, dtype=float)
    return tq.SeriesSpec(
        qoi_name="mdot::synthetic",
        qoi_units="kg/s",
        role="hydraulic",
        source_path="synthetic",
        series=_series(times, values),
    )


def _policy(**overrides: object) -> tq.WindowPolicy:
    values = {
        "stationary_drift": 0.01,
        "stationary_amp": 0.02,
        "quasi_drift": 0.05,
        "quasi_amp": 0.10,
        "min_samples": 20,
        "min_duration_s": 10.0,
        "block_count": 5,
        "min_cycles_for_oscillation": 1.5,
    }
    values.update(overrides)
    return tq.WindowPolicy(**values)


def _assess(
    values: np.ndarray,
    *,
    times: np.ndarray | None = None,
    target_value: float | None = None,
    needs_special_gate_scrutiny: bool = False,
    policy: tq.WindowPolicy | None = None,
) -> dict[str, object]:
    return tq.assess_window(
        source_id="synthetic_case",
        case_dir=Path("/tmp/synthetic_case"),
        spec=_spec(values, times),
        window_frac=1.0,
        policy=policy or _policy(),
        target_value=target_value,
        needs_special_gate_scrutiny=needs_special_gate_scrutiny,
    )


def test_stationary_correlated_noise_is_admissible_with_neff_below_n():
    rng = np.random.default_rng(123)
    n = 500
    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = 0.85 * noise[i - 1] + rng.normal(0.0, 5.0e-4)
    row = _assess(1.0 + noise)

    assert row["window_state"] == "stationary"
    assert row["fit_use_status"] == "fit_admissible"
    assert float(row["effective_sample_size"]) < row["n_samples"]
    assert float(row["uncertainty_total"]) >= float(row["uncertainty_random"])


def test_monotonic_drift_is_not_misclassified_as_oscillation():
    values = np.linspace(1.0, 1.35, 300)
    row = _assess(values)

    assert row["window_state"] == "moving_not_plateaued"
    assert row["fit_use_status"] == "excluded_drifting"
    assert float(row["drift_rel"]) > 0.05


def test_persistent_sinusoid_keeps_oscillation_uncertainty_floor():
    times = np.linspace(0.0, 120.0, 600)
    values = 1.0 + 0.09 * np.sin(2.0 * math.pi * times / 20.0)
    row = _assess(values, times=times)

    assert row["window_state"] == "oscillatory_not_steady"
    assert row["fit_use_status"] == "excluded_oscillatory"
    assert 15.0 <= float(row["dominant_period_s"]) <= 25.0
    assert float(row["uncertainty_oscillation"]) > float(row["uncertainty_random"])
    assert float(row["uncertainty_total"]) >= float(row["uncertainty_oscillation"])


def test_short_or_early_terminated_window_is_excluded():
    row = _assess(np.ones(8), policy=_policy(min_samples=20, min_duration_s=10.0))

    assert row["window_state"] == "short_or_early_terminated"
    assert row["fit_use_status"] == "excluded_short"
    assert "requires" in str(row["notes"])


def test_pass_through_target_requires_transient_model():
    values = np.linspace(0.5, 1.5, 300)
    row = _assess(values, target_value=1.0)

    assert row["window_state"] == "transient_model_only"
    assert row["fit_use_status"] == "transient_model_required"
    assert row["pass_through_risk"] is True


def test_special_gate_source_blocks_otherwise_admissible_window():
    row = _assess(np.ones(300), needs_special_gate_scrutiny=True)

    assert row["window_state"] == "stationary"
    assert row["fit_use_status"] == "excluded_gate_pending"
    assert row["needs_special_gate_scrutiny"] is True


def test_multiple_windows_share_independence_group_and_primary_prefers_longest():
    spec = _spec(np.ones(300))
    rows = [
        tq.assess_window(
            source_id="same_path",
            case_dir=Path("/tmp/same_path"),
            spec=spec,
            window_frac=frac,
            policy=_policy(),
        )
        for frac in (0.50, 0.25)
    ]
    tq.select_primary(rows)

    assert rows[0]["independence_group_id"] == rows[1]["independence_group_id"]
    assert sum(1 for row in rows if row["is_primary_window"]) == 1
    primary = [row for row in rows if row["is_primary_window"]][0]
    assert primary["window_fraction"] == 0.50
