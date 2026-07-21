#!/usr/bin/env python3
"""Unit tests for build_upcomer_correlation.py.

Run from the repo root (do NOT source OpenFOAM env):
    python -m pytest tools/analyze/test_build_upcomer_correlation.py -v
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_upcomer_correlation import (  # noqa: E402
    _UPCOMER_CELL_DIR,
    _MOMENTUM_BUDGET_CSV,
    _HTC_DIR,
    CASES,
    _DATASET_FIELDS,
    _FIT_FIELDS,
    check_monotone_bf_decreasing,
    check_monotone_nu_increasing,
    compile_dataset,
    fit_backflow_linear,
    load_htc_row,
    load_momentum_budget_row,
    load_upcomer_cell_row,
    predict_backflow,
)

WORKSPACE_ROOT = ROOT


# ---------------------------------------------------------------------------
# Fixtures — build dataset from real data once per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def dataset():
    """Load the 3-point dataset from real data files."""
    return compile_dataset(
        CASES,
        _UPCOMER_CELL_DIR,
        _MOMENTUM_BUDGET_CSV,
        _HTC_DIR,
    )


@pytest.fixture(scope="session")
def fit_result(dataset):
    """Compute the OLS fit once."""
    return fit_backflow_linear(dataset)


# ---------------------------------------------------------------------------
# 1. Test that 3 rows exist in the dataset (S2, S3, S4)
# ---------------------------------------------------------------------------

def test_dataset_has_three_rows(dataset):
    """Exactly 3 cases (Salt 2, 3, 4) must be in the dataset."""
    assert len(dataset) == 3


def test_dataset_labels(dataset):
    """All three case labels must be present."""
    labels = {r["label"] for r in dataset}
    assert "salt_2_jin" in labels
    assert "salt_3_jin" in labels
    assert "salt_4_jin" in labels


# ---------------------------------------------------------------------------
# 2. Test that backflow_fraction decreases with increasing Re (monotone)
# ---------------------------------------------------------------------------

def test_backflow_monotone_decreasing_with_re(dataset):
    """backflow_fraction must fall as Re increases (S2 -> S3 -> S4)."""
    assert check_monotone_bf_decreasing(dataset), (
        "backflow_fraction is not monotone decreasing with Re_upcomer. "
        "Physical expectation: stronger forced flow (higher Re) suppresses the "
        "buoyancy-driven recirculation cell."
    )


def test_backflow_fraction_in_expected_range(dataset):
    """backflow_fraction values must lie in 0.10-0.35 for all cases (AGENT-162 finding)."""
    for row in dataset:
        bf = row["backflow_fraction"]
        assert 0.10 <= bf <= 0.35, (
            f"backflow_fraction={bf:.4f} for {row['label']} is outside the "
            "expected 15-33% range from AGENT-162"
        )


# ---------------------------------------------------------------------------
# 3. Test that Nu increases with Re (monotone)
# ---------------------------------------------------------------------------

def test_nu_monotone_increasing_with_re(dataset):
    """Nu_upcomer must rise as Re increases (S2 -> S3 -> S4)."""
    assert check_monotone_nu_increasing(dataset), (
        "Nu_upcomer is not monotone increasing with Re_upcomer. "
        "Physical expectation: higher mass flow -> better heat transfer."
    )


def test_nu_positive_and_finite(dataset):
    """Nu must be positive and finite for all cases."""
    for row in dataset:
        nu = row["Nu_upcomer"]
        assert math.isfinite(nu), f"Nu={nu} is not finite for {row['label']}"
        assert nu > 0.0, f"Nu={nu} <= 0 for {row['label']}"


# ---------------------------------------------------------------------------
# 4. Test that fit parameters are finite and within plausible range
# ---------------------------------------------------------------------------

def test_fit_parameters_finite(fit_result):
    """OLS parameters a and b must be finite."""
    assert math.isfinite(fit_result["a"]), "Parameter a is not finite"
    assert math.isfinite(fit_result["b"]), "Parameter b is not finite"


def test_fit_parameter_a_positive_small(fit_result):
    """Intercept a must be in (0, 0.2): physically an asymptotic backflow floor."""
    a = fit_result["a"]
    assert 0.0 < a < 0.2, (
        f"a={a:.5f} is outside physically plausible range (0, 0.2). "
        "The intercept represents the asymptotic backflow fraction at high Re."
    )


def test_fit_parameter_b_positive(fit_result):
    """Coefficient b must be positive: backflow increases as Re decreases."""
    b = fit_result["b"]
    assert b > 0.0, (
        f"b={b:.4f} is not positive. "
        "Physical expectation: b/Re term must be positive (higher Re -> lower bf)."
    )


def test_fit_prediction_matches_data(fit_result, dataset):
    """OLS predictions at calibration Re must match observed bf within tolerance."""
    a = fit_result["a"]
    b = fit_result["b"]
    for row in dataset:
        re = row["Re_upcomer"]
        bf_obs = row["backflow_fraction"]
        bf_pred = predict_backflow(a, b, re)
        err = abs(bf_pred - bf_obs)
        assert err < 0.01, (
            f"Prediction error {err:.5f} > 0.01 for {row['label']} "
            f"(Re={re:.1f}, obs={bf_obs:.4f}, pred={bf_pred:.4f})"
        )


# ---------------------------------------------------------------------------
# 5. Test column presence in both output CSVs
# ---------------------------------------------------------------------------

def test_dataset_columns_present(dataset):
    """All required dataset columns must be present in every row."""
    required = [
        "label", "source_id", "Re_upcomer", "Re_section_median",
        "Ri_median", "Ra_median", "Pr_median",
        "backflow_fraction", "recirculation_intensity",
        "Nu_upcomer", "htc_wm2k", "T_bulk_K",
        "u_bulk_m_s",
    ]
    for row in dataset:
        for col in required:
            assert col in row, f"Column '{col}' missing in row for {row.get('label')}"


def test_fit_columns_present(fit_result):
    """All required fit columns must be present in the fit result dict."""
    required = [
        "model", "a", "b", "a_se_ols", "b_se_ols",
        "a_jk_std", "b_jk_std",
        "residual_sse", "sigma_hat", "n_points", "dof",
        "Re_min_calibration", "Re_max_calibration",
        "bf_asymptote_high_Re",
        "onset_Re_route_A_low", "onset_Re_route_A_high",
        "onset_Re_route_B_low", "onset_Re_route_B_high",
        "note_onset_re", "note_extrapolation",
    ]
    for col in required:
        assert col in fit_result, f"Fit result missing key '{col}'"


# ---------------------------------------------------------------------------
# 6. Test output CSV files exist and have correct row counts
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def output_dir():
    from tools.common import WORKSPACE_ROOT
    return WORKSPACE_ROOT / "work_products" / "2026-07-07_upcomer_correlation_v2"


def test_dataset_csv_exists(output_dir):
    """upcomer_dataset.csv must exist after main() is run."""
    p = output_dir / "upcomer_dataset.csv"
    if not p.exists():
        pytest.skip("upcomer_dataset.csv not yet generated; run main() first")
    assert p.stat().st_size > 0


def test_dataset_csv_has_three_data_rows(output_dir):
    """upcomer_dataset.csv must have exactly 3 data rows (header + 3)."""
    p = output_dir / "upcomer_dataset.csv"
    if not p.exists():
        pytest.skip("upcomer_dataset.csv not yet generated; run main() first")
    with p.open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 3, f"Expected 3 data rows, got {len(rows)}"


def test_fit_csv_exists(output_dir):
    """upcomer_correlation_fit.csv must exist after main() is run."""
    p = output_dir / "upcomer_correlation_fit.csv"
    if not p.exists():
        pytest.skip("upcomer_correlation_fit.csv not yet generated; run main() first")
    assert p.stat().st_size > 0


def test_fit_csv_has_required_columns(output_dir):
    """upcomer_correlation_fit.csv must contain model, a, b columns."""
    p = output_dir / "upcomer_correlation_fit.csv"
    if not p.exists():
        pytest.skip("upcomer_correlation_fit.csv not yet generated; run main() first")
    with p.open() as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    assert len(rows) == 1, f"Expected 1 fit row, got {len(rows)}"
    for col in ("model", "a", "b", "a_se_ols", "b_se_ols"):
        assert col in fieldnames, f"Column '{col}' missing from fit CSV"


# ---------------------------------------------------------------------------
# 7. Pure function unit tests
# ---------------------------------------------------------------------------

def test_predict_backflow_formula():
    """predict_backflow(a, b, Re) = a + b/Re."""
    a, b, Re = 0.054, 15.0, 100.0
    expected = 0.054 + 15.0 / 100.0
    assert predict_backflow(a, b, Re) == pytest.approx(expected)


def test_predict_backflow_negative_re_is_nan():
    """predict_backflow with non-positive Re must return NaN."""
    assert math.isnan(predict_backflow(0.05, 10.0, 0.0))
    assert math.isnan(predict_backflow(0.05, 10.0, -1.0))


def test_fit_backflow_linear_exact_two_point():
    """With 2 points and 2 params, the fit must be exact (SSE ~ 0)."""
    data = [
        {"Re_upcomer": 100.0, "backflow_fraction": 0.20, "Nu_upcomer": 3.0},
        {"Re_upcomer": 200.0, "backflow_fraction": 0.12, "Nu_upcomer": 4.0},
    ]
    result = fit_backflow_linear(data)
    assert math.isfinite(result["a"])
    assert math.isfinite(result["b"])
    # Verify exact reconstruction
    assert predict_backflow(result["a"], result["b"], 100.0) == pytest.approx(0.20, abs=1e-8)
    assert predict_backflow(result["a"], result["b"], 200.0) == pytest.approx(0.12, abs=1e-8)


def test_fit_backflow_linear_too_few_points():
    """fit_backflow_linear must raise ValueError with fewer than 2 points."""
    with pytest.raises(ValueError, match="at least 2"):
        fit_backflow_linear([{"Re_upcomer": 100.0, "backflow_fraction": 0.20}])


def test_monotone_bf_check_pass():
    """check_monotone_bf_decreasing should return True for strictly decreasing bf."""
    data = [
        {"Re_upcomer": 70.0, "backflow_fraction": 0.28},
        {"Re_upcomer": 100.0, "backflow_fraction": 0.22},
        {"Re_upcomer": 140.0, "backflow_fraction": 0.17},
    ]
    assert check_monotone_bf_decreasing(data) is True


def test_monotone_bf_check_fail():
    """check_monotone_bf_decreasing should return False if bf is not decreasing."""
    data = [
        {"Re_upcomer": 70.0, "backflow_fraction": 0.17},
        {"Re_upcomer": 100.0, "backflow_fraction": 0.22},
        {"Re_upcomer": 140.0, "backflow_fraction": 0.28},
    ]
    assert check_monotone_bf_decreasing(data) is False


def test_monotone_nu_check_pass():
    """check_monotone_nu_increasing should return True for strictly increasing Nu."""
    data = [
        {"Re_upcomer": 70.0, "Nu_upcomer": 3.1},
        {"Re_upcomer": 100.0, "Nu_upcomer": 4.1},
        {"Re_upcomer": 140.0, "Nu_upcomer": 5.0},
    ]
    assert check_monotone_nu_increasing(data) is True


def test_load_upcomer_cell_row_missing_label():
    """load_upcomer_cell_row must raise ValueError for a non-existent label."""
    csv_path = (
        _UPCOMER_CELL_DIR
        / "upcomer_convection_cell_viscosity_screening_salt_test_2_jin_coarse_mesh.csv"
    )
    if not csv_path.exists():
        pytest.skip("Upcomer cell CSV not found")
    with pytest.raises(ValueError, match="No row found"):
        load_upcomer_cell_row(csv_path, station_label="NONEXISTENT")


def test_load_momentum_budget_row_missing_case():
    """load_momentum_budget_row must raise ValueError for a non-existent case."""
    if not _MOMENTUM_BUDGET_CSV.exists():
        pytest.skip("Momentum budget CSV not found")
    with pytest.raises(ValueError, match="No row found"):
        load_momentum_budget_row(_MOMENTUM_BUDGET_CSV, "nonexistent_case_id")
