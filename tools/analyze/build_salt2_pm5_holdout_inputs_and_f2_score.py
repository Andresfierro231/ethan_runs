#!/usr/bin/env python3.11
"""All-4 CFD-referenced affine refit + Salt2 +/-5Q holdout / val_salt2 external score.

Tasks:
  TODO-SALT2-PM5-HOLDOUT-INPUTS-AND-F2-SCORE-2026-07-23
  TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23
Owner: claude

Context / definition (user steer 2026-07-23)
--------------------------------------------
The thesis main body is purely computational: the reference truth is the CFD
sensor value `reference_k` (TP -> core temperature `t_core_k`; TW -> wall
temperature `t_wall_area_avg_k`), NOT the experimental thermocouple. The published
F2 was fit 1D->experiment, so it is the wrong target here. This builder refits the
same affine FORM to CFD on ALL FOUR Salt1-4 nominal train cases, freezes it, and
blind-scores it on the Salt2 +/-5Q CFD holdout and the val_salt2 CFD external
target.

Model form (empirical discrepancy ROM, NOT a physical closure):
    T_corrected = a * T_1D + b        (2 DOF, global affine)

Provenance of inputs:
  - T_1D nominal: the TSWFC2 bounded nominal scorecard validation tables
    (predicted_K), Salt 1-4.
  - T_CFD nominal: reference_k rolled up from the OF13-reconstructed + sampled
    boundary_layer_landmark_summary.csv for each nominal case (this session).
  - T_1D holdout: frozen_1d_predictions_salt2_pm5.csv (this session; heater power
    +/-5%).
  - T_CFD holdout: reference_k rolled up from the Salt2 +/-5Q extractions
    (this session).
  - val_salt2 T_CFD: existing frozen-state cfd_sensor_reference.csv (Salt 2 Val);
    val_salt2 T_1D reuses the Salt 2 nominal 1D prediction (same operating point).

Caveats enforced:
  - Empirical discrepancy only; no physical-closure claim; a,b are not admitted
    HTCs.
  - Repeated-exposure caveat: the Salt2 +/-5Q / val_salt2 rows have been used more
    than once this session for model comparison, so this is a documented diagnostic
    refit, not a pristine single-use protected-split freeze score.
"""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

REPO = Path("/scratch/09748/andresfierro231/projects_scratch/ethan_runs")
WP = REPO / "work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score"
CFD_EXTRACT = WP / "cfd_extraction"
OUT = WP  # emit alongside inputs
NOMINAL_1D_DIR = REPO / "work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs"
VAL_SALT2_CFD = REPO / "reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation/cfd_sensor_reference.csv"
PM5_1D = WP / "frozen_1d_predictions_salt2_pm5.csv"
VAL_SALT2_1D = WP / "frozen_1d_prediction_valsalt2.csv"

# Original published F2 (Salt1/2 experiment-fit) for old-vs-new comparison.
ORIG_F2_A = 0.3729829182408737
ORIG_F2_B = 246.55192842685844

NOMINAL_CASES = [
    ("salt_1", "Salt_1", CFD_EXTRACT / "nominal_salt1_jin"),
    ("salt_2", "Salt_2", CFD_EXTRACT / "nominal_salt2_jin"),
    ("salt_3", "Salt_3", CFD_EXTRACT / "nominal_salt3_jin"),
    ("salt_4", "Salt_4", CFD_EXTRACT / "nominal_salt4_jin"),
]
SCORE_EXCLUDED = {"TP2", "TW10"}  # matches the nominal scorecard exclusions


def _read(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _f(v):
    try:
        x = float(v)
        return x if x == x else None  # drop nan
    except (TypeError, ValueError):
        return None


def rollup_cfd_reference(landmark_csv: Path) -> dict:
    """sensor -> reference_k (TP: mean t_core_k; TW: mean t_wall_area_avg_k)."""
    rows = _read(landmark_csv)
    grouped: dict[str, list[dict]] = {}
    for r in rows:
        lab = str(r.get("landmark_label", "")).strip()
        if lab[:2] in ("TP", "TW") and lab[2:].isdigit():
            grouped.setdefault(lab, []).append(r)
    ref = {}
    for lab, payload in grouped.items():
        field = "t_core_k" if lab.startswith("TP") else "t_wall_area_avg_k"
        vals = [_f(r.get(field)) for r in payload]
        vals = [v for v in vals if v is not None]
        if vals:
            ref[lab] = sum(vals) / len(vals)
    return ref


def load_1d(validation_table: Path) -> dict:
    ref = {}
    for r in _read(validation_table):
        v = _f(r.get("predicted_K"))
        if v is not None:
            ref[str(r["sensor"]).strip()] = v
    return ref


VAL_SALT2_FRESH_LM = CFD_EXTRACT / "val_salt2" / "raw_extraction" / "boundary_layer_landmark_summary.csv"


def load_valsalt2_cfd() -> tuple[dict, str]:
    """Prefer MY method-consistent 2026-07-23 extraction; fall back to 2026-06-23."""
    if VAL_SALT2_FRESH_LM.exists():
        return rollup_cfd_reference(VAL_SALT2_FRESH_LM), "2026-07-23_same_pipeline_as_nominal_and_pm5"
    ref = {}
    for r in _read(VAL_SALT2_CFD):
        v = _f(r.get("reference_k"))
        if v is not None:
            ref[str(r["sensor"]).strip()] = v
    return ref, "2026-06-23_frozen_state_prior_extraction_vintage_caveat"


def pairs_for_case(pred: dict, cfd: dict) -> list[tuple[str, float, float]]:
    out = []
    for s in sorted(set(pred) & set(cfd)):
        if s in SCORE_EXCLUDED:
            continue
        out.append((s, pred[s], cfd[s]))
    return out


def fit_affine(pairs: list[tuple[str, float, float]]) -> tuple[float, float]:
    """OLS T_CFD = a*T_1D + b."""
    n = len(pairs)
    xs = [p[1] for p in pairs]
    ys = [p[2] for p in pairs]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    a = sxy / sxx
    b = my - a * mx
    return a, b


def score(pairs, a, b) -> dict:
    if not pairs:
        return {"n": 0}
    corr_err = [(a * x + b) - y for _, x, y in pairs]
    raw_err = [x - y for _, x, y in pairs]
    n = len(pairs)
    rmse = lambda e: (sum(v * v for v in e) / n) ** 0.5
    mae = lambda e: sum(abs(v) for v in e) / n
    return {
        "n": n,
        "corrected_rmse_K": rmse(corr_err),
        "corrected_mae_K": mae(corr_err),
        "raw_rmse_K": rmse(raw_err),
        "raw_mae_K": mae(raw_err),
    }


def build() -> dict:
    # --- nominal train: pair 1D vs CFD across all 4 cases ---
    nominal_pairs = []
    nominal_coverage = []
    for cid, nom_name, extract_dir in NOMINAL_CASES:
        vt = NOMINAL_1D_DIR / nom_name / "validation_table.csv"
        lm = extract_dir / "raw_extraction" / "boundary_layer_landmark_summary.csv"
        if not (vt.exists() and lm.exists()):
            nominal_coverage.append({"case": cid, "status": "missing_input",
                                     "vt": vt.exists(), "cfd": lm.exists()})
            continue
        pred = load_1d(vt)
        cfd = rollup_cfd_reference(lm)
        cp = pairs_for_case(pred, cfd)
        nominal_pairs.extend(cp)
        nominal_coverage.append({"case": cid, "status": "ok", "paired_sensors": len(cp)})

    a_new, b_new = fit_affine(nominal_pairs)

    # --- holdout: Salt2 +/-5Q ---
    pm5_1d_rows = _read(PM5_1D)
    pm5_1d = {}
    for r in pm5_1d_rows:
        pm5_1d.setdefault(r["case_id"], {})[str(r["sensor"]).strip()] = _f(r["predicted_K"])
    holdout_scores = {}
    holdout_pairs_all = []
    for case, extract in [("salt2_lo5q", CFD_EXTRACT / "salt2_jin_lo5q_corrected"),
                          ("salt2_hi5q", CFD_EXTRACT / "salt2_jin_hi5q_corrected")]:
        cfd = rollup_cfd_reference(extract / "raw_extraction" / "boundary_layer_landmark_summary.csv")
        pred = {s: v for s, v in pm5_1d.get(case, {}).items() if v is not None}
        cp = pairs_for_case(pred, cfd)
        holdout_pairs_all.extend(cp)
        holdout_scores[case] = {
            "new_cfd_affine": score(cp, a_new, b_new),
            "orig_experiment_f2": score(cp, ORIG_F2_A, ORIG_F2_B),
        }
    holdout_combined = {
        "new_cfd_affine": score(holdout_pairs_all, a_new, b_new),
        "orig_experiment_f2": score(holdout_pairs_all, ORIG_F2_A, ORIG_F2_B),
    }

    # --- external: val_salt2 (CFD basis, salt_jin default property) ---
    # val_salt2 shares Salt2-nominal's operating point (265.7 W); on the CFD-matching
    # salt_jin default its 1D prediction (mdot 0.02219) is identical to Salt2 nominal.
    # So this is a genuine but partial external test: a DIFFERENT CFD realization
    # (val_salt_test_2 validation mesh/laminar) of the same operating point, scored
    # against the frozen all-4 CFD affine. NOTE: the parallel refit used salt_current
    # (mdot 0.0196) -- off-basis; this uses the CFD-consistent salt_jin default.
    val_1d = {}
    for r in _read(VAL_SALT2_1D):
        v = _f(r.get("predicted_K"))
        if v is not None:
            val_1d[str(r["sensor"]).strip()] = v
    val_cfd, val_cfd_vintage = load_valsalt2_cfd()
    val_pairs = pairs_for_case(val_1d, val_cfd)
    external_scores = {
        "status": "scored_cfd_basis_salt_jin",
        "cfd_target_vintage": val_cfd_vintage,
        "new_cfd_affine": score(val_pairs, a_new, b_new),
        "orig_experiment_f2": score(val_pairs, ORIG_F2_A, ORIG_F2_B),
        "note": "partial external: same operating point as Salt2 nominal train (identical salt_jin 1D input), independent val CFD realization as target.",
    }

    freeze = {
        "freeze_id": "CFD_AFFINE_ALL4_2026_07_23",
        "form": "T_corrected = a * T_1D + b (global affine, 2 DOF)",
        "target_reference": "CFD reference_k (TP=t_core_k, TW=t_wall_area_avg_k)",
        "fit_cases": "salt_1 + salt_2 + salt_3 + salt_4 nominal (all-four train)",
        "a_multiplier": a_new,
        "b_offset_K": b_new,
        "n_fit_pairs": len(nominal_pairs),
        "model_class": "empirical_discrepancy_ROM",
        "physical_closure_claim_allowed": False,
        "excluded_sensors": sorted(SCORE_EXCLUDED),
    }

    decision = {
        "cfd_affine_all4_a": a_new,
        "cfd_affine_all4_b": b_new,
        "holdout_salt2_pm5_new_cfd_affine_rmse_K": holdout_combined["new_cfd_affine"].get("corrected_rmse_K"),
        "holdout_salt2_pm5_new_cfd_affine_mae_K": holdout_combined["new_cfd_affine"].get("corrected_mae_K"),
        "holdout_salt2_pm5_raw_1D_mae_K": holdout_combined["new_cfd_affine"].get("raw_mae_K"),
        "holdout_orig_experiment_f2_mae_K": holdout_combined["orig_experiment_f2"].get("corrected_mae_K"),
        "external_val_salt2_status": external_scores.get("status"),
        "external_val_salt2_new_cfd_affine_mae_K": external_scores.get("new_cfd_affine", {}).get("corrected_mae_K"),
        "external_val_salt2_new_cfd_affine_rmse_K": external_scores.get("new_cfd_affine", {}).get("corrected_rmse_K"),
        "external_val_salt2_n": external_scores.get("new_cfd_affine", {}).get("n"),
        "physical_closure_claim": False,
        "repeated_exposure_caveat": "Salt2 +/-5Q and val_salt2 used more than once this session for model comparison; diagnostic refit, not a pristine single-use protected-split freeze score.",
    }

    guardrails = [
        ("native_output_mutation", False),
        ("registry_or_admission_mutation", False),
        ("scheduler_action", False),
        ("physical_source_property_or_qwall_release", False),
        ("physical_candidate_freeze", False),
        ("physical_closure_claim", False),
        ("coefficient_admission_as_physical_htc", False),
        ("s11_s15_s6_trigger_fired", False),
        ("hidden_multiplier_beyond_declared_affine", False),
        ("deletion_staging_commit_push", False),
    ]

    return {
        "freeze": freeze,
        "nominal_coverage": nominal_coverage,
        "holdout_scores": holdout_scores,
        "holdout_combined": holdout_combined,
        "external_scores": external_scores,
        "decision": decision,
        "guardrails": guardrails,
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    fieldnames = []
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, restval="")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    r = build()
    OUT.mkdir(parents=True, exist_ok=True)
    _write_csv(OUT / "cfd_affine_freeze_manifest.csv", [r["freeze"]])
    _write_csv(OUT / "nominal_fit_coverage.csv", r["nominal_coverage"])
    # flatten score tables
    score_rows = []
    for case, d in r["holdout_scores"].items():
        for model, s in d.items():
            score_rows.append({"split": "holdout", "case": case, "model": model, **s})
    for model, s in r["holdout_combined"].items():
        score_rows.append({"split": "holdout", "case": "salt2_pm5_combined", "model": model, **s})
    ext = r["external_scores"]
    if "new_cfd_affine" in ext:
        for model in ("new_cfd_affine", "orig_experiment_f2"):
            score_rows.append({"split": "external", "case": "val_salt2", "model": model,
                               **ext[model], "note": ext.get("note", "")})
    else:
        score_rows.append({"split": "external", "case": "val_salt2", "model": "deferred",
                           "n": 0, "note": ext.get("status")})
    _write_csv(OUT / "holdout_external_scores.csv", score_rows)
    _write_csv(OUT / "score_decision.csv", [{"key": k, "value": v} for k, v in r["decision"].items()])
    _write_csv(OUT / "no_mutation_guardrails.csv", [{"guardrail": k, "value": str(v)} for k, v in r["guardrails"]])
    (OUT / "score_summary.json").write_text(json.dumps(r["decision"], indent=2) + "\n")
    print(json.dumps({"freeze": r["freeze"], "decision": r["decision"], "coverage": r["nominal_coverage"]}, indent=2))


if __name__ == "__main__":
    main()
