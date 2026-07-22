#!/usr/bin/env python3
"""Validate suggested model-form diagnostic test package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_thesis_suggested_model_form_diagnostic_tests.py"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def as_float(value: str) -> float:
    assert value != ""
    return float(value)


def main() -> None:
    subprocess.run([sys.executable, str(BUILDER)], check=True)

    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "diagnostic_model_form_tests_executed_scoreboard_addendum_only"
    assert summary["input_signed_error_rows"] == 204
    assert summary["finite_input_rows"] == 180
    assert summary["tested_forms"] == 6
    assert summary["scored_sensor_rows"] == 270
    assert summary["train_rows_per_m3_form"] == 15
    assert summary["transfer_rows_per_m3_form"] == 30
    assert summary["uses_transfer_targets_for_fit"] is False
    assert summary["admission_status"] == "diagnostic_not_admitted"
    assert summary["total_runtime_s"] > 0.0

    scoreboard = read_csv(OUT / "tested_model_form_scoreboard.csv")
    assert len(scoreboard) == 6
    ids = {row["tested_model_form_id"] for row in scoreboard}
    assert ids == {
        "M2_as_is",
        "M3_as_is",
        "D1_M3_global_bias_offset_train",
        "D2_M3_sensor_kind_offsets_train",
        "D3_M3_wall_linear_shape_train",
        "D4_M3_segment_offsets_min2_train",
    }
    assert all(row["admission_status"] == "diagnostic_not_admitted" for row in scoreboard)
    assert all(row["uses_transfer_targets_for_fit"] == "False" for row in scoreboard)
    assert all(int(row["transfer_rows"]) == 30 for row in scoreboard)
    d1_train_bias = as_float(
        next(row for row in scoreboard if row["tested_model_form_id"] == "D1_M3_global_bias_offset_train")[
            "train_mean_signed_error_K"
        ]
    )
    assert abs(d1_train_bias) < 1e-10

    sensor_rows = read_csv(OUT / "tested_model_form_sensor_errors.csv")
    assert len(sensor_rows) == 270
    assert all(row["admission_status"] == "diagnostic_not_admitted" for row in sensor_rows)
    fitted_transfer = [
        row for row in sensor_rows
        if row["tested_model_form_id"].startswith("D") and row["split_group"] == "transfer"
    ]
    assert fitted_transfer
    assert all(row["uses_transfer_targets_for_fit"] == "False" for row in fitted_transfer)

    assumptions = read_csv(OUT / "construction_assumptions.csv")
    assert len(assumptions) == 6
    assert all("Salt2 train_candidate" in row["split_contract"] for row in assumptions)
    assert all(row["admission_status"] == "diagnostic_not_admitted" for row in assumptions)

    append = read_csv(OUT / "model_form_scoreboard_append.csv")
    assert len(append) == 6
    assert all(row["master_scoreboard_action"] == "append_candidate_addendum_not_inplace_mutation" for row in append)

    runtime = read_csv(OUT / "runtime_audit.csv")
    assert "total_runtime" in {row["phase"] for row in runtime}
    assert all(as_float(row["runtime_s"]) >= 0.0 for row in runtime)

    for rel in [
        "README.md",
        "source_manifest.csv",
        "no_mutation_guardrails.csv",
        "figures/svg/tested_model_form_transfer_rmse.svg",
        "figures/svg/transfer_signed_sensor_errors_best_vs_m3.svg",
    ]:
        path = OUT / rel
        assert path.exists() and path.stat().st_size > 200


if __name__ == "__main__":
    main()
