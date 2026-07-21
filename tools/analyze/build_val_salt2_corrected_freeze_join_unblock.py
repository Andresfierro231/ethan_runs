#!/usr/bin/env python3
"""Build val_salt2 corrected-freeze join unblock package.

Default mode is existing-evidence only: audit corrected-freeze availability and
emit explicit blocked/missing prediction status. If a caller provides a frozen
prediction CSV with the documented columns, the same builder joins predictions
to the AGENT-500 val_salt2 target contract and computes residual score tables.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-508"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock")
OUT = ROOT / OUT_REL

AGENT500_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress"
TARGETS = AGENT500_DIR / "val_salt2_external_score_targets.csv"
JOIN_CONTRACT = AGENT500_DIR / "val_salt2_prediction_join_contract.csv"
AGENT500_SUMMARY = AGENT500_DIR / "summary.json"
AGENT499_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard"
AGENT499_README = AGENT499_DIR / "README.md"
AGENT499_SUMMARY = AGENT499_DIR / "summary.json"
AGENT499_FREEZE = AGENT499_DIR / "candidate_freeze_manifest.csv"
AGENT499_GATE = AGENT499_DIR / "admission_gate_review.csv"
AGENT498_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder"
AGENT498_SUMMARY = AGENT498_DIR / "summary.json"
AGENT498_ADMISSION = AGENT498_DIR / "candidate_admission_review.csv"
AGENT498_STATUS = ROOT / ".agent/status/2026-07-17_AGENT-498.md"
JUNCTION_READY = AGENT500_DIR / "junction_heat_coefficient_readiness.csv"
CORNER_GATE = AGENT500_DIR / "corner_k_unlock_gate.csv"
PM10_WATCH = AGENT500_DIR / "pm10_holdout_admission_watch.csv"


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


def fmt(value: float | None, digits: int = 8) -> str:
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


def freeze_blocker_status(prediction_csv: Path | None = None) -> tuple[str, str]:
    if prediction_csv is not None:
        return "external_prediction_csv_provided", rel(prediction_csv)
    summary_498 = read_json(AGENT498_SUMMARY)
    decision_498 = summary_498.get("decision", {})
    admitted_498 = decision_498.get("admitted_candidates", [])
    coupled_completed = int(decision_498.get("coupled_completed_rows", 0) or 0)
    if coupled_completed == 0:
        return "freeze_blocked_waiting_for_wall_distribution_ladder", rel(AGENT498_SUMMARY)
    if not admitted_498:
        return "freeze_blocked_no_wall_candidate_admitted", rel(AGENT498_SUMMARY)
    summary_499 = read_json(AGENT499_SUMMARY)
    if int(summary_499.get("final_admitted_candidates", 0) or 0) <= 0:
        return "freeze_blocked_no_corrected_split_final_candidate", rel(AGENT499_SUMMARY)
    return "corrected_split_freeze_available", rel(AGENT499_SUMMARY)


def build_corrected_freeze_source_audit(prediction_csv: Path | None = None) -> list[dict[str, Any]]:
    status, source = freeze_blocker_status(prediction_csv)
    rows: list[dict[str, Any]] = [
        {
            "audit_item": "agent500_target_contract",
            "status": "ready",
            "admitted_for_val_salt2_join": "yes",
            "details": "AGENT-500 emitted 61 val_salt2 external-test targets and join contract.",
            "source_paths": f"{rel(TARGETS)};{rel(JOIN_CONTRACT)}",
        },
        {
            "audit_item": "corrected_freeze_availability",
            "status": status,
            "admitted_for_val_salt2_join": "yes" if prediction_csv is not None or status == "corrected_split_freeze_available" else "no",
            "details": "val_salt2 residuals require a corrected-split freeze trained without val_salt2.",
            "source_paths": source,
        },
    ]
    if AGENT499_FREEZE.exists():
        for row in read_csv(AGENT499_FREEZE):
            rows.append(
                {
                    "audit_item": "agent499_candidate_freeze_manifest",
                    "status": row.get("freeze_status", row.get("admission_status", "reviewed")),
                    "admitted_for_val_salt2_join": "no",
                    "details": row.get("candidate_id", "") + ": " + row.get("blocking_reasons", row.get("reason", "")),
                    "source_paths": rel(AGENT499_FREEZE),
                }
            )
    elif AGENT499_GATE.exists():
        for row in read_csv(AGENT499_GATE):
            rows.append(
                {
                    "audit_item": "agent499_admission_gate",
                    "status": row.get("admission_status", row.get("candidate_status", "reviewed")),
                    "admitted_for_val_salt2_join": "no",
                    "details": row.get("candidate_id", "") + ": " + row.get("blocking_reasons", ""),
                    "source_paths": rel(AGENT499_GATE),
                }
            )
    if AGENT498_ADMISSION.exists():
        for row in read_csv(AGENT498_ADMISSION):
            admitted = row.get("candidate_admitted", row.get("admitted", "false")).lower() in {"true", "yes", "1"}
            rows.append(
                {
                    "audit_item": "agent498_wall_distribution_candidate",
                    "status": row.get("admission_status", row.get("decision", "reviewed")),
                    "admitted_for_val_salt2_join": "yes_if_corrected_freeze_built" if admitted else "no",
                    "details": row.get("candidate_id", "") + ": " + row.get("blocking_reasons", row.get("why", "")),
                    "source_paths": rel(AGENT498_ADMISSION),
                }
            )
    return rows


def prediction_value_for_target(target: dict[str, str], prediction: dict[str, str]) -> tuple[str, str]:
    lane = target["evidence_lane"]
    if lane == "pressure_streamwise_map":
        return prediction.get("predicted_static_p_Pa", prediction.get("prediction_value", "")), "Pa relative to case loop start"
    if lane == "thermal_section_and_junction":
        return prediction.get("predicted_heat_W", prediction.get("prediction_value", "")), "W"
    if lane == "sensor_temperature":
        return prediction.get("predicted_temperature_K", prediction.get("prediction_value", "")), "K"
    return prediction.get("prediction_value", ""), target.get("target_units", "")


def load_predictions(prediction_csv: Path | None) -> dict[tuple[str, str, str], dict[str, str]]:
    if prediction_csv is None:
        return {}
    rows = read_csv(prediction_csv)
    out: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        case_key = row.get("case_key", "val_salt2")
        lane = row.get("evidence_lane", "")
        target_id = row.get("target_id", "")
        if lane and target_id:
            out[(case_key, lane, target_id)] = row
    return out


def build_prediction_join(
    prediction_csv: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    targets = read_csv(TARGETS)
    predictions = load_predictions(prediction_csv)
    freeze_status, freeze_source = freeze_blocker_status(prediction_csv)
    joined_rows: list[dict[str, Any]] = []
    residual_rows: list[dict[str, Any]] = []
    for target in targets:
        key = (target["case_key"], target["evidence_lane"], target["target_id"])
        prediction = predictions.get(key)
        policy_excluded = target["target_id"] in {"TP2", "TW10"} or target.get("score_allowed") == "no"
        target_value = fnum(target.get("target_value"))
        prediction_value_raw = ""
        prediction_units = target.get("target_units", "")
        model_id = ""
        if prediction:
            prediction_value_raw, prediction_units = prediction_value_for_target(target, prediction)
            model_id = prediction.get("prediction_model_id", prediction.get("model_id", ""))
        prediction_value = fnum(prediction_value_raw)
        residual = None
        abs_residual = None
        if policy_excluded:
            score_status = "policy_excluded_not_scored"
        elif prediction is None and prediction_csv is None:
            score_status = freeze_status
        elif prediction is None:
            score_status = "prediction_missing_for_target"
        elif target_value is None or prediction_value is None:
            score_status = "non_numeric_target_or_prediction"
        else:
            residual = prediction_value - target_value
            abs_residual = abs(residual)
            score_status = "joined_scored"
        common = {
            "case_key": target["case_key"],
            "evidence_lane": target["evidence_lane"],
            "target_type": target["target_type"],
            "target_id": target["target_id"],
            "loop_order_index": target.get("loop_order_index", ""),
            "target_value": target.get("target_value", ""),
            "target_units": target.get("target_units", ""),
            "prediction_value": prediction_value_raw,
            "prediction_units": prediction_units,
            "prediction_model_id": model_id,
            "score_status": score_status,
            "training_input_allowed": "no",
            "fit_allowed": "no",
            "model_selection_allowed": "no",
            "runtime_input_allowed": "no",
            "source_paths": f"{target.get('source_paths', '')};{freeze_source}",
        }
        joined_rows.append(
            {
                **common,
                "required_join_key": ";".join(key),
                "prediction_join_status": "joined" if prediction else "not_joined",
            }
        )
        residual_rows.append(
            {
                **common,
                "residual_prediction_minus_target": fmt(residual),
                "abs_residual": fmt(abs_residual),
                "aggregate_score_included": "yes" if score_status == "joined_scored" else "no",
            }
        )
    return joined_rows, residual_rows


def build_score_summary(residual_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_lane: dict[str, list[float]] = defaultdict(list)
    for row in residual_rows:
        if row["score_status"] == "joined_scored":
            residual = fnum(row.get("residual_prediction_minus_target"))
            if residual is not None:
                by_lane[row["evidence_lane"]].append(residual)
    for lane in ("pressure_streamwise_map", "thermal_section_and_junction", "sensor_temperature"):
        residuals = by_lane.get(lane, [])
        if residuals:
            mae = sum(abs(v) for v in residuals) / len(residuals)
            bias = sum(residuals) / len(residuals)
            rmse = math.sqrt(sum(v * v for v in residuals) / len(residuals))
            status = "scored"
        else:
            mae = bias = rmse = None
            status = "no_joined_predictions"
        rows.append(
            {
                "evidence_lane": lane,
                "scored_rows": len(residuals),
                "rmse": fmt(rmse),
                "mae": fmt(mae),
                "bias_prediction_minus_target": fmt(bias),
                "score_status": status,
                "score_use": "blind_external_score_only",
            }
        )
    return rows


def build_next_unblock_queue() -> list[dict[str, Any]]:
    return [
        {
            "priority": "P1",
            "task": "corrected_split_freeze_runner",
            "entry_condition": "admitted wall/test-section/cooler candidate exists under Salt1-4 nominal training split",
            "deliverable": "Frozen prediction CSV matching AGENT-500 join contract for pressure, heat, and sensors.",
            "do_not_do": "Do not tune or select candidates from val_salt2 residuals.",
        },
        {
            "priority": "P2",
            "task": "val_salt2_prediction_join",
            "entry_condition": "Frozen prediction CSV exists and carries prediction_model_id.",
            "deliverable": "Residual scorecard, lane metrics, and overlay figures.",
            "do_not_do": "Do not include TP2 or TW10 in aggregate sensor score.",
        },
        {
            "priority": "P3",
            "task": "junction_metadata_completion",
            "entry_condition": "Need junction heat coefficient review beyond diagnostics.",
            "deliverable": "Comparable area and wall-to-ambient drive metadata for val_salt2 and perturbation buckets.",
            "do_not_do": "Do not fit coefficients from realized wallHeatFlux alone.",
        },
        {
            "priority": "P4",
            "task": "corner_k_repaired_extraction",
            "entry_condition": "Pressure basis and tap design approved.",
            "deliverable": "Branch orientation, straight subtraction, recirculation mask, component isolation, and mesh/GCI gates.",
            "do_not_do": "Do not reuse current negative centerline-subtracted K rows for tuning.",
        },
        {
            "priority": "P5",
            "task": "pm10_terminal_admission_after_jobs",
            "entry_condition": "PM10 solver/harvest jobs terminal and harvested.",
            "deliverable": "PM10 terminal admission and PM5-pattern diagnostics.",
            "do_not_do": "Do not submit duplicate jobs or perform terminal admission while jobs are live/pending.",
        },
    ]


def build_runtime_audit(joined_rows: list[dict[str, Any]], residual_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = sum(row["score_status"] == "joined_scored" for row in residual_rows)
    leakage_bad = [
        row
        for row in joined_rows
        if row["training_input_allowed"] != "no" or row["fit_allowed"] != "no" or row["model_selection_allowed"] != "no"
    ]
    return [
        {
            "audit_item": "val_salt2_external_only",
            "status": "pass_forbidden",
            "evidence": f"{len(joined_rows)} rows retain no training/fit/model-selection permission; leakage rows={len(leakage_bad)}.",
            "source_paths": rel(TARGETS),
        },
        {
            "audit_item": "prediction_join_count",
            "status": "pass_reported",
            "evidence": f"{scored} residual rows scored from joined predictions.",
            "source_paths": rel(JOIN_CONTRACT),
        },
        {
            "audit_item": "tp2_tw10_policy",
            "status": "pass_excluded",
            "evidence": "TP2 and TW10 are excluded from aggregate sensor scoring.",
            "source_paths": rel(TARGETS),
        },
        {
            "audit_item": "native_output_mutation",
            "status": "pass_none",
            "evidence": "Reads existing CSV/JSON artifacts only.",
            "source_paths": rel(Path(__file__)),
        },
        {
            "audit_item": "registry_mutation",
            "status": "pass_none",
            "evidence": "No registry writes.",
            "source_paths": rel(Path(__file__)),
        },
        {
            "audit_item": "scheduler_action",
            "status": "pass_none",
            "evidence": "No sacct, squeue, sbatch, srun, OpenFOAM, or Fluid command is run.",
            "source_paths": rel(Path(__file__)),
        },
        {
            "audit_item": "scientific_admission_change",
            "status": "pass_none",
            "evidence": "Junction, corner-K, PM10, and val_salt2 split states are reported, not changed.",
            "source_paths": f"{rel(JUNCTION_READY)};{rel(CORNER_GATE)};{rel(PM10_WATCH)}",
        },
    ]


def build_source_manifest(prediction_csv: Path | None = None) -> list[dict[str, Any]]:
    sources = [
        TARGETS,
        JOIN_CONTRACT,
        AGENT500_SUMMARY,
        AGENT499_README,
        AGENT499_SUMMARY,
        AGENT499_FREEZE,
        AGENT499_GATE,
        AGENT498_SUMMARY,
        AGENT498_ADMISSION,
        AGENT498_STATUS,
        JUNCTION_READY,
        CORNER_GATE,
        PM10_WATCH,
    ]
    if prediction_csv is not None:
        sources.append(prediction_csv)
    return [{"source_path": rel(path), "exists": path.exists(), "role": "read_only_input"} for path in sources]


def nice_ticks(vmin: float, vmax: float, count: int = 6) -> list[float]:
    if math.isclose(vmin, vmax):
        return [vmin - 1, vmin, vmin + 1]
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


def write_pressure_overlay(path: Path, joined_rows: list[dict[str, Any]]) -> None:
    rows = [row for row in joined_rows if row["evidence_lane"] == "pressure_streamwise_map"]
    rows.sort(key=lambda row: int(row["loop_order_index"]))
    target_values = [float(row["target_value"]) for row in rows if row["target_value"]]
    pred_values = [float(row["prediction_value"]) for row in rows if row["prediction_value"]]
    values = target_values + pred_values
    width, height = 1080, 560
    left, right, top, bottom = 86, 40, 54, 92
    plot_w = width - left - right
    plot_h = height - top - bottom
    ticks = nice_ticks(min(values), max(values), 7) if values else [-1, 0, 1]
    ymin, ymax = min(ticks), max(ticks)

    def x_for(index: int) -> float:
        return left + index / 29.0 * plot_w

    def y_for(value: float) -> float:
        return top + (ymax - value) / (ymax - ymin) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202020}.title{font-size:20px;font-weight:700}.label{font-size:12px}.small{font-size:10px}.grid{stroke:#ddd;stroke-width:1}.axis{stroke:#333;stroke-width:1.2}</style>",
        '<rect x="0" y="0" width="100%" height="100%" fill="white"/>',
        f'<text x="{left}" y="30" class="title">val_salt2 pressure target vs corrected-freeze prediction</text>',
    ]
    for tick in ticks:
        y = y_for(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" class="label">{tick:.0f}</text>')
    for idx in range(30):
        x = x_for(idx)
        if idx % 5 == 0 or idx == 29:
            parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" class="grid"/>')
            parts.append(f'<text x="{x:.1f}" y="{height - 50}" text-anchor="middle" class="small">{idx}</text>')
    if rows:
        target_points = " ".join(f'{x_for(int(row["loop_order_index"])):.1f},{y_for(float(row["target_value"])):.1f}' for row in rows if row["target_value"])
        parts.append(f'<polyline points="{target_points}" fill="none" stroke="#2166ac" stroke-width="2.5"/>')
        if pred_values:
            pred_points = " ".join(
                f'{x_for(int(row["loop_order_index"])):.1f},{y_for(float(row["prediction_value"])):.1f}'
                for row in rows
                if row["prediction_value"]
            )
            parts.append(f'<polyline points="{pred_points}" fill="none" stroke="#b2182b" stroke-width="2.5"/>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<text x="{left}" y="{height - 18}" class="small">Blue = CFD target. Red = frozen 1D prediction when available. val_salt2 remains external-score only.</text>')
    if not pred_values:
        parts.append(f'<text x="{left + 290}" y="{top + 34}" class="label">No corrected-freeze pressure predictions joined.</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_residual_bar_svg(path: Path, residual_rows: list[dict[str, Any]], lane: str, title: str) -> None:
    rows = [row for row in residual_rows if row["evidence_lane"] == lane and row["score_status"] == "joined_scored"]
    width, height = 980, max(300, 72 + 26 * max(len(rows), 3))
    left, top = 170, 54
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202020}.title{font-size:20px;font-weight:700}.label{font-size:11px}.small{font-size:10px}.axis{stroke:#333;stroke-width:1}.grid{stroke:#ddd;stroke-width:1}</style>",
        '<rect x="0" y="0" width="100%" height="100%" fill="white"/>',
        f'<text x="52" y="30" class="title">{esc(title)}</text>',
    ]
    if not rows:
        counts = Counter(row["score_status"] for row in residual_rows if row["evidence_lane"] == lane)
        parts.append(f'<text x="52" y="92" class="label">No joined corrected-freeze predictions. Status counts: {esc(dict(counts))}</text>')
        parts.append("</svg>")
        path.write_text("\n".join(parts) + "\n")
        return
    residuals = [float(row["residual_prediction_minus_target"]) for row in rows]
    limit = max(abs(v) for v in residuals) or 1.0
    scale = 330 / limit
    zero_x = 500
    parts.append(f'<line x1="{zero_x}" y1="{top - 12}" x2="{zero_x}" y2="{height - 38}" class="axis"/>')
    for i, row in enumerate(rows):
        y = top + i * 26
        residual = float(row["residual_prediction_minus_target"])
        x = zero_x if residual >= 0 else zero_x + residual * scale
        w = abs(residual) * scale
        color = "#b2182b" if residual >= 0 else "#2166ac"
        parts.append(f'<text x="{left - 8}" y="{y + 13}" text-anchor="end" class="label">{esc(row["target_id"])}</text>')
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w, 0.6):.1f}" height="16" fill="{color}" opacity="0.86"/>')
        parts.append(f'<text x="{zero_x + (w + 8 if residual >= 0 else -w - 8):.1f}" y="{y + 13}" text-anchor="{"start" if residual >= 0 else "end"}" class="small">{residual:.3g}</text>')
    parts.append(f'<text x="52" y="{height - 14}" class="small">Residual = frozen prediction minus CFD target; external score only.</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_figures(out_dir: Path, joined_rows: list[dict[str, Any]], residual_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    figures = [
        ("val_salt2_pressure_overlay", out_dir / "val_salt2_pressure_overlay.svg"),
        ("val_salt2_sensor_residuals", out_dir / "val_salt2_sensor_residuals.svg"),
        ("val_salt2_thermal_residuals", out_dir / "val_salt2_thermal_residuals.svg"),
    ]
    write_pressure_overlay(figures[0][1], joined_rows)
    write_residual_bar_svg(figures[1][1], residual_rows, "sensor_temperature", "val_salt2 sensor residuals")
    write_residual_bar_svg(figures[2][1], residual_rows, "thermal_section_and_junction", "val_salt2 thermal residuals")
    return [
        {
            "figure_id": figure_id,
            "path": rel(path),
            "status": "written",
            "interpretation": "target_prediction_overlay_or_missing_prediction_status",
        }
        for figure_id, path in figures
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(TARGETS)}
  - {rel(JOIN_CONTRACT)}
  - {rel(AGENT499_README)}
  - {rel(AGENT498_SUMMARY)}
tags: [val-salt2, corrected-freeze, external-score, prediction-join, guardrails]
related:
  - .agent/status/2026-07-17_AGENT-508.md
  - .agent/journal/2026-07-17/val-salt2-corrected-freeze-join-unblock.md
task: AGENT-508
date: 2026-07-17
role: Forward-pred/cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 Corrected-Freeze Join Unblock

This package implements the next unblocking step for `val_salt2`: audit whether
a corrected-split frozen prediction source exists, then join predictions to the
AGENT-500 target contract when a valid source is supplied.

## Result

- Freeze status: `{summary["freeze_status"]}`.
- Target rows reviewed: `{summary["target_rows"]}`.
- Prediction rows joined/scored: `{summary["prediction_rows_joined"]}`.
- Policy-excluded rows: `{summary["policy_excluded_rows"]}`.
- Rows still blocked or missing prediction: `{summary["blocked_or_missing_rows"]}`.
- Score-summary lanes with joined predictions: `{summary["scored_lanes"]}`.

## Interpretation

The current repository state still does not provide a corrected-split final
freeze suitable for blind `val_salt2` scoring. AGENT-498 completed coupled wall
distribution scoring but admitted no wall/test-section candidate, and AGENT-499
therefore reports zero final admitted predictive candidates.

The builder is ready to rerun with `--prediction-csv` once a corrected-split
frozen prediction table exists. Until then, `val_salt2` remains target-ready but
not residual-scored.

## Continue Here

Open `corrected_freeze_source_audit.csv` and
`val_salt2_external_residual_scorecard.csv`. The next productive implementation
is a corrected-split freeze runner trained on Salt1-4 nominal only. Do not use
`val_salt2` errors to tune that runner.
"""
    (out_dir / "README.md").write_text(readme)


def build(output_dir: Path = OUT, prediction_csv: Path | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    freeze_audit = build_corrected_freeze_source_audit(prediction_csv)
    joined_rows, residual_rows = build_prediction_join(prediction_csv)
    score_summary = build_score_summary(residual_rows)
    queue = build_next_unblock_queue()
    runtime = build_runtime_audit(joined_rows, residual_rows)
    sources = build_source_manifest(prediction_csv)
    figures = write_figures(output_dir, joined_rows, residual_rows)

    write_csv(output_dir / "corrected_freeze_source_audit.csv", freeze_audit)
    write_csv(output_dir / "val_salt2_prediction_join.csv", joined_rows)
    write_csv(output_dir / "val_salt2_external_residual_scorecard.csv", residual_rows)
    write_csv(output_dir / "val_salt2_score_summary.csv", score_summary)
    write_csv(output_dir / "next_unblock_queue.csv", queue)
    write_csv(output_dir / "runtime_leakage_audit.csv", runtime)
    write_csv(output_dir / "figure_manifest.csv", figures)
    write_csv(output_dir / "source_manifest.csv", sources)

    freeze_status, _ = freeze_blocker_status(prediction_csv)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(output_dir),
        "prediction_csv": rel(prediction_csv) if prediction_csv is not None else "",
        "freeze_status": freeze_status,
        "target_rows": len(joined_rows),
        "prediction_rows_joined": sum(row["score_status"] == "joined_scored" for row in residual_rows),
        "policy_excluded_rows": sum(row["score_status"] == "policy_excluded_not_scored" for row in residual_rows),
        "blocked_or_missing_rows": sum(
            row["score_status"] not in {"joined_scored", "policy_excluded_not_scored"} for row in residual_rows
        ),
        "scored_lanes": sum(row["score_status"] == "scored" for row in score_summary),
        "figures": len(figures),
        "runtime_audit_rows": len(runtime),
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "generated_index_refresh": "not_run_active_generated_index_scope",
        "scientific_admission_change": "none",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(output_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--prediction-csv", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir, args.prediction_csv), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
