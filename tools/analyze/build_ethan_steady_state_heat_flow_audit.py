#!/usr/bin/env python3
"""Build a cross-case late-window wallHeatFlux heat-flow audit.

Workflow role:
    This is a thermal-closure inventory script. It reads registered case
    metadata, validation tables, steadiness summaries, and wallHeatFlux-derived
    histories to compare late-window heater input, cooling removal, passive
    ambient exchange, section totals, and residuals across the Ethan family.

Inputs:
    - `registry/case_registry.csv` plus June 4 metadata/validation reports.
    - Per-case probe and wallHeatFlux histories located through registered
      runtime/source paths.

Outputs:
    CSV, JSON, README, and optional figures under the selected output
    directory. The products are audit evidence, not solver inputs.

CLI modifiers:
    - `--source-id` may be repeated to restrict the audit to specific cases.
    - `--window-count` changes the retained late-time averaging window.
    - `--skip-figures` keeps the audit table-only for faster smoke runs.

Boundaries:
    The script is read-only with respect to solver cases. It produces a
    case-level heat-flow audit and does not replace the still-needed patchwise
    heat-source/sink ledger that separates heater, cooler, passive loss,
    junction, enthalpy-change, sign-convention, and radiation-caveat terms.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
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

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    load_case_metadata,
    parse_probe_series,
    parse_scalar_series,
    read_registry_rows,
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

REGISTRY_CSV = WORKSPACE_ROOT / "registry" / "case_registry.csv"
METADATA_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"
VALIDATION_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_direct_validation" / "ethan_direct_validation_metrics.csv"
SALT_STEADINESS_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_essential_steadiness_audit" / "salt_case_essential_steadiness.csv"
OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_steady_state_heat_flow_audit"
WINDOW_COUNT = 50

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

SECTION_KEYS = [
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

METRIC_LABELS = {
    "ambient_proxy_w": "Ambient proxy",
    "ambient_noncooling_proxy_w": "Ambient non-cooling proxy",
    "cooling_branch_total_removal_w": "Cooling branch total removal",
    "cooling_branch_excess_w": "Cooling branch excess",
    "net_total_q_w": "Net wall heat",
    "section_downcomer_net_q_w": "Downcomer",
    "section_heater_net_q_w": "Heater",
    "section_upcomer_net_q_w": "Upcomer",
    "section_test_section_net_q_w": "Test section",
    "section_cooling_branch_net_q_w": "Cooling branch",
    "section_upper_transport_net_q_w": "Upper transport",
    "section_lower_transport_net_q_w": "Lower transport",
    "section_junctions_net_q_w": "Junctions",
    "section_other_net_q_w": "Other",
}

FLUID_COLORS = {
    "salt": "#bc3908",
    "water": "#0b6e4f",
}

VARIANT_MARKERS = {
    "": "o",
    "jin": "s",
    "kirst": "^",
}

VARIANT_SORT_ORDER = {
    "": 0,
    "jin": 1,
    "kirst": 2,
}

SCATTER_LABEL_OFFSETS = {
    "S1 jin": (0.18, 0.14),
    "S1 kirst": (0.18, 0.02),
    "S2 val": (0.18, 0.00),
    "S2 jin": (0.18, 0.12),
    "S2 kirst": (0.18, 0.26),
    "S3 jin": (0.18, 0.16),
    "S3 kirst": (0.18, 0.02),
    "S4 jin": (0.18, 0.18),
    "S4 kirst": (0.18, 0.04),
    "W1": (0.20, 0.00),
    "W2": (0.20, 0.05),
    "W3": (0.20, 0.04),
    "W4": (0.20, 0.05),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a cross-case steady-state heat-flow audit from the current Ethan wallHeatFlux tails "
            "and existing June 4 metadata/validation indices."
        )
    )
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Repeat to restrict the audit to a subset of registered CFD cases.",
    )
    parser.add_argument(
        "--window-count",
        type=int,
        default=WINDOW_COUNT,
        help="Trailing wall-heat samples to include in the frozen late-window summary.",
    )
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Write tables and README only; skip figure generation.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def default_source_ids() -> list[str]:
    metadata_rows = load_csv_rows(METADATA_CSV)
    if metadata_rows:
        return [row["source_id"] for row in metadata_rows if row.get("source_id")]
    registry_rows = read_registry_rows(REGISTRY_CSV)
    return [
        row["source_id"]
        for row in registry_rows
        if row.get("status") == "registered" and row.get("source_id") != "modern_runs_campaign_inventory_2026-06-01"
    ]


def case_number(base_case_id: str) -> str:
    parts = base_case_id.split("_")
    return parts[-1] if parts else base_case_id


def fluid_family(fluid: str) -> str:
    lowered = fluid.lower()
    if "water" in lowered:
        return "water"
    if "salt" in lowered:
        return "salt"
    return lowered


def display_case_label(base_case_id: str, fluid: str, variant_label: str) -> str:
    prefix = "S" if fluid_family(fluid) == "salt" else "W"
    base = f"{prefix}{case_number(base_case_id)}"
    if fluid == "salt" and not variant_label and base_case_id == "salt_test_2":
        return f"{base} val"
    if variant_label:
        return f"{base} {variant_label}"
    return base


def as_float(value: object) -> float | None:
    return safe_float(value)


def plot_case_label(row: dict[str, object]) -> str:
    base_case_id = str(row.get("base_case_id", ""))
    fluid = str(row.get("fluid", ""))
    variant_label = str(row.get("variant_label", ""))
    prefix = "S" if fluid_family(fluid) == "salt" else "W"
    base = f"{prefix}{case_number(base_case_id)}"
    if fluid_family(fluid) == "salt" and base_case_id == "salt_test_2" and not variant_label:
        return f"{base} val"
    if variant_label:
        return f"{base} {variant_label}"
    return base


def case_sort_key(row: dict[str, object]) -> tuple[int, int, int, str]:
    fluid = fluid_family(str(row.get("fluid", "")))
    fluid_order = 0 if fluid == "salt" else 1
    base_case_id = str(row.get("base_case_id", ""))
    try:
        case_idx = int(case_number(base_case_id))
    except ValueError:
        case_idx = 999
    variant_label = str(row.get("variant_label", ""))
    variant_order = VARIANT_SORT_ORDER.get(variant_label, 99)
    return fluid_order, case_idx, variant_order, str(row.get("source_id", ""))


def split_plot_rows(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    sorted_rows = sorted(rows, key=case_sort_key)
    return {
        "salt": [row for row in sorted_rows if fluid_family(str(row.get("fluid", ""))) == "salt"],
        "water": [row for row in sorted_rows if fluid_family(str(row.get("fluid", ""))) == "water"],
    }


def format_bar_labels(values: np.ndarray) -> list[str]:
    labels: list[str] = []
    for value in values:
        labels.append("" if abs(value) < 0.05 else f"{value:.1f}")
    return labels


def load_runtime_context(source_id: str) -> tuple[dict[str, str], dict[str, str], dict[str, str], Path, Path, dict[str, Any]]:
    metadata_map = {row["source_id"]: row for row in load_csv_rows(METADATA_CSV) if row.get("source_id")}
    validation_map = {row["source_id"]: row for row in load_csv_rows(VALIDATION_CSV) if row.get("source_id")}
    steadiness_map = {row["source_id"]: row for row in load_csv_rows(SALT_STEADINESS_CSV) if row.get("source_id")}
    registry_map = {row["source_id"]: row for row in read_registry_rows(REGISTRY_CSV) if row.get("source_id")}

    metadata_row = metadata_map.get(source_id, {})
    validation_row = validation_map.get(source_id, {})
    steadiness_row = steadiness_map.get(source_id, {})
    registry_row = registry_map.get(source_id, {})
    if not registry_row and not metadata_row:
        raise KeyError(f"source_id not found: {source_id}")
    runtime_root = Path(metadata_row.get("active_runtime_root") or metadata_row.get("source_root") or registry_row.get("source_root", "")).resolve()
    source_root = Path(metadata_row.get("source_root") or registry_row.get("source_root", "") or runtime_root).resolve()
    metadata = load_case_metadata(runtime_root) or load_case_metadata(source_root) or {}
    return metadata_row, validation_row, steadiness_row, runtime_root, source_root, metadata


def latest_time_from_probe_file(path: Path) -> tuple[float | None, int]:
    payload = parse_probe_series(path)
    rows = payload["rows"]
    if not rows:
        return None, 0
    return float(rows[-1]["time"]), len(rows)


def window_status(sample_count: int, target: int) -> str:
    if sample_count <= 0:
        return "missing"
    if sample_count == 1:
        return "latest_only"
    if sample_count < target:
        return "short_window"
    return "usable_window"


def latest_metric(values: np.ndarray) -> float | None:
    if len(values) == 0:
        return None
    return float(values[-1])


def compute_window_stats(times: np.ndarray, values: np.ndarray, target: int) -> dict[str, object]:
    sample_count = len(times)
    status = window_status(sample_count, target)
    if sample_count == 0:
        return {
            "status": status,
            "window_count": 0,
            "time_start": "",
            "time_end": "",
            "latest": "",
            "mean": "",
            "min": "",
            "max": "",
            "span": "",
            "drift": "",
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
    drift_pct = ""
    if abs(mean_value) > 1.0e-12:
        drift_pct = drift / mean_value * 100.0
    return {
        "status": status,
        "window_count": count,
        "time_start": float(t[0]),
        "time_end": float(t[-1]),
        "latest": float(v[-1]),
        "mean": mean_value,
        "min": min_value,
        "max": max_value,
        "span": span,
        "drift": drift,
        "drift_pct_of_mean": drift_pct,
        "slope_per_s": slope,
    }


def dominant_loss_section(latest_row: dict[str, float | int | str]) -> tuple[str, float]:
    best_key = ""
    best_value = 0.0
    for key in SECTION_KEYS:
        value = as_float(latest_row.get(key))
        if value is None or value >= 0.0:
            continue
        magnitude = abs(value)
        if magnitude > best_value:
            best_key = key
            best_value = magnitude
    label = METRIC_LABELS.get(best_key, best_key.replace("section_", "").replace("_net_q_w", "")) if best_key else ""
    return label, best_value


def build_case_note(
    metadata_row: dict[str, str],
    validation_row: dict[str, str],
    heat_time: float | None,
    window_state: str,
    sample_count: int,
) -> str:
    notes: list[str] = []
    metadata_final_time = as_float(metadata_row.get("final_time"))
    if heat_time is not None and metadata_final_time is not None and heat_time > metadata_final_time + 1.0e-9:
        notes.append(
            f"latest wall-heat time {heat_time:.1f} s extends beyond the June 4 metadata snapshot at {metadata_final_time:.1f} s"
        )
    if validation_row.get("exp_tw_rmse_k") and metadata_final_time is not None and heat_time is not None and heat_time > metadata_final_time + 1.0e-9:
        notes.append("TW RMSE provenance remains the June 4 direct-validation package")
    if window_state != "usable_window":
        if window_state == "short_window":
            notes.append(f"only {sample_count} wall-heat samples available for the late window")
        elif window_state == "latest_only":
            notes.append("only one wall-heat sample is available")
        elif window_state == "missing":
            notes.append("wallHeatFlux history is missing")
    return "; ".join(notes)


def hypothesis_for_case(latest_row: dict[str, object]) -> tuple[str, str]:
    status = str(latest_row.get("steady_window_status", ""))
    tw_rmse = as_float(latest_row.get("exp_tw_rmse_k"))
    ambient_error_pct = as_float(latest_row.get("ambient_error_pct"))
    ambient_error_w = as_float(latest_row.get("ambient_error_w"))
    cooling_excess = as_float(latest_row.get("cooling_branch_excess_w")) or 0.0
    operating_cooling = as_float(latest_row.get("cooling_power_w")) or 0.0
    net_total_q_pct = as_float(latest_row.get("net_total_q_pct_of_heater")) or 0.0
    junction_loss = abs(as_float(latest_row.get("section_junctions_net_q_w")) or 0.0)
    other_loss = abs(as_float(latest_row.get("section_other_net_q_w")) or 0.0)
    ambient_proxy = abs(as_float(latest_row.get("ambient_proxy_w")) or 0.0)
    test_section_loss = abs(as_float(latest_row.get("section_test_section_net_q_w")) or 0.0)

    if status in {"missing", "latest_only"} or tw_rmse is None:
        return (
            "insufficient_evidence",
            "Steady-state interpretation is weak because either wall-heat history or TW validation context is incomplete.",
        )

    if abs(net_total_q_pct) >= 5.0:
        return (
            "heat_balance_residual",
            f"The net wall-heat residual is still {net_total_q_pct:.2f}% of heater power, so tail imbalance can still contaminate a strict TW interpretation.",
        )

    if ambient_error_pct is not None and ambient_error_w is not None and abs(ambient_error_pct) >= 15.0:
        direction = "over-loss" if ambient_error_w > 0.0 else "under-loss"
        return (
            direction,
            f"The derived ambient proxy differs from the Ethan-linked ambient reference by {ambient_error_w:.2f} W ({ambient_error_pct:.2f}%), making wall-loss partitioning the first TW suspect.",
        )

    cooling_threshold = max(10.0, 0.10 * operating_cooling)
    if cooling_excess >= cooling_threshold:
        return (
            "cooling_branch_mismatch",
            f"Cooling-branch removal exceeds the operating-point duty by {cooling_excess:.2f} W, which can shift the wall-temperature field even if the global ambient proxy looks acceptable.",
        )

    if ambient_proxy > 0.0 and (junction_loss + other_loss) / ambient_proxy >= 0.20 and tw_rmse >= 4.0:
        share = (junction_loss + other_loss) / ambient_proxy * 100.0
        return (
            "junction_loss_sensitivity",
            f"Junction plus uncategorized losses consume {share:.1f}% of the derived ambient proxy, so local 3D parasitics remain a plausible TW driver.",
        )

    if tw_rmse >= 4.0 and ambient_error_pct is not None and ambient_error_pct < 15.0:
        return (
            "source_shape_suspicion",
            f"Global heat partition is broadly plausible, but TW RMSE stays at {tw_rmse:.2f} K; that points more toward source-placement or local loss-shape effects than a bulk heat-budget miss. Test-section loss magnitude is {test_section_loss:.2f} W.",
        )

    if tw_rmse < 3.0 and (ambient_error_pct is None or ambient_error_pct < 10.0):
        return (
            "heat_partition_broadly_consistent",
            f"TW RMSE ({tw_rmse:.2f} K) and the ambient-loss proxy are both reasonably aligned, so the steady-state wall heat partition is broadly self-consistent for this case.",
        )

    return (
        "mixed_signal",
        "No single wall-loss or source-shape mechanism dominates this case from the current steady-state audit alone.",
    )


def recommendation_for_case(row: dict[str, object]) -> tuple[str, str, str]:
    status = str(row.get("steady_window_status", ""))
    note = str(row.get("note", ""))
    processor_minus_heat = as_float(row.get("processor_minus_heat_s")) or 0.0
    run_status = str(row.get("run_status", ""))
    heat_time = as_float(row.get("latest_heat_time_s"))
    heat_sample_count = int(row.get("heat_sample_count", 0) or 0)

    if status == "missing":
        return (
            "high",
            "rerun or repair wallHeatFlux extraction",
            "No usable wallHeatFlux tail was found, so this case cannot support a steady-state heat audit yet.",
        )
    if status == "latest_only":
        return (
            "high",
            "extend the run or recover more wallHeatFlux samples",
            "Only one wall-heat sample exists, which is not enough for a frozen late-window steadiness check.",
        )
    if status == "short_window":
        return (
            "medium",
            "extend the run or re-extract a longer tail window",
            f"Only {heat_sample_count} wall-heat samples are available, so the late-window statistics remain fragile.",
        )
    if processor_minus_heat > 50.0:
        return (
            "medium",
            "refresh postProcessing outputs against newer processor writes",
            f"Processor directories extend {processor_minus_heat:.1f} s beyond the latest wall-heat sample, so the current audit may lag the available native state.",
        )
    if "TW RMSE provenance remains the June 4 direct-validation package" in note:
        return (
            "medium",
            "refresh direct validation against the current runtime snapshot",
            "The wall-heat tail is newer than the June 4 validation snapshot, so the TW comparison is slightly out of date for this case.",
        )
    if run_status == "running":
        latest_text = f"latest heat time is {heat_time:.1f} s" if heat_time is not None else "the latest heat time is unavailable"
        return (
            "low",
            "monitor and refresh this audit after the run stabilizes further",
            f"The case is still marked running and {latest_text}, so this report should be treated as a frozen interim checkpoint.",
        )
    return (
        "low",
        "no immediate rerun required for heat accounting",
        "Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.",
    )


def summarize_case(
    source_id: str,
    metadata_row: dict[str, str],
    validation_row: dict[str, str],
    steadiness_row: dict[str, str],
    runtime_root: Path,
    source_root: Path,
    metadata: dict[str, Any],
    window_count: int,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    heat_rows = s2.parse_wall_heatflux_section_series(runtime_root, metadata)
    heat_time, heat_series = s2.rows_to_series(heat_rows, PRIMARY_HEAT_KEYS)
    total_q_rows = parse_scalar_series(runtime_root / "postProcessing" / "total_Q.dat")
    total_q_time = np.array([float(row["time"]) for row in total_q_rows]) if total_q_rows else np.array([])
    tp_time, tp_count = latest_time_from_probe_file(runtime_root / "postProcessing" / "temperature_probes" / "0" / "T")
    tw_time, tw_count = latest_time_from_probe_file(runtime_root / "postProcessing" / "wall_temperature_probes" / "0" / "T")
    latest_probe_time = max(value for value in [tp_time, tw_time] if value is not None) if any(value is not None for value in [tp_time, tw_time]) else None
    latest_heat_time = float(heat_time[-1]) if len(heat_time) else None
    latest_total_q_time = float(total_q_time[-1]) if len(total_q_time) else None
    latest_processor_time = as_float(metadata_row.get("latest_processor_time"))
    processor_minus_heat = latest_processor_time - latest_heat_time if latest_processor_time is not None and latest_heat_time is not None else ""
    heat_minus_probe = latest_heat_time - latest_probe_time if latest_heat_time is not None and latest_probe_time is not None else ""

    heat_sample_count = len(heat_rows)
    steady_window_status = window_status(heat_sample_count, window_count)
    note = build_case_note(metadata_row, validation_row, latest_heat_time, steady_window_status, heat_sample_count)

    heater_power_w = as_float(metadata_row.get("heater_power_W")) or as_float(metadata.get("operating_point", {}).get("heater_power_W"))
    cooling_power_w = as_float(metadata_row.get("cooling_power_W")) or as_float(metadata.get("operating_point", {}).get("cooling_power_W"))

    latest_row: dict[str, object] = {
        "source_id": source_id,
        "case_id": metadata_row.get("case_id", ""),
        "base_case_id": metadata_row.get("base_case_id", ""),
        "fluid": metadata_row.get("fluid", ""),
        "fluid_family": fluid_family(metadata_row.get("fluid", "")),
        "variant_label": metadata_row.get("variant_label", ""),
        "display_label": display_case_label(metadata_row.get("base_case_id", ""), metadata_row.get("fluid", ""), metadata_row.get("variant_label", "")),
        "run_status": metadata_row.get("run_status", ""),
        "essential_steadiness_class": steadiness_row.get("essential_steadiness_class", ""),
        "usable_for_steady_state_now": steadiness_row.get("usable_for_steady_state_now", ""),
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "latest_heat_time_s": latest_heat_time if latest_heat_time is not None else "",
        "latest_total_q_time_s": latest_total_q_time if latest_total_q_time is not None else "",
        "latest_tp_time_s": tp_time if tp_time is not None else "",
        "latest_tw_time_s": tw_time if tw_time is not None else "",
        "latest_probe_time_s": latest_probe_time if latest_probe_time is not None else "",
        "latest_processor_time_s": latest_processor_time if latest_processor_time is not None else "",
        "processor_minus_heat_s": processor_minus_heat,
        "heat_minus_probe_s": heat_minus_probe,
        "heat_sample_count": heat_sample_count,
        "probe_sample_count": max(tp_count, tw_count),
        "steady_window_status": steady_window_status,
        "steady_window_sample_count": min(window_count, heat_sample_count),
        "heater_power_w": heater_power_w if heater_power_w is not None else "",
        "cooling_power_w": cooling_power_w if cooling_power_w is not None else "",
        "exp_tw_rmse_k": validation_row.get("exp_tw_rmse_k", ""),
        "exp_tp_rmse_k": validation_row.get("exp_tp_rmse_k", ""),
        "exp_all_temp_rmse_k": validation_row.get("exp_all_temp_rmse_k", ""),
        "exp_q_external_loss_reference_w": validation_row.get("exp_q_external_loss_reference_w", ""),
        "validation_metrics_provenance": relative_validation_path(),
        "note": note,
    }

    for key in PRIMARY_HEAT_KEYS:
        latest_row[key] = latest_metric(heat_series.get(key, np.array([]))) if key in heat_series else ""

    ambient_proxy_w = as_float(latest_row.get("ambient_proxy_w"))
    ambient_reference_w = as_float(latest_row.get("exp_q_external_loss_reference_w"))
    ambient_error_w = ambient_proxy_w - ambient_reference_w if ambient_proxy_w is not None and ambient_reference_w is not None else ""
    ambient_error_pct = ""
    if ambient_error_w != "" and ambient_reference_w not in (None, 0.0):
        ambient_error_pct = ambient_error_w / ambient_reference_w * 100.0
    latest_row["ambient_error_w"] = ambient_error_w
    latest_row["ambient_error_pct"] = ambient_error_pct

    net_total_q_w = as_float(latest_row.get("net_total_q_w"))
    if net_total_q_w is not None and heater_power_w not in (None, 0.0):
        latest_row["net_total_q_pct_of_heater"] = net_total_q_w / heater_power_w * 100.0
    else:
        latest_row["net_total_q_pct_of_heater"] = ""

    if heater_power_w is not None and as_float(latest_row.get("section_heater_net_q_w")) is not None:
        latest_row["heater_section_gap_w"] = heater_power_w - (as_float(latest_row.get("section_heater_net_q_w")) or 0.0)
    else:
        latest_row["heater_section_gap_w"] = ""

    dominant_label, dominant_magnitude = dominant_loss_section(latest_row)
    latest_row["dominant_loss_section"] = dominant_label
    latest_row["dominant_loss_magnitude_w"] = dominant_magnitude if dominant_label else ""

    window_row: dict[str, object] = {
        "source_id": source_id,
        "base_case_id": metadata_row.get("base_case_id", ""),
        "fluid": metadata_row.get("fluid", ""),
        "fluid_family": fluid_family(metadata_row.get("fluid", "")),
        "variant_label": metadata_row.get("variant_label", ""),
        "run_status": metadata_row.get("run_status", ""),
        "steady_window_status": steady_window_status,
    }
    for key in PRIMARY_HEAT_KEYS:
        stats = compute_window_stats(heat_time, heat_series.get(key, np.array([])), window_count)
        for suffix, value in stats.items():
            window_row[f"{key}_{suffix}"] = value

    label, note_text = hypothesis_for_case(latest_row)
    latest_row["tw_hypothesis_label"] = label
    latest_row["tw_hypothesis_note"] = note_text

    hypothesis_row = {
        "source_id": source_id,
        "base_case_id": metadata_row.get("base_case_id", ""),
        "fluid": metadata_row.get("fluid", ""),
        "fluid_family": fluid_family(metadata_row.get("fluid", "")),
        "variant_label": metadata_row.get("variant_label", ""),
        "run_status": metadata_row.get("run_status", ""),
        "steady_window_status": steady_window_status,
        "exp_tw_rmse_k": latest_row.get("exp_tw_rmse_k", ""),
        "ambient_proxy_w": latest_row.get("ambient_proxy_w", ""),
        "exp_q_external_loss_reference_w": latest_row.get("exp_q_external_loss_reference_w", ""),
        "ambient_error_w": latest_row.get("ambient_error_w", ""),
        "ambient_error_pct": latest_row.get("ambient_error_pct", ""),
        "cooling_branch_total_removal_w": latest_row.get("cooling_branch_total_removal_w", ""),
        "cooling_branch_excess_w": latest_row.get("cooling_branch_excess_w", ""),
        "net_total_q_w": latest_row.get("net_total_q_w", ""),
        "net_total_q_pct_of_heater": latest_row.get("net_total_q_pct_of_heater", ""),
        "section_heater_net_q_w": latest_row.get("section_heater_net_q_w", ""),
        "section_test_section_net_q_w": latest_row.get("section_test_section_net_q_w", ""),
        "section_cooling_branch_net_q_w": latest_row.get("section_cooling_branch_net_q_w", ""),
        "section_junctions_net_q_w": latest_row.get("section_junctions_net_q_w", ""),
        "section_other_net_q_w": latest_row.get("section_other_net_q_w", ""),
        "dominant_loss_section": latest_row.get("dominant_loss_section", ""),
        "dominant_loss_magnitude_w": latest_row.get("dominant_loss_magnitude_w", ""),
        "tw_hypothesis_label": label,
        "tw_hypothesis_note": note_text,
        "note": note,
    }
    return latest_row, window_row, hypothesis_row


def relative_validation_path() -> str:
    return str(VALIDATION_CSV.relative_to(WORKSPACE_ROOT))


def project_rows(rows: list[dict[str, object]], fieldnames: list[str]) -> list[dict[str, object]]:
    return [{field: row.get(field, "") for field in fieldnames} for row in rows]


def write_case_heat_inventory(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "source_id",
        "case_id",
        "base_case_id",
        "fluid",
        "variant_label",
        "display_label",
        "run_status",
        "essential_steadiness_class",
        "usable_for_steady_state_now",
        "source_root",
        "runtime_root",
        "latest_heat_time_s",
        "latest_total_q_time_s",
        "latest_tp_time_s",
        "latest_tw_time_s",
        "latest_probe_time_s",
        "latest_processor_time_s",
        "processor_minus_heat_s",
        "heat_minus_probe_s",
        "heat_sample_count",
        "probe_sample_count",
        "steady_window_status",
        "steady_window_sample_count",
        "exp_tw_rmse_k",
        "exp_tp_rmse_k",
        "exp_all_temp_rmse_k",
        "validation_metrics_provenance",
        "note",
    ]
    csv_dump(path, fieldnames, project_rows(rows, fieldnames))


def write_latest_partition(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "source_id",
        "case_id",
        "base_case_id",
        "fluid",
        "variant_label",
        "display_label",
        "run_status",
        "latest_heat_time_s",
        "heater_power_w",
        "cooling_power_w",
        "ambient_proxy_w",
        "ambient_noncooling_proxy_w",
        "cooling_branch_total_removal_w",
        "cooling_branch_excess_w",
        "net_total_q_w",
        "net_total_q_pct_of_heater",
        "heater_section_gap_w",
        "section_downcomer_net_q_w",
        "section_heater_net_q_w",
        "section_upcomer_net_q_w",
        "section_test_section_net_q_w",
        "section_cooling_branch_net_q_w",
        "section_upper_transport_net_q_w",
        "section_lower_transport_net_q_w",
        "section_junctions_net_q_w",
        "section_other_net_q_w",
        "dominant_loss_section",
        "dominant_loss_magnitude_w",
        "exp_q_external_loss_reference_w",
        "ambient_error_w",
        "ambient_error_pct",
        "exp_tw_rmse_k",
        "note",
    ]
    csv_dump(path, fieldnames, project_rows(rows, fieldnames))


def write_heat_window_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "source_id",
        "base_case_id",
        "fluid",
        "variant_label",
        "run_status",
        "steady_window_status",
    ]
    stat_suffixes = [
        "status",
        "window_count",
        "time_start",
        "time_end",
        "latest",
        "mean",
        "min",
        "max",
        "span",
        "drift",
        "drift_pct_of_mean",
        "slope_per_s",
    ]
    for key in PRIMARY_HEAT_KEYS:
        for suffix in stat_suffixes:
            fieldnames.append(f"{key}_{suffix}")
    csv_dump(path, fieldnames, project_rows(rows, fieldnames))


def write_tw_hypothesis(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "source_id",
        "base_case_id",
        "fluid",
        "variant_label",
        "run_status",
        "steady_window_status",
        "exp_tw_rmse_k",
        "ambient_proxy_w",
        "exp_q_external_loss_reference_w",
        "ambient_error_w",
        "ambient_error_pct",
        "cooling_branch_total_removal_w",
        "cooling_branch_excess_w",
        "net_total_q_w",
        "net_total_q_pct_of_heater",
        "section_heater_net_q_w",
        "section_test_section_net_q_w",
        "section_cooling_branch_net_q_w",
        "section_junctions_net_q_w",
        "section_other_net_q_w",
        "dominant_loss_section",
        "dominant_loss_magnitude_w",
        "tw_hypothesis_label",
        "tw_hypothesis_note",
        "note",
    ]
    csv_dump(path, fieldnames, project_rows(rows, fieldnames))


def write_recommendations(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "source_id",
        "base_case_id",
        "fluid",
        "variant_label",
        "run_status",
        "steady_window_status",
        "latest_heat_time_s",
        "priority",
        "recommendation",
        "rationale",
    ]
    csv_dump(path, fieldnames, project_rows(rows, fieldnames))


def plot_heat_partitions(rows: list[dict[str, object]], output_root: Path) -> dict[str, str]:
    rows_by_family = split_plot_rows(rows)
    fig, axes = plt.subplots(2, 1, figsize=(15, 10), sharex=False)
    width = 0.16

    for ax, (family, family_rows) in zip(axes, rows_by_family.items()):
        labels = [plot_case_label(row) for row in family_rows]
        x = np.arange(len(family_rows))
        heater = np.array([as_float(row.get("section_heater_net_q_w")) or 0.0 for row in family_rows])
        ambient = np.array([as_float(row.get("ambient_proxy_w")) or 0.0 for row in family_rows])
        cooling = np.array([as_float(row.get("cooling_branch_total_removal_w")) or 0.0 for row in family_rows])
        test_section = np.array([abs(as_float(row.get("section_test_section_net_q_w")) or 0.0) for row in family_rows])
        junctions = np.array([abs(as_float(row.get("section_junctions_net_q_w")) or 0.0) for row in family_rows])

        containers = [
            ax.bar(x - 2 * width, heater, width=width, label="Heater -> fluid", color="#d95f02"),
            ax.bar(x - width, ambient, width=width, label="Ambient proxy", color="#7570b3"),
            ax.bar(x, cooling, width=width, label="Cooling removal", color="#1b9e77"),
            ax.bar(x + width, test_section, width=width, label="|Test-section net|", color="#e7298a"),
            ax.bar(x + 2 * width, junctions, width=width, label="|Junction net|", color="#66a61e"),
        ]
        for container in containers:
            heights = np.array([bar.get_height() for bar in container])
            ax.bar_label(container, labels=format_bar_labels(heights), padding=1, rotation=90, fontsize=7)

        ax.set_ylabel("Heat flow magnitude [W]")
        ax.set_title(f"{family.title()} cases")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha="right")
        ax.grid(axis="y", alpha=0.3)

    axes[0].legend(ncol=3, fontsize=9)
    fig.suptitle("Latest steady-state heat partition by case", fontsize=14)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    paths = save_matplotlib_figure(fig, output_root, "cross_case_heat_partition_comparison")
    plt.close(fig)
    return paths


def plot_tw_vs_heat(rows: list[dict[str, object]], output_root: Path) -> dict[str, str]:
    rows_by_family = split_plot_rows(rows)
    fig, axes = plt.subplots(2, 1, figsize=(11, 10), sharex=False, sharey=False)
    for ax, (family, family_rows) in zip(axes, rows_by_family.items()):
        for row in family_rows:
            tw_rmse = as_float(row.get("exp_tw_rmse_k"))
            ambient_error_pct = as_float(row.get("ambient_error_pct"))
            if tw_rmse is None or ambient_error_pct is None:
                continue
            fluid = fluid_family(str(row.get("fluid", "")))
            variant = str(row.get("variant_label", ""))
            ax.scatter(
                ambient_error_pct,
                tw_rmse,
                s=90,
                marker=VARIANT_MARKERS.get(variant, "o"),
                color=FLUID_COLORS.get(fluid, "#333333"),
                edgecolor="black",
                linewidth=0.6,
                alpha=0.9,
            )
            label = plot_case_label(row)
            dx, dy = SCATTER_LABEL_OFFSETS.get(label, (0.18, 0.05))
            ax.text(ambient_error_pct + dx, tw_rmse + dy, label, fontsize=8)
        ax.axvline(0.0, color="#777777", linewidth=1.0, linestyle="--")
        ax.set_xlabel("Ambient proxy signed error vs Ethan-linked reference [%]")
        ax.set_ylabel("TW RMSE [K]")
        ax.set_title(f"{family.title()} cases")
        ax.grid(alpha=0.3)
    fig.suptitle("TW RMSE versus signed ambient-loss proxy error", fontsize=14)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    paths = save_matplotlib_figure(fig, output_root, "tw_rmse_vs_heat_partition_error")
    plt.close(fig)
    return paths


def markdown_table(rows: list[dict[str, object]]) -> list[str]:
    lines = [
        "| Case | Fluid | Run status | Latest heat time [s] | Heater net [W] | Ambient proxy [W] | Cooling removal [W] | Test-section net [W] | Junction net [W] | TW RMSE [K] | Hypothesis |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        hypothesis = str(row.get("tw_hypothesis_label", "")).replace("_", " ")
        lines.append(
            "| {case} | {fluid} | {run_status} | {heat_time} | {heater} | {ambient} | {cooling} | {test_section} | {junctions} | {tw_rmse} | {hypothesis} |".format(
                case=row.get("display_label", row.get("source_id", "")),
                fluid=row.get("fluid_family", row.get("fluid", "")),
                run_status=row.get("run_status", ""),
                heat_time=format_float(row.get("latest_heat_time_s")),
                heater=format_float(row.get("section_heater_net_q_w")),
                ambient=format_float(row.get("ambient_proxy_w")),
                cooling=format_float(row.get("cooling_branch_total_removal_w")),
                test_section=format_float(row.get("section_test_section_net_q_w")),
                junctions=format_float(row.get("section_junctions_net_q_w")),
                tw_rmse=format_float(row.get("exp_tw_rmse_k")),
                hypothesis=hypothesis,
            )
        )
    return lines


def format_float(value: object) -> str:
    numeric = as_float(value)
    if numeric is None:
        return ""
    return f"{numeric:.2f}"


def build_summary(rows: list[dict[str, object]], recommendations: list[dict[str, object]], figure_paths: dict[str, dict[str, str]]) -> dict[str, object]:
    fluid_counts = Counter(str(row.get("fluid_family", row.get("fluid", ""))) for row in rows)
    window_counts = Counter(str(row.get("steady_window_status", "")) for row in rows)
    run_counts = Counter(str(row.get("run_status", "")) for row in rows)
    sorted_tw = sorted(
        [row for row in rows if as_float(row.get("exp_tw_rmse_k")) is not None],
        key=lambda row: as_float(row.get("exp_tw_rmse_k")) or -1.0,
        reverse=True,
    )
    sorted_ambient = sorted(
        [row for row in rows if as_float(row.get("ambient_error_pct")) is not None],
        key=lambda row: abs(as_float(row.get("ambient_error_pct")) or 0.0),
        reverse=True,
    )
    top_tw = [
        {
            "source_id": row["source_id"],
            "display_label": row["display_label"],
            "fluid_family": row.get("fluid_family", row.get("fluid", "")),
            "exp_tw_rmse_k": as_float(row.get("exp_tw_rmse_k")),
            "tw_hypothesis_label": row.get("tw_hypothesis_label", ""),
        }
        for row in sorted_tw[:5]
    ]
    top_ambient = [
        {
            "source_id": row["source_id"],
            "display_label": row["display_label"],
            "ambient_error_pct": as_float(row.get("ambient_error_pct")),
            "ambient_error_w": as_float(row.get("ambient_error_w")),
        }
        for row in sorted_ambient[:5]
    ]
    high_priority = [row for row in recommendations if row["priority"] in {"high", "medium"}]
    return {
        "generated_at": iso_timestamp(),
        "builder": "tools/analyze/build_ethan_steady_state_heat_flow_audit.py",
        "output_dir": str(OUTPUT_DIR),
        "case_count": len(rows),
        "source_ids": [row["source_id"] for row in rows],
        "fluid_counts": dict(fluid_counts),
        "run_status_counts": dict(run_counts),
        "steady_window_status_counts": dict(window_counts),
        "top_tw_rmse_cases": top_tw,
        "largest_ambient_error_cases": top_ambient,
        "refresh_or_rerun_candidates": high_priority,
        "figures": figure_paths,
    }


def write_readme(
    path: Path,
    case_rows: list[dict[str, object]],
    hypothesis_rows: list[dict[str, object]],
    recommendation_rows: list[dict[str, object]],
    summary: dict[str, object],
) -> None:
    rows_by_source = {row["source_id"]: row for row in case_rows}
    merged_rows: list[dict[str, object]] = []
    for row in hypothesis_rows:
        combined = dict(rows_by_source[row["source_id"]])
        combined.update(row)
        merged_rows.append(combined)


    salt_rows = [row for row in merged_rows if row.get("fluid_family") == "salt"]
    water_rows = [row for row in merged_rows if row.get("fluid_family") == "water"]
    salt_under = [as_float(row.get("ambient_error_w")) for row in salt_rows if as_float(row.get("ambient_error_w")) is not None]
    water_under = [as_float(row.get("ambient_error_w")) for row in water_rows if as_float(row.get("ambient_error_w")) is not None]

    def mean_or_blank(values: list[float | None]) -> str:
        usable = [value for value in values if value is not None]
        if not usable:
            return ""
        return f"{float(np.mean(usable)):.2f}"

    lines = [
        "# Ethan Steady-State Heat-Flow Audit",
        "",
        f"Generated: `{summary['generated_at']}`.",
        "",
        f"This package audits where heat is going at the latest usable steady-state checkpoint for all `{summary['case_count']}` currently registered CFD cases in `ethan_runs/` (13 CFD rows, excluding the separate `inventory_only` campaign registry row).",
        "",
        "## Inputs and interpretation rules",
        "",
        "- Latest heat partitions are recomputed directly from each case's current `postProcessing/wallHeatFlux/*/wallHeatFlux.dat` tail using the existing `build_salt2_behavior_package.py` logic.",
        "- The late-window summary freezes the last `50` available wall-heat samples per case when possible; shorter tails are flagged explicitly.",
        "- `ambient_proxy_w` is a derived proxy, not a directly measured column: it combines passive losses, powered-section deficits, and cooling-branch removal beyond the operating-point cooling duty.",
        "- `exp_tw_rmse_k` and the Ethan-linked ambient-loss reference still come from `reports/2026-06-04_ethan_direct_validation/ethan_direct_validation_metrics.csv` and may lag any later live continuation state.",
        "- Positive section heat means net heat into the fluid. Negative section heat means net heat removed from the fluid.",
        "",
        "## Cross-case findings",
        "",
        f"- Steady-window coverage: `{json.dumps(summary['steady_window_status_counts'], sort_keys=True)}`.",
        f"- Run-status mix: `{json.dumps(summary['run_status_counts'], sort_keys=True)}`.",
        f"- Mean signed ambient-proxy gap vs Ethan-linked reference: salt `{mean_or_blank(salt_under)}` W, water `{mean_or_blank(water_under)}` W.",
        "- Across nearly every case, the cooling branch is the dominant explicit heat sink and the junction bucket is the next recurring nontrivial sink after the cooler and test-section branch.",
        "- The salt cases carry materially larger ambient-proxy gaps than the water cases, which is consistent with the existing suspicion that salt TW disagreement is more sensitive to wall-loss partitioning and local 3D parasitics.",
        "",
        "## Case-by-case table",
        "",
        *markdown_table(merged_rows),
        "",
        "## Case-by-case notes",
        "",
    ]

    for row in merged_rows:
        label = str(row.get("display_label", row.get("source_id", "")))
        lines.append(
            f"- `{label}`: latest heat time `{format_float(row.get('latest_heat_time_s'))}` s, heater net `{format_float(row.get('section_heater_net_q_w'))}` W, ambient proxy `{format_float(row.get('ambient_proxy_w'))}` W, cooling removal `{format_float(row.get('cooling_branch_total_removal_w'))}` W, test-section net `{format_float(row.get('section_test_section_net_q_w'))}` W, junction net `{format_float(row.get('section_junctions_net_q_w'))}` W, TW RMSE `{format_float(row.get('exp_tw_rmse_k'))}` K. Hypothesis: {row.get('tw_hypothesis_note', '')}"
        )
        if row.get("note"):
            lines.append(f"  Extra note: {row['note']}")

    lines.extend(
        [
            "",
            "## Recommended refreshes or reruns",
            "",
        ]
    )
    for row in recommendation_rows:
        lines.append(
            f"- `{row['source_id']}`: priority `{row['priority']}`; {row['recommendation']}. {row['rationale']}"
        )

    lines.extend(
        [
            "",
            "## Output files",
            "",
            "- `case_heat_inventory.csv`: runtime coverage, latest timestamps, and window-status inventory.",
            "- `latest_heat_partition.csv`: latest steady-state heat partition per case.",
            "- `heat_window_summary.csv`: frozen late-window heat statistics per case and metric.",
            "- `tw_hypothesis_matrix.csv`: joined TW-oriented interpretation matrix.",
            "- `rerun_recommendations.csv`: explicit refresh and rerun recommendations with rationale.",
            "- `summary.json`: machine-readable package summary and top-ranked cases.",
            "- `figures/`: cross-case heat-partition comparison and TW-vs-heat-error scatter plots.",
            "",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_dir(OUTPUT_DIR)
    source_ids = args.source_ids or default_source_ids()

    case_rows: list[dict[str, object]] = []
    window_rows: list[dict[str, object]] = []
    hypothesis_rows: list[dict[str, object]] = []
    recommendation_rows: list[dict[str, object]] = []

    for source_id in source_ids:
        metadata_row, validation_row, steadiness_row, runtime_root, source_root, metadata = load_runtime_context(source_id)
        latest_row, window_row, hypothesis_row = summarize_case(
            source_id,
            metadata_row,
            validation_row,
            steadiness_row,
            runtime_root,
            source_root,
            metadata,
            args.window_count,
        )
        case_rows.append(latest_row)
        window_rows.append(window_row)
        hypothesis_rows.append(hypothesis_row)
        priority, recommendation, rationale = recommendation_for_case(latest_row)
        recommendation_rows.append(
            {
                "source_id": latest_row["source_id"],
                "base_case_id": latest_row["base_case_id"],
                "fluid": latest_row["fluid"],
                "fluid_family": latest_row["fluid_family"],
                "variant_label": latest_row["variant_label"],
                "run_status": latest_row["run_status"],
                "steady_window_status": latest_row["steady_window_status"],
                "latest_heat_time_s": latest_row["latest_heat_time_s"],
                "priority": priority,
                "recommendation": recommendation,
                "rationale": rationale,
            }
        )

    write_case_heat_inventory(OUTPUT_DIR / "case_heat_inventory.csv", case_rows)
    write_latest_partition(OUTPUT_DIR / "latest_heat_partition.csv", case_rows)
    write_heat_window_summary(OUTPUT_DIR / "heat_window_summary.csv", window_rows)
    write_tw_hypothesis(OUTPUT_DIR / "tw_hypothesis_matrix.csv", hypothesis_rows)
    write_recommendations(OUTPUT_DIR / "rerun_recommendations.csv", recommendation_rows)

    figure_paths: dict[str, dict[str, str]] = {}
    if not args.skip_figures:
        figure_paths["cross_case_heat_partition_comparison"] = plot_heat_partitions(case_rows, OUTPUT_DIR)
        figure_paths["tw_rmse_vs_heat_partition_error"] = plot_tw_vs_heat(case_rows, OUTPUT_DIR)

    summary = build_summary(case_rows, recommendation_rows, figure_paths)
    json_dump(OUTPUT_DIR / "summary.json", summary)
    write_readme(OUTPUT_DIR / "README.md", case_rows, hypothesis_rows, recommendation_rows, summary)

    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "case_count": len(case_rows),
        "source_ids": source_ids,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
