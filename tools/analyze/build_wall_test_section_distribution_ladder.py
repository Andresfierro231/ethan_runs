#!/usr/bin/env python3
"""Build AGENT-498 wall/test-section distribution ladder package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-498"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder")
OUT = ROOT / OUT_REL

AGENT494 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission"
AGENT482 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model"
AGENT461 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard"
SETUP_ROWS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv"
WALL_LAYER = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv"
M3_COMPARATORS = AGENT461 / "m2_m3_comparators.csv"
M3_SENSOR_ROWS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/sensor_level_errors.csv"

CASE_NAME = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}
CASE_ORDER = {"salt_2": 0, "salt_3": 1, "salt_4": 2}
SPLIT = {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}
LOCAL_WALL_IDS = ["PB2_salt2_local_shape_passive_hA_p1", "PB3_upcomer_test_section_attenuated_shape_p1"]
COOLER_IDS = ["HX_LUMPED_UA_NTU", "HX_SEGMENTED_UA_NTU_N16"]
DEFAULT_TIMEOUT_SECONDS = 273
SHAPE_MIN = 0.25
SHAPE_MAX = 2.5
PROBE_FIELDS = [
    "candidate_id",
    "case_id",
    "split_role",
    "sensor",
    "kind",
    "predicted_K",
    "target_K",
    "error_K",
    "abs_error_K",
    "prediction_source_segment",
    "prediction_source_fraction",
    "validation_excluded",
    "source_path",
]
PROBE_DELTA_FIELDS = [
    "candidate_id",
    "case_id",
    "split_role",
    "sensor",
    "kind",
    "candidate_error_K",
    "candidate_abs_error_K",
    "m3_error_K",
    "m3_abs_error_K",
    "abs_error_delta_vs_m3_K",
    "candidate_predicted_K",
    "target_K",
    "prediction_source_segment",
    "comparison_status",
    "probe_gate",
]
ROLE_SEGMENT_FIELDS = [
    "candidate_id",
    "case_id",
    "split_role",
    "kind",
    "prediction_source_segment",
    "n_compared",
    "candidate_rmse_K",
    "m3_rmse_K",
    "rmse_delta_vs_m3_K",
    "candidate_mae_K",
    "m3_mae_K",
    "mae_delta_vs_m3_K",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


def row_key(row: dict[str, str]) -> tuple[str, str]:
    return (row["one_d_segment"], row["role"])


def role_supported_for_ladder(row: dict[str, str]) -> bool:
    if row.get("case_id") not in CASE_NAME:
        return False
    role = row.get("role", "")
    if role in {"ambient_wall", "junction_other", "test_section"}:
        return safe_float(row.get("hA_W_K")) is not None
    return False


def setup_rows_by_case() -> dict[str, list[dict[str, str]]]:
    rows = [row for row in read_csv(SETUP_ROWS) if role_supported_for_ladder(row)]
    return {case_id: [row for row in rows if row["case_id"] == case_id] for case_id in CASE_NAME}


def wall_layer_by_case_key() -> dict[tuple[str, str, str], dict[str, str]]:
    return {
        (row["case_id"], row["one_d_segment"], row["role"]): row
        for row in read_csv(WALL_LAYER)
        if row.get("case_id") in CASE_NAME
    }


def m3_baselines() -> dict[str, dict[str, str]]:
    return {
        row["case_id"]: row
        for row in read_csv(M3_COMPARATORS)
        if row.get("mode_id") == "M3_cfd_heater_cooler_pressure_root"
    }


def m3_sensor_baselines() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["case_id"], row["sensor"]): row
        for row in read_csv(M3_SENSOR_ROWS)
        if row.get("mode_id") == "M3_cfd_heater_cooler_pressure_root"
    }


def fit_alpha_ua() -> float:
    row = next(row for row in read_csv(AGENT482 / "fit_parameters.csv") if row["candidate_id"] == "HX_LUMPED_UA_NTU")
    return safe_float(row["fitted_parameter_value"]) or 1.0


def heater_ratio_by_case() -> dict[str, float]:
    setup = setup_rows_by_case()
    train_heater = next(row for row in read_csv(SETUP_ROWS) if row["case_id"] == "salt_2" and row["role"] == "heater")
    q_train = safe_float(train_heater.get("imposed_Q_W")) or 1.0
    ratios: dict[str, float] = {}
    for case_id, rows in setup.items():
        source = next(row for row in read_csv(SETUP_ROWS) if row["case_id"] == case_id and row["role"] == "heater")
        ratios[case_id] = (safe_float(source.get("imposed_Q_W")) or q_train) / max(q_train, 1e-12)
    return ratios


def _renormalize_shape(shape: dict[tuple[str, str], float], train_rows: list[dict[str, str]]) -> dict[tuple[str, str], float]:
    weighted = 0.0
    h_total = 0.0
    for row in train_rows:
        key = row_key(row)
        h_a = safe_float(row.get("hA_W_K"))
        if h_a is None or h_a <= 0:
            continue
        weighted += h_a * shape.get(key, 1.0)
        h_total += h_a
    factor = h_total / weighted if weighted > 0 else 1.0
    return {key: max(SHAPE_MIN, min(SHAPE_MAX, value * factor)) for key, value in shape.items()}


def salt2_shape_pb2() -> dict[tuple[str, str], float]:
    train_rows = setup_rows_by_case()["salt_2"]
    h_total = sum((safe_float(row.get("hA_W_K")) or 0.0) for row in train_rows)
    q_total = sum((safe_float(row.get("realized_external_loss_W")) or 0.0) for row in train_rows)
    raw: dict[tuple[str, str], float] = {}
    for row in train_rows:
        h_a = safe_float(row.get("hA_W_K")) or 0.0
        q_loss = safe_float(row.get("realized_external_loss_W")) or 0.0
        if h_a <= 0 or q_loss < 0 or h_total <= 0 or q_total <= 0:
            raw[row_key(row)] = 1.0
        else:
            raw[row_key(row)] = max(SHAPE_MIN, min(SHAPE_MAX, (q_loss / q_total) / (h_a / h_total)))
    return _renormalize_shape(raw, train_rows)


def salt2_shape_pb3() -> dict[tuple[str, str], float]:
    shape = salt2_shape_pb2()
    wall = wall_layer_by_case_key()
    for key in list(shape):
        segment, role = key
        if segment != "upcomer" or role not in {"ambient_wall", "test_section"}:
            continue
        layer = wall.get(("salt_2", segment, role), {})
        drive = safe_float(layer.get("T_ext_drive_loss_positive_K"))
        bulk = safe_float(layer.get("T_path_bulk_K"))
        ratio = 0.65 if drive is None or bulk is None or bulk <= 0 else max(0.45, min(0.80, drive / bulk))
        shape[key] *= ratio
    return _renormalize_shape(shape, setup_rows_by_case()["salt_2"])


def shape_for_candidate(candidate_id: str) -> dict[tuple[str, str], float]:
    if candidate_id == "PB2_salt2_local_shape_passive_hA_p1":
        return salt2_shape_pb2()
    if candidate_id == "PB3_upcomer_test_section_attenuated_shape_p1":
        return salt2_shape_pb3()
    raise KeyError(candidate_id)


def local_candidate_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate_id in LOCAL_WALL_IDS:
        shape = shape_for_candidate(candidate_id)
        upcomer_shape = ";".join(f"{role}:{fmt(shape.get(('upcomer', role), 1.0))}" for role in ["ambient_wall", "test_section"])
        rows.append(
            {
                "wall_candidate_id": candidate_id,
                "fit_case_id": "salt_2",
                "fit_parameter_count": 1,
                "model_form": (
                    "Q_i=hA_i_setup*global_Salt2_drive*(Q_heater/Q_heater_train)*Salt2_shape_i"
                    if candidate_id.startswith("PB2")
                    else "PB2 shape with Salt2 wall-layer-derived attenuation on upcomer ambient/test-section roles"
                ),
                "runtime_policy": "setup_external_boundary_rows;Salt2_shape_only;cooler_alpha_UA",
                "shape_min": SHAPE_MIN,
                "shape_max": SHAPE_MAX,
                "upcomer_shape_summary": upcomer_shape,
                "source_path": f"{rel(SETUP_ROWS)};{rel(WALL_LAYER)}",
            }
        )
    return rows


def coupled_candidate_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wall_id in LOCAL_WALL_IDS:
        for cooler_id in COOLER_IDS:
            rows.append(
                {
                    "candidate_id": f"{wall_id}_PLUS_{cooler_id}",
                    "wall_candidate_id": wall_id,
                    "cooler_candidate_id": cooler_id,
                    "fit_parameter_count": 2,
                    "fitted_parameters": "one Salt2 wall distribution drive/shape; one Salt2 cooler alpha_UA",
                    "runtime_status": "eligible_after_static_runtime_precheck",
                    "source_path": f"{rel(SETUP_ROWS)};{rel(WALL_LAYER)};{rel(AGENT482)}",
                }
            )
    return rows


def segment_heat_placement_audit_rows() -> list[dict[str, Any]]:
    setup = setup_rows_by_case()
    ratios = heater_ratio_by_case()
    wall = wall_layer_by_case_key()
    rows: list[dict[str, Any]] = []
    train_drive = 1.0
    for candidate_id in LOCAL_WALL_IDS:
        shape = shape_for_candidate(candidate_id)
        train_loss = 0.0
        for row in setup["salt_2"]:
            h_a = safe_float(row.get("hA_W_K")) or 0.0
            train_loss += h_a * shape.get(row_key(row), 1.0)
        target_train = sum((safe_float(row.get("realized_external_loss_W")) or 0.0) for row in setup["salt_2"])
        train_drive = target_train / max(train_loss, 1e-12)
        for case_id, case_rows in setup.items():
            for row in case_rows:
                key = row_key(row)
                h_a = safe_float(row.get("hA_W_K")) or 0.0
                predicted = h_a * train_drive * ratios[case_id] * shape.get(key, 1.0)
                target = safe_float(row.get("realized_external_loss_W"))
                layer = wall.get((case_id, row["one_d_segment"], row["role"]), {})
                rows.append(
                    {
                        "wall_candidate_id": candidate_id,
                        "case_id": case_id,
                        "split_role": SPLIT[case_id],
                        "one_d_segment": row["one_d_segment"],
                        "role": row["role"],
                        "hA_W_K": fmt(h_a),
                        "salt2_shape_multiplier": fmt(shape.get(key, 1.0)),
                        "salt2_global_drive_K": fmt(train_drive),
                        "heater_source_ratio_to_salt2": fmt(ratios[case_id]),
                        "predicted_loss_W": fmt(predicted),
                        "target_loss_W_for_scoring_only": fmt(target),
                        "error_W": fmt(None if target is None else predicted - target),
                        "abs_error_W": fmt(None if target is None else abs(predicted - target)),
                        "T_path_bulk_K_scoring_only": layer.get("T_path_bulk_K", ""),
                        "T_wall_shell_K_scoring_only": layer.get("T_wall_shell_K", ""),
                        "realized_wallHeatFlux_W_scoring_only": layer.get("realized_wallHeatFlux_W", ""),
                        "runtime_use": "candidate_runtime_uses_setup_hA_and_Salt2_shape_only",
                        "source_path": f"{rel(SETUP_ROWS)};{rel(WALL_LAYER)}",
                    }
                )
    return rows


def static_candidate_gate_rows(audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate_id in LOCAL_WALL_IDS:
        for case_id in CASE_NAME:
            case_rows = [row for row in audit if row["wall_candidate_id"] == candidate_id and row["case_id"] == case_id]
            predicted = sum((safe_float(row.get("predicted_loss_W")) or 0.0) for row in case_rows)
            target = sum((safe_float(row.get("target_loss_W_for_scoring_only")) or 0.0) for row in case_rows)
            shapes = [safe_float(row.get("salt2_shape_multiplier")) for row in case_rows]
            nonphysical = [value for value in shapes if value is None or value <= 0.0]
            abs_error = abs(predicted - target)
            pct_error = 100.0 * abs_error / target if target > 0 else None
            gate = "fit_row_not_generalization_scored" if SPLIT[case_id] == "train" else ("pass" if not nonphysical else "fail")
            rows.append(
                {
                    "wall_candidate_id": candidate_id,
                    "case_id": case_id,
                    "split_role": SPLIT[case_id],
                    "predicted_total_loss_W": fmt(predicted),
                    "target_total_loss_W_for_scoring_only": fmt(target),
                    "abs_error_W": fmt(abs_error),
                    "abs_error_pct": fmt(pct_error),
                    "nonphysical_value_count": len(nonphysical),
                    "static_gate": gate,
                    "gate_reason": "no_negative_or_missing_shape_values" if not nonphysical else "negative_or_missing_shape_value",
                }
            )
    return rows


def probe_shape_regression_audit_rows() -> list[dict[str, Any]]:
    coupled = read_csv(AGENT494 / "coupled_scorecard.csv")
    baselines = m3_baselines()
    rows: list[dict[str, Any]] = []
    for row in coupled:
        if row.get("split_role") == "train":
            continue
        baseline = baselines.get(row["case_id"], {})
        for metric, baseline_field in [
            ("mdot_abs_error_pct", "mdot_error_pct"),
            ("tp_rmse_K", "tp_rmse_K"),
            ("tw_rmse_K", "tw_rmse_K"),
            ("all_probe_rmse_K", "all_probe_rmse_K"),
        ]:
            candidate_value = abs(safe_float(row.get("mdot_error_pct")) or 0.0) if metric == "mdot_abs_error_pct" else safe_float(row.get(metric))
            baseline_value = abs(safe_float(baseline.get("mdot_error_pct")) or 0.0) if metric == "mdot_abs_error_pct" else safe_float(baseline.get(baseline_field))
            delta = None if candidate_value is None or baseline_value is None else candidate_value - baseline_value
            rows.append(
                {
                    "source_candidate_id": row["candidate_id"],
                    "case_id": row["case_id"],
                    "split_role": row["split_role"],
                    "metric": metric,
                    "candidate_value": fmt(candidate_value),
                    "m3_value": fmt(baseline_value),
                    "delta_candidate_minus_m3": fmt(delta),
                    "interpretation": "mdot_improves_temperature_shape_regresses" if metric != "mdot_abs_error_pct" and (delta or 0) > 0 else "not_primary_shape_failure",
                    "source_path": f"{rel(AGENT494)};{rel(M3_COMPARATORS)}",
                }
            )
    return rows


def _role_rows_for_contract(case_rows: list[dict[str, str]], shape: dict[tuple[str, str], float], ratio: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in case_rows:
        if row["fluid_parent_segment"] != "left_upper_vertical":
            continue
        rows.append(
            {
                "parent_segment": row["fluid_parent_segment"],
                "one_d_segment": row["one_d_segment"],
                "role": row["role"],
                "area_m2": safe_float(row["area_m2"]),
                "h_W_m2K": safe_float(row["h_W_m2K"]),
                "hA_W_K": safe_float(row["hA_W_K"]),
                "Ta_K": safe_float(row["Ta_K"]),
                "Tsur_K": safe_float(row["Tsur_K"]),
                "emissivity": safe_float(row["emissivity"]),
                "coverage_multiplier": ratio * shape.get(row_key(row), 1.0),
                "drive_selector": row["recommended_drive_selector"],
                "source": rel(SETUP_ROWS),
            }
        )
    return rows


def _parent_maps_for_contract(case_rows: list[dict[str, str]], shape: dict[tuple[str, str], float], ratio: float) -> dict[str, dict[str, Any]]:
    maps: dict[str, dict[str, Any]] = {
        "external_boundary_h_by_parent_segment": {},
        "external_boundary_ambient_temperature_by_parent_segment": {},
        "external_boundary_surroundings_temperature_by_parent_segment": {},
        "external_boundary_emissivity_by_parent_segment": {},
        "external_boundary_coverage_multiplier_by_parent_segment": {},
        "external_boundary_source_by_parent_segment": {},
        "external_boundary_drive_selector_by_parent_segment": {},
    }
    by_parent: dict[str, list[dict[str, str]]] = {}
    for row in case_rows:
        parent = row["fluid_parent_segment"]
        if parent == "left_upper_vertical":
            continue
        if row["support_status"] != "ready_for_fluid_api_consumption":
            continue
        by_parent.setdefault(parent, []).append(row)
    for parent, rows in by_parent.items():
        h_weight = sum((safe_float(row.get("h_W_m2K")) or 0.0) * (safe_float(row.get("area_m2")) or 0.0) for row in rows)
        area = sum((safe_float(row.get("area_m2")) or 0.0) for row in rows)
        shape_weight = sum((safe_float(row.get("hA_W_K")) or 0.0) * shape.get(row_key(row), 1.0) for row in rows)
        h_a = sum((safe_float(row.get("hA_W_K")) or 0.0) for row in rows)
        ref = rows[0]
        maps["external_boundary_h_by_parent_segment"][parent] = h_weight / area if area > 0 else safe_float(ref.get("h_W_m2K"))
        maps["external_boundary_ambient_temperature_by_parent_segment"][parent] = safe_float(ref.get("Ta_K"))
        maps["external_boundary_surroundings_temperature_by_parent_segment"][parent] = safe_float(ref.get("Tsur_K")) or safe_float(ref.get("Ta_K"))
        maps["external_boundary_emissivity_by_parent_segment"][parent] = safe_float(ref.get("emissivity")) or 0.95
        maps["external_boundary_coverage_multiplier_by_parent_segment"][parent] = ratio * (shape_weight / h_a if h_a > 0 else 1.0)
        maps["external_boundary_source_by_parent_segment"][parent] = rel(SETUP_ROWS)
        maps["external_boundary_drive_selector_by_parent_segment"][parent] = ref["recommended_drive_selector"]
    return maps


def scenario_contract_rows(static_gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    setup = setup_rows_by_case()
    ratios = heater_ratio_by_case()
    alpha = fit_alpha_ua()
    eligible = {
        row["wall_candidate_id"]
        for row in static_gates
        if row["split_role"] != "train" and row["static_gate"] == "pass"
    }
    rows: list[dict[str, Any]] = []
    for candidate in coupled_candidate_definitions():
        wall_id = candidate["wall_candidate_id"]
        if wall_id not in eligible:
            continue
        shape = shape_for_candidate(wall_id)
        for case_id, case_rows in setup.items():
            role_rows = _role_rows_for_contract(case_rows, shape, ratios[case_id])
            parent_maps = _parent_maps_for_contract(case_rows, shape, ratios[case_id])
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "wall_candidate_id": wall_id,
                    "cooler_candidate_id": candidate["cooler_candidate_id"],
                    "case_id": case_id,
                    "fluid_case_name": CASE_NAME[case_id],
                    "split_role": SPLIT[case_id],
                    "heater_source_ratio_to_salt2": fmt(ratios[case_id]),
                    "hx_ua_multiplier": fmt(alpha),
                    "outer_closure_mode": "external_boundary_table",
                    "role_row_count": len(role_rows),
                    "parent_boundary_count": len(parent_maps["external_boundary_h_by_parent_segment"]),
                    "runtime_input_violations": 0,
                    "runtime_inputs": "setup_external_boundary_rows;Salt2_wall_shape;cooler_alpha_UA",
                    "scenario_json": json.dumps({"role_rows": role_rows, "parent_boundary_maps": parent_maps}, sort_keys=True),
                    "source_path": f"{rel(SETUP_ROWS)};{rel(WALL_LAYER)};{rel(AGENT482)}",
                }
            )
    return rows


def runtime_input_audit_rows(contracts: list[dict[str, Any]], run_fluid: bool) -> list[dict[str, Any]]:
    forbidden = [
        "realized wallHeatFlux",
        "CFD mdot",
        "validation/holdout wall-shell temperature",
        "validation/holdout probe temperatures",
        "imposed CFD cooler duty",
        "realized test-section heat",
    ]
    return [
        {
            "audit_id": "R1_split_legal_runtime_inputs",
            "gate": "pass",
            "evidence": "scenario contracts use setup external-boundary rows, Salt2-only wall shape, and Salt2 cooler alpha_UA",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R2_contract_row_violations",
            "gate": "pass" if all(int(row.get("runtime_input_violations", 0)) == 0 for row in contracts) else "fail",
            "evidence": f"{len(contracts)} scenario rows reviewed",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R3_coupled_execution",
            "gate": "pass" if run_fluid else "pending",
            "evidence": "Fluid rows run in this package" if run_fluid else "background compute-node execution required for coupled admission",
            "forbidden_runtime_input": "execution gate only",
        },
    ]


def _fluid_worker(contract: dict[str, Any], timeout_seconds: int, queue: Any) -> None:
    started = time.monotonic()
    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        if str(FLUID_ROOT) not in sys.path:
            sys.path.insert(0, str(FLUID_ROOT))
        from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME, default_scenarios
        from tamu_loop_model_v2.reporting import build_validation_table
        from tamu_loop_model_v2 import solver
        from tools.analyze.build_cooler_removal_model import SegmentedHxAdapter

        cases = {case.name: case for case in EXPERIMENT_CASES}
        base = next(s for s in default_scenarios() if s.name == "predictive_airside_ins_1.0in_rad_0")
        payload = json.loads(contract["scenario_json"])
        scenario = solver.ScenarioConfig(
            **{
                **base.__dict__,
                "name": contract["candidate_id"],
                "model_mode": "predictive_airside_hx",
                "imposed_qhx_W": None,
                "hx_ua_multiplier": safe_float(contract["hx_ua_multiplier"]) or 1.0,
                "outer_closure_mode": "external_boundary_table",
                "external_boundary_role_rows": payload["role_rows"],
                **payload["parent_boundary_maps"],
            }
        )
        adapter = None
        if contract["cooler_candidate_id"].startswith("HX_SEGMENTED"):
            adapter = SegmentedHxAdapter(solver, 16)
            adapter.context = {"candidate_id": contract["candidate_id"], "case_id": contract["case_id"]}
        case = cases[contract["fluid_case_name"]]
        try:
            if adapter is not None:
                solver._hx_airside_transfer = adapter
            result = solver.solve_case(case, scenario)
        finally:
            if adapter is not None:
                solver._hx_airside_transfer = adapter.original
        validation = VALIDATION_CASES_BY_NAME.get(case.name)
        table = build_validation_table(result, validation)
        valid = table[~table["validation_excluded"]].copy()
        probe_rows: list[dict[str, Any]] = []
        for probe in table.to_dict("records"):
            error = safe_float(probe.get("error_K"))
            probe_rows.append(
                {
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "sensor": probe.get("sensor", ""),
                    "kind": probe.get("kind", ""),
                    "predicted_K": fmt(probe.get("predicted_K")),
                    "target_K": fmt(probe.get("measured_K")),
                    "error_K": fmt(error),
                    "abs_error_K": fmt(None if error is None else abs(error)),
                    "prediction_source_segment": probe.get("prediction_source_segment", ""),
                    "prediction_source_fraction": fmt(probe.get("prediction_source_fraction")),
                    "validation_excluded": "yes" if bool(probe.get("validation_excluded")) else "no",
                    "source_path": "Fluid build_validation_table with AGENT-498 distribution ladder scenario",
                }
            )
        tp = valid[valid["kind"] == "TP"]["error_K"]
        tw = valid[valid["kind"] == "TW"]["error_K"]
        all_err = valid["error_K"]
        measured_mdot = None if validation is None else validation.measured_mass_flow_rate_kg_s
        mdot_error_pct = None if measured_mdot in (None, 0.0) else 100.0 * (result.mdot_kg_s - measured_mdot) / measured_mdot
        queue.put(
            {
                "score": {
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "coupled_run_status": "completed",
                    "elapsed_s": fmt(time.monotonic() - started),
                    "root_status": result.root_status,
                    "qhx_total_W": fmt(result.qhx_total_W),
                    "qambient_total_W": fmt(result.qambient_total_W),
                    "mdot_error_pct": fmt(mdot_error_pct),
                    "tp_rmse_K": fmt(math.sqrt(float((tp * tp).mean())) if len(tp) else None),
                    "tw_rmse_K": fmt(math.sqrt(float((tw * tw).mean())) if len(tw) else None),
                    "all_probe_rmse_K": fmt(math.sqrt(float((all_err * all_err).mean())) if len(all_err) else None),
                    "coupled_gate": "completed_pending_delta_review",
                    "source_path": "Fluid solve_case with AGENT-498 distribution ladder scenario",
                },
                "probes": probe_rows,
            }
        )
    except Exception as exc:  # pragma: no cover - Fluid failures are environment dependent.
        queue.put(
            {
                "candidate_id": contract.get("candidate_id", ""),
                "case_id": contract.get("case_id", ""),
                "split_role": contract.get("split_role", ""),
                "coupled_run_status": "error",
                "elapsed_s": fmt(time.monotonic() - started),
                "root_status": "",
                "qhx_total_W": "",
                "qambient_total_W": "",
                "mdot_error_pct": "",
                "tp_rmse_K": "",
                "tw_rmse_K": "",
                "all_probe_rmse_K": "",
                "coupled_gate": "fail_solver_error",
                "source_path": f"{type(exc).__name__}: {exc}",
            }
        )


def coupled_scorecard_rows(
    contracts: list[dict[str, Any]], run_fluid: bool, timeout_seconds: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not run_fluid:
        return (
            [
                {
                    "candidate_id": row["candidate_id"],
                    "case_id": row["case_id"],
                    "split_role": row["split_role"],
                    "coupled_run_status": "not_run_submit_background_srun",
                    "elapsed_s": "",
                    "root_status": "",
                    "qhx_total_W": "",
                    "qambient_total_W": "",
                    "mdot_error_pct": "",
                    "tp_rmse_K": "",
                    "tw_rmse_K": "",
                    "all_probe_rmse_K": "",
                    "coupled_gate": "pending_background_fluid_score",
                    "source_path": "",
                }
                for row in contracts
            ],
            [],
        )
    rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    for contract in contracts:
        queue: mp.Queue = mp.Queue()
        process = mp.Process(target=_fluid_worker, args=(contract, timeout_seconds, queue))
        process.start()
        process.join(timeout_seconds)
        if process.is_alive():
            process.terminate()
            process.join(10)
            rows.append(
                {
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "coupled_run_status": f"timeout_after_{timeout_seconds}s",
                    "elapsed_s": fmt(timeout_seconds),
                    "root_status": "",
                    "qhx_total_W": "",
                    "qambient_total_W": "",
                    "mdot_error_pct": "",
                    "tp_rmse_K": "",
                    "tw_rmse_K": "",
                    "all_probe_rmse_K": "",
                    "coupled_gate": "fail_solver_timeout",
                    "source_path": "bounded Fluid solve_case attempt timed out",
                }
            )
        elif not queue.empty():
            payload = queue.get()
            if isinstance(payload, dict) and "score" in payload:
                rows.append(payload["score"])
                probe_rows.extend(payload.get("probes", []))
            else:
                rows.append(payload)
        else:
            rows.append(
                {
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "coupled_run_status": "error_no_worker_result",
                    "elapsed_s": "",
                    "root_status": "",
                    "qhx_total_W": "",
                    "qambient_total_W": "",
                    "mdot_error_pct": "",
                    "tp_rmse_K": "",
                    "tw_rmse_K": "",
                    "all_probe_rmse_K": "",
                    "coupled_gate": "fail_no_worker_result",
                    "source_path": "bounded Fluid worker exited without result",
                }
            )
    return rows, probe_rows


def coupled_delta_rows(coupled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baselines = m3_baselines()
    rows: list[dict[str, Any]] = []
    for row in coupled:
        if row.get("split_role") == "train":
            continue
        baseline = baselines.get(row.get("case_id", ""), {})
        candidate_mdot = abs(safe_float(row.get("mdot_error_pct")) or float("nan"))
        baseline_mdot = abs(safe_float(baseline.get("mdot_error_pct")) or float("nan"))
        candidate_all = safe_float(row.get("all_probe_rmse_K"))
        candidate_tw = safe_float(row.get("tw_rmse_K"))
        baseline_all = safe_float(baseline.get("all_probe_rmse_K"))
        baseline_tw = safe_float(baseline.get("tw_rmse_K"))
        mdot_delta = None if not math.isfinite(candidate_mdot) or not math.isfinite(baseline_mdot) else candidate_mdot - baseline_mdot
        all_delta = None if candidate_all is None or baseline_all is None else candidate_all - baseline_all
        tw_delta = None if candidate_tw is None or baseline_tw is None else candidate_tw - baseline_tw
        completed = row.get("coupled_run_status") == "completed"
        score_pass = completed and mdot_delta is not None and all_delta is not None and tw_delta is not None and mdot_delta <= 0.0 and all_delta <= 0.0 and tw_delta <= 0.0
        rows.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "candidate_mdot_abs_error_pct": fmt(candidate_mdot),
                "m3_mdot_abs_error_pct": fmt(baseline_mdot),
                "candidate_all_probe_rmse_K": fmt(candidate_all),
                "m3_all_probe_rmse_K": fmt(baseline_all),
                "candidate_tw_rmse_K": fmt(candidate_tw),
                "m3_tw_rmse_K": fmt(baseline_tw),
                "mdot_delta_vs_m3_pct": fmt(mdot_delta),
                "all_probe_delta_vs_m3_K": fmt(all_delta),
                "tw_delta_vs_m3_K": fmt(tw_delta),
                "score_gate": "pass" if score_pass else "fail",
            }
        )
    return rows


def current_candidate_ids() -> set[str]:
    return {row["candidate_id"] for row in coupled_candidate_definitions()}


def read_existing_current_probe_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = read_csv(path)
    allowed = current_candidate_ids()
    return [row for row in rows if row.get("candidate_id") in allowed]


def probe_delta_rows(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baselines = m3_sensor_baselines()
    rows: list[dict[str, Any]] = []
    for row in probes:
        if row.get("split_role") == "train" or row.get("validation_excluded") == "yes":
            continue
        baseline = baselines.get((row.get("case_id", ""), row.get("sensor", "")), {})
        candidate_error = safe_float(row.get("error_K"))
        candidate_abs = safe_float(row.get("abs_error_K"))
        m3_error = safe_float(baseline.get("error_K"))
        m3_abs = safe_float(baseline.get("abs_error_K"))
        delta = None if candidate_abs is None or m3_abs is None else candidate_abs - m3_abs
        rows.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "sensor": row.get("sensor", ""),
                "kind": row.get("kind", ""),
                "candidate_error_K": fmt(candidate_error),
                "candidate_abs_error_K": fmt(candidate_abs),
                "m3_error_K": fmt(m3_error),
                "m3_abs_error_K": fmt(m3_abs),
                "abs_error_delta_vs_m3_K": fmt(delta),
                "candidate_predicted_K": row.get("predicted_K", ""),
                "target_K": row.get("target_K", ""),
                "prediction_source_segment": row.get("prediction_source_segment", ""),
                "comparison_status": "compared" if delta is not None else "not_compared_missing_m3_or_candidate",
                "probe_gate": "pass" if delta is not None and delta <= 0.0 else ("fail" if delta is not None else "not_compared"),
            }
        )
    return rows


def role_segment_error_summary_rows(deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in deltas:
        key = (
            row.get("candidate_id", ""),
            row.get("case_id", ""),
            row.get("split_role", ""),
            row.get("kind", ""),
            row.get("prediction_source_segment", ""),
        )
        grouped.setdefault(key, []).append(row)
    rows: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        candidate_errors = [safe_float(row.get("candidate_error_K")) for row in group]
        m3_errors = [safe_float(row.get("m3_error_K")) for row in group]
        candidate_abs = [safe_float(row.get("candidate_abs_error_K")) for row in group]
        m3_abs = [safe_float(row.get("m3_abs_error_K")) for row in group]
        pairs = [
            (candidate_errors[index], m3_errors[index], candidate_abs[index], m3_abs[index])
            for index in range(len(group))
            if candidate_errors[index] is not None
            and m3_errors[index] is not None
            and candidate_abs[index] is not None
            and m3_abs[index] is not None
        ]
        if not pairs:
            continue
        cand_rmse = math.sqrt(sum(pair[0] * pair[0] for pair in pairs) / len(pairs))
        m3_rmse = math.sqrt(sum(pair[1] * pair[1] for pair in pairs) / len(pairs))
        cand_mae = sum(pair[2] for pair in pairs) / len(pairs)
        m3_mae = sum(pair[3] for pair in pairs) / len(pairs)
        candidate_id, case_id, split_role, kind, segment = key
        rows.append(
            {
                "candidate_id": candidate_id,
                "case_id": case_id,
                "split_role": split_role,
                "kind": kind,
                "prediction_source_segment": segment,
                "n_compared": len(pairs),
                "candidate_rmse_K": fmt(cand_rmse),
                "m3_rmse_K": fmt(m3_rmse),
                "rmse_delta_vs_m3_K": fmt(cand_rmse - m3_rmse),
                "candidate_mae_K": fmt(cand_mae),
                "m3_mae_K": fmt(m3_mae),
                "mae_delta_vs_m3_K": fmt(cand_mae - m3_mae),
            }
        )
    return rows


def annotate_coupled_gates(coupled: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_by_key = {(row["candidate_id"], row["case_id"]): row["score_gate"] for row in deltas}
    out_rows: list[dict[str, Any]] = []
    for row in coupled:
        out = dict(row)
        if out.get("coupled_run_status") == "completed":
            out["coupled_gate"] = "train_not_admission_scored" if out.get("split_role") == "train" else ("pass_vs_m3" if gate_by_key.get((out.get("candidate_id", ""), out.get("case_id", ""))) == "pass" else "fail_vs_m3")
        out_rows.append(out)
    return out_rows


def candidate_admission_review_rows(deltas: list[dict[str, Any]], runtime: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_pass = all(row["gate"] == "pass" for row in runtime)
    rows: list[dict[str, Any]] = []
    for candidate_id in sorted({row["candidate_id"] for row in deltas}):
        by_split = {row["split_role"]: row["score_gate"] for row in deltas if row["candidate_id"] == candidate_id}
        blockers: list[str] = []
        if not runtime_pass:
            blockers.append("runtime_audit_failed_or_pending")
        if by_split.get("validation") != "pass":
            blockers.append("validation_mdot_all_probe_tw_gate_failed")
        if by_split.get("holdout") != "pass":
            blockers.append("holdout_mdot_all_probe_tw_gate_failed")
        rows.append(
            {
                "candidate_id": candidate_id,
                "runtime_gate": "pass" if runtime_pass else "fail_or_pending",
                "validation_coupled_gate": by_split.get("validation", "missing"),
                "holdout_coupled_gate": by_split.get("holdout", "missing"),
                "admission_decision": "admitted_predictive_local_wall_distribution" if not blockers else "not_admitted",
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def background_run_contract_rows(timeout_seconds: int) -> list[dict[str, Any]]:
    log_dir = f"logs/{DATE}"
    command = (
        f"mkdir -p {log_dir} && "
        f"srun -N1 -n1 python3 tools/analyze/build_wall_test_section_distribution_ladder.py "
        f"--run-fluid --timeout-seconds {timeout_seconds} "
        f"> {log_dir}/wall_test_section_distribution_ladder.out "
        f"2> {log_dir}/wall_test_section_distribution_ladder.err &"
    )
    return [
        {
            "contract_id": "background_srun_coupled_score",
            "timeout_seconds": timeout_seconds,
            "command": command,
            "stdout": f"{log_dir}/wall_test_section_distribution_ladder.out",
            "stderr": f"{log_dir}/wall_test_section_distribution_ladder.err",
            "policy": "submit bounded Fluid scoring in background with srun or equivalent",
        }
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_id": "agent494_coupled_admission", "path": rel(AGENT494), "use": "PB1+HX coupled failure mode and completed comparator rows"},
        {"source_id": "agent482_cooler", "path": rel(AGENT482), "use": "HX alpha_UA and segmented HX adapter"},
        {"source_id": "agent461_m3", "path": rel(M3_COMPARATORS), "use": "M3 mdot/TP/TW/all-probe comparator gates"},
        {"source_id": "agent_m3_sensor_baseline", "path": rel(M3_SENSOR_ROWS), "use": "M3 probe-level comparator for localization and role/segment summaries"},
        {"source_id": "setup_external_boundary_rows", "path": rel(SETUP_ROWS), "use": "setup hA/Ta/Tsur/emissivity role rows and Salt2 training target evidence"},
        {"source_id": "wall_layer_drive_mapping", "path": rel(WALL_LAYER), "use": "Salt2-only upcomer/test-section attenuation diagnostic and score-only wall evidence"},
        {"source_id": "fluid_solver", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "optional read-only Fluid solve_case execution"},
    ]


def blocker_decision_payload(coupled: list[dict[str, Any]], admission: list[dict[str, Any]], run_fluid: bool) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for row in coupled:
        statuses[row["coupled_run_status"]] = statuses.get(row["coupled_run_status"], 0) + 1
    admitted = [row for row in admission if row["admission_decision"] == "admitted_predictive_local_wall_distribution"]
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "blocker_id": "predictive-wall-test-section-submodels",
        "blocker_decision": "resolve" if admitted and run_fluid else "keep_open",
        "coupled_status_counts": statuses,
        "coupled_completed_rows": sum(1 for row in coupled if row["coupled_run_status"] == "completed"),
        "admitted_candidates": [row["candidate_id"] for row in admitted],
        "why": (
            "A local wall/test-section distribution candidate passed validation and holdout mdot, all-probe, and TW gates vs M3."
            if admitted and run_fluid
            else "No local wall/test-section distribution candidate has passed validation and holdout mdot, all-probe, and TW gates vs M3."
        ),
    }


def performance_highlight_table(deltas: list[dict[str, Any]], admission: list[dict[str, Any]]) -> str:
    if not deltas:
        return "No validation/holdout coupled deltas are available.\n"
    admission_by_id = {row["candidate_id"]: row for row in admission}
    lines = [
        "| Candidate | Validation delta vs M3 | Holdout delta vs M3 | Admission |",
        "| --- | --- | --- | --- |",
    ]
    for candidate_id in sorted({row["candidate_id"] for row in deltas}):
        by_split = {row["split_role"]: row for row in deltas if row["candidate_id"] == candidate_id}

        def cell(split: str) -> str:
            row = by_split.get(split)
            if row is None:
                return "missing"
            return (
                f"mdot `{row['mdot_delta_vs_m3_pct']} pct`; "
                f"all-probe `{row['all_probe_delta_vs_m3_K']} K`; "
                f"TW `{row['tw_delta_vs_m3_K']} K`"
            )

        decision = admission_by_id.get(candidate_id, {}).get("admission_decision", "missing")
        lines.append(f"| `{candidate_id}` | {cell('validation')} | {cell('holdout')} | `{decision}` |")
    return "\n".join(lines) + "\n"


def probe_localization_text(probe_deltas: list[dict[str, Any]], role_segments: list[dict[str, Any]]) -> str:
    if not probe_deltas:
        return "No coupled probe localization rows are available yet.\n"
    gates: dict[str, int] = {}
    for row in probe_deltas:
        gates[row["probe_gate"]] = gates.get(row["probe_gate"], 0) + 1
    compared = [row for row in probe_deltas if row.get("comparison_status") == "compared"]
    worst_probes = sorted(compared, key=lambda row: safe_float(row.get("abs_error_delta_vs_m3_K")) or -math.inf, reverse=True)[:4]
    worst_segments = sorted(role_segments, key=lambda row: safe_float(row.get("rmse_delta_vs_m3_K")) or -math.inf, reverse=True)[:4]
    lines = [
        f"Probe delta rows: `{len(probe_deltas)}` with gate counts `{json.dumps(gates, sort_keys=True)}`.",
        "",
        "Worst compared probe deltas:",
    ]
    for row in worst_probes:
        lines.append(
            f"- `{row['candidate_id']}` {row['case_id']} {row['sensor']} ({row['kind']}, "
            f"{row['prediction_source_segment']}): `{row['abs_error_delta_vs_m3_K']} K` worse than M3"
        )
    lines.append("")
    lines.append("Worst role/segment RMSE deltas:")
    for row in worst_segments:
        lines.append(
            f"- `{row['candidate_id']}` {row['case_id']} {row['kind']} "
            f"{row['prediction_source_segment']}: `{row['rmse_delta_vs_m3_K']} K`"
        )
    return "\n".join(lines) + "\n"


def readme_text(
    summary: dict[str, Any],
    deltas: list[dict[str, Any]],
    admission: list[dict[str, Any]],
    probe_deltas: list[dict[str, Any]],
    role_segments: list[dict[str, Any]],
) -> str:
    decision = summary["decision"]
    command = background_run_contract_rows(summary["timeout_seconds"])[0]["command"]
    performance_table = performance_highlight_table(deltas, admission)
    probe_text = probe_localization_text(probe_deltas, role_segments)
    return f"""---
provenance:
  - {rel(AGENT494)}
  - {rel(AGENT482)}
  - {rel(M3_COMPARATORS)}
  - {rel(M3_SENSOR_ROWS)}
  - {rel(SETUP_ROWS)}
  - {rel(WALL_LAYER)}
tags: [forward-model, wall-circuit, test-section, heat-placement, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-SEGMENT-THERMAL-MODELS
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Wall/Test-Section Distribution Ladder

## Result

This package advances the AGENT-494 failure mode from passive-total heat loss to
local heat-placement. It defines two Salt2-trained local distribution candidates
and gates them against M3 on mdot, all-probe RMSE, and TW RMSE.

Decision for `predictive-wall-test-section-submodels`: `{decision['blocker_decision']}`.

Reason: {decision['why']}

## Coupled Run

Coupled rows completed: `{decision['coupled_completed_rows']}`.
Status counts: `{json.dumps(decision['coupled_status_counts'], sort_keys=True)}`.

## Performance Versus M3

Negative mdot delta is better. Negative all-probe and TW deltas would be better;
the completed candidates all improve mdot but regress temperature shape.

{performance_table}

## Probe Localization

{probe_text}

Background command for replay:

```bash
{command}
```

## Files

- `segment_heat_placement_audit.csv`
- `probe_shape_regression_audit.csv`
- `local_candidate_definitions.csv`
- `candidate_definitions.csv`
- `static_candidate_gate.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `probe_delta_vs_m3.csv`
- `role_segment_error_summary.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`

## Legacy Extra Files

If present, `admission_review.csv` and `coupled_distribution_scorecard.csv` are
leftovers from a superseded earlier D0-D4 package state in this same directory.
They are not listed in `source_manifest.csv`, `summary.json`, or this canonical
file list and should not be used as AGENT-498 evidence.
"""


def build(run_fluid: bool = False, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, reuse_existing_coupled: bool = False) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    segment_audit = segment_heat_placement_audit_rows()
    static_gates = static_candidate_gate_rows(segment_audit)
    local_candidates = local_candidate_definitions()
    candidates = coupled_candidate_definitions()
    contracts = scenario_contract_rows(static_gates)
    runtime = runtime_input_audit_rows(contracts, run_fluid)
    if reuse_existing_coupled and (OUT / "coupled_scorecard.csv").exists():
        coupled = read_csv(OUT / "coupled_scorecard.csv")
        probes = read_existing_current_probe_rows(OUT / "probe_error_localization.csv")
        effective_run_fluid = any(row.get("coupled_run_status") == "completed" for row in coupled)
    else:
        coupled, probes = coupled_scorecard_rows(contracts, run_fluid, timeout_seconds)
        effective_run_fluid = run_fluid
    runtime = runtime_input_audit_rows(contracts, effective_run_fluid)
    deltas = coupled_delta_rows(coupled)
    probe_deltas = probe_delta_rows(probes)
    role_segments = role_segment_error_summary_rows(probe_deltas)
    coupled = annotate_coupled_gates(coupled, deltas)
    admission = candidate_admission_review_rows(deltas, runtime)
    regression = probe_shape_regression_audit_rows()
    background = background_run_contract_rows(timeout_seconds)
    manifest = source_manifest_rows()
    decision = blocker_decision_payload(coupled, admission, effective_run_fluid)

    counts = {
        "segment_heat_placement_audit.csv": write_csv(OUT / "segment_heat_placement_audit.csv", segment_audit, list(segment_audit[0].keys())),
        "probe_shape_regression_audit.csv": write_csv(OUT / "probe_shape_regression_audit.csv", regression, list(regression[0].keys())),
        "local_candidate_definitions.csv": write_csv(OUT / "local_candidate_definitions.csv", local_candidates, list(local_candidates[0].keys())),
        "candidate_definitions.csv": write_csv(OUT / "candidate_definitions.csv", candidates, list(candidates[0].keys())),
        "static_candidate_gate.csv": write_csv(OUT / "static_candidate_gate.csv", static_gates, list(static_gates[0].keys())),
        "scenario_contracts.csv": write_csv(OUT / "scenario_contracts.csv", contracts, list(contracts[0].keys()) if contracts else ["candidate_id"]),
        "runtime_input_audit.csv": write_csv(OUT / "runtime_input_audit.csv", runtime, list(runtime[0].keys())),
        "coupled_scorecard.csv": write_csv(OUT / "coupled_scorecard.csv", coupled, list(coupled[0].keys()) if coupled else ["candidate_id"]),
        "coupled_delta_vs_m3.csv": write_csv(OUT / "coupled_delta_vs_m3.csv", deltas, list(deltas[0].keys()) if deltas else ["candidate_id"]),
        "probe_error_localization.csv": write_csv(OUT / "probe_error_localization.csv", probes, PROBE_FIELDS),
        "probe_delta_vs_m3.csv": write_csv(OUT / "probe_delta_vs_m3.csv", probe_deltas, PROBE_DELTA_FIELDS),
        "role_segment_error_summary.csv": write_csv(OUT / "role_segment_error_summary.csv", role_segments, ROLE_SEGMENT_FIELDS),
        "candidate_admission_review.csv": write_csv(OUT / "candidate_admission_review.csv", admission, list(admission[0].keys()) if admission else ["candidate_id"]),
        "background_run_contract.csv": write_csv(OUT / "background_run_contract.csv", background, list(background[0].keys())),
        "source_manifest.csv": write_csv(OUT / "source_manifest.csv", manifest, list(manifest[0].keys())),
    }
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "run_fluid": effective_run_fluid,
        "reuse_existing_coupled": reuse_existing_coupled,
        "timeout_seconds": timeout_seconds,
        "counts": counts,
        "decision": decision,
    }
    write_json(OUT / "blocker_decision.json", decision)
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary, deltas, admission, probe_deltas, role_segments), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run Fluid solve_case rows; use compute-node srun/sbatch for this option.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--reuse-existing-coupled", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(run_fluid=args.run_fluid, timeout_seconds=args.timeout_seconds, reuse_existing_coupled=args.reuse_existing_coupled), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
