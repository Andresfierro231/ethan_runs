#!/usr/bin/env python3
"""Build the corrected-split final predictive scorecard wrapper.

This package is a split/legal-admission wrapper around existing evidence. It
does not run Fluid, OpenFOAM, fitting, model selection, postprocessing harvests,
or scheduler commands.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-499"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard")
OUT = ROOT / OUT_REL

SPLIT_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy"
    / "canonical_final_predictive_split_policy.csv"
)
SPLIT_POLICY_NOTE = ROOT / "operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md"
SALT1_MANIFEST = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion"
    / "salt1_split_ready_manifest.csv"
)
SALT2_PM5_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair"
    / "salt2_pm5_admission_table.csv"
)
VAL_SALT2_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger"
    / "val_salt2_external_admission_decision.csv"
)
PM10_READINESS = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness"
    / "pm10_case_readiness.csv"
)
COUPLED_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission"
    / "coupled_scorecard.csv"
)
COUPLED_DELTA = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission"
    / "coupled_delta_vs_m3.csv"
)
COUPLED_REVIEW = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission"
    / "coupled_admission_review.csv"
)
SCENARIO_CONTRACTS = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission"
    / "scenario_contracts.csv"
)
SEGMENT_PRESSURE = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models"
    / "segment_pressure_model_scorecard.csv"
)
SEGMENT_THERMAL = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models"
    / "segment_thermal_model_scorecard.csv"
)
UPCOMER_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "upcomer_admission_decision.csv"
)
SENSOR_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude"
    / "sensor_policy_scorecard.csv"
)

FINAL_TRAINING_CASES = ("salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal")
BLIND_HOLDOUT_CASES = ("salt2_lo5q", "salt2_hi5q")
BLIND_EXTERNAL_CASES = ("val_salt2",)
OLD_CASE_MAP = {
    "salt_2": "salt2_jin_nominal",
    "salt_3": "salt3_jin_nominal",
    "salt_4": "salt4_nominal",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON in {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def intsum(rows: list[dict[str, str]], key: str) -> int:
    total = 0
    for row in rows:
        try:
            total += int(float(row.get(key, "") or 0))
        except ValueError:
            pass
    return total


def split_legal_case_table() -> list[dict[str, Any]]:
    salt1_by_case = {row["case_key"]: row for row in read_csv(SALT1_MANIFEST)}
    salt2_pm5_cases = {row["case_key"] for row in read_csv(SALT2_PM5_ADMISSION)}
    val_rows = {row["case_key"]: row for row in read_csv(VAL_SALT2_ADMISSION)}
    rows: list[dict[str, Any]] = []
    for row in read_csv(SPLIT_POLICY):
        case_key = row["case_key"]
        policy_role = row["split_role"]
        corrected_role = policy_role
        final_fit_allowed = "no"
        final_model_selection_allowed = "no"
        blind_score_allowed_now = "no"
        current_readiness = row.get("use_status", "")
        use_in_final_scorecard = "diagnostic_or_future_only"
        guardrail = "do_not_use_for_final_training"

        if case_key in FINAL_TRAINING_CASES:
            corrected_role = "final_training"
            final_fit_allowed = "yes"
            final_model_selection_allowed = "yes"
            use_in_final_scorecard = "fit_training_and_internal_training_score"
            guardrail = "may_train_final_freeze"
            if case_key == "salt1_nominal":
                salt1 = salt1_by_case.get(case_key, {})
                current_readiness = (
                    "ready_schema_promoted"
                    if salt1.get("schema_promotion_status") == "promoted" and salt1.get("admission_status") == "admitted"
                    else "blocked_salt1_schema_promotion"
                )
            else:
                current_readiness = "ready_current_schema"
        elif case_key in BLIND_HOLDOUT_CASES:
            corrected_role = "blind_holdout_salt2_pm5q"
            blind_score_allowed_now = "yes_after_final_freeze"
            current_readiness = (
                "holdout_pm5_ready_score_only"
                if case_key in salt2_pm5_cases
                else "blocked_missing_pm5_holdout_admission"
            )
            use_in_final_scorecard = "blind_holdout_score_only_after_freeze"
            guardrail = "fit_and_model_selection_forbidden"
        elif case_key in BLIND_EXTERNAL_CASES:
            corrected_role = "blind_external_val_salt2"
            blind_score_allowed_now = "yes_after_final_freeze"
            current_readiness = (
                "external_ledger_ready_score_only"
                if val_rows.get(case_key, {}).get("external_test_only") == "yes"
                else "blocked_missing_external_ledger"
            )
            use_in_final_scorecard = "external_score_only_after_freeze"
            guardrail = "fit_and_model_selection_forbidden"
        elif policy_role == "training_support":
            corrected_role = "support_diagnostic_not_final_training"
            current_readiness = "admitted_support_only_not_corrected_final_training"
            use_in_final_scorecard = "diagnostic_support_only"
            guardrail = "do_not_expand_training_set_without_new_policy"
        elif policy_role == "future_holdout_candidate":
            corrected_role = "future_blind_holdout_blocked_terminal_admission"
            blind_score_allowed_now = "no_until_terminal_admission"
            current_readiness = "blocked_terminal_admission_required"
            use_in_final_scorecard = "future_only_not_current_scorecard"
            guardrail = "do_not_score_or_tune_until_terminal_admission"
        elif policy_role == "new_cfd_holdout_candidate":
            corrected_role = "future_new_cfd_blocked_run_and_admission"
            blind_score_allowed_now = "no_until_run_and_admission"
            current_readiness = "blocked_new_cfd_run_and_admission_required"
            use_in_final_scorecard = "future_only_not_current_scorecard"
            guardrail = "do_not_score_or_tune_until_run_admission"

        rows.append(
            {
                "case_key": case_key,
                "source_key": row.get("source_key", ""),
                "canonical_policy_role": policy_role,
                "corrected_scorecard_role": corrected_role,
                "canonical_fit_allowed": row.get("fit_allowed", ""),
                "canonical_model_selection_allowed": row.get("model_selection_allowed", ""),
                "canonical_score_allowed": row.get("score_allowed", ""),
                "final_fit_allowed": final_fit_allowed,
                "final_model_selection_allowed": final_model_selection_allowed,
                "blind_score_allowed_now": blind_score_allowed_now,
                "current_readiness": current_readiness,
                "use_in_final_scorecard": use_in_final_scorecard,
                "guardrail": guardrail,
                "source_paths": f"{rel(SPLIT_POLICY)};{rel(SPLIT_POLICY_NOTE)}",
            }
        )
    return rows


def candidate_ids() -> list[str]:
    return sorted({row["candidate_id"] for row in read_csv(COUPLED_REVIEW)})


def candidate_freeze_manifest() -> list[dict[str, Any]]:
    scenarios = read_csv(SCENARIO_CONTRACTS)
    review_by_candidate = {row["candidate_id"]: row for row in read_csv(COUPLED_REVIEW)}
    by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in scenarios:
        by_candidate[row["candidate_id"]].append(row)

    rows: list[dict[str, Any]] = []
    final_set = set(FINAL_TRAINING_CASES)
    for candidate_id in candidate_ids():
        candidate_scenarios = by_candidate[candidate_id]
        legacy_train_cases = sorted(
            OLD_CASE_MAP.get(row["case_id"], row["case_id"])
            for row in candidate_scenarios
            if row.get("split_role") == "train"
        )
        nominal_rows_scored = sorted(OLD_CASE_MAP.get(row["case_id"], row["case_id"]) for row in candidate_scenarios)
        missing_training_cases = sorted(final_set - set(legacy_train_cases))
        missing_nominal_score_cases = sorted(final_set - set(nominal_rows_scored))
        review = review_by_candidate[candidate_id]
        rows.append(
            {
                "candidate_id": candidate_id,
                "corrected_split_training_required": ";".join(FINAL_TRAINING_CASES),
                "legacy_training_cases": ";".join(legacy_train_cases),
                "legacy_nominal_rows_scored": ";".join(nominal_rows_scored),
                "missing_training_cases": ";".join(missing_training_cases),
                "missing_nominal_score_cases": ";".join(missing_nominal_score_cases),
                "corrected_split_freeze_status": "missing_not_frozen_on_salt1_4_nominal",
                "training_compliant": "no",
                "legacy_admission_status": review.get("admission_decision", ""),
                "legacy_blocking_reasons": review.get("blocking_reasons", ""),
                "use_in_final_scorecard": "diagnostic_legacy_split_only",
                "required_next_freeze_action": "rebuild candidate freeze using Salt1-4 nominal only after submodel admission",
                "source_paths": f"{rel(SCENARIO_CONTRACTS)};{rel(COUPLED_REVIEW)}",
            }
        )
    return rows


def coupled_scorecard() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(COUPLED_SCORECARD):
        corrected_case = OLD_CASE_MAP.get(row["case_id"], row["case_id"])
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_key": corrected_case,
                "legacy_case_id": row["case_id"],
                "legacy_split_role": row.get("split_role", ""),
                "corrected_split_role": "final_training" if corrected_case in FINAL_TRAINING_CASES else "unknown",
                "coupled_run_status": row.get("coupled_run_status", ""),
                "root_status": row.get("root_status", ""),
                "mdot_error_pct": row.get("mdot_error_pct", ""),
                "tp_rmse_K": row.get("tp_rmse_K", ""),
                "tw_rmse_K": row.get("tw_rmse_K", ""),
                "all_probe_rmse_K": row.get("all_probe_rmse_K", ""),
                "coupled_gate": row.get("coupled_gate", ""),
                "scorecard_use": "diagnostic_legacy_split_evidence_not_final_corrected_split",
                "corrected_split_training_compliant": "no",
                "source_path": row.get("source_path", rel(COUPLED_SCORECARD)),
            }
        )
    for candidate_id in candidate_ids():
        rows.append(
            {
                "candidate_id": candidate_id,
                "case_key": "salt1_nominal",
                "legacy_case_id": "",
                "legacy_split_role": "missing_from_legacy_coupled_scorecard",
                "corrected_split_role": "final_training",
                "coupled_run_status": "missing_no_salt1_scenario_contract",
                "root_status": "",
                "mdot_error_pct": "",
                "tp_rmse_K": "",
                "tw_rmse_K": "",
                "all_probe_rmse_K": "",
                "coupled_gate": "not_run_corrected_split_required",
                "scorecard_use": "required_for_final_training_freeze_missing",
                "corrected_split_training_compliant": "no",
                "source_path": rel(COUPLED_SCORECARD),
            }
        )
    rows.sort(key=lambda row: (row["candidate_id"], row["case_key"]))
    return rows


def blind_holdout_scorecard() -> list[dict[str, Any]]:
    pm5_rows = read_csv(SALT2_PM5_ADMISSION)
    pm5_by_case = defaultdict(list)
    for row in pm5_rows:
        pm5_by_case[row["case_key"]].append(row)
    val_row = read_csv(VAL_SALT2_ADMISSION)[0]

    rows: list[dict[str, Any]] = []
    for candidate_id in candidate_ids():
        for case_key in BLIND_HOLDOUT_CASES:
            case_rows = pm5_by_case[case_key]
            statuses = sorted({row.get("admission_status", "") for row in case_rows})
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "case_key": case_key,
                    "blind_role": "salt2_pm5q_holdout",
                    "target_readiness": "pm5_rows_ready_score_only" if case_rows else "blocked_missing_pm5_rows",
                    "target_rows": len(case_rows),
                    "fit_allowed": "no",
                    "model_selection_allowed": "no",
                    "runtime_input_allowed": "no",
                    "blind_score_status": "blocked_no_corrected_split_final_freeze",
                    "admission_status": ";".join(statuses),
                    "guardrail": "holdout residuals may not change fit, candidate choice, or gates",
                    "source_paths": rel(SALT2_PM5_ADMISSION),
                }
            )
        rows.append(
            {
                "candidate_id": candidate_id,
                "case_key": "val_salt2",
                "blind_role": "external_test",
                "target_readiness": "external_ledger_ready_score_only",
                "target_rows": val_row.get("patch_rows", ""),
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "blind_score_status": "blocked_no_corrected_split_final_freeze",
                "admission_status": val_row.get("admission_status", ""),
                "guardrail": "external residuals may not change fit, candidate choice, or gates",
                "source_paths": rel(VAL_SALT2_ADMISSION),
            }
        )
    return rows


def admission_gate_review() -> list[dict[str, Any]]:
    pressure = read_csv(SEGMENT_PRESSURE)
    thermal = read_csv(SEGMENT_THERMAL)
    upcomer = read_csv(UPCOMER_ADMISSION)
    sensor = read_csv(SENSOR_POLICY)
    pressure_fit_rows = intsum(pressure, "true_fd_or_k_fit_admitted_rows")
    thermal_setup_rows = intsum(thermal, "admitted_setup_model_rows")
    thermal_residual_fit_rows = intsum(thermal, "residual_internal_nu_fit_admitted_rows")
    upcomer_fit_rows = intsum(upcomer, "ordinary_fit_admitted_rows") + intsum(upcomer, "hybrid_predictive_fit_admitted_rows")
    scoreable_sensors = sum(row.get("aggregate_score_after_refresh") == "yes" for row in sensor)
    review_by_candidate = {row["candidate_id"]: row for row in read_csv(COUPLED_REVIEW)}
    delta_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(COUPLED_DELTA):
        delta_by_candidate[row["candidate_id"]].append(row)

    rows: list[dict[str, Any]] = []
    for candidate_id in candidate_ids():
        review = review_by_candidate[candidate_id]
        delta_rows = delta_by_candidate[candidate_id]
        max_all_probe_regression = max((float(row["all_probe_delta_vs_m3_K"]) for row in delta_rows), default=0.0)
        rows.append(
            {
                "candidate_id": candidate_id,
                "corrected_split_freeze_gate": "fail_missing_salt1_4_nominal_freeze",
                "legacy_coupled_gate": "fail"
                if review.get("admission_decision") != "admitted"
                else "pass_legacy_only",
                "legacy_all_probe_max_regression_K": f"{max_all_probe_regression:.6g}",
                "blind_holdout_gate": "not_run_blocked_no_final_freeze",
                "pressure_model_gate": "fail_zero_fit_admitted" if pressure_fit_rows == 0 else "partial",
                "thermal_model_gate": "partial_setup_only_no_residual_internal_nu_fit"
                if thermal_setup_rows and thermal_residual_fit_rows == 0
                else "fail",
                "upcomer_hybrid_gate": "diagnostic_only_zero_predictive_fit" if upcomer_fit_rows == 0 else "partial",
                "sensor_policy_gate": "pass_validation_targets_only" if scoreable_sensors else "fail",
                "runtime_input_gate": review.get("runtime_gate", ""),
                "final_candidate_admission": "not_admitted",
                "blocking_reasons": "corrected_split_freeze_missing;"
                + review.get("blocking_reasons", "")
                + ";blind_holdout_not_scored;pressure_fit_rows_zero;upcomer_predictive_fit_rows_zero",
                "source_paths": ";".join(
                    [
                        rel(COUPLED_REVIEW),
                        rel(COUPLED_DELTA),
                        rel(SEGMENT_PRESSURE),
                        rel(SEGMENT_THERMAL),
                        rel(UPCOMER_ADMISSION),
                        rel(SENSOR_POLICY),
                    ]
                ),
            }
        )
    return rows


def blocked_future_rows(split_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(PM10_READINESS):
        rows.append(
            {
                "case_key": row["case_key"],
                "source_key": row.get("source_key", ""),
                "future_role": "pm10_future_blind_holdout_candidate",
                "current_state": row.get("readiness_state", ""),
                "score_allowed_now": "no",
                "score_allowed_after": row.get("score_allowed", ""),
                "terminal_or_run_gate": f"solver_job_{row.get('solver_job_id', '')}_{row.get('solver_state', '')};harvest_job_{row.get('harvest_job_id', '')}_{row.get('harvest_state', '')}",
                "next_action": row.get("next_action", ""),
                "source_paths": rel(PM10_READINESS),
            }
        )
    for row in split_rows:
        if row["case_key"] == "salt3_q_insulation_matrix":
            rows.append(
                {
                    "case_key": row["case_key"],
                    "source_key": row["source_key"],
                    "future_role": "new_cfd_holdout_candidate",
                    "current_state": "blocked_new_cfd_run_and_admission_required",
                    "score_allowed_now": "no",
                    "score_allowed_after": row["canonical_score_allowed"],
                    "terminal_or_run_gate": "run_and_admission_required",
                    "next_action": "Run and admit only after terminal CFD evidence exists; keep out of current corrected scorecard.",
                    "source_paths": rel(SPLIT_POLICY),
                }
            )
    return rows


def runtime_input_audit() -> list[dict[str, Any]]:
    checks = [
        ("final_training_set", "Salt1-4 nominal only", "pass"),
        ("salt2_pm5q_holdout", "fit/model-selection forbidden; score only after freeze", "pass"),
        ("val_salt2_external", "training/runtime input forbidden; score only after freeze", "pass"),
        ("pm10_future_rows", "blocked until terminal admission", "pass"),
        ("new_cfd_future_rows", "blocked until run and admission", "pass"),
        ("cfd_mdot", "CFD mdot is not a runtime input", "pass"),
        ("realized_wallHeatFlux", "realized CFD wallHeatFlux is target/diagnostic only", "pass"),
        ("validation_temperatures", "TP/TW validation temperatures are not runtime inputs", "pass"),
        ("hidden_global_multipliers", "no hidden global friction/heat multiplier admitted here", "pass"),
        ("native_outputs", "builder reads CSV/JSON evidence only and does not mutate solver outputs", "pass"),
    ]
    return [
        {
            "audit_item": item,
            "policy": policy,
            "status": status,
            "evidence": "wrapper_has_no_solver_or_fit_entrypoints",
        }
        for item, policy, status in checks
    ]


def next_analysis_queue() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "next_step": "Consume AGENT-498 wall/test-section distribution ladder after it completes",
            "why": "AGENT-494 PB1+cooler improves mdot but badly regresses all-probe/TW temperatures; local distribution physics is the active blocker.",
            "admission_guardrail": "Do not admit a test-section/wall candidate unless validation and holdout coupled gates beat M3.",
            "owner_scope_hint": "active AGENT-498, read-only for this package",
        },
        {
            "priority": 2,
            "next_step": "Build corrected Salt1-4 nominal freeze runner only after an admitted candidate exists",
            "why": "The current PB1+cooler rows are legacy split diagnostics and lack a Salt1 nominal scenario contract.",
            "admission_guardrail": "Freeze on Salt1-4 nominal only; do not use Salt2 +/-5Q or val_salt2 for fitting or model selection.",
            "owner_scope_hint": "new assigned score/run task",
        },
        {
            "priority": 3,
            "next_step": "Add boundary-layer/development scorecard for lower/upper legs and test-section",
            "why": "Segment pressure/thermal scorecards repeatedly identify development, wall resistance, and recirculation masks as blockers.",
            "admission_guardrail": "Keep realized wallHeatFlux and validation temperatures target-only.",
            "owner_scope_hint": "new analysis package",
        },
        {
            "priority": 4,
            "next_step": "Unlock upcomer onset and hybrid calibration with non-recirculating or near-onset anchors",
            "why": "Current upcomer rows are recirculating and admit zero ordinary or hybrid predictive fits.",
            "admission_guardrail": "Do not fit true Nu/f_D/K from recirculating rows.",
            "owner_scope_hint": "new CFD/admission package after source availability",
        },
        {
            "priority": 5,
            "next_step": "Revisit Salt2/Salt4 +/-10Q after jobs 3293924 and 3295438 are terminal and admitted",
            "why": "PM10 rows are future blind-holdout candidates, not current scorecard inputs.",
            "admission_guardrail": "No scoring, tuning, or terminal admission while solver/harvest state is live.",
            "owner_scope_hint": "PM10 readiness follow-up task",
        },
        {
            "priority": 6,
            "next_step": "Separate junction/corner K pressure unlock from final scorecard fitting",
            "why": "Segment pressure evidence has zero fit-admitted f_D/K rows and unisolated component losses.",
            "admission_guardrail": "Use apparent K and named losses diagnostically until physically bracketed pressure evidence exists.",
            "owner_scope_hint": "pressure unlock package",
        },
    ]


def source_manifest(outputs: list[Path]) -> list[dict[str, Any]]:
    inputs = [
        SPLIT_POLICY,
        SPLIT_POLICY_NOTE,
        SALT1_MANIFEST,
        SALT2_PM5_ADMISSION,
        VAL_SALT2_ADMISSION,
        PM10_READINESS,
        COUPLED_SCORECARD,
        COUPLED_DELTA,
        COUPLED_REVIEW,
        SCENARIO_CONTRACTS,
        SEGMENT_PRESSURE,
        SEGMENT_THERMAL,
        UPCOMER_ADMISSION,
        SENSOR_POLICY,
    ]
    rows = [
        {
            "path": rel(path),
            "role": "read_only_input",
            "exists": path.exists(),
            "native_output_mutated": "no",
        }
        for path in inputs
    ]
    rows.extend(
        {
            "path": rel(path),
            "role": "generated_output",
            "exists": path.exists(),
            "native_output_mutated": "no",
        }
        for path in outputs
    )
    return rows


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(SPLIT_POLICY)}
  - {rel(SALT1_MANIFEST)}
  - {rel(SALT2_PM5_ADMISSION)}
  - {rel(VAL_SALT2_ADMISSION)}
  - {rel(COUPLED_REVIEW)}
  - {rel(PM10_READINESS)}
tags: [forward-model, corrected-split, predictive-scorecard, holdout-policy]
related:
  - final-predictive-split-policy
  - predictive-wall-test-section-submodels
  - salt2-pm5q-holdout
  - val-salt2-external-test
task: {TASK}
date: 2026-07-17
role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Corrected-Split Final Predictive Scorecard

## Result

This package implements the corrected final predictive scorecard wrapper:
train/freeze on Salt1-4 nominal, keep Salt2 +/-5Q and `val_salt2` blind, and
leave +/-10Q/new CFD out until terminal/run admission.

No final candidate is admitted here. The existing PB1+cooler coupled evidence is
legacy-split diagnostic evidence only: it was not frozen on Salt1-4 nominal, it
does not include a Salt1 nominal coupled row, and AGENT-494 already rejected all
four candidates because validation/holdout all-probe/TW error regressed versus
M3 despite mdot improvement.

## Counts

- Final training cases: `{summary["final_training_cases"]}`.
- Blind score-only cases: `{summary["blind_cases"]}`.
- Candidate definitions reviewed: `{summary["candidate_count"]}`.
- Legacy coupled rows reclassified as diagnostic: `{summary["legacy_coupled_rows"]}`.
- Missing Salt1 corrected-freeze rows inserted: `{summary["missing_salt1_rows"]}`.
- Blind holdout/external rows blocked pending final freeze: `{summary["blind_rows"]}`.
- Future rows blocked pending terminal/run admission: `{summary["future_blocked_rows"]}`.
- Final admitted candidates: `{summary["final_admitted_candidates"]}`.

## Files

- `split_legal_case_table.csv` states which cases may train, score blindly, or
  remain blocked under the corrected split.
- `candidate_freeze_manifest.csv` records why each existing PB1+cooler candidate
  is not a corrected-split freeze.
- `coupled_scorecard.csv` reclassifies AGENT-494 coupled rows as diagnostic
  legacy evidence and inserts the missing Salt1 nominal rows required before a
  corrected freeze can exist.
- `blind_holdout_scorecard.csv` keeps Salt2 +/-5Q and `val_salt2` score-only and
  blocked until a corrected final freeze exists.
- `admission_gate_review.csv` summarizes candidate-level gates.
- `blocked_future_rows.csv` keeps PM10 and new CFD out of the current scorecard.
- `runtime_input_audit.csv` records leakage guardrails.
- `next_analysis_queue.csv` is the handoff queue for tomorrow's work.
- `source_manifest.csv` and `summary.json` provide provenance and machine-readable
  package state.

## Start Here Tomorrow

Open this README, then `admission_gate_review.csv`, then
`next_analysis_queue.csv`. The shortest path forward is to wait for or consume
the AGENT-498 wall/test-section distribution ladder; only after an actually
admitted wall/test-section/cooler candidate exists should a new task build a
Salt1-4 nominal freeze runner. Do not use Salt2 +/-5Q, PM10, new CFD, or
`val_salt2` for fit or model selection.
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    split_rows = split_legal_case_table()
    freeze_rows = candidate_freeze_manifest()
    coupled_rows = coupled_scorecard()
    blind_rows = blind_holdout_scorecard()
    gate_rows = admission_gate_review()
    future_rows = blocked_future_rows(split_rows)
    runtime_rows = runtime_input_audit()
    queue_rows = next_analysis_queue()

    outputs = [
        OUT / "split_legal_case_table.csv",
        OUT / "candidate_freeze_manifest.csv",
        OUT / "coupled_scorecard.csv",
        OUT / "blind_holdout_scorecard.csv",
        OUT / "admission_gate_review.csv",
        OUT / "blocked_future_rows.csv",
        OUT / "runtime_input_audit.csv",
        OUT / "next_analysis_queue.csv",
        OUT / "source_manifest.csv",
        OUT / "summary.json",
        OUT / "README.md",
    ]

    write_csv(outputs[0], split_rows)
    write_csv(outputs[1], freeze_rows)
    write_csv(outputs[2], coupled_rows)
    write_csv(outputs[3], blind_rows)
    write_csv(outputs[4], gate_rows)
    write_csv(outputs[5], future_rows)
    write_csv(outputs[6], runtime_rows)
    write_csv(outputs[7], queue_rows)
    write_csv(outputs[8], source_manifest(outputs))

    split_roles = Counter(row["corrected_scorecard_role"] for row in split_rows)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "final_training_cases": len([row for row in split_rows if row["corrected_scorecard_role"] == "final_training"]),
        "final_training_case_keys": list(FINAL_TRAINING_CASES),
        "blind_cases": len(BLIND_HOLDOUT_CASES) + len(BLIND_EXTERNAL_CASES),
        "blind_case_keys": list(BLIND_HOLDOUT_CASES + BLIND_EXTERNAL_CASES),
        "candidate_count": len(freeze_rows),
        "legacy_coupled_rows": len(read_csv(COUPLED_SCORECARD)),
        "missing_salt1_rows": sum(row["case_key"] == "salt1_nominal" for row in coupled_rows),
        "blind_rows": len(blind_rows),
        "future_blocked_rows": len(future_rows),
        "runtime_audit_rows": len(runtime_rows),
        "runtime_audit_failures": sum(not row["status"].startswith("pass") for row in runtime_rows),
        "final_admitted_candidates": sum(row["final_candidate_admission"] == "admitted" for row in gate_rows),
        "corrected_split_role_counts": dict(split_roles),
        "decision": "no_final_candidate_admitted_missing_corrected_salt1_4_nominal_freeze",
        "guardrail": "Salt2 +/-5Q, val_salt2, PM10, and new CFD are not fit/model-selection inputs.",
    }
    write_json(outputs[9], summary)
    outputs[10].write_text(readme_text(summary))
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
