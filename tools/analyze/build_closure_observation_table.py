#!/usr/bin/env python3
"""Build the canonical closure observation table for admitted Salt 2/3/4 rows.

The table is a contract layer, not a new extractor. It adapts existing
post-processing products into one row-per-observable CSV with mandatory units,
time windows, mesh level, provenance, admission flags, and separate fit versus
validation eligibility.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh"

SCENARIO_CONTRACT = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/scenario_contract.csv"
LATEST_WINDOW_AUDIT = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/latest_window_audit.csv"
SOURCE_CONTRACT = ROOT / "work_products/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/source_contract_map.csv"
PRESSURE_LEDGER = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv"
HEAT_LEDGER = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv"
MOMENTUM_BUDGET = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_momentum_budget/momentum_budget.csv"
SEGMENT_FRICTION = ROOT / "work_products/2026-06/2026-06-30/2026-06-30_claude_segment_friction/segment_friction.csv"
THERMAL_HTC_DIR = ROOT / "work_products/2026-06/2026-06-30/2026-06-30_claude_thermal_htc"
TIME_WINDOW_OBS = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_time_window_quasi_steady_uq/quasi_steady_observations.csv"
ENTHALPY_LEDGER = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/patchwise_heat_ledger_enthalpy_interfaces.csv"
)
ENTHALPY_RESIDUALS = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/segment_enthalpy_residuals.csv"
)
THERMAL_OPENFOAM_SAMPLES = (
    ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/combined_openfoam_interface_samples.csv"
)
THERMAL_OPENFOAM_PLAN = (
    ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/sampling_plane_plan.csv"
)
CORRECTED_GATE = ROOT / "work_products/2026-07-07_corrected_salt_preliminary_gate/preliminary_gate_analysis.json"
LIVE_MONITOR = ROOT / "work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv"

ADMITTED_SOURCES = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
}

RECIRCULATION_SPANS = {"left_lower_leg", "left_upper_leg"}

BOOL_ENUM = {"yes", "no"}
RUN_CLASS_ENUM = {"mainline_jin_continuation"}
ADMISSION_ENUM = {"admitted_mainline", "held", "excluded"}
FIT_USE_ENUM = {
    "fit_target",
    "fit_feature",
    "validation_only",
    "diagnostic_only",
    "not_fit_recirculation",
    "not_fit_apparent_or_residual",
    "not_fit_thermal_caveat",
    "not_fit_unbracketed_junction",
    "validation_only_thermal_residual",
}
WINDOW_STATE_ENUM = {
    "stationary",
    "quasi_stationary",
    "moving_not_plateaued",
    "oscillatory_not_steady",
    "short_or_early_terminated",
    "transient_model_only",
    "not_applicable",
}
MESH_STATUS_ENUM = {"coarse_no_gci"}


SCHEMA: list[dict[str, str]] = [
    {"column": "observation_id", "required": "yes", "units": "", "allowed": "unique string", "description": "Stable row identifier; one row is one observable."},
    {"column": "source_id", "required": "yes", "units": "", "allowed": "Salt 2/3/4 Jin admitted source ids", "description": "CFD source identifier."},
    {"column": "case_id", "required": "yes", "units": "", "allowed": "salt_2|salt_3|salt_4", "description": "Short case id."},
    {"column": "case_family", "required": "yes", "units": "", "allowed": "salt", "description": "Fluid/case family."},
    {"column": "run_class", "required": "yes", "units": "", "allowed": "|".join(sorted(RUN_CLASS_ENUM)), "description": "Run class admitted by the scenario contract."},
    {"column": "mesh_level", "required": "yes", "units": "", "allowed": "coarse", "description": "Mesh level for the observable."},
    {"column": "mesh_status", "required": "yes", "units": "", "allowed": "|".join(sorted(MESH_STATUS_ENUM)), "description": "Mesh uncertainty state; current rows have no GCI band."},
    {"column": "source_case_root", "required": "yes", "units": "", "allowed": "repo-relative path", "description": "Solver case root or source contract root used as provenance."},
    {"column": "source_path", "required": "yes", "units": "", "allowed": "existing repo-relative file", "description": "CSV or artifact file containing the numeric source value."},
    {"column": "source_row_key", "required": "yes", "units": "", "allowed": "string", "description": "Join key back to the source artifact row."},
    {"column": "observable_family", "required": "yes", "units": "", "allowed": "pressure|thermal|time_window", "description": "Broad observable class."},
    {"column": "observable_type", "required": "yes", "units": "", "allowed": "string", "description": "Specific observable source/type."},
    {"column": "span", "required": "yes", "units": "", "allowed": "span or case", "description": "Span/branch identity; case-level rows use case."},
    {"column": "segment_1d", "required": "yes", "units": "", "allowed": "span/branch/case", "description": "1D segment mapping used by model consumers."},
    {"column": "station_start", "required": "no", "units": "", "allowed": "string", "description": "Station or endpoint label when available."},
    {"column": "station_end", "required": "no", "units": "", "allowed": "string", "description": "Station or endpoint label when available."},
    {"column": "window_id", "required": "yes", "units": "", "allowed": "string", "description": "Named time-window contract."},
    {"column": "time_window_start_s", "required": "yes", "units": "s", "allowed": "finite number", "description": "Start of the extraction or statistical window."},
    {"column": "time_window_end_s", "required": "yes", "units": "s", "allowed": "finite number", "description": "End of the extraction or statistical window."},
    {"column": "time_window_source", "required": "yes", "units": "", "allowed": "string", "description": "Artifact used to assign the window."},
    {"column": "n_samples", "required": "no", "units": "count", "allowed": "number or blank", "description": "Samples used where available."},
    {"column": "quantity", "required": "yes", "units": "", "allowed": "string", "description": "Observable name consumed by closure/bakeoff scripts."},
    {"column": "value", "required": "yes", "units": "see units", "allowed": "finite number", "description": "Numeric observable value."},
    {"column": "units", "required": "yes", "units": "", "allowed": "non-empty", "description": "Physical units; use dimensionless where applicable."},
    {"column": "uncertainty_value", "required": "no", "units": "uncertainty_units", "allowed": "number or blank", "description": "Uncertainty magnitude when available."},
    {"column": "uncertainty_units", "required": "no", "units": "", "allowed": "string", "description": "Units for uncertainty_value."},
    {"column": "uncertainty_method", "required": "no", "units": "", "allowed": "string", "description": "How uncertainty was estimated."},
    {"column": "geometry_source", "required": "yes", "units": "", "allowed": "string", "description": "Geometry/provenance basis for the row."},
    {"column": "pressure_method", "required": "yes", "units": "", "allowed": "string|not_applicable", "description": "Pressure reduction method."},
    {"column": "thermal_method", "required": "yes", "units": "", "allowed": "string|not_applicable", "description": "Thermal reduction method."},
    {"column": "physical_interface_bracket_status", "required": "yes", "units": "", "allowed": "string|not_applicable", "description": "Whether thermal control volume interfaces physically bracket the row."},
    {"column": "thermal_residual_status", "required": "yes", "units": "", "allowed": "string|not_applicable", "description": "Residual computation/admission state for thermal rows."},
    {"column": "thermal_residual_assignment", "required": "yes", "units": "", "allowed": "string|not_applicable", "description": "Residual assignment rule, e.g. wall flux minus enthalpy change."},
    {"column": "thermal_residual_fraction", "required": "no", "units": "dimensionless", "allowed": "number or blank", "description": "Thermal residual normalized by enthalpy change where available."},
    {"column": "thermal_residual_W", "required": "no", "units": "W", "allowed": "number or blank", "description": "Thermal wallHeatFlux minus enthalpy-change residual."},
    {"column": "interface_temperature_source", "required": "no", "units": "", "allowed": "repo-relative path or blank", "description": "Interface-temperature source table or plane file."},
    {"column": "interface_temperature_selection_rule", "required": "yes", "units": "", "allowed": "string|not_applicable", "description": "How mixing-cup and forward-flow temperatures are selected/preserved."},
    {"column": "max_interface_recirc_ratio", "required": "no", "units": "dimensionless", "allowed": "number or blank", "description": "Maximum interface recirculation/backflow metric used for row gating."},
    {"column": "recirculation_flag", "required": "yes", "units": "", "allowed": "yes|no", "description": "Whether recirculation/backflow contaminates this observable."},
    {"column": "radiation_output_term", "required": "yes", "units": "", "allowed": "string|not_applicable", "description": "OpenFOAM radiation output term status; do not infer radiation from emissivity."},
    {"column": "radiation_present", "required": "yes", "units": "", "allowed": "yes|no", "description": "Whether a sampled/output radiation term is present."},
    {"column": "control_volume", "required": "no", "units": "", "allowed": "string", "description": "Physical thermal control volume when applicable."},
    {"column": "control_volume_group", "required": "no", "units": "", "allowed": "string", "description": "Control-volume group such as heater, cooler_reducer, or junction."},
    {"column": "interface_role", "required": "no", "units": "", "allowed": "string", "description": "Role of the sampled interface plane in a control volume."},
    {"column": "dominant_flow_direction", "required": "no", "units": "", "allowed": "string", "description": "Dominant directional flux across a sampled interface plane."},
    {"column": "backflow_fraction", "required": "no", "units": "dimensionless", "allowed": "number or blank", "description": "Backflow fraction from physical-interface sampling."},
    {"column": "convergence_status", "required": "yes", "units": "", "allowed": "stationary|not_available", "description": "Convergence state from source gates."},
    {"column": "window_state", "required": "yes", "units": "", "allowed": "|".join(sorted(WINDOW_STATE_ENUM)), "description": "Time-window state for fit use."},
    {"column": "operating_point_verdict", "required": "yes", "units": "", "allowed": "admitted_mainline", "description": "Operating-point admission verdict."},
    {"column": "admission_status", "required": "yes", "units": "", "allowed": "|".join(sorted(ADMISSION_ENUM)), "description": "Row-level admission state."},
    {"column": "needs_special_gate_scrutiny", "required": "yes", "units": "", "allowed": "yes|no", "description": "Gate-scrutiny flag; corrected perturbations must be explicit."},
    {"column": "fit_eligible", "required": "yes", "units": "", "allowed": "yes|no", "description": "Whether this row may be used to fit model coefficients."},
    {"column": "validation_eligible", "required": "yes", "units": "", "allowed": "yes|no", "description": "Whether this row may be used to score a model."},
    {"column": "fit_use_status", "required": "yes", "units": "", "allowed": "|".join(sorted(FIT_USE_ENUM)), "description": "Reason for fit eligibility/exclusion."},
    {"column": "validation_use_status", "required": "yes", "units": "", "allowed": "validation_target|validation_diagnostic", "description": "Validation role."},
    {"column": "independence_group_id", "required": "yes", "units": "", "allowed": "string", "description": "Blocking group for correlated rows/windows."},
    {"column": "quality_flags", "required": "yes", "units": "", "allowed": "semicolon-delimited flags or none", "description": "Known row caveats."},
    {"column": "provenance_notes", "required": "yes", "units": "", "allowed": "string", "description": "Short source and interpretation note."},
]

FIELDS = [item["column"] for item in SCHEMA]
REQUIRED = {item["column"] for item in SCHEMA if item["required"] == "yes"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def case_id_from_source(source_id: str) -> str:
    match = re.search(r"salt_test_(\d+)_jin", source_id)
    if not match:
        return ""
    return f"salt_{match.group(1)}"


def source_contracts() -> dict[str, dict[str, str]]:
    rows = read_csv(SOURCE_CONTRACT)
    return {row["source_id"]: row for row in rows}


def scenario_contracts() -> dict[str, dict[str, str]]:
    return {row["source_id"]: row for row in read_csv(SCENARIO_CONTRACT) if row.get("run_class") == "mainline_jin_continuation"}


def window_contracts() -> dict[str, dict[str, str]]:
    return {row["source_id"]: row for row in read_csv(LATEST_WINDOW_AUDIT) if row.get("run_class") == "mainline_jin_continuation"}


def finite(value: Any) -> bool:
    if value is None or value == "":
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def base_row(
    *,
    source_id: str,
    source_path: Path,
    source_row_key: str,
    observable_family: str,
    observable_type: str,
    span: str,
    quantity: str,
    value: str,
    units: str,
    source_contract: dict[str, str],
    scenario: dict[str, str],
    window: dict[str, str],
    quality_flags: list[str] | None = None,
) -> dict[str, Any]:
    start = source_contract.get("requested_time_start_s") or window.get("prior_contract_requested_start_s")
    end = source_contract.get("requested_time_end_s") or window.get("prior_contract_requested_end_s")
    case_root = scenario.get("case_root") or source_contract.get("runtime_root") or source_contract.get("source_root")
    segment = span if span else "case"
    flags = [flag for flag in (quality_flags or []) if flag]
    if window.get("latest_window_status") == "prior_extraction_older_than_case_latest":
        flags.append("frozen_extraction_window_older_than_available_case_latest")
    return {
        "observation_id": f"{source_id}:{observable_family}:{span or 'case'}:{quantity}:{source_row_key}",
        "source_id": source_id,
        "case_id": case_id_from_source(source_id),
        "case_family": "salt",
        "run_class": "mainline_jin_continuation",
        "mesh_level": "coarse",
        "mesh_status": "coarse_no_gci",
        "source_case_root": case_root,
        "source_path": rel(source_path),
        "source_row_key": source_row_key,
        "observable_family": observable_family,
        "observable_type": observable_type,
        "span": span or "case",
        "segment_1d": segment,
        "station_start": "",
        "station_end": "",
        "window_id": f"{source_id}:source_contract_requested_window",
        "time_window_start_s": start,
        "time_window_end_s": end,
        "time_window_source": rel(SOURCE_CONTRACT),
        "n_samples": source_contract.get("requested_time_count", ""),
        "quantity": quantity,
        "value": value,
        "units": units,
        "uncertainty_value": "",
        "uncertainty_units": "",
        "uncertainty_method": "",
        "geometry_source": "source_contract_mesh_reduction_geometry",
        "pressure_method": "not_applicable",
        "thermal_method": "not_applicable",
        "physical_interface_bracket_status": "not_applicable",
        "thermal_residual_status": "not_applicable",
        "thermal_residual_assignment": "not_applicable",
        "thermal_residual_fraction": "",
        "thermal_residual_W": "",
        "interface_temperature_source": "",
        "interface_temperature_selection_rule": "not_applicable",
        "max_interface_recirc_ratio": "",
        "recirculation_flag": "no",
        "radiation_output_term": "not_applicable",
        "radiation_present": "no",
        "control_volume": "",
        "control_volume_group": "",
        "interface_role": "",
        "dominant_flow_direction": "",
        "backflow_fraction": "",
        "convergence_status": "stationary",
        "window_state": "stationary",
        "operating_point_verdict": "admitted_mainline",
        "admission_status": "admitted_mainline",
        "needs_special_gate_scrutiny": "no",
        "fit_eligible": "no",
        "validation_eligible": "yes",
        "fit_use_status": "validation_only",
        "validation_use_status": "validation_target",
        "independence_group_id": f"{source_id}:mainline_window",
        "quality_flags": ";".join(flags) if flags else "none",
        "provenance_notes": "Adapted from existing read-only post-processing artifact.",
    }


def admitted_context() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    sources = source_contracts()
    scenarios = scenario_contracts()
    windows = window_contracts()
    missing = ADMITTED_SOURCES - sources.keys()
    if missing:
        raise FileNotFoundError(f"Missing source-contract rows for admitted sources: {sorted(missing)}")
    return sources, scenarios, windows


def pressure_rows() -> list[dict[str, Any]]:
    sources, scenarios, windows = admitted_context()
    rows: list[dict[str, Any]] = []
    qois = {
        "distributed_friction_pa": ("Pa", "pressure_distributed_mechanical_loss"),
        "development_loss_pa": ("Pa", "pressure_development_loss"),
        "minor_loss_pa": ("Pa", "pressure_minor_loss"),
        "residual_pa": ("Pa", "pressure_residual"),
        "residual_fraction": ("dimensionless", "pressure_residual_fraction"),
        "f_debuoyed": ("dimensionless", "pressure_debuoyed_friction_factor"),
    }
    for row in read_csv(PRESSURE_LEDGER):
        source_id = row["source_id"]
        if source_id not in ADMITTED_SOURCES:
            continue
        span = row["span"]
        flags = []
        if row.get("recirculation_flag") == "True":
            flags.append("recirculation_invalid_single_f")
        if row.get("flow_reset_flag") == "True":
            flags.append("flow_reset_or_redevelopment")
        for quantity, (units, observable_type) in qois.items():
            out = base_row(
                source_id=source_id,
                source_path=PRESSURE_LEDGER,
                source_row_key=span,
                observable_family="pressure",
                observable_type=observable_type,
                span=span,
                quantity=quantity,
                value=row.get(quantity, ""),
                units=units,
                source_contract=sources[source_id],
                scenario=scenarios.get(source_id, {}),
                window=windows.get(source_id, {}),
                quality_flags=flags,
            )
            out["pressure_method"] = "debuoyed_momentum_budget_ledger"
            if span in RECIRCULATION_SPANS or row.get("recirculation_flag") == "True":
                out["recirculation_flag"] = "yes"
            out["provenance_notes"] = "From AGENT-193/197 pressure ledger; uses July 1 momentum-budget decomposition and July 7 ledger fixes."
            if quantity in {"f_debuoyed", "distributed_friction_pa"} and span not in RECIRCULATION_SPANS:
                out["fit_eligible"] = "yes"
                out["fit_use_status"] = "fit_target"
            elif span in RECIRCULATION_SPANS:
                out["fit_use_status"] = "not_fit_recirculation"
            elif quantity in {"residual_pa", "residual_fraction"}:
                out["fit_use_status"] = "not_fit_apparent_or_residual"
                out["validation_use_status"] = "validation_diagnostic"
            else:
                out["fit_use_status"] = "validation_only"
            rows.append(out)
    return rows


def momentum_rows() -> list[dict[str, Any]]:
    sources, scenarios, windows = admitted_context()
    rows: list[dict[str, Any]] = []
    qois = {
        "f_corrected": ("dimensionless", "momentum_budget_debuoyed_friction_factor"),
        "f_corrected_over_flam": ("dimensionless", "momentum_budget_f_over_laminar"),
        "friction_grad_corrected_pa_m": ("Pa/m", "momentum_budget_mechanical_loss_gradient"),
        "buoyancy_source_grad_pa_m": ("Pa/m", "momentum_budget_density_gradient_buoyancy"),
        "inertial_grad_pa_m": ("Pa/m", "momentum_budget_inertial_gradient"),
        "Re": ("dimensionless", "momentum_budget_reynolds_number"),
        "bulk_T_K": ("K", "momentum_budget_bulk_temperature"),
    }
    for row in read_csv(MOMENTUM_BUDGET):
        source_id = row["source_id"]
        if source_id not in ADMITTED_SOURCES:
            continue
        span = row["span"]
        flags = ["momentum_budget_reference"]
        if span in RECIRCULATION_SPANS:
            flags.append("recirculation_invalid_single_f")
        for quantity, (units, observable_type) in qois.items():
            out = base_row(
                source_id=source_id,
                source_path=MOMENTUM_BUDGET,
                source_row_key=span,
                observable_family="pressure",
                observable_type=observable_type,
                span=span,
                quantity=quantity,
                value=row.get(quantity, ""),
                units=units,
                source_contract=sources[source_id],
                scenario=scenarios.get(source_id, {}),
                window=windows.get(source_id, {}),
                quality_flags=flags,
            )
            out["pressure_method"] = "streamwise_momentum_budget_debuoyed"
            if span in RECIRCULATION_SPANS:
                out["recirculation_flag"] = "yes"
            out["provenance_notes"] = "From July 1 streamwise momentum budget; carried to make pressure-ledger reproduction and no-double-counting auditable."
            if quantity == "f_corrected" and span not in RECIRCULATION_SPANS:
                out["fit_eligible"] = "yes"
                out["fit_use_status"] = "fit_target"
            elif span in RECIRCULATION_SPANS:
                out["fit_use_status"] = "not_fit_recirculation"
            else:
                out["fit_use_status"] = "validation_only"
            rows.append(out)
    return rows


def segment_friction_rows() -> list[dict[str, Any]]:
    sources, scenarios, windows = admitted_context()
    rows: list[dict[str, Any]] = []
    qois = {
        "apparent_darcy_f": ("dimensionless", "segment_apparent_darcy_f"),
        "dp_loss_ds_pa_per_m": ("Pa/m", "segment_apparent_loss_gradient"),
        "reynolds_number": ("dimensionless", "segment_reynolds_number"),
        "excess_loss_factor_fapp_over_flam": ("dimensionless", "segment_apparent_f_over_laminar"),
    }
    for row in read_csv(SEGMENT_FRICTION):
        source_id = row["source_id"]
        if source_id not in ADMITTED_SOURCES:
            continue
        span = row["span"]
        method = row.get("method", "segment_friction")
        for quantity, (units, observable_type) in qois.items():
            value = row.get(quantity, "")
            if value == "" or value.lower() == "nan":
                continue
            flags = ["apparent_friction_diagnostic"]
            if row.get("flags"):
                flags.extend(row["flags"].split(";"))
            out = base_row(
                source_id=source_id,
                source_path=SEGMENT_FRICTION,
                source_row_key=f"{span}:{method}",
                observable_family="pressure",
                observable_type=observable_type,
                span=span,
                quantity=quantity,
                value=value,
                units=units,
                source_contract=sources[source_id],
                scenario=scenarios.get(source_id, {}),
                window=windows.get(source_id, {}),
                quality_flags=flags,
            )
            out["pressure_method"] = method
            if span in RECIRCULATION_SPANS or "recirculation" in ";".join(flags):
                out["recirculation_flag"] = "yes"
                out["fit_use_status"] = "not_fit_recirculation"
            else:
                out["fit_use_status"] = "not_fit_apparent_or_residual"
            out["validation_use_status"] = "validation_diagnostic"
            out["provenance_notes"] = "From June 30 segment-friction diagnostic; retained for comparison but not closure-fit target after debuoyed pressure ledger."
            rows.append(out)
    return rows


def thermal_rows() -> list[dict[str, Any]]:
    sources, scenarios, windows = admitted_context()
    rows: list[dict[str, Any]] = []
    qois = {
        "uaprime_wmk": ("W/m/K", "thermal_uaprime"),
        "R_prime_thermal_mkw": ("m*K/W", "thermal_resistance_per_length"),
        "htc_wm2k": ("W/m^2/K", "thermal_htc"),
        "Nu": ("dimensionless", "thermal_nusselt_number"),
        "T_bulk_k": ("K", "thermal_bulk_temperature"),
        "T_wall_k": ("K", "thermal_wall_temperature"),
        "wall_duty_Q_w": ("W", "thermal_wall_duty"),
    }
    for path in sorted(THERMAL_HTC_DIR.glob("segment_htc_uaprime_*.csv")):
        for row in read_csv(path):
            source_id_match = re.search(r"(viscosity_screening_salt_test_\d+_jin_coarse_mesh)", path.name)
            if not source_id_match:
                continue
            source_id = source_id_match.group(1)
            if source_id not in ADMITTED_SOURCES:
                continue
            span = row.get("cfd_spans") or row.get("segment")
            segment = row.get("segment") or span
            flags = ["thermal_method_enthalpy_flux_bulk_temperature"]
            if row.get("thermally_blocked") == "True":
                flags.append("thermally_blocked")
            if row.get("nu_direct_admitted") != "True":
                flags.append("nu_direct_not_admitted")
            if row.get("mesh_independence"):
                flags.append(f"mesh_independence_{row['mesh_independence']}")
            for quantity, (units, observable_type) in qois.items():
                value = row.get(quantity, "")
                if value == "" or value.lower() == "nan":
                    continue
                out = base_row(
                    source_id=source_id,
                    source_path=path,
                    source_row_key=f"{segment}:{row.get('station_label', '')}",
                    observable_family="thermal",
                    observable_type=observable_type,
                    span=span,
                    quantity=quantity,
                    value=value,
                    units=units,
                    source_contract=sources[source_id],
                    scenario=scenarios.get(source_id, {}),
                    window=windows.get(source_id, {}),
                    quality_flags=flags,
                )
                out["segment_1d"] = segment
                out["station_start"] = row.get("station_label", "")
                out["thermal_method"] = "enthalpy_flux_bulk_temperature_wall_heat_flux"
                out["geometry_source"] = "mesh_cutplane_and_wall_patch_contract"
                out["provenance_notes"] = "From June 30 thermal HTC/UAprime package; UAprime is primary ROM surface, Nu is fit-gated by row policy."
                if quantity == "uaprime_wmk" and row.get("thermally_blocked") != "True":
                    out["fit_eligible"] = "yes"
                    out["fit_use_status"] = "fit_target"
                elif quantity == "Nu" and row.get("nu_direct_admitted") == "True":
                    out["fit_eligible"] = "yes"
                    out["fit_use_status"] = "fit_target"
                elif quantity in {"T_bulk_k", "T_wall_k", "wall_duty_Q_w"}:
                    out["fit_use_status"] = "fit_feature"
                else:
                    out["fit_use_status"] = "not_fit_thermal_caveat"
                    out["validation_use_status"] = "validation_diagnostic"
                rows.append(out)
    return rows


def heat_ledger_rows() -> list[dict[str, Any]]:
    sources, scenarios, windows = admitted_context()
    rows: list[dict[str, Any]] = []
    for row in read_csv(HEAT_LEDGER):
        source_id = row["source_id"]
        if source_id not in ADMITTED_SOURCES:
            continue
        span = row.get("span") or "case"
        out = base_row(
            source_id=source_id,
            source_path=HEAT_LEDGER,
            source_row_key=f"{span}:{row.get('patch_group', '')}",
            observable_family="thermal",
            observable_type="patchwise_heat_wall_flux_integral",
            span=span,
            quantity="wallHeatFlux_integral_W",
            value=row.get("wallHeatFlux_integral_W", ""),
            units="W",
            source_contract=sources[source_id],
            scenario=scenarios.get(source_id, {}),
            window=windows.get(source_id, {}),
            quality_flags=["patchwise_heat_validation_only", "enthalpy_change_missing", "thermal_ledger_followup_required"],
        )
        out["segment_1d"] = row.get("span") or "case"
        out["thermal_method"] = "wallHeatFlux_patch_group_integral"
        out["fit_use_status"] = "not_fit_thermal_caveat"
        out["validation_use_status"] = "validation_diagnostic"
        out["provenance_notes"] = "From July 7 heat source/sink ledger; validation-only until patchwise heat ledger adds enthalpy-change closure."
        rows.append(out)
    return rows


def text_flags(*values: str) -> list[str]:
    flags: list[str] = []
    for value in values:
        if not value:
            continue
        normalized = value.replace("|", ";")
        flags.extend([item for item in normalized.split(";") if item])
    return flags


def bool_from_text(value: str) -> str:
    return "yes" if str(value).strip().lower() in {"true", "yes", "1"} else "no"


def recirculation_flag_from_ratio(value: str, quality_flags: str = "") -> str:
    ratio = 0.0
    if finite(value):
        ratio = float(value)
    if ratio > 0.5 or "high_recirculation" in quality_flags or "high_backflow_fraction" in quality_flags:
        return "yes"
    return "no"


def thermal_interface_residual_rows() -> list[dict[str, Any]]:
    sources, scenarios, windows = admitted_context()
    rows: list[dict[str, Any]] = []
    qois = {
        "wallHeatFlux_integral_W": ("W", "thermal_patch_wall_flux_integral_with_physical_interfaces"),
        "heat_to_fluid_W": ("W", "thermal_patch_heat_to_fluid_with_physical_interfaces"),
        "enthalpy_change_W": ("W", "thermal_segment_enthalpy_change"),
        "wallHeatFlux_vs_enthalpy_residual_W": ("W", "thermal_wall_flux_minus_enthalpy_residual"),
        "residual_fraction": ("dimensionless", "thermal_wall_flux_enthalpy_residual_fraction"),
        "T_bulk_inlet_K": ("K", "thermal_interface_bulk_temperature_inlet"),
        "T_bulk_outlet_K": ("K", "thermal_interface_bulk_temperature_outlet"),
        "T_bulk_span_K": ("K", "thermal_interface_bulk_temperature_span"),
        "max_interface_recirc_ratio": ("dimensionless", "thermal_interface_max_recirculation_ratio"),
    }
    for row in read_csv(ENTHALPY_LEDGER):
        source_id = row["source_id"]
        if source_id not in ADMITTED_SOURCES:
            continue
        span = row.get("span") or "case"
        patch_group = row.get("patch_group", "")
        recirc_flag = recirculation_flag_from_ratio(
            row.get("max_interface_recirc_ratio", ""),
            row.get("quality_flags", ""),
        )
        bracket_status = row.get("physical_interface_bracket_status", "") or "unknown"
        residual_status = row.get("enthalpy_change_status", "") or "not_computed"
        radiation_term = row.get("radiation_output_term", "") or "absent_no_qr_output"
        for quantity, (units, observable_type) in qois.items():
            value = row.get(quantity, "")
            if not finite(value):
                continue
            flags = text_flags(
                "physical_interface_thermal_refresh",
                row.get("quality_flags", ""),
                row.get("radiation_caveat", ""),
            )
            if recirc_flag == "yes":
                flags.append("recirculation_contaminated_not_fit")
            if "not_bracketed" in bracket_status:
                flags.append("not_physically_bracketed")
            out = base_row(
                source_id=source_id,
                source_path=ENTHALPY_LEDGER,
                source_row_key=f"{patch_group}:{span}",
                observable_family="thermal",
                observable_type=observable_type,
                span=span,
                quantity=quantity,
                value=value,
                units=units,
                source_contract=sources[source_id],
                scenario=scenarios.get(source_id, {}),
                window=windows.get(source_id, {}),
                quality_flags=flags,
            )
            out["segment_1d"] = span
            out["source_case_root"] = row.get("source_case_root", out["source_case_root"])
            out["time_window_start_s"] = row.get("source_window_start_s", out["time_window_start_s"])
            out["time_window_end_s"] = row.get("source_window_end_s", out["time_window_end_s"])
            out["n_samples"] = row.get("source_window_count", out["n_samples"])
            out["time_window_source"] = row.get("time_window_source", rel(SOURCE_CONTRACT))
            out["thermal_method"] = "physical_interface_enthalpy_wallHeatFlux_residual"
            out["geometry_source"] = row.get("physical_interface_inlet", "") + "->" + row.get("physical_interface_outlet", "")
            out["physical_interface_bracket_status"] = bracket_status
            out["thermal_residual_status"] = residual_status
            out["thermal_residual_assignment"] = row.get("residual_assignment", "") or "not_applicable"
            out["thermal_residual_fraction"] = row.get("residual_fraction", "")
            out["thermal_residual_W"] = row.get("wallHeatFlux_vs_enthalpy_residual_W", "")
            out["interface_temperature_source"] = row.get("interface_temperature_source", "")
            out["interface_temperature_selection_rule"] = row.get("interface_temperature_selection_rule", "") or "not_applicable"
            out["max_interface_recirc_ratio"] = row.get("max_interface_recirc_ratio", "")
            out["recirculation_flag"] = recirc_flag
            out["radiation_output_term"] = radiation_term
            out["radiation_present"] = bool_from_text(row.get("radiation_present", ""))
            out["control_volume"] = patch_group
            out["control_volume_group"] = row.get("physical_role", "")
            out["fit_eligible"] = "no"
            if "not_bracketed" in bracket_status:
                out["fit_use_status"] = "not_fit_unbracketed_junction"
                out["validation_use_status"] = "validation_diagnostic"
            elif recirc_flag == "yes":
                out["fit_use_status"] = "not_fit_recirculation"
                out["validation_use_status"] = "validation_diagnostic"
            elif quantity in {"wallHeatFlux_vs_enthalpy_residual_W", "residual_fraction"}:
                out["fit_use_status"] = "validation_only_thermal_residual"
                out["validation_use_status"] = "validation_target"
            else:
                out["fit_use_status"] = "validation_only"
                out["validation_use_status"] = "validation_target"
            out["provenance_notes"] = (
                "From July 8 patchwise heat ledger with physical-interface enthalpy terms; "
                "fit disabled pending reviewed control-volume method and mesh/GCI support."
            )
            rows.append(out)
    return rows


def thermal_openfoam_interface_rows() -> list[dict[str, Any]]:
    sources, scenarios, windows = admitted_context()
    rows: list[dict[str, Any]] = []
    qois = {
        "T_mixing_cup_signed_K": ("K", "openfoam_interface_signed_mixing_cup_temperature"),
        "T_positive_normal_bulk_K": ("K", "openfoam_interface_positive_normal_bulk_temperature"),
        "T_negative_normal_bulk_K": ("K", "openfoam_interface_negative_normal_bulk_temperature"),
        "T_forward_dominant_bulk_K": ("K", "openfoam_interface_dominant_forward_bulk_temperature"),
        "T_simple_K": ("K", "openfoam_interface_simple_face_temperature"),
        "mdot_signed_proxy": ("kg/m2/s_proxy", "openfoam_interface_signed_flux_proxy"),
        "positive_flux_proxy": ("kg/m2/s_proxy", "openfoam_interface_positive_flux_proxy"),
        "negative_flux_proxy_abs": ("kg/m2/s_proxy", "openfoam_interface_negative_flux_proxy_abs"),
        "backflow_fraction": ("dimensionless", "openfoam_interface_backflow_fraction"),
    }
    for row in read_csv(THERMAL_OPENFOAM_SAMPLES):
        source_id = row["source_id"]
        if source_id not in ADMITTED_SOURCES:
            continue
        recirc_flag = recirculation_flag_from_ratio(row.get("backflow_fraction", ""), row.get("quality_flags", ""))
        for quantity, (units, observable_type) in qois.items():
            value = row.get(quantity, "")
            if not finite(value):
                continue
            flags = text_flags("openfoam_physical_interface_sampling", row.get("quality_flags", ""))
            if recirc_flag == "yes":
                flags.append("recirculation_contaminated_not_fit")
            out = base_row(
                source_id=source_id,
                source_path=THERMAL_OPENFOAM_SAMPLES,
                source_row_key=f"{row.get('control_volume', '')}:{row.get('interface_role', '')}:{row.get('plane_label', '')}",
                observable_family="thermal",
                observable_type=observable_type,
                span=row.get("span", ""),
                quantity=quantity,
                value=value,
                units=units,
                source_contract=sources[source_id],
                scenario=scenarios.get(source_id, {}),
                window=windows.get(source_id, {}),
                quality_flags=flags,
            )
            out["source_case_root"] = str(scenarios.get(source_id, {}).get("case_root", out["source_case_root"]))
            out["time_window_start_s"] = row.get("time_s", "")
            out["time_window_end_s"] = row.get("time_s", "")
            out["time_window_source"] = rel(THERMAL_OPENFOAM_SAMPLES)
            out["n_samples"] = row.get("n_masked", row.get("n_faces", ""))
            out["thermal_method"] = "openfoam_sampled_cutplane_directional_bulk_temperature"
            out["geometry_source"] = rel(THERMAL_OPENFOAM_PLAN)
            out["physical_interface_bracket_status"] = "bracketed_openfoam_physical_interface_plane"
            out["thermal_residual_status"] = "not_applicable_plane_sample"
            out["thermal_residual_assignment"] = "not_applicable_plane_sample"
            out["interface_temperature_source"] = row.get("plane_file", "")
            out["interface_temperature_selection_rule"] = row.get("temperature_selection_rule", "")
            out["max_interface_recirc_ratio"] = row.get("backflow_fraction", "")
            out["recirculation_flag"] = recirc_flag
            out["radiation_output_term"] = row.get("radiation_output_term", "") or "absent_no_qr_output"
            out["radiation_present"] = "yes" if out["radiation_output_term"] == "qr_field_present_sampled" else "no"
            out["control_volume"] = row.get("control_volume", "")
            out["control_volume_group"] = row.get("control_volume_group", "")
            out["interface_role"] = row.get("interface_role", "")
            out["dominant_flow_direction"] = row.get("dominant_flow_direction", "")
            out["backflow_fraction"] = row.get("backflow_fraction", "")
            out["fit_eligible"] = "no"
            out["fit_use_status"] = "not_fit_recirculation" if recirc_flag == "yes" else "validation_only"
            out["validation_use_status"] = "validation_diagnostic"
            out["provenance_notes"] = (
                "From July 9 bounded OpenFOAM physical-interface sampling job 3287311; "
                "directional temperatures and backflow fractions are kept separate."
            )
            rows.append(out)
    return rows


def time_window_rows() -> list[dict[str, Any]]:
    sources, scenarios, windows = admitted_context()
    rows: list[dict[str, Any]] = []
    for row in read_csv(TIME_WINDOW_OBS):
        source_id = row["source_id"]
        if source_id not in ADMITTED_SOURCES or row.get("is_primary_window") != "True":
            continue
        qoi = row.get("qoi_name", "")
        family = "pressure" if qoi.startswith("mdot::") else "thermal"
        out = base_row(
            source_id=source_id,
            source_path=TIME_WINDOW_OBS,
            source_row_key=row.get("window_id", qoi),
            observable_family="time_window",
            observable_type="quasi_steady_window_mean",
            span="case",
            quantity=qoi,
            value=row.get("mean", ""),
            units=row.get("qoi_units", ""),
            source_contract=sources[source_id],
            scenario=scenarios.get(source_id, {}),
            window=windows.get(source_id, {}),
            quality_flags=["time_series_correlated_not_independent_samples", f"role_{row.get('role', '')}"],
        )
        out["observable_family"] = family
        out["observable_type"] = "quasi_steady_window_mean"
        out["window_id"] = row.get("window_id", "")
        out["time_window_start_s"] = row.get("window_start_s", "")
        out["time_window_end_s"] = row.get("window_end_s", "")
        out["time_window_source"] = rel(TIME_WINDOW_OBS)
        out["n_samples"] = row.get("n_samples", "")
        out["uncertainty_value"] = row.get("uncertainty_total", "")
        out["uncertainty_units"] = row.get("qoi_units", "")
        out["uncertainty_method"] = row.get("uncertainty_method", "")
        out["window_state"] = row.get("window_state", "")
        out["independence_group_id"] = row.get("independence_group_id", "")
        out["source_case_root"] = row.get("source_path", out["source_case_root"])
        out["fit_eligible"] = "no"
        out["fit_use_status"] = "validation_only"
        out["validation_use_status"] = "validation_target"
        out["pressure_method"] = "mass_flow_monitor_timeseries" if family == "pressure" else "not_applicable"
        out["thermal_method"] = "thermal_monitor_timeseries" if family == "thermal" else "not_applicable"
        out["provenance_notes"] = "From July 7 quasi-steady UQ table; used as validation target, not extra independent fit rows."
        rows.append(out)
    return rows


def build_observation_rows() -> list[dict[str, Any]]:
    rows = []
    rows.extend(pressure_rows())
    rows.extend(momentum_rows())
    rows.extend(segment_friction_rows())
    rows.extend(thermal_rows())
    rows.extend(heat_ledger_rows())
    rows.extend(thermal_interface_residual_rows())
    rows.extend(thermal_openfoam_interface_rows())
    rows.extend(time_window_rows())
    rows = [row for row in rows if row["source_id"] in ADMITTED_SOURCES]
    rows.sort(key=lambda row: (row["source_id"], row["observable_family"], row["span"], row["quantity"], row["source_row_key"]))
    seen: set[str] = set()
    for row in rows:
        base = row["observation_id"]
        if base not in seen:
            seen.add(base)
            continue
        suffix = 2
        candidate = f"{base}:{suffix}"
        while candidate in seen:
            suffix += 1
            candidate = f"{base}:{suffix}"
        row["observation_id"] = candidate
        seen.add(candidate)
    return rows


def validate_rows(rows: list[dict[str, Any]], *, require_source_exists: bool = True) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    for index, row in enumerate(rows, start=2):
        row_id = row.get("observation_id", f"row_{index}")
        if row_id in ids:
            errors.append(f"{row_id}: duplicate observation_id")
        ids.add(row_id)
        for field in REQUIRED:
            value = str(row.get(field, "")).strip()
            if value == "":
                errors.append(f"{row_id}: missing required field {field}")
        for field in ("time_window_start_s", "time_window_end_s", "value"):
            if not finite(row.get(field)):
                errors.append(f"{row_id}: {field} is not finite")
        if finite(row.get("time_window_start_s")) and finite(row.get("time_window_end_s")):
            if float(row["time_window_end_s"]) < float(row["time_window_start_s"]):
                errors.append(f"{row_id}: time window end precedes start")
        if row.get("source_id") not in ADMITTED_SOURCES:
            errors.append(f"{row_id}: non-admitted source_id {row.get('source_id')}")
        for field in (
            "fit_eligible",
            "validation_eligible",
            "needs_special_gate_scrutiny",
            "recirculation_flag",
            "radiation_present",
        ):
            if row.get(field) not in BOOL_ENUM:
                errors.append(f"{row_id}: {field} must be yes/no")
        if row.get("fit_eligible") == "yes" and row.get("admission_status") != "admitted_mainline":
            errors.append(f"{row_id}: fit-eligible row is not admitted_mainline")
        if row.get("fit_eligible") == "yes" and row.get("needs_special_gate_scrutiny") != "no":
            errors.append(f"{row_id}: fit-eligible row needs special gate scrutiny")
        if row.get("fit_eligible") == "yes" and row.get("recirculation_flag") == "yes":
            errors.append(f"{row_id}: recirculation-contaminated row is fit eligible")
        if row.get("fit_eligible") == "yes" and "recirculation" in row.get("quality_flags", ""):
            errors.append(f"{row_id}: recirculation-quality row is fit eligible")
        if row.get("run_class") not in RUN_CLASS_ENUM:
            errors.append(f"{row_id}: invalid run_class {row.get('run_class')}")
        if row.get("admission_status") not in ADMISSION_ENUM:
            errors.append(f"{row_id}: invalid admission_status {row.get('admission_status')}")
        if row.get("fit_use_status") not in FIT_USE_ENUM:
            errors.append(f"{row_id}: invalid fit_use_status {row.get('fit_use_status')}")
        if row.get("window_state") not in WINDOW_STATE_ENUM:
            errors.append(f"{row_id}: invalid window_state {row.get('window_state')}")
        if row.get("mesh_status") not in MESH_STATUS_ENUM:
            errors.append(f"{row_id}: invalid mesh_status {row.get('mesh_status')}")
        if require_source_exists:
            source_path = ROOT / str(row.get("source_path", ""))
            if not source_path.exists():
                errors.append(f"{row_id}: source_path does not exist: {row.get('source_path')}")
    return errors


def excluded_sources_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(SCENARIO_CONTRACT):
        source_id = row.get("source_id", "")
        if source_id in ADMITTED_SOURCES:
            continue
        reason = "not_seeded_by_this_contract"
        if source_id.startswith("viscosity_screening_salt_test_1"):
            reason = "held_salt1_qualification_required"
        if row.get("run_class") == "corrected_salt_q_perturbation":
            reason = "held_until_formal_gate_requalified"
        rows.append(
            {
                "source_id": source_id,
                "case_id": row.get("case_id", ""),
                "run_class": row.get("run_class", ""),
                "fit_use_status": row.get("fit_use_status", ""),
                "needs_special_gate_scrutiny": row.get("needs_special_gate_scrutiny", ""),
                "exclusion_reason": reason,
                "source_path": rel(SCENARIO_CONTRACT),
            }
        )
    if CORRECTED_GATE.exists():
        rows.append(
            {
                "source_id": "corrected_salt_q_gate_package",
                "case_id": "",
                "run_class": "corrected_salt_q_perturbation",
                "fit_use_status": "held",
                "needs_special_gate_scrutiny": "yes",
                "exclusion_reason": "formal corrected-Salt gate not admitted into closure_observations",
                "source_path": rel(CORRECTED_GATE),
            }
        )
    if LIVE_MONITOR.exists():
        rows.append(
            {
                "source_id": "corrected_salt_live_monitor",
                "case_id": "",
                "run_class": "corrected_salt_q_perturbation",
                "fit_use_status": "held",
                "needs_special_gate_scrutiny": "yes",
                "exclusion_reason": "live monitor is operations evidence, not closure-fit admission",
                "source_path": rel(LIVE_MONITOR),
            }
        )
    return rows


def write_readme(rows: list[dict[str, Any]], validation_errors: list[str]) -> None:
    counts = Counter(row["observable_family"] for row in rows)
    fit_count = sum(1 for row in rows if row["fit_eligible"] == "yes")
    text = f"""# Closure Observation Table Contract

Generated: `{datetime.now().isoformat(timespec='seconds')}`

## Scope

This package defines the canonical `closure_observations.csv` contract for the
current closure work. The seed rows are limited to admitted Salt 2/3/4 Jin
mainline continuations. Salt 1, Water, and corrected Salt Q perturbations are
excluded until their separate gates explicitly admit them.

## Contract

- One row is one observable, not a case summary.
- Units, mesh level, source path, source case root, time window, admission
  status, and fit/validation eligibility are mandatory.
- `fit_eligible` and `validation_eligible` are independent fields.
- Debuoyed momentum/pressure-ledger friction rows are fit targets only outside
  recirculation-invalid spans.
- Patchwise heat rows from the older heat ledger remain validation diagnostics;
  physical-interface enthalpy residual rows are carried as validation-only
  thermal evidence with bracketing status and residual assignment explicit.
- OpenFOAM physical-interface sample rows preserve signed mixing-cup
  temperatures, forward-flow temperatures, directional flux proxies, and
  backflow fractions separately. Rows flagged by recirculation/backflow are not
  fit targets.
- Radiation is not inferred from wall emissivity metadata. `radiation_present`
  is `yes` only if OpenFOAM outputs/samples a radiation term; current thermal
  rows carry `absent_no_qr_output`.
- Time-window rows are validation targets, not extra independent training
  samples, because samples from the same relaxation path are correlated.

## Outputs

- `closure_observations.csv`: canonical seed observation table.
- `closure_observation_schema.csv`: required columns, units, allowed values,
  and descriptions.
- `excluded_sources.csv`: explicit list of scenario/gate sources not admitted
  to the seed table.
- `summary.json`: counts, validation result, and source artifact list.

## Counts

- Total observation rows: `{len(rows)}`
- Fit-eligible rows: `{fit_count}`
- Pressure/time-window/thermal families: `{dict(sorted(counts.items()))}`
- Validation errors: `{len(validation_errors)}`

## Source Artifacts

- `{rel(PRESSURE_LEDGER)}`
- `{rel(MOMENTUM_BUDGET)}`
- `{rel(SEGMENT_FRICTION)}`
- `{rel(THERMAL_HTC_DIR)}`
- `{rel(HEAT_LEDGER)}`
- `{rel(ENTHALPY_LEDGER)}`
- `{rel(ENTHALPY_RESIDUALS)}`
- `{rel(THERMAL_OPENFOAM_SAMPLES)}`
- `{rel(THERMAL_OPENFOAM_PLAN)}`
- `{rel(TIME_WINDOW_OBS)}`
- `{rel(SOURCE_CONTRACT)}`
- `{rel(SCENARIO_CONTRACT)}`

## Downstream Order

Pressure-ledger hardening, patchwise heat-ledger hardening, and model-form
bakeoff should consume this table or emit rows conforming to this schema rather
than creating bespoke target-data CSVs.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_outputs(rows: list[dict[str, Any]], errors: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "closure_observations.csv", rows, FIELDS)
    write_csv(OUT / "closure_observation_schema.csv", SCHEMA, ["column", "required", "units", "allowed", "description"])
    excluded_fields = ["source_id", "case_id", "run_class", "fit_use_status", "needs_special_gate_scrutiny", "exclusion_reason", "source_path"]
    write_csv(OUT / "excluded_sources.csv", excluded_sources_rows(), excluded_fields)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "observation_rows": len(rows),
        "fit_eligible_rows": sum(1 for row in rows if row["fit_eligible"] == "yes"),
        "validation_eligible_rows": sum(1 for row in rows if row["validation_eligible"] == "yes"),
        "source_ids": sorted({row["source_id"] for row in rows}),
        "families": dict(sorted(Counter(row["observable_family"] for row in rows).items())),
        "source_artifacts": [
            rel(PRESSURE_LEDGER),
            rel(MOMENTUM_BUDGET),
            rel(SEGMENT_FRICTION),
            rel(THERMAL_HTC_DIR),
            rel(HEAT_LEDGER),
            rel(ENTHALPY_LEDGER),
            rel(ENTHALPY_RESIDUALS),
            rel(THERMAL_OPENFOAM_SAMPLES),
            rel(THERMAL_OPENFOAM_PLAN),
            rel(TIME_WINDOW_OBS),
            rel(SOURCE_CONTRACT),
            rel(SCENARIO_CONTRACT),
        ],
        "validation_errors": errors,
        "validation_passed": not errors,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(rows, errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="validate existing output instead of rebuilding")
    args = parser.parse_args(argv)
    if args.validate_only:
        rows = read_csv(OUT / "closure_observations.csv")
    else:
        rows = build_observation_rows()
    errors = validate_rows(rows)
    if not args.validate_only:
        write_outputs(rows, errors)
    print(f"closure_observation_rows={len(rows)}")
    print(f"validation_errors={len(errors)}")
    if errors:
        for error in errors[:20]:
            print(f"ERROR: {error}")
        return 1
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
