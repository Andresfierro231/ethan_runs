"""Tests for physical-interface patchwise heat-ledger follow-up."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_patchwise_heat_ledger_enthalpy_interfaces.py"
FOUNDATION = ROOT / "work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_patchwise_heat_ledger_enthalpy_interfaces", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.path.insert(0, str(SCRIPT.parent))
    spec.loader.exec_module(module)
    return module


builder = _load_module()


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_package_outputs_and_no_foundation_mutation(tmp_path: Path):
    before = _hash(FOUNDATION)
    summary = builder.build_package(tmp_path)
    after = _hash(FOUNDATION)
    assert before == after
    assert summary["foundation_unchanged"] is True
    assert summary["counts"]["patchwise_rows"] == 24
    assert summary["counts"]["segment_rows"] == 15
    assert summary["counts"]["validation_errors"] == 0
    for name in (
        "interface_registry.csv",
        "interface_temperature_samples.csv",
        "segment_enthalpy_residuals.csv",
        "patchwise_heat_ledger_enthalpy_interfaces.csv",
        "resistance_network_terms.csv",
        "source_inventory.csv",
        "README.md",
        "summary.json",
    ):
        assert (tmp_path / name).exists()


def test_enthalpy_formula_and_residual_arithmetic(tmp_path: Path):
    builder.build_package(tmp_path)
    segments = _read(tmp_path / "segment_enthalpy_residuals.csv")
    lower = next(row for row in segments if row["source_id"].endswith("salt_test_2_jin_coarse_mesh") and row["physical_segment"] == "lower_leg")
    mdot = float(lower["mdot_kg_s"])
    cp = float(lower["cp_jkgk"])
    dt = float(lower["delta_T_K"])
    enthalpy = float(lower["enthalpy_change_W"])
    assert math.isclose(enthalpy, mdot * cp * dt, rel_tol=0, abs_tol=5e-4)
    residual = float(lower["wallHeatFlux_vs_enthalpy_residual_W"])
    qwall = float(lower["segment_wallHeatFlux_sum_W"])
    assert math.isclose(residual, qwall - enthalpy, rel_tol=0, abs_tol=5e-4)


def test_patchwise_rows_have_interface_contract_and_radiation_semantics(tmp_path: Path):
    builder.build_package(tmp_path)
    rows = _read(tmp_path / "patchwise_heat_ledger_enthalpy_interfaces.csv")
    nonjunction = [row for row in rows if row["span"] != "junction"]
    junction = [row for row in rows if row["span"] == "junction"]
    assert nonjunction
    assert all(row["interface_temperature_source"] for row in nonjunction)
    assert all(row["physical_interface_inlet"] for row in nonjunction)
    assert all(row["enthalpy_change_W"] for row in nonjunction)
    assert junction and all(row["enthalpy_change_W"] == "" for row in junction)
    assert all(row["wall_flux_sign_convention"] == "positive_into_fluid_negative_out_of_fluid" for row in rows)
    assert all(row["radiation_present"] in {"False", "false", False} for row in rows)
    assert all(row["external_radiation_resistance_m2K_W"] == "absent_no_qr_output" for row in rows)
    assert all("radiation_absent_no_qr_output" in row["network_terms_resolved"] for row in rows)


def test_validate_rows_passes_generated_rows(tmp_path: Path):
    builder.build_package(tmp_path)
    rows = _read(tmp_path / "patchwise_heat_ledger_enthalpy_interfaces.csv")
    assert builder.validate_rows(rows) == []
