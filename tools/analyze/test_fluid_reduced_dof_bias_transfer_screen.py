#!/usr/bin/env python3
"""Validate the reduced-DOF bias transfer screen artifact."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen"


REQUIRED = [
    "README.md",
    "summary.json",
    "fit_and_transfer_sensor_rows.csv",
    "frozen_coefficients.csv",
    "model_family_dof_ledger.csv",
    "split_metric_scorecard.csv",
    "transfer_summary.csv",
    "split_runtime_leakage_audit.csv",
    "explanation_hypothesis_ledger.csv",
    "source_manifest.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def fnum(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return math.nan


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    missing = [name for name in REQUIRED if not (OUT / name).exists()]
    require(not missing, f"missing outputs: {missing}")

    summary = json.loads((OUT / "summary.json").read_text())
    require(summary["fit_rows"] == 32, "expected Salt1/Salt2 usable fit rows")
    require(summary["transfer_rows"] == 32, "expected Salt3/Salt4 usable transfer rows")
    require(summary["external_test_rows_scored"] == 0, "external-test rows must not be scored")
    require(summary["coefficient_refit_after_transfer_scoring"] is False, "coefficients must be frozen before transfer")
    require(summary["model_selection_from_transfer"] is False, "transfer rows must not select the model")
    require(summary["fluid_solve_run"] is False, "this package must not run Fluid")
    require(summary["final_predictive_admission"] is False, "this package must not admit a final predictive model")

    dof = rows("model_family_dof_ledger.csv")
    predeclared = [r for r in dof if r["predeclared"] == "yes"]
    require(len(predeclared) == 6, "expected six predeclared families")
    require(all(int(r["degrees_of_freedom"]) < 10 for r in predeclared), "all scored families must reduce DOF")
    require(any(r["model_family"] == "prior_per_leg_affine_not_rescored" for r in dof), "prior high-DOF context missing")

    coeffs = rows("frozen_coefficients.csv")
    require(coeffs, "coefficients missing")
    require(
        all(c["coefficient_source"] != "transfer_refit" for c in coeffs),
        "transfer rows must not be coefficient sources",
    )
    require(
        all(c["coefficient_source"] in {"predeclared_baseline", "Salt1_Salt2_train_support_fit_only"} for c in coeffs),
        "unexpected coefficient source",
    )

    scored = rows("fit_and_transfer_sensor_rows.csv")
    transfer_rows = [r for r in scored if r["fit_role"] == "frozen_transfer_score_only" and r["row_usable"] == "True"]
    fit_rows = [r for r in scored if r["fit_role"] == "train_support_fit" and r["row_usable"] == "True"]
    require(transfer_rows, "no frozen transfer rows scored")
    require(fit_rows, "no train/support fit rows scored")
    require(all(r["fit_allowed"] == "False" for r in transfer_rows), "transfer rows cannot be fit-allowed")
    require(all(r["score_allowed"] == "True" for r in transfer_rows), "transfer rows should be score-only")
    require(
        {r["transfer_role"] for r in transfer_rows}
        == {"legacy_validation_transfer_stress", "legacy_holdout_transfer_stress"},
        "unexpected transfer role labels",
    )

    metrics = rows("split_metric_scorecard.csv")
    needed_splits = {
        "train_support_fit",
        "legacy_validation_transfer_stress",
        "legacy_holdout_transfer_stress",
        "all_frozen_transfer_nonfit",
        "all_scored_rows",
    }
    for family in summary["families_scored"]:
        fam = [r for r in metrics if r["model_family"] == family]
        require({r["split_group"] for r in fam} == needed_splits, f"missing split metrics for {family}")
        for row in fam:
            if row["split_group"] != "train_support_fit":
                require(row["selection_role"] == "score_only_no_refit_no_selection", "protected/stress rows must be score-only")

    transfer = rows("transfer_summary.csv")
    require(len(transfer) == len(summary["families_scored"]), "transfer summary family count mismatch")
    nonbaseline = [r for r in transfer if r["model_family"] != "F0_null_baseline"]
    require(
        all(fnum(r["transfer_corrected_mae_K"]) < fnum(r["transfer_baseline_mae_K"]) for r in nonbaseline),
        "all empirical reduced-DOF families should improve frozen transfer against baseline",
    )
    require(
        min(fnum(r["transfer_corrected_mae_K"]) for r in nonbaseline) < 15.0,
        "expected at least one reduced-DOF transfer MAE below 15 K",
    )

    audit = rows("split_runtime_leakage_audit.csv")
    audit_status = {r["audit_item"]: r["status"] for r in audit}
    require(audit_status.get("external_test") == "blocked_not_scored", "external-test blocker must be explicit")
    require(audit_status.get("admission") == "not_admitted", "admission must remain blocked")

    manifest = rows("source_manifest.csv")
    require(all(r["mutation"] == "read_only" for r in manifest), "sources must be read-only")
    print("Reduced-DOF bias transfer screen checks passed.")


if __name__ == "__main__":
    main()
