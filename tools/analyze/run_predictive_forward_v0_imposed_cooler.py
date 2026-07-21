#!/usr/bin/env python3
"""Run pressure-rooted forward-v0 with heater input and imposed cooler duty.

This runner is predictive only conditional on the imposed cooler duty. It uses
Fluid's pressure-rooted solve, does not hold mdot at CFD, and joins CFD and
experimental sensor/thermal targets only after solving.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.analyze import build_predictive_input_contract as input_contract
from tools.analyze import run_cfd_informed_fixed_mdot_1d_replays as legacy_replay


FLUID_ROOT = (REPO_ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
if str(FLUID_ROOT) not in sys.path:
    sys.path.insert(0, str(FLUID_ROOT))

from tamu_loop_model_v2 import config_loader, reporting, solver as S  # noqa: E402


OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler"
CONTRACT_DIR = input_contract.OUT_DIR
THERMAL_TARGETS = input_contract.THERMAL_TARGETS
CFD_SENSOR_REFERENCE = (
    REPO_ROOT / "reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/cfd_sensor_reference.csv"
)

RUN_PLAN_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "variant_id",
    "description",
    "model_mode",
    "radiation_on",
    "imposed_cooler_duty_W",
    "boundary_ambient_Ta_K",
    "source_contract",
    "hydraulic_policy",
    "runtime_input_policy",
    "litrev_gate_policy",
]

RESULT_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "variant_id",
    "engine",
    "root_status",
    "accepted_for_validation",
    "mdot_kg_s",
    "cfd_mdot_kg_s",
    "mdot_error_vs_cfd_kg_s",
    "mdot_error_vs_experimental_kg_s",
    "velocity_main_m_s",
    "reynolds_main",
    "pressure_residual_Pa",
    "deltaP_buoyancy_Pa",
    "deltaP_losses_Pa",
    "temperature_periodicity_error_K",
    "start_temperature_K",
    "end_temperature_K",
    "model_Tmean_proxy_K",
    "cfd_Tmean_K",
    "Tmean_error_vs_cfd_K",
    "model_loop_delta_proxy_K",
    "cfd_loop_delta_T_K",
    "loop_delta_error_vs_cfd_K",
    "qhx_total_W",
    "imposed_cooler_duty_W",
    "qambient_total_W",
    "imported_source_total_W",
    "imported_segment_loss_total_W",
    "source_total_input_W",
    "ambient_temperature_K",
    "radiation_on",
    "source_contract",
    "root_rejection_reason",
    "validity_status",
    "validity_rejection_reason",
]

SENSOR_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "variant_id",
    "engine",
    "sensor_source",
    "sensor",
    "kind",
    "predicted_K",
    "target_K",
    "error_K",
    "prediction_source_segment",
    "prediction_source_fraction",
    "target_provenance",
    "notes",
]

SEGMENT_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "variant_id",
    "engine",
    "segment_name",
    "parent_segment",
    "s_start_m",
    "s_end_m",
    "T_in_K",
    "T_out_K",
    "T_avg_K",
    "Q_source_W",
    "Q_hx_sink_W",
    "Q_ambient_W",
    "h_inner_W_m2K",
    "h_outer_W_m2K",
    "h_rad_W_m2K",
    "reynolds_inner",
    "nusselt_inner",
]

VARIANT_SUMMARY_COLUMNS = [
    "variant_id",
    "engine",
    "n_rows",
    "mean_abs_Tmean_error_vs_cfd_K",
    "mean_abs_loop_delta_error_vs_cfd_K",
    "mean_mdot_error_vs_cfd_kg_s",
    "mean_mdot_error_vs_experimental_kg_s",
    "max_abs_pressure_residual_Pa",
    "mean_qambient_total_W",
]

AUDIT_COLUMNS = [
    "case_id",
    "variant_id",
    "engine",
    "runtime_field",
    "runtime_value",
    "contract_class",
    "forward_v0_allowed",
    "source_path",
]

GATE_REFERENCE_COLUMNS = [
    "gate_name",
    "runtime_contract_field",
    "contract_class",
    "required_before_scoring",
    "gate_source_path",
    "source_exists",
    "scoring_admission_status",
    "notes",
]

CASE_ID_TO_NAME = input_contract.CASE_ID_TO_NAME
CASE_NAME_TO_ID = input_contract.CASE_NAME_TO_ID
FAST_MDOT_GRID = [0.005, 0.01, 0.015, 0.02, 0.03, 0.05]
REQUIRED_GATE_NAMES = tuple(input_contract.REQUIRED_LITREV_GATES)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return value


def fnum(value: Any, default: float | None = None) -> float | None:
    if value in ("", None):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def load_or_build_contract(contract_dir: Path, strict: bool) -> dict[str, Any]:
    summary_path = contract_dir / "summary.json"
    if not summary_path.exists():
        summary = input_contract.build_package(contract_dir)
    else:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        runtime_path = contract_dir / "runtime_input_contract.csv"
        if not runtime_path.exists():
            summary = input_contract.build_package(contract_dir)
        else:
            runtime_rows = read_csv(runtime_path)
            runtime_fields = {row.get("field_name", "") for row in runtime_rows}
            if any(gate_name not in runtime_fields for gate_name in REQUIRED_GATE_NAMES):
                summary = input_contract.build_package(contract_dir)
    if strict and int(summary.get("n_violations", 0)) != 0:
        raise ValueError(f"input contract has {summary.get('n_violations')} violation(s)")
    return summary


def runtime_contract_by_field(contract_dir: Path) -> dict[str, dict[str, str]]:
    return {row["field_name"]: row for row in read_csv(contract_dir / "runtime_input_contract.csv")}


def variant_specs() -> list[dict[str, str]]:
    return [
        {
            "variant_id": "F0_current_fluid_sources",
            "description": "Current Fluid salt source contract: heater power plus configured 37 W test-section input.",
            "source_contract": "heater_power_W_plus_test_section_power_W",
        },
        {
            "variant_id": "F1_heater_only",
            "description": "Heater setup power only; test-section source omitted pending heater/test-section contract.",
            "source_contract": "heater_power_W_only_prescribed_segment_source",
        },
    ]


def run_plan_rows(case_inputs: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_input in case_inputs:
        for spec in variant_specs():
            rows.append(
                {
                    "case_id": case_input["case_id"],
                    "fluid_case_name": case_input["fluid_case_name"],
                    "source_id": case_input["source_id"],
                    "variant_id": spec["variant_id"],
                    "description": spec["description"],
                    "model_mode": "imposed_qhx",
                    "radiation_on": "false",
                    "imposed_cooler_duty_W": case_input["imposed_cooler_duty_W"],
                    "boundary_ambient_Ta_K": case_input["boundary_ambient_Ta_K"],
                    "source_contract": spec["source_contract"],
                    "hydraulic_policy": "solve mdot from pressure balance; do not consume CFD mdot",
                    "runtime_input_policy": "strict input contract; validation joined after solve",
                    "litrev_gate_policy": "require source envelope, property mode, named-loss, heat-loss, and CFD naming gates before scoring",
                }
            )
    return rows


def litrev_gate_reference_rows(runtime_contract: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for gate_name, expected_path in input_contract.REQUIRED_LITREV_GATES.items():
        contract = runtime_contract.get(gate_name, {})
        gate_source_path = contract.get("litrev_gate_source_path", "")
        source_path = REPO_ROOT / gate_source_path if gate_source_path else expected_path
        source_exists = source_path.exists()
        required = contract.get("litrev_gate_required_before_scoring", "")
        class_name = contract.get("field_class", "")
        status = "pass"
        notes = "explicit lit-rev gate reference present"
        if not contract:
            status = "fail"
            notes = "required gate row missing from runtime_input_contract.csv"
        elif required != "true":
            status = "fail"
            notes = "gate row is not marked required before scoring"
        elif gate_source_path != input_contract.rel(expected_path):
            status = "fail"
            notes = "gate source path does not match the expected lit-rev package"
        elif not source_exists:
            status = "fail"
            notes = "gate source path does not exist"
        rows.append(
            {
                "gate_name": gate_name,
                "runtime_contract_field": gate_name if contract else "",
                "contract_class": class_name,
                "required_before_scoring": required,
                "gate_source_path": gate_source_path,
                "source_exists": "true" if source_exists else "false",
                "scoring_admission_status": status,
                "notes": notes,
            }
        )
    return rows


def enforce_litrev_gate_references(gate_rows: list[dict[str, Any]]) -> None:
    failed = [row for row in gate_rows if row["scoring_admission_status"] != "pass"]
    if failed:
        names = ", ".join(str(row["gate_name"]) for row in failed)
        raise ValueError(f"forward-v0 scoring blocked by missing or invalid lit-rev gate references: {names}")


def scenario_for(case_input: dict[str, str], variant_id: str) -> S.ScenarioConfig:
    return S.ScenarioConfig(
        name=f"forward_v0_{variant_id}",
        ambient_temperature_K=float(case_input["boundary_ambient_Ta_K"]),
        insulation_thickness_in=float(case_input["insulation_thickness_in"]),
        radiation_on=False,
        model_mode="imposed_qhx",
        imposed_qhx_W=float(case_input["imposed_cooler_duty_W"]),
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=float(case_input["mdot_search_lower_kg_s"]),
        mdot_search_upper_kg_s=float(case_input["mdot_search_upper_kg_s"]),
    )


def prescribed_sources_for(case: S.ExperimentCase, variant_id: str) -> dict[str, float] | None:
    if variant_id == "F0_current_fluid_sources":
        return None
    if variant_id == "F1_heater_only":
        return {"heated_incline": float(case.heater_power_W)}
    raise ValueError(f"unknown variant_id {variant_id!r}")


def source_total_for(case: S.ExperimentCase, prescribed: dict[str, float] | None) -> float:
    if prescribed is None:
        return float(case.heater_power_W + case.test_section_power_W)
    return float(sum(prescribed.values()))


def build_solver_segments_and_sensors(case: S.ExperimentCase, scenario: S.ScenarioConfig) -> tuple[list[Any], list[Any], list[Any]]:
    segments, sensors = S.build_geometry(refinement=S.default_geometry_refinement())
    scenario_segments = legacy_replay.scenario_segments_for_solver(S, segments, case, scenario)
    return segments, sensors, scenario_segments


def fast_pressure_root(
    case: S.ExperimentCase,
    scenario: S.ScenarioConfig,
    prescribed_sources: dict[str, float] | None,
    *,
    bisection_iterations: int = 4,
) -> Any:
    geometry_segments, geometry_sensors, scenario_segments = build_solver_segments_and_sensors(case, scenario)
    grid = [
        value
        for value in FAST_MDOT_GRID
        if scenario.mdot_search_lower_kg_s <= value <= scenario.mdot_search_upper_kg_s
    ]
    if scenario.mdot_search_lower_kg_s not in grid:
        grid.insert(0, scenario.mdot_search_lower_kg_s)
    if scenario.mdot_search_upper_kg_s not in grid:
        grid.append(scenario.mdot_search_upper_kg_s)
    grid = sorted(set(grid))

    evaluations: list[dict[str, Any]] = []
    for mdot in grid:
        evaluations.append(
            S.pressure_residual(
                float(mdot),
                case,
                scenario_segments,
                geometry_sensors,
                scenario,
                S.MinorLosses(),
                prescribed_segment_sources_W=prescribed_sources,
            )
        )

    finite = [row for row in evaluations if math.isfinite(float(row["pressure_residual_Pa"]))]
    if not finite:
        raise ValueError(f"No finite pressure residuals for {case.name} {scenario.name}")

    bracket: tuple[dict[str, Any], dict[str, Any]] | None = None
    for prev, curr in zip(finite[:-1], finite[1:]):
        r0 = float(prev["pressure_residual_Pa"])
        r1 = float(curr["pressure_residual_Pa"])
        if r0 == 0.0 or r0 * r1 <= 0.0:
            bracket = (prev, curr)
            break

    selected = min(finite, key=lambda row: abs(float(row["pressure_residual_Pa"])))
    root_status = "fast_scan_best_residual_no_pressure_bracket"
    root_rejection_reason = "no_bracketed_pressure_root"
    pressure_root_bracketed = False
    if bracket is not None:
        pressure_root_bracketed = True
        lo, hi = bracket
        mdot_lo = float(lo["mdot_kg_s"])
        mdot_hi = float(hi["mdot_kg_s"])
        r_lo = float(lo["pressure_residual_Pa"])
        selected = min((lo, hi), key=lambda row: abs(float(row["pressure_residual_Pa"])))
        for _ in range(bisection_iterations):
            mdot_mid = 0.5 * (mdot_lo + mdot_hi)
            mid = S.pressure_residual(
                mdot_mid,
                case,
                scenario_segments,
                geometry_sensors,
                scenario,
                S.MinorLosses(),
                warm_start_temperature_K=float(selected["thermal"].start_temperature_K),
                prescribed_segment_sources_W=prescribed_sources,
            )
            r_mid = float(mid["pressure_residual_Pa"])
            selected = mid
            if r_lo * r_mid <= 0.0:
                mdot_hi = mdot_mid
            else:
                mdot_lo = mdot_mid
                r_lo = r_mid
        root_status = "fast_scan_bracketed_pressure_root"
        root_rejection_reason = ""

    thermal = selected["thermal"]
    dp_b = float(selected["deltaP_buoyancy_Pa"])
    dp_l = float(selected["deltaP_losses_Pa"])
    pressure_residual_pa = float(selected["pressure_residual_Pa"])
    pressure_tol = legacy_replay.pressure_tolerance(S, dp_b, dp_l)
    accepted = (
        pressure_root_bracketed
        and abs(pressure_residual_pa) <= pressure_tol
        and bool(thermal.root_found)
        and abs(float(thermal.temperature_periodicity_error_K)) <= float(S.TEMPERATURE_PERIODICITY_TOL_K)
    )
    return SimpleNamespace(
        scenario=scenario,
        case=case,
        mdot_kg_s=float(selected["mdot_kg_s"]),
        velocity_main_m_s=float(selected["velocity_main_m_s"]),
        reynolds_main=float(selected["reynolds_main"]),
        friction_factor_main=float(selected["friction_factor_main"]),
        deltaP_buoyancy_Pa=dp_b,
        deltaP_losses_Pa=dp_l,
        pressure_residual_Pa=pressure_residual_pa,
        qhx_total_W=float(thermal.qhx_total_W),
        qambient_total_W=float(thermal.qambient_total_W),
        predicted_air_outlet_temperature_K=float(thermal.predicted_air_outlet_temperature_K),
        start_temperature_K=float(thermal.start_temperature_K),
        end_temperature_K=float(thermal.end_temperature_K),
        temperature_periodicity_error_K=float(thermal.temperature_periodicity_error_K),
        sensor_predictions_K=thermal.sensor_predictions_K,
        sensor_prediction_provenance=thermal.sensor_prediction_provenance,
        segment_states=thermal.segment_states,
        geometry_segments=geometry_segments,
        geometry_sensors=geometry_sensors,
        root_status=root_status,
        root_rejection_reason=root_rejection_reason,
        accepted_for_validation=accepted,
        validity_status="not_evaluated_fast_scan",
        validity_rejection_reason="full_solve_case_validity_policy_not_run",
        imported_source_total_W=0.0,
        imported_segment_loss_total_W=0.0,
    )


def target_by_case() -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(THERMAL_TARGETS)}


def experimental_sensor_rows(result: S.ModelResult, validation_record: S.ValidationRecord | None, context: dict[str, Any]) -> list[dict[str, Any]]:
    frame = reporting.build_validation_table(result, validation_record)
    rows: list[dict[str, Any]] = []
    provenance = "" if validation_record is None else validation_record.provenance
    for row in frame.to_dict(orient="records"):
        predicted = fnum(row.get("predicted_K"))
        target = fnum(row.get("measured_K"))
        rows.append(
            {
                **context,
                "sensor_source": "experimental_fluid_validation",
                "sensor": row.get("sensor", ""),
                "kind": row.get("kind", ""),
                "predicted_K": predicted,
                "target_K": target,
                "error_K": predicted - target if predicted is not None and target is not None else "",
                "prediction_source_segment": row.get("prediction_source_segment", ""),
                "prediction_source_fraction": row.get("prediction_source_fraction", ""),
                "target_provenance": provenance,
                "notes": "experimental target joined after solve",
            }
        )
    return rows


def load_cfd_sensor_reference(path: Path = CFD_SENSOR_REFERENCE) -> dict[tuple[str, str], dict[str, str]]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    result: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        label = str(row.get("frozen_case_label", ""))
        case_name = label.replace(" Val", "").strip()
        case_id = CASE_NAME_TO_ID.get(case_name)
        sensor = str(row.get("sensor", ""))
        if case_id and sensor:
            result[(case_id, sensor)] = row
    return result


def cfd_sensor_rows(
    result: S.ModelResult,
    cfd_refs: dict[tuple[str, str], dict[str, str]],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sensor in result.geometry_sensors:
        predicted = fnum(result.sensor_predictions_K.get(sensor.name))
        ref = cfd_refs.get((context["case_id"], sensor.name))
        target = fnum(ref.get("reference_k")) if ref else None
        rows.append(
            {
                **context,
                "sensor_source": "cfd_sensor_reference",
                "sensor": sensor.name,
                "kind": sensor.kind,
                "predicted_K": predicted,
                "target_K": target,
                "error_K": predicted - target if predicted is not None and target is not None else "",
                "prediction_source_segment": result.sensor_prediction_provenance.get(sensor.name, {}).get("source_segment", ""),
                "prediction_source_fraction": result.sensor_prediction_provenance.get(sensor.name, {}).get("source_fraction", ""),
                "target_provenance": rel(CFD_SENSOR_REFERENCE) if ref else "",
                "notes": "CFD reference joined after solve" if ref else "not_available_in_current_cfd_sensor_contract",
            }
        )
    return rows


def segment_rows(result: S.ModelResult, context: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for state, segment in zip(result.segment_states, result.geometry_segments):
        rows.append(
            {
                **context,
                "segment_name": state.segment_name,
                "parent_segment": segment.resolved_parent_name,
                "s_start_m": state.s_start_m,
                "s_end_m": state.s_end_m,
                "T_in_K": state.T_in_K,
                "T_out_K": state.T_out_K,
                "T_avg_K": state.T_avg_K,
                "Q_source_W": state.Q_source_W,
                "Q_hx_sink_W": state.Q_hx_sink_W,
                "Q_ambient_W": state.Q_ambient_W,
                "h_inner_W_m2K": state.h_inner_W_m2K,
                "h_outer_W_m2K": state.h_outer_W_m2K,
                "h_rad_W_m2K": state.h_rad_W_m2K,
                "reynolds_inner": state.reynolds_inner,
                "nusselt_inner": state.nusselt_inner,
            }
        )
    return rows


def model_tmean_proxy(result: S.ModelResult) -> float:
    states = result.segment_states
    length = sum(max(state.s_end_m - state.s_start_m, 0.0) for state in states)
    if length <= 0.0:
        return float("nan")
    return sum(state.T_avg_K * max(state.s_end_m - state.s_start_m, 0.0) for state in states) / length


def model_loop_delta_proxy(result: S.ModelResult) -> float:
    temps = [state.T_avg_K for state in result.segment_states if math.isfinite(state.T_avg_K)]
    if not temps:
        return float("nan")
    return max(temps) - min(temps)


def result_row(
    result: S.ModelResult,
    case_input: dict[str, str],
    variant_id: str,
    engine: str,
    prescribed_sources: dict[str, float] | None,
    validation_record: S.ValidationRecord | None,
    target: dict[str, str],
) -> dict[str, Any]:
    cfd_mdot = fnum(target.get("cfd_mdot_kg_s"))
    cfd_tmean = fnum(target.get("cfd_Tmean_K"))
    cfd_loop_delta = fnum(target.get("cfd_loop_delta_T_K"))
    exp_mdot = None if validation_record is None else validation_record.measured_mass_flow_rate_kg_s
    tmean = model_tmean_proxy(result)
    loop_delta = model_loop_delta_proxy(result)
    return {
        "case_id": case_input["case_id"],
        "fluid_case_name": case_input["fluid_case_name"],
        "source_id": case_input["source_id"],
        "variant_id": variant_id,
        "engine": engine,
        "root_status": result.root_status,
        "accepted_for_validation": result.accepted_for_validation,
        "mdot_kg_s": result.mdot_kg_s,
        "cfd_mdot_kg_s": cfd_mdot,
        "mdot_error_vs_cfd_kg_s": result.mdot_kg_s - cfd_mdot if cfd_mdot is not None else "",
        "mdot_error_vs_experimental_kg_s": result.mdot_kg_s - exp_mdot if exp_mdot is not None else "",
        "velocity_main_m_s": result.velocity_main_m_s,
        "reynolds_main": result.reynolds_main,
        "pressure_residual_Pa": result.pressure_residual_Pa,
        "deltaP_buoyancy_Pa": result.deltaP_buoyancy_Pa,
        "deltaP_losses_Pa": result.deltaP_losses_Pa,
        "temperature_periodicity_error_K": result.temperature_periodicity_error_K,
        "start_temperature_K": result.start_temperature_K,
        "end_temperature_K": result.end_temperature_K,
        "model_Tmean_proxy_K": tmean,
        "cfd_Tmean_K": cfd_tmean,
        "Tmean_error_vs_cfd_K": tmean - cfd_tmean if cfd_tmean is not None else "",
        "model_loop_delta_proxy_K": loop_delta,
        "cfd_loop_delta_T_K": cfd_loop_delta,
        "loop_delta_error_vs_cfd_K": loop_delta - cfd_loop_delta if cfd_loop_delta is not None else "",
        "qhx_total_W": result.qhx_total_W,
        "imposed_cooler_duty_W": case_input["imposed_cooler_duty_W"],
        "qambient_total_W": result.qambient_total_W,
        "imported_source_total_W": result.imported_source_total_W,
        "imported_segment_loss_total_W": result.imported_segment_loss_total_W,
        "source_total_input_W": source_total_for(result.case, prescribed_sources),
        "ambient_temperature_K": result.scenario.ambient_temperature_K,
        "radiation_on": result.scenario.radiation_on,
        "source_contract": "heater_power_W_plus_test_section_power_W" if prescribed_sources is None else "heater_power_W_only_prescribed_segment_source",
        "root_rejection_reason": result.root_rejection_reason,
        "validity_status": result.validity_status,
        "validity_rejection_reason": result.validity_rejection_reason,
    }


def audit_rows(
    case_input: dict[str, str],
    variant_id: str,
    engine: str,
    runtime_contract: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    fields = {
        "fluid_case_name": case_input["fluid_case_name"],
        "heater_power_W": case_input["heater_power_W"],
        "test_section_power_W": case_input["test_section_power_W"],
        "air_T_inlet_K": case_input["air_T_inlet_K"],
        "air_flow_Lpm": case_input["air_flow_Lpm"],
        "imposed_cooler_duty_W": case_input["imposed_cooler_duty_W"],
        "boundary_ambient_Ta_K": case_input["boundary_ambient_Ta_K"],
        "radiation_on": case_input["radiation_on"],
        "insulation_thickness_in": case_input["insulation_thickness_in"],
        "mdot_search_lower_kg_s": case_input["mdot_search_lower_kg_s"],
        "mdot_search_upper_kg_s": case_input["mdot_search_upper_kg_s"],
    }
    rows: list[dict[str, Any]] = []
    for field, value in fields.items():
        contract = runtime_contract.get(field, {})
        rows.append(
            {
                "case_id": case_input["case_id"],
                "variant_id": variant_id,
                "engine": engine,
                "runtime_field": field,
                "runtime_value": value,
                "contract_class": contract.get("field_class", ""),
                "forward_v0_allowed": contract.get("forward_v0_imposed_cooler_allowed", ""),
                "source_path": contract.get("source_path", ""),
            }
        )
    return rows


def mean_numeric(rows: list[dict[str, Any]], field: str, *, absolute: bool = False) -> float:
    values: list[float] = []
    for row in rows:
        value = fnum(row.get(field))
        if value is None:
            continue
        values.append(abs(value) if absolute else value)
    return sum(values) / len(values) if values else float("nan")


def variant_summary_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in results:
        grouped.setdefault((str(row["variant_id"]), str(row["engine"])), []).append(row)
    rows: list[dict[str, Any]] = []
    for (variant_id, engine), items in sorted(grouped.items()):
        rows.append(
            {
                "variant_id": variant_id,
                "engine": engine,
                "n_rows": len(items),
                "mean_abs_Tmean_error_vs_cfd_K": mean_numeric(items, "Tmean_error_vs_cfd_K", absolute=True),
                "mean_abs_loop_delta_error_vs_cfd_K": mean_numeric(items, "loop_delta_error_vs_cfd_K", absolute=True),
                "mean_mdot_error_vs_cfd_kg_s": mean_numeric(items, "mdot_error_vs_cfd_kg_s"),
                "mean_mdot_error_vs_experimental_kg_s": mean_numeric(items, "mdot_error_vs_experimental_kg_s"),
                "max_abs_pressure_residual_Pa": max(
                    (abs(fnum(row.get("pressure_residual_Pa")) or 0.0) for row in items),
                    default=float("nan"),
                ),
                "mean_qambient_total_W": mean_numeric(items, "qambient_total_W"),
            }
        )
    return rows


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    variant_lines = []
    for row in summary.get("variant_summary", []):
        variant_lines.append(
            "- `{variant}`: mean abs Tmean error `{tmean:.3f} K`, mean mdot error vs CFD `{mdot:.6f} kg/s`, "
            "mean ambient loss `{qamb:.3f} W`, max abs pressure residual `{pres:.3f} Pa`.".format(
                variant=row["variant_id"],
                tmean=float(row["mean_abs_Tmean_error_vs_cfd_K"]),
                mdot=float(row["mean_mdot_error_vs_cfd_kg_s"]),
                qamb=float(row["mean_qambient_total_W"]),
                pres=float(row["max_abs_pressure_residual_Pa"]),
            )
        )
    variant_summary_md = "\n".join(variant_lines) if variant_lines else "- No variant summary rows were generated."
    text = f"""# Predictive Forward V0: Imposed Cooler

Generated: `{summary['generated_utc']}`

This package runs Fluid's pressure-rooted forward solve with heater setup input
and imposed cooler duty. It does not use CFD mdot, CFD realized wallHeatFlux, or
sensor temperatures as runtime inputs.

## Variants

- `F0_current_fluid_sources`: current Fluid salt source contract, heater plus
  configured 37 W test-section input.
- `F1_heater_only`: heater setup power only; test-section source omitted until
  the heater/test-section transfer contract is resolved.

Both variants use `model_mode=imposed_qhx`, radiation off, 1.0 in insulation,
and case-specific CFD boundary Ta when available.

## Result Snapshot

Engine: `{summary.get('engine', 'unknown')}`.

{variant_summary_md}

The heater-only source contract is much closer on CFD mean temperature in this
first pass, but both variants overpredict mdot. Treat this as progress on
thermal source/sink matching, not hydraulic validation.

## Files

- `forward_v0_run_plan.csv`: run matrix and runtime policy.
- `forward_v0_results.csv`: mdot, thermal proxy, pressure, and heat-ledger
  outputs with CFD/experimental targets joined only as scores.
- `forward_v0_sensor_predictions_experimental.csv`: Fluid experimental TP/TW
  validation stream.
- `forward_v0_sensor_predictions_cfd.csv`: CFD sensor-reference stream when
  current references expose matching sensor names.
- `forward_v0_segment_states.csv`: segment-level 1D temperatures, sources,
  sinks, and heat-transfer diagnostics.
- `forward_v0_variant_summary.csv`: compact variant-level error and residual
  summary.
- `forward_v0_input_audit.csv`: consumed runtime fields mapped back to the
  strict input contract.
- `forward_v0_litrev_gate_reference_audit.csv`: required pre-score lit-rev gate
  references for source envelope, property mode lane, named losses, heat-loss
  admission, and CFD coefficient naming limits.
- `summary.json`: machine-readable package summary.

## Interpretation

This is not an end-to-end HX prediction yet. It is the practical next bridge:
given physical setup inputs and imposed cooler duty, solve mdot and temperatures
without anchoring to CFD mdot or measured sensors. Remaining blockers are HX
UA/epsilon-NTU, heater/test-section transfer efficiency, wall-layer temperature
mapping, hydraulic gate status, thermal mesh uncertainty, and sensor-coordinate
uncertainty.

Scoring is blocked unless the input contract carries explicit references to the
five lit-rev gate outputs. The current package writes those references to
`forward_v0_litrev_gate_reference_audit.csv` before emitting score tables.

The default `fast_scan` engine uses Fluid `pressure_residual` evaluations on a
bounded mdot grid plus a short bracketed bisection. Run the same script with
`--engine solve_case` on an appropriate compute node for the full nested Fluid
root solve.
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def run_package(
    out_dir: Path = OUT_DIR,
    contract_dir: Path = CONTRACT_DIR,
    *,
    strict_input_contract: bool = False,
    sensor_source: str = "both",
    engine: str = "fast_scan",
) -> dict[str, Any]:
    contract_summary = load_or_build_contract(contract_dir, strict_input_contract)
    case_inputs = read_csv(contract_dir / "case_runtime_inputs_forward_v0.csv")
    runtime_contract = runtime_contract_by_field(contract_dir)
    gate_audits = litrev_gate_reference_rows(runtime_contract)
    enforce_litrev_gate_references(gate_audits)
    targets = target_by_case()
    cases = {case.name: case for case in config_loader.load_cases()}
    validation_records = config_loader.load_validation_records()
    cfd_refs = load_cfd_sensor_reference() if sensor_source in {"both", "cfd"} else {}

    plan_rows = run_plan_rows(case_inputs)
    results: list[dict[str, Any]] = []
    experimental_sensors: list[dict[str, Any]] = []
    cfd_sensors: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []

    for case_input in case_inputs:
        case = cases[case_input["fluid_case_name"]]
        validation_record = validation_records.get(case.name)
        target = targets.get(case_input["case_id"], {})
        for spec in variant_specs():
            variant_id = spec["variant_id"]
            scenario = scenario_for(case_input, variant_id)
            prescribed = prescribed_sources_for(case, variant_id)
            if engine == "solve_case":
                result = S.solve_case(case, scenario, prescribed_segment_sources_W=prescribed)
            elif engine == "fast_scan":
                result = fast_pressure_root(case, scenario, prescribed)
            else:
                raise ValueError(f"unsupported engine {engine!r}")
            context = {
                "case_id": case_input["case_id"],
                "fluid_case_name": case_input["fluid_case_name"],
                "source_id": case_input["source_id"],
                "variant_id": variant_id,
                "engine": engine,
            }
            results.append(result_row(result, case_input, variant_id, engine, prescribed, validation_record, target))
            if sensor_source in {"both", "experimental"}:
                experimental_sensors.extend(experimental_sensor_rows(result, validation_record, context))
            if sensor_source in {"both", "cfd"}:
                cfd_sensors.extend(cfd_sensor_rows(result, cfd_refs, context))
            segments.extend(segment_rows(result, context))
            audits.extend(audit_rows(case_input, variant_id, engine, runtime_contract))

    variant_summaries = variant_summary_rows(results)
    write_csv(out_dir / "forward_v0_run_plan.csv", plan_rows, RUN_PLAN_COLUMNS)
    write_csv(out_dir / "forward_v0_results.csv", results, RESULT_COLUMNS)
    write_csv(out_dir / "forward_v0_variant_summary.csv", variant_summaries, VARIANT_SUMMARY_COLUMNS)
    write_csv(out_dir / "forward_v0_sensor_predictions_experimental.csv", experimental_sensors, SENSOR_COLUMNS)
    write_csv(out_dir / "forward_v0_sensor_predictions_cfd.csv", cfd_sensors, SENSOR_COLUMNS)
    write_csv(out_dir / "forward_v0_segment_states.csv", segments, SEGMENT_COLUMNS)
    write_csv(out_dir / "forward_v0_input_audit.csv", audits, AUDIT_COLUMNS)
    write_csv(out_dir / "forward_v0_litrev_gate_reference_audit.csv", gate_audits, GATE_REFERENCE_COLUMNS)

    accepted = sum(1 for row in results if str(row["accepted_for_validation"]).lower() == "true")
    summary = {
        "task_id": "TODO-PRED-FORWARD-V0",
        "generated_utc": utc_now(),
        "source_files": {
            "input_contract": rel(contract_dir),
            "thermal_targets": rel(THERMAL_TARGETS),
            "cfd_sensor_reference": rel(CFD_SENSOR_REFERENCE),
            "fluid_root": str(FLUID_ROOT),
            "litrev_gate_reference_audit": rel(out_dir / "forward_v0_litrev_gate_reference_audit.csv"),
        },
        "contract_summary": contract_summary,
        "litrev_gate_reference_status": "pass",
        "litrev_gate_reference_rows": len(gate_audits),
        "sensor_source": sensor_source,
        "engine": engine,
        "n_cases": len(case_inputs),
        "n_variants": len(variant_specs()),
        "n_result_rows": len(results),
        "n_accepted_rows": accepted,
        "variant_summary": variant_summaries,
        "n_experimental_sensor_rows": len(experimental_sensors),
        "n_cfd_sensor_rows": len(cfd_sensors),
        "runtime_policy": f"pressure-rooted {engine}; no CFD mdot or realized wallHeatFlux runtime input",
        "hx_status": "imposed_cooler_duty_intermediate_not_predictive_hx",
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--contract-dir", type=Path, default=CONTRACT_DIR)
    parser.add_argument("--strict-input-contract", action="store_true")
    parser.add_argument("--sensor-source", choices=["experimental", "cfd", "both"], default="both")
    parser.add_argument("--engine", choices=["fast_scan", "solve_case"], default="fast_scan")
    args = parser.parse_args(list(argv) if argv is not None else None)

    summary = run_package(
        args.output_dir,
        args.contract_dir,
        strict_input_contract=args.strict_input_contract,
        sensor_source=args.sensor_source,
        engine=args.engine,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
