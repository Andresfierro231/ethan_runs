#!/usr/bin/env python3
"""Validate the experiment-basis ambient heat-loss + friction model-form
search artifact.

Task: TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-23/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search"

SRC_F2_COEFFS = (
    REPO
    / "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/refit_coefficients.csv"
)
SRC_MASTER_SCOREBOARD = (
    REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv"
)
SRC_BLOCKERS_MD = REPO / ".agent/BLOCKERS.md"
SRC_FRICTION_CLOSURES_PY = (
    REPO.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py"
)
SRC_CLAUDE_MD = REPO / "CLAUDE.md"

REQUIRED = [
    "README.md",
    "summary.json",
    "friction_closure_comparison.csv",
    "mdot_temperature_decoupling_check.csv",
    "prior_undocumented_sweeps_found.csv",
    "sign_convention_corrections.csv",
    "insulation_screening_sweep.csv",
    "insulation_friction_zero_crossing_refinement.csv",
    "salt1_4_train_validation_at_recommended_combo.csv",
    "validation_case_scores_raw_physics.csv",
    "residual_correction_on_physics_baseline.csv",
    "internal_nu_ablation.csv",
    "physical_plausibility_caveats.csv",
    "claim_boundary_table.csv",
    "validation_exposure_count.csv",
    "validation_terminology_crosswalk.csv",
    "source_manifest.csv",
    "no_mutation_guardrails.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def fnum(value: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return math.nan


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_required_outputs_exist() -> None:
    missing = [name for name in REQUIRED if not (OUT / name).exists()]
    require(not missing, f"missing outputs: {missing}")


def test_summary_flags() -> None:
    summary = json.loads((OUT / "summary.json").read_text())
    require(summary["main_body_scope"] == "off_scope_experiment_basis", "must be labeled off-scope for CFD main body")
    require(summary["validated_against"] == "experimental_measured_K_not_CFD_reference_k", "must state measured_K basis")
    require(summary["no_new_solver_runs_by_this_script"] is True, "script must not run the solver")
    require(summary["physical_closure_claim_allowed"] is False, "must not allow physical closure claim")
    require(summary["legitimate_single_use_protected_score"] is False, "must not claim a legal freeze score")
    require(summary["candidate_frozen"] is False, "must not freeze a candidate")
    require(summary["final_predictive_admission"] is False, "must not admit a final predictive model")
    require(summary["native_solver_run_by_this_script"] is False, "must not run native/1D solver")
    require(summary["registry_or_admission_mutated"] is False, "must not mutate registry/admission")


def test_friction_closure_comparison_means_are_internally_consistent() -> None:
    """The mean_pct_err_this_form column must equal mean() of the 4 per-case
    pct_err values for each friction form (self-consistency, per task
    instruction: "internal consistency of the tables you build, e.g. mean()
    of the 4 train mdot errors equals the stated 4.48%")."""
    friction_rows = rows("friction_closure_comparison.csv")
    require(len(friction_rows) == 12, "expected 12 rows (3 friction forms x 4 Salt cases)")

    by_form: dict[str, list[dict[str, str]]] = {}
    for r in friction_rows:
        by_form.setdefault(r["friction_form"], []).append(r)

    require(set(by_form) == {"F1", "F3_shah_apparent", "F3_hagenbach"}, "unexpected friction forms present")

    expected_means = {"F1": 32.6, "F3_shah_apparent": 15.8, "F3_hagenbach": 11.8}
    for form, form_rows in by_form.items():
        require(len(form_rows) == 4, f"expected 4 rows for {form}")
        pct_errs = [fnum(r["pct_err"]) for r in form_rows]
        computed_mean = sum(pct_errs) / len(pct_errs)
        stated_means = {fnum(r["mean_pct_err_this_form"]) for r in form_rows}
        require(len(stated_means) == 1, f"stored mean_pct_err_this_form not uniform across {form} rows")
        require(abs(computed_mean - stated_means.pop()) < 5e-3, f"stored mean does not match computed mean for {form}")
        require(abs(computed_mean - expected_means[form]) < 0.05, f"{form} mean {computed_mean} does not match expected ~{expected_means[form]}")

    # F3_hagenbach must win (lowest mean pct error) for this candidate.
    means = {form: sum(fnum(r["pct_err"]) for r in fr) / len(fr) for form, fr in by_form.items()}
    require(means["F3_hagenbach"] < means["F3_shah_apparent"] < means["F1"], "expected F3_hagenbach < F3_shah_apparent < F1")


def test_f1_based_f2_coefficients_match_upstream_refit_file() -> None:
    """The F1-based F2_global_affine (Salt1-4 refit) coefficients cited in the
    decoupling-check table must exactly match the upstream refit package."""
    upstream = None
    with SRC_F2_COEFFS.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["model_family"] == "F2_global_affine":
                upstream = row
                break
    require(upstream is not None, "could not find F2_global_affine row in upstream refit_coefficients.csv")
    upstream_mult = fnum(upstream["multiplier_correction"])
    upstream_offset = fnum(upstream["offset_bias_K"])

    decoupling = rows("mdot_temperature_decoupling_check.csv")
    f1_based = [r for r in decoupling if r["fit_basis"] == "F1_based"][0]
    require(abs(fnum(f1_based["multiplier_a"]) - upstream_mult) < 1e-9, "F1-based multiplier mismatch vs upstream")
    require(abs(fnum(f1_based["offset_b_K"]) - upstream_offset) < 1e-9, "F1-based offset mismatch vs upstream")

    f3h_based = [r for r in decoupling if r["fit_basis"] == "F3_hagenbach_based"][0]
    # "essentially unchanged" -- train MAE should differ by less than 0.2 K.
    require(abs(fnum(f3h_based["train_mae_K"]) - fnum(f1_based["train_mae_K"])) < 0.2, "train MAE should be essentially unchanged between fit bases")


def test_m3_comparator_matches_master_scoreboard() -> None:
    rows_ = None
    with SRC_MASTER_SCOREBOARD.open(newline="") as f:
        rows_ = [r for r in csv.DictReader(f) if r["scoreboard_id"] == "M3"]
    require(len(rows_) == 1, "expected exactly one M3 row in master scoreboard")
    m3 = rows_[0]
    require(m3["model_form_name"] == "segment_only_fluid_walls", "M3 model_form_name mismatch")
    tp = fnum(m3["tp_rmse_or_error_K"])
    tw = fnum(m3["tw_rmse_or_error_K"])
    require(abs(tp - 13.558) < 1e-3, f"M3 TP mismatch: {tp}")
    require(abs(tw - 18.9775) < 1e-3, f"M3 TW mismatch: {tw}")

    combo_rows = rows("salt1_4_train_validation_at_recommended_combo.csv")
    m3_row = [r for r in combo_rows if r["case"].startswith("COMPARATOR_M3")]
    require(len(m3_row) == 1, "expected exactly one M3 comparator row in salt1_4_train_validation_at_recommended_combo.csv")
    require(abs(fnum(m3_row[0]["TP_K"]) - tp) < 1e-3, "M3 comparator TP mismatch in package table")
    require(abs(fnum(m3_row[0]["TW_K"]) - tw) < 1e-3, "M3 comparator TW mismatch in package table")


def test_guardrail_phrase_cited_verbatim() -> None:
    blockers_text = SRC_BLOCKERS_MD.read_text()
    guardrail_phrase = (
        "do not tune Nu to absorb heater, cooler/HX, passive wall, radiation, storage, or "
        "branch-mixing residuals"
    )
    require(guardrail_phrase in blockers_text, "guardrail phrase not found verbatim in .agent/BLOCKERS.md")

    summary = json.loads((OUT / "summary.json").read_text())
    require(summary["guardrail_phrase_verified"] == guardrail_phrase, "summary.json guardrail phrase mismatch")

    readme_text = (OUT / "README.md").read_text()
    require(guardrail_phrase in readme_text, "guardrail phrase not cited verbatim in README.md")


def test_f4_docstring_line_cited_correctly() -> None:
    text = SRC_FRICTION_CLOSURES_PY.read_text()
    expected_line = "F4  calibrated global multiplier      — existing major_loss_multiplier in MinorLosses"
    require(expected_line in text, "F4 docstring line not found verbatim in friction_closures.py")
    require("Shah, R.K. (1978)" in text, "Shah (1978) citation not found in friction_closures.py")


def test_salt1_4_mean_at_recommended_combo_is_internally_consistent() -> None:
    """mean() of the 4 |mdot_err_pct| values must equal the stated 4.48% (per
    task instruction)."""
    combo_rows = rows("salt1_4_train_validation_at_recommended_combo.csv")
    per_case = [r for r in combo_rows if r["case"] in {"Salt1", "Salt2", "Salt3", "Salt4"}]
    require(len(per_case) == 4, "expected 4 per-case rows (Salt1-4)")
    mean_row = [r for r in combo_rows if r["case"] == "MEAN"]
    require(len(mean_row) == 1, "expected exactly one MEAN row")

    computed_mean_abs_mdot = sum(abs(fnum(r["mdot_err_pct"])) for r in per_case) / 4
    computed_mean_tp = sum(fnum(r["TP_K"]) for r in per_case) / 4
    computed_mean_tw = sum(fnum(r["TW_K"]) for r in per_case) / 4

    require(abs(computed_mean_abs_mdot - fnum(mean_row[0]["mdot_err_pct"])) < 5e-3, "stored mean mdot err mismatch")
    require(abs(computed_mean_tp - fnum(mean_row[0]["TP_K"])) < 5e-3, "stored mean TP mismatch")
    require(abs(computed_mean_tw - fnum(mean_row[0]["TW_K"])) < 5e-3, "stored mean TW mismatch")

    require(abs(computed_mean_abs_mdot - 4.48) < 0.02, f"mean |mdot_err_pct| {computed_mean_abs_mdot} does not match stated 4.48%")
    require(abs(computed_mean_tp - 5.73) < 0.02, f"mean TP {computed_mean_tp} does not match stated 5.73 K")


def test_internal_nu_ablation_is_monotonic_and_asymptotic() -> None:
    ablation_rows = rows("internal_nu_ablation.csv")
    numeric_rows = [r for r in ablation_rows if r["htc_mult"] not in {"CONCLUSION", "MDOT_NOTE"}]
    require(len(numeric_rows) == 9, "expected 9 htc_mult rows")

    tp_values = [fnum(r["TP_K"]) for r in numeric_rows]
    # TP must be monotonically non-increasing as htc_mult increases.
    for a, b in zip(tp_values, tp_values[1:]):
        require(a >= b - 1e-9, "TP must be monotonically non-increasing as htc_mult increases")

    gap_closed = tp_values[0] - tp_values[-1]
    require(abs(gap_closed - 2.36) < 0.02, f"gap closed {gap_closed} does not match stated 2.36 K")

    # Baseline (htc_mult=1) mdot error must match finding 1's F3_hagenbach Salt2 value.
    baseline_row = [r for r in numeric_rows if r["htc_mult"] == "1"][0]
    require(abs(fnum(baseline_row["mdot_err_pct"]) - 12.68) < 1e-6, "baseline mdot error mismatch vs finding 1")

    friction_rows = rows("friction_closure_comparison.csv")
    salt2_f3h = [r for r in friction_rows if r["friction_form"] == "F3_hagenbach" and r["case"] == "Salt2"][0]
    require(abs(fnum(salt2_f3h["pct_err"]) - fnum(baseline_row["mdot_err_pct"])) < 1e-6, "internal-Nu baseline mdot err must match friction_closure_comparison.csv Salt2/F3_hagenbach")


def test_two_prior_sweeps_confirmed_not_in_claude_md_or_scoreboard() -> None:
    claude_md_text = SRC_CLAUDE_MD.read_text()
    scoreboard_text = SRC_MASTER_SCOREBOARD.read_text()
    for name in ("joint_htc_friction_calibration_weekend_focused_v1", "practical_reduced_order_broadened_v1"):
        require(name not in claude_md_text, f"{name} unexpectedly found in CLAUDE.md")
        require(name not in scoreboard_text, f"{name} unexpectedly found in master scoreboard")

    sweep_rows = rows("prior_undocumented_sweeps_found.csv")
    require(len(sweep_rows) == 2, "expected exactly 2 prior-sweep rows")
    for r in sweep_rows:
        require(r["never_referenced_in_claude_md_or_scoreboard_before_now"] == "True", f"expected True for {r['sweep_name']}")
        require(r["friction_form_varied"] == "False", f"expected friction_form_varied False for {r['sweep_name']}")
        require(r["caveat"], f"expected a non-empty caveat for {r['sweep_name']}")


def test_claim_boundary_table_has_required_rows() -> None:
    claims = rows("claim_boundary_table.csv")
    forbidden_texts = [r["forbidden_claim"] for r in claims]
    allowed_texts = [r["allowed_claim"] for r in claims]

    require(
        any("CFD-validated thesis main-body model" in t for t in forbidden_texts),
        "must forbid the claim that this is the CFD-validated thesis main-body model",
    )
    require(
        any("verified physical measurement" in t for t in forbidden_texts),
        "must forbid claiming insulation=8% is a verified physical measurement",
    )
    require(
        any("single-use protected-split score" in t for t in forbidden_texts),
        "must forbid claiming a legitimate single-use protected-split score",
    )
    require(
        any("decisively ruled out" in t for t in allowed_texts),
        "must allow the claim that internal Nu is decisively ruled out up to 500x",
    )
    require(
        any("5.73K" in t or "5.73 K" in t for t in allowed_texts),
        "must allow the claim that F3_hagenbach + insulation reduces mean TP to 5.73K",
    )


def test_validation_exposure_count_documents_third_plus_pass() -> None:
    exposure_rows = rows("validation_exposure_count.csv")
    require(len(exposure_rows) >= 3, "expected at least 3 case rows plus summary")
    case_rows = [r for r in exposure_rows if r["case"] in {"salt2_lo5q", "salt2_hi5q", "val_salt2"}]
    require(len(case_rows) == 3, "expected exactly 3 per-case exposure rows")
    for r in case_rows:
        require("3rd" in r["exposure_number_this_session"] or "4th" in r["exposure_number_this_session"], f"expected 3rd/4th exposure language for {r['case']}")

    summary_row = [r for r in exposure_rows if r["case"] == "ALL_THREE"]
    require(len(summary_row) == 1, "expected an ALL_THREE summary row")
    require(
        "not constitute a legitimate" in summary_row[0]["cumulative_note"]
        or "None of this constitutes a legitimate" in summary_row[0]["cumulative_note"],
        "summary row must state this is not a legitimate protected-split score",
    )


def test_no_mutation_guardrails_all_false() -> None:
    guardrails = rows("no_mutation_guardrails.csv")
    require(guardrails, "no_mutation_guardrails.csv must not be empty")
    require(all(r["performed"] == "False" for r in guardrails), "all forbidden actions must be False")


def test_source_manifest_declares_read_only_or_session_only() -> None:
    manifest = rows("source_manifest.csv")
    require(manifest, "source_manifest.csv must not be empty")
    allowed_status = {"read_only", "session_only_not_a_repo_file"}
    require(all(r["mutation_status"] in allowed_status for r in manifest), "all sources must be read-only or explicitly session-only")
    require(any(r["mutation_status"] == "session_only_not_a_repo_file" for r in manifest), "must include the session-only provenance row for ad hoc numbers")


def main() -> None:
    test_required_outputs_exist()
    test_summary_flags()
    test_friction_closure_comparison_means_are_internally_consistent()
    test_f1_based_f2_coefficients_match_upstream_refit_file()
    test_m3_comparator_matches_master_scoreboard()
    test_guardrail_phrase_cited_verbatim()
    test_f4_docstring_line_cited_correctly()
    test_salt1_4_mean_at_recommended_combo_is_internally_consistent()
    test_internal_nu_ablation_is_monotonic_and_asymptotic()
    test_two_prior_sweeps_confirmed_not_in_claude_md_or_scoreboard()
    test_claim_boundary_table_has_required_rows()
    test_validation_exposure_count_documents_third_plus_pass()
    test_no_mutation_guardrails_all_false()
    test_source_manifest_declares_read_only_or_session_only()
    print("Experiment-basis ambient heat-loss + friction model-form search checks passed.")


if __name__ == "__main__":
    main()
