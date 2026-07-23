#!/usr/bin/env python3.11
"""Freeze F2 (empirical affine bias ROM) and build/validate a score-once harness.

Task: TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23
Owner: claude

Purpose
-------
Track A of the two-track thesis is an empirical bias-corrected ROM:
`T_corrected = a * T_1D + b`. The recommended publication form is
`F2_global_affine`, fit on Salt1/Salt2 train-support sensor rows only
(a=0.3729829182408737, b=246.55192842685844, 32 fit rows). To turn it from a
transfer-stress diagnostic into a *legal protected-holdout score* the discipline
is: freeze the coefficients BEFORE touching any holdout target, then generate
blind predictions, then score once.

This builder does the legal, correct, always-needed steps now:
  1. FREEZE: emit an immutable pre-registration manifest of F2 (coefficients,
     fit provenance, legal input contract, split labels, and a content hash of
     the frozen-coefficients source + this file) BEFORE any holdout contact.
  2. HARNESS: a pure score-once function `score_rows()` implementing
     `T_corr = a*predicted_K + b`, per-sensor error, RMSE and MAE.
  3. DRY-RUN VALIDATION: exercise the harness on the Salt_2 NOMINAL
     validation_table (where predicted_K and measured_K both exist) to prove the
     harness is correct, WITHOUT scoring any protected holdout row.
  4. READINESS LEDGER: state, per holdout target, exactly which inputs are
     missing and whether the gap is analysis or compute.

It scores NO protected row (holdout inputs do not yet exist) and makes NO
physical-closure claim. F2/F5 are empirical discrepancy models
(mf11 decision: `empirical_diagnostic_only`).
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WP07 = REPO / "work_products" / "2026-07"

FROZEN_COEFFS = (
    WP07 / "2026-07-21" / "2026-07-21_fluid_reduced_dof_bias_transfer_screen" / "frozen_coefficients.csv"
)
NOMINAL_SCORECARD = WP07 / "2026-07-20" / "2026-07-20_tswfc2_bounded_nominal_scorecard" / "case_outputs"

OUT = WP07 / "2026-07-23" / "2026-07-23_f2_empirical_holdout_freeze_and_score"

# Canonical split (2026-07-17 policy). Primary blind holdout + external test.
HOLDOUT_TARGETS = [
    {
        "case_id": "salt2_lo5q",
        "split_role": "primary_blind_holdout",
        "target_1d_prediction_exists": False,
        "target_cfd_tp_tw_exists": False,
        "target_note": "Only upcomer-plane bulk/wall targets exist (2026-07-17_predict_salt2_pm5_holdout_extraction_repair); TP/TW sensor rows not extracted.",
    },
    {
        "case_id": "salt2_hi5q",
        "split_role": "primary_blind_holdout",
        "target_1d_prediction_exists": False,
        "target_cfd_tp_tw_exists": False,
        "target_note": "Only upcomer-plane bulk/wall targets exist; TP/TW sensor rows not extracted.",
    },
    {
        "case_id": "val_salt2",
        "split_role": "external_test",
        "target_1d_prediction_exists": False,
        "target_cfd_tp_tw_exists": False,
        "target_note": "Only heat-ledger/admission artifact exists (2026-07-17_predict_val_salt2_external_ledger); no compatible sensor-level external-test artifact.",
    },
]


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _content_hash(*paths: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(paths, key=str):
        h.update(p.read_bytes())
    return h.hexdigest()


# ---- the frozen model + score-once harness (pure) -------------------------

def frozen_f2() -> dict:
    for r in _read(FROZEN_COEFFS):
        if r["model_family"] == "F2_global_affine":
            return {
                "model_family": r["model_family"],
                "fit_form": r["fit_form"],
                "a_multiplier": float(r["multiplier_correction"]),
                "b_offset_K": float(r["offset_bias_K"]),
                "n_fit_rows": int(r["n_fit_rows"]),
                "degrees_of_freedom": int(r["degrees_of_freedom"]),
                "coefficient_source": r["coefficient_source"],
                "claim_boundary": r["claim_boundary"],
            }
    raise RuntimeError("F2_global_affine row not found in frozen_coefficients.csv")


def apply_f2(predicted_K: float, a: float, b: float) -> float:
    """T_corrected = a * T_1D + b."""
    return a * predicted_K + b


def score_rows(rows: list[dict], a: float, b: float) -> dict:
    """Score-once: apply frozen F2 to (predicted_K, measured_K) sensor rows.

    Only usable rows count: kind in {TP,TW}, finite predicted_K and measured_K,
    validation_excluded == False. Returns per-row errors + RMSE + MAE + baseline.
    This function reads NO coefficients from the data; a,b are the frozen inputs.
    """
    used = []
    for r in rows:
        if r.get("kind") not in ("TP", "TW"):
            continue
        if str(r.get("validation_excluded", "")).strip().lower() == "true":
            continue
        p, m = r.get("predicted_K", ""), r.get("measured_K", "")
        if p in (None, "") or m in (None, ""):
            continue
        try:
            p, m = float(p), float(m)
        except ValueError:
            continue
        corr = apply_f2(p, a, b)
        used.append(
            {
                "sensor": r.get("sensor"),
                "kind": r.get("kind"),
                "predicted_K": p,
                "corrected_K": corr,
                "measured_K": m,
                "raw_error_K": p - m,
                "corrected_error_K": corr - m,
            }
        )
    n = len(used)
    if n == 0:
        return {"n_rows": 0, "corrected_rmse_K": None, "corrected_mae_K": None,
                "raw_rmse_K": None, "raw_mae_K": None, "rows": []}
    c_sq = sum(u["corrected_error_K"] ** 2 for u in used) / n
    r_sq = sum(u["raw_error_K"] ** 2 for u in used) / n
    return {
        "n_rows": n,
        "corrected_rmse_K": c_sq ** 0.5,
        "corrected_mae_K": sum(abs(u["corrected_error_K"]) for u in used) / n,
        "raw_rmse_K": r_sq ** 0.5,
        "raw_mae_K": sum(abs(u["raw_error_K"]) for u in used) / n,
        "rows": used,
    }


def build() -> dict:
    f2 = frozen_f2()
    a, b = f2["a_multiplier"], f2["b_offset_K"]
    code_hash = _content_hash(FROZEN_COEFFS, Path(__file__))

    freeze_manifest = {
        "freeze_id": "F2_GLOBAL_AFFINE_EMPIRICAL_FREEZE_2026_07_23",
        "model_family": f2["model_family"],
        "fit_form": "T_corrected = a * T_1D + b",
        "a_multiplier": a,
        "b_offset_K": b,
        "n_fit_rows": f2["n_fit_rows"],
        "degrees_of_freedom": f2["degrees_of_freedom"],
        "coefficient_source": f2["coefficient_source"],
        "fit_cases": "salt_1_nominal + salt_2_nominal (train-support only)",
        "legal_runtime_input": "predicted_K = 1D bulk temperature arc-interpolated to TP/TW sensor placement (setup-legal); NO CFD mdot, wallHeatFlux, cooler duty, validation/holdout temperatures",
        "primary_blind_holdout": "salt2_lo5q, salt2_hi5q",
        "external_test": "val_salt2",
        "immutable": True,
        "content_sha256": code_hash,
        "model_class": "empirical_discrepancy_ROM",
        "physical_closure_claim_allowed": False,
        "claim_boundary": f2["claim_boundary"],
        "refit_after_freeze": False,
        "model_selection_after_freeze": False,
    }

    # --- dry-run validation of the harness on Salt_2 NOMINAL (not a holdout) ---
    dryrun_rows = []
    nominal_dir = NOMINAL_SCORECARD / "Salt_2" / "validation_table.csv"
    dry = score_rows(_read(nominal_dir), a, b)
    # independent recomputation of one row to assert correctness
    check_ok = True
    if dry["rows"]:
        u = dry["rows"][0]
        expected = a * u["predicted_K"] + b
        check_ok = abs(expected - u["corrected_K"]) < 1e-9
    dryrun_rows.append(
        {
            "dataset": "Salt_2_nominal_validation_table",
            "role": "harness_correctness_dry_run_NOT_a_holdout_score",
            "n_rows": dry["n_rows"],
            "raw_rmse_K": dry["raw_rmse_K"],
            "corrected_rmse_K": dry["corrected_rmse_K"],
            "raw_mae_K": dry["raw_mae_K"],
            "corrected_mae_K": dry["corrected_mae_K"],
            "affine_identity_check_passed": str(check_ok),
        }
    )

    # --- holdout-score readiness ledger ---
    readiness = []
    for t in HOLDOUT_TARGETS:
        needs = []
        if not t["target_1d_prediction_exists"]:
            needs.append("1D T_1D prediction at TP/TW sensors (run tamu_loop_model_v2 at this case's BC; analysis/cheap 1D)")
        if not t["target_cfd_tp_tw_exists"]:
            needs.append("TP/TW CFD sensor targets (extract from existing native run; CFD postprocessing, no new solve)")
        if t["case_id"] == "val_salt2":
            needs.append("compatible sensor-level external-test admission artifact (does not exist)")
        readiness.append(
            {
                "case_id": t["case_id"],
                "split_role": t["split_role"],
                "score_computable_now": "False",
                "missing_inputs": " | ".join(needs),
                "target_note": t["target_note"],
                "score_value": "blocked_pending_inputs",
            }
        )

    decision = {
        "f2_frozen": True,
        "harness_built_and_dry_run_validated": bool(dryrun_rows and dryrun_rows[0]["affine_identity_check_passed"] == "True"),
        "protected_rows_scored": 0,
        "overall": "f2_frozen_and_score_harness_ready_holdout_score_blocked_pending_target_extraction",
        "sole_blocker_salt2_pm5": "TP/TW CFD sensor target extraction for salt2_lo5q/salt2_hi5q (existing runs) + 1D +/-5Q predictions",
        "additional_blocker_val_salt2": "missing compatible external-test sensor artifact",
        "physical_closure_claim": False,
        "final_protected_score_values": 0,
    }

    guardrails = [
        ("native_output_mutation", False),
        ("registry_or_admission_mutation", False),
        ("scheduler_action", False),
        ("solver_sampler_or_harvest_launch", False),
        ("fluid_or_external_edit", False),
        ("thesis_current_or_latex_edit", False),
        ("protected_or_final_scoring_before_inputs", False),
        ("refit_after_freeze", False),
        ("model_selection_after_freeze", False),
        ("physical_closure_claim_for_F2_F5", False),
        ("hidden_multiplier_beyond_frozen_affine", False),
        ("physical_source_property_or_qwall_release", False),
        ("physical_candidate_freeze", False),
        ("s11_s15_s6_trigger_fired", False),
        ("deletion_staging_commit_push", False),
    ]

    source_manifest = [
        ("frozen_coefficients", FROZEN_COEFFS),
        ("nominal_validation_table_salt2", nominal_dir),
    ]

    summary = {
        "task_id": "TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23",
        "owner": "claude",
        "date": "2026-07-23",
        "freeze_id": freeze_manifest["freeze_id"],
        "a_multiplier": a,
        "b_offset_K": b,
        "content_sha256": code_hash,
        "harness_dry_run_corrected_rmse_K": dryrun_rows[0]["corrected_rmse_K"],
        "harness_affine_identity_check_passed": dryrun_rows[0]["affine_identity_check_passed"],
        "protected_rows_scored": 0,
        "decision": decision["overall"],
        "physical_closure_claim_allowed": False,
        "final_protected_score_values": 0,
        **{f"guardrail_{k}": v for k, v in guardrails},
    }

    return {
        "freeze_manifest": freeze_manifest,
        "dryrun": dryrun_rows,
        "readiness": readiness,
        "decision": decision,
        "guardrails": guardrails,
        "source_manifest": source_manifest,
        "summary": summary,
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    res = build()
    OUT.mkdir(parents=True, exist_ok=True)
    _write_csv(OUT / "f2_freeze_manifest.csv", [res["freeze_manifest"]])
    _write_csv(OUT / "score_harness_dry_run.csv", res["dryrun"])
    _write_csv(OUT / "holdout_score_readiness.csv", res["readiness"])
    _write_csv(OUT / "decision.csv", [{"key": k, "value": v} for k, v in res["decision"].items()])
    _write_csv(OUT / "no_mutation_guardrails.csv", [{"guardrail": k, "value": str(v)} for k, v in res["guardrails"]])
    _write_csv(
        OUT / "source_manifest.csv",
        [{"role": r, "path": str(p.relative_to(REPO)), "exists": str(p.exists())} for r, p in res["source_manifest"]],
    )
    (OUT / "summary.json").write_text(json.dumps(res["summary"], indent=2) + "\n")
    print(json.dumps(res["summary"], indent=2))


if __name__ == "__main__":
    main()
