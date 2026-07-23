#!/usr/bin/env python3
"""Validate the Salt1-4 refit holdout/external score artifact.

Task: TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score"

REQUIRED = [
    "README.md",
    "summary.json",
    "refit_coefficients.csv",
    "train_fit_quality.csv",
    "holdout_external_score_old_vs_new.csv",
    "best_model_recommendation.csv",
    "claim_boundary_table.csv",
    "source_manifest.csv",
    "no_mutation_guardrails.csv",
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


def test_required_outputs_exist() -> None:
    missing = [name for name in REQUIRED if not (OUT / name).exists()]
    require(not missing, f"missing outputs: {missing}")


def test_summary_flags() -> None:
    summary = json.loads((OUT / "summary.json").read_text())
    require(summary["n_train_rows"] == 64, "expected 64 usable Salt1-4 fit rows")
    require(summary["fit_cases"] == "Salt1,Salt2,Salt3,Salt4", "fit_cases must be all four salts")
    require(summary["second_exposure_of_holdout_and_external_rows_this_session"] is True, "must flag second exposure")
    require(summary["legitimate_single_use_protected_score"] is False, "must not claim a legal freeze score")
    require(summary["physical_closure_claim_allowed"] is False, "must not allow physical closure claim")
    require(summary["native_solver_run"] is False, "must not claim native solver run")
    require(summary["candidate_frozen"] is False, "must not freeze a candidate")
    require(summary["final_predictive_admission"] is False, "must not admit a final predictive model")


def test_f0_identity() -> None:
    """F0 (null baseline) must be the exact identity transform: 0 offset, 1x multiplier."""
    coeffs = rows("refit_coefficients.csv")
    f0 = [c for c in coeffs if c["model_family"] == "F0_null_baseline"]
    require(len(f0) == 1, "F0 should have exactly one coefficient row")
    require(fnum(f0[0]["multiplier_correction"]) == 1.0, "F0 multiplier must be 1.0")
    require(fnum(f0[0]["offset_bias_K"]) == 0.0, "F0 offset must be 0.0")
    require(int(f0[0]["degrees_of_freedom"]) == 0, "F0 must have 0 DOF")


def test_f2_global_affine_refit_coefficients() -> None:
    """Independently-verified refit F2 coefficients (OLS affine on 64 Salt1-4 rows)."""
    coeffs = rows("refit_coefficients.csv")
    f2 = [c for c in coeffs if c["model_family"] == "F2_global_affine"]
    require(len(f2) == 1, "F2 should have exactly one coefficient row (global grouping)")
    mult = fnum(f2[0]["multiplier_correction"])
    offset = fnum(f2[0]["offset_bias_K"])
    require(abs(mult - 0.5746889644933884) < 1e-9, f"unexpected F2 refit multiplier: {mult}")
    require(abs(offset - 138.28222646893295) < 1e-6, f"unexpected F2 refit offset: {offset}")
    require(int(f2[0]["n_fit_rows"]) == 64, "F2 refit must use all 64 Salt1-4 rows")
    require(f2[0]["coefficient_source"] != "Salt1_Salt2_train_support_fit_only", "must not reuse old coefficient_source label")


def test_train_fit_quality_f0_matches_recomputation() -> None:
    """F0 in-sample MAE/RMSE must equal the mean/RMS of the raw baseline residuals
    in the source sensor rows (independent recomputation, not read back from the CSV)."""
    src = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/fit_and_transfer_sensor_rows.csv"
    with src.open(newline="") as f:
        src_rows = list(csv.DictReader(f))
    base = [r for r in src_rows if r["model_family"] == "F0_null_baseline" and r["row_usable"] == "True"]
    require(len(base) == 64, "expected 64 usable Salt1-4 rows in the source file")
    errs = [float(r["baseline_residual_K"]) for r in base]
    mae = sum(abs(e) for e in errs) / len(errs)
    rmse = math.sqrt(sum(e * e for e in errs) / len(errs))

    quality = rows("train_fit_quality.csv")
    f0 = [r for r in quality if r["model_family"] == "F0_null_baseline"][0]
    require(abs(fnum(f0["train_mae_K"]) - mae) < 1e-9, "F0 train MAE mismatch vs independent recomputation")
    require(abs(fnum(f0["train_rmse_K"]) - rmse) < 1e-9, "F0 train RMSE mismatch vs independent recomputation")


def test_old_fit_scores_match_cited_prior_pass() -> None:
    """The recomputed OLD (Salt1/2) fit MAE values must match the cited prior
    in-conversation-pass numbers to within rounding (independent cross-check
    that the raw 1D reproduction + station mapping + target join are correct)."""
    cited = {
        ("salt2_lo5q", "F0_null_baseline"): 89.44,
        ("salt2_lo5q", "F2_global_affine"): 3.47,
        ("salt2_hi5q", "F0_null_baseline"): 100.34,
        ("salt2_hi5q", "F5_thermal_family_offset_shared_multiplier"): 2.89,
        ("val_salt2", "F0_null_baseline"): 90.65,
        ("val_salt2", "F2_global_affine"): 6.45,
    }
    old_vs_new = rows("holdout_external_score_old_vs_new.csv")
    recomputed = {
        (r["case"], r["model_family"]): fnum(r["MAE_K"])
        for r in old_vs_new
        if r["fit_basis"] == "Salt1_2_only"
    }
    for key, cited_mae in cited.items():
        require(key in recomputed, f"missing recomputed old-fit MAE for {key}")
        require(
            abs(recomputed[key] - cited_mae) < 0.01,
            f"recomputed old-fit MAE for {key} = {recomputed[key]} does not match cited {cited_mae}",
        )


def test_f2_is_overall_recommendation() -> None:
    recs = rows("best_model_recommendation.csv")
    by_dim = {r["dimension"]: r["recommended_family"] for r in recs}
    require(by_dim.get("holdout") == "F2_global_affine", "expected F2_global_affine best on holdout")
    require(by_dim.get("external") == "F2_global_affine", "expected F2_global_affine best on external")
    require(by_dim.get("robustness") == "F2_global_affine", "expected F2_global_affine best on robustness")
    require(by_dim.get("overall_recommendation") == "F2_global_affine", "expected F2_global_affine overall")


def test_second_exposure_and_no_mutation_claims() -> None:
    claims = rows("claim_boundary_table.csv")
    require(
        any("second scoring exposure" in r["forbidden_claim"] or "protected-split" in r["forbidden_claim"] for r in claims),
        "must include a claim row forbidding treating this as a legitimate single-use protected score",
    )
    require(
        any("physical closure" in r["forbidden_claim"] for r in claims),
        "must include a claim row forbidding physical closure claims",
    )

    manifest = rows("source_manifest.csv")
    require(all(r["mutation_status"] == "read_only" for r in manifest), "all sources must be read-only")

    guardrails = rows("no_mutation_guardrails.csv")
    require(guardrails, "no_mutation_guardrails.csv must not be empty")
    require(all(r["performed"] == "False" for r in guardrails), "all forbidden actions must be False")


def main() -> None:
    test_required_outputs_exist()
    test_summary_flags()
    test_f0_identity()
    test_f2_global_affine_refit_coefficients()
    test_train_fit_quality_f0_matches_recomputation()
    test_old_fit_scores_match_cited_prior_pass()
    test_f2_is_overall_recommendation()
    test_second_exposure_and_no_mutation_claims()
    print("Empirical bias Salt1-4 refit holdout/external score checks passed.")


if __name__ == "__main__":
    main()
