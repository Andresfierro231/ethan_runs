"""Tests for AGENT-264 rcExternalTemperature implementation audit."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PATCH_SCRIPT = ROOT / "tools/analyze/build_thermal_boundary_patch_role_table.py"
SCRIPT = ROOT / "tools/analyze/build_rc_external_temperature_implementation_audit.py"
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_implementation_audit"
EVIDENCE_CSV = OUT / "rc_external_temperature_evidence_table.csv"
DECISION_JSON = OUT / "radiation_parity_decision.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_rc_external_temperature_implementation_audit", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.path.insert(0, str(SCRIPT.parent))
    spec.loader.exec_module(mod)
    return mod


builder = _load_module()


@pytest.fixture(scope="session")
def generated_package():
    first = subprocess.run([sys.executable, str(PATCH_SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert first.returncode == 0, first.stdout + first.stderr
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    with EVIDENCE_CSV.open(newline="", encoding="utf-8") as handle:
        evidence_rows = list(csv.DictReader(handle))
    decision = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    return evidence_rows, decision


def test_decision_is_inseparable(generated_package):
    _, decision = generated_package
    assert decision["emissivity_Tsur_affect_heat_flux"] == "yes"
    assert decision["parity_radiation_mode"] == "inseparable"
    assert decision["separable_radiation_output_available"] == "no"


def test_compiled_library_evidence_present(generated_package):
    evidence_rows, _ = generated_package
    by_id = {row["evidence_id"]: row for row in evidence_rows}
    assert "compiled_library_strings" in by_id
    assert "compiled_library_symbols" in by_id
    assert by_id["compiled_library_symbols"]["supports_emissivity_Tsur_effect"] == "yes"
    assert "sigma" in by_id["compiled_library_symbols"]["observed"]


def test_case_dictionary_metadata_present(generated_package):
    evidence_rows, decision = generated_package
    by_id = {row["evidence_id"]: row for row in evidence_rows}
    observed = json.loads(by_id["admitted_case_dictionary_fields"]["observed"])
    assert observed["rc_rows"] == 108
    assert observed["rc_rows_with_emissivity"] == 108
    assert observed["rc_rows_with_Tsur"] == 108
    assert decision["all_admitted_rc_patches_have_emissivity_and_Tsur"] is True


def test_builder_validation(generated_package):
    evidence_rows, decision = generated_package
    assert builder.validate(evidence_rows, decision) == []
