#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shlex
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

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
    load_case_metadata,
    parse_scalar_series,
    save_matplotlib_figure,
    safe_float,
)


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


s2 = load_module("build_salt2_behavior_package", ROOT / "tools" / "analyze" / "build_salt2_behavior_package.py")
sec = load_module("build_ethan_section_transport_package", ROOT / "tools" / "analyze" / "build_ethan_section_transport_package.py")

OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_transient_axial_package"
METADATA_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"
VALIDATION_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_direct_validation" / "ethan_direct_validation_metrics.csv"
STATUS_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "all_salt_case_status.csv"
REPRESENTATIVE_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "representative_case_selection.csv"
PRESSURE_SUMMARY_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_section_transport_package" / "representative_section_summary.csv"
LAST_WINDOW_COUNT = 50
TRANSIENT_HEAT_METRICS = [
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
TP_LABELS = [f"TP{i}" for i in range(1, 7)]
TW_LABELS = [f"TW{i}" for i in range(1, 12)]
SELECTED_TW = ["TW5", "TW9"]
LEG_ORDER = ["lower_leg", "right_leg", "upper_leg", "left_leg"]
LEG_TITLES = {
    "lower_leg": "Lower leg / heater leg",
    "right_leg": "Right leg / downcomer",
    "upper_leg": "Upper leg / cooling leg",
    "left_leg": "Left leg / upcomer",
}
DEFAULT_COLORS = {
    "val": "#1f1f1f",
    "jin": "#0b6e4f",
    "kirst": "#bc3908",
    "other": "#5f0f40",
}
METRIC_UNITS = {
    "mdot_mean_abs_kg_s": "kg/s",
    "tp_mean_k": "K",
    "total_q_net_w": "W",
    **{label: "K" for label in TP_LABELS + TW_LABELS},
    **{key: "W" for key in TRANSIENT_HEAT_METRICS},
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a reusable transient-plus-axial package for Ethan salt cases. "
            "Transient outputs come from native probe and wall-heat files; latest-time "
            "axial patch reductions are augmented with reconstructed T/Nu/wallHeatFlux fields."
        )
    )
    parser.add_argument("--source-id", action="append", dest="source_ids", help="Repeat to override the default all-salt source set.")
    parser.add_argument("--last-window-count", type=int, default=LAST_WINDOW_COUNT, help="Trailing sample count used for steadiness statistics.")
    parser.add_argument(
        "--skip-axial-field-extraction",
        action="store_true",
        help="Reuse existing axial field reductions if they are already present in the temp extraction roots.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def default_source_ids() -> list[str]:
    return [row["source_id"] for row in load_csv_rows(METADATA_CSV) if "salt" in row.get("source_id", "")]


def load_runtime_context(source_id: str) -> tuple[Path, Path, dict[str, object], dict[str, str]]:
    metadata_map = {row["source_id"]: row for row in load_csv_rows(METADATA_CSV) if row.get("source_id")}
    meta_row = metadata_map.get(source_id, {})
    runtime_root = Path(meta_row.get("active_runtime_root") or meta_row.get("source_root") or "").resolve()
    source_root = Path(meta_row.get("source_root") or runtime_root).resolve()
    metadata = load_case_metadata(runtime_root) or load_case_metadata(source_root) or {}
    return source_root, runtime_root, metadata, meta_row


def parse_total_q_series(source_root: Path) -> tuple[np.ndarray, np.ndarray]:
    rows = parse_scalar_series(source_root / "postProcessing" / "total_Q.dat")
    if not rows:
        return np.array([]), np.array([])
    return np.array([float(row["time"]) for row in rows]), np.array([float(row["value"]) for row in rows])


def append_series_rows(rows: list[dict[str, object]], source_id: str, base_case_id: str, variant_label: str, family: str, metric: str, times: np.ndarray, values: np.ndarray) -> None:
    unit = METRIC_UNITS.get(metric, "")
    for time_value, value in zip(times, values):
        rows.append(
            {
                "source_id": source_id,
                "base_case_id": base_case_id,
                "variant_label": variant_label,
                "family": family,
                "metric": metric,
                "unit": unit,
                "time_s": float(time_value),
                "value": float(value),
            }
        )


def build_transient_rows(source_id: str, base_case_id: str, variant_label: str, runtime_root: Path, metadata: dict[str, object], wall_probe_order: list[str], last_window_count: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    transient_rows: list[dict[str, object]] = []
    last_window_rows: list[dict[str, object]] = []
    mdot_t, mdot_v = s2.parse_mdot_mean_series(runtime_root)
    tp_t, tp_series, tp_mean = s2.parse_temperature_probe_series(runtime_root)
    tw_t, tw_series = s2.parse_wall_temperature_series(runtime_root, wall_probe_order)
    heat_rows = s2.parse_wall_heatflux_section_series(runtime_root, metadata)
    heat_t, heat_series = s2.rows_to_series(heat_rows, TRANSIENT_HEAT_METRICS)
    total_q_t, total_q_v = parse_total_q_series(runtime_root)

    append_series_rows(transient_rows, source_id, base_case_id, variant_label, "flow", "mdot_mean_abs_kg_s", mdot_t, mdot_v)
    append_series_rows(transient_rows, source_id, base_case_id, variant_label, "temperature", "tp_mean_k", tp_t, tp_mean)
    for metric, values in tp_series.items():
        append_series_rows(transient_rows, source_id, base_case_id, variant_label, "temperature", metric, tp_t, values)
    for metric, values in tw_series.items():
        append_series_rows(transient_rows, source_id, base_case_id, variant_label, "wall_temperature", metric, tw_t, values)
    append_series_rows(transient_rows, source_id, base_case_id, variant_label, "heat_balance", "total_q_net_w", total_q_t, total_q_v)
    for metric, values in heat_series.items():
        append_series_rows(transient_rows, source_id, base_case_id, variant_label, "heat_balance", metric, heat_t, values)

    metric_map = {
        "mdot_mean_abs_kg_s": ("flow", mdot_t, mdot_v),
        "tp_mean_k": ("temperature", tp_t, tp_mean),
        "total_q_net_w": ("heat_balance", total_q_t, total_q_v),
    }
    metric_map.update({metric: ("temperature", tp_t, values) for metric, values in tp_series.items()})
    metric_map.update({metric: ("wall_temperature", tw_t, values) for metric, values in tw_series.items()})
    metric_map.update({metric: ("heat_balance", heat_t, values) for metric, values in heat_series.items()})
    for metric, (family, times, values) in metric_map.items():
        stats = s2.compute_last_window_stats(source_id, metric, times, values, last_window_count)
        stats.update({"base_case_id": base_case_id, "variant_label": variant_label, "family": family, "unit": METRIC_UNITS.get(metric, "")})
        last_window_rows.append(stats)
    return transient_rows, last_window_rows


def leg_group_for_patch(patch: str) -> str:
    if patch.startswith("pipeleg_lower_"):
        return "lower_leg"
    if patch.startswith("pipeleg_right_"):
        return "right_leg"
    if patch.startswith("pipeleg_upper_"):
        return "upper_leg"
    if patch.startswith("pipeleg_left_"):
        return "left_leg"
    if patch.startswith("junction_"):
        return "junctions"
    return "other"


def thermal_role_for_patch(patch: str) -> str:
    if patch in s2.HEATER_PATCHES:
        return "heater"
    if patch in s2.COOLING_BRANCH_PATCHES:
        return "cooling_branch"
    if patch in s2.TEST_SECTION_PATCHES:
        return "test_section"
    if patch.startswith("junction_"):
        return "junction"
    if patch.startswith("pipeleg_"):
        return "transport"
    return "other"


def patch_order_value(patch: str) -> int:
    import re

    match = re.search(r"_(\d+)_", patch)
    return int(match.group(1)) if match else 999


def parse_wall_heatflux_patch_rows(source_id: str, base_case_id: str, variant_label: str, source_root: Path) -> list[dict[str, object]]:
    candidates = sorted(source_root.glob("postProcessing/wallHeatFlux/*/wallHeatFlux.dat"), key=lambda item: item.parent.name)
    if not candidates:
        return []
    imposed_q = s2.parse_patch_imposed_q(source_root)
    rows: list[dict[str, object]] = []
    with candidates[-1].open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 6 or parts[1].startswith("ncc_"):
                continue
            time_value = safe_float(parts[0])
            q_min = safe_float(parts[2])
            q_max = safe_float(parts[3])
            q_total = safe_float(parts[4])
            q_avg = safe_float(parts[5])
            if None in (time_value, q_min, q_max, q_total, q_avg):
                continue
            patch = parts[1]
            imposed = imposed_q.get(patch)
            ambient_like = 0.0
            if imposed is not None and imposed > 0.0:
                ambient_like = max(imposed - q_total, 0.0)
            elif q_total < 0.0:
                ambient_like = abs(q_total)
            rows.append(
                {
                    "source_id": source_id,
                    "base_case_id": base_case_id,
                    "variant_label": variant_label,
                    "time_s": float(time_value),
                    "patch_name": patch,
                    "leg_group": leg_group_for_patch(patch),
                    "thermal_role": thermal_role_for_patch(patch),
                    "patch_order": patch_order_value(patch),
                    "q_min_w_m2": float(q_min),
                    "q_max_w_m2": float(q_max),
                    "q_total_w": float(q_total),
                    "q_avg_w_m2": float(q_avg),
                    "imposed_q_w": "" if imposed is None else float(imposed),
                    "ambient_like_component_w": ambient_like,
                }
            )
    return rows


def build_axial_latest_rows(patch_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    latest_by_patch: dict[tuple[str, str], dict[str, object]] = {}
    for row in patch_rows:
        key = (str(row["source_id"]), str(row["patch_name"]))
        current = latest_by_patch.get(key)
        if current is None or float(row["time_s"]) >= float(current["time_s"]):
            latest_by_patch[key] = dict(row)
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in latest_by_patch.values():
        grouped[(str(row["source_id"]), str(row["leg_group"]))].append(row)
    latest_rows: list[dict[str, object]] = []
    for rows in grouped.values():
        ordered = sorted(rows, key=lambda item: (int(item["patch_order"]), str(item["patch_name"])))
        denom = max(len(ordered) - 1, 1)
        for index, row in enumerate(ordered):
            payload = dict(row)
            payload["patch_rank_in_leg"] = index + 1
            payload["patch_count_in_leg"] = len(ordered)
            payload["section_progress_0to1"] = index / denom if len(ordered) > 1 else 0.0
            latest_rows.append(payload)
    return sorted(latest_rows, key=lambda item: (str(item["source_id"]), str(item["leg_group"]), int(item["patch_rank_in_leg"])))


def write_axial_patch_dict(path: Path, patch_names: list[str]) -> list[str]:
    object_names: list[str] = []
    lines = [
        "FoamFile",
        "{",
        "    format      ascii;",
        "    class       dictionary;",
        "    location    \"system\";",
        "    object      functions;",
        "}",
        "",
    ]
    for patch_name in patch_names:
        object_name = f"patch_{patch_name}"
        object_names.append(object_name)
        lines.extend(
            [
                object_name,
                "{",
                "    type            surfaceFieldValue;",
                "    libs            (\"libfieldFunctionObjects.so\");",
                "    writeControl    timeStep;",
                "    writeInterval   1;",
                "    surfaceFormat   none;",
                "    writeFields     false;",
                "    writeToFile     true;",
                "    log             false;",
                f"    patch           {patch_name};",
                "    operation       areaAverage;",
                "    fields          (T Nu wallHeatFlux);",
                "}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return object_names


def parse_axial_surface_output(path: Path) -> dict[str, object]:
    payload: dict[str, object] = {"areaAverage_T_k": "", "areaAverage_Nu": "", "areaAverage_wallHeatFlux_w_m2": "", "latest_time": ""}
    if not path.exists():
        return payload
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) >= 4:
                payload["latest_time"] = parts[0]
                payload["areaAverage_T_k"] = safe_float(parts[1], parts[1])
                payload["areaAverage_Nu"] = safe_float(parts[2], parts[2])
                payload["areaAverage_wallHeatFlux_w_m2"] = safe_float(parts[3], parts[3])
    return payload


def axial_outputs_ready(case_dir: Path, object_names: list[str], latest_time: str) -> bool:
    for object_name in object_names:
        path = case_dir / "postProcessing" / object_name / latest_time / "surfaceFieldValue.dat"
        if not path.exists():
            return False
    return True


def augment_axial_latest_rows(latest_rows: list[dict[str, object]], skip_axial_field_extraction: bool) -> list[dict[str, object]]:
    rows_by_source: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in latest_rows:
        rows_by_source[str(row["source_id"])] += [row]
    augmented: list[dict[str, object]] = []
    for source_id, source_rows in sorted(rows_by_source.items()):
        source_root, runtime_root, _, _ = load_runtime_context(source_id)
        case_dir = sec.ensure_extract_case(source_id, runtime_root)
        latest_time = sec.latest_processor_time(runtime_root)
        patch_names = sorted({str(row["patch_name"]) for row in source_rows})
        functions_path = case_dir / "system" / "axial_patch_functions"
        object_names = write_axial_patch_dict(functions_path, patch_names)
        root_time_dir = case_dir / latest_time
        extraction_error = ""
        try:
            if not skip_axial_field_extraction or not root_time_dir.exists() or not axial_outputs_ready(case_dir, object_names, latest_time):
                if not root_time_dir.exists() or not all((root_time_dir / field).exists() for field in ("T", "Nu", "wallHeatFlux")):
                    sec.shell_run(case_dir, f"reconstructPar -case {shlex.quote(str(case_dir))} -time {latest_time} -fields '(T Nu wallHeatFlux)'")
                sec.shell_run(case_dir, f"foamPostProcess -case {shlex.quote(str(case_dir))} -dict {shlex.quote(str(functions_path))} -time {latest_time}")
        except Exception as exc:
            extraction_error = str(exc)
            print(f"Axial field extraction failed for {source_id} at time {latest_time}: {exc}", file=sys.stderr)
        field_map = {}
        for patch_name in patch_names:
            path = case_dir / "postProcessing" / f"patch_{patch_name}" / latest_time / "surfaceFieldValue.dat"
            field_map[patch_name] = parse_axial_surface_output(path)
        for row in source_rows:
            payload = dict(row)
            payload.update(field_map.get(str(row["patch_name"]), {}))
            payload["runtime_root"] = str(runtime_root)
            payload["source_root"] = str(source_root)
            payload["axial_field_extraction_error"] = extraction_error
            augmented.append(payload)
    return augmented


def build_axial_summary_rows(latest_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in latest_rows:
        grouped[(str(row["source_id"]), str(row["leg_group"]), str(row["thermal_role"]))].append(row)
    summary_rows: list[dict[str, object]] = []
    for (source_id, leg_group, thermal_role), rows in sorted(grouped.items()):
        nu_values = [float(row["areaAverage_Nu"]) for row in rows if row.get("areaAverage_Nu") not in ("", None)]
        temp_values = [float(row["areaAverage_T_k"]) for row in rows if row.get("areaAverage_T_k") not in ("", None)]
        summary_rows.append(
            {
                "source_id": source_id,
                "leg_group": leg_group,
                "thermal_role": thermal_role,
                "patch_count": len(rows),
                "sum_q_total_w": sum(float(row["q_total_w"]) for row in rows),
                "mean_q_avg_w_m2": mean(float(row["q_avg_w_m2"]) for row in rows),
                "mean_areaAverage_Nu": mean(nu_values) if nu_values else "",
                "mean_areaAverage_T_k": mean(temp_values) if temp_values else "",
                "max_abs_q_avg_w_m2": max(abs(float(row["q_avg_w_m2"])) for row in rows),
            }
        )
    return summary_rows


def case_color(source_id: str, variant_label: str) -> str:
    variant = (variant_label or "").lower()
    if variant in DEFAULT_COLORS:
        return DEFAULT_COLORS[variant]
    if source_id.startswith("val_"):
        return DEFAULT_COLORS["val"]
    return DEFAULT_COLORS["other"]


def case_label(source_id: str) -> str:
    return source_id.replace("viscosity_screening_", "").replace("_coarse_mesh_laminar", "").replace("_coarse_mesh", "").replace("_", " ")


def build_timeseries_lookup(rows: list[dict[str, object]]) -> dict[tuple[str, str], tuple[np.ndarray, np.ndarray]]:
    grouped: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["source_id"]), str(row["metric"]))].append((float(row["time_s"]), float(row["value"])))
    lookup: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]] = {}
    for key, pairs in grouped.items():
        pairs.sort(key=lambda item: item[0])
        lookup[key] = (np.array([pair[0] for pair in pairs]), np.array([pair[1] for pair in pairs]))
    return lookup


def plot_transient_bundle(base_case_id: str, case_ids: list[str], transient_lookup: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]], variant_map: dict[str, str]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    primary_metrics = [
        (axes[0, 0], "mdot_mean_abs_kg_s", "|mdot| mean [kg/s]", "Mass flow"),
        (axes[0, 1], "tp_mean_k", "TP mean [K]", "Bulk temperature"),
        (axes[1, 0], "ambient_proxy_w", "Ambient proxy [W]", "Ambient-like loss"),
        (axes[1, 1], "total_q_net_w", "Net wall heat [W]", "Net heat-balance tail"),
    ]
    for ax, metric, ylabel, title in primary_metrics:
        for source_id in case_ids:
            times, values = transient_lookup.get((source_id, metric), (np.array([]), np.array([])))
            if len(times) == 0:
                continue
            ax.plot(times, values, linewidth=2.0, color=case_color(source_id, variant_map.get(source_id, "")), label=case_label(source_id))
        ax.set_title(title)
        ax.set_xlabel("Time [s]")
        ax.set_ylabel(ylabel)
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle(f"{base_case_id}: transient comparison")
    save_matplotlib_figure(fig, OUTPUT_DIR, f"{base_case_id}_transient_primary", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    tw_ax = axes[0, 0]
    section_specs = [
        (axes[0, 1], "section_heater_net_q_w", "Heater net Q [W]", "Heater"),
        (axes[1, 0], "section_cooling_branch_net_q_w", "Cooling branch net Q [W]", "Cooling branch"),
        (axes[1, 1], "section_junctions_net_q_w", "Junction net Q [W]", "Junctions"),
    ]
    for source_id in case_ids:
        color = case_color(source_id, variant_map.get(source_id, ""))
        for tw_metric, linestyle in zip(SELECTED_TW, ["-", "--"]):
            times, values = transient_lookup.get((source_id, tw_metric), (np.array([]), np.array([])))
            if len(times) == 0:
                continue
            tw_ax.plot(times, values, linewidth=1.8, linestyle=linestyle, color=color, label=f"{case_label(source_id)} {tw_metric}")
    tw_ax.set_title("Selected wall temperatures")
    tw_ax.set_xlabel("Time [s]")
    tw_ax.set_ylabel("T [K]")
    tw_ax.legend(loc="best", fontsize=7)
    for ax, metric, ylabel, title in section_specs:
        for source_id in case_ids:
            times, values = transient_lookup.get((source_id, metric), (np.array([]), np.array([])))
            if len(times) == 0:
                continue
            ax.plot(times, values, linewidth=2.0, color=case_color(source_id, variant_map.get(source_id, "")), label=case_label(source_id))
        ax.set_title(title)
        ax.set_xlabel("Time [s]")
        ax.set_ylabel(ylabel)
    fig.suptitle(f"{base_case_id}: wall-temperature and section-heat comparison")
    save_matplotlib_figure(fig, OUTPUT_DIR, f"{base_case_id}_transient_sections", dpi=200)
    plt.close(fig)


def plot_axial_bundle(base_case_id: str, case_ids: list[str], latest_rows: list[dict[str, object]], variant_map: dict[str, str], field: str, ylabel: str, suffix: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    axis_map = dict(zip(LEG_ORDER, axes.flatten()))
    for leg_group in LEG_ORDER:
        ax = axis_map[leg_group]
        for source_id in case_ids:
            series = sorted(
                [row for row in latest_rows if row["source_id"] == source_id and row["leg_group"] == leg_group and row.get(field) not in ("", None)],
                key=lambda item: float(item["section_progress_0to1"]),
            )
            if not series:
                continue
            x = [float(row["section_progress_0to1"]) for row in series]
            y = [float(row[field]) for row in series]
            ax.plot(x, y, marker="o", linewidth=1.8, color=case_color(source_id, variant_map.get(source_id, "")), label=case_label(source_id))
        ax.set_title(LEG_TITLES[leg_group])
        ax.set_xlabel("Ordered patch progress within leg [-]")
        ax.set_ylabel(ylabel)
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle(f"{base_case_id}: latest-time axial {suffix}")
    save_matplotlib_figure(fig, OUTPUT_DIR, f"{base_case_id}_axial_{suffix}", dpi=200)
    plt.close(fig)


def write_readme(source_ids: list[str], representative_rows: list[dict[str, str]], case_status_map: dict[str, dict[str, str]], pressure_map: dict[str, dict[str, str]]) -> None:
    lines = [
        "# Ethan Transient and Axial Package",
        "",
        "This package combines transient behavior analysis from native post-processing outputs with latest-time axial wall-transfer reductions from reconstructed `T`, `Nu`, and `wallHeatFlux` fields.",
        "",
        "## Important limitations",
        "",
        "- `TW10` remains excluded from RMSE scorecards elsewhere; this package still exports the raw `TW10` time history for transparency.",
        "- Metric end times are source dependent. The active `val_salt_test_2` continuation has field and wall-heat data beyond the current probe-history horizon.",
        "- The axial coordinate used here is ordered patch progress from 0 to 1 within each leg, not geometric arc length.",
        "- Pressure-drop evolution is not yet reconstructed transiently here; reuse the existing June 4 section-transport package for latest-time pressure ranking.",
        "",
        "## Cases processed",
        "",
    ]
    for source_id in source_ids:
        status = case_status_map.get(source_id, {})
        lines.append(f"- `{source_id}`: `run_status={status.get('run_status', '')}`, `essential_steadiness_class={status.get('essential_steadiness_class', '')}`, `usable_for_steady_state_now={status.get('usable_for_steady_state_now', '')}`")
    lines.extend(["", "## Representative groups", ""])
    for row in representative_rows:
        lines.append(f"- `{row['base_case_id']}`: manuscript representative `{row['primary_manuscript_representative'] or 'none yet'}`; sensitivity set `{row['sensitivity_rows']}`")
    lines.extend(["", "## Pressure-drop context reused here", ""])
    for source_id, row in sorted(pressure_map.items()):
        lines.append(f"- `{source_id}`: `upper_leg_abs_delta_p_rgh_pa={row.get('upper_leg_abs_delta_p_rgh_pa', '')}`, `left_leg_abs_delta_p_rgh_pa={row.get('left_leg_abs_delta_p_rgh_pa', '')}`, `right_leg_abs_delta_p_rgh_pa={row.get('right_leg_abs_delta_p_rgh_pa', '')}`")
    lines.extend([
        "",
        "## Output files",
        "",
        "- `all_salt_transient_timeseries.csv`: long-form transient metrics for all salt cases.",
        "- `all_salt_transient_last_window.csv`: trailing-window steadiness statistics for all exported metrics.",
        "- `all_salt_axial_patch_heat_timeseries.csv`: long-form patchwise wall-heat histories from `wallHeatFlux.dat`.",
        "- `all_salt_axial_patch_latest.csv`: latest-time patchwise wall-heat rows augmented with area-averaged `T`, `Nu`, and `wallHeatFlux`.",
        "- `all_salt_axial_leg_summary.csv`: aggregated axial summaries by case, leg, and thermal role.",
        "- `representative_transient_summary.csv`: manuscript-facing summary rows for the selected representative and sensitivity cases.",
        "- `figures/png/*_transient_*.png` and `figures/png/*_axial_*.png`: shared-axis comparison plots by base case.",
    ])
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_notes(representative_rows: list[dict[str, object]]) -> None:
    notes = [
        "# Scientific Writeup Notes",
        "",
        "## Observed outputs",
        "",
        "- Transient mdot, probe-temperature, wall-temperature, and wall-heat histories now exist in a single report package for every salt case.",
        "- Latest-time axial patch rows now carry ordered wall-heat, wall-temperature, and Nusselt summaries for each loop leg.",
        "- Pressure-drop interpretation still comes from the separate section-transport package, where the upper leg dominates `|Delta p_rgh|` among use-ready Salt 2-4 rows.",
        "",
        "## Inferred interpretation",
        "",
        "- Jin-vs-Kirst differences remain strongest in flow and upper-leg resistance behavior, not in the shared ambient-loss bias.",
        "- The transient heat-balance tail can now be inspected per section and per wall patch, which is the right way to test the collaborator's claim that slow net-heat decay is the main barrier to practical convergence.",
        "- The axial latest-time rows are suitable for a first scientific writeup on where heat is added, removed, and lost along each leg, even though the axial coordinate is currently patch progress rather than geometric arc length.",
        "",
        "## Representative-case reminders",
        "",
    ]
    for row in representative_rows:
        notes.append(f"- `{row['source_id']}`: `base_case_id={row['base_case_id']}`, `variant_label={row['variant_label']}`, `run_status={row['run_status']}`, `usable_for_steady_state_now={row['usable_for_steady_state_now']}`, `exp_all_temp_rmse_k={row['exp_all_temp_rmse_k']}`, `exp_mdot_abs_error_pct={row['exp_mdot_abs_error_pct']}`")
    notes.extend(["", "## Next suggested actions", "", "- Extend this package with sampled transient pressure reconstruction if the manuscript needs section pressure-drop evolution instead of latest-time ranking only.", "- If a true `h(x)` with geometric distance is required, add a centerline-aware mesh extraction step rather than back-solving it from patch order."])
    (OUTPUT_DIR / "scientific_writeup_notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = args.source_ids or default_source_ids()
    ensure_dir(OUTPUT_DIR)
    wall_probe_order = s2.load_wall_probe_order()
    validation_map = {row["source_id"]: row for row in load_csv_rows(VALIDATION_CSV) if row.get("source_id")}
    case_status_map = {row["source_id"]: row for row in load_csv_rows(STATUS_CSV) if row.get("source_id")}
    representative_groups = load_csv_rows(REPRESENTATIVE_CSV)
    pressure_map = {row["source_id"]: row for row in load_csv_rows(PRESSURE_SUMMARY_CSV) if row.get("source_id")}

    transient_rows: list[dict[str, object]] = []
    last_window_rows: list[dict[str, object]] = []
    patch_time_rows: list[dict[str, object]] = []
    variant_map: dict[str, str] = {}
    for source_id in source_ids:
        _, runtime_root, metadata, meta_row = load_runtime_context(source_id)
        base_case_id = str(meta_row.get("base_case_id", ""))
        variant_label = str(meta_row.get("variant_label", ""))
        variant_map[source_id] = variant_label
        case_transient_rows, case_last_window_rows = build_transient_rows(source_id, base_case_id, variant_label, runtime_root, metadata, wall_probe_order, args.last_window_count)
        transient_rows.extend(case_transient_rows)
        last_window_rows.extend(case_last_window_rows)
        patch_time_rows.extend(parse_wall_heatflux_patch_rows(source_id, base_case_id, variant_label, runtime_root))

    axial_latest_rows = build_axial_latest_rows(patch_time_rows)
    axial_latest_rows = augment_axial_latest_rows(axial_latest_rows, args.skip_axial_field_extraction)
    axial_summary_rows = build_axial_summary_rows(axial_latest_rows)
    transient_lookup = build_timeseries_lookup(transient_rows)

    selected_case_ids: set[str] = set()
    for row in representative_groups:
        case_ids = [item.strip() for item in str(row.get("sensitivity_rows", "")).split(";") if item.strip()]
        case_ids = [case_id for case_id in case_ids if case_id in source_ids]
        if not case_ids:
            continue
        selected_case_ids.update(case_ids)
        plot_transient_bundle(str(row["base_case_id"]), case_ids, transient_lookup, variant_map)
        plot_axial_bundle(str(row["base_case_id"]), case_ids, axial_latest_rows, variant_map, "q_avg_w_m2", "Patch-averaged q [W/m^2]", "q_profile")
        plot_axial_bundle(str(row["base_case_id"]), case_ids, axial_latest_rows, variant_map, "areaAverage_Nu", "Patch-averaged Nu [-]", "nu_profile")

    representative_summary_rows: list[dict[str, object]] = []
    for source_id in sorted(selected_case_ids):
        status = case_status_map.get(source_id, {})
        validation = validation_map.get(source_id, {})
        representative_summary_rows.append({
            "source_id": source_id,
            "base_case_id": status.get("base_case_id", ""),
            "variant_label": status.get("variant_label", ""),
            "run_status": status.get("run_status", ""),
            "essential_steadiness_class": status.get("essential_steadiness_class", ""),
            "usable_for_steady_state_now": status.get("usable_for_steady_state_now", ""),
            "exp_tp_rmse_k": validation.get("exp_tp_rmse_k", ""),
            "exp_tw_rmse_k": validation.get("exp_tw_rmse_k", ""),
            "exp_all_temp_rmse_k": validation.get("exp_all_temp_rmse_k", ""),
            "exp_mdot_abs_error_pct": validation.get("exp_mdot_abs_error_pct", ""),
            "exp_q_external_loss_abs_error_pct": validation.get("exp_q_external_loss_abs_error_pct", ""),
            "upper_leg_abs_delta_p_rgh_pa": pressure_map.get(source_id, {}).get("upper_leg_abs_delta_p_rgh_pa", ""),
            "left_leg_abs_delta_p_rgh_pa": pressure_map.get(source_id, {}).get("left_leg_abs_delta_p_rgh_pa", ""),
            "right_leg_abs_delta_p_rgh_pa": pressure_map.get(source_id, {}).get("right_leg_abs_delta_p_rgh_pa", ""),
            "ambient_proxy_w": validation.get("sim_ambient_proxy_w", ""),
            "section_heater_net_q_w": validation.get("sim_section_heater_net_q_w", ""),
            "section_cooling_branch_net_q_w": validation.get("sim_section_cooling_branch_net_q_w", ""),
            "section_test_section_net_q_w": validation.get("sim_section_test_section_net_q_w", ""),
        })

    csv_dump(OUTPUT_DIR / "all_salt_transient_timeseries.csv", list(transient_rows[0].keys()), transient_rows)
    csv_dump(OUTPUT_DIR / "all_salt_transient_last_window.csv", list(last_window_rows[0].keys()), last_window_rows)
    csv_dump(OUTPUT_DIR / "all_salt_axial_patch_heat_timeseries.csv", list(patch_time_rows[0].keys()), patch_time_rows)
    csv_dump(OUTPUT_DIR / "all_salt_axial_patch_latest.csv", list(axial_latest_rows[0].keys()), axial_latest_rows)
    csv_dump(OUTPUT_DIR / "all_salt_axial_leg_summary.csv", list(axial_summary_rows[0].keys()), axial_summary_rows)
    csv_dump(OUTPUT_DIR / "representative_transient_summary.csv", list(representative_summary_rows[0].keys()), representative_summary_rows)

    write_readme(source_ids, representative_groups, case_status_map, pressure_map)
    write_notes(representative_summary_rows)
    summary = {
        "generated_at": iso_timestamp(),
        "source_ids": source_ids,
        "transient_row_count": len(transient_rows),
        "last_window_row_count": len(last_window_rows),
        "axial_patch_timeseries_row_count": len(patch_time_rows),
        "axial_patch_latest_row_count": len(axial_latest_rows),
        "axial_leg_summary_row_count": len(axial_summary_rows),
        "representative_summary_row_count": len(representative_summary_rows),
    }
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
