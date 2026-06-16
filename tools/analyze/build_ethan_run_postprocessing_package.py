#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import mean
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
    base_case_id,
    case_variant_label,
    csv_dump,
    ensure_dir,
    get_registry_row,
    iso_timestamp,
    json_dump,
    load_case_metadata,
    parse_log_summary,
    parse_probe_series,
    parse_scalar_series,
    parse_vol_field_series,
    read_registry_rows,
    safe_float,
)


METADATA_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"
VALIDATION_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_direct_validation" / "ethan_direct_validation_metrics.csv"
HEAT_AUDIT_CSV = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_steady_state_heat_flow_audit" / "case_heat_inventory.csv"
CONTRACT_CSV = (
    WORKSPACE_ROOT.parent
    / "cfd-modeling-tools"
    / "cross_model_comparison"
    / "campaigns"
    / "2026-06-02_ethan_modern_runs_first_batch_v1"
    / "data"
    / "cross_model_case_contract.csv"
)
WALL_PROBE_LOCATIONS = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "tp_tw_probe_locations.csv"

HEATER_PATCHES = {"pipeleg_lower_04_straight", "pipeleg_lower_05_straight", "pipeleg_lower_06_straight"}
TEST_SECTION_PATCHES = {"pipeleg_left_04_test_section"}
COOLING_BRANCH_PATCHES = {"pipeleg_upper_04_reducer", "pipeleg_upper_05_cooler", "pipeleg_upper_06_reducer"}

SETUP_COLUMNS = [
    "source_id",
    "case_id",
    "base_case_id",
    "variant_label",
    "fluid",
    "turbulence_model",
    "heater_power_W",
    "cooling_power_W",
    "T_init_K",
    "nprocs",
    "mesh_group_id",
    "ncc_couples",
    "three_d_outer_insulation_thickness_in",
    "three_d_loss_bc_summary",
    "three_d_radiation_summary",
    "mu_coeff_summary",
    "kappa_coeff_summary",
    "cp_model_summary",
    "rho_model_summary",
    "loss_setup_summary",
    "friction_treatment_summary",
    "assumption_note",
]

RUNTIME_COLUMNS = [
    "source_id",
    "display_label",
    "readiness_label",
    "run_status",
    "termination_reason",
    "convergence_reached",
    "convergence_iteration",
    "convergence_dTsigma",
    "final_time_metadata_s",
    "latest_heat_time_s",
    "latest_probe_time_s",
    "latest_processor_time_s",
    "heat_minus_probe_s",
    "processor_minus_heat_s",
    "essential_steadiness_class",
    "usable_for_steady_state_now",
    "comparison_ready",
    "disposition_note",
]

FIELD_ORDER = [
    "setup",
    "runtime",
    "velocity",
    "temperature",
    "pressure",
    "heat_transfer",
    "wall_quality",
    "comparison",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build one per-run Ethan postprocessing package.")
    parser.add_argument("--source-id", required=True, help="Registered Ethan source identifier.")
    parser.add_argument("--campaign-root", required=True, help="Campaign root where the run package will be written.")
    parser.add_argument(
        "--reuse-existing-renders",
        action="store_true",
        help="Record already-generated field renders in the artifact map when available.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_map(path: Path, key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in load_csv_rows(path) if row.get(key)}


def maybe_float(value: object) -> float | None:
    return safe_float(value)


def as_bool_str(value: object) -> str:
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes"}:
        return "True"
    if lowered in {"false", "0", "no"}:
        return "False"
    return str(value)


def default_source_ids() -> list[str]:
    return [
        row["source_id"]
        for row in read_registry_rows(WORKSPACE_ROOT / "registry" / "case_registry.csv")
        if row.get("status") == "registered" and row.get("source_id") != "modern_runs_campaign_inventory_2026-06-01"
    ]


def display_label_for_row(metadata_row: dict[str, str], contract_row: dict[str, str]) -> str:
    label = contract_row.get("test_id", "")
    if label:
        return f"{label} {contract_row.get('ethan_variant_label', '').strip()}".strip()
    heat_row = HEAT_AUDIT_MAP.get(metadata_row.get("source_id", ""), {})
    if heat_row.get("display_label"):
        return heat_row["display_label"]
    base_id = metadata_row.get("base_case_id") or base_case_id(metadata_row.get("case_id", ""))
    variant = metadata_row.get("variant_label") or case_variant_label(metadata_row.get("case_id", ""))
    number = base_id.split("_")[-1] if base_id else metadata_row.get("source_id", "")
    prefix = "S" if "salt" in metadata_row.get("fluid", "").lower() else "W"
    pieces = [f"{prefix}{number}"]
    if variant:
        pieces.append(variant)
    if metadata_row.get("source_id") == "val_salt_test_2_coarse_mesh_laminar":
        pieces.append("val")
    return " ".join(pieces)


def readiness_label(metadata_row: dict[str, str], heat_row: dict[str, str]) -> str:
    ready = metadata_row.get("comparison_ready", "")
    run_status = metadata_row.get("run_status", "")
    convergence = str(metadata_row.get("convergence_reached", "")).lower() == "true"
    if ready:
        return ready
    if run_status == "completed" and convergence:
        return "comparison_candidate"
    if heat_row.get("usable_for_steady_state_now", "").lower() == "yes":
        return "review_required"
    if run_status == "terminated":
        return "continuation_affected"
    return "diagnostic_only"


def section_bucket(patch: str) -> str:
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
        if not q_match:
            continue
        value = maybe_float(q_match.group(1))
        if value is not None:
            imposed[patch] = value
    return imposed


def parse_wall_heatflux_section_rows(runtime_root: Path, source_root: Path, metadata: dict[str, Any]) -> list[dict[str, float]]:
    candidates = sorted(runtime_root.glob("postProcessing/wallHeatFlux/*/wallHeatFlux.dat"), key=lambda item: item.parent.name)
    if not candidates:
        return []
    rows_by_time: dict[float, dict[str, float]] = {}
    with candidates[-1].open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 5:
                continue
            time_value = maybe_float(parts[0])
            q_value = maybe_float(parts[4])
            if time_value is None or q_value is None:
                continue
            rows_by_time.setdefault(float(time_value), {})[parts[1]] = float(q_value)

    imposed_q = parse_patch_imposed_q(source_root)
    operating_cooling = maybe_float(metadata.get("operating_point", {}).get("cooling_power_W")) or 0.0
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
        powered_ambient = 0.0
        cooling_total = 0.0
        for patch, q_value in patch_map.items():
            if patch.startswith("ncc_"):
                continue
            sections[section_bucket(patch)] += q_value
            if patch in COOLING_BRANCH_PATCHES and q_value < 0.0:
                cooling_total += abs(q_value)
                continue
            imposed = imposed_q.get(patch)
            if imposed is not None and imposed > 0.0:
                powered_ambient += max(imposed - q_value, 0.0)
            elif q_value < 0.0:
                passive_ambient += abs(q_value)
        cooling_excess = max(cooling_total - operating_cooling, 0.0)
        section_rows.append(
            {
                "time_s": time_value,
                "ambient_proxy_w": passive_ambient + powered_ambient + cooling_excess,
                "ambient_noncooling_proxy_w": passive_ambient + powered_ambient,
                "cooling_branch_total_removal_w": cooling_total,
                "cooling_branch_excess_w": cooling_excess,
                "net_total_q_w": sum(value for patch, value in patch_map.items() if not patch.startswith("ncc_")),
                **{f"section_{name}_net_q_w": value for name, value in sections.items()},
            }
        )
    return section_rows


def parse_yplus_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 5:
                continue
            time_value = maybe_float(parts[0])
            min_value = maybe_float(parts[2])
            max_value = maybe_float(parts[3])
            avg_value = maybe_float(parts[4])
            if time_value is None or min_value is None or max_value is None or avg_value is None:
                continue
            rows.append(
                {
                    "time_s": float(time_value),
                    "patch": parts[1],
                    "min_yplus": float(min_value),
                    "max_yplus": float(max_value),
                    "avg_yplus": float(avg_value),
                }
            )
    return rows


VECTOR_PATTERN = re.compile(
    r"^\s*([^\s]+)\s+([^\s]+)\s+\(([^)]+)\)\s+\(([^)]+)\)\s*$"
)


def vector_magnitude(parts: str) -> float:
    values = [maybe_float(item) or 0.0 for item in parts.split()]
    return math.sqrt(sum(value * value for value in values))


def parse_wall_shear_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = VECTOR_PATTERN.match(stripped)
            if not match:
                continue
            time_value = maybe_float(match.group(1))
            if time_value is None:
                continue
            min_mag = vector_magnitude(match.group(3))
            max_mag = vector_magnitude(match.group(4))
            rows.append(
                {
                    "time_s": float(time_value),
                    "patch": match.group(2),
                    "min_tau_mag": min_mag,
                    "max_tau_mag": max_mag,
                }
            )
    return rows


def latest_numeric_dir(root: Path) -> Path | None:
    if not root.exists():
        return None
    candidates = [path for path in root.iterdir() if path.is_dir() and path.name.replace(".", "", 1).isdigit()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: float(path.name))


def parse_velocity_profile_file(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 4:
                continue
            distance = maybe_float(parts[0])
            ux = maybe_float(parts[1])
            uy = maybe_float(parts[2])
            uz = maybe_float(parts[3])
            if None in (distance, ux, uy, uz):
                continue
            rows.append(
                {
                    "distance_m": float(distance),
                    "U_x_m_s": float(ux),
                    "U_y_m_s": float(uy),
                    "U_z_m_s": float(uz),
                }
            )
    return rows


def wall_probe_order() -> list[str]:
    labels: list[str] = []
    if not WALL_PROBE_LOCATIONS.exists():
        return labels
    with WALL_PROBE_LOCATIONS.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("group") == "TW":
                labels.append(row["label"])
    return labels


def tp_timeseries_rows(path: Path) -> list[dict[str, Any]]:
    payload = parse_probe_series(path)
    rows: list[dict[str, Any]] = []
    for row in payload["rows"]:
        output: dict[str, Any] = {"time_s": float(row["time"])}
        values = [float(value) for value in row["values"]]
        for index, value in enumerate(values):
            output[f"TP{index + 1}_K"] = value
        if values:
            output["TP_avg_K"] = mean(values)
            output["TP_min_K"] = min(values)
            output["TP_max_K"] = max(values)
        rows.append(output)
    return rows


def tw_timeseries_rows(path: Path, probe_labels: list[str]) -> list[dict[str, Any]]:
    payload = parse_probe_series(path)
    rows: list[dict[str, Any]] = []
    for row in payload["rows"]:
        station_values: dict[str, list[float]] = {}
        for index, value in enumerate(row["values"]):
            label = probe_labels[index] if index < len(probe_labels) else f"TW_unknown_{index}"
            station = label.split("_", 1)[0]
            station_values.setdefault(station, []).append(float(value))
        output: dict[str, Any] = {"time_s": float(row["time"])}
        for station, values in sorted(station_values.items()):
            output[f"{station}_K"] = mean(values)
        rows.append(output)
    return rows


def join_time_series(series_list: list[tuple[str, list[dict[str, float]]]]) -> list[dict[str, Any]]:
    time_map: dict[float, dict[str, Any]] = {}
    for series_name, rows in series_list:
        for row in rows:
            time_value = float(row["time"])
            target = time_map.setdefault(time_value, {"time_s": time_value})
            target[series_name] = row["value"]
    merged = [time_map[key] for key in sorted(time_map)]
    for row in merged:
        numeric_values = [value for key, value in row.items() if key != "time_s" and isinstance(value, (int, float))]
        if numeric_values:
            row["mdot_mean_abs_kg_s"] = mean(abs(float(value)) for value in numeric_values)
    return merged


def ensure_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> str:
    if fieldnames is None:
        discovered: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in discovered:
                    discovered.append(key)
        fieldnames = discovered
    csv_dump(path, fieldnames, rows)
    return str(path.resolve())


def plot_line_figure(
    rows: list[dict[str, Any]],
    x_key: str,
    series_specs: list[dict[str, str]],
    title: str,
    xlabel: str,
    ylabel: str,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.6, 4.8), constrained_layout=True)
    for spec in series_specs:
        xs = [float(row[x_key]) for row in rows if row.get(spec["y"]) not in ("", None)]
        ys = [float(row[spec["y"]]) for row in rows if row.get(spec["y"]) not in ("", None)]
        if not xs:
            continue
        ax.plot(xs, ys, label=spec["label"], linewidth=1.8)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    if any(spec["label"] for spec in series_specs):
        ax.legend(loc="best", fontsize=8)
    return fig


def plot_ranked_figure(
    rows: list[dict[str, Any]],
    x_key: str,
    y_key: str,
    title: str,
    xlabel: str,
    ylabel: str,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.6, 4.8), constrained_layout=True)
    xs = [int(row[x_key]) for row in rows]
    ys = [float(row[y_key]) for row in rows]
    ax.plot(xs, ys, marker="o", linewidth=1.4)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    return fig


def write_pgfplots_line_wrapper(
    path: Path,
    csv_relative_path: str,
    x_key: str,
    series_specs: list[dict[str, str]],
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    lines = [
        "\\begin{tikzpicture}",
        f"\\begin{{axis}}[title={{{title}}}, xlabel={{{xlabel}}}, ylabel={{{ylabel}}}, width=12cm, height=7cm, grid=both, legend style={{font=\\small}}]",
    ]
    for spec in series_specs:
        lines.append(f"\\addplot table [col sep=comma, x={x_key}, y={spec['y']}] {{{csv_relative_path}}};")
        lines.append(f"\\addlegendentry{{{spec['label']}}}")
    lines.extend(["\\end{axis}", "\\end{tikzpicture}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def save_figure_bundle(
    fig: plt.Figure,
    run_root: Path,
    field: str,
    stem: str,
    csv_path: Path,
    x_key: str,
    series_specs: list[dict[str, str]],
    title: str,
    xlabel: str,
    ylabel: str,
) -> dict[str, str]:
    svg_path = ensure_dir(run_root / "figures" / field / "svg") / f"{stem}.svg"
    pdf_path = ensure_dir(run_root / "figures" / field / "pdf") / f"{stem}.pdf"
    tikz_path = ensure_dir(run_root / "figures" / field / "tikz") / f"{stem}.tex"
    fig.savefig(svg_path)
    fig.savefig(pdf_path)
    write_pgfplots_line_wrapper(
        tikz_path,
        os.path.relpath(csv_path, tikz_path.parent),
        x_key,
        series_specs,
        title,
        xlabel,
        ylabel,
    )
    plt.close(fig)
    return {
        "svg": str(svg_path.resolve()),
        "pdf": str(pdf_path.resolve()),
        "tikz": str(tikz_path.resolve()),
    }


def series_latest(rows: list[dict[str, Any]], key: str) -> float | None:
    for row in reversed(rows):
        value = maybe_float(row.get(key))
        if value is not None:
            return float(value)
    return None


def stats_text(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} mean; {min(values):.4f} min; {max(values):.4f} max"


def write_markdown(path: Path, text: str) -> str:
    ensure_dir(path.parent)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return str(path.resolve())


def build_run_package(source_id: str, campaign_root: Path, reuse_existing_renders: bool = False) -> dict[str, Any]:
    registry_row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)
    metadata_row = METADATA_MAP.get(source_id, {})
    validation_row = VALIDATION_MAP.get(source_id, {})
    heat_row = HEAT_AUDIT_MAP.get(source_id, {})
    contract_row = CONTRACT_MAP.get(source_id, {})

    source_root = Path(registry_row["source_root"]).resolve()
    runtime_root = Path(metadata_row.get("active_runtime_root") or source_root).resolve()
    metadata = load_case_metadata(runtime_root) or load_case_metadata(source_root) or {}
    log_summary = parse_log_summary(runtime_root / "logs" / "log.foamRun")
    probe_labels = wall_probe_order()

    display_label = display_label_for_row(metadata_row, contract_row)
    readiness = readiness_label(metadata_row, heat_row)

    run_root = ensure_dir(campaign_root / "runs" / source_id)
    manifests_root = ensure_dir(run_root / "manifests")
    reports_root = ensure_dir(run_root / "reports")

    source_paths = {
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "case_config": str((runtime_root / "case_config.yaml").resolve() if (runtime_root / "case_config.yaml").exists() else (source_root / "case_config.yaml").resolve()),
        "control_dict": str((runtime_root / "system" / "controlDict").resolve()),
        "functions": str((runtime_root / "system" / "functions").resolve()),
        "solver_log": str((runtime_root / "logs" / "log.foamRun").resolve()),
        "tp_probes": str((runtime_root / "postProcessing" / "temperature_probes" / "0" / "T").resolve()),
        "tw_probes": str((runtime_root / "postProcessing" / "wall_temperature_probes" / "0" / "T").resolve()),
        "piv_slab": str((runtime_root / "postProcessing" / "piv_slab_velocity" / "0" / "volFieldValue.dat").resolve()),
        "total_q": str((runtime_root / "postProcessing" / "total_Q.dat").resolve()),
    }

    tables: dict[str, list[str]] = {field: [] for field in FIELD_ORDER}
    figures: dict[str, list[dict[str, Any]]] = {field: [] for field in FIELD_ORDER}
    missing_artifacts: list[dict[str, str]] = []
    reused_existing_artifacts: list[str] = []

    if reuse_existing_renders:
        render_status = WORKSPACE_ROOT / "figures_rendered" / source_id / "status.json"
        if render_status.exists():
            reused_existing_artifacts.append(str(render_status.resolve()))

    setup_row = {key: metadata_row.get(key, "") for key in SETUP_COLUMNS}
    setup_row.update({"display_label": display_label, "readiness_label": readiness})
    setup_csv = run_root / "tables" / "setup" / "setup_summary.csv"
    tables["setup"].append(ensure_csv(setup_csv, [setup_row]))

    runtime_row = {
        "source_id": source_id,
        "display_label": display_label,
        "readiness_label": readiness,
        "run_status": metadata_row.get("run_status") or log_summary.get("status", ""),
        "termination_reason": metadata_row.get("run_termination_reason") or log_summary.get("termination_reason", ""),
        "convergence_reached": as_bool_str(metadata_row.get("convergence_reached", log_summary.get("convergence", {}).get("reached", ""))),
        "convergence_iteration": metadata_row.get("convergence_iteration") or log_summary.get("convergence", {}).get("iteration", ""),
        "convergence_dTsigma": metadata_row.get("convergence_dTsigma") or log_summary.get("convergence", {}).get("dTsigma", ""),
        "final_time_metadata_s": metadata_row.get("final_time", ""),
        "latest_heat_time_s": heat_row.get("latest_heat_time_s", ""),
        "latest_probe_time_s": heat_row.get("latest_probe_time_s", ""),
        "latest_processor_time_s": heat_row.get("latest_processor_time_s", metadata_row.get("latest_processor_time", "")),
        "heat_minus_probe_s": heat_row.get("heat_minus_probe_s", ""),
        "processor_minus_heat_s": heat_row.get("processor_minus_heat_s", ""),
        "essential_steadiness_class": heat_row.get("essential_steadiness_class", ""),
        "usable_for_steady_state_now": heat_row.get("usable_for_steady_state_now", ""),
        "comparison_ready": metadata_row.get("comparison_ready", ""),
        "disposition_note": metadata_row.get("disposition_note", ""),
    }
    runtime_csv = run_root / "tables" / "runtime" / "runtime_summary.csv"
    tables["runtime"].append(ensure_csv(runtime_csv, [runtime_row], RUNTIME_COLUMNS))

    mdot_series_list: list[tuple[str, list[dict[str, float]]]] = []
    for path in sorted((runtime_root / "postProcessing").glob("mdot_*/0/surfaceFieldValue.dat")):
        mdot_series_list.append((path.parent.parent.name, parse_scalar_series(path)))
    mdot_rows = join_time_series(mdot_series_list)
    mdot_csv = run_root / "tables" / "velocity" / "mdot_monitor_timeseries.csv"
    if mdot_rows:
        tables["velocity"].append(ensure_csv(mdot_csv, mdot_rows))
        mdot_specs = [
            {"y": key, "label": key.replace("mdot_", "").replace("_", " ")}
            for key in mdot_rows[0].keys()
            if key not in {"time_s", "mdot_mean_abs_kg_s"}
        ]
        mdot_specs.append({"y": "mdot_mean_abs_kg_s", "label": "mean abs"})
        fig = plot_line_figure(
            mdot_rows,
            "time_s",
            mdot_specs,
            f"{display_label} mass-flow monitor histories",
            "Time [s]",
            "Mass flow [kg/s]",
        )
        paths = save_figure_bundle(
            fig,
            run_root,
            "velocity",
            "mass_flow_monitor_histories",
            mdot_csv,
            "time_s",
            mdot_specs,
            f"{display_label} mass-flow monitor histories",
            "Time [s]",
            "Mass flow [kg/s]",
        )
        figures["velocity"].append(
            {
                "figure_id": "velocity_mass_flow_monitor_histories",
                "field": "velocity",
                "table_csv": str(mdot_csv.resolve()),
                "caption": "Native mass-flow monitor histories from the four labeled mdot sections plus their mean absolute envelope.",
                **paths,
            }
        )
    else:
        missing_artifacts.append({"field": "velocity", "artifact": "mass flow histories", "reason": "No mdot monitor files were found."})

    piv_rows = parse_vol_field_series(runtime_root / "postProcessing" / "piv_slab_velocity" / "0" / "volFieldValue.dat")
    piv_csv = run_root / "tables" / "velocity" / "piv_slab_timeseries.csv"
    if piv_rows:
        tables["velocity"].append(ensure_csv(piv_csv, piv_rows))
        piv_specs = [{"y": "magU", "label": "PIV slab |U|"}]
        fig = plot_line_figure(
            piv_rows,
            "time",
            piv_specs,
            f"{display_label} PIV slab speed history",
            "Time [s]",
            "Speed [m/s]",
        )
        paths = save_figure_bundle(
            fig,
            run_root,
            "velocity",
            "piv_slab_speed_history",
            piv_csv,
            "time",
            piv_specs,
            f"{display_label} PIV slab speed history",
            "Time [s]",
            "Speed [m/s]",
        )
        figures["velocity"].append(
            {
                "figure_id": "velocity_piv_slab_speed_history",
                "field": "velocity",
                "table_csv": str(piv_csv.resolve()),
                "caption": "Area/volume monitor history for the labeled PIV slab speed magnitude.",
                **paths,
            }
        )
    else:
        missing_artifacts.append({"field": "velocity", "artifact": "PIV slab monitor", "reason": "No `piv_slab_velocity` data were found."})

    latest_profile_dir = latest_numeric_dir(runtime_root / "postProcessing" / "velocity_profiles")
    velocity_profile_rows: list[dict[str, Any]] = []
    if latest_profile_dir is not None:
        for suffix in ("X", "Z"):
            long_rows: list[dict[str, Any]] = []
            specs: list[dict[str, str]] = []
            for level in ("0.25", "0.50", "0.75"):
                file_name = f"Y_H_{level}_{suffix}.xy"
                rows = parse_velocity_profile_file(latest_profile_dir / file_name)
                if not rows:
                    continue
                series_key = f"Uy_H_{level}_{suffix}_m_s"
                specs.append({"y": series_key, "label": f"H={level} {suffix}"})
                for row in rows:
                    long_rows.append(
                        {
                            "distance_m": row["distance_m"],
                            series_key: row["U_y_m_s"],
                            "source_profile": file_name,
                        }
                    )
                    velocity_profile_rows.append(
                        {
                            "time_dir": latest_profile_dir.name,
                            "profile_file": file_name,
                            "distance_m": row["distance_m"],
                            "U_x_m_s": row["U_x_m_s"],
                            "U_y_m_s": row["U_y_m_s"],
                            "U_z_m_s": row["U_z_m_s"],
                        }
                    )
            if long_rows:
                consolidated: dict[float, dict[str, Any]] = {}
                for row in long_rows:
                    target = consolidated.setdefault(row["distance_m"], {"distance_m": row["distance_m"]})
                    for key, value in row.items():
                        if key not in {"distance_m", "source_profile"}:
                            target[key] = value
                ordered = [consolidated[key] for key in sorted(consolidated)]
                csv_path = run_root / "tables" / "velocity" / f"latest_velocity_profiles_{suffix.lower()}.csv"
                tables["velocity"].append(ensure_csv(csv_path, ordered))
                fig = plot_line_figure(
                    ordered,
                    "distance_m",
                    specs,
                    f"{display_label} latest velocity profiles ({suffix}-cuts)",
                    "Distance [m]",
                    "U_y [m/s]",
                )
                paths = save_figure_bundle(
                    fig,
                    run_root,
                    "velocity",
                    f"latest_velocity_profiles_{suffix.lower()}",
                    csv_path,
                    "distance_m",
                    specs,
                    f"{display_label} latest velocity profiles ({suffix}-cuts)",
                    "Distance [m]",
                    "U_y [m/s]",
                )
                figures["velocity"].append(
                    {
                        "figure_id": f"velocity_latest_velocity_profiles_{suffix.lower()}",
                        "field": "velocity",
                        "table_csv": str(csv_path.resolve()),
                        "caption": f"Latest labeled velocity-profile cuts from `velocity_profiles/{latest_profile_dir.name}` for the {suffix}-oriented exports.",
                        **paths,
                    }
                )
        if velocity_profile_rows:
            profile_summary_csv = run_root / "tables" / "velocity" / "velocity_profile_snapshot_long.csv"
            tables["velocity"].append(ensure_csv(profile_summary_csv, velocity_profile_rows))
    else:
        missing_artifacts.append({"field": "velocity", "artifact": "velocity profile snapshot", "reason": "No numeric `velocity_profiles` directory was found."})

    tp_rows = tp_timeseries_rows(runtime_root / "postProcessing" / "temperature_probes" / "0" / "T")
    tp_csv = run_root / "tables" / "temperature" / "tp_probe_timeseries.csv"
    if tp_rows:
        tables["temperature"].append(ensure_csv(tp_csv, tp_rows))
        tp_specs = []
        for key in ("TP1_K", "TP4_K", "TP6_K", "TP_avg_K"):
            if key in tp_rows[0]:
                tp_specs.append({"y": key, "label": key.replace("_K", "").replace("_", " ")})
        fig = plot_line_figure(
            tp_rows,
            "time_s",
            tp_specs,
            f"{display_label} bulk probe temperatures",
            "Time [s]",
            "Temperature [K]",
        )
        paths = save_figure_bundle(
            fig,
            run_root,
            "temperature",
            "tp_probe_temperatures",
            tp_csv,
            "time_s",
            tp_specs,
            f"{display_label} bulk probe temperatures",
            "Time [s]",
            "Temperature [K]",
        )
        figures["temperature"].append(
            {
                "figure_id": "temperature_tp_probe_temperatures",
                "field": "temperature",
                "table_csv": str(tp_csv.resolve()),
                "caption": "Selected bulk-fluid probe histories from the labeled TP monitor set, plus the across-probe average.",
                **paths,
            }
        )
    else:
        missing_artifacts.append({"field": "temperature", "artifact": "TP probe histories", "reason": "No `temperature_probes` data were found."})

    tw_rows = tw_timeseries_rows(runtime_root / "postProcessing" / "wall_temperature_probes" / "0" / "T", probe_labels)
    tw_csv = run_root / "tables" / "temperature" / "tw_station_timeseries.csv"
    if tw_rows:
        tables["temperature"].append(ensure_csv(tw_csv, tw_rows))
        available_tw_keys = [key for key in tw_rows[0].keys() if key.startswith("TW")]
        preferred = [key for key in ("TW5_K", "TW9_K") if key in available_tw_keys]
        if len(preferred) < 2:
            preferred = available_tw_keys[: min(3, len(available_tw_keys))]
        tw_specs = [{"y": key, "label": key.replace("_K", "")} for key in preferred]
        fig = plot_line_figure(
            tw_rows,
            "time_s",
            tw_specs,
            f"{display_label} wall temperature stations",
            "Time [s]",
            "Temperature [K]",
        )
        paths = save_figure_bundle(
            fig,
            run_root,
            "temperature",
            "tw_station_temperatures",
            tw_csv,
            "time_s",
            tw_specs,
            f"{display_label} wall temperature stations",
            "Time [s]",
            "Temperature [K]",
        )
        figures["temperature"].append(
            {
                "figure_id": "temperature_tw_station_temperatures",
                "field": "temperature",
                "table_csv": str(tw_csv.resolve()),
                "caption": "Selected wall-station histories from the labeled TW monitor set.",
                **paths,
            }
        )
    else:
        missing_artifacts.append({"field": "temperature", "artifact": "TW probe histories", "reason": "No `wall_temperature_probes` data were found."})

    total_q_rows = parse_scalar_series(runtime_root / "postProcessing" / "total_Q.dat")
    total_q_csv = run_root / "tables" / "heat_transfer" / "total_q_timeseries.csv"
    if total_q_rows:
        tables["heat_transfer"].append(ensure_csv(total_q_csv, [{"time_s": row["time"], "total_q_w": row["value"]} for row in total_q_rows]))
    section_rows = parse_wall_heatflux_section_rows(runtime_root, source_root, metadata)
    section_csv = run_root / "tables" / "heat_transfer" / "section_heat_timeseries.csv"
    if section_rows:
        tables["heat_transfer"].append(ensure_csv(section_csv, section_rows))
        heat_specs = [
            {"y": "net_total_q_w", "label": "net total"},
            {"y": "ambient_proxy_w", "label": "ambient proxy"},
            {"y": "cooling_branch_total_removal_w", "label": "cooling removal"},
        ]
        fig = plot_line_figure(
            section_rows,
            "time_s",
            heat_specs,
            f"{display_label} total heat and ambient proxy",
            "Time [s]",
            "Heat [W]",
        )
        paths = save_figure_bundle(
            fig,
            run_root,
            "heat_transfer",
            "total_heat_histories",
            section_csv,
            "time_s",
            heat_specs,
            f"{display_label} total heat and ambient proxy",
            "Time [s]",
            "Heat [W]",
        )
        figures["heat_transfer"].append(
            {
                "figure_id": "heat_transfer_total_heat_histories",
                "field": "heat_transfer",
                "table_csv": str(section_csv.resolve()),
                "caption": "Total wall heat, reconstructed ambient-loss proxy, and cooling removal from the existing wallHeatFlux reductions.",
                **paths,
            }
        )
        section_specs = [
            {"y": "section_heater_net_q_w", "label": "heater"},
            {"y": "section_test_section_net_q_w", "label": "test section"},
            {"y": "section_cooling_branch_net_q_w", "label": "cooling branch"},
            {"y": "section_junctions_net_q_w", "label": "junctions"},
        ]
        fig = plot_line_figure(
            section_rows,
            "time_s",
            section_specs,
            f"{display_label} section heat histories",
            "Time [s]",
            "Heat [W]",
        )
        paths = save_figure_bundle(
            fig,
            run_root,
            "heat_transfer",
            "section_heat_histories",
            section_csv,
            "time_s",
            section_specs,
            f"{display_label} section heat histories",
            "Time [s]",
            "Heat [W]",
        )
        figures["heat_transfer"].append(
            {
                "figure_id": "heat_transfer_section_heat_histories",
                "field": "heat_transfer",
                "table_csv": str(section_csv.resolve()),
                "caption": "Selected section-wise net heat histories derived from `wallHeatFlux.dat`.",
                **paths,
            }
        )
    else:
        missing_artifacts.append({"field": "heat_transfer", "artifact": "wall heat section histories", "reason": "No `wallHeatFlux` reductions were found."})
    if not total_q_rows:
        missing_artifacts.append({"field": "heat_transfer", "artifact": "total_Q history", "reason": "No `total_Q.dat` file was found."})

    yplus_dir = latest_numeric_dir(runtime_root / "postProcessing" / "yPlus")
    if yplus_dir is not None:
        yplus_rows = [row for row in parse_yplus_rows(yplus_dir / "yPlus.dat") if not row["patch"].startswith("ncc_")]
        ranked = sorted(yplus_rows, key=lambda row: row["avg_yplus"], reverse=True)[:12]
        for index, row in enumerate(ranked, start=1):
            row["rank"] = index
        yplus_csv = run_root / "tables" / "wall_quality" / "yplus_patch_summary.csv"
        tables["wall_quality"].append(ensure_csv(yplus_csv, ranked))
        fig = plot_ranked_figure(
            ranked,
            "rank",
            "avg_yplus",
            f"{display_label} top yPlus patches",
            "Patch rank",
            "Average yPlus",
        )
        paths = save_figure_bundle(
            fig,
            run_root,
            "wall_quality",
            "top_yplus_patches",
            yplus_csv,
            "rank",
            [{"y": "avg_yplus", "label": "avg yPlus"}],
            f"{display_label} top yPlus patches",
            "Patch rank",
            "Average yPlus",
        )
        figures["wall_quality"].append(
            {
                "figure_id": "wall_quality_top_yplus_patches",
                "field": "wall_quality",
                "table_csv": str(yplus_csv.resolve()),
                "caption": "Highest-average non-NCC yPlus patches from the latest available yPlus reduction.",
                **paths,
            }
        )
    else:
        missing_artifacts.append({"field": "wall_quality", "artifact": "yPlus summary", "reason": "No numeric `yPlus` directory was found."})

    wall_shear_rows = [row for row in parse_wall_shear_rows(runtime_root / "postProcessing" / "wallShearStress" / "0" / "wallShearStress.dat") if not row["patch"].startswith("ncc_")]
    if wall_shear_rows:
        ranked_shear = sorted(wall_shear_rows, key=lambda row: row["max_tau_mag"], reverse=True)[:12]
        for index, row in enumerate(ranked_shear, start=1):
            row["rank"] = index
        shear_csv = run_root / "tables" / "wall_quality" / "wall_shear_patch_summary.csv"
        tables["wall_quality"].append(ensure_csv(shear_csv, ranked_shear))
        fig = plot_ranked_figure(
            ranked_shear,
            "rank",
            "max_tau_mag",
            f"{display_label} top wall-shear patches",
            "Patch rank",
            "|tau| max [Pa-equivalent units]",
        )
        paths = save_figure_bundle(
            fig,
            run_root,
            "wall_quality",
            "top_wall_shear_patches",
            shear_csv,
            "rank",
            [{"y": "max_tau_mag", "label": "max |tau|"}],
            f"{display_label} top wall-shear patches",
            "Patch rank",
            "|tau| max [Pa-equivalent units]",
        )
        figures["wall_quality"].append(
            {
                "figure_id": "wall_quality_top_wall_shear_patches",
                "field": "wall_quality",
                "table_csv": str(shear_csv.resolve()),
                "caption": "Highest non-NCC wall-shear patch maxima from the existing `wallShearStress.dat` reduction.",
                **paths,
            }
        )
    else:
        missing_artifacts.append({"field": "wall_quality", "artifact": "wall shear summary", "reason": "No `wallShearStress.dat` file was found."})

    pressure_note = (
        "The baseline per-run monitor package starts from the easy labeled native `postProcessing` outputs. "
        "No direct pressure monitor family is published there for this run, so pressure is recorded as unavailable "
        "from the baseline native monitor set. Existing richer pressure interpretations remain in earlier derived report packages."
    )
    pressure_csv = run_root / "tables" / "pressure" / "pressure_availability.csv"
    tables["pressure"].append(
        ensure_csv(
            pressure_csv,
            [
                {
                    "source_id": source_id,
                    "native_pressure_monitor_available": "False",
                    "baseline_status": "not_available_from_native_labeled_postprocessing",
                    "note": pressure_note,
                }
            ],
        )
    )
    missing_artifacts.append({"field": "pressure", "artifact": "pressure figures", "reason": pressure_note})

    comparison_csv = run_root / "tables" / "comparison" / "validation_summary.csv"
    comparison_row = {
        "source_id": source_id,
        "display_label": display_label,
        "exp_case_name": validation_row.get("exp_case_name", metadata_row.get("exp_case_name", "")),
        "exp_reference_status": validation_row.get("exp_reference_status", metadata_row.get("exp_reference_status", "")),
        "exp_tp_rmse_k": validation_row.get("exp_tp_rmse_k", metadata_row.get("exp_tp_rmse_k", "")),
        "exp_tw_rmse_k": validation_row.get("exp_tw_rmse_k", metadata_row.get("exp_tw_rmse_k", "")),
        "exp_all_temp_rmse_k": validation_row.get("exp_all_temp_rmse_k", metadata_row.get("exp_all_temp_rmse_k", "")),
        "exp_mdot_abs_error_pct": validation_row.get("exp_mdot_abs_error_pct", metadata_row.get("exp_mdot_abs_error_pct", "")),
        "exp_q_external_loss_abs_error_pct": validation_row.get(
            "exp_q_external_loss_abs_error_pct",
            metadata_row.get("exp_q_external_loss_abs_error_pct", ""),
        ),
        "comparison_ready": metadata_row.get("comparison_ready", ""),
        "disposition_note": metadata_row.get("disposition_note", ""),
    }
    tables["comparison"].append(ensure_csv(comparison_csv, [comparison_row]))

    mdot_latest = series_latest(mdot_rows, "mdot_mean_abs_kg_s")
    probe_latest = series_latest(tp_rows, "TP_avg_K")
    tw_latest_values = [
        float(value)
        for key, value in (tw_rows[-1].items() if tw_rows else [])
        if key.startswith("TW") and maybe_float(value) is not None
    ]
    ambient_latest = series_latest(section_rows, "ambient_proxy_w")
    yplus_values = [float(row["avg_yplus"]) for row in parse_yplus_rows(yplus_dir / "yPlus.dat")] if yplus_dir is not None else []

    executive_summary_path = reports_root / "executive_summary.md"
    technical_analysis_path = reports_root / "technical_analysis.md"
    artifact_map_path = reports_root / "artifact_map.md"
    run_summary_path = manifests_root / "run_summary.json"
    artifact_map_json_path = manifests_root / "artifact_map.json"

    executive_summary = f"""
# {display_label} executive summary

- Source id: `{source_id}`
- Readiness label: `{readiness}`
- Runtime status: `{runtime_row['run_status']}`
- Convergence reached: `{runtime_row['convergence_reached']}`
- Final metadata time: `{runtime_row['final_time_metadata_s']}`

Key observed metrics:

- Mean absolute monitored mass flow: `{mdot_latest if mdot_latest is not None else 'n/a'}` kg/s
- Final average fluid probe temperature: `{probe_latest if probe_latest is not None else 'n/a'}` K
- Final ambient-loss proxy from wall heat reductions: `{ambient_latest if ambient_latest is not None else 'n/a'}` W
- Direct-validation TP RMSE: `{comparison_row['exp_tp_rmse_k'] or 'n/a'}` K
- Direct-validation TW RMSE: `{comparison_row['exp_tw_rmse_k'] or 'n/a'}` K

Headline interpretation:

- Setup and BC/model context were auto-derived from `{source_paths['case_config']}` plus the June 4 metadata index.
- The baseline analysis uses the native labeled `postProcessing` outputs first: mass-flow monitors, TP/TW probes, `total_Q.dat`, `piv_slab_velocity`, `wallHeatFlux`, `yPlus`, `wallShearStress`, and `velocity_profiles` when present.
- Pressure is intentionally marked unavailable from the baseline native monitor set for this v1 package.
"""
    write_markdown(executive_summary_path, executive_summary)

    technical_analysis = f"""
# {display_label} technical analysis

## Setup and solver context

- Source root: `{source_root}`
- Active runtime root: `{runtime_root}`
- Fluid / model: `{setup_row.get('fluid', '')}` / `{setup_row.get('turbulence_model', '')}`
- Heater / cooler operating point: `{setup_row.get('heater_power_W', '')}` W heater, `{setup_row.get('cooling_power_W', '')}` W cooler target
- Initial fluid temperature: `{setup_row.get('T_init_K', '')}` K
- NCC couples: `{setup_row.get('ncc_couples', '')}`
- Transport/property summary:
  - viscosity: `{setup_row.get('mu_coeff_summary', '')}`
  - conductivity: `{setup_row.get('kappa_coeff_summary', '')}`
  - Cp: `{setup_row.get('cp_model_summary', '')}`
  - density: `{setup_row.get('rho_model_summary', '')}`
- Loss BC summary: `{setup_row.get('three_d_loss_bc_summary', '')}`
- Radiation summary: `{setup_row.get('three_d_radiation_summary', '')}`

Primary setup table: `{setup_csv.resolve()}`

## Runtime and maturity

- Run status: `{runtime_row['run_status']}`
- Termination reason: `{runtime_row['termination_reason']}`
- Convergence reached: `{runtime_row['convergence_reached']}`
- Comparison readiness: `{runtime_row['comparison_ready']}`
- Essential steadiness class: `{runtime_row['essential_steadiness_class']}`
- Latest heat time / probe time / processor time: `{runtime_row['latest_heat_time_s']}` / `{runtime_row['latest_probe_time_s']}` / `{runtime_row['latest_processor_time_s']}`
- Heat minus probe lag: `{runtime_row['heat_minus_probe_s']}` s

Runtime table: `{runtime_csv.resolve()}`

## Velocity

- Mean monitored mass-flow latest value: `{mdot_latest if mdot_latest is not None else 'n/a'}` kg/s
- PIV slab latest speed: `{series_latest(piv_rows, 'magU') if piv_rows else 'n/a'}` m/s
- Velocity-profile snapshot source: `{latest_profile_dir if latest_profile_dir is not None else 'not available'}`

Tables:

- `{mdot_csv.resolve()}`
- `{piv_csv.resolve()}`
{f"- `{(run_root / 'tables' / 'velocity' / 'velocity_profile_snapshot_long.csv').resolve()}`" if velocity_profile_rows else "- velocity profile snapshot unavailable"}

## Temperature

- Latest average TP temperature: `{probe_latest if probe_latest is not None else 'n/a'}` K
- Latest TW station mean summary: `{stats_text(tw_latest_values)}`

Tables:

- `{tp_csv.resolve()}`
- `{tw_csv.resolve()}`

## Heat transfer

- Latest total heat from `total_Q.dat`: `{total_q_rows[-1]['value'] if total_q_rows else 'n/a'}` W
- Latest ambient proxy from wall-heat sections: `{ambient_latest if ambient_latest is not None else 'n/a'}` W
- Latest cooling-branch removal: `{series_latest(section_rows, 'cooling_branch_total_removal_w') if section_rows else 'n/a'}` W

Tables:

- `{total_q_csv.resolve()}`
- `{section_csv.resolve()}`

## Pressure

- Baseline native pressure monitor availability: `False`
- Boundary note: `{pressure_note}`

Table:

- `{pressure_csv.resolve()}`

## Wall quality

- yPlus summary source: `{(yplus_dir / 'yPlus.dat') if yplus_dir is not None else 'not available'}`
- yPlus average summary: `{stats_text([row['avg_yplus'] for row in yplus_rows]) if yplus_dir is not None and yplus_rows else 'n/a'}`
- Wall-shear summary source: `{(runtime_root / 'postProcessing' / 'wallShearStress' / '0' / 'wallShearStress.dat').resolve()}`

Tables:

- `{(run_root / 'tables' / 'wall_quality' / 'yplus_patch_summary.csv').resolve() if yplus_dir is not None and yplus_rows else 'yPlus summary unavailable'}`
- `{(run_root / 'tables' / 'wall_quality' / 'wall_shear_patch_summary.csv').resolve() if wall_shear_rows else 'wall shear summary unavailable'}`

## Validation and comparison context

- Direct validation case: `{comparison_row['exp_case_name'] or 'n/a'}`
- TP RMSE: `{comparison_row['exp_tp_rmse_k'] or 'n/a'}`
- TW RMSE: `{comparison_row['exp_tw_rmse_k'] or 'n/a'}`
- mdot absolute error: `{comparison_row['exp_mdot_abs_error_pct'] or 'n/a'}` %
- external-loss absolute error: `{comparison_row['exp_q_external_loss_abs_error_pct'] or 'n/a'}` %

Comparison table:

- `{comparison_csv.resolve()}`

## Caveats

- This v1 per-run package starts from the easy labeled native `postProcessing` outputs and does not require new OpenFOAM reconstruction or new field slicing.
- Pressure figures are not inferred when the native baseline monitor family does not publish them.
- Runs that remain terminated, continuation-affected, or not comparison-clean are still included, but their maturity label remains explicit.
- Existing richer derived artifacts from the June 4/9/10 report stack remain useful context and are listed in the artifact map where reused.
"""
    write_markdown(technical_analysis_path, technical_analysis)

    report_sections = [
        {"section_id": "executive_summary", "path": str(executive_summary_path.resolve())},
        {"section_id": "technical_analysis", "path": str(technical_analysis_path.resolve())},
    ]
    artifact_map = {
        "source_id": source_id,
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "readiness_label": readiness,
        "setup_sources": source_paths,
        "postprocessing_sources": source_paths,
        "derived_tables": tables,
        "figures": figures,
        "report_sections": report_sections,
        "missing_expected_artifacts": missing_artifacts,
        "reused_existing_artifacts": reused_existing_artifacts,
        "notes": [
            "Pressure is recorded as unavailable from the baseline native monitor set when no direct labeled pressure family exists.",
            "This run package is meant to be paper-reusable but conservative about what is directly evidenced by the native monitor stack.",
        ],
    }
    json_dump(artifact_map_json_path, artifact_map)

    artifact_lines = [
        f"# {display_label} artifact map",
        "",
        f"- Source id: `{source_id}`",
        f"- Source root: `{source_root}`",
        f"- Runtime root: `{runtime_root}`",
        f"- Readiness label: `{readiness}`",
        "",
        "## Tables",
        "",
    ]
    for field in FIELD_ORDER:
        artifact_lines.append(f"### {field}")
        for path in tables[field]:
            artifact_lines.append(f"- `{path}`")
        if not tables[field]:
            artifact_lines.append("- none")
        artifact_lines.append("")
    artifact_lines.append("## Figures")
    artifact_lines.append("")
    for field in FIELD_ORDER:
        artifact_lines.append(f"### {field}")
        if not figures[field]:
            artifact_lines.append("- none")
        for figure in figures[field]:
            artifact_lines.append(f"- `{figure['figure_id']}`")
            artifact_lines.append(f"  - svg: `{figure['svg']}`")
            artifact_lines.append(f"  - pdf: `{figure['pdf']}`")
            artifact_lines.append(f"  - tikz: `{figure['tikz']}`")
            artifact_lines.append(f"  - table: `{figure['table_csv']}`")
        artifact_lines.append("")
    artifact_lines.extend(["## Missing expected artifacts", ""])
    if missing_artifacts:
        for item in missing_artifacts:
            artifact_lines.append(f"- `{item['field']}` / `{item['artifact']}`: {item['reason']}")
    else:
        artifact_lines.append("- none")
    write_markdown(artifact_map_path, "\n".join(artifact_lines))

    run_summary = {
        "generated_at": iso_timestamp(),
        "source_id": source_id,
        "display_label": display_label,
        "readiness_label": readiness,
        "run_status": runtime_row["run_status"],
        "convergence_reached": runtime_row["convergence_reached"],
        "fluid": setup_row.get("fluid", ""),
        "variant_label": setup_row.get("variant_label", ""),
        "base_case_id": setup_row.get("base_case_id", ""),
        "final_time_metadata_s": maybe_float(runtime_row["final_time_metadata_s"]),
        "latest_heat_time_s": maybe_float(runtime_row["latest_heat_time_s"]),
        "latest_probe_time_s": maybe_float(runtime_row["latest_probe_time_s"]),
        "mdot_mean_abs_kg_s": mdot_latest,
        "probe_T_avg_K": probe_latest,
        "tw_station_mean_avg_K": mean(tw_latest_values) if tw_latest_values else None,
        "ambient_proxy_w": ambient_latest,
        "total_q_latest_w": total_q_rows[-1]["value"] if total_q_rows else None,
        "avg_yplus": mean(yplus_values) if yplus_values else None,
        "exp_tp_rmse_k": maybe_float(comparison_row["exp_tp_rmse_k"]),
        "exp_tw_rmse_k": maybe_float(comparison_row["exp_tw_rmse_k"]),
        "exp_mdot_abs_error_pct": maybe_float(comparison_row["exp_mdot_abs_error_pct"]),
        "exp_q_external_loss_abs_error_pct": maybe_float(comparison_row["exp_q_external_loss_abs_error_pct"]),
        "report_paths": {
            "executive_summary": str(executive_summary_path.resolve()),
            "technical_analysis": str(technical_analysis_path.resolve()),
            "artifact_map": str(artifact_map_path.resolve()),
        },
    }
    json_dump(run_summary_path, run_summary)
    return run_summary


def main() -> int:
    args = parse_args()
    build_run_package(
        args.source_id,
        Path(args.campaign_root).resolve(),
        reuse_existing_renders=args.reuse_existing_renders,
    )
    return 0


METADATA_MAP = csv_map(METADATA_CSV, "source_id")
VALIDATION_MAP = csv_map(VALIDATION_CSV, "source_id")
HEAT_AUDIT_MAP = csv_map(HEAT_AUDIT_CSV, "source_id")
CONTRACT_MAP = csv_map(CONTRACT_CSV, "ethan_source_id")


if __name__ == "__main__":
    raise SystemExit(main())
