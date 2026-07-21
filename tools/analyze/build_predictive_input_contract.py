#!/usr/bin/env python3
"""Build a strict input contract for predictive forward 1D work.

This package is a guardrail, not a fit. It classifies every field needed by the
next forward-model slice and makes the key rule machine-checkable: predictive
runtime modes must not consume CFD mdot, realized CFD wallHeatFlux, or measured
temperatures as solver inputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (REPO_ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
if str(FLUID_ROOT) not in sys.path:
    sys.path.insert(0, str(FLUID_ROOT))

from tamu_loop_model_v2 import config_loader  # noqa: E402

OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract"
PATCH_TABLE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)
THERMAL_TARGETS = (
    REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv"
)
FLUID_CASES = REPO_ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml"
FLUID_VALIDATION = REPO_ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/validation_cases.csv"
AGENT_286_PLAN = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/research_plan.md"
)
LITREV_CAMPAIGN_INDEX = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_todo_campaign_index/README.md"
)
LITREV_SOURCE_ENVELOPE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/source_overlap_flags.csv"
)
LITREV_PROPERTY_MODE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/property_sensitivity_summary.csv"
)
LITREV_NAMED_LOSSES = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv"
)
LITREV_HEAT_LOSS = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/heat_closure_admission.csv"
)
LITREV_CFD_NAMING = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/coefficient_naming_limits.csv"
)

REQUIRED_LITREV_GATES = {
    "source_envelope_gate": LITREV_SOURCE_ENVELOPE,
    "property_mode_lane": LITREV_PROPERTY_MODE,
    "named_loss_table": LITREV_NAMED_LOSSES,
    "heat_loss_admission_table": LITREV_HEAT_LOSS,
    "cfd_coefficient_naming_limits": LITREV_CFD_NAMING,
}

RUNTIME_COLUMNS = [
    "field_name",
    "source_system",
    "source_path",
    "field_class",
    "forward_v0_imposed_cooler_allowed",
    "predictive_hx_allowed",
    "runtime_use",
    "blocked_runtime_reason",
    "litrev_gate",
    "litrev_gate_source_path",
    "litrev_gate_required_before_scoring",
    "notes",
]

MODE_COLUMNS = [
    "mode_id",
    "description",
    "allowed_runtime_classes",
    "explicitly_forbidden_runtime_fields",
    "validation_join_policy",
    "status",
]

CASE_INPUT_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "heater_power_W",
    "test_section_power_W",
    "air_T_inlet_K",
    "air_flow_Lpm",
    "imposed_cooler_duty_W",
    "boundary_ambient_Ta_K",
    "radiation_on",
    "insulation_thickness_in",
    "source_contract_variants",
    "mdot_search_lower_kg_s",
    "mdot_search_upper_kg_s",
    "runtime_input_status",
]

VALIDATION_COLUMNS = [
    "case_id",
    "target_name",
    "target_source",
    "target_field",
    "field_class",
    "runtime_allowed",
    "notes",
]

VIOLATION_COLUMNS = [
    "field_name",
    "mode_id",
    "violation",
    "severity",
]

CASE_NAME_TO_ID = {
    "Salt 2": "salt_2",
    "Salt 3": "salt_3",
    "Salt 4": "salt_4",
}
CASE_ID_TO_NAME = {value: key for key, value in CASE_NAME_TO_ID.items()}


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


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def runtime_row(
    field_name: str,
    source_system: str,
    source_path: Path,
    field_class: str,
    forward_allowed: bool,
    hx_allowed: bool,
    runtime_use: str,
    blocked_reason: str,
    notes: str,
    *,
    litrev_gate: str = "",
    litrev_gate_source_path: Path | None = None,
    litrev_gate_required_before_scoring: bool = False,
) -> dict[str, Any]:
    return {
        "field_name": field_name,
        "source_system": source_system,
        "source_path": rel(source_path),
        "field_class": field_class,
        "forward_v0_imposed_cooler_allowed": bool_text(forward_allowed),
        "predictive_hx_allowed": bool_text(hx_allowed),
        "runtime_use": runtime_use,
        "blocked_runtime_reason": blocked_reason,
        "litrev_gate": litrev_gate,
        "litrev_gate_source_path": rel(litrev_gate_source_path) if litrev_gate_source_path else "",
        "litrev_gate_required_before_scoring": bool_text(litrev_gate_required_before_scoring),
        "notes": notes,
    }


def build_runtime_contract_rows() -> list[dict[str, Any]]:
    return [
        runtime_row("fluid_case_name", "Fluid cases config", FLUID_CASES, "setup_input", True, True, "case selection", "", "Selects the physical operating case."),
        runtime_row("fluid_name", "Fluid cases config", FLUID_CASES, "setup_input", True, True, "material selection", "", "Selects salt material/property family."),
        runtime_row("property_set_name", "Fluid cases config", FLUID_CASES, "setup_input", True, True, "material selection", "", "Optional declared property set."),
        runtime_row("geometry", "Fluid tracked geometry", FLUID_CASES, "setup_input", True, True, "loop geometry", "", "Current repo-local runner imports Fluid geometry read-only."),
        runtime_row("heater_power_W", "Fluid cases config", FLUID_CASES, "setup_input", True, True, "heater source input", "", "Electrical/setup heater power; not realized CFD wall flux."),
        runtime_row("test_section_power_W", "Fluid cases config", FLUID_CASES, "setup_input", True, True, "source-contract variant", "", "Forward-v0 reports both current Fluid source contract and heater-only sensitivity."),
        runtime_row("air_T_inlet_K", "Fluid cases config", FLUID_CASES, "setup_input", True, True, "HX setup metadata", "", "Used by predictive HX later; carried but not first-order in imposed-cooler mode."),
        runtime_row("air_flow_Lpm", "Fluid cases config", FLUID_CASES, "setup_input", True, True, "HX setup metadata", "", "Used by predictive HX later; carried but not first-order in imposed-cooler mode."),
        runtime_row("boundary_ambient_Ta_K", "CFD boundary dictionary setup", PATCH_TABLE, "setup_input", True, True, "ambient setup", "", "Area/hA-weighted declared CFD boundary Ta; not a validation temperature."),
        runtime_row("insulation_thickness_in", "Fluid scenario setup", FLUID_CASES, "setup_input", True, True, "wall/insulation setup", "", "Initial v0 uses 1.0 in to match current Fluid salt comparisons."),
        runtime_row("radiation_on", "scenario control", FLUID_CASES, "setup_input", True, True, "physics toggle", "", "Forward-v0 CFD comparison uses radiation_off; later experiment prediction may re-enable radiation explicitly."),
        runtime_row("mdot_search_lower_kg_s", "scenario numerical control", AGENT_286_PLAN, "setup_input", True, True, "root-search bound", "", "Broad salt natural-circulation numerical lower bound; not a measured or CFD mdot anchor."),
        runtime_row("mdot_search_upper_kg_s", "scenario numerical control", AGENT_286_PLAN, "setup_input", True, True, "root-search bound", "", "Broad salt natural-circulation numerical upper bound; not a measured or CFD mdot anchor."),
        runtime_row("imposed_cooler_duty_W", "CFD/OpenFOAM boundary setup", THERMAL_TARGETS, "setup_input", True, False, "cooler sink input", "", "Allowed only for forward_v0_imposed_cooler; predictive HX must replace this with UA/epsilon-NTU."),
        runtime_row("internal_Nu_multiplier", "future fit package", AGENT_286_PLAN, "calibrated_parameter", True, True, "optional calibrated correction", "", "Must come from declared train rows before held-out use."),
        runtime_row("external_h_or_radiation_terms", "future fit package", AGENT_286_PLAN, "calibrated_parameter", False, True, "future calibrated correction", "", "Blocked in v0; later low-dimensional fit only."),
        runtime_row("HX_UA_or_epsilon_NTU", "future fit package", AGENT_286_PLAN, "calibrated_parameter", False, True, "future predictive HX", "", "Replacement for imposed cooler duty."),
        runtime_row("cfd_mdot_kg_s", "CFD thermal target table", THERMAL_TARGETS, "validation_target", False, False, "validation only", "predictive modes must solve mdot from pressure balance", "Can be joined after solve for scoring."),
        runtime_row("cfd_Tmean_K", "CFD thermal target table", THERMAL_TARGETS, "validation_target", False, False, "validation only", "measured/CFD temperatures cannot set runtime thermal state", "Can be joined after solve for scoring."),
        runtime_row("cfd_loop_delta_T_K", "CFD thermal target table", THERMAL_TARGETS, "validation_target", False, False, "validation only", "measured/CFD temperatures cannot set runtime thermal state", "Can be joined after solve for scoring."),
        runtime_row("TP_TW_measured_K", "Fluid validation table", FLUID_VALIDATION, "validation_target", False, False, "validation only", "sensor measurements are joined after predictive solve", "Experimental sensor score stream."),
        runtime_row("CFD_sensor_reference_K", "CFD sensor reference packages", REPO_ROOT / "reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/cfd_sensor_reference.csv", "validation_target", False, False, "validation only", "CFD sensors are joined after predictive solve", "CFD sensor score stream when available."),
        runtime_row("heater_wallHeatFlux_W", "CFD wallHeatFlux diagnostic", THERMAL_TARGETS, "diagnostic_cfd_evidence", False, False, "diagnostic only", "realized CFD wall flux would leak target information", "Used to diagnose heater transfer efficiency later."),
        runtime_row("cooler_wallHeatFlux_W", "CFD wallHeatFlux diagnostic", THERMAL_TARGETS, "diagnostic_cfd_evidence", False, False, "diagnostic only", "realized CFD wall flux would leak target information", "Use imposed cooler setup duty in v0, not realized wallHeatFlux."),
        runtime_row("test_section_wallHeatFlux_W", "CFD wallHeatFlux diagnostic", THERMAL_TARGETS, "diagnostic_cfd_evidence", False, False, "diagnostic only", "realized CFD wall flux would leak target information", "Feeds future heater/test-section contract, not v0 runtime."),
        runtime_row("time_window_uncertainty", "uncertainty packages", AGENT_286_PLAN, "uncertainty_metadata", False, False, "score annotation", "uncertainty is not a boundary condition", "Added to later scorecards before thesis-strength claims."),
        runtime_row("mesh_uncertainty", "mesh/GCI packages", AGENT_286_PLAN, "uncertainty_metadata", False, False, "score annotation", "uncertainty is not a boundary condition", "Thermal mesh closure remains blocked."),
        runtime_row(
            "source_envelope_gate",
            "lit-rev source envelope gate",
            LITREV_CAMPAIGN_INDEX,
            "blocked_closure_gate",
            False,
            False,
            "pre-score admission gate",
            "predictive scoring must state whether candidate closure sources overlap TAMU branch Re/Pr/Gr/Ri/Ra/Gz/Bo/L/D/reset/orientation/heating-cooling envelope",
            "Gate output classifies source overlap and admissibility by branch before Chen, Tian, Everts/Meyer, Muzychka-Yovanovich, or related forms can be used.",
            litrev_gate="source_envelope_gate",
            litrev_gate_source_path=LITREV_SOURCE_ENVELOPE,
            litrev_gate_required_before_scoring=True,
        ),
        runtime_row(
            "property_mode_lane",
            "lit-rev property sensitivity gate",
            LITREV_CAMPAIGN_INDEX,
            "setup_input",
            True,
            True,
            "pre-score property lane selection",
            "",
            "Select and declare the property mode before interpreting mdot, Re, Pr, buoyancy head, pressure residual, or heat residual.",
            litrev_gate="property_mode_lane",
            litrev_gate_source_path=LITREV_PROPERTY_MODE,
            litrev_gate_required_before_scoring=True,
        ),
        runtime_row(
            "named_loss_table",
            "lit-rev reset and named-loss gate",
            LITREV_CAMPAIGN_INDEX,
            "blocked_closure_gate",
            False,
            False,
            "pre-score pressure-loss attribution gate",
            "do not hide straight-section, component-K, cluster-K, or branch-apparent losses inside a global friction multiplier",
            "Named-loss table separates pressure terms before hydraulic residuals are fitted or scored.",
            litrev_gate="named_loss_table",
            litrev_gate_source_path=LITREV_NAMED_LOSSES,
            litrev_gate_required_before_scoring=True,
        ),
        runtime_row(
            "heat_loss_admission_table",
            "lit-rev heat-loss admission gate",
            LITREV_CAMPAIGN_INDEX,
            "blocked_closure_gate",
            False,
            False,
            "pre-score heat-loss attribution gate",
            "internal Nu must not absorb jacket/cooler removal, passive convection, radiation metadata, heater efficiency, wall/storage, or residual heat paths",
            "Admission table decides which heat paths are setup inputs, fitted terms, diagnostics, or blocked closures.",
            litrev_gate="heat_loss_admission_table",
            litrev_gate_source_path=LITREV_HEAT_LOSS,
            litrev_gate_required_before_scoring=True,
        ),
        runtime_row(
            "cfd_coefficient_naming_limits",
            "lit-rev CFD validity gate",
            LITREV_CAMPAIGN_INDEX,
            "diagnostic_cfd_evidence",
            False,
            False,
            "pre-score CFD evidence naming gate",
            "section-effective CFD f, K, or Nu must not be promoted as universal transferable coefficients without validity diagnostics",
            "Coefficient naming limits classify reverse-flow/secondary-flow/recirculation/skewed-wall-flux rows as diagnostic or section-effective.",
            litrev_gate="cfd_coefficient_naming_limits",
            litrev_gate_source_path=LITREV_CFD_NAMING,
            litrev_gate_required_before_scoring=True,
        ),
    ]


def build_mode_contract_rows() -> list[dict[str, Any]]:
    forbidden = "cfd_mdot_kg_s;heater_wallHeatFlux_W;cooler_wallHeatFlux_W;test_section_wallHeatFlux_W;cfd_Tmean_K;cfd_loop_delta_T_K;TP_TW_measured_K;CFD_sensor_reference_K"
    return [
        {
            "mode_id": "fixed_mdot_diagnostic",
            "description": "Diagnostic replay that may intentionally use CFD mdot or realized CFD wall flux.",
            "allowed_runtime_classes": "setup_input;diagnostic_cfd_evidence;validation_target",
            "explicitly_forbidden_runtime_fields": "",
            "validation_join_policy": "not predictive; label separately",
            "status": "diagnostic_only",
        },
        {
            "mode_id": "forward_v0_imposed_cooler",
            "description": "Pressure-rooted forward solve with heater setup input and imposed cooler duty.",
            "allowed_runtime_classes": "setup_input;declared_pretrained_calibrated_parameter",
            "explicitly_forbidden_runtime_fields": forbidden,
            "validation_join_policy": "join experimental and CFD targets only after solve",
            "status": "active_next_slice",
        },
        {
            "mode_id": "predictive_hx",
            "description": "End-to-end predictive mode replacing imposed cooler duty with HX UA/epsilon-NTU.",
            "allowed_runtime_classes": "setup_input;declared_pretrained_calibrated_parameter",
            "explicitly_forbidden_runtime_fields": forbidden + ";imposed_cooler_duty_W",
            "validation_join_policy": "join experimental and CFD targets only after solve",
            "status": "blocked_pending_HX_fit",
        },
    ]


def boundary_ambient_by_case(patch_rows: list[dict[str, str]]) -> dict[str, float]:
    accum: dict[str, tuple[float, float]] = {}
    for row in patch_rows:
        case_id = row.get("case_id", "")
        if case_id not in CASE_ID_TO_NAME or row.get("role") == "cooler":
            continue
        h = fnum(row.get("h_W_m2K"))
        area = fnum(row.get("area_m2"))
        ta = fnum(row.get("Ta_K"))
        if h is None or area is None or ta is None:
            continue
        weight = h * area
        old_weight, old_sum = accum.get(case_id, (0.0, 0.0))
        accum[case_id] = (old_weight + weight, old_sum + weight * ta)
    return {
        case_id: weighted_sum / weight
        for case_id, (weight, weighted_sum) in accum.items()
        if weight > 0.0
    }


def build_case_runtime_inputs(
    target_rows: list[dict[str, str]],
    validation_rows: list[dict[str, str]],
    patch_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    fluid_cases = {case.name: case for case in config_loader.load_cases()}
    ta_by_case = boundary_ambient_by_case(patch_rows)
    rows: list[dict[str, Any]] = []
    for target in target_rows:
        case_id = target["case_id"]
        if case_id not in CASE_ID_TO_NAME:
            continue
        case_name = CASE_ID_TO_NAME[case_id]
        fluid_case = fluid_cases[case_name]
        cooler = abs(fnum(target.get("cooler_removed_duty_W"), 0.0) or 0.0)
        rows.append(
            {
                "case_id": case_id,
                "fluid_case_name": case_name,
                "source_id": target["source_id"],
                "heater_power_W": fluid_case.heater_power_W,
                "test_section_power_W": fluid_case.test_section_power_W,
                "air_T_inlet_K": fluid_case.air_T_inlet_K,
                "air_flow_Lpm": fluid_case.air_flow_Lpm,
                "imposed_cooler_duty_W": cooler,
                "boundary_ambient_Ta_K": ta_by_case.get(case_id, 300.0),
                "radiation_on": "false",
                "insulation_thickness_in": 1.0,
                "source_contract_variants": "F0_current_fluid_sources;F1_heater_only",
                "mdot_search_lower_kg_s": 0.005,
                "mdot_search_upper_kg_s": 0.05,
                "runtime_input_status": "allowed_forward_v0_imposed_cooler",
            }
        )
    return rows


def build_validation_target_rows(target_rows: list[dict[str, str]], validation_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in target_rows:
        case_id = target["case_id"]
        for field in ("cfd_mdot_kg_s", "cfd_Tmean_K", "cfd_loop_delta_T_K", "cfd_Tmin_K", "cfd_Tmax_K"):
            rows.append(
                {
                    "case_id": case_id,
                    "target_name": field,
                    "target_source": rel(THERMAL_TARGETS),
                    "target_field": field,
                    "field_class": "validation_target",
                    "runtime_allowed": "false",
                    "notes": "CFD target joined after solve only.",
                }
            )
        for field in ("heater_wallHeatFlux_W", "cooler_wallHeatFlux_W", "test_section_wallHeatFlux_W"):
            rows.append(
                {
                    "case_id": case_id,
                    "target_name": field,
                    "target_source": rel(THERMAL_TARGETS),
                    "target_field": field,
                    "field_class": "diagnostic_cfd_evidence",
                    "runtime_allowed": "false",
                    "notes": "Realized CFD wall heat is diagnostic evidence, not a forward runtime input.",
                }
            )
    for row in validation_rows:
        if row.get("case_name") not in CASE_NAME_TO_ID:
            continue
        case_id = CASE_NAME_TO_ID[row["case_name"]]
        for field in row:
            if field.startswith(("TP", "TW")) and field.endswith("_C"):
                rows.append(
                    {
                        "case_id": case_id,
                        "target_name": field.removesuffix("_C"),
                        "target_source": rel(FLUID_VALIDATION),
                        "target_field": field,
                        "field_class": "validation_target",
                        "runtime_allowed": "false",
                        "notes": "Experimental sensor measurement joined after solve only.",
                    }
                )
    return rows


def validate_contract(runtime_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    forbidden_forward_fields = {
        "cfd_mdot_kg_s",
        "cfd_Tmean_K",
        "cfd_loop_delta_T_K",
        "TP_TW_measured_K",
        "CFD_sensor_reference_K",
        "heater_wallHeatFlux_W",
        "cooler_wallHeatFlux_W",
        "test_section_wallHeatFlux_W",
    }
    for row in runtime_rows:
        field = str(row["field_name"])
        if field in forbidden_forward_fields and row["forward_v0_imposed_cooler_allowed"] == "true":
            violations.append(
                {
                    "field_name": field,
                    "mode_id": "forward_v0_imposed_cooler",
                    "violation": "forbidden_target_or_diagnostic_allowed_at_runtime",
                    "severity": "error",
                }
            )
        if field == "imposed_cooler_duty_W" and row["predictive_hx_allowed"] == "true":
            violations.append(
                {
                    "field_name": field,
                    "mode_id": "predictive_hx",
                    "violation": "imposed_cooler_duty_would_bypass_predictive_hx",
                    "severity": "error",
                }
            )
    by_field = {str(row["field_name"]): row for row in runtime_rows}
    for gate_name, gate_path in REQUIRED_LITREV_GATES.items():
        row = by_field.get(gate_name)
        if row is None:
            violations.append(
                {
                    "field_name": gate_name,
                    "mode_id": "forward_v0_imposed_cooler",
                    "violation": "required_litrev_gate_missing_from_runtime_contract",
                    "severity": "error",
                }
            )
            continue
        if row.get("litrev_gate_required_before_scoring") != "true":
            violations.append(
                {
                    "field_name": gate_name,
                    "mode_id": "forward_v0_imposed_cooler",
                    "violation": "required_litrev_gate_not_marked_before_scoring",
                    "severity": "error",
                }
            )
        if row.get("litrev_gate_source_path") != rel(gate_path):
            violations.append(
                {
                    "field_name": gate_name,
                    "mode_id": "forward_v0_imposed_cooler",
                    "violation": "required_litrev_gate_source_path_mismatch",
                    "severity": "error",
                }
            )
        if not gate_path.exists():
            violations.append(
                {
                    "field_name": gate_name,
                    "mode_id": "forward_v0_imposed_cooler",
                    "violation": "required_litrev_gate_source_path_missing",
                    "severity": "error",
                }
            )
    return violations


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""# Predictive Input Contract

Generated: `{summary['generated_utc']}`

This package defines the runtime-input guardrail for the next pressure-rooted
forward 1D model slice.

## What Is Allowed

- `forward_v0_imposed_cooler` may use physical setup inputs, declared Fluid
  geometry/properties, heater setup power, no-radiation scenario control,
  insulation setup, ambient/Ta setup, and imposed cooler duty.
- `predictive_hx` must not use imposed cooler duty; it remains blocked until a
  low-dimensional UA or epsilon-NTU model is fit and validated.

## What Is Forbidden At Runtime

The forward solver must not consume CFD mdot, CFD mean/delta temperatures,
realized CFD wallHeatFlux, experimental TP/TW measurements, or CFD sensor
references. Those fields are validation or diagnostic evidence and are joined
only after the solve.

## Files

- `runtime_input_contract.csv`: field-level classes and runtime permissions.
- `mode_contract.csv`: mode-level allowed/forbidden input policy.
- `case_runtime_inputs_forward_v0.csv`: Salt 2-4 runtime input rows for the
  imposed-cooler forward-v0 runner.
- `validation_target_contract.csv`: validation and diagnostic fields to join
  after solving.
- `violations.csv`: strict-contract violations; expected to be empty.
- `summary.json`: machine-readable package metadata.

## Current Boundaries

This is predictive only conditional on imposed cooler duty. It does not solve
the HX boundary yet, does not fit heater transfer efficiency, and does not admit
thermal mesh-sensitive h/Nu/UA corrections.

Before any forward-v0 score is treated as meaningful, the runtime contract must
carry five lit-rev gate references: source envelope, property mode lane,
named-loss table, heat-loss admission table, and CFD coefficient naming limits.
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    target_rows = read_csv(THERMAL_TARGETS)
    patch_rows = read_csv(PATCH_TABLE)
    validation_rows = read_csv(FLUID_VALIDATION)
    runtime_rows = build_runtime_contract_rows()
    mode_rows = build_mode_contract_rows()
    case_rows = build_case_runtime_inputs(target_rows, validation_rows, patch_rows)
    validation_contract_rows = build_validation_target_rows(target_rows, validation_rows)
    violations = validate_contract(runtime_rows)

    write_csv(out_dir / "runtime_input_contract.csv", runtime_rows, RUNTIME_COLUMNS)
    write_csv(out_dir / "mode_contract.csv", mode_rows, MODE_COLUMNS)
    write_csv(out_dir / "case_runtime_inputs_forward_v0.csv", case_rows, CASE_INPUT_COLUMNS)
    write_csv(out_dir / "validation_target_contract.csv", validation_contract_rows, VALIDATION_COLUMNS)
    write_csv(out_dir / "violations.csv", violations, VIOLATION_COLUMNS)

    summary = {
        "task_id": "TODO-PRED-INPUT-CONTRACT",
        "generated_utc": utc_now(),
        "source_files": {
            "patch_table": rel(PATCH_TABLE),
            "thermal_targets": rel(THERMAL_TARGETS),
            "fluid_cases": rel(FLUID_CASES),
            "fluid_validation": rel(FLUID_VALIDATION),
            "research_plan": rel(AGENT_286_PLAN),
            "litrev_campaign_index": rel(LITREV_CAMPAIGN_INDEX),
            "source_envelope_gate": rel(LITREV_SOURCE_ENVELOPE),
            "property_mode_lane": rel(LITREV_PROPERTY_MODE),
            "named_loss_table": rel(LITREV_NAMED_LOSSES),
            "heat_loss_admission_table": rel(LITREV_HEAT_LOSS),
            "cfd_coefficient_naming_limits": rel(LITREV_CFD_NAMING),
        },
        "n_runtime_fields": len(runtime_rows),
        "n_modes": len(mode_rows),
        "n_case_runtime_rows": len(case_rows),
        "n_validation_targets": len(validation_contract_rows),
        "n_violations": len(violations),
        "strict_status": "pass" if not violations else "fail",
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--strict", action="store_true", help="Fail if strict-contract violations are emitted.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    summary = build_package(args.output_dir)
    if args.strict and summary["n_violations"]:
        raise SystemExit(f"strict input contract failed with {summary['n_violations']} violation(s)")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
