#!/usr/bin/env python3
"""Focused tests for AGENT-297 predictive external-boundary bridge package."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_predictive_external_bc_implementation_wave.py"
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_predictive_external_bc_implementation_wave", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


builder = _load_module()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_external_boundary_rows_preserve_radiation_policy():
    rows = builder.build_external_bc_dictionary()
    assert len(rows) == 24
    passive = [
        row
        for row in rows
        if row["recommended_runtime_mode"] == "external_boundary_table_setup_candidate"
    ]
    assert passive
    assert {row["emissivity"] for row in passive} == {0.95}
    assert all("include_rcExternalTemperature" in row["setup_radiation_policy"] for row in passive)
    assert all("do_not_add_radiation" in row["realized_flux_replay_policy"] for row in rows)


def test_hx_scorecard_enforces_split_and_hydraulic_guardrail():
    rows = builder.build_hx_scorecard()
    assert len(rows) == 6
    assert {(row["case_id"], row["fit_role"]) for row in rows} >= {
        ("salt_2", "train"),
        ("salt_3", "validation"),
        ("salt_4", "holdout"),
    }
    assert all(row["guardrail_status"] == "hydraulic_guardrail_failed_mdot_overprediction" for row in rows)


def test_real_artifact_build_outputs_expected_files():
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    assert summary["row_counts"]["external_boundary_rows"] == 24
    assert summary["row_counts"]["hx_score_rows"] == 6
    assert summary["fluid_source_modified"] is False
    assert summary["native_solver_outputs_modified"] is False

    external_rows = _read_csv(OUT / "cfd_external_boundary_dictionary.csv")
    decisions = _read_csv(OUT / "implementation_decision_table.csv")
    assert len(external_rows) == 24
    assert any(row["validation_split_role"] == "train" for row in external_rows)
    assert any(row["decision_id"] == "D1_external_boundary_table_contract" for row in decisions)
    assert (OUT / "fluid_external_boundary_patch_plan.md").exists()


if __name__ == "__main__":
    test_external_boundary_rows_preserve_radiation_policy()
    test_hx_scorecard_enforces_split_and_hydraulic_guardrail()
    test_real_artifact_build_outputs_expected_files()
    print("predictive_external_bc_implementation_wave tests passed")
