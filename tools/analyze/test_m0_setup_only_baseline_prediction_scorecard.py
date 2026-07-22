#!/usr/bin/env python3.11
"""Validate the M0 setup-only baseline scorecard package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_m0_setup_only_baseline_prediction_scorecard.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard"
TASK_ID = "TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True)
    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
    assert summary["task_id"] == TASK_ID
    assert summary["decision"] == "m0_setup_only_baseline_shell_ready_all_predictions_explicitly_missing"
    assert summary["scorecard_target_rows"] > 0
    assert summary["case_rows"] >= 10
    assert summary["metric_rows"] >= 4
    assert summary["numerical_prediction_rows"] == 0
    assert summary["missing_prediction_rows"] == summary["scorecard_target_rows"]
    assert summary["fit_allowed_rows"] == 0
    assert summary["model_selection_allowed_rows"] == 0
    assert summary["runtime_leakage_failures"] == 0
    assert summary["fluid_or_external_edit"] is False
    assert summary["solver_or_scheduler_launch"] is False
    assert summary["validation_holdout_external_scoring"] is False
    assert summary["fitting_tuning_model_selection"] is False
    assert summary["source_property_release"] is False
    assert summary["coefficient_admission"] is False
    assert summary["final_score_claim"] is False
    assert summary["s11_s12_s13_s15_s6_trigger"] is False
    assert summary["hidden_multiplier"] is False

    matrix = read_csv(OUT_DIR / "m0_prediction_matrix.csv")
    assert len(matrix) == summary["scorecard_target_rows"]
    assert {row["model_id"] for row in matrix} == {"M0_setup_only_baseline"}
    assert {row["m0_prediction_status"] for row in matrix} == {"missing_no_frozen_runtime_legal_runner"}
    assert all(row["m0_prediction_value"] == "" for row in matrix)
    assert all(row["fit_allowed"] == "no" for row in matrix)
    assert all(row["model_selection_allowed"] == "no" for row in matrix)

    runtime = read_csv(OUT_DIR / "runtime_input_audit.csv")
    assert runtime
    assert all(row["status"].startswith("pass") for row in runtime)
    forbidden = {row["input_or_action"] for row in runtime if row["runtime_role"] == "forbidden_runtime_input"}
    assert "CFD_mdot" in forbidden
    assert "realized_CFD_wallHeatFlux" in forbidden
    assert "validation_holdout_external_temperatures" in forbidden

    coverage = read_csv(OUT_DIR / "setup_input_coverage_table.csv")
    assert any(row["input_group"] == "frozen_prediction_artifact" and row["coverage_status"] == "missing" for row in coverage)
    assert any(row["input_group"] == "scorecard_schema" and row["coverage_status"] == "available" for row in coverage)

    assert (OUT_DIR / "README.md").exists()
    assert (ROOT / f".agent/status/2026-07-22_{TASK_ID}.md").exists()
    assert (ROOT / ".agent/journal/2026-07-22/m0-setup-only-baseline-prediction-scorecard.md").exists()
    assert (ROOT / "imports/2026-07-22_m0_setup_only_baseline_prediction_scorecard.json").exists()
    print("M0 setup-only baseline scorecard package passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
