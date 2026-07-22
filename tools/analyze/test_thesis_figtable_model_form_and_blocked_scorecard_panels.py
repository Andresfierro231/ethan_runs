#!/usr/bin/env python3
"""Regression checks for thesis model-form figure/table panel builder."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools" / "analyze" / "build_thesis_figtable_model_form_and_blocked_scorecard_panels.py"
OUT_DIR = (
    ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-22"
    / "2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels"
)
TP_TW_MODEL_IDS = ["M1", "M1b", "M2", "M3", "D2_M3_sensor_kind_offsets_train"]
MODEL_SUMMARY_IDS = [*TP_TW_MODEL_IDS, "PASSIVE-H2-CAND001"]


def figure_slug(value: str) -> str:
    return value.lower().replace("/", "_").replace(" ", "_").replace("+", "plus")


def display_model_form_id(value: str) -> str:
    return "D2" if value == "D2_M3_sensor_kind_offsets_train" else value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def approx(value: str, expected: float, tol: float = 1.0e-9) -> None:
    assert abs(float(value) - expected) <= tol, (value, expected)


def main() -> None:
    subprocess.run([sys.executable, str(BUILDER)], check=True, cwd=ROOT)

    expected_files = [
        OUT_DIR / "figures" / "progress" / "svg" / "model_form_ladder_no_admission.svg",
        OUT_DIR / "figures" / "progress" / "png" / "model_form_ladder_no_admission.png",
        OUT_DIR / "figures" / "progress" / "svg" / "blocked_scorecard_waterfall.svg",
        OUT_DIR / "figures" / "progress" / "png" / "blocked_scorecard_waterfall.png",
        OUT_DIR / "tp_tw_temperature_elevation_panel_points.csv",
        OUT_DIR / "tp_temperature_elevation_panel_points.csv",
        OUT_DIR / "signed_error_panel_points.csv",
        OUT_DIR / "model_form_ladder_panel.csv",
        OUT_DIR / "blocked_scorecard_waterfall_panel.csv",
        OUT_DIR / "caption_ledger.csv",
        OUT_DIR / "model_form_summary.csv",
        OUT_DIR / "source_manifest.csv",
        OUT_DIR / "no_mutation_guardrails.csv",
        OUT_DIR / "summary.json",
        OUT_DIR / "README.md",
    ]
    for model_form_id in TP_TW_MODEL_IDS:
        slug = figure_slug(model_form_id)
        expected_files.append(OUT_DIR / "figures" / model_form_id / "README.md")
        expected_files.extend(
            [
                OUT_DIR / "figures" / model_form_id / "diagnostics" / "svg" / f"{slug}_signed_sensor_error_shape.svg",
                OUT_DIR / "figures" / model_form_id / "diagnostics" / "png" / f"{slug}_signed_sensor_error_shape.png",
            ]
        )
        for case_id in ["salt_2", "salt_3", "salt_4"]:
            expected_files.extend(
                [
                    OUT_DIR
                    / "figures"
                    / model_form_id
                    / "tp_vs_elevation"
                    / "svg"
                    / f"{slug}_tp_temperature_vs_elevation_{case_id}.svg",
                    OUT_DIR
                    / "figures"
                    / model_form_id
                    / "tp_vs_elevation"
                    / "png"
                    / f"{slug}_tp_temperature_vs_elevation_{case_id}.png",
                    OUT_DIR
                    / "figures"
                    / model_form_id
                    / "tp_tw_vs_elevation"
                    / "svg"
                    / f"{slug}_tp_tw_temperature_vs_elevation_{case_id}.svg",
                    OUT_DIR
                    / "figures"
                    / model_form_id
                    / "tp_tw_vs_elevation"
                    / "png"
                    / f"{slug}_tp_tw_temperature_vs_elevation_{case_id}.png",
                ]
            )
    expected_files.extend(
        [
            OUT_DIR / "figures" / "PASSIVE-H2-CAND001" / "README.md",
            OUT_DIR
            / "figures"
            / "PASSIVE-H2-CAND001"
            / "operator"
            / "svg"
            / "passive_h2_case_heat_path_operator.svg",
            OUT_DIR
            / "figures"
            / "PASSIVE-H2-CAND001"
            / "operator"
            / "png"
            / "passive_h2_case_heat_path_operator.png",
            OUT_DIR
            / "figures"
            / "PASSIVE-H2-CAND001"
            / "operator"
            / "svg"
            / "passive_h2_segment_family_heat_path_operator.svg",
            OUT_DIR
            / "figures"
            / "PASSIVE-H2-CAND001"
            / "operator"
            / "png"
            / "passive_h2_segment_family_heat_path_operator.png",
            OUT_DIR
            / "figures"
            / "PASSIVE-H2-CAND001"
            / "operator"
            / "svg"
            / "passive_h2_global_patch_rejection_operator.svg",
            OUT_DIR
            / "figures"
            / "PASSIVE-H2-CAND001"
            / "operator"
            / "png"
            / "passive_h2_global_patch_rejection_operator.png",
            OUT_DIR / "passive_h2_operator_case_points.csv",
            OUT_DIR / "passive_h2_operator_family_points.csv",
            OUT_DIR / "passive_h2_operator_global_patch_points.csv",
        ]
    )
    missing = [str(path) for path in expected_files if not path.exists()]
    assert not missing, f"missing expected outputs: {missing}"
    assert not (OUT_DIR / "figures" / "svg").exists()
    assert not (OUT_DIR / "figures" / "png").exists()
    assert not (OUT_DIR / "figures" / "tp_vs_elevation").exists()
    assert not (OUT_DIR / "figures" / "tp_tw_vs_elevation").exists()
    assert not (OUT_DIR / "figures" / "diagnostics").exists()
    assert not (OUT_DIR / "figures" / "operator").exists()

    signed_rows = read_csv(OUT_DIR / "signed_error_panel_points.csv")
    assert len(signed_rows) == 225, len(signed_rows)
    assert {row["model_form"] for row in signed_rows} == set(TP_TW_MODEL_IDS)
    assert {row["case_id"] for row in signed_rows} == {"salt_2", "salt_3", "salt_4"}
    assert {row["sensor_kind"] for row in signed_rows} == {"TP", "TW"}
    assert {row["temperature_target_source"] for row in signed_rows} == {
        "experimental_fluid_validation"
    }
    signed_by_model_case_sensor = {
        (row["model_form"], row["case_id"], row["sensor_id"]): row for row in signed_rows
    }
    approx(signed_by_model_case_sensor[("M3", "salt_2", "TP1")]["target_K"], 453.26)
    approx(
        signed_by_model_case_sensor[("M3", "salt_2", "TW5")]["signed_error_K"],
        float(signed_by_model_case_sensor[("M3", "salt_2", "TW5")]["predicted_K"]) - 471.69,
    )

    tp_tw_rows = read_csv(OUT_DIR / "tp_tw_temperature_elevation_panel_points.csv")
    tp_only_rows = read_csv(OUT_DIR / "tp_temperature_elevation_panel_points.csv")
    assert len(tp_tw_rows) == 255, len(tp_tw_rows)
    assert len(tp_only_rows) == 90, len(tp_only_rows)
    assert {row["case_id"] for row in tp_tw_rows} == {"salt_2", "salt_3", "salt_4"}
    assert {row["sensor_id"] for row in tp_tw_rows if row["sensor_kind"] == "TP"} == {
        "TP1",
        "TP2",
        "TP3",
        "TP4",
        "TP5",
        "TP6",
    }
    assert {row["sensor_id"] for row in tp_tw_rows if row["sensor_kind"] == "TW"} == {
        "TW1",
        "TW2",
        "TW3",
        "TW4",
        "TW5",
        "TW6",
        "TW7",
        "TW8",
        "TW9",
        "TW10",
        "TW11",
    }
    assert {row["model_form_id"] for row in tp_tw_rows} == set(TP_TW_MODEL_IDS)
    assert all(row["target_K"] for row in tp_tw_rows)
    assert all(row["elevation_m"] for row in tp_tw_rows)
    assert all(row["scoreboard_source_path"] for row in tp_tw_rows)
    assert {row["temperature_target_source"] for row in tp_tw_rows} == {
        "experimental_fluid_validation"
    }
    assert {row["elevation_source_field"] for row in tp_tw_rows} == {
        "reference_plot_Y_ABSOLUTE_M_minus_TP2_datum"
    }
    assert all(row["scoreboard_reference_target_K"] for row in tp_tw_rows)
    assert all(row["target_delta_experimental_minus_scoreboard_K"] for row in tp_tw_rows)

    by_model_case_sensor = {
        (row["model_form_id"], row["case_id"], row["sensor_id"]): row for row in tp_tw_rows
    }
    approx(by_model_case_sensor[("M3", "salt_2", "TP1")]["target_K"], 453.26)
    approx(by_model_case_sensor[("M3", "salt_2", "TW5")]["target_K"], 471.69)
    approx(by_model_case_sensor[("M3", "salt_3", "TP1")]["target_K"], 465.81)
    approx(by_model_case_sensor[("M3", "salt_4", "TW5")]["target_K"], 503.72)
    approx(by_model_case_sensor[("M3", "salt_2", "TP1")]["scoreboard_reference_target_K"], 450.599118072)
    assert abs(float(by_model_case_sensor[("M3", "salt_2", "TW5")]["target_delta_experimental_minus_scoreboard_K"])) > 20.0
    approx(by_model_case_sensor[("M3", "salt_2", "TP2")]["elevation_m"], 0.0)
    approx(by_model_case_sensor[("M3", "salt_2", "TP1")]["elevation_m"], 0.9144)
    approx(by_model_case_sensor[("M3", "salt_2", "TP6")]["elevation_m"], 1.227143219056991)
    approx(by_model_case_sensor[("M3", "salt_2", "TW5")]["elevation_m"], 0.156371609528495)
    for case_id in {"salt_2", "salt_3", "salt_4"}:
        for model_form_id in TP_TW_MODEL_IDS:
            assert by_model_case_sensor[(model_form_id, case_id, "TP5")]["target_next_sensor_in_plot"] == "TP6"
            assert by_model_case_sensor[(model_form_id, case_id, "TP5")]["prediction_next_sensor_in_plot"] == "TP6"
            assert by_model_case_sensor[(model_form_id, case_id, "TW11")]["target_next_sensor_in_plot"] == "TW1"
            assert by_model_case_sensor[(model_form_id, case_id, "TW11")]["prediction_next_sensor_in_plot"] == "TW1"
            display_id = display_model_form_id(model_form_id)
            assert by_model_case_sensor[(model_form_id, case_id, "TP5")]["prediction_label"] == f"{display_id} TP5"
            assert by_model_case_sensor[(model_form_id, case_id, "TW11")]["prediction_label"] == f"{display_id} TW11"
    prediction_label_rows = [
        row
        for row in tp_tw_rows
        if row["prediction_curve_included"] == "True" and row["prediction_label"]
    ]
    assert len(prediction_label_rows) == 225, len(prediction_label_rows)

    tp2_rows = [row for row in tp_tw_rows if row["sensor_id"] == "TP2"]
    assert len(tp2_rows) == 15, len(tp2_rows)
    assert all(row["target_K"] for row in tp2_rows)
    assert all(row["prediction_available"] == "False" for row in tp2_rows)
    assert all(row["predicted_K"] == "" for row in tp2_rows)
    assert all(row["target_curve_included"] == "True" for row in tp2_rows)
    assert any(
        row["missing_or_excluded_reason"].endswith("_prediction_missing_in_diagnostic_addendum")
        for row in tp2_rows
    )

    tw10_rows = [row for row in tp_tw_rows if row["sensor_id"] == "TW10"]
    assert len(tw10_rows) == 15, len(tw10_rows)
    assert all(row["target_K"] for row in tw10_rows)
    assert all(row["prediction_available"] == "False" for row in tw10_rows)
    assert all(row["target_curve_included"] == "False" for row in tw10_rows)
    assert all(
        row["missing_or_excluded_reason"] == "excluded_active_hx_shell_state_absent_no_model_prediction"
        for row in tw10_rows
    )

    plotted_tw_rows = [
        row
        for row in tp_tw_rows
        if row["sensor_kind"] == "TW" and row["target_curve_included"] == "True"
    ]
    assert len(plotted_tw_rows) == 150, len(plotted_tw_rows)
    assert all(row["prediction_available"] == "True" for row in plotted_tw_rows)

    ladder_rows = read_csv(OUT_DIR / "model_form_ladder_panel.csv")
    assert len(ladder_rows) == 6, len(ladder_rows)
    assert ladder_rows[0]["short_label"] == "M0"
    assert ladder_rows[-1]["short_label"] == "M6"

    model_summary_rows = read_csv(OUT_DIR / "model_form_summary.csv")
    assert len(model_summary_rows) == 6, len(model_summary_rows)
    assert {row["model_form_id"] for row in model_summary_rows} == set(MODEL_SUMMARY_IDS)
    model_summary_by_id = {row["model_form_id"]: row for row in model_summary_rows}
    assert model_summary_by_id["D2_M3_sensor_kind_offsets_train"]["current_numeric_rank_by_experimental_tp_tw_rmse"] == "1"
    assert (
        model_summary_by_id["D2_M3_sensor_kind_offsets_train"]["current_numeric_disposition"]
        == "best_numeric_diagnostic_projection_addendum_not_admitted"
    )
    assert model_summary_by_id["M3"]["current_numeric_rank_by_experimental_tp_tw_rmse"] == "2"
    assert model_summary_by_id["M3"]["current_numeric_disposition"] == "best_current_legacy_numeric_comparator_not_frozen"
    assert float(model_summary_by_id["M3"]["experimental_target_rmse_K"]) < float(
        model_summary_by_id["M2"]["experimental_target_rmse_K"]
    )
    assert model_summary_by_id["PASSIVE-H2-CAND001"]["current_numeric_rank_by_experimental_tp_tw_rmse"] == ""
    assert (
        model_summary_by_id["PASSIVE-H2-CAND001"]["current_numeric_disposition"]
        == "operator_only_passive_boundary_development_evidence_no_tp_tw_prediction"
    )

    caption_rows = read_csv(OUT_DIR / "caption_ledger.csv")
    assert len(caption_rows) == 40, len(caption_rows)
    assert caption_rows[0]["figure_id"] == "fig_m1_tp_tw_temperature_vs_elevation_salt_2"
    assert any("/figures/progress/svg/model_form_ladder_no_admission.svg" in row["svg_path"] for row in caption_rows)
    assert any("/figures/progress/svg/blocked_scorecard_waterfall.svg" in row["svg_path"] for row in caption_rows)
    assert any("/figures/M3/tp_vs_elevation/svg/m3_tp_temperature_vs_elevation_salt_2.svg" in row["svg_path"] for row in caption_rows)
    assert any(
        "/figures/M3/tp_tw_vs_elevation/svg/m3_tp_tw_temperature_vs_elevation_salt_2.svg" in row["svg_path"]
        for row in caption_rows
    )
    assert any(
        "/figures/D2_M3_sensor_kind_offsets_train/tp_tw_vs_elevation/svg/d2_m3_sensor_kind_offsets_train_tp_tw_temperature_vs_elevation_salt_2.svg"
        in row["svg_path"]
        for row in caption_rows
    )
    assert any(
        "/figures/PASSIVE-H2-CAND001/operator/svg/passive_h2_case_heat_path_operator.svg" in row["svg_path"]
        for row in caption_rows
    )
    joined_forbidden = " ".join(row["forbidden_claim"] for row in caption_rows).lower()
    assert "final predictive accuracy" in joined_forbidden
    assert "closure admission" in joined_forbidden or "admitted" in joined_forbidden

    with (OUT_DIR / "summary.json").open(encoding="utf-8") as handle:
        summary = json.load(handle)
    assert summary["decision"] == "thesis_figure_panels_ready_no_closure_admission"
    assert summary["figure_panels"] == 40
    assert summary["figure_category_layout"].startswith("figures/<model_form>/")
    assert summary["model_form_ids"] == MODEL_SUMMARY_IDS
    assert summary["model_form_count"] == 6
    assert summary["model_form_readme_count"] == 6
    assert summary["current_best_numeric_model_form_by_experimental_tp_tw_rmse"] == "D2_M3_sensor_kind_offsets_train"
    assert summary["current_best_numeric_model_form_status"] == "best_numeric_diagnostic_projection_addendum_not_admitted"
    assert summary["most_likely_future_predictive_family"] == "M5 / MF-04 throughflow-plus-recirculation exchange cell"
    assert summary["progress_figure_panels"] == 2
    assert summary["tp_vs_elevation_figure_panels"] == 15
    assert summary["tp_tw_vs_elevation_figure_panels"] == 15
    assert summary["diagnostic_figure_panels"] == 5
    assert summary["operator_figure_panels"] == 3
    assert summary["legacy_flat_figure_paths_retained"] == 0
    assert summary["tp_tw_temperature_elevation_panel_rows"] == 255
    assert summary["tp_temperature_elevation_panel_rows"] == 90
    assert summary["tp_tw_target_rows_plotted"] == 240
    assert summary["tw_target_rows_plotted_excluding_tw10"] == 150
    assert summary["missing_m3_predictions_marked"] == 30
    assert summary["missing_m3_tp2_predictions_marked"] == 15
    assert summary["missing_m3_tp_predictions_marked"] == 15
    assert summary["excluded_tw10_rows_marked"] == 15
    assert summary["tp_tw_placeholder_temperature_values_used"] is False
    assert summary["tp_tw_placeholder_elevation_values_used"] is False
    assert summary["temperature_target_basis"] == "experimental_fluid_validation_targets"
    assert summary["experimental_target_rows"] == 255
    assert summary["scoreboard_cfd_reference_target_used_as_plotted_target"] is False
    assert summary["scoreboard_target_audit_rows"] == 255
    assert summary["reference_geometry_elevation_basis"] == "reference_plot_Y_ABSOLUTE_M_minus_TP2_datum"
    assert summary["reference_geometry_elevation_rows"] == 255
    assert summary["tw10_rows_preserved_unplotted"] == 15
    assert summary["tp5_to_tp6_target_connection_plotted"] is True
    assert summary["tp5_to_tp6_prediction_connection_plotted"] is True
    assert summary["tw11_to_tw1_target_closure_plotted"] is True
    assert summary["tw11_to_tw1_prediction_closure_plotted"] is True
    assert summary["prediction_marker_labels_plotted"] is True
    assert summary["prediction_marker_label_rows"] == 225
    assert summary["finite_signed_error_panel_rows"] == 225
    assert summary["model_form_summary_rows"] == 6
    assert "reference geometry Y_ABSOLUTE_M" in summary["tp_tw_coordinate_basis"]
    assert summary["final_score_values"] == 0
    assert summary["s6_final_score_values_published"] == 0
    for guardrail in [
        "native_output_mutation",
        "registry_or_admission_mutation",
        "scheduler_action",
        "solver_sampler_harvest_uq_launched",
        "validation_holdout_external_new_scoring",
        "fitting_or_model_selection",
        "source_property_release",
        "coefficient_admission",
        "s11_s12_s13_s15_s6_trigger",
        "thesis_current_file_edit",
        "blocker_register_change",
        "generated_index_refresh",
        "residual_absorbed_into_internal_nu",
    ]:
        assert summary[guardrail] is False, guardrail

    print("thesis fig/table model-form panel checks passed")


if __name__ == "__main__":
    main()
