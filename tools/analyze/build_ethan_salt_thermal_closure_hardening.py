#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp, json_dump
from tools.analyze.ethan_salt_hardening_common import (
    DIRECT_THERMAL_BRANCHES,
    FIELD_TRANSPORT_DIR,
    MODEL_DEPENDENCY_V1_DIR,
    NONDIM_DIR,
    PRESSURE_DIR,
    SALT_CHECKPOINT_DIR,
    THERMAL_BLOCKED_BRANCHES,
    THERMAL_DERIVED_BRANCHES,
    CaseContext,
    build_dimensionless_bundle,
    csv_dump_rows,
    finite_float,
    load_case_contexts,
    load_csv_rows,
    normalized_residual,
    require_columns,
    safe_mean,
    safe_sum,
    sign_token,
)

DEFAULT_OUTPUT_DIR = Path("reports/2026-06-19_ethan_salt_thermal_closure_hardening")
SUPPORT_FRACTION_MIN = 0.90
DELTA_T_MIN_K = 0.25
RESIDUAL_FRACTION_MAX = 0.30
GROUP_RECONSTRUCTION_MAX = 0.05
PASS_TIME_FRACTION_MIN = 0.75


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an additive Salt-only thermal closure hardening package from the "
            "preserved case-analysis and June 17/18 additive artifacts."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more Salt source IDs.",
    )
    parser.add_argument(
        "--property-convention",
        default="branch_bulk",
        choices=("branch_bulk", "case_probe"),
        help="Temperature convention used for derived dimensionless groups.",
    )
    return parser.parse_args()


def load_branch_gate_rows(source_ids: set[str] | None = None) -> list[dict[str, str]]:
    rows = load_csv_rows(SALT_CHECKPOINT_DIR / "phase3_branch_trust_gate" / "branch_promotion_gate.csv")
    require_columns(
        rows,
        [
            "source_id",
            "branch_name",
            "branch_type",
            "component_spans",
            "case_order",
            "fit_status",
            "fit_reason",
            "usable_fraction",
        ],
        "branch_promotion_gate.csv",
    )
    if source_ids:
        rows = [row for row in rows if row["source_id"] in source_ids]
    return rows


def classify_role_label(q_intended_transfer_w: float, q_parasitic_loss_w: float) -> str:
    intended_mag = abs(q_intended_transfer_w) if math.isfinite(q_intended_transfer_w) else 0.0
    parasitic_mag = abs(q_parasitic_loss_w) if math.isfinite(q_parasitic_loss_w) else 0.0
    if q_intended_transfer_w > 0.0 and intended_mag >= parasitic_mag:
        return "intended_heating_dominant"
    if q_intended_transfer_w < 0.0 and intended_mag >= parasitic_mag:
        return "intended_cooling_dominant"
    if q_parasitic_loss_w < 0.0 and parasitic_mag > intended_mag:
        return "parasitic_cooling_dominant"
    if q_parasitic_loss_w > 0.0 and parasitic_mag > intended_mag:
        return "parasitic_gain_dominant"
    return "mixed_role"


def classify_time_row(
    branch_name: str,
    branch_fit_status: str,
    support_fraction: float,
    delta_t_wall_bulk_mean_k: float,
    residual_fraction: float,
    thermal_direction_consistent: bool,
    grouped_reconstruction_fraction: float,
) -> tuple[str, str]:
    if branch_name in THERMAL_BLOCKED_BRANCHES:
        return "excluded", "right_leg_blocked_by_policy"
    if branch_name in THERMAL_DERIVED_BRANCHES:
        return "sensitivity_only", "derived_branch_overlap_double_counting"
    if branch_fit_status != "candidate":
        return "sensitivity_only", "branch_support_screened_not_candidate"
    if not math.isfinite(support_fraction) or support_fraction < SUPPORT_FRACTION_MIN:
        return "sensitivity_only", "support_fraction_below_candidate_gate"
    if not math.isfinite(delta_t_wall_bulk_mean_k) or delta_t_wall_bulk_mean_k < DELTA_T_MIN_K:
        return "sensitivity_only", "weak_twall_minus_tbulk_support"
    if not math.isfinite(residual_fraction) or residual_fraction > RESIDUAL_FRACTION_MAX:
        return "sensitivity_only", "enthalpy_wall_heat_balance_loose"
    if not thermal_direction_consistent:
        return "sensitivity_only", "enthalpy_wall_direction_inconsistent"
    if not math.isfinite(grouped_reconstruction_fraction) or grouped_reconstruction_fraction > GROUP_RECONSTRUCTION_MAX:
        return "sensitivity_only", "grouped_heat_reconstruction_mismatch"
    return "candidate_time", "closure_supported"


def classify_case_row(row: dict[str, Any]) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    branch_name = str(row["branch_name"])
    if branch_name in THERMAL_BLOCKED_BRANCHES:
        reasons.append("right_leg_blocked_by_policy")
    if branch_name in THERMAL_DERIVED_BRANCHES:
        reasons.append("derived_branch_overlap_double_counting")
    if row["branch_fit_status"] != "candidate":
        reasons.append(str(row["branch_fit_reason"]))
    if not math.isfinite(finite_float(row.get("mean_support_fraction"))) or finite_float(row.get("mean_support_fraction")) < SUPPORT_FRACTION_MIN:
        reasons.append("support_fraction_below_candidate_gate")
    if not math.isfinite(finite_float(row.get("min_delta_t_wall_bulk_mean_k"))) or finite_float(row.get("min_delta_t_wall_bulk_mean_k")) < DELTA_T_MIN_K:
        reasons.append("weak_twall_minus_tbulk_support")
    if not math.isfinite(finite_float(row.get("mean_residual_fraction_of_wall_heat"))) or finite_float(row.get("mean_residual_fraction_of_wall_heat")) > RESIDUAL_FRACTION_MAX:
        reasons.append("enthalpy_wall_heat_balance_loose")
    if not math.isfinite(finite_float(row.get("max_residual_fraction_of_wall_heat"))) or finite_float(row.get("max_residual_fraction_of_wall_heat")) > 0.50:
        reasons.append("enthalpy_wall_heat_balance_loose")
    if not math.isfinite(finite_float(row.get("pass_time_fraction"))) or finite_float(row.get("pass_time_fraction")) < PASS_TIME_FRACTION_MIN:
        reasons.append("closure_pass_fraction_too_low")
    if not bool(row.get("direction_consistent_all_times")):
        reasons.append("enthalpy_wall_direction_inconsistent")
    if not math.isfinite(finite_float(row.get("mean_grouped_reconstruction_fraction"))) or finite_float(row.get("mean_grouped_reconstruction_fraction")) > GROUP_RECONSTRUCTION_MAX:
        reasons.append("grouped_heat_reconstruction_mismatch")
    if not math.isfinite(finite_float(row.get("mean_nu_effective"))) or finite_float(row.get("mean_nu_effective")) <= 0.0:
        reasons.append("nonpositive_effective_nusselt")
    if reasons:
        if branch_name in THERMAL_DERIVED_BRANCHES:
            return "sensitivity_only", "derived_branch_overlap_double_counting", reasons
        if branch_name in THERMAL_BLOCKED_BRANCHES:
            return "excluded", "right_leg_blocked_by_policy", reasons
        if row["branch_fit_status"] == "candidate":
            return "sensitivity_only", reasons[0], reasons
        return "excluded", reasons[0], reasons
    return "fit_used", "closure_supported", []


def aggregate_grouped_heat(case_root: Path) -> dict[tuple[str, str, str], dict[str, float]]:
    rows = load_csv_rows(case_root / "azimuthal_wall_transport_summary.csv")
    require_columns(rows, ["source_id", "time_s", "span_name", "thermal_role_group", "total_wall_heat_w"], f"{case_root.name}/azimuthal_wall_transport_summary.csv")
    grouped: dict[tuple[str, str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in rows:
        key = (row["source_id"], row["span_name"], row["time_s"])
        q_value = finite_float(row.get("total_wall_heat_w"))
        if not math.isfinite(q_value):
            continue
        group_name = row["thermal_role_group"]
        grouped[key]["grouped_total_wall_heat_w"] += q_value
        grouped[key][f"group_{group_name}_w"] += q_value
        if group_name == "intended_transfer":
            if q_value >= 0.0:
                grouped[key]["q_intended_transfer_w"] += q_value
                grouped[key]["q_sink_or_cooling_w"] += 0.0
            else:
                grouped[key]["q_intended_transfer_w"] += q_value
                grouped[key]["q_sink_or_cooling_w"] += q_value
        elif group_name == "parasitic_loss":
            grouped[key]["q_external_or_loss_w"] += q_value
    return grouped


def aggregate_major_support(case_root: Path) -> dict[tuple[str, str, str], dict[str, float]]:
    rows = load_csv_rows(case_root / "major_loss_cumulative_timeseries.csv")
    require_columns(rows, ["source_id", "time_s", "span_name", "thermal_support_status", "bulk_minus_wall_temp_k", "bulk_velocity_m_s", "hydraulic_diameter_geom_m", "bulk_temp_fluid_area_avg_k"], f"{case_root.name}/major_loss_cumulative_timeseries.csv")
    grouped: dict[tuple[str, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    counts: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        key = (row["source_id"], row["span_name"], row["time_s"])
        counts[key]["total"] += 1
        if row.get("thermal_support_status") == "usable":
            counts[key]["usable"] += 1
        delta_t = abs(finite_float(row.get("bulk_minus_wall_temp_k")))
        if math.isfinite(delta_t):
            grouped[key]["delta_t_wall_bulk_k"].append(delta_t)
        velocity = finite_float(row.get("bulk_velocity_m_s"))
        if math.isfinite(velocity):
            grouped[key]["bulk_velocity_m_s"].append(velocity)
        dh_m = finite_float(row.get("hydraulic_diameter_geom_m"))
        if math.isfinite(dh_m):
            grouped[key]["hydraulic_diameter_geom_m"].append(dh_m)
        bulk_temp_k = finite_float(row.get("bulk_temp_fluid_area_avg_k"))
        if math.isfinite(bulk_temp_k):
            grouped[key]["bulk_temp_k"].append(bulk_temp_k)
    payload: dict[tuple[str, str, str], dict[str, float]] = {}
    for key, values in grouped.items():
        total = counts[key]["total"]
        usable = counts[key]["usable"]
        payload[key] = {
            "support_fraction": usable / max(total, 1),
            "delta_t_wall_bulk_mean_k": safe_mean(values["delta_t_wall_bulk_k"]),
            "delta_t_wall_bulk_min_k": min(values["delta_t_wall_bulk_k"], default=math.nan),
            "bulk_velocity_m_s": safe_mean(values["bulk_velocity_m_s"]),
            "hydraulic_diameter_geom_m": safe_mean(values["hydraulic_diameter_geom_m"]),
            "bulk_temp_k": safe_mean(values["bulk_temp_k"]),
        }
    return payload


def build_thermal_timeseries_rows(
    contexts: dict[str, CaseContext],
    branch_gate_rows: list[dict[str, str]],
    property_convention: str,
) -> list[dict[str, Any]]:
    enthalpy_rows = load_csv_rows(PRESSURE_DIR / "enthalpy_balance_by_leg.csv")
    section_rows = load_csv_rows(PRESSURE_DIR / "fluid_side_htc_nu_section_summary.csv")
    correction_rows = load_csv_rows(PRESSURE_DIR / "bulk_vs_centerline_temperature_correction.csv")
    require_columns(enthalpy_rows, ["source_id", "time_s", "span_name", "enthalpy_change_w"], "enthalpy_balance_by_leg.csv")
    require_columns(section_rows, ["source_id", "time_s", "span_name", "wall_heat_integral_w", "delta_t_wall_minus_bulk_integral_k_m2", "wall_area_total_m2"], "fluid_side_htc_nu_section_summary.csv")
    require_columns(correction_rows, ["source_id", "time_s", "span_name", "bulk_minus_centerline_temp_k"], "bulk_vs_centerline_temperature_correction.csv")
    enthalpy_lookup = {(row["source_id"], row["span_name"], row["time_s"]): row for row in enthalpy_rows if row["source_id"] in contexts}
    section_lookup = {(row["source_id"], row["span_name"], row["time_s"]): row for row in section_rows if row["source_id"] in contexts}
    correction_group: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in correction_rows:
        if row["source_id"] not in contexts:
            continue
        value = finite_float(row.get("bulk_minus_centerline_temp_k"))
        if math.isfinite(value):
            correction_group[(row["source_id"], row["span_name"], row["time_s"])].append(value)

    rows_out: list[dict[str, Any]] = []
    grouped_heat_by_case: dict[str, dict[tuple[str, str, str], dict[str, float]]] = {}
    major_support_by_case: dict[str, dict[tuple[str, str, str], dict[str, float]]] = {}
    for branch_row in sorted(branch_gate_rows, key=lambda item: (int(item["case_order"]), item["branch_name"])):
        source_id = branch_row["source_id"]
        context = contexts[source_id]
        if source_id not in grouped_heat_by_case:
            case_root = context.package_root
            grouped_heat_by_case[source_id] = aggregate_grouped_heat(case_root)
            major_support_by_case[source_id] = aggregate_major_support(case_root)
        grouped_heat_lookup = grouped_heat_by_case[source_id]
        major_support_lookup = major_support_by_case[source_id]
        component_spans = [part.strip() for part in branch_row["component_spans"].split(",") if part.strip()]
        candidate_times = sorted(
            {
                row_key[2]
                for row_key in section_lookup
                if row_key[0] == source_id and row_key[1] in component_spans
            },
            key=float,
        )
        for time_s in candidate_times:
            enthalpy_change_w = safe_sum(
                finite_float(enthalpy_lookup.get((source_id, span_name, time_s), {}).get("enthalpy_change_w"))
                for span_name in component_spans
            )
            wall_heat_total_w = safe_sum(
                finite_float(section_lookup.get((source_id, span_name, time_s), {}).get("wall_heat_integral_w"))
                for span_name in component_spans
            )
            wall_area_total_m2 = safe_sum(
                finite_float(section_lookup.get((source_id, span_name, time_s), {}).get("wall_area_total_m2"))
                for span_name in component_spans
            )
            delta_t_integral_k_m2 = safe_sum(
                finite_float(section_lookup.get((source_id, span_name, time_s), {}).get("delta_t_wall_minus_bulk_integral_k_m2"))
                for span_name in component_spans
            )
            grouped_total_w = safe_sum(
                finite_float(grouped_heat_lookup.get((source_id, span_name, time_s), {}).get("grouped_total_wall_heat_w"))
                for span_name in component_spans
            )
            q_intended_transfer_w = safe_sum(
                finite_float(grouped_heat_lookup.get((source_id, span_name, time_s), {}).get("q_intended_transfer_w"))
                for span_name in component_spans
            )
            q_external_or_loss_w = safe_sum(
                finite_float(grouped_heat_lookup.get((source_id, span_name, time_s), {}).get("q_external_or_loss_w"))
                for span_name in component_spans
            )
            q_sink_or_cooling_w = safe_sum(
                finite_float(grouped_heat_lookup.get((source_id, span_name, time_s), {}).get("q_sink_or_cooling_w"))
                for span_name in component_spans
            )
            q_junction_or_unresolved_w = wall_heat_total_w - grouped_total_w if math.isfinite(wall_heat_total_w) and math.isfinite(grouped_total_w) else math.nan
            q_residual_w = enthalpy_change_w - wall_heat_total_w if math.isfinite(enthalpy_change_w) and math.isfinite(wall_heat_total_w) else math.nan
            residual_fraction = normalized_residual(q_residual_w, wall_heat_total_w)
            grouped_reconstruction_fraction = normalized_residual(q_junction_or_unresolved_w, wall_heat_total_w)

            support_fraction = safe_mean(
                finite_float(major_support_lookup.get((source_id, span_name, time_s), {}).get("support_fraction"))
                for span_name in component_spans
            )
            delta_t_wall_bulk_mean_k = safe_mean(
                finite_float(major_support_lookup.get((source_id, span_name, time_s), {}).get("delta_t_wall_bulk_mean_k"))
                for span_name in component_spans
            )
            delta_t_wall_bulk_min_k = min(
                (
                    finite_float(major_support_lookup.get((source_id, span_name, time_s), {}).get("delta_t_wall_bulk_min_k"))
                    for span_name in component_spans
                    if math.isfinite(finite_float(major_support_lookup.get((source_id, span_name, time_s), {}).get("delta_t_wall_bulk_min_k")))
                ),
                default=math.nan,
            )
            bulk_temp_k = safe_mean(
                finite_float(major_support_lookup.get((source_id, span_name, time_s), {}).get("bulk_temp_k"))
                for span_name in component_spans
            )
            bulk_velocity_m_s = safe_mean(
                finite_float(major_support_lookup.get((source_id, span_name, time_s), {}).get("bulk_velocity_m_s"))
                for span_name in component_spans
            )
            dh_m = safe_mean(
                finite_float(major_support_lookup.get((source_id, span_name, time_s), {}).get("hydraulic_diameter_geom_m"))
                for span_name in component_spans
            )
            htc_effective_w_m2_k = wall_heat_total_w / delta_t_integral_k_m2 if math.isfinite(wall_heat_total_w) and math.isfinite(delta_t_integral_k_m2) and abs(delta_t_integral_k_m2) > 0.0 else math.nan
            dimensionless = build_dimensionless_bundle(
                context=context,
                bulk_temp_k=bulk_temp_k,
                velocity_m_s=bulk_velocity_m_s,
                dh_m=dh_m,
                htc_w_m2_k=htc_effective_w_m2_k,
                convention=property_convention,
            )
            correction_values: list[float] = []
            for span_name in component_spans:
                correction_values.extend(correction_group.get((source_id, span_name, time_s), []))
            bulk_centerline_correction_k = safe_mean(correction_values)
            q_bulk_centerline_correction_proxy_w = (
                htc_effective_w_m2_k * wall_area_total_m2 * bulk_centerline_correction_k
                if all(math.isfinite(v) for v in (htc_effective_w_m2_k, wall_area_total_m2, bulk_centerline_correction_k))
                else math.nan
            )
            enthalpy_sign = sign_token(enthalpy_change_w, zero_tol=1.0)
            wall_sign = sign_token(wall_heat_total_w, zero_tol=1.0)
            thermal_direction_consistent = enthalpy_sign == wall_sign or "zero" in {enthalpy_sign, wall_sign}
            role_label = classify_role_label(q_intended_transfer_w, q_external_or_loss_w)
            fit_use_status, exclusion_reason_primary = classify_time_row(
                branch_name=branch_row["branch_name"],
                branch_fit_status=branch_row["fit_status"],
                support_fraction=support_fraction,
                delta_t_wall_bulk_mean_k=delta_t_wall_bulk_mean_k,
                residual_fraction=residual_fraction,
                thermal_direction_consistent=thermal_direction_consistent,
                grouped_reconstruction_fraction=grouped_reconstruction_fraction,
            )
            rows_out.append(
                {
                    "source_id": source_id,
                    "case_label": context.display_label,
                    "case_order": context.case_order,
                    "branch_name": branch_row["branch_name"],
                    "branch_type": branch_row["branch_type"],
                    "component_spans": branch_row["component_spans"],
                    "time_s": float(time_s),
                    "branch_fit_status": branch_row["fit_status"],
                    "branch_fit_reason": branch_row["fit_reason"],
                    "q_enthalpy_w": enthalpy_change_w,
                    "q_wall_total_w": wall_heat_total_w,
                    "q_intended_transfer_w": q_intended_transfer_w,
                    "q_external_or_loss_w": q_external_or_loss_w,
                    "q_sink_or_cooling_w": q_sink_or_cooling_w,
                    "q_junction_or_unresolved_w": q_junction_or_unresolved_w,
                    "q_bulk_centerline_correction_proxy_w": q_bulk_centerline_correction_proxy_w,
                    "q_residual_w": q_residual_w,
                    "residual_fraction_of_wall_heat": residual_fraction,
                    "grouped_reconstruction_fraction": grouped_reconstruction_fraction,
                    "support_fraction": support_fraction,
                    "thermal_direction_consistent": "yes" if thermal_direction_consistent else "no",
                    "delta_t_wall_bulk_mean_k": delta_t_wall_bulk_mean_k,
                    "delta_t_wall_bulk_min_k": delta_t_wall_bulk_min_k,
                    "role_label": role_label,
                    "wall_area_total_m2": wall_area_total_m2,
                    "delta_t_wall_minus_bulk_integral_k_m2": delta_t_integral_k_m2,
                    "htc_effective_w_m2_k": htc_effective_w_m2_k,
                    "bulk_temp_k": bulk_temp_k,
                    "bulk_velocity_m_s": bulk_velocity_m_s,
                    "hydraulic_diameter_geom_m": dh_m,
                    "property_temperature_k": dimensionless["property_temperature_k"],
                    "rho_effective_kg_m3": dimensionless["rho_effective_kg_m3"],
                    "re_effective": dimensionless["re_effective"],
                    "pr_effective": dimensionless["pr_effective"],
                    "pe_effective": dimensionless["pe_effective"],
                    "nu_effective": dimensionless["nu_effective"],
                    "bulk_minus_centerline_temp_k": bulk_centerline_correction_k,
                    "fit_use_status": fit_use_status,
                    "exclusion_reason_primary": exclusion_reason_primary,
                }
            )
    return rows_out


def aggregate_case_rows(timeseries_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in timeseries_rows:
        grouped[(row["source_id"], row["branch_name"])].append(row)
    case_rows: list[dict[str, Any]] = []
    for (source_id, branch_name), payload in sorted(grouped.items(), key=lambda item: (int(item[1][0]["case_order"]), item[0][1])):
        summary = {
            "source_id": source_id,
            "case_label": payload[0]["case_label"],
            "case_order": payload[0]["case_order"],
            "branch_name": branch_name,
            "branch_type": payload[0]["branch_type"],
            "component_spans": payload[0]["component_spans"],
            "branch_fit_status": payload[0]["branch_fit_status"],
            "branch_fit_reason": payload[0]["branch_fit_reason"],
            "mean_q_enthalpy_w": safe_mean(finite_float(row.get("q_enthalpy_w")) for row in payload),
            "mean_q_wall_total_w": safe_mean(finite_float(row.get("q_wall_total_w")) for row in payload),
            "mean_q_intended_transfer_w": safe_mean(finite_float(row.get("q_intended_transfer_w")) for row in payload),
            "mean_q_external_or_loss_w": safe_mean(finite_float(row.get("q_external_or_loss_w")) for row in payload),
            "mean_q_sink_or_cooling_w": safe_mean(finite_float(row.get("q_sink_or_cooling_w")) for row in payload),
            "mean_q_junction_or_unresolved_w": safe_mean(finite_float(row.get("q_junction_or_unresolved_w")) for row in payload),
            "mean_q_bulk_centerline_correction_proxy_w": safe_mean(finite_float(row.get("q_bulk_centerline_correction_proxy_w")) for row in payload),
            "mean_q_residual_w": safe_mean(finite_float(row.get("q_residual_w")) for row in payload),
            "mean_residual_fraction_of_wall_heat": safe_mean(finite_float(row.get("residual_fraction_of_wall_heat")) for row in payload),
            "max_residual_fraction_of_wall_heat": max((finite_float(row.get("residual_fraction_of_wall_heat")) for row in payload), default=math.nan),
            "mean_grouped_reconstruction_fraction": safe_mean(finite_float(row.get("grouped_reconstruction_fraction")) for row in payload),
            "mean_support_fraction": safe_mean(finite_float(row.get("support_fraction")) for row in payload),
            "min_delta_t_wall_bulk_mean_k": min((finite_float(row.get("delta_t_wall_bulk_mean_k")) for row in payload), default=math.nan),
            "min_delta_t_wall_bulk_min_k": min((finite_float(row.get("delta_t_wall_bulk_min_k")) for row in payload), default=math.nan),
            "mean_htc_effective_w_m2_k": safe_mean(finite_float(row.get("htc_effective_w_m2_k")) for row in payload),
            "mean_nu_effective": safe_mean(finite_float(row.get("nu_effective")) for row in payload),
            "mean_re_effective": safe_mean(finite_float(row.get("re_effective")) for row in payload),
            "mean_pr_effective": safe_mean(finite_float(row.get("pr_effective")) for row in payload),
            "mean_pe_effective": safe_mean(finite_float(row.get("pe_effective")) for row in payload),
            "mean_bulk_minus_centerline_temp_k": safe_mean(finite_float(row.get("bulk_minus_centerline_temp_k")) for row in payload),
            "pass_time_fraction": sum(1 for row in payload if row["fit_use_status"] == "candidate_time") / max(len(payload), 1),
            "direction_consistent_all_times": all(str(row["thermal_direction_consistent"]).lower() == "yes" for row in payload),
            "role_label": payload[0]["role_label"],
            "time_sample_count": len(payload),
        }
        fit_use_status, exclusion_reason_primary, reasons = classify_case_row(summary)
        summary["fit_use_status"] = fit_use_status
        summary["exclusion_reason_primary"] = exclusion_reason_primary
        summary["exclusion_reasons_json"] = json.dumps(reasons)
        case_rows.append(summary)
    return case_rows


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    content = f"""# Ethan Salt Thermal Closure Hardening

Generated: `2026-06-19`

## Purpose

This package rebuilds Salt branch/leg thermal closure from exact retained-time
enthalpy rows and exact retained-time section wall-heat rows, then decomposes
the wall exchange into intended-transfer, parasitic-loss, sink, grouped
reconstruction gap, and closure residual buckets. It is an audit-first package:
rows remain excluded unless support, sign, and residual gates are all met.

## Inputs

- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/enthalpy_balance_by_leg.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/fluid_side_htc_nu_section_summary.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/bulk_vs_centerline_temperature_correction.csv`
- `reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/phase3_branch_trust_gate/branch_promotion_gate.csv`
- `tmp/2026-06-15_live_case_analysis/**/azimuthal_wall_transport_summary.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_cumulative_timeseries.csv`

## Key counts

- case count: `{summary["case_count"]}`
- time row count: `{summary["timeseries_row_count"]}`
- case row count: `{summary["case_row_count"]}`
- fit-ready branch rows: `{summary["fit_ready_count"]}`

## Gate logic

- `right_leg` stays hard-blocked
- `upcomer` stays sensitivity-only because it is derived from overlapping direct spans
- direct branches require:
  - support fraction at least `{SUPPORT_FRACTION_MIN:.2f}`
  - `|Twall - Tbulk|` at least `{DELTA_T_MIN_K:.2f} K`
  - mean residual fraction at most `{RESIDUAL_FRACTION_MAX:.2f}`
  - pass-time fraction at least `{PASS_TIME_FRACTION_MIN:.2f}`
  - consistent enthalpy vs wall-heat direction

## Important limitation

This package still does **not** resolve a full internal convection / wall
conduction / external convection-radiation resistance split. It keeps those
unknowns separated into explicit buckets instead of hiding them inside Salt-side
`Nu`.
"""
    path.write_text(content, encoding="utf-8")


def write_math_companion(path: Path) -> None:
    content = """# Math Companion

For each branch/time row:

- `Q_enthalpy = sum_component_spans(mdot * cp * (T_bulk,out - T_bulk,in))`
- `Q_wall = sum_component_spans(wall_heat_integral)`
- `Q_residual = Q_enthalpy - Q_wall`
- `residual_fraction = |Q_residual| / |Q_wall|`
- `Q_grouped_total = Q_intended_transfer + Q_external_or_loss + other_grouped_terms`
- `Q_junction_or_unresolved = Q_wall - Q_grouped_total`
- `grouped_reconstruction_fraction = |Q_junction_or_unresolved| / |Q_wall|`

Signed interpretation:

- Positive `Q_wall` means wall heat enters the fluid.
- Negative `Q_wall` means wall heat leaves the fluid.
- Positive `Q_enthalpy` means the fluid gains energy along the local branch direction.

The effective HTC / Nu columns are computed from the exact retained-time section
integrals:

- `h = Q_wall / integral_wall(T_wall - T_bulk) dA`
- `Nu = h * D_h / k(T_property)`

The `bulk-vs-centerline correction proxy` is a reporting aid only:

- `Q_bc_proxy = h * A_wall * (T_bulk - T_centerline)`

It is not used as a fitting gate.
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    contexts = load_case_contexts(source_ids)
    branch_gate_rows = load_branch_gate_rows(source_ids)
    timeseries_rows = build_thermal_timeseries_rows(contexts, branch_gate_rows, property_convention=args.property_convention)
    case_rows = aggregate_case_rows(timeseries_rows)
    fit_ready_rows = [row for row in case_rows if row["fit_use_status"] == "fit_used"]
    exclusion_counter = Counter(row["exclusion_reason_primary"] for row in case_rows if row["fit_use_status"] != "fit_used")
    trust_counter: dict[str, Counter[str]] = defaultdict(Counter)
    for row in case_rows:
        trust_counter[row["branch_name"]][row["fit_use_status"]] += 1

    output_dir = ensure_dir(Path(args.output_dir))
    timeseries_fieldnames = list(timeseries_rows[0].keys())
    case_fieldnames = list(case_rows[0].keys())
    csv_dump_rows(output_dir / "thermal_closure_timeseries.csv", timeseries_rows, fieldnames=timeseries_fieldnames)
    csv_dump_rows(output_dir / "thermal_closure_by_case.csv", case_rows, fieldnames=case_fieldnames)
    csv_dump_rows(output_dir / "thermal_fit_ready_rows.csv", fit_ready_rows, fieldnames=case_fieldnames)
    csv_dump_rows(
        output_dir / "thermal_exclusion_summary.csv",
        [
            {
                "asset_family": "thermal_branch",
                "exclusion_reason_primary": reason,
                "row_count": count,
            }
            for reason, count in sorted(exclusion_counter.items())
        ],
        fieldnames=["asset_family", "exclusion_reason_primary", "row_count"],
    )
    csv_dump_rows(
        output_dir / "branch_trust_summary.csv",
        [
            {
                "branch_name": branch_name,
                "fit_used_count": counter.get("fit_used", 0),
                "sensitivity_only_count": counter.get("sensitivity_only", 0),
                "excluded_count": counter.get("excluded", 0),
            }
            for branch_name, counter in sorted(trust_counter.items())
        ],
        fieldnames=["branch_name", "fit_used_count", "sensitivity_only_count", "excluded_count"],
    )
    csv_dump_rows(
        output_dir / "closure_waterfall_by_case.csv",
        [
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "branch_name": row["branch_name"],
                "mean_q_enthalpy_w": row["mean_q_enthalpy_w"],
                "mean_q_wall_total_w": row["mean_q_wall_total_w"],
                "mean_q_intended_transfer_w": row["mean_q_intended_transfer_w"],
                "mean_q_external_or_loss_w": row["mean_q_external_or_loss_w"],
                "mean_q_sink_or_cooling_w": row["mean_q_sink_or_cooling_w"],
                "mean_q_junction_or_unresolved_w": row["mean_q_junction_or_unresolved_w"],
                "mean_q_residual_w": row["mean_q_residual_w"],
                "fit_use_status": row["fit_use_status"],
            }
            for row in case_rows
        ],
        fieldnames=[
            "source_id",
            "case_label",
            "branch_name",
            "mean_q_enthalpy_w",
            "mean_q_wall_total_w",
            "mean_q_intended_transfer_w",
            "mean_q_external_or_loss_w",
            "mean_q_sink_or_cooling_w",
            "mean_q_junction_or_unresolved_w",
            "mean_q_residual_w",
            "fit_use_status",
        ],
    )

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(contexts),
        "timeseries_row_count": len(timeseries_rows),
        "case_row_count": len(case_rows),
        "fit_ready_count": len(fit_ready_rows),
        "branch_fit_ready_counts": dict(Counter(row["branch_name"] for row in fit_ready_rows)),
        "property_convention": args.property_convention,
        "support_fraction_min": SUPPORT_FRACTION_MIN,
        "delta_t_min_k": DELTA_T_MIN_K,
        "residual_fraction_max": RESIDUAL_FRACTION_MAX,
        "grouped_reconstruction_max": GROUP_RECONSTRUCTION_MAX,
        "pass_time_fraction_min": PASS_TIME_FRACTION_MIN,
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir / "README.md", summary)
    write_math_companion(output_dir / "MATH_COMPANION.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
