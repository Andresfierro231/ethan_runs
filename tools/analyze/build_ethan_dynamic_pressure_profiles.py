#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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

from tools.case_analysis_profiles import get_case_analysis_profile  # noqa: E402
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure, safe_float  # noqa: E402

DEFAULT_PACKAGE_INDEX = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package" / "package_index.csv"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-23_ethan_dynamic_pressure_profiles"

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build additive distance-resolved dynamic-pressure profiles from the preserved "
            "per-case major-loss streamwise bins."
        )
    )
    parser.add_argument("--package-index", default=str(DEFAULT_PACKAGE_INDEX))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: Any) -> float:
    parsed = safe_float(value)
    if parsed is None or not math.isfinite(parsed):
        return math.nan
    return float(parsed)


def dynamic_pressure_pa(row: dict[str, str]) -> float:
    rho_bulk = finite_float(row.get("rho_bulk_kg_m3"))
    bulk_velocity = finite_float(row.get("bulk_velocity_m_s"))
    if not math.isfinite(rho_bulk) or not math.isfinite(bulk_velocity):
        return math.nan
    return 0.5 * rho_bulk * bulk_velocity * bulk_velocity


def dynamic_profile_rows(package_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    output_rows: list[dict[str, Any]] = []
    missing_packages: list[str] = []
    for package_row in package_rows:
        source_id = package_row["source_id"]
        package_dir = Path(package_row["package_dir"])
        major_path = package_dir / "major_loss_cumulative_timeseries.csv"
        if not major_path.exists():
            missing_packages.append(source_id)
            continue
        for row in load_csv_rows(major_path):
            q_dyn = dynamic_pressure_pa(row)
            output_rows.append(
                {
                    "source_id": source_id,
                    "case_label": package_row["case_label"],
                    "family": package_row["family"],
                    "profile_name": package_row["profile_name"],
                    "package_dir": str(package_dir),
                    "time_s": finite_float(row.get("time_s")),
                    "span_name": row.get("span_name", ""),
                    "span_kind": row.get("span_kind", ""),
                    "bin_index": int(float(row["bin_index"])),
                    "s_start_m": finite_float(row.get("s_start_m")),
                    "s_end_m": finite_float(row.get("s_end_m")),
                    "s_mid_m": finite_float(row.get("s_mid_m")),
                    "rho_bulk_kg_m3": finite_float(row.get("rho_bulk_kg_m3")),
                    "bulk_velocity_m_s": finite_float(row.get("bulk_velocity_m_s")),
                    "dynamic_pressure_pa": q_dyn,
                    "p_wall_area_avg_pa": finite_float(row.get("p_wall_area_avg_pa")),
                    "p_rgh_wall_area_avg_pa": finite_float(row.get("p_rgh_wall_area_avg_pa")),
                }
            )
    return output_rows, missing_packages


def aggregate_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["source_id"]), str(row["span_name"]))].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (source_id, span_name), payload in sorted(grouped.items()):
        q_values = [float(item["dynamic_pressure_pa"]) for item in payload if math.isfinite(float(item["dynamic_pressure_pa"]))]
        s_values = [float(item["s_mid_m"]) for item in payload if math.isfinite(float(item["s_mid_m"]))]
        times = sorted({float(item["time_s"]) for item in payload if math.isfinite(float(item["time_s"]))})
        case_label = str(payload[0]["case_label"])
        family = str(payload[0]["family"])
        summary_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "family": family,
                "span_name": span_name,
                "time_sample_count": len(times),
                "bin_row_count": len(payload),
                "s_min_m": min(s_values) if s_values else math.nan,
                "s_max_m": max(s_values) if s_values else math.nan,
                "dynamic_pressure_mean_pa": float(np.mean(q_values)) if q_values else math.nan,
                "dynamic_pressure_min_pa": min(q_values) if q_values else math.nan,
                "dynamic_pressure_max_pa": max(q_values) if q_values else math.nan,
            }
        )
    return summary_rows


def mean_profile_by_span(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row["span_name"])][int(row["bin_index"])].append(row)

    span_profiles: dict[str, list[dict[str, Any]]] = {}
    for span_name, by_bin in grouped.items():
        payload: list[dict[str, Any]] = []
        for bin_index, bin_rows in sorted(by_bin.items()):
            q_values = [float(item["dynamic_pressure_pa"]) for item in bin_rows if math.isfinite(float(item["dynamic_pressure_pa"]))]
            s_mid_values = [float(item["s_mid_m"]) for item in bin_rows if math.isfinite(float(item["s_mid_m"]))]
            payload.append(
                {
                    "bin_index": bin_index,
                    "s_mid_m": float(np.mean(s_mid_values)) if s_mid_values else math.nan,
                    "dynamic_pressure_mean_pa": float(np.mean(q_values)) if q_values else math.nan,
                    "dynamic_pressure_min_pa": min(q_values) if q_values else math.nan,
                    "dynamic_pressure_max_pa": max(q_values) if q_values else math.nan,
                }
            )
        span_profiles[span_name] = payload
    return span_profiles


def plot_case(case_rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    source_id = str(case_rows[0]["source_id"])
    case_label = str(case_rows[0]["case_label"])
    family = str(case_rows[0]["family"])
    profile = get_case_analysis_profile(source_id)
    span_order = [name for name in profile.major_spans.keys() if any(str(row["span_name"]) == name for row in case_rows)]
    if not span_order:
        span_order = sorted({str(row["span_name"]) for row in case_rows})

    n_spans = len(span_order)
    ncols = 2
    nrows = math.ceil(n_spans / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, max(3.0 * nrows, 4.5)), squeeze=False)
    fig.suptitle(f"{case_label}: dynamic pressure by leg\n$q_{{dyn}}(s) = 0.5\\rho_{{bulk}}U_{{bulk}}^2$", fontsize=14)
    span_profiles = mean_profile_by_span(case_rows)

    rows_by_span_time: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        time_s = float(row["time_s"])
        if math.isfinite(time_s):
            rows_by_span_time[(str(row["span_name"]), time_s)].append(row)

    for ax in axes.flat:
        ax.set_visible(False)

    for idx, span_name in enumerate(span_order):
        ax = axes.flat[idx]
        ax.set_visible(True)
        payload = span_profiles.get(span_name, [])
        if not payload:
            ax.set_title(span_name)
            ax.text(0.5, 0.5, "no valid rows", ha="center", va="center", transform=ax.transAxes)
            continue

        times = sorted({time_s for (span_key, time_s) in rows_by_span_time.keys() if span_key == span_name})
        for time_s in times:
            time_rows = sorted(rows_by_span_time[(span_name, time_s)], key=lambda item: int(item["bin_index"]))
            x_vals = [float(item["s_mid_m"]) for item in time_rows if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["dynamic_pressure_pa"]))]
            y_vals = [float(item["dynamic_pressure_pa"]) for item in time_rows if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["dynamic_pressure_pa"]))]
            if x_vals and y_vals:
                ax.plot(x_vals, y_vals, color="0.75", linewidth=0.8, alpha=0.7)

        x_mean = [float(item["s_mid_m"]) for item in payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["dynamic_pressure_mean_pa"]))]
        y_mean = [float(item["dynamic_pressure_mean_pa"]) for item in payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["dynamic_pressure_mean_pa"]))]
        y_min = [float(item["dynamic_pressure_min_pa"]) for item in payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["dynamic_pressure_mean_pa"]))]
        y_max = [float(item["dynamic_pressure_max_pa"]) for item in payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["dynamic_pressure_mean_pa"]))]
        ax.plot(x_mean, y_mean, color="#004488", linewidth=2.0, label="late-window mean")
        ax.fill_between(x_mean, y_min, y_max, color="#77aadd", alpha=0.25, label="late-window range")
        ax.set_title(span_name)
        ax.set_xlabel("distance along leg, s [m]")
        ax.set_ylabel("dynamic pressure [Pa]")
        ax.legend(loc="best", fontsize=8)

    fig.text(
        0.5,
        0.01,
        "Gray lines: retained times. Blue line and band: mean, min, and max over retained times.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    return save_matplotlib_figure(fig, output_dir, f"{source_id}_dynamic_pressure_by_leg")


def build_readme(output_dir: Path, summary_rows: list[dict[str, Any]], missing_packages: list[str]) -> None:
    source_ids = sorted({str(row["source_id"]) for row in summary_rows})
    families = sorted({str(row["family"]) for row in summary_rows})
    max_q = max((float(row["dynamic_pressure_max_pa"]) for row in summary_rows if math.isfinite(float(row["dynamic_pressure_max_pa"]))), default=math.nan)
    lines = [
        "# Ethan Dynamic Pressure Profiles",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## What This Package Answers",
        "",
        "- `p_rgh` is available in the preserved streamwise-bin artifacts, but it is **not** dynamic pressure.",
        "- In this workspace, `p_rgh` means pressure with the hydrostatic head removed.",
        "- True dynamic pressure is derived here as `q_dyn = 0.5 * rho_bulk * U_bulk^2` using the preserved streamwise-bin `rho_bulk_kg_m3` and `bulk_velocity_m_s` fields.",
        "- This package publishes `q_dyn(s)` as a function of distance through each repaired major leg for every case present in the June 17 pressure / HTC / boundary-layer package index.",
        "",
        "## Scope",
        "",
        f"- cases processed: `{len(source_ids)}`",
        f"- families present: `{', '.join(families)}`",
        f"- maximum reported dynamic pressure: `{max_q:.3f} Pa`" if math.isfinite(max_q) else "- maximum reported dynamic pressure: `nan`",
        "",
        "## Primary Artifacts",
        "",
        "- `dynamic_pressure_profile_rows.csv`",
        "- `dynamic_pressure_profile_summary.csv`",
        "- `summary.json`",
        "- `figures/png/*_dynamic_pressure_by_leg.png` plus matching `svg` / `pdf`",
        "",
        "## Method Boundary",
        "",
        "- `q_dyn` here is a postprocessed bulk surrogate built from the preserved case-analysis bin reductions.",
        "- It uses the same reduced `rho_bulk_kg_m3` and `bulk_velocity_m_s` already used elsewhere in the hydraulic packages.",
        "- It is therefore appropriate for the current repo’s internal hydraulic comparisons, but it is not a direct raw-cell field integral or a separate solver output.",
    ]
    if missing_packages:
        lines.extend(
            [
                "",
                "## Missing package roots",
                "",
                *[f"- `{source_id}`" for source_id in sorted(missing_packages)],
            ]
        )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    package_index_path = Path(args.package_index)
    output_dir = ensure_dir(Path(args.output_dir))
    package_rows = load_csv_rows(package_index_path)
    dynamic_rows, missing_packages = dynamic_profile_rows(package_rows)
    if not dynamic_rows:
        raise SystemExit("No dynamic-pressure rows were built from the package index.")

    fieldnames = [
        "source_id",
        "case_label",
        "family",
        "profile_name",
        "package_dir",
        "time_s",
        "span_name",
        "span_kind",
        "bin_index",
        "s_start_m",
        "s_end_m",
        "s_mid_m",
        "rho_bulk_kg_m3",
        "bulk_velocity_m_s",
        "dynamic_pressure_pa",
        "p_wall_area_avg_pa",
        "p_rgh_wall_area_avg_pa",
    ]
    csv_dump(output_dir / "dynamic_pressure_profile_rows.csv", fieldnames, dynamic_rows)

    summary_rows = aggregate_summary(dynamic_rows)
    csv_dump(
        output_dir / "dynamic_pressure_profile_summary.csv",
        [
            "source_id",
            "case_label",
            "family",
            "span_name",
            "time_sample_count",
            "bin_row_count",
            "s_min_m",
            "s_max_m",
            "dynamic_pressure_mean_pa",
            "dynamic_pressure_min_pa",
            "dynamic_pressure_max_pa",
        ],
        summary_rows,
    )

    figures: list[dict[str, Any]] = []
    rows_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in dynamic_rows:
        rows_by_case[str(row["source_id"])].append(row)
    for source_id, case_rows in sorted(rows_by_case.items()):
        figure_paths = plot_case(case_rows, output_dir)
        figures.append(
            {
                "source_id": source_id,
                "case_label": case_rows[0]["case_label"],
                "family": case_rows[0]["family"],
                **figure_paths,
            }
        )
    csv_dump(output_dir / "figure_index.csv", ["source_id", "case_label", "family", "png", "svg", "pdf"], figures)

    summary_payload = {
        "generated_at": iso_timestamp(),
        "package_index": str(package_index_path),
        "case_count": len(rows_by_case),
        "family_count": len({str(row["family"]) for row in dynamic_rows}),
        "row_count": len(dynamic_rows),
        "figure_count": len(figures),
        "missing_packages": sorted(missing_packages),
        "dynamic_pressure_definition": "0.5 * rho_bulk_kg_m3 * bulk_velocity_m_s^2",
        "pressure_definition_note": "p_rgh is hydrostatic-corrected pressure, not dynamic pressure.",
    }
    json_dump(output_dir / "summary.json", summary_payload)
    build_readme(output_dir, summary_rows, missing_packages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
