"""Tests for the canonical closure observation table contract."""

from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_closure_observation_table.py"
def _load_module():
    spec = importlib.util.spec_from_file_location("build_closure_observation_table", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


builder = _load_module()
OUT = builder.OUT
OBS = OUT / "closure_observations.csv"
SUMMARY = OUT / "summary.json"


@pytest.fixture(scope="session")
def generated_rows():
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert OBS.exists()
    assert SUMMARY.exists()
    with OBS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validator_rejects_missing_contract_fields():
    row = {field: "x" for field in builder.FIELDS}
    row.update(
        {
            "observation_id": "bad-row",
            "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "run_class": "mainline_jin_continuation",
            "admission_status": "admitted_mainline",
            "fit_eligible": "yes",
            "validation_eligible": "yes",
            "needs_special_gate_scrutiny": "no",
            "recirculation_flag": "no",
            "radiation_present": "no",
            "fit_use_status": "fit_target",
            "window_state": "stationary",
            "mesh_status": "coarse_no_gci",
            "time_window_start_s": "",
            "time_window_end_s": "2431.0",
            "value": "1.0",
            "units": "",
        }
    )
    errors = builder.validate_rows([row], require_source_exists=False)
    assert any("missing required field time_window_start_s" in error for error in errors)
    assert any("missing required field units" in error for error in errors)


def test_generated_rows_only_admit_salt_2_3_4(generated_rows):
    source_ids = {row["source_id"] for row in generated_rows}
    assert source_ids == builder.ADMITTED_SOURCES
    assert all(row["admission_status"] == "admitted_mainline" for row in generated_rows)
    assert all(row["needs_special_gate_scrutiny"] == "no" for row in generated_rows)


def test_generated_rows_satisfy_required_schema(generated_rows):
    errors = builder.validate_rows(generated_rows)
    assert errors == []
    for row in generated_rows:
        for field in builder.REQUIRED:
            assert row[field] != "", f"{row['observation_id']} missing {field}"
        assert row["recirculation_flag"] in {"yes", "no"}
        assert row["radiation_present"] in {"yes", "no"}


def test_fit_and_validation_eligibility_are_separate(generated_rows):
    fit_rows = [row for row in generated_rows if row["fit_eligible"] == "yes"]
    validation_only = [
        row for row in generated_rows
        if row["fit_eligible"] == "no" and row["validation_eligible"] == "yes"
    ]
    assert fit_rows
    assert validation_only
    assert any(row["quantity"] == "f_debuoyed" for row in fit_rows)
    assert any(row["quantity"] == "wallHeatFlux_integral_W" for row in validation_only)


def test_recirculation_spans_are_not_fit_targets(generated_rows):
    recirc = [
        row for row in generated_rows
        if row["span"] in builder.RECIRCULATION_SPANS and row["quantity"] in {"f_debuoyed", "f_corrected"}
    ]
    assert recirc
    assert all(row["fit_eligible"] == "no" for row in recirc)
    assert all(row["fit_use_status"] == "not_fit_recirculation" for row in recirc)


def test_heat_ledger_rows_remain_validation_diagnostics(generated_rows):
    heat_rows = [
        row for row in generated_rows
        if row["source_path"].endswith("2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv")
    ]
    assert heat_rows
    assert all(row["fit_eligible"] == "no" for row in heat_rows)
    assert all("enthalpy_change_missing" in row["quality_flags"] for row in heat_rows)


def test_physical_interface_openfoam_sampling_rows_are_present(generated_rows):
    sample_rows = [
        row for row in generated_rows
        if row["source_path"].endswith("2026-07-09_thermal_openfoam_interface_sampling/combined_openfoam_interface_samples.csv")
    ]
    assert sample_rows
    assert {row["control_volume_group"] for row in sample_rows} >= {"heater", "cooler_reducer", "junction"}
    assert any(row["quantity"] == "T_mixing_cup_signed_K" for row in sample_rows)
    assert any(row["quantity"] == "T_forward_dominant_bulk_K" for row in sample_rows)
    assert any(row["quantity"] == "backflow_fraction" for row in sample_rows)
    assert all(row["fit_eligible"] == "no" for row in sample_rows)
    assert all(row["radiation_output_term"] == "absent_no_qr_output" for row in sample_rows)
    assert all(row["radiation_present"] == "no" for row in sample_rows)


def test_physical_interface_residual_rows_are_validation_only(generated_rows):
    residual_rows = [
        row for row in generated_rows
        if row["source_path"].endswith("2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/patchwise_heat_ledger_enthalpy_interfaces.csv")
    ]
    assert residual_rows
    assert any(row["quantity"] == "wallHeatFlux_vs_enthalpy_residual_W" for row in residual_rows)
    assert any(row["quantity"] == "residual_fraction" for row in residual_rows)
    assert all(row["fit_eligible"] == "no" for row in residual_rows)
    assert all(row["physical_interface_bracket_status"] != "not_applicable" for row in residual_rows)
    assert all(row["thermal_residual_status"] != "not_applicable" for row in residual_rows)


def test_recirculation_contaminated_interfaces_are_never_fit_targets(generated_rows):
    contaminated = [
        row for row in generated_rows
        if row["recirculation_flag"] == "yes" or "recirculation" in row["quality_flags"] or "backflow" in row["quality_flags"]
    ]
    assert contaminated
    assert all(row["fit_eligible"] == "no" for row in contaminated)
    assert all(row["fit_use_status"] == "not_fit_recirculation" for row in contaminated if row["recirculation_flag"] == "yes")
