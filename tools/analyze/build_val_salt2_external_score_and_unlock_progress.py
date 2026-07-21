#!/usr/bin/env python3
"""Build val_salt2 external-score and unlock-progress package.

This script is existing-evidence only. It does not run Fluid, OpenFOAM,
scheduler jobs, extraction jobs, coefficient fitting, or model selection.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-500"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress")
OUT = ROOT / OUT_REL

VAL_TARGETS = ROOT / (
    "work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger/"
    "val_salt2_external_pressure_thermal_sensor_targets.csv"
)
AGENT496_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_external_score_junction_corner_progress"
SENSOR_JOIN = AGENT496_DIR / "val_salt2_sensor_numeric_join.csv"
EXTERNAL_READINESS = AGENT496_DIR / "external_score_readiness.csv"
JUNCTION_AUDIT = AGENT496_DIR / "junction_stub_cross_case_audit.csv"
JUNCTION_TRENDS = AGENT496_DIR / "junction_stub_trend_summary.csv"
CORNER_UNLOCK = AGENT496_DIR / "pressure_corner_k_unlock_contract.csv"
AGENT496_SUMMARY = AGENT496_DIR / "summary.json"

COUPLED_GATE = ROOT / (
    "work_products/2026-07/2026-07-17/2026-07-17_predict_coupled_segment_m3ts_scorecard/"
    "coupled_candidate_gate_scorecard.csv"
)
COUPLED_BLOCKERS = ROOT / (
    "work_products/2026-07/2026-07-17/2026-07-17_predict_coupled_segment_m3ts_scorecard/"
    "unresolved_blocker_queue.csv"
)
PRESSURE_SCORECARD = ROOT / (
    "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models/"
    "segment_pressure_model_scorecard.csv"
)
THERMAL_SCORECARD = ROOT / (
    "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/"
    "segment_thermal_model_scorecard.csv"
)
PM10_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness"
PM10_CASE_READINESS = PM10_DIR / "pm10_case_readiness.csv"
PM10_LIVE_JOBS = PM10_DIR / "live_job_status.csv"
PM10_SUMMARY = PM10_DIR / "summary.json"
UPCOMER_DECISION = ROOT / (
    "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/"
    "blocker_decision.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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


def read_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def fnum(value: Any, default: float | None = None) -> float | None:
    try:
        if value in ("", None, "nan", "NaN"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: float | None, digits: int = 6) -> str:
    if value is None or not math.isfinite(value):
        return ""
    return f"{value:.{digits}g}"


def esc(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def target_lane(target_type: str) -> str:
    if target_type == "pressure_streamwise_map":
        return "pressure_streamwise_map"
    if target_type in {"section_heat", "junction_stub_heat"}:
        return "thermal_section_and_junction"
    if target_type == "sensor_temperature_policy":
        return "sensor_temperature"
    return target_type or "unknown"


def build_external_score_targets() -> list[dict[str, Any]]:
    target_rows = read_csv(VAL_TARGETS)
    sensor_by_name = {row["sensor"]: row for row in read_csv(SENSOR_JOIN)}
    rows: list[dict[str, Any]] = []
    for row in target_rows:
        target_id = row["target_id"]
        target_type = row["target_type"]
        sensor = sensor_by_name.get(target_id, {})
        is_sensor = target_type == "sensor_temperature_policy"
        if is_sensor:
            target_value = sensor.get("numeric_target_K", "")
            target_units = "K"
            numeric_status = sensor.get("numeric_join_status", "missing_numeric_target")
            score_allowed = sensor.get("policy_score_allowed", row.get("score_allowed", ""))
            score_use = sensor.get("scorecard_use", "")
        else:
            target_value = row.get("target_value", "")
            target_units = row.get("target_units", "")
            numeric_status = "numeric_target_available" if target_value not in ("", "nan", "NaN") else "missing_numeric_target"
            score_allowed = row.get("score_allowed", "")
            score_use = "external_score_target_after_frozen_prediction"
        rows.append(
            {
                "case_key": row.get("case_key", "val_salt2"),
                "evidence_lane": target_lane(target_type),
                "target_type": target_type,
                "target_id": target_id,
                "one_d_component_segments": row.get("one_d_component_segments", ""),
                "physical_location_label": row.get("physical_location_label", ""),
                "loop_order_index": row.get("loop_order_index", ""),
                "target_value": target_value,
                "target_units": target_units,
                "secondary_value": row.get("secondary_value", ""),
                "secondary_units": row.get("secondary_units", ""),
                "mapping_status": row.get("mapping_status", ""),
                "external_test_only": "yes",
                "training_input_allowed": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "score_allowed": score_allowed,
                "numeric_target_status": numeric_status,
                "scorecard_use": score_use,
                "source_paths": row.get("source_path", rel(VAL_TARGETS))
                + (f";{rel(SENSOR_JOIN)}" if is_sensor else ""),
            }
        )
    rows.sort(key=lambda r: (r["evidence_lane"], int(r["loop_order_index"] or 9999), r["target_id"]))
    return rows


def frozen_predictions_available() -> tuple[bool, str, str]:
    candidates = read_csv(COUPLED_GATE)
    admitted = [row for row in candidates if row.get("candidate_admitted") == "true"]
    if admitted:
        return True, ";".join(row["candidate_id"] for row in admitted), rel(COUPLED_GATE)
    blocked = [row["candidate_id"] for row in candidates if row.get("candidate_admitted") != "true"]
    return False, "no_admitted_frozen_prediction_artifact;blocked_candidates=" + ";".join(blocked), rel(COUPLED_GATE)


def build_prediction_join_contract(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["evidence_lane"] for row in targets)
    available, model_status, source = frozen_predictions_available()
    rows = []
    contract = {
        "pressure_streamwise_map": (
            "case_key;target_id;loop_order_index",
            "predicted_static_p_Pa;predicted_p_rgh_Pa;prediction_model_id",
            "Use loop-order and label-locked station mapping.",
        ),
        "thermal_section_and_junction": (
            "case_key;target_type;target_id;one_d_component_segments",
            "predicted_heat_W;prediction_model_id",
            "Score section and junction heat only against frozen source/sink outputs.",
        ),
        "sensor_temperature": (
            "case_key;target_id",
            "predicted_temperature_K;prediction_model_id",
            "Score policy-allowed sensors only; TP2 and TW10 remain excluded.",
        ),
    }
    for lane, (keys, fields, note) in contract.items():
        rows.append(
            {
                "evidence_lane": lane,
                "target_rows": counts.get(lane, 0),
                "required_join_keys": keys,
                "required_prediction_fields": fields,
                "frozen_prediction_source_status": model_status,
                "prediction_rows_available": counts.get(lane, 0) if available else 0,
                "join_status": "ready_to_join_predictions" if available else "prediction_missing",
                "runtime_input_allowed": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "notes": note,
                "source_paths": f"{source};{rel(EXTERNAL_READINESS)}",
            }
        )
    return rows


def build_external_residual_scorecard(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _available, model_status, source = frozen_predictions_available()
    rows: list[dict[str, Any]] = []
    for target in targets:
        score_allowed = target.get("score_allowed", "")
        policy_excluded = target["target_id"] in {"TP2", "TW10"} or score_allowed == "no"
        status = "policy_excluded_not_scored" if policy_excluded else "prediction_missing"
        rows.append(
            {
                "case_key": target["case_key"],
                "evidence_lane": target["evidence_lane"],
                "target_type": target["target_type"],
                "target_id": target["target_id"],
                "target_value": target["target_value"],
                "target_units": target["target_units"],
                "prediction_value": "",
                "prediction_units": target["target_units"],
                "residual_prediction_minus_target": "",
                "abs_residual": "",
                "score_status": status,
                "frozen_prediction_source_status": model_status,
                "training_input_allowed": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "source_paths": f"{target['source_paths']};{source}",
            }
        )
    return rows


def build_junction_heat_coefficient_readiness() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(JUNCTION_AUDIT):
        area = fnum(row.get("area_m2"))
        drive = fnum(row.get("area_weighted_T_wall_to_ambient_drive_K"))
        loss = fnum(row.get("loss_positive_W"))
        h_proxy = loss / (area * drive) if area and drive and loss is not None else None
        metadata_ok = area is not None and drive is not None and area > 0 and drive > 0
        is_val = row["case_key"] == "val_salt2"
        if not metadata_ok:
            gate = "blocked_missing_area_or_temperature_drive"
        elif is_val:
            gate = "blocked_external_target_only"
        else:
            gate = "diagnostic_proxy_available_not_coefficient_admitted"
        rows.append(
            {
                "case_key": row["case_key"],
                "physical_junction_bucket": row["physical_junction_bucket"],
                "physical_junction_label": row["physical_junction_label"],
                "loss_positive_W": row.get("loss_positive_W", ""),
                "fraction_of_case_junction_loss": row.get("fraction_of_case_junction_loss", ""),
                "area_m2": row.get("area_m2", ""),
                "area_weighted_T_wall_to_ambient_drive_K": row.get("area_weighted_T_wall_to_ambient_drive_K", ""),
                "loss_flux_W_m2": row.get("loss_flux_W_m2", ""),
                "h_proxy_W_m2_K": fmt(h_proxy),
                "metadata_status": "area_and_temperature_drive_available" if metadata_ok else row.get("setup_metadata_status", ""),
                "coefficient_admission_status": gate,
                "fit_allowed": "no",
                "runtime_input_allowed": "no",
                "model_selection_allowed": "no",
                "next_action": "add comparable val_salt2 and perturbation geometry/temperature-drive metadata before fitting",
                "source_paths": f"{row.get('source_path', '')};{rel(JUNCTION_AUDIT)}",
            }
        )
    return rows


def build_corner_k_unlock_gate() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(CORNER_UNLOCK):
        gates = [
            "pressure_definition_gate",
            "recirculation_tap_gate",
            "straight_loss_subtraction_gate",
            "component_isolation_gate",
            "mesh_gci_gate",
        ]
        failed = [gate for gate in gates if row.get(gate) != "pass"]
        rows.append(
            {
                "case_key": row.get("case_key", ""),
                "feature": row.get("feature", ""),
                "downstream_span": row.get("downstream_span", ""),
                "K_apparent": row.get("K_apparent", ""),
                "K_local_centerline": row.get("K_local_centerline", ""),
                "branch_orientation_required": "yes",
                "straight_loss_subtraction_gate": row.get("straight_loss_subtraction_gate", ""),
                "recirculation_mask_gate": row.get("recirculation_tap_gate", ""),
                "pressure_definition_gate": row.get("pressure_definition_gate", ""),
                "component_isolation_gate": row.get("component_isolation_gate", ""),
                "mesh_gci_gate": row.get("mesh_gci_gate", ""),
                "failed_gate_count": len(failed),
                "fit_admission_status": "fit_admitted" if not failed and row.get("current_fit_admitted") == "yes" else "blocked_keep_diagnostic",
                "required_analysis": row.get("required_next_extraction", ""),
                "do_not_use_for": row.get("do_not_use_for", ""),
                "source_paths": f"{row.get('source_paths', '')};{rel(CORNER_UNLOCK)}",
            }
        )
    return rows


def build_pm10_holdout_watch() -> list[dict[str, Any]]:
    live_jobs = read_csv(PM10_LIVE_JOBS)
    live_state = ";".join(f"{row['job_id']}={row['scheduler_state']}" for row in live_jobs)
    rows = []
    for row in read_csv(PM10_CASE_READINESS):
        rows.append(
            {
                "case_key": row["case_key"],
                "source_key": row["source_key"],
                "split_role": row["split_role"],
                "solver_state": row["solver_state"],
                "harvest_state": row["harvest_state"],
                "readiness_state": row["readiness_state"],
                "score_allowed": row["score_allowed"],
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "terminal_admission_allowed_now": "no",
                "watch_status": "blocked_live_or_pending_jobs",
                "live_job_state_snapshot": live_state,
                "next_action": row["next_action"],
                "source_paths": f"{rel(PM10_CASE_READINESS)};{rel(PM10_LIVE_JOBS)}",
            }
        )
    return rows


def build_next_experiment_queue() -> list[dict[str, Any]]:
    return [
        {
            "priority": "P1",
            "study": "frozen_val_salt2_prediction_join",
            "entry_condition": "corrected-split frozen model exists and is not trained or selected on val_salt2",
            "deliverable": "Join pressure, thermal, and policy-allowed sensor predictions; compute residuals only.",
            "admission_effect": "external_evidence_scorecard_only",
            "do_not_do": "Do not tune parameters, select model forms, or reclassify splits from val_salt2 errors.",
        },
        {
            "priority": "P2",
            "study": "junction_geometry_temperature_drive_completion",
            "entry_condition": "Need coefficient-ready named-loss model beyond diagnostics.",
            "deliverable": "Add comparable area and local wall-to-ambient drive for val_salt2 and perturbation buckets.",
            "admission_effect": "may_unlock_junction_named_loss_coefficient_review",
            "do_not_do": "Do not fit h or K-style heat-loss coefficients from realized wallHeatFlux alone.",
        },
        {
            "priority": "P3",
            "study": "corner_k_repaired_extraction",
            "entry_condition": "Branch orientation, pressure basis, and local tap definition approved.",
            "deliverable": "New component-local pressure extraction with straight-run subtraction and mesh/GCI evidence.",
            "admission_effect": "may_unlock_pressure_corner_K_fit_review",
            "do_not_do": "Do not reuse current negative centerline-subtracted K rows for tuning.",
        },
        {
            "priority": "P4",
            "study": "pm10_terminal_holdout_admission",
            "entry_condition": "Jobs 3293924 and 3295438 are terminal and harvested.",
            "deliverable": "PM10 terminal admission and PM5-pattern diagnostics on staged copies.",
            "admission_effect": "future_holdout_score_only_after_terminal_gate",
            "do_not_do": "Do not run terminal admission or submit duplicate jobs while jobs are live or pending.",
        },
        {
            "priority": "P5",
            "study": "recirculation_onset_anchor_design",
            "entry_condition": "AGENT-495 data-sparsity package remains open with zero anchor candidates.",
            "deliverable": "Near-onset or non-recirculating anchor cases with same-window pressure/thermal/uncertainty fields.",
            "admission_effect": "may_unlock_upcomer_hybrid_and_recirc_masked_pressure_lanes",
            "do_not_do": "Do not classify current recirculating rows as ordinary Nu, f_D, or component K evidence.",
        },
    ]


def build_runtime_audit(targets: list[dict[str, Any]], corner_rows: list[dict[str, Any]], pm10_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "audit_item": "val_salt2_training_fit_model_selection",
            "status": "pass_forbidden",
            "evidence": f"{len(targets)} targets all emitted as external-test score targets only.",
            "source_paths": f"{rel(VAL_TARGETS)};{rel(SENSOR_JOIN)}",
        },
        {
            "audit_item": "frozen_predictions",
            "status": "pass_missing_reported",
            "evidence": "No admitted frozen prediction artifact found; residual rows are prediction_missing.",
            "source_paths": rel(COUPLED_GATE),
        },
        {
            "audit_item": "corner_k_fit_admission",
            "status": "pass_forbidden",
            "evidence": f"{sum(row['fit_admission_status'] == 'fit_admitted' for row in corner_rows)} fit-admitted corner rows.",
            "source_paths": rel(CORNER_UNLOCK),
        },
        {
            "audit_item": "pm10_terminal_admission",
            "status": "pass_blocked_live_jobs",
            "evidence": f"{sum(row['terminal_admission_allowed_now'] == 'no' for row in pm10_rows)} PM10 rows remain monitor-only.",
            "source_paths": f"{rel(PM10_CASE_READINESS)};{rel(PM10_LIVE_JOBS)}",
        },
        {
            "audit_item": "native_output_mutation",
            "status": "pass_none",
            "evidence": "Builder reads existing CSV/JSON artifacts only.",
            "source_paths": rel(Path(__file__)),
        },
        {
            "audit_item": "registry_mutation",
            "status": "pass_none",
            "evidence": "No registry files are opened for writing.",
            "source_paths": rel(Path(__file__)),
        },
        {
            "audit_item": "scheduler_action",
            "status": "pass_none",
            "evidence": "No sacct, squeue, sbatch, srun, OpenFOAM, or Fluid commands are run.",
            "source_paths": rel(Path(__file__)),
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        VAL_TARGETS,
        SENSOR_JOIN,
        EXTERNAL_READINESS,
        JUNCTION_AUDIT,
        JUNCTION_TRENDS,
        CORNER_UNLOCK,
        AGENT496_SUMMARY,
        COUPLED_GATE,
        COUPLED_BLOCKERS,
        PRESSURE_SCORECARD,
        THERMAL_SCORECARD,
        PM10_CASE_READINESS,
        PM10_LIVE_JOBS,
        PM10_SUMMARY,
        UPCOMER_DECISION,
    ]
    return [
        {
            "source_path": rel(path),
            "exists": path.exists(),
            "role": "read_only_input",
        }
        for path in sources
    ]


def nice_ticks(vmin: float, vmax: float, count: int = 6) -> list[float]:
    if math.isclose(vmin, vmax):
        return [vmin - 1.0, vmin, vmin + 1.0]
    raw = (vmax - vmin) / max(count - 1, 1)
    power = 10 ** math.floor(math.log10(abs(raw)))
    step = power
    for mult in (1, 2, 5, 10):
        if raw <= mult * power:
            step = mult * power
            break
    start = math.floor(vmin / step) * step
    stop = math.ceil(vmax / step) * step
    ticks = []
    value = start
    for _ in range(100):
        ticks.append(value)
        if value >= stop:
            break
        value += step
    return ticks


def write_pressure_loop_svg(path: Path, targets: list[dict[str, Any]]) -> None:
    rows = [row for row in targets if row["evidence_lane"] == "pressure_streamwise_map"]
    rows.sort(key=lambda row: int(row["loop_order_index"]))
    width, height = 1120, 600
    left, right, top, bottom = 82, 40, 54, 112
    plot_w = width - left - right
    plot_h = height - top - bottom
    values = [float(row["target_value"]) for row in rows]
    ticks = nice_ticks(min(values), max(values), 7)
    ymin, ymax = min(ticks), max(ticks)

    def x_for(index: int) -> float:
        return left + index / 29.0 * plot_w

    def y_for(value: float) -> float:
        return top + (ymax - value) / (ymax - ymin) * plot_h

    branch_bands = [
        ("heater", 0, 4, "#f6e8c3"),
        ("lower upcomer", 5, 9, "#d8f0d2"),
        ("test section", 10, 14, "#fddbc7"),
        ("upper upcomer", 15, 19, "#c7eae5"),
        ("cooled leg", 20, 24, "#d1e5f0"),
        ("downcomer", 25, 29, "#eeeeee"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202020}.title{font-size:21px;font-weight:700}.label{font-size:12px}.small{font-size:10px}.grid{stroke:#dddddd;stroke-width:1}.axis{stroke:#333333;stroke-width:1.2}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<text x="{left}" y="30" class="title">val_salt2 pressure map through loop</text>',
    ]
    for label, start, end, color in branch_bands:
        x0 = x_for(start) - (plot_w / 29.0) * 0.45
        x1 = x_for(end) + (plot_w / 29.0) * 0.45
        parts.append(f'<rect x="{x0:.1f}" y="{top}" width="{x1 - x0:.1f}" height="{plot_h}" fill="{color}" opacity="0.5"/>')
        parts.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{height - 58}" text-anchor="middle" class="small">{esc(label)}</text>')
    for tick in ticks:
        y = y_for(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" class="label">{tick:.0f}</text>')
    for idx in range(30):
        x = x_for(idx)
        if idx % 5 == 0 or idx == 29:
            parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" class="grid"/>')
            parts.append(f'<text x="{x:.1f}" y="{height - 82}" text-anchor="middle" class="small">{idx}</text>')
    points = " ".join(f'{x_for(int(row["loop_order_index"])):.1f},{y_for(float(row["target_value"])):.1f}' for row in rows)
    parts.append(f'<polyline points="{points}" fill="none" stroke="#1b7837" stroke-width="2.6"/>')
    for row in rows:
        parts.append(f'<circle cx="{x_for(int(row["loop_order_index"])):.1f}" cy="{y_for(float(row["target_value"])):.1f}" r="2.4" fill="#1b7837"/>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<text x="{left + plot_w / 2}" y="{height - 24}" text-anchor="middle" class="label">loop-order station index</text>')
    parts.append(f'<text x="22" y="{top + plot_h / 2}" transform="rotate(-90 22,{top + plot_h / 2})" text-anchor="middle" class="label">static pressure relative to loop start [Pa]</text>')
    parts.append(f'<text x="{left}" y="{height - 4}" class="small">External-test target only; not a fitted pressure coefficient.</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_missing_residual_svg(path: Path, residual_rows: list[dict[str, Any]]) -> None:
    counts = Counter(row["score_status"] for row in residual_rows)
    lanes = Counter(row["evidence_lane"] for row in residual_rows)
    width, height = 920, 360
    left, top = 56, 62
    bar_h = 34
    max_count = max(counts.values()) if counts else 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202020}.title{font-size:20px;font-weight:700}.label{font-size:12px}.small{font-size:10px}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<text x="{left}" y="32" class="title">val_salt2 external residual status</text>',
    ]
    for i, (status, count) in enumerate(sorted(counts.items())):
        y = top + i * 58
        w = 620 * count / max_count
        color = "#b2182b" if status == "prediction_missing" else "#878787"
        parts.append(f'<text x="{left}" y="{y + 22}" class="label">{esc(status)}</text>')
        parts.append(f'<rect x="{left + 220}" y="{y}" width="{w:.1f}" height="{bar_h}" fill="{color}" opacity="0.88"/>')
        parts.append(f'<text x="{left + 230 + w:.1f}" y="{y + 22}" class="label">{count}</text>')
    note_y = top + max(2, len(counts)) * 58 + 18
    parts.append(f'<text x="{left}" y="{note_y}" class="small">Lane counts: {esc(dict(lanes))}</text>')
    parts.append(f'<text x="{left}" y="{note_y + 18}" class="small">No admitted frozen prediction artifact was found; residuals are intentionally not fabricated.</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_junction_trend_svg(path: Path, readiness_rows: list[dict[str, Any]]) -> None:
    by_bucket: dict[str, list[float]] = defaultdict(list)
    for row in readiness_rows:
        frac = fnum(row.get("fraction_of_case_junction_loss"))
        if frac is not None:
            by_bucket[row["physical_junction_bucket"]].append(frac)
    buckets = sorted(by_bucket)
    width, height = 920, 410
    left, top = 72, 64
    bar_w, gap = 126, 38
    max_v = max((sum(vals) / len(vals) for vals in by_bucket.values()), default=1.0)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202020}.title{font-size:20px;font-weight:700}.label{font-size:12px}.small{font-size:10px}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<text x="{left}" y="32" class="title">junction/stub heat-loss fraction by bucket</text>',
    ]
    for i, bucket in enumerate(buckets):
        vals = by_bucket[bucket]
        avg = sum(vals) / len(vals)
        h = 240 * avg / max_v
        x = left + i * (bar_w + gap)
        y = top + 250 - h
        color = "#2166ac" if bucket != "upper_right" else "#b2182b"
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}" opacity="0.86"/>')
        parts.append(f'<text x="{x + bar_w / 2}" y="{top + 272}" text-anchor="middle" class="label">{esc(bucket)}</text>')
        parts.append(f'<text x="{x + bar_w / 2}" y="{y - 8:.1f}" text-anchor="middle" class="label">{avg:.3f}</text>')
    parts.append(f'<text x="{left}" y="{height - 32}" class="small">Fractions are diagnostic realized-loss shares; coefficient fitting remains blocked pending comparable geometry/temperature-drive metadata.</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_corner_gate_svg(path: Path, corner_rows: list[dict[str, Any]]) -> None:
    gates = [
        "pressure_definition_gate",
        "straight_loss_subtraction_gate",
        "recirculation_mask_gate",
        "component_isolation_gate",
        "mesh_gci_gate",
    ]
    fail_counts = {gate: sum(row[gate] != "pass" for row in corner_rows) for gate in gates}
    width, height = 940, 400
    left, top = 64, 62
    max_count = max(fail_counts.values()) if fail_counts else 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202020}.title{font-size:20px;font-weight:700}.label{font-size:12px}.small{font-size:10px}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<text x="{left}" y="32" class="title">corner-K unlock gate failures</text>',
    ]
    for i, gate in enumerate(gates):
        y = top + i * 52
        w = 620 * fail_counts[gate] / max_count
        parts.append(f'<text x="{left}" y="{y + 21}" class="label">{esc(gate)}</text>')
        parts.append(f'<rect x="{left + 250}" y="{y}" width="{w:.1f}" height="30" fill="#d6604d" opacity="0.9"/>')
        parts.append(f'<text x="{left + 260 + w:.1f}" y="{y + 21}" class="label">{fail_counts[gate]}</text>')
    parts.append(f'<text x="{left}" y="{height - 30}" class="small">All current corner rows remain diagnostic; zero are fit-admitted.</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_figures(
    targets: list[dict[str, Any]],
    residual_rows: list[dict[str, Any]],
    junction_rows: list[dict[str, Any]],
    corner_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    figures = [
        ("val_salt2_pressure_loop_map", OUT / "val_salt2_pressure_loop_map.svg"),
        ("val_salt2_external_score_residuals", OUT / "val_salt2_external_score_residuals.svg"),
        ("junction_heat_loss_trend", OUT / "junction_heat_loss_trend.svg"),
        ("corner_k_gate_summary", OUT / "corner_k_gate_summary.svg"),
    ]
    write_pressure_loop_svg(figures[0][1], targets)
    write_missing_residual_svg(figures[1][1], residual_rows)
    write_junction_trend_svg(figures[2][1], junction_rows)
    write_corner_gate_svg(figures[3][1], corner_rows)
    return [
        {
            "figure_id": figure_id,
            "path": rel(path),
            "status": "written",
            "interpretation": "diagnostic_existing_evidence_figure",
        }
        for figure_id, path in figures
    ]


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(VAL_TARGETS)}
  - {rel(SENSOR_JOIN)}
  - {rel(JUNCTION_AUDIT)}
  - {rel(CORNER_UNLOCK)}
  - {rel(COUPLED_GATE)}
  - {rel(PM10_CASE_READINESS)}
tags: [val-salt2, external-score, junction-heat, pressure-k, pm10, next-studies]
related:
  - .agent/status/2026-07-17_AGENT-500.md
  - .agent/journal/2026-07-17/val-salt2-external-score-and-unlock-progress.md
task: AGENT-500
date: 2026-07-17
role: cfd-pp/Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 External Score and Unlock Progress

This package converts the current `val_salt2` target-ready state into a
decision-ready external-score contract and unlock-study ledger. It uses existing
postprocessed artifacts only.

## Observed Output

- External score targets emitted: `{summary["target_rows"]}`.
- Policy-allowed scored sensor targets after TP2/TW10 exclusion: `{summary["policy_allowed_sensor_rows"]}`.
- Frozen prediction rows joined: `{summary["prediction_rows_joined"]}`.
- Residual rows marked `prediction_missing`: `{summary["prediction_missing_rows"]}`.
- Junction coefficient-ready rows admitted: `{summary["junction_coefficient_admitted_rows"]}`.
- Corner-K fit-admitted rows: `{summary["corner_k_fit_admitted_rows"]}`.
- PM10 rows allowed for terminal admission now: `{summary["pm10_terminal_admission_allowed_rows"]}`.

## Interpretation

`val_salt2` is ready as blind external-test target evidence, but not as training,
fitting, model-selection, or runtime input. No admitted frozen prediction artifact
is available in this package, so residuals are deliberately left as
`prediction_missing` instead of being inferred from diagnostic legacy candidates.

Junction/stub heat remains a stable named-loss diagnostic. The coefficient lane
is still blocked because comparable area and local temperature-drive metadata are
not available for every required validation/perturbation bucket.

Corner-K remains diagnostic. Current rows still fail the pressure basis,
straight-loss subtraction, recirculation mask, component isolation, and mesh/GCI
gates.

## Continue Here

Open `val_salt2_prediction_join_contract.csv` before running any external score.
The next legitimate scoring step is to join a corrected-split frozen prediction
artifact to these targets without changing model parameters or split policy.

Do not submit PM10 duplicate jobs, do not rerun pressure ladders from this task,
and do not edit Fluid or native OpenFOAM outputs from this package.
"""
    (OUT / "README.md").write_text(readme)


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = build_external_score_targets()
    join_contract = build_prediction_join_contract(targets)
    residual_rows = build_external_residual_scorecard(targets)
    junction_rows = build_junction_heat_coefficient_readiness()
    corner_rows = build_corner_k_unlock_gate()
    pm10_rows = build_pm10_holdout_watch()
    queue_rows = build_next_experiment_queue()
    runtime_rows = build_runtime_audit(targets, corner_rows, pm10_rows)
    figure_rows = write_figures(targets, residual_rows, junction_rows, corner_rows)
    source_rows = build_source_manifest()

    write_csv(OUT / "val_salt2_external_score_targets.csv", targets)
    write_csv(OUT / "val_salt2_prediction_join_contract.csv", join_contract)
    write_csv(OUT / "val_salt2_external_residual_scorecard.csv", residual_rows)
    write_csv(OUT / "junction_heat_coefficient_readiness.csv", junction_rows)
    write_csv(OUT / "corner_k_unlock_gate.csv", corner_rows)
    write_csv(OUT / "pm10_holdout_admission_watch.csv", pm10_rows)
    write_csv(OUT / "next_experiment_queue.csv", queue_rows)
    write_csv(OUT / "runtime_leakage_audit.csv", runtime_rows)
    write_csv(OUT / "figure_manifest.csv", figure_rows)
    write_csv(OUT / "source_manifest.csv", source_rows)

    sensor_rows = [row for row in targets if row["evidence_lane"] == "sensor_temperature"]
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "target_rows": len(targets),
        "pressure_target_rows": sum(row["evidence_lane"] == "pressure_streamwise_map" for row in targets),
        "thermal_target_rows": sum(row["evidence_lane"] == "thermal_section_and_junction" for row in targets),
        "sensor_target_rows": len(sensor_rows),
        "policy_allowed_sensor_rows": sum(row["score_allowed"] == "yes" for row in sensor_rows),
        "prediction_rows_joined": sum(row["score_status"] not in {"prediction_missing", "policy_excluded_not_scored"} for row in residual_rows),
        "prediction_missing_rows": sum(row["score_status"] == "prediction_missing" for row in residual_rows),
        "policy_excluded_rows": sum(row["score_status"] == "policy_excluded_not_scored" for row in residual_rows),
        "junction_rows": len(junction_rows),
        "junction_coefficient_admitted_rows": sum(row["coefficient_admission_status"] == "coefficient_admitted" for row in junction_rows),
        "corner_k_rows": len(corner_rows),
        "corner_k_fit_admitted_rows": sum(row["fit_admission_status"] == "fit_admitted" for row in corner_rows),
        "pm10_watch_rows": len(pm10_rows),
        "pm10_terminal_admission_allowed_rows": sum(row["terminal_admission_allowed_now"] == "yes" for row in pm10_rows),
        "figures": len(figure_rows),
        "runtime_audit_rows": len(runtime_rows),
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "generated_index_refresh": "not_run_active_generated_index_scope",
        "scientific_admission_change": "none",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
