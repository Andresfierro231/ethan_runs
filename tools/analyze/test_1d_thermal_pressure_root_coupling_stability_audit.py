import csv

from tools.analyze import build_1d_thermal_pressure_root_coupling_stability_audit as builder


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_root_coupling_audit_is_dry_and_non_admitting(tmp_path):
    summary = builder.build(tmp_path)

    assert summary["decision"] == "root_coupling_stability_audit_ready_dry_no_compute"
    assert summary["root_audit_rows"] == 4
    assert summary["failure_mode_rows"] == 5
    assert summary["fluid_smoke_test_rows"] == 5
    assert summary["fit_or_model_selection"] is False
    assert summary["protected_scoring"] is False
    assert summary["source_property_release"] is False
    assert summary["candidate_freeze"] is False
    assert summary["native_output_mutation"] is False
    assert summary["registry_or_admission_mutation"] is False
    assert summary["scheduler_action"] is False
    assert summary["fluid_or_external_edit"] is False


def test_root_audit_blocks_admission_and_preserves_f6_gate(tmp_path):
    builder.build(tmp_path)

    root_rows = read_csv(tmp_path / "root_monotonicity_bracketing_audit.csv")
    assert {row["admission_or_score_allowed"] for row in root_rows} == {"no"}

    failures = read_csv(tmp_path / "root_failure_mode_table.csv")
    assert any(row["failure_mode"] == "ordinary_closure_leakage" for row in failures)
    assert any(row["failure_mode"] == "source_property_leakage" for row in failures)

    smoke = read_csv(tmp_path / "fluid_smoke_test_recommendations.csv")
    assert any("F6/component-K terms are disabled" in row["check"] for row in smoke)
    assert any("runtime input manifest" in row["check"] for row in smoke)


def test_sensitivity_matrix_contains_high_risk_mdot_paths(tmp_path):
    summary = builder.build(tmp_path)

    risks = read_csv(tmp_path / "coupled_sensitivity_risk_matrix.csv")
    high = {row["input_family"] for row in risks if row["coupled_root_risk"] == "high"}
    assert {"cooler_hx_strength", "fluid_property_mode", "pressure_loss_terms"}.issubset(high)
    assert summary["high_coupled_root_risk_rows"] >= 3
