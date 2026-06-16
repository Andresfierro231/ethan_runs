#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
import shutil
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    date_stamp,
    ensure_dir,
    iso_timestamp,
    json_dump,
    save_matplotlib_figure,
    safe_float,
)

REPRESENTATIVE_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "representative_case_selection.csv"
JIN_KIRST_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "jin_vs_kirst_summary.csv"
STATUS_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "all_salt_case_status.csv"
SECTION_PRESSURE_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_section_transport_package" / "section_pressure_drops.csv"
SECTION_REP_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_section_transport_package" / "representative_section_summary.csv"
TRANSIENT_LAST_WINDOW_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_transient_axial_package" / "all_salt_transient_last_window.csv"
AXIAL_LEG_SUMMARY_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_transient_axial_package" / "all_salt_axial_leg_summary.csv"

DEFAULT_BASE_CASES = ["salt_test_2", "salt_test_3", "salt_test_4"]
DEFAULT_SLICE_SOURCES = [
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
]
DEFAULT_FIGURES = [
    "branch_pressure",
    "jin_kirst_delta",
    "heat_balance",
    "steadiness",
    "slice_panel",
]
PRESSURE_SECTIONS = ["lower_leg", "right_leg", "upper_leg", "left_leg", "test_section_branch"]
PRESSURE_SECTION_LABELS = {
    "lower_leg": "Lower leg",
    "right_leg": "Right leg",
    "upper_leg": "Upper leg",
    "left_leg": "Left leg",
    "test_section_branch": "Test-section branch",
}
CASE_COLORS = {
    "salt_test_1": "#9a031e",
    "salt_test_2": "#0b6e4f",
    "salt_test_3": "#005f73",
    "salt_test_4": "#bc3908",
}
DELTA_COLORS = {
    "delta_exp_mdot_abs_error_pct_jin_minus_kirst": "#0b6e4f",
    "delta_sim_ambient_proxy_w_jin_minus_kirst": "#005f73",
    "delta_upper_leg_abs_delta_p_rgh_pa_jin_minus_kirst": "#bc3908",
    "delta_exp_all_temp_rmse_k_jin_minus_kirst": "#6a4c93",
}
HEAT_ROLE_COLORS = {
    "heater": "#d62828",
    "cooling_branch": "#1d3557",
    "test_section": "#457b9d",
    "junctions": "#6c757d",
    "transport": "#2a9d8f",
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a presentation-oriented Ethan figure package from the existing "
            "June 4-8 structured report outputs."
        )
    )
    parser.add_argument(
        "--output-dir",
        default=str(WORKSPACE_ROOT / "reports" / f"{date_stamp()}_ethan_presentation_figure_package"),
        help="Output report package directory.",
    )
    parser.add_argument(
        "--base-case-id",
        action="append",
        dest="base_case_ids",
        default=[],
        help="Repeat to choose the representative salt families to emphasize.",
    )
    parser.add_argument(
        "--figure-family",
        action="append",
        choices=DEFAULT_FIGURES,
        dest="figure_families",
        default=[],
        help="Repeat to limit which figure families are generated.",
    )
    parser.add_argument(
        "--slice-source-id",
        action="append",
        dest="slice_source_ids",
        default=[],
        help="Repeat to override the default field-slice panel source IDs.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def slug_label(value: str) -> str:
    return value.replace("_", " ")


def pretty_case_label(source_id: str, base_case_id: Optional[str] = None) -> str:
    if source_id.startswith("val_"):
        return f"{slug_label(base_case_id or source_id)} val"
    if "_jin_" in source_id or source_id.endswith("_jin"):
        return f"{slug_label(base_case_id or source_id)} Jin"
    if "_kirst_" in source_id or source_id.endswith("_kirst"):
        return f"{slug_label(base_case_id or source_id)} Kirst"
    return slug_label(base_case_id or source_id)


def load_representative_map(base_case_ids: list[str]) -> dict[str, dict[str, str]]:
    rep_rows = load_csv_rows(REPRESENTATIVE_CSV)
    selected = base_case_ids or DEFAULT_BASE_CASES
    rep_map: dict[str, dict[str, str]] = {}
    for row in rep_rows:
        base_case_id = row.get("base_case_id", "")
        if base_case_id not in selected:
            continue
        primary = row.get("primary_manuscript_representative", "")
        if primary:
            rep_map[base_case_id] = row
    return rep_map


def load_status_map() -> dict[str, dict[str, str]]:
    return {row["source_id"]: row for row in load_csv_rows(STATUS_CSV) if row.get("source_id")}


def load_section_pressure_map() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["source_id"], row["section_name"]): row
        for row in load_csv_rows(SECTION_PRESSURE_CSV)
        if row.get("source_id") and row.get("section_name")
    }


def load_transient_last_window_map() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["source_id"], row["metric"]): row
        for row in load_csv_rows(TRANSIENT_LAST_WINDOW_CSV)
        if row.get("source_id") and row.get("metric")
    }


def role_heat_totals(axial_rows: list[dict[str, str]], source_id: str) -> dict[str, float]:
    totals = {"heater": 0.0, "cooling_branch": 0.0, "test_section": 0.0, "junctions": 0.0, "transport": 0.0}
    for row in axial_rows:
        if row.get("source_id") != source_id:
            continue
        role = row.get("thermal_role", "")
        value = safe_float(row.get("sum_q_total_w"), 0.0) or 0.0
        if role == "transport":
            totals["transport"] += value
        elif role == "junction":
            totals["junctions"] += value
        elif role in totals:
            totals[role] += value
    return totals


def normalized_drift_pct(row: dict[str, str]) -> float:
    mean_value = safe_float(row.get("mean"))
    end_minus_start = safe_float(row.get("end_minus_start"))
    metric = row.get("metric", "")
    if mean_value is None or end_minus_start is None:
        return np.nan
    scale = abs(mean_value)
    if metric == "mdot_mean_abs_kg_s":
        scale = max(scale, 1.0e-6)
    elif metric == "tp_mean_k":
        scale = max(scale, 1.0)
    else:
        scale = max(scale, 1.0)
    return 100.0 * abs(end_minus_start) / scale


def source_slice_path(source_id: str, kind: str, fmt: str) -> Path:
    root = WORKSPACE_ROOT / "figures" / fmt
    if kind == "temperature":
        if fmt == "png":
            return root / f"{source_id}.png"
        return root / f"{source_id}_last_timestep_temperature_slice.{fmt}"
    return root / f"{source_id}_last_timestep_velocity_slice.{fmt}"


def plot_branch_pressure(output_dir: Path, rep_map: dict[str, dict[str, str]], pressure_map: dict[tuple[str, str], dict[str, str]]) -> str:
    case_ids = list(rep_map.keys())
    fig, axes = plt.subplots(1, len(case_ids), figsize=(5.5 * len(case_ids), 6), constrained_layout=True)
    if len(case_ids) == 1:
        axes = [axes]
    for ax, base_case_id in zip(axes, case_ids):
        row = rep_map[base_case_id]
        source_id = row["primary_manuscript_representative"]
        values = []
        labels = []
        for section_name in PRESSURE_SECTIONS:
            entry = pressure_map.get((source_id, section_name), {})
            value = safe_float(entry.get("abs_delta_p_rgh_pa"), np.nan)
            values.append(value)
            labels.append(PRESSURE_SECTION_LABELS[section_name])
        ypos = np.arange(len(labels))
        ax.barh(ypos, values, color=CASE_COLORS.get(base_case_id, "#333333"))
        ax.set_yticks(ypos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlabel("|Δp_rgh| [Pa]")
        ax.set_title(pretty_case_label(source_id, base_case_id))
    fig.suptitle("Representative branch pressure ranking")
    save_matplotlib_figure(fig, output_dir, "representative_branch_pressure_drop", dpi=200)
    plt.close(fig)
    return "representative_branch_pressure_drop"


def plot_jin_kirst_delta(
    output_dir: Path,
    pressure_map: dict[tuple[str, str], dict[str, str]],
) -> str:
    rows = load_csv_rows(JIN_KIRST_CSV)
    delta_rows: list[dict[str, Any]] = []
    for row in rows:
        base_case_id = row["base_case_id"]
        jin_source = row["jin_source_id"]
        kirst_source = row["kirst_source_id"]
        jin_upper = safe_float(pressure_map.get((jin_source, "upper_leg"), {}).get("abs_delta_p_rgh_pa"), np.nan)
        kirst_upper = safe_float(pressure_map.get((kirst_source, "upper_leg"), {}).get("abs_delta_p_rgh_pa"), np.nan)
        delta_rows.append(
            {
                **row,
                "delta_upper_leg_abs_delta_p_rgh_pa_jin_minus_kirst": jin_upper - kirst_upper,
            }
        )

    metrics = [
        ("delta_exp_mdot_abs_error_pct_jin_minus_kirst", "Δ |mdot| error [%]"),
        ("delta_sim_ambient_proxy_w_jin_minus_kirst", "Δ ambient proxy [W]"),
        ("delta_upper_leg_abs_delta_p_rgh_pa_jin_minus_kirst", "Δ upper-leg |Δp_rgh| [Pa]"),
        ("delta_exp_all_temp_rmse_k_jin_minus_kirst", "Δ all-temperature RMSE [K]"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    axes = axes.flatten()
    x = np.arange(len(delta_rows))
    labels = [slug_label(row["base_case_id"]) for row in delta_rows]
    for ax, (metric, ylabel) in zip(axes, metrics):
        values = [safe_float(row.get(metric), np.nan) for row in delta_rows]
        ax.bar(x, values, color=DELTA_COLORS[metric])
        ax.axhline(0.0, color="black", linewidth=1.0)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel.replace("Δ ", ""))
    fig.suptitle("Jin minus Kirst deltas by salt family")
    save_matplotlib_figure(fig, output_dir, "jin_vs_kirst_delta_dashboard", dpi=200)
    plt.close(fig)
    return "jin_vs_kirst_delta_dashboard"


def plot_heat_balance(output_dir: Path, rep_map: dict[str, dict[str, str]], axial_rows: list[dict[str, str]]) -> str:
    case_ids = list(rep_map.keys())
    x = np.arange(len(case_ids))
    width = 0.72
    role_order = ["heater", "cooling_branch", "test_section", "junctions", "transport"]
    fig, ax = plt.subplots(figsize=(12, 7), constrained_layout=True)
    positive_bottom = np.zeros(len(case_ids))
    negative_bottom = np.zeros(len(case_ids))
    labels = []
    totals_by_case = []
    for base_case_id in case_ids:
        source_id = rep_map[base_case_id]["primary_manuscript_representative"]
        labels.append(pretty_case_label(source_id, base_case_id))
        totals_by_case.append(role_heat_totals(axial_rows, source_id))
    for role in role_order:
        values = np.array([case_totals[role] for case_totals in totals_by_case], dtype=float)
        bottoms = np.where(values >= 0.0, positive_bottom, negative_bottom)
        ax.bar(x, values, width=width, bottom=bottoms, color=HEAT_ROLE_COLORS[role], label=slug_label(role))
        positive_bottom = np.where(values >= 0.0, positive_bottom + values, positive_bottom)
        negative_bottom = np.where(values < 0.0, negative_bottom + values, negative_bottom)
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Latest summed wall heat [W]")
    ax.set_title("Representative branch-wise heat partition")
    ax.legend(loc="best", ncol=2)
    save_matplotlib_figure(fig, output_dir, "representative_heat_balance_partition", dpi=200)
    plt.close(fig)
    return "representative_heat_balance_partition"


def plot_steadiness(output_dir: Path, rep_map: dict[str, dict[str, str]], transient_map: dict[tuple[str, str], dict[str, str]]) -> str:
    source_ids = [
        "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    ]
    source_ids.extend(row["primary_manuscript_representative"] for row in rep_map.values())
    metric_order = ["mdot_mean_abs_kg_s", "tp_mean_k", "ambient_proxy_w", "total_q_net_w"]
    metric_labels = ["|mdot|", "TP mean", "Ambient proxy", "Net Q"]
    z = np.full((len(source_ids), len(metric_order)), np.nan)
    for i, source_id in enumerate(source_ids):
        for j, metric in enumerate(metric_order):
            row = transient_map.get((source_id, metric))
            if row:
                z[i, j] = normalized_drift_pct(row)

    fig, ax = plt.subplots(figsize=(10, 5.8), constrained_layout=True)
    image = ax.imshow(z, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(np.arange(len(metric_order)))
    ax.set_xticklabels(metric_labels)
    ylabels = []
    for source_id in source_ids:
        status_row = load_status_map().get(source_id, {})
        ylabels.append(pretty_case_label(source_id, status_row.get("base_case_id", source_id)))
    ax.set_yticks(np.arange(len(source_ids)))
    ax.set_yticklabels(ylabels)
    ax.set_title("Late-window relative drift over last analysis window [%]")
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Absolute end-minus-start / mean [%]")
    for i in range(len(source_ids)):
        for j in range(len(metric_order)):
            value = z[i, j]
            if np.isnan(value):
                label = "NA"
            else:
                label = f"{value:.2f}"
            ax.text(j, i, label, ha="center", va="center", fontsize=8, color="black")
    save_matplotlib_figure(fig, output_dir, "late_window_steadiness_dashboard", dpi=200)
    plt.close(fig)
    return "late_window_steadiness_dashboard"


def collect_slice_figures(output_dir: Path, slice_source_ids: list[str], status_map: dict[str, dict[str, str]]) -> list[str]:
    rows = slice_source_ids or DEFAULT_SLICE_SOURCES
    figure_root = ensure_dir(output_dir / "figures")
    stems: list[str] = []
    for source_id in rows:
        status_row = status_map.get(source_id, {})
        base_case_id = status_row.get("base_case_id", source_id)
        for kind in ("temperature", "velocity"):
            stem = f"{source_id}_{kind}_slice"
            stems.append(stem)
            for fmt in ("png", "svg", "pdf"):
                src = source_slice_path(source_id, kind, fmt)
                dst = ensure_dir(figure_root / fmt) / f"{stem}.{fmt}"
                shutil.copy2(src, dst)
    return stems


def write_readme(output_dir: Path, figure_stems: list[str], rep_map: dict[str, dict[str, str]]) -> None:
    lines = [
        "# Ethan Presentation Figure Package",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "This package repackages the June 4-8 Ethan analysis products into a compact presentation-oriented figure set.",
        "",
        "## Figure set",
        "",
    ]
    for stem in figure_stems:
        lines.append(f"- `{stem}`")
    lines.extend(
        [
            "",
            "## Representative cases",
            "",
        ]
    )
    for base_case_id, row in rep_map.items():
        source_id = row["primary_manuscript_representative"]
        lines.append(f"- `{base_case_id}` -> `{source_id}`")
    lines.extend(
        [
            "",
            "## Inputs reused",
            "",
            f"- `{REPRESENTATIVE_CSV.relative_to(WORKSPACE_ROOT)}`",
            f"- `{JIN_KIRST_CSV.relative_to(WORKSPACE_ROOT)}`",
            f"- `{STATUS_CSV.relative_to(WORKSPACE_ROOT)}`",
            f"- `{SECTION_PRESSURE_CSV.relative_to(WORKSPACE_ROOT)}`",
            f"- `{SECTION_REP_CSV.relative_to(WORKSPACE_ROOT)}`",
            f"- `{TRANSIENT_LAST_WINDOW_CSV.relative_to(WORKSPACE_ROOT)}`",
            f"- `{AXIAL_LEG_SUMMARY_CSV.relative_to(WORKSPACE_ROOT)}`",
            "",
            "## Notes",
            "",
            "- The branch-pressure figure uses latest-time section `|Δp_rgh|` rankings, not full transient `Δp_rgh(t)` histories.",
            "- The reused June 4 transient-axial package already provides `Nu(x)` and `q''(x)` style plots; it does not yet provide a separately derived `HTC(x)` curve.",
            "- The slice figure set now carries the individual stamped temperature and velocity files directly, avoiding blurry composite PDFs.",
            "- Salt 1 is included in the steadiness dashboard as a caution row, not as a steady-state representative.",
            "",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir).resolve())
    base_case_ids = args.base_case_ids or DEFAULT_BASE_CASES
    figure_families = args.figure_families or DEFAULT_FIGURES
    slice_source_ids = args.slice_source_ids or DEFAULT_SLICE_SOURCES

    rep_map = load_representative_map(base_case_ids)
    status_map = load_status_map()
    pressure_map = load_section_pressure_map()
    transient_map = load_transient_last_window_map()
    axial_rows = load_csv_rows(AXIAL_LEG_SUMMARY_CSV)

    figure_stems: list[str] = []
    if "branch_pressure" in figure_families:
        figure_stems.append(plot_branch_pressure(output_dir, rep_map, pressure_map))
    if "jin_kirst_delta" in figure_families:
        figure_stems.append(plot_jin_kirst_delta(output_dir, pressure_map))
    if "heat_balance" in figure_families:
        figure_stems.append(plot_heat_balance(output_dir, rep_map, axial_rows))
    if "steadiness" in figure_families:
        figure_stems.append(plot_steadiness(output_dir, rep_map, transient_map))
    if "slice_panel" in figure_families:
        figure_stems.extend(collect_slice_figures(output_dir, slice_source_ids, status_map))

    summary = {
        "generated_at": iso_timestamp(),
        "output_dir": str(output_dir),
        "base_case_ids": base_case_ids,
        "figure_families": figure_families,
        "slice_source_ids": slice_source_ids,
        "representative_sources": {
            base_case_id: row["primary_manuscript_representative"]
            for base_case_id, row in rep_map.items()
        },
        "figure_stems": figure_stems,
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, figure_stems, rep_map)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
