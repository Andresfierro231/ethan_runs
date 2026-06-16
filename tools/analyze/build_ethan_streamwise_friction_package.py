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
    safe_float,
)

EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_streamwise_friction_patch_averages.py"
TP_TW_LOCATIONS = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "tp_tw_probe_locations.csv"
OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_streamwise_friction_package"
DEFAULT_SOURCE_ID = "val_salt_test_2_coarse_mesh_laminar"
MAIN_LOOP_SEQUENCE = [
    "TP1",
    "TW1",
    "TW2",
    "TW3",
    "TP2",
    "TW4",
    "TW5",
    "TW6",
    "TP3",
    "TW7",
    "TP4",
    "TP5",
    "TW8",
    "TP6",
    "TW11",
    "TW10",
    "TW9",
    "TP1",
]
TP_LABELS = [f"TP{i}" for i in range(1, 7)]
LEG_PATCH_MAP = {
    "lower_leg": [
        "pipeleg_lower_01_fitting",
        "pipeleg_lower_02_straight",
        "pipeleg_lower_03_bend",
        "pipeleg_lower_04_straight",
        "pipeleg_lower_05_straight",
        "pipeleg_lower_06_straight",
        "pipeleg_lower_07_bend",
        "pipeleg_lower_08_straight",
        "pipeleg_lower_09_fitting",
    ],
    "right_leg": [
        "pipeleg_right_01_lower",
        "pipeleg_right_02_middle",
        "pipeleg_right_03_upper",
    ],
    "left_leg": [
        "pipeleg_left_07_lower",
        "pipeleg_left_06_connector",
        "pipeleg_left_02_connector",
        "pipeleg_left_01_upper",
    ],
    "upper_leg": [
        "pipeleg_upper_09_straight",
        "pipeleg_upper_08_bend",
        "pipeleg_upper_07_straight",
        "pipeleg_upper_06_reducer",
        "pipeleg_upper_05_cooler",
        "pipeleg_upper_04_reducer",
        "pipeleg_upper_03_straight",
        "pipeleg_upper_02_bend",
        "pipeleg_upper_01_straight",
    ],
}
LEG_TP_BOUNDS = {
    "lower_leg": ("TP1", "TP2"),
    "right_leg": ("TP2", "TP3"),
    "left_leg": ("TP3", "TP6"),
    "upper_leg": ("TP6", "TP1"),
}
BRANCH_PATCHES = [
    "pipeleg_left_03_fitting",
    "pipeleg_left_04_test_section",
    "pipeleg_left_05_fitting",
]
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


extractor = load_module("sample_streamwise_friction_patch_averages", EXTRACTOR_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the first Salt 2 streamwise-friction package. This merges chunked "
            "continuation histories, samples retained latest-time wall-shear fields by "
            "patch, and reports Darcy friction factor along the TP1-anchored main loop."
        )
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--last-n-times", type=int, default=5)
    parser.add_argument("--skip-extraction", action="store_true")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_probe_chunk(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                continue
            time_value = safe_float(parts[0])
            values = [safe_float(item) for item in parts[1:]]
            if time_value is None or any(value is None for value in values):
                continue
            rows.append({"time": float(time_value), "values": [float(value) for value in values if value is not None]})
    return rows


def merge_probe_chunks(root: Path, relative_dir: str, suffix: str) -> list[dict[str, Any]]:
    merged: dict[float, list[float]] = {}
    target_root = root / "postProcessing" / relative_dir
    if not target_root.exists():
        return []
    time_dirs: list[tuple[float, Path]] = []
    for item in target_root.iterdir():
        if not item.is_dir():
            continue
        try:
            time_dirs.append((float(item.name), item))
        except ValueError:
            continue
    for _, item in sorted(time_dirs):
        for row in parse_probe_chunk(item / suffix):
            merged[row["time"]] = row["values"]
    return [{"time": time_value, "values": merged[time_value]} for time_value in sorted(merged)]


def parse_scalar_chunk(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                continue
            time_value = safe_float(parts[0])
            scalar_value = safe_float(parts[1])
            if time_value is None or scalar_value is None:
                continue
            rows.append({"time": float(time_value), "value": float(scalar_value)})
    return rows


def merge_scalar_chunks(root: Path, relative_dir: str, suffix: str) -> list[dict[str, float]]:
    merged: dict[float, float] = {}
    target_root = root / "postProcessing" / relative_dir
    if not target_root.exists():
        return []
    time_dirs: list[tuple[float, Path]] = []
    for item in target_root.iterdir():
        if not item.is_dir():
            continue
        try:
            time_dirs.append((float(item.name), item))
        except ValueError:
            continue
    for _, item in sorted(time_dirs):
        for row in parse_scalar_chunk(item / suffix):
            merged[row["time"]] = row["value"]
    return [{"time": time_value, "value": merged[time_value]} for time_value in sorted(merged)]


def parse_surface_area(path: Path) -> float:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("# Area"):
                value = safe_float(stripped.split(":", 1)[1].strip())
                if value is not None:
                    return float(value)
    raise RuntimeError(f"Failed to parse face-zone area from {path}")


def load_station_centers() -> dict[str, tuple[float, float, float]]:
    grouped: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    with TP_TW_LOCATIONS.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            label = row["label"]
            x_value = float(row["x_m"])
            y_value = float(row["y_m"])
            z_value = float(row["z_m"])
            if row["group"] == "TP":
                grouped[label].append((x_value, y_value, z_value))
            else:
                station = label.split("_", 1)[0]
                grouped[station].append((x_value, y_value, z_value))
    centers: dict[str, tuple[float, float, float]] = {}
    for label, coords in grouped.items():
        xs = [item[0] for item in coords]
        ys = [item[1] for item in coords]
        zs = [item[2] for item in coords]
        centers[label] = (float(np.mean(xs)), float(np.mean(ys)), float(np.mean(zs)))
    return centers


def distance(point_a: tuple[float, float, float], point_b: tuple[float, float, float]) -> float:
    return math.sqrt(
        (point_b[0] - point_a[0]) ** 2
        + (point_b[1] - point_a[1]) ** 2
        + (point_b[2] - point_a[2]) ** 2
    )


def unit_vector(point_a: tuple[float, float, float], point_b: tuple[float, float, float]) -> tuple[float, float, float]:
    delta = np.array([point_b[0] - point_a[0], point_b[1] - point_a[1], point_b[2] - point_a[2]], dtype=float)
    norm = float(np.linalg.norm(delta))
    if norm <= 0.0:
        raise RuntimeError(f"Zero-length tangent between {point_a} and {point_b}")
    values = delta / norm
    return float(values[0]), float(values[1]), float(values[2])


def build_station_rows(station_centers: dict[str, tuple[float, float, float]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cumulative = 0.0
    for index, label in enumerate(MAIN_LOOP_SEQUENCE[:-1]):
        next_label = MAIN_LOOP_SEQUENCE[index + 1]
        point = station_centers[label]
        rows.append(
            {
                "station_label": label,
                "order_index": index,
                "x_m": point[0],
                "y_m": point[1],
                "z_m": point[2],
                "s_m": cumulative,
            }
        )
        cumulative += distance(point, station_centers[next_label])
    return rows


def station_s_map(station_rows: list[dict[str, Any]]) -> dict[str, float]:
    return {str(row["station_label"]): float(row["s_m"]) for row in station_rows}


def build_patch_positions(station_rows: list[dict[str, Any]], station_centers: dict[str, tuple[float, float, float]]) -> tuple[list[dict[str, Any]], dict[str, tuple[float, float, float]]]:
    s_map = station_s_map(station_rows)
    tangent_map = {
        leg_name: unit_vector(station_centers[start_label], station_centers[end_label])
        for leg_name, (start_label, end_label) in LEG_TP_BOUNDS.items()
    }
    rows: list[dict[str, Any]] = []
    for leg_name, patch_names in LEG_PATCH_MAP.items():
        start_label, end_label = LEG_TP_BOUNDS[leg_name]
        leg_start = s_map[start_label]
        leg_end = s_map[end_label]
        patch_count = len(patch_names)
        leg_length = leg_end - leg_start
        for index, patch_name in enumerate(patch_names):
            start_fraction = index / patch_count
            end_fraction = (index + 1) / patch_count
            patch_start = leg_start + leg_length * start_fraction
            patch_end = leg_start + leg_length * end_fraction
            patch_mid = 0.5 * (patch_start + patch_end)
            rows.append(
                {
                    "patch_name": patch_name,
                    "leg_name": leg_name,
                    "patch_index_in_leg": index + 1,
                    "patch_count_in_leg": patch_count,
                    "s_start_m": patch_start,
                    "s_end_m": patch_end,
                    "s_mid_m": patch_mid,
                    "tangent_x": tangent_map[leg_name][0],
                    "tangent_y": tangent_map[leg_name][1],
                    "tangent_z": tangent_map[leg_name][2],
                }
            )
    return rows, tangent_map


def run_extractor(source_id: str, last_n_times: int, output_dir: Path, skip_extraction: bool) -> Path:
    extraction_dir = ensure_dir(output_dir / "raw_extraction")
    cmd = [
        sys.executable,
        str(EXTRACTOR_PATH),
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
    return extraction_dir / "surface_reductions.csv"


def load_reduction_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "x": safe_float(row["x"]),
                "y": safe_float(row["y"]),
                "z": safe_float(row["z"]),
                "scalar": safe_float(row["scalar"]),
            }
        )
    return rows


def vector_norm(x_value: float | None, y_value: float | None, z_value: float | None) -> float:
    return float(math.sqrt((x_value or 0.0) ** 2 + (y_value or 0.0) ** 2 + (z_value or 0.0) ** 2))


def dot_with_tangent(row: dict[str, Any], tangent: tuple[float, float, float]) -> float:
    x_value = float(row.get("x") or 0.0)
    y_value = float(row.get("y") or 0.0)
    z_value = float(row.get("z") or 0.0)
    return x_value * tangent[0] + y_value * tangent[1] + z_value * tangent[2]


def build_reduction_lookup(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str, float], dict[str, Any]]:
    lookup: dict[tuple[str, str, str, float], dict[str, Any]] = {}
    for row in rows:
        key = (
            str(row["target_name"]),
            str(row["field_name"]),
            str(row["operation"]),
            float(row["time_s"]),
        )
        lookup[key] = row
    return lookup


def build_mdot_series(runtime_root: Path) -> tuple[list[dict[str, float]], float]:
    grouped: dict[float, list[float]] = defaultdict(list)
    areas: list[float] = []
    for face_zone in extractor.FACE_ZONES:
        relative_dir = f"{face_zone}"
        rows = merge_scalar_chunks(runtime_root, relative_dir, "surfaceFieldValue.dat")
        target_root = runtime_root / "postProcessing" / relative_dir
        time_dirs = sorted(
            (
                float(item.name),
                item / "surfaceFieldValue.dat",
            )
            for item in target_root.iterdir()
            if item.is_dir() and safe_float(item.name) is not None
        )
        if time_dirs:
            areas.append(parse_surface_area(time_dirs[-1][1]))
        for row in rows:
            grouped[row["time"]].append(abs(row["value"]))
    if not grouped or not areas:
        raise RuntimeError("Mass-flow face-zone histories were not available for the requested case.")
    merged_rows = [{"time_s": time_value, "mdot_mean_abs_kg_s": float(np.mean(values))} for time_value, values in sorted(grouped.items())]
    return merged_rows, float(np.mean(areas))


def build_temperature_rows(runtime_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tp_chunks = merge_probe_chunks(runtime_root, "temperature_probes", "T")
    tw_chunks = merge_probe_chunks(runtime_root, "wall_temperature_probes", "T")
    tp_rows: list[dict[str, Any]] = []
    tw_rows: list[dict[str, Any]] = []
    for row in tp_chunks:
        payload = {"time_s": row["time"]}
        for index, label in enumerate(TP_LABELS):
            if index < len(row["values"]):
                payload[label] = row["values"][index]
        tp_rows.append(payload)
    wall_probe_order = []
    with TP_TW_LOCATIONS.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["group"] == "TW":
                wall_probe_order.append(row["label"])
    for row in tw_chunks:
        grouped: dict[str, list[float]] = defaultdict(list)
        for index, value in enumerate(row["values"]):
            label = wall_probe_order[index] if index < len(wall_probe_order) else f"TW_unknown_{index}"
            grouped[label.split("_", 1)[0]].append(float(value))
        payload = {"time_s": row["time"]}
        for station, values in grouped.items():
            payload[station] = float(np.mean(values))
        tw_rows.append(payload)
    return tp_rows, tw_rows


def make_history_lookup(rows: list[dict[str, Any]], value_key: str) -> dict[float, dict[str, float]]:
    lookup: dict[float, dict[str, float]] = {}
    for row in rows:
        payload: dict[str, float] = {}
        for key, value in row.items():
            if key == "time_s":
                continue
            if isinstance(value, (int, float)):
                payload[key] = float(value)
        lookup[float(row["time_s"])] = payload
    return lookup


def build_tp_bulk_rho_map(tp_rows: list[dict[str, Any]]) -> dict[float, float]:
    rho_map: dict[float, float] = {}
    for row in tp_rows:
        values = [float(row[label]) for label in TP_LABELS if label in row and safe_float(row[label]) is not None]
        if not values:
            continue
        mean_tp = float(np.mean(values))
        rho_map[float(row["time_s"])] = 2293.6 - 0.7497 * mean_tp
    return rho_map


def build_patch_friction_rows(
    source_id: str,
    patch_rows: list[dict[str, Any]],
    reduction_lookup: dict[tuple[str, str, str, float], dict[str, Any]],
    bulk_rho_map: dict[float, float],
    mdot_lookup: dict[float, float],
    flow_area_m2: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for patch in patch_rows:
        tangent = (patch["tangent_x"], patch["tangent_y"], patch["tangent_z"])
        for time_value in sorted(bulk_rho_map):
            avg_row = reduction_lookup.get((patch["patch_name"], "wallShearStress", "areaAverage", time_value))
            min_row = reduction_lookup.get((patch["patch_name"], "wallShearStress", "min", time_value))
            max_row = reduction_lookup.get((patch["patch_name"], "wallShearStress", "max", time_value))
            yplus_avg = reduction_lookup.get((patch["patch_name"], "yPlus", "areaAverage", time_value))
            yplus_max = reduction_lookup.get((patch["patch_name"], "yPlus", "max", time_value))
            mdot_value = mdot_lookup.get(time_value)
            rho_bulk = bulk_rho_map.get(time_value)
            if avg_row is None or mdot_value is None or rho_bulk is None:
                continue
            tau_streamwise_signed = dot_with_tangent(avg_row, tangent)
            tau_streamwise_abs = abs(tau_streamwise_signed)
            velocity_bulk = abs(mdot_value) / max(rho_bulk * flow_area_m2, EPS)
            friction_factor = 8.0 * tau_streamwise_abs / max(rho_bulk * velocity_bulk * velocity_bulk, EPS)
            avg_norm = vector_norm(avg_row.get("x"), avg_row.get("y"), avg_row.get("z"))
            min_norm = vector_norm(min_row.get("x"), min_row.get("y"), min_row.get("z")) if min_row else math.nan
            max_norm = vector_norm(max_row.get("x"), max_row.get("y"), max_row.get("z")) if max_row else math.nan
            spread_proxy_rel = float(
                max(abs(max_norm - avg_norm), abs(min_norm - avg_norm)) / max(avg_norm, EPS)
            ) if not math.isnan(min_norm) and not math.isnan(max_norm) else math.nan
            yplus_avg_value = float(yplus_avg["scalar"]) if yplus_avg and safe_float(yplus_avg["scalar"]) is not None else math.nan
            yplus_max_value = float(yplus_max["scalar"]) if yplus_max and safe_float(yplus_max["scalar"]) is not None else math.nan
            yplus_ratio = float(yplus_max_value / max(yplus_avg_value, EPS)) if not math.isnan(yplus_avg_value) and not math.isnan(yplus_max_value) else math.nan
            warning_flag = (
                (not math.isnan(spread_proxy_rel) and spread_proxy_rel > 0.20)
                or (not math.isnan(yplus_ratio) and yplus_ratio > 5.0)
            )
            rows.append(
                {
                    "source_id": source_id,
                    "time_s": time_value,
                    "patch_name": patch["patch_name"],
                    "leg_name": patch["leg_name"],
                    "patch_index_in_leg": patch["patch_index_in_leg"],
                    "patch_count_in_leg": patch["patch_count_in_leg"],
                    "s_start_m": patch["s_start_m"],
                    "s_end_m": patch["s_end_m"],
                    "s_mid_m": patch["s_mid_m"],
                    "tangent_x": tangent[0],
                    "tangent_y": tangent[1],
                    "tangent_z": tangent[2],
                    "rho_bulk_kg_m3": rho_bulk,
                    "mdot_mean_abs_kg_s": mdot_value,
                    "flow_area_m2": flow_area_m2,
                    "bulk_velocity_m_s": velocity_bulk,
                    "tauw_streamwise_signed_pa": tau_streamwise_signed,
                    "tauw_streamwise_abs_pa": tau_streamwise_abs,
                    "darcy_f": friction_factor,
                    "wall_shear_avg_vector_norm_pa": avg_norm,
                    "wall_shear_min_vector_norm_pa": min_norm,
                    "wall_shear_max_vector_norm_pa": max_norm,
                    "wall_shear_spread_proxy_rel": spread_proxy_rel,
                    "yplus_avg": yplus_avg_value,
                    "yplus_max": yplus_max_value,
                    "yplus_max_over_avg": yplus_ratio,
                    "warning_flag": "yes" if warning_flag else "no",
                }
            )
    return rows


def summarize_patch_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    patch_meta: dict[str, dict[str, Any]] = {}
    for row in rows:
        patch_name = str(row["patch_name"])
        grouped[patch_name].append(row)
        patch_meta[patch_name] = row
    summary_rows: list[dict[str, Any]] = []
    for patch_name, payload_rows in sorted(grouped.items(), key=lambda item: float(patch_meta[item[0]]["s_mid_m"])):
        friction_values = np.array([float(item["darcy_f"]) for item in payload_rows], dtype=float)
        yplus_values = np.array([float(item["yplus_avg"]) for item in payload_rows], dtype=float)
        warning_count = sum(1 for item in payload_rows if item["warning_flag"] == "yes")
        meta = patch_meta[patch_name]
        summary_rows.append(
            {
                "patch_name": patch_name,
                "leg_name": meta["leg_name"],
                "s_start_m": meta["s_start_m"],
                "s_end_m": meta["s_end_m"],
                "s_mid_m": meta["s_mid_m"],
                "darcy_f_mean": float(np.mean(friction_values)),
                "darcy_f_min": float(np.min(friction_values)),
                "darcy_f_max": float(np.max(friction_values)),
                "darcy_f_std": float(np.std(friction_values, ddof=0)),
                "yplus_avg_mean": float(np.mean(yplus_values)),
                "warning_fraction": float(warning_count / max(len(payload_rows), 1)),
                "time_sample_count": len(payload_rows),
            }
        )
    return summary_rows


def plot_main_loop_profile(output_dir: Path, patch_summary_rows: list[dict[str, Any]], station_rows: list[dict[str, Any]]) -> dict[str, str]:
    s_values = [float(row["s_mid_m"]) for row in patch_summary_rows]
    f_mean = [float(row["darcy_f_mean"]) for row in patch_summary_rows]
    f_min = [float(row["darcy_f_min"]) for row in patch_summary_rows]
    f_max = [float(row["darcy_f_max"]) for row in patch_summary_rows]
    yplus_values = [float(row["yplus_avg_mean"]) for row in patch_summary_rows]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [2.2, 1.0]})
    axes[0].plot(s_values, f_mean, color="#0b3954", linewidth=2.0, marker="o", markersize=4)
    axes[0].fill_between(s_values, f_min, f_max, color="#0b3954", alpha=0.18)
    axes[0].set_ylabel("Darcy friction factor, f_D")
    axes[0].set_title("Salt 2 main-loop Darcy friction profile from retained latest-time wall-shear fields")

    axes[1].plot(s_values, yplus_values, color="#bc3908", linewidth=1.8, marker="s", markersize=3.5)
    axes[1].set_ylabel("Patch-avg yPlus")
    axes[1].set_xlabel("Streamwise distance from TP1, s [m]")

    for axis in axes:
        for row in station_rows:
            if row["station_label"] not in TP_LABELS:
                continue
            s_value = float(row["s_m"])
            axis.axvline(s_value, color="#5c677d", linewidth=0.8, alpha=0.35)
        ymin, ymax = axis.get_ylim()
        for row in station_rows:
            if row["station_label"] not in TP_LABELS:
                continue
            s_value = float(row["s_m"])
            axis.text(s_value, ymax, row["station_label"], rotation=90, va="top", ha="right", fontsize=8, color="#33415c")

    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "salt2_val_main_loop_late_window_profile", dpi=220)
    plt.close(fig)
    return paths


def plot_bulk_context(output_dir: Path, mdot_rows: list[dict[str, Any]], tp_rows: list[dict[str, Any]]) -> dict[str, str]:
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    axes[0].plot(
        [float(row["time_s"]) for row in mdot_rows],
        [float(row["mdot_mean_abs_kg_s"]) for row in mdot_rows],
        color="#1f1f1f",
        linewidth=1.6,
    )
    axes[0].set_ylabel("|mdot| mean [kg/s]")
    axes[0].set_title("Merged continuation history used for live friction context")

    for label in TP_LABELS:
        axes[1].plot(
            [float(row["time_s"]) for row in tp_rows if label in row],
            [float(row[label]) for row in tp_rows if label in row],
            linewidth=1.0,
            label=label,
        )
    axes[1].set_xlabel("Time [s]")
    axes[1].set_ylabel("TP bulk temperature [K]")
    axes[1].legend(ncol=3, fontsize=8, loc="best")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "salt2_val_loop_bulk_context", dpi=220)
    plt.close(fig)
    return paths


def write_notes(
    output_dir: Path,
    source_id: str,
    selected_times: list[float],
    flow_area_m2: float,
    dh_m: float,
    history_end_s: float,
) -> None:
    lines = [
        "# Implementation Notes",
        "",
        f"- Source case: `{source_id}`.",
        "- Primary coordinate: main-loop streamwise distance `s` with `s = 0 m` at `TP1`.",
        "- Main-loop direction used in this package: `TP1 -> TP2 -> TP3 -> TP6 -> TP1`.",
        "- The main-loop friction profile is patchwise in this first pass, not dense centerline-resolved.",
        f"- Retained field times sampled for wall-shear reductions: `{', '.join(f'{value:g}' for value in selected_times)}` s.",
        f"- Merged continuation probe and mdot histories extend through `{history_end_s:g}` s.",
        "- Darcy friction factor is reported as `f_D = 8 tau_w / (rho U^2)`.",
        "- `tau_w` is the streamwise projection of the patch area-average `wallShearStress` vector.",
        "- `rho` is reconstructed from the merged TP bulk-temperature history using the case density law `rho(T) = 2293.6 - 0.7497 T`.",
        "- `U` is derived from the merged mean absolute mdot history and a fixed bulk flow area from the mdot face-zone monitor.",
        f"- Bulk flow area used: `{flow_area_m2:.9e}` m^2.",
        f"- Equivalent circular hydraulic diameter from that area: `{dh_m:.6f}` m.",
        "- `warning_flag=yes` marks either large wall-shear spread proxy (>20%) or strong yPlus nonuniformity proxy (`yPlus_max / yPlus_avg > 5`).",
        "- The branch/test-section patches are extracted in raw form for future use, but this v1 package keeps the public friction profile on the primary main loop only.",
        "- Next pass target: replace patchwise positions with much denser `s` sampling and preserve the same reduction contract so internal HTC can be added without changing the package schema.",
    ]
    path = output_dir / "implementation_notes.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    runtime_root = extractor.load_runtime_root(args.source_id)
    reduction_csv = run_extractor(args.source_id, args.last_n_times, output_dir, args.skip_extraction)
    reduction_rows = load_reduction_rows(reduction_csv)
    reduction_lookup = build_reduction_lookup(reduction_rows)

    mdot_rows, flow_area_m2 = build_mdot_series(runtime_root)
    mdot_lookup = {float(row["time_s"]): float(row["mdot_mean_abs_kg_s"]) for row in mdot_rows}
    tp_rows, tw_rows = build_temperature_rows(runtime_root)
    bulk_rho_map = build_tp_bulk_rho_map(tp_rows)
    station_centers = load_station_centers()
    station_rows = build_station_rows(station_centers)
    patch_positions, _ = build_patch_positions(station_rows, station_centers)
    patch_friction_rows = build_patch_friction_rows(
        args.source_id,
        patch_positions,
        reduction_lookup,
        bulk_rho_map,
        mdot_lookup,
        flow_area_m2,
    )
    if not patch_friction_rows:
        raise RuntimeError("No patchwise friction rows were produced.")
    patch_summary_rows = summarize_patch_rows(patch_friction_rows)

    csv_dump(
        output_dir / "main_loop_station_definitions.csv",
        ["station_label", "order_index", "x_m", "y_m", "z_m", "s_m"],
        station_rows,
    )
    csv_dump(
        output_dir / "main_loop_patch_positions.csv",
        [
            "patch_name",
            "leg_name",
            "patch_index_in_leg",
            "patch_count_in_leg",
            "s_start_m",
            "s_end_m",
            "s_mid_m",
            "tangent_x",
            "tangent_y",
            "tangent_z",
        ],
        patch_positions,
    )
    csv_dump(
        output_dir / "main_loop_patch_friction_timeseries.csv",
        list(patch_friction_rows[0].keys()),
        patch_friction_rows,
    )
    csv_dump(
        output_dir / "main_loop_patch_friction_summary.csv",
        list(patch_summary_rows[0].keys()),
        patch_summary_rows,
    )
    csv_dump(
        output_dir / "tp_temperature_timeseries.csv",
        ["time_s", *TP_LABELS],
        tp_rows,
    )
    tw_columns = sorted({key for row in tw_rows for key in row if key != "time_s"})
    csv_dump(
        output_dir / "tw_temperature_timeseries.csv",
        ["time_s", *tw_columns],
        tw_rows,
    )
    csv_dump(
        output_dir / "loop_bulk_timeseries.csv",
        ["time_s", "mdot_mean_abs_kg_s"],
        mdot_rows,
    )

    profile_paths = plot_main_loop_profile(output_dir, patch_summary_rows, station_rows)
    context_paths = plot_bulk_context(output_dir, mdot_rows, tp_rows)

    selected_times = sorted({float(row["time_s"]) for row in patch_friction_rows})
    dh_m = math.sqrt(4.0 * flow_area_m2 / math.pi)
    summary = {
        "generated_at": iso_timestamp(),
        "source_id": args.source_id,
        "runtime_root": str(runtime_root),
        "history_time_end_s": max(float(row["time_s"]) for row in mdot_rows),
        "retained_field_times_s": selected_times,
        "flow_area_m2": flow_area_m2,
        "equivalent_circular_diameter_m": dh_m,
        "main_loop_total_length_m": station_rows[-1]["s_m"] + distance(
            station_centers[MAIN_LOOP_SEQUENCE[-2]],
            station_centers[MAIN_LOOP_SEQUENCE[-1]],
        ),
        "profile_figure_paths": profile_paths,
        "context_figure_paths": context_paths,
        "warning_proxy_note": "warning_flag=yes uses wall-shear spread proxy and yPlus nonuniformity proxy; it is not yet a true circumferential station-by-station spread metric.",
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")

    write_notes(
        output_dir,
        args.source_id,
        selected_times,
        flow_area_m2,
        dh_m,
        max(float(row["time_s"]) for row in mdot_rows),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
