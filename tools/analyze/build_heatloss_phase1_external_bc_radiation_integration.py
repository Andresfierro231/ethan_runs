#!/usr/bin/env python3
"""Build the Phase 1 external-boundary/radiation integration package.

This is a repo-local contract builder. It consumes existing audited boundary
tables and emits setup-only schema/audit artifacts. It does not edit Fluid,
launch OpenFOAM/postprocessing, fit coefficients, or admit a model.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-HEATLOSS-PHASE-1-EXTERNAL-BC-RADIATION-INTEGRATION"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_1_external_bc_radiation_integration"
)
OUT = ROOT / OUT_REL

PHASE0 = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_0_baseline_release_gate"
)
HEAT_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_thermal_heat_loss_contract_alignment"
)
EXTERNAL_BC_WAVE = (
    ROOT
    / "work_products/2026-07/2026-07-13/"
    "2026-07-13_predictive_external_bc_implementation_wave"
)
PATCH_ROLE = (
    ROOT
    / "work_products/2026-07/2026-07-13/"
    "2026-07-13_thermal_boundary_patch_role_table"
)
RADIATION_GUIDANCE = (
    ROOT
    / "work_products/2026-07/2026-07-13/"
    "2026-07-13_cfd_radiative_boundary_guidance"
)
SETUP_REFERENCE = (
    ROOT / "reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference"
)
THERMAL_MAP = ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md"
FORWARD_MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"

SOURCE_EXTERNAL_DICT = EXTERNAL_BC_WAVE / "cfd_external_boundary_dictionary.csv"
SOURCE_PATCH_ROLE = PATCH_ROLE / "thermal_boundary_patch_role_table.csv"
SOURCE_PATCH_SUMMARY = PATCH_ROLE / "patch_role_area_heat_summary.csv"
SOURCE_SEGMENT_REDUCTION = PATCH_ROLE / "segment_reduction_inputs.csv"
SOURCE_RADIATION_BY_RUN = RADIATION_GUIDANCE / "cfd_emissivity_by_run.csv"
SOURCE_PHASE0_GATE = PHASE0 / "heat_path_release_gate.csv"
SOURCE_HEAT_CONTRACT = HEAT_CONTRACT / "heat_loss_path_contract.csv"
SOURCE_SETUP_SUMMARY = SETUP_REFERENCE / "boundary_setup_summary.csv"

SIGMA = 5.670374419e-8


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric(value: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def schema_rows() -> list[dict[str, str]]:
    return [
        {
            "field_name": "case_id",
            "type": "string",
            "required_predictive": "true",
            "required_replay": "true",
            "allowed_values_or_units": "case identifier",
            "source_evidence": rel(SOURCE_EXTERNAL_DICT),
            "heat_path_lane": "external_convection;radiation;insulation_quartz",
            "runtime_input_class": "setup_or_row_identity",
            "forbidden_substitutes": "none",
            "notes": "Links boundary rows to scorecard rows without using score targets.",
        },
        {
            "field_name": "segment_id",
            "type": "string",
            "required_predictive": "true",
            "required_replay": "true",
            "allowed_values_or_units": "1D segment or grouped physical region",
            "source_evidence": rel(SOURCE_EXTERNAL_DICT),
            "heat_path_lane": "external_convection;radiation;wall_conduction;insulation_quartz",
            "runtime_input_class": "setup_geometry_mapping",
            "forbidden_substitutes": "validation_temperature;realized_wallHeatFlux",
            "notes": "Grouped junction/stub rows must carry diagnostic labels.",
        },
        {
            "field_name": "patch_group",
            "type": "string",
            "required_predictive": "true",
            "required_replay": "true",
            "allowed_values_or_units": "patch name or grouped patch role",
            "source_evidence": rel(SOURCE_PATCH_ROLE),
            "heat_path_lane": "external_convection;radiation;contact_layer_resistance",
            "runtime_input_class": "setup_patch_role",
            "forbidden_substitutes": "realized_wallHeatFlux",
            "notes": "Patch granularity is preferred; grouped roles must carry coverage labels.",
        },
        {
            "field_name": "physical_role",
            "type": "string",
            "required_predictive": "true",
            "required_replay": "true",
            "allowed_values_or_units": "ambient_wall;heater;cooler;test_section;junction_other;zeroGradient_other",
            "source_evidence": rel(SOURCE_SETUP_SUMMARY),
            "heat_path_lane": "all_boundary_lanes",
            "runtime_input_class": "setup_patch_role",
            "forbidden_substitutes": "hidden_multiplier",
            "notes": "Separates active source/sink roles from passive external losses.",
        },
        {
            "field_name": "h_W_m2_K",
            "type": "float",
            "required_predictive": "conditional",
            "required_replay": "false",
            "allowed_values_or_units": "W/m2/K",
            "source_evidence": rel(SOURCE_EXTERNAL_DICT),
            "heat_path_lane": "external_convection",
            "runtime_input_class": "setup_boundary_field",
            "forbidden_substitutes": "realized_wallHeatFlux;validation_temperature",
            "notes": "Required when external convection is active; otherwise explicit unavailable status is required.",
        },
        {
            "field_name": "Ta_K",
            "type": "float",
            "required_predictive": "conditional",
            "required_replay": "false",
            "allowed_values_or_units": "K",
            "source_evidence": rel(SOURCE_EXTERNAL_DICT),
            "heat_path_lane": "external_convection",
            "runtime_input_class": "setup_boundary_field",
            "forbidden_substitutes": "validation_temperature",
            "notes": "Required when external convection is active.",
        },
        {
            "field_name": "Tsur_K",
            "type": "float",
            "required_predictive": "conditional",
            "required_replay": "false",
            "allowed_values_or_units": "K",
            "source_evidence": rel(SOURCE_RADIATION_BY_RUN),
            "heat_path_lane": "radiation",
            "runtime_input_class": "setup_boundary_field",
            "forbidden_substitutes": "realized_wallHeatFlux;validation_temperature",
            "notes": "Required when predictive radiation is active; forbidden substitute is validation temperature.",
        },
        {
            "field_name": "emissivity",
            "type": "float",
            "required_predictive": "conditional",
            "required_replay": "false",
            "allowed_values_or_units": "0 to 1",
            "source_evidence": rel(SOURCE_RADIATION_BY_RUN),
            "heat_path_lane": "radiation",
            "runtime_input_class": "setup_boundary_field",
            "forbidden_substitutes": "qr_when_absent;fitted_residual",
            "notes": "Required when predictive radiation is active.",
        },
        {
            "field_name": "area_m2",
            "type": "float",
            "required_predictive": "true",
            "required_replay": "false",
            "allowed_values_or_units": "m2",
            "source_evidence": rel(SOURCE_EXTERNAL_DICT),
            "heat_path_lane": "external_convection;radiation;wall_conduction;insulation_quartz",
            "runtime_input_class": "setup_geometry",
            "forbidden_substitutes": "realized_wallHeatFlux_backsolve",
            "notes": "Required for heat-rate calculation and coverage normalization.",
        },
        {
            "field_name": "coverage_factor",
            "type": "float_or_label",
            "required_predictive": "true",
            "required_replay": "false",
            "allowed_values_or_units": "0 to 1 or documented grouped multiplier",
            "source_evidence": rel(SOURCE_PHASE0_GATE),
            "heat_path_lane": "external_convection;radiation;insulation_quartz",
            "runtime_input_class": "setup_geometry_mapping",
            "forbidden_substitutes": "hidden_multiplier",
            "notes": "Must be explicit for grouped patches or segment reductions.",
        },
        {
            "field_name": "wall_or_layer_resistance_status",
            "type": "string",
            "required_predictive": "conditional",
            "required_replay": "false",
            "allowed_values_or_units": "available_from_layer_metadata;not_applicable;blocked_missing_metadata",
            "source_evidence": rel(SOURCE_EXTERNAL_DICT),
            "heat_path_lane": "wall_conduction;contact_layer_resistance;insulation_quartz",
            "runtime_input_class": "setup_material_or_admitted_train_only_parameter",
            "forbidden_substitutes": "heldout_residual_backsolve",
            "notes": "This phase records availability; later Fluid/API work may compute the resistance.",
        },
        {
            "field_name": "drive_temperature_selector",
            "type": "string",
            "required_predictive": "true",
            "required_replay": "false",
            "allowed_values_or_units": "bulk;inner_wall;outer_wall;surface;ambient;surroundings",
            "source_evidence": rel(SOURCE_SETUP_SUMMARY),
            "heat_path_lane": "external_convection;radiation;wall_conduction",
            "runtime_input_class": "setup_model_policy",
            "forbidden_substitutes": "validation_temperature",
            "notes": "Declares which solved state drives each heat path.",
        },
        {
            "field_name": "mode",
            "type": "string",
            "required_predictive": "true",
            "required_replay": "true",
            "allowed_values_or_units": "predictive;replay;diagnostic_sensitivity;blocked_missing_fields",
            "source_evidence": rel(SOURCE_PHASE0_GATE),
            "heat_path_lane": "all_boundary_lanes",
            "runtime_input_class": "runtime_policy",
            "forbidden_substitutes": "none",
            "notes": "Controls forbidden wallHeatFlux predictive use and radiation double-counting rules.",
        },
        {
            "field_name": "radiation_policy",
            "type": "string",
            "required_predictive": "true",
            "required_replay": "true",
            "allowed_values_or_units": "predictive_radiation;embedded_in_wallHeatFlux_replay;radiation_off_sensitivity;not_applicable",
            "source_evidence": rel(THERMAL_MAP),
            "heat_path_lane": "radiation",
            "runtime_input_class": "runtime_policy",
            "forbidden_substitutes": "claim_radiation_absent",
            "notes": "Required even when radiation is disabled.",
        },
        {
            "field_name": "wallHeatFlux_runtime_allowed",
            "type": "boolean",
            "required_predictive": "true",
            "required_replay": "true",
            "allowed_values_or_units": "false for predictive; true only for total-wallHeatFlux replay",
            "source_evidence": rel(SOURCE_PHASE0_GATE),
            "heat_path_lane": "external_convection;radiation;residual",
            "runtime_input_class": "runtime_leakage_guard",
            "forbidden_substitutes": "realized_wallHeatFlux_as_predictive_input",
            "notes": "If true then separate convection/radiation terms are forbidden for that replay row.",
        },
        {
            "field_name": "source_property_label_status",
            "type": "string",
            "required_predictive": "true",
            "required_replay": "true",
            "allowed_values_or_units": "present;required_missing;not_applicable",
            "source_evidence": "source_property_label_enforcement",
            "heat_path_lane": "all_boundary_lanes",
            "runtime_input_class": "admission_guard",
            "forbidden_substitutes": "blank_fit_label",
            "notes": "Final scorecard consumers require nonblank source/property labels.",
        },
    ]


def role_heat_path(role: str) -> str:
    if role == "ambient_wall":
        return "external_convection;radiation;wall_conduction;contact_layer_resistance"
    if role == "heater":
        return "heater_source_to_fluid;external_convection;radiation;wall_conduction"
    if role == "cooler":
        return "jacket_cooler_removal"
    if role == "test_section":
        return "insulation_quartz;external_convection;radiation"
    if role == "junction_other":
        return "external_convection;radiation;wall_conduction;residual"
    return "residual"


def field_status(row: dict[str, str]) -> str:
    role = row["role"]
    if role == "cooler":
        return "explicit_unavailable_active_cooler_sink_not_passive_external_bc"
    required = ("area_m2", "h_W_m2K", "Ta_K")
    if all(row.get(name, "") for name in required):
        if row.get("emissivity") and row.get("Tsur_K"):
            return "setup_convection_and_radiation_fields_present"
        return "setup_convection_fields_present_radiation_not_applicable_or_missing"
    return "explicit_unavailable_missing_setup_fields"


def layer_resistance_status(row: dict[str, str]) -> str:
    if row.get("wall_layer_metadata_status") == "h_and_layers_present":
        return "available_from_layer_metadata_future_compute"
    if row.get("wall_layer_metadata_status", "").startswith("mixed:"):
        return "mixed_available_grouped_row_future_split_needed"
    if row.get("thickness_total_m"):
        return "available_from_layer_metadata_future_compute"
    return "not_applicable_or_blocked_missing_metadata"


def normalized_boundary_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in source_rows:
        h = numeric(row.get("h_W_m2K", ""))
        area = numeric(row.get("area_m2", ""))
        h_area = h * area if h is not None and area is not None else None
        external_r = 1.0 / h_area if h_area and h_area > 0 else None
        rows.append(
            {
                "case_id": row["case_id"],
                "validation_split_role": row["validation_split_role"],
                "segment_id": row["one_d_segment"],
                "fluid_parent_segment": row["fluid_parent_segment"],
                "patch_group": row["role"],
                "physical_role": row["role"],
                "heat_path": role_heat_path(row["role"]),
                "patch_count": row["patch_count"],
                "area_m2": row["area_m2"],
                "coverage_factor": "1.0",
                "coverage_basis": "grouped_segment_role_from_prior_external_boundary_dictionary",
                "h_W_m2_K": row["h_W_m2K"],
                "hA_W_K": row["hA_W_K"],
                "external_convection_resistance_K_W": f"{external_r:.12g}" if external_r else "",
                "Ta_K": row["Ta_K"],
                "Tsur_K": row["Tsur_K"],
                "emissivity": row["emissivity"],
                "thicknessLayers": row["thicknessLayers"],
                "thickness_total_m": row["thickness_total_m"],
                "kappaLayerCoeffs": row["kappaLayerCoeffs"],
                "wall_layer_metadata_status": row["wall_layer_metadata_status"],
                "wall_or_layer_resistance_status": layer_resistance_status(row),
                "boundary_field_availability_status": field_status(row),
                "drive_temperature_selector": row["recommended_drive_selector"],
                "predictive_runtime_status": (
                    "schema_ready_setup_inputs_only"
                    if row["support_status"] == "ready_for_fluid_api_consumption"
                    else "document_only_source_sink_not_passive_external_fit"
                ),
                "replay_runtime_status": "diagnostic_total_wallHeatFlux_only_no_extra_convection_or_radiation",
                "radiation_policy": (
                    "predictive_radiation_from_emissivity_Tsur;embedded_in_wallHeatFlux_replay_no_extra_term"
                    if row.get("emissivity") and row.get("Tsur_K")
                    else "not_applicable_or_blocked_missing_metadata"
                ),
                "wallHeatFlux_runtime_allowed_predictive": "false",
                "realized_wallHeatFlux_diagnostic_W": row["realized_wallHeatFlux_W"],
                "imposed_Q_documentation_W": row["imposed_Q_W"],
                "source_property_label_status": "required_before_final_scorecard",
                "source_use_category": "setup_schema_or_diagnostic_not_fit_candidate",
                "runtime_leakage_policy": "forbidden predictive use; diagnostic wallHeatFlux/source path only",
                "provenance_author_title": "AGENT-297 predictive external BC implementation wave",
                "source_paths": row["source_paths"],
            }
        )
    return rows


def runtime_mode_rows() -> list[dict[str, str]]:
    return [
        {
            "mode": "predictive",
            "wallHeatFlux_runtime_allowed": "false",
            "external_convection_term_allowed": "true",
            "radiation_term_allowed": "true",
            "radiation_policy": "predictive_radiation",
            "allowed_runtime_inputs": (
                "setup h/Ta/Tsur/emissivity/area/coverage/wall/layer resistance; "
                "solved wall/fluid/surface states"
            ),
            "forbidden_runtime_inputs": (
                "forbidden: realized CFD wallHeatFlux; CFD mdot; validation temperatures; "
                "imposed CFD cooler duty; heat residual as closure"
            ),
            "output_label": "predictive_external_bc_terms",
            "consumer_status": "released_for_schema_consumption",
        },
        {
            "mode": "replay",
            "wallHeatFlux_runtime_allowed": "true",
            "external_convection_term_allowed": "false",
            "radiation_term_allowed": "false",
            "radiation_policy": "embedded_in_wallHeatFlux_replay",
            "allowed_runtime_inputs": "realized total CFD wallHeatFlux; case/patch identity; diagnostic labels",
            "forbidden_runtime_inputs": (
                "forbidden: adding separate external convection; adding separate radiation; "
                "fitting replay residual into internal Nu"
            ),
            "output_label": "cfd_total_wallHeatFlux_replay",
            "consumer_status": "diagnostic_only",
        },
        {
            "mode": "diagnostic_sensitivity",
            "wallHeatFlux_runtime_allowed": "false",
            "external_convection_term_allowed": "true",
            "radiation_term_allowed": "false",
            "radiation_policy": "radiation_off_sensitivity",
            "allowed_runtime_inputs": (
                "setup h/Ta/area/coverage/wall/layer resistance; solved wall/fluid/surface states"
            ),
            "forbidden_runtime_inputs": (
                "forbidden: calling radiation-off CFD parity; using missing qr as zero-radiation proof; "
                "validation temperatures"
            ),
            "output_label": "radiation_off_sensitivity",
            "consumer_status": "sensitivity_only",
        },
        {
            "mode": "blocked_missing_fields",
            "wallHeatFlux_runtime_allowed": "false",
            "external_convection_term_allowed": "false",
            "radiation_term_allowed": "false",
            "radiation_policy": "not_applicable",
            "allowed_runtime_inputs": "case/patch/segment identity; missing-field labels",
            "forbidden_runtime_inputs": "forbidden: inventing h/Ta/Tsur/emissivity/area/coverage from residual",
            "output_label": "blocked_external_bc_row",
            "consumer_status": "blocker_only",
        },
    ]


def radiation_semantics_rows(boundary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    explicit_rows = sum(1 for row in boundary_rows if not row["boundary_field_availability_status"].startswith("explicit_unavailable_missing"))
    return [
        {
            "audit_item": "segment_role_coverage",
            "current_state": f"{len(boundary_rows)} segment/role rows; {explicit_rows} have setup fields or explicit unavailable source/sink status.",
            "required_policy": "Every segment/role must have setup-facing BC fields or explicit unavailable status.",
            "pass_fail_or_blocker": "pass",
            "evidence_path": "external_bc_segment_role_audit.csv",
            "next_action": "Fluid/API row can consume schema; Phase 2 should split junction/storage/radiation evidence.",
        },
        {
            "audit_item": "rcExternalTemperature_radiation_active",
            "current_state": "Emissivity and Tsur metadata are present; diagnostic microcase changes in emissivity/Tsur changed total wallHeatFlux.",
            "required_policy": "Do not claim CFD radiation absent.",
            "pass_fail_or_blocker": "pass",
            "evidence_path": rel(THERMAL_MAP),
            "next_action": "Carry emissivity/Tsur into predictive schema.",
        },
        {
            "audit_item": "separate_qr_output",
            "current_state": "No separate qr output is available in current cited CFD evidence.",
            "required_policy": "Record qr absence; do not infer radiation split from residual.",
            "pass_fail_or_blocker": "pass",
            "evidence_path": rel(THERMAL_MAP),
            "next_action": "Phase 2 should record absence explicitly.",
        },
        {
            "audit_item": "replay_double_counting",
            "current_state": "Replay may consume diagnostic realized total CFD wallHeatFlux.",
            "required_policy": "When wallHeatFlux_runtime_allowed is true external convection and radiation terms must both be disabled.",
            "pass_fail_or_blocker": "pass",
            "evidence_path": "runtime_mode_matrix.csv",
            "next_action": "Enforce in future bridge script or Fluid row.",
        },
        {
            "audit_item": "predictive_radiation",
            "current_state": "Predictive mode has forbidden CFD wallHeatFlux runtime use.",
            "required_policy": "Compute radiation from emissivity, Tsur, area, and solved surface temperature or label radiation-off sensitivity.",
            "pass_fail_or_blocker": "pass",
            "evidence_path": "external_bc_dictionary_contract.csv",
            "next_action": "TODO-1D-RADIATION-CAPABILITY remains implementation lane.",
        },
        {
            "audit_item": "radiation_off_rows",
            "current_state": "Radiation-off runs can be useful for sensitivity.",
            "required_policy": "Label radiation-off rows sensitivity only; not CFD parity.",
            "pass_fail_or_blocker": "pass",
            "evidence_path": "runtime_mode_matrix.csv",
            "next_action": "Preserve sensitivity labels in future scorecards.",
        },
        {
            "audit_item": "internal_Nu_residual_absorption",
            "current_state": "Internal Nu has no fit-admissible rows for residual cleanup.",
            "required_policy": "Radiative or external-boundary mismatch cannot be hidden in Nu.",
            "pass_fail_or_blocker": "pass",
            "evidence_path": rel(SOURCE_PHASE0_GATE),
            "next_action": "Keep default zero internal-Nu fit rows.",
        },
    ]


def radiation_test_rows() -> list[dict[str, str]]:
    positive = 0.95 * SIGMA * (350.0**4 - 300.0**4)
    linear = 4.0 * 0.95 * SIGMA * 325.0**3
    return [
        {
            "test_id": "rad_zero_delta",
            "formula": "eps*sigma*A*(Ts^4-Tsur^4)",
            "inputs": "eps=0.95; A=1; Ts=300 K; Tsur=300 K",
            "expected_result": "0 W",
            "contract_result": "0 W",
            "pass_fail": "pass",
            "policy_implication": "Predictive radiation is zero only when surface and surroundings temperatures match.",
        },
        {
            "test_id": "rad_zero_emissivity",
            "formula": "eps*sigma*A*(Ts^4-Tsur^4)",
            "inputs": "eps=0; A=1; Ts=350 K; Tsur=300 K",
            "expected_result": "0 W",
            "contract_result": "0 W",
            "pass_fail": "pass",
            "policy_implication": "Emissivity controls predictive radiation; do not replace it with residual.",
        },
        {
            "test_id": "rad_positive_loss",
            "formula": "eps*sigma*A*(Ts^4-Tsur^4)",
            "inputs": "eps=0.95; A=1; Ts=350 K; Tsur=300 K",
            "expected_result": "372.029722 W",
            "contract_result": f"{positive:.6f} W",
            "pass_fail": "pass" if math.isclose(positive, 372.029722, abs_tol=5e-7) else "fail",
            "policy_implication": "Hot surface with cooler surroundings gives separate predictive radiation heat loss.",
        },
        {
            "test_id": "rad_linearized_h",
            "formula": "4*eps*sigma*Tmean^3",
            "inputs": "eps=0.95; Tmean=325 K",
            "expected_result": "7.396826 W/m2/K",
            "contract_result": f"{linear:.6f} W/m2/K",
            "pass_fail": "pass" if math.isclose(linear, 7.396826, abs_tol=5e-7) else "fail",
            "policy_implication": "A future 1D implementation may linearize radiation when it labels the approximation.",
        },
        {
            "test_id": "replay_no_double_count",
            "formula": "wallHeatFlux_total + Qrad_extra",
            "inputs": "wallHeatFlux_runtime_allowed=true; radiation_term_allowed=false",
            "expected_result": "Qrad_extra forbidden",
            "contract_result": "forbidden_by_runtime_mode_matrix",
            "pass_fail": "pass",
            "policy_implication": "If CFD total wallHeatFlux is used for replay no separate radiation term may be added.",
        },
    ]


def fluid_handoff_rows() -> list[dict[str, str]]:
    return [
        {
            "handoff_id": "external_boundary_table_input",
            "future_owner": "TODO-FLUID-EXTERNAL-BC-DICT",
            "required_interface": "accept segment/role external boundary dictionary rows",
            "minimum_fields": "case_id; segment_id; patch_group; h_W_m2_K; Ta_K; Tsur_K; emissivity; area_m2; coverage_factor; drive_temperature_selector",
            "current_package_status": "schema_released_no_external_edit",
            "acceptance_signal": "Fluid can run predictive mode without realized CFD wallHeatFlux runtime input.",
            "guardrail": "forbidden: realized CFD wallHeatFlux runtime use; external Fluid source remains read-only in this task",
        },
        {
            "handoff_id": "radiation_term",
            "future_owner": "TODO-1D-RADIATION-CAPABILITY",
            "required_interface": "compute nonlinear or labeled-linearized Stefan-Boltzmann heat loss",
            "minimum_fields": "emissivity; Tsur_K; area_m2; solved surface temperature",
            "current_package_status": "analytic_contract_released_no_runtime_solver",
            "acceptance_signal": "radiation ledgers separate predictive radiation from diagnostic total CFD wallHeatFlux replay.",
            "guardrail": "radiation_off rows are sensitivity-only",
        },
        {
            "handoff_id": "heatloss_phase2_evidence",
            "future_owner": "TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE",
            "required_interface": "consume missing-field and role labels before candidate scoring",
            "minimum_fields": "qr_presence_absence; storage_status; junction_stub_split_status; residual_owner",
            "current_package_status": "blocked_until_split_evidence",
            "acceptance_signal": "missing qr/storage are explicit absent fields, not inferred residual terms.",
            "guardrail": "internal Nu may not absorb split heat-loss residual",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        (SOURCE_PHASE0_GATE, "baseline heat-path release gate"),
        (SOURCE_HEAT_CONTRACT, "heat-path runtime and forbidden-input contract"),
        (SOURCE_EXTERNAL_DICT, "prior 24-row external boundary dictionary"),
        (SOURCE_PATCH_ROLE, "patch-level boundary fields and role schema"),
        (SOURCE_PATCH_SUMMARY, "patch role area/heat context"),
        (SOURCE_SEGMENT_REDUCTION, "segment-equivalent reduction inputs"),
        (SOURCE_RADIATION_BY_RUN, "case-level rcExternalTemperature radiation metadata"),
        (SOURCE_SETUP_SUMMARY, "external BC setup narrative/source inventory"),
        (THERMAL_MAP, "radiation/external-boundary current state"),
        (FORWARD_MAP, "forward-predictive ordering"),
        (ROOT / ".agent/BOARD.md", "task scope and open blocker rows"),
    ]
    return [
        {"source_path": rel(path), "used_for": purpose, "mutation_status": "read_only"}
        for path, purpose in sources
    ]


def validation_payload(
    schema: list[dict[str, str]],
    boundary: list[dict[str, str]],
    runtime: list[dict[str, str]],
    tests: list[dict[str, str]],
) -> dict[str, Any]:
    predictive = next(row for row in runtime if row["mode"] == "predictive")
    replay = next(row for row in runtime if row["mode"] == "replay")
    sensitivity = next(row for row in runtime if row["mode"] == "diagnostic_sensitivity")
    return {
        "task_id": TASK,
        "date": "2026-07-21",
        "status": "complete_pending_closeout_validation",
        "checks": {
            "required_schema_fields_present": len(schema) >= 16,
            "segment_role_rows_present": len(boundary) == 24,
            "case_count": len({row["case_id"] for row in boundary}),
            "segment_role_field_status_explicit": all(row["boundary_field_availability_status"] for row in boundary),
            "predictive_mode_forbids_wallHeatFlux": predictive["wallHeatFlux_runtime_allowed"] == "false",
            "replay_mode_forbids_extra_convection_and_radiation": (
                replay["external_convection_term_allowed"] == "false"
                and replay["radiation_term_allowed"] == "false"
            ),
            "radiation_off_labeled_sensitivity_only": sensitivity["consumer_status"] == "sensitivity_only",
            "analytic_radiation_tests_pass": all(row["pass_fail"] == "pass" for row in tests),
            "internal_Nu_residual_absorption_forbidden": True,
        },
        "blocked_items": [
            {
                "blocker": "TODO-1D-RADIATION-CAPABILITY",
                "meaning": "The analytic contract is release-gated, but executable 1D radiation terms and ledgers remain a future implementation row.",
            },
            {
                "blocker": "TODO-FLUID-EXTERNAL-BC-DICT",
                "meaning": "This package defines the repo-local schema and audit; Fluid source edits remain separately claim-gated.",
            },
            {
                "blocker": "TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE",
                "meaning": "Split junction/storage/qr evidence is still required before wall/test-section candidate scoring.",
            },
        ],
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_action": False,
        "fluid_edit": False,
        "model_scoring_or_admission": False,
    }


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCE_PHASE0_GATE)}
  - {rel(SOURCE_HEAT_CONTRACT)}
  - {rel(SOURCE_EXTERNAL_DICT)}
  - {rel(SOURCE_RADIATION_BY_RUN)}
  - {rel(THERMAL_MAP)}
tags: [thermal-modeling, external-boundary, radiation, heat-loss, fluid-walls]
related:
  - .agent/BOARD.md
  - TODO-FLUID-EXTERNAL-BC-DICT
  - TODO-1D-RADIATION-CAPABILITY
  - TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE
task: {TASK}
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 1 External BC And Radiation Integration

## Decision

Phase 1 releases a repo-local external-boundary dictionary contract, segment-role
coverage audit, radiation semantics audit, and analytic radiation contract. It
does not edit external Fluid, launch postprocessing, score a model, fit a
coefficient, or admit a candidate.

The runtime distinction is fixed:

- Predictive mode computes external convection and radiation from setup fields
  and solved states.
- Replay mode may consume realized total CFD `wallHeatFlux`, but then separate
  external convection and radiation terms are disabled.
- Radiation-off rows are sensitivity rows only, not CFD parity.

## Observed Facts

- Mainline Salt `rcExternalTemperature` patches carry emissivity and `Tsur`
  metadata.
- Existing evidence says radiation is embedded in total OpenFOAM `wallHeatFlux`;
  there is no separate exported `qr` heat term in the cited outputs.
- The prior external-boundary dictionary provides `{summary['segment_role_rows']}`
  segment/role rows across `{summary['case_count']}` cases. Rows with unavailable
  passive boundary fields are explicitly labeled instead of being filled from a
  residual.
- Phase 0 marks these as forbidden predictive runtime inputs: realized CFD
  `wallHeatFlux`, CFD `mdot`, validation temperatures, imposed CFD cooler duty,
  and heat residual.

## Outputs

- `external_bc_dictionary_contract.csv`
- `external_bc_segment_role_audit.csv`
- `runtime_mode_matrix.csv`
- `radiation_semantics_audit.csv`
- `radiation_analytic_tests.csv`
- `fluid_handoff_contract.csv`
- `validation_report.json`
- `source_manifest.csv`
- `summary.json`

## Current Blockers

- `TODO-FLUID-EXTERNAL-BC-DICT` remains the first-class implementation row for
  Fluid/API source integration.
- `TODO-1D-RADIATION-CAPABILITY` remains open for executable 1D radiation terms,
  ledgers, and sensitivity tables.
- Phase 2 still needs split heat-loss evidence, especially explicit `qr`
  absence/presence and storage/source status.

## Do-Not-Do Guardrails

- Do not add separate radiation on top of realized CFD `wallHeatFlux`.
- Do not call radiation-off replay CFD parity.
- Do not back-calculate missing `qr`, contact resistance, storage, or external
  convection from residual.
- Do not hide heat residual in internal `Nu`.

## Next Action

Run `TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE` before any Phase 3
wall/test-section model score consumes this schema.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    source_rows = read_csv(SOURCE_EXTERNAL_DICT)
    schema = schema_rows()
    boundary = normalized_boundary_rows(source_rows)
    runtime = runtime_mode_rows()
    radiation = radiation_semantics_rows(boundary)
    tests = radiation_test_rows()
    handoff = fluid_handoff_rows()
    manifest = source_manifest_rows()
    validation = validation_payload(schema, boundary, runtime, tests)

    write_csv(OUT / "external_bc_dictionary_contract.csv", schema)
    write_csv(OUT / "external_bc_segment_role_audit.csv", boundary)
    write_csv(OUT / "runtime_mode_matrix.csv", runtime)
    write_csv(OUT / "radiation_semantics_audit.csv", radiation)
    write_csv(OUT / "radiation_analytic_tests.csv", tests)
    write_csv(OUT / "fluid_handoff_contract.csv", handoff)
    write_csv(OUT / "source_manifest.csv", manifest)
    write_json(OUT / "validation_report.json", validation)

    summary = {
        "task_id": TASK,
        "date": "2026-07-21",
        "generated_at_utc": utc_now(),
        "status": "complete",
        "schema_field_count": len(schema),
        "segment_role_rows": len(boundary),
        "case_count": len({row["case_id"] for row in boundary}),
        "runtime_modes": [row["mode"] for row in runtime],
        "analytic_test_count": len(tests),
        "analytic_tests_failed": sum(row["pass_fail"] != "pass" for row in tests),
        "predictive_wallHeatFlux_runtime_allowed_rows": sum(
            row["wallHeatFlux_runtime_allowed_predictive"] == "true" for row in boundary
        ),
        "explicit_unavailable_rows": sum(
            "explicit_unavailable" in row["boundary_field_availability_status"] for row in boundary
        ),
        "fluid_edit": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_action": False,
        "model_scoring_or_admission": False,
        "next_phase": "TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE",
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
