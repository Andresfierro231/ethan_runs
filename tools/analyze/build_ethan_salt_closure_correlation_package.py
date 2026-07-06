#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, safe_float, save_matplotlib_figure  # noqa: E402

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package"
DEFAULT_SMOKE_OUTPUT_DIR = ROOT / "tmp" / "2026-06-18_ethan_salt_closure_correlation_package_smoke"
PRESSURE_PACKAGE_DIR = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"
DASHBOARD_PACKAGE_DIR = ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package"
TRANSPORT_PACKAGE_DIR = ROOT / "reports" / "2026-06-15_ethan_all_runs_field_transport_campaign"
HEAT_AUDIT_DIR = ROOT / "reports" / "2026-06-09_ethan_steady_state_heat_flow_audit"

BRANCH_USABLE_MIN_FRACTION = 0.90
BRANCH_SCREENING_MIN_FRACTION = 0.75
BRANCH_WARNING_MAX_FRACTION = 0.10
BRANCH_SCREENING_MAX_WARNING_FRACTION = 0.25
BRANCH_MIN_DELTA_T_K = 0.50
BRANCH_BLOCKED_DELTA_T_K = 0.25
STRAIGHT_SECTION_MIN_SUPPORT = 0.75
STRAIGHT_SECTION_RATIO_MIN = 0.50
STRAIGHT_SECTION_RATIO_MAX = 2.00
FEATURE_MIN_KEFF = 0.0
ENTHALPY_RESIDUAL_FRACTION_CANDIDATE = 0.15
ENTHALPY_RESIDUAL_FRACTION_SCREENING = 0.30
REPRESENTATIVE_SALT_CASES = (
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an additive Salt-only closure and correlation-input package "
            "from the existing Ethan June 9/15/17 analysis artifacts."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more Salt source IDs.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: Any, default: float = math.nan) -> float:
    parsed = safe_float(value)
    if parsed is None or not math.isfinite(parsed):
        return default
    return float(parsed)


def is_finite(value: Any) -> bool:
    parsed = safe_float(value)
    return parsed is not None and math.isfinite(parsed)


def safe_mean(values: Iterable[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def safe_abs_max(values: Iterable[float]) -> float:
    payload = [abs(value) for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(max(payload))


def filter_salt_rows(rows: list[dict[str, str]], source_ids: set[str] | None = None) -> list[dict[str, str]]:
    payload = [row for row in rows if str(row.get("source_id", "")).strip()]
    payload = [row for row in payload if "water" not in str(row.get("source_id", "")).lower()]
    if source_ids:
        payload = [row for row in payload if row["source_id"] in source_ids]
    return payload


def filter_source_rows(rows: list[dict[str, str]], source_ids: set[str] | None = None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids]


def sign_token(value: float) -> str:
    if not math.isfinite(value):
        return "nan"
    if value > 0.0:
        return "positive"
    if value < 0.0:
        return "negative"
    return "zero"


def bool_text(flag: bool) -> str:
    return "yes" if flag else "no"


def case_order_lookup(dashboard_rows: list[dict[str, str]]) -> tuple[dict[str, int], dict[str, str]]:
    order: dict[str, int] = {}
    labels: dict[str, str] = {}
    for index, row in enumerate(dashboard_rows):
        source_id = row["source_id"]
        order[source_id] = index
        labels[source_id] = row["display_label"]
    return order, labels


def classify_branch_usability(row: dict[str, str]) -> tuple[str, str]:
    usable_fraction = finite_float(row.get("usable_fraction"))
    warning_fraction = finite_float(row.get("thermal_warning_fraction"))
    min_abs_delta_t = finite_float(row.get("min_abs_bulk_minus_wall_temp_k"))
    if (
        usable_fraction >= BRANCH_USABLE_MIN_FRACTION
        and warning_fraction <= BRANCH_WARNING_MAX_FRACTION
        and min_abs_delta_t >= BRANCH_MIN_DELTA_T_K
    ):
        return "candidate", "thermal_support_clean"
    if (
        usable_fraction < BRANCH_SCREENING_MIN_FRACTION
        or warning_fraction > BRANCH_SCREENING_MAX_WARNING_FRACTION
        or min_abs_delta_t < BRANCH_BLOCKED_DELTA_T_K
    ):
        if usable_fraction < BRANCH_SCREENING_MIN_FRACTION:
            return "do_not_fit", "thermal_low_usable_fraction"
        if min_abs_delta_t < BRANCH_BLOCKED_DELTA_T_K:
            return "do_not_fit", "thermal_small_delta_t"
        return "do_not_fit", "thermal_warning_dominated"
    return "screening_only", "thermal_support_marginal"


def classify_straight_section(row: dict[str, str]) -> tuple[str, str, float]:
    support_fraction = finite_float(row.get("mean_thermal_support_usable_fraction"))
    hydro_loss = finite_float(row.get("mean_pressure_loss_hydro_pa"))
    direct_darcy = finite_float(row.get("mean_direct_prgh_darcy_existing"))
    shear_darcy = finite_float(row.get("mean_shear_darcy_core"))
    ratio = (
        abs(direct_darcy / shear_darcy)
        if math.isfinite(direct_darcy) and math.isfinite(shear_darcy) and abs(shear_darcy) > 0.0
        else math.nan
    )
    if support_fraction < STRAIGHT_SECTION_MIN_SUPPORT:
        return "screening_only", "support_fraction_below_floor", ratio
    if not math.isfinite(hydro_loss):
        return "do_not_fit", "missing_hydro_loss", ratio
    if hydro_loss <= 0.0:
        return "screening_only", "buoyancy_aided_or_net_gain_section", ratio
    if not math.isfinite(direct_darcy) or not math.isfinite(shear_darcy):
        return "screening_only", "missing_direct_or_shear_reference", ratio
    if direct_darcy <= 0.0 or shear_darcy <= 0.0:
        return "do_not_fit", "nonpositive_direct_or_shear_friction_proxy", ratio
    if not math.isfinite(ratio):
        return "screening_only", "missing_direct_to_shear_ratio", ratio
    if ratio < STRAIGHT_SECTION_RATIO_MIN or ratio > STRAIGHT_SECTION_RATIO_MAX:
        return "screening_only", "direct_to_shear_magnitude_gap", ratio
    return "candidate", "dissipative_with_agreeing_friction_proxies", ratio


def classify_feature(row: dict[str, Any]) -> tuple[str, str]:
    keff = finite_float(row.get("mean_keff_reference"))
    if not math.isfinite(keff):
        return "do_not_fit", "missing_keff"
    if keff > FEATURE_MIN_KEFF:
        return "candidate", "positive_residual_feature_loss"
    return "screening_only", "nonpositive_residual_feature_loss"


def classify_enthalpy_closure(residual_fraction: float) -> tuple[str, str]:
    if not math.isfinite(residual_fraction):
        return "screening_only", "missing_wall_heat_reference"
    if residual_fraction <= ENTHALPY_RESIDUAL_FRACTION_CANDIDATE:
        return "candidate", "enthalpy_wall_heat_balance_tight"
    if residual_fraction <= ENTHALPY_RESIDUAL_FRACTION_SCREENING:
        return "screening_only", "enthalpy_wall_heat_balance_marginal"
    return "do_not_fit", "enthalpy_wall_heat_balance_loose"


def build_salt_hydraulic_sections(
    rows: list[dict[str, str]],
    case_order: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    section_rows: list[dict[str, Any]] = []
    fit_exclusions: list[dict[str, Any]] = []
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in filter_salt_rows(rows):
        fit_status, fit_reason, direct_to_shear_ratio = classify_straight_section(row)
        hydro_loss = finite_float(row.get("mean_pressure_loss_hydro_pa"))
        direct_loss = finite_float(row.get("mean_pressure_loss_prgh_endpoint_pa"))
        residual_vs_prgh = finite_float(row.get("mean_pressure_closure_residual_vs_prgh_endpoint_pa"))
        payload = {
            **row,
            "case_order": case_order.get(row["source_id"], 999),
            "net_section_role": "dissipative" if hydro_loss > 0.0 else "buoyancy_aided_or_net_gain",
            "hydro_loss_sign": sign_token(hydro_loss),
            "prgh_loss_sign": sign_token(direct_loss),
            "hydro_vs_prgh_direction_match": bool_text(
                sign_token(hydro_loss) == sign_token(direct_loss)
                if math.isfinite(hydro_loss) and math.isfinite(direct_loss)
                else False
            ),
            "direct_to_shear_darcy_ratio": direct_to_shear_ratio,
            "abs_pressure_closure_residual_vs_prgh_endpoint_pa": abs(residual_vs_prgh)
            if math.isfinite(residual_vs_prgh)
            else math.nan,
            "fit_status": fit_status,
            "fit_reason": fit_reason,
        }
        section_rows.append(payload)
        by_case[row["source_id"]].append(payload)
        if fit_status != "candidate":
            fit_exclusions.append(
                {
                    "source_id": row["source_id"],
                    "case_label": row["case_label"],
                    "asset_family": "straight_section_friction",
                    "scope_name": row["span_name"],
                    "fit_status": fit_status,
                    "fit_reason": fit_reason,
                }
            )

    case_rows: list[dict[str, Any]] = []
    for source_id, payload in sorted(by_case.items(), key=lambda item: case_order.get(item[0], 999)):
        hydro_losses = [finite_float(row["mean_pressure_loss_hydro_pa"]) for row in payload]
        direct_to_shear_ratios = [finite_float(row["direct_to_shear_darcy_ratio"]) for row in payload]
        case_rows.append(
            {
                "source_id": source_id,
                "case_label": payload[0]["case_label"],
                "straight_section_count": len(payload),
                "candidate_section_count": sum(1 for row in payload if row["fit_status"] == "candidate"),
                "screening_section_count": sum(1 for row in payload if row["fit_status"] == "screening_only"),
                "blocked_section_count": sum(1 for row in payload if row["fit_status"] == "do_not_fit"),
                "mean_abs_hydro_pressure_loss_pa": safe_mean(abs(value) for value in hydro_losses),
                "max_abs_hydro_pressure_loss_pa": safe_abs_max(hydro_losses),
                "mean_direct_to_shear_darcy_ratio": safe_mean(direct_to_shear_ratios),
                "buoyancy_aided_section_count": sum(
                    1 for row in payload if row["net_section_role"] == "buoyancy_aided_or_net_gain"
                ),
            }
        )
    section_rows.sort(key=lambda row: (row["case_order"], row["span_name"]))
    return section_rows, case_rows, fit_exclusions


def build_salt_feature_rows(
    rows: list[dict[str, str]],
    case_order: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payloads: list[dict[str, Any]] = []
    fit_exclusions: list[dict[str, Any]] = []
    for row in filter_salt_rows(rows):
        fit_status, fit_reason = classify_feature(row)
        payload = {
            **row,
            "case_order": case_order.get(row["source_id"], 999),
            "keff_sign": sign_token(finite_float(row.get("mean_keff_reference"))),
            "fit_status": fit_status,
            "fit_reason": fit_reason,
        }
        payloads.append(payload)
        if fit_status != "candidate":
            fit_exclusions.append(
                {
                    "source_id": row["source_id"],
                    "case_label": row["case_label"],
                    "asset_family": "feature_keff",
                    "scope_name": row["feature_name"],
                    "fit_status": fit_status,
                    "fit_reason": fit_reason,
                }
            )
    payloads.sort(key=lambda row: (row["case_order"], row["feature_name"]))
    return payloads, fit_exclusions


def build_salt_heat_partition_rows(
    heat_window_rows: list[dict[str, str]],
    heat_latest_rows: list[dict[str, str]],
    dashboard_rows: list[dict[str, str]],
    case_order: dict[str, int],
) -> list[dict[str, Any]]:
    latest_lookup = {row["source_id"]: row for row in filter_salt_rows(heat_latest_rows)}
    dashboard_lookup = {row["source_id"]: row for row in filter_salt_rows(dashboard_rows)}
    payloads: list[dict[str, Any]] = []
    for row in filter_salt_rows(heat_window_rows):
        source_id = row["source_id"]
        latest = latest_lookup[source_id]
        dashboard = dashboard_lookup[source_id]
        heater_power = finite_float(latest.get("heater_power_w"))
        ambient_proxy_mean = finite_float(row.get("ambient_proxy_w_mean"))
        ambient_noncooling_mean = finite_float(row.get("ambient_noncooling_proxy_w_mean"))
        cooling_total_mean = finite_float(row.get("cooling_branch_total_removal_w_mean"))
        cooling_excess_mean = finite_float(row.get("cooling_branch_excess_w_mean"))
        junction_mean = finite_float(row.get("section_junctions_net_q_w_mean"))
        payloads.append(
            {
                "source_id": source_id,
                "case_label": dashboard["display_label"],
                "case_order": case_order.get(source_id, 999),
                "run_status": dashboard.get("run_status", ""),
                "heater_power_w": heater_power,
                "cooling_power_nominal_w": finite_float(latest.get("cooling_power_w")),
                "ambient_proxy_mean_w": ambient_proxy_mean,
                "ambient_noncooling_proxy_mean_w": ambient_noncooling_mean,
                "cooling_branch_total_removal_mean_w": cooling_total_mean,
                "cooling_branch_excess_mean_w": cooling_excess_mean,
                "junction_loss_mean_w": junction_mean,
                "upper_transport_mean_w": finite_float(row.get("section_upper_transport_net_q_w_mean")),
                "lower_transport_mean_w": finite_float(row.get("section_lower_transport_net_q_w_mean")),
                "upcomer_mean_w": finite_float(row.get("section_upcomer_net_q_w_mean")),
                "downcomer_mean_w": finite_float(row.get("section_downcomer_net_q_w_mean")),
                "heater_section_mean_w": finite_float(row.get("section_heater_net_q_w_mean")),
                "test_section_mean_w": finite_float(row.get("section_test_section_net_q_w_mean")),
                "net_total_mean_w": finite_float(row.get("net_total_q_w_mean")),
                "ambient_proxy_fraction_of_heater": ambient_proxy_mean / heater_power
                if math.isfinite(ambient_proxy_mean) and math.isfinite(heater_power) and abs(heater_power) > 0.0
                else math.nan,
                "ambient_noncooling_fraction_of_heater": ambient_noncooling_mean / heater_power
                if math.isfinite(ambient_noncooling_mean) and math.isfinite(heater_power) and abs(heater_power) > 0.0
                else math.nan,
                "cooling_total_fraction_of_heater": cooling_total_mean / heater_power
                if math.isfinite(cooling_total_mean) and math.isfinite(heater_power) and abs(heater_power) > 0.0
                else math.nan,
                "cooling_excess_fraction_of_heater": cooling_excess_mean / heater_power
                if math.isfinite(cooling_excess_mean) and math.isfinite(heater_power) and abs(heater_power) > 0.0
                else math.nan,
                "junction_fraction_of_heater": junction_mean / heater_power
                if math.isfinite(junction_mean) and math.isfinite(heater_power) and abs(heater_power) > 0.0
                else math.nan,
                "latest_dominant_loss_section": latest.get("dominant_loss_section", ""),
                "latest_ambient_error_pct": finite_float(latest.get("ambient_error_pct")),
            }
        )
    payloads.sort(key=lambda row: row["case_order"])
    return payloads


def build_salt_enthalpy_rows(
    leg_rows: list[dict[str, str]],
    case_order: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in filter_salt_rows(leg_rows):
        grouped[(row["source_id"], row["span_name"])].append(row)

    payloads: list[dict[str, Any]] = []
    fit_exclusions: list[dict[str, Any]] = []
    for (source_id, span_name), rows in sorted(grouped.items(), key=lambda item: (case_order.get(item[0][0], 999), item[0][1])):
        mean_enthalpy = safe_mean(finite_float(row.get("enthalpy_change_w")) for row in rows)
        mean_wall = safe_mean(finite_float(row.get("wall_heat_total_w")) for row in rows)
        mean_residual = safe_mean(finite_float(row.get("enthalpy_minus_wall_heat_w")) for row in rows)
        residual_fraction = (
            abs(mean_residual) / abs(mean_wall)
            if math.isfinite(mean_residual) and math.isfinite(mean_wall) and abs(mean_wall) > 0.0
            else math.nan
        )
        fit_status, fit_reason = classify_enthalpy_closure(residual_fraction)
        payload = {
            "source_id": source_id,
            "case_label": rows[0]["case_label"],
            "case_order": case_order.get(source_id, 999),
            "span_name": span_name,
            "span_kind": rows[0]["span_kind"],
            "time_sample_count": len(rows),
            "mean_mdot_mean_abs_kg_s": safe_mean(finite_float(row.get("mdot_mean_abs_kg_s")) for row in rows),
            "mean_cp_bulk_j_kg_k": safe_mean(finite_float(row.get("cp_bulk_j_kg_k")) for row in rows),
            "mean_t_bulk_in_k": safe_mean(finite_float(row.get("t_bulk_in_k")) for row in rows),
            "mean_t_bulk_out_k": safe_mean(finite_float(row.get("t_bulk_out_k")) for row in rows),
            "mean_enthalpy_change_w": mean_enthalpy,
            "mean_wall_heat_total_w": mean_wall,
            "mean_enthalpy_minus_wall_heat_w": mean_residual,
            "mean_abs_enthalpy_minus_wall_heat_w": safe_mean(
                abs(finite_float(row.get("enthalpy_minus_wall_heat_w"))) for row in rows
            ),
            "enthalpy_residual_fraction_of_wall_heat": residual_fraction,
            "fit_status": fit_status,
            "fit_reason": fit_reason,
            "bulk_temperature_method": rows[0].get("bulk_temperature_method", ""),
        }
        payloads.append(payload)
        if fit_status != "candidate":
            fit_exclusions.append(
                {
                    "source_id": source_id,
                    "case_label": rows[0]["case_label"],
                    "asset_family": "enthalpy_balance",
                    "scope_name": span_name,
                    "fit_status": fit_status,
                    "fit_reason": fit_reason,
                }
            )
    return payloads, fit_exclusions


def build_salt_branch_rows(
    branch_rows: list[dict[str, str]],
    case_order: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payloads: list[dict[str, Any]] = []
    fit_exclusions: list[dict[str, Any]] = []
    for row in filter_salt_rows(branch_rows):
        fit_status, fit_reason = classify_branch_usability(row)
        payload = {
            **row,
            "case_order": case_order.get(row["source_id"], 999),
            "fit_status": fit_status,
            "fit_reason": fit_reason,
        }
        payloads.append(payload)
        if fit_status != "candidate":
            fit_exclusions.append(
                {
                    "source_id": row["source_id"],
                    "case_label": row["case_label"],
                    "asset_family": "branch_thermal",
                    "scope_name": row["branch_name"],
                    "fit_status": fit_status,
                    "fit_reason": fit_reason,
                }
            )
    payloads.sort(key=lambda row: (row["case_order"], row["branch_name"]))
    return payloads, fit_exclusions


def build_salt_boundary_rows(
    boundary_rows: list[dict[str, str]],
    representative_rows: list[dict[str, str]],
    case_order: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    summary_payloads: list[dict[str, Any]] = []
    for row in filter_salt_rows(boundary_rows):
        usable_fraction = finite_float(row.get("usable_fraction"))
        if usable_fraction >= 0.75:
            status = "context_ready"
            reason = "landmark_support_usable"
        else:
            status = "screening_only"
            reason = "landmark_support_marginal"
        summary_payloads.append(
            {
                **row,
                "case_order": case_order.get(row["source_id"], 999),
                "fit_status": status,
                "fit_reason": reason,
            }
        )
    summary_payloads.sort(key=lambda row: (row["case_order"], row["span_name"]))

    representative_payloads: list[dict[str, Any]] = []
    for row in filter_salt_rows(representative_rows):
        if row["source_id"] not in REPRESENTATIVE_SALT_CASES:
            continue
        representative_payloads.append(
            {
                **row,
                "case_order": case_order.get(row["source_id"], 999),
            }
        )
    representative_payloads.sort(key=lambda row: (row["case_order"], row["span_name"], finite_float(row.get("distance_over_dh"))))
    return summary_payloads, representative_payloads


def build_case_correlation_inputs(
    dashboard_rows: list[dict[str, str]],
    case_pressure_rows: list[dict[str, str]],
    heat_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    hydraulic_case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    pressure_lookup = {row["source_id"]: row for row in filter_salt_rows(case_pressure_rows)}
    heat_lookup = {row["source_id"]: row for row in heat_rows}
    hydraulic_lookup = {row["source_id"]: row for row in hydraulic_case_rows}
    branch_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rows:
        branch_grouped[row["source_id"]].append(row)

    payloads: list[dict[str, Any]] = []
    for row in filter_salt_rows(dashboard_rows):
        source_id = row["source_id"]
        pressure = pressure_lookup[source_id]
        heat = heat_lookup[source_id]
        hydraulic = hydraulic_lookup[source_id]
        branches = branch_grouped[source_id]
        payloads.append(
            {
                "source_id": source_id,
                "display_label": row["display_label"],
                "run_status": row.get("run_status", ""),
                "heater_power_w": finite_float(row.get("heater_power_W")),
                "cooling_power_w": finite_float(row.get("cooling_power_W")),
                "insulation_thickness_in": finite_float(row.get("three_d_outer_insulation_thickness_in")),
                "mdot_mean_abs_kg_s": finite_float(row.get("mdot_mean_abs_kg_s")),
                "probe_t_avg_k": finite_float(row.get("probe_T_avg_K")),
                "max_branch_temp_delta_k": finite_float(row.get("max_branch_temp_delta_k")),
                "heater_to_cooler_bulk_delta_k": finite_float(row.get("heater_to_cooler_bulk_delta_k")),
                "downcomer_to_upcomer_bulk_delta_k": finite_float(row.get("downcomer_to_upcomer_bulk_delta_k")),
                "loop_total_pressure_loss_hydro_pa": finite_float(pressure.get("loop_total_pressure_loss_hydro_pa")),
                "max_hydro_head_proxy_range_pa": finite_float(pressure.get("max_hydro_head_proxy_range_pa")),
                "straight_pipe_total_pressure_loss_hydro_pa": finite_float(
                    pressure.get("straight_pipe_total_pressure_loss_hydro_pa")
                ),
                "ambient_proxy_fraction_of_heater": finite_float(row.get("ambient_proxy_fraction_of_heater")),
                "cooling_removal_fraction_of_heater": finite_float(row.get("cooling_removal_fraction_of_heater")),
                "junction_loss_fraction_of_heater": finite_float(row.get("junction_loss_fraction_of_heater")),
                "net_heat_imbalance_fraction_of_heater": finite_float(row.get("net_heat_imbalance_fraction_of_heater")),
                "candidate_straight_section_count": int(hydraulic.get("candidate_section_count", 0)),
                "candidate_branch_count": sum(1 for branch in branches if branch["fit_status"] == "candidate"),
                "screening_branch_count": sum(1 for branch in branches if branch["fit_status"] == "screening_only"),
                "blocked_branch_count": sum(1 for branch in branches if branch["fit_status"] == "do_not_fit"),
                "cooling_branch_total_removal_mean_w": finite_float(heat.get("cooling_branch_total_removal_mean_w")),
                "ambient_proxy_mean_w": finite_float(heat.get("ambient_proxy_mean_w")),
                "junction_loss_mean_w": finite_float(heat.get("junction_loss_mean_w")),
            }
        )
    return payloads


def build_straight_section_correlation_inputs(
    hydraulic_rows: list[dict[str, Any]],
    enthalpy_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    enthalpy_lookup = {(row["source_id"], row["span_name"]): row for row in enthalpy_rows}
    boundary_lookup = {(row["source_id"], row["span_name"]): row for row in boundary_rows}
    case_lookup = {row["source_id"]: row for row in case_rows}
    branch_lookup = {(row["source_id"], row["branch_name"]): row for row in branch_rows}
    payloads: list[dict[str, Any]] = []
    for row in hydraulic_rows:
        source_id = row["source_id"]
        span_name = row["span_name"]
        enthalpy = enthalpy_lookup.get((source_id, span_name), {})
        boundary = boundary_lookup.get((source_id, span_name), {})
        branch = branch_lookup.get((source_id, span_name), {})
        case = case_lookup[source_id]
        payloads.append(
            {
                "source_id": source_id,
                "case_label": row["case_label"],
                "span_name": span_name,
                "span_kind": row["span_kind"],
                "fit_status": row["fit_status"],
                "fit_reason": row["fit_reason"],
                "net_section_role": row["net_section_role"],
                "section_length_m": finite_float(row.get("section_length_m")),
                "hydraulic_diameter_m": finite_float(row.get("mean_hydraulic_diameter_geom_m")),
                "rho_bulk_kg_m3": finite_float(row.get("mean_rho_bulk_kg_m3")),
                "bulk_velocity_m_s": finite_float(row.get("mean_bulk_velocity_m_s")),
                "mdot_mean_abs_kg_s": finite_float(row.get("mean_mdot_mean_abs_kg_s")),
                "dynamic_head_local_pa": finite_float(row.get("mean_dynamic_head_local_pa")),
                "pressure_loss_hydro_pa": finite_float(row.get("mean_pressure_loss_hydro_pa")),
                "apparent_darcy_f_local": finite_float(row.get("mean_apparent_darcy_f_local")),
                "apparent_darcy_f_loop_ref": finite_float(row.get("mean_apparent_darcy_f_loop_ref")),
                "direct_prgh_darcy": finite_float(row.get("mean_direct_prgh_darcy_existing")),
                "shear_darcy_core": finite_float(row.get("mean_shear_darcy_core")),
                "direct_to_shear_darcy_ratio": finite_float(row.get("direct_to_shear_darcy_ratio")),
                "pressure_loss_to_driving_head_ratio": (
                    finite_float(row.get("mean_pressure_loss_hydro_pa")) / finite_float(case.get("max_hydro_head_proxy_range_pa"))
                    if is_finite(case.get("max_hydro_head_proxy_range_pa")) and abs(finite_float(case.get("max_hydro_head_proxy_range_pa"))) > 0.0
                    else math.nan
                ),
                "max_branch_temp_delta_k": finite_float(case.get("max_branch_temp_delta_k")),
                "ambient_proxy_fraction_of_heater": finite_float(case.get("ambient_proxy_fraction_of_heater")),
                "enthalpy_residual_fraction_of_wall_heat": finite_float(
                    enthalpy.get("enthalpy_residual_fraction_of_wall_heat")
                ),
                "boundary_delta99_u_over_dh": finite_float(boundary.get("mean_delta99_u_over_dh")),
                "boundary_delta99_t_over_dh": finite_float(boundary.get("mean_delta99_t_over_dh")),
                "boundary_delta99_t_over_delta99_u": finite_float(boundary.get("mean_delta99_t_over_delta99_u")),
                "branch_fit_status": branch.get("fit_status", ""),
            }
        )
    return payloads


def build_feature_correlation_inputs(
    feature_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    case_lookup = {row["source_id"]: row for row in case_rows}
    payloads: list[dict[str, Any]] = []
    for row in feature_rows:
        case = case_lookup[row["source_id"]]
        payloads.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "feature_name": row["feature_name"],
                "feature_kind": row["feature_kind"],
                "fit_status": row["fit_status"],
                "fit_reason": row["fit_reason"],
                "adjacent_major_spans": row["adjacent_major_spans"],
                "reference_length_m": finite_float(row.get("reference_length_m")),
                "mean_feature_loss_prgh_pa": finite_float(row.get("mean_feature_loss_prgh_pa")),
                "mean_feature_residual_dp_pa": finite_float(row.get("mean_feature_residual_dp_pa")),
                "mean_dynamic_head_reference_pa": finite_float(row.get("mean_dynamic_head_reference_pa")),
                "mean_keff_reference": finite_float(row.get("mean_keff_reference")),
                "max_branch_temp_delta_k": finite_float(case.get("max_branch_temp_delta_k")),
                "mdot_mean_abs_kg_s": finite_float(case.get("mdot_mean_abs_kg_s")),
                "ambient_proxy_fraction_of_heater": finite_float(case.get("ambient_proxy_fraction_of_heater")),
            }
        )
    return payloads


def render_hydraulic_agreement_figure(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    cases = sorted({row["source_id"] for row in rows}, key=lambda item: min(int(row["case_order"]) for row in rows if row["source_id"] == item))
    spans = sorted({row["span_name"] for row in rows})
    ratio_matrix = np.full((len(cases), len(spans)), np.nan, dtype=float)
    f_matrix = np.full((len(cases), len(spans)), np.nan, dtype=float)
    for row in rows:
        ci = cases.index(row["source_id"])
        si = spans.index(row["span_name"])
        ratio_matrix[ci, si] = finite_float(row.get("direct_to_shear_darcy_ratio"))
        f_matrix[ci, si] = finite_float(row.get("mean_apparent_darcy_f_local"))

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), constrained_layout=True)
    im0 = axes[0].imshow(np.log10(ratio_matrix), aspect="auto", cmap="coolwarm")
    axes[0].set_title("Salt Straight-Section Direct/Shear Darcy Ratio (log10)")
    axes[0].set_xticks(range(len(spans)))
    axes[0].set_xticklabels(spans, rotation=45, ha="right")
    axes[0].set_yticks(range(len(cases)))
    axes[0].set_yticklabels(cases)
    fig.colorbar(im0, ax=axes[0], label="log10(direct/shear)")

    im1 = axes[1].imshow(f_matrix, aspect="auto", cmap="viridis")
    axes[1].set_title("Salt Straight-Section Signed Apparent Darcy Factor")
    axes[1].set_xticks(range(len(spans)))
    axes[1].set_xticklabels(spans, rotation=45, ha="right")
    axes[1].set_yticks(range(len(cases)))
    axes[1].set_yticklabels(cases)
    fig.colorbar(im1, ax=axes[1], label="f_D,app")
    return save_matplotlib_figure(fig, output_dir, "salt_hydraulic_agreement")


def render_branch_usability_figure(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    cases = sorted({row["source_id"] for row in rows}, key=lambda item: min(int(row["case_order"]) for row in rows if row["source_id"] == item))
    branches = sorted({row["branch_name"] for row in rows})
    mapping = {"do_not_fit": 0.0, "screening_only": 1.0, "candidate": 2.0}
    matrix = np.full((len(cases), len(branches)), np.nan, dtype=float)
    for row in rows:
        ci = cases.index(row["source_id"])
        bi = branches.index(row["branch_name"])
        matrix[ci, bi] = mapping[row["fit_status"]]
    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    cmap = plt.get_cmap("RdYlGn", 3)
    im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0.0, vmax=2.0)
    ax.set_title("Salt Branch Thermal Usability Mask")
    ax.set_xticks(range(len(branches)))
    ax.set_xticklabels(branches, rotation=45, ha="right")
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels(cases)
    colorbar = fig.colorbar(im, ax=ax, ticks=[0.0, 1.0, 2.0])
    colorbar.ax.set_yticklabels(["do_not_fit", "screening_only", "candidate"])
    return save_matplotlib_figure(fig, output_dir, "salt_branch_usability")


def render_heat_partition_figure(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    labels = [row["case_label"] for row in rows]
    x = np.arange(len(rows))
    width = 0.18
    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    ax.bar(x - 1.5 * width, [finite_float(row["cooling_total_fraction_of_heater"]) for row in rows], width, label="cooling total / heater")
    ax.bar(x - 0.5 * width, [finite_float(row["ambient_proxy_fraction_of_heater"]) for row in rows], width, label="ambient proxy / heater")
    ax.bar(x + 0.5 * width, [finite_float(row["ambient_noncooling_fraction_of_heater"]) for row in rows], width, label="ambient noncooling / heater")
    ax.bar(x + 1.5 * width, [finite_float(row["junction_fraction_of_heater"]) for row in rows], width, label="junction / heater")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("fraction of heater power")
    ax.set_title("Salt Heat-Loss Partition Indicators")
    ax.legend(loc="upper right", fontsize=8)
    return save_matplotlib_figure(fig, output_dir, "salt_heat_loss_partition")


def render_boundary_ratio_figure(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    spans = sorted({row["span_name"] for row in rows})
    by_span: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_span[row["span_name"]].append(row)
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), constrained_layout=True)
    axes[0].boxplot(
        [[finite_float(row["mean_delta99_u_over_dh"]) for row in by_span[span]] for span in spans],
        labels=spans,
        vert=True,
    )
    axes[0].set_title("Salt Hydraulic Boundary Thickness Proxy")
    axes[0].set_ylabel("mean delta99_u / D_h")
    axes[0].tick_params(axis="x", rotation=45)

    axes[1].boxplot(
        [[finite_float(row["mean_delta99_t_over_delta99_u"]) for row in by_span[span]] for span in spans],
        labels=spans,
        vert=True,
    )
    axes[1].set_title("Salt Thermal/Hydraulic Boundary Thickness Ratio")
    axes[1].set_ylabel("mean delta99_T / delta99_u")
    axes[1].tick_params(axis="x", rotation=45)
    return save_matplotlib_figure(fig, output_dir, "salt_boundary_layer_ratios")


def render_representative_profile_figure(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    payload = [row for row in rows if row["source_id"] == "val_salt_test_2_coarse_mesh_laminar"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    span_names = sorted({row["span_name"] for row in payload})
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(span_names), 1)))
    for color, span_name in zip(colors, span_names):
        span_rows = [row for row in payload if row["span_name"] == span_name]
        x = [finite_float(row["distance_over_dh"]) for row in span_rows]
        axes[0].plot(x, [finite_float(row["u_over_ucore"]) for row in span_rows], marker="o", ms=2.5, lw=1.0, color=color, label=span_name)
        axes[1].plot(x, [finite_float(row["theta_norm"]) for row in span_rows], marker="o", ms=2.5, lw=1.0, color=color, label=span_name)
    axes[0].set_title("Salt 2 Val Landmark Velocity Profiles")
    axes[0].set_xlabel("distance / D_h")
    axes[0].set_ylabel("u / u_core")
    axes[1].set_title("Salt 2 Val Landmark Thermal Profiles")
    axes[1].set_xlabel("distance / D_h")
    axes[1].set_ylabel("theta_norm")
    axes[1].legend(loc="best", fontsize=7)
    return save_matplotlib_figure(fig, output_dir, "salt_representative_boundary_profiles")


def write_math_companion(output_dir: Path) -> None:
    text = """# Salt Closure / Correlation Package Math Companion

Generated: `2026-06-18`

This note documents the derived quantities used by
`tools/analyze/build_ethan_salt_closure_correlation_package.py`.

## Straight-section hydraulic screening

The package reuses the additive June 17 sectionwise pressure closure:

`Delta p_hydro = Delta p_wall + integral rho g dot t_hat ds`

and retains:

- signed apparent Darcy factor from the hydro-corrected section loss
- direct wall-registered `p_rgh` Darcy proxy
- shear-based Darcy proxy from the established streamwise package

The Salt straight-section fit status is:

- `candidate` when the section is net dissipative (`Delta p_hydro > 0`),
  thermal support fraction is at least `0.75`, direct and shear friction
  proxies are both positive, and `0.5 <= direct/shear <= 2.0`
- `screening_only` when the section is buoyancy-aided, support-limited, or the
  direct/shear ratio is materially mismatched
- `do_not_fit` when the direct or shear proxy is nonpositive or missing

These statuses are correlation-fit gates, not claims that the underlying raw
reduction is invalid.

## Feature K_eff

Feature `K_eff` is inherited from the additive June 17 package:

`K_eff = Delta p_feature,residual / q_ref`

where the residual closure is still based on the stored `p_rgh` feature path.
The current package treats positive residual `K_eff` as a fit candidate and
negative `K_eff` as screening-only because it likely reflects subtraction and
support ambiguity rather than a physically useful minor-loss coefficient.

## Branch thermal usability

The branch usability mask follows the scrutiny thresholds:

- `candidate` when usable fraction `>= 0.90`, warning fraction `<= 0.10`, and
  minimum resolved `|T_bulk - T_wall| >= 0.50 K`
- `do_not_fit` when usable fraction `< 0.75`, warning fraction `> 0.25`, or
  minimum resolved `|T_bulk - T_wall| < 0.25 K`
- `screening_only` otherwise

These thresholds determine whether an effective thermal ratio is suitable for a
correlation input table. They do not claim intrinsic local HTC closure quality.

## Enthalpy residual

For each Salt span, the package reuses:

`Delta H_leg = mdot cp (T_out - T_in)`

`Q_wall,leg = integral q'_wall ds`

and reports the normalized residual

`r_H = |Delta H_leg - Q_wall,leg| / |Q_wall,leg|`

The current status thresholds are:

- `candidate` when `r_H <= 0.15`
- `screening_only` when `0.15 < r_H <= 0.30`
- `do_not_fit` when `r_H > 0.30`

## Heat-loss partition indicators

The package reports case-level Salt indicators using the June 9 heat audit:

- ambient proxy mean
- noncooling ambient proxy mean
- cooling branch total removal mean
- cooling branch excess mean
- junction loss mean

These are not a full internal-convection / wall-conduction / external-radiation
decomposition. They are screening indicators for how much heater power leaves
through intended versus parasitic channels.
"""
    (output_dir / "MATH_COMPANION.md").write_text(text, encoding="utf-8")


def write_readme(
    output_dir: Path,
    case_rows: list[dict[str, Any]],
    hydraulic_rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    figure_paths: dict[str, Any],
) -> None:
    text = f"""# Ethan Salt Closure / Correlation Package

Generated: `2026-06-18`

This package is a Salt-only additive closure-first analysis layer built from
the existing June 9, June 15, and June 17 Ethan artifacts. It does not reopen
the active shared extraction or package-builder paths.

## What this package adds

- Salt straight-section hydraulic screening with correlation-fit gates
- Salt feature `K_eff` screening tables
- Salt heat-loss partition indicators from the June 9 audit
- Salt branch thermal usability masks for effective HTC / UA / thermal-resistance use
- Salt legwise enthalpy-balance summary tables
- Salt-only straight-section, feature, and case-level correlation-input tables
- Salt boundary-layer context summaries and the currently available representative Salt landmark profile figure

## Primary interpretation boundaries

1. Straight-section apparent Darcy factors are signed net section closures.
   Negative values are retained as buoyancy-aided or net-gain sections, not
   mislabeled as positive friction losses.
2. Feature `K_eff` still inherits the June 17 residual `p_rgh` feature path;
   this package does not pretend that feature hydro integrals are now fully resolved.
3. Branch thermal fit status is a support mask for effective ratios, not a claim
   that the underlying branch physics are absent when a row is blocked.
4. The heat-loss partition remains case-level and audit-style. It is not yet a
   resolved decomposition into internal convection, wall conduction, and external
   radiation/convection.
5. Representative boundary-layer context is currently limited to the preserved
   Salt 2 landmark profile set already available in the additive June 17 package.

## Main artifacts

- `salt_hydraulic_section_closure.csv`
- `salt_hydraulic_case_summary.csv`
- `salt_feature_keff.csv`
- `salt_heat_loss_partition_case.csv`
- `salt_leg_enthalpy_summary.csv`
- `salt_branch_usability.csv`
- `salt_boundary_layer_summary.csv`
- `salt_representative_boundary_profiles.csv`
- `salt_case_correlation_inputs.csv`
- `salt_straight_section_correlation_inputs.csv`
- `salt_feature_correlation_inputs.csv`
- `salt_fit_exclusion_log.csv`
- `MATH_COMPANION.md`

## Summary counts

- Salt cases covered: `{len(case_rows)}`
- Straight-section rows: `{len(hydraulic_rows)}`
- Feature rows: `{len(feature_rows)}`
- Branch rows: `{len(branch_rows)}`
- Straight-section fit candidates: `{sum(1 for row in hydraulic_rows if row['fit_status'] == 'candidate')}`
- Branch thermal fit candidates: `{sum(1 for row in branch_rows if row['fit_status'] == 'candidate')}`

## Figures

- hydraulic agreement: `{figure_paths['hydraulic_agreement']['png']}`
- branch usability: `{figure_paths['branch_usability']['png']}`
- heat-loss partition: `{figure_paths['heat_partition']['png']}`
- boundary-layer ratios: `{figure_paths['boundary_ratios']['png']}`
- representative Salt boundary profile: `{figure_paths['representative_profiles']['png']}`

## Summary JSON

Machine-readable package summary is in `summary.json`.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    source_ids = set(args.source_ids or [])

    pressure_section_rows = load_csv_rows(PRESSURE_PACKAGE_DIR / "pressure_closure_by_section.csv")
    pressure_case_rows = load_csv_rows(PRESSURE_PACKAGE_DIR / "pressure_closure_by_case.csv")
    feature_rows = load_csv_rows(PRESSURE_PACKAGE_DIR / "feature_keff_by_case.csv")
    enthalpy_rows = load_csv_rows(PRESSURE_PACKAGE_DIR / "enthalpy_balance_by_leg.csv")
    boundary_rows = load_csv_rows(PRESSURE_PACKAGE_DIR / "boundary_layer_summary_by_section.csv")
    representative_rows = load_csv_rows(PRESSURE_PACKAGE_DIR / "representative_boundary_layer_profiles.csv")
    dashboard_rows = load_csv_rows(DASHBOARD_PACKAGE_DIR / "salt_dashboard.csv")
    branch_rows = load_csv_rows(TRANSPORT_PACKAGE_DIR / "field_transport_branch_thermal_comparison.csv")
    heat_window_rows = load_csv_rows(HEAT_AUDIT_DIR / "heat_window_summary.csv")
    heat_latest_rows = load_csv_rows(HEAT_AUDIT_DIR / "latest_heat_partition.csv")

    pressure_section_rows = filter_source_rows(pressure_section_rows, source_ids or None)
    pressure_case_rows = filter_source_rows(pressure_case_rows, source_ids or None)
    feature_rows = filter_source_rows(feature_rows, source_ids or None)
    enthalpy_rows = filter_source_rows(enthalpy_rows, source_ids or None)
    boundary_rows = filter_source_rows(boundary_rows, source_ids or None)
    representative_rows = filter_source_rows(representative_rows, source_ids or None)
    dashboard_rows = filter_source_rows(dashboard_rows, source_ids or None)
    branch_rows = filter_source_rows(branch_rows, source_ids or None)
    heat_window_rows = filter_source_rows(heat_window_rows, source_ids or None)
    heat_latest_rows = filter_source_rows(heat_latest_rows, source_ids or None)

    case_order, _case_labels = case_order_lookup(dashboard_rows)

    hydraulic_rows, hydraulic_case_rows, hydraulic_exclusions = build_salt_hydraulic_sections(pressure_section_rows, case_order)
    feature_payloads, feature_exclusions = build_salt_feature_rows(feature_rows, case_order)
    heat_payloads = build_salt_heat_partition_rows(heat_window_rows, heat_latest_rows, dashboard_rows, case_order)
    enthalpy_payloads, enthalpy_exclusions = build_salt_enthalpy_rows(enthalpy_rows, case_order)
    branch_payloads, branch_exclusions = build_salt_branch_rows(branch_rows, case_order)
    boundary_payloads, representative_payloads = build_salt_boundary_rows(boundary_rows, representative_rows, case_order)
    case_correlation_inputs = build_case_correlation_inputs(
        dashboard_rows,
        pressure_case_rows,
        heat_payloads,
        branch_payloads,
        hydraulic_case_rows,
    )
    straight_section_inputs = build_straight_section_correlation_inputs(
        hydraulic_rows,
        enthalpy_payloads,
        boundary_payloads,
        case_correlation_inputs,
        branch_payloads,
    )
    feature_inputs = build_feature_correlation_inputs(feature_payloads, case_correlation_inputs)
    fit_exclusion_log = hydraulic_exclusions + feature_exclusions + enthalpy_exclusions + branch_exclusions

    csv_dump(output_dir / "salt_hydraulic_section_closure.csv", list(hydraulic_rows[0].keys()), hydraulic_rows)
    csv_dump(output_dir / "salt_hydraulic_case_summary.csv", list(hydraulic_case_rows[0].keys()), hydraulic_case_rows)
    csv_dump(output_dir / "salt_feature_keff.csv", list(feature_payloads[0].keys()), feature_payloads)
    csv_dump(output_dir / "salt_heat_loss_partition_case.csv", list(heat_payloads[0].keys()), heat_payloads)
    csv_dump(output_dir / "salt_leg_enthalpy_summary.csv", list(enthalpy_payloads[0].keys()), enthalpy_payloads)
    csv_dump(output_dir / "salt_branch_usability.csv", list(branch_payloads[0].keys()), branch_payloads)
    csv_dump(output_dir / "salt_boundary_layer_summary.csv", list(boundary_payloads[0].keys()), boundary_payloads)
    csv_dump(
        output_dir / "salt_representative_boundary_profiles.csv",
        list(representative_payloads[0].keys()) if representative_payloads else ["source_id"],
        representative_payloads,
    )
    csv_dump(output_dir / "salt_case_correlation_inputs.csv", list(case_correlation_inputs[0].keys()), case_correlation_inputs)
    csv_dump(
        output_dir / "salt_straight_section_correlation_inputs.csv",
        list(straight_section_inputs[0].keys()),
        straight_section_inputs,
    )
    csv_dump(output_dir / "salt_feature_correlation_inputs.csv", list(feature_inputs[0].keys()), feature_inputs)
    csv_dump(output_dir / "salt_fit_exclusion_log.csv", list(fit_exclusion_log[0].keys()), fit_exclusion_log)

    figure_paths = {
        "hydraulic_agreement": render_hydraulic_agreement_figure(hydraulic_rows, output_dir),
        "branch_usability": render_branch_usability_figure(branch_payloads, output_dir),
        "heat_partition": render_heat_partition_figure(heat_payloads, output_dir),
        "boundary_ratios": render_boundary_ratio_figure(boundary_payloads, output_dir),
        "representative_profiles": render_representative_profile_figure(representative_payloads, output_dir),
    }

    write_math_companion(output_dir)

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(case_correlation_inputs),
        "straight_section_row_count": len(hydraulic_rows),
        "feature_row_count": len(feature_payloads),
        "branch_row_count": len(branch_payloads),
        "enthalpy_row_count": len(enthalpy_payloads),
        "boundary_summary_row_count": len(boundary_payloads),
        "representative_profile_row_count": len(representative_payloads),
        "straight_section_fit_candidates": sum(1 for row in hydraulic_rows if row["fit_status"] == "candidate"),
        "feature_fit_candidates": sum(1 for row in feature_payloads if row["fit_status"] == "candidate"),
        "branch_fit_candidates": sum(1 for row in branch_payloads if row["fit_status"] == "candidate"),
        "enthalpy_fit_candidates": sum(1 for row in enthalpy_payloads if row["fit_status"] == "candidate"),
        "figure_paths": figure_paths,
        "limitations": [
            "Feature K_eff remains tied to the June 17 residual p_rgh feature path rather than a dedicated feature hydro integral.",
            "Heat-loss partition remains case-level and audit-style; it is not yet a resolved internal-convection / wall-conduction / external-radiation decomposition.",
            "Representative boundary-layer context is limited to the currently preserved Salt 2 landmark profile set already available in the additive June 17 package.",
        ],
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(
        output_dir,
        case_correlation_inputs,
        hydraulic_rows,
        feature_payloads,
        branch_payloads,
        summary,
        figure_paths,
    )


if __name__ == "__main__":
    main()
