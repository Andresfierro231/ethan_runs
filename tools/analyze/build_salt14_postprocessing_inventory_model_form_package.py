#!/usr/bin/env python3
"""Build a Salt1-4 postProcessing inventory for model-form diagnostics.

This builder reads OpenFOAM function-object outputs from registered Salt1-4
case trees and writes a task-scoped tidy table plus summary products. It never
mutates native solver outputs, registry/admission state, or predictive runtime
contracts. Realized CFD mdot, wallHeatFlux, and temperature rows are explicitly
marked as diagnostic evidence, not runtime-admissible inputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    parse_probe_series,
    parse_scalar_series,
    parse_vol_field_series,
    read_registry_rows,
    relative_to_workspace,
    safe_float,
)
from tools.extract import postprocessing_registry_common as pp  # noqa: E402


TASK_ID = "TODO-SALT14-POSTPROCESSING-INVENTORY-MODEL-FORM-PACKAGE-2026-07-22"
OUT_DIR = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_salt14_postprocessing_inventory_model_form_package"
)

TIDY_COLUMNS = [
    "source_id",
    "case_id",
    "case_family",
    "source_path",
    "function_object",
    "time_s",
    "quantity",
    "patch_or_surface",
    "value",
    "unit",
    "sign_convention",
    "admissibility_role",
    "dataset",
    "value_name",
    "source_file_relpath",
    "mesh_level",
    "variant_label",
    "run_status",
    "comparison_ready",
    "window_role",
    "source_owner",
    "profile_distance_m",
    "profile_axis",
    "profile_level",
]

WINDOW_COLUMNS = [
    "source_id",
    "case_id",
    "case_family",
    "function_object",
    "quantity",
    "patch_or_surface",
    "unit",
    "admissibility_role",
    "window_start_s",
    "window_end_s",
    "n",
    "mean",
    "std",
    "min",
    "max",
    "first_value",
    "last_value",
    "drift_abs",
    "drift_pct",
    "model_form_use",
]

DELTA_COLUMNS = [
    "comparison_id",
    "basis",
    "case_family",
    "left_source_id",
    "right_source_id",
    "quantity",
    "left_value",
    "right_value",
    "delta",
    "delta_pct",
    "unit",
    "admissibility_role",
    "model_form_use",
]

MANIFEST_COLUMNS = [
    "source_id",
    "case_id",
    "case_family",
    "source_owner",
    "source_root",
    "runtime_root",
    "postprocessing_root",
    "postprocessing_exists",
    "parsed_tidy_rows",
    "profile_time_dirs_seen",
    "profile_files_seen",
    "profile_mode",
    "terminal_rows_per_file",
    "profile_time_dirs_parsed",
    "missing_function_objects",
    "native_solver_output_mutated",
    "registry_or_admission_mutated",
]

USE_CASE_COLUMNS = [
    "use_case_id",
    "title",
    "input_quantities",
    "derived_outputs",
    "model_form_value",
    "admissibility_boundary",
    "primary_outputs",
]

SUMMARY_COLUMNS = [
    "task_id",
    "generated_at",
    "source_count",
    "parsed_source_count",
    "tidy_rows",
    "window_stat_rows",
    "case_delta_rows",
    "use_case_rows",
    "profile_mode",
    "native_solver_outputs_mutated",
    "registry_or_admission_mutated",
    "runtime_forbidden_inputs_released",
    "decision",
]


@dataclass
class RunningStat:
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0
    min_value: float = math.inf
    max_value: float = -math.inf
    first_time: float | None = None
    last_time: float | None = None
    first_value: float | None = None
    last_value: float | None = None

    def add(self, time_s: float, value: float) -> None:
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (value - self.mean)
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        if self.first_time is None or time_s < self.first_time:
            self.first_time = time_s
            self.first_value = value
        if self.last_time is None or time_s > self.last_time:
            self.last_time = time_s
            self.last_value = value

    @property
    def std(self) -> float:
        if self.n < 2:
            return 0.0
        return math.sqrt(self.m2 / (self.n - 1))


def fmt(value: Any) -> str:
    numeric = safe_float(value)
    if numeric is None or not math.isfinite(numeric):
        return ""
    return f"{numeric:.12g}"


def bool_text(value: bool) -> str:
    return str(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def recent_data_lines(path: Path, max_rows: int) -> list[str]:
    if not path.exists():
        return []
    if max_rows <= 0:
        return []
    # OpenFOAM function-object files can contain millions of rows. Read from
    # the end and grow the buffer until enough non-comment data rows are found.
    chunk_size = 1024 * 1024
    with path.open("rb") as handle:
        handle.seek(0, 2)
        end = handle.tell()
        chunks: list[bytes] = []
        position = end
        data_rows: list[str] = []
        while position > 0:
            read_size = min(chunk_size, position)
            position -= read_size
            handle.seek(position)
            chunks.append(handle.read(read_size))
            text = b"".join(reversed(chunks)).decode("utf-8", errors="replace")
            rows = [
                line.strip()
                for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            data_rows = rows[-max_rows:]
            if len(data_rows) >= max_rows:
                break
        return data_rows


def parse_scalar_series_recent(path: Path, max_rows: int) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for stripped in recent_data_lines(path, max_rows):
        parts = stripped.split()
        if len(parts) < 2:
            continue
        time_value = safe_float(parts[0])
        scalar_value = safe_float(parts[1])
        if time_value is None or scalar_value is None:
            continue
        rows.append({"time": time_value, "value": scalar_value})
    return rows


def parse_vol_field_series_recent(path: Path, max_rows: int) -> list[dict[str, float]]:
    pattern = re.compile(r"^\s*([^\s]+)\s+\(([^)]+)\)\s+([^\s]+)\s+([^\s]+)\s*$")
    rows: list[dict[str, float]] = []
    for stripped in recent_data_lines(path, max_rows):
        match = pattern.match(stripped)
        if not match:
            continue
        time_value = safe_float(match.group(1))
        vector_parts = [safe_float(part, 0.0) for part in match.group(2).split()]
        mag_u = safe_float(match.group(3))
        temp_k = safe_float(match.group(4))
        if time_value is None or mag_u is None or temp_k is None or len(vector_parts) != 3:
            continue
        rows.append(
            {
                "time": time_value,
                "Ux": vector_parts[0] or 0.0,
                "Uy": vector_parts[1] or 0.0,
                "Uz": vector_parts[2] or 0.0,
                "magU": mag_u,
                "T": temp_k,
            }
        )
    return rows


def parse_probe_series_recent(path: Path, max_rows: int) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for stripped in recent_data_lines(path, max_rows):
        parts = stripped.split()
        if len(parts) < 2:
            continue
        time_value = safe_float(parts[0])
        values = [safe_float(part) for part in parts[1:]]
        if time_value is None or any(value is None for value in values):
            continue
        rows.append({"time": time_value, "values": values})
    return {"probe_positions": [], "rows": rows}


def parse_wall_heatflux_rows_recent(path: Path, max_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stripped in recent_data_lines(path, max_rows):
        parts = stripped.split()
        if len(parts) < 6:
            continue
        time_value = safe_float(parts[0])
        min_value = safe_float(parts[2])
        max_value = safe_float(parts[3])
        q_total = safe_float(parts[4])
        q_avg = safe_float(parts[5])
        if None in (time_value, min_value, max_value, q_total, q_avg):
            continue
        rows.append(
            {
                "time_s": float(time_value),
                "patch": parts[1],
                "min_w_m2": float(min_value),
                "max_w_m2": float(max_value),
                "q_net_w": float(q_total),
                "q_avg_w_m2": float(q_avg),
            }
        )
    return rows


def parse_yplus_rows_recent(path: Path, max_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stripped in recent_data_lines(path, max_rows):
        parts = stripped.split()
        if len(parts) < 5:
            continue
        time_value = safe_float(parts[0])
        min_value = safe_float(parts[2])
        max_value = safe_float(parts[3])
        avg_value = safe_float(parts[4])
        if None in (time_value, min_value, max_value, avg_value):
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


def parse_wall_shear_rows_recent(path: Path, max_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stripped in recent_data_lines(path, max_rows):
        match = pp.VECTOR_PATTERN.match(stripped)
        if not match:
            continue
        time_value = safe_float(match.group(1))
        if time_value is None:
            continue
        rows.append(
            {
                "time_s": float(time_value),
                "patch": match.group(2),
                "min_tau_mag": pp.vector_magnitude(match.group(3)),
                "max_tau_mag": pp.vector_magnitude(match.group(4)),
            }
        )
    return rows


def salt_case_family(row: dict[str, str]) -> str:
    text = f"{row.get('case_id', '')} {row.get('source_id', '')}".lower()
    match = re.search(r"salt[_-]?test[_-]?([1-4])", text)
    if match:
        return f"salt{match.group(1)}"
    match = re.search(r"\bsalt([1-4])\b", text)
    if match:
        return f"salt{match.group(1)}"
    return ""


def mesh_level(source_id: str, source_root: Path) -> str:
    text = f"{source_id} {source_root}".lower()
    for candidate in ("coarse", "medium", "fine"):
        if candidate in text:
            return candidate
    return ""


def variant_label(source_id: str, case_id: str) -> str:
    text = f"{source_id} {case_id}".lower()
    if "corrected" in text:
        for token in ("lo10q", "lo5q", "hi5q", "hi10q"):
            if token in text:
                return f"corrected_{token}"
        return "corrected_q"
    if "jin" in text:
        return "jin"
    if "kirst" in text:
        return "kirst"
    if "val_" in source_id or "validation" in text:
        return "validation"
    return ""


def is_registered_salt14(row: dict[str, str]) -> bool:
    return row.get("status") == "registered" and bool(salt_case_family(row))


def default_source_ids() -> list[str]:
    rows = read_registry_rows(ROOT / "registry/case_registry.csv")
    return [row["source_id"] for row in rows if row.get("source_id") and is_registered_salt14(row)]


def case_role(source_id: str, case_id: str, comparison_ready: str, run_status: str) -> str:
    label = variant_label(source_id, case_id)
    if label.startswith("corrected_"):
        return "perturbation_sensitivity_diagnostic"
    if label == "kirst":
        return "legacy_historical_comparison"
    if label == "validation":
        return "external_validation_diagnostic"
    if label == "jin" and comparison_ready == "comparison_candidate" and run_status == "completed":
        return "mainline_comparison_candidate"
    if label == "jin":
        return "mainline_convergence_or_continuation_diagnostic"
    return "diagnostic_context"


def admissibility_role(quantity: str) -> str:
    forbidden = {
        "mdot_kg_s",
        "total_Q_postProc_W",
        "temperature_K",
        "temperature_station_avg_K",
        "Q_wall_patch_W",
        "q_avg_W_m2",
        "q_min_W_m2",
        "q_max_W_m2",
        "slab_T_K",
    }
    if quantity in forbidden:
        return "diagnostic_only_forbidden_runtime_input"
    if quantity in {"min_yplus", "max_yplus", "avg_yplus"}:
        return "comparison_or_uq_support"
    if quantity in {"min_tau_mag", "max_tau_mag", "Ux_m_s", "Uy_m_s", "Uz_m_s", "magU_m_s"}:
        return "comparison_or_uq_support"
    if quantity.startswith("profile_U"):
        return "comparison_or_uq_support"
    return "candidate_model_form_feature_requires_gate"


def sign_convention(function_object: str, quantity: str) -> str:
    if function_object.startswith("mdot_"):
        return "native OpenFOAM surfaceFieldValue sum(phi); signed by faceZone orientation; preserved as diagnostic"
    if function_object == "wallHeatFlux" or quantity.startswith("q_") or quantity.startswith("Q_wall"):
        return "native OpenFOAM wallHeatFlux sign preserved; realized heat-flow diagnostic only; not predictive runtime input"
    if function_object == "total_Q":
        return "native postProcessing total_Q sign preserved; realized global heat-flow diagnostic only"
    if quantity in {"min_yplus", "max_yplus", "avg_yplus"}:
        return "dimensionless wall-distance statistic; nonnegative mesh-quality support"
    if "tau" in quantity:
        return "wallShearStress vector magnitude statistic; nonnegative diagnostic support"
    if "temperature" in quantity or quantity == "slab_T_K":
        return "native temperature value in K; validation/runtime leakage guard applies"
    return "native component orientation preserved"


def context_for_source(source_id: str) -> dict[str, Any]:
    context = pp.case_context(source_id)
    context["case_family"] = salt_case_family(context["registry_row"])
    context["mesh_level"] = mesh_level(source_id, context["source_root"])
    context["variant_label"] = variant_label(source_id, context["case_id"])
    context["run_status"] = context["meta_row"].get("run_status", "")
    context["comparison_ready"] = context["meta_row"].get("comparison_ready", "")
    context["case_role"] = case_role(
        source_id,
        context["case_id"],
        context["comparison_ready"],
        context["run_status"],
    )
    return context


def tidy_row(
    context: dict[str, Any],
    *,
    source_file: Path,
    function_object: str,
    time_s: float | None,
    quantity: str,
    patch_or_surface: str,
    value: float | None,
    unit: str,
    dataset: str,
    value_name: str,
    profile_distance_m: float | None = None,
    profile_axis: str = "",
    profile_level: float | None = None,
) -> dict[str, Any]:
    return {
        "source_id": context["source_id"],
        "case_id": context["case_id"],
        "case_family": context["case_family"],
        "source_path": str(source_file),
        "function_object": function_object,
        "time_s": fmt(time_s),
        "quantity": quantity,
        "patch_or_surface": patch_or_surface,
        "value": fmt(value),
        "unit": unit,
        "sign_convention": sign_convention(function_object, quantity),
        "admissibility_role": admissibility_role(quantity),
        "dataset": dataset,
        "value_name": value_name,
        "source_file_relpath": relative_to_runtime_fast(context["runtime_root"], source_file),
        "mesh_level": context["mesh_level"],
        "variant_label": context["variant_label"],
        "run_status": context["run_status"],
        "comparison_ready": context["comparison_ready"],
        "window_role": context["case_role"],
        "source_owner": context["source_owner"],
        "profile_distance_m": fmt(profile_distance_m),
        "profile_axis": profile_axis,
        "profile_level": fmt(profile_level),
    }


def relative_to_runtime_fast(runtime_root: Path, source_file: Path) -> str:
    try:
        return str(source_file.relative_to(runtime_root))
    except ValueError:
        return relative_to_workspace(source_file)


def numeric_dirs(root: Path) -> list[Path]:
    return pp.numeric_time_dirs(root)


def latest_or_all_dirs(root: Path, latest_only: bool = False) -> list[Path]:
    dirs = numeric_dirs(root)
    if latest_only and dirs:
        return [dirs[-1]]
    return dirs


def parse_probe_outputs(
    context: dict[str, Any],
    post_root: Path,
    name: str,
    dataset: str,
    station_average: bool = False,
    max_time_rows: int = 500,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for time_dir in numeric_dirs(post_root / name):
        path = time_dir / "T"
        payload = parse_probe_series_recent(path, max_time_rows)
        labels = [f"probe_{index}" for index in range(len(payload["rows"][0]["values"]))] if payload["rows"] else []
        for item in payload["rows"]:
            time_value = float(item["time"])
            values = [float(value) for value in item["values"]]
            for index, value in enumerate(values):
                if dataset == "temperature_probe":
                    label = f"TP{index + 1}"
                elif dataset == "wall_temperature_probe":
                    known = pp.probe_labels("TW")
                    label = known[index] if index < len(known) else f"TW{index + 1}"
                else:
                    label = labels[index] if index < len(labels) else f"probe_{index}"
                rows.append(
                    tidy_row(
                        context,
                        source_file=path,
                        function_object=name,
                        time_s=time_value,
                        quantity="temperature_K",
                        patch_or_surface=label,
                        value=value,
                        unit="K",
                        dataset=dataset,
                        value_name="temperature_K",
                    )
                )
            if values and not station_average:
                rows.append(
                    tidy_row(
                        context,
                        source_file=path,
                        function_object=name,
                        time_s=time_value,
                        quantity="temperature_station_avg_K",
                        patch_or_surface=f"{dataset}_avg",
                        value=mean(values),
                        unit="K",
                        dataset=f"{dataset}_stat",
                        value_name="temperature_K",
                    )
                )
            if station_average and values:
                station_values: dict[str, list[float]] = defaultdict(list)
                for index, value in enumerate(values):
                    known = pp.probe_labels("TW")
                    label = known[index] if index < len(known) else f"TW{index + 1}"
                    station_values[label.split("_", 1)[0]].append(value)
                for station, station_items in station_values.items():
                    rows.append(
                        tidy_row(
                            context,
                            source_file=path,
                            function_object=name,
                            time_s=time_value,
                            quantity="temperature_station_avg_K",
                            patch_or_surface=station,
                            value=mean(station_items),
                            unit="K",
                            dataset="wall_temperature_station",
                            value_name="temperature_K",
                        )
                    )
    return rows


def parse_velocity_profiles(
    context: dict[str, Any],
    post_root: Path,
    profile_mode: str,
) -> tuple[list[dict[str, Any]], int, int, int]:
    root = post_root / "velocity_profiles"
    time_dirs = numeric_dirs(root)
    files_seen = sum(len(list(path.glob("*.xy"))) for path in time_dirs)
    if profile_mode == "none":
        return [], len(time_dirs), files_seen, 0
    selected_dirs = time_dirs if profile_mode == "all" else time_dirs[-1:] if time_dirs else []
    rows: list[dict[str, Any]] = []
    for time_dir in selected_dirs:
        profile_time = float(time_dir.name)
        for path in sorted(time_dir.glob("*.xy")):
            match = re.match(r"Y_H_([0-9.]+)_([A-Za-z]+)", path.stem)
            profile_level = safe_float(match.group(1)) if match else None
            profile_axis = match.group(2) if match else ""
            for item in pp.parse_velocity_profile_file(path):
                for value_name, quantity in (
                    ("U_x_m_s", "profile_Ux_m_s"),
                    ("U_y_m_s", "profile_Uy_m_s"),
                    ("U_z_m_s", "profile_Uz_m_s"),
                ):
                    rows.append(
                        tidy_row(
                            context,
                            source_file=path,
                            function_object="velocity_profiles",
                            time_s=profile_time,
                            quantity=quantity,
                            patch_or_surface=path.stem,
                            value=float(item[value_name]),
                            unit="m/s",
                            dataset="velocity_profile",
                            value_name=value_name,
                            profile_distance_m=float(item["distance_m"]),
                            profile_axis=profile_axis,
                            profile_level=profile_level,
                        )
                    )
    return rows, len(time_dirs), files_seen, len(selected_dirs)


def parse_source(
    context: dict[str, Any],
    profile_mode: str,
    max_time_rows: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    post_root = context["runtime_root"] / "postProcessing"
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    profile_time_dirs = 0
    profile_files = 0
    profile_dirs_parsed = 0

    if not post_root.exists():
        manifest = source_manifest_row(context, post_root, 0, 0, 0, profile_mode, ["postProcessing"])
        return [], manifest

    mdot_dirs = sorted(post_root.glob("mdot_*"))
    if not mdot_dirs:
        missing.append("mdot_*")
    for monitor_dir in mdot_dirs:
        for time_dir in numeric_dirs(monitor_dir):
            path = time_dir / "surfaceFieldValue.dat"
            for item in parse_scalar_series_recent(path, max_time_rows):
                rows.append(
                    tidy_row(
                        context,
                        source_file=path,
                        function_object=monitor_dir.name,
                        time_s=float(item["time"]),
                        quantity="mdot_kg_s",
                        patch_or_surface=monitor_dir.name,
                        value=float(item["value"]),
                        unit="kg/s",
                        dataset="mdot_monitor",
                        value_name="mdot_kg_s",
                    )
                )

    total_q_path = post_root / "total_Q.dat"
    total_q_rows = parse_scalar_series_recent(total_q_path, max_time_rows)
    if not total_q_rows:
        missing.append("total_Q.dat")
    for item in total_q_rows:
        rows.append(
            tidy_row(
                context,
                source_file=total_q_path,
                function_object="total_Q",
                time_s=float(item["time"]),
                quantity="total_Q_postProc_W",
                patch_or_surface="all_walls",
                value=float(item["value"]),
                unit="W",
                dataset="total_Q",
                value_name="total_Q_postProc_w",
            )
        )

    piv_dirs = numeric_dirs(post_root / "piv_slab_velocity")
    if not piv_dirs:
        missing.append("piv_slab_velocity")
    for time_dir in piv_dirs:
        path = time_dir / "volFieldValue.dat"
        for item in parse_vol_field_series_recent(path, max_time_rows):
            time_value = float(item["time"])
            for key, quantity, unit in (
                ("Ux", "Ux_m_s", "m/s"),
                ("Uy", "Uy_m_s", "m/s"),
                ("Uz", "Uz_m_s", "m/s"),
                ("magU", "magU_m_s", "m/s"),
                ("T", "slab_T_K", "K"),
            ):
                rows.append(
                    tidy_row(
                        context,
                        source_file=path,
                        function_object="piv_slab_velocity",
                        time_s=time_value,
                        quantity=quantity,
                        patch_or_surface="piv_slab",
                        value=float(item[key]),
                        unit=unit,
                        dataset="piv_slab_velocity",
                        value_name=key,
                    )
                )

    temperature_rows = parse_probe_outputs(
        context, post_root, "temperature_probes", "temperature_probe", max_time_rows=max_time_rows
    )
    if not temperature_rows:
        missing.append("temperature_probes")
    rows.extend(temperature_rows)
    wall_temperature_rows = parse_probe_outputs(
        context,
        post_root,
        "wall_temperature_probes",
        "wall_temperature_probe",
        station_average=True,
        max_time_rows=max_time_rows,
    )
    if not wall_temperature_rows:
        missing.append("wall_temperature_probes")
    rows.extend(wall_temperature_rows)

    wall_dirs = numeric_dirs(post_root / "wallHeatFlux")
    if not wall_dirs:
        missing.append("wallHeatFlux")
    for time_dir in wall_dirs:
        path = time_dir / "wallHeatFlux.dat"
        for item in parse_wall_heatflux_rows_recent(path, max_time_rows):
            for key, quantity, unit in (
                ("q_net_w", "Q_wall_patch_W", "W"),
                ("q_avg_w_m2", "q_avg_W_m2", "W/m^2"),
                ("min_w_m2", "q_min_W_m2", "W/m^2"),
                ("max_w_m2", "q_max_W_m2", "W/m^2"),
            ):
                rows.append(
                    tidy_row(
                        context,
                        source_file=path,
                        function_object="wallHeatFlux",
                        time_s=float(item["time_s"]),
                        quantity=quantity,
                        patch_or_surface=str(item["patch"]),
                        value=float(item[key]),
                        unit=unit,
                        dataset="wall_heat_flux",
                        value_name=quantity,
                    )
                )

    yplus_dirs = numeric_dirs(post_root / "yPlus")
    if not yplus_dirs:
        missing.append("yPlus")
    for time_dir in yplus_dirs:
        path = time_dir / "yPlus.dat"
        for item in parse_yplus_rows_recent(path, max_time_rows):
            for quantity in ("min_yplus", "max_yplus", "avg_yplus"):
                rows.append(
                    tidy_row(
                        context,
                        source_file=path,
                        function_object="yPlus",
                        time_s=float(item["time_s"]),
                        quantity=quantity,
                        patch_or_surface=str(item["patch"]),
                        value=float(item[quantity]),
                        unit="",
                        dataset="yplus",
                        value_name=quantity,
                    )
                )

    shear_dirs = numeric_dirs(post_root / "wallShearStress")
    if not shear_dirs:
        missing.append("wallShearStress")
    for time_dir in shear_dirs:
        path = time_dir / "wallShearStress.dat"
        for item in parse_wall_shear_rows_recent(path, max_time_rows):
            for quantity in ("min_tau_mag", "max_tau_mag"):
                rows.append(
                    tidy_row(
                        context,
                        source_file=path,
                        function_object="wallShearStress",
                        time_s=float(item["time_s"]),
                        quantity=quantity,
                        patch_or_surface=str(item["patch"]),
                        value=float(item[quantity]),
                        unit="m2/s2",
                        dataset="wall_shear_stress",
                        value_name=quantity,
                    )
                )

    profile_rows, profile_time_dirs, profile_files, profile_dirs_parsed = parse_velocity_profiles(
        context, post_root, profile_mode
    )
    if profile_time_dirs == 0:
        missing.append("velocity_profiles")
    rows.extend(profile_rows)

    deduped = dedupe_tidy(rows)
    manifest = source_manifest_row(
        context,
        post_root,
        len(deduped),
        profile_time_dirs,
        profile_files,
        profile_mode,
        missing,
        profile_dirs_parsed=profile_dirs_parsed,
        max_time_rows=max_time_rows,
    )
    return deduped, manifest


def source_manifest_row(
    context: dict[str, Any],
    post_root: Path,
    parsed_rows: int,
    profile_time_dirs: int,
    profile_files: int,
    profile_mode: str,
    missing: list[str],
    profile_dirs_parsed: int = 0,
    max_time_rows: int = 500,
) -> dict[str, Any]:
    return {
        "source_id": context["source_id"],
        "case_id": context["case_id"],
        "case_family": context["case_family"],
        "source_owner": context["source_owner"],
        "source_root": str(context["source_root"]),
        "runtime_root": str(context["runtime_root"]),
        "postprocessing_root": str(post_root),
        "postprocessing_exists": bool_text(post_root.exists()),
        "parsed_tidy_rows": parsed_rows,
        "profile_time_dirs_seen": profile_time_dirs,
        "profile_files_seen": profile_files,
        "profile_mode": profile_mode,
        "terminal_rows_per_file": max_time_rows,
        "profile_time_dirs_parsed": profile_dirs_parsed,
        "missing_function_objects": ";".join(sorted(set(missing))),
        "native_solver_output_mutated": "false",
        "registry_or_admission_mutated": "false",
    }


def dedupe_tidy(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        key = (
            row["source_id"],
            row["function_object"],
            row["time_s"],
            row["quantity"],
            row["patch_or_surface"],
            row["profile_distance_m"],
            row["profile_axis"],
            row["profile_level"],
        )
        deduped[key] = row
    return sorted(
        deduped.values(),
        key=lambda row: (
            row["source_id"],
            row["function_object"],
            safe_float(row["time_s"], float("-inf")) or float("-inf"),
            row["quantity"],
            row["patch_or_surface"],
            safe_float(row["profile_distance_m"], float("-inf")) or float("-inf"),
        ),
    )


def model_form_use(quantity: str, function_object: str) -> str:
    if quantity in {"Q_wall_patch_W", "q_avg_W_m2", "q_min_W_m2", "q_max_W_m2", "total_Q_postProc_W"}:
        return "thermal source/sink imbalance, passive-loss diagnosis, heat-flow UQ support"
    if quantity in {"mdot_kg_s", "Ux_m_s", "Uy_m_s", "Uz_m_s", "magU_m_s"} or quantity.startswith("profile_U"):
        return "hydraulic stability, recirculation/profile-shape comparison, source-family error support"
    if "temperature" in quantity or quantity == "slab_T_K":
        return "thermal drift, TP/TW residual shape, wall/core contrast diagnosis"
    if "yplus" in quantity:
        return "mesh/wall-resolution adequacy support"
    if "tau" in quantity:
        return "wall-friction and local hydraulic forcing support"
    return "diagnostic feature candidate requiring a separate gate"


def build_window_stats(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stats: dict[tuple[str, ...], RunningStat] = defaultdict(RunningStat)
    exemplar: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        time_value = safe_float(row["time_s"])
        value = safe_float(row["value"])
        if time_value is None or value is None:
            continue
        key = (
            row["source_id"],
            row["case_id"],
            row["case_family"],
            row["function_object"],
            row["quantity"],
            row["patch_or_surface"],
            row["unit"],
            row["admissibility_role"],
        )
        stats[key].add(float(time_value), float(value))
        exemplar[key] = row

    out: list[dict[str, Any]] = []
    for key, stat in sorted(stats.items()):
        row = exemplar[key]
        drift = (stat.last_value - stat.first_value) if stat.last_value is not None and stat.first_value is not None else None
        drift_pct = (100.0 * drift / abs(stat.first_value)) if drift is not None and stat.first_value not in (None, 0.0) else None
        out.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "case_family": row["case_family"],
                "function_object": row["function_object"],
                "quantity": row["quantity"],
                "patch_or_surface": row["patch_or_surface"],
                "unit": row["unit"],
                "admissibility_role": row["admissibility_role"],
                "window_start_s": fmt(stat.first_time),
                "window_end_s": fmt(stat.last_time),
                "n": stat.n,
                "mean": fmt(stat.mean),
                "std": fmt(stat.std),
                "min": fmt(stat.min_value),
                "max": fmt(stat.max_value),
                "first_value": fmt(stat.first_value),
                "last_value": fmt(stat.last_value),
                "drift_abs": fmt(drift),
                "drift_pct": fmt(drift_pct),
                "model_form_use": model_form_use(row["quantity"], row["function_object"]),
            }
        )
    return out


def latest_feature_values(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    selected = {"total_Q_postProc_W", "mdot_kg_s", "temperature_station_avg_K", "magU_m_s", "avg_yplus"}
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if row["quantity"] not in selected:
            continue
        if row["quantity"] == "temperature_station_avg_K" and not row["patch_or_surface"].endswith("_avg"):
            continue
        time_value = safe_float(row["time_s"])
        value = safe_float(row["value"])
        if time_value is None or value is None:
            continue
        key = (row["source_id"], row["quantity"], row["patch_or_surface"])
        previous = latest.get(key)
        if previous is None or float(time_value) >= float(previous["time_s"]):
            latest[key] = {**row, "time_s": float(time_value), "value_float": float(value)}

    collapsed: dict[tuple[str, str], dict[str, Any]] = {}
    by_source_quantity: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for (_source_id, quantity, _surface), row in latest.items():
        by_source_quantity[(row["source_id"], quantity)].append(row)
    for key, items in by_source_quantity.items():
        values = [abs(float(item["value_float"])) if key[1] == "mdot_kg_s" else float(item["value_float"]) for item in items]
        if not values:
            continue
        representative = items[0]
        collapsed[key] = {**representative, "value_float": mean(values)}
    return collapsed


def build_case_delta_matrix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    features = latest_feature_values(rows)
    by_source = {row["source_id"]: row for row in rows}
    source_meta: dict[str, dict[str, str]] = {}
    for row in rows:
        source_meta[row["source_id"]] = row

    nominal_by_family: dict[str, str] = {}
    for source_id, meta in sorted(source_meta.items()):
        if meta["variant_label"] == "jin" and meta["case_family"] not in nominal_by_family:
            nominal_by_family[meta["case_family"]] = source_id

    out: list[dict[str, Any]] = []
    quantities = ["total_Q_postProc_W", "mdot_kg_s", "temperature_station_avg_K", "magU_m_s", "avg_yplus"]

    ordered_families = sorted(nominal_by_family)
    for left_family, right_family in zip(ordered_families, ordered_families[1:]):
        left_source = nominal_by_family[left_family]
        right_source = nominal_by_family[right_family]
        for quantity in quantities:
            left = features.get((left_source, quantity))
            right = features.get((right_source, quantity))
            if left is None or right is None:
                continue
            out.append(delta_row("nominal_jin_sequence", left_family, left_source, right_source, quantity, left, right))

    for source_id, meta in sorted(source_meta.items()):
        family = meta["case_family"]
        nominal = nominal_by_family.get(family)
        if not nominal or nominal == source_id:
            continue
        if meta["variant_label"] not in {"kirst", "corrected_lo10q", "corrected_lo5q", "corrected_hi5q", "corrected_hi10q", "validation"}:
            continue
        for quantity in quantities:
            left = features.get((nominal, quantity))
            right = features.get((source_id, quantity))
            if left is None or right is None:
                continue
            out.append(delta_row(f"{meta['variant_label']}_minus_nominal", family, nominal, source_id, quantity, left, right))
    return out


def delta_row(
    basis: str,
    family: str,
    left_source: str,
    right_source: str,
    quantity: str,
    left: dict[str, Any],
    right: dict[str, Any],
) -> dict[str, Any]:
    left_value = float(left["value_float"])
    right_value = float(right["value_float"])
    delta = right_value - left_value
    delta_pct = 100.0 * delta / abs(left_value) if left_value else None
    role = admissibility_role(quantity)
    return {
        "comparison_id": f"{basis}:{left_source}->{right_source}:{quantity}",
        "basis": basis,
        "case_family": family,
        "left_source_id": left_source,
        "right_source_id": right_source,
        "quantity": quantity,
        "left_value": fmt(left_value),
        "right_value": fmt(right_value),
        "delta": fmt(delta),
        "delta_pct": fmt(delta_pct),
        "unit": left["unit"],
        "admissibility_role": role,
        "model_form_use": model_form_use(quantity, right["function_object"]),
    }


def use_case_rows() -> list[dict[str, str]]:
    return [
        {
            "use_case_id": "thermal_source_sink_diagnosis",
            "title": "Thermal source/sink model-form diagnosis",
            "input_quantities": "Q_wall_patch_W;q_avg_W_m2;total_Q_postProc_W;temperature_K;temperature_station_avg_K",
            "derived_outputs": "window drift/std;patch heat-flow deltas;nominal/perturbation heat-flow response",
            "model_form_value": "Identifies heater/cooler/passive-loss imbalance and source-placement candidates while keeping realized wallHeatFlux forbidden as a runtime input.",
            "admissibility_boundary": "Realized wallHeatFlux, total_Q, and probe temperatures are diagnostic/scoring evidence only until a separate source/property gate releases setup-safe inputs.",
            "primary_outputs": "salt14_postprocessing_tidy.csv;salt14_postprocessing_window_stats.csv;salt14_case_delta_matrix.csv",
        },
        {
            "use_case_id": "hydraulic_recirculation_support",
            "title": "Hydraulic and recirculation model-form support",
            "input_quantities": "mdot_kg_s;Ux_m_s;Uy_m_s;Uz_m_s;magU_m_s;profile_Ux_m_s;profile_Uy_m_s;profile_Uz_m_s;min_tau_mag;max_tau_mag;avg_yplus",
            "derived_outputs": "mdot monitor agreement;profile-shape deltas;wall-resolution adequacy;wall-shear support",
            "model_form_value": "Supports pressure/recirculation model-form diagnosis and source-family error analysis without substituting these rows for exact S13 exchange labels.",
            "admissibility_boundary": "CFD mdot remains forbidden as a predictive runtime input; velocity, yPlus, and shear rows are comparison/UQ support unless a later gate admits a setup-safe derived feature.",
            "primary_outputs": "salt14_postprocessing_tidy.csv;salt14_postprocessing_window_stats.csv;salt14_case_delta_matrix.csv",
        },
    ]


def write_readme(out_dir: Path, summary: dict[str, Any], profile_mode: str) -> None:
    text = f"""---
provenance:
  generated_by: {TASK_ID}
  generated_at: {summary['generated_at']}
tags: [salt1-4, postprocessing, model-form, diagnostic-evidence]
related:
  - tools/extract/postprocessing_registry_common.py
  - registry/case_registry.csv
---

# Salt1-4 postProcessing inventory and model-form evidence package

This package normalizes registered Salt1-4 OpenFOAM `postProcessing` outputs
into a tidy diagnostic table. It is designed to make the existing function
objects usable for model-form reasoning: heat-flow balance, mass-flow
stability, profile-shape comparison, wall-resolution checks, wall-shear support,
and case-to-case/source-family deltas.

Decision: `{summary['decision']}`.

## Outputs

- `salt14_postprocessing_tidy.csv`: one row per parsed function-object value.
- `salt14_postprocessing_window_stats.csv`: window mean/std/drift/min/max by
  source/function/quantity/entity.
- `salt14_case_delta_matrix.csv`: nominal and variant deltas for selected
  model-form diagnostic quantities.
- `salt14_model_form_use_cases.csv`: two documented model-form use cases.
- `salt14_inventory_manifest.csv`: source coverage, missing function objects,
  and profile scan metadata.

Velocity-profile mode: `{profile_mode}`. The default task mode parses the
latest available velocity-profile time per source and records total profile
directory/file coverage in the manifest. Use `--profile-mode all` only in a
separate heavy row if full profile history is needed.

## Guardrails

Native solver outputs are read-only. No OpenFOAM `postProcess`, solver launch,
scheduler action, registry/admission mutation, Fluid edit, coefficient
admission, source/property release, Qwall release, final-score claim, or S13
label substitution is performed.

Realized CFD `mdot`, realized `wallHeatFlux`, `total_Q`, and probe/wall
temperatures are marked `diagnostic_only_forbidden_runtime_input`. They may be
used to explain errors, compare cases, quantify drift/UQ support, and design
candidate model forms; they are not predictive runtime inputs.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build(
    source_ids: list[str] | None = None,
    out_dir: Path = OUT_DIR,
    profile_mode: str = "latest",
    max_time_rows: int = 500,
) -> dict[str, Any]:
    generated_at = iso_timestamp()
    ensure_dir(out_dir)
    selected_ids = source_ids or default_source_ids()
    tidy_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for source_id in selected_ids:
        try:
            context = context_for_source(source_id)
            rows, manifest = parse_source(context, profile_mode, max_time_rows)
            tidy_rows.extend(rows)
            manifest_rows.append(manifest)
        except Exception as exc:
            errors.append(
                {
                    "source_id": source_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "native_solver_output_mutated": "false",
                    "registry_or_admission_mutated": "false",
                }
            )

    tidy_rows = dedupe_tidy(tidy_rows)
    window_rows = build_window_stats(tidy_rows)
    delta_rows = build_case_delta_matrix(tidy_rows)
    uses = use_case_rows()

    csv_dump(out_dir / "salt14_postprocessing_tidy.csv", TIDY_COLUMNS, tidy_rows)
    csv_dump(out_dir / "salt14_postprocessing_window_stats.csv", WINDOW_COLUMNS, window_rows)
    csv_dump(out_dir / "salt14_case_delta_matrix.csv", DELTA_COLUMNS, delta_rows)
    csv_dump(out_dir / "salt14_model_form_use_cases.csv", USE_CASE_COLUMNS, uses)
    csv_dump(out_dir / "salt14_inventory_manifest.csv", MANIFEST_COLUMNS, manifest_rows)
    csv_dump(
        out_dir / "salt14_inventory_errors.csv",
        ["source_id", "error_type", "error_message", "native_solver_output_mutated", "registry_or_admission_mutated"],
        errors,
    )

    summary = {
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_count": len(selected_ids),
        "parsed_source_count": sum(1 for row in manifest_rows if int(row["parsed_tidy_rows"]) > 0),
        "tidy_rows": len(tidy_rows),
        "window_stat_rows": len(window_rows),
        "case_delta_rows": len(delta_rows),
        "use_case_rows": len(uses),
        "profile_mode": profile_mode,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "runtime_forbidden_inputs_released": False,
        "decision": "postprocessing_inventory_published_diagnostic_only_no_runtime_release",
    }
    json_dump(out_dir / "summary.json", summary)
    csv_dump(out_dir / "summary.csv", SUMMARY_COLUMNS, [summary])
    write_readme(out_dir, summary, profile_mode)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--profile-mode", choices=("latest", "all", "none"), default="latest")
    parser.add_argument("--max-time-rows", type=int, default=500)
    args = parser.parse_args()
    summary = build(args.source_ids, args.out, args.profile_mode, args.max_time_rows)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
