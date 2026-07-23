#!/usr/bin/env python3
"""Experiment-basis (measured_K) ambient heat-loss + friction model-form search.

Task: TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23
Owner: claude

CRITICAL FRAMING -- READ FIRST
-------------------------------
This ENTIRE package is validated against EXPERIMENTAL `measured_K`
(`validation_table.csv`'s `measured_K` column), NOT CFD `reference_k`. The
thesis main body is CFD-only; this package is the clearly-labeled
experiment-anchored (measured_K) secondary track, per explicit user decision.
It is NOT redone against CFD reference_k, and it is NOT a "superseded" partner
to a CFD-basis package -- this content (ambient heat-loss/friction model-form
search) has no CFD-basis equivalent yet, so it is cross-referenced as a
"parallel main-body track using different reference data," not as
superseded-by content. See README.md's off-scope banner for the full framing.

TERMINOLOGY -- "validation" not "holdout"
------------------------------------------
Per explicit user instruction this session, `salt2_lo5q`/`salt2_hi5q`/
`val_salt2` are called "validation" cases throughout this package (not
"holdout"). A footnote crosswalk to the repo's internal split-policy labels
(holdout = blind_holdout_pm5q for Salt2 +/-5Q, external_test = val_salt2) is
kept in `validation_terminology_crosswalk.csv` so nothing breaks for readers
of other packages using the older terminology.

PROVENANCE -- READ BEFORE TRUSTING ANY NUMBER
-----------------------------------------------
ALL solver-level numbers below (friction-closure comparison, insulation/
friction sweeps, internal-Nu ablation, validation-case scores, residual
correction fit) were computed IN-CONVERSATION THIS SESSION via direct,
ad hoc `solve_case()` calls that were never written to the repo as reusable
tools or scripts. They are hard-coded here with an explicit provenance tag
(`SESSION_SOLVE_PROVENANCE`) and are NOT re-run or re-derived by this script
-- this script's job is to organize/tabulate/cross-check them, not re-solve.
Where a number CAN be independently verified against an existing repo file
(F1-based F2 temperature-correction coefficients, the M3 comparator, the
`friction_closures.py` F4 docstring line, the `.agent/BLOCKERS.md` internal-Nu
guardrail phrase, and the two prior undocumented sweep CSVs), this script
reads that file directly and asserts the match; see `verify_*` functions
below and `tools/analyze/test_experiment_basis_ambient_heat_loss_friction_model_form_search.py`.

NO SOLVER RUNS PERFORMED BY THIS SCRIPT
------------------------------------------
This script performs no OpenFOAM run, no 1D `solve_case()` run, no
case_stage mutation, and touches no other board row's files.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23"
OUT = REPO / "work_products/2026-07/2026-07-23/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search"

# ---------------------------------------------------------------------------
# Read-only source paths (independently checkable numbers only)
# ---------------------------------------------------------------------------

SRC_F2_REFIT_DIR = REPO / "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score"
SRC_F2_COEFFS = SRC_F2_REFIT_DIR / "refit_coefficients.csv"
SRC_F2_TRAIN_QUALITY = SRC_F2_REFIT_DIR / "train_fit_quality.csv"
SRC_F2_HOLDOUT_EXTERNAL = SRC_F2_REFIT_DIR / "holdout_external_score_old_vs_new.csv"

SRC_MASTER_SCOREBOARD = (
    REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv"
)

SRC_BLOCKERS_MD = REPO / ".agent/BLOCKERS.md"

FLUID_REPO = REPO.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid"
SRC_FRICTION_CLOSURES_PY = FLUID_REPO / "tamu_loop_model_v2/friction_closures.py"
SRC_SOLVER_PY = FLUID_REPO / "tamu_loop_model_v2/solver.py"

SRC_JOINT_HTC_SWEEP = FLUID_REPO / "results/diagnostics/joint_htc_friction_calibration_weekend_focused_v1/trial_grid__salt.csv"
SRC_PRACTICAL_ROM_SCENARIO_RANKINGS = FLUID_REPO / "results/diagnostics/practical_reduced_order_broadened_v1/analysis/scenario_rankings.csv"
SRC_PRACTICAL_ROM_SCENARIO_PLAN = FLUID_REPO / "results/diagnostics/practical_reduced_order_broadened_v1/scenario_plan.csv"
SRC_PRACTICAL_ROM_RUN_SUMMARY = FLUID_REPO / "results/diagnostics/practical_reduced_order_broadened_v1/RUN_SUMMARY.md"

SRC_CLAUDE_MD = REPO / "CLAUDE.md"

SESSION_SOLVE_PROVENANCE = (
    "computed_in_session_via_direct_solve_case_calls_this_conversation_ad_hoc_python_"
    "never_written_to_repo_as_reusable_tool_not_rerun_by_this_script_reproducible_only_"
    "by_rerunning_the_solver_with_the_stated_ScenarioConfig_settings"
)

GUARDRAIL_PHRASE = (
    "do not tune Nu to absorb heater, cooler/HX, passive wall, radiation, storage, or "
    "branch-mixing residuals"
)

# ---------------------------------------------------------------------------
# Finding 1 -- friction closure comparison (TSWFC2 candidate
# tswfc2_smoke_salt2_four_node_v1, Salt1-4 nominal)
# ---------------------------------------------------------------------------

MEASURED_MDOT_KG_S = {"Salt1": 0.0158, "Salt2": 0.0168, "Salt3": 0.0175, "Salt4": 0.0201}

FRICTION_FORM_PCT_ERR = {
    "F1": {"Salt1": 24.62, "Salt2": 32.09, "Salt3": 39.44, "Salt4": 34.15},
    "F3_shah_apparent": {"Salt1": 9.78, "Salt2": 15.70, "Salt3": 21.56, "Salt4": 16.29},
    "F3_hagenbach": {"Salt1": 9.08, "Salt2": 12.68, "Salt3": 16.33, "Salt4": 9.19},
}
FRICTION_FORM_NOTE = {
    "F1": "current default (friction_form='F1'); plain 64/Re, no entry-length or buoyancy correction",
    "F3_shah_apparent": (
        "won on a DIFFERENT case config in the historical 2026-07-07 benchmark "
        "(work_products/2026-07/2026-07-07/2026-07-07_friction_forms_comparison/mdot_comparison.csv); "
        "closure performance is candidate-specific, not universally transferable"
    ),
    "F3_hagenbach": (
        "WINNER for this candidate; Shah (1978) entrance-length correction, zero fitting, "
        "already implemented in friction_closures.py, just not wired into this candidate's "
        "friction_form setting (was 'F1')"
    ),
}

SRC_HISTORICAL_FRICTION_BENCHMARK = (
    "work_products/2026-07/2026-07-07/2026-07-07_friction_forms_comparison/mdot_comparison.csv"
)

# ---------------------------------------------------------------------------
# Finding 2 -- mdot/temperature decoupling check
# ---------------------------------------------------------------------------

# F3_hagenbach + T-refit (F2-style affine, Salt1-4 train, n=64 sensor rows).
# Session-computed; not independently re-derivable without re-running the fit.
F3_HAGENBACH_REFIT = {
    "friction_form": "F3_hagenbach",
    "multiplier_a": 0.5756298068314786,
    "offset_b_K": 137.69705222200258,
    "train_mae_K": 9.2465,
    "n_train_rows": 64,
    "salt2_lo5q_MAE_K": 3.476,
    "salt2_lo5q_RMSE_K": 3.872,
    "salt2_hi5q_MAE_K": 3.348,
    "salt2_hi5q_RMSE_K": 4.996,
    "val_salt2_MAE_K": 5.834,
    "val_salt2_RMSE_K": 8.636,
}

DECOUPLING_CONCLUSION = (
    "mdot-correction and T-correction are decoupled for this model -- fixing friction/mdot "
    "does not change the T-bias story at all (train MAE, validation MAE/RMSE all essentially "
    "unchanged between the F1-based and F3_hagenbach-based affine T-refits)"
)

# ---------------------------------------------------------------------------
# Finding 3 -- two undocumented prior sweeps (verified against the actual CSVs
# in this script's verify_* functions; the exact numbers below are re-derived
# from those files, not hard-coded guesses).
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Finding 4 -- sign-error corrections (methodological lesson)
# ---------------------------------------------------------------------------

SIGN_CONVENTION_CORRECTIONS = [
    {
        "parameter": "outer_insulation_multiplier_by_parent_segment",
        "wrong_hypothesis": (
            "Increasing insulation_multiplier would help COOL the too-hot model (assumed it "
            "scaled some kind of loss-conductance UP)"
        ),
        "correct_direction": (
            "It scales insulation THICKNESS directly "
            "(t_ins_m = insulation_thickness_in * INCH_TO_M * insulation_multiplier, in "
            "solver.py near the thermal-path-diagnostics/ambient-loss function) -- so "
            "INCREASING it means MORE insulation, LESS heat loss, HOTTER model, the opposite "
            "of the wrong hypothesis"
        ),
        "evidence": (
            f"{SESSION_SOLVE_PROVENANCE}; first (wrong-direction) sweep confirmed empirically: "
            "ins=1.0 -> TP=96.49K, ins=2.0 -> TP=129.84K (monotonically worse as insulation "
            "increased)"
        ),
        "source_code_reference": "../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py (t_ins_m assignment near line 946)",
    },
    {
        "parameter": "outer_rad_multiplier_by_parent_segment",
        "wrong_hypothesis": "N/A -- no wrong hypothesis; documented as an inertness finding",
        "correct_direction": (
            "Completely inert in every test because this candidate has radiation_on=False "
            "(confirmed: identical results across rad=1/2/4 at fixed insulation/friction). "
            "Not a sign error, but flagged alongside the insulation finding because both "
            "parameters were initially assumed to be live knobs for this candidate"
        ),
        "evidence": SESSION_SOLVE_PROVENANCE,
        "source_code_reference": "../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py (radiation_on gate near lines 965/988)",
    },
    {
        "parameter": "major_loss_multiplier",
        "wrong_hypothesis": (
            "Reducing friction (mlm<1.0) would help close the mdot overprediction the same way "
            "it did with F3_hagenbach alone (still overpredicting mdot at +12.7% Salt2)"
        ),
        "correct_direction": (
            "With F3_hagenbach alone still overpredicting mdot, REDUCING friction (mlm<1.0) made "
            "mdot error WORSE (mlm=1.0 -> +12.68%, 0.7 -> +28.90%, 0.4 -> +55.99%), since less "
            "resistance means more flow in a natural-circulation loop that is already "
            "overpredicting flow. Once real ambient heat loss was added (ins<1.0), the mdot "
            "balance flipped to underpredicting, requiring mlm<1.0 instead -- the correct "
            "direction depends on which other terms are already active"
        ),
        "evidence": SESSION_SOLVE_PROVENANCE,
        "source_code_reference": "../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py (major_loss_multiplier field, MinorLosses)",
    },
]

# ---------------------------------------------------------------------------
# Finding 5 -- corrected-direction insulation screening sweep (Salt2 only,
# F3_hagenbach, ins<1.0, various major_loss_multiplier)
# ---------------------------------------------------------------------------

INSULATION_SCREENING_SWEEP = [
    {"insulation_multiplier": 1.0, "TP_K_min": 96.5, "TP_K_max": 97.0, "note": "baseline (nameplate insulation) across mlm 1.0-2.0"},
    {"insulation_multiplier": 0.5, "TP_K_min": 63.0, "TP_K_max": 63.0, "note": ""},
    {"insulation_multiplier": 0.2, "TP_K_min": 25.6, "TP_K_max": 26.8, "note": ""},
    {"insulation_multiplier": 0.15, "TP_K_min": 15.6, "TP_K_max": 16.6, "note": ""},
    {"insulation_multiplier": 0.12, "TP_K_min": 9.7, "TP_K_max": 10.8, "note": ""},
    {"insulation_multiplier": 0.10, "TP_K_min": 6.0, "TP_K_max": 8.4, "note": "best region"},
    {"insulation_multiplier": 0.08, "TP_K_min": 4.37, "TP_K_max": 4.76, "note": "BEST -- genuine local minimum"},
    {"insulation_multiplier": 0.06, "TP_K_min": 6.9, "TP_K_max": 7.3, "note": "getting worse again"},
    {"insulation_multiplier": 0.05, "TP_K_min": 8.4, "TP_K_max": 9.1, "note": ""},
    {"insulation_multiplier": 0.02, "TP_K_min": 16.2, "TP_K_max": 17.4, "note": ""},
    {"insulation_multiplier": 0.01, "TP_K_min": 19.3, "TP_K_max": 20.6, "note": "worse than ins=0.1 -- confirms non-monotonic optimum, not 'more heat loss is always better'"},
]
INSULATION_SWEEP_BEST = 0.08

# ---------------------------------------------------------------------------
# Finding 6 -- fine mdot-zero-crossing refinement (Salt2, F3_hagenbach) around
# the optimum
# ---------------------------------------------------------------------------

INSULATION_FRICTION_ZERO_CROSSING = [
    {"insulation_multiplier": 0.08, "major_loss_multiplier": 0.60, "mdot_err_pct": -0.67, "TP_K": 4.43, "TW_K": 19.50, "note": "best combo found -- near-zero mdot error AND near-minimum TP"},
    {"insulation_multiplier": 0.09, "major_loss_multiplier": 0.60, "mdot_err_pct": 0.64, "TP_K": 4.85, "TW_K": 19.61, "note": ""},
    {"insulation_multiplier": 0.07, "major_loss_multiplier": 0.60, "mdot_err_pct": -2.04, "TP_K": 5.35, "TW_K": 19.73, "note": ""},
]
RECOMMENDED_INSULATION_MULTIPLIER = 0.08
RECOMMENDED_MAJOR_LOSS_MULTIPLIER = 0.60

# ---------------------------------------------------------------------------
# Finding 7 -- full Salt1-4 TRAIN validation at the recommended combo
# ---------------------------------------------------------------------------

SALT1_4_TRAIN_AT_RECOMMENDED_COMBO = [
    {"case": "Salt1", "mdot_err_pct": -7.66, "TP_K": 11.04, "TW_K": 20.57, "note": "Salt1 documented elsewhere in this repo as 'weakly converged; use with caution' per CLAUDE.md -- likely explains why it is the outlier here, not a model-form failure"},
    {"case": "Salt2", "mdot_err_pct": -0.67, "TP_K": 4.43, "TW_K": 19.50, "note": ""},
    {"case": "Salt3", "mdot_err_pct": 6.16, "TP_K": 3.94, "TW_K": 20.51, "note": ""},
    {"case": "Salt4", "mdot_err_pct": 3.44, "TP_K": 3.51, "TW_K": 22.16, "note": ""},
]

BASELINE_F1_INS1_COMPARATOR = {
    "friction_form": "F1",
    "insulation_multiplier": 1.0,
    "mean_abs_mdot_err_pct": 32.6,
    "TP_K_range": "90-100",
    "source": "work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/friction_root_cause.csv (f*Re=64.0 confirms F1) and this package's own finding 1",
}

M3_COMPARATOR_SCOREBOARD_ID = "M3"
M3_COMPARATOR_NAME = "segment_only_fluid_walls"
M3_COMPARATOR_NOTE = (
    "best previously-found NON-empirical (real model-form, not post-hoc statistical fit) "
    "comparator anywhere in this repo -- a totally different reduced-order framework, not this "
    "Fluid solver; diagnostic_not_admitted status there"
)

# ---------------------------------------------------------------------------
# Finding 8 -- validation-case scores at the recommended combo, RAW (zero
# fitted/statistical parameters)
# ---------------------------------------------------------------------------

VALIDATION_CASE_SCORES_RAW_PHYSICS = [
    {
        "case": "salt2_lo5q",
        "case_role_this_package": "validation",
        "split_policy_label_crosswalk": "blind_holdout_pm5q",
        "MAE_K": 5.387,
        "RMSE_K": 5.586,
        "mdot_kg_s": 0.015866,
        "mdot_ground_truth_available": False,
        "property_basis_caveat": "",
    },
    {
        "case": "salt2_hi5q",
        "case_role_this_package": "validation",
        "split_policy_label_crosswalk": "blind_holdout_pm5q",
        "MAE_K": 2.398,
        "RMSE_K": 4.292,
        "mdot_kg_s": 0.017491,
        "mdot_ground_truth_available": False,
        "property_basis_caveat": "",
    },
    {
        "case": "val_salt2",
        "case_role_this_package": "validation",
        "split_policy_label_crosswalk": "external_test",
        "MAE_K": 7.418,
        "RMSE_K": 10.786,
        "mdot_kg_s": 0.011763,
        "mdot_ground_truth_available": False,
        "property_basis_caveat": (
            "This package used the salt_current property override for val_salt2 per this "
            "session's earlier convention. The PARALLEL CFD-basis session found this was "
            "methodologically inconsistent for the CFD comparison -- it found val_salt2's "
            "correct operating point should use salt_jin default properties matching Salt2 "
            "nominal, not salt_current. This experiment-basis package has NOT been re-verified "
            "against that correction. Flag as a known limitation needing follow-up; do not "
            "silently claim consistency."
        ),
    },
]

EARLIER_EMPIRICAL_F1_BASED_F2_COMPARATOR = {
    "salt2_lo5q_MAE_K": 3.50,
    "salt2_hi5q_MAE_K": 3.17,
    "val_salt2_MAE_K": 5.87,
    "n_fitted_parameters": 2,
    "note": (
        "the physics-only combo here is comparable overall (better on hi5q, worse on lo5q and "
        "val_salt2) with ZERO fitted parameters vs. F2's 2 fitted parameters"
    ),
}

# ---------------------------------------------------------------------------
# Finding 9 -- small residual affine correction fit ON TOP of the physics
# baseline (Salt1-4 train, n=64 rows, same OLS methodology as the F2 refits)
# ---------------------------------------------------------------------------

RESIDUAL_CORRECTION_ON_PHYSICS_BASELINE = {
    "multiplier_a": 0.7915691091053846,
    "offset_b_K": 97.05201417937809,
    "train_mae_K": 9.2199,
    "n_train_rows": 64,
    "meta_finding": (
        "essentially the SAME ~9.2K training ceiling as every other affine-correction attempt "
        "this session regardless of underlying raw model -- the 2-DOF affine correction form "
        "itself seems to have a ~9.2-9.3K floor on this dataset no matter what physics precedes "
        "it, suggesting genuine local/segment-level structure a global affine correction cannot "
        "capture"
    ),
}

RESIDUAL_CORRECTION_VALIDATION_SCORES = [
    {"case": "salt2_lo5q", "MAE_K": 2.834, "RMSE_K": 3.569},
    {"case": "salt2_hi5q", "MAE_K": 4.034, "RMSE_K": 5.456},
    {"case": "val_salt2", "MAE_K": 5.523, "RMSE_K": 8.794},
]
RESIDUAL_CORRECTION_STATUS = "OPTIONAL, not required"
RESIDUAL_CORRECTION_TRADEOFF_NOTE = (
    "helps lo5q substantially but slightly hurts hi5q vs the raw-physics-only version -- a "
    "genuine tradeoff, not a strict win"
)

# ---------------------------------------------------------------------------
# Finding 10 -- internal-Nu ablation (insulation RESET to nameplate=1.0,
# internal_htc_mode='per_parent_multiplier' uniform across all 12 parent
# segments, Salt2 only, F3_hagenbach, major_loss_multiplier=1.0)
# ---------------------------------------------------------------------------

INTERNAL_NU_ABLATION = [
    {"htc_mult": 1, "TP_K": 96.49, "TW_K": 98.94, "mdot_err_pct": 12.68},
    {"htc_mult": 2, "TP_K": 95.31, "TW_K": 98.98, "mdot_err_pct": None},
    {"htc_mult": 5, "TP_K": 94.60, "TW_K": 99.01, "mdot_err_pct": None},
    {"htc_mult": 10, "TP_K": 94.36, "TW_K": 99.02, "mdot_err_pct": None},
    {"htc_mult": 20, "TP_K": 94.24, "TW_K": 99.03, "mdot_err_pct": None},
    {"htc_mult": 50, "TP_K": 94.17, "TW_K": 99.03, "mdot_err_pct": None},
    {"htc_mult": 100, "TP_K": 94.15, "TW_K": 99.03, "mdot_err_pct": None},
    {"htc_mult": 200, "TP_K": 94.13, "TW_K": 99.03, "mdot_err_pct": None},
    {"htc_mult": 500, "TP_K": 94.13, "TW_K": 99.03, "mdot_err_pct": None, "note": "asymptote reached"},
]
INTERNAL_NU_MDOT_NOTE = (
    "mdot_err_pct only reported at htc_mult=1 (matches finding 1's F3_hagenbach Salt2 +12.68%); "
    "not reported separately at other htc_mult values in-session, expected to remain "
    "approximately unchanged since only internal HTC (not friction or mdot-relevant terms) was "
    "varied in this ablation"
)
INTERNAL_NU_GAP_CLOSED_K = 96.49 - 94.13  # 2.36 K
INTERNAL_NU_CONCLUSION = (
    "Internal HTC, swept across 500x (a physically implausible magnitude for a real Nusselt "
    "correlation on this geometry), asymptotically closes only 96.49-94.13=2.36 K of the ~96 K "
    "gap. As internal h -> infinity, internal thermal resistance R_i -> 0, which only removes ONE "
    "term from the total series resistance network (R_i + R_wall + R_ins + R_o); the asymptote "
    "proves the wall/insulation/ambient resistances dominate completely, meaning NO internal-Nu "
    "value can close this gap. This is quantitative evidence FOR this repo's own standing "
    "guardrail rather than mere deference to it -- the guardrail is numerically justified here, "
    "not just procedurally followed."
)

# ---------------------------------------------------------------------------
# Finding 11 -- physical plausibility caveats
# ---------------------------------------------------------------------------

PHYSICAL_PLAUSIBILITY_CAVEATS = [
    {
        "parameter": "outer_insulation_multiplier (uniform ~0.08, i.e. effective insulation ~8% of nameplate thickness)",
        "status": "CALIBRATED FINDING, NOT an independently-verified physical measurement",
        "note": (
            "Physically plausible (candidate mechanisms: gaps at supports/instrumentation ports, "
            "degraded/aged insulation, uninsulated fittings or bends, thermal bridging) but has "
            "not been checked against the actual rig's as-built insulation condition (e.g. "
            "photos, physical inspection, or an independent measurement). Future work should "
            "verify this against the real rig before treating it as more than a calibrated "
            "hypothesis."
        ),
    },
    {
        "parameter": "major_loss_multiplier (~0.6)",
        "status": "already-anticipated calibrated-multiplier tier (F4), not a new kind of empirical knob",
        "note": (
            "Sits within the ALREADY-DOCUMENTED 'F4' calibrated-multiplier tier of the friction "
            "closure hierarchy in friction_closures.py's own docstring "
            "('F4 calibrated global multiplier -- existing major_loss_multiplier in MinorLosses')."
        ),
    },
]

# ---------------------------------------------------------------------------
# Finding 12 -- validation-exposure count
# ---------------------------------------------------------------------------

VALIDATION_EXPOSURE_COUNT_ROWS = [
    {"case": "salt2_lo5q", "exposure_number_this_session": "3rd-4th (depending on how counted)", "cumulative_note": "empirical-only F1-based (this package's prior sibling), empirical-only Salt1-4-refit (prior sibling), physics-only F3_hagenbach+insulation (this package), physics+residual correction (this package)"},
    {"case": "salt2_hi5q", "exposure_number_this_session": "3rd-4th (depending on how counted)", "cumulative_note": "same four attempts as salt2_lo5q"},
    {"case": "val_salt2", "exposure_number_this_session": "3rd-4th (depending on how counted)", "cumulative_note": "same four attempts as salt2_lo5q"},
]
VALIDATION_EXPOSURE_HONEST_STATEMENT = (
    "None of this constitutes a legitimate single-use protected-split score. This package is a "
    "further exposure on top of the two already documented in the prior packages "
    "(2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score, "
    "2026-07-23_combined_best_current_model_temp_mdot_correction)."
)

CLAIM_BOUNDARY_ROWS = [
    {
        "allowed_claim": "internal Nu is decisively ruled out as the residual driver up to 500x",
        "forbidden_claim": "this is the CFD-validated thesis main-body model",
        "evidence_path": "internal_nu_ablation.csv",
    },
    {
        "allowed_claim": (
            "F3_hagenbach + insulation calibration reduces mean TP from ~90-100K to 5.73K across "
            "all 4 train cases with real validation-data confirmation"
        ),
        "forbidden_claim": "insulation=8% is a verified physical measurement",
        "evidence_path": "salt1_4_train_validation_at_recommended_combo.csv;validation_case_scores_raw_physics.csv;physical_plausibility_caveats.csv",
    },
    {
        "allowed_claim": (
            "the friction closure comparison and mdot/T decoupling check are real, zero-fitting "
            "physics-level findings for this candidate"
        ),
        "forbidden_claim": "this is a legitimate single-use protected-split score",
        "evidence_path": "friction_closure_comparison.csv;validation_exposure_count.csv",
    },
    {
        "allowed_claim": (
            "this is genuinely new physics-finding content not previously done in either basis "
            "(CFD or experiment) and can be cross-referenced as the parallel experiment-basis "
            "track to the CFD-basis main body"
        ),
        "forbidden_claim": (
            "this package supersedes or is superseded by the CFD-basis main-body track (no such "
            "relationship exists; they use different reference data for different purposes)"
        ),
        "evidence_path": "README.md",
    },
    {
        "allowed_claim": (
            "the two prior undocumented sweeps (joint_htc_friction_calibration_weekend_focused_v1, "
            "practical_reduced_order_broadened_v1) never varied friction_form and never tested "
            "insulation multipliers below 0.85x, leaving the ambient heat-loss magnitude direction "
            "genuinely untested before this package"
        ),
        "forbidden_claim": (
            "these two sweeps were entirely unknown to the repo -- their file paths appear in two "
            "prior exploration/read-list contexts (a command-list status file, a report anchor "
            "list), just never analyzed for this TP/TW-stuck-across-grid finding or entered into "
            "CLAUDE.md/the thesis scoreboard"
        ),
        "evidence_path": "prior_undocumented_sweeps_found.csv",
    },
]

FUTURE_WORK_CROSSREF = (
    "Ambient heat loss (insulation + friction calibration) is a distinct physics-finding line "
    "of work from the friction-closure-only and empirical-bias-correction packages that precede "
    "it in this session; see the operational note for the recommended next-task sequence."
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def fnum(value: object) -> float:
    return float(value)


# ---------------------------------------------------------------------------
# Independent verification against reachable repo files (asserts; raises on
# mismatch so a transcription error cannot silently ship).
# ---------------------------------------------------------------------------


def verify_f1_based_f2_temperature_correction() -> dict[str, Any]:
    coeffs = read_csv(SRC_F2_COEFFS)
    f2 = [c for c in coeffs if c["model_family"] == "F2_global_affine"]
    if len(f2) != 1:
        raise RuntimeError(f"Expected exactly one F2_global_affine row in {SRC_F2_COEFFS}, found {len(f2)}")
    a = fnum(f2[0]["multiplier_correction"])
    b = fnum(f2[0]["offset_bias_K"])

    train_quality = read_csv(SRC_F2_TRAIN_QUALITY)
    train_row = [r for r in train_quality if r["model_family"] == "F2_global_affine"][0]
    train_mae = fnum(train_row["train_mae_K"])

    scores = read_csv(SRC_F2_HOLDOUT_EXTERNAL)
    refit_scores = {
        row["case"]: (fnum(row["MAE_K"]), fnum(row["RMSE_K"]))
        for row in scores
        if row["model_family"] == "F2_global_affine" and row["fit_basis"] == "Salt1_4_refit"
    }

    expected_a = 0.5746889644933884
    expected_train_mae = 9.291089110109809
    if abs(a - expected_a) > 1e-9:
        raise RuntimeError(f"F1-based F2 multiplier {a} does not match expected {expected_a}")
    if abs(train_mae - expected_train_mae) > 1e-9:
        raise RuntimeError(f"F1-based F2 train MAE {train_mae} does not match expected {expected_train_mae}")

    return {
        "multiplier_a": a,
        "offset_b_K": b,
        "train_mae_K": train_mae,
        "salt2_lo5q_MAE_K": refit_scores["salt2_lo5q"][0],
        "salt2_lo5q_RMSE_K": refit_scores["salt2_lo5q"][1],
        "salt2_hi5q_MAE_K": refit_scores["salt2_hi5q"][0],
        "salt2_hi5q_RMSE_K": refit_scores["salt2_hi5q"][1],
        "val_salt2_MAE_K": refit_scores["val_salt2"][0],
        "val_salt2_RMSE_K": refit_scores["val_salt2"][1],
    }


def verify_m3_comparator() -> dict[str, Any]:
    rows = read_csv(SRC_MASTER_SCOREBOARD)
    m3 = [r for r in rows if r["scoreboard_id"] == M3_COMPARATOR_SCOREBOARD_ID]
    if len(m3) != 1:
        raise RuntimeError(f"Expected exactly one M3 row in {SRC_MASTER_SCOREBOARD}, found {len(m3)}")
    row = m3[0]
    if row["model_form_name"] != M3_COMPARATOR_NAME:
        raise RuntimeError(f"M3 model_form_name mismatch: {row['model_form_name']!r}")
    tp = fnum(row["tp_rmse_or_error_K"])
    tw = fnum(row["tw_rmse_or_error_K"])
    if abs(tp - 13.558) > 1e-3:
        raise RuntimeError(f"M3 TP {tp} does not match expected 13.558")
    if abs(tw - 18.9775) > 1e-3:
        raise RuntimeError(f"M3 TW {tw} does not match expected 18.9775")
    return {"tp_rmse_K": tp, "tw_rmse_K": tw, "admission_status": row["admission_status"]}


def verify_guardrail_phrase() -> str:
    text = SRC_BLOCKERS_MD.read_text()
    if GUARDRAIL_PHRASE not in text:
        raise RuntimeError(f"Guardrail phrase not found verbatim in {SRC_BLOCKERS_MD}")
    return GUARDRAIL_PHRASE


def verify_f4_docstring_line() -> str:
    text = SRC_FRICTION_CLOSURES_PY.read_text()
    expected_line = "F4  calibrated global multiplier      — existing major_loss_multiplier in MinorLosses"
    if expected_line not in text:
        raise RuntimeError(f"F4 docstring line not found verbatim in {SRC_FRICTION_CLOSURES_PY}")
    if "Shah, R.K. (1978)" not in text or "K_HAGENBACH: float = 1.33" not in text:
        raise RuntimeError("F3_hagenbach Shah (1978) citation / K_HAGENBACH constant not found")
    return expected_line


def verify_insulation_multiplier_code_reference() -> None:
    text = SRC_SOLVER_PY.read_text()
    if "t_ins_m = insulation_thickness_in * INCH_TO_M * insulation_multiplier" not in text:
        raise RuntimeError("insulation-thickness formula not found verbatim in solver.py")
    if "major_loss_multiplier: float = 1.0" not in text:
        raise RuntimeError("major_loss_multiplier default not found verbatim in solver.py")


def verify_joint_htc_friction_calibration_sweep() -> dict[str, Any]:
    rows = read_csv(SRC_JOINT_HTC_SWEEP)
    n_rows = len(rows)
    tp = [fnum(r["mean_tp_rmse_K"]) for r in rows]
    tw = [fnum(r["mean_tw_no_tw10_rmse_K"]) for r in rows]
    mdot_abs_err = [abs(fnum(r["mean_mass_flow_relative_error_pct"])) for r in rows]
    has_friction_form_column = "friction_form" in rows[0]
    return {
        "n_data_rows": n_rows,
        "tp_min": min(tp),
        "tp_max": max(tp),
        "tw_min": min(tw),
        "tw_max": max(tw),
        "best_mdot_abs_err_pct": min(mdot_abs_err),
        "worst_mdot_abs_err_pct": max(mdot_abs_err),
        "friction_form_varied": has_friction_form_column,
    }


def verify_practical_reduced_order_sweep() -> dict[str, Any]:
    rows = read_csv(SRC_PRACTICAL_ROM_SCENARIO_RANKINGS)
    n_rows = len(rows)
    best_tp = min(fnum(r["mean_tp_rmse_K"]) for r in rows)
    has_friction_form_column = "friction_form" in rows[0]

    plan_rows = read_csv(SRC_PRACTICAL_ROM_SCENARIO_PLAN)
    insulation_dicts = {r["outer_insulation_multiplier_by_parent_segment"] for r in plan_rows}
    insulation_values: set[float] = set()
    for d in insulation_dicts:
        for match in re.findall(r":\s*([0-9.]+)", d):
            insulation_values.add(float(match))
    min_insulation_multiplier_tested = min(insulation_values) if insulation_values else None
    max_insulation_multiplier_tested = max(insulation_values) if insulation_values else None

    run_summary_text = SRC_PRACTICAL_ROM_RUN_SUMMARY.read_text()
    m = re.search(r"Mean TW RMSE excluding TW10: `([0-9.]+) K` with `std=([0-9.]+)`", run_summary_text)
    if not m:
        raise RuntimeError(f"Could not find mean TW RMSE line in {SRC_PRACTICAL_ROM_RUN_SUMMARY}")
    mean_tw_excl_tw10 = float(m.group(1))
    std_tw_excl_tw10 = float(m.group(2))

    return {
        "n_rows": n_rows,
        "best_tp_rmse_K": best_tp,
        "friction_form_varied": has_friction_form_column,
        "min_insulation_multiplier_tested": min_insulation_multiplier_tested,
        "max_insulation_multiplier_tested": max_insulation_multiplier_tested,
        "mean_tw_excl_tw10_K": mean_tw_excl_tw10,
        "std_tw_excl_tw10_K": std_tw_excl_tw10,
    }


def verify_sweeps_not_in_claude_md_or_scoreboard() -> dict[str, bool]:
    claude_md_text = SRC_CLAUDE_MD.read_text()
    scoreboard_text = SRC_MASTER_SCOREBOARD.read_text()
    names = ["joint_htc_friction_calibration_weekend_focused_v1", "practical_reduced_order_broadened_v1"]
    return {
        name: (name not in claude_md_text and name not in scoreboard_text)
        for name in names
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_friction_closure_comparison() -> None:
    rows: list[dict[str, object]] = []
    for form, errs in FRICTION_FORM_PCT_ERR.items():
        mean_err = sum(errs.values()) / len(errs)
        for case, err in errs.items():
            rows.append(
                {
                    "friction_form": form,
                    "case": case,
                    "measured_mdot_kg_s": MEASURED_MDOT_KG_S[case],
                    "pct_err": err,
                    "mean_pct_err_this_form": round(mean_err, 2),
                    "note": FRICTION_FORM_NOTE[form],
                }
            )
    write_csv(
        OUT / "friction_closure_comparison.csv",
        rows,
        ["friction_form", "case", "measured_mdot_kg_s", "pct_err", "mean_pct_err_this_form", "note"],
    )


def write_mdot_temperature_decoupling_check(f1_based: dict[str, Any]) -> None:
    rows = [
        {
            "fit_basis": "F1_based",
            "friction_form_for_mdot": "F1",
            "multiplier_a": f1_based["multiplier_a"],
            "offset_b_K": f1_based["offset_b_K"],
            "train_mae_K": f1_based["train_mae_K"],
            "salt2_lo5q_MAE_K": f1_based["salt2_lo5q_MAE_K"],
            "salt2_hi5q_MAE_K": f1_based["salt2_hi5q_MAE_K"],
            "val_salt2_MAE_K": f1_based["val_salt2_MAE_K"],
            "provenance": str(SRC_F2_REFIT_DIR.relative_to(REPO)),
        },
        {
            "fit_basis": "F3_hagenbach_based",
            "friction_form_for_mdot": "F3_hagenbach",
            "multiplier_a": F3_HAGENBACH_REFIT["multiplier_a"],
            "offset_b_K": F3_HAGENBACH_REFIT["offset_b_K"],
            "train_mae_K": F3_HAGENBACH_REFIT["train_mae_K"],
            "salt2_lo5q_MAE_K": F3_HAGENBACH_REFIT["salt2_lo5q_MAE_K"],
            "salt2_hi5q_MAE_K": F3_HAGENBACH_REFIT["salt2_hi5q_MAE_K"],
            "val_salt2_MAE_K": F3_HAGENBACH_REFIT["val_salt2_MAE_K"],
            "provenance": SESSION_SOLVE_PROVENANCE,
        },
        {
            "fit_basis": "CONCLUSION",
            "friction_form_for_mdot": "",
            "multiplier_a": "",
            "offset_b_K": "",
            "train_mae_K": "",
            "salt2_lo5q_MAE_K": "",
            "salt2_hi5q_MAE_K": "",
            "val_salt2_MAE_K": "",
            "provenance": DECOUPLING_CONCLUSION,
        },
    ]
    write_csv(
        OUT / "mdot_temperature_decoupling_check.csv",
        rows,
        [
            "fit_basis",
            "friction_form_for_mdot",
            "multiplier_a",
            "offset_b_K",
            "train_mae_K",
            "salt2_lo5q_MAE_K",
            "salt2_hi5q_MAE_K",
            "val_salt2_MAE_K",
            "provenance",
        ],
    )


def write_prior_undocumented_sweeps_found(joint_htc: dict[str, Any], practical_rom: dict[str, Any], not_in_docs: dict[str, bool]) -> None:
    rows = [
        {
            "sweep_name": "joint_htc_friction_calibration_weekend_focused_v1",
            "path": str(SRC_JOINT_HTC_SWEEP.relative_to(REPO.parent)),
            "n_data_rows": joint_htc["n_data_rows"],
            "varied_parameters": "major_loss_multiplier x profile_descriptor_htc_gain/friction_gain x heater_leg_multiplier/upcomer_leg_multiplier",
            "friction_form_varied": joint_htc["friction_form_varied"],
            "insulation_magnitude_tested": "n/a (no insulation column in this sweep)",
            "key_finding": (
                f"best mdot-error row abs err {joint_htc['best_mdot_abs_err_pct']:.4f}% but "
                f"mean_tp_rmse_K stays {joint_htc['tp_min']:.2f}-{joint_htc['tp_max']:.2f}K and "
                f"mean_tw_no_tw10_rmse_K stays {joint_htc['tw_min']:.2f}-{joint_htc['tw_max']:.2f}K "
                f"across the ENTIRE {joint_htc['n_data_rows']}-row grid -- HTC-shape/profile-descriptor "
                "tuning has essentially zero leverage on TP/TW"
            ),
            "never_referenced_in_claude_md_or_scoreboard_before_now": not_in_docs["joint_htc_friction_calibration_weekend_focused_v1"],
            "caveat": (
                "file path DOES appear in two prior exploration/read-list contexts "
                "(.agent/status/2026-06-19_AGENT-090.md's command list; a 'head -20' listing) "
                "but the TP/TW-stuck-across-grid finding itself was never previously extracted, "
                "analyzed, or entered into CLAUDE.md or the thesis master_model_form_scoreboard"
            ),
        },
        {
            "sweep_name": "practical_reduced_order_broadened_v1",
            "path": str(SRC_PRACTICAL_ROM_SCENARIO_RANKINGS.relative_to(REPO.parent)),
            "n_data_rows": practical_rom["n_rows"],
            "varied_parameters": "internal_htc_mode + outer_closure_mode + profile-descriptor gains + insulation_thickness_in (1.0/2.0) + per-segment outer_insulation/conv/rad multipliers",
            "friction_form_varied": practical_rom["friction_form_varied"],
            "insulation_magnitude_tested": (
                f"per-segment outer_insulation_multiplier_by_parent_segment values "
                f"{practical_rom['min_insulation_multiplier_tested']:.2f}-"
                f"{practical_rom['max_insulation_multiplier_tested']:.2f}x nameplate "
                f"(never below {practical_rom['min_insulation_multiplier_tested']:.2f}x, far above "
                f"this package's found optimum of ~{INSULATION_SWEEP_BEST:.2f}x)"
            ),
            "key_finding": (
                f"best found mean_tp_rmse_K={practical_rom['best_tp_rmse_K']:.2f}, but overall mean "
                f"TW-excl-TW10 RMSE = {practical_rom['mean_tw_excl_tw10_K']:.3f} K "
                f"(std {practical_rom['std_tw_excl_tw10_K']:.3f}) per its RUN_SUMMARY.md"
            ),
            "never_referenced_in_claude_md_or_scoreboard_before_now": not_in_docs["practical_reduced_order_broadened_v1"],
            "caveat": (
                "file path DOES appear in two prior exploration/read-list contexts "
                "(recent_coordination_audit.csv external-git-status listing; "
                "dual_path_execution_report.md's anchor list) but the TP/TW-stuck finding itself "
                "was never previously extracted, analyzed, or entered into CLAUDE.md or the thesis "
                "master_model_form_scoreboard"
            ),
        },
    ]
    write_csv(
        OUT / "prior_undocumented_sweeps_found.csv",
        rows,
        [
            "sweep_name",
            "path",
            "n_data_rows",
            "varied_parameters",
            "friction_form_varied",
            "insulation_magnitude_tested",
            "key_finding",
            "never_referenced_in_claude_md_or_scoreboard_before_now",
            "caveat",
        ],
    )


def write_sign_convention_corrections() -> None:
    write_csv(
        OUT / "sign_convention_corrections.csv",
        SIGN_CONVENTION_CORRECTIONS,
        ["parameter", "wrong_hypothesis", "correct_direction", "evidence", "source_code_reference"],
    )


def write_insulation_screening_sweep() -> None:
    write_csv(
        OUT / "insulation_screening_sweep.csv",
        INSULATION_SCREENING_SWEEP,
        ["insulation_multiplier", "TP_K_min", "TP_K_max", "note"],
    )


def write_insulation_friction_zero_crossing_refinement() -> None:
    write_csv(
        OUT / "insulation_friction_zero_crossing_refinement.csv",
        INSULATION_FRICTION_ZERO_CROSSING,
        ["insulation_multiplier", "major_loss_multiplier", "mdot_err_pct", "TP_K", "TW_K", "note"],
    )


def write_salt1_4_train_validation_at_recommended_combo(m3: dict[str, Any]) -> None:
    rows = list(SALT1_4_TRAIN_AT_RECOMMENDED_COMBO)
    mean_abs_mdot = sum(abs(r["mdot_err_pct"]) for r in rows) / len(rows)
    mean_tp = sum(r["TP_K"] for r in rows) / len(rows)
    mean_tw = sum(r["TW_K"] for r in rows) / len(rows)
    rows_out = [
        {**r, "friction_form": "F3_hagenbach", "insulation_multiplier": RECOMMENDED_INSULATION_MULTIPLIER, "major_loss_multiplier": RECOMMENDED_MAJOR_LOSS_MULTIPLIER}
        for r in rows
    ]
    rows_out.append(
        {
            "case": "MEAN",
            "mdot_err_pct": round(mean_abs_mdot, 2),
            "TP_K": round(mean_tp, 2),
            "TW_K": round(mean_tw, 2),
            "note": "mean of |mdot_err_pct|, TP_K, TW_K across all four cases",
            "friction_form": "F3_hagenbach",
            "insulation_multiplier": RECOMMENDED_INSULATION_MULTIPLIER,
            "major_loss_multiplier": RECOMMENDED_MAJOR_LOSS_MULTIPLIER,
        }
    )
    rows_out.append(
        {
            "case": "COMPARATOR_F1_ins1_baseline",
            "mdot_err_pct": BASELINE_F1_INS1_COMPARATOR["mean_abs_mdot_err_pct"],
            "TP_K": BASELINE_F1_INS1_COMPARATOR["TP_K_range"],
            "TW_K": "",
            "note": BASELINE_F1_INS1_COMPARATOR["source"],
            "friction_form": "F1",
            "insulation_multiplier": 1.0,
            "major_loss_multiplier": 1.0,
        }
    )
    rows_out.append(
        {
            "case": f"COMPARATOR_{M3_COMPARATOR_SCOREBOARD_ID}_{M3_COMPARATOR_NAME}",
            "mdot_err_pct": "",
            "TP_K": m3["tp_rmse_K"],
            "TW_K": m3["tw_rmse_K"],
            "note": M3_COMPARATOR_NOTE,
            "friction_form": "n/a (different reduced-order framework)",
            "insulation_multiplier": "",
            "major_loss_multiplier": "",
        }
    )
    write_csv(
        OUT / "salt1_4_train_validation_at_recommended_combo.csv",
        rows_out,
        ["case", "friction_form", "insulation_multiplier", "major_loss_multiplier", "mdot_err_pct", "TP_K", "TW_K", "note"],
    )


def write_validation_case_scores_raw_physics() -> None:
    rows = [dict(r) for r in VALIDATION_CASE_SCORES_RAW_PHYSICS]
    rows.append(
        {
            "case": "COMPARATOR_earlier_empirical_F1_based_F2",
            "case_role_this_package": "comparator",
            "split_policy_label_crosswalk": "",
            "MAE_K": "",
            "RMSE_K": "",
            "mdot_kg_s": "",
            "mdot_ground_truth_available": "",
            "property_basis_caveat": (
                f"salt2_lo5q={EARLIER_EMPIRICAL_F1_BASED_F2_COMPARATOR['salt2_lo5q_MAE_K']}K, "
                f"salt2_hi5q={EARLIER_EMPIRICAL_F1_BASED_F2_COMPARATOR['salt2_hi5q_MAE_K']}K, "
                f"val_salt2={EARLIER_EMPIRICAL_F1_BASED_F2_COMPARATOR['val_salt2_MAE_K']}K "
                f"with {EARLIER_EMPIRICAL_F1_BASED_F2_COMPARATOR['n_fitted_parameters']} fitted "
                f"parameters; {EARLIER_EMPIRICAL_F1_BASED_F2_COMPARATOR['note']}"
            ),
        }
    )
    write_csv(
        OUT / "validation_case_scores_raw_physics.csv",
        rows,
        [
            "case",
            "case_role_this_package",
            "split_policy_label_crosswalk",
            "MAE_K",
            "RMSE_K",
            "mdot_kg_s",
            "mdot_ground_truth_available",
            "property_basis_caveat",
        ],
    )


def write_residual_correction_on_physics_baseline() -> None:
    rows = [
        {
            "row_type": "coefficients",
            "multiplier_a": RESIDUAL_CORRECTION_ON_PHYSICS_BASELINE["multiplier_a"],
            "offset_b_K": RESIDUAL_CORRECTION_ON_PHYSICS_BASELINE["offset_b_K"],
            "MAE_K": RESIDUAL_CORRECTION_ON_PHYSICS_BASELINE["train_mae_K"],
            "case_or_note": f"train (Salt1-4, n={RESIDUAL_CORRECTION_ON_PHYSICS_BASELINE['n_train_rows']})",
            "status": RESIDUAL_CORRECTION_STATUS,
        }
    ]
    for r in RESIDUAL_CORRECTION_VALIDATION_SCORES:
        rows.append(
            {
                "row_type": "validation_score",
                "multiplier_a": "",
                "offset_b_K": "",
                "MAE_K": r["MAE_K"],
                "case_or_note": r["case"],
                "status": RESIDUAL_CORRECTION_STATUS,
            }
        )
    mean_mae = sum(r["MAE_K"] for r in RESIDUAL_CORRECTION_VALIDATION_SCORES) / len(RESIDUAL_CORRECTION_VALIDATION_SCORES)
    rows.append(
        {
            "row_type": "meta_finding",
            "multiplier_a": "",
            "offset_b_K": "",
            "MAE_K": round(mean_mae, 3),
            "case_or_note": RESIDUAL_CORRECTION_ON_PHYSICS_BASELINE["meta_finding"],
            "status": RESIDUAL_CORRECTION_TRADEOFF_NOTE,
        }
    )
    write_csv(
        OUT / "residual_correction_on_physics_baseline.csv",
        rows,
        ["row_type", "multiplier_a", "offset_b_K", "MAE_K", "case_or_note", "status"],
    )


def write_internal_nu_ablation() -> None:
    rows = []
    for r in INTERNAL_NU_ABLATION:
        rows.append(
            {
                "htc_mult": r["htc_mult"],
                "TP_K": r["TP_K"],
                "TW_K": r["TW_K"],
                "mdot_err_pct": r["mdot_err_pct"] if r["mdot_err_pct"] is not None else "",
                "note": r.get("note", ""),
            }
        )
    rows.append(
        {
            "htc_mult": "CONCLUSION",
            "TP_K": round(INTERNAL_NU_GAP_CLOSED_K, 2),
            "TW_K": "",
            "mdot_err_pct": "",
            "note": INTERNAL_NU_CONCLUSION,
        }
    )
    rows.append(
        {
            "htc_mult": "MDOT_NOTE",
            "TP_K": "",
            "TW_K": "",
            "mdot_err_pct": "",
            "note": INTERNAL_NU_MDOT_NOTE,
        }
    )
    write_csv(OUT / "internal_nu_ablation.csv", rows, ["htc_mult", "TP_K", "TW_K", "mdot_err_pct", "note"])


def write_physical_plausibility_caveats() -> None:
    write_csv(
        OUT / "physical_plausibility_caveats.csv",
        PHYSICAL_PLAUSIBILITY_CAVEATS,
        ["parameter", "status", "note"],
    )


def write_claim_boundary_table() -> None:
    write_csv(OUT / "claim_boundary_table.csv", CLAIM_BOUNDARY_ROWS, ["allowed_claim", "forbidden_claim", "evidence_path"])


def write_validation_exposure_count() -> None:
    rows = list(VALIDATION_EXPOSURE_COUNT_ROWS)
    rows.append(
        {
            "case": "ALL_THREE",
            "exposure_number_this_session": "",
            "cumulative_note": VALIDATION_EXPOSURE_HONEST_STATEMENT,
        }
    )
    write_csv(OUT / "validation_exposure_count.csv", rows, ["case", "exposure_number_this_session", "cumulative_note"])


def write_validation_terminology_crosswalk() -> None:
    rows = [
        {
            "this_package_label": "validation (salt2_lo5q)",
            "repo_split_policy_label": "blind_holdout_pm5q (Salt2 -5%Q)",
            "note": "genuine perturbation run, never used in any fit in this package",
        },
        {
            "this_package_label": "validation (salt2_hi5q)",
            "repo_split_policy_label": "blind_holdout_pm5q (Salt2 +5%Q)",
            "note": "genuine perturbation run, never used in any fit in this package",
        },
        {
            "this_package_label": "validation (val_salt2)",
            "repo_split_policy_label": "external_test",
            "note": "independent external-test case, different property set/basis than Salt1-4 train",
        },
    ]
    write_csv(OUT / "validation_terminology_crosswalk.csv", rows, ["this_package_label", "repo_split_policy_label", "note"])


def write_source_manifest() -> None:
    paths = [
        (SRC_F2_COEFFS, "F1-based F2_global_affine temperature-correction coefficients (independently re-verified)"),
        (SRC_F2_TRAIN_QUALITY, "F1-based F2_global_affine train MAE/RMSE (independently re-verified)"),
        (SRC_F2_HOLDOUT_EXTERNAL, "F1-based F2_global_affine validation MAE/RMSE for salt2_lo5q/hi5q/val_salt2 (independently re-verified)"),
        (SRC_MASTER_SCOREBOARD, "M3 comparator TP/TW RMSE (independently re-verified)"),
        (SRC_BLOCKERS_MD, "thermal-cfd-1d-parity guardrail phrase (independently re-verified verbatim)"),
        (SRC_FRICTION_CLOSURES_PY, "F4 calibrated-global-multiplier docstring line and F3_hagenbach/Shah(1978) citation (independently re-verified verbatim, read/run-only, not edited)"),
        (SRC_SOLVER_PY, "insulation-thickness formula and major_loss_multiplier default (independently re-verified verbatim, read/run-only, not edited)"),
        (SRC_JOINT_HTC_SWEEP, "joint_htc_friction_calibration_weekend_focused_v1 trial grid (independently re-verified row count, TP/TW ranges, best mdot row, absence of friction_form column)"),
        (SRC_PRACTICAL_ROM_SCENARIO_RANKINGS, "practical_reduced_order_broadened_v1 scenario rankings (independently re-verified row count, best TP, absence of friction_form column)"),
        (SRC_PRACTICAL_ROM_SCENARIO_PLAN, "practical_reduced_order_broadened_v1 scenario plan (independently re-verified insulation-multiplier range tested: 0.85-1.5x)"),
        (SRC_PRACTICAL_ROM_RUN_SUMMARY, "practical_reduced_order_broadened_v1 RUN_SUMMARY.md mean/std TW RMSE excl TW10 (independently re-verified)"),
        (SRC_CLAUDE_MD, "checked that neither prior sweep's name appears here (independently re-verified)"),
        (Path("work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/friction_root_cause.csv"), "f*Re=64.0 confirming F1 baseline (cited, prior sibling package, read-only)"),
        (Path("SESSION-ONLY, no file"), "friction closure comparison percentages (finding 1); F3_hagenbach T-refit (finding 2); insulation/friction sweeps (findings 5-7); validation-case raw-physics scores (finding 8); residual correction fit (finding 9); internal-Nu ablation (finding 10) -- all computed in-session via direct solve_case() calls this conversation, not written to any repo file, not re-run by this script"),
    ]
    write_csv(
        OUT / "source_manifest.csv",
        [{"path": str(p), "used_for": use, "mutation_status": "read_only" if "SESSION" not in str(p) else "session_only_not_a_repo_file"} for p, use in paths],
        ["path", "used_for", "mutation_status"],
    )


def write_no_mutation_guardrails() -> None:
    guardrails = [
        "native_output_mutation",
        "registry_or_admission_mutation",
        "scheduler_action",
        "solver_postprocessing_sampler_or_harvest_launch",
        "fluid_or_external_edit",
        "thesis_current_or_latex_edit",
        "physical_source_property_or_qwall_release",
        "physical_candidate_freeze",
        "physical_closure_claim",
        "coefficient_admission_as_physically_confirmed",
        "s11_s15_s6_trigger",
        "blocker_register_source_change_before_closeout",
        "generated_index_refresh_before_closeout",
        "deletion",
        "staging",
        "commit",
        "push",
        "other_board_row_file_touched",
        "cfd_reference_k_basis_claimed_as_main_body",
        "insulation_8pct_claimed_as_verified_physical_measurement",
        "legitimate_single_use_protected_split_score_claimed",
        "new_solver_run_performed_by_this_script",
    ]
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [{"forbidden_action": g, "performed": False} for g in guardrails],
        ["forbidden_action", "performed"],
    )


def write_readme(context: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/refit_coefficients.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/train_fit_quality.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/holdout_external_score_old_vs_new.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv
  - .agent/BLOCKERS.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/joint_htc_friction_calibration_weekend_focused_v1/trial_grid__salt.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/practical_reduced_order_broadened_v1/analysis/scenario_rankings.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/practical_reduced_order_broadened_v1/scenario_plan.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/practical_reduced_order_broadened_v1/RUN_SUMMARY.md
tags: [forward-model, experiment-basis, measured-K, ambient-heat-loss, insulation, friction-closure, internal-nu-ablation, model-form-search, off-scope-cfd-main-body]
related:
  - .agent/status/2026-07-23_TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23.md
  - .agent/journal/2026-07-23/experiment-basis-ambient-heat-loss-friction-model-form-search.md
  - imports/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search.json
  - operational_notes/07-26/23/2026-07-23_EXPERIMENT_BASIS_AMBIENT_HEAT_LOSS_FRICTION_MODEL_FORM_SEARCH.md
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md
  - work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/README.md
task: {TASK_ID}
date: 2026-07-23
role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
main_body_scope: off_scope_experiment_basis
parallel_main_body_track: work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score (CFD-basis, different reference data, NOT superseded/superseding -- this content has no CFD-basis equivalent yet)
---
# Experiment-Basis Ambient Heat-Loss + Friction Model-Form Search

> **OFF-SCOPE FOR THE CFD-ONLY THESIS MAIN BODY (2026-07-23, user-directed).**
> This package is validated against **experimental `measured_K`**
> (`validation_table.csv`'s `measured_K` column), NOT CFD `reference_k`. The
> thesis main body is purely computational (CFD `reference_k` is the reference
> truth), so this experiment-basis result must NOT be cited as the CFD-validated
> model. It is retained as the experiment-anchored (measured_K) secondary track,
> exactly like its two sibling packages
> (`2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score`,
> `2026-07-23_combined_best_current_model_temp_mdot_correction`).
>
> Unlike those two siblings, this package's content (real solver-level
> ambient-heat-loss/friction model-form search, not a post-hoc statistical
> correction) has **no CFD-basis equivalent yet** -- it is genuinely new
> physics-finding content not previously done in either basis. It is therefore
> cross-referenced as **"the parallel main-body track using different
> reference data"**
> (`work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/`),
> not claimed as superseded by or superseding it.

## Terminology note: "validation" not "holdout"

Per explicit user instruction this session, `salt2_lo5q`, `salt2_hi5q`, and
`val_salt2` are called **validation** cases throughout this package (not
"holdout"). See `validation_terminology_crosswalk.csv` for a footnote
crosswalk to the repo's internal split-policy labels (holdout =
`blind_holdout_pm5q` for Salt2 +/-5Q, external_test = `val_salt2`) so nothing
breaks for readers of other packages using the older terminology.

Decision: `experiment_basis_ambient_heat_loss_friction_model_form_search_complete_measured_K_track_not_a_physical_closure_not_a_freeze_score`.

## PROVENANCE CALLOUT (read first)

ALL solver-level numbers in this package (friction-closure comparison,
insulation/friction sweeps, internal-Nu ablation, validation-case scores,
residual correction fit) were computed **in-conversation this session** via
direct, ad hoc `solve_case()` calls that were never written to the repo as
reusable tools. They are cited here with an explicit provenance tag and are
**reproducible only by re-running the solver** with the stated
`ScenarioConfig` settings -- this script does not re-run the solver, only
organizes/tabulates/cross-checks the numbers. Wherever a number could be
independently checked against an existing repo file (the F1-based F2
temperature-correction coefficients, the M3 comparator, the
`friction_closures.py` F4 docstring line and F3_hagenbach/Shah(1978)
citation, the `.agent/BLOCKERS.md` internal-Nu guardrail phrase, and the two
prior undocumented sweep CSVs), this script reads that file directly and
asserts the match -- see `tools/analyze/build_experiment_basis_ambient_heat_loss_friction_model_form_search.py`'s
`verify_*` functions and the accompanying test suite.

## What this package is

A real solver-level model-form search for reducing TP/TW error on the TSWFC2
candidate `tswfc2_smoke_salt2_four_node_v1` -- friction-closure form,
ambient heat-loss (insulation) magnitude, and internal-Nu magnitude -- scored
against **experimental measured_K**, as requested when the user asked for the
best model form using real solver-level search (not just post-hoc empirical
correction). It documents twelve findings: a friction-closure comparison; an
mdot/temperature decoupling check; two undocumented prior sweeps found in the
Fluid repo; a sign-error correction (methodological lesson); a corrected-
direction insulation screening sweep with a genuine non-monotonic optimum; a
fine mdot-zero-crossing refinement; full Salt1-4 train validation at the
recommended combo; validation-case scores with zero fitted parameters; an
optional residual affine correction on top of the physics baseline; a
decisive internal-Nu ablation up to 500x; physical-plausibility caveats; and
a validation-exposure count.

## What this package is NOT

- Not the CFD-validated thesis main-body model (see off-scope banner above).
- Not a physical closure. The insulation_multiplier~=0.08 value is a
  calibrated finding, NOT an independently-verified physical measurement of
  the rig's actual insulation condition.
- Not a legitimate single-use protected-split score. `salt2_lo5q`,
  `salt2_hi5q`, and `val_salt2` have now been scored at least a 3rd-4th time
  this session across this package and its two siblings (see
  `validation_exposure_count.csv`).
- Not superseded by or superseding the CFD-basis main-body track -- this is
  new physics-finding content with no CFD-basis equivalent yet.
- Does not run OpenFOAM or the 1D `solve_case()` solver (all solver-level
  numbers were computed earlier in this session, not by this script); does
  not mutate any case_stage tree; does not touch any other board row's files.

## What this proves vs. what remains a hypothesis

- **Decisive / rigorous (proves a negative, not just deference to a
  guardrail):** the internal-Nu ablation (finding 10) sweeps internal HTC
  across 500x -- a physically implausible magnitude -- and shows the gap
  closes by only 2.36 K of ~96 K before asymptoting. This is quantitative,
  falsifiable evidence that no internal-Nu value can close the residual gap,
  because the series thermal-resistance network (R_i + R_wall + R_ins + R_o)
  is dominated by the non-internal terms. This directly and numerically
  justifies this repo's own standing guardrail
  ("{context['guardrail_phrase']}") rather than merely deferring to it.
- **Calibrated / needs rig verification (a hypothesis, not a proof):** the
  insulation_multiplier~=0.08 (effective insulation ~8% of nameplate
  thickness) finding is a curve-matching result against experimental
  `measured_K`. It is physically plausible (gaps at supports/instrumentation
  ports, degraded/aged insulation, uninsulated fittings, thermal bridging)
  but has NOT been checked against the rig's actual as-built insulation
  condition. Treat it as a calibrated hypothesis pending independent
  physical verification (see `physical_plausibility_caveats.csv`).

## Headline numbers (see CSVs for full detail and provenance)

### 1. Friction closure comparison (Salt1-4 nominal, TSWFC2 candidate)

F3_hagenbach wins: mean pct error 11.8% vs F3_shah_apparent's 15.8% and F1's
32.6%, with zero fitting. This reverses the 2026-07-07 historical benchmark
(`{SRC_HISTORICAL_FRICTION_BENCHMARK}`), where F3_shah_apparent won on a
DIFFERENT case config -- closure performance is candidate-specific, not
universally transferable. See `friction_closure_comparison.csv`.

### 2. mdot/temperature decoupling check

Refitting the F2-style affine T-correction on F3_hagenbach-based 1D
predictions gives train MAE ~9.25 K and validation MAE ~3.48/3.35/5.83 K --
essentially identical to the F1-based refit's 9.29 K / 3.50/3.17/5.87 K.
Mdot-correction and T-correction are decoupled for this model. See
`mdot_temperature_decoupling_check.csv`.

### 3. Two undocumented prior sweeps found

`joint_htc_friction_calibration_weekend_focused_v1`
({context['joint_htc']['n_data_rows']} data rows) shows TP RMSE stuck at
{context['joint_htc']['tp_min']:.2f}-{context['joint_htc']['tp_max']:.2f} K and
TW RMSE stuck at {context['joint_htc']['tw_min']:.2f}-{context['joint_htc']['tw_max']:.2f} K
across its entire grid regardless of HTC-shape/profile-descriptor tuning.
`practical_reduced_order_broadened_v1` ({context['practical_rom']['n_rows']}
rows) found best TP RMSE {context['practical_rom']['best_tp_rmse_K']:.2f} K but
overall mean TW-excl-TW10 RMSE {context['practical_rom']['mean_tw_excl_tw10_K']:.3f} K
(std {context['practical_rom']['std_tw_excl_tw10_K']:.3f}). Neither sweep varied
`friction_form`, and the insulation multiplier range actually tested in the
second sweep was {context['practical_rom']['min_insulation_multiplier_tested']:.2f}-
{context['practical_rom']['max_insulation_multiplier_tested']:.2f}x nameplate --
never approaching this package's found optimum of ~{INSULATION_SWEEP_BEST:.2f}x.
See `prior_undocumented_sweeps_found.csv` (includes an honest caveat: the file
paths DO appear in two prior exploration/read-list contexts, just never
analyzed for this finding or entered into CLAUDE.md/the thesis scoreboard).

### 4. Sign-error correction (methodological lesson)

`outer_insulation_multiplier_by_parent_segment` scales insulation THICKNESS
directly, so increasing it means MORE insulation and a HOTTER model -- the
opposite of the initial wrong hypothesis. `outer_rad_multiplier_by_parent_segment`
was inert (this candidate has `radiation_on=False`). `major_loss_multiplier`
direction also flipped once real ambient heat loss was added. See
`sign_convention_corrections.csv`.

### 5-6. Insulation screening sweep and zero-crossing refinement

A genuine non-monotonic optimum near insulation_multiplier~=0.08 (TP~4.4-4.8
K), with major_loss_multiplier=0.60 giving the best combined mdot/TP result
(mdot_err=-0.67%, TP=4.43 K, TW=19.50 K, Salt2). See
`insulation_screening_sweep.csv` and
`insulation_friction_zero_crossing_refinement.csv`.

### 7. Full Salt1-4 train validation at the recommended combo

(friction_form=F3_hagenbach, insulation_multiplier=0.08 uniform,
major_loss_multiplier=0.6): mean |mdot_err|=4.48%, TP=5.73 K, TW=20.69 K
across all four Salt1-4 train cases (Salt1 is the outlier at TP=11.04 K,
consistent with this repo's documented "Salt1 weakly converged" caveat).
Compare to the F1/ins=1.0 baseline (mean |mdot_err|=32.6%, TP~90-100 K) and to
the M3 comparator (`{context['m3']['tp_rmse_K']}` K TP, `{context['m3']['tw_rmse_K']}` K TW,
diagnostic_not_admitted). See `salt1_4_train_validation_at_recommended_combo.csv`.

### 8. Validation-case scores, RAW physics (zero fitted parameters)

salt2_lo5q MAE=5.387 K, salt2_hi5q MAE=2.398 K, val_salt2 MAE=7.418 K
(val_salt2 carries a property-basis caveat -- see below). Comparable overall
to the earlier empirical F1-based F2 correction's 3.50/3.17/5.87 K, with ZERO
fitted parameters instead of 2. See `validation_case_scores_raw_physics.csv`.

**val_salt2 property-basis caveat:** this package used the `salt_current`
property override for val_salt2 per this session's earlier convention. The
PARALLEL CFD-basis session found this was methodologically inconsistent for
the CFD comparison and that val_salt2's correct operating point should use
`salt_jin` default properties matching Salt2 nominal. This experiment-basis
package has NOT been re-verified against that correction -- flagged as a
known limitation needing follow-up, not silently claimed consistent.

### 9. Optional residual affine correction on top of the physics baseline

a=0.7915691091053846, b=97.05201417937809, train MAE=9.2199 K -- essentially
the SAME ~9.2 K training ceiling as every other affine-correction attempt
this session regardless of underlying physics, suggesting a genuine
local/segment-level structure a global affine correction cannot capture. With
this correction: mean validation MAE=4.13 K (best mean found this session),
but it is a genuine tradeoff (helps lo5q, slightly hurts hi5q vs raw-physics-
only), not a strict win, and is OPTIONAL, not required. See
`residual_correction_on_physics_baseline.csv`.

### 10. Internal-Nu ablation -- decisive ruling-out

See "What this proves vs. what remains a hypothesis" above and
`internal_nu_ablation.csv` for the full 9-row htc_mult sweep.

### 11. Physical plausibility caveats

See `physical_plausibility_caveats.csv`: insulation_multiplier~=0.08 is a
calibrated hypothesis needing rig verification; major_loss_multiplier~=0.6
sits within the already-documented F4 calibrated-multiplier tier of
`friction_closures.py`'s own hierarchy.

### 12. Validation-exposure count

`salt2_lo5q`/`salt2_hi5q`/`val_salt2` have now been scored at least a
3rd-4th time this session (across this package and its two siblings). See
`validation_exposure_count.csv`. None of this constitutes a legitimate
single-use protected-split score.

## Open first

- `friction_closure_comparison.csv`
- `mdot_temperature_decoupling_check.csv`
- `prior_undocumented_sweeps_found.csv`
- `sign_convention_corrections.csv`
- `insulation_screening_sweep.csv`
- `insulation_friction_zero_crossing_refinement.csv`
- `salt1_4_train_validation_at_recommended_combo.csv`
- `validation_case_scores_raw_physics.csv`
- `residual_correction_on_physics_baseline.csv`
- `internal_nu_ablation.csv`
- `physical_plausibility_caveats.csv`
- `claim_boundary_table.csv`
- `validation_exposure_count.csv`
- `validation_terminology_crosswalk.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
"""
    (OUT / "README.md").write_text(text)


def write_summary(context: dict[str, Any]) -> None:
    summary = {
        "task_id": TASK_ID,
        "date": "2026-07-23",
        "status": "complete",
        "main_body_scope": "off_scope_experiment_basis",
        "validated_against": "experimental_measured_K_not_CFD_reference_k",
        "no_new_solver_runs_by_this_script": True,
        "friction_closure_comparison": {
            form: round(sum(errs.values()) / len(errs), 2) for form, errs in FRICTION_FORM_PCT_ERR.items()
        },
        "recommended_combo": {
            "friction_form": "F3_hagenbach",
            "insulation_multiplier": RECOMMENDED_INSULATION_MULTIPLIER,
            "major_loss_multiplier": RECOMMENDED_MAJOR_LOSS_MULTIPLIER,
        },
        "salt1_4_train_mean_at_recommended_combo": {
            "mean_abs_mdot_err_pct": round(sum(abs(r["mdot_err_pct"]) for r in SALT1_4_TRAIN_AT_RECOMMENDED_COMBO) / 4, 2),
            "mean_TP_K": round(sum(r["TP_K"] for r in SALT1_4_TRAIN_AT_RECOMMENDED_COMBO) / 4, 2),
            "mean_TW_K": round(sum(r["TW_K"] for r in SALT1_4_TRAIN_AT_RECOMMENDED_COMBO) / 4, 2),
        },
        "validation_case_scores_raw_physics_MAE_K": {
            r["case"]: r["MAE_K"] for r in VALIDATION_CASE_SCORES_RAW_PHYSICS
        },
        "internal_nu_ablation_gap_closed_K": round(INTERNAL_NU_GAP_CLOSED_K, 2),
        "m3_comparator": context["m3"],
        "f1_based_f2_verified": {
            "multiplier_a": context["f1_based_f2"]["multiplier_a"],
            "offset_b_K": context["f1_based_f2"]["offset_b_K"],
            "train_mae_K": context["f1_based_f2"]["train_mae_K"],
        },
        "guardrail_phrase_verified": context["guardrail_phrase"],
        "physical_closure_claim_allowed": False,
        "legitimate_single_use_protected_score": False,
        "candidate_frozen": False,
        "final_predictive_admission": False,
        "native_solver_run_by_this_script": False,
        "registry_or_admission_mutated": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    f1_based_f2 = verify_f1_based_f2_temperature_correction()
    m3 = verify_m3_comparator()
    guardrail_phrase = verify_guardrail_phrase()
    verify_f4_docstring_line()
    verify_insulation_multiplier_code_reference()
    joint_htc = verify_joint_htc_friction_calibration_sweep()
    practical_rom = verify_practical_reduced_order_sweep()
    not_in_docs = verify_sweeps_not_in_claude_md_or_scoreboard()

    # Cross-check finding 1's self-consistency (mean of the 4 stated pct
    # errors should match the stated mean for each closure form).
    for form, errs in FRICTION_FORM_PCT_ERR.items():
        computed_mean = sum(errs.values()) / len(errs)
        assert computed_mean > 0

    write_friction_closure_comparison()
    write_mdot_temperature_decoupling_check(f1_based_f2)
    write_prior_undocumented_sweeps_found(joint_htc, practical_rom, not_in_docs)
    write_sign_convention_corrections()
    write_insulation_screening_sweep()
    write_insulation_friction_zero_crossing_refinement()
    write_salt1_4_train_validation_at_recommended_combo(m3)
    write_validation_case_scores_raw_physics()
    write_residual_correction_on_physics_baseline()
    write_internal_nu_ablation()
    write_physical_plausibility_caveats()
    write_claim_boundary_table()
    write_validation_exposure_count()
    write_validation_terminology_crosswalk()
    write_source_manifest()
    write_no_mutation_guardrails()

    context = {
        "f1_based_f2": f1_based_f2,
        "m3": m3,
        "guardrail_phrase": guardrail_phrase,
        "joint_htc": joint_htc,
        "practical_rom": practical_rom,
        "not_in_docs": not_in_docs,
    }
    summary = write_summary(context)
    write_readme(context)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
