#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from statistics import mean

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    ensure_dir,
    get_registry_row,
    iso_timestamp,
    load_case_metadata,
    parse_probe_series,
    parse_scalar_series,
    path_lookup,
    save_matplotlib_figure,
    safe_float,
)

DEFAULT_SOURCE_IDS = [
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
]
ACTIVE_CONTINUATION_ROOTS = {
    "val_salt_test_2_coarse_mesh_laminar": WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "case_stage" / "val_salt_test_2_coarse_mesh_laminar_continuation",
}
WALL_PROBE_LOCATIONS = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "tp_tw_probe_locations.csv"
DIRECT_VALIDATION_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_direct_validation" / "ethan_direct_validation_metrics.csv"
OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-04_salt2_behavior_package"
LAST_WINDOW_COUNT = 50
TP_LABELS = [f"TP{i}" for i in range(1, 7)]
TW_LABELS = [f"TW{i}" for i in range(1, 12)]
SELECTED_TP = ["TP1", "TP4", "TP6"]
SELECTED_TW = ["TW5", "TW9"]
HEATER_PATCHES = {"pipeleg_lower_04_straight", "pipeleg_lower_05_straight", "pipeleg_lower_06_straight"}
TEST_SECTION_PATCHES = {"pipeleg_left_04_test_section"}
COOLING_BRANCH_PATCHES = {"pipeleg_upper_04_reducer", "pipeleg_upper_05_cooler", "pipeleg_upper_06_reducer"}
CASE_COLORS = {
    "val_salt_test_2_coarse_mesh_laminar": "#1f1f1f",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "#0b6e4f",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": "#bc3908",
}
CASE_LABELS = {
    "val_salt_test_2_coarse_mesh_laminar": "val_salt_test_2",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "salt2 Jin",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": "salt2 Kirst",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a compact Salt 2 behavior package with shared-axis time histories and last-window summaries.")
    parser.add_argument("--source-id", action="append", dest="source_ids", help="Repeat to override the default Salt 2 comparison set.")
    parser.add_argument("--last-window-count", type=int, default=LAST_WINDOW_COUNT, help="Number of trailing samples used for steady-state window statistics.")
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_runtime_root(source_id: str) -> tuple[Path, Path, dict[str, object]]:
    registry_row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)
    source_root = Path(registry_row["source_root"]).resolve()
    runtime_root = ACTIVE_CONTINUATION_ROOTS.get(source_id, source_root)
    metadata = load_case_metadata(runtime_root) or load_case_metadata(source_root)
    return source_root, runtime_root, metadata


def load_wall_probe_order() -> list[str]:
    labels: list[str] = []
    with WALL_PROBE_LOCATIONS.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("group") == "TW":
                labels.append(row["label"])
    return labels


def parse_outer_insulation_thickness_in(source_root: Path) -> float | None:
    path = source_root / "0" / "T"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"thicknessLayers\s*\(([^)]+)\)", text)
    if not match:
        return None
    parts = [safe_float(item) for item in match.group(1).split()]
    if len(parts) < 2 or parts[1] is None:
        return None
    return float(parts[1]) / 0.0254


def parse_patch_imposed_q(source_root: Path) -> dict[str, float]:
    path = source_root / "0" / "T"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    imposed: dict[str, float] = {}
    for match in re.finditer(r'"([^\"]+)"\s*\{(.*?)\n\}', text, re.S):
        patch = match.group(1)
        body = match.group(2)
        q_match = re.search(r"\bQ\s+constant\s+([^;\s]+)", body)
        if q_match:
            value = safe_float(q_match.group(1))
            if value is not None:
                imposed[patch] = value
    return imposed


def wall_section_bucket(patch: str) -> str:
    if patch in HEATER_PATCHES:
        return "heater"
    if patch in TEST_SECTION_PATCHES:
        return "test_section"
    if patch in COOLING_BRANCH_PATCHES:
        return "cooling_branch"
    if patch.startswith("pipeleg_right_"):
        return "downcomer"
    if patch.startswith("pipeleg_left_"):
        return "upcomer"
    if patch.startswith("pipeleg_upper_"):
        return "upper_transport"
    if patch.startswith("pipeleg_lower_"):
        return "lower_transport"
    if patch.startswith("junction_"):
        return "junctions"
    return "other"


def parse_mdot_mean_series(source_root: Path) -> tuple[np.ndarray, np.ndarray]:
    time_map: dict[float, list[float]] = {}
    for path in sorted((source_root / "postProcessing").glob("mdot_*/0/surfaceFieldValue.dat")):
        for row in parse_scalar_series(path):
            time_map.setdefault(float(row["time"]), []).append(abs(float(row["value"])))
    times = sorted(time_map)
    return np.array(times), np.array([mean(time_map[t]) for t in times])


def parse_temperature_probe_series(source_root: Path) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]:
    payload = parse_probe_series(source_root / "postProcessing" / "temperature_probes" / "0" / "T")
    rows = payload["rows"]
    if not rows:
        return np.array([]), {}, np.array([])
    times = np.array([float(row["time"]) for row in rows])
    matrix = np.array([[float(value) for value in row["values"]] for row in rows])
    series = {label: matrix[:, index] for index, label in enumerate(TP_LABELS) if index < matrix.shape[1]}
    return times, series, matrix.mean(axis=1)


def parse_wall_temperature_series(source_root: Path, wall_probe_order: list[str]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    payload = parse_probe_series(source_root / "postProcessing" / "wall_temperature_probes" / "0" / "T")
    rows = payload["rows"]
    if not rows:
        return np.array([]), {}
    times = np.array([float(row["time"]) for row in rows])
    grouped: dict[str, list[list[float]]] = {}
    for row in rows:
        station_map: dict[str, list[float]] = {}
        for index, value in enumerate(row["values"]):
            label = wall_probe_order[index] if index < len(wall_probe_order) else f"TW_unknown_{index}"
            station = label.split("_", 1)[0]
            station_map.setdefault(station, []).append(float(value))
        for station, values in station_map.items():
            grouped.setdefault(station, []).append(values)
    averaged = {station: np.array([mean(samples) for samples in grouped[station]]) for station in grouped}
    return times, averaged


def parse_wall_heatflux_section_series(source_root: Path, metadata: dict[str, object]) -> list[dict[str, float]]:
    candidates = sorted(source_root.glob("postProcessing/wallHeatFlux/*/wallHeatFlux.dat"), key=lambda item: item.parent.name)
    if not candidates:
        return []
    imposed_q = parse_patch_imposed_q(source_root)
    rows_by_time: dict[float, dict[str, float]] = {}
    with candidates[-1].open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 5:
                continue
            time_value = safe_float(parts[0])
            q_value = safe_float(parts[4])
            if time_value is None or q_value is None:
                continue
            rows_by_time.setdefault(float(time_value), {})[parts[1]] = float(q_value)
    operating_cooling = safe_float(path_lookup(metadata, "operating_point.cooling_power_W")) or 0.0
    section_rows: list[dict[str, float]] = []
    for time_value in sorted(rows_by_time):
        patch_map = rows_by_time[time_value]
        sections = {
            "downcomer": 0.0,
            "heater": 0.0,
            "upcomer": 0.0,
            "test_section": 0.0,
            "cooling_branch": 0.0,
            "upper_transport": 0.0,
            "lower_transport": 0.0,
            "junctions": 0.0,
            "other": 0.0,
        }
        passive_ambient = 0.0
        powered_section_ambient = 0.0
        cooling_branch_total = 0.0
        for patch, q_value in patch_map.items():
            if patch.startswith("ncc_"):
                continue
            sections[wall_section_bucket(patch)] += q_value
            if patch in COOLING_BRANCH_PATCHES and q_value < 0.0:
                cooling_branch_total += abs(q_value)
                continue
            imposed = imposed_q.get(patch)
            if imposed is not None and imposed > 0.0:
                powered_section_ambient += max(imposed - q_value, 0.0)
            elif q_value < 0.0:
                passive_ambient += abs(q_value)
        cooling_branch_excess = max(cooling_branch_total - operating_cooling, 0.0)
        section_rows.append(
            {
                "time": time_value,
                "ambient_proxy_w": passive_ambient + powered_section_ambient + cooling_branch_excess,
                "ambient_noncooling_proxy_w": passive_ambient + powered_section_ambient,
                "cooling_branch_total_removal_w": cooling_branch_total,
                "cooling_branch_excess_w": cooling_branch_excess,
                "net_total_q_w": sum(value for patch, value in patch_map.items() if not patch.startswith("ncc_")),
                **{f"section_{name}_net_q_w": value for name, value in sections.items()},
            }
        )
    return section_rows


def rows_to_series(rows: list[dict[str, float]], keys: list[str]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    if not rows:
        return np.array([]), {key: np.array([]) for key in keys}
    times = np.array([row["time"] for row in rows])
    series = {key: np.array([row[key] for row in rows]) for key in keys}
    return times, series


def compute_last_window_stats(source_id: str, metric: str, times: np.ndarray, values: np.ndarray, window_count: int) -> dict[str, object]:
    if len(times) == 0 or len(values) == 0:
        return {
            "source_id": source_id,
            "metric": metric,
            "window_count": 0,
            "time_start": "",
            "time_end": "",
            "mean": "",
            "std": "",
            "min": "",
            "max": "",
            "slope_per_s": "",
            "end_minus_start": "",
        }
    count = min(window_count, len(times))
    t = times[-count:]
    v = values[-count:]
    slope = 0.0 if count < 2 else float(np.polyfit(t, v, 1)[0])
    return {
        "source_id": source_id,
        "metric": metric,
        "window_count": count,
        "time_start": float(t[0]),
        "time_end": float(t[-1]),
        "mean": float(np.mean(v)),
        "std": float(np.std(v)),
        "min": float(np.min(v)),
        "max": float(np.max(v)),
        "slope_per_s": slope,
        "end_minus_start": float(v[-1] - v[0]),
    }


def csv_dump(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_case_payload(source_id: str, wall_probe_order: list[str], window_count: int) -> dict[str, object]:
    source_root, runtime_root, metadata = load_runtime_root(source_id)
    mdot_t, mdot_v = parse_mdot_mean_series(runtime_root)
    tp_t, tp_series, tp_mean = parse_temperature_probe_series(runtime_root)
    tw_t, tw_series = parse_wall_temperature_series(runtime_root, wall_probe_order)
    heat_rows = parse_wall_heatflux_section_series(runtime_root, metadata)
    heat_keys = [
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
    heat_t, heat_series = rows_to_series(heat_rows, heat_keys)
    validation_rows = {row["source_id"]: row for row in load_csv_rows(DIRECT_VALIDATION_CSV)}
    validation_row = validation_rows.get(source_id, {})

    setup = {
        "source_id": source_id,
        "label": CASE_LABELS[source_id],
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "T_init_K": path_lookup(metadata, "operating_point.T_init_K", ""),
        "cooler_h_W_m2K": path_lookup(metadata, "bc_params.cooler.h", ""),
        "outer_insulation_thickness_in": parse_outer_insulation_thickness_in(runtime_root) or "",
        "mu_spec_type": path_lookup(metadata, "fluid_properties.mu_spec.type", ""),
        "mu_coeffs": json.dumps(path_lookup(metadata, "fluid_properties.mu_spec.coeffs", []) or []),
        "cp_model": "constant 1423.47 J/kg-K" if path_lookup(metadata, "fluid_properties.Cp_coeffs.0", None) == 1423.47 else json.dumps(path_lookup(metadata, "fluid_properties.Cp_coeffs", []) or []),
        "mdot_time_end_s": float(mdot_t[-1]) if len(mdot_t) else "",
        "tp_time_end_s": float(tp_t[-1]) if len(tp_t) else "",
        "tw_time_end_s": float(tw_t[-1]) if len(tw_t) else "",
        "wall_heat_time_end_s": float(heat_t[-1]) if len(heat_t) else "",
        "tw10_excluded_from_rmse": validation_row.get("tw10_excluded_from_rmse", ""),
        "exp_tp_rmse_k": validation_row.get("exp_tp_rmse_k", ""),
        "exp_tw_rmse_k": validation_row.get("exp_tw_rmse_k", ""),
        "exp_all_temp_rmse_k": validation_row.get("exp_all_temp_rmse_k", ""),
        "exp_mdot_abs_error_pct": validation_row.get("exp_mdot_abs_error_pct", ""),
    }

    timeseries_rows: list[dict[str, object]] = []
    all_times = sorted(set(mdot_t.tolist()) | set(tp_t.tolist()) | set(tw_t.tolist()) | set(heat_t.tolist()))
    mdot_map = {float(t): float(v) for t, v in zip(mdot_t, mdot_v)}
    tp_mean_map = {float(t): float(v) for t, v in zip(tp_t, tp_mean)}
    tp_maps = {label: {float(t): float(v) for t, v in zip(tp_t, values)} for label, values in tp_series.items()}
    tw_maps = {label: {float(t): float(v) for t, v in zip(tw_t, values)} for label, values in tw_series.items()}
    heat_maps = {key: {float(t): float(v) for t, v in zip(heat_t, values)} for key, values in heat_series.items()}
    for time_value in all_times:
        row = {
            "source_id": source_id,
            "label": CASE_LABELS[source_id],
            "time": time_value,
            "mdot_mean_abs_kg_s": mdot_map.get(time_value, ""),
            "tp_mean_K": tp_mean_map.get(time_value, ""),
        }
        for label in SELECTED_TP:
            row[f"{label}_K"] = tp_maps.get(label, {}).get(time_value, "")
        for label in SELECTED_TW:
            row[f"{label}_K"] = tw_maps.get(label, {}).get(time_value, "")
        for key in heat_keys:
            row[key] = heat_maps.get(key, {}).get(time_value, "")
        timeseries_rows.append(row)

    metrics = {
        "mdot_mean_abs_kg_s": (mdot_t, mdot_v),
        "tp_mean_K": (tp_t, tp_mean),
        **{f"{label}_K": (tp_t, tp_series[label]) for label in SELECTED_TP if label in tp_series},
        **{f"{label}_K": (tw_t, tw_series[label]) for label in SELECTED_TW if label in tw_series},
        **{key: (heat_t, values) for key, values in heat_series.items() if key in {
            "ambient_proxy_w",
            "section_downcomer_net_q_w",
            "section_heater_net_q_w",
            "section_upcomer_net_q_w",
            "section_test_section_net_q_w",
            "section_cooling_branch_net_q_w",
        }},
    }
    last_window_rows = [compute_last_window_stats(source_id, metric, times, values, window_count) for metric, (times, values) in metrics.items()]

    return {
        "source_id": source_id,
        "setup": setup,
        "timeseries_rows": timeseries_rows,
        "last_window_rows": last_window_rows,
        "metrics": metrics,
        "validation_row": validation_row,
    }


def plot_shared_metric(cases: list[dict[str, object]], metric: str, ylabel: str, title: str, stem: str) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    for case in cases:
        times, values = case["metrics"][metric]
        ax.plot(times, values, linewidth=2.2, label=CASE_LABELS[case["source_id"]], color=CASE_COLORS[case["source_id"]])
    ax.set_title(title)
    ax.set_xlabel("Simulation time [s]")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    save_matplotlib_figure(fig, OUTPUT_DIR, stem, dpi=180)
    plt.close(fig)


def plot_multi_panel(cases: list[dict[str, object]], metrics: list[tuple[str, str, str]], stem: str, fig_title: str) -> None:
    fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 2.8 * len(metrics)), sharex=True)
    if len(metrics) == 1:
        axes = [axes]
    for ax, (metric, ylabel, subtitle) in zip(axes, metrics):
        for case in cases:
            times, values = case["metrics"][metric]
            ax.plot(times, values, linewidth=2.0, label=CASE_LABELS[case["source_id"]], color=CASE_COLORS[case["source_id"]])
        ax.set_ylabel(ylabel)
        ax.set_title(subtitle)
        ax.grid(True, alpha=0.25)
    axes[-1].set_xlabel("Simulation time [s]")
    axes[0].legend(loc="best", ncol=3, fontsize=9)
    fig.suptitle(fig_title, y=0.995)
    fig.tight_layout()
    save_matplotlib_figure(fig, OUTPUT_DIR, stem, dpi=180)
    plt.close(fig)


def write_readme(cases: list[dict[str, object]], output_dir: Path, window_count: int) -> None:
    by_id = {case["source_id"]: case for case in cases}
    val = by_id["val_salt_test_2_coarse_mesh_laminar"]["validation_row"]
    jin = by_id["viscosity_screening_salt_test_2_jin_coarse_mesh"]["validation_row"]
    kirst = by_id["viscosity_screening_salt_test_2_kirst_coarse_mesh"]["validation_row"]
    lines = [
        "# Salt 2 Behavior Package",
        "",
        "This package compares the three Salt 2 3D CFD rows on shared axes and summarizes their late-window behavior.",
        "",
        "## Scope",
        "",
        "- `val_salt_test_2_coarse_mesh_laminar` is the native validation/continuation case and is still running.",
        "- `viscosity_screening_salt_test_2_jin_coarse_mesh` is the staged Jin branch.",
        "- `viscosity_screening_salt_test_2_kirst_coarse_mesh` is the staged Kirst branch.",
        "",
        "## Explicit validation convention",
        "",
        "- `TW10` is intentionally excluded from RMSE-based wall metrics and combined temperature RMSE in this package and in the direct-validation package.",
        "- Raw `TW10` error is still retained in the direct-validation CSV for transparency, but it is not used to score wall RMSE or combined RMSE.",
        "",
        "## Data availability note",
        "",
        "- The active `val_salt_test_2` continuation tree currently carries mdot, TP, and wall-temperature probe outputs through `1724 s`, while `wallHeatFlux` extends through about `3291 s`.",
        "- Because of that mismatch, mdot and probe last-window statistics for `val_salt_test_2` reflect the late pre-continuation window, while ambient-loss and section-heat statistics reflect the active continuation tail.",
        "- The generated `salt2_setup_comparison.csv` now records metric-specific end times so that this distinction is explicit.",
        "",
        "## Key findings so far",
        "",
        f"- `val_salt_test_2` still has the best Salt 2 bulk-probe agreement: TP RMSE `{val['exp_tp_rmse_k']}` K vs staged Jin `{jin['exp_tp_rmse_k']}` K and staged Kirst `{kirst['exp_tp_rmse_k']}` K.",
        f"- `val_salt_test_2` also has the best Salt 2 mass-flow agreement: mdot absolute error `{val['exp_mdot_abs_error_pct']}`% vs staged Jin `{jin['exp_mdot_abs_error_pct']}`% and staged Kirst `{kirst['exp_mdot_abs_error_pct']}`%.",
        f"- Under the corrected ambient-loss basis, the three Salt 2 rows are relatively close to one another on derived ambient loss: val `{val['exp_q_external_loss_abs_error_pct']}`%, Jin `{jin['exp_q_external_loss_abs_error_pct']}`%, Kirst `{kirst['exp_q_external_loss_abs_error_pct']}`% low relative to the Ethan-linked `qambient_total_W` reference.",
        "- The strongest current explanation for the better `val_salt_test_2` behavior is the combined setup difference: thicker insulation, slightly lower cooler `h`, hotter start, Jin-type viscosity, and longer runtime.",
        "",
        "## Recommended Salt 2 defaults for subsequent runs",
        "",
        "- Use the `val_salt_test_2` Salt 2 setup as the default basis for future Salt 2 runs.",
        "- Carry forward the hotter start, the thicker insulation, and the slightly lower cooler `h`.",
        "- Keep the Jin-style viscosity branch as the starting point when mdot matching matters.",
        "- `Cp` in `val_salt_test_2` is effectively constant `1423.47 J/kg-K`.",
        "",
        "## Figures",
        "",
        "- `figures/png/salt2_mdot_compare.png`: mean absolute mdot on shared axes.",
        "- `figures/png/salt2_tp_compare.png`: `TPmean`, `TP1`, `TP4`, and `TP6` on shared axes.",
        "- `figures/png/salt2_tw_and_ambient_compare.png`: selected wall stations (`TW5`, `TW9`) plus derived ambient-loss proxy on shared axes.",
        "- `figures/png/salt2_section_heat_compare.png`: downcomer, heater, upcomer, test-section, and cooling-branch section totals on shared axes.",
        "",
        "## Last-window summary",
        "",
        f"- Late-window statistics use the last `{window_count}` samples of each metric independently.",
        "- Use `salt2_last_window_summary.csv` for mean/std/slope comparisons and `salt2_behavior_timeseries.csv` for direct follow-on analysis.",
        "",
        "## Suggested next analysis step",
        "",
        "- Extend this same script to compare section-wise drift rates and to derive a stricter steady-state audit from last-window slopes rather than from the coded convergence flag alone.",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = args.source_ids or DEFAULT_SOURCE_IDS
    wall_probe_order = load_wall_probe_order()
    ensure_dir(OUTPUT_DIR)

    cases = [build_case_payload(source_id, wall_probe_order, args.last_window_count) for source_id in source_ids]

    setup_rows = [case["setup"] for case in cases]
    setup_fields = list(setup_rows[0].keys())
    csv_dump(OUTPUT_DIR / "salt2_setup_comparison.csv", setup_fields, setup_rows)

    timeseries_rows = [row for case in cases for row in case["timeseries_rows"]]
    timeseries_fields = list(timeseries_rows[0].keys())
    csv_dump(OUTPUT_DIR / "salt2_behavior_timeseries.csv", timeseries_fields, timeseries_rows)

    last_window_rows = [row for case in cases for row in case["last_window_rows"]]
    last_window_fields = list(last_window_rows[0].keys())
    csv_dump(OUTPUT_DIR / "salt2_last_window_summary.csv", last_window_fields, last_window_rows)

    plot_shared_metric(cases, "mdot_mean_abs_kg_s", "|mdot| [kg/s]", "Salt 2 mean absolute mass flow", "salt2_mdot_compare")
    plot_multi_panel(
        cases,
        [
            ("tp_mean_K", "TP mean [K]", "TP mean"),
            ("TP1_K", "TP1 [K]", "TP1"),
            ("TP4_K", "TP4 [K]", "TP4"),
            ("TP6_K", "TP6 [K]", "TP6"),
        ],
        "salt2_tp_compare",
        "Salt 2 bulk-temperature probe comparison",
    )
    plot_multi_panel(
        cases,
        [
            ("TW5_K", "TW5 [K]", "TW5"),
            ("TW9_K", "TW9 [K]", "TW9"),
            ("ambient_proxy_w", "Ambient proxy [W]", "Derived ambient-loss proxy"),
        ],
        "salt2_tw_and_ambient_compare",
        "Salt 2 selected wall temperatures and ambient-loss proxy",
    )
    plot_multi_panel(
        cases,
        [
            ("section_downcomer_net_q_w", "Q [W]", "Downcomer"),
            ("section_heater_net_q_w", "Q [W]", "Heater"),
            ("section_upcomer_net_q_w", "Q [W]", "Upcomer"),
            ("section_test_section_net_q_w", "Q [W]", "Test section"),
            ("section_cooling_branch_net_q_w", "Q [W]", "Cooling branch"),
        ],
        "salt2_section_heat_compare",
        "Salt 2 section-wise heat-transfer comparison",
    )

    summary_payload = {
        "generated_at": iso_timestamp(),
        "source_ids": source_ids,
        "setup_rows": setup_rows,
        "last_window_rows": last_window_rows,
    }
    with (OUTPUT_DIR / "salt2_behavior_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, indent=2)
        handle.write("\n")

    write_readme(cases, OUTPUT_DIR, args.last_window_count)
    print(json.dumps({"output_dir": str(OUTPUT_DIR), "source_ids": source_ids}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
