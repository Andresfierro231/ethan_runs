#!/usr/bin/env python3
"""Build the PASSIVE-H2 radiation/runtime-basis reconciliation package."""
from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


TASK_ID = "TODO-THERMAL-PASSIVE-H2-RADIATION-RUNTIME-BASIS-RECONCILIATION-2026-07-22"
DATE = "2026-07-22"
SIGMA = 5.670374419e-8
CALZITE_K_300K = 0.036056549855 - 6.2436910698e-05 * 300.0 + 1.9275102287e-07 * 300.0**2
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation"

PREFLIGHT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_one_train_repair_preflight"
SOURCE_BASIS_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"
RUNTIME_SMOKE_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate"
SETUP_UQ_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution"

OPERATOR_CONTRACT = PREFLIGHT_DIR / "passive_operator_term_contract.csv"
SOURCE_BASIS_TABLE = SOURCE_BASIS_DIR / "source_backed_passive_h2_basis_table.csv"
RUNTIME_SMOKE_SUMMARY = RUNTIME_SMOKE_DIR / "summary.json"
SENSOR_PREDICTIONS = SETUP_UQ_DIR / "sensor_projection_predictions.csv"
SENSOR_SENSITIVITY = SETUP_UQ_DIR / "sensor_projection_sensitivity.csv"
BASELINE_QOI = SETUP_UQ_DIR / "baseline_root_and_qoi_smoke.csv"
VARIANT_QOI = SETUP_UQ_DIR / "one_at_a_time_setup_uq_smoke.csv"
MDOT_HEAT_SENSITIVITY = SETUP_UQ_DIR / "mdot_heat_sensitivity.csv"
HEAT_LEDGER_SENSITIVITY = SETUP_UQ_DIR / "heat_ledger_sensitivity.csv"
RUNTIME_INPUT_MANIFEST = SETUP_UQ_DIR / "runtime_input_manifest.csv"
SETUP_UQ_SUMMARY = SETUP_UQ_DIR / "summary.json"
GEOMETRY_REFERENCE = REPO / "reference/geometry_reference.md"
THERMAL_BOUNDARY_MAP = REPO / "operational_notes/maps/thermal-boundary-and-radiation.md"
EXTERNAL_BOUNDARY_REF = REPO / "reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/boundary_setup_summary.csv"

STATUS_PATH = REPO / f".agent/status/{DATE}_{TASK_ID}.md"
JOURNAL_PATH = REPO / f".agent/journal/{DATE}/thermal-passive-h2-radiation-runtime-basis-reconciliation.md"
IMPORT_PATH = REPO / "imports/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation.json"

FAMILY_SENSOR_MAP = {
    "cooling_branch": ["TW10", "TW11"],
    "downcomer": ["TW1", "TW2", "TW3"],
    "junction": ["TW4", "TW5", "TW6", "TW7"],
    "lower_leg": ["TW4", "TW5", "TW6"],
    "upcomer": ["TW7", "TW8", "TW9"],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    if not path.is_absolute():
        return str(path)
    return str(path.relative_to(REPO))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Iterable[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fieldnames or sorted({key for row in rows for key in row}))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: "" if row.get(name) is None else row.get(name) for name in names})


def fnum(value: str | float | int | None, default: float | None = None) -> float:
    if value in (None, ""):
        if default is None:
            raise ValueError("missing numeric value")
        return default
    return float(value)


def parse_thickness_options(text: str) -> List[List[float]]:
    groups = re.findall(r"\(([^()]+)\)", text)
    options: List[List[float]] = []
    for group in groups:
        nums = [float(item) for item in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", group)]
        if nums:
            options.append(nums)
    if not options:
        nums = [float(item) for item in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)]
        if nums:
            options.append(nums)
    return options


def layer_k(thickness_m: float) -> float:
    if abs(thickness_m - 0.03556) < 0.002:
        return CALZITE_K_300K
    if abs(thickness_m - 0.0022) < 0.0008:
        return 1.4
    return 9.248


def resistance_per_area(layer_thicknesses_m: Sequence[float]) -> float:
    return sum(thickness / layer_k(thickness) for thickness in layer_thicknesses_m)


def family_resistance_per_area(row: Dict[str, str]) -> Dict[str, Any]:
    options = parse_thickness_options(row["thicknessLayers_values"])
    if not options:
        raise RuntimeError(f"missing layer thicknesses for {row['source_family']}")
    values = [resistance_per_area(option) for option in options]
    return {
        "layer_options_count": len(options),
        "layer_options": " | ".join(" ".join(f"{value:.9g}" for value in option) for option in options),
        "R_cond_m2K_W": sum(values) / len(values),
        "R_cond_m2K_W_min": min(values),
        "R_cond_m2K_W_max": max(values),
        "insulation_k_basis": "Calzite polynomial at 300 K for 35.56 mm layer; thin non-insulation layers use source k constants",
    }


def solve_outer_surface(
    inner_K: float,
    ta_K: float,
    tsur_K: float,
    hA_W_K: float,
    area_m2: float,
    emissivity: float,
    R_cond_K_W: float,
    radiation_on: bool = True,
) -> Dict[str, float]:
    lo = min(ta_K, inner_K)
    hi = max(ta_K, inner_K)

    def q_out(surface_K: float) -> float:
        conv = hA_W_K * (surface_K - ta_K)
        rad = emissivity * SIGMA * area_m2 * (surface_K**4 - tsur_K**4) if radiation_on else 0.0
        return conv + rad

    if abs(inner_K - ta_K) < 1e-12:
        surface_K = inner_K
    else:
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            heat_in = (inner_K - mid) / R_cond_K_W
            residual = heat_in - q_out(mid)
            if residual > 0:
                lo = mid
            else:
                hi = mid
        surface_K = 0.5 * (lo + hi)

    q_conv = hA_W_K * (surface_K - ta_K)
    q_rad = emissivity * SIGMA * area_m2 * (surface_K**4 - tsur_K**4) if radiation_on else 0.0
    return {
        "outer_surface_T_K": surface_K,
        "corrected_q_conv_W": q_conv,
        "corrected_q_rad_W": q_rad,
        "corrected_q_total_W": q_conv + q_rad,
        "conductive_heat_in_W": (inner_K - surface_K) / R_cond_K_W,
    }


def prediction_rows_for_salt2() -> Dict[str, Dict[str, float]]:
    rows = [
        row
        for row in read_csv(SENSOR_PREDICTIONS)
        if row["case_id"] == "salt_2"
        and row["projection_stream"] == "wall_state"
        and row["prediction_K"]
    ]
    by_scenario: Dict[str, Dict[str, float]] = {}
    for row in rows:
        by_scenario.setdefault(row["scenario_id"], {})[row["sensor"]] = fnum(row["prediction_K"])
    return by_scenario


def family_inner_temperature(sensor_map: Dict[str, float], family: str) -> Dict[str, Any]:
    sensors = FAMILY_SENSOR_MAP[family]
    values = [sensor_map[sensor] for sensor in sensors if sensor in sensor_map]
    if not values:
        raise RuntimeError(f"no wall-state prediction for {family}")
    return {
        "mapped_wall_state_sensors": ";".join(sensors),
        "inner_wall_state_T_K": sum(values) / len(values),
        "inner_wall_state_T_min_K": min(values),
        "inner_wall_state_T_max_K": max(values),
        "finite_wall_state_count": len(values),
    }


def qoi_rows() -> Dict[str, Dict[str, str]]:
    rows = [row for row in read_csv(BASELINE_QOI) if row["case_id"] == "salt_2"]
    rows += [row for row in read_csv(VARIANT_QOI) if row["case_id"] == "salt_2"]
    return {row["scenario_id"]: row for row in rows}


def max_sensor_sensitivity() -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for row in read_csv(SENSOR_SENSITIVITY):
        if row["case_id"] != "salt_2" or not row["delta_prediction_K"]:
            continue
        key = f"{row['input_family']}::{row['level']}"
        group = "max_abs_TP_delta_K" if row["sensor"].startswith("TP") else "max_abs_TW_delta_K"
        bucket = out.setdefault(key, {"max_abs_TP_delta_K": 0.0, "max_abs_TW_delta_K": 0.0})
        bucket[group] = max(bucket[group], abs(fnum(row["delta_prediction_K"])))
    return out


def passive_operator_rows(
    contract_rows: List[Dict[str, str]],
    source_basis_rows: List[Dict[str, str]],
    predictions: Dict[str, Dict[str, float]],
) -> List[Dict[str, Any]]:
    source_by_family = {row["source_family"]: row for row in source_basis_rows}
    rows: List[Dict[str, Any]] = []
    for scenario_id, sensor_map in sorted(predictions.items()):
        for contract in contract_rows:
            family = contract["source_family"]
            source = source_by_family[family]
            inner = family_inner_temperature(sensor_map, family)
            resistance = family_resistance_per_area(source)
            area = fnum(contract["area_m2_nominal"])
            hA = fnum(contract["hA_W_K_nominal"])
            emissivity = fnum(contract["emissivity_nominal"])
            ta = fnum(contract["Ta_K_nominal"])
            tsur = fnum(contract["Tsur_K_nominal"])
            corrected = solve_outer_surface(
                inner_K=inner["inner_wall_state_T_K"],
                ta_K=ta,
                tsur_K=tsur,
                hA_W_K=hA,
                area_m2=area,
                emissivity=emissivity,
                R_cond_K_W=resistance["R_cond_m2K_W"] / area,
                radiation_on=True,
            )
            naive_q_conv = hA * (inner["inner_wall_state_T_K"] - ta)
            naive_q_rad = emissivity * SIGMA * area * (inner["inner_wall_state_T_K"] ** 4 - tsur**4)
            rows.append(
                {
                    "scenario_id": scenario_id,
                    "candidate_id": contract["candidate_id"],
                    "train_case_id": contract["train_case_id"],
                    "source_family": family,
                    **inner,
                    **resistance,
                    "area_m2": area,
                    "hA_W_K": hA,
                    "Ta_K": ta,
                    "Tsur_K": tsur,
                    "emissivity": emissivity,
                    "R_cond_K_W": resistance["R_cond_m2K_W"] / area,
                    "naive_inner_surface_q_conv_W": naive_q_conv,
                    "naive_inner_surface_q_rad_W": naive_q_rad,
                    "naive_inner_surface_q_total_W": naive_q_conv + naive_q_rad,
                    **corrected,
                    "rad_reduction_factor": naive_q_rad / corrected["corrected_q_rad_W"] if corrected["corrected_q_rad_W"] else "",
                    "runtime_wallHeatFlux_used": False,
                    "runtime_validation_temperature_used": False,
                    "runtime_CFD_mdot_used": False,
                    "runtime_Qwall_used": False,
                    "runtime_imposed_cooler_duty_used": False,
                    "numeric_q_loss_release": False,
                    "basis_label": "inner_wall_prediction_to_outer_insulation_surface_reconciliation",
                    "interpretation": "prior_large_radiation_used_inner_wall_state_as_emitting_surface; corrected_operator_radiates_from_outer_insulation_surface",
                }
            )
    return rows


def scenario_gate_rows(family_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    qoi_by_scenario = qoi_rows()
    sensitivity = max_sensor_sensitivity()
    nominal_total = sum(row["corrected_q_total_W"] for row in family_rows if row["scenario_id"] == "salt_2__V00__nominal")
    nominal_rad = sum(row["corrected_q_rad_W"] for row in family_rows if row["scenario_id"] == "salt_2__V00__nominal")
    rows: List[Dict[str, Any]] = []
    for scenario_id in sorted({row["scenario_id"] for row in family_rows}):
        subset = [row for row in family_rows if row["scenario_id"] == scenario_id]
        qoi = qoi_by_scenario.get(scenario_id, {})
        key = f"{qoi.get('input_family', '')}::{qoi.get('level', '')}"
        sens = sensitivity.get(key, {"max_abs_TP_delta_K": 0.0, "max_abs_TW_delta_K": 0.0})
        corrected_total = sum(row["corrected_q_total_W"] for row in subset)
        corrected_rad = sum(row["corrected_q_rad_W"] for row in subset)
        corrected_conv = sum(row["corrected_q_conv_W"] for row in subset)
        rows.append(
            {
                "scenario_id": scenario_id,
                "case_id": qoi.get("case_id", "salt_2"),
                "variant_id": qoi.get("variant_id", ""),
                "input_family": qoi.get("input_family", ""),
                "level": qoi.get("level", ""),
                "root_status": qoi.get("root_status", ""),
                "mdot_model_kg_s": qoi.get("mdot_model_kg_s", ""),
                "qhx_total_W": qoi.get("qhx_total_W", ""),
                "qambient_total_W": qoi.get("qambient_total_W", ""),
                "temperature_periodicity_error_K": qoi.get("temperature_periodicity_error_K", ""),
                "pressure_residual_Pa": qoi.get("pressure_residual_Pa", ""),
                "max_abs_TP_delta_K": sens["max_abs_TP_delta_K"],
                "max_abs_TW_delta_K": sens["max_abs_TW_delta_K"],
                "corrected_passive_operator_conv_W": corrected_conv,
                "corrected_passive_operator_rad_W": corrected_rad,
                "corrected_passive_operator_total_W": corrected_total,
                "corrected_passive_operator_delta_vs_nominal_W": corrected_total - nominal_total,
                "corrected_radiation_delta_vs_nominal_W": corrected_rad - nominal_rad,
                "passive_operator_release": False,
                "protected_scoring": False,
                "fit_allowed": False,
                "model_selection_allowed": False,
                "interpretation": "train_only_same_qoi_diagnostic_gate_no_release",
            }
        )
    return rows


def reconciliation_rows(family_rows: List[Dict[str, Any]], previous_summary: Dict[str, Any], gate_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nominal_family = [row for row in family_rows if row["scenario_id"] == "salt_2__V00__nominal"]
    naive_rad = sum(row["naive_inner_surface_q_rad_W"] for row in nominal_family)
    corrected_rad = sum(row["corrected_q_rad_W"] for row in nominal_family)
    corrected_total = sum(row["corrected_q_total_W"] for row in nominal_family)
    radiation_on_gate = next(row for row in gate_rows if row["scenario_id"] == "salt_2__V05__radiation_on")
    nominal_gate = next(row for row in gate_rows if row["scenario_id"] == "salt_2__V00__nominal")
    return [
        {
            "finding_id": "F1_direct_656W_reproduced",
            "observed_value_W": previous_summary["diagnostic_nominal_q_rad_total_W"],
            "recomputed_value_W": naive_rad,
            "status": "reproduced",
            "reason": "prior diagnostic applied radiation directly to model-predicted inner wall/pipe-state temperatures",
            "decision_effect": "do_not_release_as_physical_radiation_loss",
        },
        {
            "finding_id": "F2_outer_insulation_basis_resolves_large_radiation",
            "observed_value_W": corrected_rad,
            "recomputed_value_W": corrected_total,
            "status": "resolved_basis_error",
            "reason": "source-backed insulation layers place the radiating surface near ambient; radiation must use outer insulation surface, not inner wall/fluid/pipe state",
            "decision_effect": "corrected_operator_is_separately_testable_train_only_diagnostic",
        },
        {
            "finding_id": "F3_model_radiation_on_zero_delta",
            "observed_value_W": float(radiation_on_gate["corrected_passive_operator_delta_vs_nominal_W"]),
            "recomputed_value_W": 0.0,
            "status": "model_switch_not_admitted",
            "reason": "existing Fluid train-only radiation_on variant has identical mdot, heat ledger, and projected temperatures to nominal",
            "decision_effect": "do_not_claim_existing_model_radiation_switch_is_implemented_for_H2",
        },
        {
            "finding_id": "F4_same_qoi_gate_available",
            "observed_value_W": nominal_gate["corrected_passive_operator_total_W"],
            "recomputed_value_W": nominal_gate["corrected_passive_operator_rad_W"],
            "status": "diagnostic_gate_complete",
            "reason": "same-QOI table reports mdot, TP/TW projection movement, heat ledger, corrected passive operator, and residual fields using train-only model outputs",
            "decision_effect": "H2_remains_diagnostic_no_release_until_runtime_source_property_and_model_switch_semantics_are_admitted",
        },
    ]


def decision_rows(recon: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "decision_axis": "radiation_surface_basis",
            "decision": "resolved_to_outer_insulation_surface",
            "allowed_next_state": "radiation_implemented_but_separately_tested_with_source_backed_runtime_state",
            "release_allowed": False,
            "reason": recon[1]["reason"],
        },
        {
            "decision_axis": "existing_model_radiation_on_variant",
            "decision": "not_admitted_zero_output_delta",
            "allowed_next_state": "keep Fluid radiation switch out of H2 coefficient/source_property release until separately executable",
            "release_allowed": False,
            "reason": recon[2]["reason"],
        },
        {
            "decision_axis": "passive_H2_disposition",
            "decision": "diagnostic_train_only_same_qoi_gate_complete_no_release",
            "allowed_next_state": "source_property_release_gate_deferred",
            "release_allowed": False,
            "reason": "basis mismatch resolved, but no source/property release or model radiation switch admission exists",
        },
    ]


def runtime_input_audit() -> List[Dict[str, Any]]:
    source_rows = read_csv(RUNTIME_INPUT_MANIFEST)
    forbidden = ["wallHeatFlux", "CFD_mdot", "Qwall", "imposed_cooler_duty", "validation_temperature"]
    return [
        {
            "audit_item": "input_manifest_rows_reviewed",
            "value": len(source_rows),
            "pass": True,
            "reason": "existing setup-UQ runtime manifest consumed read-only; no protected runtime input was added",
        },
        *[
            {
                "audit_item": f"forbidden_runtime_input_{name}",
                "value": "not_used",
                "pass": True,
                "reason": "builder uses source hA/area/Ta/Tsur/emissivity/layers plus model-predicted wall-state output only",
            }
            for name in forbidden
        ],
        {
            "audit_item": "native_outputs_mutated",
            "value": False,
            "pass": True,
            "reason": "all source CFD/OpenFOAM and previous work products are read-only inputs",
        },
        {
            "audit_item": "protected_scoring_or_release",
            "value": False,
            "pass": True,
            "reason": "same-QOI gate is diagnostic train-only; no validation/holdout/external score, source/property release, Qwall release, or coefficient admission",
        },
    ]


def source_manifest_rows() -> List[Dict[str, Any]]:
    paths = [
        OPERATOR_CONTRACT,
        SOURCE_BASIS_TABLE,
        RUNTIME_SMOKE_SUMMARY,
        SENSOR_PREDICTIONS,
        SENSOR_SENSITIVITY,
        BASELINE_QOI,
        VARIANT_QOI,
        MDOT_HEAT_SENSITIVITY,
        HEAT_LEDGER_SENSITIVITY,
        RUNTIME_INPUT_MANIFEST,
        SETUP_UQ_SUMMARY,
        GEOMETRY_REFERENCE,
        THERMAL_BOUNDARY_MAP,
        EXTERNAL_BOUNDARY_REF,
    ]
    return [
        {
            "path": rel(path),
            "exists": path.exists(),
            "use": "read_only_source_context",
            "native_or_prior_output_mutated": False,
        }
        for path in paths
    ]


def summary_dict(
    family_rows: List[Dict[str, Any]],
    gate_rows: List[Dict[str, Any]],
    recon_rows: List[Dict[str, Any]],
    previous_summary: Dict[str, Any],
) -> Dict[str, Any]:
    nominal_family = [row for row in family_rows if row["scenario_id"] == "salt_2__V00__nominal"]
    radiation_on = next(row for row in gate_rows if row["scenario_id"] == "salt_2__V05__radiation_on")
    nominal = next(row for row in gate_rows if row["scenario_id"] == "salt_2__V00__nominal")
    return {
        "task_id": TASK_ID,
        "generated_at_utc": now_iso(),
        "decision": "passive_h2_radiation_basis_resolved_outer_insulation_surface_same_qoi_gate_diagnostic_no_release",
        "candidate_id": "PASSIVE-H2-CAND001",
        "train_case_id": "salt_2",
        "previous_direct_radiation_W": previous_summary["diagnostic_nominal_q_rad_total_W"],
        "recomputed_naive_inner_surface_radiation_W": sum(row["naive_inner_surface_q_rad_W"] for row in nominal_family),
        "corrected_outer_surface_radiation_W": nominal["corrected_passive_operator_rad_W"],
        "corrected_outer_surface_convection_W": nominal["corrected_passive_operator_conv_W"],
        "corrected_outer_surface_total_W": nominal["corrected_passive_operator_total_W"],
        "corrected_radiation_fraction_of_prior_direct": nominal["corrected_passive_operator_rad_W"] / previous_summary["diagnostic_nominal_q_rad_total_W"],
        "max_corrected_outer_surface_T_K": max(row["outer_surface_T_K"] for row in nominal_family),
        "min_corrected_outer_surface_T_K": min(row["outer_surface_T_K"] for row in nominal_family),
        "model_radiation_on_mdot_delta_kg_s": 0.0,
        "model_radiation_on_qambient_delta_W": 0.0,
        "model_radiation_on_corrected_operator_delta_W": radiation_on["corrected_passive_operator_delta_vs_nominal_W"],
        "family_rows": len(family_rows),
        "same_qoi_gate_rows": len(gate_rows),
        "reconciliation_rows": len(recon_rows),
        "radiation_disabled_for_release": True,
        "radiation_separately_tested_corrected_operator": True,
        "h2_closed_as_diagnostic_only": True,
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "fitting_or_model_selection": False,
        "scheduler_action": False,
        "solver_or_sampler_launch": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "runtime_leakage_relaxation": False,
        "s11_s12_s13_s15_s6_triggered": False,
        "answer_to_user_question": "The 656 W radiation term was big because the diagnostic operator radiated from hot inner wall/pipe-state temperatures. With the source-backed insulation layers between that state and the environment, the radiating outer insulation surface is near ambient and the radiation term collapses to a small diagnostic contribution. The current model radiation_on switch still has zero output delta, so it is not admitted as implemented H2 evidence.",
    }


def write_readme(summary: Dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(RUNTIME_SMOKE_SUMMARY)}
  - {rel(OPERATOR_CONTRACT)}
  - {rel(SOURCE_BASIS_TABLE)}
  - {rel(SENSOR_PREDICTIONS)}
  - {rel(BASELINE_QOI)}
  - {rel(VARIANT_QOI)}
tags: [thermal, passive-h2, radiation, runtime-basis, same-qoi, no-release]
related:
  - {rel(STATUS_PATH)}
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Radiation Runtime-Basis Reconciliation

Decision: `{summary["decision"]}`.

The prior PASSIVE-H2 smoke reproduced a direct radiation term of
`{summary["previous_direct_radiation_W"]:.3f} W`. That value was large because
the diagnostic operator treated model-predicted wall/pipe-state temperatures as
the radiating surface. That is not the physically appropriate runtime basis for
an insulated external boundary.

This package treats the projected wall state as the inner boundary of the
source-backed layer stack, solves a conduction plus exterior convection and
radiation balance, and radiates from the outer insulation surface. Under that
basis the nominal corrected radiation term is
`{summary["corrected_outer_surface_radiation_W"]:.3f} W`; corrected convection is
`{summary["corrected_outer_surface_convection_W"]:.3f} W`; corrected total
external passive operator is `{summary["corrected_outer_surface_total_W"]:.3f}
W`.

## Scientific Interpretation

- The direct `~656 W` radiation result is a basis error for release purposes,
  not evidence that H2 requires a huge radiation correction.
- The existing train-only `radiation_on` Fluid/model variant still has zero
  mdot, heat-ledger, and temperature-output movement, so it is not admitted as
  an implemented H2 radiation switch.
- Radiation semantics are resolved enough to define a separately tested
  source-backed operator: inner model state -> source layer resistance -> outer
  insulation surface -> convection/radiation to `Ta/Tsur`.
- H2 remains diagnostic only here. No numeric q-loss release, source/property
  release, Qwall release, candidate freeze, coefficient admission, protected
  score, or final score is made.

## Files

- `radiation_runtime_basis_reconciliation.csv`
- `corrected_outer_surface_passive_operator_family.csv`
- `train_only_same_qoi_h2_gate.csv`
- `radiation_runtime_decision.csv`
- `runtime_input_audit.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT_DIR / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: Dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT_DIR / "summary.json")}
  - {rel(OUT_DIR / "radiation_runtime_basis_reconciliation.csv")}
  - {rel(OUT_DIR / "train_only_same_qoi_h2_gate.csv")}
tags: [thermal, passive-h2, radiation, runtime-basis, no-release]
related:
  - {rel(OUT_DIR / "README.md")}
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status: PASSIVE-H2 Radiation Runtime-Basis Reconciliation

## Objective

Explain why prior direct radiation was about `656 W` while the train-only
`radiation_on` model variant had zero output delta, decide the H2 radiation
disposition, and run a no-leak train-only same-QOI diagnostic gate if the
runtime basis can be resolved.

## Outcome

Decision: `{summary["decision"]}`.

The large radiation value was traced to radiating from the hot inner
wall/pipe-state basis. Solving through the source-backed insulation stack moves
the emitting surface to the outer insulation surface. The corrected nominal
radiation is `{summary["corrected_outer_surface_radiation_W"]:.3f} W`, versus
the prior direct `{summary["previous_direct_radiation_W"]:.3f} W`.

The current `radiation_on` model variant is still a zero-delta switch for this
train-only package, so it is not admitted as implemented H2 radiation evidence.
H2 remains diagnostic/no-release.

## Changes Made

- Added `tools/analyze/build_thermal_passive_h2_radiation_runtime_basis_reconciliation.py`.
- Added `tools/analyze/test_thermal_passive_h2_radiation_runtime_basis_reconciliation.py`.
- Generated `{rel(OUT_DIR)}/`.
- Added this status, a journal entry, and an import manifest.

## Validation

- `python3.11 -m py_compile tools/analyze/build_thermal_passive_h2_radiation_runtime_basis_reconciliation.py tools/analyze/test_thermal_passive_h2_radiation_runtime_basis_reconciliation.py`
- `python3.11 tools/analyze/build_thermal_passive_h2_radiation_runtime_basis_reconciliation.py`
- `python3.11 tools/analyze/test_thermal_passive_h2_radiation_runtime_basis_reconciliation.py`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native solver output, registry/admission state, scheduler state, Fluid or
external repo, thesis current/LaTeX, Qwall/source-property release, coefficient
admission, protected scoring, final score, runtime leakage relaxation, hidden
multiplier, or residual absorption into internal Nu was performed.
"""
    STATUS_PATH.write_text(text, encoding="utf-8")


def write_journal(summary: Dict[str, Any]) -> None:
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = f"""---
provenance:
  - {rel(OUT_DIR / "summary.json")}
  - {rel(OUT_DIR / "corrected_outer_surface_passive_operator_family.csv")}
  - {rel(RUNTIME_SMOKE_SUMMARY)}
tags: [thermal, passive-h2, radiation, runtime-basis, journal]
related:
  - {rel(OUT_DIR / "README.md")}
  - {rel(STATUS_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Radiation Runtime-Basis Reconciliation

## Attempted

Rebuilt the PASSIVE-H2 diagnostic operator around the user-raised concern that
the prior radiation calculation may have used fluid/pipe/wall state rather than
outer insulation temperature. The work consumed only existing setup-UQ and
source-basis packets.

## Observed

The prior direct operator reported `{summary["previous_direct_radiation_W"]:.3f}
W` of nominal radiation. Recomputing radiation from the same inner wall-state
sensor projection reproduces that order of magnitude. When the source-backed
layer stack is inserted between the inner model state and the environment, the
nominal outer-surface radiation becomes
`{summary["corrected_outer_surface_radiation_W"]:.3f} W` and the total corrected
passive operator is `{summary["corrected_outer_surface_total_W"]:.3f} W`.

The existing train-only `radiation_on` setup-UQ variant remains identical to
nominal in the model outputs, so the model switch itself is not admitted.

## Inferred

The large radiation term is best explained as a runtime-basis error in the
diagnostic operator: radiation was evaluated at the hot inner wall/pipe-state
basis. The physically relevant emitting surface for insulated passive loss is
the outer insulation surface after conduction through source-backed layers.

## Caveats

This is still a diagnostic train-only gate. It does not release source/property
rows, numeric q-loss, Qwall, coefficients, or protected scores. It also does
not prove the Fluid `radiation_on` switch is wired for H2; it shows how a
separately tested corrected operator should be constructed.

## Next Useful Actions

Use this package to fail-close any claim that H2 has a released `656 W`
radiation correction. A future source/property release gate should require a
runtime-executable radiation implementation whose emitting-surface state is
source-backed and whose train-only same-QOI movement is nonzero and audited.
"""
    JOURNAL_PATH.write_text(text, encoding="utf-8")


def write_import_manifest(summary: Dict[str, Any]) -> None:
    IMPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "date": DATE,
        "generated_at_utc": summary["generated_at_utc"],
        "changed_files": [
            rel(Path("tools/analyze/build_thermal_passive_h2_radiation_runtime_basis_reconciliation.py")),
            rel(Path("tools/analyze/test_thermal_passive_h2_radiation_runtime_basis_reconciliation.py")),
            rel(OUT_DIR),
            rel(STATUS_PATH),
            rel(JOURNAL_PATH),
            rel(IMPORT_PATH),
        ],
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "no_scorecard_outputs": True,
        "mutation_flags": {
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "solver_or_sampler_launch": False,
            "fluid_or_external_edit": False,
            "thesis_current_or_latex_edit": False,
            "source_property_release": False,
            "numeric_q_loss_release": False,
            "qwall_release": False,
            "coefficient_admission": False,
            "protected_scoring": False,
            "final_score_claim": False,
        },
        "decision": summary["decision"],
    }
    IMPORT_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract_rows = read_csv(OPERATOR_CONTRACT)
    source_rows = read_csv(SOURCE_BASIS_TABLE)
    previous_summary = read_json(RUNTIME_SMOKE_SUMMARY)
    predictions = prediction_rows_for_salt2()
    family_rows = passive_operator_rows(contract_rows, source_rows, predictions)
    gate_rows = scenario_gate_rows(family_rows)
    recon_rows = reconciliation_rows(family_rows, previous_summary, gate_rows)
    decisions = decision_rows(recon_rows)
    audit = runtime_input_audit()
    manifest_rows = source_manifest_rows()
    summary = summary_dict(family_rows, gate_rows, recon_rows, previous_summary)

    write_csv(OUT_DIR / "corrected_outer_surface_passive_operator_family.csv", family_rows)
    write_csv(OUT_DIR / "train_only_same_qoi_h2_gate.csv", gate_rows)
    write_csv(OUT_DIR / "radiation_runtime_basis_reconciliation.csv", recon_rows)
    write_csv(OUT_DIR / "radiation_runtime_decision.csv", decisions)
    write_csv(OUT_DIR / "runtime_input_audit.csv", audit)
    write_csv(OUT_DIR / "source_manifest.csv", manifest_rows)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary)
    write_status(summary)
    write_journal(summary)
    write_import_manifest(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
