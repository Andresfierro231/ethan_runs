#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    save_matplotlib_figure,
)

DENSE_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_streamwise_friction_dense_faces.py"
PATCH_BUILDER_PATH = ROOT / "tools" / "analyze" / "build_ethan_streamwise_friction_package.py"
OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_dense_streamwise_friction_package"
DEFAULT_SOURCE_ID = "val_salt_test_2_coarse_mesh_laminar"
DEFAULT_TARGET_DS_M = 0.025
EPS = 1.0e-12

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


dense_extractor = load_module("sample_streamwise_friction_dense_faces", DENSE_EXTRACTOR_PATH)
patch_builder = load_module("build_ethan_streamwise_friction_package", PATCH_BUILDER_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a denser Salt 2 streamwise friction package from reconstructed "
            "wall-face data. The package keeps `s = 0` at TP1 and bins wall-face "
            "shear along the main-loop streamwise coordinate."
        )
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--last-n-times", type=int, default=5)
    parser.add_argument("--target-ds-m", type=float, default=DEFAULT_TARGET_DS_M)
    parser.add_argument("--skip-extraction", action="store_true")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_extractor(source_id: str, last_n_times: int, output_dir: Path, skip_extraction: bool) -> tuple[Path, Path]:
    extraction_dir = ensure_dir(output_dir / "raw_extraction")
    cmd = [
        sys.executable,
        str(DENSE_EXTRACTOR_PATH),
        "--source-id",
        source_id,
        "--last-n-times",
        str(last_n_times),
        "--output-dir",
        str(extraction_dir),
    ]
    if skip_extraction:
        cmd.append("--skip-extraction")
    subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), check=True)
    return extraction_dir / "wall_face_geometry.csv", extraction_dir / "wall_face_samples.csv"


def load_station_rows() -> tuple[list[dict[str, Any]], dict[str, float], float]:
    station_centers = dense_extractor.load_station_centers()
    station_s_map, main_loop_length_m = dense_extractor.build_station_s_map(station_centers)
    rows: list[dict[str, Any]] = []
    for order_index, label in enumerate(dense_extractor.MAIN_LOOP_SEQUENCE[:-1]):
        center = station_centers[label]
        rows.append(
            {
                "station_label": label,
                "group": "TP" if label.startswith("TP") else "TW",
                "order_index": order_index,
                "s_m": float(station_s_map[label]),
                "x_m": float(center[0]),
                "y_m": float(center[1]),
                "z_m": float(center[2]),
            }
        )
    return rows, station_s_map, float(main_loop_length_m)


def build_bin_rows(main_loop_length_m: float, target_ds_m: float) -> list[dict[str, Any]]:
    bin_count = max(1, int(math.ceil(main_loop_length_m / max(target_ds_m, EPS))))
    edges = np.linspace(0.0, main_loop_length_m, bin_count + 1)
    rows: list[dict[str, Any]] = []
    for index in range(bin_count):
        rows.append(
            {
                "bin_index": index,
                "s_start_m": float(edges[index]),
                "s_end_m": float(edges[index + 1]),
                "s_mid_m": float(0.5 * (edges[index] + edges[index + 1])),
                "bin_width_m": float(edges[index + 1] - edges[index]),
            }
        )
    return rows


def load_geometry_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                "face_index": int(row["face_index"]),
                "patch_name": row["patch_name"],
                "leg_name": row["leg_name"],
                "s_leg_local_m": float(row["s_leg_local_m"]),
                "s_m": float(row["s_m"]),
                "area_m2": float(row["area_m2"]),
                "center_x_m": float(row["center_x_m"]),
                "center_y_m": float(row["center_y_m"]),
                "center_z_m": float(row["center_z_m"]),
            }
        )
    return rows


def load_sample_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                "time_s": float(row["time_s"]),
                "face_index": int(row["face_index"]),
                "patch_name": row["patch_name"],
                "leg_name": row["leg_name"],
                "s_m": float(row["s_m"]),
                "area_m2": float(row["area_m2"]),
                "center_x_m": float(row["center_x_m"]),
                "center_y_m": float(row["center_y_m"]),
                "center_z_m": float(row["center_z_m"]),
                "tauw_x_pa": float(row["tauw_x_pa"]),
                "tauw_y_pa": float(row["tauw_y_pa"]),
                "tauw_z_pa": float(row["tauw_z_pa"]),
                "tauw_streamwise_signed_pa": float(row["tauw_streamwise_signed_pa"]),
                "tauw_streamwise_abs_pa": float(row["tauw_streamwise_abs_pa"]),
                "yplus": float(row["yplus"]),
            }
        )
    return rows


def aggregate_dense_rows(
    source_id: str,
    sample_rows: list[dict[str, Any]],
    bin_rows: list[dict[str, Any]],
    bulk_rho_map: dict[float, float],
    mdot_lookup: dict[float, float],
    flow_area_m2: float,
) -> list[dict[str, Any]]:
    bin_edges = np.array([float(row["s_start_m"]) for row in bin_rows] + [float(bin_rows[-1]["s_end_m"])], dtype=float)
    grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for row in sample_rows:
        grouped[float(row["time_s"])].append(row)

    output_rows: list[dict[str, Any]] = []
    for time_value, payload in sorted(grouped.items()):
        rho_bulk = bulk_rho_map.get(time_value)
        mdot_value = mdot_lookup.get(time_value)
        if rho_bulk is None or mdot_value is None:
            continue
        velocity_bulk = abs(mdot_value) / max(rho_bulk * flow_area_m2, EPS)
        s_values = np.array([float(row["s_m"]) for row in payload], dtype=float)
        areas = np.array([float(row["area_m2"]) for row in payload], dtype=float)
        tau_signed = np.array([float(row["tauw_streamwise_signed_pa"]) for row in payload], dtype=float)
        tau_abs = np.array([float(row["tauw_streamwise_abs_pa"]) for row in payload], dtype=float)
        yplus = np.array([float(row["yplus"]) for row in payload], dtype=float)
        bin_indices = np.digitize(s_values, bin_edges, right=False) - 1
        bin_indices = np.clip(bin_indices, 0, len(bin_rows) - 1)

        for bin_row in bin_rows:
            bin_index = int(bin_row["bin_index"])
            mask = bin_indices == bin_index
            face_count = int(np.count_nonzero(mask))
            if face_count <= 0:
                output_rows.append(
                    {
                        "source_id": source_id,
                        "time_s": time_value,
                        "bin_index": bin_index,
                        "s_start_m": float(bin_row["s_start_m"]),
                        "s_end_m": float(bin_row["s_end_m"]),
                        "s_mid_m": float(bin_row["s_mid_m"]),
                        "bin_width_m": float(bin_row["bin_width_m"]),
                        "face_count": 0,
                        "wall_area_m2": 0.0,
                        "rho_bulk_kg_m3": rho_bulk,
                        "mdot_mean_abs_kg_s": mdot_value,
                        "flow_area_m2": flow_area_m2,
                        "bulk_velocity_m_s": velocity_bulk,
                        "tauw_streamwise_mean_signed_pa": math.nan,
                        "tauw_streamwise_mean_abs_pa": math.nan,
                        "tauw_streamwise_std_abs_pa": math.nan,
                        "tauw_streamwise_max_rel_dev": math.nan,
                        "darcy_f_mean": math.nan,
                        "darcy_f_std_rel": math.nan,
                        "yplus_area_avg": math.nan,
                        "yplus_max": math.nan,
                        "warning_flag": "no",
                    }
                )
                continue

            area_values = areas[mask]
            tau_signed_values = tau_signed[mask]
            tau_abs_values = tau_abs[mask]
            yplus_values = yplus[mask]
            wall_area = float(np.sum(area_values))
            tau_mean_signed = float(np.sum(area_values * tau_signed_values) / max(wall_area, EPS))
            tau_mean_abs = float(np.sum(area_values * tau_abs_values) / max(wall_area, EPS))
            tau_std_abs = float(
                math.sqrt(np.sum(area_values * (tau_abs_values - tau_mean_abs) ** 2) / max(wall_area, EPS))
            )
            tau_max_rel = float(np.max(np.abs(tau_abs_values - tau_mean_abs)) / max(tau_mean_abs, EPS))
            yplus_avg = float(np.sum(area_values * yplus_values) / max(wall_area, EPS))
            yplus_max = float(np.max(yplus_values))
            darcy_mean = float(8.0 * tau_mean_abs / max(rho_bulk * velocity_bulk * velocity_bulk, EPS))
            output_rows.append(
                {
                    "source_id": source_id,
                    "time_s": time_value,
                    "bin_index": bin_index,
                    "s_start_m": float(bin_row["s_start_m"]),
                    "s_end_m": float(bin_row["s_end_m"]),
                    "s_mid_m": float(bin_row["s_mid_m"]),
                    "bin_width_m": float(bin_row["bin_width_m"]),
                    "face_count": face_count,
                    "wall_area_m2": wall_area,
                    "rho_bulk_kg_m3": rho_bulk,
                    "mdot_mean_abs_kg_s": mdot_value,
                    "flow_area_m2": flow_area_m2,
                    "bulk_velocity_m_s": velocity_bulk,
                    "tauw_streamwise_mean_signed_pa": tau_mean_signed,
                    "tauw_streamwise_mean_abs_pa": tau_mean_abs,
                    "tauw_streamwise_std_abs_pa": tau_std_abs,
                    "tauw_streamwise_max_rel_dev": tau_max_rel,
                    "darcy_f_mean": darcy_mean,
                    "darcy_f_std_rel": float(tau_std_abs / max(tau_mean_abs, EPS)),
                    "yplus_area_avg": yplus_avg,
                    "yplus_max": yplus_max,
                    "warning_flag": "yes" if tau_max_rel > 0.20 else "no",
                }
            )
    return output_rows


def summarize_dense_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    meta: dict[int, dict[str, Any]] = {}
    for row in rows:
        bin_index = int(row["bin_index"])
        grouped[bin_index].append(row)
        meta[bin_index] = row

    summary_rows: list[dict[str, Any]] = []
    for bin_index in sorted(grouped):
        payload = grouped[bin_index]
        valid = [row for row in payload if not math.isnan(float(row["darcy_f_mean"]))]
        row0 = meta[bin_index]
        if not valid:
            summary_rows.append(
                {
                    "bin_index": bin_index,
                    "s_start_m": float(row0["s_start_m"]),
                    "s_end_m": float(row0["s_end_m"]),
                    "s_mid_m": float(row0["s_mid_m"]),
                    "bin_width_m": float(row0["bin_width_m"]),
                    "darcy_f_mean": math.nan,
                    "darcy_f_min": math.nan,
                    "darcy_f_max": math.nan,
                    "darcy_f_std": math.nan,
                    "yplus_area_avg_mean": math.nan,
                    "warning_fraction": 0.0,
                    "time_sample_count": 0,
                }
            )
            continue
        darcy_values = np.array([float(row["darcy_f_mean"]) for row in valid], dtype=float)
        yplus_values = np.array([float(row["yplus_area_avg"]) for row in valid], dtype=float)
        warning_fraction = float(sum(1 for row in valid if row["warning_flag"] == "yes") / max(len(valid), 1))
        summary_rows.append(
            {
                "bin_index": bin_index,
                "s_start_m": float(row0["s_start_m"]),
                "s_end_m": float(row0["s_end_m"]),
                "s_mid_m": float(row0["s_mid_m"]),
                "bin_width_m": float(row0["bin_width_m"]),
                "darcy_f_mean": float(np.mean(darcy_values)),
                "darcy_f_min": float(np.min(darcy_values)),
                "darcy_f_max": float(np.max(darcy_values)),
                "darcy_f_std": float(np.std(darcy_values, ddof=0)),
                "yplus_area_avg_mean": float(np.mean(yplus_values)),
                "warning_fraction": warning_fraction,
                "time_sample_count": len(valid),
            }
        )
    return summary_rows


def build_tp_landmark_rows(
    dense_rows: list[dict[str, Any]],
    station_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tp_rows = [row for row in station_rows if row["station_label"].startswith("TP")]
    grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for row in dense_rows:
        grouped[float(row["time_s"])].append(row)
    output_rows: list[dict[str, Any]] = []
    for time_value, payload in sorted(grouped.items()):
        valid = [row for row in payload if not math.isnan(float(row["darcy_f_mean"]))]
        if not valid:
            continue
        valid.sort(key=lambda row: float(row["s_mid_m"]))
        s_values = np.array([float(row["s_mid_m"]) for row in valid], dtype=float)
        friction_values = np.array([float(row["darcy_f_mean"]) for row in valid], dtype=float)
        yplus_values = np.array([float(row["yplus_area_avg"]) for row in valid], dtype=float)
        nearest_spacing = float(np.median(np.diff(s_values))) if len(s_values) > 1 else math.inf
        for station in tp_rows:
            s_station = float(station["s_m"])
            nearest_distance = float(np.min(np.abs(s_values - s_station)))
            if s_station < float(np.min(s_values)) or s_station > float(np.max(s_values)) or nearest_distance > 1.5 * nearest_spacing:
                friction_value = math.nan
                yplus_value = math.nan
            else:
                friction_value = float(np.interp(s_station, s_values, friction_values))
                yplus_value = float(np.interp(s_station, s_values, yplus_values))
            output_rows.append(
                {
                    "time_s": time_value,
                    "station_label": station["station_label"],
                    "s_m": s_station,
                    "darcy_f_mean": friction_value,
                    "yplus_area_avg": yplus_value,
                }
            )
    return output_rows


def plot_dense_profile(output_dir: Path, summary_rows: list[dict[str, Any]], station_rows: list[dict[str, Any]]) -> dict[str, str]:
    s_values = [float(row["s_mid_m"]) for row in summary_rows]
    f_mean = [float(row["darcy_f_mean"]) for row in summary_rows]
    f_min = [float(row["darcy_f_min"]) for row in summary_rows]
    f_max = [float(row["darcy_f_max"]) for row in summary_rows]
    yplus_mean = [float(row["yplus_area_avg_mean"]) for row in summary_rows]
    warning = [float(row["warning_fraction"]) for row in summary_rows]

    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True, gridspec_kw={"height_ratios": [2.2, 1.0, 0.9]})
    axes[0].plot(s_values, f_mean, color="#0b3954", linewidth=2.0)
    axes[0].fill_between(s_values, f_min, f_max, color="#0b3954", alpha=0.16)
    axes[0].set_ylabel("Darcy friction factor, f_D")
    axes[0].set_title("Salt 2 dense main-loop friction profile from retained wall-face fields")

    axes[1].plot(s_values, yplus_mean, color="#bc3908", linewidth=1.5)
    axes[1].set_ylabel("Area-avg yPlus")

    axes[2].plot(s_values, warning, color="#7a306c", linewidth=1.5)
    axes[2].set_ylabel("Warn frac")
    axes[2].set_xlabel("Streamwise distance from TP1, s [m]")
    axes[2].set_ylim(-0.02, 1.02)

    for axis in axes:
        ymin, ymax = axis.get_ylim()
        for station in station_rows:
            if not station["station_label"].startswith("TP"):
                continue
            s_value = float(station["s_m"])
            axis.axvline(s_value, color="#5c677d", linewidth=0.8, alpha=0.35)
            axis.text(
                s_value,
                ymax,
                f"{station['station_label']}\n{s_value:.2f} m",
                rotation=90,
                va="top",
                ha="right",
                fontsize=8,
                color="#33415c",
            )

    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "salt2_val_dense_main_loop_late_window_profile", dpi=220)
    plt.close(fig)
    return paths


def plot_dense_heatmap(output_dir: Path, dense_rows: list[dict[str, Any]], station_rows: list[dict[str, Any]]) -> dict[str, str]:
    times = sorted({float(row["time_s"]) for row in dense_rows})
    bins = sorted({int(row["bin_index"]) for row in dense_rows})
    s_by_bin = {int(row["bin_index"]): float(row["s_mid_m"]) for row in dense_rows}
    matrix = np.full((len(times), len(bins)), np.nan, dtype=float)
    time_index = {time_value: index for index, time_value in enumerate(times)}
    bin_index = {bin_value: index for index, bin_value in enumerate(bins)}
    for row in dense_rows:
        if math.isnan(float(row["darcy_f_mean"])):
            continue
        matrix[time_index[float(row["time_s"])], bin_index[int(row["bin_index"])]] = float(row["darcy_f_mean"])

    fig, ax = plt.subplots(figsize=(13, 4.6))
    extent = [min(s_by_bin.values()), max(s_by_bin.values()), min(times), max(times)]
    mesh = ax.imshow(matrix, aspect="auto", origin="lower", extent=extent, cmap="viridis")
    ax.set_xlabel("Streamwise distance from TP1, s [m]")
    ax.set_ylabel("Time [s]")
    ax.set_title("Salt 2 dense main-loop friction factor field over retained times")
    for station in station_rows:
        if not station["station_label"].startswith("TP"):
            continue
        ax.axvline(float(station["s_m"]), color="white", linewidth=0.8, alpha=0.5)
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label("Darcy friction factor, f_D")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "salt2_val_dense_main_loop_heatmap", dpi=220)
    plt.close(fig)
    return paths


def plot_tp_timeseries(output_dir: Path, tp_rows: list[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in tp_rows:
        grouped[str(row["station_label"])].append(row)
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    palette = ["#0b3954", "#087e8b", "#bfd7ea", "#ff5a5f", "#c81d25", "#5c415d"]
    for color, label in zip(palette, sorted(grouped)):
        payload = sorted(grouped[label], key=lambda row: float(row["time_s"]))
        axes[0].plot(
            [float(row["time_s"]) for row in payload],
            [float(row["darcy_f_mean"]) for row in payload],
            label=label,
            linewidth=1.6,
            color=color,
        )
        axes[1].plot(
            [float(row["time_s"]) for row in payload],
            [float(row["yplus_area_avg"]) for row in payload],
            label=label,
            linewidth=1.2,
            color=color,
        )
    axes[0].set_ylabel("Interpolated f_D")
    axes[0].set_title("Salt 2 dense friction at TP landmarks over retained field times")
    axes[0].legend(ncol=3, fontsize=8)
    axes[1].set_ylabel("Interpolated yPlus")
    axes[1].set_xlabel("Time [s]")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "salt2_val_dense_tp_landmark_timeseries", dpi=220)
    plt.close(fig)
    return paths


def write_implementation_notes(
    path: Path,
    source_id: str,
    target_ds_m: float,
    history_end_s: float,
    retained_times: list[float],
    flow_area_m2: float,
    main_loop_length_m: float,
    dense_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
) -> None:
    warning_rows = sum(1 for row in dense_rows if row["warning_flag"] == "yes")
    valid_summary = [row for row in summary_rows if not math.isnan(float(row["darcy_f_mean"]))]
    first_valid_s = float(valid_summary[0]["s_start_m"]) if valid_summary else math.nan
    lines = [
        "# Implementation Notes",
        "",
        f"- Source case: `{source_id}`.",
        "- Primary coordinate: main-loop streamwise distance `s` with `s = 0 m` at `TP1`.",
        "- Main-loop direction used in this package: `TP1 -> TP2 -> TP3 -> TP6 -> TP1`.",
        f"- Dense streamwise bins target a spacing of `{target_ds_m:.3f}` m over a main-loop length of `{main_loop_length_m:.3f}` m.",
        f"- Retained wall-field times sampled in this package: `{', '.join(f'{value:g}' for value in retained_times)}` s.",
        f"- Merged continuation probe and mdot histories extend through `{history_end_s:g}` s.",
        "- Darcy friction factor is reported as `f_D = 8 tau_w / (rho U^2)`.",
        "- `tau_w` is built from wall-face `wallShearStress` values projected onto the TP-anchored legwise streamwise direction, then area-averaged within each dense `s` bin.",
        "- `rho` is reconstructed from the merged TP bulk-temperature history using the case density law `rho(T) = 2293.6 - 0.7497 T`.",
        "- `U` is derived from the merged mean absolute mdot history and a fixed bulk flow area from the mdot face-zone monitor.",
        f"- Bulk flow area used: `{flow_area_m2:.9e}` m^2.",
        "- `warning_flag=yes` marks dense bins where the retained wall-face streamwise shear deviates by more than 20% from the area-weighted bin mean at that time.",
        f"- Warning rows in the dense timeseries: `{warning_rows}` of `{len(dense_rows)}`.",
        f"- Dense main-loop wall coverage first appears at `s = {first_valid_s:.3f}` m in this implementation; `TP1` is the coordinate origin, but the lower-left corner/junction wall surfaces are not yet included in the dense main-loop patch set.",
        "- This dense pass still uses a legwise projected `s` coordinate through bends and connectors; the next pass can replace the station generator with a centerline-based or slice-based sampler without changing the CSV contract.",
        "- The retained-time limitation remains: this package is late-window resolved in space, while the long mdot/temperature context is still provided separately for the full continuation history.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    geometry_path, samples_path = run_extractor(args.source_id, args.last_n_times, output_dir, args.skip_extraction)
    geometry_rows = load_geometry_rows(geometry_path)
    sample_rows = load_sample_rows(samples_path)

    runtime_root = patch_builder.extractor.load_runtime_root(args.source_id)
    station_rows, station_s_map, main_loop_length_m = load_station_rows()
    bin_rows = build_bin_rows(main_loop_length_m, args.target_ds_m)
    mdot_rows, flow_area_m2 = patch_builder.build_mdot_series(runtime_root)
    mdot_lookup = {float(row["time_s"]): float(row["mdot_mean_abs_kg_s"]) for row in mdot_rows}
    tp_rows, tw_rows = patch_builder.build_temperature_rows(runtime_root)
    bulk_rho_map = patch_builder.build_tp_bulk_rho_map(tp_rows)
    dense_rows = aggregate_dense_rows(args.source_id, sample_rows, bin_rows, bulk_rho_map, mdot_lookup, flow_area_m2)
    summary_rows = summarize_dense_rows(dense_rows)
    tp_landmark_rows = build_tp_landmark_rows(dense_rows, station_rows)

    csv_dump(
        output_dir / "main_loop_station_definitions.csv",
        ["station_label", "group", "order_index", "s_m", "x_m", "y_m", "z_m"],
        station_rows,
    )
    csv_dump(
        output_dir / "main_loop_dense_bin_definitions.csv",
        ["bin_index", "s_start_m", "s_end_m", "s_mid_m", "bin_width_m"],
        bin_rows,
    )
    csv_dump(
        output_dir / "main_loop_dense_friction_timeseries.csv",
        [
            "source_id",
            "time_s",
            "bin_index",
            "s_start_m",
            "s_end_m",
            "s_mid_m",
            "bin_width_m",
            "face_count",
            "wall_area_m2",
            "rho_bulk_kg_m3",
            "mdot_mean_abs_kg_s",
            "flow_area_m2",
            "bulk_velocity_m_s",
            "tauw_streamwise_mean_signed_pa",
            "tauw_streamwise_mean_abs_pa",
            "tauw_streamwise_std_abs_pa",
            "tauw_streamwise_max_rel_dev",
            "darcy_f_mean",
            "darcy_f_std_rel",
            "yplus_area_avg",
            "yplus_max",
            "warning_flag",
        ],
        dense_rows,
    )
    csv_dump(
        output_dir / "main_loop_dense_friction_summary.csv",
        [
            "bin_index",
            "s_start_m",
            "s_end_m",
            "s_mid_m",
            "bin_width_m",
            "darcy_f_mean",
            "darcy_f_min",
            "darcy_f_max",
            "darcy_f_std",
            "yplus_area_avg_mean",
            "warning_fraction",
            "time_sample_count",
        ],
        summary_rows,
    )
    csv_dump(
        output_dir / "tp_landmark_friction_timeseries.csv",
        ["time_s", "station_label", "s_m", "darcy_f_mean", "yplus_area_avg"],
        tp_landmark_rows,
    )
    csv_dump(
        output_dir / "loop_bulk_timeseries.csv",
        ["time_s", "mdot_mean_abs_kg_s"],
        mdot_rows,
    )
    csv_dump(
        output_dir / "tp_temperature_timeseries.csv",
        ["time_s", *patch_builder.TP_LABELS],
        tp_rows,
    )
    tw_fieldnames = sorted({key for row in tw_rows for key in row if key != "time_s"})
    csv_dump(
        output_dir / "tw_temperature_timeseries.csv",
        ["time_s", *tw_fieldnames],
        tw_rows,
    )

    profile_paths = plot_dense_profile(output_dir, summary_rows, station_rows)
    heatmap_paths = plot_dense_heatmap(output_dir, dense_rows, station_rows)
    tp_paths = plot_tp_timeseries(output_dir, tp_landmark_rows)
    context_paths = patch_builder.plot_bulk_context(output_dir, mdot_rows, tp_rows)

    retained_times = sorted({float(row["time_s"]) for row in dense_rows})
    history_end_s = max(float(row["time_s"]) for row in mdot_rows)
    write_implementation_notes(
        output_dir / "implementation_notes.md",
        args.source_id,
        float(args.target_ds_m),
        history_end_s,
        retained_times,
        flow_area_m2,
        main_loop_length_m,
        dense_rows,
        summary_rows,
    )
    valid_summary = [row for row in summary_rows if not math.isnan(float(row["darcy_f_mean"]))]
    first_valid_s = float(valid_summary[0]["s_start_m"]) if valid_summary else math.nan
    summary = {
        "generated_at": iso_timestamp(),
        "source_id": args.source_id,
        "runtime_root": str(runtime_root),
        "history_time_end_s": history_end_s,
        "retained_field_times_s": retained_times,
        "target_ds_m": float(args.target_ds_m),
        "main_loop_total_length_m": main_loop_length_m,
        "bin_count": len(bin_rows),
        "face_count": len(geometry_rows),
        "sample_row_count": len(sample_rows),
        "valid_bin_count": len(valid_summary),
        "first_valid_s_m": first_valid_s,
        "flow_area_m2": flow_area_m2,
        "equivalent_circular_diameter_m": float(math.sqrt(4.0 * flow_area_m2 / math.pi)),
        "tp_landmarks_m": {row["station_label"]: float(row["s_m"]) for row in station_rows if row["station_label"].startswith("TP")},
        "figure_paths": {
            "late_window_profile": profile_paths,
            "heatmap": heatmap_paths,
            "tp_landmark_timeseries": tp_paths,
            "bulk_context": context_paths,
        },
        "warning_note": "warning_flag=yes marks >20% max relative deviation of retained wall-face streamwise shear inside a dense s-bin; this is stronger than the v1 patchwise proxy but still not a slice-normal circumferential average.",
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
