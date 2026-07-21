"""
test_pressure_term_ledger.py — TODO-PRESSURE-TERM-LEDGER, 2026-07-08

Pytest tests for the pressure term ledger.  Tests run against the GENERATED
CSV at work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv.
Run build_pressure_term_ledger.py first, or use the fixture that calls it.

Tests:
  1. All 18 rows present (3 cases × 6 spans)
  2. f_debuoyed matches f_corrected from momentum_budget within 1%
  3. |residual_fraction| < 0.05 for main legs
  4. recirculation_flag is True only for left_lower_leg and left_upper_leg
  5. Required columns are present
  6. test_section_span residual documented (not failed)
  7. minor_loss_upper_bound_flag is True where minor_loss_pa > 0
  8. development_loss_pa >= 0 everywhere
  9. x_plus > 0 everywhere
 10. development_loss_pa == 0.0 for non-entry spans (AGENT-197 fix)
 11. flow_reset_flag is False for non-entry spans, True for entry spans (AGENT-197 fix)
"""

from __future__ import annotations

import csv
import math
import pathlib
import subprocess
import sys

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERE = pathlib.Path(__file__).resolve()
WORKSPACE_ROOT = HERE.parent.parent.parent

LEDGER_CSV = (
    WORKSPACE_ROOT
    / "work_products"
    / "2026-07-08_pressure_term_ledger"
    / "pressure_term_ledger.csv"
)
MOMENTUM_CSV = (
    WORKSPACE_ROOT
    / "work_products"
    / "2026-07-01_claude_momentum_budget"
    / "momentum_budget.csv"
)
SCRIPT = HERE.parent / "build_pressure_term_ledger.py"

SOURCE_IDS = [
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
]
SPANS = [
    "lower_leg",
    "right_leg",
    "left_lower_leg",
    "test_section_span",
    "left_upper_leg",
    "upper_leg",
]
MAIN_SPANS = {"lower_leg", "right_leg", "left_lower_leg", "left_upper_leg", "upper_leg"}
RECIRCULATION_SPANS = {"left_lower_leg", "left_upper_leg"}

REQUIRED_COLUMNS = [
    "source_id", "case_id", "run_class", "mesh_level", "mesh_status",
    "source_case_root", "source_window_start_s", "source_window_end_s",
    "geometry_source", "pressure_method", "span", "station_start_label",
    "station_end_label", "station_count_used", "L_m", "D_h_m", "Re",
    "rho_kg_m3", "u_bulk_m_s", "q_ref_pa", "x_plus", "p_rgh_start_pa",
    "p_rgh_end_pa", "dynamic_head_start_pa", "dynamic_head_end_pa",
    "total_pressure_proxy_start_pa", "total_pressure_proxy_end_pa",
    "dp_rgh_dxi_pa_m", "gh_drho_dxi_pa_m", "rho_u_du_dxi_pa_m",
    "gross_static_dp_pa", "buoyancy_contribution_pa",
    "distributed_friction_pa", "development_loss_pa", "minor_loss_pa",
    "minor_loss_K", "minor_loss_upper_bound_flag", "recirculation_flag",
    "flow_reset_flag", "residual_assignment", "buoyancy_counting_policy",
    "residual_pa", "residual_fraction", "f_debuoyed", "f_lam_64_over_re",
    "f_debuoyed_over_flam", "fit_eligible", "validation_eligible",
    "fit_use_status", "quality_flags", "admission_note",
]

# Spans that receive already-developed inflow — Shah entry assumption does not apply.
# The three contiguous upcomer sub-spans: left_lower_leg → test_section_span → left_upper_leg
# Only left_lower_leg gets a fresh entry (after the lower-left bend).
NON_ENTRY_SPANS = {"test_section_span", "left_upper_leg"}
ENTRY_SPANS = {"lower_leg", "right_leg", "left_lower_leg", "upper_leg"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def ledger_rows():
    """Load the generated ledger CSV; regenerate if missing."""
    if not LEDGER_CSV.exists():
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            pytest.fail(
                f"build_pressure_term_ledger.py failed:\n{result.stderr}"
            )
    assert LEDGER_CSV.exists(), f"Ledger CSV not found: {LEDGER_CSV}"
    with LEDGER_CSV.open() as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="session")
def momentum_rows():
    """Load momentum_budget.csv for cross-reference checks."""
    assert MOMENTUM_CSV.exists(), f"Momentum budget CSV not found: {MOMENTUM_CSV}"
    with MOMENTUM_CSV.open() as fh:
        return {
            (row["source_id"], row["span"]): row
            for row in csv.DictReader(fh)
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _f(row, key):
    val = row[key]
    if val in ("NaN", "nan", ""):
        return float("nan")
    if val in ("True", "true"):
        return True
    if val in ("False", "false"):
        return False
    return float(val)


def _bool(row, key):
    return row[key] in ("True", "true", "1")


# ---------------------------------------------------------------------------
# Test 1: Row count
# ---------------------------------------------------------------------------

def test_row_count(ledger_rows):
    """18 rows (3 cases × 6 spans) must be present."""
    assert len(ledger_rows) == 18, (
        f"Expected 18 rows, got {len(ledger_rows)}"
    )
    found_keys = {(r["source_id"], r["span"]) for r in ledger_rows}
    expected_keys = {(s, sp) for s in SOURCE_IDS for sp in SPANS}
    missing = expected_keys - found_keys
    assert not missing, f"Missing (source_id, span) combinations: {missing}"


# ---------------------------------------------------------------------------
# Test 2: f_debuoyed round-trip within 1% of f_corrected
# ---------------------------------------------------------------------------

def test_f_debuoyed_roundtrip(ledger_rows, momentum_rows):
    """f_debuoyed must match f_corrected from momentum_budget within 1%."""
    failures = []
    for row in ledger_rows:
        key = (row["source_id"], row["span"])
        f_debuoyed = _f(row, "f_debuoyed")
        # f_corrected_ref is an optional extra column; fall back to momentum CSV
        if "f_corrected_ref" in row and row["f_corrected_ref"] not in ("", "NaN"):
            f_ref = float(row["f_corrected_ref"])
        else:
            f_ref = float(momentum_rows[key]["f_corrected"])
        if math.isnan(f_debuoyed) or abs(f_ref) < 1e-12:
            failures.append(f"{key}: f_debuoyed is NaN or f_ref~0")
            continue
        err_pct = 100 * abs(f_debuoyed - f_ref) / abs(f_ref)
        if err_pct > 1.0:
            failures.append(
                f"{key}: f_debuoyed={f_debuoyed:.6f}, f_ref={f_ref:.6f}, err={err_pct:.3f}%"
            )
    assert not failures, "f_debuoyed round-trip failures:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Test 3: |residual_fraction| < 0.05 for main legs
# ---------------------------------------------------------------------------

def test_residual_fraction_main_legs(ledger_rows):
    """
    |residual_fraction| < 0.05 for main-leg spans.
    Residual is normalized by distributed_friction_pa (always positive).
    The residual reflects: -(development_loss + minor_loss) / distributed.
    For spans with bends and entry effects, residual is O(0.05–0.15) — acceptable
    for this ledger which verifies budget closure before adding extra loss terms.

    Note: 'before extra losses' means we check the budget identity closure itself.
    After subtracting dev and minor from a closed budget, residual = -(dev+minor)/dist.
    Main legs with larger L_m typically have smaller residual_fraction.
    """
    # First verify momentum budget identity closes (residual before dev+minor ~ 0)
    failures = []
    for row in ledger_rows:
        if row["span"] not in MAIN_SPANS:
            continue
        rf = _f(row, "residual_fraction")
        if math.isnan(rf):
            failures.append(f"{row['source_id']}/{row['span']}: residual_fraction is NaN")
            continue
        if abs(rf) >= 0.05:
            failures.append(
                f"{row['source_id']}/{row['span']}: |residual_fraction|={abs(rf):.4f} >= 0.05"
            )
    assert not failures, (
        "residual_fraction out of tolerance for main legs:\n" + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Test 4: recirculation_flag only for left_lower_leg and left_upper_leg
# ---------------------------------------------------------------------------

def test_recirculation_flag(ledger_rows):
    """recirculation_flag must be True only for left_lower_leg and left_upper_leg."""
    wrong = []
    for row in ledger_rows:
        flag = _bool(row, "recirculation_flag")
        span = row["span"]
        should_be_true = span in RECIRCULATION_SPANS
        if flag != should_be_true:
            wrong.append(
                f"{row['source_id']}/{span}: flag={flag}, expected={should_be_true}"
            )
    assert not wrong, "recirculation_flag mismatch:\n" + "\n".join(wrong)


# ---------------------------------------------------------------------------
# Test 5: Required columns present
# ---------------------------------------------------------------------------

def test_required_columns(ledger_rows):
    """All required columns must be present in the ledger CSV."""
    if not ledger_rows:
        pytest.skip("No rows loaded")
    actual_cols = set(ledger_rows[0].keys())
    missing = set(REQUIRED_COLUMNS) - actual_cols
    assert not missing, f"Missing columns: {missing}"


# ---------------------------------------------------------------------------
# Test 6: test_section_span residual documented (informational, not failed)
# ---------------------------------------------------------------------------

def test_test_section_span_documented(ledger_rows):
    """
    test_section_span may have larger residual due to junction effects not captured
    by the four main bends.  This test verifies the span IS present and documents
    its residual but does NOT fail if |residual_fraction| >= 0.05.
    """
    test_rows = [r for r in ledger_rows if r["span"] == "test_section_span"]
    assert len(test_rows) == 3, (
        f"Expected 3 test_section_span rows, got {len(test_rows)}"
    )
    for row in test_rows:
        rf = _f(row, "residual_fraction")
        # Just print for diagnostic purposes; no assertion on magnitude
        print(
            f"test_section_span residual_fraction: "
            f"{row['source_id']}: {rf:.4f}"
        )


# ---------------------------------------------------------------------------
# Test 7: minor_loss_upper_bound_flag where minor_loss_pa > 0
# ---------------------------------------------------------------------------

def test_minor_loss_upper_bound_flag(ledger_rows):
    """minor_loss_upper_bound_flag must be True exactly where minor_loss_pa > 0."""
    failures = []
    for row in ledger_rows:
        pa = _f(row, "minor_loss_pa")
        flag = _bool(row, "minor_loss_upper_bound_flag")
        expected_flag = pa > 0.0
        if flag != expected_flag:
            failures.append(
                f"{row['source_id']}/{row['span']}: "
                f"minor_loss_pa={pa:.4f}, flag={flag}"
            )
    assert not failures, "minor_loss_upper_bound_flag mismatch:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Test 8: development_loss_pa >= 0 everywhere
# ---------------------------------------------------------------------------

def test_development_loss_nonnegative(ledger_rows):
    """development_loss_pa must be >= 0 everywhere (Shah >= F1 always)."""
    failures = []
    for row in ledger_rows:
        dl = _f(row, "development_loss_pa")
        if math.isnan(dl) or dl < -1e-10:
            failures.append(
                f"{row['source_id']}/{row['span']}: development_loss_pa={dl:.6f}"
            )
    assert not failures, "Negative development_loss_pa:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Test 9: x_plus > 0 everywhere
# ---------------------------------------------------------------------------

def test_x_plus_positive(ledger_rows):
    """x_plus = L / (D_h × Re) must be positive for all spans."""
    failures = []
    for row in ledger_rows:
        xp = _f(row, "x_plus")
        if math.isnan(xp) or xp <= 0:
            failures.append(
                f"{row['source_id']}/{row['span']}: x_plus={xp}"
            )
    assert not failures, "Non-positive x_plus:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Test 10: development_loss_pa == 0.0 for non-entry spans (AGENT-197 fix)
# ---------------------------------------------------------------------------

def test_development_loss_zero_for_non_entry_spans(ledger_rows):
    """
    development_loss_pa must be exactly 0.0 for non-entry spans
    (test_section_span, left_upper_leg).

    These spans receive already-developed inflow from the preceding sub-span
    (left_lower_leg → test_section_span → left_upper_leg).  Applying the Shah
    flat-inlet entry assumption to them is physically incorrect and causes
    dev_frac > 1.0 for Salt 3/4 (AGENT-197 fix).
    """
    failures = []
    for row in ledger_rows:
        if row["span"] not in NON_ENTRY_SPANS:
            continue
        dl = _f(row, "development_loss_pa")
        if math.isnan(dl) or abs(dl) > 1e-12:
            failures.append(
                f"{row['source_id']}/{row['span']}: development_loss_pa={dl} (expected 0.0)"
            )
    assert not failures, (
        "Non-zero development_loss_pa for non-entry spans:\n" + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Test 11: flow_reset_flag — False for non-entry spans, True for entry spans
# ---------------------------------------------------------------------------

def test_flow_reset_flag(ledger_rows):
    """
    flow_reset_flag must be:
      False for test_section_span and left_upper_leg (developed inflow)
      True  for lower_leg, right_leg, left_lower_leg, upper_leg (fresh entry after bend)

    AGENT-197 adds this column to make the entry assumption explicit and auditable.
    """
    failures = []
    for row in ledger_rows:
        span = row["span"]
        flag = _bool(row, "flow_reset_flag")
        if span in NON_ENTRY_SPANS:
            if flag:
                failures.append(
                    f"{row['source_id']}/{span}: flow_reset_flag=True, expected False"
                )
        elif span in ENTRY_SPANS:
            if not flag:
                failures.append(
                    f"{row['source_id']}/{span}: flow_reset_flag=False, expected True"
                )
        else:
            failures.append(f"{row['source_id']}/{span}: span not in NON_ENTRY_SPANS or ENTRY_SPANS")
    assert not failures, "flow_reset_flag mismatch:\n" + "\n".join(failures)


def test_station_endpoint_and_window_metadata_present(ledger_rows):
    """Every row must carry fit-ready station endpoints and source-window metadata."""
    failures = []
    for row in ledger_rows:
        for key in [
            "source_window_start_s",
            "source_window_end_s",
            "station_start_label",
            "station_end_label",
            "p_rgh_start_pa",
            "p_rgh_end_pa",
            "dynamic_head_start_pa",
            "dynamic_head_end_pa",
            "total_pressure_proxy_start_pa",
            "total_pressure_proxy_end_pa",
        ]:
            if row.get(key, "") == "":
                failures.append(f"{row['source_id']}/{row['span']}: missing {key}")
        if row["station_start_label"] == row["station_end_label"]:
            failures.append(f"{row['source_id']}/{row['span']}: endpoint labels are identical")
        if float(row["source_window_end_s"]) < float(row["source_window_start_s"]):
            failures.append(f"{row['source_id']}/{row['span']}: source window end precedes start")
    assert not failures, "Missing station/window metadata:\n" + "\n".join(failures)


def test_buoyancy_terms_are_reported_not_fit_as_friction(ledger_rows):
    """The density-gradient buoyancy term must remain separate from fit friction."""
    for row in ledger_rows:
        assert row["buoyancy_counting_policy"] == "density_gradient_buoyancy_reported_separately_not_fit_as_friction"
        assert row["pressure_method"] == "streamwise_momentum_budget_debuoyed"
        assert row["gh_drho_dxi_pa_m"] not in ("", "NaN", "nan")
        assert row["distributed_mechanical_loss_pa_m"] not in ("", "NaN", "nan")


def test_residual_assignment_and_fit_status(ledger_rows):
    """Residual assignment and fit status must expose recirculation-invalid rows."""
    for row in ledger_rows:
        recirc = row["span"] in RECIRCULATION_SPANS
        if recirc:
            assert row["residual_assignment"] == "recirculation_invalid_single_stream_diagnostic"
            assert row["fit_eligible"] == "False"
            assert row["fit_use_status"] == "not_fit_recirculation"
        else:
            assert row["residual_assignment"] == "budget_identity_inertial_residual"
            assert row["fit_eligible"] == "True"
            assert row["fit_use_status"] == "fit_target"
        assert row["validation_eligible"] == "True"
