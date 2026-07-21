from pathlib import Path

from tools.analyze.build_thermal_control_volume_admission_review import build


OUT = Path("work_products/2026-07/2026-07-09/2026-07-09_thermal_control_volume_admission_review")


def test_thermal_control_volume_review_outputs() -> None:
    summary = build()
    assert summary["detail_rows"] > 0
    assert summary["thesis_evidence_rows"] == 9
    assert summary["fit_eligible_detail_rows"] == 0
    assert summary["radiation_present_detail_rows"] == 0
    assert (OUT / "thermal_control_volume_admission.csv").exists()
    assert (OUT / "thermal_thesis_evidence_table.csv").exists()
    assert (OUT / "summary.json").exists()
    assert (OUT / "README.md").exists()


def test_thermal_control_volume_review_carries_expected_classes() -> None:
    build()
    text = (OUT / "thermal_thesis_evidence_table.csv").read_text()
    assert "heater" in text
    assert "cooler_reducer" in text
    assert "junction" in text
    assert "thermal_validation_evidence_only" in text


def test_thermal_control_volume_review_preserves_gates() -> None:
    summary = build()
    detail = (OUT / "thermal_control_volume_admission.csv").read_text()
    assert "validation_only_recirc_contaminated" in detail
    assert "validation_only_not_bracketed" in detail
    assert "absent_no_qr_output" in detail
    assert summary["recirculation_detail_rows"] > 0
