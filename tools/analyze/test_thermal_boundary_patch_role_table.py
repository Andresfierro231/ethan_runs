"""Tests for AGENT-263 thermal boundary patch-role table."""

from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_thermal_boundary_patch_role_table.py"
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table"
PATCH_CSV = OUT / "thermal_boundary_patch_role_table.csv"
SEGMENT_CSV = OUT / "segment_reduction_inputs.csv"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_thermal_boundary_patch_role_table", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.path.insert(0, str(SCRIPT.parent))
    spec.loader.exec_module(mod)
    return mod


builder = _load_module()


@pytest.fixture(scope="session")
def generated_rows():
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    with PATCH_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="session")
def segment_rows(generated_rows):
    with SEGMENT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_patch_row_count_and_sources(generated_rows):
    assert len(generated_rows) == 207
    assert {row["source_id"] for row in generated_rows} == set(builder.CASES)


def test_bc_type_counts_per_source(generated_rows):
    expected = {"externalTemperature": 10, "rcExternalTemperature": 36, "zeroGradient": 23}
    for source_id in builder.CASES:
        rows = [row for row in generated_rows if row["source_id"] == source_id]
        counts = {key: sum(1 for row in rows if row["bc_type"] == key) for key in expected}
        assert counts == expected


def test_required_roles_present(generated_rows):
    expected = {
        "heater",
        "cooler",
        "test_section",
        "ambient_wall",
        "junction_other",
        "zero_gradient_ncc_connector",
    }
    for source_id in builder.CASES:
        roles = {row["role"] for row in generated_rows if row["source_id"] == source_id}
        assert expected <= roles


def test_patch_heat_sums_match_grouped_ledger(generated_rows):
    expected = builder.grouped_ledger_totals()
    for source_id, grouped_total in expected.items():
        actual = sum(
            float(row["realized_wallHeatFlux_W"])
            for row in generated_rows
            if row["source_id"] == source_id and row["realized_wallHeatFlux_W"]
        )
        assert abs(actual - grouped_total) <= 5e-4


def test_key_patch_fields(generated_rows):
    heater = [row for row in generated_rows if row["role"] == "heater"]
    cooler = [row for row in generated_rows if row["role"] == "cooler"]
    rc_rows = [row for row in generated_rows if row["bc_type"] == "rcExternalTemperature"]
    assert heater and all(float(row["imposed_Q_W"]) > 0 for row in heater)
    assert heater and all(float(row["realized_wallHeatFlux_W"]) > 0 for row in heater)
    assert cooler and all(float(row["imposed_Q_W"]) < 0 for row in cooler)
    assert cooler and all(float(row["realized_wallHeatFlux_W"]) < 0 for row in cooler)
    assert rc_rows and all(row["emissivity"] for row in rc_rows)
    assert rc_rows and all(row["Tsur_K"] for row in rc_rows)


def test_segment_reduction_inputs(segment_rows):
    assert len(segment_rows) == 15
    expected_segments = {"lower_leg", "downcomer", "cooling_branch", "upcomer", "junction"}
    for source_id in builder.CASES:
        rows = [row for row in segment_rows if row["source_id"] == source_id]
        assert {row["one_d_segment"] for row in rows} == expected_segments
        assert all(row["realized_wallHeatFlux_W"] for row in rows)


def test_builder_validation(generated_rows):
    assert builder.validate_rows(generated_rows) == []
