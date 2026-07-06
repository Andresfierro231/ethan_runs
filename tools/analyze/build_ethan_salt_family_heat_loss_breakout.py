#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure  # noqa: E402
from tools.case_analysis_profiles import TP_TW_LOCATIONS  # noqa: E402

DEFAULT_SOURCE_REPORT_DIR = ROOT / "reports" / "2026-06-15_ethan_field_transport_campaign"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-23_ethan_salt_family_heat_loss_breakout"

SALT_FAMILY_CASES: dict[int, tuple[str, ...]] = {
    1: (
        "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    ),
    2: (
        "val_salt_test_2_coarse_mesh_laminar",
        "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    ),
    3: (
        "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    ),
    4: (
        "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "viscosity_screening_salt_test_4_kirst_coarse_mesh",
    ),
}

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
}

ROLE_LAYOUT = (
    ("total", "Net total", "net_total"),
    ("intended_transfer", "Intended transfer only", "intended_transfer"),
    ("parasitic_loss", "Parasitic loss only", "parasitic_loss"),
)

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build presentation-friendly per-family Salt heat-loss breakout figures "
            "from the existing June 15 field-transport campaign package."
        )
    )
    parser.add_argument("--source-report-dir", default=str(DEFAULT_SOURCE_REPORT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def case_label(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[0]


def case_color(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[1]


def normalize_endpoint_label(label: str) -> str:
    value = str(label).strip()
    if re.fullmatch(r"TP[0-9]+", value):
        return value
    return "corner"


def family_case_label(family_id: int) -> str:
    return f"Salt {family_id}"


def read_package_index(path: Path) -> dict[str, dict[str, str]]:
    rows = load_csv_rows(path)
    return {str(row["source_id"]): row for row in rows}


def read_tp_locations(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        if str(row["group"]) != "TP":
            continue
        rows.append(
            {
                "label": str(row["label"]),
                "x_m": float(row["x_m"]),
                "y_m": float(row["y_m"]),
                "z_m": float(row["z_m"]),
            }
        )
    return rows


def infer_endpoint_label(
    raw_label: str,
    x_value: float,
    y_value: float,
    z_value: float,
    tp_rows: list[dict[str, Any]],
    tolerance_m: float = 0.035,
) -> str:
    normalized = normalize_endpoint_label(raw_label)
    if normalized != "corner":
        return normalized
    best_label = "corner"
    best_distance = float("inf")
    for row in tp_rows:
        dx = float(x_value - row["x_m"])
        dy = float(y_value - row["y_m"])
        dz = float(z_value - row["z_m"])
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if distance < best_distance:
            best_distance = distance
            best_label = str(row["label"])
    return best_label if best_distance <= tolerance_m else "corner"


def read_span_chunks(
    total_rows: list[dict[str, str]],
    representative_source_id: str,
    representative_package_dir: Path,
    tp_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    summary = load_json(representative_package_dir / "summary.json")
    loop_order = [str(value) for value in summary["major_loss"]["loop_span_order"]]
    station_rows = load_csv_rows(representative_package_dir / "leg_centerline_station_definitions.csv")
    station_by_span: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in station_rows:
        station_by_span[str(row["span_name"])].append(row)
    heat_by_span: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in total_rows:
        if str(row["source_id"]) != representative_source_id:
            continue
        heat_by_span[str(row["span_name"])].append(row)

    span_chunks: list[dict[str, Any]] = []
    for span_name in loop_order:
        station_payload = sorted(station_by_span.get(span_name, []), key=lambda row: float(row["s_mid_m"]))
        heat_payload = sorted(heat_by_span.get(span_name, []), key=lambda row: float(row["loop_s_mid_m"]))
        if not station_payload or not heat_payload:
            continue
        start_row = station_payload[0]
        end_row = station_payload[-1]
        span_chunks.append(
            {
                "span_name": span_name,
                "plot_start_m": float(heat_payload[0]["loop_s_mid_m"]),
                "plot_end_m": float(heat_payload[-1]["loop_s_mid_m"]),
                "start_label": str(start_row["segment_start_label"]),
                "end_label": str(end_row["segment_end_label"]),
                "start_label_display": infer_endpoint_label(
                    str(start_row["segment_start_label"]),
                    float(start_row["x_m"]),
                    float(start_row["y_m"]),
                    float(start_row["z_m"]),
                    tp_rows,
                ),
                "end_label_display": infer_endpoint_label(
                    str(end_row["segment_end_label"]),
                    float(end_row["x_m"]),
                    float(end_row["y_m"]),
                    float(end_row["z_m"]),
                    tp_rows,
                ),
            }
        )
    return span_chunks, loop_order


def add_span_background(ax: Any, span_chunks: list[dict[str, Any]]) -> None:
    for index, chunk in enumerate(span_chunks):
        color = "#e5e7eb" if index % 2 == 0 else "#f3f4f6"
        ax.axvspan(chunk["plot_start_m"], chunk["plot_end_m"], color=color, alpha=0.30, zorder=0)
        ax.axvline(chunk["plot_start_m"], color="#9ca3af", linewidth=0.8, alpha=0.75, zorder=1)
        ax.axvline(chunk["plot_end_m"], color="#9ca3af", linewidth=0.8, alpha=0.75, zorder=1)
    for left, right in zip(span_chunks[:-1], span_chunks[1:]):
        if right["plot_start_m"] <= left["plot_end_m"]:
            continue
        ax.axvspan(left["plot_end_m"], right["plot_start_m"], color="#d1d5db", alpha=0.12, zorder=0)


def span_display_name(span_name: str) -> str:
    return {
        "lower_leg": "lower leg",
        "right_leg": "right leg",
        "upper_leg": "upper leg",
        "left_upper_leg": "left upper",
        "test_section_span": "test section",
        "left_lower_leg": "left lower",
    }.get(span_name, span_name.replace("_", " "))


def draw_shared_span_guide(ax: Any, span_chunks: list[dict[str, Any]]) -> None:
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks([])
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    for index, chunk in enumerate(span_chunks):
        color = "#e5e7eb" if index % 2 == 0 else "#f3f4f6"
        ax.axvspan(chunk["plot_start_m"], chunk["plot_end_m"], color=color, alpha=0.50, zorder=0)
        ax.axvline(chunk["plot_start_m"], color="#9ca3af", linewidth=0.9, alpha=0.80, zorder=1)
        ax.axvline(chunk["plot_end_m"], color="#9ca3af", linewidth=0.9, alpha=0.80, zorder=1)
        midpoint = 0.5 * (chunk["plot_start_m"] + chunk["plot_end_m"])
        width = float(chunk["plot_end_m"]) - float(chunk["plot_start_m"])
        fontsize = 8.4 if width >= 0.26 else 7.3
        y_text = 0.82 if index % 2 == 0 else 0.28
        label = (
            f"{span_display_name(str(chunk['span_name']))}\n"
            f"{chunk['start_label_display']} -> {chunk['end_label_display']}"
        )
        ax.text(
            midpoint,
            y_text,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            color="#374151",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "none", "alpha": 0.88},
            zorder=2,
        )
    for left, right in zip(span_chunks[:-1], span_chunks[1:]):
        if right["plot_start_m"] <= left["plot_end_m"]:
            continue
        ax.axvspan(left["plot_end_m"], right["plot_start_m"], color="#d1d5db", alpha=0.18, zorder=0)
    ax.text(
        0.995,
        0.04,
        "grey gaps = omitted corners / junctions",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#6b7280",
    )


def grouped_rows_by_role(grouped_rows: list[dict[str, str]], source_id: str, role_name: str) -> list[dict[str, str]]:
    payload = [
        row
        for row in grouped_rows
        if str(row["source_id"]) == source_id and str(row["thermal_role_group"]) == role_name
    ]
    return sorted(payload, key=lambda row: float(row["loop_s_mid_m"]))


def total_rows_for_source(total_rows: list[dict[str, str]], source_id: str) -> list[dict[str, str]]:
    payload = [row for row in total_rows if str(row["source_id"]) == source_id]
    return sorted(payload, key=lambda row: float(row["loop_s_mid_m"]))


def plot_family_breakout(
    output_dir: Path,
    family_id: int,
    source_ids: tuple[str, ...],
    total_rows: list[dict[str, str]],
    grouped_rows: list[dict[str, str]],
    span_chunks: list[dict[str, Any]],
) -> dict[str, str]:
    fig = plt.figure(figsize=(17.2, 11.8))
    grid = fig.add_gridspec(4, 2, height_ratios=(0.34, 1.0, 1.0, 1.0), hspace=0.24, wspace=0.15)
    span_ax = fig.add_subplot(grid[0, :])
    draw_shared_span_guide(span_ax, span_chunks)
    axes = [
        [fig.add_subplot(grid[row_index + 1, column_index], sharex=span_ax) for column_index in range(2)]
        for row_index in range(3)
    ]
    for row_index, (role_name, row_label, _) in enumerate(ROLE_LAYOUT):
        for column_index, metric_name in enumerate(("local", "cumulative")):
            ax = axes[row_index][column_index]
            add_span_background(ax, span_chunks)
            ax.axhline(0.0, color="#9ca3af", linewidth=0.9, zorder=1)
            for source_id in source_ids:
                payload = (
                    total_rows_for_source(total_rows, source_id)
                    if role_name == "total"
                    else grouped_rows_by_role(grouped_rows, source_id, role_name)
                )
                if not payload:
                    continue
                x_values = [float(row["loop_s_mid_m"]) for row in payload]
                if metric_name == "local":
                    y_values = [float(row["mean_wall_heat_per_length_w_m"]) for row in payload]
                else:
                    y_values = [float(row["mean_cumulative_wall_heat_w"]) for row in payload]
                ax.plot(
                    x_values,
                    y_values,
                    color=case_color(source_id),
                    linewidth=2.1,
                    label=case_label(source_id),
                    zorder=2,
                )
            if column_index == 0:
                ax.set_ylabel(f"{row_label}\nq' [W/m]")
            else:
                ax.set_ylabel(f"{row_label}\nQ [W]")
            if row_index == 0:
                ax.set_title(
                    "Local signed wall heat per length"
                    if metric_name == "local"
                    else "Cumulative signed wall heat"
                )
    axes[0][1].legend(loc="upper right", fontsize=9)
    axes[2][0].set_xlabel("Visible loop distance s [m]")
    axes[2][1].set_xlabel("Visible loop distance s [m]")
    fig.suptitle(
        f"{family_case_label(family_id)} streamwise wall-heat breakout",
        fontsize=17,
        y=0.995,
    )
    fig.text(
        0.5,
        0.012,
        "Components are separated by row to avoid dashed/dotted ambiguity. "
        "The shared top strip labels the full authored span endpoints once for the whole figure. "
        "Grey gaps mark omitted corners, junctions, or bins with no published streamwise heat rows.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#4b5563",
    )
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.08, top=0.88)
    return save_matplotlib_figure(fig, output_dir, f"salt{family_id}_heat_loss_breakout", dpi=220)


def write_readme(
    output_dir: Path,
    generated_at: str,
    source_report_dir: Path,
    family_figure_rows: list[dict[str, Any]],
    span_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Salt-Family Heat-Loss Breakout",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Purpose",
        "",
        "- Replace the dense all-Salt overlay with one figure per Salt family.",
        "- Separate `net total`, `intended transfer`, and `parasitic loss` into different subplot rows.",
        "- Make the plotted span chunks and their TP endpoint labels explicit without repeating the same labels on every subplot.",
        "",
        "## Source",
        "",
        f"- Reuses the published June 15 field-transport campaign package at `{source_report_dir}`.",
        "- No CFD extraction was reopened for this breakout.",
        "",
        "## Reading Notes",
        "",
        "- Each family figure uses solid case-colored lines only; there are no dashed or dotted role encodings.",
        "- Left column: local signed wall heat per length `q'(s)`.",
        "- Right column: cumulative signed wall heat `Q(s)`.",
        "- Rows: `net total`, `intended transfer only`, `parasitic loss only`.",
        "- A shared span guide at the top of each figure shows the full authored span and TP endpoints once for the whole canvas.",
        "- Grey span blocks inside the plots mark the visible plotted chunk for each repaired span.",
        "- Grey gaps between blocks indicate omitted corners, junctions, or masked / unpublished bins.",
        "",
        "## Figure Inventory",
        "",
    ]
    for row in family_figure_rows:
        lines.append(
            f"- `Salt {row['family_id']}`: `{row['png_path']}`"
        )
    lines.extend(
        [
            "",
            "## Metadata Tables",
            "",
            "- `figure_index.csv`",
            "- `span_chunk_map.csv`",
            "- `summary.json`",
            "",
        ]
    )
    span_names = sorted({str(row["span_name"]) for row in span_rows})
    lines.append("## Span Chunks")
    lines.append("")
    lines.append(f"- Spans represented: `{', '.join(span_names)}`.")
    lines.append("")
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_report_dir = Path(args.source_report_dir).resolve()
    output_dir = ensure_dir(Path(args.output_dir).resolve())
    generated_at = iso_timestamp()

    package_index = read_package_index(source_report_dir / "field_transport_package_index.csv")
    total_rows = load_csv_rows(source_report_dir / "field_transport_streamwise_heat_comparison.csv")
    grouped_rows = load_csv_rows(source_report_dir / "field_transport_grouped_heat_comparison.csv")
    tp_rows = read_tp_locations(TP_TW_LOCATIONS)

    figure_index_rows: list[dict[str, Any]] = []
    span_chunk_rows: list[dict[str, Any]] = []

    for family_id, source_ids in SALT_FAMILY_CASES.items():
        available_source_ids = tuple(source_id for source_id in source_ids if source_id in package_index)
        if not available_source_ids:
            continue
        representative_source_id = available_source_ids[0]
        representative_package_dir = Path(package_index[representative_source_id]["package_dir"]).resolve()
        span_chunks, loop_order = read_span_chunks(
            total_rows,
            representative_source_id,
            representative_package_dir,
            tp_rows,
        )
        for row in span_chunks:
            span_chunk_rows.append(
                {
                    "family_id": family_id,
                    "representative_source_id": representative_source_id,
                    "loop_order_index": loop_order.index(str(row["span_name"])),
                    **row,
                }
            )
        figure_paths = plot_family_breakout(
            output_dir,
            family_id,
            available_source_ids,
            total_rows,
            grouped_rows,
            span_chunks,
        )
        figure_index_rows.append(
            {
                "family_id": family_id,
                "family_label": family_case_label(family_id),
                "source_ids": ",".join(available_source_ids),
                "png_path": figure_paths["png"],
                "svg_path": figure_paths["svg"],
                "pdf_path": figure_paths["pdf"],
            }
        )

    csv_dump(output_dir / "figure_index.csv", list(figure_index_rows[0].keys()), figure_index_rows)
    csv_dump(output_dir / "span_chunk_map.csv", list(span_chunk_rows[0].keys()), span_chunk_rows)

    summary = {
        "generated_at": generated_at,
        "source_report_dir": str(source_report_dir),
        "families": figure_index_rows,
        "span_chunks": span_chunk_rows,
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, generated_at, source_report_dir, figure_index_rows, span_chunk_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
