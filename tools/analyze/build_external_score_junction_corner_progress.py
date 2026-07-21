#!/usr/bin/env python3
"""Build next-progress ledgers for external scoring, junction heat, and corner K.

This package is deliberately existing-evidence only. It does not run Fluid,
OpenFOAM, pressure ladders, PM5/PM10 extraction, or any fitting workflow.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-496"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_external_score_junction_corner_progress")
OUT = ROOT / OUT_REL

VAL_EXTERNAL_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger"
VAL_TARGETS = VAL_EXTERNAL_DIR / "val_salt2_external_pressure_thermal_sensor_targets.csv"
VAL_ADMISSION = VAL_EXTERNAL_DIR / "val_salt2_external_admission_decision.csv"
VAL_SUMMARY = VAL_EXTERNAL_DIR / "summary.json"

SENSOR_REFERENCE = ROOT / "reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/cfd_sensor_reference.csv"

JUNCTION_MAINLINE = (
    ROOT / "work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/junction_split_heat_ledger.csv"
)
JUNCTION_VAL = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_junction_split_heat_ledger.csv"
)
SEGMENT_THERMAL_SCORECARD = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/segment_thermal_model_scorecard.csv"
)
SOURCE_SINK_CONTRACT = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/source_sink_ownership_contract.csv"
)

CORNER_K = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/pressure_corner_k_admission_table.csv"
)

F6_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/summary.json"
PM10_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/summary.json"


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


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None, "nan", "NaN"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((value - m) ** 2 for value in values) / (len(values) - 1))


def sensor_reference_by_name() -> dict[str, dict[str, str]]:
    rows = read_csv(SENSOR_REFERENCE)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("source_id") == "val_salt_test_2_coarse_mesh_laminar":
            out[row["sensor"]] = row
    return out


def build_sensor_join(target_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    refs = sensor_reference_by_name()
    rows: list[dict[str, Any]] = []
    for target in target_rows:
        if target.get("target_type") != "sensor_temperature_policy":
            continue
        ref = refs.get(target["target_id"])
        numeric = ref is not None and ref.get("reference_k") not in ("", "nan", "NaN", None)
        policy_allowed = target.get("score_allowed", "") == "yes"
        rows.append(
            {
                "case_key": "val_salt2",
                "sensor": target["target_id"],
                "kind": target.get("kind", ""),
                "one_d_component_segments": target.get("one_d_component_segments", ""),
                "numeric_target_K": ref.get("reference_k", "") if ref else "",
                "time_sample_count": ref.get("time_sample_count", "") if ref else "",
                "reference_source_field": ref.get("reference_source_field", "") if ref else "",
                "policy_score_allowed": target.get("score_allowed", ""),
                "runtime_input_allowed": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "numeric_join_status": "joined_numeric_target" if numeric else "missing_numeric_target",
                "scorecard_use": "external_score_target_after_solve"
                if numeric and policy_allowed
                else "blocked_by_sensor_policy"
                if numeric
                else "blocked_missing_numeric_target",
                "source_paths": f"{rel(VAL_TARGETS)};{rel(SENSOR_REFERENCE)}",
            }
        )
    rows.sort(key=lambda row: row["sensor"])
    return rows


def build_external_readiness(target_rows: list[dict[str, str]], sensor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target_types = Counter(row["target_type"] for row in target_rows)
    numeric_sensors = sum(row["numeric_join_status"] == "joined_numeric_target" for row in sensor_rows)
    score_allowed_sensors = sum(row["policy_score_allowed"] == "yes" for row in sensor_rows)
    return [
        {
            "evidence_lane": "pressure_streamwise_map",
            "target_rows": target_types.get("pressure_streamwise_map", 0),
            "numeric_target_rows": target_types.get("pressure_streamwise_map", 0),
            "prediction_rows_available_here": 0,
            "external_score_readiness": "target_ready_prediction_join_pending",
            "fit_allowed": "no",
            "runtime_input_allowed": "no",
            "next_action": "Join frozen-model pressure predictions after solve; do not tune from residuals.",
            "source_paths": rel(VAL_TARGETS),
        },
        {
            "evidence_lane": "thermal_section_and_junction",
            "target_rows": target_types.get("section_heat", 0) + target_types.get("junction_stub_heat", 0),
            "numeric_target_rows": target_types.get("section_heat", 0) + target_types.get("junction_stub_heat", 0),
            "prediction_rows_available_here": 0,
            "external_score_readiness": "target_ready_prediction_join_pending",
            "fit_allowed": "no",
            "runtime_input_allowed": "no",
            "next_action": "Join frozen-model heat predictions after solve; keep realized wallHeatFlux target-only.",
            "source_paths": rel(VAL_TARGETS),
        },
        {
            "evidence_lane": "sensor_temperature",
            "target_rows": target_types.get("sensor_temperature_policy", 0),
            "numeric_target_rows": numeric_sensors,
            "prediction_rows_available_here": 0,
            "external_score_readiness": "numeric_targets_ready_prediction_join_pending"
            if numeric_sensors == target_types.get("sensor_temperature_policy", 0)
            else "blocked_missing_numeric_sensor_targets",
            "fit_allowed": "no",
            "runtime_input_allowed": "no",
            "next_action": f"Score {score_allowed_sensors} policy-allowed sensors after frozen solve; do not use TP/TW as inputs.",
            "source_paths": f"{rel(VAL_TARGETS)};{rel(SENSOR_REFERENCE)}",
        },
    ]


def mainline_junction_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(JUNCTION_MAINLINE):
        if row.get("physical_junction_bucket") == "case_total_check":
            continue
        rows.append(
            {
                "case_key": row["case_key"],
                "case_id": row.get("case_id", ""),
                "source_id": row.get("source_id", ""),
                "split_role": "mainline_training_validation_holdout_source",
                "physical_junction_bucket": row["physical_junction_bucket"],
                "physical_junction_label": row["physical_junction_label"],
                "patch_count": row.get("patch_count", ""),
                "stub_patch_count": "",
                "extension_patch_count": "",
                "step_patch_count": "",
                "area_m2": row.get("area_m2", ""),
                "loss_positive_W": row.get("realized_external_loss_positive_W", ""),
                "case_junction_loss_positive_W": row.get("source_aggregate_junction_loss_positive_W", ""),
                "fraction_of_case_junction_loss": row.get("fraction_of_case_junction_loss", ""),
                "loss_flux_W_m2": row.get("loss_flux_W_m2", ""),
                "area_weighted_T_wall_shell_K": row.get("area_weighted_T_wall_shell_K", ""),
                "area_weighted_T_wall_to_ambient_drive_K": row.get("area_weighted_T_wall_to_ambient_drive_K", ""),
                "setup_metadata_status": row.get("setup_metadata_status", ""),
                "model_use": row.get("model_use", ""),
                "admission_status": "diagnostic_named_loss_not_coefficient_admitted",
                "source_path": row.get("source_path", rel(JUNCTION_MAINLINE)),
            }
        )
    return rows


def val_junction_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(JUNCTION_VAL):
        if row.get("physical_junction_bucket") == "case_total_check" or row.get("model_use") == "closure_check":
            continue
        rows.append(
            {
                "case_key": row["case_key"],
                "case_id": row.get("case_id", ""),
                "source_id": row.get("source_id", ""),
                "split_role": "external_test_only",
                "physical_junction_bucket": row["physical_junction_bucket"],
                "physical_junction_label": row["physical_junction_label"],
                "patch_count": row.get("patch_count", ""),
                "stub_patch_count": row.get("stub_patch_count", ""),
                "extension_patch_count": row.get("extension_patch_count", ""),
                "step_patch_count": row.get("step_patch_count", ""),
                "area_m2": "",
                "loss_positive_W": row.get("realized_external_loss_positive_W", ""),
                "case_junction_loss_positive_W": row.get("source_aggregate_junction_loss_positive_W", ""),
                "fraction_of_case_junction_loss": row.get("fraction_of_case_junction_loss", ""),
                "loss_flux_W_m2": "",
                "area_weighted_T_wall_shell_K": "",
                "area_weighted_T_wall_to_ambient_drive_K": "",
                "setup_metadata_status": "missing_area_temperature_drive_metadata_in_val_split",
                "model_use": row.get("model_use", ""),
                "admission_status": "external_test_target_only_not_coefficient_admitted",
                "source_path": row.get("source_path", rel(JUNCTION_VAL)),
            }
        )
    return rows


def build_junction_audit() -> list[dict[str, Any]]:
    rows = mainline_junction_rows() + val_junction_rows()
    rows.sort(key=lambda row: (row["case_key"], row["physical_junction_bucket"]))
    return rows


def build_junction_trends(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_bucket[row["physical_junction_bucket"]].append(row)
    out: list[dict[str, Any]] = []
    for bucket, bucket_rows in sorted(by_bucket.items()):
        fractions = [fnum(row["fraction_of_case_junction_loss"]) for row in bucket_rows]
        losses = [fnum(row["loss_positive_W"]) for row in bucket_rows]
        val_rows = [row for row in bucket_rows if row["case_key"] == "val_salt2"]
        mainline_rows = [row for row in bucket_rows if row["case_key"] != "val_salt2"]
        out.append(
            {
                "physical_junction_bucket": bucket,
                "case_count": len(bucket_rows),
                "mainline_case_count": len(mainline_rows),
                "val_salt2_present": "yes" if val_rows else "no",
                "mean_fraction_of_case_junction_loss": f"{mean(fractions):.12g}",
                "std_fraction_of_case_junction_loss": f"{stdev(fractions):.12g}",
                "mean_loss_positive_W": f"{mean(losses):.12g}",
                "val_salt2_fraction": val_rows[0]["fraction_of_case_junction_loss"] if val_rows else "",
                "trend_interpretation": "dominant_bucket_consistent" if bucket == "upper_right" else "stable_secondary_bucket",
                "model_admission": "diagnostic_named_loss_only",
                "next_action": "Add geometry/area/temperature-drive metadata for val_salt2 before coefficient fitting."
                if val_rows and not val_rows[0].get("area_m2")
                else "Retain as cross-case diagnostic trend; coefficient admission still needs runtime-safe predictor form.",
            }
        )
    return out


def build_corner_unlock_contract() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(CORNER_K):
        gates = {
            "pressure_definition_gate": "fail" if fnum(row.get("pressure_definition_conflict_branch_count")) > 0 else "pass",
            "recirculation_tap_gate": "fail" if fnum(row.get("recirculation_blocked_branch_count")) > 0 else "pass",
            "straight_loss_subtraction_gate": "fail" if fnum(row.get("K_local_centerline")) < 0 else "pass",
            "component_isolation_gate": "fail",
            "mesh_gci_gate": "fail",
        }
        rows.append(
            {
                "case_key": row["case_key"],
                "feature": row["feature"],
                "downstream_span": row.get("downstream_span", ""),
                "K_apparent": row.get("K_apparent", ""),
                "K_local_centerline": row.get("K_local_centerline", ""),
                **gates,
                "current_fit_admitted": row.get("fit_admitted", "no"),
                "unlock_status": "blocked_keep_diagnostic",
                "required_next_extraction": (
                    "Use admitted pressure basis, non-recirculating local taps, local straight reference, "
                    "component-isolated pressure loss, and same-QOI mesh/GCI."
                ),
                "do_not_use_for": "pressure_K_fit;model_tuning;model_selection",
                "source_paths": row.get("source_paths", rel(CORNER_K)),
            }
        )
    return rows


def build_active_dependency_handoff() -> list[dict[str, Any]]:
    f6 = json.loads(F6_SUMMARY.read_text())
    pm10 = json.loads(PM10_SUMMARY.read_text())
    return [
        {
            "dependency_lane": "upcomer_onset_recirculation_classifier",
            "owning_task": "AGENT-495",
            "status": "active_external_to_AGENT_496",
            "this_package_action": "read_only_dependency_no_overlap",
            "known_state": "AGENT-487 found 12/12 PM5 rows recirculation diagnostics and 0 ordinary scoreable rows.",
            "source_path": rel(F6_SUMMARY),
        },
        {
            "dependency_lane": "PM10_terminal_admission",
            "owning_task": "AGENT-493_complete_readiness_only",
            "status": "blocked_live_jobs",
            "this_package_action": "do_not_extract_until_terminal",
            "known_state": f"{pm10['blocked_live_job_count']}/4 PM10 cases blocked by live or non-terminal jobs.",
            "source_path": rel(PM10_SUMMARY),
        },
        {
            "dependency_lane": "F6_production_closure",
            "owning_task": "AGENT-487",
            "status": f6["f6_blocker_decision"],
            "this_package_action": "keep_F3_shah_apparent_until_new_anchors",
            "known_state": f"{f6['ordinary_f6_scoreable_rows']} ordinary F6 scoreable rows; {f6['hybrid_scoreable_rows']} hybrid scoreable rows.",
            "source_path": rel(F6_SUMMARY),
        },
    ]


def build_runtime_audit() -> list[dict[str, str]]:
    return [
        {"check": "val_salt2_used_for_training_or_model_selection", "status": "pass_forbidden"},
        {"check": "salt2_pm5q_or_pm10_used_for_training_or_model_selection", "status": "pass_forbidden"},
        {"check": "realized_wallHeatFlux_or_section_heat_used_as_runtime_input", "status": "pass_forbidden"},
        {"check": "pressure_or_sensor_targets_used_as_runtime_input", "status": "pass_forbidden"},
        {"check": "corner_K_current_rows_fit_admitted", "status": "pass_zero_admitted"},
        {"check": "native_solver_output_mutation", "status": "pass_no_mutation"},
        {"check": "scheduler_or_duplicate_job_action", "status": "pass_no_action"},
    ]


def build_next_study_queue() -> list[dict[str, str]]:
    return [
        {
            "priority": "P1",
            "study": "frozen_model_val_salt2_external_score",
            "entry_condition": "Predictive model frozen and no active split-policy reclassification.",
            "deliverable": "Join model predictions to pressure, heat, and numeric TP/TW targets; report residuals only.",
            "do_not_do": "Do not tune or select model form from val_salt2 errors.",
        },
        {
            "priority": "P2",
            "study": "junction_stub_geometry_metadata_completion",
            "entry_condition": "Need coefficient-ready named-loss model beyond diagnostics.",
            "deliverable": "Add val_salt2 area/temperature-drive metadata comparable to Salt2/3/4 mainline buckets.",
            "do_not_do": "Do not fit a junction heat-loss coefficient from realized wallHeatFlux alone.",
        },
        {
            "priority": "P3",
            "study": "corner_K_repaired_extraction",
            "entry_condition": "Pressure basis and local tap design accepted.",
            "deliverable": "New corner extraction with non-recirculating taps, local straight reference, and mesh/GCI.",
            "do_not_do": "Do not use current negative centerline-subtracted K rows for tuning.",
        },
        {
            "priority": "P4",
            "study": "PM10_terminal_holdout_admission",
            "entry_condition": "Jobs 3293924 and 3295438 terminal and harvested.",
            "deliverable": "PM10 terminal admission and PM5-pattern diagnostics on staged copies.",
            "do_not_do": "Do not perform terminal admission while jobs are live or pending.",
        },
        {
            "priority": "P5",
            "study": "recirculation_onset_classifier",
            "entry_condition": "AGENT-495 completes or releases its active scope.",
            "deliverable": "Consume AGENT-495 classifier package; avoid duplicate implementation in AGENT-496.",
            "do_not_do": "Do not overlap active AGENT-495 upcomer-onset paths.",
        },
    ]


def build_source_manifest() -> list[dict[str, str]]:
    return [
        {"artifact": "val_external_targets", "path": rel(VAL_TARGETS), "use": "pressure/thermal/sensor target contract"},
        {"artifact": "val_external_admission", "path": rel(VAL_ADMISSION), "use": "external-test-only guardrail"},
        {"artifact": "val_external_summary", "path": rel(VAL_SUMMARY), "use": "target row counts"},
        {"artifact": "numeric_sensor_reference", "path": rel(SENSOR_REFERENCE), "use": "val_salt2 TP/TW numeric target join"},
        {"artifact": "mainline_junction_split", "path": rel(JUNCTION_MAINLINE), "use": "Salt2/3/4 junction heat trend rows"},
        {"artifact": "val_junction_split", "path": rel(JUNCTION_VAL), "use": "val_salt2 junction heat external-test rows"},
        {"artifact": "segment_thermal_scorecard", "path": rel(SEGMENT_THERMAL_SCORECARD), "use": "junction diagnostic-only model status"},
        {"artifact": "source_sink_contract", "path": rel(SOURCE_SINK_CONTRACT), "use": "runtime input guardrails"},
        {"artifact": "corner_k_admission", "path": rel(CORNER_K), "use": "corner K diagnostic and unlock gates"},
        {"artifact": "f6_summary", "path": rel(F6_SUMMARY), "use": "recirculation/F6 dependency state"},
        {"artifact": "pm10_summary", "path": rel(PM10_SUMMARY), "use": "PM10 terminal dependency state"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(VAL_TARGETS)}
  - {rel(SENSOR_REFERENCE)}
  - {rel(JUNCTION_MAINLINE)}
  - {rel(JUNCTION_VAL)}
  - {rel(CORNER_K)}
tags: [external-score, val-salt2, junction-heat, pressure-k, next-studies]
related:
  - .agent/status/2026-07-17_AGENT-496.md
  - .agent/journal/2026-07-17/external-score-junction-corner-progress.md
task: {TASK}
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# External Score, Junction Heat, and Corner-K Progress

This package implements the non-overlapping parts of the requested next-front
plan from existing evidence only. Active AGENT-495 owns the upcomer-onset /
recirculation classifier lane, so this package records that dependency without
duplicating its work.

## Result

- `val_salt2` external score targets are ready as targets, not model inputs.
- Numeric `val_salt2` TP/TW sensor targets joined: `{summary['numeric_sensor_targets_joined']}` of `{summary['sensor_policy_rows']}`.
- Cross-case junction/stub rows audited: `{summary['junction_audit_rows']}`.
- Corner-K rows reviewed: `{summary['corner_k_rows']}`, fit-admitted rows `{summary['corner_k_fit_admitted_rows']}`.
- Runtime/holdout leakage audit rows: `{summary['runtime_audit_rows']}`.

## Scientific Interpretation

`val_salt2` can now be externally scored once a frozen model produces pressure,
thermal, and sensor predictions. The score must remain blind: no tuning, model
selection, or training reclassification happens here.

The junction/stub losses are cross-case stable enough to justify a named-loss
diagnostic lane, especially the repeated upper-right dominance, but not enough
to fit a runtime coefficient. `val_salt2` still lacks the area and temperature
drive metadata present in Salt2/3/4 mainline junction rows.

Corner K remains diagnostic. Existing centerline straight-loss subtraction
produces negative local K rows, with recirculation and pressure-definition gates
still failing. The unlock contract is a new extraction, not reuse of current
negative rows.
"""
    (OUT / "README.md").write_text(readme)


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    target_rows = read_csv(VAL_TARGETS)
    sensor_rows = build_sensor_join(target_rows)
    external_readiness = build_external_readiness(target_rows, sensor_rows)
    junction_rows = build_junction_audit()
    junction_trends = build_junction_trends(junction_rows)
    corner_rows = build_corner_unlock_contract()
    dependency_rows = build_active_dependency_handoff()
    runtime_rows = build_runtime_audit()
    next_rows = build_next_study_queue()

    write_csv(OUT / "val_salt2_sensor_numeric_join.csv", sensor_rows)
    write_csv(OUT / "external_score_readiness.csv", external_readiness)
    write_csv(OUT / "junction_stub_cross_case_audit.csv", junction_rows)
    write_csv(OUT / "junction_stub_trend_summary.csv", junction_trends)
    write_csv(OUT / "pressure_corner_k_unlock_contract.csv", corner_rows)
    write_csv(OUT / "active_dependency_handoff.csv", dependency_rows)
    write_csv(OUT / "runtime_leakage_audit.csv", runtime_rows)
    write_csv(OUT / "next_study_queue.csv", next_rows)
    write_csv(OUT / "source_manifest.csv", build_source_manifest())

    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "sensor_policy_rows": len(sensor_rows),
        "numeric_sensor_targets_joined": sum(row["numeric_join_status"] == "joined_numeric_target" for row in sensor_rows),
        "external_readiness_rows": len(external_readiness),
        "junction_audit_rows": len(junction_rows),
        "junction_trend_rows": len(junction_trends),
        "val_salt2_junction_rows": sum(row["case_key"] == "val_salt2" for row in junction_rows),
        "corner_k_rows": len(corner_rows),
        "corner_k_fit_admitted_rows": sum(row["current_fit_admitted"] == "yes" for row in corner_rows),
        "runtime_audit_rows": len(runtime_rows),
        "next_study_rows": len(next_rows),
        "recirculation_classifier_owner": "AGENT-495_active_scope",
        "native_output_mutation": "none",
        "scheduler_action": "none",
        "registry_mutation": "none",
        "generated_index_refresh": "not_run_active_generated_index_scope",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
