#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
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
    path_lookup,
    relative_to_workspace,
    safe_float,
)

DEFAULT_SOURCE_IDS = [
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
]

DEFAULT_CONTRACT = (
    WORKSPACE_ROOT.parent
    / "cfd-modeling-tools"
    / "cross_model_comparison"
    / "campaigns"
    / "2026-06-02_ethan_modern_runs_first_batch_v1"
    / "data"
    / "cross_model_case_contract.csv"
)
VALIDATION_CASES = (
    WORKSPACE_ROOT.parent
    / "cfd-modeling-tools"
    / "tamu_first_order_model"
    / "Fluid"
    / "results"
    / "diagnostics"
    / "validation_imposed_ethan_v2"
    / "config_used"
    / "validation_cases.csv"
)
VALIDATION_SUMMARY_ROOT = (
    WORKSPACE_ROOT.parent
    / "cfd-modeling-tools"
    / "tamu_first_order_model"
    / "Fluid"
    / "results"
    / "diagnostics"
    / "validation_imposed_ethan_v2"
    / "imposed_hx_duty"
)
WALL_PROBE_LOCATIONS = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "tp_tw_probe_locations.csv"
ACTIVE_CONTINUATION_JOBS = {
    "val_salt_test_2_coarse_mesh_laminar": "3202708",
}
ACTIVE_CONTINUATION_ROOTS = {
    "val_salt_test_2_coarse_mesh_laminar": WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "case_stage" / "val_salt_test_2_coarse_mesh_laminar_continuation",
}
WINDOW_COUNT = 50

METADATA_OUTPUT = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_case_metadata_index"
VALIDATION_OUTPUT = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_direct_validation"
DECISION_OUTPUT = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_runtime_and_hypothesis_matrix"

HEATER_PATCHES = {"pipeleg_lower_04_straight", "pipeleg_lower_05_straight", "pipeleg_lower_06_straight"}
TEST_SECTION_PATCHES = {"pipeleg_left_04_test_section"}
COOLING_BRANCH_PATCHES = {"pipeleg_upper_04_reducer", "pipeleg_upper_05_cooler", "pipeleg_upper_06_reducer"}
TP_LABELS = [f"TP{i}" for i in range(1, 7)]
TW_LABELS = [f"TW{i}" for i in range(1, 12)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the June 4 Ethan reporting package.")
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Registered source identifier. Repeat to override the default list.",
    )
    parser.add_argument(
        "--contract-csv",
        default=str(DEFAULT_CONTRACT),
        help="Published comparison contract CSV used for 1D/2D enrichment.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def maybe_float_str(value: float | None) -> str:
    return "" if value is None else str(value)


def relative_error_pct(value: float | None, target: float | None) -> float | None:
    if value is None or target in (None, 0.0):
        return None
    return abs(value - target) / abs(target) * 100.0


def signed_error(value: float | None, target: float | None) -> float | None:
    if value is None or target is None:
        return None
    return value - target


def rmse(lhs: list[float], rhs: list[float]) -> float | None:
    if not lhs or not rhs or len(lhs) != len(rhs):
        return None
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lhs, rhs)) / len(lhs))


def latest_processor_time(source_root: Path) -> str:
    candidate_roots = sorted(path for path in source_root.iterdir() if path.is_dir() and path.name.startswith("processors"))
    latest_value: float | None = None
    latest_label = ""
    for root in candidate_roots:
        times = sorted(
            child.name
            for child in root.iterdir()
            if child.is_dir() and child.name.replace(".", "", 1).isdigit()
        )
        if not times:
            continue
        current_value = float(times[-1])
        if latest_value is None or current_value > latest_value:
            latest_value = current_value
            latest_label = times[-1]
    return latest_label


def geometry_inventory(source_root: Path) -> tuple[str, int, str]:
    geometry_dir = source_root / "constant" / "geometry"
    if not geometry_dir.exists():
        return "", 0, ""
    stls = sorted(path.name for path in geometry_dir.glob("*.stl"))
    return relative_to_workspace(geometry_dir), len(stls), ";".join(stls[:8])


def case_name_from_base(base_id: str) -> str:
    fluid = "Salt" if base_id.startswith("salt") else "Water"
    number = base_id.split("_")[-1]
    return f"{fluid} {number}"


def case_dir_name_from_case_name(case_name: str) -> str:
    return case_name.replace(" ", "_")


def load_contract_maps(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    rows = load_csv_rows(path)
    by_source = {row["ethan_source_id"]: row for row in rows if row.get("ethan_source_id")}
    by_test = {row["test_id"]: row for row in rows if row.get("test_id")}
    return by_source, by_test


def load_validation_maps() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    validation_rows = {row["case_name"]: row for row in load_csv_rows(VALIDATION_CASES) if row.get("case_name")}
    summary_rows: dict[str, dict[str, str]] = {}
    for case_name in validation_rows:
        summary_path = VALIDATION_SUMMARY_ROOT / case_dir_name_from_case_name(case_name) / "summary.csv"
        rows = load_csv_rows(summary_path)
        if rows:
            summary_rows[case_name] = rows[0]
    return validation_rows, summary_rows


def load_wall_probe_order() -> list[str]:
    if not WALL_PROBE_LOCATIONS.exists():
        return []
    labels: list[str] = []
    with WALL_PROBE_LOCATIONS.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("group") == "TW":
                labels.append(row["label"])
    return labels


def parse_tp_final(source_root: Path) -> tuple[list[float], float | None]:
    payload = parse_probe_series(source_root / "postProcessing" / "temperature_probes" / "0" / "T")
    rows = payload["rows"]
    if not rows:
        return [], None
    final = rows[-1]
    return [float(value) for value in final["values"]], safe_float(final["time"])


def parse_tw_final(source_root: Path, wall_probe_order: list[str]) -> tuple[dict[str, float], float | None, int]:
    payload = parse_probe_series(source_root / "postProcessing" / "wall_temperature_probes" / "0" / "T")
    rows = payload["rows"]
    if not rows:
        return {}, None, 0
    final = rows[-1]
    values = [float(value) for value in final["values"]]
    grouped: dict[str, list[float]] = {}
    for index, value in enumerate(values):
        label = wall_probe_order[index] if index < len(wall_probe_order) else f"TW_unknown_{index}"
        station = label.split("_", 1)[0]
        grouped.setdefault(station, []).append(value)
    averaged = {station: mean(samples) for station, samples in grouped.items()}
    return averaged, safe_float(final["time"]), len(values)


def parse_mdot_summary(source_root: Path) -> dict[str, float | int | None]:
    post_root = source_root / "postProcessing"
    mdot_paths = sorted(post_root.glob("mdot_*/0/surfaceFieldValue.dat"))
    final_values: list[float] = []
    start_values: list[float] = []
    time_spans: list[float] = []
    final_time: float | None = None
    for path in mdot_paths:
        rows = parse_scalar_series(path)
        if not rows:
            continue
        final = abs(rows[-1]["value"])
        start_row = rows[-WINDOW_COUNT] if len(rows) >= WINDOW_COUNT else rows[0]
        start = abs(start_row["value"])
        final_values.append(final)
        start_values.append(start)
        time_spans.append(rows[-1]["time"] - start_row["time"])
        final_time = rows[-1]["time"] if final_time is None else max(final_time, rows[-1]["time"])
    final_mean = mean(final_values) if final_values else None
    start_mean = mean(start_values) if start_values else None
    drift_pct = None
    if final_mean not in (None, 0.0) and start_mean is not None:
        drift_pct = abs(final_mean - start_mean) / abs(final_mean) * 100.0
    return {
        "monitor_count": len(final_values),
        "final_mean_abs_kg_s": final_mean,
        "window_start_mean_abs_kg_s": start_mean,
        "late_window_drift_pct": drift_pct,
        "late_window_span_s": mean(time_spans) if time_spans else None,
        "final_time": final_time,
    }


def parse_total_q_summary(source_root: Path) -> dict[str, float | None]:
    rows = parse_scalar_series(source_root / "postProcessing" / "total_Q.dat")
    if not rows:
        return {
            "final_signed_w": None,
            "final_abs_w": None,
            "window_start_signed_w": None,
            "window_start_abs_w": None,
            "late_window_drift_abs_w": None,
            "late_window_span_s": None,
            "final_time": None,
        }
    final_signed = rows[-1]["value"]
    final = abs(final_signed)
    start_row = rows[-WINDOW_COUNT] if len(rows) >= WINDOW_COUNT else rows[0]
    start_signed = start_row["value"]
    start = abs(start_signed)
    return {
        "final_signed_w": final_signed,
        "final_abs_w": final,
        "window_start_signed_w": start_signed,
        "window_start_abs_w": start,
        "late_window_drift_abs_w": abs(final - start),
        "late_window_span_s": rows[-1]["time"] - start_row["time"],
        "final_time": rows[-1]["time"],
    }


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


def parse_wall_heatflux_summary(source_root: Path, metadata: dict[str, object]) -> dict[str, object]:
    candidates = sorted(source_root.glob("postProcessing/wallHeatFlux/*/wallHeatFlux.dat"), key=lambda item: item.parent.name)
    empty_sections = {
        "heater": 0.0,
        "test_section": 0.0,
        "cooling_branch": 0.0,
        "downcomer": 0.0,
        "upcomer": 0.0,
        "upper_transport": 0.0,
        "lower_transport": 0.0,
        "junctions": 0.0,
        "other": 0.0,
    }
    if not candidates:
        return {
            "latest_time": None,
            "patch_q_w": {},
            "section_q_w": empty_sections,
            "sim_total_wall_q_net_w": None,
            "sim_ambient_noncooling_proxy_w": None,
            "sim_ambient_proxy_w": None,
            "sim_cooling_branch_total_removal_w": None,
            "sim_cooling_branch_excess_over_operating_cooling_w": None,
        }
    rows = candidates[-1].read_text(encoding="utf-8", errors="replace").splitlines()
    latest_time: float | None = None
    latest_patch_q: dict[str, float] = {}
    for line in rows:
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
        patch = parts[1]
        if latest_time is None or time_value > latest_time:
            latest_time = time_value
            latest_patch_q = {patch: q_value}
        elif time_value == latest_time:
            latest_patch_q[patch] = q_value
    sections = dict(empty_sections)
    for patch, q_value in latest_patch_q.items():
        if patch.startswith("ncc_"):
            continue
        sections[wall_section_bucket(patch)] += q_value
    imposed_q = parse_patch_imposed_q(source_root)
    passive_ambient = 0.0
    powered_section_ambient = 0.0
    cooling_branch_total = 0.0
    for patch, q_value in latest_patch_q.items():
        if patch.startswith("ncc_"):
            continue
        if patch in COOLING_BRANCH_PATCHES and q_value < 0.0:
            cooling_branch_total += abs(q_value)
            continue
        imposed = imposed_q.get(patch)
        if imposed is not None and imposed > 0.0:
            powered_section_ambient += max(imposed - q_value, 0.0)
        elif q_value < 0.0:
            passive_ambient += abs(q_value)
    operating_cooling = safe_float(path_lookup(metadata, "operating_point.cooling_power_W")) or 0.0
    cooling_branch_excess = max(cooling_branch_total - operating_cooling, 0.0)
    ambient_proxy = passive_ambient + powered_section_ambient + cooling_branch_excess
    return {
        "latest_time": latest_time,
        "patch_q_w": latest_patch_q,
        "section_q_w": sections,
        "sim_total_wall_q_net_w": sum(latest_patch_q.values()) if latest_patch_q else None,
        "sim_ambient_noncooling_proxy_w": passive_ambient + powered_section_ambient,
        "sim_ambient_proxy_w": ambient_proxy,
        "sim_cooling_branch_total_removal_w": cooling_branch_total,
        "sim_cooling_branch_excess_over_operating_cooling_w": cooling_branch_excess,
    }


def parse_probe_trend(source_root: Path) -> dict[str, float | None]:
    payload = parse_probe_series(source_root / "postProcessing" / "temperature_probes" / "0" / "T")
    rows = payload["rows"]
    if not rows:
        return {
            "final_avg_k": None,
            "window_start_avg_k": None,
            "late_window_drift_abs_k": None,
            "late_window_span_s": None,
            "probe_count": 0,
        }
    final_values = [float(value) for value in rows[-1]["values"]]
    start_row = rows[-WINDOW_COUNT] if len(rows) >= WINDOW_COUNT else rows[0]
    start_values = [float(value) for value in start_row["values"]]
    final_avg = mean(final_values) if final_values else None
    start_avg = mean(start_values) if start_values else None
    return {
        "final_avg_k": final_avg,
        "window_start_avg_k": start_avg,
        "late_window_drift_abs_k": None if final_avg is None or start_avg is None else abs(final_avg - start_avg),
        "late_window_span_s": rows[-1]["time"] - start_row["time"],
        "probe_count": len(final_values),
    }


def parse_thermal_boundary_summary(source_root: Path) -> dict[str, object]:
    path = source_root / "0" / "T"
    if not path.exists():
        return {
            "three_d_outer_insulation_thickness_m": "",
            "three_d_outer_insulation_thickness_in": "",
            "three_d_loss_bc_summary": "boundary file unavailable",
            "three_d_radiation_summary": "boundary file unavailable",
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    layer_matches = []
    for match in __import__("re").finditer(r"thicknessLayers\s*\(([^)]+)\)", text):
        parts = [safe_float(part) for part in match.group(1).split()]
        if len(parts) >= 2 and parts[1] is not None:
            layer_matches.append(float(parts[1]))
    outer_thickness_m = layer_matches[0] if layer_matches else None
    outer_thickness_in = outer_thickness_m / 0.0254 if outer_thickness_m is not None else None
    has_rc = "rcExternalTemperature" in text
    has_ext = "externalTemperature" in text
    emissivities = sorted(set(__import__("re").findall(r"emissivity\s+([^;\s]+)", text)))
    bc_bits = []
    if has_rc:
        bc_bits.append("patchwise rcExternalTemperature layered walls")
    if has_ext:
        bc_bits.append("externalTemperature fixed-loss surrogates")
    if outer_thickness_in is not None:
        bc_bits.append(f"outer insulation layer about {outer_thickness_in:.2f} in")
    rad_summary = (
        "rcExternalTemperature uses Tsur/emissivity, so radiation-like surface exchange is encoded patchwise in the 3D wall model"
        if has_rc and emissivities
        else "no explicit rcExternalTemperature emissivity/Tsur terms were parsed from 0/T"
    )
    if emissivities:
        rad_summary += f"; parsed emissivity entries: {', '.join(emissivities)}"
    return {
        "three_d_outer_insulation_thickness_m": maybe_float_str(outer_thickness_m),
        "three_d_outer_insulation_thickness_in": maybe_float_str(outer_thickness_in),
        "three_d_loss_bc_summary": "; ".join(bc_bits) if bc_bits else "no external wall-loss patches parsed",
        "three_d_radiation_summary": rad_summary,
    }


def property_summary(metadata: dict[str, object], key: str, label: str) -> tuple[str, int]:
    if key in ("Cp_coeffs", "rho_coeffs"):
        coeffs = path_lookup(metadata, f"fluid_properties.{key}", []) or []
        count = len(coeffs)
        if key == "Cp_coeffs":
            if count and all(abs(float(value)) < 1e-12 for value in coeffs[1:]):
                return f"{label} polynomial coefficient array with only c0 active; effectively constant {coeffs[0]}", count
            return f"{label} polynomial coefficient array length {count}: {coeffs}", count
        if count and all(abs(float(value)) < 1e-12 for value in coeffs[2:]):
            return f"{label} polynomial coefficient array length {count}; first two terms active {coeffs[:2]}", count
        return f"{label} polynomial coefficient array length {count}: {coeffs}", count
    spec = path_lookup(metadata, f"fluid_properties.{key}", {}) or {}
    coeffs = spec.get("coeffs", []) or []
    spec_type = spec.get("type", "")
    count = len(coeffs)
    if spec_type == "expInvT":
        return f"{label} expInvT law A*exp(b0/T+b1/T^2+...) with coefficients {coeffs}", count
    return f"{label} {spec_type} coefficients {coeffs}", count


def mu_family_note(variant_label: str, coeff_summary: str) -> str:
    if variant_label == "jin":
        return f"Jin viscosity variant: {coeff_summary}"
    if variant_label == "kirst":
        return f"Kirst viscosity variant: {coeff_summary}"
    return coeff_summary


def fluid_case_note(source_id: str, case_id: str, all_case_rows: dict[str, dict[str, object]]) -> str:
    base_id = base_case_id(case_id)
    if source_id == "val_salt_test_2_coarse_mesh_laminar":
        return (
            "native continuation salt_test_2 case; differs from the staged viscosity-screening salt_test_2 rows by starting at T_init=451.5 K, "
            "using the Jin-style viscosity coefficients, a slightly lower cooler h, and a thicker parsed outer insulation layer"
        )
    if base_id == "salt_test_2":
        return (
            "staged viscosity-screening salt_test_2 row; compare against val_salt_test_2_coarse_mesh_laminar for the thicker-insulation native continuation case"
        )
    return ""


def load_scheduler_state(job_id: str) -> str:
    try:
        result = subprocess.run(
            ["squeue", "-j", job_id, "-h", "-o", "%T"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return "scheduler_unavailable"
    state = (result.stdout or "").strip()
    if state:
        return state
    return "not_in_queue"


def build_case_snapshot(
    source_id: str,
    contract_by_source: dict[str, dict[str, str]],
    contract_by_test: dict[str, dict[str, str]],
    validation_rows: dict[str, dict[str, str]],
    validation_summaries: dict[str, dict[str, str]],
    wall_probe_order: list[str],
) -> dict[str, object]:
    registry_row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)
    source_root = Path(registry_row["source_root"]).resolve()
    runtime_root = ACTIVE_CONTINUATION_ROOTS.get(source_id, source_root)
    metadata = load_case_metadata(runtime_root) or load_case_metadata(source_root)
    case_id = registry_row["case_id"]
    base_id = base_case_id(case_id)
    variant = case_variant_label(case_id)
    case_name = case_name_from_base(base_id)
    geometry_dir, geometry_stl_count, geometry_examples = geometry_inventory(runtime_root)
    log_path = runtime_root / "logs" / "log.foamRun_continuation"
    if not log_path.exists():
        log_path = runtime_root / "logs" / "log.foamRun"
    if not log_path.exists():
        log_path = source_root / "logs" / "log.foamRun"
    log_summary = parse_log_summary(log_path)
    contract = contract_by_source.get(source_id)
    contract_match_type = "exact_source_id"
    if contract is None:
        contract = contract_by_test.get(base_id, {})
        contract_match_type = "base_case_fallback" if contract else "unmatched"

    tp_values, tp_time = parse_tp_final(runtime_root)
    tw_values, tw_time, tw_subprobe_count = parse_tw_final(runtime_root, wall_probe_order)
    mdot_summary = parse_mdot_summary(runtime_root)
    total_q_summary = parse_total_q_summary(runtime_root)
    wall_heat_summary = parse_wall_heatflux_summary(runtime_root, metadata)
    probe_trend = parse_probe_trend(runtime_root)
    thermal_boundary = parse_thermal_boundary_summary(runtime_root)
    latest_time = max(
        [value for value in [tp_time, tw_time, safe_float(mdot_summary["final_time"]), safe_float(total_q_summary["final_time"])] if value is not None],
        default=None,
    )
    processor_time = latest_processor_time(runtime_root)
    latest_processor_time_float = safe_float(processor_time)
    qoi_gap = None
    if latest_time is not None and latest_processor_time_float is not None:
        qoi_gap = latest_processor_time_float - latest_time

    validation = validation_rows.get(case_name, {})
    validation_summary = validation_summaries.get(case_name, {})
    exp_tp_raw = [safe_float(validation.get(f"TP{i}_C")) for i in range(1, 7)]
    exp_tp_k_map = {label: value + 273.15 for label, value in zip(TP_LABELS, exp_tp_raw) if value is not None}
    exp_tp_k = [exp_tp_k_map[label] for label in TP_LABELS if label in exp_tp_k_map]
    exp_tw_k = {label: safe_float(validation.get(f"{label}_C")) for label in TW_LABELS}
    exp_tw_k = {label: value + 273.15 for label, value in exp_tw_k.items() if value is not None}
    tw_rmse_labels = [label for label in TW_LABELS if label != "TW10"]
    cfd_tw_list = [tw_values[label] for label in TW_LABELS if label in tw_values and label in exp_tw_k]
    exp_tw_list = [exp_tw_k[label] for label in TW_LABELS if label in tw_values and label in exp_tw_k]
    cfd_tw_rmse_list = [tw_values[label] for label in tw_rmse_labels if label in tw_values and label in exp_tw_k]
    exp_tw_rmse_list = [exp_tw_k[label] for label in tw_rmse_labels if label in tw_values and label in exp_tw_k]
    all_cfd = tp_values[: len(exp_tp_k)] + cfd_tw_rmse_list
    all_exp = exp_tp_k + exp_tw_rmse_list

    tp_error_map = {
        f"exp_minus_sim_{label}_K": exp_tp_k_map[label] - tp_values[index]
        for index, label in enumerate(TP_LABELS)
        if label in exp_tp_k_map and index < len(tp_values)
    }
    tw_error_map = {
        f"exp_minus_sim_{label}_K": exp_tw_k[label] - tw_values[label]
        for label in TW_LABELS
        if label in exp_tw_k and label in tw_values
    }
    tp_error_pairs = {label: tp_error_map[f"exp_minus_sim_{label}_K"] for label in TP_LABELS if f"exp_minus_sim_{label}_K" in tp_error_map}
    tw_error_pairs = {label: tw_error_map[f"exp_minus_sim_{label}_K"] for label in TW_LABELS if f"exp_minus_sim_{label}_K" in tw_error_map}
    tw_error_pairs_no_tw10 = {label: value for label, value in tw_error_pairs.items() if label != "TW10"}
    tp_max_label = max(tp_error_pairs, key=lambda item: abs(tp_error_pairs[item])) if tp_error_pairs else ""
    tw_max_label = max(tw_error_pairs_no_tw10, key=lambda item: abs(tw_error_pairs_no_tw10[item])) if tw_error_pairs_no_tw10 else ""
    tw_top3 = sorted(tw_error_pairs_no_tw10.items(), key=lambda item: abs(item[1]), reverse=True)[:3]

    exp_mdot = safe_float(validation.get("measured_mass_flow_rate_kg_s"))
    exp_qambient = safe_float(validation_summary.get("qambient_total_W"))
    exp_qhx = safe_float(validation_summary.get("qhx_total_W"))
    sim_mdot = safe_float(mdot_summary["final_mean_abs_kg_s"])
    sim_ambient_proxy = safe_float(wall_heat_summary["sim_ambient_proxy_w"])
    q_reference_status = "ethan_prescribed_segment_loss_proxy_from_validation_imposed_ethan_v2_qambient_total_W" if exp_qambient is not None else "reference_missing"
    section_q = wall_heat_summary["section_q_w"]
    validation_metrics = {
        "exp_case_name": case_name if validation else "",
        "exp_reference_status": "available" if validation else "reference_missing",
        "exp_tp_rmse_k": rmse(tp_values[: len(exp_tp_k)], exp_tp_k) if tp_values and exp_tp_k and len(tp_values) >= len(exp_tp_k) else None,
        "exp_tw_rmse_k": rmse(cfd_tw_rmse_list, exp_tw_rmse_list) if cfd_tw_rmse_list and exp_tw_rmse_list else None,
        "exp_all_temp_rmse_k": rmse(all_cfd, all_exp) if all_cfd and all_exp and len(all_cfd) == len(all_exp) else None,
        "exp_mdot_abs_error_pct": relative_error_pct(sim_mdot, exp_mdot),
        "exp_q_external_loss_abs_error_pct": relative_error_pct(sim_ambient_proxy, exp_qambient),
        "exp_q_external_loss_reference_w": exp_qambient,
        "exp_qhx_reference_w": exp_qhx,
        "exp_q_external_loss_reference_status": q_reference_status,
        "exp_tp_sensor_count": len(exp_tp_k),
        "exp_tw_sensor_count": len(exp_tw_rmse_list),
        "tw10_excluded_from_rmse": True,
        "tw10_raw_error_k": tw_error_pairs.get("TW10"),
        "exp_tw_subprobe_count": tw_subprobe_count,
        "sim_mdot_kg_s": sim_mdot,
        "exp_mdot_kg_s": exp_mdot,
        "exp_minus_sim_mdot_kg_s": None if exp_mdot is None or sim_mdot is None else exp_mdot - sim_mdot,
        "sim_total_wall_q_net_w": safe_float(wall_heat_summary["sim_total_wall_q_net_w"]),
        "sim_ambient_proxy_w": sim_ambient_proxy,
        "sim_ambient_noncooling_proxy_w": safe_float(wall_heat_summary["sim_ambient_noncooling_proxy_w"]),
        "sim_cooling_branch_total_removal_w": safe_float(wall_heat_summary["sim_cooling_branch_total_removal_w"]),
        "sim_cooling_branch_excess_over_operating_cooling_w": safe_float(wall_heat_summary["sim_cooling_branch_excess_over_operating_cooling_w"]),
        "sim_section_downcomer_net_q_w": section_q["downcomer"],
        "sim_section_heater_net_q_w": section_q["heater"],
        "sim_section_upcomer_net_q_w": section_q["upcomer"],
        "sim_section_test_section_net_q_w": section_q["test_section"],
        "sim_section_cooling_branch_net_q_w": section_q["cooling_branch"],
        "sim_section_upper_transport_net_q_w": section_q["upper_transport"],
        "sim_section_lower_transport_net_q_w": section_q["lower_transport"],
        "sim_section_junctions_net_q_w": section_q["junctions"],
        "sim_section_other_net_q_w": section_q["other"],
        "tp_max_abs_error_label": tp_max_label,
        "tp_max_abs_error_k": abs(tp_error_pairs[tp_max_label]) if tp_max_label else None,
        "tw_max_abs_error_label": tw_max_label,
        "tw_max_abs_error_k": abs(tw_error_pairs[tw_max_label]) if tw_max_label else None,
        "tw_top3_abs_error_summary": "; ".join(f"{label}:{value:.3f}" for label, value in tw_top3),
        **tp_error_map,
        **tw_error_map,
    }

    active_job_id = ACTIVE_CONTINUATION_JOBS.get(source_id, "")
    scheduler_state = load_scheduler_state(active_job_id) if active_job_id else ""
    if scheduler_state == "RUNNING":
        runtime_status = "running"
        termination_reason = "active continuation in queue"
    else:
        runtime_status = log_summary.get("status", "unknown")
        termination_reason = log_summary.get("termination_reason", "")

    convergence = log_summary.get("convergence", {})
    convergence_reached = convergence.get("reached", False)
    convergence_provenance = "solver_log"
    if active_job_id and scheduler_state == "RUNNING":
        convergence_provenance = (
            "older solver log plus live continuation state; final QoI extraction predates current processor writes"
            if qoi_gap is not None and qoi_gap > 1.0
            else "older solver log plus live continuation state"
        )

    mu_summary, mu_coeff_count = property_summary(metadata, "mu_spec", "mu")
    kappa_summary, kappa_coeff_count = property_summary(metadata, "kappa_spec", "kappa")
    cp_summary, cp_coeff_count = property_summary(metadata, "Cp_coeffs", "Cp")
    rho_summary, rho_coeff_count = property_summary(metadata, "rho_coeffs", "rho")

    loss_setup_summary = (
        f"3D wall-loss treatment is patchwise: {thermal_boundary['three_d_loss_bc_summary']}. "
        f"Zone-level bc_params are heater h={path_lookup(metadata, 'bc_params.heater.h', '')}, cooler h={path_lookup(metadata, 'bc_params.cooler.h', '')}, "
        f"test-section h={path_lookup(metadata, 'bc_params.test_section.h', '')}, insulated-region h={path_lookup(metadata, 'bc_params.insulated.h', '')}."
    )
    friction_treatment_summary = (
        "3D CFD resolves viscous and pressure losses directly from the Navier-Stokes solution; no separate Darcy friction-factor input is carried in case_config. "
        "Blank two_d_friction_factor_* fields in the contract mean the reduced comparison table did not publish those derived factors, not that 3D friction is zero."
    )
    comparison_note = (
        "two_d_* and one_d_stage* columns are comparison-contract enrichment fields from the cross-model publication table; they describe 2D/1D reference scenarios, not native 3D solver switches."
    )
    assumption_note = (
        f"{path_lookup(metadata, 'fluid', '')} / {path_lookup(metadata, 'turbulence_model', '')} case. "
        f"{loss_setup_summary} {thermal_boundary['three_d_radiation_summary']}. "
        f"{mu_family_note(variant, mu_summary)}. {cp_summary}. {rho_summary}. {friction_treatment_summary} {comparison_note}"
    )

    return {
        "source_id": source_id,
        "case_id": case_id,
        "base_case_id": base_id,
        "variant_label": variant,
        "source_owner": registry_row["source_owner"],
        "source_root": str(source_root),
        "active_runtime_root": str(runtime_root),
        "fluid": path_lookup(metadata, "fluid", ""),
        "turbulence_model": path_lookup(metadata, "turbulence_model", ""),
        "heater_power_W": path_lookup(metadata, "operating_point.heater_power_W", ""),
        "cooling_power_W": path_lookup(metadata, "operating_point.cooling_power_W", ""),
        "T_init_K": path_lookup(metadata, "operating_point.T_init_K", ""),
        "nprocs": path_lookup(metadata, "nprocs", ""),
        "scale_to_meters": path_lookup(metadata, "scale_to_meters", ""),
        "mesh_group_id": path_lookup(metadata, "mesh_group_id", ""),
        "ncc_couples": path_lookup(metadata, "ncc_couples", ""),
        "geometry_dir": geometry_dir,
        "geometry_stl_count": geometry_stl_count,
        "geometry_stl_examples": geometry_examples,
        "heater_h_W_m2K": path_lookup(metadata, "bc_params.heater.h", ""),
        "heater_Ta_K": path_lookup(metadata, "bc_params.heater.Ta", ""),
        "heater_emissivity": path_lookup(metadata, "bc_params.heater.emissivity", ""),
        "cooler_h_W_m2K": path_lookup(metadata, "bc_params.cooler.h", ""),
        "cooler_Ta_K": path_lookup(metadata, "bc_params.cooler.Ta", ""),
        "test_section_h_W_m2K": path_lookup(metadata, "bc_params.test_section.h", ""),
        "test_section_Ta_K": path_lookup(metadata, "bc_params.test_section.Ta", ""),
        "insulated_h_W_m2K": path_lookup(metadata, "bc_params.insulated.h", ""),
        "insulated_Ta_K": path_lookup(metadata, "bc_params.insulated.Ta", ""),
        "three_d_outer_insulation_thickness_m": thermal_boundary["three_d_outer_insulation_thickness_m"],
        "three_d_outer_insulation_thickness_in": thermal_boundary["three_d_outer_insulation_thickness_in"],
        "three_d_loss_bc_summary": thermal_boundary["three_d_loss_bc_summary"],
        "three_d_radiation_summary": thermal_boundary["three_d_radiation_summary"],
        "mesh_kernel_factor": path_lookup(metadata, "mesh_settings.kernel_factor", ""),
        "mesh_kernel_blend": path_lookup(metadata, "mesh_settings.kernel_blend", ""),
        "mesh_core_ratio": path_lookup(metadata, "mesh_settings.core_ratio", ""),
        "inflation_first_cell_size": path_lookup(metadata, "mesh_settings.inflation.first_cell_size", ""),
        "inflation_bulk_cell_size": path_lookup(metadata, "mesh_settings.inflation.bulk_cell_size", ""),
        "inflation_c2c_expansion": path_lookup(metadata, "mesh_settings.inflation.c2c_expansion", ""),
        "convergence_enabled": path_lookup(metadata, "convergence.enabled", ""),
        "convergence_check_interval": path_lookup(metadata, "convergence.check_interval", ""),
        "convergence_min_iterations": path_lookup(metadata, "convergence.min_iterations", ""),
        "convergence_qoi_rtol": path_lookup(metadata, "convergence.qoi.rtol", ""),
        "convergence_qoi_window": path_lookup(metadata, "convergence.qoi.window", ""),
        "mu_spec_type": path_lookup(metadata, "fluid_properties.mu_spec.type", ""),
        "mu_coeff_count": mu_coeff_count,
        "mu_coeff_summary": mu_family_note(variant, mu_summary),
        "kappa_spec_type": path_lookup(metadata, "fluid_properties.kappa_spec.type", ""),
        "kappa_coeff_count": kappa_coeff_count,
        "kappa_coeff_summary": kappa_summary,
        "cp_coeff_count": cp_coeff_count,
        "cp_model_summary": cp_summary,
        "rho_coeff_count": rho_coeff_count,
        "rho_model_summary": rho_summary,
        "walltime": path_lookup(metadata, "walltime", ""),
        "run_status": runtime_status,
        "run_termination_reason": termination_reason,
        "final_time": maybe_float_str(latest_time),
        "latest_processor_time": processor_time,
        "qoi_vs_processor_time_gap_s": maybe_float_str(qoi_gap),
        "convergence_reached": convergence_reached,
        "convergence_iteration": convergence.get("iteration", ""),
        "convergence_dTsigma": convergence.get("dTsigma", ""),
        "convergence_tol": convergence.get("tol", ""),
        "convergence_status_provenance": convergence_provenance,
        "continuation_job_id": active_job_id,
        "continuation_scheduler_state": scheduler_state,
        "mdot_mean_abs_kg_s": maybe_float_str(safe_float(mdot_summary["final_mean_abs_kg_s"])),
        "final_total_wall_heat_abs_w": maybe_float_str(safe_float(total_q_summary["final_abs_w"])),
        "sim_total_wall_q_net_w": maybe_float_str(safe_float(wall_heat_summary["sim_total_wall_q_net_w"])),
        "sim_ambient_proxy_w": maybe_float_str(sim_ambient_proxy),
        "probe_T_avg_K": maybe_float_str(safe_float(probe_trend["final_avg_k"])),
        "two_d_ins_s1_thickness_in": contract.get("two_d_ins_s1_thickness_in", ""),
        "two_d_ins_s2_thickness_in": contract.get("two_d_ins_s2_thickness_in", ""),
        "two_d_radiation_on": contract.get("two_d_radiation_on", ""),
        "one_d_stage1_scenario": contract.get("one_d_stage1_scenario", ""),
        "one_d_stage1_insulation_thickness_in": contract.get("one_d_stage1_insulation_thickness_in", ""),
        "one_d_stage1_radiation_on": contract.get("one_d_stage1_radiation_on", ""),
        "one_d_stage2_source_available": contract.get("one_d_stage2_source_available", ""),
        "one_d_stage2_scenario": contract.get("one_d_stage2_scenario", ""),
        "comparison_contract_match_type": contract_match_type,
        "comparison_ready": contract.get("comparison_ready", ""),
        "disposition_note": contract.get("disposition_note", ""),
        "exp_case_name": validation_metrics["exp_case_name"],
        "exp_reference_status": validation_metrics["exp_reference_status"],
        "exp_tp_rmse_k": maybe_float_str(validation_metrics["exp_tp_rmse_k"]),
        "exp_tw_rmse_k": maybe_float_str(validation_metrics["exp_tw_rmse_k"]),
        "exp_all_temp_rmse_k": maybe_float_str(validation_metrics["exp_all_temp_rmse_k"]),
        "exp_mdot_abs_error_pct": maybe_float_str(validation_metrics["exp_mdot_abs_error_pct"]),
        "exp_q_external_loss_reference_w": maybe_float_str(validation_metrics["exp_q_external_loss_reference_w"]),
        "exp_q_external_loss_reference_status": validation_metrics["exp_q_external_loss_reference_status"],
        "exp_q_external_loss_abs_error_pct": maybe_float_str(validation_metrics["exp_q_external_loss_abs_error_pct"]),
        "loss_setup_summary": loss_setup_summary,
        "friction_treatment_summary": friction_treatment_summary,
        "base_case_family_note": fluid_case_note(source_id, case_id, {}),
        "assumption_note": assumption_note,
        "validation_metrics": validation_metrics,
        "probe_trend": probe_trend,
        "mdot_summary": mdot_summary,
        "total_q_summary": total_q_summary,
    }


def build_decision_row(case: dict[str, object]) -> dict[str, object]:
    source_id = str(case["source_id"])
    convergence_reached = case["convergence_reached"] is True
    mdot_drift_pct = safe_float(case["mdot_summary"].get("late_window_drift_pct"))
    probe_drift_k = safe_float(case["probe_trend"].get("late_window_drift_abs_k"))
    q_drift_w = safe_float(case["total_q_summary"].get("late_window_drift_abs_w"))
    mdot_err_pct = safe_float(case.get("exp_mdot_abs_error_pct"))
    q_err_pct = safe_float(case.get("exp_q_external_loss_abs_error_pct"))
    final_time = safe_float(case.get("final_time"))
    scheduler_state = str(case.get("continuation_scheduler_state", ""))

    steadyish = (
        mdot_drift_pct is not None and mdot_drift_pct <= 5.0 and
        probe_drift_k is not None and probe_drift_k <= 1.0 and
        q_drift_w is not None and q_drift_w <= 5.0
    )
    strong_physics_mismatch = (
        (q_err_pct is not None and q_err_pct >= 50.0) or
        (mdot_err_pct is not None and mdot_err_pct >= 20.0)
    )

    if source_id == "val_salt_test_2_coarse_mesh_laminar" and scheduler_state == "RUNNING":
        decision = "continue_now"
        reason = "active continuation is still running and this row is the only already-justified extension target"
    elif convergence_reached:
        decision = "alternate_case_first" if strong_physics_mismatch else "analyze_as_steady_state"
        reason = (
            "converged but still misses validation materially, so more runtime is unlikely to fix the dominant error"
            if decision == "alternate_case_first"
            else "converged and suitable for steady-state analysis"
        )
    elif str(case.get("fluid", "")).startswith("water"):
        decision = "analyze_as_diagnostic_only"
        reason = "water rows remain useful for trend inspection, but are not yet strong continuation candidates"
    elif steadyish and strong_physics_mismatch:
        decision = "alternate_case_first"
        reason = "late-window trends are already relatively flat while validation mismatch is still large, which points to setup assumptions rather than runtime"
    elif final_time is not None and final_time < 1500.0:
        decision = "continue_now"
        reason = "runtime ended early enough that additional evolution could still change the interpretation"
    else:
        decision = "analyze_as_diagnostic_only"
        reason = "non-converged row is analyzable for behavior/trends, but a blanket rerun is not justified by the current evidence"

    return {
        "source_id": source_id,
        "case_id": case["case_id"],
        "base_case_id": case["base_case_id"],
        "variant_label": case["variant_label"],
        "run_status": case["run_status"],
        "convergence_reached": case["convergence_reached"],
        "final_time": case["final_time"],
        "latest_processor_time": case["latest_processor_time"],
        "mdot_late_window_drift_pct": maybe_float_str(mdot_drift_pct),
        "probe_late_window_drift_abs_k": maybe_float_str(probe_drift_k),
        "wall_heat_late_window_drift_abs_w": maybe_float_str(q_drift_w),
        "exp_mdot_abs_error_pct": case["exp_mdot_abs_error_pct"],
        "exp_q_external_loss_abs_error_pct": case["exp_q_external_loss_abs_error_pct"],
        "exp_all_temp_rmse_k": case["exp_all_temp_rmse_k"],
        "decision": decision,
        "decision_reason": reason,
        "submission_note": (
            "If a rerun is submitted, default to 64 ranks and pack 3 runs per 256-core node before attempting 4-up packing."
            if decision == "continue_now"
            else "No immediate continuation submission recommended."
        ),
    }


def build_hypothesis_row(case: dict[str, object], decision_row: dict[str, object]) -> dict[str, object]:
    q_err_pct = safe_float(case.get("exp_q_external_loss_abs_error_pct"))
    mdot_err_pct = safe_float(case.get("exp_mdot_abs_error_pct"))
    one_d_stage2 = str(case.get("one_d_stage2_scenario", ""))
    two_d_rad = str(case.get("two_d_radiation_on", ""))
    if q_err_pct is not None and q_err_pct >= 50.0:
        if "rad_1" in one_d_stage2 or two_d_rad == "False":
            primary = "3D wall-loss treatment is too weak relative to the Ethan-linked reference losses"
            next_case = "radiation_on_sensitivity"
            insulation = "do_not_thicken_first"
            note = "Thicker insulation would likely reduce external loss further; check radiation-on and wall-loss calibration first."
        else:
            primary = "external heat-loss boundary treatment is underpowered even without an obvious stage-metadata radiation mismatch"
            next_case = "revisit_patchwise_h_and_loss_surrogates"
            insulation = "do_not_thicken_first"
            note = "Loss mismatch is too large to justify thicker insulation as the first alternate."
    elif mdot_err_pct is not None and mdot_err_pct >= 15.0:
        primary = "flow resistance and wall-loss coupling likely need revision"
        next_case = "revisit_property_and_loss_coupling"
        insulation = "hold"
        note = "Low flow with poor validation alignment is more likely a coupled physics/setup issue than a runtime-only issue."
    else:
        primary = "no strong alternate-case inference yet"
        next_case = "analyze_time_histories_first"
        insulation = "hold"
        note = "Use the time-series diagnostics before changing assumptions."
    return {
        "source_id": case["source_id"],
        "case_id": case["case_id"],
        "decision": decision_row["decision"],
        "primary_hypothesis": primary,
        "recommended_next_case": next_case,
        "insulation_direction": insulation,
        "notes": note,
    }


def write_validation_outputs(rows: list[dict[str, object]]) -> None:
    ensure_dir(VALIDATION_OUTPUT)
    base_fields = [
        "source_id",
        "case_id",
        "base_case_id",
        "variant_label",
        "fluid",
        "run_status",
        "convergence_reached",
        "final_time",
        "exp_case_name",
        "exp_reference_status",
        "exp_tp_rmse_k",
        "exp_tw_rmse_k",
        "exp_all_temp_rmse_k",
        "tw10_excluded_from_rmse",
        "tw10_raw_error_k",
        "exp_mdot_abs_error_pct",
        "sim_mdot_kg_s",
        "exp_mdot_kg_s",
        "sim_total_wall_q_net_w",
        "sim_ambient_noncooling_proxy_w",
        "sim_ambient_proxy_w",
        "sim_cooling_branch_total_removal_w",
        "sim_cooling_branch_excess_over_operating_cooling_w",
        "exp_qhx_reference_w",
        "exp_q_external_loss_reference_w",
        "exp_q_external_loss_reference_status",
        "exp_q_external_loss_abs_error_pct",
        "tp_max_abs_error_label",
        "tp_max_abs_error_k",
        "tw_max_abs_error_label",
        "tw_max_abs_error_k",
        "tw_top3_abs_error_summary",
        "sim_section_downcomer_net_q_w",
        "sim_section_heater_net_q_w",
        "sim_section_upcomer_net_q_w",
        "sim_section_test_section_net_q_w",
        "sim_section_cooling_branch_net_q_w",
        "sim_section_upper_transport_net_q_w",
        "sim_section_lower_transport_net_q_w",
        "sim_section_junctions_net_q_w",
        "sim_section_other_net_q_w",
    ]
    error_fields = [f"exp_minus_sim_{label}_K" for label in TP_LABELS + TW_LABELS] + ["exp_minus_sim_mdot_kg_s"]
    fieldnames = base_fields + error_fields
    report_rows = []
    for row in rows:
        validation_metrics = row.get("validation_metrics", {})
        report_row = {key: validation_metrics.get(key, row.get(key, "")) for key in fieldnames}
        report_rows.append(report_row)
        json_dump(
            WORKSPACE_ROOT / "work_products" / str(row["source_id"]) / "direct_validation_summary.json",
            {
                "generated_at": iso_timestamp(),
                **report_row,
            },
        )
    csv_dump(VALIDATION_OUTPUT / "ethan_direct_validation_metrics.csv", fieldnames, report_rows)
    json_dump(VALIDATION_OUTPUT / "ethan_direct_validation_metrics.json", {"generated_at": iso_timestamp(), "rows": report_rows})
    readme = "\n".join(
        [
            "# Ethan Direct Validation Metrics",
            "",
            "This report compares the 3D CFD rows directly against the Ethan-linked validation data and also carries raw channel errors plus a derived section heat-transfer breakdown.",
            "",
            "## Metrics",
            "",
            "- `exp_tp_rmse_k`: RMSE between CFD `TP1..TP6` and measured bulk temperature probes.",
            "- `exp_tw_rmse_k`: RMSE between CFD wall-temperature stations and measured wall temperatures after averaging the 4 CFD azimuthal wall probes at each station, with `TW10` explicitly excluded from the RMSE calculation.",
            "- `exp_all_temp_rmse_k`: RMSE across `TP1..TP6` plus wall stations excluding `TW10`; `TW10` is intentionally omitted from this combined RMSE.",
            "- `tw10_excluded_from_rmse`: explicit boolean flag showing that `TW10` was excluded from the RMSE-based wall metrics.",
            "- `tw10_raw_error_k`: raw signed `experiment - simulation` error for `TW10`, retained for transparency even though it is excluded from RMSE.",
            "- `sim_mdot_kg_s`, `exp_mdot_kg_s`, and `exp_minus_sim_mdot_kg_s`: side-by-side CFD and experimental flow values with signed `experiment - simulation` error.",
            "- `sim_total_wall_q_net_w`: signed net wall heat transfer from the saved `wallHeatFlux` patch totals; this is not a pure ambient-loss quantity.",
            "- `sim_ambient_noncooling_proxy_w`: derived proxy for ambient losses outside the cooling branch, built from patchwise `wallHeatFlux` plus imposed positive-power patches.",
            "- `sim_ambient_proxy_w`: derived proxy for total ambient-like loss, equal to `sim_ambient_noncooling_proxy_w` plus cooling-branch removal beyond the operating-point cooling duty.",
            "- `sim_cooling_branch_total_removal_w`: total magnitude of removal through `pipeleg_upper_04_reducer`, `pipeleg_upper_05_cooler`, and `pipeleg_upper_06_reducer` from `wallHeatFlux.dat`.",
            "- `exp_qhx_reference_w`: Ethan-linked HX-duty reference (`qhx_total_W`) from the validation-imposed campaign summary.",
            "- `exp_q_external_loss_reference_w`: Ethan-linked ambient-loss reference (`qambient_total_W`) from the validation-imposed campaign summary.",
            "- `exp_q_external_loss_abs_error_pct`: absolute percent error between `sim_ambient_proxy_w` and the Ethan-linked `qambient_total_W` reference.",
            "- `sim_section_*_net_q_w`: signed section totals derived from `postProcessing/wallHeatFlux/1/wallHeatFlux.dat` using patch-name aggregation.",
            "- final `exp_minus_sim_*` columns: signed channel-level errors (`experiment - simulation`) for all TP, TW, and mdot channels. `TW10` remains present here even though it is excluded from RMSE.",
            "",
            "## Ethan-linked external-loss proxy",
            "",
            "- The phrase `Ethan-linked external-loss proxy` refers to `qambient_total_W` from `validation_imposed_ethan_v2/imposed_hx_duty/<Case>/summary.csv`.",
            "- That quantity is not a single raw column from the original validation table. It comes from the Ethan-prescribed segment-loss reconstruction used by the first-order validation-imposed campaign.",
            "- It is still the most coherent current reference for total ambient loss, but it should be read as an Ethan-linked reconstructed target rather than a directly measured one-line ambient-loss measurement.",
            "",
            "## Important note",
            "",
            "- Temperature and mass-flow metrics are direct CFD-vs-measurement comparisons.",
            "- The heat-loss comparison is now based on a derived 3D ambient-loss proxy from `wallHeatFlux.dat`, not on the older net `total_Q` value.",
            "",
        ]
    )
    (VALIDATION_OUTPUT / "README.md").write_text(readme, encoding="utf-8")


def write_metadata_outputs(rows: list[dict[str, object]], contract_path: Path) -> None:
    ensure_dir(METADATA_OUTPUT)
    excluded = {"validation_metrics", "probe_trend", "mdot_summary", "total_q_summary"}
    fieldnames = [key for key in rows[0].keys() if key not in excluded]
    csv_rows = [{key: row.get(key, "") for key in fieldnames} for row in rows]
    csv_dump(METADATA_OUTPUT / "ethan_case_metadata_index.csv", fieldnames, csv_rows)
    json_dump(METADATA_OUTPUT / "ethan_case_metadata_index.json", {"generated_at": iso_timestamp(), "rows": csv_rows})

    glossary = {
        "source_id": "registered local source identifier for the imported or staged 3D CFD case",
        "case_id": "case identifier from case_config; includes variant suffixes like `_jin` or `_kirst` when present",
        "base_case_id": "base test family identifier with Jin/Kirst suffix removed; for example `salt_test_2`",
        "variant_label": "property-model branch label extracted from the case ID; blank means no Jin/Kirst split",
        "source_owner": "provenance owner from the local registry",
        "source_root": "absolute path to the native staged source tree; native solver outputs were not mutated",
        "active_runtime_root": "runtime tree actually inspected for current postProcessing, logs, and processor writes; differs from source_root for the active salt2 continuation",
        "fluid": "working-fluid label from case_config",
        "turbulence_model": "OpenFOAM flow model label from case_config",
        "heater_power_W": "imposed heater power in watts from the operating point",
        "cooling_power_W": "target HX/cooler duty in watts from the operating point",
        "T_init_K": "initial fluid temperature in kelvin",
        "nprocs": "MPI rank count configured for the original case",
        "scale_to_meters": "geometry scaling factor from model units to meters",
        "mesh_group_id": "mesh fingerprint/group identifier used to tie related cases together",
        "ncc_couples": "count of non-conformal coupling interfaces in the case",
        "geometry_dir": "geometry directory relative to the workspace when possible",
        "geometry_stl_count": "number of STL geometry files present under `constant/geometry`",
        "geometry_stl_examples": "up to 8 example STL filenames",
        "heater_h_W_m2K": "nominal heater-side external transfer coefficient in case_config bc_params",
        "heater_Ta_K": "heater-side ambient reference temperature in kelvin from case_config bc_params",
        "heater_emissivity": "heater emissivity value carried in case_config bc_params",
        "cooler_h_W_m2K": "nominal cooler-side external transfer coefficient in case_config bc_params",
        "cooler_Ta_K": "cooler-side ambient reference temperature in kelvin from case_config bc_params",
        "test_section_h_W_m2K": "nominal test-section external transfer coefficient in case_config bc_params",
        "test_section_Ta_K": "test-section ambient reference temperature in kelvin from case_config bc_params",
        "insulated_h_W_m2K": "nominal insulated-region external transfer coefficient in case_config bc_params",
        "insulated_Ta_K": "insulated-region ambient reference temperature in kelvin from case_config bc_params",
        "three_d_outer_insulation_thickness_m": "outer insulation-layer thickness parsed from the first layered `rcExternalTemperature` entry in `0/T`",
        "three_d_outer_insulation_thickness_in": "same parsed outer insulation thickness converted to inches; this fills the missing salt2 native-case insulation context",
        "three_d_loss_bc_summary": "plain-language summary of how the 3D case treats wall losses in `0/T`",
        "three_d_radiation_summary": "plain-language summary of how radiation-like exchange appears in the 3D wall boundary condition file",
        "mesh_kernel_factor": "mesh-generation kernel factor from case_config",
        "mesh_kernel_blend": "mesh-generation kernel blend from case_config",
        "mesh_core_ratio": "mesh core-ratio control from case_config",
        "inflation_first_cell_size": "first wall-adjacent inflation cell size from case_config",
        "inflation_bulk_cell_size": "bulk inflation cell size from case_config",
        "inflation_c2c_expansion": "cell-to-cell inflation expansion ratio from case_config",
        "convergence_enabled": "whether the coded convergence monitor was enabled",
        "convergence_check_interval": "iteration interval between convergence checks",
        "convergence_min_iterations": "minimum iteration count before convergence checks activate",
        "convergence_qoi_rtol": "relative tolerance used by the coded convergence monitor",
        "convergence_qoi_window": "window length used by the coded convergence monitor",
        "mu_spec_type": "viscosity model family name from case_config; `expInvT` means `A*exp(b0/T+b1/T^2+...)`",
        "mu_coeff_count": "number of viscosity coefficients in the chosen model",
        "mu_coeff_summary": "human-readable viscosity-model summary; this distinguishes the Jin and Kirst coefficient sets even though both use `expInvT`",
        "kappa_spec_type": "thermal-conductivity model family name from case_config",
        "kappa_coeff_count": "number of thermal-conductivity coefficients",
        "kappa_coeff_summary": "human-readable conductivity-model summary",
        "cp_coeff_count": "length of the `Cp_coeffs` array in case_config; it is a coefficient-array length, not a count of physical Cp components",
        "cp_model_summary": "human-readable Cp model summary; for the salt cases this shows the array is effectively constant Cp with only the c0 term active",
        "rho_coeff_count": "length of the `rho_coeffs` array in case_config; again this is a coefficient-array length, not a physical component count",
        "rho_model_summary": "human-readable density-model summary",
        "walltime": "requested walltime string in case_config",
        "run_status": "best current runtime state; uses live scheduler state for the active salt2 continuation when available",
        "run_termination_reason": "reason parsed from the solver log or set from live continuation context",
        "final_time": "latest physical time observed across the extracted postProcessing files",
        "latest_processor_time": "latest numeric processor-write directory seen under `processors*`",
        "qoi_vs_processor_time_gap_s": "latest processor time minus latest extracted postProcessing time; positive values signal that the QoI products lag behind newer writes",
        "convergence_reached": "whether the coded convergence monitor explicitly reported convergence in the parsed solver log",
        "convergence_iteration": "iteration where the coded convergence monitor declared convergence",
        "convergence_dTsigma": "temperature-spread convergence metric from the coded convergence monitor",
        "convergence_tol": "coded convergence tolerance from the solver log summary",
        "convergence_status_provenance": "explains whether convergence status came purely from the old solver log or from that log plus an active continuation context",
        "continuation_job_id": "active continuation job ID when this row is being tracked as a live continuation",
        "continuation_scheduler_state": "live scheduler state from `squeue` for the active continuation job when available",
        "mdot_mean_abs_kg_s": "mean absolute mass flow from the four monitored faceZones at the latest extracted time",
        "final_total_wall_heat_abs_w": "absolute value of the final `postProcessing/total_Q.dat` sample; this is the magnitude of the net all-wall heat-transfer sum, not a pure ambient-loss quantity",
        "sim_total_wall_q_net_w": "signed total wall heat transfer reconstructed from the latest `wallHeatFlux.dat` patch totals",
        "sim_ambient_proxy_w": "derived ambient-loss proxy from `wallHeatFlux.dat`, built from passive losses plus powered-section deficits and cooling-branch excess beyond the operating-point cooling duty",
        "probe_T_avg_K": "average of the latest `TP1..TP6` CFD probe temperatures in kelvin",
        "two_d_ins_s1_thickness_in": "2D comparison-contract insulation thickness for section 1 in inches; this is a 2D reference-scenario field, not a native 3D input",
        "two_d_ins_s2_thickness_in": "2D comparison-contract insulation thickness for section 2 in inches; again a 2D reference-scenario field",
        "two_d_radiation_on": "2D comparison-contract radiation flag; this does not by itself prove the 3D case had radiation on or off",
        "one_d_stage1_scenario": "name of the first-order-model stage-1 scenario from the cross-model comparison contract",
        "one_d_stage1_insulation_thickness_in": "stage-1 first-order-model insulation thickness in inches from the comparison contract",
        "one_d_stage1_radiation_on": "stage-1 first-order-model radiation flag from the comparison contract",
        "one_d_stage2_source_available": "whether the comparison contract published a stage-2 first-order-model source row",
        "one_d_stage2_scenario": "name of the first-order-model stage-2 scenario from the comparison contract",
        "comparison_contract_match_type": "how this metadata row was enriched from the comparison contract: exact source match, base-case fallback, or unmatched",
        "comparison_ready": "comparison-disposition label from the published comparison contract",
        "disposition_note": "published comparison-contract note about whether the row was considered ready for validation comparison",
        "exp_case_name": "linked experimental validation case name used by the direct CFD-vs-experiment report",
        "exp_reference_status": "whether a direct validation row was found for this case",
        "exp_tp_rmse_k": "direct CFD-vs-experiment RMSE for the bulk-fluid temperature probes TP1..TP6",
        "exp_tw_rmse_k": "direct CFD-vs-experiment RMSE for wall-temperature stations after averaging the 4 CFD wall subprobes per station, with TW10 explicitly excluded",
        "exp_all_temp_rmse_k": "direct CFD-vs-experiment RMSE across TP1..TP6 plus wall stations excluding TW10",
        "exp_mdot_abs_error_pct": "direct absolute percent mass-flow error against the experimental measured mass flow rate",
        "exp_q_external_loss_reference_w": "Ethan-linked external-loss proxy used for comparison; drawn from `validation_imposed_ethan_v2` `qambient_total_W`",
        "exp_q_external_loss_reference_status": "documents that the external-loss reference is an Ethan-prescribed-segment-loss proxy rather than a single direct measured column in the validation table",
        "exp_q_external_loss_abs_error_pct": "absolute percent error between CFD wall heat loss and the Ethan-linked external-loss proxy",
        "loss_setup_summary": "plain-language note on how heat-transfer coefficients are treated in the 3D setup",
        "friction_treatment_summary": "plain-language note on how friction is treated in the 3D CFD and how blank reduced friction columns should be interpreted",
        "base_case_family_note": "case-family note used to explain special relationships such as `val_salt_test_2` versus the viscosity-screening salt2 rows",
        "assumption_note": "full setup note combining wall-loss treatment, radiation treatment, property models, and friction interpretation",
    }

    lines = [
        "# Ethan Case Metadata Index",
        "",
        "This is the June 4 expanded metadata index for the Ethan rows. It keeps the June 2 artifacts intact and adds clearer setup explanations, direct validation metrics, and explicit continuation provenance.",
        "",
        "## Key interpretation rules",
        "",
        "- `two_d_*` columns describe the 2D reference row published in the cross-model comparison contract.",
        "- `one_d_stage*` columns describe first-order-model reference scenarios from that same contract.",
        "- Those 2D/1D columns are enrichment metadata only. They are not direct evidence that the native 3D case used the same insulation or radiation settings.",
        "- `cp_coeff_count` and `rho_coeff_count` are coefficient-array lengths from `case_config.yaml`, not counts of physical modes or components.",
        "- `final_total_wall_heat_abs_w` is the magnitude of the final `total_Q.dat` sample from the 3D run and is used here as the CFD external-loss quantity.",
        "",
        "## Inputs",
        "",
        f"- Comparison contract CSV: `{contract_path}`" if contract_path.exists() else "- Comparison contract CSV: unavailable",
        f"- Validation cases CSV: `{VALIDATION_CASES}`",
        f"- Validation summary root: `{VALIDATION_SUMMARY_ROOT}`",
        f"- Wall probe map CSV: `{WALL_PROBE_LOCATIONS}`",
        "",
        "## Column glossary",
        "",
    ]
    for field in fieldnames:
        lines.append(f"- `{field}`: {glossary.get(field, 'description not yet written')}.")
    (METADATA_OUTPUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision_outputs(case_rows: list[dict[str, object]]) -> None:
    ensure_dir(DECISION_OUTPUT)
    decision_rows = [build_decision_row(case) for case in case_rows]
    hypothesis_rows = [build_hypothesis_row(case, decision) for case, decision in zip(case_rows, decision_rows)]
    decision_fields = list(decision_rows[0].keys())
    hypothesis_fields = list(hypothesis_rows[0].keys())
    csv_dump(DECISION_OUTPUT / "continuation_decisions.csv", decision_fields, decision_rows)
    csv_dump(DECISION_OUTPUT / "alternate_case_hypotheses.csv", hypothesis_fields, hypothesis_rows)
    json_dump(
        DECISION_OUTPUT / "runtime_and_hypothesis_matrix.json",
        {
            "generated_at": iso_timestamp(),
            "continuation_decisions": decision_rows,
            "alternate_case_hypotheses": hypothesis_rows,
        },
    )
    readme = "\n".join(
        [
            "# Ethan Runtime And Hypothesis Matrix",
            "",
            "This report separates three questions:",
            "",
            "- which rows should continue now,",
            "- which rows are usable for diagnostic analysis as they stand,",
            "- which rows point more strongly toward alternate assumptions than toward more runtime.",
            "",
            "## Default runtime recommendation",
            "",
            "- Do not submit a blanket continuation campaign for every non-converged Ethan row.",
            "- Treat `val_salt_test_2_coarse_mesh_laminar` as the only already-justified active continuation target.",
            "- If continuation jobs are submitted, default to 64 MPI ranks per run and pack 3 runs per 256-core node before attempting 4-up packing. That is a conservative memory headroom choice and is sufficient for the current physics-audit stage.",
            "",
            "## Decision labels",
            "",
            "- `continue_now`: runtime evidence still supports extending the case.",
            "- `analyze_as_diagnostic_only`: useful for time-history and trend interpretation, but not currently worth a dedicated continuation submission.",
            "- `alternate_case_first`: current mismatch is better explained by setup assumptions than by more runtime.",
            "- `analyze_as_steady_state`: converged and ready for downstream steady-state reduction work.",
            "",
            "## Alternate-case rules",
            "",
            "- When CFD underpredicts external loss badly, thicker insulation is not the first next case.",
            "- Radiation-on sensitivity and wall-loss boundary recalibration come before insulation-thickening in that regime.",
            "",
        ]
    )
    (DECISION_OUTPUT / "README.md").write_text(readme + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = args.source_ids or DEFAULT_SOURCE_IDS
    contract_path = Path(args.contract_csv).resolve()
    contract_by_source, contract_by_test = load_contract_maps(contract_path)
    validation_rows, validation_summaries = load_validation_maps()
    wall_probe_order = load_wall_probe_order()

    case_rows = [
        build_case_snapshot(source_id, contract_by_source, contract_by_test, validation_rows, validation_summaries, wall_probe_order)
        for source_id in source_ids
    ]

    write_validation_outputs(case_rows)
    write_metadata_outputs(case_rows, contract_path)
    write_decision_outputs(case_rows)

    print(
        json.dumps(
            {
                "generated_at": iso_timestamp(),
                "metadata_output": str(METADATA_OUTPUT),
                "validation_output": str(VALIDATION_OUTPUT),
                "decision_output": str(DECISION_OUTPUT),
                "row_count": len(case_rows),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
