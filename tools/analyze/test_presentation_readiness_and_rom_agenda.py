#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_presentation_readiness_and_rom_agenda import (  # noqa: E402
    figure_inventory,
    find_attempt,
    find_surface,
    future_model_rows,
    model_form_rows,
    paper_readiness_rows,
)


def test_find_attempt_and_surface_return_matching_rows():
    attempts = [
        {"attempt_name": "a", "mean_mdot_abs_error_kg_s": "1.0"},
        {"attempt_name": "b", "mean_mdot_abs_error_kg_s": "2.0"},
    ]
    surfaces = [
        {"surface_label": "x", "best_primary_scenario": "sx"},
        {"surface_label": "y", "best_primary_scenario": "sy"},
    ]
    assert find_attempt(attempts, "b")["mean_mdot_abs_error_kg_s"] == "2.0"
    assert find_attempt(attempts, "missing") == {}
    assert find_surface(surfaces, "y")["best_primary_scenario"] == "sy"
    assert find_surface(surfaces, "missing") == {}


def test_figure_inventory_tracks_known_pngs_and_readiness_fields():
    rows = figure_inventory()
    ids = {row["figure_id"] for row in rows}
    assert "1d_bakeoff_full_coverage_case_metrics" in ids
    assert "frozen_validation_mass_flow" in ids
    assert all("readiness" in row for row in rows)
    assert all(row["provenance"].startswith("existing generated figure") for row in rows)


def test_model_form_inventory_contains_expected_comparison_forms():
    surface = {
        "best_primary_mean_energy_error_pct_of_heater": "11.27",
        "best_primary_mean_mass_flow_relative_error_pct_vs_cfd": "26.69",
    }
    replays = [
        {"attempt_name": "major_plus_feature_probe_baseline", "mean_mdot_abs_error_kg_s": "0.000255"},
        {"attempt_name": "major_plus_feature_endpoint_baseline", "mean_mdot_abs_error_kg_s": "0.484"},
        {"attempt_name": "major_only_baseline", "mean_mdot_abs_error_kg_s": "0.554"},
    ]
    rows = model_form_rows(surface, replays)
    by_id = {row["model_id"]: row for row in rows}
    assert {"F0", "F1", "F2", "F3", "F4", "F5"}.issubset(by_id)
    assert "0.000255" in by_id["F4"]["primary_metric"]
    assert by_id["F3"]["current_status"] == "highest_value_next_model_form"


def test_paper_readiness_rows_separate_blocked_future_and_meeting_ready():
    surface = {
        "best_primary_mean_energy_error_pct_of_heater": "11.27",
        "best_primary_mean_mass_flow_relative_error_pct_vs_cfd": "26.69",
    }
    probe = {"mean_mdot_abs_error_kg_s": "0.000255"}
    major = {"mean_mdot_abs_error_kg_s": "0.554"}
    endpoint = {"mean_mdot_abs_error_kg_s": "0.484"}
    rows = paper_readiness_rows(surface, probe, major, endpoint, {"pressure_friction_rows": 36})
    readiness = {row["item_id"]: row["readiness"] for row in rows}
    assert readiness["mesh_independence_gci"] == "blocked"
    assert readiness["experimental_validation"] == "required_future_work"
    assert readiness["current_1d_validation"] == "meeting_ready_diagnostic"


def test_future_model_rows_include_uncertainty_and_experiment_path():
    rows = future_model_rows()
    ids = {row["candidate_id"] for row in rows}
    assert "M1" in ids
    assert "M6" in ids
    assert all(row["uncertainty_plan"] for row in rows)
