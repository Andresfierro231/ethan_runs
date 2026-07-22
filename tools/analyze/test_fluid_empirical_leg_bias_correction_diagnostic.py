#!/usr/bin/env python3
"""Validate empirical leg bias/correction diagnostic package."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic"
REQUIRED = [
    "README.md",
    "train_bias_fit_rows.csv",
    "leg_bias_correction_coefficients.csv",
    "corrected_train_residual_metrics.csv",
    "identifiability_audit.csv",
    "explanation_hypothesis_ledger.csv",
    "split_runtime_leakage_audit.csv",
    "source_manifest.csv",
    "summary.json",
]


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    missing = [name for name in REQUIRED if not (OUT / name).exists()]
    assert not missing, f"missing outputs: {missing}"
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["status"] == "complete"
    assert summary["validation_rows_scored"] == 0
    assert summary["holdout_rows_scored"] == 0
    assert summary["external_test_rows_scored"] == 0
    assert summary["fluid_solve_run"] is False
    assert summary["fit_for_physics_admission"] is False
    assert summary["empirical_train_fit"] is True
    assert summary["freeze_or_admission_decision"] is False
    assert summary["corrected_all_mae_K"] < summary["baseline_all_mae_K"]

    coeffs = read_csv("leg_bias_correction_coefficients.csv")
    legs = {row["leg"] for row in coeffs}
    assert {"junction", "downcomer", "upcomer", "cooling_branch", "lower_leg", "unmapped"} <= legs
    assert all(row["physics_admission_status"] == "not_admitted" for row in coeffs)
    assert any(row["identifiability_status"] == "not_identifiable" for row in coeffs)

    fit_rows = read_csv("train_bias_fit_rows.csv")
    assert any(row["fit_usable"] == "False" for row in fit_rows)
    assert any(row["corrected_residual_K"] not in {"", "nan"} for row in fit_rows)

    metrics = read_csv("corrected_train_residual_metrics.csv")
    assert {row["metric_group"] for row in metrics} == {"all", "TP", "TW"}
    for row in metrics:
        assert float(row["corrected_mae_K"]) <= float(row["baseline_mae_K"]) + 1e-9

    audit = read_csv("split_runtime_leakage_audit.csv")
    assert all(row["status"] == "pass" for row in audit)
    assert any("validation, holdout, and external-test rows scored: 0/0/0" in row["detail"] for row in audit)

    print("Empirical leg bias/correction diagnostic checks passed.")


if __name__ == "__main__":
    main()
