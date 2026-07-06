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
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, save_matplotlib_figure, safe_float  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-15_ethan_field_transport_campaign"
DEFAULT_CASE_ORDER = (
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
)
CASE_STYLE = {
    "val_salt_test_2_coarse_mesh_laminar": ("Salt 2 val", "#111827"),
    "viscosity_screening_salt_test_1_jin_coarse_mesh": ("Salt 1 Jin", "#0b6e4f"),
    "viscosity_screening_salt_test_1_kirst_coarse_mesh": ("Salt 1 Kirst", "#7c3aed"),
    "viscosity_screening_salt_test_2_jin_coarse_mesh": ("Salt 2 Jin", "#0f766e"),
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": ("Salt 2 Kirst", "#bc3908"),
    "viscosity_screening_salt_test_3_jin_coarse_mesh": ("Salt 3 Jin", "#1d4ed8"),
    "viscosity_screening_salt_test_3_kirst_coarse_mesh": ("Salt 3 Kirst", "#be123c"),
    "viscosity_screening_salt_test_4_jin_coarse_mesh": ("Salt 4 Jin", "#a16207"),
    "viscosity_screening_salt_test_4_kirst_coarse_mesh": ("Salt 4 Kirst", "#b45309"),
    # Water cases are plotted after the Salt-family set so the final all-runs
    # report preserves the already-established salt rollout ordering while still
    # giving each validation case a stable label/color identity.
    "val_water_test_1_coarse_mesh_laminar": ("Water 1", "#2563eb"),
    "val_water_test_2_coarse_mesh_laminar": ("Water 2", "#0891b2"),
    "val_water_test_3_coarse_mesh_laminar": ("Water 3", "#0f766e"),
    "val_water_test_4_coarse_mesh_laminar": ("Water 4", "#4338ca"),
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a cross-case field-transport comparison package from per-case "
            "analysis packages that publish azimuthal transport and streamwise heat-loss outputs."
        )
    )
    parser.add_argument(
        "--package-dir",
        action="append",
        required=True,
        help="Per-case package directory containing summary.json and field-transport CSV outputs.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sort_key(source_id: str) -> int:
    try:
        return DEFAULT_CASE_ORDER.index(source_id)
    except ValueError:
        return len(DEFAULT_CASE_ORDER)


def case_label(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[0]


def case_color(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[1]


def nanmean(values: list[float]) -> float:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not finite:
        return math.nan
    return float(np.mean(np.array(finite, dtype=float)))


def load_streamwise_heat_rows(path: Path, source_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "source_id": source_id,
                "case_label": case_label(source_id),
                "loop_s_mid_m": float(row["loop_s_mid_m"]),
                "loop_s_fraction": float(row["loop_s_fraction"]),
                "mean_wall_heat_w": float(row["mean_wall_heat_w"]),
                "mean_wall_heat_abs_w": float(row["mean_wall_heat_abs_w"]),
                "mean_wall_heat_per_length_w_m": float(row["mean_wall_heat_per_length_w_m"]),
                "mean_wall_heat_abs_per_length_w_m": float(row["mean_wall_heat_abs_per_length_w_m"]),
                "mean_cumulative_wall_heat_w": float(row["mean_cumulative_wall_heat_w"]),
                "mean_cumulative_wall_heat_abs_w": float(row["mean_cumulative_wall_heat_abs_w"]),
            }
        )
    return rows


def load_grouped_heat_rows(path: Path, source_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "source_id": source_id,
                "case_label": case_label(source_id),
                "thermal_role_group": str(row["thermal_role_group"]),
                "loop_s_mid_m": float(row["loop_s_mid_m"]),
                "loop_s_fraction": float(row["loop_s_fraction"]),
                "mean_wall_heat_per_length_w_m": float(row["mean_wall_heat_per_length_w_m"]),
                "mean_cumulative_wall_heat_w": float(row["mean_cumulative_wall_heat_w"]),
            }
        )
    return rows


def load_azimuthal_rows(path: Path, source_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "source_id": source_id,
                "case_label": case_label(source_id),
                "span_name": str(row["span_name"]),
                "streamwise_bin_index": int(row["streamwise_bin_index"]),
                "theta_bin_index": int(row["theta_bin_index"]),
                "loop_s_mid_m": float(row["loop_s_mid_m"]),
                "loop_s_fraction": float(row["loop_s_fraction"]),
                "mean_area_m2": safe_float(row.get("mean_area_m2"), math.nan),
                "mean_wall_heat_flux_w_m2": safe_float(row.get("mean_wall_heat_flux_w_m2"), math.nan),
                "mean_fanning_cf_shear": safe_float(row.get("mean_fanning_cf_shear"), math.nan),
                "mean_darcy_f_shear": safe_float(row.get("mean_darcy_f_shear"), math.nan),
            }
        )
    return rows


def load_branch_thermal_rows(path: Path, source_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "source_id": source_id,
                "case_label": case_label(source_id),
                "branch_name": str(row["branch_name"]),
                "branch_type": str(row["branch_type"]),
                "component_spans": str(row["component_spans"]),
                "branch_total_length_m": safe_float(row.get("branch_total_length_m"), math.nan),
                "usable_row_count": int(row["usable_row_count"]),
                "masked_row_count": int(row["masked_row_count"]),
                "warning_fraction": safe_float(row.get("warning_fraction"), math.nan),
                "thermal_warning_fraction": safe_float(row.get("thermal_warning_fraction"), math.nan),
                "usable_fraction": (
                    float(int(row["usable_row_count"]) / max(int(row["total_row_count"]), 1))
                    if row.get("total_row_count")
                    else math.nan
                ),
                "mean_mdot_mean_abs_kg_s": safe_float(row.get("mean_mdot_mean_abs_kg_s"), math.nan),
                "mean_bulk_positive_mass_flux_kg_s": safe_float(
                    row.get("mean_bulk_positive_mass_flux_kg_s"),
                    math.nan,
                ),
                "min_bulk_positive_mass_flux_kg_s": safe_float(
                    row.get("min_bulk_positive_mass_flux_kg_s"),
                    math.nan,
                ),
                "mean_t_wall_area_avg_k": safe_float(row.get("mean_t_wall_area_avg_k"), math.nan),
                "mean_bulk_temp_fluid_area_avg_k": safe_float(row.get("mean_bulk_temp_fluid_area_avg_k"), math.nan),
                "mean_bulk_temp_area_weighted_k": safe_float(row.get("mean_bulk_temp_area_weighted_k"), math.nan),
                "mean_bulk_minus_wall_temp_k": safe_float(row.get("mean_bulk_minus_wall_temp_k"), math.nan),
                "mean_abs_bulk_minus_wall_temp_k": safe_float(
                    row.get("mean_abs_bulk_minus_wall_temp_k"),
                    math.nan,
                ),
                "min_abs_bulk_minus_wall_temp_k": safe_float(
                    row.get("min_abs_bulk_minus_wall_temp_k"),
                    math.nan,
                ),
                "mean_area_ratio_to_reference": safe_float(
                    row.get("mean_area_ratio_to_reference"),
                    math.nan,
                ),
                "max_area_ratio_to_reference": safe_float(
                    row.get("max_area_ratio_to_reference"),
                    math.nan,
                ),
                "mean_wall_heat_per_length_w_m": safe_float(row.get("mean_wall_heat_per_length_w_m"), math.nan),
                "mean_wall_heatflux_area_avg_w_m2": safe_float(row.get("mean_wall_heatflux_area_avg_w_m2"), math.nan),
                "mean_effective_htc_w_m2_k": safe_float(row.get("mean_effective_htc_w_m2_k"), math.nan),
                "mean_effective_ua_per_m_w_m_k": safe_float(row.get("mean_effective_ua_per_m_w_m_k"), math.nan),
                "mean_effective_thermal_resistance_k_m_w": safe_float(
                    row.get("mean_effective_thermal_resistance_k_m_w"),
                    math.nan,
                ),
            }
        )
    return rows


def collapse_azimuthal_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["source_id"]), str(row["span_name"]), int(row["streamwise_bin_index"]))].append(row)
    output_rows: list[dict[str, Any]] = []
    for key, payload in sorted(grouped.items(), key=lambda item: (sort_key(item[0][0]), nanmean([float(row["loop_s_mid_m"]) for row in item[1]]))):
        source_id, span_name, streamwise_bin_index = key
        weights = [float(row["mean_area_m2"]) for row in payload if math.isfinite(float(row["mean_area_m2"]))]
        total_weight = sum(weights)

        def weighted_mean(field_name: str) -> float:
            numer = 0.0
            denom = 0.0
            for row in payload:
                value = safe_float(row.get(field_name), math.nan)
                weight = safe_float(row.get("mean_area_m2"), math.nan)
                if value is None or weight is None or not math.isfinite(value) or not math.isfinite(weight):
                    continue
                numer += float(value) * float(weight)
                denom += float(weight)
            return float(numer / denom) if denom > 0.0 else math.nan

        first = payload[0]
        output_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label(source_id),
                "span_name": span_name,
                "streamwise_bin_index": int(streamwise_bin_index),
                "loop_s_mid_m": float(first["loop_s_mid_m"]),
                "loop_s_fraction": float(first["loop_s_fraction"]),
                "theta_sample_count": len(payload),
                "total_area_m2": float(total_weight),
                "circumferential_mean_wall_heat_flux_w_m2": weighted_mean("mean_wall_heat_flux_w_m2"),
                "circumferential_mean_fanning_cf_shear": weighted_mean("mean_fanning_cf_shear"),
                "circumferential_mean_darcy_f_shear": weighted_mean("mean_darcy_f_shear"),
            }
        )
    return output_rows


def plot_heat_loss_comparison(output_dir: Path, total_rows: list[dict[str, Any]], grouped_rows: list[dict[str, Any]]) -> dict[str, str]:
    grouped_total: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_role: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in total_rows:
        grouped_total[str(row["source_id"])].append(row)
    for row in grouped_rows:
        grouped_role[(str(row["source_id"]), str(row["thermal_role_group"]))].append(row)

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    for source_id in sorted(grouped_total, key=sort_key):
        payload = sorted(grouped_total[source_id], key=lambda row: float(row["loop_s_mid_m"]))
        x = [float(row["loop_s_mid_m"]) for row in payload]
        axes[0].plot(x, [float(row["mean_wall_heat_per_length_w_m"]) for row in payload], color=case_color(source_id), linewidth=2.0, label=f"{case_label(source_id)} total")
        axes[1].plot(x, [float(row["mean_cumulative_wall_heat_w"]) for row in payload], color=case_color(source_id), linewidth=2.0, label=f"{case_label(source_id)} total")
        for role_name, style in (("parasitic_loss", ":"), ("intended_transfer", "--")):
            role_payload = sorted(grouped_role.get((source_id, role_name), []), key=lambda row: float(row["loop_s_mid_m"]))
            if not role_payload:
                continue
            role_x = [float(row["loop_s_mid_m"]) for row in role_payload]
            axes[0].plot(role_x, [float(row["mean_wall_heat_per_length_w_m"]) for row in role_payload], color=case_color(source_id), linewidth=1.2, linestyle=style)
            axes[1].plot(role_x, [float(row["mean_cumulative_wall_heat_w"]) for row in role_payload], color=case_color(source_id), linewidth=1.2, linestyle=style)
    axes[0].axhline(0.0, color="#9ca3af", linewidth=0.9)
    axes[1].axhline(0.0, color="#9ca3af", linewidth=0.9)
    axes[0].set_ylabel("q' [W/m]")
    axes[1].set_ylabel("Cumulative Q [W]")
    axes[1].set_xlabel("Distance along loop [m]")
    axes[0].set_title("Cross-case streamwise heat-loss comparison")
    axes[1].set_title("Cross-case cumulative heat-loss comparison")
    axes[0].legend(loc="best", fontsize=8)
    axes[1].legend(loc="best", fontsize=8)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "field_transport_heat_loss_comparison", dpi=220)
    plt.close(fig)
    return paths


def plot_azimuthal_transport_comparison(output_dir: Path, rows: list[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["source_id"])].append(row)
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    for source_id in sorted(grouped, key=sort_key):
        payload = sorted(grouped[source_id], key=lambda row: float(row["loop_s_mid_m"]))
        x = [float(row["loop_s_mid_m"]) for row in payload]
        axes[0].plot(x, [float(row["circumferential_mean_darcy_f_shear"]) for row in payload], color=case_color(source_id), linewidth=1.8, label=case_label(source_id))
        axes[1].plot(x, [float(row["circumferential_mean_wall_heat_flux_w_m2"]) for row in payload], color=case_color(source_id), linewidth=1.8, label=case_label(source_id))
    axes[0].set_ylabel("Circumferential mean Darcy f")
    axes[1].set_ylabel("Circumferential mean q'' [W/m^2]")
    axes[1].set_xlabel("Distance along loop [m]")
    axes[0].set_title("Cross-case circumferential-mean friction comparison")
    axes[1].set_title("Cross-case circumferential-mean wall heat-flux comparison")
    axes[0].legend(loc="best")
    axes[1].legend(loc="best")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "field_transport_azimuthal_means_comparison", dpi=220)
    plt.close(fig)
    return paths


def plot_branch_thermal_comparison(output_dir: Path, rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {}
    branch_names = sorted(
        {str(row["branch_name"]) for row in rows},
        key=lambda name: (name != "upcomer", name),
    )
    x = np.arange(len(branch_names), dtype=float)
    fig, axes = plt.subplots(4, 1, figsize=(15, 13), sharex=True)
    width = 0.75 / max(len({str(row["source_id"]) for row in rows}), 1)
    ordered_source_ids = sorted({str(row["source_id"]) for row in rows}, key=sort_key)
    branch_lookup = {(str(row["source_id"]), str(row["branch_name"])): row for row in rows}
    panel_specs = [
        ("mean_bulk_temp_fluid_area_avg_k", "Mean bulk T [K]", "Branch mean bulk temperature"),
        ("mean_effective_htc_w_m2_k", "Mean HTC [W/m^2/K]", "Branch mean effective HTC"),
        ("mean_effective_ua_per_m_w_m_k", "Mean UA' [W/m/K]", "Branch mean effective UA'"),
        ("mean_effective_thermal_resistance_k_m_w", "Mean R_th' [K m / W]", "Branch mean effective thermal resistance"),
    ]
    for series_index, source_id in enumerate(ordered_source_ids):
        offset = (series_index - (len(ordered_source_ids) - 1) / 2.0) * width
        for axis, (field_name, ylabel, title) in zip(axes, panel_specs):
            values = [
                float(branch_lookup[(source_id, branch_name)].get(field_name, math.nan))
                if (source_id, branch_name) in branch_lookup
                else math.nan
                for branch_name in branch_names
            ]
            axis.bar(
                x + offset,
                values,
                width=width,
                color=case_color(source_id),
                label=case_label(source_id) if axis is axes[0] else None,
            )
            axis.set_ylabel(ylabel)
            axis.set_title(title)
    axes[0].legend(loc="best", ncol=2, fontsize=8)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([name.replace("_", "\n") for name in branch_names])
    axes[-1].set_xlabel("Branch")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "field_transport_branch_thermal_comparison", dpi=220)
    plt.close(fig)
    return paths


def plot_branch_thermal_qc_comparison(output_dir: Path, rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {}
    branch_names = sorted(
        {str(row["branch_name"]) for row in rows},
        key=lambda name: (name != "upcomer", name),
    )
    x = np.arange(len(branch_names), dtype=float)
    fig, axes = plt.subplots(4, 1, figsize=(15, 13), sharex=True)
    width = 0.75 / max(len({str(row["source_id"]) for row in rows}), 1)
    ordered_source_ids = sorted({str(row["source_id"]) for row in rows}, key=sort_key)
    branch_lookup = {(str(row["source_id"]), str(row["branch_name"])): row for row in rows}
    panel_specs = [
        ("usable_fraction", "Usable fraction [-]", "Branch usable thermal-support fraction"),
        ("thermal_warning_fraction", "Masked fraction [-]", "Branch masked thermal-support fraction"),
        ("mean_bulk_positive_mass_flux_kg_s", "Mean +mass flux [kg/s]", "Branch positive mass-flux support"),
        ("min_abs_bulk_minus_wall_temp_k", "Min |T_bulk - T_wall| [K]", "Branch minimum resolved thermal driving force"),
    ]
    for series_index, source_id in enumerate(ordered_source_ids):
        offset = (series_index - (len(ordered_source_ids) - 1) / 2.0) * width
        for axis, (field_name, ylabel, title) in zip(axes, panel_specs):
            values = [
                float(branch_lookup[(source_id, branch_name)].get(field_name, math.nan))
                if (source_id, branch_name) in branch_lookup
                else math.nan
                for branch_name in branch_names
            ]
            axis.bar(
                x + offset,
                values,
                width=width,
                color=case_color(source_id),
                label=case_label(source_id) if axis is axes[0] else None,
            )
            axis.set_ylabel(ylabel)
            axis.set_title(title)
    axes[0].legend(loc="best", ncol=2, fontsize=8)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([name.replace("_", "\n") for name in branch_names])
    axes[-1].set_xlabel("Branch")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "field_transport_branch_thermal_qc_comparison", dpi=220)
    plt.close(fig)
    return paths


def build_readme_context(package_index_rows: list[dict[str, Any]]) -> tuple[str, str, str]:
    source_ids = {str(row["source_id"]) for row in package_index_rows}
    includes_water = any("_water_" in source_id for source_id in source_ids)
    if includes_water:
        return (
            "# All-Runs Field Transport Campaign",
            (
                "This package compares per-case field-transport outputs across the "
                "current Salt-family rollout plus the four Water validation cases, "
                "publishing matched streamwise heat-loss and azimuthal wall-transport reductions."
            ),
            (
                "- `parasitic_heat_loss_summary.csv` groups those reductions by the "
                "case-profile thermal role groups, currently `intended_transfer` and "
                "`parasitic_loss` across the included Salt and Water cases."
            ),
        )
    return (
        "# Salt-Family Field Transport Campaign",
        (
            "This package compares per-case field-transport outputs that publish "
            "streamwise heat-loss and azimuthal wall-transport reductions."
        ),
        (
            "- `parasitic_heat_loss_summary.csv` groups those reductions by the "
            "case-profile thermal role groups, currently `intended_transfer` and "
            "`parasitic_loss` for the Salt-family path."
        ),
    )


def write_readme(output_dir: Path, package_index_rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    title, scope_sentence, grouped_heat_sentence = build_readme_context(package_index_rows)
    lines = [
        title,
        "",
        "## Scope",
        "",
        scope_sentence,
        "",
        "Included packages:",
    ]
    for row in sorted(package_index_rows, key=lambda item: sort_key(str(item["source_id"]))):
        lines.append(f"- `{row['source_id']}` from `{row['package_dir']}`")
    lines.extend(
        [
            "",
            "## Method",
            "",
            "- `streamwise_heat_loss_summary.csv` provides total signed and absolute loopwise heat-loss reductions.",
            grouped_heat_sentence,
            "- `azimuthal_transport_mean_summary.csv` is collapsed to circumferential means using exported wall-face area weights so cross-case friction and wall-heat comparisons stay tied to the sampled wall geometry.",
            "- `branch_thermal_summary.csv` carries branch-local bulk temperature, mass-flux support, and support-gated effective thermal reductions for the six repaired span sections plus the derived `upcomer` branch when the input packages were rebuilt on the June 17 branch-thermal path.",
            "- The same branch summary rows now carry thermal-support QC metrics such as usable fraction, positive mass-flux support, and minimum resolved `|T_bulk - T_wall|`, so branch comparisons can distinguish physical trends from support-limited bins.",
            "",
            "## Assumptions And Limits",
            "",
            "- This builder assumes every input package is already QC-clean enough to advertise both azimuthal and streamwise heat-loss outputs. It does not repair partial packages.",
            "- Grouped parasitic-vs-intended results depend on `tools/case_analysis_profiles.py` thermal role metadata. Reclassifying a patch family changes the interpretation of these aggregates.",
            "- Branch thermal means reuse the per-case support-gated thermal rows. Masked thermal rows remain excluded from branch HTC / UA' / R_th means, so sparse support can still matter when comparing cases.",
            "- Boundary-layer landmarks are intentionally not re-reduced here; use the representative Salt 2 package or the per-case package roots when near-wall landmark context matters.",
            "",
            "## Artifacts",
            "",
            f"- `field_transport_package_index.csv`: `{summary['artifacts']['package_index_csv']}`",
            f"- `field_transport_streamwise_heat_comparison.csv`: `{summary['artifacts']['streamwise_heat_csv']}`",
            f"- `field_transport_grouped_heat_comparison.csv`: `{summary['artifacts']['grouped_heat_csv']}`",
            f"- `field_transport_azimuthal_transport_comparison.csv`: `{summary['artifacts']['azimuthal_transport_csv']}`",
            f"- `field_transport_branch_thermal_comparison.csv`: `{summary['artifacts']['branch_thermal_csv']}`",
            "- `figures/`: cross-case heat-loss, circumferential-mean azimuthal transport, branch-thermal comparisons, and branch-thermal QC comparisons",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))

    total_heat_rows: list[dict[str, Any]] = []
    grouped_heat_rows: list[dict[str, Any]] = []
    azimuthal_mean_rows: list[dict[str, Any]] = []
    branch_thermal_rows: list[dict[str, Any]] = []
    package_index_rows: list[dict[str, Any]] = []

    for package_dir_value in args.package_dir:
        package_dir = Path(package_dir_value).resolve()
        summary_path = package_dir / "summary.json"
        if not summary_path.exists():
            raise RuntimeError(f"Missing summary.json under {package_dir}")
        summary = load_json(summary_path)
        source_id = str(summary.get("source_id", "")).strip()
        if not source_id:
            raise RuntimeError(f"Package summary is missing source_id under {package_dir}")

        total_heat_path = package_dir / "streamwise_heat_loss_summary.csv"
        grouped_heat_path = package_dir / "parasitic_heat_loss_summary.csv"
        azimuthal_path = package_dir / "azimuthal_transport_mean_summary.csv"
        branch_thermal_path = package_dir / "branch_thermal_summary.csv"
        missing = [path.name for path in (total_heat_path, grouped_heat_path, azimuthal_path, branch_thermal_path) if not path.exists()]
        if missing:
            raise RuntimeError(f"Package {package_dir} is missing required field-transport artifacts: {', '.join(missing)}")

        total_heat_rows.extend(load_streamwise_heat_rows(total_heat_path, source_id))
        grouped_heat_rows.extend(load_grouped_heat_rows(grouped_heat_path, source_id))
        azimuthal_mean_rows.extend(load_azimuthal_rows(azimuthal_path, source_id))
        branch_thermal_rows.extend(load_branch_thermal_rows(branch_thermal_path, source_id))
        package_index_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label(source_id),
                "package_dir": str(package_dir),
                "profile_name": str(summary.get("profile_name", "")),
                "branch_thermal_available": bool(summary.get("branch_thermal", {}).get("available")),
            }
        )

    collapsed_azimuthal_rows = collapse_azimuthal_rows(azimuthal_mean_rows)
    csv_dump(output_dir / "field_transport_package_index.csv", list(package_index_rows[0].keys()), package_index_rows)
    csv_dump(output_dir / "field_transport_streamwise_heat_comparison.csv", list(total_heat_rows[0].keys()), total_heat_rows)
    csv_dump(output_dir / "field_transport_grouped_heat_comparison.csv", list(grouped_heat_rows[0].keys()), grouped_heat_rows)
    csv_dump(output_dir / "field_transport_azimuthal_transport_comparison.csv", list(collapsed_azimuthal_rows[0].keys()), collapsed_azimuthal_rows)
    csv_dump(output_dir / "field_transport_branch_thermal_comparison.csv", list(branch_thermal_rows[0].keys()), branch_thermal_rows)

    heat_paths = plot_heat_loss_comparison(output_dir, total_heat_rows, grouped_heat_rows)
    azimuthal_paths = plot_azimuthal_transport_comparison(output_dir, collapsed_azimuthal_rows)
    branch_thermal_paths = plot_branch_thermal_comparison(output_dir, branch_thermal_rows)
    branch_thermal_qc_paths = plot_branch_thermal_qc_comparison(output_dir, branch_thermal_rows)
    summary = {
        "generated_at": iso_timestamp(),
        "package_count": len(package_index_rows),
        "source_ids": [row["source_id"] for row in sorted(package_index_rows, key=lambda row: sort_key(str(row["source_id"])))],
        "artifacts": {
            "package_index_csv": str((output_dir / "field_transport_package_index.csv").resolve()),
            "streamwise_heat_csv": str((output_dir / "field_transport_streamwise_heat_comparison.csv").resolve()),
            "grouped_heat_csv": str((output_dir / "field_transport_grouped_heat_comparison.csv").resolve()),
            "azimuthal_transport_csv": str((output_dir / "field_transport_azimuthal_transport_comparison.csv").resolve()),
            "branch_thermal_csv": str((output_dir / "field_transport_branch_thermal_comparison.csv").resolve()),
        },
        "figure_paths": {
            "heat_loss_comparison": heat_paths,
            "azimuthal_means_comparison": azimuthal_paths,
            "branch_thermal_comparison": branch_thermal_paths,
            "branch_thermal_qc_comparison": branch_thermal_qc_paths,
        },
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=False)
        handle.write("\n")
    write_readme(output_dir, package_index_rows, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
