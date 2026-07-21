#!/usr/bin/env python3
"""Build the final predictive scorecard shell.

The shell is intentionally non-scoring. It defines the scorecard rows, metrics,
release gates, and prediction-join placeholders for the corrected split:

* train/freeze only on Salt1-4 nominal;
* score Salt2 +/-5Q and val_salt2 only after a corrected final freeze exists;
* keep future +/-10Q and new CFD rows blocked until terminal/run admission.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-509"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell")
OUT = ROOT / OUT_REL

AGENT499_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard"
SPLIT_LEGAL = AGENT499_DIR / "split_legal_case_table.csv"
CANDIDATE_FREEZE = AGENT499_DIR / "candidate_freeze_manifest.csv"
AGENT499_SUMMARY = AGENT499_DIR / "summary.json"
BLOCKED_FUTURE = AGENT499_DIR / "blocked_future_rows.csv"

SALT2_PM5 = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair"
    / "salt2_pm5_admission_table.csv"
)
VAL_EXTERNAL_DIR = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress"
)
VAL_EXTERNAL_SUMMARY = VAL_EXTERNAL_DIR / "summary.json"
VAL_TARGETS = VAL_EXTERNAL_DIR / "val_salt2_external_score_targets.csv"
VAL_JOIN_CONTRACT = VAL_EXTERNAL_DIR / "val_salt2_prediction_join_contract.csv"
PM10_WATCH = VAL_EXTERNAL_DIR / "pm10_holdout_admission_watch.csv"
WALL_DISTRIBUTION_SUMMARY = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder" / "summary.json"
)
SOURCE_PROPERTY_DIR = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward"
SOURCE_PROPERTY_LABELS = SOURCE_PROPERTY_DIR / "source_property_label_contract.csv"
SOURCE_PROPERTY_COVERAGE = SOURCE_PROPERTY_DIR / "final_scorecard_case_coverage_audit.csv"
SOURCE_PROPERTY_CONTRACT = SOURCE_PROPERTY_DIR / "future_scorecard_label_contract.csv"
SOURCE_PROPERTY_REFRESH_DIR = (
    ROOT / "work_products/2026-07/2026-07-20/2026-07-20_final_scorecard_source_property_refresh"
)
SOURCE_PROPERTY_REFRESH_LABELS = SOURCE_PROPERTY_REFRESH_DIR / "refreshed_final_scorecard_source_property_labels.csv"
SOURCE_ENVELOPE_RESOLUTION_DIR = (
    ROOT / "work_products/2026-07/2026-07-20/2026-07-20_final_scorecard_source_envelope_resolution"
)
SOURCE_PROPERTY_RESOLUTION_POLICY = SOURCE_ENVELOPE_RESOLUTION_DIR / "scorecard_source_property_resolution_policy.csv"

FINAL_TRAINING_CASES = ("salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal")
BLIND_HOLDOUT_CASES = ("salt2_lo5q", "salt2_hi5q")
BLIND_EXTERNAL_CASES = ("val_salt2",)
FUTURE_PM10_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q")
FUTURE_NEW_CFD_CASES = ("salt3_q_insulation_matrix",)
PREFERRED_PROPERTY_MODE = "jin_viscosity_parida_cp_santini_k"
REQUIRED_SOURCE_PROPERTY_COLUMNS = (
    "case_id",
    "section_or_segment",
    "property_mode",
    "property_mode_status",
    "property_sensitivity_label",
    "source_validity_envelope_status",
    "source_overlap_status",
    "source_use_category",
    "provenance_author_title",
    "fit_use_status",
)

METRIC_CONTRACTS = [
    {
        "metric_id": "loop_mdot_abs_error_pct",
        "metric_family": "hydraulic_global",
        "target_lane": "case_scalar",
        "required_prediction_fields": "predicted_mdot_kg_s;prediction_model_id",
        "target_source_status": "training_rows_need_nominal_targets;holdout_rows_need_frozen_predictions",
        "primary_score_aggregate": "yes",
        "lower_is_better": "yes",
        "units": "percent",
        "allowed_on_train": "yes",
        "allowed_on_blind_holdout": "yes_after_final_freeze",
        "allowed_on_external": "yes_after_final_freeze",
        "allowed_on_future": "yes_after_terminal_or_run_admission_and_final_freeze",
        "notes": "Global loop-flow score; mdot must be predicted, not supplied from CFD at runtime.",
    },
    {
        "metric_id": "all_probe_temperature_rmse_K",
        "metric_family": "thermal_global",
        "target_lane": "sensor_temperature",
        "required_prediction_fields": "predicted_temperature_K;prediction_model_id",
        "target_source_status": "val_salt2_has_sensor_targets;nominal/pm5 target joins pending final prediction artifact",
        "primary_score_aggregate": "yes",
        "lower_is_better": "yes",
        "units": "K",
        "allowed_on_train": "yes",
        "allowed_on_blind_holdout": "yes_after_final_freeze",
        "allowed_on_external": "yes_after_final_freeze",
        "allowed_on_future": "yes_after_terminal_or_run_admission_and_final_freeze",
        "notes": "Aggregate policy-allowed TP/TW sensors only; excluded sensors remain out of aggregate.",
    },
    {
        "metric_id": "tp_sensor_rmse_K",
        "metric_family": "thermal_sensor",
        "target_lane": "sensor_temperature",
        "required_prediction_fields": "predicted_temperature_K;prediction_model_id",
        "target_source_status": "val_salt2_has_policy_filtered_TP_targets",
        "primary_score_aggregate": "yes",
        "lower_is_better": "yes",
        "units": "K",
        "allowed_on_train": "yes",
        "allowed_on_blind_holdout": "yes_after_final_freeze",
        "allowed_on_external": "yes_after_final_freeze",
        "allowed_on_future": "yes_after_terminal_or_run_admission_and_final_freeze",
        "notes": "Fluid temperature probe score; validation temperatures are never runtime inputs.",
    },
    {
        "metric_id": "tw_sensor_rmse_K",
        "metric_family": "thermal_wall",
        "target_lane": "sensor_temperature",
        "required_prediction_fields": "predicted_temperature_K;prediction_model_id",
        "target_source_status": "val_salt2_has_policy_filtered_TW_targets",
        "primary_score_aggregate": "yes",
        "lower_is_better": "yes",
        "units": "K",
        "allowed_on_train": "yes",
        "allowed_on_blind_holdout": "yes_after_final_freeze",
        "allowed_on_external": "yes_after_final_freeze",
        "allowed_on_future": "yes_after_terminal_or_run_admission_and_final_freeze",
        "notes": "Wall-temperature probe score; wall targets are post-solve validation only.",
    },
    {
        "metric_id": "pressure_streamwise_rmse_Pa",
        "metric_family": "hydraulic_distribution",
        "target_lane": "pressure_streamwise_map",
        "required_prediction_fields": "predicted_static_p_Pa;predicted_p_rgh_Pa;prediction_model_id",
        "target_source_status": "val_salt2_has_30_pressure_targets;train/holdout pressure joins pending",
        "primary_score_aggregate": "yes",
        "lower_is_better": "yes",
        "units": "Pa",
        "allowed_on_train": "yes",
        "allowed_on_blind_holdout": "yes_after_final_freeze",
        "allowed_on_external": "yes_after_final_freeze",
        "allowed_on_future": "yes_after_terminal_or_run_admission_and_final_freeze",
        "notes": "Loop-order pressure map score; no component K fitting from blind rows.",
    },
    {
        "metric_id": "thermal_section_heat_abs_residual_W",
        "metric_family": "thermal_source_sink",
        "target_lane": "thermal_section_and_junction",
        "required_prediction_fields": "predicted_heat_W;prediction_model_id",
        "target_source_status": "val_salt2_has_section_and_junction_targets",
        "primary_score_aggregate": "diagnostic_secondary",
        "lower_is_better": "yes",
        "units": "W",
        "allowed_on_train": "yes",
        "allowed_on_blind_holdout": "yes_after_final_freeze",
        "allowed_on_external": "yes_after_final_freeze",
        "allowed_on_future": "yes_after_terminal_or_run_admission_and_final_freeze",
        "notes": "Named source/sink score; realized wallHeatFlux is target evidence, not a runtime input.",
    },
    {
        "metric_id": "pm5_upcomer_recirculation_diagnostic",
        "metric_family": "recirculation_diagnostic",
        "target_lane": "pm5_upcomer_planes",
        "required_prediction_fields": "predicted_recirculation_class;prediction_model_id",
        "target_source_status": "salt2_pm5_has_holdout_diagnostic_rows",
        "primary_score_aggregate": "diagnostic_only",
        "lower_is_better": "not_applicable",
        "units": "categorical",
        "allowed_on_train": "no",
        "allowed_on_blind_holdout": "yes_after_final_freeze_diagnostic_only",
        "allowed_on_external": "no",
        "allowed_on_future": "yes_after_terminal_or_run_admission_diagnostic_only",
        "notes": "PM5 rows may diagnose regime transfer; they cannot fit ordinary Nu/f_D/K.",
    },
]


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


def unique_join(values: list[str]) -> str:
    seen: list[str] = []
    for value in values:
        for item in str(value).split(";"):
            item = item.strip()
            if item and item not in seen:
                seen.append(item)
    return ";".join(seen)


def source_property_coverage_by_case() -> dict[str, dict[str, str]]:
    return {row["case_key"]: row for row in read_csv(SOURCE_PROPERTY_COVERAGE)}


def source_property_labels_by_case() -> dict[str, list[dict[str, str]]]:
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(SOURCE_PROPERTY_LABELS):
        if row.get("property_mode") == PREFERRED_PROPERTY_MODE:
            by_case[row["case_id"]].append(row)
    return by_case


def refreshed_source_property_labels_by_case() -> dict[str, dict[str, str]]:
    if not SOURCE_PROPERTY_REFRESH_LABELS.exists():
        return {}
    return {row["case_key"]: row for row in read_csv(SOURCE_PROPERTY_REFRESH_LABELS)}


def source_property_resolution_policy_by_case() -> dict[str, dict[str, str]]:
    if not SOURCE_PROPERTY_RESOLUTION_POLICY.exists():
        return {}
    return {row["case_key"]: row for row in read_csv(SOURCE_PROPERTY_RESOLUTION_POLICY)}


def blocked_source_property_labels(case_key: str, coverage_row: dict[str, str], section_or_segment: str) -> dict[str, str]:
    reason = coverage_row.get("coverage_reason", "source/property coverage missing")
    return {
        "case_id": coverage_row.get("normalized_case_id", case_key),
        "section_or_segment": section_or_segment,
        "property_mode": "source_property_refresh_required",
        "property_mode_status": "source_or_property_gate_missing",
        "property_sensitivity_label": "source_or_property_gate_missing",
        "source_validity_envelope_status": "source_or_property_gate_missing",
        "source_overlap_status": "source_or_property_gate_missing",
        "source_use_category": "blocked_or_diagnostic_until_refresh",
        "provenance_author_title": "AGENT-538 coverage audit; row-specific refresh required",
        "fit_use_status": "blocked_or_diagnostic_until_source_property_labels_present",
        "source_property_label_coverage": coverage_row.get("source_property_label_coverage", "source_or_property_gate_missing"),
        "source_property_gate_status": "blocked_source_or_property_gate_missing",
        "source_property_gate_reason": reason,
    }


def refreshed_source_property_labels(row: dict[str, str], section_or_segment: str) -> dict[str, str]:
    return {
        "case_id": row["normalized_case_id"],
        "section_or_segment": section_or_segment,
        "property_mode": row["property_mode"],
        "property_mode_status": row["property_mode_status"],
        "property_sensitivity_label": row["property_sensitivity_label"],
        "source_validity_envelope_status": row["source_validity_envelope_status"],
        "source_overlap_status": row["source_overlap_status"],
        "source_use_category": row["source_use_category"],
        "provenance_author_title": row["provenance_author_title"],
        "fit_use_status": row["fit_use_status"],
        "source_property_label_coverage": row["source_property_label_coverage"],
        "source_property_gate_status": row["source_property_gate_status"],
        "source_property_gate_reason": row["source_property_gate_reason"],
    }


def apply_source_property_resolution_policy(
    labels: dict[str, str],
    policy_row: dict[str, str] | None,
) -> dict[str, str]:
    if not policy_row:
        return labels

    out = dict(labels)
    out.update(
        {
            "property_mode": policy_row["property_mode"],
            "property_sensitivity_label": policy_row["property_sensitivity_label"],
            "source_validity_envelope_status": policy_row["source_validity_envelope_status"],
            "source_overlap_status": policy_row["source_validity_envelope_status"],
            "source_use_category": policy_row["source_use_category"],
            "provenance_author_title": policy_row["provenance_author_title"],
            "fit_use_status": "final_no_fit_source_property_resolution_policy"
            if policy_row["final_fit_allowed"] != "yes"
            else "fit_target_source_property_resolution_policy",
            "source_property_label_coverage": "source_property_resolution_policy_applied"
            if policy_row["integration_action"] == "apply_resolution_before_scorecard_regeneration"
            else labels["source_property_label_coverage"],
            "source_property_gate_status": policy_row["source_property_gate_status"],
            "source_property_gate_reason": (
                f"Final source/property resolution policy {policy_row['resolution_decision']}; "
                f"final_fit_allowed={policy_row['final_fit_allowed']}; "
                f"final_model_selection_allowed={policy_row['final_model_selection_allowed']}."
            ),
        }
    )
    return out


def aggregate_source_property_labels(
    case_key: str,
    coverage_row: dict[str, str],
    labels_by_case: dict[str, list[dict[str, str]]],
    section_or_segment: str,
) -> dict[str, str]:
    if coverage_row.get("source_property_label_coverage") != "source_property_labels_available":
        return blocked_source_property_labels(case_key, coverage_row, section_or_segment)

    normalized_case = coverage_row["normalized_case_id"]
    rows = labels_by_case.get(normalized_case, [])
    if not rows:
        return blocked_source_property_labels(case_key, coverage_row, section_or_segment)

    return {
        "case_id": normalized_case,
        "section_or_segment": section_or_segment,
        "property_mode": PREFERRED_PROPERTY_MODE,
        "property_mode_status": unique_join([row["property_mode_status"] for row in rows]),
        "property_sensitivity_label": unique_join([row["property_sensitivity_label"] for row in rows]),
        "source_validity_envelope_status": unique_join([row["source_validity_envelope_status"] for row in rows]),
        "source_overlap_status": unique_join([row["source_validity_envelope_status"] for row in rows]),
        "source_use_category": unique_join([row["source_use_categories"] for row in rows]),
        "provenance_author_title": unique_join([row["provenance_author_title"] for row in rows]),
        "fit_use_status": unique_join([row["fit_use_status"] for row in rows]),
        "source_property_label_coverage": coverage_row["source_property_label_coverage"],
        "source_property_gate_status": "pass_source_property_labels_available",
        "source_property_gate_reason": coverage_row.get("coverage_reason", "AGENT-538 labels available"),
    }


def source_property_labels_for_case(
    case_key: str,
    coverage_row: dict[str, str],
    labels_by_case: dict[str, list[dict[str, str]]],
    refreshed_by_case: dict[str, dict[str, str]],
    policy_by_case: dict[str, dict[str, str]],
    section_or_segment: str,
) -> dict[str, str]:
    if case_key in refreshed_by_case:
        labels = refreshed_source_property_labels(refreshed_by_case[case_key], section_or_segment)
    else:
        labels = aggregate_source_property_labels(case_key, coverage_row, labels_by_case, section_or_segment)
    return apply_source_property_resolution_policy(labels, policy_by_case.get(case_key))


def gate_aware_split_allowed(original_split_value: str, final_allowed_value: str) -> str:
    if original_split_value == "yes" and final_allowed_value != "yes":
        return "no_source_property_policy_blocked"
    return original_split_value


def case_partition_contract() -> list[dict[str, Any]]:
    pm5_counts = Counter(row["case_key"] for row in read_csv(SALT2_PM5))
    val_summary = read_json(VAL_EXTERNAL_SUMMARY)
    future_by_case = {row["case_key"]: row for row in read_csv(BLOCKED_FUTURE)}
    coverage_by_case = source_property_coverage_by_case()
    labels_by_case = source_property_labels_by_case()
    refreshed_by_case = refreshed_source_property_labels_by_case()
    policy_by_case = source_property_resolution_policy_by_case()

    rows: list[dict[str, Any]] = []
    for row in read_csv(SPLIT_LEGAL):
        case_key = row["case_key"]
        corrected_role = row["corrected_scorecard_role"]
        if case_key in FINAL_TRAINING_CASES:
            partition = "train_nominal"
            release_gate = "available_for_fit_after_final_freeze_builder_consumes_nominal_targets"
            shell_score_status = "training_placeholder_waiting_for_final_prediction_artifact"
            target_evidence_status = row["current_readiness"]
            score_use = "fit_and_training_internal_score"
        elif case_key in BLIND_HOLDOUT_CASES:
            partition = "blind_holdout_pm5q"
            release_gate = "requires_corrected_salt1_4_final_freeze"
            shell_score_status = "blocked_pending_corrected_final_freeze"
            target_evidence_status = f"pm5_diagnostic_rows={pm5_counts.get(case_key, 0)}"
            score_use = "holdout_score_after_freeze_no_tuning"
        elif case_key in BLIND_EXTERNAL_CASES:
            partition = "blind_external_val_salt2"
            release_gate = "requires_corrected_salt1_4_final_freeze"
            shell_score_status = "blocked_pending_corrected_final_freeze"
            target_evidence_status = (
                f"external_targets={val_summary.get('target_rows', 0)};"
                f"pressure={val_summary.get('pressure_target_rows', 0)};"
                f"thermal={val_summary.get('thermal_target_rows', 0)};"
                f"sensors={val_summary.get('sensor_target_rows', 0)}"
            )
            score_use = "external_score_after_freeze_no_tuning"
        elif case_key in FUTURE_PM10_CASES:
            partition = "future_holdout_pm10"
            release_gate = "requires_terminal_admission_and_corrected_final_freeze"
            future = future_by_case[case_key]
            shell_score_status = "blocked_pending_terminal_admission"
            target_evidence_status = future["current_state"]
            score_use = "future_holdout_after_terminal_admission_no_tuning"
        elif case_key in FUTURE_NEW_CFD_CASES:
            partition = "future_external_new_cfd"
            release_gate = "requires_new_cfd_run_admission_and_corrected_final_freeze"
            future = future_by_case[case_key]
            shell_score_status = "blocked_pending_run_and_admission"
            target_evidence_status = future["current_state"]
            score_use = "future_external_after_run_admission_no_tuning"
        else:
            partition = "excluded_support_diagnostic"
            release_gate = "not_part_of_final_scorecard_without_new_policy"
            shell_score_status = "excluded_from_final_scorecard"
            target_evidence_status = row["current_readiness"]
            score_use = "diagnostic_support_only"

        coverage_row = coverage_by_case.get(
            case_key,
            {
                "case_key": case_key,
                "normalized_case_id": row["source_key"],
                "source_property_label_coverage": "source_or_property_gate_missing",
                "coverage_reason": "AGENT-538 coverage audit has no row for this scorecard case.",
            },
        )
        labels = source_property_labels_for_case(
            case_key,
            coverage_row,
            labels_by_case,
            refreshed_by_case,
            policy_by_case,
            "scorecard_case_partition",
        )
        original_split_fit_allowed = row["final_fit_allowed"]
        original_split_model_selection_allowed = row["final_model_selection_allowed"]
        policy = policy_by_case.get(case_key)
        if policy:
            final_fit_allowed = policy["final_fit_allowed"]
            final_model_selection_allowed = policy["final_model_selection_allowed"]
        else:
            labels_available = labels["source_property_gate_status"] == "pass_source_property_labels_available"
            final_fit_allowed = "yes" if original_split_fit_allowed == "yes" and labels_available else "no"
            final_model_selection_allowed = (
                "yes" if original_split_model_selection_allowed == "yes" and labels_available else "no"
            )
        split_fit_allowed = gate_aware_split_allowed(original_split_fit_allowed, final_fit_allowed)
        split_model_selection_allowed = gate_aware_split_allowed(
            original_split_model_selection_allowed,
            final_model_selection_allowed,
        )

        rows.append(
            {
                "case_key": case_key,
                "source_key": row["source_key"],
                "corrected_scorecard_role": corrected_role,
                "final_scorecard_partition": partition,
                "original_split_fit_allowed": original_split_fit_allowed,
                "original_split_model_selection_allowed": original_split_model_selection_allowed,
                "split_fit_allowed": split_fit_allowed,
                "split_model_selection_allowed": split_model_selection_allowed,
                "fit_allowed": final_fit_allowed,
                "model_selection_allowed": final_model_selection_allowed,
                "score_allowed": "yes_after_freeze_or_gate"
                if partition in {"train_nominal", "blind_holdout_pm5q", "blind_external_val_salt2"}
                else "yes_after_future_gate"
                if partition.startswith("future_")
                else "no",
                "release_gate": release_gate,
                "shell_score_status": shell_score_status,
                "target_evidence_status": target_evidence_status,
                "score_use": score_use,
                "guardrail": row["guardrail"],
                "source_paths": unique_join(
                    [
                        row["source_paths"],
                        rel(SOURCE_PROPERTY_COVERAGE),
                        rel(SOURCE_PROPERTY_LABELS),
                        rel(SOURCE_PROPERTY_REFRESH_LABELS),
                        rel(SOURCE_PROPERTY_RESOLUTION_POLICY),
                    ]
                ),
                **labels,
            }
        )
    return rows


def model_freeze_contract() -> list[dict[str, Any]]:
    wall_summary = read_json(WALL_DISTRIBUTION_SUMMARY)
    corrected_summary = read_json(AGENT499_SUMMARY)
    rows = [
        {
            "freeze_id": "FINAL_FREEZE_TBD",
            "freeze_status": "not_created",
            "training_cases_required": ";".join(FINAL_TRAINING_CASES),
            "fit_rows_allowed": "Salt1-4 nominal only",
            "model_selection_rows_allowed": "Salt1-4 nominal only",
            "forbidden_fit_or_selection_rows": "salt2_lo5q;salt2_hi5q;val_salt2;salt2_lo10q;salt2_hi10q;salt4_lo10q;salt4_hi10q;salt3_q_insulation_matrix",
            "candidate_admission_dependency": "requires admitted wall/test-section/cooler/pressure/thermal model candidate before freeze",
            "current_candidate_status": corrected_summary["decision"],
            "wall_distribution_dependency": wall_summary["decision"]["blocker_decision"],
            "prediction_artifact_required": "final_frozen_predictions.csv with prediction_model_id and metric-specific fields",
            "scorecard_use": "shell_contract_only",
            "source_paths": f"{rel(AGENT499_SUMMARY)};{rel(WALL_DISTRIBUTION_SUMMARY)}",
        }
    ]
    for row in read_csv(CANDIDATE_FREEZE):
        rows.append(
            {
                "freeze_id": row["candidate_id"],
                "freeze_status": "diagnostic_legacy_candidate_not_final_freeze",
                "training_cases_required": row["corrected_split_training_required"],
                "fit_rows_allowed": "none_for_final_scorecard",
                "model_selection_rows_allowed": "none_for_final_scorecard",
                "forbidden_fit_or_selection_rows": "all_blind_and_future_rows",
                "candidate_admission_dependency": row["legacy_blocking_reasons"],
                "current_candidate_status": row["legacy_admission_status"],
                "wall_distribution_dependency": wall_summary["decision"]["why"],
                "prediction_artifact_required": "not_applicable_until_candidate_admitted_and_refrozen",
                "scorecard_use": row["use_in_final_scorecard"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def metric_contract() -> list[dict[str, Any]]:
    return [
        {
            **row,
            "fit_or_selection_from_blind_rows": "no",
            "runtime_forbidden_inputs": "CFD mdot;realized wallHeatFlux;validation TP/TW;blind residuals;hidden global multipliers",
            "source_paths": f"{rel(VAL_JOIN_CONTRACT)};{rel(SALT2_PM5)}",
        }
        for row in METRIC_CONTRACTS
    ]


def metric_ids_for_partition(partition: str) -> list[str]:
    if partition == "excluded_support_diagnostic":
        return []
    if partition == "blind_holdout_pm5q":
        return [
            "loop_mdot_abs_error_pct",
            "all_probe_temperature_rmse_K",
            "tp_sensor_rmse_K",
            "tw_sensor_rmse_K",
            "pressure_streamwise_rmse_Pa",
            "thermal_section_heat_abs_residual_W",
            "pm5_upcomer_recirculation_diagnostic",
        ]
    if partition == "blind_external_val_salt2":
        return [
            "loop_mdot_abs_error_pct",
            "all_probe_temperature_rmse_K",
            "tp_sensor_rmse_K",
            "tw_sensor_rmse_K",
            "pressure_streamwise_rmse_Pa",
            "thermal_section_heat_abs_residual_W",
        ]
    if partition.startswith("future_"):
        return [
            "loop_mdot_abs_error_pct",
            "all_probe_temperature_rmse_K",
            "tp_sensor_rmse_K",
            "tw_sensor_rmse_K",
            "pressure_streamwise_rmse_Pa",
            "thermal_section_heat_abs_residual_W",
            "pm5_upcomer_recirculation_diagnostic",
        ]
    return [
        "loop_mdot_abs_error_pct",
        "all_probe_temperature_rmse_K",
        "tp_sensor_rmse_K",
        "tw_sensor_rmse_K",
        "pressure_streamwise_rmse_Pa",
        "thermal_section_heat_abs_residual_W",
    ]


def prediction_join_shell(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics = {row["metric_id"]: row for row in metric_contract()}
    rows: list[dict[str, Any]] = []
    for case in case_rows:
        partition = case["final_scorecard_partition"]
        for metric_id in metric_ids_for_partition(partition):
            metric = metrics[metric_id]
            if partition == "train_nominal":
                join_status = "pending_final_freeze_training_prediction"
            elif partition in {"blind_holdout_pm5q", "blind_external_val_salt2"}:
                join_status = "blocked_pending_corrected_final_freeze"
            elif partition.startswith("future_"):
                join_status = "blocked_pending_future_admission_and_final_freeze"
            else:
                join_status = "excluded"
            labels = {column: case[column] for column in REQUIRED_SOURCE_PROPERTY_COLUMNS}
            labels["section_or_segment"] = f"scorecard_case_aggregate:{metric['target_lane']}"
            rows.append(
                {
                    "freeze_id": "FINAL_FREEZE_TBD",
                    "case_key": case["case_key"],
                    "final_scorecard_partition": partition,
                    "metric_id": metric_id,
                    "target_lane": metric["target_lane"],
                    "required_prediction_fields": metric["required_prediction_fields"],
                    "target_value_source_status": case["target_evidence_status"],
                    "prediction_source_status": "no_final_frozen_prediction_artifact",
                    "join_status": join_status,
                    "prediction_value": "",
                    "target_value": "",
                    "residual_prediction_minus_target": "",
                    "score_aggregate_allowed": "yes"
                    if metric["primary_score_aggregate"] == "yes" and not partition.startswith("future_")
                    else metric["primary_score_aggregate"],
                    "fit_allowed": case["fit_allowed"] if partition == "train_nominal" else "no",
                    "model_selection_allowed": case["model_selection_allowed"] if partition == "train_nominal" else "no",
                    "runtime_input_allowed": "no",
                    "release_gate": case["release_gate"],
                    "source_paths": f"{case['source_paths']};{metric['source_paths']}",
                    "source_property_label_coverage": case["source_property_label_coverage"],
                    "source_property_gate_status": case["source_property_gate_status"],
                    "source_property_gate_reason": case["source_property_gate_reason"],
                    **labels,
                }
            )
    return rows


def holdout_release_gates(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in case_rows:
        partition = row["final_scorecard_partition"]
        if partition not in {
            "blind_holdout_pm5q",
            "blind_external_val_salt2",
            "future_holdout_pm10",
            "future_external_new_cfd",
        }:
            continue
        if partition in {"blind_holdout_pm5q", "blind_external_val_salt2"}:
            current_release = "not_released_no_corrected_final_freeze"
            gate_inputs_required = "admitted FINAL_FREEZE_TBD prediction artifact"
        elif partition == "future_holdout_pm10":
            current_release = "not_released_terminal_admission_blocked"
            gate_inputs_required = "terminal PM10 admission plus admitted FINAL_FREEZE_TBD prediction artifact"
        else:
            current_release = "not_released_new_cfd_not_run_or_admitted"
            gate_inputs_required = "new CFD run/admission plus admitted FINAL_FREEZE_TBD prediction artifact"
        rows.append(
            {
                "case_key": row["case_key"],
                "final_scorecard_partition": partition,
                "current_release_status": current_release,
                "fit_allowed_after_release": "no",
                "model_selection_allowed_after_release": "no",
                "score_allowed_after_release": "yes",
                "gate_inputs_required": gate_inputs_required,
                "guardrail": "release permits scoring only; it never retroactively permits fitting or candidate selection",
                "source_paths": row["source_paths"],
            }
        )
    return rows


def admission_gate_shell() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "corrected_split_freeze_exists",
            "current_state": "fail",
            "required_to_score": "all blind/current holdout/external rows",
            "evidence": "AGENT-499 found no corrected Salt1-4 nominal freeze",
            "next_action": "Create admitted final freeze from Salt1-4 nominal only after model candidate admission.",
        },
        {
            "gate_id": "candidate_admitted",
            "current_state": "fail",
            "required_to_score": "all rows",
            "evidence": "AGENT-498/499 report 0 admitted wall/test-section/coupled candidates",
            "next_action": "Resolve wall/test-section/source-placement/axial-mixing blockers before freeze.",
        },
        {
            "gate_id": "blind_rows_excluded_from_fit",
            "current_state": "pass",
            "required_to_score": "holdout/external integrity",
            "evidence": "case partition contract sets fit/model_selection no for Salt2 +/-5Q, val_salt2, PM10, and new CFD",
            "next_action": "Keep this invariant in any future scorer.",
        },
        {
            "gate_id": "pm10_terminal_admission",
            "current_state": "fail_live_or_pending_jobs",
            "required_to_score": "future +/-10Q rows",
            "evidence": "PM10 watch rows remain blocked by live/pending jobs in the cited readiness package",
            "next_action": "Monitor/admit after terminal state in a separate task.",
        },
        {
            "gate_id": "new_cfd_admission",
            "current_state": "fail_not_run",
            "required_to_score": "future new CFD row",
            "evidence": "Salt3 Q x insulation matrix is proposed and not admitted",
            "next_action": "Run/admit new CFD before adding it to scoring.",
        },
    ]


def assumption_ledger() -> list[dict[str, Any]]:
    return [
        {
            "assumption_id": "A1",
            "assumption": "Salt1-4 nominal are the only rows allowed to fit or select the final model.",
            "status": "enforced_in_shell",
            "risk_if_wrong": "Leakage or optimistic holdout scores.",
            "verification_path": rel(SPLIT_LEGAL),
        },
        {
            "assumption_id": "A2",
            "assumption": "Salt2 +/-5Q and val_salt2 are blind score-only after final freeze.",
            "status": "enforced_in_shell",
            "risk_if_wrong": "Holdout/external residuals could steer the model.",
            "verification_path": f"{rel(SPLIT_LEGAL)};{rel(SALT2_PM5)};{rel(VAL_TARGETS)}",
        },
        {
            "assumption_id": "A3",
            "assumption": "PM10 and new CFD rows are future tests, not current score rows.",
            "status": "enforced_in_shell",
            "risk_if_wrong": "Live or not-yet-run CFD would be treated as evidence.",
            "verification_path": f"{rel(BLOCKED_FUTURE)};{rel(PM10_WATCH)}",
        },
        {
            "assumption_id": "A4",
            "assumption": "No final frozen prediction artifact exists yet.",
            "status": "current_blocker",
            "risk_if_wrong": "Shell would incorrectly report missing predictions.",
            "verification_path": rel(AGENT499_SUMMARY),
        },
        {
            "assumption_id": "A5",
            "assumption": "Existing PB1+cooler/distribution candidates remain diagnostic and not admitted.",
            "status": "current_blocker",
            "risk_if_wrong": "Final scorecard could score an unadmitted model.",
            "verification_path": f"{rel(CANDIDATE_FREEZE)};{rel(WALL_DISTRIBUTION_SUMMARY)}",
        },
        {
            "assumption_id": "A6",
            "assumption": "Realized CFD mdot, wallHeatFlux, validation temperatures, blind residuals, and hidden global multipliers are forbidden runtime inputs.",
            "status": "enforced_in_runtime_audit",
            "risk_if_wrong": "The model would no longer be predictive.",
            "verification_path": "runtime_input_audit.csv",
        },
    ]


def runtime_input_audit(case_rows: list[dict[str, Any]], prediction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blind_bad = [
        row
        for row in case_rows
        if row["final_scorecard_partition"] != "train_nominal"
        and (row["fit_allowed"] != "no" or row["model_selection_allowed"] != "no")
    ]
    prediction_runtime_bad = [row for row in prediction_rows if row["runtime_input_allowed"] != "no"]
    label_blank_bad = [
        row
        for row in case_rows + prediction_rows
        if any(not str(row.get(column, "")).strip() for column in REQUIRED_SOURCE_PROPERTY_COLUMNS)
    ]
    return [
        {
            "audit_item": "blind_fit_model_selection_exclusion",
            "status": "pass" if not blind_bad else "fail",
            "details": f"bad_rows={len(blind_bad)}",
        },
        {
            "audit_item": "prediction_rows_no_runtime_target_input",
            "status": "pass" if not prediction_runtime_bad else "fail",
            "details": f"bad_rows={len(prediction_runtime_bad)}",
        },
        {
            "audit_item": "no_solver_or_postprocessor_launch",
            "status": "pass",
            "details": "builder reads existing CSV/JSON evidence only",
        },
        {
            "audit_item": "future_rows_blocked_before_terminal_or_run_admission",
            "status": "pass",
            "details": "future partitions use explicit release gates",
        },
        {
            "audit_item": "no_scientific_admission_change",
            "status": "pass",
            "details": "shell records current blockers and placeholders only",
        },
        {
            "audit_item": "source_property_labels_present_before_fit_or_admission_language",
            "status": "pass" if not label_blank_bad else "fail",
            "details": f"bad_rows={len(label_blank_bad)}",
        },
    ]


def scorecard_summary(case_rows: list[dict[str, Any]], prediction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    partition_counts = Counter(row["final_scorecard_partition"] for row in case_rows)
    join_counts = Counter(row["join_status"] for row in prediction_rows)
    return [
        {
            "summary_key": "case_partitions",
            "value": json.dumps(dict(sorted(partition_counts.items())), sort_keys=True),
            "interpretation": "Salt1-4 nominal training rows are separated from blind/current/future test rows.",
        },
        {
            "summary_key": "prediction_join_status",
            "value": json.dumps(dict(sorted(join_counts.items())), sort_keys=True),
            "interpretation": "All score rows are placeholders because no final frozen prediction artifact exists.",
        },
        {
            "summary_key": "current_decision",
            "value": "scorecard_shell_ready_no_final_scores",
            "interpretation": "The shell is ready for a future frozen prediction join but does not score or admit a model.",
        },
    ]


def source_property_label_gate_audit(
    case_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output_rows = [
        ("case_partition_contract.csv", "case_partition", case_rows),
        ("prediction_join_shell.csv", "prediction_join", prediction_rows),
    ]
    audit_rows: list[dict[str, Any]] = []
    for artifact, row_type, rows in output_rows:
        missing = [
            row
            for row in rows
            if any(not str(row.get(column, "")).strip() for column in REQUIRED_SOURCE_PROPERTY_COLUMNS)
        ]
        blocked = [row for row in rows if row.get("source_property_gate_status") != "pass_source_property_labels_available"]
        fit_language_bad = [
            row
            for row in rows
            if row.get("source_property_gate_status") != "pass_source_property_labels_available"
            and (row.get("fit_allowed") == "yes" or row.get("model_selection_allowed") == "yes")
        ]
        audit_rows.append(
            {
                "artifact": artifact,
                "row_type": row_type,
                "rows_checked": len(rows),
                "required_label_columns": ";".join(REQUIRED_SOURCE_PROPERTY_COLUMNS),
                "missing_required_label_rows": len(missing),
                "source_property_blocked_rows": len(blocked),
                "fit_or_selection_allowed_despite_missing_labels": len(fit_language_bad),
                "audit_status": "pass" if not missing and not fit_language_bad else "fail",
                "source_paths": (
                    f"{rel(SOURCE_PROPERTY_CONTRACT)};{rel(SOURCE_PROPERTY_COVERAGE)};"
                    f"{rel(SOURCE_PROPERTY_LABELS)};{rel(SOURCE_PROPERTY_REFRESH_LABELS)};"
                    f"{rel(SOURCE_PROPERTY_RESOLUTION_POLICY)}"
                ),
            }
        )
    return audit_rows


def source_manifest(outputs: list[Path]) -> list[dict[str, Any]]:
    inputs = [
        SPLIT_LEGAL,
        CANDIDATE_FREEZE,
        AGENT499_SUMMARY,
        BLOCKED_FUTURE,
        SALT2_PM5,
        VAL_EXTERNAL_SUMMARY,
        VAL_TARGETS,
        VAL_JOIN_CONTRACT,
        PM10_WATCH,
        WALL_DISTRIBUTION_SUMMARY,
        SOURCE_PROPERTY_LABELS,
        SOURCE_PROPERTY_COVERAGE,
        SOURCE_PROPERTY_CONTRACT,
        SOURCE_PROPERTY_REFRESH_LABELS,
        SOURCE_PROPERTY_RESOLUTION_POLICY,
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
  - {rel(SPLIT_LEGAL)}
  - {rel(CANDIDATE_FREEZE)}
  - {rel(SALT2_PM5)}
  - {rel(VAL_TARGETS)}
  - {rel(PM10_WATCH)}
  - {rel(WALL_DISTRIBUTION_SUMMARY)}
  - {rel(SOURCE_PROPERTY_RESOLUTION_POLICY)}
tags: [forward-model, final-scorecard, corrected-split, holdout-policy]
related:
  - .agent/status/2026-07-18_TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS.md
  - final-predictive-split-policy
  - val-salt2-external-test
  - salt2-pm5q-holdout
  - predictive-wall-test-section-submodels
task: {TASK}
updated_by: TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS
date: 2026-07-17
role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Final Predictive Scorecard Shell

## Purpose

This package prepares the final scorecard shell without running a model or
computing final scores. It fixes the corrected split in a machine-readable
contract:

- Train/freeze: Salt1 nominal, Salt2 nominal, Salt3 nominal, Salt4 nominal.
- Current blind tests: Salt2 +/-5Q and `val_salt2`, released only after a
  corrected final freeze exists.
- Future tests: Salt2/Salt4 +/-10Q and new CFD, released only after terminal or
  run/admission gates and a corrected final freeze.

## Current State

Final scores are not available. The shell is blocked by the absence of an
admitted Salt1-4 nominal final freeze and by the current wall/test-section
candidate blockers. Existing PB1+cooler/distribution rows remain diagnostic, not
final model evidence.

## Outputs

- `case_partition_contract.csv` is the authoritative row-level split contract.
- `model_freeze_contract.csv` defines `FINAL_FREEZE_TBD` and documents why old
  candidates are not final freezes.
- `metric_contract.csv` defines score lanes and required prediction fields.
- `prediction_join_shell.csv` is the placeholder table that a future frozen
  prediction join should fill.
- `source_property_label_gate_audit.csv` verifies that partition and prediction
  rows carry source/property labels and apply the July 20 source-envelope
  resolution policy before any fit/admission language.
- `holdout_release_gates.csv` records when blind/current/future tests may be
  released.
- `admission_gate_shell.csv` records the gates that still block final scoring.
- `assumption_ledger.csv` lists assumptions and verification paths.
- `runtime_input_audit.csv` verifies no leakage is encoded in this shell.
- `scorecard_summary.csv`, `source_manifest.csv`, and `summary.json` summarize
  the generated package.

## Counts

- Training cases: `{summary["training_cases"]}`.
- Current blind holdout/external cases: `{summary["current_blind_cases"]}`.
- Future test cases: `{summary["future_test_cases"]}`.
- Prediction placeholder rows: `{summary["prediction_placeholder_rows"]}`.
- Source/property gate failures: `{summary["source_property_gate_failures"]}`.
- Fit-enabled rows after source/property policy: `{summary["fit_allowed_after_source_property_gate"]}`.
- Model-selection-enabled rows after source/property policy: `{summary["model_selection_allowed_after_source_property_gate"]}`.
- Runtime audit failures: `{summary["runtime_audit_failures"]}`.

## How To Use This Later

After a candidate is admitted, a separate task should produce a frozen
prediction artifact with `prediction_model_id` and the metric-specific fields
listed in `metric_contract.csv`. Join that artifact into
`prediction_join_shell.csv`; then compute residuals only for released rows.
Salt2 +/-5Q, `val_salt2`, PM10, and new CFD rows must remain unavailable to
fitting and model selection.
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    case_rows = case_partition_contract()
    freeze_rows = model_freeze_contract()
    metric_rows = metric_contract()
    prediction_rows = prediction_join_shell(case_rows)
    release_rows = holdout_release_gates(case_rows)
    gate_rows = admission_gate_shell()
    assumption_rows = assumption_ledger()
    runtime_rows = runtime_input_audit(case_rows, prediction_rows)
    source_property_audit_rows = source_property_label_gate_audit(case_rows, prediction_rows)
    summary_rows = scorecard_summary(case_rows, prediction_rows)

    outputs = [
        OUT / "case_partition_contract.csv",
        OUT / "model_freeze_contract.csv",
        OUT / "metric_contract.csv",
        OUT / "prediction_join_shell.csv",
        OUT / "holdout_release_gates.csv",
        OUT / "admission_gate_shell.csv",
        OUT / "assumption_ledger.csv",
        OUT / "runtime_input_audit.csv",
        OUT / "source_property_label_gate_audit.csv",
        OUT / "scorecard_summary.csv",
        OUT / "source_manifest.csv",
        OUT / "summary.json",
        OUT / "README.md",
    ]

    write_csv(outputs[0], case_rows)
    write_csv(outputs[1], freeze_rows)
    write_csv(outputs[2], metric_rows)
    write_csv(outputs[3], prediction_rows)
    write_csv(outputs[4], release_rows)
    write_csv(outputs[5], gate_rows)
    write_csv(outputs[6], assumption_rows)
    write_csv(outputs[7], runtime_rows)
    write_csv(outputs[8], source_property_audit_rows)
    write_csv(outputs[9], summary_rows)
    write_csv(outputs[10], source_manifest(outputs))

    partition_counts = Counter(row["final_scorecard_partition"] for row in case_rows)
    source_property_gate_failures = sum(int(row["audit_status"] != "pass") for row in source_property_audit_rows)
    summary = {
        "task": TASK,
        "label_propagation_task": "TODO-FINAL-SCORECARD-POLICY-INTEGRATION",
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "training_cases": partition_counts["train_nominal"],
        "training_case_keys": list(FINAL_TRAINING_CASES),
        "current_blind_cases": partition_counts["blind_holdout_pm5q"] + partition_counts["blind_external_val_salt2"],
        "current_blind_case_keys": list(BLIND_HOLDOUT_CASES + BLIND_EXTERNAL_CASES),
        "future_test_cases": partition_counts["future_holdout_pm10"] + partition_counts["future_external_new_cfd"],
        "future_test_case_keys": list(FUTURE_PM10_CASES + FUTURE_NEW_CFD_CASES),
        "excluded_support_cases": partition_counts["excluded_support_diagnostic"],
        "metric_contract_rows": len(metric_rows),
        "prediction_placeholder_rows": len(prediction_rows),
        "holdout_release_gate_rows": len(release_rows),
        "runtime_audit_rows": len(runtime_rows),
        "runtime_audit_failures": sum(not row["status"].startswith("pass") for row in runtime_rows),
        "source_property_label_gate_rows": len(source_property_audit_rows),
        "source_property_gate_failures": source_property_gate_failures,
        "source_property_blocked_case_rows": sum(
            row["source_property_gate_status"] != "pass_source_property_labels_available" for row in case_rows
        ),
        "fit_allowed_after_source_property_gate": sum(row["fit_allowed"] == "yes" for row in case_rows),
        "model_selection_allowed_after_source_property_gate": sum(
            row["model_selection_allowed"] == "yes" for row in case_rows
        ),
        "score_status": "shell_ready_no_final_scores",
        "freeze_status": "FINAL_FREEZE_TBD_not_created",
        "scientific_admission_change": "none",
        "source_property_label_policy": "final_source_envelope_resolution_policy_required_before_fit_or_model_selection",
        "guardrail": "Holdout/external/future rows are score-only and never fit/model-selection inputs; source/property blocked rows cannot fit/select.",
    }
    write_json(outputs[11], summary)
    outputs[12].write_text(readme_text(summary))
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
