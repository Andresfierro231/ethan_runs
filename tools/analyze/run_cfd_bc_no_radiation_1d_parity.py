#!/usr/bin/env python3
"""Run radiation-off fixed-mdot 1D sensitivity diagnostics.

AGENT-279 extends the AGENT-271 parity work. It keeps Fluid read-only, holds
mdot at the CFD value, forces radiation off in the primary modes, imposes the
CFD heater and cooler boundary inputs together, and compares section heat
gain/loss against the CFD patch ledger.

AGENT-287 corrects the interpretation: after AGENT-277, this package is a
radiation-off sensitivity/diagnostic, not Ethan-CFD parity. Ethan CFD
rcExternalTemperature uses emissivity/Tsur in realized wallHeatFlux, with no
separate exported radiation ledger.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import socket
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.analyze import build_thermal_mismatch_remedy_deep_dive as deep
from tools.analyze import run_cfd_informed_fixed_mdot_1d_replays as legacy


TASK_ID = "AGENT-279"
DEFAULT_PATCH_TABLE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)
DEFAULT_TARGETS = (
    REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv"
)
DEFAULT_OUTPUT = (
    REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity"
)

CASE_NAME = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}
SEGMENT_TO_FLUID_PARENT = {
    "lower_leg": "heated_incline",
    "upcomer": "left_upper_vertical",
    "downcomer": "right_vertical",
    "cooling_branch": "cooled_incline_hx_active",
    "junction": "top_horizontal_exit",
}
PARENT_TO_SEGMENT = {value: key for key, value in SEGMENT_TO_FLUID_PARENT.items()}
PARENT_TO_SEGMENT["test_section"] = "upcomer"

CONTRACT_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "fluid_parent_segment",
    "role",
    "bc_types",
    "patch_count",
    "area_m2",
    "hA_W_per_K",
    "area_weighted_Ta_K",
    "imposed_Q_W",
    "imposed_source_W",
    "imposed_loss_W",
    "realized_wallHeatFlux_W",
    "realized_source_W",
    "realized_loss_W",
    "radiation_policy",
    "bc_equivalent_policy",
]

RUN_PLAN_COLUMNS = [
    "case_id",
    "source_id",
    "path_id",
    "description",
    "fixed_mdot_kg_s",
    "radiation_on",
    "thermal_input_policy",
    "hydraulic_policy",
    "score_partition",
    "modeling_status",
]

RESULT_COLUMNS = legacy.RESULT_COLUMNS + [
    "radiation_on",
    "source_map_json",
    "fixed_loss_map_json",
    "external_hA_map_json",
    "external_Ta_map_json",
    "boundary_condition_mode",
]

SUMMARY_COLUMNS = legacy.SUMMARY_COLUMNS + ["radiation_on", "best_case_count"]

SECTION_COLUMNS = [
    "case_id",
    "source_id",
    "path_id",
    "one_d_segment",
    "model_source_W",
    "model_cooler_loss_W",
    "model_external_loss_W",
    "model_net_to_fluid_W",
    "cfd_imposed_source_W",
    "cfd_imposed_loss_W",
    "cfd_imposed_net_to_fluid_W",
    "cfd_realized_source_W",
    "cfd_realized_loss_W",
    "cfd_realized_net_to_fluid_W",
    "model_minus_cfd_realized_net_W",
    "model_minus_cfd_imposed_net_W",
]

DISCREPANCY_COLUMNS = [
    "case_id",
    "path_id",
    "lane",
    "model_W",
    "cfd_imposed_W",
    "cfd_realized_W",
    "model_minus_cfd_realized_W",
    "interpretation",
]

CORRECTION_COLUMNS = [
    "correction_id",
    "applies_to",
    "initial_value",
    "fit_status",
    "basis",
    "next_action",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
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


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    return value


def fnum(value: Any, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def rounded(value: Any, digits: int = 6) -> float | str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    return round(parsed, digits)


def parent_for_patch(row: dict[str, str]) -> str:
    if row.get("role") == "test_section":
        return "test_section"
    return SEGMENT_TO_FLUID_PARENT.get(row.get("one_d_segment", ""), "")


def build_boundary_contract(patch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = {}
    for row in patch_rows:
        one_d_segment = row.get("one_d_segment", "")
        parent = parent_for_patch(row)
        role = row.get("role", "")
        if not one_d_segment or not parent or role == "zero_gradient_ncc_connector":
            continue
        key = (row["source_id"], row["case_id"], one_d_segment, parent, role)
        grouped.setdefault(key, []).append(row)

    rows: list[dict[str, Any]] = []
    for (source_id, case_id, one_d_segment, parent, role), items in sorted(grouped.items()):
        area = sum(fnum(row.get("area_m2")) for row in items)
        hA_terms = [
            (fnum(row.get("h_W_m2K")) * fnum(row.get("area_m2")), fnum(row.get("Ta_K")))
            for row in items
            if row.get("h_W_m2K") not in ("", None) and row.get("Ta_K") not in ("", None)
        ]
        hA = sum(term for term, _ in hA_terms)
        Ta = sum(term * ta for term, ta in hA_terms) / hA if hA > 0.0 else ""
        imposed = sum(fnum(row.get("imposed_Q_W")) for row in items)
        realized = sum(fnum(row.get("realized_wallHeatFlux_W")) for row in items)
        rows.append(
            {
                "source_id": source_id,
                "case_id": case_id,
                "one_d_segment": one_d_segment,
                "fluid_parent_segment": parent,
                "role": role,
                "bc_types": ";".join(sorted({row.get("bc_type", "") for row in items if row.get("bc_type")})),
                "patch_count": len(items),
                "area_m2": rounded(area, 9),
                "hA_W_per_K": rounded(hA, 9),
                "area_weighted_Ta_K": rounded(Ta, 6) if Ta != "" else "",
                "imposed_Q_W": rounded(imposed, 9),
                "imposed_source_W": rounded(max(imposed, 0.0), 9),
                "imposed_loss_W": rounded(max(-imposed, 0.0), 9),
                "realized_wallHeatFlux_W": rounded(realized, 9),
                "realized_source_W": rounded(max(realized, 0.0), 9),
                "realized_loss_W": rounded(max(-realized, 0.0), 9),
                "radiation_policy": "radiation_off_sensitivity_not_cfd_parity_after_AGENT_277",
                "bc_equivalent_policy": (
                    "non_cooler_rows_use_hA_Ta_convection_only_when_executed; "
                    "cooler_uses_imposed_externalTemperature_duty"
                ),
            }
        )
    return rows


def add_to_map(mapping: dict[str, float], key: str, value: float) -> None:
    mapping[key] = mapping.get(key, 0.0) + value


def case_maps(contract_rows: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    rows = [row for row in contract_rows if row["case_id"] == case_id]
    heater_sources: dict[str, float] = {}
    heater_test_sources: dict[str, float] = {}
    realized_sources: dict[str, float] = {}
    realized_losses: dict[str, float] = {}
    fixed_imposed_losses: dict[str, float] = {}
    hA_map: dict[str, float] = {}
    hA_Ta_weight: dict[str, float] = {}
    cooler_imposed_loss = 0.0

    for row in rows:
        parent = str(row["fluid_parent_segment"])
        role = str(row["role"])
        imposed_source = fnum(row.get("imposed_source_W"))
        imposed_loss = fnum(row.get("imposed_loss_W"))
        realized_source = fnum(row.get("realized_source_W"))
        realized_loss = fnum(row.get("realized_loss_W"))
        hA = fnum(row.get("hA_W_per_K"))
        Ta = fnum(row.get("area_weighted_Ta_K"), default=300.0)

        if role == "heater" and imposed_source > 0.0:
            add_to_map(heater_sources, parent, imposed_source)
            add_to_map(heater_test_sources, parent, imposed_source)
        if role == "test_section" and imposed_source > 0.0:
            add_to_map(heater_test_sources, "test_section", imposed_source)
        if role == "cooler":
            cooler_imposed_loss += imposed_loss
        if imposed_loss > 0.0:
            add_to_map(fixed_imposed_losses, parent, imposed_loss)
        if realized_source > 0.0:
            add_to_map(realized_sources, parent, realized_source)
        if realized_loss > 0.0:
            add_to_map(realized_losses, parent, realized_loss)
        if role != "cooler" and hA > 0.0:
            add_to_map(hA_map, parent, hA)
            add_to_map(hA_Ta_weight, parent, hA * Ta)

    Ta_map = {parent: hA_Ta_weight[parent] / hA for parent, hA in hA_map.items() if hA > 0.0}
    return {
        "heater_sources": heater_sources,
        "heater_test_sources": heater_test_sources,
        "realized_sources": realized_sources,
        "realized_losses": realized_losses,
        "fixed_imposed_losses": fixed_imposed_losses,
        "cooler_imposed_loss": cooler_imposed_loss,
        "hA_map": hA_map,
        "Ta_map": Ta_map,
    }


def run_plan_rows(targets: list[dict[str, str]]) -> list[dict[str, Any]]:
    specs = trial_specs()
    rows: list[dict[str, Any]] = []
    for target in targets:
        for spec in specs:
            rows.append(
                {
                    "case_id": target["case_id"],
                    "source_id": target["source_id"],
                    "path_id": spec["path_id"],
                    "description": spec["description"],
                    "fixed_mdot_kg_s": target["cfd_mdot_kg_s"],
                    "radiation_on": "False",
                    "thermal_input_policy": spec["thermal_input_policy"],
                    "hydraulic_policy": "hold mdot at CFD observation; do not perform pressure root search",
                    "score_partition": "thermal_periodicity_and_section_heat_parity; pressure_residual_diagnostic",
                    "modeling_status": spec["modeling_status"],
                }
            )
    return rows


def trial_specs() -> list[dict[str, str]]:
    return [
        {
            "path_id": "N0_current_fluid_rad_off",
            "description": "Current Fluid salt contract at CFD mdot with 1D radiation disabled.",
            "thermal_input_policy": "current Fluid heater/test-section source and predictive air-side HX/ambient models; radiation_on=False",
            "modeling_status": "reference_only_current_contract_no_radiation",
        },
        {
            "path_id": "N1_heater_cooler_imposed_rad_off",
            "description": "Impose CFD heater source and CFD cooler duty together, no radiation.",
            "thermal_input_policy": "CFD heater imposed source plus CFD cooler imposed sink; no test-section source; Fluid no-radiation ambient model remains active",
            "modeling_status": "combined_heater_cooler_boundary_probe_no_radiation",
        },
        {
            "path_id": "N2_cfd_setup_bc_plus_passive_conv_rad_off",
            "description": "Impose CFD setup sources/sinks and non-cooler hA/Ta convection-only external losses with radiation disabled.",
            "thermal_input_policy": "CFD heater/test-section imposed sources, CFD cooler imposed sink, and non-cooler CFD hA/Ta external losses; radiation_on=False",
            "modeling_status": "radiation_off_hA_Ta_sensitivity_not_cfd_parity_after_AGENT_277",
        },
        {
            "path_id": "N3_realized_wallflux_diagnostic_rad_off",
            "description": "Fixed-Q diagnostic using CFD realized wallHeatFlux roles, no radiation term added.",
            "thermal_input_policy": "positive realized wallHeatFlux as source and negative realized wallHeatFlux as fixed segment loss",
            "modeling_status": "fixed_Q_realized_wallflux_diagnostic_not_predictive_boundary_model",
        },
    ]


def base_scenario(S: Any) -> Any:
    return S.ScenarioConfig(
        name="fixed_mdot_cfd_bc_no_radiation",
        ambient_temperature_K=300.0,
        insulation_thickness_in=1.0,
        radiation_on=False,
        model_mode="predictive_airside_hx",
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=1.0e-5,
        mdot_search_upper_kg_s=0.2,
    )


def parent_fraction(seg: Any, parent: str) -> float:
    if seg.name == parent:
        return 1.0
    if seg.resolved_parent_name == parent:
        return max(float(seg.parent_end_fraction) - float(seg.parent_start_fraction), 0.0)
    return 0.0


def external_hA_loss_for_segment(seg: Any, T_avg_K: float, hA_map: dict[str, float], Ta_map: dict[str, float]) -> float:
    total = 0.0
    for parent, hA in hA_map.items():
        fraction = parent_fraction(seg, parent)
        if fraction <= 0.0:
            continue
        total += float(hA) * fraction * max(float(T_avg_K) - float(Ta_map.get(parent, 300.0)), 0.0)
    return total


def march_temperatures_hA(
    S: Any,
    case: Any,
    segments: list[Any],
    sensors: list[Any],
    mdot_kg_s: float,
    T_start_K: float,
    scenario: Any,
    prescribed_sources: dict[str, float],
    cooler_loss_W: float,
    hA_map: dict[str, float],
    Ta_map: dict[str, float],
) -> tuple[list[Any], dict[str, float], dict[str, dict[str, object]], float, float, float]:
    segment_states: list[Any] = []
    sensor_predictions: dict[str, float] = {}
    sensor_provenance: dict[str, dict[str, object]] = {}
    s_cum = 0.0
    T_in = T_start_K
    qambient_total = 0.0
    qhx_total = 0.0
    hx_length = S.active_hx_length_m(segments)
    air_out = S.effective_air_inlet_temperature_K(case, scenario)

    for seg in segments:
        Q_source = S.heating_power_for_segment_with_scenario(
            seg,
            case,
            scenario,
            prescribed_segment_sources_W=prescribed_sources,
        )
        q_sink = float(cooler_loss_W) * seg.length_m / max(hx_length, 1.0e-12) if seg.has_hx else 0.0
        T_out = T_in
        q_ext = 0.0
        diag = None
        for _ in range(10):
            T_avg = 0.5 * (T_in + T_out)
            cp_avg = case.fluid.cp(T_avg)
            diag = S.wall_and_insulation_resistances_per_length(seg, case, T_avg, mdot_kg_s, scenario)
            q_ext = external_hA_loss_for_segment(seg, T_avg, hA_map, Ta_map)
            T_new = T_in + (Q_source - q_sink - q_ext) / max(mdot_kg_s * cp_avg, 1.0e-12)
            if abs(T_new - T_out) < 1.0e-9:
                T_out = T_new
                break
            T_out = 0.5 * T_out + 0.5 * T_new

        if diag is None:
            diag = S.wall_and_insulation_resistances_per_length(seg, case, T_in, mdot_kg_s, scenario)
        T_avg = 0.5 * (T_in + T_out)
        state = S.SegmentState(
            segment_name=seg.name,
            s_start_m=s_cum,
            s_end_m=s_cum + seg.length_m,
            T_in_K=T_in,
            T_out_K=T_out,
            T_avg_K=T_avg,
            Q_source_W=Q_source,
            Q_hx_sink_W=q_sink,
            Q_ambient_W=q_ext,
            q_ambient_W_per_m=q_ext / max(seg.length_m, 1.0e-12),
            h_inner_W_m2K=diag.h_inner_W_m2K,
            h_outer_W_m2K=diag.h_outer_W_m2K,
            h_rad_W_m2K=0.0,
            reynolds_inner=diag.reynolds_inner,
            prandtl_inner=diag.prandtl_inner,
            nusselt_inner=diag.nusselt_inner,
            h_inner_multiplier=diag.h_inner_multiplier,
            profile_descriptor_htc_signal=diag.profile_descriptor_htc_signal,
            profile_descriptor_friction_signal=diag.profile_descriptor_friction_signal,
            profile_descriptor_developing_signal=diag.profile_descriptor_developing_signal,
            profile_descriptor_htc_shape_signal=diag.profile_descriptor_htc_shape_signal,
            profile_descriptor_friction_shape_signal=diag.profile_descriptor_friction_shape_signal,
            profile_descriptor_htc_shape_contribution=diag.profile_descriptor_htc_shape_contribution,
            profile_descriptor_htc_developing_contribution=diag.profile_descriptor_htc_developing_contribution,
            profile_descriptor_friction_shape_contribution=diag.profile_descriptor_friction_shape_contribution,
            profile_descriptor_friction_developing_contribution=diag.profile_descriptor_friction_developing_contribution,
            profile_descriptor_source_kind=diag.profile_descriptor_source_kind,
            profile_descriptor_source_case_id=diag.profile_descriptor_source_case_id,
            profile_descriptor_reference_path=diag.profile_descriptor_reference_path,
            profile_descriptor_section_id=diag.profile_descriptor_section_id,
            profile_descriptor_section_label=diag.profile_descriptor_section_label,
            profile_descriptor_htc_multiplier=diag.profile_descriptor_htc_multiplier,
            profile_descriptor_friction_multiplier=diag.profile_descriptor_friction_multiplier,
            outer_conv_multiplier=diag.outer_conv_multiplier,
            outer_rad_multiplier=0.0,
            outer_insulation_multiplier=diag.outer_insulation_multiplier,
            R_i_prime_K_m_W=diag.R_i_prime_K_m_W,
            R_wall_prime_K_m_W=diag.R_wall_prime_K_m_W,
            R_ins_prime_K_m_W=diag.R_ins_prime_K_m_W,
            R_o_prime_K_m_W=diag.R_o_prime_K_m_W,
            R_total_prime_K_m_W=diag.R_total_prime_K_m_W,
            T_pipe_outer_wall_K=diag.T_pipe_outer_wall_K,
            T_outer_surface_K=diag.T_outer_surface_K,
            notes="cfd_hA_Ta_convection_only_no_radiation",
        )
        segment_states.append(state)
        qambient_total += q_ext
        qhx_total += q_sink
        T_in = T_out
        s_cum += seg.length_m

    return segment_states, sensor_predictions, sensor_provenance, qambient_total, qhx_total, air_out


def solve_temperature_periodicity_hA(
    S: Any,
    case: Any,
    segments: list[Any],
    sensors: list[Any],
    mdot_kg_s: float,
    scenario: Any,
    prescribed_sources: dict[str, float],
    cooler_loss_W: float,
    hA_map: dict[str, float],
    Ta_map: dict[str, float],
) -> Any:
    lo, hi = S._temperature_scan_bounds(case, scenario, mdot_kg_s, prescribed_segment_sources_W=prescribed_sources)
    grid = S._temperature_scan_grid(lo, hi, None)
    snapshots = []
    for T0 in grid:
        seg_states, sensor_preds, sensor_provenance, qamb, qhx, air_out = march_temperatures_hA(
            S, case, segments, sensors, mdot_kg_s, float(T0), scenario, prescribed_sources, cooler_loss_W, hA_map, Ta_map
        )
        residual = seg_states[-1].T_out_K - float(T0)
        snapshots.append((float(T0), residual, seg_states, sensor_preds, sensor_provenance, qamb, qhx, air_out))

    best = min(snapshots, key=lambda item: abs(item[1]))
    bracket = None
    for prev, curr in zip(snapshots[:-1], snapshots[1:]):
        if prev[1] == 0.0 or prev[1] * curr[1] < 0.0 or curr[1] == 0.0:
            bracket = (prev[0], curr[0], prev[1], curr[1])
            break

    if bracket is None:
        T0, residual, seg_states, sensor_preds, sensor_provenance, qamb, qhx, air_out = best
        return S.ThermalClosureResult(
            start_temperature_K=T0,
            end_temperature_K=seg_states[-1].T_out_K,
            temperature_periodicity_error_K=residual,
            qhx_total_W=qhx,
            qambient_total_W=qamb,
            predicted_air_outlet_temperature_K=air_out,
            sensor_predictions_K=sensor_preds,
            sensor_prediction_provenance=sensor_provenance,
            segment_states=seg_states,
            root_found=False,
            root_bracketed=False,
            root_reason="no_bracketed_temperature_periodicity_root",
        )

    T_lo, T_hi, r_lo, _ = bracket
    for _ in range(25):
        T_mid = 0.5 * (T_lo + T_hi)
        seg_states, _, _, _, _, _ = march_temperatures_hA(
            S, case, segments, sensors, mdot_kg_s, T_mid, scenario, prescribed_sources, cooler_loss_W, hA_map, Ta_map
        )
        r_mid = seg_states[-1].T_out_K - T_mid
        if abs(r_mid) < 1.0e-9:
            T_lo = T_hi = T_mid
            break
        if r_lo * r_mid <= 0.0:
            T_hi = T_mid
        else:
            T_lo = T_mid
            r_lo = r_mid

    T_root = 0.5 * (T_lo + T_hi)
    seg_states, sensor_preds, sensor_provenance, qamb, qhx, air_out = march_temperatures_hA(
        S, case, segments, sensors, mdot_kg_s, T_root, scenario, prescribed_sources, cooler_loss_W, hA_map, Ta_map
    )
    residual = seg_states[-1].T_out_K - T_root
    return S.ThermalClosureResult(
        start_temperature_K=T_root,
        end_temperature_K=seg_states[-1].T_out_K,
        temperature_periodicity_error_K=residual,
        qhx_total_W=qhx,
        qambient_total_W=qamb,
        predicted_air_outlet_temperature_K=air_out,
        sensor_predictions_K=sensor_preds,
        sensor_prediction_provenance=sensor_provenance,
        segment_states=seg_states,
        root_found=True,
        root_bracketed=True,
        root_reason="temperature_periodicity_root_found",
    )


def pressure_snapshot_hA(
    S: Any,
    case: Any,
    segments: list[Any],
    sensors: list[Any],
    scenario: Any,
    mdot: float,
    sources: dict[str, float],
    cooler_loss: float,
    hA_map: dict[str, float],
    Ta_map: dict[str, float],
) -> dict[str, Any]:
    thermal = solve_temperature_periodicity_hA(S, case, segments, sensors, mdot, scenario, sources, cooler_loss, hA_map, Ta_map)
    dp_b = S.buoyancy_pressure(case, thermal.segment_states, segments)
    dp_l, re_main, f_main, v_main = S.distributed_and_minor_losses(
        case, scenario, mdot, thermal.segment_states, segments, S.MinorLosses()
    )
    return {
        "thermal": thermal,
        "deltaP_buoyancy_Pa": dp_b,
        "deltaP_losses_Pa": dp_l,
        "pressure_residual_Pa": dp_l - dp_b,
        "reynolds_main": re_main,
        "friction_factor_main": f_main,
        "velocity_main_m_s": v_main,
    }


def section_for_parent(parent: str) -> str:
    return PARENT_TO_SEGMENT.get(parent, "")


def summarize_model_sections(case_id: str, source_id: str, path_id: str, states: list[Any], segments: list[Any]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, float]] = {}
    for state, seg in zip(states, segments):
        parent = seg.resolved_parent_name
        section = section_for_parent(parent)
        if not section:
            continue
        rec = grouped.setdefault(section, {"source": 0.0, "cooler": 0.0, "external": 0.0})
        rec["source"] += float(state.Q_source_W)
        rec["cooler"] += float(state.Q_hx_sink_W)
        rec["external"] += float(state.Q_ambient_W)
    return [
        {
            "case_id": case_id,
            "source_id": source_id,
            "path_id": path_id,
            "one_d_segment": section,
            "model_source_W": values["source"],
            "model_cooler_loss_W": values["cooler"],
            "model_external_loss_W": values["external"],
            "model_net_to_fluid_W": values["source"] - values["cooler"] - values["external"],
        }
        for section, values in sorted(grouped.items())
    ]


def cfd_section_totals(contract_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, float]]:
    totals: dict[tuple[str, str], dict[str, float]] = {}
    for row in contract_rows:
        key = (str(row["case_id"]), str(row["one_d_segment"]))
        rec = totals.setdefault(
            key,
            {"imposed_source": 0.0, "imposed_loss": 0.0, "realized_source": 0.0, "realized_loss": 0.0},
        )
        rec["imposed_source"] += fnum(row.get("imposed_source_W"))
        rec["imposed_loss"] += fnum(row.get("imposed_loss_W"))
        rec["realized_source"] += fnum(row.get("realized_source_W"))
        rec["realized_loss"] += fnum(row.get("realized_loss_W"))
    return totals


def merge_section_comparison(section_rows: list[dict[str, Any]], contract_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cfd = cfd_section_totals(contract_rows)
    out: list[dict[str, Any]] = []
    for row in section_rows:
        totals = cfd.get((str(row["case_id"]), str(row["one_d_segment"])), {})
        imp_source = totals.get("imposed_source", 0.0)
        imp_loss = totals.get("imposed_loss", 0.0)
        real_source = totals.get("realized_source", 0.0)
        real_loss = totals.get("realized_loss", 0.0)
        model_net = float(row["model_net_to_fluid_W"])
        imposed_net = imp_source - imp_loss
        realized_net = real_source - real_loss
        out.append(
            {
                **row,
                "cfd_imposed_source_W": imp_source,
                "cfd_imposed_loss_W": imp_loss,
                "cfd_imposed_net_to_fluid_W": imposed_net,
                "cfd_realized_source_W": real_source,
                "cfd_realized_loss_W": real_loss,
                "cfd_realized_net_to_fluid_W": realized_net,
                "model_minus_cfd_realized_net_W": model_net - realized_net,
                "model_minus_cfd_imposed_net_W": model_net - imposed_net,
            }
        )
    return out


def result_row(
    S: Any,
    target: dict[str, str],
    path_id: str,
    spec: dict[str, str],
    snapshot: dict[str, Any],
    mdot: float,
    source_total: float,
    fixed_loss_total: float,
    source_map: dict[str, float],
    fixed_loss_map: dict[str, float],
    hA_map: dict[str, float],
    Ta_map: dict[str, float],
    boundary_mode: str,
) -> dict[str, Any]:
    thermal = snapshot["thermal"]
    tmean = deep.length_weighted_mean(thermal.segment_states)
    dt = deep.loop_delta(thermal.segment_states)
    dp_b = float(snapshot["deltaP_buoyancy_Pa"])
    dp_l = float(snapshot["deltaP_losses_Pa"])
    residual = float(snapshot["pressure_residual_Pa"])
    tol = legacy.pressure_tolerance(S, dp_b, dp_l)
    cfd_tmean = fnum(target["cfd_Tmean_K"])
    cfd_dt = fnum(target["cfd_loop_delta_T_K"])
    return {
        "case_id": target["case_id"],
        "source_id": target["source_id"],
        "path_id": path_id,
        "description": spec["description"],
        "fixed_mdot_kg_s": rounded(mdot, 8),
        "cfd_mdot_kg_s": rounded(mdot, 8),
        "mdot_relative_error": 0.0,
        "thermal_root_found": bool(thermal.root_found),
        "temperature_root_bracketed": bool(thermal.root_bracketed),
        "temperature_root_reason": thermal.root_reason,
        "temperature_periodicity_error_K": rounded(thermal.temperature_periodicity_error_K, 6),
        "model_Tmean_K": rounded(tmean, 6),
        "cfd_Tmean_K": rounded(cfd_tmean, 6),
        "Tmean_error_K": rounded(tmean - cfd_tmean, 6),
        "model_loop_delta_T_K": rounded(dt, 6),
        "cfd_loop_delta_T_K": rounded(cfd_dt, 6),
        "loop_delta_T_error_K": rounded(dt - cfd_dt, 6),
        "qhx_total_W": rounded(thermal.qhx_total_W, 6),
        "qambient_total_W": rounded(thermal.qambient_total_W, 6),
        "source_total_W": rounded(source_total, 6),
        "prescribed_loss_total_W": rounded(fixed_loss_total, 6),
        "deltaP_buoyancy_Pa": rounded(dp_b, 6),
        "deltaP_losses_Pa": rounded(dp_l, 6),
        "pressure_residual_Pa": rounded(residual, 6),
        "pressure_residual_tolerance_Pa": rounded(tol, 6),
        "pressure_residual_margin_Pa": rounded(abs(residual) - tol, 6),
        "pressure_root_policy": "not_rooted_fixed_mdot_pressure_residual_diagnostic",
        "reynolds_main": rounded(snapshot["reynolds_main"], 6),
        "velocity_main_m_s": rounded(snapshot["velocity_main_m_s"], 8),
        "friction_factor_main": rounded(snapshot["friction_factor_main"], 8),
        "predicted_air_outlet_temperature_K": rounded(thermal.predicted_air_outlet_temperature_K, 6),
        "start_temperature_K": rounded(thermal.start_temperature_K, 6),
        "end_temperature_K": rounded(thermal.end_temperature_K, 6),
        "thermal_input_policy": spec["thermal_input_policy"],
        "hydraulic_policy": "hold mdot at CFD observation; do not perform pressure root search",
        "score_partition": "thermal_periodicity_and_section_heat_parity; pressure_residual_diagnostic",
        "modeling_status": spec["modeling_status"],
        "radiation_on": "False",
        "source_map_json": json.dumps(source_map, sort_keys=True),
        "fixed_loss_map_json": json.dumps(fixed_loss_map, sort_keys=True),
        "external_hA_map_json": json.dumps(hA_map, sort_keys=True),
        "external_Ta_map_json": json.dumps(Ta_map, sort_keys=True),
        "boundary_condition_mode": boundary_mode,
    }


def run_replays(targets: list[dict[str, str]], contract_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    S, build_geometry, default_geometry_refinement, cases = legacy.import_fluid_cases()
    base = base_scenario(S)
    segments, sensors = build_geometry(refinement=default_geometry_refinement())
    specs = {spec["path_id"]: spec for spec in trial_specs()}
    results: list[dict[str, Any]] = []
    model_sections: list[dict[str, Any]] = []

    for target in targets:
        case_id = target["case_id"]
        case = cases[CASE_NAME[case_id]]
        mdot = legacy.safe_float(target["cfd_mdot_kg_s"])
        maps = case_maps(contract_rows, case_id)
        scenario_segments = legacy.scenario_segments_for_solver(S, segments, case, base)

        trials = [
            ("N0_current_fluid_rad_off", base, None, None, {}, {}, "current_fluid_no_radiation"),
            (
                "N1_heater_cooler_imposed_rad_off",
                replace(base, name="heater_cooler_imposed_rad_off", model_mode="imposed_qhx", imposed_qhx_W=maps["cooler_imposed_loss"]),
                maps["heater_sources"],
                None,
                {},
                {},
                "heater_source_plus_cooler_duty_no_radiation",
            ),
            (
                "N3_realized_wallflux_diagnostic_rad_off",
                replace(base, name="realized_wallflux_diagnostic_rad_off", model_mode="imposed_qhx", imposed_qhx_W=0.0),
                maps["realized_sources"],
                maps["realized_losses"],
                {},
                {},
                "fixed_Q_realized_wallflux_no_radiation",
            ),
        ]
        for path_id, scenario, sources, losses, hA_map, Ta_map, mode in trials:
            snapshot = S.pressure_residual(
                mdot,
                case,
                scenario_segments,
                sensors,
                scenario,
                S.MinorLosses(),
                warm_start_temperature_K=None,
                prescribed_segment_sources_W=sources,
                prescribed_segment_losses_W=losses,
            )
            source_total = sum(float(v) for v in sources.values()) if sources is not None else case.heater_power_W + case.test_section_power_W
            fixed_loss_total = sum(float(v) for v in losses.values()) if losses is not None else 0.0
            results.append(
                result_row(
                    S,
                    target,
                    path_id,
                    specs[path_id],
                    snapshot,
                    mdot,
                    source_total,
                    fixed_loss_total,
                    sources or {},
                    losses or {},
                    hA_map,
                    Ta_map,
                    mode,
                )
            )
            model_sections.extend(
                summarize_model_sections(case_id, target["source_id"], path_id, snapshot["thermal"].segment_states, scenario_segments)
            )

        path_id = "N2_cfd_setup_bc_plus_passive_conv_rad_off"
        scenario = replace(base, name="cfd_setup_bc_plus_passive_conv_rad_off", model_mode="imposed_qhx", imposed_qhx_W=maps["cooler_imposed_loss"])
        snapshot = pressure_snapshot_hA(
            S,
            case,
            scenario_segments,
            sensors,
            scenario,
            mdot,
            maps["heater_test_sources"],
            maps["cooler_imposed_loss"],
            maps["hA_map"],
            maps["Ta_map"],
        )
        results.append(
            result_row(
                S,
                target,
                path_id,
                specs[path_id],
                snapshot,
                mdot,
                sum(float(v) for v in maps["heater_test_sources"].values()),
                0.0,
                maps["heater_test_sources"],
                {},
                maps["hA_map"],
                maps["Ta_map"],
                "setup_sources_cooler_duty_hA_Ta_convection_no_radiation",
            )
        )
        model_sections.extend(
            summarize_model_sections(case_id, target["source_id"], path_id, snapshot["thermal"].segment_states, scenario_segments)
        )
    return results, model_sections


def summarize_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["path_id"]), []).append(row)
    summaries: list[dict[str, Any]] = []
    for path_id, items in grouped.items():
        t_errors = [abs(float(item["Tmean_error_K"])) for item in items]
        dt_errors = [abs(float(item["loop_delta_T_error_K"])) for item in items]
        p_resids = [abs(float(item["pressure_residual_Pa"])) for item in items]
        summaries.append(
            {
                "path_id": path_id,
                "case_count": len(items),
                "mean_abs_Tmean_error_K": rounded(sum(t_errors) / len(t_errors), 6),
                "max_abs_Tmean_error_K": rounded(max(t_errors), 6),
                "mean_abs_loop_delta_T_error_K": rounded(sum(dt_errors) / len(dt_errors), 6),
                "max_abs_loop_delta_T_error_K": rounded(max(dt_errors), 6),
                "mean_abs_pressure_residual_Pa": rounded(sum(p_resids) / len(p_resids), 6),
                "max_abs_pressure_residual_Pa": rounded(max(p_resids), 6),
                "thermal_gate_pass": all(err <= 2.0 for err in t_errors) and all(err <= 1.0 for err in dt_errors),
                "pressure_is_diagnostic_not_gate": True,
                "interpretation": interpretation_for_path(path_id),
                "radiation_on": "False",
                "best_case_count": sum(1 for item in items if abs(float(item["Tmean_error_K"])) == min(t_errors)),
            }
        )
    return sorted(summaries, key=lambda row: str(row["path_id"]))


def interpretation_for_path(path_id: str) -> str:
    return {
        "N0_current_fluid_rad_off": "Current Fluid contract with radiation disabled; reference only.",
        "N1_heater_cooler_imposed_rad_off": "Tests whether imposing heater and cooler setup terms together fixes the first-order thermal state.",
        "N2_cfd_setup_bc_plus_passive_conv_rad_off": "Radiation-off hA/Ta sensitivity: setup sources/sinks plus hA/Ta convection-only external losses. Superseded as CFD parity after AGENT-277/287.",
        "N3_realized_wallflux_diagnostic_rad_off": "Fixed-Q realized-wallHeatFlux diagnostic; useful for heat accounting but not a predictive boundary model.",
    }[path_id]


def discrepancy_rows(results: list[dict[str, Any]], section_rows: list[dict[str, Any]], contract_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    roles: dict[tuple[str, str], dict[str, float]] = {}
    for row in contract_rows:
        key = (str(row["case_id"]), str(row["role"]))
        rec = roles.setdefault(key, {"imposed": 0.0, "realized": 0.0})
        rec["imposed"] += fnum(row.get("imposed_source_W")) - fnum(row.get("imposed_loss_W"))
        rec["realized"] += fnum(row.get("realized_source_W")) - fnum(row.get("realized_loss_W"))

    section_by_case_path: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in section_rows:
        section_by_case_path.setdefault((str(row["case_id"]), str(row["path_id"])), []).append(row)

    for result in results:
        case_id = str(result["case_id"])
        path_id = str(result["path_id"])
        sections = section_by_case_path.get((case_id, path_id), [])
        source_map = json.loads(str(result.get("source_map_json") or "{}"))
        model_heater_source = (
            float(source_map["heated_incline"])
            if "heated_incline" in source_map
            else sum(float(row["model_source_W"]) for row in sections if row["one_d_segment"] == "lower_leg")
        )
        model_test_source = (
            float(source_map["test_section"])
            if "test_section" in source_map
            else sum(float(row["model_source_W"]) for row in sections if row["one_d_segment"] == "upcomer")
        )
        model_cooler = sum(float(row["model_cooler_loss_W"]) for row in sections)
        model_external = sum(float(row["model_external_loss_W"]) for row in sections)
        lanes = [
            ("heater_source", model_heater_source, roles.get((case_id, "heater"), {}).get("imposed", 0.0), roles.get((case_id, "heater"), {}).get("realized", 0.0)),
            ("cooler_sink", -model_cooler, roles.get((case_id, "cooler"), {}).get("imposed", 0.0), roles.get((case_id, "cooler"), {}).get("realized", 0.0)),
            ("test_section", model_test_source, roles.get((case_id, "test_section"), {}).get("imposed", 0.0), roles.get((case_id, "test_section"), {}).get("realized", 0.0)),
            ("external_passive_loss", -model_external, 0.0, sum(roles.get((case_id, role), {}).get("realized", 0.0) for role in ("ambient_wall", "junction_other"))),
        ]
        for lane, model, imposed, realized in lanes:
            out.append(
                {
                    "case_id": case_id,
                    "path_id": path_id,
                    "lane": lane,
                    "model_W": rounded(model, 6),
                    "cfd_imposed_W": rounded(imposed, 6),
                    "cfd_realized_W": rounded(realized, 6),
                    "model_minus_cfd_realized_W": rounded(model - realized, 6),
                    "interpretation": discrepancy_interpretation(lane),
                }
            )
    return out


def discrepancy_interpretation(lane: str) -> str:
    return {
        "heater_source": "Heater setup versus heat actually transferred to the fluid.",
        "cooler_sink": "Cooling-jacket duty parity; negative means heat removed from fluid.",
        "test_section": "Quartz/test-section role discrepancy; CFD setup source can realize as net sink.",
        "external_passive_loss": "Ambient/junction passive external heat-loss lane with radiation disabled in the 1D pass; heater/test/cooler are reported separately.",
    }[lane]


def correction_proposals(contract_rows: list[dict[str, Any]], section_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    heater_ratios = []
    cooler_ratios = []
    for case_id in sorted({row["case_id"] for row in contract_rows}):
        heater_imp = sum(fnum(row.get("imposed_source_W")) for row in contract_rows if row["case_id"] == case_id and row["role"] == "heater")
        heater_real = sum(fnum(row.get("realized_source_W")) for row in contract_rows if row["case_id"] == case_id and row["role"] == "heater")
        cooler_imp = sum(fnum(row.get("imposed_loss_W")) for row in contract_rows if row["case_id"] == case_id and row["role"] == "cooler")
        cooler_real = sum(fnum(row.get("realized_loss_W")) for row in contract_rows if row["case_id"] == case_id and row["role"] == "cooler")
        if heater_imp > 0.0:
            heater_ratios.append(heater_real / heater_imp)
        if cooler_imp > 0.0:
            cooler_ratios.append(cooler_real / cooler_imp)
    best_path = min(summary_rows, key=lambda row: float(row["mean_abs_Tmean_error_K"]))["path_id"] if summary_rows else ""
    n2_rows = [row for row in section_rows if row["path_id"] == "N2_cfd_setup_bc_plus_passive_conv_rad_off"]
    passive_model = sum(float(row["model_external_loss_W"]) for row in n2_rows)
    passive_cfd = sum(
        fnum(row.get("realized_loss_W"))
        for row in contract_rows
        if row.get("role") != "cooler" and fnum(row.get("hA_W_per_K")) > 0.0
    )
    passive_ratio = passive_cfd / passive_model if passive_model > 0.0 else math.nan
    return [
        {
            "correction_id": "heater_effective_transfer_efficiency",
            "applies_to": "heater rcExternalTemperature setup source",
            "initial_value": rounded(sum(heater_ratios) / len(heater_ratios), 6) if heater_ratios else "",
            "fit_status": "candidate_after_boundary_parity_review",
            "basis": "CFD heater realized wallHeatFlux divided by imposed heater Q across Salt2-4.",
            "next_action": "Use as one global efficiency only if hA boundary replay still overpredicts heater transfer.",
        },
        {
            "correction_id": "cooler_duty_multiplier",
            "applies_to": "cooler externalTemperature imposed duty",
            "initial_value": rounded(sum(cooler_ratios) / len(cooler_ratios), 6) if cooler_ratios else "",
            "fit_status": "already_near_exact_for_current_cfd_setup",
            "basis": "CFD cooler realized wallHeatFlux is numerically equal to imposed cooler Q in AGENT-263.",
            "next_action": "Do not fit per-case cooler hacks; convert to UA/epsilon-NTU only in Fluid predictive mode.",
        },
        {
            "correction_id": "external_convection_hA_multiplier_no_radiation",
            "applies_to": "non-cooler hA/Ta external boundary rows",
            "initial_value": rounded(passive_ratio, 6),
            "fit_status": "diagnostic_only_until_wall_layer_and_bulk_temperature_mapping_review",
            "basis": "Ratio of non-cooler CFD realized hA-row losses to N2 convection-only hA losses.",
            "next_action": "Review section residuals before fitting a low-dimensional section-family multiplier.",
        },
        {
            "correction_id": "test_section_source_sink_contract",
            "applies_to": "quartz test-section rcExternalTemperature row",
            "initial_value": "separate_source_plus_external_loss",
            "fit_status": "required_model_form_change",
            "basis": "CFD setup imposes +37 W but realized wallHeatFlux is a net sink in Salt2-4.",
            "next_action": "Represent test section as imposed source plus external hA loss, not a pure source.",
        },
        {
            "correction_id": "current_best_path",
            "applies_to": "model selection diagnostic",
            "initial_value": best_path,
            "fit_status": "diagnostic_only",
            "basis": "Lowest mean absolute Tmean error among no-radiation fixed-mdot modes.",
            "next_action": "Use section residuals, not only Tmean, to decide the next Fluid API patch.",
        },
    ]


def validate_inputs(patch_rows: list[dict[str, str]], targets: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if len(patch_rows) != 207:
        errors.append(f"expected 207 AGENT-263 patch rows, found {len(patch_rows)}")
    cases = {row.get("case_id", "") for row in targets}
    if cases != {"salt_2", "salt_3", "salt_4"}:
        errors.append(f"unexpected target cases {sorted(cases)}")
    for row in patch_rows:
        if row.get("role") != "zero_gradient_ncc_connector" and not parent_for_patch(row):
            errors.append(f"missing parent mapping for {row.get('case_id')} {row.get('patch_name')} {row.get('one_d_segment')}")
            break
    return errors


def git_revision(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def write_readme(output_dir: Path, metadata: dict[str, Any]) -> None:
    text = f"""# CFD BC No-Radiation 1D Parity

Generated: `{metadata['generated_utc']}`
Task: `{TASK_ID}`

## Purpose

This package tests a radiation-off fixed-mdot sensitivity: impose the CFD
heater and cooler setup together in the 1D model, force radiation off, and
compare whether the same sections gain and lose the same heat. It is fixed-mdot
and repo-local. It does not edit Fluid, mutate CFD solver outputs, or change
admissions.

Important correction from AGENT-287: this package is not Ethan-CFD parity.
AGENT-277 showed that Ethan CFD `rcExternalTemperature` responds to
`emissivity` and `Tsur`, so radiative exchange is embedded in total CFD
`wallHeatFlux`. This radiation-off package remains useful as a diagnostic
sensitivity only.

## Outputs

- `cfd_boundary_condition_contract_no_radiation.csv`: role-level CFD boundary
  inputs mapped to Fluid parent segments, including imposed Q, realized
  wallHeatFlux, and convection-only `hA/Ta` terms.
- `fixed_mdot_no_radiation_parity_results.csv`: no-radiation fixed-mdot replay
  results for N0-N3.
- `section_heat_loss_comparison.csv`: section-by-section model heat gain/loss
  versus CFD imposed and realized heat.
- `discrepancy_attribution.csv`: heater, cooler, test-section, and passive
  external residual lanes.
- `correction_proposal.csv`: low-dimensional correction candidates.
- `path_summary.csv` and `run_metadata.json`.

## Main Result

Best radiation-off sensitivity path by mean absolute Tmean error:
`{metadata['best_path_by_mean_abs_Tmean_error']}`.

The package should be read with the section residuals, not only the mean
temperature score. `N2_cfd_setup_bc_plus_passive_conv_rad_off` is the closest
current repo-local radiation-off hA/Ta replay: heater/test-section imposed
sources, cooler imposed duty, and non-cooler `hA/Ta` convection-only losses.
Wall-layer parity remains approximate until Fluid has a first-class external
boundary dictionary mode.

## How To Read This Package

Use this package as a radiation-off sensitivity diagnostic, not as a final
thermal-closure fit and not as evidence that CFD radiation is absent. The
intended reading order is:

1. `cfd_boundary_condition_contract_no_radiation.csv`
   Defines the CFD patch roles reduced to Fluid parent segments. It preserves
   imposed heater/cooler/test-section setup terms, realized `wallHeatFlux`,
   non-cooler `hA/Ta`, and the explicit radiation-off sensitivity policy used
   in this pass.
2. `run_plan.csv`
   Lists the four fixed-mdot no-radiation replay modes for Salt2-4.
3. `path_summary.csv`
   Shows which mode best closes bulk mean temperature. This is only a first
   screen; it does not prove section heat parity.
4. `section_heat_loss_comparison.csv`
   Compares model heat gain/loss against CFD imposed and realized heat by
   physical section. This is the main table for finding where the model is
   losing heat in the wrong place.
5. `discrepancy_attribution.csv`
   Separates heater, cooler, test-section, and passive external residual lanes.
   Do not combine these lanes into one fitted scalar.
6. `correction_proposal.csv`
   Records low-dimensional correction candidates and blocks. Values marked
   diagnostic are not admissions.

## Replay Modes

- `N0_current_fluid_rad_off`: current Fluid thermal contract at CFD mdot, with
  radiation disabled.
- `N1_heater_cooler_imposed_rad_off`: CFD heater imposed source plus CFD cooler
  imposed duty, no radiation. This tests the first-order setup parity.
- `N2_cfd_setup_bc_plus_passive_conv_rad_off`: CFD heater/test-section setup
  sources, CFD cooler imposed duty, and non-cooler `hA/Ta` convection-only
  losses using 1D bulk temperature as the driving temperature. This is the
  closest current repo-local radiation-off hA/Ta replay, but it is not
  Ethan-CFD parity after AGENT-277/287 and is not yet wall-layer equivalent.
- `N3_realized_wallflux_diagnostic_rad_off`: fixed-Q diagnostic from realized
  CFD wall fluxes. It is heat-accounting evidence, not a predictive boundary
  model.

## Wall-Layer Mapping Block

The N2 replay intentionally applies CFD `hA/Ta` rows to the current 1D bulk
state through `q = hA * max(T_bulk - Ta, 0)`. That is a useful stress test, but
it is not the same as OpenFOAM's wall-boundary calculation. In CFD, the
boundary condition acts at the wall/near-wall temperature field, while the 1D
state is a segment bulk temperature. If wall-adjacent fluid is cooler or hotter
than the 1D bulk, the same `hA/Ta` can remove too much or too little heat.

The recommended mapping ladder is documented in:

`wall_layer_bulk_temperature_mapping_recommendations.md`

Until that ladder is implemented, external hA multipliers in
`correction_proposal.csv` should remain diagnostic only.

## Scientific Boundary

Radiation is forced off for this pass only as a sensitivity. AGENT-277 and
AGENT-287 supersede the original assumption that this matched CFD. The CFD
`rcExternalTemperature` boundary uses emissivity/Tsur and includes radiative
exchange inside total `wallHeatFlux`, but no separate `qr`/radiation ledger is
available. Therefore:

- Do not add a separate 1D radiation term on top of CFD `wallHeatFlux`.
- Do not call this radiation-off package CFD parity.
- For predictive 1D setup from physical inputs, retain/add radiative external
  loss capability or label radiation disabled as a sensitivity.

## Counts

- Boundary contract rows: `{metadata['boundary_contract_rows']}`
- Run-plan rows: `{metadata['run_plan_rows']}`
- Result rows: `{metadata['result_rows']}`
- Section comparison rows: `{metadata['section_comparison_rows']}`
- Discrepancy rows: `{metadata['discrepancy_rows']}`
- Correction proposal rows: `{metadata['correction_rows']}`
- Validation errors: `{len(metadata['validation_errors'])}`
"""
    output_dir.joinpath("README.md").write_text(text, encoding="utf-8")


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    patch_rows = read_csv(Path(args.patch_table))
    target_rows = read_csv(Path(args.targets))
    validation_errors = validate_inputs(patch_rows, target_rows)
    if validation_errors and args.strict:
        raise ValueError("; ".join(validation_errors))

    contract = build_boundary_contract(patch_rows)
    plan = run_plan_rows(target_rows)
    write_csv(output_dir / "cfd_boundary_condition_contract_no_radiation.csv", contract, CONTRACT_COLUMNS)
    write_csv(output_dir / "run_plan.csv", plan, RUN_PLAN_COLUMNS)

    results: list[dict[str, Any]] = []
    section_comparison: list[dict[str, Any]] = []
    path_summary: list[dict[str, Any]] = []
    discrepancies: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    if not args.plan_only:
        results, model_sections = run_replays(target_rows, contract)
        path_summary = summarize_results(results)
        section_comparison = merge_section_comparison(model_sections, contract)
        discrepancies = discrepancy_rows(results, section_comparison, contract)
        proposals = correction_proposals(contract, section_comparison, path_summary)
        write_csv(output_dir / "fixed_mdot_no_radiation_parity_results.csv", results, RESULT_COLUMNS)
        write_csv(output_dir / "path_summary.csv", path_summary, SUMMARY_COLUMNS)
        write_csv(output_dir / "section_heat_loss_comparison.csv", section_comparison, SECTION_COLUMNS)
        write_csv(output_dir / "discrepancy_attribution.csv", discrepancies, DISCREPANCY_COLUMNS)
        write_csv(output_dir / "correction_proposal.csv", proposals, CORRECTION_COLUMNS)

    metadata = {
        "generated_utc": utc_now(),
        "task": TASK_ID,
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""),
        "cwd": str(Path.cwd()),
        "command": " ".join(sys.argv),
        "patch_table": rel(Path(args.patch_table)),
        "targets": rel(Path(args.targets)),
        "fluid_root": str(deep.FLUID_ROOT),
        "ethan_runs_git_revision": git_revision(REPO_ROOT),
        "fluid_git_revision": git_revision(deep.FLUID_ROOT),
        "validation_errors": validation_errors,
        "boundary_contract_rows": len(contract),
        "run_plan_rows": len(plan),
        "result_rows": len(results),
        "path_summary_rows": len(path_summary),
        "section_comparison_rows": len(section_comparison),
        "discrepancy_rows": len(discrepancies),
        "correction_rows": len(proposals),
        "best_path_by_mean_abs_Tmean_error": (
            min(path_summary, key=lambda row: float(row["mean_abs_Tmean_error_K"]))["path_id"] if path_summary else ""
        ),
        "radiation_policy": "forced_off_sensitivity_not_cfd_parity_after_AGENT_277_AGENT_287",
        "superseding_radiation_guidance": rel(
            REPO_ROOT
            / "work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/radiation_guidance_decision.json"
        ),
        "admission_decision": "no_admission_changes",
    }
    output_dir.joinpath("run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, metadata)
    return metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch-table", default=str(DEFAULT_PATCH_TABLE))
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--plan-only", action="store_true", help="Write contracts and run plan without invoking Fluid.")
    parser.add_argument("--strict", action="store_true", help="Fail on validation warnings.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    metadata = build_package(args)
    print(f"Wrote CFD BC no-radiation 1D parity package to {args.output_dir}")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
