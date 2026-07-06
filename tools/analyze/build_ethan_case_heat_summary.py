#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.case_analysis_profiles import (  # noqa: E402
    DEFAULT_HEAT_WINDOW_COUNT,
    DEFAULT_SOURCE_ID,
    get_case_analysis_profile,
    resolve_case_paths,
)
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, safe_float, save_matplotlib_figure  # noqa: E402


s2 = __import__("tools.analyze.build_salt2_behavior_package", fromlist=["dummy"])  # noqa: E402

VALIDATION_CSV = ROOT / "reports" / "2026-06-04_ethan_direct_validation" / "ethan_direct_validation_metrics.csv"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-10_ethan_salt2_case_analysis_package"

PRIMARY_HEAT_KEYS = [
    "ambient_proxy_w",
    "ambient_noncooling_proxy_w",
    "cooling_branch_total_removal_w",
    "cooling_branch_excess_w",
    "net_total_q_w",
    "section_downcomer_net_q_w",
    "section_heater_net_q_w",
    "section_upcomer_net_q_w",
    "section_test_section_net_q_w",
    "section_cooling_branch_net_q_w",
    "section_upper_transport_net_q_w",
    "section_lower_transport_net_q_w",
    "section_junctions_net_q_w",
    "section_other_net_q_w",
]

PLOT_SECTION_KEYS = [
    "section_heater_net_q_w",
    "ambient_proxy_w",
    "section_cooling_branch_net_q_w",
    "section_test_section_net_q_w",
    "section_junctions_net_q_w",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a case-scoped heat-loss summary using the current wallHeatFlux tail."
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--window-count", type=int, default=DEFAULT_HEAT_WINDOW_COUNT)
    parser.add_argument(
        "--runtime-root",
        help="Optional runtime-root override for continuation or packed relaunch case trees.",
    )
    parser.add_argument(
        "--validation-csv",
        default=str(VALIDATION_CSV),
        help=(
            "Optional validation-reference CSV. When missing or when the source_id row is absent, "
            "the heat summary is still generated and records that validation provenance is unavailable."
        ),
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: object) -> float | None:
    return safe_float(value)


def window_status(sample_count: int, target: int) -> str:
    if sample_count <= 0:
        return "missing"
    if sample_count == 1:
        return "latest_only"
    if sample_count < target:
        return "short_window"
    return "usable_window"


def load_validation_reference(source_id: str, validation_csv: Path) -> tuple[dict[str, str], str]:
    if not validation_csv.exists():
        return {}, "missing_validation_csv"
    validation_rows = {row["source_id"]: row for row in load_csv_rows(validation_csv) if row.get("source_id")}
    row = validation_rows.get(source_id)
    if not row:
        return {}, "missing_source_validation_row"
    return row, "available"


def compute_window_stats(times: np.ndarray, values: np.ndarray, target: int) -> dict[str, object]:
    sample_count = len(times)
    if sample_count == 0:
        return {
            "window_count": 0,
            "time_start_s": "",
            "time_end_s": "",
            "latest_value": "",
            "mean_value": "",
            "min_value": "",
            "max_value": "",
            "span_value": "",
            "drift_value": "",
            "drift_pct_of_mean": "",
            "slope_per_s": "",
        }
    count = min(target, sample_count)
    t = times[-count:]
    v = values[-count:]
    mean_value = float(np.mean(v))
    min_value = float(np.min(v))
    max_value = float(np.max(v))
    drift = float(v[-1] - v[0]) if count >= 2 else 0.0
    span = max_value - min_value
    slope = float(np.polyfit(t, v, 1)[0]) if count >= 2 else 0.0
    return {
        "window_count": count,
        "time_start_s": float(t[0]),
        "time_end_s": float(t[-1]),
        "latest_value": float(v[-1]),
        "mean_value": mean_value,
        "min_value": min_value,
        "max_value": max_value,
        "span_value": span,
        "drift_value": drift,
        "drift_pct_of_mean": float(drift / mean_value * 100.0) if abs(mean_value) > 1.0e-12 else "",
        "slope_per_s": slope,
    }


def plot_heat_sections(output_dir: Path, heat_rows: list[dict[str, float]]) -> dict[str, str]:
    if not heat_rows:
        return {}
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    times = np.array([float(row["time"]) for row in heat_rows], dtype=float)
    for key, color in zip(PLOT_SECTION_KEYS, ["#bc3908", "#0b3954", "#2a9d8f", "#f4a261", "#6d597a"]):
        values = np.array([float(row[key]) for row in heat_rows], dtype=float)
        ax.plot(times, values, linewidth=1.9, label=key.replace("_w", "").replace("section_", ""), color=color)
    ax.set_title("Case heat-loss summary over wallHeatFlux tail")
    ax.set_xlabel("Simulation time [s]")
    ax.set_ylabel("Heat [W]")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "case_heat_loss_summary", dpi=180)
    plt.close(fig)
    return paths


def build_case_heat_summary(
    source_id: str,
    output_dir: Path,
    window_count: int,
    validation_csv: Path = VALIDATION_CSV,
    runtime_root_override: Path | None = None,
) -> dict[str, Any]:
    profile = get_case_analysis_profile(source_id)
    source_root, resolved_runtime_root, metadata = resolve_case_paths(source_id)
    runtime_root = runtime_root_override.resolve() if runtime_root_override else resolved_runtime_root
    heat_rows = s2.parse_wall_heatflux_section_series(runtime_root, metadata)
    validation_row, validation_status = load_validation_reference(source_id, validation_csv)

    ensure_dir(output_dir)
    if not heat_rows:
        summary = {
            "generated_at": iso_timestamp(),
            "profile_name": profile.profile_name,
            "source_id": source_id,
            "source_root": str(source_root),
            "runtime_root": str(runtime_root),
            "heat_window_count": window_count,
            "validation_reference_status": validation_status,
            "validation_reference_source": str(validation_csv),
            "warning": "wallHeatFlux history is missing",
            "figure_paths": {},
        }
        json_dump(output_dir / "heat_loss_summary.json", summary)
        return summary

    heat_times = np.array([float(row["time"]) for row in heat_rows], dtype=float)
    steady_window = window_status(len(heat_rows), window_count)
    window_rows: list[dict[str, object]] = []
    for key in PRIMARY_HEAT_KEYS:
        values = np.array([float(row[key]) for row in heat_rows], dtype=float)
        window_rows.append(
            {
                "source_id": source_id,
                "metric": key,
                **compute_window_stats(heat_times, values, window_count),
            }
        )

    latest_row = dict(heat_rows[-1])
    latest_row["time_s"] = latest_row.pop("time")
    ambient_proxy_w = as_float(latest_row.get("ambient_proxy_w"))
    ambient_reference_w = as_float(validation_row.get("exp_q_external_loss_reference_w"))
    ambient_error_w = (
        ambient_proxy_w - ambient_reference_w
        if ambient_proxy_w is not None and ambient_reference_w is not None
        else ""
    )
    ambient_error_pct = ""
    if ambient_error_w != "" and ambient_reference_w not in (None, 0.0):
        ambient_error_pct = ambient_error_w / ambient_reference_w * 100.0
    heater_section_q_w = as_float(latest_row.get("section_heater_net_q_w"))
    net_total_q_w = as_float(latest_row.get("net_total_q_w"))
    validation_final_time_s = as_float(validation_row.get("final_time"))
    validation_reference_lag_s = ""
    latest_heat_time_s = as_float(latest_row.get("time_s"))
    if latest_heat_time_s is not None and validation_final_time_s is not None:
        validation_reference_lag_s = float(latest_heat_time_s - validation_final_time_s)
    net_total_q_pct_of_heater = ""
    if net_total_q_w is not None and heater_section_q_w not in (None, 0.0):
        net_total_q_pct_of_heater = net_total_q_w / heater_section_q_w * 100.0

    summary_row = {
        "source_id": source_id,
        "profile_name": profile.profile_name,
        "runtime_root": str(runtime_root),
        "latest_heat_time_s": latest_row["time_s"],
        "steady_window_status": steady_window,
        "validation_reference_status": validation_status,
        "validation_reference_source": str(validation_csv),
        "validation_reference_lag_s": validation_reference_lag_s,
        "ambient_proxy_w": latest_row.get("ambient_proxy_w", ""),
        "exp_q_external_loss_reference_w": validation_row.get("exp_q_external_loss_reference_w", ""),
        "ambient_error_w": ambient_error_w,
        "ambient_error_pct": ambient_error_pct,
        "cooling_branch_total_removal_w": latest_row.get("cooling_branch_total_removal_w", ""),
        "section_heater_net_q_w": latest_row.get("section_heater_net_q_w", ""),
        "section_test_section_net_q_w": latest_row.get("section_test_section_net_q_w", ""),
        "section_junctions_net_q_w": latest_row.get("section_junctions_net_q_w", ""),
        "net_total_q_pct_of_heater": net_total_q_pct_of_heater,
        "exp_tw_rmse_k": validation_row.get("exp_tw_rmse_k", ""),
        "validation_reference_final_time_s": validation_row.get("final_time", ""),
    }
    figure_paths = plot_heat_sections(output_dir, heat_rows)
    summary = {
        "generated_at": iso_timestamp(),
        "profile_name": profile.profile_name,
        "source_id": source_id,
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "heat_window_count": window_count,
        "validation_reference_status": validation_status,
        "validation_reference_source": str(validation_csv),
        "validation_reference_lag_s": validation_reference_lag_s,
        "latest_heat_time_s": latest_row["time_s"],
        "steady_window_status": steady_window,
        "latest_summary": summary_row,
        "validation_reference": validation_row,
        "figure_paths": figure_paths,
    }

    csv_dump(
        output_dir / "heat_loss_timeseries.csv",
        ["time"] + [key for key in heat_rows[0].keys() if key != "time"],
        heat_rows,
    )
    csv_dump(
        output_dir / "heat_loss_window_summary.csv",
        list(window_rows[0].keys()),
        window_rows,
    )
    csv_dump(
        output_dir / "heat_loss_summary.csv",
        list(summary_row.keys()),
        [summary_row],
    )
    json_dump(output_dir / "heat_loss_summary.json", summary)
    return summary


def main() -> int:
    args = parse_args()
    runtime_root_override = Path(args.runtime_root).resolve() if args.runtime_root else None
    build_case_heat_summary(
        args.source_id,
        Path(args.output_dir),
        args.window_count,
        Path(args.validation_csv),
        runtime_root_override=runtime_root_override,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
