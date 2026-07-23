from pathlib import Path

from tools.analyze.build_model_form_bakeoff_from_observations import build


def test_model_form_bakeoff_outputs() -> None:
    summary = build()
    out = Path("work_products/2026-07/2026-07-22/2026-07-22_model_form_bakeoff")
    assert summary["observation_rows"] == 1032
    assert summary["case_score_rows"] == 15
    assert summary["recirculation_flagged_observation_rows"] == 291
    assert summary["radiation_present_observation_rows"] == 0
    assert (out / "model_form_summary.csv").exists()
    assert (out / "model_form_case_scores.csv").exists()
    assert (out / "observation_use_summary.csv").exists()
    assert (out / "observation_quality_summary.csv").exists()
    assert (out / "source_manifest.csv").exists()
    assert (out / "README.md").exists()
    assert summary["task"] == "TODO-MODEL-FORM-BAKEOFF"
    assert summary["protected_scoring_executed"] is False


def test_model_form_bakeoff_separates_score_axes() -> None:
    out = Path("work_products/2026-07/2026-07-22/2026-07-22_model_form_bakeoff")
    build()
    text = (out / "model_form_summary.csv").read_text()
    assert "mean_abs_mdot_error_pct" in text
    assert "mean_pressure_distribution_mape_pct" in text
    assert "mean_thermal_state_mismatch_W" in text
    assert "F3_shah_apparent" in text
    assert "F4_leg_class" in text


def test_model_form_bakeoff_carries_thermal_refresh_fields() -> None:
    out = Path("work_products/2026-07/2026-07-22/2026-07-22_model_form_bakeoff")
    build()
    case_scores = (out / "model_form_case_scores.csv").read_text()
    quality = (out / "observation_quality_summary.csv").read_text()
    assert "openfoam_interface_observation_rows" in case_scores
    assert "physical_interface_residual_observation_rows" in case_scores
    assert "max_abs_thermal_residual_fraction" in case_scores
    assert "canonical_validation_axis_not_model_specific_no_fit_promotion" in case_scores
    assert "bracketed_openfoam_physical_interface_plane" in quality
    assert "not_fit_recirculation" in quality
