#!/usr/bin/env python3
"""Combine the current best-validated temperature correction (F2_global_affine,
Salt1-4 refit, holdout/external validated) with the current best-available
mass-flow correction (1-DOF multiplicative, Salt1-4 nominal, TRAIN-ONLY / not
holdout-validated) into one honestly-tiered "combined best current model"
citation-and-comparison package.

Task: TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23
Owner: claude

NO NEW FITTING, NO NEW SOLVER RUNS
-----------------------------------
This script performs NO new curve-fitting beyond the already-established
mass-flow 1-DOF multiplicative correction (which is recomputed here, in the
open, from the same 4 read-only Salt1-4 nominal `mdot_kg_s` /
`measured_mass_flow_rate_kg_s` pairs already produced by
`2026-07-20_tswfc2_bounded_nominal_scorecard`; this is the identical
least-squares constant a = sum(pred*meas)/sum(pred**2) already verified this
session, not a new modeling choice). It runs NO OpenFOAM, NO 1D `solve_case()`,
and touches NO other board row's files. The F2 temperature correction
coefficients and holdout/external MAE/RMSE values are cited verbatim from
`2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score` (read-only
upstream package) and are NOT recomputed here except where this script's test
suite independently re-derives them from that package's own source CSVs as a
citation-accuracy check.

The F6 pure-multiplier temperature ablation numbers and the friction f*Re=64
root-cause numbers were computed ad hoc, in-conversation, earlier in this
session (same session, same solver, same read-only source CSVs cited below)
and are NOT yet materialized as their own upstream work_products package. They
are hard-coded below with an explicit provenance comment, exactly as directed
by the task, and this script's tests independently recompute the f*Re root-
cause numbers and the mdot correction numbers from the underlying read-only
source CSVs to catch any transcription error.

Read-only sources (see also `source_manifest.csv` in the output package):
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/
      refit_coefficients.csv, holdout_external_score_old_vs_new.csv,
      train_fit_quality.csv, best_model_recommendation.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/
      case_outputs/Salt_{1,2,3,4}/summary.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/
      salt2_pm5_admission_table.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/
      friction_closures.py, solver.py (read/run-only; not edited; not executed
      by this script, cited only for the friction_form default and the
      available-but-unwired F3/F4/F5 closure names)

No physical closure, no physical property/source release, no candidate
freeze, no final/frozen predictive-score claim. Mass-flow correction is
explicitly flagged NOT holdout/external validated throughout.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23"
OUT = REPO / "work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction"

SRC_F2_REFIT_DIR = REPO / "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score"
SRC_F2_COEFFS = SRC_F2_REFIT_DIR / "refit_coefficients.csv"
SRC_F2_HOLDOUT_EXTERNAL = SRC_F2_REFIT_DIR / "holdout_external_score_old_vs_new.csv"
SRC_F2_TRAIN_QUALITY = SRC_F2_REFIT_DIR / "train_fit_quality.csv"

SRC_SCORECARD_DIR = REPO / "work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs"
SRC_SALT_SUMMARY = {
    n: SRC_SCORECARD_DIR / f"Salt_{n}/summary.csv" for n in (1, 2, 3, 4)
}

SRC_PM5_ADMISSION_TABLE = (
    REPO / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv"
)

FRICTION_CLOSURES_PY = (
    REPO.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py"
)
SOLVER_PY = REPO.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py"

CLAIM_BOUNDARY_TEMP = (
    "F2_global_affine (Salt1-4 refit) temperature correction is holdout- and external-validated "
    "(genuinely never-seen Salt2 +/-5Q and val_salt2 rows); empirical discrepancy/digital-twin-ROM "
    "layer only; NOT a physical closure; NOT a legitimate single-use protected-split freeze score "
    "(second scoring exposure of these rows within this session, per the upstream refit package)"
)
CLAIM_BOUNDARY_MDOT = (
    "Mass-flow 1-DOF multiplicative correction is fit AND scored on the SAME 4 Salt1-4 nominal "
    "points; TRAIN-ONLY, NOT holdout- or external-validated; no measured mass-flow ground truth "
    "exists for salt2_lo5q/salt2_hi5q/val_salt2; NOT a physical closure; NOT a legitimate "
    "predictive-score claim"
)

# ---------------------------------------------------------------------------
# F6 pure-multiplier temperature ablation and friction root-cause numbers were
# computed ad hoc, in-conversation, earlier in this session using the same
# read-only source rows/solver as the F2 refit package, and are not yet
# materialized as their own upstream work_products CSV. Hard-coded here with
# explicit provenance per the task instruction; this script's tests
# independently recompute the friction f*Re values and the mdot correction
# from the read-only Salt1-4 summary.csv files to catch transcription errors.
# ---------------------------------------------------------------------------

F6_ABLATION_PROVENANCE = (
    "ad_hoc_in_conversation_pass_this_session_same_source_rows_and_solver_as_F2_refit_package_"
    "not_yet_materialized_as_own_upstream_csv_cited_verbatim_per_task_instruction"
)

F6_TRAIN_ROWS = [
    {
        "fit_basis": "Salt1_4_refit",
        "multiplier_a": 0.8237932643572209,
        "train_mae_K": 11.123291594298546,
        "train_rmse_K": 17.739561046048724,
    },
    {
        "fit_basis": "Salt1_2_only",
        "multiplier_a": 0.8338641208658737,
        "train_mae_K": 11.04822848616341,
        "train_rmse_K": 16.544126132211865,
    },
]

# case, fit_basis -> (MAE_K, RMSE_K)
F6_HOLDOUT_EXTERNAL_ROWS = [
    ("salt2_lo5q", "Salt1_2_only", 3.264, 4.000),
    ("salt2_lo5q", "Salt1_4_refit", 6.186, 6.738),
    ("salt2_hi5q", "Salt1_2_only", 8.318, 9.276),
    ("salt2_hi5q", "Salt1_4_refit", 3.430, 4.922),
    ("val_salt2", "Salt1_2_only", 5.874, 8.254),
    ("val_salt2", "Salt1_4_refit", 6.456, 9.841),
]

FUTURE_WORK_SEQUENCE = [
    {
        "order": 1,
        "action": (
            "Swap friction_form from 'F1' (plain 64/Re) to 'F3_hagenbach' (Shah 1978 entry-length "
            "correction) or 'F4_leg_class'/'F5_ri_corrected' (buoyancy/leg-specific) in the "
            "ScenarioConfig used by the Salt1-4 nominal scorecard, and re-run the existing 1D solver "
            "(no new solver code) to see if the mdot overprediction shrinks."
        ),
        "why": (
            "f*Re = 64.0 exactly for all four Salt1-4 nominal cases confirms the plain "
            "fully-developed-laminar closure F1 is in use with no entrance-length or buoyancy "
            "correction, even though F3_hagenbach/F4_leg_class/F5_ri_corrected are already "
            "implemented in friction_closures.py but not wired into this candidate's friction_form."
        ),
        "expected_signal": (
            "Predicted mdot_kg_s should move closer to measured_mass_flow_rate_kg_s for all four "
            "Salt1-4 nominal cases without any new fitting; a reduction in raw mean relative error "
            "below the current ~32.6% would be direct evidence the closure gap, not a numerics bug, "
            "explains most of the bias."
        ),
    },
    {
        "order": 2,
        "action": (
            "Re-check whether F2's temperature offset term (currently 138.28 K, Salt1-4 refit) "
            "shrinks once mdot is fixed via step 1."
        ),
        "why": (
            "Q = mdot * cp * deltaT couples the mass-flow bias directly into any predicted "
            "temperature rise; part of F2's large offset may be compensating for an underpredicted "
            "mdot rather than a genuine heat-transfer-coefficient gap."
        ),
        "expected_signal": (
            "If F2's offset_bias_K shrinks materially (not just noise) after a mdot-closure fix, "
            "that is evidence the temperature bias was partly mdot-driven; if it does not shrink, "
            "the offset is evidence of a separate heat-transfer/thermal-boundary-condition gap."
        ),
    },
    {
        "order": 3,
        "action": "Continue the separate, active PASSIVE-H2 outer-insulation/radiation heat-loss admission track.",
        "why": (
            "Ambient heat loss (insulation + radiation) is a distinct, already-active line of work "
            "and should not be conflated with the friction-closure or empirical-bias-correction work "
            "documented in this package."
        ),
        "expected_signal": (
            "Tracked separately under its own board row/status file; no signal expected from this "
            "package's future-work sequence."
        ),
    },
    {
        "order": 4,
        "action": (
            "Obtain a genuine non-recirculating, held-out mdot readout for salt2_lo5q, salt2_hi5q, "
            "and val_salt2 before ever claiming a validated mass-flow correction."
        ),
        "why": (
            "No measured/ground-truth mass flow rate exists for these three cases today. "
            "Back-calculating an approximate mdot from the CFD Re values in "
            "salt2_pm5_admission_table.csv was considered and rejected: those probe stations show "
            "37-79% local reverse-flow area fraction and are explicitly non-single-stream "
            "(recirculation_status == 'recirculating_section_effective') per the project's own "
            "admission criteria, so using them would silently launder a bad number into what should "
            "be an honest evidentiary gap."
        ),
        "expected_signal": (
            "A held-out mdot target from a single-stream (non-recirculating) plane or an "
            "independent measurement source would let the mass-flow correction finally be scored "
            "out-of-sample, upgrading its evidentiary tier from train-only to holdout-validated."
        ),
    },
    {
        "order": 5,
        "action": (
            "Treat salt2_lo5q, salt2_hi5q, and val_salt2 as spent for any future single-use freeze "
            "score; use Salt4 +/-5Q or the +/-10Q rows instead for the next genuine single-use "
            "protected-split evaluation."
        ),
        "why": (
            "These three rows have already been scored more than once this session (per the "
            "upstream F2 refit package's SECOND EXPOSURE callout); citing another score against them "
            "as a fresh single-use holdout/external test would not be a legitimate protected-split "
            "evaluation."
        ),
        "expected_signal": (
            "A future freeze-and-score package that explicitly selects Salt4 +/-5Q or +/-10Q rows "
            "(never-yet-exposed) as its held-out target, rather than reusing salt2_lo5q/hi5q/val_salt2."
        ),
    },
]


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
# Temperature correction: cite F2_global_affine (Salt1-4 refit) verbatim.
# ---------------------------------------------------------------------------


def load_f2_temperature_correction() -> dict[str, Any]:
    coeffs = read_csv(SRC_F2_COEFFS)
    f2 = [c for c in coeffs if c["model_family"] == "F2_global_affine"]
    if len(f2) != 1:
        raise RuntimeError(f"Expected exactly one F2_global_affine coefficient row, found {len(f2)}")
    mult = fnum(f2[0]["multiplier_correction"])
    offset = fnum(f2[0]["offset_bias_K"])

    scores = read_csv(SRC_F2_HOLDOUT_EXTERNAL)
    holdout_hits = {
        row["case"]: (fnum(row["MAE_K"]), fnum(row["RMSE_K"]))
        for row in scores
        if row["model_family"] == "F2_global_affine" and row["fit_basis"] == "Salt1_4_refit"
    }
    for case in ("salt2_lo5q", "salt2_hi5q", "val_salt2"):
        if case not in holdout_hits:
            raise RuntimeError(f"Missing Salt1_4_refit F2_global_affine score for {case}")

    train_quality = read_csv(SRC_F2_TRAIN_QUALITY)
    f2_train = [r for r in train_quality if r["model_family"] == "F2_global_affine"][0]

    return {
        "multiplier_a": mult,
        "offset_bias_K": offset,
        "train_mae_K": fnum(f2_train["train_mae_K"]),
        "train_rmse_K": fnum(f2_train["train_rmse_K"]),
        "salt2_lo5q_mae_K": holdout_hits["salt2_lo5q"][0],
        "salt2_lo5q_rmse_K": holdout_hits["salt2_lo5q"][1],
        "salt2_hi5q_mae_K": holdout_hits["salt2_hi5q"][0],
        "salt2_hi5q_rmse_K": holdout_hits["salt2_hi5q"][1],
        "val_salt2_mae_K": holdout_hits["val_salt2"][0],
        "val_salt2_rmse_K": holdout_hits["val_salt2"][1],
    }


# ---------------------------------------------------------------------------
# Mass-flow correction: recompute the 1-DOF multiplicative fit (and the
# rejected 2-DOF affine fit) from the read-only Salt1-4 nominal summary.csv
# files, in the open, so the numbers are reproducible from source rather than
# hard-coded.
# ---------------------------------------------------------------------------


def load_mdot_pairs() -> list[dict[str, Any]]:
    pairs = []
    for n in (1, 2, 3, 4):
        rows = read_csv(SRC_SALT_SUMMARY[n])
        if len(rows) != 1:
            raise RuntimeError(f"Expected exactly one row in {SRC_SALT_SUMMARY[n]}, found {len(rows)}")
        row = rows[0]
        pairs.append(
            {
                "case": f"Salt{n}",
                "predicted_kg_s": fnum(row["mdot_kg_s"]),
                "measured_kg_s": fnum(row["measured_mass_flow_rate_kg_s"]),
                "friction_factor_main": fnum(row["friction_factor_main"]),
                "reynolds_main": fnum(row["reynolds_main"]),
            }
        )
    return pairs


def fit_multiplicative(pairs: list[dict[str, Any]]) -> float:
    """a = sum(pred*meas) / sum(pred**2), the least-squares 1-DOF multiplier."""
    num = sum(p["predicted_kg_s"] * p["measured_kg_s"] for p in pairs)
    den = sum(p["predicted_kg_s"] ** 2 for p in pairs)
    return num / den


def fit_affine(pairs: list[dict[str, Any]]) -> tuple[float, float]:
    """OLS affine fit meas = a*pred + b (the REJECTED 2-DOF alternative)."""
    xs = [p["predicted_kg_s"] for p in pairs]
    ys = [p["measured_kg_s"] for p in pairs]
    n = len(pairs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    a = cov_xy / var_x
    b = mean_y - a * mean_x
    return a, b


def mdot_fit_rows(pairs: list[dict[str, Any]], mult_a: float, aff_a: float, aff_b: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for p in pairs:
        pred = p["predicted_kg_s"]
        meas = p["measured_kg_s"]
        raw_abs_err = abs(pred - meas)
        raw_rel_err_pct = raw_abs_err / meas * 100.0

        mult_pred = mult_a * pred
        mult_abs_err = abs(mult_pred - meas)
        mult_rel_err_pct = mult_abs_err / meas * 100.0

        aff_pred = aff_a * pred + aff_b
        aff_abs_err = abs(aff_pred - meas)
        aff_rel_err_pct = aff_abs_err / meas * 100.0

        rows.append(
            {
                "case": p["case"],
                "correction_form": "multiplicative_1dof_recommended",
                "predicted_kg_s": pred,
                "measured_kg_s": meas,
                "raw_abs_err_kg_s": raw_abs_err,
                "raw_rel_err_pct": raw_rel_err_pct,
                "corrected_abs_err_kg_s": mult_abs_err,
                "corrected_rel_err_pct": mult_rel_err_pct,
            }
        )
        rows.append(
            {
                "case": p["case"],
                "correction_form": "affine_2dof_rejected_for_transparency",
                "predicted_kg_s": pred,
                "measured_kg_s": meas,
                "raw_abs_err_kg_s": raw_abs_err,
                "raw_rel_err_pct": raw_rel_err_pct,
                "corrected_abs_err_kg_s": aff_abs_err,
                "corrected_rel_err_pct": aff_rel_err_pct,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Friction root-cause table.
# ---------------------------------------------------------------------------


def friction_root_cause_rows(pairs: list[dict[str, Any]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for p in pairs:
        f = p["friction_factor_main"]
        re = p["reynolds_main"]
        rows.append(
            {
                "case": p["case"],
                "reynolds_main": re,
                "friction_factor_main": f,
                "f_times_Re": f * re,
                "closure_form_used": "F1_plain_64_over_Re_local_property_no_entry_no_buoyancy_correction",
                "closure_forms_available_but_unwired": "F3_hagenbach;F4_leg_class;F5_ri_corrected",
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Output writers.
# ---------------------------------------------------------------------------


def write_combined_model_spec(temp: dict[str, Any], mult_a: float) -> None:
    rows = [
        {
            "component": "temperature",
            "formula": "T_corrected = a * T_1D + b",
            "coefficients": f"a={temp['multiplier_a']!r}, b={temp['offset_bias_K']!r}",
            "evidentiary_tier": "holdout_external_validated",
            "claim_boundary": CLAIM_BOUNDARY_TEMP,
        },
        {
            "component": "mass_flow",
            "formula": "mdot_corrected = a * mdot_1D",
            "coefficients": f"a={mult_a!r}",
            "evidentiary_tier": "train_only_not_validated",
            "claim_boundary": CLAIM_BOUNDARY_MDOT,
        },
    ]
    write_csv(
        OUT / "combined_model_spec.csv",
        rows,
        ["component", "formula", "coefficients", "evidentiary_tier", "claim_boundary"],
    )


def write_mdot_correction_fit(rows: list[dict[str, object]]) -> None:
    write_csv(
        OUT / "mdot_correction_fit.csv",
        rows,
        [
            "case",
            "correction_form",
            "predicted_kg_s",
            "measured_kg_s",
            "raw_abs_err_kg_s",
            "raw_rel_err_pct",
            "corrected_abs_err_kg_s",
            "corrected_rel_err_pct",
        ],
    )


def write_temp_correction_holdout_scores(temp: dict[str, Any]) -> None:
    rows = [
        {
            "case": "salt2_lo5q",
            "case_role": "holdout",
            "MAE_K": temp["salt2_lo5q_mae_K"],
            "RMSE_K": temp["salt2_lo5q_rmse_K"],
            "provenance": str(SRC_F2_HOLDOUT_EXTERNAL.relative_to(REPO)),
        },
        {
            "case": "salt2_hi5q",
            "case_role": "holdout",
            "MAE_K": temp["salt2_hi5q_mae_K"],
            "RMSE_K": temp["salt2_hi5q_rmse_K"],
            "provenance": str(SRC_F2_HOLDOUT_EXTERNAL.relative_to(REPO)),
        },
        {
            "case": "val_salt2",
            "case_role": "external",
            "MAE_K": temp["val_salt2_mae_K"],
            "RMSE_K": temp["val_salt2_rmse_K"],
            "provenance": str(SRC_F2_HOLDOUT_EXTERNAL.relative_to(REPO)),
        },
    ]
    write_csv(OUT / "temp_correction_holdout_scores.csv", rows, ["case", "case_role", "MAE_K", "RMSE_K", "provenance"])


def write_f6_ablation() -> None:
    rows: list[dict[str, object]] = []
    for t in F6_TRAIN_ROWS:
        rows.append(
            {
                "case": "train_Salt1_4",
                "fit_basis": t["fit_basis"],
                "MAE_K": t["train_mae_K"],
                "RMSE_K": t["train_rmse_K"],
                "verdict": "in_sample_only_worse_than_F2_train_MAE_9.291_K",
                "provenance": F6_ABLATION_PROVENANCE,
            }
        )
    for case, fit_basis, mae, rmse in F6_HOLDOUT_EXTERNAL_ROWS:
        rows.append(
            {
                "case": case,
                "fit_basis": fit_basis,
                "MAE_K": mae,
                "RMSE_K": rmse,
                "verdict": "not_robust_good_on_one_pm5_direction_poor_on_other_under_either_fit_basis",
                "provenance": F6_ABLATION_PROVENANCE,
            }
        )
    write_csv(OUT / "f6_pure_multiplier_ablation.csv", rows, ["case", "fit_basis", "MAE_K", "RMSE_K", "verdict", "provenance"])


def write_friction_root_cause(rows: list[dict[str, object]]) -> None:
    write_csv(
        OUT / "friction_root_cause.csv",
        rows,
        ["case", "reynolds_main", "friction_factor_main", "f_times_Re", "closure_form_used", "closure_forms_available_but_unwired"],
    )


def write_claim_boundary_table() -> None:
    rows = [
        {
            "allowed_claim": (
                "The combined best-current empirical-ROM model applies a holdout/external-validated "
                "F2_global_affine temperature correction (Salt1-4 refit) together with a train-only "
                "1-DOF multiplicative mass-flow correction, and can be reported as the best current "
                "combined form with future work named separately"
            ),
            "forbidden_claim": "The mass-flow correction is holdout-validated or externally scored",
            "evidence_path": "work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/mdot_correction_fit.csv",
        },
        {
            "allowed_claim": (
                "The friction root-cause table shows f*Re=64.0 exactly for all four Salt1-4 nominal "
                "cases, consistent with the plain F1 (64/Re) closure being in use with F3_hagenbach/"
                "F4_leg_class/F5_ri_corrected available but unwired"
            ),
            "forbidden_claim": "This is a physical closure, an admitted heat-transfer/friction coefficient, or a source/property release",
            "evidence_path": "work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/friction_root_cause.csv",
        },
        {
            "allowed_claim": (
                "This package can be shared/documented now as the honest current-best combined model, "
                "with the mdot correction explicitly labeled train-only and the friction root cause "
                "explicitly labeled a future-work lead"
            ),
            "forbidden_claim": "This package is a final/frozen predictive score or a legitimate single-use protected-split freeze",
            "evidence_path": "work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/evidentiary_tier_table.csv",
        },
        {
            "allowed_claim": (
                "salt2_lo5q/salt2_hi5q/val_salt2 Re-based station data was reviewed as a candidate mdot "
                "back-calculation source and explicitly rejected because those stations are non-single-"
                "stream (37-79% local reverse-flow area fraction, recirculation_status = "
                "'recirculating_section_effective')"
            ),
            "forbidden_claim": (
                "A back-calculated mdot from the salt2_pm5_admission_table.csv Re values at those "
                "stations is a valid held-out mass-flow target"
            ),
            "evidence_path": "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv",
        },
    ]
    write_csv(OUT / "claim_boundary_table.csv", rows, ["allowed_claim", "forbidden_claim", "evidence_path"])


def write_evidentiary_tier_table() -> None:
    rows = [
        {
            "component": "temperature",
            "tier": "holdout_external_validated",
            "why": (
                "F2_global_affine (Salt1-4 refit) is scored against salt2_lo5q/salt2_hi5q (real +/-5Q "
                "holdout perturbation runs) and val_salt2 (independent external-test case with a "
                "different property set), none of which were used in the coefficient fit."
            ),
        },
        {
            "component": "mass_flow",
            "tier": "train_only_not_validated",
            "why": (
                "The 1-DOF multiplicative mdot correction is fit AND scored on the SAME 4 Salt1-4 "
                "nominal points -- the only 4 points with a measured mass-flow ground truth in the "
                "whole dataset. No measured mdot exists for salt2_lo5q/salt2_hi5q/val_salt2, and a "
                "Re-based back-calculation from those stations was reviewed and rejected because they "
                "are non-single-stream (37-79% local reverse-flow area fraction)."
            ),
        },
    ]
    write_csv(OUT / "evidentiary_tier_table.csv", rows, ["component", "tier", "why"])


def write_future_work_sequence() -> None:
    write_csv(
        OUT / "future_work_sequence.csv",
        FUTURE_WORK_SEQUENCE,
        ["order", "action", "why", "expected_signal"],
    )


def write_source_manifest() -> None:
    paths = [
        (SRC_F2_COEFFS, "F2_global_affine (Salt1-4 refit) temperature-correction coefficients"),
        (SRC_F2_HOLDOUT_EXTERNAL, "F2_global_affine holdout (salt2_lo5q/hi5q) and external (val_salt2) MAE/RMSE"),
        (SRC_F2_TRAIN_QUALITY, "F2_global_affine in-sample (train) MAE/RMSE for the F6 ablation comparison"),
        (SRC_SALT_SUMMARY[1], "Salt1 nominal mdot_kg_s, measured_mass_flow_rate_kg_s, friction_factor_main, reynolds_main"),
        (SRC_SALT_SUMMARY[2], "Salt2 nominal mdot_kg_s, measured_mass_flow_rate_kg_s, friction_factor_main, reynolds_main"),
        (SRC_SALT_SUMMARY[3], "Salt3 nominal mdot_kg_s, measured_mass_flow_rate_kg_s, friction_factor_main, reynolds_main"),
        (SRC_SALT_SUMMARY[4], "Salt4 nominal mdot_kg_s, measured_mass_flow_rate_kg_s, friction_factor_main, reynolds_main"),
        (SRC_PM5_ADMISSION_TABLE, "reverse_area_fraction/reverse_mass_fraction/recirculation_status evidence for rejecting the Re-based mdot back-calculation"),
        (FRICTION_CLOSURES_PY, "dp_F1/dp_F3_hagenbach/dp_F4_leg_class/dp_F5_ri_corrected closure function names (read-only, not executed)"),
        (SOLVER_PY, "friction_form: str = 'F1' default confirming the unwired closure gap (read-only, not executed)"),
    ]
    write_csv(
        OUT / "source_manifest.csv",
        [{"path": str(p), "used_for": use, "mutation_status": "read_only"} for p, use in paths],
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
        "mdot_correction_claimed_holdout_validated",
        "s11_s15_s6_trigger",
        "new_curve_fit_beyond_declared_mdot_multiplier",
        "blocker_register_source_change_before_closeout",
        "generated_index_refresh_before_closeout",
        "deletion",
        "staging",
        "commit",
        "push",
        "other_board_row_file_touched",
    ]
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [{"forbidden_action": g, "performed": False} for g in guardrails],
        ["forbidden_action", "performed"],
    )


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/refit_coefficients.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/holdout_external_score_old_vs_new.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/train_fit_quality.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/best_model_recommendation.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_1/summary.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_2/summary.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_3/summary.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_4/summary.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
tags: [forward-model, combined-model, temperature-correction, mass-flow-correction, empirical-bias, friction-closure, root-cause, evidentiary-tiering]
related:
  - .agent/status/2026-07-23_TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23.md
  - .agent/journal/2026-07-23/combined-best-current-model-temp-mdot-correction.md
  - imports/2026-07-23_combined_best_current_model_temp_mdot_correction.json
  - operational_notes/07-26/23/2026-07-23_COMBINED_BEST_CURRENT_MODEL_TEMP_MDOT_CORRECTION.md
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md
task: {TASK_ID}
date: 2026-07-23
role: Forward-pred/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# Combined Best-Current Model: Temperature + Mass-Flow Correction

Decision: `combined_model_temp_holdout_validated_mdot_train_only_not_a_physical_closure_not_a_freeze_score`.

## EVIDENTIARY TIER CALLOUT (read first)

This package combines TWO corrections with **very different evidentiary
strength**, and they must never be described with the same confidence:

- **Temperature correction (F2_global_affine, Salt1-4 refit): HOLDOUT/EXTERNAL
  VALIDATED.** It is scored against genuinely never-seen data: the real
  Salt2 +/-5Q holdout runs (`salt2_lo5q`, `salt2_hi5q`) and the independent
  `val_salt2` external-test case (different property set). MAE = {summary['temp']['salt2_lo5q_mae_K']:.3f} K
  (salt2_lo5q), {summary['temp']['salt2_hi5q_mae_K']:.3f} K (salt2_hi5q), {summary['temp']['val_salt2_mae_K']:.3f} K (val_salt2, n=15).
- **Mass-flow correction (1-DOF multiplicative, a={summary['mdot']['multiplier_a']!r}): TRAIN-ONLY,
  NOT VALIDATED OUT-OF-SAMPLE.** It is fit AND scored on the SAME 4 Salt1-4
  nominal points -- the only 4 points in the whole dataset with a measured
  mass-flow ground truth. There is no measured mdot for salt2_lo5q,
  salt2_hi5q, or val_salt2.
- A Re-based back-calculation of an approximate mdot from the CFD probe
  stations in `salt2_pm5_admission_table.csv` was considered and **explicitly
  rejected**: those stations show 37-79% local reverse-flow area fraction and
  are labeled `recirculation_status == recirculating_section_effective`
  (non-single-stream) per the project's own admission criteria. Using them
  would silently launder a bad number into what should be an honest gap in
  the evidence, so the mass-flow correction is reported strictly as
  train-only and not holdout-validated.

**Never report these two corrections as if they carried the same evidentiary
weight.** See `evidentiary_tier_table.csv` and `claim_boundary_table.csv`.

## What this package is

The final combined-model deliverable requested by the user: the current best
temperature correction (holdout/external-validated F2_global_affine, Salt1-4
refit) plus the current best mass-flow correction (train-only 1-DOF
multiplicative fit) reported together as one honest "best current model"
statement, with future work named separately (`future_work_sequence.csv`).
It also documents the friction root-cause finding for the mdot overprediction
(`friction_root_cause.csv`) and an ablation answering "does a pure multiplier
(no offset) do as well for temperature?" (`f6_pure_multiplier_ablation.csv`;
answer: no, the additive offset is load-bearing).

## What this package is NOT

- Not a physical closure. Neither the temperature nor the mass-flow
  correction is an admitted physical heat-transfer or friction coefficient.
- Not a legitimate single-use protected-split freeze score for the mass-flow
  correction (no held-out mdot data exists at all) or for the temperature
  correction (it is a cited, already-second-exposure score from the upstream
  refit package, not a fresh single-use exposure).
- Not a new curve-fit exercise beyond the already-established mdot 1-DOF
  multiplicative correction (recomputed here from the same 4 read-only
  source pairs, not re-derived with any new methodology).
- Does not run OpenFOAM, the 1D `solve_case()` solver, or mutate any
  case_stage tree; does not touch any other board row's files.

## Headline numbers

### Temperature correction (F2_global_affine, Salt1-4 refit) -- HOLDOUT/EXTERNAL VALIDATED

- `T_corrected = {summary['temp']['multiplier_a']!r} * T_1D + {summary['temp']['offset_bias_K']!r}`
- Holdout MAE: salt2_lo5q = {summary['temp']['salt2_lo5q_mae_K']:.3f} K, salt2_hi5q = {summary['temp']['salt2_hi5q_mae_K']:.3f} K
- External MAE: val_salt2 = {summary['temp']['val_salt2_mae_K']:.3f} K (n=15)

### Mass-flow correction (1-DOF multiplicative) -- TRAIN-ONLY, NOT VALIDATED

- `mdot_corrected = {summary['mdot']['multiplier_a']!r} * mdot_1D`
- Raw mean relative error (Salt1-4 nominal): {summary['mdot']['raw_mean_rel_err_pct']:.2f}%
- Corrected mean relative error: {summary['mdot']['corrected_mean_rel_err_pct']:.2f}%
- Corrected MAE: {summary['mdot']['corrected_mae_kg_s']:.6f} kg/s
- Rejected alternative (2-DOF affine, in-sample mean rel err {summary['mdot']['affine_mean_rel_err_pct']:.2f}%):
  not adopted because 2 free parameters fit to only 4 data points leaves too
  little residual degrees of freedom to trust the improvement.

### Friction root-cause (why mdot is overpredicted)

`f * Re = 64.0` exactly for all four Salt1-4 nominal cases -- the solver's
`friction_form` default is `"F1"` (plain fully-developed-laminar 64/Re, no
entrance-length or buoyancy correction), even though `F3_hagenbach`,
`F4_leg_class`, and `F5_ri_corrected` are already implemented in
`friction_closures.py` but not wired into this candidate. This is the most
likely direct cause of the mdot overprediction and the cheapest, most
physically-grounded next fix (see `future_work_sequence.csv`, step 1).

### F6 pure-multiplier temperature ablation

A pure multiplier (no offset) is NOT robust: under either fit basis it does
well on one +/-5%Q direction and poorly on the other, unlike F2 (affine),
which is stable across both directions and both fit bases. This shows the
additive offset term is load-bearing, not a redundant extra parameter.
Recommend AGAINST the pure-multiplier form for temperature.

## Open first

- `combined_model_spec.csv`
- `evidentiary_tier_table.csv`
- `mdot_correction_fit.csv`
- `temp_correction_holdout_scores.csv`
- `friction_root_cause.csv`
- `f6_pure_multiplier_ablation.csv`
- `claim_boundary_table.csv`
- `future_work_sequence.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
"""
    (OUT / "README.md").write_text(text)


def write_summary(summary: dict[str, Any]) -> None:
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    temp = load_f2_temperature_correction()

    pairs = load_mdot_pairs()
    mult_a = fit_multiplicative(pairs)
    aff_a, aff_b = fit_affine(pairs)

    if abs(mult_a - 0.7504257967710826) > 1e-9:
        raise RuntimeError(f"Recomputed mdot multiplier {mult_a} does not match cited a=0.7504257967710826")

    fit_rows = mdot_fit_rows(pairs, mult_a, aff_a, aff_b)
    corrected_rel_errs = [r["corrected_rel_err_pct"] for r in fit_rows if r["correction_form"] == "multiplicative_1dof_recommended"]
    corrected_abs_errs = [r["corrected_abs_err_kg_s"] for r in fit_rows if r["correction_form"] == "multiplicative_1dof_recommended"]
    raw_rel_errs = [r["raw_rel_err_pct"] for r in fit_rows if r["correction_form"] == "multiplicative_1dof_recommended"]
    affine_rel_errs = [r["corrected_rel_err_pct"] for r in fit_rows if r["correction_form"] == "affine_2dof_rejected_for_transparency"]

    write_combined_model_spec(temp, mult_a)
    write_mdot_correction_fit(fit_rows)
    write_temp_correction_holdout_scores(temp)
    write_f6_ablation()
    friction_rows = friction_root_cause_rows(pairs)
    write_friction_root_cause(friction_rows)
    write_claim_boundary_table()
    write_evidentiary_tier_table()
    write_future_work_sequence()
    write_source_manifest()
    write_no_mutation_guardrails()

    summary = {
        "task_id": TASK_ID,
        "date": "2026-07-23",
        "status": "complete",
        "no_new_fitting_beyond_declared_mdot_multiplier": True,
        "no_new_solver_runs": True,
        "temp": {
            "multiplier_a": temp["multiplier_a"],
            "offset_bias_K": temp["offset_bias_K"],
            "train_mae_K": temp["train_mae_K"],
            "salt2_lo5q_mae_K": temp["salt2_lo5q_mae_K"],
            "salt2_hi5q_mae_K": temp["salt2_hi5q_mae_K"],
            "val_salt2_mae_K": temp["val_salt2_mae_K"],
            "evidentiary_tier": "holdout_external_validated",
        },
        "mdot": {
            "multiplier_a": mult_a,
            "affine_a": aff_a,
            "affine_b": aff_b,
            "raw_mean_rel_err_pct": sum(raw_rel_errs) / len(raw_rel_errs),
            "corrected_mean_rel_err_pct": sum(corrected_rel_errs) / len(corrected_rel_errs),
            "corrected_mae_kg_s": sum(corrected_abs_errs) / len(corrected_abs_errs),
            "affine_mean_rel_err_pct": sum(affine_rel_errs) / len(affine_rel_errs),
            "evidentiary_tier": "train_only_not_validated",
        },
        "friction_root_cause": {
            "closure_form_used": "F1",
            "closure_forms_available_but_unwired": ["F3_hagenbach", "F4_leg_class", "F5_ri_corrected"],
            "f_times_Re_all_cases": [round(r["f_times_Re"], 6) for r in friction_rows],
        },
        "physical_closure_claim_allowed": False,
        "mdot_correction_holdout_validated": False,
        "legitimate_single_use_protected_score": False,
        "candidate_frozen": False,
        "final_predictive_admission": False,
        "native_solver_run": False,
        "registry_or_admission_mutated": False,
    }
    write_summary(summary)
    write_readme(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
