#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
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

from tools.case_analysis_profiles import TP_TW_LOCATIONS  # noqa: E402
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure  # noqa: E402

DEFAULT_SOURCE_REPORT_DIR = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-23_ethan_salt_pressure_closure_breakout"

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

SPAN_ORDER = ("lower_leg", "right_leg", "upper_leg", "left_upper_leg", "left_lower_leg")

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build presentation-friendly per-family Salt pressure-closure figures "
            "from the existing June 17 pressure / HTC / boundary-layer package."
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


def normalize_endpoint_label(label: str) -> str:
    value = str(label).strip()
    if re.fullmatch(r"TP[0-9]+", value):
        return value
    return "corner"


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


def read_span_label_map(package_dir: Path, tp_rows: list[dict[str, Any]]) -> dict[str, str]:
    station_rows = load_csv_rows(package_dir / "leg_centerline_station_definitions.csv")
    by_span: dict[str, list[dict[str, str]]] = {}
    for row in station_rows:
        by_span.setdefault(str(row["span_name"]), []).append(row)
    labels: dict[str, str] = {}
    for span_name in SPAN_ORDER:
        payload = sorted(by_span.get(span_name, []), key=lambda row: float(row["s_mid_m"]))
        if not payload:
            continue
        start = payload[0]
        end = payload[-1]
        start_label = infer_endpoint_label(
            str(start["segment_start_label"]),
            float(start["x_m"]),
            float(start["y_m"]),
            float(start["z_m"]),
            tp_rows,
        )
        end_label = infer_endpoint_label(
            str(end["segment_end_label"]),
            float(end["x_m"]),
            float(end["y_m"]),
            float(end["z_m"]),
            tp_rows,
        )
        labels[span_name] = f"{span_name}\n{start_label} -> {end_label}"
    return labels


def numeric_or_nan(value: str) -> float:
    if value in ("", "nan", "NaN", "None", "null"):
        return math.nan
    return float(value)


def read_section_rows(path: Path) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        if str(row["family"]) != "salt" or str(row["straight_section_flag"]) != "yes":
            continue
        payload.append(
            {
                **row,
                "section_length_m": numeric_or_nan(str(row["section_length_m"])),
                "mean_pressure_loss_hydro_pa": numeric_or_nan(str(row["mean_pressure_loss_hydro_pa"])),
                "mean_pressure_loss_prgh_endpoint_pa": numeric_or_nan(str(row["mean_pressure_loss_prgh_endpoint_pa"])),
                "mean_pressure_closure_residual_vs_prgh_endpoint_pa": numeric_or_nan(
                    str(row["mean_pressure_closure_residual_vs_prgh_endpoint_pa"])
                ),
            }
        )
    return payload


def plot_family_breakout(
    output_dir: Path,
    family_id: int,
    source_ids: tuple[str, ...],
    section_rows: list[dict[str, Any]],
    span_labels: dict[str, str],
) -> dict[str, str]:
    rows_by_case_span = {
        (str(row["source_id"]), str(row["span_name"])): row
        for row in section_rows
        if str(row["source_id"]) in source_ids and str(row["span_name"]) in SPAN_ORDER
    }
    x = np.arange(len(SPAN_ORDER))
    fig, axes = plt.subplots(3, 1, figsize=(12.5, 10.5), sharex=True)
    panel_specs = (
        ("mean_pressure_loss_hydro_pa", "Hydro-corrected pressure loss from p + buoyancy", "Hydro-corrected loss [Pa]"),
        ("mean_pressure_loss_prgh_endpoint_pa", "Endpoint p_rgh pressure loss", "Endpoint p_rgh loss [Pa]"),
        (
            "mean_pressure_closure_residual_vs_prgh_endpoint_pa",
            "Closure residual: hydro-corrected minus endpoint p_rgh",
            "Residual [Pa]",
        ),
    )
    for source_id in source_ids:
        for axis, (field_name, title, ylabel) in zip(axes, panel_specs):
            y_values = []
            for span_name in SPAN_ORDER:
                row = rows_by_case_span.get((source_id, span_name))
                y_values.append(math.nan if row is None else float(row[field_name]))
            axis.plot(
                x,
                y_values,
                color=case_color(source_id),
                linewidth=2.0,
                marker="o",
                markersize=5.5,
                label=case_label(source_id),
            )
            axis.axhline(0.0, color="#9ca3af", linewidth=0.9)
            axis.set_ylabel(ylabel)
            axis.set_title(title)
    axes[0].legend(loc="upper right", fontsize=9)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([span_labels.get(name, name) for name in SPAN_ORDER], fontsize=9)
    axes[-1].set_xlabel("Straight span and authored TP endpoints")
    fig.suptitle(
        f"{family_case_label(family_id)} straight-section pressure-closure breakout",
        fontsize=16,
        y=0.995,
    )
    fig.text(
        0.5,
        0.012,
        "This breakout uses endpoint p_rgh loss rather than integrated p_rgh loss because the integrated quantity is only published on lower_leg and right_leg in the June 17 package.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#4b5563",
    )
    fig.tight_layout(rect=(0.0, 0.035, 1.0, 0.975))
    return save_matplotlib_figure(fig, output_dir, f"salt{family_id}_pressure_closure_breakout", dpi=220)


def write_readme(
    output_dir: Path,
    generated_at: str,
    source_report_dir: Path,
    figure_rows: list[dict[str, Any]],
    span_label_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Salt Pressure-Closure Breakout",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Purpose",
        "",
        "- Replace the unreadable all-case straight-section pressure-closure scatter with one figure per Salt family.",
        "- Keep each figure to at most three cases and five straight spans.",
        "- Use one consistent hydraulic comparison basis across all spans: hydro-corrected `p` loss, endpoint `p_rgh` loss, and their residual.",
        "",
        "## Source",
        "",
        f"- Reuses the published June 17 pressure / HTC / boundary-layer package at `{source_report_dir}`.",
        "- No CFD extraction was reopened for this breakout.",
        "",
        "## Reading Notes",
        "",
        "- Each figure is one Salt family only.",
        "- Top panel: hydro-corrected pressure loss from wall `p` plus the buoyancy integral.",
        "- Middle panel: endpoint `p_rgh` pressure loss, used because it exists on all five straight Salt spans.",
        "- Bottom panel: closure residual between those two quantities.",
        "- Span headers include the authored TP endpoints for the full span.",
        "",
        "## Figure Inventory",
        "",
    ]
    for row in figure_rows:
        lines.append(f"- `Salt {row['family_id']}`: `{row['png_path']}`")
    lines.extend(
        [
            "",
            "## Metadata Tables",
            "",
            "- `figure_index.csv`",
            "- `span_label_map.csv`",
            "- `pressure_closure_breakout_rows.csv`",
            "- `summary.json`",
            "",
        ]
    )
    span_names = ", ".join(sorted({str(row['span_name']) for row in span_label_rows}))
    lines.append("## Span Coverage")
    lines.append("")
    lines.append(f"- Straight spans represented: `{span_names}`.")
    lines.append("")
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_report_dir = Path(args.source_report_dir).resolve()
    output_dir = ensure_dir(Path(args.output_dir).resolve())
    generated_at = iso_timestamp()

    package_index = read_package_index(source_report_dir / "package_index.csv")
    section_rows = read_section_rows(source_report_dir / "pressure_closure_by_section.csv")
    tp_rows = read_tp_locations(TP_TW_LOCATIONS)

    figure_rows: list[dict[str, Any]] = []
    span_label_rows: list[dict[str, Any]] = []
    breakout_rows: list[dict[str, Any]] = []

    for family_id, source_ids in SALT_FAMILY_CASES.items():
        available_source_ids = tuple(source_id for source_id in source_ids if source_id in package_index)
        if not available_source_ids:
            continue
        representative_source_id = available_source_ids[0]
        representative_package_dir = Path(package_index[representative_source_id]["package_dir"]).resolve()
        span_labels = read_span_label_map(representative_package_dir, tp_rows)
        for span_name, label in span_labels.items():
            span_label_rows.append(
                {
                    "family_id": family_id,
                    "representative_source_id": representative_source_id,
                    "span_name": span_name,
                    "span_label": label,
                }
            )
        family_rows = [
            row for row in section_rows if str(row["source_id"]) in available_source_ids and str(row["span_name"]) in SPAN_ORDER
        ]
        for row in family_rows:
            breakout_rows.append(
                {
                    "family_id": family_id,
                    "span_label": span_labels.get(str(row["span_name"]), str(row["span_name"])),
                    **row,
                }
            )
        figure_paths = plot_family_breakout(output_dir, family_id, available_source_ids, family_rows, span_labels)
        figure_rows.append(
            {
                "family_id": family_id,
                "family_label": family_case_label(family_id),
                "source_ids": ",".join(available_source_ids),
                "png_path": figure_paths["png"],
                "svg_path": figure_paths["svg"],
                "pdf_path": figure_paths["pdf"],
            }
        )

    csv_dump(output_dir / "figure_index.csv", list(figure_rows[0].keys()), figure_rows)
    csv_dump(output_dir / "span_label_map.csv", list(span_label_rows[0].keys()), span_label_rows)
    csv_dump(output_dir / "pressure_closure_breakout_rows.csv", list(breakout_rows[0].keys()), breakout_rows)
    summary = {
        "generated_at": generated_at,
        "source_report_dir": str(source_report_dir),
        "figures": figure_rows,
        "span_labels": span_label_rows,
        "notes": [
            "Endpoint p_rgh loss is used in the breakout because it exists across all five straight Salt spans.",
            "Integrated p_rgh loss remains available in the source package only for lower_leg and right_leg.",
        ],
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, generated_at, source_report_dir, figure_rows, span_label_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
