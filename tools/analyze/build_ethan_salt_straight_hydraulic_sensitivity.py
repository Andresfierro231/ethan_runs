#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import (
    ROOT,
    csv_dump_rows,
    finite_float,
    load_csv_rows,
    require_columns,
    write_json,
)
from tools.analyze.ethan_salt_hardening_common import build_dimensionless_bundle, load_case_contexts

MODEL_DEPENDENCY_V1_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_model_dependency_package"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_straight_hydraulic_sensitivity"

DIRECT_SHEAR_BASE_MIN = 0.50
DIRECT_SHEAR_BASE_MAX = 2.00
DIRECT_SHEAR_STRICT_MIN = 0.67
DIRECT_SHEAR_STRICT_MAX = 1.50
DIRECT_SHEAR_LOOSE_MIN = 0.40
DIRECT_SHEAR_LOOSE_MAX = 2.50
LATE_WINDOW_TARGET_S = 20.0
MIN_LATE_WINDOW_COVERAGE_S = 19.0
TARGET_SPAN_NAMES = {"lower_leg", "test_section_span"}
GRAVITY_RE = re.compile(r"value\s*\(\s*([^\s]+)\s+([^\s]+)\s+([^\s]+)\s*\)\s*;")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the Salt straight-section hydraulic sensitivity package from the "
            "preserved retained-time major-loss artifacts and keep the late-window "
            "status honest when the retained tail is shorter than about 20 s."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument(
        "--package-root-override",
        action="append",
        default=[],
        help="Override one Salt package root as source_id=/abs/or/relative/path.",
    )
    return parser.parse_args()


def parse_package_root_overrides(values: list[str]) -> dict[str, Path]:
    overrides: dict[str, Path] = {}
    for value in values:
        source_id, separator, raw_path = value.partition("=")
        source_id = source_id.strip()
        raw_path = raw_path.strip()
        if separator != "=" or not source_id or not raw_path:
            raise ValueError(
                f"invalid package-root override `{value}`; expected source_id=/path/to/package"
            )
        overrides[source_id] = Path(raw_path).resolve()
    return overrides


def filter_rows(rows: list[dict[str, str]], source_ids: set[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids]


def ratio_pass(row: dict[str, str], ratio_min: float, ratio_max: float) -> bool:
    ratio = finite_float(row.get("direct_to_shear_darcy_ratio"))
    return ratio_min <= ratio <= ratio_max


def safe_weighted_mean(pairs: list[tuple[float, float]]) -> float:
    usable = [(value, weight) for value, weight in pairs if math.isfinite(value) and math.isfinite(weight) and weight > 0.0]
    if not usable:
        return math.nan
    total_weight = sum(weight for _value, weight in usable)
    if total_weight <= 0.0:
        return math.nan
    return float(sum(value * weight for value, weight in usable) / total_weight)


def parse_gravity_vector(case_root: Path) -> tuple[float, float, float]:
    path = case_root / "constant" / "g"
    if not path.exists():
        return (0.0, -9.81, 0.0)
    match = GRAVITY_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        return (0.0, -9.81, 0.0)
    return tuple(float(match.group(index)) for index in range(1, 4))  # type: ignore[return-value]


def build_station_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, int], dict[str, float]]:
    lookup: dict[tuple[str, int], dict[str, float]] = {}
    for row in rows:
        key = (str(row["span_name"]), int(row["bin_index"]))
        s_start = finite_float(row.get("s_start_m"))
        s_end = finite_float(row.get("s_end_m"))
        lookup[key] = {
            "s_start_m": s_start,
            "s_end_m": s_end,
            "tangent_x": finite_float(row.get("tangent_x")),
            "tangent_y": finite_float(row.get("tangent_y")),
            "tangent_z": finite_float(row.get("tangent_z")),
        }
    return lookup


def build_major_row_groups(rows: list[dict[str, str]]) -> dict[tuple[float, str], list[dict[str, Any]]]:
    grouped: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        span_name = str(row.get("span_name", ""))
        if span_name not in TARGET_SPAN_NAMES:
            continue
        time_s = finite_float(row.get("time_s"))
        if not math.isfinite(time_s):
            continue
        grouped[(time_s, span_name)].append(row)
    for key in grouped:
        grouped[key].sort(key=lambda item: int(item["bin_index"]))
    return grouped


def flow_ordered_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]:
    valid = [row for row in rows if math.isfinite(finite_float(row.get("p_wall_area_avg_pa"))) and math.isfinite(finite_float(row.get("p_rgh_wall_area_avg_pa")))]
    if not valid:
        return [], math.nan
    flow_sign = finite_float(valid[0].get("flow_alignment_sign"))
    if not math.isfinite(flow_sign) or flow_sign == 0.0:
        return [], math.nan
    ordered = list(valid)
    if flow_sign < 0.0:
        ordered.reverse()
    return ordered, flow_sign


def section_core_rows(rows: list[dict[str, Any]], dh_mean: float, section_length_m: float) -> list[dict[str, Any]]:
    if not math.isfinite(dh_mean) or dh_mean <= 0.0 or not math.isfinite(section_length_m) or section_length_m <= 0.0:
        return []
    exclusion_m = max(2.0 * dh_mean, 0.05 * section_length_m)
    core: list[dict[str, Any]] = []
    for row in rows:
        s0 = finite_float(row.get("s_start_m"))
        s1 = finite_float(row.get("s_end_m"))
        if not math.isfinite(s0) or not math.isfinite(s1):
            continue
        smid = 0.5 * (s0 + s1)
        if smid < exclusion_m or smid > (section_length_m - exclusion_m):
            continue
        core.append(row)
    return core


def weighted_section_scalars(rows: list[dict[str, Any]]) -> dict[str, float]:
    def weight(row: dict[str, Any]) -> float:
        return max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m")))

    weighted_rows = [(row, weight(row)) for row in rows]
    return {
        "rho_bulk_kg_m3": safe_weighted_mean([(finite_float(row.get("rho_bulk_kg_m3")), ds) for row, ds in weighted_rows]),
        "bulk_velocity_m_s": safe_weighted_mean([(finite_float(row.get("bulk_velocity_m_s")), ds) for row, ds in weighted_rows]),
        "hydraulic_diameter_geom_m": safe_weighted_mean(
            [(finite_float(row.get("hydraulic_diameter_geom_m")), ds) for row, ds in weighted_rows]
        ),
        "mdot_mean_abs_kg_s": safe_weighted_mean([(finite_float(row.get("mdot_mean_abs_kg_s")), ds) for row, ds in weighted_rows]),
        "bulk_temp_fluid_area_avg_k": safe_weighted_mean(
            [(finite_float(row.get("bulk_temp_fluid_area_avg_k")), ds) for row, ds in weighted_rows]
        ),
        "section_length_m": float(sum(ds for _row, ds in weighted_rows if math.isfinite(ds))),
    }


def direct_to_shear_ratio(direct_darcy: float, shear_darcy: float) -> float:
    if not math.isfinite(direct_darcy) or not math.isfinite(shear_darcy) or abs(shear_darcy) <= 0.0:
        return math.nan
    return float(abs(direct_darcy / shear_darcy))


def classify_retained_time_row(
    support_fraction: float,
    pressure_loss_hydro_pa: float,
    direct_prgh_darcy: float,
    shear_darcy_core: float,
) -> tuple[str, str]:
    ratio = direct_to_shear_ratio(direct_prgh_darcy, shear_darcy_core)
    if not math.isfinite(support_fraction) or support_fraction < 0.75:
        return "excluded", "support_fraction_below_floor"
    if not math.isfinite(pressure_loss_hydro_pa):
        return "excluded", "missing_hydro_loss"
    if pressure_loss_hydro_pa <= 0.0:
        return "excluded", "buoyancy_aided_or_net_gain_section"
    if not math.isfinite(direct_prgh_darcy) or not math.isfinite(shear_darcy_core):
        return "excluded", "missing_direct_or_shear_reference"
    if direct_prgh_darcy <= 0.0 or shear_darcy_core <= 0.0:
        return "excluded", "nonpositive_direct_or_shear_friction_proxy"
    if not math.isfinite(ratio):
        return "excluded", "missing_direct_to_shear_ratio"
    if ratio < DIRECT_SHEAR_BASE_MIN or ratio > DIRECT_SHEAR_BASE_MAX:
        return "excluded", "direct_to_shear_magnitude_gap"
    return "fit_used", ""


def build_retained_time_rows(
    source_ids: set[str] | None,
    package_root_overrides: dict[str, Path] | None = None,
) -> list[dict[str, Any]]:
    contexts = load_case_contexts(source_ids, package_root_overrides=package_root_overrides)
    rows_out: list[dict[str, Any]] = []
    for source_id, context in sorted(contexts.items(), key=lambda item: item[1].case_order):
        major_rows = load_csv_rows(context.package_root / "major_loss_cumulative_timeseries.csv")
        station_rows = load_csv_rows(context.package_root / "leg_centerline_station_definitions.csv")
        require_columns(
            major_rows,
            [
                "time_s",
                "span_name",
                "span_kind",
                "bin_index",
                "flow_alignment_sign",
                "s_start_m",
                "s_end_m",
                "darcy_f",
                "darcy_f_pressure_drop_prgh",
                "dp_major_gradient_direct_prgh_pa_per_m",
                "dp_major_gradient_direct_p_pa_per_m",
                "p_wall_area_avg_pa",
                "p_rgh_wall_area_avg_pa",
                "bulk_temp_fluid_area_avg_k",
                "thermal_support_status",
                "hydraulic_diameter_geom_m",
                "bulk_velocity_m_s",
                "rho_bulk_kg_m3",
                "mdot_mean_abs_kg_s",
            ],
            f"{source_id}/major_loss_cumulative_timeseries.csv",
        )
        require_columns(
            station_rows,
            ["span_name", "bin_index", "s_start_m", "s_end_m", "tangent_x", "tangent_y", "tangent_z"],
            f"{source_id}/leg_centerline_station_definitions.csv",
        )
        station_lookup = build_station_lookup(station_rows)
        gravity_vec = parse_gravity_vector(context.source_root)
        grouped = build_major_row_groups(major_rows)
        for (time_s, span_name), time_rows in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
            merged_rows = []
            for row in time_rows:
                merged_rows.append({**row, **station_lookup.get((span_name, int(row["bin_index"])), {})})
            ordered_rows, flow_sign = flow_ordered_rows(merged_rows)
            if not ordered_rows:
                continue
            stats = weighted_section_scalars(ordered_rows)
            section_length_m = stats["section_length_m"]
            rho_mean = stats["rho_bulk_kg_m3"]
            velocity_mean = stats["bulk_velocity_m_s"]
            dh_mean = stats["hydraulic_diameter_geom_m"]
            local_q = 0.5 * rho_mean * velocity_mean * velocity_mean if math.isfinite(rho_mean) and math.isfinite(velocity_mean) else math.nan

            p_start = finite_float(ordered_rows[0].get("p_wall_area_avg_pa"))
            p_end = finite_float(ordered_rows[-1].get("p_wall_area_avg_pa"))
            pressure_drop_p = p_start - p_end
            hydro_integral = 0.0
            for row in ordered_rows:
                ds = max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m")))
                tangent_x = finite_float(row.get("tangent_x"))
                tangent_y = finite_float(row.get("tangent_y"))
                tangent_z = finite_float(row.get("tangent_z"))
                tangent_norm = math.sqrt(tangent_x * tangent_x + tangent_y * tangent_y + tangent_z * tangent_z)
                if tangent_norm <= 0.0:
                    continue
                tangent_dot_g = (
                    gravity_vec[0] * (tangent_x / tangent_norm)
                    + gravity_vec[1] * (tangent_y / tangent_norm)
                    + gravity_vec[2] * (tangent_z / tangent_norm)
                )
                hydro_integral += finite_float(row.get("rho_bulk_kg_m3")) * flow_sign * tangent_dot_g * ds
            pressure_loss_hydro = pressure_drop_p + hydro_integral
            core_rows = section_core_rows(ordered_rows, dh_mean, section_length_m)
            direct_prgh_darcy = safe_weighted_mean(
                [
                    (
                        finite_float(row.get("darcy_f_pressure_drop_prgh")),
                        max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m"))),
                    )
                    for row in ordered_rows
                ]
            )
            shear_darcy_core = safe_weighted_mean(
                [
                    (
                        finite_float(row.get("darcy_f")),
                        max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m"))),
                    )
                    for row in core_rows
                ]
            )
            support_fraction = safe_weighted_mean(
                [
                    (
                        1.0 if str(row.get("thermal_support_status", "")) == "usable" else 0.0,
                        max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m"))),
                    )
                    for row in ordered_rows
                ]
            )
            ratio = direct_to_shear_ratio(direct_prgh_darcy, shear_darcy_core)
            fit_use_status, exclusion_reason_primary = classify_retained_time_row(
                support_fraction,
                pressure_loss_hydro,
                direct_prgh_darcy,
                shear_darcy_core,
            )
            dimensionless = build_dimensionless_bundle(
                context=context,
                bulk_temp_k=stats["bulk_temp_fluid_area_avg_k"],
                velocity_m_s=velocity_mean,
                dh_m=dh_mean,
                htc_w_m2_k=0.0,
                convention="branch_bulk",
            )
            rows_out.append(
                {
                    "source_id": source_id,
                    "case_label": context.display_label,
                    "time_s": time_s,
                    "section_name": span_name,
                    "section_kind": str(ordered_rows[0].get("span_kind", "")),
                    "net_section_role": "dissipative" if pressure_loss_hydro > 0.0 else "buoyancy_aided_or_net_gain",
                    "pressure_loss_hydro_pa": pressure_loss_hydro,
                    "friction_target_value": (
                        pressure_loss_hydro * 2.0 * dh_mean / (local_q * section_length_m)
                        if math.isfinite(local_q)
                        and local_q > 0.0
                        and math.isfinite(dh_mean)
                        and dh_mean > 0.0
                        and math.isfinite(section_length_m)
                        and section_length_m > 0.0
                        else math.nan
                    ),
                    "direct_prgh_darcy": direct_prgh_darcy,
                    "shear_darcy_core": shear_darcy_core,
                    "direct_to_shear_ratio": ratio,
                    "support_fraction": support_fraction,
                    "bulk_velocity_effective_m_s": velocity_mean,
                    "hydraulic_diameter_m": dh_mean,
                    "rho_bulk_kg_m3": rho_mean,
                    "mdot_mean_abs_kg_s": stats["mdot_mean_abs_kg_s"],
                    "property_temperature_k": dimensionless["property_temperature_k"],
                    "re_value": dimensionless["re_effective"],
                    "time_resolution_status": "retained_time_sample",
                    "fit_use_status": fit_use_status,
                    "exclusion_reason_primary": exclusion_reason_primary,
                }
            )
    rows_out.sort(key=lambda row: (row["case_label"], row["section_name"], row["time_s"]))
    return rows_out


def build_late_window_rows(retained_time_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not retained_time_rows:
        return []
    source_max_time: dict[str, float] = {}
    for row in retained_time_rows:
        source_id = row["source_id"]
        source_max_time[source_id] = max(source_max_time.get(source_id, -math.inf), finite_float(row.get("time_s")))
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in retained_time_rows:
        source_id = row["source_id"]
        if finite_float(row.get("time_s")) >= source_max_time[source_id] - LATE_WINDOW_TARGET_S:
            grouped[(source_id, row["section_name"])].append(row)

    rows_out: list[dict[str, Any]] = []
    for (_source_id, _section_name), payload in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        payload.sort(key=lambda row: finite_float(row.get("time_s")))
        support_fraction = safe_weighted_mean([(finite_float(row.get("support_fraction")), 1.0) for row in payload])
        pressure_loss_hydro = safe_weighted_mean([(finite_float(row.get("pressure_loss_hydro_pa")), 1.0) for row in payload])
        direct_prgh_darcy = safe_weighted_mean([(finite_float(row.get("direct_prgh_darcy")), 1.0) for row in payload])
        shear_darcy_core = safe_weighted_mean([(finite_float(row.get("shear_darcy_core")), 1.0) for row in payload])
        fit_use_status, exclusion_reason_primary = classify_retained_time_row(
            support_fraction,
            pressure_loss_hydro,
            direct_prgh_darcy,
            shear_darcy_core,
        )
        times = [finite_float(row.get("time_s")) for row in payload if math.isfinite(finite_float(row.get("time_s")))]
        rows_out.append(
            {
                "source_id": payload[0]["source_id"],
                "case_label": payload[0]["case_label"],
                "section_name": payload[0]["section_name"],
                "section_kind": payload[0]["section_kind"],
                "re_value": safe_weighted_mean([(finite_float(row.get("re_value")), 1.0) for row in payload]),
                "friction_target_value": safe_weighted_mean(
                    [(finite_float(row.get("friction_target_value")), 1.0) for row in payload]
                ),
                "support_fraction": support_fraction,
                "direct_to_shear_ratio": direct_to_shear_ratio(direct_prgh_darcy, shear_darcy_core),
                "pressure_loss_hydro_pa": pressure_loss_hydro,
                "direct_prgh_darcy": direct_prgh_darcy,
                "shear_darcy_core": shear_darcy_core,
                "property_temperature_k": safe_weighted_mean(
                    [(finite_float(row.get("property_temperature_k")), 1.0) for row in payload]
                ),
                "window_start_s": source_max_time[payload[0]["source_id"]] - LATE_WINDOW_TARGET_S,
                "window_end_s": source_max_time[payload[0]["source_id"]],
                "window_min_time_s": min(times, default=math.nan),
                "window_span_s": (max(times) - min(times)) if len(times) >= 2 else 0.0,
                "time_sample_count": len(payload),
                "time_resolution_status": "late_window_mean",
                "fit_use_status": fit_use_status,
                "exclusion_reason_primary": exclusion_reason_primary,
            }
        )
    return rows_out


def build_late_window_sensitivity_row(
    base_fit_rows: list[dict[str, str]],
    late_window_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not late_window_rows:
        return {
            "asset_family": "straight_section_friction",
            "sensitivity_name": "late_window_choice",
            "status": "not_run",
            "base_row_count": len(base_fit_rows),
            "sensitivity_row_count": 0,
            "row_count_delta": -len(base_fit_rows),
            "qualitative_conclusion_changed": "unknown",
            "note": "retained-time straight rows were not rebuilt from the preserved additive package roots",
        }
    spans = [finite_float(row.get("window_span_s")) for row in late_window_rows if math.isfinite(finite_float(row.get("window_span_s")))]
    min_span = min(spans, default=math.nan)
    max_span = max(spans, default=math.nan)
    if not math.isfinite(min_span) or min_span < MIN_LATE_WINDOW_COVERAGE_S:
        return {
            "asset_family": "straight_section_friction",
            "sensitivity_name": "late_window_choice",
            "status": "not_run",
            "base_row_count": len(base_fit_rows),
            "sensitivity_row_count": len([row for row in late_window_rows if row["fit_use_status"] == "fit_used"]),
            "row_count_delta": len([row for row in late_window_rows if row["fit_use_status"] == "fit_used"]) - len(base_fit_rows),
            "qualitative_conclusion_changed": "unknown",
            "note": (
                "retained-time defended straight rows were rebuilt, but the preserved late-window "
                f"coverage is only {min_span:.1f}-{max_span:.1f} s across target sections; "
                "need about 20 s of preserved continuation support before rerunning the late-window sensitivity"
            ),
        }
    late_fit_rows = [row for row in late_window_rows if row["fit_use_status"] == "fit_used"]
    base_keys = {(row["source_id"], row["scope_name"]) for row in base_fit_rows}
    late_keys = {(row["source_id"], row["section_name"]) for row in late_fit_rows}
    return {
        "asset_family": "straight_section_friction",
        "sensitivity_name": "late_window_choice",
        "status": "run",
        "base_row_count": len(base_fit_rows),
        "sensitivity_row_count": len(late_fit_rows),
        "row_count_delta": len(late_fit_rows) - len(base_fit_rows),
        "qualitative_conclusion_changed": "yes" if base_keys != late_keys else "no",
        "note": (
            "late-window rows were rebuilt from retained-time hydro-corrected section samples "
            f"with {min_span:.1f}-{max_span:.1f} s preserved coverage inside the target {LATE_WINDOW_TARGET_S:.0f} s window"
        ),
    }


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    package_root_overrides = parse_package_root_overrides(args.package_root_override)
    audit_rows = filter_rows(load_csv_rows(MODEL_DEPENDENCY_V1_DIR / "hydraulic_hardening_audit.csv"), source_ids)
    fit_rows = filter_rows(load_csv_rows(MODEL_DEPENDENCY_V1_DIR / "hydraulic_fit_ready_rows.csv"), source_ids)

    straight_rows = [row for row in audit_rows if row["asset_family"] == "straight_section_friction"]
    base_fit_rows = [row for row in fit_rows if row["scope_name"] in TARGET_SPAN_NAMES]
    retained_time_rows = build_retained_time_rows(source_ids, package_root_overrides=package_root_overrides)
    late_window_rows = build_late_window_rows(retained_time_rows)

    fit_ready_rows = [
        {
            "source_id": row["source_id"],
            "case_label": row["case_label"],
            "section_name": row["scope_name"],
            "section_kind": row["scope_kind"],
            "re_value": finite_float(row.get("re_effective")),
            "friction_target_value": finite_float(row.get("apparent_darcy_f_local")),
            "support_fraction": finite_float(row.get("support_fraction")),
            "direct_to_shear_ratio": finite_float(row.get("direct_to_shear_darcy_ratio")),
            "time_resolution_status": "case_mean_only",
            "fit_use_status": row["fit_use_status"],
            "exclusion_reason_primary": "",
        }
        for row in base_fit_rows
    ]

    exclusion_rows = [
        {
            "asset_family": "straight_section_friction",
            "fit_use_status": status,
            "exclusion_reason_primary": reason,
            "row_count": count,
        }
        for (status, reason), count in sorted(
            Counter((row["fit_use_status"], row["exclusion_reason_primary"]) for row in straight_rows if row["fit_use_status"] != "fit_used").items()
        )
    ]
    retained_exclusion_counts = Counter(
        (row["fit_use_status"], row["exclusion_reason_primary"]) for row in retained_time_rows if row["fit_use_status"] != "fit_used"
    )
    for (status, reason), count in sorted(retained_exclusion_counts.items()):
        exclusion_rows.append(
            {
                "asset_family": "straight_section_friction_retained_time",
                "fit_use_status": status,
                "exclusion_reason_primary": reason,
                "row_count": count,
            }
        )

    def sensitivity_row(name: str, ratio_min: float, ratio_max: float) -> dict[str, Any]:
        kept = [row for row in straight_rows if row["fit_use_status"] == "fit_used" and ratio_pass(row, ratio_min, ratio_max)]
        return {
            "asset_family": "straight_section_friction",
            "sensitivity_name": name,
            "status": "run",
            "base_row_count": len(base_fit_rows),
            "sensitivity_row_count": len(kept),
            "row_count_delta": len(kept) - len(base_fit_rows),
            "qualitative_conclusion_changed": "yes" if len(kept) != len(base_fit_rows) else "no",
            "note": f"direct-to-shear ratio gate {ratio_min:.2f}-{ratio_max:.2f} on case-mean defended rows",
        }

    sensitivity_rows = [
        sensitivity_row("direct_to_shear_gate_loose", DIRECT_SHEAR_LOOSE_MIN, DIRECT_SHEAR_LOOSE_MAX),
        sensitivity_row("direct_to_shear_gate_base", DIRECT_SHEAR_BASE_MIN, DIRECT_SHEAR_BASE_MAX),
        sensitivity_row("direct_to_shear_gate_strict", DIRECT_SHEAR_STRICT_MIN, DIRECT_SHEAR_STRICT_MAX),
        build_late_window_sensitivity_row(base_fit_rows, late_window_rows),
    ]

    late_window_row = sensitivity_rows[-1]
    late_window_status = str(late_window_row["status"])
    blocked_rows = []
    if late_window_status != "run":
        blocked_rows.append(
            {
                "dependency_or_gap": "hydraulic_late_window_sensitivity",
                "current_status": late_window_status,
                "missing_requirement": "about 20 s of preserved retained-time defended straight-section rows from the continuation artifacts",
                "why_it_matters": "late-window stability of the defended straight-section friction model should be shown from retained-time rows, not only case means",
                "current_bias_risk": "the currently preserved 3-5 s tails are long enough to rebuild retained-time rows, but too short to claim a true 20 s late-window sensitivity",
            }
        )

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(
        output_dir / "straight_retained_time_rows.csv",
        retained_time_rows,
        [
            "source_id",
            "case_label",
            "time_s",
            "section_name",
            "section_kind",
            "net_section_role",
            "pressure_loss_hydro_pa",
            "re_value",
            "friction_target_value",
            "support_fraction",
            "direct_prgh_darcy",
            "shear_darcy_core",
            "direct_to_shear_ratio",
            "bulk_velocity_effective_m_s",
            "hydraulic_diameter_m",
            "rho_bulk_kg_m3",
            "mdot_mean_abs_kg_s",
            "property_temperature_k",
            "time_resolution_status",
            "fit_use_status",
            "exclusion_reason_primary",
        ],
    )
    csv_dump_rows(
        output_dir / "straight_late_window_rows.csv",
        late_window_rows,
        [
            "source_id",
            "case_label",
            "section_name",
            "section_kind",
            "re_value",
            "friction_target_value",
            "support_fraction",
            "direct_to_shear_ratio",
            "pressure_loss_hydro_pa",
            "direct_prgh_darcy",
            "shear_darcy_core",
            "property_temperature_k",
            "window_start_s",
            "window_end_s",
            "window_min_time_s",
            "window_span_s",
            "time_sample_count",
            "time_resolution_status",
            "fit_use_status",
            "exclusion_reason_primary",
        ],
    )
    csv_dump_rows(output_dir / "straight_fit_ready_rows.csv", fit_ready_rows)
    csv_dump_rows(output_dir / "straight_exclusion_summary.csv", exclusion_rows)
    csv_dump_rows(output_dir / "straight_sensitivity_runs.csv", sensitivity_rows)
    csv_dump_rows(output_dir / "straight_blocked_requirements.csv", blocked_rows)

    window_spans = [finite_float(row.get("window_span_s")) for row in late_window_rows if math.isfinite(finite_float(row.get("window_span_s")))]
    summary = {
        "generated_at": iso_timestamp(),
        "base_fit_row_count": len(base_fit_rows),
        "retained_time_row_count": len(retained_time_rows),
        "late_window_row_count": len(late_window_rows),
        "late_window_fit_used_row_count": len([row for row in late_window_rows if row["fit_use_status"] == "fit_used"]),
        "late_window_status": late_window_status,
        "min_available_window_span_s": min(window_spans, default=math.nan),
        "max_available_window_span_s": max(window_spans, default=math.nan),
        "fit_status_counts": dict(Counter(row["fit_use_status"] for row in fit_ready_rows)),
        "retained_time_fit_status_counts": dict(Counter(row["fit_use_status"] for row in retained_time_rows)),
    }
    write_json(output_dir / "summary.json", summary)

    override_inputs = ""
    if package_root_overrides:
        override_lines = "\n".join(
            f"- `{source_id}` -> `{path}`" for source_id, path in sorted(package_root_overrides.items())
        )
        override_inputs = f"\n- continuation-refresh package overrides:\n{override_lines}"

    readme = f"""# Ethan Salt Straight Hydraulic Sensitivity

Generated: `2026-06-19`

## Purpose

This package rebuilds retained-time hydro-corrected straight-section rows from
the preserved Salt case-analysis package roots, then keeps the late-window
sensitivity result honest when the retained tail is shorter than the target
approximately `{LATE_WINDOW_TARGET_S:.0f} s`.

## Inputs

- `reports/2026-06-18_ethan_salt_model_dependency_package/hydraulic_hardening_audit.csv`
- `reports/2026-06-18_ethan_salt_model_dependency_package/hydraulic_fit_ready_rows.csv`
- `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_cumulative_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/leg_centerline_station_definitions.csv`
{override_inputs}

## Important boundary

The preserved additive package roots now support explicit retained-time straight
rows, but the currently published Salt package roots only preserve about `3-5 s`
of tail data. The package therefore upgrades the blocker from "no retained-time
rows exist" to the narrower statement that a true last-`{LATE_WINDOW_TARGET_S:.0f} s`
window still needs continuation-derived retained support before the late-window
sensitivity can be called complete.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
