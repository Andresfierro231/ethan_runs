from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "analyze" / "build_hydraulic_closure_rigor_audit.py"
OUT_DIR = ROOT / "work_products" / "2026-07" / "2026-07-08" / "2026-07-08_hydraulic_closure_rigor_audit"
SOURCE_IDS = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
}
SPANS = {"lower_leg", "right_leg", "left_lower_leg", "test_section_span", "left_upper_leg", "upper_leg"}
RECIRCULATION_SPANS = {"left_lower_leg", "left_upper_leg"}


@pytest.fixture(scope="session", autouse=True)
def build_package() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr + result.stdout


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fnum(value: str) -> float:
    if value == "":
        return math.nan
    return float(value)


def test_expected_outputs_exist() -> None:
    expected = {
        "independent_total_pressure_ledger.csv",
        "minor_loss_two_tap_refined.csv",
        "station_development_analysis.csv",
        "recirculation_invalidity.csv",
        "hydraulic_uncertainty_budget.csv",
        "loop_closure_audit.csv",
        "closure_decision_matrix.csv",
        "source_inventory.csv",
        "summary.json",
        "README.md",
    }
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    assert not missing


def test_total_pressure_identity_and_span_coverage() -> None:
    rows = read_csv("independent_total_pressure_ledger.csv")
    assert len(rows) == 18
    assert {(r["source_id"], r["span"]) for r in rows} == {(s, span) for s in SOURCE_IDS for span in SPANS}
    for row in rows:
        lhs = fnum(row["delta_total_pressure_proxy_pa"])
        rhs = fnum(row["delta_p_rgh_pa"]) + fnum(row["delta_q_dyn_pa"])
        assert math.isclose(lhs, rhs, rel_tol=1e-9, abs_tol=1e-9)
        assert row["total_pressure_proxy_label"] == "p_rgh_plus_half_rho_Ubulk_squared"


def test_recirc_spans_are_never_fit_eligible() -> None:
    total_rows = read_csv("independent_total_pressure_ledger.csv")
    recirc_rows = read_csv("recirculation_invalidity.csv")
    for row in total_rows:
        if row["span"] in RECIRCULATION_SPANS:
            assert row["fit_eligible"] == "False"
    for row in recirc_rows:
        if row["span"] in RECIRCULATION_SPANS:
            assert row["fit_eligible"] == "False"
            assert "diagnostic_only" in row["recirculation_invalidity_status"]


def test_missing_gci_and_raw_taps_are_explicit_not_zero() -> None:
    uncertainty = read_csv("hydraulic_uncertainty_budget.csv")
    mesh_rows = [r for r in uncertainty if r["uncertainty_term"] == "mesh_gci"]
    assert mesh_rows
    assert all(r["status"] == "not_quantified" for r in mesh_rows)
    assert all("open" in r["basis"] or "coarse mesh only" in r["basis"] for r in mesh_rows)

    minor = read_csv("minor_loss_two_tap_refined.csv")
    missing = [r for r in minor if r["feature"] == "test_section_complex"]
    assert len(missing) == 3
    assert all(r["refinement_status"] == "raw_extraction_required" for r in missing)
    assert all(r["closure_grade_K_available"] == "False" for r in minor)


def test_loop_sums_and_summary_counts() -> None:
    loops = read_csv("loop_closure_audit.csv")
    assert len(loops) == 3
    for row in loops:
        assert fnum(row["total_mechanical_loss_pa"]) > 0
        assert fnum(row["total_minor_loss_upper_bound_pa"]) >= 0
        assert row["closure_status"] == "recirculation_regime_switch_required"

    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
    assert summary["pressure_span_rows"] == 18
    assert summary["minor_loss_rows"] == 15
    assert summary["openfoam_extraction_run"] is False
