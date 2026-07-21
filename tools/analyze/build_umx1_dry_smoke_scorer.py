#!/usr/bin/env python3
"""Build and optionally run the UMX1 dry/smoke scorer package.

The dry path writes predeclared UMX1 candidates, split/runtime contracts, and a
compute harness. The smoke path runs the small Fluid solve_case matrix only for
predeclared Salt2/Salt3/Salt4 nominal rows and labels every output no-admission.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shlex
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FLUID_ROOT = (REPO_ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
if str(FLUID_ROOT) not in sys.path:
    sys.path.insert(0, str(FLUID_ROOT))

from tamu_loop_model_v2 import config_loader, reporting, solver as S  # noqa: E402
from tools.analyze import run_predictive_forward_v0_imposed_cooler as forward_v0  # noqa: E402


TASK_ID = "AGENT-544"
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer"
INPUT_CONTRACT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract"
SPLIT_POLICY = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy"
    / "canonical_final_predictive_split_policy.csv"
)
AGENT_540_PACKAGE = (
    REPO_ROOT / "work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation"
)
FOCUS_PARENT_SEGMENTS = ("left_lower_vertical", "test_section", "left_upper_vertical")
EXECUTABLE_SOURCE_IDS = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
}
FORBIDDEN_RUNTIME_FIELDS = {
    "cfd_mdot_kg_s",
    "heater_wallHeatFlux_W",
    "cooler_wallHeatFlux_W",
    "test_section_wallHeatFlux_W",
    "imposed_cooler_duty_W",
    "TP_TW_measured_K",
    "CFD_sensor_reference_K",
}
CONSERVATION_TOL_W = 1.0e-9


CANDIDATE_COLUMNS = [
    "candidate_id",
    "upcomer_mixing_mode",
    "upcomer_exchange_multiplier",
    "upcomer_exchange_parent_segments",
    "candidate_role",
    "fit_allowed",
    "model_selection_allowed",
    "admission_status",
    "notes",
]
SPLIT_COLUMNS = [
    "case_key",
    "source_key",
    "case_id",
    "fluid_case_name",
    "split_role",
    "fit_allowed",
    "model_selection_allowed",
    "score_allowed",
    "use_status",
    "executable_status",
    "executable_in_smoke",
    "blocked_reason",
    "no_admission_policy",
]
SCENARIO_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "candidate_id",
    "scenario_name",
    "model_mode",
    "radiation_on",
    "ambient_temperature_K",
    "insulation_thickness_in",
    "air_inlet_temperature_K",
    "air_flow_Lpm",
    "imposed_qhx_W",
    "upcomer_mixing_mode",
    "upcomer_exchange_multiplier",
    "upcomer_exchange_parent_segments",
    "runtime_status",
    "admission_status",
]
AUDIT_COLUMNS = [
    "case_id",
    "candidate_id",
    "runtime_field",
    "runtime_value",
    "field_class",
    "runtime_allowed",
    "audit_status",
    "source_path",
    "notes",
]
RESULT_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "candidate_id",
    "scenario_name",
    "engine",
    "root_status",
    "accepted_for_validation",
    "root_rejection_reason",
    "validity_status",
    "validity_rejection_reason",
    "mdot_kg_s",
    "pressure_residual_Pa",
    "temperature_periodicity_error_K",
    "deltaP_buoyancy_Pa",
    "deltaP_losses_Pa",
    "qhx_total_W",
    "qambient_total_W",
    "start_temperature_K",
    "end_temperature_K",
    "predicted_air_outlet_temperature_K",
    "admission_status",
]
ROOT_COLUMNS = [
    "case_id",
    "candidate_id",
    "engine",
    "root_status",
    "accepted_for_validation",
    "pressure_residual_Pa",
    "temperature_periodicity_error_K",
    "root_gate_status",
    "notes",
]
SEGMENT_COLUMNS = [
    "case_id",
    "candidate_id",
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
    "upcomer_exchange_Q_main_to_reservoir_W",
    "upcomer_exchange_Q_reservoir_to_main_W",
    "upcomer_exchange_reservoir_energy_residual_W",
    "upcomer_main_stream_temperature_K",
    "upcomer_reservoir_temperature_K",
    "upcomer_prediction_stream",
]
CONSERVATION_COLUMNS = [
    "case_id",
    "candidate_id",
    "engine",
    "active_umx_segment_count",
    "finite_temperature_count",
    "max_abs_reservoir_energy_residual_W",
    "net_exchange_residual_W",
    "conservation_gate_status",
    "notes",
]
PROBE_COLUMNS = [
    "case_id",
    "candidate_id",
    "engine",
    "probe_group",
    "n_sensors",
    "mean_abs_error_K",
    "max_abs_error_K",
    "target_join_policy",
    "admission_status",
]
ADMISSION_COLUMNS = [
    "gate_id",
    "status",
    "blocks_expansion",
    "blocks_admission",
    "evidence",
    "next_action",
]
EXPECTED_COLUMNS = ["path", "producer", "required_for_validation", "notes"]

SUMMARY_CONSISTENCY_FIELDS = [
    "candidate_count",
    "executable_case_count",
    "planned_smoke_rows",
    "smoke_result_rows",
    "root_pass_rows",
    "root_rows",
    "conservation_pass_rows",
    "conservation_rows",
    "split_executable_rows",
    "salt1_status",
    "admission_status",
    "expansion_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def q(path: Path) -> str:
    return shlex.quote(str(path))


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def fnum(value: Any, default: float | None = None) -> float | None:
    if value in ("", None):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def btext(value: Any) -> str:
    return "true" if bool(value) else "false"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def candidate_rows() -> list[dict[str, Any]]:
    parent_segments = ";".join(FOCUS_PARENT_SEGMENTS)
    return [
        {
            "candidate_id": "UMX1_disabled_baseline",
            "upcomer_mixing_mode": "disabled",
            "upcomer_exchange_multiplier": 0.0,
            "upcomer_exchange_parent_segments": parent_segments,
            "candidate_role": "no_op_baseline_contract_check",
            "fit_allowed": "false",
            "model_selection_allowed": "false",
            "admission_status": "not_admitted_smoke_only",
            "notes": "Verifies AGENT-540 no-op default path.",
        },
        {
            "candidate_id": "UMX1_exchange_0p01",
            "upcomer_mixing_mode": "energy_conserving_exchange_v1",
            "upcomer_exchange_multiplier": 0.01,
            "upcomer_exchange_parent_segments": parent_segments,
            "candidate_role": "low_exchange_smoke",
            "fit_allowed": "false",
            "model_selection_allowed": "false",
            "admission_status": "not_admitted_smoke_only",
            "notes": "Predeclared smoke point, not selected from residuals.",
        },
        {
            "candidate_id": "UMX1_exchange_0p05",
            "upcomer_mixing_mode": "energy_conserving_exchange_v1",
            "upcomer_exchange_multiplier": 0.05,
            "upcomer_exchange_parent_segments": parent_segments,
            "candidate_role": "higher_exchange_smoke",
            "fit_allowed": "false",
            "model_selection_allowed": "false",
            "admission_status": "not_admitted_smoke_only",
            "notes": "Predeclared smoke point, not selected from residuals.",
        },
    ]


def case_input_rows() -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(INPUT_CONTRACT_DIR / "case_runtime_inputs_forward_v0.csv")
        if row["source_id"] in EXECUTABLE_SOURCE_IDS
    ]


def runtime_contract_by_field() -> dict[str, dict[str, str]]:
    return {row["field_name"]: row for row in read_csv(INPUT_CONTRACT_DIR / "runtime_input_contract.csv")}


def split_contract_rows(case_inputs: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_source = {row["source_id"]: row for row in case_inputs}
    rows: list[dict[str, Any]] = []
    for split in read_csv(SPLIT_POLICY):
        source_key = split["source_key"]
        case_input = by_source.get(source_key)
        executable = case_input is not None and split["split_role"] == "final_training"
        blocked_reason = ""
        if executable:
            executable_status = "smoke_executable_nominal_current_schema"
        elif split["case_key"].startswith("salt1"):
            executable_status = "blocked_schema_promotion_missing"
            blocked_reason = "Salt1 must be promoted into the Salt2-4 postprocessing/runtime schema before this scorer consumes it."
        elif split["split_role"] in {"holdout_testing", "external_test", "future_holdout_candidate", "new_cfd_holdout_candidate"}:
            executable_status = "not_in_smoke_score_only_or_future_row"
            blocked_reason = "Holdout/external/future rows are not used by the UMX1 smoke."
        else:
            executable_status = "not_in_current_input_contract"
            blocked_reason = "Row is outside the current executable predictive input contract."
        rows.append(
            {
                "case_key": split["case_key"],
                "source_key": source_key,
                "case_id": case_input["case_id"] if case_input else "",
                "fluid_case_name": case_input["fluid_case_name"] if case_input else "",
                "split_role": split["split_role"],
                "fit_allowed": "false",
                "model_selection_allowed": "false",
                "score_allowed": split["score_allowed"],
                "use_status": split["use_status"],
                "executable_status": executable_status,
                "executable_in_smoke": btext(executable),
                "blocked_reason": blocked_reason,
                "no_admission_policy": "Smoke checks roots/conservation only; no fitted parameter or scientific admission.",
            }
        )
    return rows


def scenario_name(case_id: str, candidate_id: str) -> str:
    return f"umx1_smoke__{case_id}__{candidate_id}"


def scenario_contract_rows(case_inputs: list[dict[str, str]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_input in case_inputs:
        for candidate in candidates:
            rows.append(
                {
                    "case_id": case_input["case_id"],
                    "fluid_case_name": case_input["fluid_case_name"],
                    "source_id": case_input["source_id"],
                    "candidate_id": candidate["candidate_id"],
                    "scenario_name": scenario_name(case_input["case_id"], candidate["candidate_id"]),
                    "model_mode": "predictive_airside_hx",
                    "radiation_on": case_input["radiation_on"],
                    "ambient_temperature_K": case_input["boundary_ambient_Ta_K"],
                    "insulation_thickness_in": case_input["insulation_thickness_in"],
                    "air_inlet_temperature_K": case_input["air_T_inlet_K"],
                    "air_flow_Lpm": case_input["air_flow_Lpm"],
                    "imposed_qhx_W": "",
                    "upcomer_mixing_mode": candidate["upcomer_mixing_mode"],
                    "upcomer_exchange_multiplier": candidate["upcomer_exchange_multiplier"],
                    "upcomer_exchange_parent_segments": candidate["upcomer_exchange_parent_segments"],
                    "runtime_status": "runtime_legal_setup_only",
                    "admission_status": "not_admitted_smoke_only",
                }
            )
    return rows


def runtime_audit_rows(
    case_inputs: list[dict[str, str]],
    candidates: list[dict[str, Any]],
    runtime_contract: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_input in case_inputs:
        for candidate in candidates:
            allowed_fields = {
                "fluid_case_name": case_input["fluid_case_name"],
                "heater_power_W": case_input["heater_power_W"],
                "test_section_power_W": case_input["test_section_power_W"],
                "air_T_inlet_K": case_input["air_T_inlet_K"],
                "air_flow_Lpm": case_input["air_flow_Lpm"],
                "boundary_ambient_Ta_K": case_input["boundary_ambient_Ta_K"],
                "radiation_on": case_input["radiation_on"],
                "insulation_thickness_in": case_input["insulation_thickness_in"],
                "mdot_search_lower_kg_s": case_input["mdot_search_lower_kg_s"],
                "mdot_search_upper_kg_s": case_input["mdot_search_upper_kg_s"],
                "upcomer_mixing_mode": candidate["upcomer_mixing_mode"],
                "upcomer_exchange_multiplier": candidate["upcomer_exchange_multiplier"],
                "upcomer_exchange_parent_segments": candidate["upcomer_exchange_parent_segments"],
            }
            for field, value in allowed_fields.items():
                contract = runtime_contract.get(field, {})
                rows.append(
                    {
                        "case_id": case_input["case_id"],
                        "candidate_id": candidate["candidate_id"],
                        "runtime_field": field,
                        "runtime_value": value,
                        "field_class": contract.get("field_class", "setup_or_model_input"),
                        "runtime_allowed": "true",
                        "audit_status": "pass",
                        "source_path": contract.get("source_path", rel(AGENT_540_PACKAGE)),
                        "notes": "Runtime setup/model input only.",
                    }
                )
            for field in sorted(FORBIDDEN_RUNTIME_FIELDS):
                rows.append(
                    {
                        "case_id": case_input["case_id"],
                        "candidate_id": candidate["candidate_id"],
                        "runtime_field": field,
                        "runtime_value": "",
                        "field_class": runtime_contract.get(field, {}).get("field_class", "forbidden_or_validation_target"),
                        "runtime_allowed": "false",
                        "audit_status": "pass_absent",
                        "source_path": runtime_contract.get(field, {}).get("source_path", ""),
                        "notes": "Forbidden runtime input is absent before solve.",
                    }
                )
    return rows


def scenario_from_contract(row: dict[str, str]) -> S.ScenarioConfig:
    parent_segments = [value for value in row["upcomer_exchange_parent_segments"].split(";") if value]
    return S.ScenarioConfig(
        name=row["scenario_name"],
        ambient_temperature_K=float(row["ambient_temperature_K"]),
        insulation_thickness_in=float(row["insulation_thickness_in"]),
        radiation_on=str(row["radiation_on"]).strip().lower() == "true",
        model_mode="predictive_airside_hx",
        imposed_qhx_W=None,
        air_flow_Lpm=float(row["air_flow_Lpm"]),
        air_inlet_temperature_K=float(row["air_inlet_temperature_K"]),
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=float(row["mdot_search_lower_kg_s"])
        if "mdot_search_lower_kg_s" in row
        else S.DEFAULT_MDOT_SEARCH_LOWER_KG_S,
        mdot_search_upper_kg_s=float(row["mdot_search_upper_kg_s"])
        if "mdot_search_upper_kg_s" in row
        else S.DEFAULT_MDOT_SEARCH_UPPER_KG_S,
        upcomer_mixing_mode=row["upcomer_mixing_mode"],
        upcomer_exchange_multiplier=float(row["upcomer_exchange_multiplier"]),
        upcomer_exchange_parent_segments=parent_segments,
        upcomer_reservoir_heat_sources=[
            {"source": "setup_role_row_contract_placeholder", "runtime_policy": "setup_only_not_target"}
        ],
    )


def scenario_for(case_input: dict[str, str], candidate: dict[str, Any]) -> S.ScenarioConfig:
    return S.ScenarioConfig(
        name=scenario_name(case_input["case_id"], candidate["candidate_id"]),
        ambient_temperature_K=float(case_input["boundary_ambient_Ta_K"]),
        insulation_thickness_in=float(case_input["insulation_thickness_in"]),
        radiation_on=str(case_input["radiation_on"]).strip().lower() == "true",
        model_mode="predictive_airside_hx",
        imposed_qhx_W=None,
        air_flow_Lpm=float(case_input["air_flow_Lpm"]),
        air_inlet_temperature_K=float(case_input["air_T_inlet_K"]),
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=float(case_input["mdot_search_lower_kg_s"]),
        mdot_search_upper_kg_s=float(case_input["mdot_search_upper_kg_s"]),
        upcomer_mixing_mode=str(candidate["upcomer_mixing_mode"]),
        upcomer_exchange_multiplier=float(candidate["upcomer_exchange_multiplier"]),
        upcomer_exchange_parent_segments=list(FOCUS_PARENT_SEGMENTS),
        upcomer_reservoir_heat_sources=[
            {"source": "setup_role_row_contract_placeholder", "runtime_policy": "setup_only_not_target"}
        ],
    )


def result_row(result: Any, case_input: dict[str, str], candidate: dict[str, Any], engine: str) -> dict[str, Any]:
    return {
        "case_id": case_input["case_id"],
        "fluid_case_name": case_input["fluid_case_name"],
        "source_id": case_input["source_id"],
        "candidate_id": candidate["candidate_id"],
        "scenario_name": result.scenario.name,
        "engine": engine,
        "root_status": result.root_status,
        "accepted_for_validation": result.accepted_for_validation,
        "root_rejection_reason": result.root_rejection_reason,
        "validity_status": result.validity_status,
        "validity_rejection_reason": result.validity_rejection_reason,
        "mdot_kg_s": result.mdot_kg_s,
        "pressure_residual_Pa": result.pressure_residual_Pa,
        "temperature_periodicity_error_K": result.temperature_periodicity_error_K,
        "deltaP_buoyancy_Pa": result.deltaP_buoyancy_Pa,
        "deltaP_losses_Pa": result.deltaP_losses_Pa,
        "qhx_total_W": result.qhx_total_W,
        "qambient_total_W": result.qambient_total_W,
        "start_temperature_K": result.start_temperature_K,
        "end_temperature_K": result.end_temperature_K,
        "predicted_air_outlet_temperature_K": result.predicted_air_outlet_temperature_K,
        "admission_status": "not_admitted_smoke_only",
    }


def root_row(row: dict[str, Any]) -> dict[str, Any]:
    accepted = str(row["accepted_for_validation"]).lower() == "true"
    finite = all(
        fnum(row.get(field)) is not None
        for field in ("mdot_kg_s", "pressure_residual_Pa", "temperature_periodicity_error_K")
    )
    status = "pass" if row["root_status"] in {"accepted", "fast_scan_bracketed_pressure_root"} and accepted and finite else "fail"
    return {
        "case_id": row["case_id"],
        "candidate_id": row["candidate_id"],
        "engine": row["engine"],
        "root_status": row["root_status"],
        "accepted_for_validation": row["accepted_for_validation"],
        "pressure_residual_Pa": row["pressure_residual_Pa"],
        "temperature_periodicity_error_K": row["temperature_periodicity_error_K"],
        "root_gate_status": status,
        "notes": "Accepted pressure and temperature roots required for smoke expansion.",
    }


def segment_rows(result: Any, case_input: dict[str, str], candidate: dict[str, Any], engine: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for state, segment in zip(result.segment_states, result.geometry_segments):
        rows.append(
            {
                "case_id": case_input["case_id"],
                "candidate_id": candidate["candidate_id"],
                "engine": engine,
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
                "upcomer_exchange_Q_main_to_reservoir_W": state.upcomer_exchange_Q_main_to_reservoir_W,
                "upcomer_exchange_Q_reservoir_to_main_W": state.upcomer_exchange_Q_reservoir_to_main_W,
                "upcomer_exchange_reservoir_energy_residual_W": state.upcomer_exchange_reservoir_energy_residual_W,
                "upcomer_main_stream_temperature_K": state.upcomer_main_stream_temperature_K,
                "upcomer_reservoir_temperature_K": state.upcomer_reservoir_temperature_K,
                "upcomer_prediction_stream": state.upcomer_prediction_stream,
            }
        )
    return rows


def conservation_rows(segment_ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in segment_ledger:
        grouped[(str(row["case_id"]), str(row["candidate_id"]), str(row["engine"]))].append(row)
    rows: list[dict[str, Any]] = []
    for (case_id, candidate_id, engine), items in sorted(grouped.items()):
        active = [row for row in items if row.get("upcomer_prediction_stream")]
        residuals = [abs(fnum(row.get("upcomer_exchange_reservoir_energy_residual_W"), 0.0) or 0.0) for row in active]
        net = sum(fnum(row.get("upcomer_exchange_reservoir_energy_residual_W"), 0.0) or 0.0 for row in active)
        finite_temps = [
            row
            for row in active
            if fnum(row.get("upcomer_main_stream_temperature_K")) is not None
            and fnum(row.get("upcomer_reservoir_temperature_K")) is not None
        ]
        if candidate_id == "UMX1_disabled_baseline":
            status = "pass_noop" if not active else "fail_disabled_has_active_segments"
        else:
            status = (
                "pass"
                if active
                and len(finite_temps) == len(active)
                and max(residuals, default=0.0) <= CONSERVATION_TOL_W
                and abs(net) <= CONSERVATION_TOL_W
                else "fail"
            )
        rows.append(
            {
                "case_id": case_id,
                "candidate_id": candidate_id,
                "engine": engine,
                "active_umx_segment_count": len(active),
                "finite_temperature_count": len(finite_temps),
                "max_abs_reservoir_energy_residual_W": max(residuals, default=0.0),
                "net_exchange_residual_W": net,
                "conservation_gate_status": status,
                "notes": f"Tolerance {CONSERVATION_TOL_W:g} W; disabled candidate must remain inactive.",
            }
        )
    return rows


def probe_score_rows(
    result: Any,
    case_input: dict[str, str],
    candidate: dict[str, Any],
    validation_record: S.ValidationRecord | None,
    engine: str,
) -> list[dict[str, Any]]:
    if validation_record is None:
        return []
    frame = reporting.build_validation_table(result, validation_record)
    records = frame.to_dict(orient="records")
    groups: dict[str, list[dict[str, Any]]] = {
        "all_experimental": records,
        "tp": [row for row in records if str(row.get("kind", "")).upper() == "TP"],
        "tw": [row for row in records if str(row.get("kind", "")).upper() == "TW"],
        "umx_focus_segments": [
            row for row in records if str(row.get("prediction_source_segment", "")) in set(FOCUS_PARENT_SEGMENTS)
        ],
    }
    rows: list[dict[str, Any]] = []
    for group_id, items in groups.items():
        errors = [abs(value) for value in (fnum(row.get("error_K")) for row in items) if value is not None]
        rows.append(
            {
                "case_id": case_input["case_id"],
                "candidate_id": candidate["candidate_id"],
                "engine": engine,
                "probe_group": group_id,
                "n_sensors": len(errors),
                "mean_abs_error_K": sum(errors) / len(errors) if errors else "",
                "max_abs_error_K": max(errors) if errors else "",
                "target_join_policy": "experimental targets joined after solve only",
                "admission_status": "not_admitted_smoke_only",
            }
        )
    return rows


def no_admission_rows(
    results: list[dict[str, Any]],
    root_rows_: list[dict[str, Any]],
    conservation_rows_: list[dict[str, Any]],
    audit_rows_: list[dict[str, Any]],
    split_rows_: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime_pass = all(row["audit_status"] in {"pass", "pass_absent"} for row in audit_rows_)
    roots_pass = bool(root_rows_) and all(row["root_gate_status"] == "pass" for row in root_rows_)
    conservation_pass = bool(conservation_rows_) and all(
        row["conservation_gate_status"] in {"pass", "pass_noop"} for row in conservation_rows_
    )
    split_pass = (
        sum(str(row["executable_in_smoke"]).lower() == "true" for row in split_rows_) == 3
        and any(row["executable_status"] == "blocked_schema_promotion_missing" for row in split_rows_)
    )
    return [
        {
            "gate_id": "runtime_legality",
            "status": "pass" if runtime_pass else "fail",
            "blocks_expansion": btext(not runtime_pass),
            "blocks_admission": "true",
            "evidence": f"{len(audit_rows_)} runtime audit rows; forbidden runtime fields absent.",
            "next_action": "stop_before_grid" if not runtime_pass else "eligible_for_smoke_review_only",
        },
        {
            "gate_id": "accepted_roots",
            "status": "pass" if roots_pass else "fail_or_not_run",
            "blocks_expansion": btext(not roots_pass),
            "blocks_admission": "true",
            "evidence": f"{sum(row['root_gate_status'] == 'pass' for row in root_rows_)}/{len(root_rows_)} root rows pass.",
            "next_action": "stop_before_grid" if not roots_pass else "eligible_for_bounded_followup_only",
        },
        {
            "gate_id": "conservation_residual",
            "status": "pass" if conservation_pass else "fail_or_not_run",
            "blocks_expansion": btext(not conservation_pass),
            "blocks_admission": "true",
            "evidence": f"{sum(row['conservation_gate_status'] in {'pass', 'pass_noop'} for row in conservation_rows_)}/{len(conservation_rows_)} conservation rows pass.",
            "next_action": "stop_before_grid" if not conservation_pass else "eligible_for_bounded_followup_only",
        },
        {
            "gate_id": "split_discipline",
            "status": "pass" if split_pass else "fail",
            "blocks_expansion": btext(not split_pass),
            "blocks_admission": "true",
            "evidence": "Salt2/Salt3/Salt4 nominal executable; Salt1 explicitly blocked pending schema promotion.",
            "next_action": "promote Salt1 schema before final-training admission work",
        },
        {
            "gate_id": "scientific_admission",
            "status": "not_admitted_smoke_only",
            "blocks_expansion": "false" if results and roots_pass and conservation_pass and runtime_pass else "true",
            "blocks_admission": "true",
            "evidence": "This task is a smoke scorer only; no fitting, tuning, model selection, or admission.",
            "next_action": "open a separate scored-grid/admission row only after reviewing smoke artifacts",
        },
    ]


def expected_output_rows(out_dir: Path) -> list[dict[str, str]]:
    expected = [
        "umx1_candidate_definitions.csv",
        "umx1_case_split_contract.csv",
        "umx1_scenario_contracts.csv",
        "umx1_runtime_input_audit.csv",
        "umx1_smoke_results.csv",
        "umx1_root_status_by_case.csv",
        "umx1_segment_ledger.csv",
        "umx1_conservation_ledger.csv",
        "umx1_probe_smoke_score.csv",
        "umx1_no_admission_review.csv",
        "source_manifest.csv",
        "summary.json",
        "README.md",
    ]
    return [
        {
            "path": rel(out_dir / filename),
            "producer": "build_umx1_dry_smoke_scorer.py",
            "required_for_validation": "true",
            "notes": "Dry contract output" if "smoke" not in filename and "ledger" not in filename else "Smoke output after --run-smoke",
        }
        for filename in expected
    ]


def script_text(out_dir: Path) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail

ROOT={q(REPO_ROOT)}
OUT={q(out_dir)}
LOGS="${{OUT}}/logs"

cd "${{ROOT}}"
mkdir -p "${{LOGS}}"
module load python/3.12.11 2>/dev/null || true
echo "started_at=$(date +%Y-%m-%dT%H:%M:%S%z) host=$(hostname) job=${{SLURM_JOB_ID:-none}}" > "${{LOGS}}/run_provenance.env"
python3 tools/analyze/build_umx1_dry_smoke_scorer.py --output-dir "${{OUT}}" --dry-only > "${{LOGS}}/dry.log" 2>&1
python3 tools/analyze/build_umx1_dry_smoke_scorer.py --output-dir "${{OUT}}" --run-smoke --engine solve_case > "${{LOGS}}/smoke.log" 2>&1
python3 tools/analyze/build_umx1_dry_smoke_scorer.py --output-dir "${{OUT}}" --validate-existing > "${{LOGS}}/validate.log" 2>&1
echo "completed_at=$(date +%Y-%m-%dT%H:%M:%S%z)" >> "${{LOGS}}/run_provenance.env"
"""


def sbatch_text(out_dir: Path) -> str:
    return f"""#!/usr/bin/env bash
#SBATCH -J umx1_smoke
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 4
#SBATCH -t 06:00:00
#SBATCH -o {out_dir}/logs/slurm_%j.out
#SBATCH -e {out_dir}/logs/slurm_%j.err

set -euo pipefail
cd {q(REPO_ROOT)}
mkdir -p {q(out_dir / "logs")}
srun -N1 -n1 -c4 bash {q(out_dir / "scripts/run_umx1_smoke.sh")}
"""


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "source_type": "input",
            "path": rel(AGENT_540_PACKAGE),
            "used_for": "UMX1 API contract and guardrails",
            "mutation_status": "read_only",
        },
        {
            "source_type": "input",
            "path": rel(INPUT_CONTRACT_DIR),
            "used_for": "runtime input contract and executable Salt2-4 rows",
            "mutation_status": "read_only",
        },
        {
            "source_type": "input",
            "path": rel(SPLIT_POLICY),
            "used_for": "canonical split discipline and Salt1 blocker",
            "mutation_status": "read_only",
        },
        {
            "source_type": "input",
            "path": str(FLUID_ROOT),
            "used_for": "read-only Fluid solve_case import",
            "mutation_status": "read_only",
        },
        {
            "source_type": "output",
            "path": rel(OUT_DIR),
            "used_for": "UMX1 dry/smoke scorer package",
            "mutation_status": "mutated",
        },
    ]


def build_dry(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    candidates = candidate_rows()
    case_inputs = case_input_rows()
    runtime_contract = runtime_contract_by_field()
    split_rows_ = split_contract_rows(case_inputs)
    scenario_rows_ = scenario_contract_rows(case_inputs, candidates)
    audit_rows_ = runtime_audit_rows(case_inputs, candidates, runtime_contract)

    write_csv(out_dir / "umx1_candidate_definitions.csv", candidates, CANDIDATE_COLUMNS)
    write_csv(out_dir / "umx1_case_split_contract.csv", split_rows_, SPLIT_COLUMNS)
    write_csv(out_dir / "umx1_scenario_contracts.csv", scenario_rows_, SCENARIO_COLUMNS)
    write_csv(out_dir / "umx1_runtime_input_audit.csv", audit_rows_, AUDIT_COLUMNS)
    write_csv(out_dir / "expected_outputs.csv", expected_output_rows(out_dir), EXPECTED_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", source_manifest_rows(), ["source_type", "path", "used_for", "mutation_status"])
    write_text(out_dir / "scripts/run_umx1_smoke.sh", script_text(out_dir), executable=True)
    write_text(out_dir / "scripts/run_umx1_smoke.sbatch", sbatch_text(out_dir))

    no_admission = no_admission_rows([], [], [], audit_rows_, split_rows_)
    write_csv(out_dir / "umx1_no_admission_review.csv", no_admission, ADMISSION_COLUMNS)
    summary = summary_payload(out_dir, "dry_contract_ready", candidates, case_inputs, split_rows_, [], [], [], no_admission)
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def run_smoke(out_dir: Path = OUT_DIR, *, engine: str = "fast_scan") -> dict[str, Any]:
    build_dry(out_dir)
    candidates = candidate_rows()
    case_inputs = case_input_rows()
    cases = {case.name: case for case in config_loader.load_cases()}
    validation_records = config_loader.load_validation_records()

    results: list[dict[str, Any]] = []
    root_rows_: list[dict[str, Any]] = []
    segment_ledger: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    for case_input in case_inputs:
        case = cases[case_input["fluid_case_name"]]
        validation_record = validation_records.get(case.name)
        for candidate in candidates:
            scenario = scenario_for(case_input, candidate)
            if engine == "solve_case":
                result = S.solve_case(case, scenario)
            elif engine == "fast_scan":
                result = forward_v0.fast_pressure_root(case, scenario, prescribed_sources=None)
            else:
                raise ValueError(f"unsupported engine {engine!r}")
            row = result_row(result, case_input, candidate, engine)
            results.append(row)
            root_rows_.append(root_row(row))
            segment_ledger.extend(segment_rows(result, case_input, candidate, engine))
            probe_rows.extend(probe_score_rows(result, case_input, candidate, validation_record, engine))

    conservation = conservation_rows(segment_ledger)
    audit_rows_ = read_csv(out_dir / "umx1_runtime_input_audit.csv")
    split_rows_ = read_csv(out_dir / "umx1_case_split_contract.csv")
    no_admission = no_admission_rows(results, root_rows_, conservation, audit_rows_, split_rows_)

    write_csv(out_dir / "umx1_smoke_results.csv", results, RESULT_COLUMNS)
    write_csv(out_dir / "umx1_root_status_by_case.csv", root_rows_, ROOT_COLUMNS)
    write_csv(out_dir / "umx1_segment_ledger.csv", segment_ledger, SEGMENT_COLUMNS)
    write_csv(out_dir / "umx1_conservation_ledger.csv", conservation, CONSERVATION_COLUMNS)
    write_csv(out_dir / "umx1_probe_smoke_score.csv", probe_rows, PROBE_COLUMNS)
    write_csv(out_dir / "umx1_no_admission_review.csv", no_admission, ADMISSION_COLUMNS)

    summary = summary_payload(out_dir, f"{engine}_smoke_complete", candidates, case_inputs, split_rows_, results, root_rows_, conservation, no_admission)
    summary["engine"] = engine
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def load_existing_state(out_dir: Path) -> dict[str, Any]:
    candidates = read_csv(out_dir / "umx1_candidate_definitions.csv")
    split_rows_ = read_csv(out_dir / "umx1_case_split_contract.csv")
    audit_rows_ = read_csv(out_dir / "umx1_runtime_input_audit.csv")
    results: list[dict[str, Any]] = []
    root_rows_: list[dict[str, Any]] = []
    conservation: list[dict[str, Any]] = []
    smoke_path = out_dir / "umx1_smoke_results.csv"
    if smoke_path.exists():
        results = read_csv(smoke_path)
        root_rows_ = read_csv(out_dir / "umx1_root_status_by_case.csv")
        conservation = read_csv(out_dir / "umx1_conservation_ledger.csv")
    no_admission = no_admission_rows(results, root_rows_, conservation, audit_rows_, split_rows_)
    engines = sorted({str(row.get("engine", "")) for row in results if row.get("engine")})
    status = "dry_contract_ready" if not results else f"{engines[0]}_smoke_complete" if len(engines) == 1 else "mixed_smoke_complete"
    summary = summary_payload(
        out_dir,
        status,
        candidates,
        case_input_rows(),
        split_rows_,
        results,
        root_rows_,
        conservation,
        no_admission,
    )
    if engines:
        summary["engine"] = engines[0] if len(engines) == 1 else "mixed"
    return {
        "candidates": candidates,
        "split_rows": split_rows_,
        "audit_rows": audit_rows_,
        "results": results,
        "root_rows": root_rows_,
        "conservation": conservation,
        "no_admission": no_admission,
        "summary": summary,
    }


def refresh_summary(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    state = load_existing_state(out_dir)
    no_admission = state["no_admission"]
    summary = state["summary"]
    write_csv(out_dir / "umx1_no_admission_review.csv", no_admission, ADMISSION_COLUMNS)
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def summary_payload(
    out_dir: Path,
    status: str,
    candidates: list[dict[str, Any]],
    case_inputs: list[dict[str, str]],
    split_rows_: list[dict[str, Any]],
    results: list[dict[str, Any]],
    root_rows_: list[dict[str, Any]],
    conservation: list[dict[str, Any]],
    no_admission: list[dict[str, Any]],
) -> dict[str, Any]:
    root_pass = sum(row.get("root_gate_status") == "pass" for row in root_rows_)
    conservation_pass = sum(row.get("conservation_gate_status") in {"pass", "pass_noop"} for row in conservation)
    return {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "package": rel(out_dir),
        "status": status,
        "candidate_count": len(candidates),
        "executable_case_count": len(case_inputs),
        "planned_smoke_rows": len(candidates) * len(case_inputs),
        "smoke_result_rows": len(results),
        "root_pass_rows": root_pass,
        "root_rows": len(root_rows_),
        "conservation_pass_rows": conservation_pass,
        "conservation_rows": len(conservation),
        "split_executable_rows": sum(str(row.get("executable_in_smoke", "")).lower() == "true" for row in split_rows_),
        "salt1_status": "blocked_schema_promotion_missing",
        "admission_status": "not_admitted_smoke_only",
        "expansion_status": "eligible_for_review" if results and root_pass == len(root_rows_) and conservation_pass == len(conservation) else "stop_before_grid",
        "source_files": {
            "agent_540_package": rel(AGENT_540_PACKAGE),
            "input_contract": rel(INPUT_CONTRACT_DIR),
            "split_policy": rel(SPLIT_POLICY),
            "fluid_root": str(FLUID_ROOT),
        },
        "solve_case_note": "Full predictive-HX solve_case remains available through scripts/run_umx1_smoke.sbatch; interactive AGENT-544 run uses fast_scan when selected.",
        "no_admission_gates": no_admission,
    }


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(AGENT_540_PACKAGE)}
  - {rel(INPUT_CONTRACT_DIR)}
  - {rel(SPLIT_POLICY)}
tags: [umx1, forward-predictive, smoke, no-admission]
related:
  - .agent/status/2026-07-18_AGENT-544.md
  - .agent/journal/2026-07-18/umx1-dry-smoke-scorer.md
task: {TASK_ID}
date: 2026-07-18
role: Implementer/Tester/Writer
type: work_product
status: {summary['status']}
---

# UMX1 Dry/Smoke Scorer

Generated: `{summary['generated_utc']}`

## Result

Status: `{summary['status']}`.

This package uses the AGENT-540 Fluid UMX1 API as a smoke scorer only. It checks
runtime legality, split discipline, accepted roots, and UMX energy conservation.
It does not fit, tune, select, or admit a candidate.

## Contract

- Candidates: `UMX1_disabled_baseline`, `UMX1_exchange_0p01`,
  `UMX1_exchange_0p05`.
- Executable smoke cases: Salt2, Salt3, Salt4 nominal from the current
  predictive input contract.
- Salt1: explicitly blocked until schema promotion, per canonical final split
  policy.
- Runtime: predictive air-side HX only; no imposed cooler duty, CFD mdot,
  realized wallHeatFlux, or TP/TW targets before solve.

## Outputs

- `umx1_candidate_definitions.csv`
- `umx1_case_split_contract.csv`
- `umx1_scenario_contracts.csv`
- `umx1_runtime_input_audit.csv`
- `umx1_smoke_results.csv`
- `umx1_root_status_by_case.csv`
- `umx1_segment_ledger.csv`
- `umx1_conservation_ledger.csv`
- `umx1_probe_smoke_score.csv`
- `umx1_no_admission_review.csv`

## Summary

- Planned smoke rows: `{summary['planned_smoke_rows']}`.
- Completed smoke rows: `{summary['smoke_result_rows']}`.
- Root pass rows: `{summary['root_pass_rows']}/{summary['root_rows']}`.
- Conservation pass rows: `{summary['conservation_pass_rows']}/{summary['conservation_rows']}`.
- Expansion status: `{summary['expansion_status']}`.
- Admission status: `{summary['admission_status']}`.
"""
    write_text(out_dir / "README.md", text)


def validate_existing(out_dir: Path = OUT_DIR, *, allow_failed_smoke: bool = False) -> dict[str, Any]:
    required = [
        out_dir / "umx1_candidate_definitions.csv",
        out_dir / "umx1_case_split_contract.csv",
        out_dir / "umx1_scenario_contracts.csv",
        out_dir / "umx1_runtime_input_audit.csv",
        out_dir / "umx1_no_admission_review.csv",
        out_dir / "summary.json",
        out_dir / "README.md",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing required dry outputs: " + ", ".join(missing))
    candidates = read_csv(out_dir / "umx1_candidate_definitions.csv")
    if [row["candidate_id"] for row in candidates] != [row["candidate_id"] for row in candidate_rows()]:
        raise ValueError("candidate grid changed from predeclared order")
    audit = read_csv(out_dir / "umx1_runtime_input_audit.csv")
    failed_audit = [row for row in audit if row["audit_status"] not in {"pass", "pass_absent"}]
    if failed_audit:
        raise ValueError(f"{len(failed_audit)} runtime audit rows failed")
    admission = read_csv(out_dir / "umx1_no_admission_review.csv")
    if not admission or any(row["blocks_admission"] != "true" for row in admission):
        raise ValueError("no-admission review does not block admission on every gate")

    smoke_path = out_dir / "umx1_smoke_results.csv"
    if smoke_path.exists():
        roots = read_csv(out_dir / "umx1_root_status_by_case.csv")
        conservation = read_csv(out_dir / "umx1_conservation_ledger.csv")
        failed_roots = [row for row in roots if row["root_gate_status"] != "pass"]
        failed_conservation = [
            row for row in conservation if row["conservation_gate_status"] not in {"pass", "pass_noop"}
        ]
        if failed_roots and not allow_failed_smoke:
            raise ValueError(f"{len(failed_roots)} root gate rows failed")
        if failed_conservation and not allow_failed_smoke:
            raise ValueError(f"{len(failed_conservation)} conservation gate rows failed")
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    expected = load_existing_state(out_dir)
    expected_summary = expected["summary"]
    mismatched = [
        field
        for field in SUMMARY_CONSISTENCY_FIELDS
        if summary.get(field) != expected_summary.get(field)
    ]
    if mismatched:
        details = ", ".join(
            f"{field}: summary={summary.get(field)!r} csv={expected_summary.get(field)!r}"
            for field in mismatched
        )
        raise ValueError("summary.json is stale relative to CSV outputs: " + details)
    expected_admission = expected["no_admission"]
    if admission != expected_admission:
        raise ValueError("umx1_no_admission_review.csv is stale relative to runtime/root/conservation CSVs")
    if summary.get("no_admission_gates") != expected_admission:
        raise ValueError("summary.json no_admission_gates are stale relative to no-admission CSV")
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--dry-only", action="store_true")
    parser.add_argument("--run-smoke", action="store_true")
    parser.add_argument("--refresh-summary", action="store_true")
    parser.add_argument("--engine", choices=["fast_scan", "solve_case"], default="fast_scan")
    parser.add_argument("--validate-existing", action="store_true")
    parser.add_argument("--allow-failed-smoke", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    modes = [args.dry_only, args.run_smoke, args.refresh_summary, args.validate_existing]
    if sum(bool(mode) for mode in modes) != 1:
        parser.error("choose exactly one of --dry-only, --run-smoke, --refresh-summary, or --validate-existing")

    if args.dry_only:
        summary = build_dry(args.output_dir)
    elif args.run_smoke:
        summary = run_smoke(args.output_dir, engine=args.engine)
    elif args.refresh_summary:
        summary = refresh_summary(args.output_dir)
    else:
        summary = validate_existing(args.output_dir, allow_failed_smoke=args.allow_failed_smoke)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
