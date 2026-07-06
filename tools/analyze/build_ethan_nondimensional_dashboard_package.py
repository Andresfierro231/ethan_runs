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
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    relative_to_workspace,
    safe_float,
    save_matplotlib_figure,
)


REPORT_ROOT = WORKSPACE_ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package"
MANIFEST_PATH = WORKSPACE_ROOT / "imports" / "2026-06-17_ethan_nondimensional_dashboard_package.json"
TMP_SMOKE_ROOT = WORKSPACE_ROOT / "tmp" / "2026-06-17_ethan_nondimensional_dashboard_smoke"

METADATA_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"
HEAT_LATEST_CSV = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_steady_state_heat_flow_audit" / "latest_heat_partition.csv"
HEAT_WINDOW_CSV = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_steady_state_heat_flow_audit" / "heat_window_summary.csv"
FIELD_TRANSPORT_README = WORKSPACE_ROOT / "reports" / "2026-06-15_ethan_all_runs_field_transport_campaign" / "README.md"
BOUNDARY_REPORT_README = WORKSPACE_ROOT / "reports" / "2026-06-15_ethan_boundary_modeling_report" / "README.md"

LIVE_CASE_ANALYSIS_ROOT = WORKSPACE_ROOT / "tmp" / "2026-06-15_live_case_analysis"

SOURCE_ID_ORDER = [
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
]

SPAN_REGION_ORDER = (
    "lower_leg",
    "right_leg",
    "left_lower_leg",
    "test_section_span",
    "left_upper_leg",
    "upper_leg",
)
BRANCH_REGION_ORDER = (
    "heater",
    "downcomer",
    "upcomer",
    "cooler",
)
REGION_MEMBERS = {
    "lower_leg": ("lower_leg",),
    "right_leg": ("right_leg",),
    "left_lower_leg": ("left_lower_leg",),
    "test_section_span": ("test_section_span",),
    "left_upper_leg": ("left_upper_leg",),
    "upper_leg": ("upper_leg",),
    "heater": ("lower_leg",),
    "downcomer": ("right_leg",),
    "upcomer": ("left_lower_leg", "test_section_span", "left_upper_leg"),
    "cooler": ("upper_leg",),
}
REGION_LABELS = {
    "lower_leg": "Lower Leg",
    "right_leg": "Right Leg",
    "left_lower_leg": "Left Lower Leg",
    "test_section_span": "Test Section",
    "left_upper_leg": "Left Upper Leg",
    "upper_leg": "Upper Leg",
    "heater": "Heater Branch",
    "downcomer": "Downcomer Branch",
    "upcomer": "Upcomer Branch",
    "cooler": "Cooler Branch",
}
BRANCH_COLORS = {
    "heater": "#bc3908",
    "downcomer": "#7c3aed",
    "upcomer": "#0b6e4f",
    "cooler": "#1d4ed8",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Ethan nondimensional dashboard and candidate-input package."
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPORT_ROOT),
        help="Destination report package root.",
    )
    parser.add_argument(
        "--manifest-path",
        default=str(MANIFEST_PATH),
        help="Provenance manifest path.",
    )
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        default=[],
        help="Optional source ID filter. Repeat to limit the build to a subset.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_map(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def family_from_metadata(row: dict[str, str]) -> str:
    fluid = row.get("fluid", "").lower()
    return "water" if "water" in fluid else "salt"


def order_index(source_id: str) -> int:
    try:
        return SOURCE_ID_ORDER.index(source_id)
    except ValueError:
        return len(SOURCE_ID_ORDER)


def display_label(row: dict[str, str]) -> str:
    source_id = row.get("source_id", "")
    base_case = row.get("base_case_id", "")
    variant = row.get("variant_label", "").strip().title()
    if source_id == "val_salt_test_2_coarse_mesh_laminar":
        return "Salt 2 Val"
    if base_case.startswith("salt_test_"):
        number = base_case.split("_")[-1]
        if variant:
            return f"Salt {number} {variant}"
        return f"Salt {number}"
    if base_case.startswith("water_test_"):
        number = base_case.split("_")[-1]
        return f"Water {number}"
    return source_id


def first_finite(*values: object) -> float | None:
    for value in values:
        numeric = safe_float(value)
        if numeric is not None and math.isfinite(numeric):
            return float(numeric)
    return None


def mean_or_none(values: list[float]) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return None
    return float(mean(finite))


def ratio_or_none(numerator: object, denominator: object) -> float | None:
    top = safe_float(numerator)
    bottom = safe_float(denominator)
    if top is None or bottom in (None, 0.0) or not math.isfinite(bottom):
        return None
    return float(top) / float(bottom)


def resolve_case_analysis_root(source_id: str) -> Path | None:
    candidates = [
        LIVE_CASE_ANALYSIS_ROOT / "contract_fix_salt2" / source_id,
        LIVE_CASE_ANALYSIS_ROOT / "contract_fix_salt_family" / source_id,
        LIVE_CASE_ANALYSIS_ROOT / "contract_fix_water_family" / source_id,
        LIVE_CASE_ANALYSIS_ROOT / "local_probe_water1" / source_id,
        LIVE_CASE_ANALYSIS_ROOT / source_id,
    ]
    for candidate in candidates:
        if (candidate / "summary.json").exists() and (candidate / "thermal_streamwise_summary.csv").exists():
            return candidate
    return None


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_time_token(value: object) -> float | None:
    numeric = safe_float(value)
    if numeric is None or not math.isfinite(numeric):
        return None
    return round(float(numeric), 6)


def load_region_temperatures(
    package_root: Path,
    requested_times: list[float],
) -> tuple[dict[str, float | None], dict[str, Any]]:
    raw_path = package_root / "raw_extraction" / "bulk_cross_section_temperature_samples.csv"
    if not raw_path.exists():
        return (
            {region: None for region in REGION_MEMBERS},
            {
                "source": relative_to_workspace(raw_path),
                "coverage_status": "missing_raw_temperature_samples",
                "time_count": 0,
            },
        )

    requested = {normalize_time_token(value) for value in requested_times if normalize_time_token(value) is not None}
    if not requested:
        requested = set()

    weighted_sums: dict[tuple[str, float], float] = defaultdict(float)
    weight_sums: dict[tuple[str, float], float] = defaultdict(float)
    time_tokens_seen: set[float] = set()

    with raw_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            time_token = normalize_time_token(row.get("time_s"))
            if time_token is None:
                continue
            if requested and time_token not in requested:
                continue
            span_name = str(row.get("span_name", ""))
            value = first_finite(
                row.get("bulk_temp_flow_weighted_k"),
                row.get("bulk_temp_area_avg_k"),
                row.get("bulk_temp_union_area_avg_k"),
            )
            if value is None:
                continue
            weight = first_finite(
                row.get("cross_section_chosen_region_positive_mass_flux_kg_s"),
                row.get("cross_section_area_m2"),
                1.0,
            )
            if weight is None or weight <= 0.0:
                weight = 1.0
            time_tokens_seen.add(time_token)
            for region_name, members in REGION_MEMBERS.items():
                if span_name not in members:
                    continue
                key = (region_name, time_token)
                weighted_sums[key] += float(value) * float(weight)
                weight_sums[key] += float(weight)

    requested_or_seen = sorted(requested or time_tokens_seen)
    temperatures: dict[str, float | None] = {}
    coverage_counts: dict[str, int] = {}
    for region_name in REGION_MEMBERS:
        region_values: list[float] = []
        for time_token in requested_or_seen:
            key = (region_name, time_token)
            total_weight = weight_sums.get(key, 0.0)
            if total_weight <= 0.0:
                continue
            region_values.append(weighted_sums[key] / total_weight)
        temperatures[region_name] = mean_or_none(region_values)
        coverage_counts[region_name] = len(region_values)

    requested_count = len(requested_or_seen)
    if requested_count == 0:
        coverage_status = "no_requested_times"
    elif min(coverage_counts.values(), default=0) == requested_count:
        coverage_status = "complete"
    else:
        coverage_status = "partial"

    return (
        temperatures,
        {
            "source": relative_to_workspace(raw_path),
            "coverage_status": coverage_status,
            "time_count": requested_count,
            "region_coverage_counts": coverage_counts,
            "requested_times_s": requested_or_seen,
            "weighting_note": "positive_mass_flux_else_area",
            "value_note": "bulk_temp_flow_weighted_k preferred, then area-average bulk temperature",
        },
    )


def format_float(value: object, digits: int = 2) -> str:
    numeric = safe_float(value)
    if numeric is None or not math.isfinite(numeric):
        return ""
    return f"{numeric:.{digits}f}"


def compute_dashboard_row(
    metadata_row: dict[str, str],
    heat_latest_row: dict[str, str],
    heat_window_row: dict[str, str],
    package_root: Path,
    package_summary: dict[str, Any],
    region_temperatures: dict[str, float | None],
    temperature_meta: dict[str, Any],
) -> dict[str, Any]:
    source_id = metadata_row["source_id"]
    heater_power = safe_float(metadata_row.get("heater_power_W"))
    cooling_power = safe_float(metadata_row.get("cooling_power_W"))
    requested_times = [float(value) for value in package_summary.get("requested_times_s", [])]
    late_start = min(requested_times) if requested_times else None
    late_end = max(requested_times) if requested_times else None
    branch_values = [region_temperatures.get(name) for name in BRANCH_REGION_ORDER]
    finite_branch_values = [value for value in branch_values if value is not None and math.isfinite(value)]
    span_values = [region_temperatures.get(name) for name in SPAN_REGION_ORDER]
    finite_span_values = [value for value in span_values if value is not None and math.isfinite(value)]

    heater_temp = region_temperatures.get("heater")
    cooler_temp = region_temperatures.get("cooler")
    downcomer_temp = region_temperatures.get("downcomer")
    upcomer_temp = region_temperatures.get("upcomer")
    probe_temp = safe_float(metadata_row.get("probe_T_avg_K"))
    t_init = safe_float(metadata_row.get("T_init_K"))

    row: dict[str, Any] = {
        "source_id": source_id,
        "display_label": display_label(metadata_row),
        "base_case_id": metadata_row.get("base_case_id", ""),
        "variant_label": metadata_row.get("variant_label", ""),
        "fluid_family": family_from_metadata(metadata_row),
        "fluid_model": metadata_row.get("fluid", ""),
        "turbulence_model": metadata_row.get("turbulence_model", ""),
        "run_status": metadata_row.get("run_status", ""),
        "comparison_ready": metadata_row.get("comparison_ready", ""),
        "convergence_reached": metadata_row.get("convergence_reached", ""),
        "final_time_s": metadata_row.get("final_time", ""),
        "latest_processor_time_s": metadata_row.get("latest_processor_time", ""),
        "T_init_K": metadata_row.get("T_init_K", ""),
        "probe_T_avg_K": metadata_row.get("probe_T_avg_K", ""),
        "probe_minus_t_init_k": (
            float(probe_temp - t_init) if probe_temp is not None and t_init is not None else ""
        ),
        "heater_power_W": metadata_row.get("heater_power_W", ""),
        "cooling_power_W": metadata_row.get("cooling_power_W", ""),
        "heater_to_cooling_power_ratio": ratio_or_none(heater_power, cooling_power),
        "three_d_outer_insulation_thickness_in": metadata_row.get("three_d_outer_insulation_thickness_in", ""),
        "cooler_h_W_m2K": metadata_row.get("cooler_h_W_m2K", ""),
        "three_d_loss_bc_summary": metadata_row.get("three_d_loss_bc_summary", ""),
        "three_d_radiation_summary": metadata_row.get("three_d_radiation_summary", ""),
        "mu_coeff_summary": metadata_row.get("mu_coeff_summary", ""),
        "kappa_coeff_summary": metadata_row.get("kappa_coeff_summary", ""),
        "cp_model_summary": metadata_row.get("cp_model_summary", ""),
        "rho_model_summary": metadata_row.get("rho_model_summary", ""),
        "mdot_mean_abs_kg_s": metadata_row.get("mdot_mean_abs_kg_s", ""),
        "initial_hydraulic_state_status": "not_published_in_case_metadata_index",
        "late_window_time_start_s": late_start if late_start is not None else "",
        "late_window_time_end_s": late_end if late_end is not None else "",
        "late_window_time_count": len(requested_times),
        "temperature_source_root": temperature_meta.get("source", ""),
        "temperature_coverage_status": temperature_meta.get("coverage_status", ""),
        "temperature_weighting_note": temperature_meta.get("weighting_note", ""),
        "package_root": relative_to_workspace(package_root),
        "package_summary_path": relative_to_workspace(package_root / "summary.json"),
        "heat_latest_source": relative_to_workspace(HEAT_LATEST_CSV),
        "heat_window_source": relative_to_workspace(HEAT_WINDOW_CSV),
        "ambient_proxy_w_mean": heat_window_row.get("ambient_proxy_w_mean", ""),
        "cooling_branch_total_removal_w_mean": heat_window_row.get("cooling_branch_total_removal_w_mean", ""),
        "section_junctions_net_q_w_mean": heat_window_row.get("section_junctions_net_q_w_mean", ""),
        "net_total_q_w_mean": heat_window_row.get("net_total_q_w_mean", ""),
        "ambient_proxy_w_latest": heat_latest_row.get("ambient_proxy_w", ""),
        "cooling_branch_total_removal_w_latest": heat_latest_row.get("cooling_branch_total_removal_w", ""),
        "section_junctions_net_q_w_latest": heat_latest_row.get("section_junctions_net_q_w", ""),
        "net_total_q_w_latest": heat_latest_row.get("net_total_q_w", ""),
        "ambient_proxy_fraction_of_heater": ratio_or_none(
            heat_window_row.get("ambient_proxy_w_mean"),
            heater_power,
        ),
        "cooling_removal_fraction_of_heater": ratio_or_none(
            heat_window_row.get("cooling_branch_total_removal_w_mean"),
            heater_power,
        ),
        "junction_loss_fraction_of_heater": ratio_or_none(
            abs(safe_float(heat_window_row.get("section_junctions_net_q_w_mean")) or 0.0),
            heater_power,
        ),
        "net_heat_imbalance_fraction_of_heater": ratio_or_none(
            heat_window_row.get("net_total_q_w_mean"),
            heater_power,
        ),
        "heater_to_cooler_bulk_delta_k": (
            float(heater_temp - cooler_temp)
            if heater_temp is not None and cooler_temp is not None
            else ""
        ),
        "downcomer_to_upcomer_bulk_delta_k": (
            float(downcomer_temp - upcomer_temp)
            if downcomer_temp is not None and upcomer_temp is not None
            else ""
        ),
        "max_branch_temp_delta_k": (
            float(max(finite_branch_values) - min(finite_branch_values))
            if finite_branch_values
            else ""
        ),
        "max_span_temp_delta_k": (
            float(max(finite_span_values) - min(finite_span_values))
            if finite_span_values
            else ""
        ),
    }

    for region_name in SPAN_REGION_ORDER + BRANCH_REGION_ORDER:
        row[f"temp_{region_name}_bulk_k"] = region_temperatures.get(region_name, "")
    return row


def candidate_input_row(dashboard_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": dashboard_row["source_id"],
        "display_label": dashboard_row["display_label"],
        "base_case_id": dashboard_row["base_case_id"],
        "variant_label": dashboard_row["variant_label"],
        "fluid_family": dashboard_row["fluid_family"],
        "run_status": dashboard_row["run_status"],
        "comparison_ready": dashboard_row["comparison_ready"],
        "heater_power_W": dashboard_row["heater_power_W"],
        "cooling_power_W": dashboard_row["cooling_power_W"],
        "heater_to_cooling_power_ratio": dashboard_row["heater_to_cooling_power_ratio"],
        "T_init_K": dashboard_row["T_init_K"],
        "probe_T_avg_K": dashboard_row["probe_T_avg_K"],
        "probe_minus_t_init_k": dashboard_row["probe_minus_t_init_k"],
        "mdot_mean_abs_kg_s": dashboard_row["mdot_mean_abs_kg_s"],
        "three_d_outer_insulation_thickness_in": dashboard_row["three_d_outer_insulation_thickness_in"],
        "cooler_h_W_m2K": dashboard_row["cooler_h_W_m2K"],
        "late_window_time_start_s": dashboard_row["late_window_time_start_s"],
        "late_window_time_end_s": dashboard_row["late_window_time_end_s"],
        "late_window_time_count": dashboard_row["late_window_time_count"],
        "temp_heater_bulk_k": dashboard_row["temp_heater_bulk_k"],
        "temp_downcomer_bulk_k": dashboard_row["temp_downcomer_bulk_k"],
        "temp_upcomer_bulk_k": dashboard_row["temp_upcomer_bulk_k"],
        "temp_cooler_bulk_k": dashboard_row["temp_cooler_bulk_k"],
        "temp_test_section_span_bulk_k": dashboard_row["temp_test_section_span_bulk_k"],
        "heater_to_cooler_bulk_delta_k": dashboard_row["heater_to_cooler_bulk_delta_k"],
        "downcomer_to_upcomer_bulk_delta_k": dashboard_row["downcomer_to_upcomer_bulk_delta_k"],
        "max_branch_temp_delta_k": dashboard_row["max_branch_temp_delta_k"],
        "max_span_temp_delta_k": dashboard_row["max_span_temp_delta_k"],
        "ambient_proxy_fraction_of_heater": dashboard_row["ambient_proxy_fraction_of_heater"],
        "cooling_removal_fraction_of_heater": dashboard_row["cooling_removal_fraction_of_heater"],
        "junction_loss_fraction_of_heater": dashboard_row["junction_loss_fraction_of_heater"],
        "net_heat_imbalance_fraction_of_heater": dashboard_row["net_heat_imbalance_fraction_of_heater"],
        "candidate_control_note": (
            "Treat these as lower-dimensional screening inputs for later effective friction/HTC correlation work, "
            "not as final nondimensional groups."
        ),
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body_lines = []
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                values.append(format_float(value))
            else:
                values.append(str(value))
        body_lines.append("| " + " | ".join(values) + " |")
    return "\n".join([header, divider, *body_lines])


def summarize_family(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["- No cases were available in this family slice."]
    insulation = [safe_float(row.get("three_d_outer_insulation_thickness_in")) for row in rows]
    insulation = [value for value in insulation if value is not None and math.isfinite(value)]
    max_branch_delta = [safe_float(row.get("max_branch_temp_delta_k")) for row in rows]
    max_branch_delta = [value for value in max_branch_delta if value is not None and math.isfinite(value)]
    ambient_fraction = [safe_float(row.get("ambient_proxy_fraction_of_heater")) for row in rows]
    ambient_fraction = [value for value in ambient_fraction if value is not None and math.isfinite(value)]
    notes: list[str] = []
    if insulation:
        notes.append(
            f"- Outer insulation spans `{min(insulation):.2f}` to `{max(insulation):.2f}` in across this family."
        )
    if max_branch_delta:
        notes.append(
            f"- The late-window max branch bulk-temperature spread spans `{min(max_branch_delta):.2f}` to `{max(max_branch_delta):.2f}` K."
        )
    if ambient_fraction:
        notes.append(
            f"- The late-window ambient-proxy fraction spans `{min(ambient_fraction):.3f}` to `{max(ambient_fraction):.3f}` of heater power."
        )
    hottest = max(
        rows,
        key=lambda item: safe_float(item.get("probe_T_avg_K")) if safe_float(item.get("probe_T_avg_K")) is not None else -1.0,
    )
    notes.append(
        f"- Highest reported case-average probe temperature is `{hottest['display_label']}` at `{format_float(hottest.get('probe_T_avg_K'))}` K."
    )
    return notes


def plot_family_branch_dashboard(output_root: Path, family: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {}
    labels = [row["display_label"] for row in rows]
    x_values = list(range(len(rows)))

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    for branch_name in BRANCH_REGION_ORDER:
        axes[0].plot(
            x_values,
            [safe_float(row.get(f"temp_{branch_name}_bulk_k")) for row in rows],
            marker="o",
            linewidth=1.7,
            color=BRANCH_COLORS[branch_name],
            label=REGION_LABELS[branch_name],
        )
    axes[0].plot(
        x_values,
        [safe_float(row.get("probe_T_avg_K")) for row in rows],
        marker="s",
        linewidth=1.3,
        linestyle="--",
        color="#111827",
        label="Case-average probe T",
    )
    axes[0].plot(
        x_values,
        [safe_float(row.get("T_init_K")) for row in rows],
        marker="^",
        linewidth=1.2,
        linestyle=":",
        color="#6b7280",
        label="Initial T",
    )
    axes[0].set_ylabel("Temperature [K]")
    axes[0].set_title(f"{family.title()} branch-temperature dashboard")
    axes[0].legend(loc="best", ncol=2)
    axes[0].grid(alpha=0.25, linewidth=0.5)

    axes[1].bar(
        [value - 0.18 for value in x_values],
        [safe_float(row.get("heater_power_W")) or 0.0 for row in rows],
        width=0.36,
        color="#bc3908",
        label="Heater power [W]",
    )
    axes[1].bar(
        [value + 0.18 for value in x_values],
        [safe_float(row.get("cooling_power_W")) or 0.0 for row in rows],
        width=0.36,
        color="#1d4ed8",
        label="Cooling power [W]",
    )
    axis_secondary = axes[1].twinx()
    axis_secondary.plot(
        x_values,
        [safe_float(row.get("three_d_outer_insulation_thickness_in")) for row in rows],
        color="#0b6e4f",
        marker="D",
        linewidth=1.5,
        label="Outer insulation [in]",
    )
    axis_secondary.plot(
        x_values,
        [safe_float(row.get("max_branch_temp_delta_k")) for row in rows],
        color="#7c3aed",
        marker="o",
        linewidth=1.4,
        linestyle="--",
        label="Max branch delta [K]",
    )
    axes[1].set_ylabel("Power [W]")
    axis_secondary.set_ylabel("Insulation [in] / delta T [K]")
    axes[1].grid(alpha=0.25, linewidth=0.5)
    axes[1].set_xticks(x_values)
    axes[1].set_xticklabels(labels, rotation=20, ha="right")

    handles_left, labels_left = axes[1].get_legend_handles_labels()
    handles_right, labels_right = axis_secondary.get_legend_handles_labels()
    axes[1].legend(handles_left + handles_right, labels_left + labels_right, loc="best", ncol=2)
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_root, f"{family}_dashboard_overview", dpi=220)


def build_readme(
    output_root: Path,
    manifest_payload: dict[str, Any],
    salt_rows: list[dict[str, Any]],
    water_rows: list[dict[str, Any]],
    figure_paths: dict[str, dict[str, str]],
) -> None:
    salt_table = markdown_table(
        salt_rows,
        [
            ("display_label", "Case"),
            ("run_status", "Run status"),
            ("T_init_K", "T_init [K]"),
            ("heater_power_W", "Heater [W]"),
            ("cooling_power_W", "Cooling [W]"),
            ("three_d_outer_insulation_thickness_in", "Insulation [in]"),
            ("mdot_mean_abs_kg_s", "|mdot| [kg/s]"),
            ("max_branch_temp_delta_k", "Max branch dT [K]"),
        ],
    )
    water_table = markdown_table(
        water_rows,
        [
            ("display_label", "Case"),
            ("run_status", "Run status"),
            ("T_init_K", "T_init [K]"),
            ("heater_power_W", "Heater [W]"),
            ("cooling_power_W", "Cooling [W]"),
            ("three_d_outer_insulation_thickness_in", "Insulation [in]"),
            ("mdot_mean_abs_kg_s", "|mdot| [kg/s]"),
            ("max_branch_temp_delta_k", "Max branch dT [K]"),
        ],
    )
    readme_lines = [
        "# Ethan Nondimensional Dashboard Package",
        "",
        f"Generated: `{manifest_payload['generated_at']}`",
        "",
        "## Purpose",
        "",
        "This package is a first dashboard and quick-spec layer for later reduced-order correlation work on Ethan CFD runs.",
        "It separates water and salt families, inventories the starting and boundary conditions already present in the repo,",
        "publishes late-window bulk-temperature summaries for the main loop regions, and assembles candidate lower-dimensional inputs",
        "for later effective friction-factor and effective HTC correlation work.",
        "",
        "## Theory, semantics, and scope boundaries",
        "",
        "- Effective friction factor is treated here as a later derived loop/leg indicator from CFD support data, not as a primitive solver input.",
        "- Effective HTC, `UA'`, and related thermal-resistance quantities are treated as support-gated effective transfer indicators rather than intrinsic local closure coefficients.",
        "- The cooler metadata field `cooler_h_W_m2K` is retained as a setup descriptor because it is useful for screening, but the readable 3D `0/T` implementation is still a fixed-`Q` cooling sink and not a clean resolved cooler-side convective coefficient.",
        "- The temperature dashboard values are late-window bulk-fluid summaries built from retained cut-plane bulk-temperature bins, not instantaneous one-timestep snapshots.",
        "- Initial hydraulic state is not cleanly published in the canonical Ethan metadata index, so this package records that gap explicitly and uses late-window circulation strength (`mdot_mean_abs_kg_s`) as the reusable hydraulic context field.",
        "",
        "## Data sources",
        "",
        f"- Metadata index: `{relative_to_workspace(METADATA_CSV)}`",
        f"- Heat audit latest/late-window tables: `{relative_to_workspace(HEAT_LATEST_CSV)}` and `{relative_to_workspace(HEAT_WINDOW_CSV)}`",
        f"- All-runs field-transport campaign provenance: `{relative_to_workspace(FIELD_TRANSPORT_README)}`",
        f"- Boundary-modeling caveats: `{relative_to_workspace(BOUNDARY_REPORT_README)}`",
        "- Late-window temperature reductions come from the June 15 live case-analysis package roots listed in `summary.json` and the import manifest.",
        "",
        "## Temperature method",
        "",
        "- Span and branch temperatures use the retained cut-plane bulk-temperature samples in `raw_extraction/bulk_cross_section_temperature_samples.csv` from the selected June 15 live case-analysis package for each case.",
        "- The preferred bulk metric is `bulk_temp_flow_weighted_k`; if it is unavailable for a row, the reduction falls back to area-average bulk temperature.",
        "- Within each retained time, rows are weighted by positive aligned mass flux when available, otherwise by cut-plane area.",
        "- The published temperature is then the mean across the retained late-window times advertised by that package's `summary.json`.",
        "- The derived branches are: heater=`lower_leg`, downcomer=`right_leg`, upcomer=`left_lower_leg + test_section_span + left_upper_leg`, cooler=`upper_leg`.",
        "",
        "## Salt dashboard",
        "",
        salt_table,
        "",
        *summarize_family(salt_rows),
        "",
        "## Water dashboard",
        "",
        water_table,
        "",
        *summarize_family(water_rows),
        "",
        "## Artifacts",
        "",
        f"- `salt_dashboard.csv`: `{relative_to_workspace(output_root / 'salt_dashboard.csv')}`",
        f"- `water_dashboard.csv`: `{relative_to_workspace(output_root / 'water_dashboard.csv')}`",
        f"- `salt_candidate_correlation_inputs.csv`: `{relative_to_workspace(output_root / 'salt_candidate_correlation_inputs.csv')}`",
        f"- `water_candidate_correlation_inputs.csv`: `{relative_to_workspace(output_root / 'water_candidate_correlation_inputs.csv')}`",
        f"- `summary.json`: `{relative_to_workspace(output_root / 'summary.json')}`",
    ]
    for family, paths in figure_paths.items():
        if not paths:
            continue
        readme_lines.append(f"- `{family}_dashboard_overview`: `{relative_to_workspace(Path(paths['png']))}`")
    readme_lines.extend(
        [
            "",
            "## Recommended next derived quantities",
            "",
            "- Add case- and leg-level effective friction scalars once the separate friction-factor/minor-loss work is ready.",
            "- Add late-temperature fluid-property snapshots and family-specific Reynolds/Prandtl-style groups only after deciding the exact property-evaluation convention to use.",
            "- Keep salt and water as separate fitting families unless a later audit shows that a shared nondimensionalization truly collapses the two sets.",
        ]
    )
    (output_root / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_root = ensure_dir(Path(args.output_dir))
    ensure_dir(TMP_SMOKE_ROOT)

    metadata_rows = [
        row
        for row in load_csv_rows(METADATA_CSV)
        if row.get("source_id")
        and row.get("source_id") != "modern_runs_campaign_inventory_2026-06-01"
        and row.get("source_id") in SOURCE_ID_ORDER
    ]
    if args.source_ids:
        requested_ids = set(args.source_ids)
        metadata_rows = [row for row in metadata_rows if row["source_id"] in requested_ids]
    metadata_rows.sort(key=lambda row: order_index(row["source_id"]))

    heat_latest_map = csv_map(load_csv_rows(HEAT_LATEST_CSV), "source_id")
    heat_window_map = csv_map(load_csv_rows(HEAT_WINDOW_CSV), "source_id")

    dashboard_rows: list[dict[str, Any]] = []
    case_input_records: list[dict[str, Any]] = []
    missing_cases: list[dict[str, Any]] = []

    for metadata_row in metadata_rows:
        source_id = metadata_row["source_id"]
        package_root = resolve_case_analysis_root(source_id)
        if package_root is None:
            missing_cases.append(
                {
                    "source_id": source_id,
                    "reason": "case_analysis_package_not_found",
                }
            )
            continue
        package_summary = load_json(package_root / "summary.json")
        requested_times = [float(value) for value in package_summary.get("requested_times_s", [])]
        region_temperatures, temperature_meta = load_region_temperatures(package_root, requested_times)
        dashboard_row = compute_dashboard_row(
            metadata_row=metadata_row,
            heat_latest_row=heat_latest_map.get(source_id, {}),
            heat_window_row=heat_window_map.get(source_id, {}),
            package_root=package_root,
            package_summary=package_summary,
            region_temperatures=region_temperatures,
            temperature_meta=temperature_meta,
        )
        dashboard_rows.append(dashboard_row)
        case_input_records.append(
            {
                "source_id": source_id,
                "package_root": relative_to_workspace(package_root),
                "package_summary_path": relative_to_workspace(package_root / "summary.json"),
                "requested_times_s": requested_times,
                "temperature_source": temperature_meta,
            }
        )

    dashboard_rows.sort(key=lambda row: order_index(str(row["source_id"])))
    salt_rows = [row for row in dashboard_rows if row["fluid_family"] == "salt"]
    water_rows = [row for row in dashboard_rows if row["fluid_family"] == "water"]

    csv_dump(output_root / "salt_dashboard.csv", list(salt_rows[0].keys()) if salt_rows else [], salt_rows)
    csv_dump(output_root / "water_dashboard.csv", list(water_rows[0].keys()) if water_rows else [], water_rows)

    salt_candidate_rows = [candidate_input_row(row) for row in salt_rows]
    water_candidate_rows = [candidate_input_row(row) for row in water_rows]
    csv_dump(
        output_root / "salt_candidate_correlation_inputs.csv",
        list(salt_candidate_rows[0].keys()) if salt_candidate_rows else [],
        salt_candidate_rows,
    )
    csv_dump(
        output_root / "water_candidate_correlation_inputs.csv",
        list(water_candidate_rows[0].keys()) if water_candidate_rows else [],
        water_candidate_rows,
    )

    figure_paths = {
        "salt": plot_family_branch_dashboard(output_root, "salt", salt_rows),
        "water": plot_family_branch_dashboard(output_root, "water", water_rows),
    }

    manifest_payload = {
        "generated_at": iso_timestamp(),
        "script_path": relative_to_workspace(Path(__file__)),
        "output_root": relative_to_workspace(output_root),
        "dashboard_case_count": len(dashboard_rows),
        "family_case_counts": {
            "salt": len(salt_rows),
            "water": len(water_rows),
        },
        "input_paths": {
            "metadata_csv": relative_to_workspace(METADATA_CSV),
            "heat_latest_csv": relative_to_workspace(HEAT_LATEST_CSV),
            "heat_window_csv": relative_to_workspace(HEAT_WINDOW_CSV),
            "field_transport_readme": relative_to_workspace(FIELD_TRANSPORT_README),
            "boundary_report_readme": relative_to_workspace(BOUNDARY_REPORT_README),
        },
        "assumptions": [
            "Water and salt remain separate dashboard/correlation-screening families.",
            "Branch temperatures are late-window means over retained cut-plane bins, not instantaneous final-timestep values.",
            "Initial hydraulic state is not published cleanly enough in the canonical metadata index, so the dashboard records that gap and carries late-window |mdot| as the hydraulic context field.",
            "Metadata cooler h is retained as a screening descriptor even though the readable 3D `0/T` implementation applies fixed-Q cooling sinks.",
            "Candidate correlation inputs are not final nondimensional groups; they are quick screening descriptors for the next reduced-order pass.",
        ],
        "case_inputs": case_input_records,
        "missing_cases": missing_cases,
        "artifacts": {
            "salt_dashboard_csv": relative_to_workspace(output_root / "salt_dashboard.csv"),
            "water_dashboard_csv": relative_to_workspace(output_root / "water_dashboard.csv"),
            "salt_candidate_inputs_csv": relative_to_workspace(output_root / "salt_candidate_correlation_inputs.csv"),
            "water_candidate_inputs_csv": relative_to_workspace(output_root / "water_candidate_correlation_inputs.csv"),
            "summary_json": relative_to_workspace(output_root / "summary.json"),
            "readme_md": relative_to_workspace(output_root / "README.md"),
            "figures": {
                family: {fmt: relative_to_workspace(Path(path)) for fmt, path in paths.items()}
                for family, paths in figure_paths.items()
            },
        },
    }
    json_dump(output_root / "summary.json", manifest_payload)
    json_dump(Path(args.manifest_path), manifest_payload)
    build_readme(output_root, manifest_payload, salt_rows, water_rows, figure_paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
