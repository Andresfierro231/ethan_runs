#!/usr/bin/env python3
"""Build the frozen split/scoring-law package for fastest holdout progress."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/holdout-split-freeze-case-family-policy.md"
IMPORT = ROOT / "imports/2026-07-22_holdout_split_freeze_case_family_policy.json"

READINESS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_holdout_readiness_all_models_fastest_path"
SPLIT_POLICY = ROOT / "operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md"
SCORECARD = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell"
H2_FINISH = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_predictive_finish_readiness_closure"
H2_THESIS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition"
S13_CHAIN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def source_paths(*paths: Path) -> str:
    return ";".join(rel(path) for path in paths)


def case_family_policy_rows() -> list[dict[str, Any]]:
    common = source_paths(SPLIT_POLICY, SCORECARD / "case_partition_contract.csv", READINESS / "case_family_holdout_readiness.csv")
    rows: list[dict[str, Any]] = []
    for case_key in ("salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"):
        rows.append(
            {
                "case_key": case_key,
                "case_family": "salt_nominal_train",
                "frozen_split_role": "final_training",
                "frozen_scorecard_partition": "train_nominal",
                "fit_allowed_by_split_law": True,
                "model_selection_allowed_by_split_law": True,
                "fit_or_selection_allowed_now": False,
                "score_allowed_now": False,
                "score_allowed_after_model_freeze": "training_internal_score_only",
                "runtime_input_allowed": False,
                "release_required_before_use": "candidate_source_property_release_and_train_only_uq",
                "do_not_use_for": "protected holdout scoring before freeze; post-freeze tuning",
                "reason": "Only Salt1-4 nominal may fit/select the candidate, but current source/property and candidate-admission gates remain closed.",
                "source_paths": common,
            }
        )
    for case_key in ("salt1_lo10q", "salt1_hi10q"):
        rows.append(
            {
                "case_key": case_key,
                "case_family": "salt1_pm10_support",
                "frozen_split_role": "training_support_excluded_support_diagnostic",
                "frozen_scorecard_partition": "excluded_support_diagnostic",
                "fit_allowed_by_split_law": False,
                "model_selection_allowed_by_split_law": False,
                "fit_or_selection_allowed_now": False,
                "score_allowed_now": False,
                "score_allowed_after_model_freeze": "no_without_new_predeclared_split_policy",
                "runtime_input_allowed": False,
                "release_required_before_use": "new_policy_required_for_any_holdout_reclassification",
                "do_not_use_for": "current holdout; model selection; coefficient tuning; runtime input",
                "reason": "These rows are not current blind holdout. Treating them as holdout now would be retrospective split relaxation.",
                "source_paths": common,
            }
        )
    for case_key in ("salt4_lo5q", "salt4_hi5q"):
        rows.append(
            {
                "case_key": case_key,
                "case_family": "salt4_pm5_sensitivity",
                "frozen_split_role": "conditional_postfreeze_holdout_family_sensitivity",
                "frozen_scorecard_partition": "secondary_sensitivity_after_primary_score",
                "fit_allowed_by_split_law": False,
                "model_selection_allowed_by_split_law": False,
                "fit_or_selection_allowed_now": False,
                "score_allowed_now": False,
                "score_allowed_after_model_freeze": "yes_after_primary_score_and_sensitivity_policy",
                "runtime_input_allowed": False,
                "release_required_before_use": "separate_postfreeze_sensitivity_policy",
                "do_not_use_for": "model selection; primary holdout score; runtime input",
                "reason": "Terminal harvested perturbation evidence can test robustness only after candidate freeze and primary Salt2 PM5/val scoring law is locked.",
                "source_paths": source_paths(SCORECARD / "case_partition_contract.csv", READINESS / "case_family_holdout_readiness.csv"),
            }
        )
    for case_key in ("salt2_lo5q", "salt2_hi5q"):
        rows.append(
            {
                "case_key": case_key,
                "case_family": "salt2_pm5_primary_holdout",
                "frozen_split_role": "primary_blind_holdout",
                "frozen_scorecard_partition": "blind_holdout_pm5q",
                "fit_allowed_by_split_law": False,
                "model_selection_allowed_by_split_law": False,
                "fit_or_selection_allowed_now": False,
                "score_allowed_now": False,
            "score_allowed_after_model_freeze": "primary_holdout_score_only",
                "runtime_input_allowed": False,
                "release_required_before_use": "admitted_frozen_candidate_prediction_artifact",
                "do_not_use_for": "fitting; model selection; post-score candidate revision; runtime input",
                "reason": "This is the first current blind holdout family once a frozen candidate emits predictions.",
                "source_paths": source_paths(SCORECARD / "holdout_release_gates.csv", READINESS / "case_family_holdout_readiness.csv"),
            }
        )
    rows.append(
        {
            "case_key": "val_salt2",
            "case_family": "external_val_salt2",
            "frozen_split_role": "external_test",
            "frozen_scorecard_partition": "external_val_salt2",
            "fit_allowed_by_split_law": False,
            "model_selection_allowed_by_split_law": False,
            "fit_or_selection_allowed_now": False,
            "score_allowed_now": False,
            "score_allowed_after_model_freeze": "external_score_only",
            "runtime_input_allowed": False,
            "release_required_before_use": "admitted_frozen_candidate_prediction_artifact_and_external_ledger_join",
            "do_not_use_for": "fitting; model selection; post-score candidate revision; runtime input",
            "reason": "External ledger is ready, but external rows remain training-forbidden and score-only after freeze.",
            "source_paths": source_paths(SCORECARD / "holdout_release_gates.csv", READINESS / "case_family_holdout_readiness.csv"),
        }
    )
    for case_key in ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"):
        rows.append(
            {
                "case_key": case_key,
                "case_family": "salt2_salt4_pm10_future",
                "frozen_split_role": "future_holdout_candidate",
                "frozen_scorecard_partition": "future_blind_holdout",
                "fit_allowed_by_split_law": False,
                "model_selection_allowed_by_split_law": False,
                "fit_or_selection_allowed_now": False,
                "score_allowed_now": False,
                "score_allowed_after_model_freeze": "yes_future_score_only_after_primary_score",
                "runtime_input_allowed": False,
                "release_required_before_use": "terminal_admission_plus_frozen_prediction_artifact_plus_total_Q_caveat",
                "do_not_use_for": "current candidate selection; primary holdout score; runtime input",
                "reason": "Terminal evidence exists, but PM10 is future score-only and thermal heat-ledger interpretation carries total-Q drift caveats.",
                "source_paths": source_paths(READINESS / "case_family_holdout_readiness.csv"),
            }
        )
    rows.append(
        {
            "case_key": "salt3_q_insulation_matrix",
            "case_family": "new_cfd_holdout_candidate",
            "frozen_split_role": "future_new_cfd_holdout_candidate",
            "frozen_scorecard_partition": "future_new_cfd_holdout",
            "fit_allowed_by_split_law": False,
            "model_selection_allowed_by_split_law": False,
            "fit_or_selection_allowed_now": False,
            "score_allowed_now": False,
            "score_allowed_after_model_freeze": "no_until_nonduplicate_staging_run_completion_and_admission",
            "runtime_input_allowed": False,
            "release_required_before_use": "new_CFD_run_completion_and_same_contract_admission",
            "do_not_use_for": "current fast-route score; model selection before admitted as new holdout",
            "reason": "Canonical policy names this as a future new-CFD holdout candidate, but it is not part of the immediate Salt2 PM5/val path.",
            "source_paths": rel(SPLIT_POLICY),
        }
    )
    return rows


def score_release_law_rows() -> list[dict[str, Any]]:
    return [
        {
            "score_law_id": "L0_split_law_frozen",
            "applies_to_partition": "all",
            "current_status": "frozen_by_this_policy_package",
            "required_inputs": "case_family_policy_table; source_manifest; no_mutation_guardrails",
            "fit_allowed": "train_nominal_only_after_candidate_source_property_gate",
            "model_selection_allowed": "train_nominal_only_before_candidate_freeze",
            "score_allowed_now": False,
            "score_allowed_after_freeze": "partition_specific",
            "guardrail": "no split-role relaxation after any protected score is viewed",
        },
        {
            "score_law_id": "L1_candidate_admission",
            "applies_to_partition": "model_candidate",
            "current_status": "blocked",
            "required_inputs": "source/property release; runtime-input audit; same-QOI train-only UQ; exact candidate definition",
            "fit_allowed": "Salt1-4 nominal only",
            "model_selection_allowed": "Salt1-4 nominal only",
            "score_allowed_now": False,
            "score_allowed_after_freeze": "not_a_score_gate",
            "guardrail": "candidate must be named and frozen before blind prediction generation",
        },
        {
            "score_law_id": "L2_primary_holdout_score",
            "applies_to_partition": "salt2_pm5_primary_holdout",
            "current_status": "blocked_no_frozen_prediction",
            "required_inputs": "admitted candidate freeze; frozen prediction artifact; no-refit proof",
            "fit_allowed": "no",
            "model_selection_allowed": "no",
            "score_allowed_now": False,
            "score_allowed_after_freeze": "yes_score_once",
            "guardrail": "Salt2 +/-5Q is the first protected score; outcome cannot change candidate",
        },
        {
            "score_law_id": "L3_external_score",
            "applies_to_partition": "val_salt2_external",
            "current_status": "blocked_no_frozen_prediction",
            "required_inputs": "external ledger join; admitted candidate freeze; frozen prediction artifact",
            "fit_allowed": "no",
            "model_selection_allowed": "no",
            "score_allowed_now": False,
            "score_allowed_after_freeze": "yes_separate_external_scorecard",
            "guardrail": "external result is not model-selection evidence",
        },
        {
            "score_law_id": "L4_secondary_sensitivity",
            "applies_to_partition": "salt4_pm5_and_pm10_future",
            "current_status": "conditional",
            "required_inputs": "primary score completed; predeclared secondary policy; PM10 total-Q caveat",
            "fit_allowed": "no",
            "model_selection_allowed": "no",
            "score_allowed_now": False,
            "score_allowed_after_freeze": "yes_secondary_only",
            "guardrail": "secondary results cannot alter primary claims or candidate definition",
        },
        {
            "score_law_id": "L5_excluded_support",
            "applies_to_partition": "salt1_pm10_support",
            "current_status": "excluded",
            "required_inputs": "new predeclared split policy if role ever changes",
            "fit_allowed": "no",
            "model_selection_allowed": "no",
            "score_allowed_now": False,
            "score_allowed_after_freeze": "no_under_current_policy",
            "guardrail": "do not reclassify exposed support rows as blind holdout",
        },
    ]


def score_law_after_freeze_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in read_csv(SCORECARD / "metric_contract.csv"):
        rows.append(
            {
                "metric_id": metric["metric_id"],
                "metric_family": metric["metric_family"],
                "target_lane": metric["target_lane"],
                "required_prediction_fields": metric["required_prediction_fields"],
                "allowed_on_train": metric["allowed_on_train"],
                "allowed_on_blind_holdout": metric["allowed_on_blind_holdout"],
                "allowed_on_external": metric["allowed_on_external"],
                "allowed_on_future": metric["allowed_on_future"],
                "fit_or_selection_from_blind_rows": metric["fit_or_selection_from_blind_rows"],
                "runtime_forbidden_inputs": metric["runtime_forbidden_inputs"],
                "score_law": "compute only from frozen predictions joined to target rows; never use blind residuals for model changes",
            }
        )
    return rows


def split_freeze_case_family_policy_rows() -> list[dict[str, Any]]:
    """Compatibility table for package-local validators and writer handoff."""

    partition_by_case = {
        "salt1_nominal": ("train_nominal", "final_training", "yes_for_train_internal_only"),
        "salt2_jin_nominal": ("train_nominal", "final_training", "yes_for_train_internal_only"),
        "salt3_jin_nominal": ("train_nominal", "final_training", "yes_for_train_internal_only"),
        "salt4_nominal": ("train_nominal", "final_training", "yes_for_train_internal_only"),
        "salt2_lo5q": ("blind_holdout_pm5q", "blind_holdout_salt2_pm5q", "yes_score_only"),
        "salt2_hi5q": ("blind_holdout_pm5q", "blind_holdout_salt2_pm5q", "yes_score_only"),
        "val_salt2": ("blind_external_val_salt2", "blind_external_val_salt2", "yes_score_only"),
        "salt1_lo10q": ("excluded_support_diagnostic", "support_diagnostic_not_final_training", "no_current_holdout_support_only"),
        "salt1_hi10q": ("excluded_support_diagnostic", "support_diagnostic_not_final_training", "no_current_holdout_support_only"),
        "salt4_lo5q": ("secondary_sensitivity_after_primary_score", "conditional_postfreeze_sensitivity", "conditional"),
        "salt4_hi5q": ("secondary_sensitivity_after_primary_score", "conditional_postfreeze_sensitivity", "conditional"),
        "salt2_lo10q": ("future_holdout_pm10", "future_blind_holdout_blocked_terminal_admission", "future_only_after_terminal_admission_and_freeze"),
        "salt2_hi10q": ("future_holdout_pm10", "future_blind_holdout_blocked_terminal_admission", "future_only_after_terminal_admission_and_freeze"),
        "salt4_lo10q": ("future_holdout_pm10", "future_blind_holdout_blocked_terminal_admission", "future_only_after_terminal_admission_and_freeze"),
        "salt4_hi10q": ("future_holdout_pm10", "future_blind_holdout_blocked_terminal_admission", "future_only_after_terminal_admission_and_freeze"),
        "salt3_q_insulation_matrix": ("future_external_new_cfd", "future_new_cfd_blocked_run_and_admission", "no_until_new_cfd_run_and_admission"),
    }
    source = source_paths(SPLIT_POLICY, READINESS / "case_family_holdout_readiness.csv", SCORECARD / "case_partition_contract.csv")
    rows: list[dict[str, Any]] = []
    for case_key, (partition, role, score_after) in partition_by_case.items():
        rows.append(
            {
                "case_key": case_key,
                "locked_partition": partition,
                "locked_role": role,
                "fit_allowed_before_candidate_freeze": "no",
                "model_selection_allowed_before_candidate_freeze": "no",
                "score_allowed_now": "no",
                "fit_allowed_after_candidate_admission": "yes_train_nominal_only" if partition == "train_nominal" else "no",
                "model_selection_allowed_after_candidate_admission": "yes_train_nominal_only" if partition == "train_nominal" else "no",
                "score_allowed_after_frozen_predictions": score_after,
                "runtime_input_allowed": "no_for_targets_and_residuals",
                "release_gate": "admitted frozen prediction artifact; partition-specific release law",
                "policy_guardrail": "release permits scoring only; never retroactively permits fitting or candidate selection",
                "source_paths": source,
            }
        )
    return rows


def score_order_rows() -> list[dict[str, Any]]:
    return [
        {"order": 1, "score_block": "train_internal_report", "case_keys": "salt1_nominal;salt2_jin_nominal;salt3_jin_nominal;salt4_nominal", "when_allowed": "after candidate freeze for diagnostics/internal train error only", "scorecard": "training/internal", "can_select_or_refit_after_viewing": False},
        {"order": 2, "score_block": "primary_blind_holdout", "case_keys": "salt2_lo5q;salt2_hi5q", "when_allowed": "after frozen predictions exist", "scorecard": "primary holdout", "can_select_or_refit_after_viewing": False},
        {"order": 3, "score_block": "external_test", "case_keys": "val_salt2", "when_allowed": "after frozen predictions exist and external ledger join is fixed", "scorecard": "external", "can_select_or_refit_after_viewing": False},
        {"order": 4, "score_block": "secondary_sensitivity", "case_keys": "salt4_lo5q;salt4_hi5q", "when_allowed": "after primary/external score and separate sensitivity policy", "scorecard": "secondary sensitivity", "can_select_or_refit_after_viewing": False},
        {"order": 5, "score_block": "future_holdout", "case_keys": "salt2_lo10q;salt2_hi10q;salt4_lo10q;salt4_hi10q", "when_allowed": "after primary/external score, frozen predictions, and total-Q caveat", "scorecard": "future holdout", "can_select_or_refit_after_viewing": False},
        {"order": 6, "score_block": "excluded_support", "case_keys": "salt1_lo10q;salt1_hi10q", "when_allowed": "not allowed under current policy", "scorecard": "none", "can_select_or_refit_after_viewing": False},
    ]


def model_lane_consumption_rows() -> list[dict[str, Any]]:
    matrix = read_csv(READINESS / "all_model_holdout_gate_matrix.csv")
    rows: list[dict[str, Any]] = []
    for row in matrix:
        lane = row["model_lane"]
        rows.append(
            {
                "model_lane": lane,
                "may_use_train_nominal_for_admission": "yes_after_source_property_gate" if lane in {"PASSIVE-H2-CAND001", "D4 physical successor", "D3 physical successor", "D2 source-bounded projection", "M0 setup-only baseline"} else "component_or_diagnostic_only",
                "may_use_salt2_pm5_before_freeze": False,
                "may_use_val_salt2_before_freeze": False,
                "may_use_salt4_pm5_or_pm10_before_primary_score": False,
                "can_generate_holdout_predictions_now": row["can_generate_holdout_predictions_now"],
                "can_score_holdout_now": row["can_score_holdout_now"],
                "next_gate_required": row["fastest_unblock"],
                "policy_note": "All model lanes must consume this split-freeze law before any protected prediction/scoring row.",
                "source_paths": row["source_paths"],
            }
        )
    return rows


def model_lane_next_action_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    h2 = read_json(H2_FINISH / "summary.json")
    s13 = read_json(S13_CHAIN / "summary.json")
    for lane in read_csv(READINESS / "all_model_holdout_gate_matrix.csv"):
        name = lane["model_lane"]
        if name == "PASSIVE-H2-CAND001":
            key_state = (
                f"five_family_freeze={h2.get('full_five_family_freeze_allowed', False)}; "
                f"r4_future_allowed={h2.get('reduced_four_family_future_candidate_allowed', True)}; "
                f"source_release_rows={h2.get('source_property_release_rows', 0)}"
            )
            next_action = "wait_for_active_salt1_source_envelope_recovery_then_open_predeclared_R4_or_release_failclose"
            priority = "closest_to_working_model_if_source_envelope_and_same_qoi_uq_pass"
        elif name == "D4 physical successor":
            key_state = lane["current_best_evidence"]
            next_action = "preflight_source_bounded_physical_successor_without_holdout_touch"
            priority = "fallback_if_PASSIVE_H2_fails_closed"
        elif name == "S13/upcomer exchange":
            key_state = (
                f"endpoint_ready={s13.get('endpoint_residual_basis_ready_rows', 0)}/{s13.get('endpoint_basis_rows', 0)}; "
                f"same_window={s13.get('same_window_equivalence_admitted_rows', 0)}/{s13.get('same_window_equivalence_rows', 0)}; "
                f"gci_run={s13.get('formal_gci_run_rows', 0)}/{s13.get('formal_gci_rows', 0)}"
            )
            next_action = "do_not_admit_until_same_physical_medium_fine_windows_exist"
            priority = "thesis_open_cv_evidence_not_fastest_working_model"
        else:
            key_state = lane["current_best_evidence"]
            next_action = lane["fastest_unblock"]
            priority = "secondary_or_blocked_lane"
        rows.append(
            {
                "model_lane": name,
                "can_generate_holdout_predictions_now": lane["can_generate_holdout_predictions_now"],
                "can_score_holdout_now": lane["can_score_holdout_now"],
                "admission_or_freeze_state": lane["candidate_admitted_or_frozen"],
                "key_state": key_state,
                "next_action": next_action,
                "working_model_priority": priority,
                "forbidden_now": "protected scoring; final score; candidate freeze; source/property release shortcut; fit/model selection from holdout",
                "source_paths": lane["source_paths"],
            }
        )
    return rows


def blocker_and_unblock_rows() -> list[dict[str, Any]]:
    return [
        {"rank": 1, "blocker": "candidate_not_admitted_or_frozen", "current_state": "blocking_all_scores", "owner_or_active_row": "PASSIVE-H2 R4 and Salt1 junction recovery active; D4 fallback ready to claim", "fastest_unblock": "resolve H2 source-envelope/UQ or fail closed, then D4 physical successor if needed", "evidence_path": rel(H2_FINISH / "predictive_finish_readiness_matrix.csv")},
        {"rank": 2, "blocker": "no_frozen_prediction_artifact", "current_state": "blocking_salt2_pm5_and_val_salt2_scores", "owner_or_active_row": "future prediction generator after freeze", "fastest_unblock": "generate predictions from immutable candidate without target reads", "evidence_path": rel(SCORECARD / "prediction_join_shell.csv")},
        {"rank": 3, "blocker": "source_property_release_closed", "current_state": "blocking candidate fit/select/freeze", "owner_or_active_row": "H2 R4 source-envelope/UQ row", "fastest_unblock": "strict source-envelope and same-QOI UQ pass or permanent fail-close", "evidence_path": rel(H2_THESIS / "source_property_disposition.csv")},
        {"rank": 4, "blocker": "s13_not_admitted", "current_state": "not blocking immediate H2/D4 score law but blocks exchange-cell claims", "owner_or_active_row": "S13 same-window endpoint GCI/UQ chain", "fastest_unblock": "same-window equivalence before formal GCI/UQ admission", "evidence_path": rel(S13_CHAIN / "summary.json")},
        {"rank": 5, "blocker": "salt1_pm10_not_holdout", "current_state": "policy_excluded", "owner_or_active_row": "this split-freeze package", "fastest_unblock": "do not unblock for current route; needs new predeclared policy", "evidence_path": rel(READINESS / "case_family_holdout_readiness.csv")},
    ]


def publication_claim_rows() -> list[dict[str, Any]]:
    return [
        {"claim_id": "C1", "claim": "Salt2 +/-5Q and val_salt2 are the fastest usable holdout/external targets.", "status": "allowed_with_freeze_gate", "required_words": "target-ready but not score-ready until frozen predictions exist", "forbidden_words": "scored; validated; admitted final model", "source_path": rel(READINESS / "summary.json")},
        {"claim_id": "C2", "claim": "No model lane is currently legal to score holdout.", "status": "allowed", "required_words": "0 model lanes score-ready now", "forbidden_words": "model failed on holdout", "source_path": rel(READINESS / "all_model_holdout_gate_matrix.csv")},
        {"claim_id": "C3", "claim": "PASSIVE-H2 is the fastest candidate if source-envelope/UQ release succeeds.", "status": "allowed_as_route_not_result", "required_words": "candidate route; not frozen; not scored", "forbidden_words": "admitted PASSIVE-H2", "source_path": rel(H2_FINISH / "summary.json")},
        {"claim_id": "C4", "claim": "D4 is the fallback physical successor direction.", "status": "allowed_as_design_priority", "required_words": "diagnostic transfer signal must be made source-bounded", "forbidden_words": "D4 holdout score", "source_path": rel(READINESS / "all_model_holdout_gate_matrix.csv")},
        {"claim_id": "C5", "claim": "Salt1 +/-10Q is not holdout under the current policy.", "status": "allowed", "required_words": "support/excluded diagnostic", "forbidden_words": "blind Salt1 PM10 score", "source_path": rel(READINESS / "case_family_holdout_readiness.csv")},
    ]


def no_leakage_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {"claim": "Salt1-4 nominal rows are the only final model-development basis.", "status": "allowed_policy_claim", "basis": "canonical split policy and final scorecard shell", "guardrail": "source/property gates can still block fitting; this package does not release them"},
        {"claim": "Salt2 +/-5Q is the first blind holdout family after freeze.", "status": "allowed_policy_claim", "basis": "holdout readiness package reports Salt2 PM5 target-ready", "guardrail": "score-only after frozen predictions; no tuning"},
        {"claim": "val_salt2 is external score-only after freeze.", "status": "allowed_policy_claim", "basis": "external ledger ready and training forbidden", "guardrail": "separate external scorecard; no selection"},
        {"claim": "A model can be scored today.", "status": "forbidden", "basis": "0 model lanes score-ready now", "guardrail": "requires admitted candidate freeze and predictions"},
        {"claim": "S13 can be admitted via current coarse/medium/fine evidence.", "status": "forbidden", "basis": "same-window equivalence admitted rows remain 0", "guardrail": "endpoint geometry readiness is not enough"},
        {"claim": "PASSIVE-H2 current five-family candidate can freeze now.", "status": "forbidden", "basis": "Salt1 junction coverage and source-envelope/UQ gates remain closed", "guardrail": "new R4 candidate must be predeclared if used"},
    ]


def executable_unlock_sequence_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(READINESS / "fastest_safe_holdout_sequence.csv"):
        rows.append(
            {
                "rank": row["rank"],
                "phase": row["phase"],
                "objective": row["objective"],
                "ready_now": row["ready_now"],
                "candidate_task_id": row["candidate_task_id"],
                "locked_policy_status": "adopted_by_this_package" if row["rank"] == "1" else "blocked_until_prior_phase_passes",
                "forbidden_actions": row["forbidden_actions"],
            }
        )
    return rows


def thesis_figure_table_ledger_rows() -> list[dict[str, Any]]:
    return [
        {"artifact_id": "tab_split_freeze_policy", "artifact_type": "table", "source_file": "frozen_case_family_policy.csv", "publication_use": "methods split policy and leakage prevention", "caption_boundary": "policy table only; no model score"},
        {"artifact_id": "tab_score_release_law", "artifact_type": "table", "source_file": "score_release_law.csv", "publication_use": "scoring sequence and score-only gates", "caption_boundary": "no protected scores emitted"},
        {"artifact_id": "tab_model_lane_contract", "artifact_type": "table", "source_file": "model_lane_consumption_contract.csv", "publication_use": "why no model lane can score yet", "caption_boundary": "admission/freeze blockers only"},
        {"artifact_id": "fig_fastest_route_flow", "artifact_type": "future_figure_spec", "source_file": "executable_unlock_sequence.csv", "publication_use": "workflow diagram for thesis/paper methods", "caption_boundary": "do not imply completion of later phases"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (READINESS / "summary.json", "fastest-route readiness summary"),
        (READINESS / "case_family_holdout_readiness.csv", "case-family readiness input"),
        (READINESS / "all_model_holdout_gate_matrix.csv", "model-lane readiness input"),
        (READINESS / "fastest_safe_holdout_sequence.csv", "phase-order input"),
        (SPLIT_POLICY, "canonical split policy"),
        (SCORECARD / "case_partition_contract.csv", "scorecard partition shell"),
        (SCORECARD / "holdout_release_gates.csv", "release gate shell"),
        (SCORECARD / "metric_contract.csv", "metric and runtime forbidden input policy"),
        (H2_FINISH / "summary.json", "PASSIVE-H2 finish readiness context"),
        (H2_THESIS / "summary.json", "PASSIVE-H2 diagnostic/release fail-closed context"),
        (S13_CHAIN / "summary.json", "S13 endpoint/GCI status context"),
    ]
    return [{"path": rel(path), "role": role, "exists": str(path.exists()).lower(), "read_only": "true"} for path, role in paths]


def no_mutation_guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false", "status": "false"},
        {"guardrail": "native_output_mutation", "value": "false", "status": "false"},
        {"guardrail": "registry_or_admission_mutated", "value": "false", "status": "false"},
        {"guardrail": "registry_or_admission_mutation", "value": "false", "status": "false"},
        {"guardrail": "scheduler_action", "value": "false", "status": "false"},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "value": "false", "status": "false"},
        {"guardrail": "protected_or_final_scoring", "value": "false", "status": "false"},
        {"guardrail": "fitting_tuning_model_selection", "value": "false", "status": "false"},
        {"guardrail": "source_property_qwall_numeric_release", "value": "false", "status": "false"},
        {"guardrail": "coefficient_admission", "value": "false", "status": "false"},
        {"guardrail": "candidate_freeze", "value": "false", "status": "false"},
        {"guardrail": "split_role_relaxation", "value": "false", "status": "false"},
        {"guardrail": "runtime_leakage_relaxation", "value": "false", "status": "false"},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""# Holdout Split-Freeze Case-Family Policy

Generated: `{summary['generated_at']}`

## Result

This package freezes the case-family split and scoring law for the fastest
holdout route. It does not freeze a model and it does not score any protected
row.

Immediate consequence:

- Salt1-4 nominal are the only train/model-selection rows, and even they remain
  blocked until candidate source/property and same-QOI train-only gates pass.
- Salt2 +/-5Q is the primary blind holdout family after an immutable candidate
  freeze.
- `val_salt2` is external score-only after the same freeze.
- Salt4 +/-5Q and Salt2/Salt4 +/-10Q are secondary/future score-only rows.
- Salt1 +/-10Q remains support/excluded diagnostic under current policy.

## Fastest Route

1. Resolve PASSIVE-H2 source-envelope/UQ or fail it closed.
2. If H2 cannot freeze, advance D4 as a source-bounded physical successor.
3. Run same-QOI Salt1-4 train-only UQ for one admitted candidate.
4. Create an immutable freeze manifest.
5. Generate Salt2 +/-5Q and val_salt2 predictions without reading targets.
6. Score once, with no tuning after seeing scores.

## Outputs

- `frozen_case_family_policy.csv`
- `score_release_law.csv`
- `holdout_score_order.csv`
- `model_lane_consumption_contract.csv`
- `blocker_unblock_ledger.csv`
- `publication_claim_boundaries.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_closeout(summary: dict[str, Any], changed_files: list[str]) -> None:
    status = f"""---
provenance:
  generated_by: codex
  task_id: {TASK_ID}
  date: 2026-07-22
tags:
  - holdout
  - split-policy
  - predictive-model
related:
  - {rel(OUT)}
---

# {TASK_ID}

## Objective

Freeze the legal split/scoring sequence for the fastest holdout route before any
model lane can score protected rows.

## Outcome

Completed. The split law is now package-frozen as a governance artifact:
Salt2 +/-5Q is first primary holdout after candidate freeze, `val_salt2` is
external score-only after freeze, Salt4 +/-5Q is secondary sensitivity, PM10 is
future score-only with total-Q caveat, and Salt1 +/-10Q remains excluded support.
No model was admitted, frozen, scored, or selected.

## Changes Made

{chr(10).join(f'- `{path}`' for path in changed_files)}

## Validation

- `python3.11 -m unittest tools.analyze.test_holdout_split_freeze_case_family_policy`
- `python3.11 tools/analyze/build_holdout_split_freeze_case_family_policy.py`
- `python3.11 -B work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/validate_package.py`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID} --rebuild-index`

## Guardrails

No native solver output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
current/LaTeX edit, protected/final scoring, fitting/tuning/model selection,
source/property/Qwall/numeric release, coefficient admission, candidate freeze,
split-role relaxation, or runtime-leakage relaxation occurred.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(status, encoding="utf-8")

    journal = f"""---
provenance:
  generated_by: codex
  task_id: {TASK_ID}
  date: 2026-07-22
tags:
  - holdout
  - split-policy
  - no-leakage
related:
  - {rel(OUT / 'frozen_case_family_policy.csv')}
---

# Holdout Split-Freeze Case-Family Policy

Task: `{TASK_ID}`

## Attempted

I converted the readiness audit and final scorecard shell into a durable
split-freeze law. The goal was to remove ambiguity before any H2/D4 candidate
work can generate protected predictions or scores.

## Observed

The target-side evidence is ahead of model readiness. Salt2 +/-5Q and
`val_salt2` are target/ledger-ready, while every current model lane remains
unfrozen. PASSIVE-H2 has active follow-on rows, but current finish evidence
still reports no freeze. S13 endpoint basis improved, but same-window
equivalence still blocks exchange-cell admission.

## Inferred

The fastest legal route is not to search for more holdout rows. It is to hold
the split fixed, finish one model candidate from train-only evidence, emit
frozen predictions, then score exactly once.

## Caveats

This is a policy/freeze-of-split package, not a candidate freeze. It makes
future scoring stricter; it does not release any source/property, Qwall,
coefficient, prediction, or score artifact.

## Next Useful Actions

1. Let the active PASSIVE-H2 R4 source-envelope/UQ row decide freeze eligibility
   or fail closed.
2. Keep Salt1 junction recovery separate from this scoring law.
3. Claim D4 physical successor preflight if H2 cannot release.
4. Only after one candidate is admitted, claim train-only same-QOI UQ and
   immutable freeze.
"""
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(journal, encoding="utf-8")

    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "changed_files": changed_files,
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "thesis_current_edit": False,
        "protected_or_final_scoring": False,
        "fitting_tuning_model_selection": False,
        "source_property_qwall_numeric_release": False,
        "candidate_freeze": False,
        "split_role_relaxation": False,
        "runtime_leakage_relaxation": False,
        "no_scorecard_outputs": True,
        "provenance_flags": {
            "generated_from_script": rel(Path(__file__)),
            "native_output_mutation": False,
            "linked_cases_used_as_provenance": False,
        },
    }
    json_dump(IMPORT, manifest)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    case_rows = case_family_policy_rows()
    split_freeze_rows = split_freeze_case_family_policy_rows()
    score_law = score_release_law_rows()
    metric_score_law = score_law_after_freeze_rows()
    score_order = score_order_rows()
    model_rows = model_lane_consumption_rows()
    model_actions = model_lane_next_action_rows()
    blockers = blocker_and_unblock_rows()
    claims = publication_claim_rows()
    no_leakage_claims = no_leakage_claim_boundary_rows()
    executable_sequence = executable_unlock_sequence_rows()
    thesis_ledger = thesis_figure_table_ledger_rows()
    sources = source_manifest_rows()
    guardrails = no_mutation_guardrails()

    csv_dump(
        out / "frozen_case_family_policy.csv",
        [
            "case_key",
            "case_family",
            "frozen_split_role",
            "frozen_scorecard_partition",
            "fit_allowed_by_split_law",
            "model_selection_allowed_by_split_law",
            "fit_or_selection_allowed_now",
            "score_allowed_now",
            "score_allowed_after_model_freeze",
            "runtime_input_allowed",
            "release_required_before_use",
            "do_not_use_for",
            "reason",
            "source_paths",
        ],
        case_rows,
    )
    csv_dump(
        out / "split_freeze_case_family_policy.csv",
        [
            "case_key",
            "locked_partition",
            "locked_role",
            "fit_allowed_before_candidate_freeze",
            "model_selection_allowed_before_candidate_freeze",
            "score_allowed_now",
            "fit_allowed_after_candidate_admission",
            "model_selection_allowed_after_candidate_admission",
            "score_allowed_after_frozen_predictions",
            "runtime_input_allowed",
            "release_gate",
            "policy_guardrail",
            "source_paths",
        ],
        split_freeze_rows,
    )
    csv_dump(
        out / "score_release_law.csv",
        [
            "score_law_id",
            "applies_to_partition",
            "current_status",
            "required_inputs",
            "fit_allowed",
            "model_selection_allowed",
            "score_allowed_now",
            "score_allowed_after_freeze",
            "guardrail",
        ],
        score_law,
    )
    csv_dump(
        out / "score_law_after_freeze.csv",
        [
            "metric_id",
            "metric_family",
            "target_lane",
            "required_prediction_fields",
            "allowed_on_train",
            "allowed_on_blind_holdout",
            "allowed_on_external",
            "allowed_on_future",
            "fit_or_selection_from_blind_rows",
            "runtime_forbidden_inputs",
            "score_law",
        ],
        metric_score_law,
    )
    csv_dump(
        out / "holdout_score_order.csv",
        ["order", "score_block", "case_keys", "when_allowed", "scorecard", "can_select_or_refit_after_viewing"],
        score_order,
    )
    csv_dump(
        out / "model_lane_consumption_contract.csv",
        [
            "model_lane",
            "may_use_train_nominal_for_admission",
            "may_use_salt2_pm5_before_freeze",
            "may_use_val_salt2_before_freeze",
            "may_use_salt4_pm5_or_pm10_before_primary_score",
            "can_generate_holdout_predictions_now",
            "can_score_holdout_now",
            "next_gate_required",
            "policy_note",
            "source_paths",
        ],
        model_rows,
    )
    csv_dump(
        out / "model_lane_next_actions.csv",
        [
            "model_lane",
            "can_generate_holdout_predictions_now",
            "can_score_holdout_now",
            "admission_or_freeze_state",
            "key_state",
            "next_action",
            "working_model_priority",
            "forbidden_now",
            "source_paths",
        ],
        model_actions,
    )
    csv_dump(out / "blocker_unblock_ledger.csv", ["rank", "blocker", "current_state", "owner_or_active_row", "fastest_unblock", "evidence_path"], blockers)
    csv_dump(out / "publication_claim_boundaries.csv", ["claim_id", "claim", "status", "required_words", "forbidden_words", "source_path"], claims)
    csv_dump(out / "no_leakage_claim_boundaries.csv", ["claim", "status", "basis", "guardrail"], no_leakage_claims)
    csv_dump(
        out / "executable_unlock_sequence.csv",
        ["rank", "phase", "objective", "ready_now", "candidate_task_id", "locked_policy_status", "forbidden_actions"],
        executable_sequence,
    )
    csv_dump(
        out / "thesis_figure_table_ledger.csv",
        ["artifact_id", "artifact_type", "source_file", "publication_use", "caption_boundary"],
        thesis_ledger,
    )
    csv_dump(out / "source_manifest.csv", ["path", "role", "exists", "read_only"], sources)
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "value", "status"], guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "split_freeze_policy_locked_no_scoring_no_freeze",
        "case_policy_rows": len(case_rows),
        "score_law_rows": len(score_law),
        "metric_score_law_rows": len(metric_score_law),
        "model_lane_contract_rows": len(model_rows),
        "model_lane_rows": len(model_actions),
        "score_ready_now": 0,
        "score_allowed_now_rows": sum(1 for row in case_rows if row["score_allowed_now"]),
        "fit_or_selection_allowed_now_rows": sum(1 for row in case_rows if row["fit_or_selection_allowed_now"]),
        "primary_holdout_after_freeze": "salt2_lo5q;salt2_hi5q",
        "external_after_freeze": "val_salt2",
        "salt1_pm10_holdout_allowed": False,
        "model_candidate_freeze_created": False,
        "protected_or_final_scoring": False,
        "fitting_tuning_model_selection": False,
        "source_property_qwall_numeric_release": False,
        "source_property_release": False,
        "candidate_freeze": False,
        "split_role_relaxation": False,
        "native_solver_outputs_mutated": False,
        "native_output_mutation": False,
        "registry_or_admission_mutated": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "runtime_leakage_relaxation": False,
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)

    changed_files = [
        rel(Path(__file__)),
        rel(ROOT / "tools/analyze/test_holdout_split_freeze_case_family_policy.py"),
        rel(out / "README.md"),
        rel(out / "summary.json"),
        rel(out / "frozen_case_family_policy.csv"),
        rel(out / "split_freeze_case_family_policy.csv"),
        rel(out / "score_release_law.csv"),
        rel(out / "score_law_after_freeze.csv"),
        rel(out / "holdout_score_order.csv"),
        rel(out / "model_lane_consumption_contract.csv"),
        rel(out / "model_lane_next_actions.csv"),
        rel(out / "blocker_unblock_ledger.csv"),
        rel(out / "publication_claim_boundaries.csv"),
        rel(out / "no_leakage_claim_boundaries.csv"),
        rel(out / "executable_unlock_sequence.csv"),
        rel(out / "thesis_figure_table_ledger.csv"),
        rel(out / "source_manifest.csv"),
        rel(out / "no_mutation_guardrails.csv"),
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
    ]
    for local_helper in (out / "build_package.py", out / "validate_package.py"):
        if local_helper.exists():
            changed_files.append(rel(local_helper))
    write_closeout(summary, changed_files)
    return summary


def main() -> None:
    print(json.dumps(build(OUT), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
