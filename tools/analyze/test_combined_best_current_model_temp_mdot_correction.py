#!/usr/bin/env python3
"""Validate the combined best-current-model (temperature + mass-flow correction)
artifact.

Task: TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction"
SRC_F2_COEFFS = (
    REPO
    / "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/refit_coefficients.csv"
)

REQUIRED = [
    "README.md",
    "summary.json",
    "combined_model_spec.csv",
    "mdot_correction_fit.csv",
    "temp_correction_holdout_scores.csv",
    "f6_pure_multiplier_ablation.csv",
    "friction_root_cause.csv",
    "claim_boundary_table.csv",
    "evidentiary_tier_table.csv",
    "future_work_sequence.csv",
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
    require(summary["no_new_fitting_beyond_declared_mdot_multiplier"] is True, "must declare no new fitting")
    require(summary["no_new_solver_runs"] is True, "must declare no new solver runs")
    require(summary["physical_closure_claim_allowed"] is False, "must not allow physical closure claim")
    require(summary["mdot_correction_holdout_validated"] is False, "must not claim mdot correction is holdout-validated")
    require(summary["legitimate_single_use_protected_score"] is False, "must not claim a legal freeze score")
    require(summary["candidate_frozen"] is False, "must not freeze a candidate")
    require(summary["final_predictive_admission"] is False, "must not admit a final predictive model")
    require(summary["temp"]["evidentiary_tier"] == "holdout_external_validated", "temp tier mismatch")
    require(summary["mdot"]["evidentiary_tier"] == "train_only_not_validated", "mdot tier mismatch")


def test_mdot_correction_reduces_error_vs_raw_baseline() -> None:
    """The 1-DOF multiplicative mdot correction must reduce error relative to
    the raw (uncorrected) baseline on all 4 known Salt1-4 nominal pairs, both
    in mean relative error and in every individual case."""
    fit_rows = rows("mdot_correction_fit.csv")
    mult_rows = [r for r in fit_rows if r["correction_form"] == "multiplicative_1dof_recommended"]
    require(len(mult_rows) == 4, "expected 4 multiplicative-correction rows (Salt1-4)")

    raw_rel = [fnum(r["raw_rel_err_pct"]) for r in mult_rows]
    corr_rel = [fnum(r["corrected_rel_err_pct"]) for r in mult_rows]
    require(sum(corr_rel) / len(corr_rel) < sum(raw_rel) / len(raw_rel), "corrected mean rel error must be lower than raw")
    for r in mult_rows:
        require(
            fnum(r["corrected_rel_err_pct"]) < fnum(r["raw_rel_err_pct"]),
            f"corrected rel error must be lower than raw for {r['case']}",
        )

    mean_corr = sum(corr_rel) / len(corr_rel)
    require(abs(mean_corr - 3.1658220088627402) < 1e-6, f"unexpected corrected mean rel error: {mean_corr}")


def test_mdot_multiplier_matches_least_squares_recomputation() -> None:
    """Independently recompute a = sum(pred*meas)/sum(pred**2) from the 4
    known Salt1-4 nominal pairs and confirm it matches the value used in
    combined_model_spec.csv / mdot_correction_fit.csv."""
    pairs = [
        (0.019690419543584803, 0.0158),
        (0.0221909170412141, 0.0168),
        (0.02440139973612717, 0.0175),
        (0.026964136779488168, 0.0201),
    ]
    num = sum(p * m for p, m in pairs)
    den = sum(p * p for p, m in pairs)
    a = num / den
    require(abs(a - 0.7504257967710826) < 1e-9, f"recomputed mdot multiplier mismatch: {a}")

    spec = rows("combined_model_spec.csv")
    mdot_spec = [r for r in spec if r["component"] == "mass_flow"][0]
    require(f"a={a!r}" == mdot_spec["coefficients"], "combined_model_spec.csv mdot coefficient mismatch")


def test_friction_f_times_re_is_64() -> None:
    """f*Re must equal 64.0 (within float tolerance) for all four Salt1-4
    nominal cases, confirming the F1 (64/Re) closure is in use."""
    friction_rows = rows("friction_root_cause.csv")
    require(len(friction_rows) == 4, "expected 4 friction root-cause rows (Salt1-4)")
    for r in friction_rows:
        f = fnum(r["friction_factor_main"])
        re = fnum(r["reynolds_main"])
        require(abs(f * re - 64.0) < 1e-6, f"f*Re != 64.0 for {r['case']}: {f * re}")
        require(fnum(r["f_times_Re"]) == fnum(r["f_times_Re"]), "f_times_Re must be numeric")
        require(abs(fnum(r["f_times_Re"]) - 64.0) < 1e-6, f"stored f_times_Re != 64.0 for {r['case']}")
        require(r["closure_form_used"].startswith("F1_"), f"expected F1 closure form for {r['case']}")
        require(
            "F3_hagenbach" in r["closure_forms_available_but_unwired"]
            and "F4_leg_class" in r["closure_forms_available_but_unwired"]
            and "F5_ri_corrected" in r["closure_forms_available_but_unwired"],
            f"expected all three unwired closure names listed for {r['case']}",
        )


def test_f2_temp_coefficients_match_upstream_refit_file() -> None:
    """T-correction coefficients cited in this package's spec must exactly
    match the upstream F2_global_affine (Salt1-4 refit) coefficient file."""
    upstream = None
    with SRC_F2_COEFFS.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["model_family"] == "F2_global_affine":
                upstream = row
                break
    require(upstream is not None, "could not find F2_global_affine row in upstream refit_coefficients.csv")
    upstream_mult = fnum(upstream["multiplier_correction"])
    upstream_offset = fnum(upstream["offset_bias_K"])

    spec = rows("combined_model_spec.csv")
    temp_spec = [r for r in spec if r["component"] == "temperature"][0]
    require(f"a={upstream_mult!r}" in temp_spec["coefficients"], "temp spec multiplier mismatch vs upstream")
    require(f"b={upstream_offset!r}" in temp_spec["coefficients"], "temp spec offset mismatch vs upstream")

    scores = rows("temp_correction_holdout_scores.csv")
    by_case = {r["case"]: r for r in scores}
    require(abs(fnum(by_case["salt2_lo5q"]["MAE_K"]) - 3.5017398572680727) < 1e-9, "salt2_lo5q MAE mismatch")
    require(abs(fnum(by_case["salt2_hi5q"]["MAE_K"]) - 3.1694407461151193) < 1e-9, "salt2_hi5q MAE mismatch")
    require(abs(fnum(by_case["val_salt2"]["MAE_K"]) - 5.868112800214832) < 1e-9, "val_salt2 MAE mismatch")


def test_claim_boundary_table_has_required_forbidden_rows() -> None:
    claims = rows("claim_boundary_table.csv")
    forbidden_texts = [r["forbidden_claim"] for r in claims]

    require(
        any("holdout-validated" in t or "holdout validated" in t for t in forbidden_texts),
        "must include a row forbidding the claim that the mdot correction is holdout-validated",
    )
    require(
        any("physical closure" in t for t in forbidden_texts),
        "must include a row forbidding a physical-closure claim",
    )
    require(
        any("final/frozen predictive score" in t or "protected-split freeze" in t for t in forbidden_texts),
        "must include a row forbidding a final/frozen predictive-score or freeze claim",
    )

    allowed_texts = [r["allowed_claim"] for r in claims]
    require(
        any("combined" in t.lower() and "current" in t.lower() for t in allowed_texts),
        "must include an allowed row for the honest combined-model claim",
    )


def test_evidentiary_tier_table_matches_spec() -> None:
    tiers = {r["component"]: r["tier"] for r in rows("evidentiary_tier_table.csv")}
    require(tiers.get("temperature") == "holdout_external_validated", "temperature tier mismatch")
    require(tiers.get("mass_flow") == "train_only_not_validated", "mass_flow tier mismatch")


def test_f6_ablation_shows_offset_load_bearing() -> None:
    ablation = rows("f6_pure_multiplier_ablation.csv")
    train_rows = [r for r in ablation if r["case"] == "train_Salt1_4"]
    require(len(train_rows) == 2, "expected 2 train rows (both fit bases)")
    for r in train_rows:
        require(fnum(r["MAE_K"]) > 9.291089110109809, "F6 train MAE should be worse than F2 train MAE (9.291 K)")

    holdout_rows = {(r["case"], r["fit_basis"]): fnum(r["MAE_K"]) for r in ablation if r["case"] != "train_Salt1_4"}
    require(len(holdout_rows) == 6, "expected 6 holdout/external rows (3 cases x 2 fit bases)")
    require(
        all("not_robust" in r["verdict"] for r in ablation if r["case"] != "train_Salt1_4"),
        "holdout/external rows must carry the not_robust verdict",
    )


def test_no_mutation_guardrails_all_false() -> None:
    guardrails = rows("no_mutation_guardrails.csv")
    require(guardrails, "no_mutation_guardrails.csv must not be empty")
    require(all(r["performed"] == "False" for r in guardrails), "all forbidden actions must be False")

    manifest = rows("source_manifest.csv")
    require(all(r["mutation_status"] == "read_only" for r in manifest), "all sources must be read-only")


def main() -> None:
    test_required_outputs_exist()
    test_summary_flags()
    test_mdot_correction_reduces_error_vs_raw_baseline()
    test_mdot_multiplier_matches_least_squares_recomputation()
    test_friction_f_times_re_is_64()
    test_f2_temp_coefficients_match_upstream_refit_file()
    test_claim_boundary_table_has_required_forbidden_rows()
    test_evidentiary_tier_table_matches_spec()
    test_f6_ablation_shows_offset_load_bearing()
    test_no_mutation_guardrails_all_false()
    print("Combined best-current model temp/mdot correction checks passed.")


if __name__ == "__main__":
    main()
