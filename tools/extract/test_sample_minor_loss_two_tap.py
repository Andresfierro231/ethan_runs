import csv
import math
from pathlib import Path

from tools.extract.sample_minor_loss_two_tap import (
    build_package,
    build_rows,
    compute_adjacent_straight_loss,
    fnum,
    load_pressure_ledger,
)


def test_build_rows_counts_and_unavailable_feature() -> None:
    rows = build_rows()
    assert len(rows) == 15  # 3 salts x (4 preserved corners + 1 expected connector)

    computed = [row for row in rows if row["status"] == "computed_from_preserved_two_tap_feature_rows"]
    unavailable = [row for row in rows if row["status"] == "missing_preserved_two_tap_feature_output"]
    assert len(computed) == 12
    assert len(unavailable) == 3
    assert {row["feature"] for row in unavailable} == {"test_section_complex"}
    assert all("requires_raw_two_tap_extraction" in row["quality_flags"] for row in unavailable)


def test_k_local_is_no_larger_than_k_apparent_for_computed_rows() -> None:
    rows = build_rows()
    computed = [row for row in rows if row["status"] == "computed_from_preserved_two_tap_feature_rows"]
    assert computed
    assert all(fnum(row["K_local"]) <= fnum(row["K_apparent"]) for row in computed)
    assert any(fnum(row["adjacent_straight_loss_subtracted_pa"]) > 0 for row in computed)
    assert all(row["straight_loss_subtraction_status"] == "subtracted_minimum_dz_proxy_straight_loss" for row in computed)


def test_recirc_adjacent_rows_are_flagged() -> None:
    rows = build_rows()
    flagged = [row for row in rows if "recirculation_adjacent" in row["quality_flags"]]
    assert flagged
    assert {row["feature"] for row in flagged} >= {"corner_lower_left", "corner_upper_left"}
    assert all(row["fit_eligible"] == "no" for row in flagged)


def test_adjacent_straight_loss_uses_fit_eligible_adjacent_spans() -> None:
    pressure = load_pressure_ledger(Path("work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv"))
    result = compute_adjacent_straight_loss(
        "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "corner_lower_left",
        -0.01755775,
        pressure,
    )
    assert result["straight_loss_gradient_basis"] == "fit_eligible_adjacent_average"
    assert result["recirculation_adjacent_spans"] == "left_lower_leg"
    assert math.isclose(float(result["tap_length_proxy_m"]), 0.01755775)
    assert float(result["adjacent_straight_loss_subtracted_pa"]) > 0


def test_build_package_writes_expected_artifacts(tmp_path: Path) -> None:
    payload = build_package(tmp_path)
    assert payload["summary"]["row_count"] == 15
    assert payload["summary"]["computed_rows"] == 12
    assert (tmp_path / "minor_loss_two_tap.csv").exists()
    assert (tmp_path / "minor_loss_two_tap.json").exists()
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "README.md").exists()

    with (tmp_path / "minor_loss_two_tap.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 15
    assert "K_local" in rows[0]
