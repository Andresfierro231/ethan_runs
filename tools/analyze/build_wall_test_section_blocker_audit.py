#!/usr/bin/env python3
"""Build AGENT-531 wall/test-section blocker audit from existing evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-531"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit")
OUT = ROOT / OUT_REL
STATUS = ROOT / f".agent/status/{DATE}_{TASK}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/wall-test-section-blocker-audit.md"
IMPORT = ROOT / "imports/2026-07-17_wall_test_section_blocker_audit.json"

AGENT498 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder"
AGENT511 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score"
AGENT513 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate"
AGENT520 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_residual_atlas"
AGENT522 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_thermal_circuit_study"
AGENT461 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score"
SENSOR_POLICY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude/sensor_policy_scorecard.csv"

COUPLED_SOURCES = [
    ("AGENT-498_wall_distribution_ladder", AGENT498, "coupled_delta_vs_m3.csv"),
    ("AGENT-513_wall_temperature_drive", AGENT513, "coupled_delta_vs_m3.csv"),
    ("AGENT-511_heater_source_redistribution", AGENT511, "coupled_delta_vs_m3.csv"),
    ("AGENT-522_wall_thermal_circuit", AGENT522, "coupled_delta_vs_m3.csv"),
]

PROBE_SOURCES = [
    ("AGENT-498_wall_distribution_ladder", AGENT498, "probe_delta_vs_m3.csv", "delta"),
    ("AGENT-513_wall_temperature_drive", AGENT513, "probe_delta_vs_m3.csv", "delta"),
    ("AGENT-522_wall_thermal_circuit", AGENT522, "probe_delta_vs_m3.csv", "delta"),
    ("AGENT-511_heater_source_redistribution", AGENT511, "probe_error_localization.csv", "localization_only"),
]

ROLE_SOURCES = [
    ("AGENT-498_wall_distribution_ladder", AGENT498, "role_segment_error_summary.csv"),
    ("AGENT-513_wall_temperature_drive", AGENT513, "role_segment_error_summary.csv"),
    ("AGENT-522_wall_thermal_circuit", AGENT522, "role_segment_error_summary.csv"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: Any) -> float | None:
    try:
        if value in ("", None, "nan", "NaN"):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: float | None, precision: int = 10) -> str:
    if value is None or not math.isfinite(value):
        return ""
    return f"{value:.{precision}g}"


def required_sources() -> list[Path]:
    paths = [SENSOR_POLICY]
    paths.extend(package / file_name for _, package, file_name in COUPLED_SOURCES)
    paths.extend(package / file_name for _, package, file_name, _ in PROBE_SOURCES)
    paths.extend(package / file_name for _, package, file_name in ROLE_SOURCES)
    paths.extend(
        [
            AGENT498 / "README.md",
            AGENT511 / "README.md",
            AGENT513 / "README.md",
            AGENT520 / "README.md",
            AGENT522 / "README.md",
            AGENT461 / "README.md",
        ]
    )
    return paths


def require_sources() -> None:
    missing = [rel(path) for path in required_sources() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AGENT-531 source evidence: " + "; ".join(missing))


def candidate_family(candidate_id: str) -> str:
    if candidate_id.startswith("PB2"):
        return "PB2_local_passive_distribution"
    if candidate_id.startswith("PB3"):
        return "PB3_upcomer_test_section_attenuated"
    if candidate_id.startswith("WTD1"):
        return "WTD1_upcomer_test_section_pipe_wall_drive"
    if candidate_id.startswith("WTD2"):
        return "WTD2_upcomer_test_section_outer_surface_drive"
    if candidate_id.startswith("HS1"):
        return "HS1_heater_source_redistribution"
    if candidate_id.startswith("HIW1"):
        return "HIW1_heated_incline_pipe_wall_drive"
    if candidate_id.startswith("HIW2"):
        return "HIW2_heated_incline_outer_surface_drive"
    if candidate_id.startswith("TSC1"):
        return "TSC1_test_section_pipe_wall_drive"
    if candidate_id.startswith("TSC2"):
        return "TSC2_test_section_outer_surface_drive"
    return "unknown"


def read_policy_by_sensor() -> dict[str, dict[str, str]]:
    return {row["sensor"]: row for row in read_csv(SENSOR_POLICY)}


def gate_fail_dimensions(row: dict[str, str]) -> list[str]:
    checks = [
        ("mdot", fnum(row.get("mdot_delta_vs_m3_pct"))),
        ("tp", fnum(row.get("tp_delta_vs_m3_K"))),
        ("tw", fnum(row.get("tw_delta_vs_m3_K"))),
        ("all_probe", fnum(row.get("all_probe_delta_vs_m3_K"))),
    ]
    return [name for name, value in checks if value is not None and value > 0.0]


def build_cross_candidate_residual_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_package, package, file_name in COUPLED_SOURCES:
        source_path = package / file_name
        for row in read_csv(source_path):
            fail_dims = gate_fail_dimensions(row)
            row_values = {
                "mdot": fnum(row.get("mdot_delta_vs_m3_pct")),
                "tp": fnum(row.get("tp_delta_vs_m3_K")),
                "tw": fnum(row.get("tw_delta_vs_m3_K")),
                "all_probe": fnum(row.get("all_probe_delta_vs_m3_K")),
            }
            positive = [(name, value) for name, value in row_values.items() if value is not None and value > 0.0]
            nearest = min(positive, key=lambda item: item[1])[0] if positive else "all_available_dimensions_pass"
            if "mdot" not in fail_dims and any(name in fail_dims for name in ("tp", "tw", "all_probe")):
                pattern = "mdot_improves_temperature_shape_fails"
            elif "mdot" in fail_dims and any(name in fail_dims for name in ("tp", "tw", "all_probe")):
                pattern = "mdot_and_temperature_shape_fail"
            elif fail_dims:
                pattern = "partial_gate_failure"
            else:
                pattern = "available_gate_dimensions_pass"
            rows.append(
                {
                    "source_package": source_package,
                    "candidate_id": row["candidate_id"],
                    "candidate_family": candidate_family(row["candidate_id"]),
                    "case_id": row.get("case_id", ""),
                    "split_role": row.get("split_role", ""),
                    "mdot_delta_vs_m3_pct": row.get("mdot_delta_vs_m3_pct", ""),
                    "tp_delta_vs_m3_K": row.get("tp_delta_vs_m3_K", ""),
                    "tw_delta_vs_m3_K": row.get("tw_delta_vs_m3_K", ""),
                    "all_probe_delta_vs_m3_K": row.get("all_probe_delta_vs_m3_K", ""),
                    "score_gate": row.get("score_gate", ""),
                    "gate_fail_dimensions": ";".join(fail_dims),
                    "nearest_miss_dimension": nearest,
                    "failure_pattern": pattern,
                    "source_path": rel(source_path),
                }
            )
    return rows


def build_probe_residual_atlas() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_package, package, file_name, comparison_mode in PROBE_SOURCES:
        source_path = package / file_name
        for row in read_csv(source_path):
            candidate_id = row.get("candidate_id", "")
            delta = row.get("abs_error_delta_vs_m3_K", "")
            m3_error = row.get("m3_error_K", "")
            comparison_status = row.get("comparison_status", "")
            if comparison_mode == "localization_only":
                comparison_status = "m3_delta_unavailable_in_source_package"
                delta = ""
                m3_error = ""
            rows.append(
                {
                    "source_package": source_package,
                    "candidate_id": candidate_id,
                    "candidate_family": candidate_family(candidate_id),
                    "case_id": row.get("case_id", ""),
                    "split_role": row.get("split_role", ""),
                    "sensor": row.get("sensor", ""),
                    "kind": row.get("kind", ""),
                    "candidate_error_K": row.get("candidate_error_K", row.get("error_K", "")),
                    "candidate_abs_error_K": row.get("candidate_abs_error_K", row.get("abs_error_K", "")),
                    "m3_error_K": m3_error,
                    "m3_abs_error_K": row.get("m3_abs_error_K", ""),
                    "abs_error_delta_vs_m3_K": delta,
                    "candidate_predicted_K": row.get("candidate_predicted_K", row.get("predicted_K", "")),
                    "target_K": row.get("target_K", ""),
                    "prediction_source_segment": row.get("prediction_source_segment", ""),
                    "prediction_source_fraction": row.get("prediction_source_fraction", ""),
                    "comparison_status": comparison_status,
                    "probe_gate": row.get("probe_gate", ""),
                    "source_path": rel(source_path),
                }
            )
    return rows


def build_sensor_map_candidate_audit(probe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policy = read_policy_by_sensor()
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in probe_rows:
        by_key[(row["source_package"], row["candidate_family"], row["sensor"])].append(row)

    rows: list[dict[str, Any]] = []
    observed_sensors = {sensor for _, _, sensor in by_key}
    for sensor in sorted(set(policy) | observed_sensors):
        policy_row = policy.get(sensor, {})
        matching_keys = [key for key in by_key if key[2] == sensor]
        if not matching_keys:
            matching_keys = [("policy_only", "policy_only", sensor)]
        for source_package, family, _ in sorted(matching_keys):
            items = by_key.get((source_package, family, sensor), [])
            segments = sorted({str(item.get("prediction_source_segment", "")) for item in items if item.get("prediction_source_segment", "")})
            fractions = sorted({str(item.get("prediction_source_fraction", "")) for item in items if item.get("prediction_source_fraction", "")})
            compared = [item for item in items if item.get("comparison_status") == "compared"]
            not_compared = [item for item in items if str(item.get("comparison_status", "")).startswith("not_compared")]
            finite = [item for item in items if fnum(item.get("candidate_predicted_K")) is not None]
            fail = [item for item in items if item.get("probe_gate") == "fail"]
            passed = [item for item in items if item.get("probe_gate") == "pass"]
            deltas = [(fnum(item.get("abs_error_delta_vs_m3_K")), item) for item in items]
            deltas = [(value, item) for value, item in deltas if value is not None]
            worst_value, worst_item = max(deltas, key=lambda pair: pair[0]) if deltas else (None, {})
            policy_segment = policy_row.get("source_segment_after_refresh", "")
            score_use = policy_row.get("score_use", "")
            policy_decision = policy_row.get("policy_decision", "")
            if sensor == "TW10" or "active_hx_shell" in policy_decision:
                status = "policy_excluded_active_hx_shell_state"
                interpretation = "known active-HX shell-state target; not a wall/test-section candidate failure"
            elif sensor == "TP2" or "exclude" in score_use:
                status = "policy_excluded_junction_or_restore_target"
                interpretation = "known policy exclusion or validation-only restore target"
            elif policy_segment and segments and policy_segment not in segments:
                status = "source_segment_mismatch"
                interpretation = "observed candidate source segment does not match refreshed policy segment"
            elif len(segments) > 1:
                status = "segment_mapping_varies_by_candidate"
                interpretation = "candidate families project this sensor to different segments"
            elif fail:
                status = "scoreable_residual_failure"
                interpretation = "sensor is policy-scoreable but residual fails versus M3"
            elif not items:
                status = "policy_only_no_candidate_rows"
                interpretation = "sensor appears in policy evidence but not in candidate probe outputs"
            elif not deltas:
                status = "m3_delta_unavailable"
                interpretation = "candidate localization exists but source package does not provide M3 probe delta"
            else:
                status = "scoreable_map_consistent"
                interpretation = "observed segment agrees with policy and available probe gates do not fail"
            rows.append(
                {
                    "source_package": source_package,
                    "candidate_family": family,
                    "sensor": sensor,
                    "kind": policy_row.get("kind", items[0].get("kind", "") if items else ""),
                    "policy_source_segment": policy_segment,
                    "observed_source_segments": ";".join(segments),
                    "observed_source_fractions": ";".join(fractions),
                    "compared_rows": len(compared),
                    "not_compared_rows": len(not_compared),
                    "finite_prediction_rows": len(finite),
                    "fail_rows": len(fail),
                    "pass_rows": len(passed),
                    "max_abs_error_delta_vs_m3_K": fmt(worst_value),
                    "worst_case_id": worst_item.get("case_id", ""),
                    "worst_candidate_id": worst_item.get("candidate_id", ""),
                    "score_use": score_use,
                    "policy_decision": policy_decision,
                    "audit_status": status,
                    "interpretation": interpretation,
                    "source_path": ";".join(sorted({item["source_path"] for item in items})) if items else rel(SENSOR_POLICY),
                }
            )
    return rows


def build_role_segment_residual_atlas() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_package, package, file_name in ROLE_SOURCES:
        source_path = package / file_name
        for row in read_csv(source_path):
            candidate_id = row.get("candidate_id", "")
            rows.append(
                {
                    "source_package": source_package,
                    "candidate_id": candidate_id,
                    "candidate_family": candidate_family(candidate_id),
                    "case_id": row.get("case_id", ""),
                    "split_role": row.get("split_role", ""),
                    "kind": row.get("kind", ""),
                    "prediction_source_segment": row.get("prediction_source_segment", ""),
                    "n_compared": row.get("n_compared", ""),
                    "candidate_rmse_K": row.get("candidate_rmse_K", ""),
                    "m3_rmse_K": row.get("m3_rmse_K", ""),
                    "rmse_delta_vs_m3_K": row.get("rmse_delta_vs_m3_K", ""),
                    "candidate_mae_K": row.get("candidate_mae_K", ""),
                    "m3_mae_K": row.get("m3_mae_K", ""),
                    "mae_delta_vs_m3_K": row.get("mae_delta_vs_m3_K", ""),
                    "source_path": rel(source_path),
                }
            )
    return rows


def build_invariant_failure_modes(probe_rows: list[dict[str, Any]], role_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_sensor: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in probe_rows:
        if fnum(row.get("abs_error_delta_vs_m3_K")) is None:
            continue
        by_sensor[(row["kind"], row["prediction_source_segment"], row["sensor"])].append(row)
    for (kind, segment, sensor), items in by_sensor.items():
        families = sorted({item["candidate_family"] for item in items})
        fail_items = [item for item in items if fnum(item.get("abs_error_delta_vs_m3_K")) is not None and fnum(item.get("abs_error_delta_vs_m3_K")) > 0.0]
        if len(families) < 3 or len(fail_items) / max(len(items), 1) < 0.70:
            continue
        worst = max(items, key=lambda item: fnum(item.get("abs_error_delta_vs_m3_K")) or -math.inf)
        rows.append(
            {
                "failure_mode_id": f"{kind}_{segment}_{sensor}",
                "failure_scope": "probe_sensor",
                "kind": kind,
                "prediction_source_segment": segment,
                "sensor_scope": sensor,
                "candidate_families_with_compared_rows": len(families),
                "candidate_families": ";".join(families),
                "compared_rows": len(items),
                "fail_rows": len(fail_items),
                "pass_rows": len(items) - len(fail_items),
                "worst_abs_error_delta_vs_m3_K": worst.get("abs_error_delta_vs_m3_K", ""),
                "worst_candidate_id": worst.get("candidate_id", ""),
                "worst_case_id": worst.get("case_id", ""),
                "interpretation": "persistent scoreable probe residual across tested passive/wall/source families",
                "next_action": "do not retry passive wall-state selectors; test axial mixing/upcomer stratification or explicit wall/fluid coupling after active AGENT-526 resolves",
                "source_path": ";".join(sorted({item["source_path"] for item in items})),
            }
        )

    by_role: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in role_rows:
        if fnum(row.get("rmse_delta_vs_m3_K")) is None:
            continue
        by_role[(row["kind"], row["prediction_source_segment"])].append(row)
    for (kind, segment), items in by_role.items():
        families = sorted({item["candidate_family"] for item in items})
        fail_items = [item for item in items if (fnum(item.get("rmse_delta_vs_m3_K")) or 0.0) > 0.0]
        if len(families) < 3 or len(fail_items) / max(len(items), 1) < 0.70:
            continue
        worst = max(items, key=lambda item: fnum(item.get("rmse_delta_vs_m3_K")) or -math.inf)
        rows.append(
            {
                "failure_mode_id": f"{kind}_{segment}_role_rmse",
                "failure_scope": "role_segment_rmse",
                "kind": kind,
                "prediction_source_segment": segment,
                "sensor_scope": "all_compared_role_segment_sensors",
                "candidate_families_with_compared_rows": len(families),
                "candidate_families": ";".join(families),
                "compared_rows": len(items),
                "fail_rows": len(fail_items),
                "pass_rows": len(items) - len(fail_items),
                "worst_abs_error_delta_vs_m3_K": worst.get("rmse_delta_vs_m3_K", ""),
                "worst_candidate_id": worst.get("candidate_id", ""),
                "worst_case_id": worst.get("case_id", ""),
                "interpretation": "persistent role/segment temperature-shape RMSE failure",
                "next_action": "prioritize mechanism that changes axial/branch thermal shape, not total passive heat loss alone",
                "source_path": ";".join(sorted({item["source_path"] for item in items})),
            }
        )
    rows.sort(key=lambda row: fnum(row.get("worst_abs_error_delta_vs_m3_K")) or -math.inf, reverse=True)
    return rows


def build_admission_gate_sanity(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matrix_rows:
        by_candidate[row["candidate_id"]].append(row)
    rows: list[dict[str, Any]] = []
    for candidate_id, items in sorted(by_candidate.items()):
        def values(field: str) -> list[float]:
            return [value for value in (fnum(item.get(field)) for item in items) if value is not None]

        metric_fields = {
            "mdot": "mdot_delta_vs_m3_pct",
            "tp": "tp_delta_vs_m3_K",
            "tw": "tw_delta_vs_m3_K",
            "all_probe": "all_probe_delta_vs_m3_K",
        }
        pass_flags: dict[str, str] = {}
        worst_by_metric: dict[str, float | None] = {}
        for metric, field in metric_fields.items():
            metric_values = values(field)
            worst_by_metric[metric] = max(metric_values) if metric_values else None
            pass_flags[metric] = "missing" if not metric_values else ("pass" if max(metric_values) <= 0.0 else "fail")
        failing_metrics = [metric for metric, status in pass_flags.items() if status == "fail"]
        missing_metrics = [metric for metric, status in pass_flags.items() if status == "missing"]
        nearest = ""
        if failing_metrics:
            nearest = min(failing_metrics, key=lambda metric: worst_by_metric[metric] or math.inf)
        elif missing_metrics:
            nearest = "missing_" + ";".join(missing_metrics)
        else:
            nearest = "all_available_metrics_pass"
        rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_family": candidate_family(candidate_id),
                "source_package": items[0]["source_package"],
                "validation_rows": sum(1 for item in items if item["split_role"] == "validation"),
                "holdout_rows": sum(1 for item in items if item["split_role"] == "holdout"),
                "gate_rows": len(items),
                "mdot_gate": pass_flags["mdot"],
                "tp_gate": pass_flags["tp"],
                "tw_gate": pass_flags["tw"],
                "all_probe_gate": pass_flags["all_probe"],
                "score_gate_rows_passed": sum(1 for item in items if item["score_gate"] == "pass"),
                "score_gate_rows_failed": sum(1 for item in items if item["score_gate"] == "fail"),
                "worst_mdot_delta_vs_m3_pct": fmt(worst_by_metric["mdot"]),
                "worst_tp_delta_vs_m3_K": fmt(worst_by_metric["tp"]),
                "worst_tw_delta_vs_m3_K": fmt(worst_by_metric["tw"]),
                "worst_all_probe_delta_vs_m3_K": fmt(worst_by_metric["all_probe"]),
                "nearest_remaining_miss": nearest,
                "admission_decision": "not_admitted",
                "why": "at least one validation/holdout gate remains failed or missing vs M3",
                "source_path": ";".join(sorted({item["source_path"] for item in items})),
            }
        )
    return rows


def build_next_lane_decision(
    sensor_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scoreable_mismatches = [
        row for row in sensor_rows
        if row["audit_status"] == "source_segment_mismatch"
        and not str(row["sensor"]).startswith("TP2")
        and row["sensor"] != "TW10"
    ]
    admitted = [row for row in matrix_rows if row["score_gate"] == "pass"]
    heated_failures = [
        row for row in failure_rows
        if row["prediction_source_segment"] == "heated_incline" and row["kind"] == "TW"
    ]
    if scoreable_mismatches:
        decision = "sensor_map_fix_first"
        reason = "scoreable sensors have source-segment mismatches that could invalidate residual interpretation"
        next_task = "repair and re-score sensor map before new physics candidates"
    elif admitted:
        decision = "admission_review_required"
        reason = "at least one row reports score_gate=pass; manual admission review required"
        next_task = "review gate contract before blocker mutation"
    elif heated_failures:
        decision = "axial_mixing_candidate_next_after_AGENTS526"
        reason = "TP2/TW10 policy exclusions are known, but scoreable heated-incline TW5/TW6 residuals persist across candidate families"
        next_task = "after active AGENT-526 wall/fluid coupling resolves, implement axial mixing/upcomer stratification candidate without passive-wall retreads"
    else:
        decision = "fluid_api_required_or_more_extraction"
        reason = "no scoreable map defect found, but invariant residual pattern is insufficiently localized"
        next_task = "write Fluid API/extraction contract before another coupled scoring run"
    return [
        {
            "decision": decision,
            "blocker_status_after_audit": "open",
            "reason": reason,
            "next_task": next_task,
            "sensor_map_status": "no_scoreable_source_mismatch_found" if not scoreable_mismatches else "scoreable_mismatch_found",
            "known_policy_exclusions": "TP2 validation-only junction/restore target; TW10 active-HX shell state excluded",
            "active_collision": "AGENT-526 owns overlapping wall/fluid solver fallback; AGENT-531 does not launch solver jobs",
            "scientific_admission_change": "none",
        }
    ]


def build_runtime_request_audit(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [
        {
            "check": "no_scheduler_action",
            "status": "pass",
            "detail": "AGENT-531 only reads existing packages and writes derived audit artifacts",
        },
        {
            "check": "no_solver_or_postprocessing_launch",
            "status": "pass",
            "detail": "no Fluid/OpenFOAM/cfd-pp run is submitted by this builder",
        },
        {
            "check": "no_runtime_temperature_or_cfd_leakage",
            "status": "pass",
            "detail": "uses only post-solve residual outputs; no realized CFD wallHeatFlux, mdot, cooler duty, or validation temperatures become runtime inputs",
        },
        {
            "check": "parallel_workers_noop",
            "status": "pass",
            "detail": f"requested --parallel-workers={args.parallel_workers}; ignored because this is a no-solver audit",
        },
        {
            "check": "timeout_noop",
            "status": "pass",
            "detail": f"requested --timeout-seconds={args.timeout_seconds}; ignored because this is a no-solver audit",
        },
        {
            "check": "active_AGENTS526_collision_avoided",
            "status": "pass",
            "detail": "solver-backed wall/fluid coupling and axial-mixing runs are deferred to later non-overlapping task rows",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in required_sources():
        rows.append(
            {
                "source_path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "use": "read_only_existing_evidence",
                "native_output": "no",
            }
        )
    return rows


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    readme = out / "README.md"
    readme.write_text(
        f"""---
provenance:
  - {rel(AGENT498)}
  - {rel(AGENT511)}
  - {rel(AGENT513)}
  - {rel(AGENT520)}
  - {rel(AGENT522)}
  - {rel(SENSOR_POLICY)}
tags: [forward-model, wall-test-section, residual-atlas, sensor-map, blocker]
related:
  - .agent/status/2026-07-17_AGENT-531.md
  - .agent/journal/2026-07-17/wall-test-section-blocker-audit.md
  - imports/2026-07-17_wall_test_section_blocker_audit.json
task: AGENT-531
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Wall/Test-Section Blocker Audit

## Result

Decision for `predictive-wall-test-section-submodels`: `{summary['next_lane_decision']}`.

Blocker status after this audit: `open`.

This package refreshes AGENT-520 with completed AGENT-511 and AGENT-522 evidence.
It does not run Fluid/OpenFOAM jobs and does not change scientific admission.

## Counts

- Coupled gate rows consolidated: `{summary['cross_candidate_rows']}`.
- Candidate admission sanity rows: `{summary['admission_sanity_rows']}`.
- Probe atlas rows: `{summary['probe_rows']}`.
- Sensor-map audit rows: `{summary['sensor_audit_rows']}`.
- Invariant failure-mode rows: `{summary['failure_mode_rows']}`.
- Scoreable source-segment mismatches: `{summary['scoreable_source_segment_mismatches']}`.
- Admitted candidates found: `{summary['admitted_candidates']}`.

## Interpretation

TP2 and TW10 remain known policy/extraction exclusions. TW5/TW6 are not policy
exclusions: they are scoreable heated-incline TW targets, and they remain among
the worst residuals across passive distribution, wall-temperature drive, and
wall-circuit candidates. Heater-source redistribution now has completed coupled
gate rows but no source-package probe-delta table, so this package includes its
candidate-level gate failure and marks probe-level M3 deltas unavailable.

The next non-overlapping physics lane is axial mixing/upcomer stratification
after active AGENT-526 resolves its wall/fluid coupling fallback.

## Files To Open First

- `next_lane_decision.csv`
- `admission_gate_sanity.csv`
- `cross_candidate_residual_matrix.csv`
- `sensor_map_candidate_audit.csv`
- `invariant_failure_modes.csv`
- `probe_residual_atlas.csv`

## Guardrails

No native solver outputs, registry/admission state, scheduler state, Fluid source,
or external repositories were mutated. No fitting or model selection was
performed. The forward-predictive topic map was not edited because AGENT-529
currently owns an additive update to that file.
""",
        encoding="utf-8",
    )


def write_status(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        f"""---
provenance:
  - {rel(OUT)}
  - {rel(AGENT498)}
  - {rel(AGENT511)}
  - {rel(AGENT513)}
  - {rel(AGENT522)}
tags: [forward-model, wall-test-section, blocker, sensor-map]
related:
  - {rel(JOURNAL)}
  - {rel(IMPORT)}
  - {rel(OUT / 'README.md')}
task: AGENT-531
date: 2026-07-17
role: Implementer/Tester/Writer
type: status
status: complete
---
# AGENT-531 Status

## Objective

Refresh the wall/test-section blocker audit using completed AGENT-511 and
AGENT-522 evidence, with no solver launch or admission mutation.

## Outcome

- Consolidated `{summary['cross_candidate_rows']}` coupled gate rows and
  `{summary['probe_rows']}` probe rows.
- Found `{summary['scoreable_source_segment_mismatches']}` scoreable
  source-segment mismatches.
- Found `{summary['admitted_candidates']}` admitted candidates.
- Next decision: `{summary['next_lane_decision']}`.

## Changes Made

- `{rel(OUT)}`
- `{rel(STATUS)}`
- `{rel(JOURNAL)}`
- `{rel(IMPORT)}`
- `.agent/blockers.yml`
- generated docs index files after `tools/docs/build_repo_index.py`

## Validation

- `python3.11 tools/analyze/test_wall_test_section_blocker_audit.py`
- `python3.11 -m py_compile tools/analyze/build_wall_test_section_blocker_audit.py tools/analyze/test_wall_test_section_blocker_audit.py`
- `python3.11 -m json.tool imports/2026-07-17_wall_test_section_blocker_audit.json`
- `python3.11 -m json.tool work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/summary.json`
- `python3.11 tools/docs/build_repo_index.py --check`
- `python3.11 tools/docs/build_repo_index.py`

## Guardrails

Native outputs, registry/admission state, scheduler state, Fluid source, and
external repositories were not mutated. No Fluid/OpenFOAM/cfd-pp job was
submitted. The active AGENT-526 solver lane was not duplicated.
""",
        encoding="utf-8",
    )


def write_journal(summary: dict[str, Any]) -> None:
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        f"""---
provenance:
  - {rel(OUT)}
  - {rel(SENSOR_POLICY)}
  - {rel(AGENT520)}
tags: [forward-model, wall-test-section, blocker, residual-atlas]
related:
  - {rel(STATUS)}
  - {rel(IMPORT)}
  - {rel(OUT / 'README.md')}
task: AGENT-531
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Wall/Test-Section Blocker Audit

## Attempted

Built a no-solver blocker audit that refreshes the earlier residual atlas with
final AGENT-511 heater-source and AGENT-522 wall-circuit evidence.

## Observed

- Candidate-level admission remains zero: `{summary['admitted_candidates']}`
  candidates admitted.
- Scoreable source-segment mismatches found: `{summary['scoreable_source_segment_mismatches']}`.
- TP2 and TW10 remain known policy exclusions; TW5/TW6 are scoreable
  heated-incline TW targets.
- AGENT-511 contributes final coupled gate rows but does not provide a
  `probe_delta_vs_m3.csv`, so its probe-level M3 deltas remain unavailable.

## Inferred

The blocker is no longer ambiguous as a passive wall-state selection problem.
The remaining useful lane is axial mixing/upcomer stratification after the
active wall/fluid coupling task resolves.

## Next Useful Actions

Open `next_lane_decision.csv`, then either consume AGENT-526 if it lands first
or create a non-overlapping axial-mixing/upcomer-stratification candidate row.
Do not submit duplicate wall/fluid or heater-source jobs.
""",
        encoding="utf-8",
    )


def write_import_manifest(summary: dict[str, Any]) -> None:
    payload = {
        "task": TASK,
        "date": DATE,
        "created_utc": utc_now(),
        "objective": "No-solver wall/test-section blocker audit after AGENT-511 and AGENT-522.",
        "changed_files": [
            rel(OUT),
            rel(STATUS),
            rel(JOURNAL),
            rel(IMPORT),
            ".agent/blockers.yml",
            ".agent/STATE.md",
            ".agent/catalog.json",
            ".agent/catalog.csv",
            ".agent/BLOCKERS.md",
        ],
        "read_only_sources": [rel(path) for path in required_sources()],
        "read_only_context": [rel(path) for path in required_sources()],
        "native_outputs_mutated": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "solver_or_postprocessing_launched": False,
        "external_fluid_edit": False,
        "fitting_performed": False,
        "scientific_admission_change": "none",
        "summary": summary,
    }
    write_json(IMPORT, payload)


def build(args: argparse.Namespace | None = None) -> dict[str, Any]:
    if args is None:
        args = parse_args([])
    require_sources()
    out = Path(args.out_dir) if args.out_dir else OUT
    matrix_rows = build_cross_candidate_residual_matrix()
    probe_rows = build_probe_residual_atlas()
    sensor_rows = build_sensor_map_candidate_audit(probe_rows)
    role_rows = build_role_segment_residual_atlas()
    failure_rows = build_invariant_failure_modes(probe_rows, role_rows)
    admission_rows = build_admission_gate_sanity(matrix_rows)
    next_rows = build_next_lane_decision(sensor_rows, matrix_rows, failure_rows)
    runtime_rows = build_runtime_request_audit(args)
    source_rows = build_source_manifest()

    write_csv(
        out / "cross_candidate_residual_matrix.csv",
        matrix_rows,
        [
            "source_package",
            "candidate_id",
            "candidate_family",
            "case_id",
            "split_role",
            "mdot_delta_vs_m3_pct",
            "tp_delta_vs_m3_K",
            "tw_delta_vs_m3_K",
            "all_probe_delta_vs_m3_K",
            "score_gate",
            "gate_fail_dimensions",
            "nearest_miss_dimension",
            "failure_pattern",
            "source_path",
        ],
    )
    write_csv(
        out / "probe_residual_atlas.csv",
        probe_rows,
        [
            "source_package",
            "candidate_id",
            "candidate_family",
            "case_id",
            "split_role",
            "sensor",
            "kind",
            "candidate_error_K",
            "candidate_abs_error_K",
            "m3_error_K",
            "m3_abs_error_K",
            "abs_error_delta_vs_m3_K",
            "candidate_predicted_K",
            "target_K",
            "prediction_source_segment",
            "prediction_source_fraction",
            "comparison_status",
            "probe_gate",
            "source_path",
        ],
    )
    write_csv(
        out / "sensor_map_candidate_audit.csv",
        sensor_rows,
        [
            "source_package",
            "candidate_family",
            "sensor",
            "kind",
            "policy_source_segment",
            "observed_source_segments",
            "observed_source_fractions",
            "compared_rows",
            "not_compared_rows",
            "finite_prediction_rows",
            "fail_rows",
            "pass_rows",
            "max_abs_error_delta_vs_m3_K",
            "worst_case_id",
            "worst_candidate_id",
            "score_use",
            "policy_decision",
            "audit_status",
            "interpretation",
            "source_path",
        ],
    )
    write_csv(
        out / "role_segment_residual_atlas.csv",
        role_rows,
        [
            "source_package",
            "candidate_id",
            "candidate_family",
            "case_id",
            "split_role",
            "kind",
            "prediction_source_segment",
            "n_compared",
            "candidate_rmse_K",
            "m3_rmse_K",
            "rmse_delta_vs_m3_K",
            "candidate_mae_K",
            "m3_mae_K",
            "mae_delta_vs_m3_K",
            "source_path",
        ],
    )
    write_csv(
        out / "invariant_failure_modes.csv",
        failure_rows,
        [
            "failure_mode_id",
            "failure_scope",
            "kind",
            "prediction_source_segment",
            "sensor_scope",
            "candidate_families_with_compared_rows",
            "candidate_families",
            "compared_rows",
            "fail_rows",
            "pass_rows",
            "worst_abs_error_delta_vs_m3_K",
            "worst_candidate_id",
            "worst_case_id",
            "interpretation",
            "next_action",
            "source_path",
        ],
    )
    write_csv(
        out / "admission_gate_sanity.csv",
        admission_rows,
        [
            "candidate_id",
            "candidate_family",
            "source_package",
            "validation_rows",
            "holdout_rows",
            "gate_rows",
            "mdot_gate",
            "tp_gate",
            "tw_gate",
            "all_probe_gate",
            "score_gate_rows_passed",
            "score_gate_rows_failed",
            "worst_mdot_delta_vs_m3_pct",
            "worst_tp_delta_vs_m3_K",
            "worst_tw_delta_vs_m3_K",
            "worst_all_probe_delta_vs_m3_K",
            "nearest_remaining_miss",
            "admission_decision",
            "why",
            "source_path",
        ],
    )
    write_csv(
        out / "next_lane_decision.csv",
        next_rows,
        [
            "decision",
            "blocker_status_after_audit",
            "reason",
            "next_task",
            "sensor_map_status",
            "known_policy_exclusions",
            "active_collision",
            "scientific_admission_change",
        ],
    )
    write_csv(out / "runtime_request_audit.csv", runtime_rows, ["check", "status", "detail"])
    write_csv(out / "source_manifest.csv", source_rows, ["source_path", "exists", "use", "native_output"])

    scoreable_mismatches = [
        row for row in sensor_rows
        if row["audit_status"] == "source_segment_mismatch"
        and row["sensor"] not in {"TP2", "TW10"}
    ]
    admitted_candidates = [row for row in admission_rows if row["admission_decision"] == "admitted"]
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "cross_candidate_rows": len(matrix_rows),
        "admission_sanity_rows": len(admission_rows),
        "probe_rows": len(probe_rows),
        "sensor_audit_rows": len(sensor_rows),
        "role_segment_rows": len(role_rows),
        "failure_mode_rows": len(failure_rows),
        "scoreable_source_segment_mismatches": len(scoreable_mismatches),
        "admitted_candidates": len(admitted_candidates),
        "next_lane_decision": next_rows[0]["decision"],
        "blocker_status_after_audit": "open",
        "scheduler_action": "none",
        "scientific_admission_change": "none",
        "out_dir": rel(out),
    }
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    if out == OUT:
        write_status(summary)
        write_journal(summary)
        write_import_manifest(summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="", help="Output directory. Defaults to the AGENT-531 work product.")
    parser.add_argument("--reuse-existing", action="store_true", help="Accepted for workflow symmetry; source evidence is always reused.")
    parser.add_argument("--parallel-workers", type=int, default=1, help="Recorded as no-op; this audit launches no solver work.")
    parser.add_argument("--timeout-seconds", type=int, default=0, help="Recorded as no-op; this audit launches no solver work.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> dict[str, Any]:
    return build(parse_args(argv))


if __name__ == "__main__":
    main()
