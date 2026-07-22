#!/usr/bin/env python3
"""Build thesis figure/table panels from completed model-form evidence.

The output is intentionally diagnostic-only. It reformats signed sensor errors,
the model-form ladder, and blocked scorecard gates for thesis insertion without
admitting a closure, fitting a coefficient, or publishing final score values.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

os.environ.setdefault("MPLCONFIGDIR", "/tmp/ethan_runs_matplotlib")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


TASK_ID = "TODO-THESIS-FIGTABLE-D2-H2-DIAGNOSTIC-FIGURE-EXTENSION-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
DATE_PATH = Path("work_products/2026-07/2026-07-22")
PACKAGE = DATE_PATH / "2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels"
OUT_DIR = ROOT / PACKAGE
FIG_ROOT = OUT_DIR / "figures"
FIGURE_CATEGORIES = ("tp_vs_elevation", "tp_tw_vs_elevation", "diagnostics", "operator", "progress")
FIGURE_TYPES = ("svg", "png")

MASTER = (
    ROOT
    / DATE_PATH
    / "2026-07-22_thesis_master_model_form_scoreboard"
)
SHAPE_DISPATCH = (
    ROOT
    / DATE_PATH
    / "2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch"
)
N1_GATE = (
    ROOT
    / DATE_PATH
    / "2026-07-22_thesis_n1_frozen_runtime_legal_candidate_gate"
)
N2_PANELS = (
    ROOT
    / DATE_PATH
    / "2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels"
)
N3_ABLATION = (
    ROOT
    / DATE_PATH
    / "2026-07-22_thesis_n3_thermal_residual_owner_train_ablation"
)
N4_SENSOR = (
    ROOT
    / DATE_PATH
    / "2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table"
)
DIAGNOSTIC_TESTS = (
    ROOT
    / DATE_PATH
    / "2026-07-22_thesis_suggested_model_form_diagnostic_tests"
)
PASSIVE_H2_PACKET = (
    ROOT
    / DATE_PATH
    / "2026-07-22_passive_h2_corrected_operator_predictive_train_packet"
)
PASSIVE_H2_SMOKE = (
    ROOT
    / DATE_PATH
    / "2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke"
)
REFERENCE_PLOT = (
    ROOT
    / DATE_PATH
    / "2026-07-22_TP_TW_vs_elevation"
    / "plot.py"
)
REFERENCE_GEOMETRY = ROOT / "reference" / "geometry_reference.md"
EXPERIMENTAL_TARGET_ROWS = (
    ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-13"
    / "2026-07-13_predictive_forward_v0_solve_case_confirmation"
    / "solve_case_full"
    / "forward_v0_sensor_predictions_experimental.csv"
)

SIGNED_ROWS = MASTER / "figure_ready_signed_sensor_errors.csv"
SCOREBOARD_ERRORS = MASTER / "signed_sensor_errors.csv"
SIGNED_SUMMARY = MASTER / "signed_sensor_error_summary.csv"
LADDER_ROWS = MASTER / "recommended_model_forms_to_try.csv"
MASTER_SUMMARY = MASTER / "summary.json"
SHAPE_SUMMARY = SHAPE_DISPATCH / "summary.json"
BLOCKED_LOGIC = N1_GATE / "blocked_scorecard_logic.csv"
N1_SUMMARY = N1_GATE / "summary.json"
S7_SENSOR_MAP = (
    ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-21"
    / "2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract"
)
SENSOR_COORDINATES = S7_SENSOR_MAP / "sensor_coordinate_ledger.csv"
SENSOR_PROJECTION = N4_SENSOR / "sensor_qoi_projection_table.csv"
DIAGNOSTIC_SENSOR_ERRORS = DIAGNOSTIC_TESTS / "tested_model_form_sensor_errors.csv"
DIAGNOSTIC_MODEL_SCOREBOARD = DIAGNOSTIC_TESTS / "tested_model_form_scoreboard.csv"
PASSIVE_H2_CANDIDATE_MANIFEST = PASSIVE_H2_PACKET / "candidate_manifest.csv"
PASSIVE_H2_FAMILY_LEDGER = PASSIVE_H2_PACKET / "corrected_operator_family_ledger.csv"
PASSIVE_H2_HEAT_LEDGER_DELTA = PASSIVE_H2_PACKET / "predictive_heat_ledger_delta.csv"
PASSIVE_H2_CASE_SUMMARY = PASSIVE_H2_SMOKE / "case_corrected_radiation_summary.csv"

D2_MODEL_FORM_ID = "D2_M3_sensor_kind_offsets_train"
PASSIVE_H2_MODEL_FORM_ID = "PASSIVE-H2-CAND001"

TP_ORDER = ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6"]
TW_ORDER = ["TW1", "TW2", "TW3", "TW4", "TW5", "TW6", "TW7", "TW8", "TW9", "TW10", "TW11"]
TW_TARGET_ORDER = ["TW1", "TW2", "TW3", "TW4", "TW5", "TW6", "TW7", "TW8", "TW9", "TW11"]
TW_TARGET_ORDER_CLOSED = [*TW_TARGET_ORDER, "TW1"]
CASE_ORDER = ["salt_2", "salt_3", "salt_4"]
SENSOR_ORDER = {sensor: index + 1 for index, sensor in enumerate(TP_ORDER + TW_ORDER)}
TP_LABEL_OFFSETS = {
    "TP1": (-34, -10),
    "TP2": (6, -13),
    "TP3": (6, 4),
    "TP4": (6, 4),
    "TP5": (6, 8),
    "TP6": (6, -12),
}
TW_LABEL_OFFSETS = {
    "TW1": (6, 8),
    "TW2": (6, -10),
    "TW3": (6, 6),
    "TW4": (6, -12),
    "TW5": (6, 7),
    "TW6": (6, -10),
    "TW7": (6, 6),
    "TW8": (8, -17),
    "TW9": (6, 10),
    "TW11": (6, -14),
}
TP_PREDICTION_LABEL_OFFSETS = {
    "TP1": (7, -2),
    "TP3": (7, -2),
    "TP4": (7, -2),
    "TP5": (7, -2),
    "TP6": (7, -2),
}
TW_PREDICTION_LABEL_OFFSETS = {
    "TW1": (7, 4),
    "TW2": (7, -2),
    "TW3": (7, -2),
    "TW4": (7, 4),
    "TW5": (7, -2),
    "TW6": (7, -2),
    "TW7": (7, 4),
    "TW8": (7, -2),
    "TW9": (7, 4),
    "TW11": (7, -2),
}
REFERENCE_Y_ABSOLUTE_M = {
    "TP1": 0.6016567809430090,
    "TP2": -0.3127432190569910,
    "TP3": 0.0,
    "TP4": 0.364236,
    "TP5": 0.550164,
    "TP6": 0.9144,
    "TW1": 0.3730567809430090,
    "TW2": 0.1444567809430090,
    "TW3": -0.0841432190569915,
    "TW4": -0.2345574142927440,
    "TW5": -0.1563716095284960,
    "TW6": -0.0781858047642479,
    "TW7": 0.182118,
    "TW8": 0.732282,
    "TW9": 0.8362141952357520,
    "TW10": 0.7580283904715040,
    "TW11": 0.6798425857072560,
}
REFERENCE_TP2_DATUM_M = REFERENCE_Y_ABSOLUTE_M["TP2"]
REFERENCE_ELEVATION_M = {
    sensor: y_absolute - REFERENCE_TP2_DATUM_M
    for sensor, y_absolute in REFERENCE_Y_ABSOLUTE_M.items()
}
REFERENCE_ELEVATION_SOURCE = "reference_plot_Y_ABSOLUTE_M_minus_TP2_datum"


@dataclass(frozen=True)
class FigureResult:
    figure_id: str
    title: str
    svg_path: Path
    png_path: Path
    data_path: Path
    caption: str
    allowed_claim: str
    forbidden_claim: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: Sequence[dict[str, object]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_float(value: str) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def model_dir_name(model_form_id: str) -> str:
    return model_form_id


def figure_slug(value: str) -> str:
    return (
        value.lower()
        .replace("/", "_")
        .replace(" ", "_")
        .replace("+", "plus")
    )


def display_model_form_id(model_form_id: str) -> str:
    if model_form_id == D2_MODEL_FORM_ID:
        return "D2"
    if model_form_id == PASSIVE_H2_MODEL_FORM_ID:
        return "PASSIVE-H2"
    return model_form_id


def save_figure(
    fig: plt.Figure,
    category: str,
    basename: str,
    model_form_id: str | None = None,
) -> tuple[Path, Path]:
    if category not in FIGURE_CATEGORIES:
        raise ValueError(f"unknown figure category: {category}")
    if category == "progress":
        base_dir = FIG_ROOT / "progress"
    else:
        if model_form_id is None:
            raise ValueError(f"model_form_id is required for category {category}")
        base_dir = FIG_ROOT / model_dir_name(model_form_id) / category
    svg_path = base_dir / "svg" / f"{basename}.svg"
    png_path = base_dir / "png" / f"{basename}.png"
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(svg_path, dpi=250, bbox_inches="tight")
    fig.savefig(png_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return svg_path, png_path


def cleanup_legacy_flat_figure_outputs() -> None:
    flat_basenames = [
        "blocked_scorecard_waterfall",
        "m3_signed_sensor_error_shape",
        "m3_tp_temperature_vs_elevation_salt_2",
        "m3_tp_temperature_vs_elevation_salt_3",
        "m3_tp_temperature_vs_elevation_salt_4",
        "m3_tp_tw_temperature_vs_elevation_salt_2",
        "m3_tp_tw_temperature_vs_elevation_salt_3",
        "m3_tp_tw_temperature_vs_elevation_salt_4",
        "model_form_ladder_no_admission",
    ]
    for figure_type in FIGURE_TYPES:
        flat_dir = FIG_ROOT / figure_type
        for basename in flat_basenames:
            path = flat_dir / f"{basename}.{figure_type}"
            if path.exists():
                path.unlink()
        if flat_dir.exists():
            try:
                flat_dir.rmdir()
            except OSError:
                pass
    for legacy_category in ["diagnostics", "operator", "tp_vs_elevation", "tp_tw_vs_elevation"]:
        legacy_dir = FIG_ROOT / legacy_category
        if legacy_dir.exists():
            shutil.rmtree(legacy_dir)


def wrapped(text: str, width: int = 28) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def load_sensor_metadata() -> dict[str, dict[str, str]]:
    coordinate_rows = {row["sensor"]: row for row in read_csv(SENSOR_COORDINATES)}
    projection_rows = {row["sensor"]: row for row in read_csv(SENSOR_PROJECTION)}
    metadata: dict[str, dict[str, str]] = {}
    for sensor in TP_ORDER + TW_ORDER:
        if sensor not in coordinate_rows:
            raise ValueError(f"missing S7 coordinate row for {sensor}")
        if sensor not in projection_rows:
            raise ValueError(f"missing N4 projection row for {sensor}")
        metadata[sensor] = {**coordinate_rows[sensor], **projection_rows[sensor]}
    return metadata


def load_experimental_targets() -> dict[tuple[str, str], dict[str, str]]:
    rows = [
        row
        for row in read_csv(EXPERIMENTAL_TARGET_ROWS)
        if row["case_id"] in CASE_ORDER
        and row["variant_id"] == "F0_current_fluid_sources"
        and row["sensor_source"] == "experimental_fluid_validation"
        and row["sensor"] in set(TP_ORDER + TW_ORDER)
    ]
    by_case_sensor = {(row["case_id"], row["sensor"]): row for row in rows}
    expected = {(case_id, sensor) for case_id in CASE_ORDER for sensor in TP_ORDER + TW_ORDER}
    missing = sorted(expected - set(by_case_sensor))
    extra = sorted(set(by_case_sensor) - expected)
    if missing or extra or len(rows) != len(expected):
        raise ValueError(
            "unexpected experimental target rows: "
            f"rows={len(rows)} expected={len(expected)} missing={missing} extra={extra}"
        )
    for key, row in by_case_sensor.items():
        if as_float(row["target_K"]) is None:
            raise ValueError(f"missing experimental target for {key}")
    return by_case_sensor


def sorted_curve_rows(rows: Sequence[dict[str, object]], order: Sequence[str]) -> list[dict[str, object]]:
    order_index = {sensor: index for index, sensor in enumerate(order)}
    return sorted(rows, key=lambda row: order_index[str(row["sensor_id"])])


def close_tw_curve(rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    closed = list(rows)
    if closed and str(closed[0]["sensor_id"]) == "TW1" and str(closed[-1]["sensor_id"]) == "TW11":
        closed.append(closed[0])
    return closed


def next_target_sensor(sensor: str) -> str:
    if sensor in TP_ORDER:
        index = TP_ORDER.index(sensor)
        return TP_ORDER[index + 1] if index + 1 < len(TP_ORDER) else ""
    if sensor in TW_TARGET_ORDER:
        index = TW_TARGET_ORDER.index(sensor)
        return TW_TARGET_ORDER[index + 1] if index + 1 < len(TW_TARGET_ORDER) else "TW1"
    return ""


def next_prediction_sensor(
    case_id: str,
    model_form_id: str,
    sensor: str,
    by_model_case_sensor: dict[tuple[str, str, str], dict[str, str]],
) -> str:
    next_sensor = next_target_sensor(sensor)
    if not next_sensor:
        return ""
    next_row = by_model_case_sensor.get((model_form_id, case_id, next_sensor))
    if next_row is None:
        return ""
    if as_float(next_row["predicted_K"]) is None or next_row["finite_prediction"].lower() != "true":
        return ""
    return next_sensor


def model_sort_key(model_form_id: str) -> tuple[int, str]:
    digits = "".join(char for char in model_form_id if char.isdigit())
    return (int(digits) if digits else 999, model_form_id)


def scoreboard_model_form_ids(rows: Sequence[dict[str, str]]) -> list[str]:
    return sorted({row["model_form_id"] for row in rows}, key=model_sort_key)


def load_d2_prediction_rows() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_csv(DIAGNOSTIC_SENSOR_ERRORS)
        if row["tested_model_form_id"] == D2_MODEL_FORM_ID
        and row["case_id"] in CASE_ORDER
        and row["sensor"] in set(TP_ORDER + TW_ORDER)
    ]
    return [
        {
            "model_form_id": D2_MODEL_FORM_ID,
            "case_id": row["case_id"],
            "sensor": row["sensor"],
            "legacy_mode_id": row["base_model_form_id"],
            "model_form_label": row["model_form_label"],
            "sensor_kind": row["sensor_kind"],
            "target_K": row["target_K"],
            "predicted_K": row["adjusted_predicted_K"],
            "finite_prediction": "True",
            "admission_status": row["admission_status"],
            "source_path": rel(DIAGNOSTIC_SENSOR_ERRORS),
        }
        for row in rows
    ]


def plot_prediction_segments(
    ax: plt.Axes,
    rows: Sequence[dict[str, object]],
    color: str,
    marker: str,
    linestyle: str,
    label: str,
) -> None:
    current_segment: list[dict[str, object]] = []
    label_used = False
    for row in list(rows) + [{"prediction_available": False}]:
        if row.get("prediction_available") is True and row.get("target_curve_included") is True:
            current_segment.append(row)
            continue
        if current_segment:
            ax.plot(
                [float(item["predicted_K"]) for item in current_segment],
                [float(item["elevation_m"]) for item in current_segment],
                linestyle + marker,
                color=color,
                linewidth=1.45,
                markersize=4.7,
                label=label if not label_used else None,
            )
            label_used = True
            current_segment = []


def build_tp_tw_temperature_elevation_panels() -> list[FigureResult]:
    source_rows = [
        row
        for row in read_csv(SCOREBOARD_ERRORS)
        if row["case_id"] in CASE_ORDER
        and row["sensor"] in set(TP_ORDER + TW_ORDER)
    ]
    source_rows.extend(load_d2_prediction_rows())
    model_form_ids = scoreboard_model_form_ids(source_rows)
    by_model_case_sensor = {
        (row["model_form_id"], row["case_id"], row["sensor"]): row
        for row in source_rows
    }
    metadata = load_sensor_metadata()
    experimental_targets = load_experimental_targets()

    panel_rows: list[dict[str, object]] = []
    for model_form_id in model_form_ids:
        for case_id in CASE_ORDER:
            for sensor in TP_ORDER + TW_ORDER:
                row = by_model_case_sensor.get((model_form_id, case_id, sensor))
                sensor_meta = metadata[sensor]
                elevation_m = REFERENCE_ELEVATION_M[sensor]
                y_absolute_m = REFERENCE_Y_ABSOLUTE_M[sensor]
                target_row = experimental_targets[(case_id, sensor)]
                target_k = as_float(target_row["target_K"])
                if target_k is None:
                    raise ValueError(f"missing target temperature for {case_id} {sensor}")
                scoreboard_reference_target_k = (
                    as_float(row["target_K"]) if row is not None else target_k
                )
                predicted_k = as_float(row["predicted_K"]) if row is not None else None
                if scoreboard_reference_target_k is None:
                    raise ValueError(f"missing scoreboard reference target for {model_form_id} {case_id} {sensor}")
                target_curve_included = sensor != "TW10"
                prediction_available = (
                    predicted_k is not None
                    and row is not None
                    and row["finite_prediction"].lower() == "true"
                )
                target_next = next_target_sensor(sensor) if target_curve_included else ""
                prediction_next = (
                    next_prediction_sensor(case_id, model_form_id, sensor, by_model_case_sensor)
                    if target_curve_included and prediction_available
                    else ""
                )
                missing_reason = ""
                if sensor == "TW10":
                    missing_reason = "excluded_active_hx_shell_state_absent_no_model_prediction"
                elif not prediction_available:
                    missing_source = (
                        "diagnostic_addendum"
                        if model_form_id == D2_MODEL_FORM_ID
                        else "master_scoreboard"
                    )
                    missing_reason = f"{model_form_id}_prediction_missing_in_{missing_source}"
                panel_rows.append(
                    {
                        "figure_id": f"fig_{model_form_id.lower()}_tp_tw_temperature_vs_elevation_{case_id}",
                        "case_id": case_id,
                        "model_form_id": model_form_id,
                        "legacy_mode_id": row["legacy_mode_id"] if row is not None else "",
                        "model_form_label": (
                            row["model_form_label"]
                            if row is not None
                            else "D2 diagnostic TP/TW projection addendum"
                        ),
                        "sensor_id": sensor,
                        "sensor_kind": row["sensor_kind"] if row is not None else sensor[:2],
                        "sensor_order": SENSOR_ORDER[sensor],
                        "target_curve_included": target_curve_included,
                        "prediction_curve_included": target_curve_included and prediction_available,
                        "target_next_sensor_in_plot": target_next,
                        "prediction_next_sensor_in_plot": prediction_next,
                        "elevation_m": elevation_m,
                        "reference_y_absolute_m": y_absolute_m,
                        "elevation_source_field": REFERENCE_ELEVATION_SOURCE,
                        "reference_tp2_datum_m": REFERENCE_TP2_DATUM_M,
                        "native_centroid_y_m": sensor_meta.get("native_centroid_y_m", ""),
                        "registry_y_m": sensor_meta.get("registry_y_m", ""),
                        "coordinate_claim_level": sensor_meta.get("coordinate_claim_level", ""),
                        "placement_class": sensor_meta.get("placement_class", ""),
                        "coordinate_caveat": sensor_meta.get("coordinate_caveat", ""),
                        "one_d_segment_or_state": sensor_meta.get("one_d_segment_or_state", ""),
                        "one_d_fraction_or_marker": sensor_meta.get("one_d_fraction_or_marker", ""),
                        "target_K": target_k,
                        "temperature_target_source": "experimental_fluid_validation",
                        "target_provenance": target_row["target_provenance"],
                        "scoreboard_reference_target_K": scoreboard_reference_target_k,
                        "target_delta_experimental_minus_scoreboard_K": target_k - scoreboard_reference_target_k,
                        "predicted_K": "" if predicted_k is None else predicted_k,
                        "prediction_available": prediction_available,
                        "prediction_label": (
                            f"{display_model_form_id(model_form_id)} {sensor}"
                            if target_curve_included and prediction_available
                            else ""
                        ),
                        "finite_prediction": row["finite_prediction"] if row is not None else "False",
                        "missing_or_excluded_reason": missing_reason,
                        "signed_error_K": "" if predicted_k is None else predicted_k - target_k,
                        "admission_status": (
                            row["admission_status"] if row is not None else "diagnostic_not_admitted"
                        ),
                        "scoreboard_source_path": (
                            row["source_path"] if row is not None else rel(DIAGNOSTIC_SENSOR_ERRORS)
                        ),
                    }
                )

    data_path = OUT_DIR / "tp_tw_temperature_elevation_panel_points.csv"
    write_csv(
        data_path,
        panel_rows,
        [
            "figure_id",
            "case_id",
            "model_form_id",
            "legacy_mode_id",
            "model_form_label",
            "sensor_id",
            "sensor_kind",
            "sensor_order",
            "target_curve_included",
            "prediction_curve_included",
            "target_next_sensor_in_plot",
            "prediction_next_sensor_in_plot",
            "elevation_m",
            "reference_y_absolute_m",
            "elevation_source_field",
            "reference_tp2_datum_m",
            "native_centroid_y_m",
            "registry_y_m",
            "coordinate_claim_level",
            "placement_class",
            "coordinate_caveat",
            "one_d_segment_or_state",
            "one_d_fraction_or_marker",
            "target_K",
            "temperature_target_source",
            "target_provenance",
            "scoreboard_reference_target_K",
            "target_delta_experimental_minus_scoreboard_K",
            "predicted_K",
            "prediction_available",
            "prediction_label",
            "finite_prediction",
            "missing_or_excluded_reason",
            "signed_error_K",
            "admission_status",
            "scoreboard_source_path",
        ],
    )

    tp_data_path = OUT_DIR / "tp_temperature_elevation_panel_points.csv"
    tp_panel_rows = [
        {
            "figure_id": f"fig_{str(row['model_form_id']).lower()}_tp_temperature_vs_elevation_{row['case_id']}",
            "case_id": row["case_id"],
            "model_form_id": row["model_form_id"],
            "legacy_mode_id": row["legacy_mode_id"],
            "model_form_label": row["model_form_label"],
            "sensor_id": row["sensor_id"],
            "sensor_kind": row["sensor_kind"],
            "sensor_order": row["sensor_order"],
            "target_curve_included": row["target_curve_included"],
            "prediction_curve_included": row["prediction_curve_included"],
            "target_next_sensor_in_plot": row["target_next_sensor_in_plot"],
            "prediction_next_sensor_in_plot": row["prediction_next_sensor_in_plot"],
            "elevation_m": row["elevation_m"],
            "reference_y_absolute_m": row["reference_y_absolute_m"],
            "elevation_source_field": row["elevation_source_field"],
            "reference_tp2_datum_m": row["reference_tp2_datum_m"],
            "target_K": row["target_K"],
            "temperature_target_source": row["temperature_target_source"],
            "target_provenance": row["target_provenance"],
            "scoreboard_reference_target_K": row["scoreboard_reference_target_K"],
            "target_delta_experimental_minus_scoreboard_K": row[
                "target_delta_experimental_minus_scoreboard_K"
            ],
            "predicted_K": row["predicted_K"],
            "prediction_available": row["prediction_available"],
            "prediction_label": row["prediction_label"],
            "finite_prediction": row["finite_prediction"],
            "missing_or_excluded_reason": row["missing_or_excluded_reason"],
            "signed_error_K": row["signed_error_K"],
            "admission_status": row["admission_status"],
            "scoreboard_source_path": row["scoreboard_source_path"],
        }
        for row in panel_rows
        if row["sensor_kind"] == "TP"
    ]
    write_csv(
        tp_data_path,
        tp_panel_rows,
        [
            "figure_id",
            "case_id",
            "model_form_id",
            "legacy_mode_id",
            "model_form_label",
            "sensor_id",
            "sensor_kind",
            "sensor_order",
            "target_curve_included",
            "prediction_curve_included",
            "target_next_sensor_in_plot",
            "prediction_next_sensor_in_plot",
            "elevation_m",
            "reference_y_absolute_m",
            "elevation_source_field",
            "reference_tp2_datum_m",
            "target_K",
            "temperature_target_source",
            "target_provenance",
            "scoreboard_reference_target_K",
            "target_delta_experimental_minus_scoreboard_K",
            "predicted_K",
            "prediction_available",
            "prediction_label",
            "finite_prediction",
            "missing_or_excluded_reason",
            "signed_error_K",
            "admission_status",
            "scoreboard_source_path",
        ],
    )

    figures: list[FigureResult] = []
    for model_form_id in model_form_ids:
        for case_id in CASE_ORDER:
            rows = [
                row
                for row in panel_rows
                if row["model_form_id"] == model_form_id and row["case_id"] == case_id
            ]
            model_label = str(rows[0]["model_form_label"])
            display_model_id = display_model_form_id(model_form_id)
            tp_rows = sorted_curve_rows(
                [
                    row
                    for row in rows
                    if row["sensor_kind"] == "TP" and row["target_curve_included"] is True
                ],
                TP_ORDER,
            )
            tw_rows = sorted_curve_rows(
                [
                    row
                    for row in rows
                    if row["sensor_kind"] == "TW" and row["target_curve_included"] is True
                ],
                TW_TARGET_ORDER,
            )
            tw_rows_closed = close_tw_curve(tw_rows)

            plotted_rows = [row for row in rows if row["target_curve_included"] is True]
            all_temperatures = [
                float(row["target_K"])
                for row in plotted_rows
            ] + [
                float(row["predicted_K"])
                for row in plotted_rows
                if row["prediction_available"] is True and row["prediction_curve_included"] is True
            ]
            all_elevations = [float(row["elevation_m"]) for row in plotted_rows]
            x_margin = max(4.0, (max(all_temperatures) - min(all_temperatures)) * 0.08)
            y_margin = max(0.05, (max(all_elevations) - min(all_elevations)) * 0.08)

            fig, ax = plt.subplots(figsize=(9.6, 6.8))
            ax.plot(
                [float(row["target_K"]) for row in tp_rows],
                [float(row["elevation_m"]) for row in tp_rows],
                "-o",
                color="blue",
                linewidth=1.8,
                markersize=5.2,
                label="TP target",
            )
            ax.plot(
                [float(row["target_K"]) for row in tw_rows_closed],
                [float(row["elevation_m"]) for row in tw_rows_closed],
                "--s",
                color="green",
                linewidth=1.55,
                markersize=4.7,
                label="TW target",
            )
            plot_prediction_segments(ax, tp_rows, "cornflowerblue", "^", ":", f"{display_model_id} TP prediction")
            plot_prediction_segments(ax, tw_rows_closed, "mediumseagreen", "D", ":", f"{display_model_id} TW prediction")

            for row in tp_rows:
                sensor = str(row["sensor_id"])
                ax.annotate(
                    sensor,
                    (float(row["target_K"]), float(row["elevation_m"])),
                    xytext=TP_LABEL_OFFSETS[sensor],
                    textcoords="offset points",
                    fontsize=8,
                    color="blue",
                )
                if row["prediction_available"] is False:
                    ax.annotate(
                        f"{display_model_id} missing",
                        (float(row["target_K"]), float(row["elevation_m"])),
                        xytext=(12, 16),
                        textcoords="offset points",
                        fontsize=7.5,
                        color="0.25",
                    )
                elif row["prediction_curve_included"] is True:
                    ax.annotate(
                        str(row["prediction_label"]),
                        (float(row["predicted_K"]), float(row["elevation_m"])),
                        xytext=TP_PREDICTION_LABEL_OFFSETS[sensor],
                        textcoords="offset points",
                        fontsize=7.0,
                        color="cornflowerblue",
                    )

            for row in tw_rows:
                sensor = str(row["sensor_id"])
                ax.annotate(
                    sensor,
                    (float(row["target_K"]), float(row["elevation_m"])),
                    xytext=TW_LABEL_OFFSETS[sensor],
                    textcoords="offset points",
                    fontsize=7.5,
                    color="green",
                )
                if row["prediction_curve_included"] is True:
                    ax.annotate(
                        str(row["prediction_label"]),
                        (float(row["predicted_K"]), float(row["elevation_m"])),
                        xytext=TW_PREDICTION_LABEL_OFFSETS[sensor],
                        textcoords="offset points",
                        fontsize=6.8,
                        color="mediumseagreen",
                    )
            ax.text(
                0.985,
                0.025,
                "TW10 retained in CSV; omitted from plot range",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=7.3,
                color="0.25",
            )

            ax.set_xlim(min(all_temperatures) - x_margin, max(all_temperatures) + x_margin)
            ax.set_ylim(min(all_elevations) - y_margin, max(all_elevations) + y_margin)
            ax.set_title(
                f"Experimental TP/TW Targets + {display_model_id} vs Elevation "
                f"({case_id.replace('_', ' ').title()})"
            )
            ax.set_xlabel("Temperature (K)")
            ax.set_ylabel("Elevation above TP2 datum (m; reference geometry)")
            ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.16), ncol=4, fontsize=8)
            ax.grid(False)

            basename = f"{figure_slug(model_form_id)}_tp_tw_temperature_vs_elevation_{case_id}"
            svg_path, png_path = save_figure(fig, "tp_tw_vs_elevation", basename, model_form_id)
            figures.append(
                FigureResult(
                    figure_id=f"fig_{figure_slug(model_form_id)}_tp_tw_temperature_vs_elevation_{case_id}",
                    title=f"{model_form_id} TP/TW temperature vs elevation, {case_id}",
                    svg_path=svg_path,
                    png_path=png_path,
                    data_path=data_path,
                    caption=(
                        f"Experimental TP1-TP6 and TW1-TW9/TW11 target temperatures with "
                        f"available {model_form_id} predictions versus reference-geometry elevation "
                        f"above the TP2 datum for {case_id.replace('_', ' ').title()}. "
                        f"Model definition: {model_label}. TP2 is retained as a target "
                        "with missing model prediction; TW10 is "
                        "retained in the CSV but omitted from the plotted curve/range. "
                        f"The TW curve closes from TW11 back to TW1, and available {model_form_id} "
                        f"prediction markers are labeled explicitly as {model_form_id} sensors."
                    ),
                    allowed_claim=(
                        f"This panel shows experimental TP/TW targets and legacy {model_form_id} "
                        "prediction profiles on the reference-geometry elevation basis, "
                        "with scoreboard targets retained only as audit columns."
                    ),
                    forbidden_claim=(
                        f"Do not report {model_form_id} as a frozen final prediction, validation score, "
                        "closure admission, or complete TP/TW predictive curve because TP2 "
                        f"and TW10 are unavailable to {model_form_id}."
                    ),
                )
            )

            fig_tp, ax_tp = plt.subplots(figsize=(7.4, 5.9))
            ax_tp.plot(
                [float(row["target_K"]) for row in tp_rows],
                [float(row["elevation_m"]) for row in tp_rows],
                "-o",
                color="blue",
                linewidth=1.8,
                markersize=5.2,
                label="TP target",
            )
            plot_prediction_segments(ax_tp, tp_rows, "cornflowerblue", "^", ":", f"{display_model_id} TP prediction")
            tp_temperatures = [
                float(row["target_K"])
                for row in tp_rows
            ] + [
                float(row["predicted_K"])
                for row in tp_rows
                if row["prediction_available"] is True and row["prediction_curve_included"] is True
            ]
            tp_elevations = [float(row["elevation_m"]) for row in tp_rows]
            tp_x_margin = max(3.0, (max(tp_temperatures) - min(tp_temperatures)) * 0.10)
            tp_y_margin = max(0.05, (max(tp_elevations) - min(tp_elevations)) * 0.08)
            for row in tp_rows:
                sensor = str(row["sensor_id"])
                ax_tp.annotate(
                    sensor,
                    (float(row["target_K"]), float(row["elevation_m"])),
                    xytext=TP_LABEL_OFFSETS[sensor],
                    textcoords="offset points",
                    fontsize=8,
                    color="blue",
                )
                if row["prediction_available"] is False:
                    ax_tp.annotate(
                        f"{display_model_id} missing",
                        (float(row["target_K"]), float(row["elevation_m"])),
                        xytext=(12, 16),
                        textcoords="offset points",
                        fontsize=7.5,
                        color="0.25",
                    )
                elif row["prediction_curve_included"] is True:
                    ax_tp.annotate(
                        str(row["prediction_label"]),
                        (float(row["predicted_K"]), float(row["elevation_m"])),
                        xytext=TP_PREDICTION_LABEL_OFFSETS[sensor],
                        textcoords="offset points",
                        fontsize=7.0,
                        color="cornflowerblue",
                    )
            ax_tp.set_xlim(min(tp_temperatures) - tp_x_margin, max(tp_temperatures) + tp_x_margin)
            ax_tp.set_ylim(min(tp_elevations) - tp_y_margin, max(tp_elevations) + tp_y_margin)
            ax_tp.set_title(
                f"Experimental TP Targets + {display_model_id} vs Elevation "
                f"({case_id.replace('_', ' ').title()})"
            )
            ax_tp.set_xlabel("Temperature (K)")
            ax_tp.set_ylabel("Elevation above TP2 datum (m; reference geometry)")
            ax_tp.legend(loc="lower center", bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=8)
            ax_tp.grid(False)
            tp_basename = f"{figure_slug(model_form_id)}_tp_temperature_vs_elevation_{case_id}"
            tp_svg_path, tp_png_path = save_figure(fig_tp, "tp_vs_elevation", tp_basename, model_form_id)
            figures.append(
                FigureResult(
                    figure_id=f"fig_{figure_slug(model_form_id)}_tp_temperature_vs_elevation_{case_id}",
                    title=f"{model_form_id} TP temperature vs elevation, {case_id}",
                    svg_path=tp_svg_path,
                    png_path=tp_png_path,
                    data_path=tp_data_path,
                    caption=(
                        f"Experimental TP1-TP6 target temperatures with available {model_form_id} "
                        f"predictions versus reference-geometry elevation above the "
                        f"TP2 datum for {case_id.replace('_', ' ').title()}. TP5 "
                        f"connects to TP6; TP2 is retained as a missing-{model_form_id} target."
                    ),
                    allowed_claim=(
                        f"This panel isolates the TP target and {model_form_id} prediction profile "
                        "from the combined TP/TW figure on the same corrected basis."
                    ),
                    forbidden_claim=(
                        "Do not report the TP-only panel as final predictive accuracy, "
                        "closure admission, or a frozen candidate score."
                    ),
                )
            )

    return figures


def build_signed_error_panels() -> list[FigureResult]:
    source_rows = read_csv(SIGNED_ROWS)
    experimental_targets = load_experimental_targets()
    finite_rows = [
        row
        for row in source_rows
        if row["facet_case"] in CASE_ORDER
        and row["finite_prediction"].lower() == "true"
    ]
    order_index = {sensor: idx + 1 for idx, sensor in enumerate(TP_ORDER + TW_ORDER)}
    panel_rows: list[dict[str, object]] = []
    for row in finite_rows:
        sensor = row["y_sensor"]
        target_row = experimental_targets[(row["facet_case"], sensor)]
        target_k = float(target_row["target_K"])
        predicted_k = float(row["predicted_K"])
        scoreboard_reference_target_k = float(row["target_K"])
        panel_rows.append(
            {
                "figure_id": f"fig_{row['x_model_form'].lower()}_signed_sensor_error_shape",
                "model_form": row["x_model_form"],
                "case_id": row["facet_case"],
                "sensor_kind": row["facet_sensor_kind"],
                "sensor_id": sensor,
                "sensor_index": order_index[sensor],
                "signed_error_K": predicted_k - target_k,
                "target_K": target_k,
                "temperature_target_source": "experimental_fluid_validation",
                "scoreboard_reference_target_K": scoreboard_reference_target_k,
                "target_delta_experimental_minus_scoreboard_K": target_k - scoreboard_reference_target_k,
                "predicted_K": predicted_k,
                "admission_status": row["admission_status"],
            }
        )
    for row in load_d2_prediction_rows():
        sensor = row["sensor"]
        target_row = experimental_targets[(row["case_id"], sensor)]
        target_k = float(target_row["target_K"])
        predicted_k = float(row["predicted_K"])
        scoreboard_reference_target_k = float(row["target_K"])
        panel_rows.append(
            {
                "figure_id": f"fig_{figure_slug(row['model_form_id'])}_signed_sensor_error_shape",
                "model_form": row["model_form_id"],
                "case_id": row["case_id"],
                "sensor_kind": row["sensor_kind"],
                "sensor_id": sensor,
                "sensor_index": order_index[sensor],
                "signed_error_K": predicted_k - target_k,
                "target_K": target_k,
                "temperature_target_source": "experimental_fluid_validation",
                "scoreboard_reference_target_K": scoreboard_reference_target_k,
                "target_delta_experimental_minus_scoreboard_K": target_k - scoreboard_reference_target_k,
                "predicted_K": predicted_k,
                "admission_status": row["admission_status"],
            }
        )
    model_form_ids = sorted({str(row["model_form"]) for row in panel_rows}, key=model_sort_key)

    data_path = OUT_DIR / "signed_error_panel_points.csv"
    write_csv(
        data_path,
        panel_rows,
        [
            "figure_id",
            "model_form",
            "case_id",
            "sensor_kind",
            "sensor_id",
            "sensor_index",
            "signed_error_K",
            "target_K",
            "temperature_target_source",
            "scoreboard_reference_target_K",
            "target_delta_experimental_minus_scoreboard_K",
            "predicted_K",
            "admission_status",
        ],
    )

    figures: list[FigureResult] = []
    xtick_labels = TP_ORDER + TW_ORDER
    xtick_positions = [order_index[sensor] for sensor in xtick_labels]
    for model_form_id in model_form_ids:
        model_rows = [row for row in panel_rows if row["model_form"] == model_form_id]
        fig, axes = plt.subplots(1, 3, figsize=(12.0, 5.6), sharey=True)
        for ax, case_id in zip(axes, CASE_ORDER, strict=True):
            case_rows = [row for row in model_rows if row["case_id"] == case_id]
            for kind, marker, linestyle, color, label in [
                ("TP", "o", "-", "blue", "TP"),
                ("TW", "s", "--", "green", "TW"),
            ]:
                rows_by_sensor = {row["sensor_id"]: row for row in case_rows if row["sensor_kind"] == kind}
                sensors = TP_ORDER if kind == "TP" else TW_ORDER
                current_x: list[int] = []
                current_y: list[float] = []
                label_used = False
                for sensor in sensors + [""]:
                    row = rows_by_sensor.get(sensor)
                    if row is not None:
                        current_x.append(int(row["sensor_index"]))
                        current_y.append(float(row["signed_error_K"]))
                        continue
                    if current_x:
                        ax.plot(
                            current_x,
                            current_y,
                            linestyle + marker,
                            color=color,
                            linewidth=1.7 if kind == "TP" else 1.5,
                            markersize=5.0,
                            label=label if not label_used else None,
                        )
                        label_used = True
                        current_x = []
                        current_y = []
            ax.axhline(0.0, color="0.25", linewidth=1.0)
            ax.axvline(6.5, color="0.75", linewidth=0.8)
            ax.set_title(case_id.replace("_", " ").title())
            ax.set_xlabel("Sensor")
            ax.set_xticks(xtick_positions)
            ax.set_xticklabels(xtick_labels, rotation=45, ha="right", fontsize=7.5)
            ax.grid(False)

        axes[0].set_ylabel("Signed error, prediction - target (K)")
        axes[0].legend(loc="upper right")
        fig.suptitle(f"{model_form_id} Signed TP/TW Sensor Errors")
        basename = f"{figure_slug(model_form_id)}_signed_sensor_error_shape"
        svg_path, png_path = save_figure(fig, "diagnostics", basename, model_form_id)

        figures.append(
            FigureResult(
                figure_id=f"fig_{figure_slug(model_form_id)}_signed_sensor_error_shape",
                title=f"{model_form_id} signed TP/TW sensor errors",
                svg_path=svg_path,
                png_path=png_path,
                data_path=data_path,
                caption=(
                    f"Signed TP/TW errors for {model_form_id} across Salt2-Salt4, "
                    "recomputed against the experimental validation target "
                    "temperatures. Negative values show underprediction. Rows are "
                    "legacy numeric context only and are not a frozen final score."
                ),
                allowed_claim=(
                    f"{model_form_id} can be compared as a legacy numeric model-form "
                    "shape diagnostic against the experimental TP/TW targets."
                ),
                forbidden_claim=(
                    "Do not report these rows as final predictive accuracy, validation, "
                    "holdout, external-test scoring, or closure admission."
                ),
            )
        )
    return figures


def build_passive_h2_operator_panels() -> list[FigureResult]:
    case_rows = read_csv(PASSIVE_H2_CASE_SUMMARY)
    family_rows = read_csv(PASSIVE_H2_FAMILY_LEDGER)
    projection_rows = read_csv(PASSIVE_H2_HEAT_LEDGER_DELTA)
    manifest_row = read_csv(PASSIVE_H2_CANDIDATE_MANIFEST)[0]

    case_panel_rows = [
        {
            "figure_id": "fig_passive_h2_case_heat_path_operator",
            "candidate_id": PASSIVE_H2_MODEL_FORM_ID,
            "case_id": row["case_id"],
            "baseline_qambient_total_W": row["baseline_qambient_total_W"],
            "baseline_qhx_total_W": row["baseline_qhx_total_W"],
            "corrected_outer_surface_convection_W": row["corrected_outer_surface_convection_W"],
            "corrected_outer_surface_radiation_W": row["corrected_outer_surface_radiation_W"],
            "corrected_outer_surface_total_W": row["corrected_outer_surface_total_W"],
            "corrected_radiation_fraction_of_naive": row["corrected_radiation_fraction_of_naive"],
            "corrected_total_fraction_of_baseline_qambient": row[
                "corrected_total_fraction_of_baseline_qambient"
            ],
            "numeric_q_loss_release": row["numeric_q_loss_release"],
            "admission_or_score": row["admission_or_score"],
        }
        for row in case_rows
    ]
    family_panel_rows = [
        {
            "figure_id": "fig_passive_h2_segment_family_heat_path_operator",
            "candidate_id": row["candidate_id"],
            "case_id": row["case_id"],
            "source_family": row["source_family"],
            "corrected_q_conv_W": row["corrected_q_conv_W"],
            "corrected_q_rad_W": row["corrected_q_rad_W"],
            "corrected_q_total_W": row["corrected_q_total_W"],
            "external_bc_split_role": row["external_bc_split_role"],
            "recommended_fluid_mapping": row["recommended_fluid_mapping"],
            "admission_or_score": row["admission_or_score"],
        }
        for row in family_rows
        if row["candidate_id"] == PASSIVE_H2_MODEL_FORM_ID
    ]
    projection_panel_rows = [
        {
            "figure_id": "fig_passive_h2_global_patch_rejection_operator",
            "candidate_id": PASSIVE_H2_MODEL_FORM_ID,
            "case_id": row["case_id"],
            "hypothesis": row["hypothesis"],
            "delta_qambient_W": row["delta_qambient_W"],
            "extrapolation_factor": row["extrapolation_factor"],
            "inside_local_hA_response_envelope": row["inside_local_hA_response_envelope"],
            "predictive_claim_allowed": row["predictive_claim_allowed"],
            "projection_status": row["projection_status"],
        }
        for row in projection_rows
    ]

    case_data_path = OUT_DIR / "passive_h2_operator_case_points.csv"
    family_data_path = OUT_DIR / "passive_h2_operator_family_points.csv"
    projection_data_path = OUT_DIR / "passive_h2_operator_global_patch_points.csv"
    write_csv(
        case_data_path,
        case_panel_rows,
        [
            "figure_id",
            "candidate_id",
            "case_id",
            "baseline_qambient_total_W",
            "baseline_qhx_total_W",
            "corrected_outer_surface_convection_W",
            "corrected_outer_surface_radiation_W",
            "corrected_outer_surface_total_W",
            "corrected_radiation_fraction_of_naive",
            "corrected_total_fraction_of_baseline_qambient",
            "numeric_q_loss_release",
            "admission_or_score",
        ],
    )
    write_csv(
        family_data_path,
        family_panel_rows,
        [
            "figure_id",
            "candidate_id",
            "case_id",
            "source_family",
            "corrected_q_conv_W",
            "corrected_q_rad_W",
            "corrected_q_total_W",
            "external_bc_split_role",
            "recommended_fluid_mapping",
            "admission_or_score",
        ],
    )
    write_csv(
        projection_data_path,
        projection_panel_rows,
        [
            "figure_id",
            "candidate_id",
            "case_id",
            "hypothesis",
            "delta_qambient_W",
            "extrapolation_factor",
            "inside_local_hA_response_envelope",
            "predictive_claim_allowed",
            "projection_status",
        ],
    )

    figures: list[FigureResult] = []
    x_positions = list(range(len(case_panel_rows)))
    x_labels = [str(row["case_id"]).replace("_", " ").title() for row in case_panel_rows]
    conv = [float(row["corrected_outer_surface_convection_W"]) for row in case_panel_rows]
    rad = [float(row["corrected_outer_surface_radiation_W"]) for row in case_panel_rows]
    baseline = [float(row["baseline_qambient_total_W"]) for row in case_panel_rows]

    fig, ax = plt.subplots(figsize=(7.6, 5.3))
    ax.bar(x_positions, conv, color="blue", label="Corrected convection")
    ax.bar(x_positions, rad, bottom=conv, color="green", label="Corrected radiation")
    ax.plot(x_positions, baseline, "s--", color="0.25", linewidth=1.4, label="Current qambient")
    for x_value, total in zip(x_positions, [c + r for c, r in zip(conv, rad, strict=True)], strict=True):
        ax.annotate(f"{total:.1f} W", (x_value, total), xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=8)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_labels)
    ax.set_ylabel("Heat rate (W)")
    ax.set_title("PASSIVE-H2 Corrected Outer-Surface Operator")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(False)
    svg_path, png_path = save_figure(
        fig,
        "operator",
        "passive_h2_case_heat_path_operator",
        PASSIVE_H2_MODEL_FORM_ID,
    )
    figures.append(
        FigureResult(
            figure_id="fig_passive_h2_case_heat_path_operator",
            title="PASSIVE-H2 corrected case heat-path operator",
            svg_path=svg_path,
            png_path=png_path,
            data_path=case_data_path,
            caption=(
                "PASSIVE-H2 corrected outer-surface convection and radiation heat "
                "rates by case, compared with the current global qambient ledger. "
                "The corrected operator is development evidence only."
            ),
            allowed_claim=(
                "PASSIVE-H2 corrects the passive-boundary heat-path basis and "
                "produces nonzero setup-backed radiation/operator magnitudes."
            ),
            forbidden_claim=(
                "Do not treat corrected heat rates as a released numeric q-loss, "
                "protected score, closure admission, or frozen predictive model."
            ),
        )
    )

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 5.4), sharey=True)
    for ax, case_id in zip(axes, CASE_ORDER, strict=True):
        rows = [row for row in family_panel_rows if row["case_id"] == case_id]
        labels = [str(row["source_family"]) for row in rows]
        conv_values = [float(row["corrected_q_conv_W"]) for row in rows]
        rad_values = [float(row["corrected_q_rad_W"]) for row in rows]
        positions = list(range(len(rows)))
        ax.bar(positions, conv_values, color="blue", label="Convection")
        ax.bar(positions, rad_values, bottom=conv_values, color="green", label="Radiation")
        ax.set_title(case_id.replace("_", " ").title())
        ax.set_xticks(positions)
        ax.set_xticklabels([wrapped(label, 10) for label in labels], rotation=35, ha="right", fontsize=7.2)
        ax.grid(False)
    axes[0].set_ylabel("Corrected heat rate (W)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("PASSIVE-H2 Segment-Local Heat-Path Distribution")
    svg_path, png_path = save_figure(
        fig,
        "operator",
        "passive_h2_segment_family_heat_path_operator",
        PASSIVE_H2_MODEL_FORM_ID,
    )
    figures.append(
        FigureResult(
            figure_id="fig_passive_h2_segment_family_heat_path_operator",
            title="PASSIVE-H2 segment-local heat-path distribution",
            svg_path=svg_path,
            png_path=png_path,
            data_path=family_data_path,
            caption=(
                "Segment-family decomposition of the PASSIVE-H2 corrected operator. "
                "The intended mapping is segment-local external-boundary development "
                "evidence, not a global heat-loss patch."
            ),
            allowed_claim=(
                "PASSIVE-H2 is best treated as a segment-local passive-boundary "
                "implementation target."
            ),
            forbidden_claim=(
                "Do not collapse these rows into a hidden global multiplier, a "
                "numeric q-loss release, or a residual absorbed into internal Nu."
            ),
        )
    )

    hypothesis_order = ["replace_current_global_qambient_with_h2_total", "add_h2_as_missing_global_sink"]
    colors = {
        "replace_current_global_qambient_with_h2_total": "0.35",
        "add_h2_as_missing_global_sink": "green",
    }
    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    width = 0.34
    for offset, hypothesis in zip([-width / 2, width / 2], hypothesis_order, strict=True):
        rows = [row for row in projection_panel_rows if row["hypothesis"] == hypothesis]
        values = [float(row["delta_qambient_W"]) for row in rows]
        positions = [index + offset for index in range(len(rows))]
        label = "Replace current qambient" if hypothesis.startswith("replace") else "Add H2 as global sink"
        ax.bar(positions, values, width=width, color=colors[hypothesis], label=label)
    ax.axhline(0.0, color="0.20", linewidth=1.0)
    ax.set_xticks(range(len(CASE_ORDER)))
    ax.set_xticklabels([case_id.replace("_", " ").title() for case_id in CASE_ORDER])
    ax.set_ylabel("Projected global qambient change (W)")
    ax.set_title("PASSIVE-H2 Global Patch Rejection")
    ax.legend(loc="lower left", fontsize=8)
    ax.text(
        0.98,
        0.96,
        "All rows outside local hA response envelope",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color="0.20",
    )
    ax.grid(False)
    svg_path, png_path = save_figure(
        fig,
        "operator",
        "passive_h2_global_patch_rejection_operator",
        PASSIVE_H2_MODEL_FORM_ID,
    )
    figures.append(
        FigureResult(
            figure_id="fig_passive_h2_global_patch_rejection_operator",
            title="PASSIVE-H2 global patch rejection",
            svg_path=svg_path,
            png_path=png_path,
            data_path=projection_data_path,
            caption=(
                "Train-context global-patch projection for PASSIVE-H2. Replacement "
                "and additive global qambient hypotheses are outside the existing "
                "local hA response envelope, so this is a rejection figure."
            ),
            allowed_claim=(
                "The current evidence supports a segment-local operator path and "
                "rejects direct global qambient replacement/addition."
            ),
            forbidden_claim=(
                "Do not use this panel to justify global heat-loss calibration, "
                "protected scoring, final prediction, or coefficient admission."
            ),
        )
    )

    operator_readme = f"""---
provenance:
  - {rel(PASSIVE_H2_CANDIDATE_MANIFEST)}
  - {rel(PASSIVE_H2_CASE_SUMMARY)}
  - {rel(PASSIVE_H2_FAMILY_LEDGER)}
  - {rel(PASSIVE_H2_HEAT_LEDGER_DELTA)}
tags: [thesis, figures, passive-h2, operator-only, no-admission]
related:
  - {rel(OUT_DIR / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Figures / Thermal-modeling / Forward-pred / Writer / Reviewer
type: model_form_readme
status: complete
---
# {PASSIVE_H2_MODEL_FORM_ID} Figure Folder

## Model Definition

- model form: `{PASSIVE_H2_MODEL_FORM_ID}`
- slot: `{manifest_row["model_form_slot"]}`
- operator basis: `{manifest_row["operator_basis"]}`
- development decision: `{manifest_row["development_decision"]}`

## Current Evidence

- corrected radiation range (W): `{manifest_row["corrected_radiation_min_W"]}` to `{manifest_row["corrected_radiation_max_W"]}`
- corrected passive operator total range (W): `{manifest_row["corrected_total_min_W"]}` to `{manifest_row["corrected_total_max_W"]}`
- coefficient admission: `{manifest_row["coefficient_admission"]}`
- protected scoring: `{manifest_row["protected_scoring"]}`
- source/property release: `{manifest_row["source_property_release"]}`

## Figures

- `operator/svg/`
- `operator/png/`

## Claim Boundary

PASSIVE-H2 is operator-only development evidence in this package. It does not
emit per-sensor TP/TW predictions for the elevation panels, does not release a
numeric q-loss, does not admit a coefficient, does not score protected rows,
and does not freeze a predictive candidate.
"""
    write_text(FIG_ROOT / model_dir_name(PASSIVE_H2_MODEL_FORM_ID) / "README.md", operator_readme)
    return figures


def classify_ladder_status(row: dict[str, str]) -> str:
    text = " ".join(
        [
            row.get("admission_status", ""),
            row.get("allowed_now", ""),
            row.get("required_gates_before_claim", ""),
        ]
    ).lower()
    if "blocked" in text:
        return "blocked"
    if "diagnostic" in text or "not_admitted" in text:
        return "diagnostic_only"
    if "future" in text:
        return "future"
    if "not_scored" in text or "builder" in text:
        return "specification_only"
    return "not_admitted"


def ladder_short_label(name: str) -> str:
    if name.startswith("M5"):
        return "M5 / MF-04"
    if name.startswith("MF-02"):
        return "MF-02"
    if name.startswith("MF-01"):
        return "MF-01"
    return name.split()[0]


def build_model_form_ladder_panel() -> FigureResult:
    rows = read_csv(LADDER_ROWS)
    panel_rows: list[dict[str, object]] = []
    for row in rows:
        panel_rows.append(
            {
                "figure_id": "fig_model_form_ladder",
                "rank": row["rank"],
                "short_label": ladder_short_label(row["model_form_to_try"]),
                "model_form_to_try": row["model_form_to_try"],
                "visual_status": classify_ladder_status(row),
                "reason": row["reason"],
                "required_gates_before_claim": row["required_gates_before_claim"],
                "allowed_now": row["allowed_now"],
                "expected_thesis_use": row["expected_thesis_use"],
                "admission_status": row["admission_status"],
            }
        )

    data_path = OUT_DIR / "model_form_ladder_panel.csv"
    write_csv(
        data_path,
        panel_rows,
        [
            "figure_id",
            "rank",
            "short_label",
            "model_form_to_try",
            "visual_status",
            "reason",
            "required_gates_before_claim",
            "allowed_now",
            "expected_thesis_use",
            "admission_status",
        ],
    )

    fig, ax = plt.subplots(figsize=(8.0, 5.4))
    x_values = [int(row["rank"]) for row in panel_rows]
    ax.plot(x_values, [0.0] * len(x_values), "-", color="0.35", linewidth=1.2)
    styles = {
        "specification_only": ("o", "blue", "Specification"),
        "diagnostic_only": ("s", "green", "Diagnostic only"),
        "future": ("^", "0.55", "Future"),
        "blocked": ("x", "0.30", "Blocked"),
        "not_admitted": ("D", "0.45", "Not admitted"),
    }
    seen: set[str] = set()
    for row in panel_rows:
        x_value = int(row["rank"])
        status = str(row["visual_status"])
        marker, color, label = styles[status]
        ax.plot(
            [x_value],
            [0.0],
            marker,
            color=color,
            markersize=8.5,
            linestyle="",
            label=label if status not in seen else None,
        )
        seen.add(status)
        dy = 0.14 if x_value % 2 else -0.22
        va = "bottom" if dy > 0 else "top"
        ax.annotate(
            wrapped(f"{row['short_label']}: {row['expected_thesis_use']}", 27),
            (x_value, 0.0),
            xytext=(0, int(dy * 100)),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=8,
        )

    ax.set_xlim(0.55, len(panel_rows) + 0.45)
    ax.set_ylim(-0.95, 0.85)
    ax.set_yticks([])
    ax.set_xticks(x_values)
    ax.set_xlabel("Recommended model-form trial order")
    ax.set_title("Model-Form Ladder (No Closure Admitted)")
    ax.legend(loc="upper right")
    ax.grid(False)
    for spine in ["left", "right", "top"]:
        ax.spines[spine].set_visible(False)

    svg_path, png_path = save_figure(fig, "progress", "model_form_ladder_no_admission")

    return FigureResult(
        figure_id="fig_model_form_ladder",
        title="Model-form ladder",
        svg_path=svg_path,
        png_path=png_path,
        data_path=data_path,
        caption=(
            "Recommended model-form trial ladder from the master scoreboard. "
            "Each rung is labeled by thesis use and admission state. The ladder "
            "is a planning and figure device, not a candidate release."
        ),
        allowed_claim=(
            "The next scientific sequence is organized around setup-only, "
            "recirculation-exchange, section-effective pressure, ordinary-branch, "
            "passive thermal, and final-freeze gates."
        ),
        forbidden_claim=(
            "Do not infer that any rung is admitted, frozen, scored, or allowed "
            "to use protected runtime temperatures or realized CFD fields."
        ),
    )


def build_blocked_scorecard_panel() -> FigureResult:
    rows = read_csv(BLOCKED_LOGIC)
    panel_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        panel_rows.append(
            {
                "figure_id": "fig_blocked_scorecard_waterfall",
                "gate_order": index,
                "gate": row["gate"],
                "status": row["status"],
                "scorecard_effect": row["scorecard_effect"],
                "protected_rows_touched": row["protected_rows_touched"],
                "reason": row["reason"],
                "final_score_values": 0,
            }
        )

    data_path = OUT_DIR / "blocked_scorecard_waterfall_panel.csv"
    write_csv(
        data_path,
        panel_rows,
        [
            "figure_id",
            "gate_order",
            "gate",
            "status",
            "scorecard_effect",
            "protected_rows_touched",
            "reason",
            "final_score_values",
        ],
    )

    fig, ax = plt.subplots(figsize=(8.0, 5.4))
    y_values = list(range(len(panel_rows), 0, -1))
    ax.plot([0.0] * len(y_values), y_values, "--s", color="green", linewidth=1.6, markersize=5.2)
    for y_value, row in zip(y_values, panel_rows, strict=True):
        ax.annotate(
            wrapped(str(row["gate"]), 30),
            (0.0, y_value),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=8.2,
        )
        ax.annotate(
            wrapped(str(row["scorecard_effect"]), 34),
            (0.0, y_value),
            xytext=(175, 0),
            textcoords="offset points",
            va="center",
            fontsize=7.7,
            color="0.20",
        )

    ax.set_xlim(-0.12, 1.0)
    ax.set_ylim(0.4, len(panel_rows) + 0.6)
    ax.set_xticks([0.0])
    ax.set_xticklabels(["blocked / no final score"])
    ax.set_yticks([])
    ax.set_title("Frozen Scorecard Waterfall (Blocked)")
    ax.set_xlabel("Admission state")
    ax.grid(False)
    for spine in ["left", "right", "top"]:
        ax.spines[spine].set_visible(False)

    svg_path, png_path = save_figure(fig, "progress", "blocked_scorecard_waterfall")

    return FigureResult(
        figure_id="fig_blocked_scorecard_waterfall",
        title="Blocked frozen-candidate waterfall",
        svg_path=svg_path,
        png_path=png_path,
        data_path=data_path,
        caption=(
            "Frozen-scorecard gate waterfall showing why the final scorecard "
            "remains a blocked shell: thermal residual ownership, exchange/Qwall "
            "UQ, pressure/F6 admission, and the frozen candidate gate have not "
            "all passed."
        ),
        allowed_claim=(
            "The thesis can cite the current no-final-score state as a rigorous "
            "admission result rather than as missing implementation."
        ),
        forbidden_claim=(
            "Do not publish final predictive accuracy, component K, F6, ordinary "
            "upcomer Nu, ordinary upcomer f_D, ordinary upcomer K, or any frozen "
            "candidate from this panel."
        ),
    )


def build_caption_ledger(figures: Sequence[FigureResult]) -> None:
    rows = []
    for figure in figures:
        rows.append(
            {
                "figure_id": figure.figure_id,
                "title": figure.title,
                "svg_path": rel(figure.svg_path),
                "png_path": rel(figure.png_path),
                "data_path": rel(figure.data_path),
                "caption": figure.caption,
                "allowed_claim": figure.allowed_claim,
                "forbidden_claim": figure.forbidden_claim,
                "split_or_admission_label": "diagnostic_only_no_final_score_no_closure_admission",
                "runtime_leakage_caveat": (
                    "No CFD mdot, realized wallHeatFlux, imposed cooler duty, "
                    "validation/holdout/external-test temperatures, or scored "
                    "TP/TW temperatures are released as runtime inputs."
                ),
            }
        )
    write_csv(
        OUT_DIR / "caption_ledger.csv",
        rows,
        [
            "figure_id",
            "title",
            "svg_path",
            "png_path",
            "data_path",
            "caption",
            "allowed_claim",
            "forbidden_claim",
            "split_or_admission_label",
            "runtime_leakage_caveat",
        ],
    )


def build_source_manifest() -> list[dict[str, object]]:
    rows = [
        {
            "source_path": rel(SCOREBOARD_ERRORS),
            "use": "scoreboard model-form TP/TW predictions plus audit-only scoreboard reference targets",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(EXPERIMENTAL_TARGET_ROWS),
            "use": "experimental TP/TW validation target temperatures for plotted targets and signed errors",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(SIGNED_ROWS),
            "use": "figure-ready signed-error context",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(DIAGNOSTIC_SENSOR_ERRORS),
            "use": "D2 diagnostic addendum per-sensor adjusted TP/TW predictions",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(DIAGNOSTIC_MODEL_SCOREBOARD),
            "use": "D2 diagnostic addendum RMSE and no-admission context",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(PASSIVE_H2_CANDIDATE_MANIFEST),
            "use": "PASSIVE-H2 operator-only candidate definition and no-admission context",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(PASSIVE_H2_CASE_SUMMARY),
            "use": "PASSIVE-H2 corrected case-level convection/radiation operator rows",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(PASSIVE_H2_FAMILY_LEDGER),
            "use": "PASSIVE-H2 segment-family corrected operator rows",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(PASSIVE_H2_HEAT_LEDGER_DELTA),
            "use": "PASSIVE-H2 global-patch rejection projection rows",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(SIGNED_SUMMARY),
            "use": "signed-error summary context",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(LADDER_ROWS),
            "use": "model-form ladder figure/table rows",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(MASTER_SUMMARY),
            "use": "master scoreboard guardrails",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(SHAPE_SUMMARY),
            "use": "best current legacy numeric comparator context",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(BLOCKED_LOGIC),
            "use": "blocked frozen-scorecard waterfall rows",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(N1_SUMMARY),
            "use": "zero final-score and no-candidate guardrails",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(N2_PANELS / "panel_manifest.csv"),
            "use": "upcomer exchange/S13 diagnostic-only paper-panel context",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(N3_ABLATION / "thermal_residual_ablation_table.csv"),
            "use": "thermal residual-owner blocker context",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(SENSOR_COORDINATES),
            "use": "S7 TP/TW sensor coordinate ledger and coordinate caveats",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(SENSOR_PROJECTION),
            "use": "sensor/QOI projection and runtime-temperature prohibition context",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(REFERENCE_GEOMETRY),
            "use": "canonical geometry convention and reference-coordinate caveats",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(REFERENCE_PLOT),
            "use": "reference elevation constants, TP2 datum convention, and visual style",
            "mutation_status": "read_only",
        },
    ]
    write_csv(
        OUT_DIR / "source_manifest.csv",
        rows,
        ["source_path", "use", "mutation_status"],
    )
    return rows


def build_guardrails() -> list[dict[str, object]]:
    rows = [
        ("native_output_mutation", False),
        ("registry_or_admission_mutation", False),
        ("scheduler_action", False),
        ("solver_sampler_harvest_uq_launched", False),
        ("validation_holdout_external_new_scoring", False),
        ("fitting_or_model_selection", False),
        ("source_property_release", False),
        ("coefficient_admission", False),
        ("s11_s12_s13_s15_s6_trigger", False),
        ("thesis_current_file_edit", False),
        ("blocker_register_change", False),
        ("generated_index_refresh", False),
        ("residual_absorbed_into_internal_nu", False),
        ("final_score_values", 0),
    ]
    records = [
        {
            "guardrail": name,
            "value": value,
            "note": "figure/table packaging only from completed evidence",
        }
        for name, value in rows
    ]
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", records, ["guardrail", "value", "note"])
    return records


def rmse(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return (sum(value * value for value in values) / len(values)) ** 0.5


def mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def fmt_float(value: float | None) -> str:
    return "" if value is None else f"{value:.12g}"


def model_predictive_note(model_form_id: str, numeric_rank: int) -> str:
    if model_form_id == D2_MODEL_FORM_ID:
        return "best_numeric_diagnostic_projection_addendum_not_admitted" if numeric_rank == 1 else "diagnostic_projection_addendum_not_admitted"
    if model_form_id == PASSIVE_H2_MODEL_FORM_ID:
        return "operator_only_passive_boundary_development_evidence_no_tp_tw_prediction"
    if model_form_id == "M3":
        return "best_current_legacy_numeric_comparator_not_frozen"
    if numeric_rank == 1:
        return "best_current_legacy_numeric_comparator_not_frozen"
    if model_form_id == "M2":
        return "secondary_current_numeric_candidate_blocked_pending_passive_source_basis"
    if model_form_id in {"M1", "M1b"}:
        return "historical_cfd_boundary_replay_not_likely_predictive_candidate"
    return "legacy_numeric_context_not_frozen"


def build_model_form_summary(tp_tw_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    model_ids = sorted({row["model_form_id"] for row in tp_tw_rows}, key=model_sort_key)
    metrics: dict[str, dict[str, object]] = {}
    for model_form_id in model_ids:
        model_rows = [row for row in tp_tw_rows if row["model_form_id"] == model_form_id]
        finite_rows = [row for row in model_rows if row["prediction_available"] == "True"]
        errors = [float(row["signed_error_K"]) for row in finite_rows if row["signed_error_K"]]
        tp_errors = [
            float(row["signed_error_K"])
            for row in finite_rows
            if row["sensor_kind"] == "TP" and row["signed_error_K"]
        ]
        tw_errors = [
            float(row["signed_error_K"])
            for row in finite_rows
            if row["sensor_kind"] == "TW" and row["signed_error_K"]
        ]
        labels = sorted({row["model_form_label"] for row in model_rows if row["model_form_label"]})
        if model_form_id == D2_MODEL_FORM_ID:
            labels = [label for label in labels if label != "D2 diagnostic TP/TW projection addendum"] or labels
        metrics[model_form_id] = {
            "model_form_id": model_form_id,
            "model_form_label": labels[0],
            "legacy_mode_ids": "; ".join(sorted({row["legacy_mode_id"] for row in model_rows if row["legacy_mode_id"]})),
            "admission_statuses": "; ".join(sorted({row["admission_status"] for row in model_rows})),
            "case_count": len({row["case_id"] for row in model_rows}),
            "tp_tw_rows": len(model_rows),
            "finite_prediction_rows": len(finite_rows),
            "missing_prediction_rows": len(model_rows) - len(finite_rows),
            "experimental_target_rmse_K": rmse(errors),
            "experimental_target_mean_signed_error_K": mean(errors),
            "experimental_target_tp_rmse_K": rmse(tp_errors),
            "experimental_target_tw_rmse_K": rmse(tw_errors),
            "source_paths": "; ".join(sorted({row["scoreboard_source_path"] for row in model_rows})),
        }
    ranked_ids = sorted(
        model_ids,
        key=lambda model_form_id: (
            metrics[model_form_id]["experimental_target_rmse_K"]
            if metrics[model_form_id]["experimental_target_rmse_K"] is not None
            else float("inf")
        ),
    )
    rank_by_model = {model_form_id: index + 1 for index, model_form_id in enumerate(ranked_ids)}
    for model_form_id in model_ids:
        metric = metrics[model_form_id]
        numeric_rank = rank_by_model[model_form_id]
        rows.append(
            {
                "model_form_id": model_form_id,
                "model_form_label": metric["model_form_label"],
                "legacy_mode_ids": metric["legacy_mode_ids"],
                "current_numeric_rank_by_experimental_tp_tw_rmse": numeric_rank,
                "current_numeric_disposition": model_predictive_note(model_form_id, numeric_rank),
                "case_count": metric["case_count"],
                "tp_tw_rows": metric["tp_tw_rows"],
                "finite_prediction_rows": metric["finite_prediction_rows"],
                "missing_prediction_rows": metric["missing_prediction_rows"],
                "experimental_target_rmse_K": fmt_float(metric["experimental_target_rmse_K"]),
                "experimental_target_mean_signed_error_K": fmt_float(
                    metric["experimental_target_mean_signed_error_K"]
                ),
                "experimental_target_tp_rmse_K": fmt_float(metric["experimental_target_tp_rmse_K"]),
                "experimental_target_tw_rmse_K": fmt_float(metric["experimental_target_tw_rmse_K"]),
                "admission_statuses": metric["admission_statuses"],
                "source_paths": metric["source_paths"],
                "predictive_model_caveat": (
                    "Numeric rank is a diagnostic comparison against experimental TP/TW targets; "
                    "no model is frozen, admitted, or final-scored."
                ),
            }
        )
    passive_manifest = read_csv(PASSIVE_H2_CANDIDATE_MANIFEST)[0]
    rows.append(
        {
            "model_form_id": PASSIVE_H2_MODEL_FORM_ID,
            "model_form_label": "PASSIVE-H2 corrected outer-insulation radiation/passive-boundary operator",
            "legacy_mode_ids": "PASSIVE-H2-CAND001",
            "current_numeric_rank_by_experimental_tp_tw_rmse": "",
            "current_numeric_disposition": model_predictive_note(PASSIVE_H2_MODEL_FORM_ID, 999),
            "case_count": len(CASE_ORDER),
            "tp_tw_rows": 0,
            "finite_prediction_rows": 0,
            "missing_prediction_rows": 0,
            "experimental_target_rmse_K": "",
            "experimental_target_mean_signed_error_K": "",
            "experimental_target_tp_rmse_K": "",
            "experimental_target_tw_rmse_K": "",
            "admission_statuses": "operator_only_development_evidence_no_admission",
            "source_paths": "; ".join(
                [
                    rel(PASSIVE_H2_CANDIDATE_MANIFEST),
                    rel(PASSIVE_H2_CASE_SUMMARY),
                    rel(PASSIVE_H2_FAMILY_LEDGER),
                    rel(PASSIVE_H2_HEAT_LEDGER_DELTA),
                ]
            ),
            "predictive_model_caveat": (
                "PASSIVE-H2 is an operator/heat-path figure family here, not a "
                "per-sensor TP/TW prediction, final score, release, or admission. "
                f"Corrected operator total range is {passive_manifest['corrected_total_min_W']} "
                f"to {passive_manifest['corrected_total_max_W']} W."
            ),
        }
    )
    write_csv(
        OUT_DIR / "model_form_summary.csv",
        rows,
        [
            "model_form_id",
            "model_form_label",
            "legacy_mode_ids",
            "current_numeric_rank_by_experimental_tp_tw_rmse",
            "current_numeric_disposition",
            "case_count",
            "tp_tw_rows",
            "finite_prediction_rows",
            "missing_prediction_rows",
            "experimental_target_rmse_K",
            "experimental_target_mean_signed_error_K",
            "experimental_target_tp_rmse_K",
            "experimental_target_tw_rmse_K",
            "admission_statuses",
            "source_paths",
            "predictive_model_caveat",
        ],
    )
    return rows


def write_model_form_readmes(model_summary_rows: Sequence[dict[str, object]]) -> None:
    for row in model_summary_rows:
        model_form_id = str(row["model_form_id"])
        if model_form_id == PASSIVE_H2_MODEL_FORM_ID:
            continue
        model_dir = FIG_ROOT / model_dir_name(model_form_id)
        text = f"""---
provenance:
  - {rel(SCOREBOARD_ERRORS)}
  - {rel(EXPERIMENTAL_TARGET_ROWS)}
  - {rel(OUT_DIR / "model_form_summary.csv")}
tags: [thesis, figures, model-form, {model_form_id}]
related:
  - {rel(OUT_DIR / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Figures / Forward-pred / Writer / Reviewer
type: model_form_readme
status: complete
---
# {model_form_id} Figure Folder

## Model Definition

- model form: `{model_form_id}`
- label: `{row["model_form_label"]}`
- legacy mode id(s): `{row["legacy_mode_ids"]}`
- admission status: `{row["admission_statuses"]}`

## Current Numeric Comparison

- rank among current scoreboard model forms by experimental TP/TW RMSE:
  `{row["current_numeric_rank_by_experimental_tp_tw_rmse"]}`
- experimental TP/TW RMSE (K): `{row["experimental_target_rmse_K"]}`
- TP RMSE (K): `{row["experimental_target_tp_rmse_K"]}`
- TW RMSE (K): `{row["experimental_target_tw_rmse_K"]}`
- finite prediction rows: `{row["finite_prediction_rows"]}`
- missing prediction rows: `{row["missing_prediction_rows"]}`
- disposition: `{row["current_numeric_disposition"]}`

## Figures

- `tp_tw_vs_elevation/svg/`
- `tp_tw_vs_elevation/png/`
- `tp_vs_elevation/svg/`
- `tp_vs_elevation/png/`
- `diagnostics/svg/`
- `diagnostics/png/`

## Claim Boundary

These figures are diagnostic legacy model-form comparisons against experimental
TP/TW target temperatures on the reference-geometry elevation basis. They do not
freeze `{model_form_id}`, admit a closure, release source/property or Qwall
inputs, publish final predictive accuracy, or trigger S11/S12/S13/S15/S6.

## Source Paths

`{row["source_paths"]}`
"""
        write_text(model_dir / "README.md", text)


def build_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - {rel(SCOREBOARD_ERRORS)}
  - {rel(EXPERIMENTAL_TARGET_ROWS)}
  - {rel(SIGNED_ROWS)}
  - {rel(DIAGNOSTIC_SENSOR_ERRORS)}
  - {rel(DIAGNOSTIC_MODEL_SCOREBOARD)}
  - {rel(PASSIVE_H2_CANDIDATE_MANIFEST)}
  - {rel(PASSIVE_H2_CASE_SUMMARY)}
  - {rel(PASSIVE_H2_FAMILY_LEDGER)}
  - {rel(PASSIVE_H2_HEAT_LEDGER_DELTA)}
  - {rel(LADDER_ROWS)}
  - {rel(BLOCKED_LOGIC)}
  - {rel(SENSOR_COORDINATES)}
  - {rel(SENSOR_PROJECTION)}
  - {rel(REFERENCE_GEOMETRY)}
  - {rel(REFERENCE_PLOT)}
tags: [thesis, figures, model-form-scoreboard, tp-tw-elevation, no-admission]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thesis-figtable-model-form-folder-and-scoreboard-reader.md
  - .agent/journal/2026-07-22/thesis-figtable-reference-geometry-experimental-target-panel-correction.md
task: {TASK_ID}
date: 2026-07-22
role: Figures / Implementer / Writer / Reviewer / Tester
type: work_product
status: complete
---
# Thesis Figure/Table Model-Form and Blocked-Scorecard Panels

This package converts completed scoreboard evidence into insert-ready thesis
figures styled after `{rel(REFERENCE_PLOT)}`. The visual language intentionally
matches the reference temperature-elevation plot and now uses the reference
geometry elevation convention: absolute probe coordinates shifted so TP2 is
0 m. Plotted target temperatures come from the experimental Fluid validation
table, not the master-scoreboard `target_K` values. The scoreboard target values
are preserved only as audit columns named `scoreboard_reference_target_K` and
`target_delta_experimental_minus_scoreboard_K`.

The primary panels plot TP1-TP6 as a blue solid target curve, TW1-TW9/TW11-TW1
as a closed green dashed target curve, and available model-form predictions as
lighter overlays with explicit `<model_form> TP*` and `<model_form> TW*` marker
labels. TP2 is retained as an explicit missing-prediction target. TW10 is retained in
`tp_tw_temperature_elevation_panel_points.csv` but omitted from the plotted
curve and axis range because it is the active heat-exchanger shell state and current model forms
do not emit it. The signed-error panel remains in the package as a secondary
diagnostic artifact, now recomputed against the same experimental target table.

The current legacy numeric scoreboard model closest to the experimental TP/TW
targets is `{summary["current_best_numeric_model_form_by_experimental_tp_tw_rmse"]}`
with experimental-basis TP/TW RMSE
`{summary["current_best_numeric_model_form_experimental_tp_tw_rmse_K"]} K`.
This is not a frozen predictive model. The most likely future predictive family
remains `{summary["most_likely_future_predictive_family"]}`, with status
`{summary["most_likely_future_predictive_family_status"]}`.

## Figure Organization

Figures are organized by model form, then category, then file type:

- `figures/progress/{{svg,png}}/`: model-form ladder and blocked scorecard
  waterfall.
- `figures/<model_form>/README.md`: model definition, numeric rank, and claim
  boundary.
- `figures/<model_form>/tp_vs_elevation/{{svg,png}}/`: TP-only
  target/prediction elevation panels.
- `figures/<model_form>/tp_tw_vs_elevation/{{svg,png}}/`: combined TP/TW
  target/prediction elevation panels.
- `figures/<model_form>/diagnostics/{{svg,png}}/`: signed-error diagnostic
  panel.
- `figures/<model_form>/operator/{{svg,png}}/`: scalar/operator panels for
  model forms that do not emit TP/TW predictions.

## Outputs

- `figures/<model_form>/README.md`
- `figures/<model_form>/diagnostics/svg/<model_form>_signed_sensor_error_shape.svg`
- `figures/<model_form>/diagnostics/png/<model_form>_signed_sensor_error_shape.png`
- `figures/<model_form>/tp_vs_elevation/svg/<model_form>_tp_temperature_vs_elevation_salt_*.svg`
- `figures/<model_form>/tp_vs_elevation/png/<model_form>_tp_temperature_vs_elevation_salt_*.png`
- `figures/<model_form>/tp_tw_vs_elevation/svg/<model_form>_tp_tw_temperature_vs_elevation_salt_*.svg`
- `figures/<model_form>/tp_tw_vs_elevation/png/<model_form>_tp_tw_temperature_vs_elevation_salt_*.png`
- `figures/<model_form>/operator/svg/*_operator.svg`
- `figures/<model_form>/operator/png/*_operator.png`
- `figures/progress/svg/model_form_ladder_no_admission.svg`
- `figures/progress/png/model_form_ladder_no_admission.png`
- `figures/progress/svg/blocked_scorecard_waterfall.svg`
- `figures/progress/png/blocked_scorecard_waterfall.png`
- `tp_tw_temperature_elevation_panel_points.csv`
- `signed_error_panel_points.csv`
- `model_form_summary.csv`
- `model_form_ladder_panel.csv`
- `blocked_scorecard_waterfall_panel.csv`
- `caption_ledger.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Claim Boundary

These figures support thesis writing and scientific communication. They do not
release a closure, fit a coefficient, mutate any native solver output, score a
protected validation/holdout/external row, trigger S11/S12/S13/S15/S6, or admit
component K/F6/upcomer Nu/upcomer f_D/upcomer K.

## Result

- figure panels: `{summary["figure_panels"]}`
- figure category layout: `{summary["figure_category_layout"]}`
- model forms: `{summary["model_form_ids"]}`
- current best numeric model form: `{summary["current_best_numeric_model_form_by_experimental_tp_tw_rmse"]}`
- current best numeric model-form RMSE (K): `{summary["current_best_numeric_model_form_experimental_tp_tw_rmse_K"]}`
- most likely future predictive family: `{summary["most_likely_future_predictive_family"]}`
- progress figure panels: `{summary["progress_figure_panels"]}`
- TP-only elevation figure panels: `{summary["tp_vs_elevation_figure_panels"]}`
- TP/TW elevation figure panels: `{summary["tp_tw_vs_elevation_figure_panels"]}`
- diagnostic figure panels: `{summary["diagnostic_figure_panels"]}`
- operator figure panels: `{summary["operator_figure_panels"]}`
- legacy flat figure paths retained: `{summary["legacy_flat_figure_paths_retained"]}`
- TP temperature-elevation panel rows: `{summary["tp_temperature_elevation_panel_rows"]}`
- missing model-form TP predictions marked: `{summary["missing_m3_tp_predictions_marked"]}`
- finite signed-error panel rows: `{summary["finite_signed_error_panel_rows"]}`
- model-form summary rows: `{summary["model_form_summary_rows"]}`
- model-form ladder rows: `{summary["model_form_ladder_rows"]}`
- blocked scorecard gate rows: `{summary["blocked_scorecard_gate_rows"]}`
- final score values: `{summary["final_score_values"]}`
- decision: `{summary["decision"]}`
- TP/TW panel coordinate basis: `{summary["tp_tw_coordinate_basis"]}`
- TP/TW panel reference geometry basis: `{summary["reference_geometry_elevation_basis"]}`
- TP/TW panel target basis: `{summary["temperature_target_basis"]}`
- experimental target rows: `{summary["experimental_target_rows"]}`
- scoreboard target audit rows: `{summary["scoreboard_target_audit_rows"]}`
- TP/TW target rows plotted: `{summary["tp_tw_target_rows_plotted"]}`
- TP5-to-TP6 target connection plotted: `{summary["tp5_to_tp6_target_connection_plotted"]}`
- TP5-to-TP6 prediction connection plotted: `{summary["tp5_to_tp6_prediction_connection_plotted"]}`
- TW11-to-TW1 target closure plotted: `{summary["tw11_to_tw1_target_closure_plotted"]}`
- TW11-to-TW1 prediction closure plotted: `{summary["tw11_to_tw1_prediction_closure_plotted"]}`
- prediction marker labels plotted: `{summary["prediction_marker_labels_plotted"]}`
- missing model-form TP2 rows marked: `{summary["missing_m3_tp2_predictions_marked"]}`
- excluded/missing TW10 rows marked: `{summary["excluded_tw10_rows_marked"]}`
"""
    write_text(OUT_DIR / "README.md", text)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_legacy_flat_figure_outputs()

    figures = [
        *build_tp_tw_temperature_elevation_panels(),
        *build_signed_error_panels(),
        *build_passive_h2_operator_panels(),
        build_model_form_ladder_panel(),
        build_blocked_scorecard_panel(),
    ]
    build_caption_ledger(figures)
    sources = build_source_manifest()
    guardrails = build_guardrails()

    signed_rows = read_csv(OUT_DIR / "signed_error_panel_points.csv")
    tp_tw_elevation_rows = read_csv(OUT_DIR / "tp_tw_temperature_elevation_panel_points.csv")
    tp_elevation_rows = read_csv(OUT_DIR / "tp_temperature_elevation_panel_points.csv")
    model_form_summary_rows = build_model_form_summary(tp_tw_elevation_rows)
    write_model_form_readmes(model_form_summary_rows)
    ladder_rows = read_csv(OUT_DIR / "model_form_ladder_panel.csv")
    blocked_rows = read_csv(OUT_DIR / "blocked_scorecard_waterfall_panel.csv")
    master_summary = read_json(MASTER_SUMMARY)
    shape_summary = read_json(SHAPE_SUMMARY)
    n1_summary = read_json(N1_SUMMARY)
    current_best_model = next(
        row
        for row in model_form_summary_rows
        if str(row["current_numeric_rank_by_experimental_tp_tw_rmse"]) == "1"
    )

    summary: dict[str, object] = {
        "task": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "thesis_figure_panels_ready_no_closure_admission",
        "figure_panels": len(figures),
        "svg_figures": len(figures),
        "png_figures": len(figures),
        "figure_category_layout": (
            "figures/<model_form>/<category>/<svg-or-png>/<basename>; "
            "progress figures use figures/progress/<svg-or-png>/<basename>"
        ),
        "figure_categories": list(FIGURE_CATEGORIES),
        "model_form_ids": [row["model_form_id"] for row in model_form_summary_rows],
        "model_form_count": len(model_form_summary_rows),
        "model_form_readme_count": len(model_form_summary_rows),
        "current_best_numeric_model_form_by_experimental_tp_tw_rmse": current_best_model["model_form_id"],
        "current_best_numeric_model_form_experimental_tp_tw_rmse_K": current_best_model[
            "experimental_target_rmse_K"
        ],
        "current_best_numeric_model_form_status": current_best_model["current_numeric_disposition"],
        "most_likely_future_predictive_family": "M5 / MF-04 throughflow-plus-recirculation exchange cell",
        "most_likely_future_predictive_family_status": (
            "diagnostic_only_until_Qwall_UQ_source_property_and_freeze_gates_release"
        ),
        "progress_figure_panels": len([figure for figure in figures if "/progress/" in rel(figure.svg_path)]),
        "tp_vs_elevation_figure_panels": len(
            [figure for figure in figures if "/tp_vs_elevation/" in rel(figure.svg_path)]
        ),
        "tp_tw_vs_elevation_figure_panels": len(
            [figure for figure in figures if "/tp_tw_vs_elevation/" in rel(figure.svg_path)]
        ),
        "diagnostic_figure_panels": len(
            [figure for figure in figures if "/diagnostics/" in rel(figure.svg_path)]
        ),
        "operator_figure_panels": len(
            [figure for figure in figures if "/operator/" in rel(figure.svg_path)]
        ),
        "legacy_flat_figure_paths_retained": sum(
            1
            for figure_type in FIGURE_TYPES
            for path in (FIG_ROOT / figure_type).glob(f"*.{figure_type}")
        )
        if any((FIG_ROOT / figure_type).exists() for figure_type in FIGURE_TYPES)
        else 0,
        "tp_tw_temperature_elevation_panel_rows": len(tp_tw_elevation_rows),
        "tp_temperature_elevation_panel_rows": len(
            tp_elevation_rows
        ),
        "tp_tw_target_rows_plotted": sum(
            1 for row in tp_tw_elevation_rows if row["target_curve_included"] == "True"
        ),
        "missing_m3_predictions_marked": sum(
            1 for row in tp_tw_elevation_rows if row["prediction_available"] == "False"
        ),
        "missing_model_form_predictions_marked": sum(
            1 for row in tp_tw_elevation_rows if row["prediction_available"] == "False"
        ),
        "missing_m3_tp2_predictions_marked": sum(
            1
            for row in tp_tw_elevation_rows
            if row["sensor_id"] == "TP2" and row["prediction_available"] == "False"
        ),
        "missing_model_form_tp2_predictions_marked": sum(
            1
            for row in tp_tw_elevation_rows
            if row["sensor_id"] == "TP2" and row["prediction_available"] == "False"
        ),
        "missing_m3_tp_predictions_marked": sum(
            1
            for row in tp_tw_elevation_rows
            if row["sensor_kind"] == "TP" and row["prediction_available"] == "False"
        ),
        "missing_model_form_tp_predictions_marked": sum(
            1
            for row in tp_tw_elevation_rows
            if row["sensor_kind"] == "TP" and row["prediction_available"] == "False"
        ),
        "excluded_tw10_rows_marked": sum(
            1
            for row in tp_tw_elevation_rows
            if row["sensor_id"] == "TW10"
            and row["missing_or_excluded_reason"]
            == "excluded_active_hx_shell_state_absent_no_model_prediction"
        ),
        "temperature_target_basis": "experimental_fluid_validation_targets",
        "experimental_target_rows": len(tp_tw_elevation_rows),
        "scoreboard_cfd_reference_target_used_as_plotted_target": False,
        "scoreboard_target_audit_rows": sum(
            1 for row in tp_tw_elevation_rows if row["scoreboard_reference_target_K"]
        ),
        "reference_geometry_elevation_basis": REFERENCE_ELEVATION_SOURCE,
        "reference_tp2_datum_m": REFERENCE_TP2_DATUM_M,
        "reference_geometry_elevation_rows": len(tp_tw_elevation_rows),
        "tw10_rows_preserved_unplotted": sum(
            1
            for row in tp_tw_elevation_rows
            if row["sensor_id"] == "TW10" and row["target_curve_included"] == "False"
        ),
        "tp_tw_coordinate_basis": (
            "reference geometry Y_ABSOLUTE_M shifted by TP2 datum; "
            "S7/N4 coordinate/projection ledgers retained as metadata/caveats"
        ),
        "tp_tw_placeholder_temperature_values_used": False,
        "tp_tw_placeholder_elevation_values_used": False,
        "tw_target_rows_plotted_excluding_tw10": sum(
            1
            for row in tp_tw_elevation_rows
            if row["sensor_kind"] == "TW" and row["target_curve_included"] == "True"
        ),
        "tp5_to_tp6_target_connection_plotted": all(
            row["target_next_sensor_in_plot"] == "TP6"
            for row in tp_tw_elevation_rows
            if row["sensor_id"] == "TP5"
        ),
        "tp5_to_tp6_prediction_connection_plotted": all(
            row["prediction_next_sensor_in_plot"] == "TP6"
            for row in tp_tw_elevation_rows
            if row["sensor_id"] == "TP5"
        ),
        "tw11_to_tw1_target_closure_plotted": all(
            row["target_next_sensor_in_plot"] == "TW1"
            for row in tp_tw_elevation_rows
            if row["sensor_id"] == "TW11"
        ),
        "tw11_to_tw1_prediction_closure_plotted": all(
            row["prediction_next_sensor_in_plot"] == "TW1"
            for row in tp_tw_elevation_rows
            if row["sensor_id"] == "TW11"
        ),
        "prediction_marker_labels_plotted": all(
            row["prediction_label"].startswith(f"{display_model_form_id(row['model_form_id'])} ")
            for row in tp_tw_elevation_rows
            if row["prediction_curve_included"] == "True"
        ),
        "prediction_marker_label_rows": sum(
            1
            for row in tp_tw_elevation_rows
            if row["prediction_curve_included"] == "True" and row["prediction_label"]
        ),
        "finite_signed_error_panel_rows": len(signed_rows),
        "model_form_summary_rows": len(model_form_summary_rows),
        "model_form_ladder_rows": len(ladder_rows),
        "blocked_scorecard_gate_rows": len(blocked_rows),
        "source_manifest_rows": len(sources),
        "guardrail_rows": len(guardrails),
        "best_current_legacy_numeric_model": shape_summary["best_current_legacy_numeric_model"],
        "best_current_mean_group_rmse_K": shape_summary["best_current_mean_group_rmse_K"],
        "master_finite_signed_sensor_error_rows": master_summary["finite_signed_sensor_error_rows"],
        "s6_final_score_values_published": n1_summary["s6_final_score_values_published"],
        "final_score_values": 0,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "validation_holdout_external_new_scoring": False,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "thesis_current_file_edit": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    write_json(OUT_DIR / "summary.json", summary)
    build_readme(summary)
    print(f"Wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
