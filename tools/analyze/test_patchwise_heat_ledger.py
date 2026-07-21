"""Tests for the formal patchwise heat ledger."""

from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_patchwise_heat_ledger.py"
OUT = ROOT / "work_products/2026-07-08_patchwise_heat_ledger"
CSV_PATH = OUT / "patchwise_heat_ledger.csv"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_patchwise_heat_ledger", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.path.insert(0, str(SCRIPT.parent))
    spec.loader.exec_module(mod)
    return mod


builder = _load_module()


@pytest.fixture(scope="session")
def rows():
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_row_count_and_sources(rows):
    assert len(rows) == 24
    assert {row["source_id"] for row in rows} == builder.ADMITTED_SOURCES


def test_required_groups_present_per_source(rows):
    expected = {"heater", "cooler", "ambient_wall", "test_section", "junction_other"}
    for source_id in builder.ADMITTED_SOURCES:
        groups = {row["patch_group"] for row in rows if row["source_id"] == source_id}
        assert expected <= groups


def test_wall_flux_signs(rows):
    heater = [row for row in rows if row["patch_group"] == "heater"]
    cooler = [row for row in rows if row["patch_group"] == "cooler"]
    test_section = [row for row in rows if row["patch_group"] == "test_section"]
    assert heater and all(float(row["wallHeatFlux_integral_W"]) > 0 for row in heater)
    assert cooler and all(float(row["wallHeatFlux_integral_W"]) < 0 for row in cooler)
    assert test_section and all(float(row["wallHeatFlux_integral_W"]) < 0 for row in test_section)
    assert all(row["wall_flux_sign_convention"] == "positive_into_fluid_negative_out_of_fluid" for row in rows)


def test_enthalpy_residual_is_segment_quantified(rows):
    nonjunction = [row for row in rows if row["span"] != "junction"]
    junction = [row for row in rows if row["span"] == "junction"]
    assert nonjunction
    assert all(row["enthalpy_change_W"] != "" for row in nonjunction)
    assert all(row["wallHeatFlux_vs_enthalpy_residual_W"] != "" for row in nonjunction)
    assert all(row["segment_enthalpy_source"].endswith(tuple(builder.SEGMENT_ENDPOINT_SPANS[row["span"]])) for row in nonjunction)
    assert junction and all(row["enthalpy_change_W"] == "" for row in junction)
    assert all(row["residual_assignment"] == "junction_loss_reported_as_wall_flux_not_segment_enthalpy" for row in junction)


def test_imposed_and_role_duties(rows):
    heater = [row for row in rows if row["patch_group"] == "heater"]
    cooler = [row for row in rows if row["patch_group"] == "cooler"]
    passive = [row for row in rows if row["patch_group"] == "ambient_wall"]
    junction = [row for row in rows if row["patch_group"] == "junction_other"]
    assert all(float(row["heater_imposed_duty_W"]) > float(row["wallHeatFlux_integral_W"]) for row in heater)
    assert all(float(row["cooler_removed_duty_W"]) > 0 for row in cooler)
    assert all(abs(float(row["imposed_Q_minus_wallHeatFlux_W"])) < 0.001 for row in cooler)
    assert all(row["passive_wall_heat_leak_gain_W"] != "" for row in passive)
    assert all(row["junction_loss_W"] != "" for row in junction)


def test_resistance_network_and_radiation_contract(rows):
    assert all(float(row["patch_area_m2"]) > 0 for row in rows)
    assert all(row["wall_temperature_source"] for row in rows)
    assert all(row["wall_T_mean_K"] for row in rows)
    assert all(row["radiation_present"] in {"False", "false", False} for row in rows)
    assert all(row["external_radiation_resistance_m2K_W"] == "absent_no_qr_output" for row in rows)
    assert all("radiation_absent_no_qr_output" in row["network_terms_resolved"] for row in rows)
    rc_external = [row for row in rows if "rcExternalTemperature" in row["bc_type"]]
    assert rc_external
    assert all(row["wall_conduction_resistance_m2K_W"] for row in rc_external)
    assert all(row["external_convection_resistance_m2K_W"] for row in rc_external)


def test_rows_are_validation_only(rows):
    assert all(row["fit_eligible"] == "no" for row in rows)
    assert all(row["validation_eligible"] == "yes" for row in rows)
    assert all(row["fit_use_status"] == "validation_only_thermal_residual_not_fit_target" for row in rows)


def test_builder_validation(rows):
    assert builder.validate_rows(rows) == []
