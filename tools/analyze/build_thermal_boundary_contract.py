#!/usr/bin/env python3
"""Build the CFD thermal boundary contract and frozen-replay gate plan.

This builder is intentionally read-only with respect to solver outputs.  It
collects the July 8 patchwise heat ledger, span endpoint temperatures, and the
July 2 1D/CFD thermal comparison into one auditable package for the next 1D
thermal-state reconstruction pass.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO_ROOT / "work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv"
DEFAULT_SPANS = REPO_ROOT / "work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv"
DEFAULT_DRIVER_COMPARE = REPO_ROOT / "work_products/2026-07-02_overnight/driver_thermal_compare.json"
DEFAULT_OUTPUT = REPO_ROOT / "work_products/2026-07-08_thermal_boundary_contract"

SOURCE_TO_CASE = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "salt_2",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "salt_3",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "salt_4",
}

PATCH_ROLE_TO_REPLAY = {
    "heater": "prescribed_source_profile_candidate_with_imposed_vs_wallflux_discrepancy",
    "cooler": "prescribed_cooler_sink_candidate",
    "ambient_wall": "prescribed_passive_ambient_exchange_candidate",
    "test_section": "explicit_quartz_test_section_exchange_candidate",
    "junction_other": "grouped_diagnostic_loss_not_segment_bracketed",
}

CONTRACT_COLUMNS = [
    "source_id",
    "case_id",
    "run_class",
    "mesh_level",
    "source_case_root",
    "source_window_start_s",
    "source_window_end_s",
    "wallheatflux_source_path",
    "patch_group",
    "physical_role",
    "span",
    "patch_names",
    "bc_type",
    "wall_flux_sign_convention",
    "wallHeatFlux_integral_W",
    "heat_to_fluid_W",
    "heater_imposed_duty_W",
    "cooler_removed_duty_W",
    "passive_wall_heat_leak_gain_W",
    "junction_loss_W",
    "imposed_Q_sum_W",
    "imposed_Q_minus_wallHeatFlux_W",
    "T_bulk_inlet_K",
    "T_bulk_outlet_K",
    "T_bulk_span_K",
    "mdot_kg_s",
    "cp_jkgk",
    "enthalpy_change_W",
    "enthalpy_change_status",
    "segment_wallHeatFlux_sum_W",
    "wallHeatFlux_vs_enthalpy_residual_W",
    "residual_fraction",
    "residual_assignment",
    "patch_area_m2",
    "wall_T_mean_K",
    "boundary_ambient_T_K",
    "boundary_h_W_m2K",
    "wall_conduction_resistance_m2K_W",
    "external_convection_resistance_m2K_W",
    "external_radiation_resistance_m2K_W",
    "total_boundary_resistance_m2K_W",
    "network_terms_resolved",
    "radiation_present",
    "radiation_caveat",
    "fit_eligible",
    "validation_eligible",
    "quality_flags",
    "notes",
    "replay_contract_role",
    "thermal_contract_label",
]

TARGET_COLUMNS = [
    "case_id",
    "source_id",
    "cfd_mdot_kg_s",
    "cfd_Re_main",
    "cfd_Tmean_K",
    "cfd_Tmin_K",
    "cfd_Tmax_K",
    "cfd_loop_delta_T_K",
    "prior_1d_scenario",
    "prior_1d_mdot_kg_s",
    "prior_1d_Re_main",
    "prior_1d_Tmean_K",
    "prior_1d_loop_delta_T_K",
    "prior_1d_qhx_duty_W",
    "prior_1d_Tmean_error_K",
    "prior_1d_loop_delta_T_error_K",
    "prior_1d_mdot_error_kg_s",
    "heater_imposed_duty_W",
    "heater_wallHeatFlux_W",
    "heater_imposed_minus_wallHeatFlux_W",
    "cooler_removed_duty_W",
    "cooler_wallHeatFlux_W",
    "test_section_wallHeatFlux_W",
    "net_wallHeatFlux_W",
    "max_abs_segment_enthalpy_residual_W",
    "mean_T_abs_gate_K",
    "loop_delta_T_abs_gate_K",
    "mdot_hold_rel_gate",
    "classification",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = list(rows)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({col: _csv_value(row.get(col, "")) for col in columns})


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return value


def _to_float(value: Any) -> float:
    if value is None or value == "":
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _round_or_blank(value: float, digits: int = 6) -> float | str:
    if not math.isfinite(value):
        return ""
    return round(float(value), digits)


def _truthy_text(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def build_contract_rows(ledger_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in ledger_rows:
        patch_group = raw["patch_group"]
        out = {col: raw.get(col, "") for col in CONTRACT_COLUMNS}
        out["replay_contract_role"] = PATCH_ROLE_TO_REPLAY.get(patch_group, "unclassified")
        out["thermal_contract_label"] = (
            "cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field"
        )
        rows.append(out)
    return rows


def aggregate_ledger(ledger_rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ledger_rows:
        grouped[row["source_id"]].append(row)

    summary: dict[str, dict[str, float]] = {}
    for source_id, rows in grouped.items():
        by_patch = {row["patch_group"]: row for row in rows}
        heater = by_patch.get("heater", {})
        cooler = by_patch.get("cooler", {})
        test_section = by_patch.get("test_section", {})
        wall_fluxes = [_to_float(row.get("wallHeatFlux_integral_W")) for row in rows]
        residuals = [_to_float(row.get("wallHeatFlux_vs_enthalpy_residual_W")) for row in rows]
        summary[source_id] = {
            "heater_imposed_duty_W": _to_float(heater.get("heater_imposed_duty_W")),
            "heater_wallHeatFlux_W": _to_float(heater.get("wallHeatFlux_integral_W")),
            "heater_imposed_minus_wallHeatFlux_W": _to_float(heater.get("imposed_Q_minus_wallHeatFlux_W")),
            "cooler_removed_duty_W": -abs(_to_float(cooler.get("cooler_removed_duty_W"))),
            "cooler_wallHeatFlux_W": _to_float(cooler.get("wallHeatFlux_integral_W")),
            "test_section_wallHeatFlux_W": _to_float(test_section.get("wallHeatFlux_integral_W")),
            "net_wallHeatFlux_W": sum(v for v in wall_fluxes if math.isfinite(v)),
            "max_abs_segment_enthalpy_residual_W": max((abs(v) for v in residuals if math.isfinite(v)), default=math.nan),
        }
    return summary


def load_driver_compare(path: Path) -> dict[str, dict[str, dict[str, float]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for row in raw:
        case_id = f"salt_{int(row['case'])}"
        result[case_id][str(row["src"])] = {
            "mdot": _to_float(row.get("mdot")),
            "Re": _to_float(row.get("Re")),
            "Tmean": _to_float(row.get("Tmean")),
            "Tmin": _to_float(row.get("Tmin")),
            "Tmax": _to_float(row.get("Tmax")),
            "dT": _to_float(row.get("dT")),
            "duty": _to_float(row.get("duty")),
        }
    return result


def build_target_rows(
    driver_compare: dict[str, dict[str, dict[str, float]]],
    aggregate: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, case_id in SOURCE_TO_CASE.items():
        cfd = driver_compare[case_id]["CFD"]
        one_d = driver_compare[case_id]["1D"]
        agg = aggregate[source_id]
        rows.append(
            {
                "case_id": case_id,
                "source_id": source_id,
                "cfd_mdot_kg_s": _round_or_blank(cfd["mdot"], 8),
                "cfd_Re_main": _round_or_blank(cfd["Re"], 3),
                "cfd_Tmean_K": _round_or_blank(cfd["Tmean"], 3),
                "cfd_Tmin_K": _round_or_blank(cfd["Tmin"], 3),
                "cfd_Tmax_K": _round_or_blank(cfd["Tmax"], 3),
                "cfd_loop_delta_T_K": _round_or_blank(cfd["dT"], 3),
                "prior_1d_scenario": "predictive_airside_ins_1.0in_rad_1",
                "prior_1d_mdot_kg_s": _round_or_blank(one_d["mdot"], 8),
                "prior_1d_Re_main": _round_or_blank(one_d["Re"], 3),
                "prior_1d_Tmean_K": _round_or_blank(one_d["Tmean"], 3),
                "prior_1d_loop_delta_T_K": _round_or_blank(one_d["dT"], 3),
                "prior_1d_qhx_duty_W": _round_or_blank(one_d["duty"], 3),
                "prior_1d_Tmean_error_K": _round_or_blank(one_d["Tmean"] - cfd["Tmean"], 3),
                "prior_1d_loop_delta_T_error_K": _round_or_blank(one_d["dT"] - cfd["dT"], 3),
                "prior_1d_mdot_error_kg_s": _round_or_blank(one_d["mdot"] - cfd["mdot"], 8),
                "heater_imposed_duty_W": _round_or_blank(agg["heater_imposed_duty_W"], 3),
                "heater_wallHeatFlux_W": _round_or_blank(agg["heater_wallHeatFlux_W"], 3),
                "heater_imposed_minus_wallHeatFlux_W": _round_or_blank(
                    agg["heater_imposed_minus_wallHeatFlux_W"], 3
                ),
                "cooler_removed_duty_W": _round_or_blank(agg["cooler_removed_duty_W"], 3),
                "cooler_wallHeatFlux_W": _round_or_blank(agg["cooler_wallHeatFlux_W"], 3),
                "test_section_wallHeatFlux_W": _round_or_blank(agg["test_section_wallHeatFlux_W"], 3),
                "net_wallHeatFlux_W": _round_or_blank(agg["net_wallHeatFlux_W"], 3),
                "max_abs_segment_enthalpy_residual_W": _round_or_blank(
                    agg["max_abs_segment_enthalpy_residual_W"], 3
                ),
                "mean_T_abs_gate_K": 2.0,
                "loop_delta_T_abs_gate_K": 1.0,
                "mdot_hold_rel_gate": 0.05,
                "classification": "thermal_state_mismatch_requires_frozen_hydraulics_replay",
            }
        )
    return rows


def build_span_heat_residual_rows(ledger_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, Any]] = []
    for row in ledger_rows:
        key = (row["source_id"], row["span"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "span": row["span"],
                "T_bulk_inlet_K": row.get("T_bulk_inlet_K", ""),
                "T_bulk_outlet_K": row.get("T_bulk_outlet_K", ""),
                "T_bulk_span_K": row.get("T_bulk_span_K", ""),
                "mdot_kg_s": row.get("mdot_kg_s", ""),
                "cp_jkgk": row.get("cp_jkgk", ""),
                "enthalpy_change_W": row.get("enthalpy_change_W", ""),
                "enthalpy_change_status": row.get("enthalpy_change_status", ""),
                "segment_wallHeatFlux_sum_W": row.get("segment_wallHeatFlux_sum_W", ""),
                "wallHeatFlux_vs_enthalpy_residual_W": row.get("wallHeatFlux_vs_enthalpy_residual_W", ""),
                "residual_fraction": row.get("residual_fraction", ""),
                "residual_assignment": row.get("residual_assignment", ""),
                "quality_flags": row.get("quality_flags", ""),
            }
        )
    return sorted(rows, key=lambda item: (item["source_id"], item["span"]))


def build_fluid_solver_state_audit() -> list[dict[str, Any]]:
    return [
        {
            "capability": "global_ambient_temperature",
            "current_state": "ScenarioConfig.ambient_temperature_K",
            "paper_replay_status": "supported_but_must_match_cfd_contract",
            "evidence": "../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py",
            "required_action": "Set from CFD boundary metadata rather than treating 300 K as implicit.",
        },
        {
            "capability": "global_insulation_thickness",
            "current_state": "ScenarioConfig.insulation_thickness_in plus case default",
            "paper_replay_status": "supported_only_as_global_scalar",
            "evidence": "effective_insulation_thickness_in(case, scenario)",
            "required_action": "Do not label 0.25/0.30 in 1D sweeps as CFD. CFD Salt contract is 1.4 in layer where present.",
        },
        {
            "capability": "per_parent_insulation_multiplier",
            "current_state": "outer_insulation_multiplier_by_parent_segment",
            "paper_replay_status": "partial_support",
            "evidence": "wall_and_insulation_resistances_per_length() applies per-parent multiplier",
            "required_action": "Create explicit per-segment reconstruction for insulated pipe legs versus bare quartz test section.",
        },
        {
            "capability": "surface_radiation_switch",
            "current_state": "ScenarioConfig.radiation_on with surface emissivity helper",
            "paper_replay_status": "not_equivalent_to_cfd_qr_term",
            "evidence": "patchwise ledger radiation_present=False for all rows",
            "required_action": "Treat surface emissivity metadata separately from an OpenFOAM qr heat-ledger term.",
        },
        {
            "capability": "per_parent_outer_convection_multiplier",
            "current_state": "outer_conv_multiplier_by_parent_segment",
            "paper_replay_status": "partial_support",
            "evidence": "_outer_closure_multipliers_for_segment()",
            "required_action": "Map CFD boundary_h_W_m2K and ambient per role before tuning any multiplier.",
        },
        {
            "capability": "three_d_source_profile",
            "current_state": "three_d_contract_case_id and use_three_d_source_profile",
            "paper_replay_status": "supported_after_normalized_contract",
            "evidence": "three_d_coupling.py REQUIRED_SOURCE_COLUMNS",
            "required_action": "Normalize heater wallHeatFlux/source rows into parent segments with explicit subspans.",
        },
        {
            "capability": "three_d_segment_losses",
            "current_state": "ambient_loss_model=external_prescribed_segment_loss and use_three_d_segment_losses",
            "paper_replay_status": "supported_after_normalized_contract",
            "evidence": "three_d_coupling.py REQUIRED_LOSS_COLUMNS",
            "required_action": "Normalize cooler, passive ambient, test-section, and grouped junction losses with sign convention checks.",
        },
        {
            "capability": "frozen_mdot_or_frozen_hydraulics",
            "current_state": "mdot search bounds and warm starts exist; no explicit frozen-mdot ScenarioConfig field found",
            "paper_replay_status": "requires_solver_extension_or_wrapper",
            "evidence": "ScenarioConfig has mdot_search_lower_kg_s/mdot_search_upper_kg_s but no fixed_mdot_kg_s",
            "required_action": "Add or wrap a thermal-only replay mode before claiming friction-independent thermal closure.",
        },
    ]


def build_replay_plan() -> list[dict[str, Any]]:
    return [
        {
            "sequence": 0,
            "stage_id": "replay_00_reproduce_current_baseline",
            "objective": "Reproduce the July 2 1D rows before changing the solver contract.",
            "hydraulics_policy": "existing_predictive_solution",
            "thermal_policy": "predictive_airside_ins_1.0in_rad_1",
            "entry_criteria": "driver_thermal_compare.json available",
            "exit_gate": "Numerically match prior_1d_Tmean_K and prior_1d_loop_delta_T_K within script tolerance.",
            "bakeoff_allowed": "no",
        },
        {
            "sequence": 1,
            "stage_id": "replay_01_freeze_cfd_hydraulics",
            "objective": "Hold mdot/hydraulic state near CFD so the thermal contract can be isolated.",
            "hydraulics_policy": "fixed CFD mdot target with 5 pct relative gate",
            "thermal_policy": "unchanged from replay_00",
            "entry_criteria": "fixed-mdot solver hook or equivalent wrapper reviewed",
            "exit_gate": "For each Salt case, abs(mdot_model-cfd_mdot)/cfd_mdot <= 0.05.",
            "bakeoff_allowed": "no",
        },
        {
            "sequence": 2,
            "stage_id": "replay_02_prescribe_cfd_patch_heat_ledger",
            "objective": "Use patchwise CFD heat sources/sinks instead of tuning global losses.",
            "hydraulics_policy": "frozen from replay_01",
            "thermal_policy": "heater wallHeatFlux source, cooler sink, passive ambient exchange, test-section exchange, grouped junction diagnostic loss",
            "entry_criteria": "thermal sign-convention and role-completeness tests pass",
            "exit_gate": "Heat ledger residuals are reported by span; no residual row is silently used as a fit target.",
            "bakeoff_allowed": "no",
        },
        {
            "sequence": 3,
            "stage_id": "replay_03_reconstruct_boundary_network",
            "objective": "Replace global 1D insulation/radiation assumptions with the CFD boundary contract.",
            "hydraulics_policy": "frozen from replay_01",
            "thermal_policy": "1.4 in insulated pipe legs where present; bare quartz test section; CFD ambient/h; emissivity metadata tracked separately from qr",
            "entry_criteria": "per-segment insulation, ambient h, and radiation semantics documented",
            "exit_gate": "Case documentation states exact solver inputs and unresolved boundary-network approximations.",
            "bakeoff_allowed": "no",
        },
        {
            "sequence": 4,
            "stage_id": "replay_04_thermal_iteration_gate",
            "objective": "Iterate thermal BC reconstruction until mean T and loop delta T match CFD.",
            "hydraulics_policy": "frozen from replay_01",
            "thermal_policy": "adjust only documented thermal contract terms, not friction",
            "entry_criteria": "replay_03 output complete for Salt 2/3/4",
            "exit_gate": "abs(Tmean error) <= 2 K and abs(loop delta T error) <= 1 K for all admitted cases.",
            "bakeoff_allowed": "no",
        },
        {
            "sequence": 5,
            "stage_id": "replay_05_model_form_bakeoff",
            "objective": "Compare hydraulic/thermal model forms only after thermal-state reconstruction is gated.",
            "hydraulics_policy": "candidate model forms scored separately",
            "thermal_policy": "frozen accepted replay_04 contract",
            "entry_criteria": "all replay_04 gates pass with provenance",
            "exit_gate": "Separate scores for pressure distribution, mdot, mean T, and loop delta T.",
            "bakeoff_allowed": "yes_after_gate",
        },
    ]


def build_test_plan() -> list[dict[str, Any]]:
    return [
        {
            "test_id": "role_completeness",
            "type": "unit",
            "requirement": "Contract contains heater, cooler, ambient_wall, test_section, and junction_other rows for Salt 2/3/4.",
            "pass_condition": "24 rows total and expected patch groups present.",
        },
        {
            "test_id": "sign_convention",
            "type": "unit",
            "requirement": "Positive heat is into fluid; cooler/passive losses remain negative where appropriate.",
            "pass_condition": "Heater wallHeatFlux > 0, cooler wallHeatFlux < 0, net wallHeatFlux near zero in aggregate.",
        },
        {
            "test_id": "radiation_semantics",
            "type": "unit",
            "requirement": "No OpenFOAM qr output term may be inferred from emissivity metadata.",
            "pass_condition": "All rows have radiation_present=False and a non-empty caveat.",
        },
        {
            "test_id": "enthalpy_residual_caveats",
            "type": "unit",
            "requirement": "Span endpoint enthalpy residuals are preserved with recirculation and bracket caveats.",
            "pass_condition": "Junction rows remain not bracketed; upcomer/test-section quality flags survive.",
        },
        {
            "test_id": "frozen_hydraulics_capability",
            "type": "review_gate",
            "requirement": "A fixed-mdot or frozen-hydraulics path is explicit before replay claims thermal-only iteration.",
            "pass_condition": "Solver audit resolves current requires_solver_extension_or_wrapper status.",
        },
        {
            "test_id": "thermal_replay_gate",
            "type": "analysis_gate",
            "requirement": "Mean T and loop delta T are matched before model-form bakeoff.",
            "pass_condition": "All Salt rows have abs(Tmean error) <= 2 K and abs(loop delta T error) <= 1 K.",
        },
    ]


def validate_outputs(
    contract_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    solver_audit_rows: list[dict[str, Any]],
    replay_plan_rows: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    if len(contract_rows) != 24:
        errors.append(f"Expected 24 contract rows, found {len(contract_rows)}")
    groups = {row["patch_group"] for row in contract_rows}
    expected_groups = set(PATCH_ROLE_TO_REPLAY)
    if groups != expected_groups:
        errors.append(f"Patch groups mismatch: expected {sorted(expected_groups)}, found {sorted(groups)}")
    if any(_truthy_text(row.get("radiation_present")) for row in contract_rows):
        errors.append("At least one row has radiation_present=True; expected no qr term for this package")
    if any(not str(row.get("radiation_caveat", "")).strip() for row in contract_rows):
        errors.append("At least one row lacks a radiation caveat")
    if any(float(row["prior_1d_Tmean_error_K"]) < 50.0 for row in target_rows):
        errors.append("Prior 1D thermal mismatch is unexpectedly small; target provenance may be wrong")
    frozen = [row for row in solver_audit_rows if row["capability"] == "frozen_mdot_or_frozen_hydraulics"]
    if not frozen or frozen[0]["paper_replay_status"] != "requires_solver_extension_or_wrapper":
        errors.append("Frozen-hydraulics capability status is not explicit")
    bakeoff_rows = [row for row in replay_plan_rows if "bakeoff" in row["stage_id"]]
    if not bakeoff_rows or bakeoff_rows[0]["bakeoff_allowed"] != "yes_after_gate":
        errors.append("Bakeoff row must be gated behind replay_04")
    pre_bakeoff = [row for row in replay_plan_rows if int(row["sequence"]) < int(bakeoff_rows[0]["sequence"])]
    if any(row["bakeoff_allowed"] != "no" for row in pre_bakeoff):
        errors.append("A pre-gate replay stage allows bakeoff")
    return errors


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Thermal Boundary Contract and Frozen Replay Plan",
        "",
        f"Generated: `{summary['generated_utc']}`",
        "Task: `AGENT-208`",
        "",
        "## Scope",
        "",
        "This package reconstructs the current CFD thermal boundary contract for admitted Salt 2/3/4 Jin mainline continuation rows and defines the frozen-hydraulics replay gate needed before any model-form bakeoff.",
        "",
        "## Key Findings",
        "",
        "- CFD Salt rows are labeled `cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field`.",
        "- The July 2 1D reference scenario `predictive_airside_ins_1.0in_rad_1` is 61.950 to 66.201 K hotter than CFD and has a loop delta T 3.7 to 3.9 K smaller.",
        "- `radiation_present=False` in the patchwise heat ledger means no OpenFOAM `qr` output term was available. Surface emissivity metadata is preserved as metadata, not converted into a heat-ledger radiation term.",
        "- Heater imposed duty exceeds realized heater wallHeatFlux by about 22 to 27 W; this remains a boundary/solid/storage or staging mismatch until a same-time solid-energy audit exists.",
        "- Frozen hydraulics are not an obvious first-class Fluid `ScenarioConfig` option yet. The replay needs a fixed-mdot solver hook or a reviewed wrapper before thermal-only iteration can be claimed.",
        "",
        "## Outputs",
        "",
        "- `cfd_thermal_boundary_contract.csv`: patchwise CFD thermal roles and reconstructed boundary metadata.",
        "- `span_heat_residuals.csv`: unique span endpoint enthalpy-change and wallHeatFlux residual rows.",
        "- `case_thermal_targets.csv`: CFD targets, prior 1D mismatch, and aggregate heat ledger quantities.",
        "- `fluid_solver_state_audit.csv`: current 1D solver capabilities and gaps relevant to the replay.",
        "- `frozen_hydraulics_replay_plan.csv`: required sequence and gates before bakeoff.",
        "- `test_plan.csv`: tests and review gates required for paper-grade use.",
        "- `summary.json`: machine-readable counts and validation errors.",
        "",
        "## Source Evidence",
        "",
        "- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`",
        "- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`",
        "- `work_products/2026-07-02_overnight/driver_thermal_compare.json`",
        "- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`",
        "- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/three_d_coupling.py`",
        "",
        "## Validation",
        "",
        f"- Contract rows: `{summary['contract_rows']}`",
        f"- Target rows: `{summary['target_rows']}`",
        f"- Validation errors: `{len(summary['validation_errors'])}`",
    ]
    if summary["validation_errors"]:
        lines.append("")
        lines.append("Validation errors:")
        for error in summary["validation_errors"]:
            lines.append(f"- {error}")
    output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    ledger_rows = _read_csv(Path(args.patchwise_heat_ledger))
    _ = _read_csv(Path(args.span_endpoint_temperatures))
    driver_compare = load_driver_compare(Path(args.driver_thermal_compare))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract_rows = build_contract_rows(ledger_rows)
    aggregate = aggregate_ledger(ledger_rows)
    target_rows = build_target_rows(driver_compare, aggregate)
    residual_rows = build_span_heat_residual_rows(ledger_rows)
    solver_audit_rows = build_fluid_solver_state_audit()
    replay_plan_rows = build_replay_plan()
    test_plan_rows = build_test_plan()

    _write_csv(output_dir / "cfd_thermal_boundary_contract.csv", contract_rows, CONTRACT_COLUMNS)
    _write_csv(
        output_dir / "case_thermal_targets.csv",
        target_rows,
        TARGET_COLUMNS,
    )
    _write_csv(
        output_dir / "span_heat_residuals.csv",
        residual_rows,
        [
            "source_id",
            "case_id",
            "span",
            "T_bulk_inlet_K",
            "T_bulk_outlet_K",
            "T_bulk_span_K",
            "mdot_kg_s",
            "cp_jkgk",
            "enthalpy_change_W",
            "enthalpy_change_status",
            "segment_wallHeatFlux_sum_W",
            "wallHeatFlux_vs_enthalpy_residual_W",
            "residual_fraction",
            "residual_assignment",
            "quality_flags",
        ],
    )
    _write_csv(
        output_dir / "fluid_solver_state_audit.csv",
        solver_audit_rows,
        ["capability", "current_state", "paper_replay_status", "evidence", "required_action"],
    )
    _write_csv(
        output_dir / "frozen_hydraulics_replay_plan.csv",
        replay_plan_rows,
        [
            "sequence",
            "stage_id",
            "objective",
            "hydraulics_policy",
            "thermal_policy",
            "entry_criteria",
            "exit_gate",
            "bakeoff_allowed",
        ],
    )
    _write_csv(output_dir / "test_plan.csv", test_plan_rows, ["test_id", "type", "requirement", "pass_condition"])

    validation_errors = validate_outputs(contract_rows, target_rows, solver_audit_rows, replay_plan_rows)
    target_error_values = [_to_float(row["prior_1d_Tmean_error_K"]) for row in target_rows]
    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "patchwise_heat_ledger": str(Path(args.patchwise_heat_ledger)),
        "span_endpoint_temperatures": str(Path(args.span_endpoint_temperatures)),
        "driver_thermal_compare": str(Path(args.driver_thermal_compare)),
        "contract_rows": len(contract_rows),
        "target_rows": len(target_rows),
        "span_residual_rows": len(residual_rows),
        "patch_groups": dict(sorted({group: sum(1 for row in contract_rows if row["patch_group"] == group) for group in set(PATCH_ROLE_TO_REPLAY)}.items())),
        "thermal_contract_label": "cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field",
        "prior_1d_Tmean_error_K_range": [
            _round_or_blank(min(target_error_values), 3),
            _round_or_blank(max(target_error_values), 3),
        ],
        "replay_gates": {
            "mean_T_abs_gate_K": 2.0,
            "loop_delta_T_abs_gate_K": 1.0,
            "mdot_hold_rel_gate": 0.05,
            "bakeoff_requires_stage": "replay_04_thermal_iteration_gate",
        },
        "validation_errors": validation_errors,
    }
    output_dir.joinpath("summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patchwise-heat-ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--span-endpoint-temperatures", default=str(DEFAULT_SPANS))
    parser.add_argument("--driver-thermal-compare", default=str(DEFAULT_DRIVER_COMPARE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_package(args)
    if summary["validation_errors"]:
        for error in summary["validation_errors"]:
            print(f"ERROR: {error}")
        return 1
    print(f"Wrote thermal boundary contract package to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
