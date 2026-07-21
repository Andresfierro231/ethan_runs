from __future__ import annotations

import csv
import json
import math
import re
import sqlite3
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from tools.common import (
    WORKSPACE_ROOT,
    base_case_id,
    csv_dump,
    ensure_dir,
    get_registry_row,
    iso_timestamp,
    json_dump,
    parse_probe_series,
    parse_scalar_series,
    parse_vol_field_series,
    read_registry_rows,
    safe_float,
)


WALL_PROBE_LOCATIONS = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "tp_tw_probe_locations.csv"
METADATA_CANDIDATES = (
    WORKSPACE_ROOT / "reports" / "2026-06" / "2026-06-04" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv",
    WORKSPACE_ROOT / "reports" / "2026-06" / "2026-06-02" / "2026-06-02_ethan_case_metadata_index" / "ethan_case_metadata_index.csv",
)
HEAT_AUDIT_CSV = WORKSPACE_ROOT / "reports" / "2026-06" / "2026-06-09" / "2026-06-09_ethan_steady_state_heat_flow_audit" / "case_heat_inventory.csv"
MDOT_TOLERANCE_KG_S = 1.0e-6

HEATER_PATCHES = {"pipeleg_lower_04_straight", "pipeleg_lower_05_straight", "pipeleg_lower_06_straight"}
TEST_SECTION_PATCHES = {"pipeleg_left_04_test_section"}
COOLING_BRANCH_PATCHES = {"pipeleg_upper_04_reducer", "pipeleg_upper_05_cooler", "pipeleg_upper_06_reducer"}
VECTOR_PATTERN = re.compile(r"^\s*([^\s]+)\s+([^\s]+)\s+\(([^)]+)\)\s+\(([^)]+)\)\s*$")
PROBE_POSITION_PATTERN = re.compile(r"# Probe\s+\d+\s+\(([^)]+)\)")

NORMALIZED_COLUMNS = [
    "source_id",
    "source_owner",
    "case_id",
    "bucket",
    "run_name",
    "dataset",
    "time_s",
    "entity_name",
    "value_name",
    "value",
    "units",
    "x_m",
    "y_m",
    "z_m",
    "distance_m",
    "profile_time_s",
    "profile_axis",
    "profile_level",
    "source_file_relpath",
]

WALL_HEAT_GROUPED_COLUMNS = [
    "total_Q_postProc",
    "time_s",
    "ambient_proxy_w",
    "ambient_noncooling_proxy_w",
    "cooling_branch_total_removal_w",
    "cooling_branch_excess_w",
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

SUMMARY_COLUMNS = [
    "generated_at",
    "source_id",
    "source_owner",
    "case_id",
    "bucket",
    "run_name",
    "fluid",
    "variant_label",
    "source_root",
    "runtime_root",
    "mdot_monitor_count",
    "mdot_all_same",
    "mdot_consensus_kg_s",
    "mdot_mean_abs_kg_s",
    "mdot_abs_min_kg_s",
    "mdot_abs_max_kg_s",
    "mdot_abs_spread_kg_s",
    "mdot_discrepancy_note",
    "latest_total_Q_postProc_w",
    "latest_piv_magU_m_s",
    "latest_tp_avg_k",
    "latest_tw_station_count",
    "latest_velocity_profile_time_s",
    "latest_yplus_time_s",
    "latest_wall_shear_time_s",
    "comparison_ready",
    "run_status",
    "disposition_note",
]

INDEX_COLUMNS = [
    "generated_at",
    "source_id",
    "source_owner",
    "case_id",
    "bucket",
    "run_name",
    "fluid",
    "variant_label",
    "run_root",
    "normalized_csv",
    "heat_grouped_csv",
    "summary_csv",
    "sqlite_db",
    "mdot_all_same",
    "mdot_consensus_kg_s",
    "mdot_abs_spread_kg_s",
    "latest_total_Q_postProc_w",
    "latest_tp_avg_k",
    "run_status",
    "comparison_ready",
]

NORMALIZED_NUMERIC_COLUMNS = {
    "time_s",
    "value",
    "x_m",
    "y_m",
    "z_m",
    "distance_m",
    "profile_time_s",
    "profile_level",
}
WALL_HEAT_NUMERIC_COLUMNS = set(WALL_HEAT_GROUPED_COLUMNS)
SUMMARY_NUMERIC_COLUMNS = {
    "mdot_monitor_count",
    "mdot_all_same",
    "mdot_consensus_kg_s",
    "mdot_mean_abs_kg_s",
    "mdot_abs_min_kg_s",
    "mdot_abs_max_kg_s",
    "mdot_abs_spread_kg_s",
    "latest_total_Q_postProc_w",
    "latest_piv_magU_m_s",
    "latest_tp_avg_k",
    "latest_tw_station_count",
    "latest_velocity_profile_time_s",
    "latest_yplus_time_s",
    "latest_wall_shear_time_s",
}
INDEX_NUMERIC_COLUMNS = {
    "mdot_all_same",
    "mdot_consensus_kg_s",
    "mdot_abs_spread_kg_s",
    "latest_total_Q_postProc_w",
    "latest_tp_avg_k",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_map(path: Path, key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in read_csv_rows(path) if row.get(key)}


@lru_cache(maxsize=1)
def metadata_map() -> dict[str, dict[str, str]]:
    for candidate in METADATA_CANDIDATES:
        if candidate.exists():
            return csv_map(candidate, "source_id")
    return {}


@lru_cache(maxsize=1)
def heat_audit_map() -> dict[str, dict[str, str]]:
    if not HEAT_AUDIT_CSV.exists():
        return {}
    return csv_map(HEAT_AUDIT_CSV, "source_id")


@lru_cache(maxsize=1)
def probe_location_rows() -> list[dict[str, str]]:
    return read_csv_rows(WALL_PROBE_LOCATIONS)


def probe_labels(group: str) -> list[str]:
    return [row["label"] for row in probe_location_rows() if row.get("group") == group and row.get("label")]


def probe_locations(group: str) -> dict[str, tuple[float | None, float | None, float | None]]:
    output: dict[str, tuple[float | None, float | None, float | None]] = {}
    for row in probe_location_rows():
        if row.get("group") != group or not row.get("label"):
            continue
        output[row["label"]] = (
            safe_float(row.get("x_m")),
            safe_float(row.get("y_m")),
            safe_float(row.get("z_m")),
        )
    return output


def default_source_ids() -> list[str]:
    return [
        row["source_id"]
        for row in read_registry_rows(WORKSPACE_ROOT / "registry" / "case_registry.csv")
        if row.get("status") == "registered" and row.get("source_id") != "modern_runs_campaign_inventory_2026-06-01"
    ]


def bucket_for_case(case_id: str, fluid: str = "") -> str:
    lowered_case = case_id.lower()
    lowered_fluid = fluid.lower()
    case_base = base_case_id(lowered_case)
    mapping = {
        "salt_test_1": "salt1",
        "salt_test_2": "salt2",
        "salt_test_3": "salt3",
        "salt_test_4": "salt4",
        "water_test_1": "water1",
        "water_test_2": "water2",
        "water_test_3": "water3",
        "water_test_4": "water4",
    }
    if case_base in mapping:
        return mapping[case_base]
    if "water" in lowered_case or "water" in lowered_fluid:
        return "extended_water"
    return "extended_salt"


def case_context(source_id: str) -> dict[str, Any]:
    registry_row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)
    meta_row = metadata_map().get(source_id, {})
    heat_row = heat_audit_map().get(source_id, {})
    source_root = Path(registry_row["source_root"]).resolve()
    runtime_root = Path(meta_row.get("active_runtime_root") or source_root).resolve()
    case_id = registry_row["case_id"]
    bucket = bucket_for_case(case_id, meta_row.get("fluid", ""))
    return {
        "registry_row": registry_row,
        "meta_row": meta_row,
        "heat_row": heat_row,
        "source_root": source_root,
        "runtime_root": runtime_root,
        "source_id": source_id,
        "source_owner": registry_row["source_owner"],
        "case_id": case_id,
        "bucket": bucket,
        "run_name": source_id,
    }


def case_registry_root(context: dict[str, Any]) -> Path:
    return (
        WORKSPACE_ROOT
        / "registry"
        / context["bucket"]
        / context["source_owner"]
        / context["case_id"]
        / context["run_name"]
    )


def relative_to_runtime(runtime_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(runtime_root.resolve()))
    except ValueError:
        return str(path.resolve())


def latest_numeric_dir(root: Path) -> Path | None:
    if not root.exists():
        return None
    candidates = [path for path in root.iterdir() if path.is_dir() and _is_number(path.name)]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item.name))


def numeric_time_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        [path for path in root.iterdir() if path.is_dir() and _is_number(path.name)],
        key=lambda item: float(item.name),
    )


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def parse_probe_positions(path: Path) -> list[tuple[float | None, float | None, float | None]]:
    positions: list[tuple[float | None, float | None, float | None]] = []
    if not path.exists():
        return positions
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = PROBE_POSITION_PATTERN.search(line)
            if not match:
                continue
            parts = [safe_float(part) for part in match.group(1).split()]
            if len(parts) != 3:
                positions.append((None, None, None))
            else:
                positions.append((parts[0], parts[1], parts[2]))
    return positions


def parse_wall_heatflux_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
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


def vector_magnitude(text: str) -> float:
    values = [safe_float(part) or 0.0 for part in text.split()]
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
            time_value = safe_float(match.group(1))
            if time_value is None:
                continue
            rows.append(
                {
                    "time_s": float(time_value),
                    "patch": match.group(2),
                    "min_tau_mag": vector_magnitude(match.group(3)),
                    "max_tau_mag": vector_magnitude(match.group(4)),
                }
            )
    return rows


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
            distance = safe_float(parts[0])
            u_x = safe_float(parts[1])
            u_y = safe_float(parts[2])
            u_z = safe_float(parts[3])
            if None in (distance, u_x, u_y, u_z):
                continue
            rows.append(
                {
                    "distance_m": float(distance),
                    "U_x_m_s": float(u_x),
                    "U_y_m_s": float(u_y),
                    "U_z_m_s": float(u_z),
                }
            )
    return rows


def load_velocity_profile_rows_from_runtime(context: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    velocity_profile_root = context["runtime_root"] / "postProcessing" / "velocity_profiles"
    for time_dir in numeric_time_dirs(velocity_profile_root):
        profile_time = float(time_dir.name)
        for path in sorted(time_dir.glob("*.xy")):
            stem = path.stem
            match = re.match(r"Y_H_([0-9.]+)_([A-Za-z]+)", stem)
            profile_level = safe_float(match.group(1)) if match else None
            profile_axis = match.group(2) if match else ""
            for item in parse_velocity_profile_file(path):
                for value_name in ("U_x_m_s", "U_y_m_s", "U_z_m_s"):
                    rows.append(
                        _normalized_row(
                            context,
                            "velocity_profile",
                            profile_time,
                            stem,
                            value_name,
                            float(item[value_name]),
                            "m/s",
                            path,
                            distance_m=float(item["distance_m"]),
                            profile_time_s=profile_time,
                            profile_axis=profile_axis,
                            profile_level=profile_level,
                        )
                    )
    return dedupe_normalized_rows(rows)


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
        value = safe_float(q_match.group(1))
        if value is not None:
            imposed[patch] = float(value)
    return imposed


def build_wall_heat_grouped_rows(
    context: dict[str, Any],
    wall_heat_rows: list[dict[str, Any]],
    total_q_rows: list[dict[str, float]],
) -> list[dict[str, Any]]:
    patch_by_time: dict[float, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in wall_heat_rows:
        patch_by_time[float(row["time_s"])][str(row["patch"])] = row

    imposed_q = parse_patch_imposed_q(context["source_root"])
    operating_cooling = safe_float(context["meta_row"].get("cooling_power_W")) or 0.0
    total_q_lookup = {float(row["time"]): float(row["value"]) for row in total_q_rows}
    all_times = sorted(set(total_q_lookup) | set(patch_by_time))
    grouped_rows: list[dict[str, Any]] = []
    for time_value in all_times:
        patch_map = patch_by_time.get(time_value, {})
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
        for patch, row in patch_map.items():
            if patch.startswith("ncc_"):
                continue
            q_value = float(row["q_net_w"])
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
        grouped_rows.append(
            {
                "total_Q_postProc": total_q_lookup.get(time_value),
                "time_s": time_value,
                "ambient_proxy_w": passive_ambient + powered_ambient + cooling_excess,
                "ambient_noncooling_proxy_w": passive_ambient + powered_ambient,
                "cooling_branch_total_removal_w": cooling_total,
                "cooling_branch_excess_w": cooling_excess,
                "section_downcomer_net_q_w": sections["downcomer"],
                "section_heater_net_q_w": sections["heater"],
                "section_upcomer_net_q_w": sections["upcomer"],
                "section_test_section_net_q_w": sections["test_section"],
                "section_cooling_branch_net_q_w": sections["cooling_branch"],
                "section_upper_transport_net_q_w": sections["upper_transport"],
                "section_lower_transport_net_q_w": sections["lower_transport"],
                "section_junctions_net_q_w": sections["junctions"],
                "section_other_net_q_w": sections["other"],
            }
        )
    return grouped_rows


def _normalized_row(
    context: dict[str, Any],
    dataset: str,
    time_s: float | None,
    entity_name: str,
    value_name: str,
    value: float | None,
    units: str,
    source_file: Path,
    *,
    x_m: float | None = None,
    y_m: float | None = None,
    z_m: float | None = None,
    distance_m: float | None = None,
    profile_time_s: float | None = None,
    profile_axis: str = "",
    profile_level: float | None = None,
) -> dict[str, Any]:
    return {
        "source_id": context["source_id"],
        "source_owner": context["source_owner"],
        "case_id": context["case_id"],
        "bucket": context["bucket"],
        "run_name": context["run_name"],
        "dataset": dataset,
        "time_s": time_s,
        "entity_name": entity_name,
        "value_name": value_name,
        "value": value,
        "units": units,
        "x_m": x_m,
        "y_m": y_m,
        "z_m": z_m,
        "distance_m": distance_m,
        "profile_time_s": profile_time_s,
        "profile_axis": profile_axis,
        "profile_level": profile_level,
        "source_file_relpath": relative_to_runtime(context["runtime_root"], source_file),
    }


def dedupe_normalized_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = (
            row["dataset"],
            row["time_s"],
            row["entity_name"],
            row["value_name"],
            row["distance_m"],
            row["profile_time_s"],
            row["profile_axis"],
            row["profile_level"],
        )
        deduped[key] = row
    return sorted(
        deduped.values(),
        key=lambda item: (
            str(item["dataset"]),
            _sort_number(item["time_s"]),
            str(item["entity_name"]),
            str(item["value_name"]),
            _sort_number(item["distance_m"]),
            _sort_number(item["profile_time_s"]),
        ),
    )


def dedupe_rows_by_time(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[float, dict[str, Any]] = {}
    for row in rows:
        time_value = safe_float(row.get("time_s"))
        if time_value is None:
            continue
        deduped[float(time_value)] = row
    return [deduped[key] for key in sorted(deduped)]


def _sort_number(value: Any) -> float:
    numeric = safe_float(value)
    if numeric is None:
        return float("-inf")
    return float(numeric)


def build_case_aggregation(source_id: str) -> dict[str, Any]:
    context = case_context(source_id)
    runtime_root = context["runtime_root"]
    post_root = runtime_root / "postProcessing"
    rows: list[dict[str, Any]] = []

    def progress(stage: str) -> None:
        print(f"  - {context['source_id']}: {stage}", flush=True)

    progress("mdot")
    mdot_latest_by_monitor: dict[str, float] = {}
    for path in sorted(post_root.glob("mdot_*/0/surfaceFieldValue.dat")):
        monitor_name = path.parent.parent.name
        series = parse_scalar_series(path)
        for item in series:
            rows.append(
                _normalized_row(
                    context,
                    "mdot_monitor",
                    float(item["time"]),
                    monitor_name,
                    "mdot_kg_s",
                    float(item["value"]),
                    "kg/s",
                    path,
                )
            )
        if series:
            mdot_latest_by_monitor[monitor_name] = float(series[-1]["value"])

    progress("total_Q")
    total_q_path = post_root / "total_Q.dat"
    total_q_rows = parse_scalar_series(total_q_path)
    for item in total_q_rows:
        rows.append(
            _normalized_row(
                context,
                "total_Q",
                float(item["time"]),
                "all_walls",
                "total_Q_postProc_w",
                float(item["value"]),
                "W",
                total_q_path,
            )
        )

    progress("piv_slab_velocity")
    piv_path = post_root / "piv_slab_velocity" / "0" / "volFieldValue.dat"
    piv_rows = parse_vol_field_series(piv_path)
    for item in piv_rows:
        time_value = float(item["time"])
        for value_name, units in (
            ("Ux", "m/s"),
            ("Uy", "m/s"),
            ("Uz", "m/s"),
            ("magU", "m/s"),
            ("T", "K"),
        ):
            rows.append(
                _normalized_row(
                    context,
                    "piv_slab_velocity",
                    time_value,
                    "piv_slab",
                    value_name,
                    float(item[value_name]),
                    units,
                    piv_path,
                )
            )

    progress("temperature_probes")
    tp_path = post_root / "temperature_probes" / "0" / "T"
    tp_payload = parse_probe_series(tp_path)
    tp_positions = parse_probe_positions(tp_path)
    tp_location_map = probe_locations("TP")
    tp_latest_avg: float | None = None
    tp_labels = [f"TP{index + 1}" for index in range(len(tp_payload["rows"][0]["values"]))] if tp_payload["rows"] else []
    for row_index, item in enumerate(tp_payload["rows"]):
        values = [float(value) for value in item["values"]]
        time_value = float(item["time"])
        if values:
            tp_latest_avg = mean(values)
        for index, value in enumerate(values):
            label = tp_labels[index] if index < len(tp_labels) else f"TP{index + 1}"
            coords = tp_location_map.get(label)
            if coords is None and index < len(tp_positions):
                coords = tp_positions[index]
            coords = coords or (None, None, None)
            rows.append(
                _normalized_row(
                    context,
                    "temperature_probe",
                    time_value,
                    label,
                    "temperature_K",
                    value,
                    "K",
                    tp_path,
                    x_m=coords[0],
                    y_m=coords[1],
                    z_m=coords[2],
                )
            )
        if values:
            rows.append(
                _normalized_row(
                    context,
                    "temperature_probe_stat",
                    time_value,
                    "TP_avg",
                    "temperature_K",
                    mean(values),
                    "K",
                    tp_path,
                )
            )

    progress("wall_temperature_probes")
    tw_path = post_root / "wall_temperature_probes" / "0" / "T"
    tw_payload = parse_probe_series(tw_path)
    tw_labels = probe_labels("TW")
    tw_location_map = probe_locations("TW")
    latest_tw_station_count = 0
    for item in tw_payload["rows"]:
        time_value = float(item["time"])
        station_values: dict[str, list[float]] = defaultdict(list)
        station_coords: dict[str, list[tuple[float | None, float | None, float | None]]] = defaultdict(list)
        for index, raw_value in enumerate(item["values"]):
            label = tw_labels[index] if index < len(tw_labels) else f"TW{index + 1}"
            coords = tw_location_map.get(label, (None, None, None))
            value = float(raw_value)
            rows.append(
                _normalized_row(
                    context,
                    "wall_temperature_probe",
                    time_value,
                    label,
                    "temperature_K",
                    value,
                    "K",
                    tw_path,
                    x_m=coords[0],
                    y_m=coords[1],
                    z_m=coords[2],
                )
            )
            station = label.split("_", 1)[0]
            station_values[station].append(value)
            station_coords[station].append(coords)
        latest_tw_station_count = len(station_values)
        for station, values in sorted(station_values.items()):
            x_values = [item[0] for item in station_coords[station] if item[0] is not None]
            y_values = [item[1] for item in station_coords[station] if item[1] is not None]
            z_values = [item[2] for item in station_coords[station] if item[2] is not None]
            rows.append(
                _normalized_row(
                    context,
                    "wall_temperature_station",
                    time_value,
                    station,
                    "temperature_K",
                    mean(values),
                    "K",
                    tw_path,
                    x_m=mean(x_values) if x_values else None,
                    y_m=mean(y_values) if y_values else None,
                    z_m=mean(z_values) if z_values else None,
                )
            )

    progress("wallHeatFlux")
    wall_heat_path = None
    wall_heat_file = latest_numeric_dir(post_root / "wallHeatFlux")
    wall_heat_rows: list[dict[str, Any]] = []
    if wall_heat_file is not None:
        wall_heat_path = wall_heat_file / "wallHeatFlux.dat"
        wall_heat_rows = parse_wall_heatflux_rows(wall_heat_path)
        for item in wall_heat_rows:
            time_value = float(item["time_s"])
            for value_name, units in (
                ("min_w_m2", "W/m^2"),
                ("max_w_m2", "W/m^2"),
                ("q_net_w", "W"),
                ("q_avg_w_m2", "W/m^2"),
            ):
                rows.append(
                    _normalized_row(
                        context,
                        "wall_heat_flux",
                        time_value,
                        str(item["patch"]),
                        value_name,
                        float(item[value_name]),
                        units,
                        wall_heat_path,
                    )
                )

    progress("wallHeatFlux grouped summary")
    grouped_heat_rows = build_wall_heat_grouped_rows(context, wall_heat_rows, total_q_rows)

    progress("yPlus")
    yplus_rows: list[dict[str, Any]] = []
    yplus_dir = latest_numeric_dir(post_root / "yPlus")
    if yplus_dir is not None:
        yplus_path = yplus_dir / "yPlus.dat"
        yplus_rows = parse_yplus_rows(yplus_path)
        for item in yplus_rows:
            time_value = float(item["time_s"])
            for value_name in ("min_yplus", "max_yplus", "avg_yplus"):
                rows.append(
                    _normalized_row(
                        context,
                        "yplus",
                        time_value,
                        str(item["patch"]),
                        value_name,
                        float(item[value_name]),
                        "",
                        yplus_path,
                    )
                )

    progress("wallShearStress")
    wall_shear_rows = parse_wall_shear_rows(post_root / "wallShearStress" / "0" / "wallShearStress.dat")
    wall_shear_path = post_root / "wallShearStress" / "0" / "wallShearStress.dat"
    for item in wall_shear_rows:
        time_value = float(item["time_s"])
        for value_name in ("min_tau_mag", "max_tau_mag"):
            rows.append(
                _normalized_row(
                    context,
                    "wall_shear_stress",
                    time_value,
                    str(item["patch"]),
                    value_name,
                    float(item[value_name]),
                    "",
                    wall_shear_path,
                )
            )

    progress("velocity_profiles latest time only")
    velocity_profile_root = post_root / "velocity_profiles"
    velocity_profile_time_dirs = numeric_time_dirs(velocity_profile_root)
    latest_velocity_profile_time = float(velocity_profile_time_dirs[-1].name) if velocity_profile_time_dirs else None

    progress("dedupe")
    normalized_rows = dedupe_normalized_rows(rows)
    grouped_heat_rows = dedupe_rows_by_time(grouped_heat_rows)

    mdot_abs_values = [abs(value) for value in mdot_latest_by_monitor.values()]
    mdot_spread = (max(mdot_abs_values) - min(mdot_abs_values)) if mdot_abs_values else None
    mdot_all_same = bool(mdot_spread is not None and mdot_spread <= MDOT_TOLERANCE_KG_S)
    mdot_note = ""
    if mdot_abs_values and not mdot_all_same:
        parts = [f"{name}={value:.9g}" for name, value in sorted(mdot_latest_by_monitor.items())]
        mdot_note = "; ".join(parts)

    progress("summary")
    summary_row = {
        "generated_at": iso_timestamp(),
        "source_id": context["source_id"],
        "source_owner": context["source_owner"],
        "case_id": context["case_id"],
        "bucket": context["bucket"],
        "run_name": context["run_name"],
        "fluid": context["meta_row"].get("fluid", ""),
        "variant_label": context["meta_row"].get("variant_label", ""),
        "source_root": str(context["source_root"]),
        "runtime_root": str(context["runtime_root"]),
        "mdot_monitor_count": len(mdot_latest_by_monitor),
        "mdot_all_same": 1 if mdot_all_same else 0,
        "mdot_consensus_kg_s": mean(mdot_abs_values) if mdot_all_same and mdot_abs_values else None,
        "mdot_mean_abs_kg_s": mean(mdot_abs_values) if mdot_abs_values else None,
        "mdot_abs_min_kg_s": min(mdot_abs_values) if mdot_abs_values else None,
        "mdot_abs_max_kg_s": max(mdot_abs_values) if mdot_abs_values else None,
        "mdot_abs_spread_kg_s": mdot_spread,
        "mdot_discrepancy_note": mdot_note,
        "latest_total_Q_postProc_w": float(total_q_rows[-1]["value"]) if total_q_rows else None,
        "latest_piv_magU_m_s": float(piv_rows[-1]["magU"]) if piv_rows else None,
        "latest_tp_avg_k": tp_latest_avg,
        "latest_tw_station_count": latest_tw_station_count,
        "latest_velocity_profile_time_s": latest_velocity_profile_time,
        "latest_yplus_time_s": max((float(item["time_s"]) for item in yplus_rows), default=None),
        "latest_wall_shear_time_s": max((float(item["time_s"]) for item in wall_shear_rows), default=None),
        "comparison_ready": context["meta_row"].get("comparison_ready", ""),
        "run_status": context["meta_row"].get("run_status", ""),
        "disposition_note": context["meta_row"].get("disposition_note", ""),
    }

    run_root = case_registry_root(context)
    aggregate_root = run_root / "aggregates"
    sqlite_path = aggregate_root / "postprocessing.sqlite"
    normalized_csv = aggregate_root / "postprocessing_case_long.csv"
    grouped_csv = aggregate_root / "wall_heat_flux_grouped.csv"
    summary_csv = aggregate_root / "case_summary.csv"

    index_row = {
        "generated_at": summary_row["generated_at"],
        "source_id": context["source_id"],
        "source_owner": context["source_owner"],
        "case_id": context["case_id"],
        "bucket": context["bucket"],
        "run_name": context["run_name"],
        "fluid": summary_row["fluid"],
        "variant_label": summary_row["variant_label"],
        "run_root": str(run_root),
        "normalized_csv": str(normalized_csv),
        "heat_grouped_csv": str(grouped_csv),
        "summary_csv": str(summary_csv),
        "sqlite_db": str(sqlite_path),
        "mdot_all_same": summary_row["mdot_all_same"],
        "mdot_consensus_kg_s": summary_row["mdot_consensus_kg_s"],
        "mdot_abs_spread_kg_s": summary_row["mdot_abs_spread_kg_s"],
        "latest_total_Q_postProc_w": summary_row["latest_total_Q_postProc_w"],
        "latest_tp_avg_k": summary_row["latest_tp_avg_k"],
        "run_status": summary_row["run_status"],
        "comparison_ready": summary_row["comparison_ready"],
    }

    manifest = {
        "generated_at": summary_row["generated_at"],
        "source_id": context["source_id"],
        "source_root": str(context["source_root"]),
        "runtime_root": str(context["runtime_root"]),
        "storage_format": "sqlite",
        "csv_outputs": {
            "normalized": str(normalized_csv),
            "wall_heat_grouped": str(grouped_csv),
            "case_summary": str(summary_csv),
        },
        "sqlite_output": str(sqlite_path),
        "row_counts": {
            "postprocessing_case_long": len(normalized_rows),
            "wall_heat_flux_grouped": len(grouped_heat_rows),
            "case_summary": 1,
        },
    }

    return {
        "context": context,
        "run_root": run_root,
        "aggregate_root": aggregate_root,
        "normalized_rows": normalized_rows,
        "grouped_heat_rows": grouped_heat_rows,
        "summary_row": summary_row,
        "index_row": index_row,
        "manifest": manifest,
    }


def write_case_aggregation(payload: dict[str, Any]) -> dict[str, str]:
    aggregate_root = ensure_dir(payload["aggregate_root"])
    run_root = ensure_dir(payload["run_root"])
    normalized_csv = aggregate_root / "postprocessing_case_long.csv"
    grouped_csv = aggregate_root / "wall_heat_flux_grouped.csv"
    summary_csv = aggregate_root / "case_summary.csv"
    summary_json = aggregate_root / "case_summary.json"
    manifest_json = run_root / "aggregation_manifest.json"
    sqlite_path = aggregate_root / "postprocessing.sqlite"

    csv_dump(normalized_csv, NORMALIZED_COLUMNS, payload["normalized_rows"])
    csv_dump(grouped_csv, WALL_HEAT_GROUPED_COLUMNS, payload["grouped_heat_rows"])
    csv_dump(summary_csv, SUMMARY_COLUMNS, [payload["summary_row"]])
    json_dump(summary_json, payload["summary_row"])
    json_dump(manifest_json, payload["manifest"])

    write_sqlite_database(
        sqlite_path,
        {
            "postprocessing_case_long": (NORMALIZED_COLUMNS, NORMALIZED_NUMERIC_COLUMNS, payload["normalized_rows"]),
            "wall_heat_flux_grouped": (WALL_HEAT_GROUPED_COLUMNS, WALL_HEAT_NUMERIC_COLUMNS, payload["grouped_heat_rows"]),
            "case_summary": (SUMMARY_COLUMNS, SUMMARY_NUMERIC_COLUMNS, [payload["summary_row"]]),
        },
    )
    return {
        "normalized_csv": str(normalized_csv),
        "grouped_csv": str(grouped_csv),
        "summary_csv": str(summary_csv),
        "summary_json": str(summary_json),
        "manifest_json": str(manifest_json),
        "sqlite_db": str(sqlite_path),
    }


def write_sqlite_database(
    path: Path,
    table_payloads: dict[str, tuple[list[str], set[str], list[dict[str, Any]]]],
) -> None:
    ensure_dir(path.parent)
    with sqlite3.connect(path) as connection:
        for table_name, (columns, numeric_columns, rows) in table_payloads.items():
            connection.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            column_defs = []
            for column in columns:
                declared = "REAL" if column in numeric_columns else "TEXT"
                column_defs.append(f'"{column}" {declared}')
            connection.execute(f'CREATE TABLE "{table_name}" ({", ".join(column_defs)})')
            if not rows:
                continue
            placeholders = ", ".join("?" for _ in columns)
            column_sql = ", ".join(f'"{column}"' for column in columns)
            values = [
                [coerce_sqlite_value(row.get(column), column in numeric_columns) for column in columns]
                for row in rows
            ]
            connection.executemany(
                f'INSERT INTO "{table_name}" ({column_sql}) VALUES ({placeholders})',
                values,
            )
        connection.commit()


def coerce_sqlite_value(value: Any, numeric: bool) -> Any:
    if value in ("", None):
        return None
    if numeric:
        numeric_value = safe_float(value)
        return float(numeric_value) if numeric_value is not None else None
    return str(value)


def upsert_index_file(path: Path, row: dict[str, Any], columns: list[str]) -> list[dict[str, Any]]:
    existing = {item["source_id"]: item for item in read_csv_rows(path) if item.get("source_id")}
    normalized = {column: row.get(column, "") for column in columns}
    existing[str(normalized["source_id"])] = normalized
    rows = sorted(existing.values(), key=lambda item: str(item["source_id"]))
    csv_dump(path, columns, rows)
    return rows


def write_index_sqlite(path: Path, rows: list[dict[str, Any]]) -> None:
    write_sqlite_database(path, {"runs": (INDEX_COLUMNS, INDEX_NUMERIC_COLUMNS, rows)})


def refresh_indexes(index_rows: Iterable[dict[str, Any]]) -> dict[str, str]:
    written: dict[str, str] = {}
    bucket_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in index_rows:
        bucket_rows[str(row["bucket"])].append(row)
        global_csv = WORKSPACE_ROOT / "registry" / "_all_postprocessing_runs.csv"
        global_rows = upsert_index_file(global_csv, row, INDEX_COLUMNS)
        global_sqlite = WORKSPACE_ROOT / "registry" / "_all_postprocessing_runs.sqlite"
        write_index_sqlite(global_sqlite, global_rows)
        written["global_csv"] = str(global_csv)
        written["global_sqlite"] = str(global_sqlite)
    for bucket, rows in bucket_rows.items():
        family_csv = WORKSPACE_ROOT / "registry" / bucket / "_family_index.csv"
        family_sqlite = WORKSPACE_ROOT / "registry" / bucket / "_family_index.sqlite"
        family_rows = read_csv_rows(family_csv)
        row_map = {item["source_id"]: item for item in family_rows if item.get("source_id")}
        for row in rows:
            row_map[str(row["source_id"])] = {column: row.get(column, "") for column in INDEX_COLUMNS}
        ordered_rows = sorted(row_map.values(), key=lambda item: str(item["source_id"]))
        csv_dump(family_csv, INDEX_COLUMNS, ordered_rows)
        write_index_sqlite(family_sqlite, ordered_rows)
        written[f"{bucket}_csv"] = str(family_csv)
        written[f"{bucket}_sqlite"] = str(family_sqlite)
    return written


def load_case_long_rows(source_id: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    context = case_context(source_id)
    csv_path = case_registry_root(context) / "aggregates" / "postprocessing_case_long.csv"
    return context, read_csv_rows(csv_path)


def load_case_velocity_profile_rows(source_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    context = case_context(source_id)
    return context, load_velocity_profile_rows_from_runtime(context)


def select_rows(
    rows: Iterable[dict[str, str]],
    *,
    dataset: str,
    value_name: str,
) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("dataset") == dataset and row.get("value_name") == value_name and row.get("time_s") not in ("", None)
    ]
