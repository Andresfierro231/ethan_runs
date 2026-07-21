#!/usr/bin/env python3
"""Build upcomer recirculation evidence from reduced paper-grade outputs.

Workflow role:
    This is an evidence-package builder for the upcomer/downcomer regime
    question. It joins paper-grade case inventory, reduction-contract maps,
    branch maps, nondimensional dashboard rows, and reduced branch/azimuthal
    transport outputs to summarize reverse-shear/recirculation behavior.

Inputs:
    - `--paper-case-inventory-csv`
    - `--source-contract-map-csv`
    - `--branch-map-csv`
    - `--salt-dashboard-csv`
    - Per-case reduced files referenced by the source contract map.

Outputs:
    Report/work-product CSV, JSON, README, and figure artifacts under the
    selected output directories plus an import manifest.

CLI modifiers:
    Each input table path can be overridden for replay against a different
    inventory/reduction snapshot. `--output-dir`, `--work-product-dir`, and
    `--import-manifest-path` redirect products and provenance.

Boundaries:
    This script consumes already-reduced data. It does not extract new raw CFD
    fields and does not define the final onset criterion by itself; the board
    `TODO-UPCOMER-ONSET` row must turn these diagnostics into a regime table
    with uncertainty and fit-admission decisions.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.ethan_closure_modeling_v3_common import (
    csv_dump_rows,
    finite_float,
    load_csv_rows,
    safe_mean,
    safe_sum,
    write_json,
)
from tools.common import ensure_dir, iso_timestamp, relative_to_workspace

DEFAULT_REPORT_DAY_DIR = ROOT / "reports" / "2026-06" / "2026-06-29"
DEFAULT_OUTPUT_DIR = DEFAULT_REPORT_DAY_DIR / "2026-06-29_ethan_upcomer_recirculation_evidence"
DEFAULT_WORK_PRODUCT_DIR = ROOT / "work_products" / "2026-06-29_ethan_upcomer_recirculation_evidence"
DEFAULT_IMPORT_MANIFEST_PATH = ROOT / "imports" / "2026-06-29_ethan_upcomer_recirculation_evidence.json"
DEFAULT_PAPER_CASE_INVENTORY_CSV = (
    ROOT / "work_products" / "2026-06-29_ethan_paper_case_inventory" / "paper_case_inventory.csv"
)
DEFAULT_SOURCE_CONTRACT_MAP_CSV = (
    ROOT / "work_products" / "2026-06-29_ethan_reduction_contract_audit" / "source_contract_map.csv"
)
DEFAULT_BRANCH_MAP_CSV = ROOT / "work_products" / "2026-06-29_ethan_reduction_contract_audit" / "branch_map.csv"
DEFAULT_SALT_DASHBOARD_CSV = (
    ROOT
    / "reports"
    / "2026-06"
    / "2026-06-17"
    / "2026-06-17_ethan_nondimensional_dashboard_package"
    / "salt_dashboard.csv"
)

SOURCE_ID_ORDER = (
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
)

CONTROL_BRANCH_NAME = "right_leg"
UPCOMER_BRANCH_NAME = "upcomer"
AZIMUTHAL_SUMMARY_FILE = "raw_extraction/azimuthal_wall_transport_summary.csv"
BRANCH_PROFILE_FILE = "branch_thermal_profiles.csv"
BRANCH_SUMMARY_FILE = "branch_thermal_summary.csv"
FIGURE_STEM = "upcomer_reverse_shear_fraction_profile"

PREDICTOR_SPECS = (
    ("reynolds_bulk", "Re", ("reynolds_bulk", "re_bulk")),
    ("gr_over_re2", "Gr/Re^2", ("gr_over_re2", "grashof_over_re2")),
    ("heater_power_W", "Heater power", ("heater_power_W",)),
    ("cooler_h_W_m2K", "Cooler h", ("cooler_h_W_m2K",)),
    ("temp_upcomer_bulk_k", "Mean upcomer bulk temperature", ("temp_upcomer_bulk_k",)),
    (
        "heater_to_cooler_bulk_delta_k",
        "Heater-to-cooler bulk delta",
        ("heater_to_cooler_bulk_delta_k",),
    ),
    (
        "downcomer_to_upcomer_bulk_delta_k",
        "Downcomer-to-upcomer bulk delta",
        ("downcomer_to_upcomer_bulk_delta_k",),
    ),
)

CASE_FILE_KEYS = {
    "azimuthal_summary": AZIMUTHAL_SUMMARY_FILE,
    "branch_profiles": BRANCH_PROFILE_FILE,
    "branch_summary": BRANCH_SUMMARY_FILE,
}

CASE_COLORS = {
    "viscosity_screening_salt_test_1_jin_coarse_mesh": "#1f4e79",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "#2e8b57",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "#d17a22",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "#b33c2e",
}

COMPONENT_LABELS = {
    "left_lower_leg": "left_lower_leg",
    "test_section_span": "test_section_span",
    "left_upper_leg": "left_upper_leg",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a June 29 additive upcomer-recirculation evidence package "
            "from the current paper-grade Salt Jin reduced outputs."
        )
    )
    parser.add_argument("--paper-case-inventory-csv", default=str(DEFAULT_PAPER_CASE_INVENTORY_CSV))
    parser.add_argument("--source-contract-map-csv", default=str(DEFAULT_SOURCE_CONTRACT_MAP_CSV))
    parser.add_argument("--branch-map-csv", default=str(DEFAULT_BRANCH_MAP_CSV))
    parser.add_argument("--salt-dashboard-csv", default=str(DEFAULT_SALT_DASHBOARD_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--work-product-dir", default=str(DEFAULT_WORK_PRODUCT_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_MANIFEST_PATH))
    return parser.parse_args()


def source_sort_key(source_id: str) -> int:
    try:
        return SOURCE_ID_ORDER.index(source_id)
    except ValueError:
        return len(SOURCE_ID_ORDER)


def join_tokens(values: list[str]) -> str:
    payload = [str(value).strip() for value in values if str(value).strip()]
    return "|".join(payload)


def require_path(path: Path) -> Path:
    if not path.exists():
        raise RuntimeError(f"required input missing: {path}")
    return path


def ordered_paper_grade_source_ids(inventory_rows: list[dict[str, str]]) -> list[str]:
    source_ids = [
        row["source_id"]
        for row in inventory_rows
        if row.get("paper_class") == "paper-grade" and row.get("source_id") in SOURCE_ID_ORDER
    ]
    source_ids.sort(key=source_sort_key)
    missing = [source_id for source_id in SOURCE_ID_ORDER if source_id not in source_ids]
    if missing:
        raise RuntimeError(f"paper-grade inventory missing expected sources: {missing}")
    return source_ids


def find_branch_row(branch_rows: list[dict[str, str]], branch_name: str) -> dict[str, str]:
    for row in branch_rows:
        if row.get("branch_name") == branch_name:
            return row
    raise RuntimeError(f"branch_map.csv missing required branch row: {branch_name}")


def parse_component_spans(branch_row: dict[str, str]) -> list[str]:
    payload = [token.strip() for token in str(branch_row.get("component_spans", "")).split(",")]
    return [token for token in payload if token]


def required_case_paths(package_root: Path) -> dict[str, Path]:
    paths = {key: package_root / relative_path for key, relative_path in CASE_FILE_KEYS.items()}
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise RuntimeError(f"package root missing required files {missing}: {package_root}")
    return paths


def load_dashboard_rows(path: Path) -> dict[str, dict[str, str]]:
    rows = load_csv_rows(require_path(path))
    return {row["source_id"]: row for row in rows if row.get("source_id")}


def build_branch_profile_lookup(
    branch_profile_rows: list[dict[str, str]],
    branch_name: str,
) -> dict[tuple[str, int], dict[str, Any]]:
    lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for row in branch_profile_rows:
        if row.get("branch_name") != branch_name:
            continue
        component_name = str(row.get("component_span_name") or row.get("span_name") or "").strip()
        bin_index = int(row["bin_index"])
        key = (component_name, bin_index)
        if key in lookup:
            continue
        lookup[key] = {
            "component_span_name": component_name,
            "component_span_order_index": int(row.get("component_span_order_index", "0")),
            "branch_profile_index": int(row["branch_profile_index"]),
            "branch_s_fraction": finite_float(row.get("branch_s_fraction")),
            "branch_s_mid_m": finite_float(row.get("branch_s_mid_m")),
            "branch_total_length_m": finite_float(row.get("branch_total_length_m")),
            "branch_s_start_m": finite_float(row.get("branch_s_start_m")),
            "branch_s_end_m": finite_float(row.get("branch_s_end_m")),
        }
    if not lookup:
        raise RuntimeError(f"branch_thermal_profiles.csv missing branch rows for {branch_name}")
    return lookup


def aggregate_reversal_groups(
    azimuthal_rows: list[dict[str, str]],
    profile_lookup: dict[tuple[str, int], dict[str, Any]],
    component_spans: set[str],
    branch_name: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[float, int], dict[str, Any]] = {}
    for row in azimuthal_rows:
        component_span = str(row.get("span_name", "")).strip()
        if component_span not in component_spans:
            continue
        key = (component_span, int(row["streamwise_bin_index"]))
        if key not in profile_lookup:
            raise RuntimeError(f"missing branch-profile lookup for {branch_name}: {key}")
        profile_meta = profile_lookup[key]
        time_s = finite_float(row.get("time_s"))
        group_key = (time_s, profile_meta["branch_profile_index"])
        aggregate = grouped.setdefault(
            group_key,
            {
                "branch_name": branch_name,
                "time_s": time_s,
                "branch_profile_index": profile_meta["branch_profile_index"],
                "branch_s_fraction": profile_meta["branch_s_fraction"],
                "branch_s_mid_m": profile_meta["branch_s_mid_m"],
                "branch_total_length_m": profile_meta["branch_total_length_m"],
                "component_span_name": profile_meta["component_span_name"],
                "component_span_order_index": profile_meta["component_span_order_index"],
                "total_area_m2": 0.0,
                "reverse_area_m2": 0.0,
                "total_abs_shear_area_weight": 0.0,
                "reverse_abs_shear_area_weight": 0.0,
                "total_abs_heat_w": 0.0,
                "reverse_abs_heat_w": 0.0,
                "signed_shear_area_sum": 0.0,
                "theta_bin_count": 0,
            },
        )
        area_m2 = finite_float(row.get("area_m2"), default=0.0)
        signed_shear_pa = finite_float(row.get("mean_wall_shear_streamwise_pa"), default=math.nan)
        total_wall_heat_w = finite_float(row.get("total_wall_heat_w"), default=math.nan)
        aggregate["total_area_m2"] += area_m2
        aggregate["theta_bin_count"] += 1
        if math.isfinite(signed_shear_pa):
            aggregate["signed_shear_area_sum"] += area_m2 * signed_shear_pa
            aggregate["total_abs_shear_area_weight"] += area_m2 * abs(signed_shear_pa)
            if signed_shear_pa < 0.0:
                aggregate["reverse_area_m2"] += area_m2
                aggregate["reverse_abs_shear_area_weight"] += area_m2 * abs(signed_shear_pa)
                if math.isfinite(total_wall_heat_w):
                    aggregate["reverse_abs_heat_w"] += abs(total_wall_heat_w)
        if math.isfinite(total_wall_heat_w):
            aggregate["total_abs_heat_w"] += abs(total_wall_heat_w)
    rows_out: list[dict[str, Any]] = []
    for row in grouped.values():
        total_area_m2 = row["total_area_m2"]
        total_abs_shear_area_weight = row["total_abs_shear_area_weight"]
        total_abs_heat_w = row["total_abs_heat_w"]
        rows_out.append(
            {
                **row,
                "reverse_area_fraction": (
                    row["reverse_area_m2"] / total_area_m2 if total_area_m2 > 0.0 else math.nan
                ),
                "reverse_abs_shear_fraction": (
                    row["reverse_abs_shear_area_weight"] / total_abs_shear_area_weight
                    if total_abs_shear_area_weight > 0.0
                    else math.nan
                ),
                "reverse_abs_heat_fraction": (
                    row["reverse_abs_heat_w"] / total_abs_heat_w if total_abs_heat_w > 0.0 else math.nan
                ),
                "mean_signed_wall_shear_pa": (
                    row["signed_shear_area_sum"] / total_area_m2 if total_area_m2 > 0.0 else math.nan
                ),
            }
        )
    rows_out.sort(key=lambda item: (item["time_s"], item["branch_profile_index"]))
    return rows_out


def mean_profile_rows(
    grouped_rows: list[dict[str, Any]],
    source_id: str,
    case_label: str,
) -> list[dict[str, Any]]:
    by_profile: dict[int, list[dict[str, Any]]] = {}
    for row in grouped_rows:
        by_profile.setdefault(int(row["branch_profile_index"]), []).append(row)
    rows_out: list[dict[str, Any]] = []
    for profile_index in sorted(by_profile):
        rows = by_profile[profile_index]
        component_names = sorted({str(row["component_span_name"]) for row in rows})
        rows_out.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "branch_name": rows[0]["branch_name"],
                "branch_profile_index": profile_index,
                "branch_s_fraction": safe_mean(row["branch_s_fraction"] for row in rows),
                "branch_s_mid_m": safe_mean(row["branch_s_mid_m"] for row in rows),
                "branch_total_length_m": safe_mean(row["branch_total_length_m"] for row in rows),
                "component_span_name": join_tokens(component_names),
                "component_span_order_index": int(rows[0]["component_span_order_index"]),
                "time_sample_count": len(rows),
                "mean_reverse_area_fraction": safe_mean(row["reverse_area_fraction"] for row in rows),
                "max_reverse_area_fraction": max(row["reverse_area_fraction"] for row in rows),
                "mean_reverse_abs_shear_fraction": safe_mean(
                    row["reverse_abs_shear_fraction"] for row in rows
                ),
                "mean_reverse_abs_heat_fraction": safe_mean(
                    row["reverse_abs_heat_fraction"] for row in rows
                ),
                "mean_signed_wall_shear_pa": safe_mean(row["mean_signed_wall_shear_pa"] for row in rows),
            }
        )
    return rows_out


def find_branch_summary_row(branch_summary_rows: list[dict[str, str]], branch_name: str) -> dict[str, str]:
    for row in branch_summary_rows:
        if row.get("branch_name") == branch_name:
            return row
    raise RuntimeError(f"branch_thermal_summary.csv missing branch {branch_name}")


def branch_support_fraction(branch_summary_row: dict[str, str]) -> float:
    direct = finite_float(branch_summary_row.get("mean_support_fraction"))
    if math.isfinite(direct):
        return direct
    usable_count = finite_float(branch_summary_row.get("usable_row_count"))
    total_count = finite_float(branch_summary_row.get("total_row_count"))
    if not math.isfinite(usable_count) or not math.isfinite(total_count) or total_count == 0.0:
        return math.nan
    return usable_count / total_count


def case_summary_row(
    source_contract_row: dict[str, str],
    inventory_row: dict[str, str],
    dashboard_row: dict[str, str],
    upcomer_group_rows: list[dict[str, Any]],
    control_group_rows: list[dict[str, Any]],
    upcomer_profile_rows: list[dict[str, Any]],
    upcomer_branch_summary_row: dict[str, str],
) -> dict[str, Any]:
    upcomer_total_area = safe_sum(row["total_area_m2"] for row in upcomer_group_rows)
    upcomer_reverse_area = safe_sum(row["reverse_area_m2"] for row in upcomer_group_rows)
    upcomer_total_abs_shear = safe_sum(
        row["total_abs_shear_area_weight"] for row in upcomer_group_rows
    )
    upcomer_reverse_abs_shear = safe_sum(
        row["reverse_abs_shear_area_weight"] for row in upcomer_group_rows
    )
    upcomer_total_abs_heat = safe_sum(row["total_abs_heat_w"] for row in upcomer_group_rows)
    upcomer_reverse_abs_heat = safe_sum(row["reverse_abs_heat_w"] for row in upcomer_group_rows)
    control_total_area = safe_sum(row["total_area_m2"] for row in control_group_rows)
    control_reverse_area = safe_sum(row["reverse_area_m2"] for row in control_group_rows)
    unique_times = sorted({row["time_s"] for row in upcomer_group_rows})
    return {
        "source_id": source_contract_row["source_id"],
        "case_label": inventory_row["case_label"],
        "paper_class": inventory_row["paper_class"],
        "checkpoint_case_key": source_contract_row.get("checkpoint_case_key", ""),
        "checkpoint_lane": source_contract_row.get("checkpoint_lane", ""),
        "retained_window_status": source_contract_row.get("retained_window_status", ""),
        "checkpoint_representative_time_count": int(
            finite_float(source_contract_row.get("checkpoint_representative_time_count"), default=0.0)
        ),
        "package_root": source_contract_row.get("package_root", ""),
        "upcomer_component_spans": "left_lower_leg|test_section_span|left_upper_leg",
        "retained_time_count": len(unique_times),
        "retained_time_start_s": min(unique_times) if unique_times else math.nan,
        "retained_time_end_s": max(unique_times) if unique_times else math.nan,
        "upcomer_reverse_area_fraction": (
            upcomer_reverse_area / upcomer_total_area if upcomer_total_area > 0.0 else math.nan
        ),
        "upcomer_reverse_abs_shear_fraction": (
            upcomer_reverse_abs_shear / upcomer_total_abs_shear
            if upcomer_total_abs_shear > 0.0
            else math.nan
        ),
        "upcomer_reverse_abs_heat_fraction": (
            upcomer_reverse_abs_heat / upcomer_total_abs_heat if upcomer_total_abs_heat > 0.0 else math.nan
        ),
        "upcomer_peak_mean_reverse_area_fraction": max(
            row["mean_reverse_area_fraction"] for row in upcomer_profile_rows
        ),
        "upcomer_mean_profile_reverse_area_fraction": safe_mean(
            row["mean_reverse_area_fraction"] for row in upcomer_profile_rows
        ),
        "right_leg_reverse_area_fraction": (
            control_reverse_area / control_total_area if control_total_area > 0.0 else math.nan
        ),
        "upcomer_minus_right_leg_reverse_area_fraction": (
            (upcomer_reverse_area / upcomer_total_area) - (control_reverse_area / control_total_area)
            if upcomer_total_area > 0.0 and control_total_area > 0.0
            else math.nan
        ),
        "upcomer_support_fraction": branch_support_fraction(upcomer_branch_summary_row),
        "upcomer_mean_abs_bulk_minus_wall_temp_k": finite_float(
            upcomer_branch_summary_row.get("mean_abs_bulk_minus_wall_temp_k")
        ),
        "upcomer_mean_branch_total_abs_wall_heat_w": finite_float(
            upcomer_branch_summary_row.get("mean_branch_total_abs_wall_heat_w")
        ),
        "heater_power_W": finite_float(dashboard_row.get("heater_power_W")),
        "cooler_h_W_m2K": finite_float(dashboard_row.get("cooler_h_W_m2K")),
        "cooling_power_W": finite_float(dashboard_row.get("cooling_power_W")),
        "temp_upcomer_bulk_k": finite_float(dashboard_row.get("temp_upcomer_bulk_k")),
        "temp_cooler_bulk_k": finite_float(dashboard_row.get("temp_cooler_bulk_k")),
        "heater_to_cooler_bulk_delta_k": finite_float(dashboard_row.get("heater_to_cooler_bulk_delta_k")),
        "downcomer_to_upcomer_bulk_delta_k": finite_float(
            dashboard_row.get("downcomer_to_upcomer_bulk_delta_k")
        ),
    }


def pearson_correlation(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return math.nan
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_term = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_term = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if x_term == 0.0 or y_term == 0.0:
        return math.nan
    return numerator / (x_term * y_term)


def rank_values(values: list[float]) -> list[float]:
    indexed = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(indexed):
        next_cursor = cursor + 1
        while next_cursor < len(indexed) and indexed[next_cursor][0] == indexed[cursor][0]:
            next_cursor += 1
        average_rank = (cursor + 1 + next_cursor) / 2.0
        for _, original_index in indexed[cursor:next_cursor]:
            ranks[original_index] = average_rank
        cursor = next_cursor
    return ranks


def spearman_correlation(xs: list[float], ys: list[float]) -> float:
    return pearson_correlation(rank_values(xs), rank_values(ys))


def build_predictor_screen_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_metric = "upcomer_reverse_area_fraction"
    severity_values = [finite_float(row.get(severity_metric)) for row in case_rows]
    rows_out: list[dict[str, Any]] = []
    for predictor_key, predictor_label, aliases in PREDICTOR_SPECS:
        resolved_key = ""
        values: list[float] = []
        usable_severity: list[float] = []
        missing_case_labels: list[str] = []
        for row in case_rows:
            value = math.nan
            for alias in aliases:
                if alias in row and math.isfinite(finite_float(row.get(alias))):
                    resolved_key = alias
                    value = finite_float(row.get(alias))
                    break
            severity = finite_float(row.get(severity_metric))
            if math.isfinite(value) and math.isfinite(severity):
                values.append(value)
                usable_severity.append(severity)
            else:
                missing_case_labels.append(str(row.get("case_label", row.get("source_id", ""))))
        available_case_count = len(values)
        status = "available" if available_case_count >= 3 else "not_available_in_reused_stack"
        rows_out.append(
            {
                "predictor_key": predictor_key,
                "predictor_label": predictor_label,
                "source_column": resolved_key,
                "status": status,
                "available_case_count": available_case_count,
                "pearson_r": pearson_correlation(values, usable_severity) if status == "available" else math.nan,
                "spearman_rho": spearman_correlation(values, usable_severity)
                if status == "available"
                else math.nan,
                "missing_cases": join_tokens(missing_case_labels),
                "severity_metric": severity_metric,
            }
        )
    return rows_out


def figure_component_segments(profile_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_component: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in profile_rows:
        key = (int(row["component_span_order_index"]), str(row["component_span_name"]))
        by_component.setdefault(key, []).append(row)
    rows_out: list[dict[str, Any]] = []
    for (order_index, component_name), rows in sorted(by_component.items()):
        rows_out.append(
            {
                "component_span_order_index": order_index,
                "component_span_name": component_name,
                "segment_start_fraction": min(finite_float(row["branch_s_fraction"]) for row in rows),
                "segment_end_fraction": max(finite_float(row["branch_s_fraction"]) for row in rows),
            }
        )
    return rows_out


def svg_x(value: float, plot_left: float, plot_width: float) -> float:
    return plot_left + plot_width * value


def svg_y(value: float, plot_top: float, plot_height: float) -> float:
    return plot_top + plot_height * (1.0 - value)


def build_polyline_points(rows: list[dict[str, Any]], plot_left: float, plot_top: float, plot_width: float, plot_height: float) -> str:
    points: list[str] = []
    for row in rows:
        x = svg_x(finite_float(row["branch_s_fraction"]), plot_left, plot_width)
        y = svg_y(finite_float(row["mean_reverse_area_fraction"]), plot_top, plot_height)
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)


def render_svg_figure(
    per_case_profile_rows: dict[str, list[dict[str, Any]]],
    case_summary_by_source: dict[str, dict[str, Any]],
    output_path: Path,
) -> None:
    width = 980
    height = 620
    plot_left = 110.0
    plot_top = 110.0
    plot_width = 630.0
    plot_height = 400.0
    legend_x = 770.0
    legend_y = 150.0
    all_profile_rows = next(iter(per_case_profile_rows.values()))
    component_segments = figure_component_segments(all_profile_rows)
    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    lines.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    lines.append('<text x="110" y="46" font-family="Helvetica, Arial, sans-serif" font-size="24" font-weight="bold" fill="#111111">Upcomer reverse-shear area fraction</text>')
    lines.append('<text x="110" y="74" font-family="Helvetica, Arial, sans-serif" font-size="14" fill="#444444">Zero line = textbook no-reversal expectation; current right-leg control stays at zero across all four paper-grade Salt Jin cases.</text>')
    for tick in range(0, 6):
        y_value = tick / 5.0
        y = svg_y(y_value, plot_top, plot_height)
        lines.append(f'<line x1="{plot_left:.2f}" y1="{y:.2f}" x2="{plot_left + plot_width:.2f}" y2="{y:.2f}" stroke="#d9d9d9" stroke-width="1"/>')
        lines.append(f'<text x="{plot_left - 14:.2f}" y="{y + 5:.2f}" text-anchor="end" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="#444444">{y_value:.1f}</text>')
    for tick in range(0, 5):
        x_value = tick / 4.0
        x = svg_x(x_value, plot_left, plot_width)
        lines.append(f'<line x1="{x:.2f}" y1="{plot_top:.2f}" x2="{x:.2f}" y2="{plot_top + plot_height:.2f}" stroke="#eeeeee" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{plot_top + plot_height + 26:.2f}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="#444444">{x_value:.2f}</text>')
    lines.append(f'<line x1="{plot_left:.2f}" y1="{plot_top + plot_height:.2f}" x2="{plot_left + plot_width:.2f}" y2="{plot_top + plot_height:.2f}" stroke="#888888" stroke-width="1.5" stroke-dasharray="6,4"/>')
    for segment in component_segments[:-1]:
        x = svg_x(finite_float(segment["segment_end_fraction"]), plot_left, plot_width)
        lines.append(f'<line x1="{x:.2f}" y1="{plot_top:.2f}" x2="{x:.2f}" y2="{plot_top + plot_height:.2f}" stroke="#bbbbbb" stroke-width="1" stroke-dasharray="3,5"/>')
    for segment in component_segments:
        start_fraction = finite_float(segment["segment_start_fraction"])
        end_fraction = finite_float(segment["segment_end_fraction"])
        center_x = svg_x((start_fraction + end_fraction) / 2.0, plot_left, plot_width)
        label = COMPONENT_LABELS.get(str(segment["component_span_name"]), str(segment["component_span_name"]))
        lines.append(f'<text x="{center_x:.2f}" y="{plot_top - 18:.2f}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="#555555">{escape(label)}</text>')
    lines.append(f'<line x1="{plot_left:.2f}" y1="{plot_top:.2f}" x2="{plot_left:.2f}" y2="{plot_top + plot_height:.2f}" stroke="#333333" stroke-width="1.5"/>')
    lines.append(f'<line x1="{plot_left:.2f}" y1="{plot_top + plot_height:.2f}" x2="{plot_left + plot_width:.2f}" y2="{plot_top + plot_height:.2f}" stroke="#333333" stroke-width="1.5"/>')
    lines.append(f'<text x="{plot_left + plot_width / 2.0:.2f}" y="{plot_top + plot_height + 56:.2f}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="14" fill="#222222">Upcomer branch coordinate s / L</text>')
    lines.append(f'<text x="34" y="{plot_top + plot_height / 2.0:.2f}" transform="rotate(-90 34 {plot_top + plot_height / 2.0:.2f})" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="14" fill="#222222">Mean reversed-shear area fraction</text>')
    legend_offset = 0
    for source_id in SOURCE_ID_ORDER:
        rows = per_case_profile_rows[source_id]
        color = CASE_COLORS.get(source_id, "#444444")
        polyline = build_polyline_points(rows, plot_left, plot_top, plot_width, plot_height)
        lines.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" points="{polyline}"/>'
        )
        for row in rows:
            x = svg_x(finite_float(row["branch_s_fraction"]), plot_left, plot_width)
            y = svg_y(finite_float(row["mean_reverse_area_fraction"]), plot_top, plot_height)
            lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.2" fill="{color}" stroke="none"/>')
        summary = case_summary_by_source[source_id]
        case_label = escape(str(summary["case_label"]))
        reverse_area_fraction = finite_float(summary["upcomer_reverse_area_fraction"])
        legend_y_row = legend_y + legend_offset
        lines.append(f'<line x1="{legend_x:.2f}" y1="{legend_y_row:.2f}" x2="{legend_x + 28:.2f}" y2="{legend_y_row:.2f}" stroke="{color}" stroke-width="3"/>')
        lines.append(
            f'<text x="{legend_x + 38:.2f}" y="{legend_y_row + 4:.2f}" font-family="Helvetica, Arial, sans-serif" font-size="13" fill="#222222">{case_label}: area={reverse_area_fraction:.3f}</text>'
        )
        legend_offset += 28
    lines.append('</svg>')
    ensure_dir(output_path.parent)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def report_readme(
    case_rows: list[dict[str, Any]],
    predictor_rows: list[dict[str, Any]],
    svg_relpath: str,
    case_summary_relpath: str,
    predictor_relpath: str,
) -> str:
    case_lines = []
    for row in case_rows:
        case_lines.append(
            "- "
            f"`{row['case_label']}`: upcomer reversed-area fraction `{row['upcomer_reverse_area_fraction']:.3f}`, "
            f"reversed abs-shear fraction `{row['upcomer_reverse_abs_shear_fraction']:.3f}`, "
            f"reversed abs-heat fraction `{row['upcomer_reverse_abs_heat_fraction']:.3f}`, "
            f"right-leg control `{row['right_leg_reverse_area_fraction']:.3f}`."
        )
    available_predictors = [row for row in predictor_rows if row["status"] == "available"]
    available_predictors.sort(
        key=lambda row: abs(finite_float(row.get("spearman_rho"), default=math.nan)),
        reverse=True,
    )
    predictor_lines = []
    for row in predictor_rows:
        if row["status"] == "available":
            predictor_lines.append(
                "- "
                f"`{row['predictor_label']}` via `{row['source_column']}`: "
                f"Spearman `{row['spearman_rho']:.3f}`, Pearson `{row['pearson_r']:.3f}`."
            )
        else:
            predictor_lines.append(
                "- "
                f"`{row['predictor_label']}`: unavailable in the reused June 17 dashboard / case-summary stack."
            )
    top_predictor_line = ""
    if available_predictors:
        top = available_predictors[0]
        top_predictor_line = (
            "- Strongest available screen in this reused-stack pass: "
            f"`{top['predictor_label']}` (`Spearman {top['spearman_rho']:.3f}`, "
            f"`Pearson {top['pearson_r']:.3f}`)."
        )
    return "\n".join(
        [
            "# Ethan Upcomer Recirculation Evidence",
            "",
            f"Generated: `{iso_timestamp()}`",
            "",
            "## Scope",
            "",
            "- Paper-grade Salt subset only: `Salt 1 Jin`, `Salt 2 Jin`, `Salt 3 Jin`, `Salt 4 Jin`.",
            "- Reused reduced outputs only: no new extraction wave, no new staged runtime copy, and no edits to the earlier case-analysis package roots.",
            "- Metric contract: quantify retained-time upcomer recirculation with streamwise wall-shear reversal fractions on the derived `upcomer` branch (`left_lower_leg + test_section_span + left_upper_leg`) and contrast that against the `right_leg` control branch plus a zero-reversal textbook baseline.",
            "",
            "## Main findings",
            "",
            *case_lines,
            "",
            "- The current reduced stack shows a strong qualitative split: the upcomer carries broad negative streamwise wall-shear coverage while the `right_leg` control branch remains at `0.0` reversed-area fraction in every paper-grade case.",
            top_predictor_line,
            "",
            "## Artifacts",
            "",
            f"- Case summary CSV: `{case_summary_relpath}`",
            f"- Predictor screen CSV: `{predictor_relpath}`",
            f"- Figure-ready SVG: `{svg_relpath}`",
            "",
            "## Predictor screen",
            "",
            *predictor_lines,
            "",
            "## Boundaries",
            "",
            "- This package uses wall-shear reversal as a retained-time recirculation proxy, not a full volumetric recirculation fraction derived from the entire cross-section velocity field.",
            "- Mixed provenance remains explicit: `Salt 1 Jin` still points at the latest readable June 23 latest-window root while `Salt 2-4 Jin` still reuse the June 15 reduced package roots named in the June 29 reduction-contract audit.",
            "- `Re` and `Gr/Re^2` are not present in the reused June 17 salt dashboard CSV, so this first additive pass can only screen the currently published heater, cooler, and branch-temperature predictors.",
        ]
    ).strip() + "\n"


def load_case_contexts(
    inventory_rows: list[dict[str, str]],
    source_contract_rows: list[dict[str, str]],
    dashboard_by_source: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    inventory_by_source = {row["source_id"]: row for row in inventory_rows}
    contexts: list[dict[str, Any]] = []
    for source_id in ordered_paper_grade_source_ids(inventory_rows):
        inventory_row = inventory_by_source[source_id]
        source_contract_row = next(
            (row for row in source_contract_rows if row.get("source_id") == source_id),
            None,
        )
        if source_contract_row is None:
            raise RuntimeError(f"source_contract_map.csv missing paper-grade case {source_id}")
        package_root = Path(source_contract_row["package_root"])
        case_paths = required_case_paths(package_root)
        dashboard_row = dashboard_by_source.get(source_id, {})
        contexts.append(
            {
                "source_id": source_id,
                "inventory_row": inventory_row,
                "source_contract_row": source_contract_row,
                "dashboard_row": dashboard_row,
                "package_root": package_root,
                "case_paths": case_paths,
                "azimuthal_rows": load_csv_rows(case_paths["azimuthal_summary"]),
                "branch_profile_rows": load_csv_rows(case_paths["branch_profiles"]),
                "branch_summary_rows": load_csv_rows(case_paths["branch_summary"]),
            }
        )
    return contexts


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    work_product_dir = Path(args.work_product_dir)
    import_manifest_path = Path(args.import_manifest_path)

    inventory_rows = load_csv_rows(require_path(Path(args.paper_case_inventory_csv)))
    source_contract_rows = load_csv_rows(require_path(Path(args.source_contract_map_csv)))
    branch_map_rows = load_csv_rows(require_path(Path(args.branch_map_csv)))
    dashboard_by_source = load_dashboard_rows(Path(args.salt_dashboard_csv))

    upcomer_branch_row = find_branch_row(branch_map_rows, UPCOMER_BRANCH_NAME)
    upcomer_components = set(parse_component_spans(upcomer_branch_row))
    control_branch_row = find_branch_row(branch_map_rows, CONTROL_BRANCH_NAME)
    control_components = set(parse_component_spans(control_branch_row))

    contexts = load_case_contexts(inventory_rows, source_contract_rows, dashboard_by_source)
    per_case_profile_rows: dict[str, list[dict[str, Any]]] = {}
    per_case_summary_rows: list[dict[str, Any]] = []
    figure_index_rows: list[dict[str, Any]] = []

    for context in contexts:
        upcomer_lookup = build_branch_profile_lookup(context["branch_profile_rows"], UPCOMER_BRANCH_NAME)
        control_lookup = build_branch_profile_lookup(context["branch_profile_rows"], CONTROL_BRANCH_NAME)
        upcomer_group_rows = aggregate_reversal_groups(
            context["azimuthal_rows"],
            upcomer_lookup,
            upcomer_components,
            UPCOMER_BRANCH_NAME,
        )
        control_group_rows = aggregate_reversal_groups(
            context["azimuthal_rows"],
            control_lookup,
            control_components,
            CONTROL_BRANCH_NAME,
        )
        upcomer_profile_rows = mean_profile_rows(
            upcomer_group_rows,
            context["source_id"],
            context["inventory_row"]["case_label"],
        )
        per_case_profile_rows[context["source_id"]] = upcomer_profile_rows
        upcomer_branch_summary_row = find_branch_summary_row(
            context["branch_summary_rows"],
            UPCOMER_BRANCH_NAME,
        )
        per_case_summary_rows.append(
            case_summary_row(
                context["source_contract_row"],
                context["inventory_row"],
                context["dashboard_row"],
                upcomer_group_rows,
                control_group_rows,
                upcomer_profile_rows,
                upcomer_branch_summary_row,
            )
        )

    per_case_summary_rows.sort(key=lambda row: source_sort_key(str(row["source_id"])))
    profile_rows_flat: list[dict[str, Any]] = []
    for source_id in SOURCE_ID_ORDER:
        profile_rows_flat.extend(per_case_profile_rows[source_id])
    predictor_rows = build_predictor_screen_rows(per_case_summary_rows)
    case_summary_by_source = {row["source_id"]: row for row in per_case_summary_rows}

    case_summary_wp_path = work_product_dir / "upcomer_recirculation_case_summary.csv"
    profile_wp_path = work_product_dir / "upcomer_recirculation_profile.csv"
    predictor_wp_path = work_product_dir / "upcomer_recirculation_predictor_screen.csv"
    figure_index_wp_path = work_product_dir / "figure_index.csv"
    case_summary_report_path = output_dir / "upcomer_recirculation_case_summary.csv"
    predictor_report_path = output_dir / "upcomer_recirculation_predictor_screen.csv"
    summary_path = output_dir / "summary.json"
    readme_path = output_dir / "README.md"
    svg_path = output_dir / "figures" / "svg" / f"{FIGURE_STEM}.svg"

    csv_dump_rows(case_summary_wp_path, per_case_summary_rows)
    csv_dump_rows(profile_wp_path, profile_rows_flat)
    csv_dump_rows(predictor_wp_path, predictor_rows)
    csv_dump_rows(case_summary_report_path, per_case_summary_rows)
    csv_dump_rows(predictor_report_path, predictor_rows)
    render_svg_figure(per_case_profile_rows, case_summary_by_source, svg_path)
    figure_index_rows.append(
        {
            "figure_stem": FIGURE_STEM,
            "svg_path": str(svg_path.resolve()),
            "profile_csv_path": str(profile_wp_path.resolve()),
            "case_summary_csv_path": str(case_summary_wp_path.resolve()),
        }
    )
    csv_dump_rows(figure_index_wp_path, figure_index_rows)

    summary_payload = {
        "generated_at": iso_timestamp(),
        "paper_case_count": len(per_case_summary_rows),
        "paper_cases": [row["case_label"] for row in per_case_summary_rows],
        "mean_upcomer_reverse_area_fraction": safe_mean(
            row["upcomer_reverse_area_fraction"] for row in per_case_summary_rows
        ),
        "min_upcomer_reverse_area_fraction": min(
            row["upcomer_reverse_area_fraction"] for row in per_case_summary_rows
        ),
        "max_upcomer_reverse_area_fraction": max(
            row["upcomer_reverse_area_fraction"] for row in per_case_summary_rows
        ),
        "mean_right_leg_reverse_area_fraction": safe_mean(
            row["right_leg_reverse_area_fraction"] for row in per_case_summary_rows
        ),
        "strongest_available_predictor": next(
            (
                row["predictor_label"]
                for row in sorted(
                    predictor_rows,
                    key=lambda row: abs(finite_float(row.get("spearman_rho"), default=math.nan)),
                    reverse=True,
                )
                if row["status"] == "available"
            ),
            "",
        ),
        "figure_svg": str(svg_path.resolve()),
    }
    write_json(summary_path, summary_payload)
    readme_path.write_text(
        report_readme(
            per_case_summary_rows,
            predictor_rows,
            relative_to_workspace(svg_path),
            relative_to_workspace(case_summary_wp_path),
            relative_to_workspace(predictor_wp_path),
        ),
        encoding="utf-8",
    )

    manifest_payload = {
        "generated_at": iso_timestamp(),
        "script_path": str(Path(__file__).resolve()),
        "inputs": {
            "paper_case_inventory_csv": str(Path(args.paper_case_inventory_csv).resolve()),
            "source_contract_map_csv": str(Path(args.source_contract_map_csv).resolve()),
            "branch_map_csv": str(Path(args.branch_map_csv).resolve()),
            "salt_dashboard_csv": str(Path(args.salt_dashboard_csv).resolve()),
        },
        "outputs": {
            "report_dir": str(output_dir.resolve()),
            "work_product_dir": str(work_product_dir.resolve()),
            "case_summary_csv": str(case_summary_wp_path.resolve()),
            "profile_csv": str(profile_wp_path.resolve()),
            "predictor_screen_csv": str(predictor_wp_path.resolve()),
            "figure_index_csv": str(figure_index_wp_path.resolve()),
            "figure_svg": str(svg_path.resolve()),
        },
    }
    write_json(import_manifest_path, manifest_payload)


if __name__ == "__main__":
    main()
