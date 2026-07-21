#!/usr/bin/env python3
"""Build and run patch-boundary fixed-mdot 1D thermal parity diagnostics.

AGENT-271 consumes the AGENT-263 patch/segment boundary table and the
AGENT-264 rcExternalTemperature audit. It keeps the external Fluid solver
read-only, runs only fixed-Q modes expressible through the current Fluid API,
and writes the h/Ta/Tsur/emissivity external-boundary equivalent as a documented
contract gap.
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


TASK_ID = "AGENT-271"
DEFAULT_PATCH_TABLE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)
DEFAULT_SEGMENTS = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/segment_reduction_inputs.csv"
)
DEFAULT_RADIATION = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_implementation_audit/radiation_parity_decision.json"
)
DEFAULT_TARGETS = (
    REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv"
)
DEFAULT_OUTPUT = (
    REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity"
)

SEGMENT_TO_FLUID_PARENT = {
    "lower_leg": "heated_incline",
    "upcomer": "left_upper_vertical",
    "downcomer": "right_vertical",
    "cooling_branch": "cooled_incline_hx_active",
    "junction": "top_horizontal_exit",
}

RUN_PLAN_COLUMNS = [
    "case_id",
    "source_id",
    "path_id",
    "description",
    "fixed_mdot_kg_s",
    "executable_with_current_fluid_api",
    "thermal_input_policy",
    "radiation_policy",
    "hydraulic_policy",
    "score_partition",
    "modeling_status",
]

CONTRACT_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "fluid_parent_segment",
    "component_parent_spans",
    "patch_count",
    "area_m2",
    "realized_wallHeatFlux_W",
    "realized_source_W",
    "realized_loss_W",
    "imposed_Q_W",
    "imposed_source_W",
    "imposed_loss_W",
    "area_weighted_h_W_m2K",
    "area_weighted_Ta_K",
    "area_weighted_Tsur_K",
    "area_weighted_emissivity",
    "mapping_status",
    "interface_registry_status",
    "radiation_parity_mode",
    "external_bc_equivalent_status",
]

SECTION_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "fluid_parent_segment",
    "role",
    "patch_count",
    "area_m2",
    "realized_wallHeatFlux_W",
    "realized_source_W",
    "realized_loss_W",
    "imposed_Q_W",
    "imposed_source_W",
    "imposed_loss_W",
    "bc_types",
    "wall_layer_metadata_statuses",
    "radiation_metadata_statuses",
]

RESULT_COLUMNS = legacy.RESULT_COLUMNS + [
    "executable_with_current_fluid_api",
    "radiation_policy",
    "source_map_json",
    "loss_map_json",
]

SUMMARY_COLUMNS = legacy.SUMMARY_COLUMNS + [
    "executable_with_current_fluid_api",
    "radiation_policy",
]

DECISION_COLUMNS = [
    "decision_id",
    "value",
    "basis",
    "parity_instruction",
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


def load_radiation_decision(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def build_parity_contract(
    segment_rows: list[dict[str, str]],
    radiation: dict[str, Any],
) -> list[dict[str, Any]]:
    mode = str(radiation.get("parity_radiation_mode", ""))
    rows: list[dict[str, Any]] = []
    for row in segment_rows:
        realized = fnum(row.get("realized_wallHeatFlux_W"))
        imposed = fnum(row.get("imposed_Q_W"))
        segment = row["one_d_segment"]
        rows.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "one_d_segment": segment,
                "fluid_parent_segment": SEGMENT_TO_FLUID_PARENT.get(segment, ""),
                "component_parent_spans": row.get("component_parent_spans", ""),
                "patch_count": row.get("patch_count", ""),
                "area_m2": row.get("area_m2", ""),
                "realized_wallHeatFlux_W": rounded(realized, 9),
                "realized_source_W": rounded(max(realized, 0.0), 9),
                "realized_loss_W": rounded(max(-realized, 0.0), 9),
                "imposed_Q_W": rounded(imposed, 9),
                "imposed_source_W": rounded(max(imposed, 0.0), 9),
                "imposed_loss_W": rounded(max(-imposed, 0.0), 9),
                "area_weighted_h_W_m2K": row.get("area_weighted_h_W_m2K", ""),
                "area_weighted_Ta_K": row.get("area_weighted_Ta_K", ""),
                "area_weighted_Tsur_K": row.get("area_weighted_Tsur_K", ""),
                "area_weighted_emissivity": row.get("area_weighted_emissivity", ""),
                "mapping_status": row.get("mapping_status", ""),
                "interface_registry_status": row.get("interface_registry_status", ""),
                "radiation_parity_mode": mode,
                "external_bc_equivalent_status": (
                    "contract_only_current_fluid_api_has_no_patch_h_Ta_Tsur_emissivity_external_bc_injection"
                ),
            }
        )
    return rows


def build_section_heat_balance(patch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for row in patch_rows:
        segment = row.get("one_d_segment", "")
        if not segment:
            continue
        key = (row["source_id"], row["case_id"], segment, row.get("role", ""))
        grouped.setdefault(key, []).append(row)

    out: list[dict[str, Any]] = []
    for (source_id, case_id, segment, role), rows in sorted(grouped.items()):
        realized = sum(fnum(row.get("realized_wallHeatFlux_W")) for row in rows)
        imposed = sum(fnum(row.get("imposed_Q_W")) for row in rows)
        out.append(
            {
                "source_id": source_id,
                "case_id": case_id,
                "one_d_segment": segment,
                "fluid_parent_segment": SEGMENT_TO_FLUID_PARENT.get(segment, ""),
                "role": role,
                "patch_count": len(rows),
                "area_m2": rounded(sum(fnum(row.get("area_m2")) for row in rows), 9),
                "realized_wallHeatFlux_W": rounded(realized, 9),
                "realized_source_W": rounded(max(realized, 0.0), 9),
                "realized_loss_W": rounded(max(-realized, 0.0), 9),
                "imposed_Q_W": rounded(imposed, 9),
                "imposed_source_W": rounded(max(imposed, 0.0), 9),
                "imposed_loss_W": rounded(max(-imposed, 0.0), 9),
                "bc_types": ";".join(sorted({row.get("bc_type", "") for row in rows if row.get("bc_type")})),
                "wall_layer_metadata_statuses": ";".join(
                    sorted({row.get("wall_layer_metadata_status", "") for row in rows if row.get("wall_layer_metadata_status")})
                ),
                "radiation_metadata_statuses": ";".join(
                    sorted({row.get("radiation_metadata_status", "") for row in rows if row.get("radiation_metadata_status")})
                ),
            }
        )
    return out


def map_by_case(contract_rows: list[dict[str, Any]], column: str) -> dict[str, dict[str, float]]:
    mapped: dict[str, dict[str, float]] = {}
    for row in contract_rows:
        parent = str(row["fluid_parent_segment"])
        if not parent:
            continue
        value = fnum(row.get(column))
        if value <= 0.0:
            continue
        mapped.setdefault(str(row["case_id"]), {})
        mapped[str(row["case_id"])][parent] = mapped[str(row["case_id"])].get(parent, 0.0) + value
    return mapped


def cooler_loss_by_case(section_rows: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in section_rows:
        if row["role"] == "cooler":
            out[str(row["case_id"])] = fnum(row.get("realized_loss_W"))
    return out


def trial_specs() -> list[dict[str, str]]:
    return [
        {
            "path_id": "B0_current_fluid_baseline",
            "description": "Current Fluid salt thermal contract at CFD mdot.",
            "executable": "yes",
            "thermal_input_policy": "current Fluid heater/test-section source and predictive air-side HX/ambient models",
            "modeling_status": "reference_only_not_boundary_parity",
        },
        {
            "path_id": "B1_legacy_cfd_cooler_duty",
            "description": "Legacy best replay: replace predictive HX with CFD realized cooler duty.",
            "executable": "yes",
            "thermal_input_policy": "current Fluid sources; impose AGENT-263 realized cooling-branch loss as qhx duty",
            "modeling_status": "legacy_context_cfd_cooler_duty_not_predictive",
        },
        {
            "path_id": "B2_realized_wallflux_roles",
            "description": "Prescribe AGENT-263 realized wallHeatFlux sources and losses by mapped 1D segment.",
            "executable": "yes",
            "thermal_input_policy": "fixed-Q replay using realized wallHeatFlux; positive heat as source and negative heat as segment loss",
            "modeling_status": "executable_fixed_Q_patch_boundary_parity_diagnostic",
        },
        {
            "path_id": "B3_imposed_setup_roles",
            "description": "Prescribe AGENT-263 imposed setup heat terms by mapped 1D segment.",
            "executable": "yes",
            "thermal_input_policy": "fixed-Q replay using imposed Q entries; exposes setup-vs-realized discrepancy",
            "modeling_status": "executable_fixed_Q_setup_contract_diagnostic",
        },
        {
            "path_id": "B4_external_bc_equivalent_contract",
            "description": "h/Ta/Tsur/emissivity/layer external-boundary equivalent contract.",
            "executable": "no",
            "thermal_input_policy": "contract only: current repo-local Fluid API does not accept patch-level h/Ta/Tsur/emissivity external BC injection",
            "modeling_status": "nonexecutable_api_gap_for_temperature_dependent_external_bc_parity",
        },
    ]


def build_run_plan(targets: list[dict[str, str]], radiation: dict[str, Any]) -> list[dict[str, Any]]:
    policy = str(radiation.get("one_d_parity_instruction", ""))
    rows: list[dict[str, Any]] = []
    for target in targets:
        for spec in trial_specs():
            rows.append(
                {
                    "case_id": target["case_id"],
                    "source_id": target["source_id"],
                    "path_id": spec["path_id"],
                    "description": spec["description"],
                    "fixed_mdot_kg_s": target["cfd_mdot_kg_s"],
                    "executable_with_current_fluid_api": spec["executable"],
                    "thermal_input_policy": spec["thermal_input_policy"],
                    "radiation_policy": policy,
                    "hydraulic_policy": "hold mdot at CFD observation; do not perform pressure root search",
                    "score_partition": "thermal_periodicity_and_temperature_error_only; pressure_residual_diagnostic",
                    "modeling_status": spec["modeling_status"],
                }
            )
    return rows


def run_fixed_mdot_parity(
    targets: list[dict[str, str]],
    contract_rows: list[dict[str, Any]],
    section_rows: list[dict[str, Any]],
    radiation: dict[str, Any],
) -> list[dict[str, Any]]:
    S, build_geometry, default_geometry_refinement, cases = legacy.import_fluid_cases()
    base = legacy.base_scenario(S)
    segments, sensors = build_geometry(refinement=default_geometry_refinement())
    realized_sources = map_by_case(contract_rows, "realized_source_W")
    realized_losses = map_by_case(contract_rows, "realized_loss_W")
    imposed_sources = map_by_case(contract_rows, "imposed_source_W")
    imposed_losses = map_by_case(contract_rows, "imposed_loss_W")
    cooler_losses = cooler_loss_by_case(section_rows)
    radiation_policy = str(radiation.get("one_d_parity_instruction", ""))
    results: list[dict[str, Any]] = []

    for target in targets:
        case_id = target["case_id"]
        case = cases[legacy.CASE_NAME[case_id]]
        mdot = legacy.safe_float(target["cfd_mdot_kg_s"])
        cfd_tmean = legacy.safe_float(target["cfd_Tmean_K"])
        cfd_dt = legacy.safe_float(target["cfd_loop_delta_T_K"])
        trials = [
            ("B0_current_fluid_baseline", base, None, None),
            (
                "B1_legacy_cfd_cooler_duty",
                replace(
                    base,
                    name="patch_boundary_legacy_cfd_cooler_duty",
                    model_mode="imposed_qhx",
                    imposed_qhx_W=cooler_losses[case_id],
                ),
                None,
                None,
            ),
            (
                "B2_realized_wallflux_roles",
                replace(base, name="patch_boundary_realized_wallflux_roles", model_mode="imposed_qhx", imposed_qhx_W=0.0),
                realized_sources.get(case_id, {}),
                realized_losses.get(case_id, {}),
            ),
            (
                "B3_imposed_setup_roles",
                replace(base, name="patch_boundary_imposed_setup_roles", model_mode="imposed_qhx", imposed_qhx_W=0.0),
                imposed_sources.get(case_id, {}),
                imposed_losses.get(case_id, {}),
            ),
        ]
        specs = {spec["path_id"]: spec for spec in trial_specs()}
        for path_id, scenario, sources, losses in trials:
            scenario_segments = legacy.scenario_segments_for_solver(S, segments, case, scenario)
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
            thermal = snapshot["thermal"]
            tmean = deep.length_weighted_mean(thermal.segment_states)
            dt = deep.loop_delta(thermal.segment_states)
            dp_b = float(snapshot["deltaP_buoyancy_Pa"])
            dp_l = float(snapshot["deltaP_losses_Pa"])
            residual = float(snapshot["pressure_residual_Pa"])
            tol = legacy.pressure_tolerance(S, dp_b, dp_l)
            source_total = (
                sum(float(value) for value in sources.values()) if sources is not None else case.heater_power_W + case.test_section_power_W
            )
            loss_total = sum(float(value) for value in losses.values()) if losses is not None else 0.0
            spec = specs[path_id]
            results.append(
                {
                    "case_id": case_id,
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
                    "prescribed_loss_total_W": rounded(loss_total, 6),
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
                    "score_partition": "thermal_periodicity_and_temperature_error_only; pressure_residual_diagnostic",
                    "modeling_status": spec["modeling_status"],
                    "executable_with_current_fluid_api": "yes",
                    "radiation_policy": radiation_policy,
                    "source_map_json": json.dumps(sources or {}, sort_keys=True),
                    "loss_map_json": json.dumps(losses or {}, sort_keys=True),
                }
            )
    return results


def summarize_results(rows: list[dict[str, Any]], radiation: dict[str, Any]) -> list[dict[str, Any]]:
    policy = str(radiation.get("one_d_parity_instruction", ""))
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
                "executable_with_current_fluid_api": "yes",
                "radiation_policy": policy,
            }
        )
    return sorted(summaries, key=lambda row: str(row["path_id"]))


def interpretation_for_path(path_id: str) -> str:
    return {
        "B0_current_fluid_baseline": "Reference current Fluid contract at CFD mdot; not boundary parity.",
        "B1_legacy_cfd_cooler_duty": "Legacy context path that isolates the realized cooler duty as the dominant first-order sink.",
        "B2_realized_wallflux_roles": "Fixed-Q replay of AGENT-263 realized segment heat fluxes; radiation is embedded in wallHeatFlux.",
        "B3_imposed_setup_roles": "Fixed-Q replay of imposed setup terms; exposes setup-vs-realized heat mismatch.",
    }[path_id]


def build_decision_rows(radiation: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "emissivity_Tsur_affect_heat_flux",
            "value": radiation.get("emissivity_Tsur_affect_heat_flux", ""),
            "basis": radiation.get("effect_basis", ""),
            "parity_instruction": radiation.get("one_d_parity_instruction", ""),
        },
        {
            "decision_id": "separable_radiation_output_available",
            "value": radiation.get("separable_radiation_output_available", ""),
            "basis": radiation.get("source_formula_status", ""),
            "parity_instruction": "do_not_add_separate_radiation_to_realized_wallHeatFlux_fixed_Q_replay",
        },
        {
            "decision_id": "external_bc_equivalent_mode",
            "value": "contract_only_until_Fluid_accepts_patch_or_segment_h_Ta_Tsur_emissivity",
            "basis": "current AGENT-271 scope keeps external Fluid read-only and current replay API accepts fixed sources/losses, not patch external-BC dictionaries",
            "parity_instruction": "future Fluid-owned task must implement combined convection/radiation equivalent without double-counting fixed wallHeatFlux radiation",
        },
    ]


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
    text = f"""# Patch-Boundary Fixed-mdot 1D Parity

Generated: `{metadata['generated_utc']}`
Task: `{TASK_ID}`

## Purpose

This package converts the AGENT-263 CFD patch boundary ledger into 1D segment
inputs and applies the AGENT-264 rcExternalTemperature radiation decision. It
keeps the external Fluid solver read-only. Executed modes are fixed-Q thermal
diagnostics at CFD mdot, not predictive hydraulic scores.

## Outputs

- `parity_input_contract.csv`: CFD segment-to-Fluid mapping with realized and imposed heat terms plus h/Ta/Tsur/emissivity metadata.
- `section_heat_balance.csv`: role-level patch sums by 1D segment.
- `run_plan.csv`: executable and non-executable parity modes.
- `fixed_mdot_parity_results.csv`: executed fixed-mdot results for B0-B3.
- `path_summary.csv`: thermal error and diagnostic pressure residuals by path.
- `parity_decision_table.csv`: radiation and external-BC implementation decisions.
- `run_metadata.json`: input paths, command, host, git revisions, and row counts.

## Scientific Boundary

Positive `realized_wallHeatFlux_W` means heat enters the fluid; negative means
heat leaves the fluid. The B2 realized-wallHeatFlux mode therefore treats
positive segment sums as prescribed sources and negative segment sums as
prescribed losses. AGENT-264 concluded that `rcExternalTemperature` emissivity
and `Tsur` affect heat flux, but no separable radiation ledger is exported.
Therefore this package does not add a separate 1D radiation term on top of CFD
wallHeatFlux.

`B4_external_bc_equivalent_contract` is intentionally not executed. The current
repo-local Fluid API can prescribe segment sources/losses, but does not accept
patch-level or segment-level h/Ta/Tsur/emissivity/layer boundary dictionaries.
A later Fluid-owned task should implement that combined external boundary if
temperature-dependent parity is required.

## Key Counts

- Contract rows: `{metadata['parity_contract_rows']}`
- Section heat-balance rows: `{metadata['section_heat_balance_rows']}`
- Run-plan rows: `{metadata['run_plan_rows']}`
- Result rows: `{metadata['result_rows']}`
- Best executed path by mean absolute Tmean error: `{metadata['best_path_by_mean_abs_Tmean_error']}`
"""
    output_dir.joinpath("README.md").write_text(text, encoding="utf-8")


def validate_inputs(
    patch_rows: list[dict[str, str]],
    segment_rows: list[dict[str, str]],
    radiation: dict[str, Any],
    targets: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    if len(segment_rows) != 15:
        errors.append(f"expected 15 AGENT-263 segment rows, found {len(segment_rows)}")
    if len(patch_rows) != 207:
        errors.append(f"expected 207 AGENT-263 patch rows, found {len(patch_rows)}")
    if len(targets) != 3:
        errors.append(f"expected 3 Salt target rows, found {len(targets)}")
    if radiation.get("parity_radiation_mode") != "inseparable":
        errors.append(f"expected AGENT-264 parity_radiation_mode=inseparable, found {radiation.get('parity_radiation_mode')!r}")
    target_cases = {row.get("case_id", "") for row in targets}
    segment_cases = {row.get("case_id", "") for row in segment_rows}
    if target_cases != {"salt_2", "salt_3", "salt_4"}:
        errors.append(f"unexpected target cases {sorted(target_cases)}")
    if segment_cases != target_cases:
        errors.append(f"segment cases {sorted(segment_cases)} do not match target cases {sorted(target_cases)}")
    missing_parent = sorted({row.get("one_d_segment", "") for row in segment_rows if row.get("one_d_segment", "") not in SEGMENT_TO_FLUID_PARENT})
    if missing_parent:
        errors.append(f"missing Fluid parent mapping for segments {missing_parent}")
    return errors


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    patch_rows = read_csv(Path(args.patch_table))
    segment_rows = read_csv(Path(args.segment_inputs))
    radiation = load_radiation_decision(Path(args.radiation_decision))
    targets = read_csv(Path(args.targets))
    validation_errors = validate_inputs(patch_rows, segment_rows, radiation, targets)
    if validation_errors and args.strict:
        raise ValueError("; ".join(validation_errors))

    parity_contract = build_parity_contract(segment_rows, radiation)
    section_balance = build_section_heat_balance(patch_rows)
    run_plan = build_run_plan(targets, radiation)
    decisions = build_decision_rows(radiation)

    write_csv(output_dir / "parity_input_contract.csv", parity_contract, CONTRACT_COLUMNS)
    write_csv(output_dir / "section_heat_balance.csv", section_balance, SECTION_COLUMNS)
    write_csv(output_dir / "run_plan.csv", run_plan, RUN_PLAN_COLUMNS)
    write_csv(output_dir / "parity_decision_table.csv", decisions, DECISION_COLUMNS)

    results: list[dict[str, Any]] = []
    path_summary: list[dict[str, Any]] = []
    if not args.plan_only:
        results = run_fixed_mdot_parity(targets, parity_contract, section_balance, radiation)
        path_summary = summarize_results(results, radiation)
        write_csv(output_dir / "fixed_mdot_parity_results.csv", results, RESULT_COLUMNS)
        write_csv(output_dir / "path_summary.csv", path_summary, SUMMARY_COLUMNS)

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
        "segment_inputs": rel(Path(args.segment_inputs)),
        "radiation_decision": rel(Path(args.radiation_decision)),
        "targets": rel(Path(args.targets)),
        "fluid_root": str(deep.FLUID_ROOT),
        "ethan_runs_git_revision": git_revision(REPO_ROOT),
        "fluid_git_revision": git_revision(deep.FLUID_ROOT),
        "validation_errors": validation_errors,
        "parity_contract_rows": len(parity_contract),
        "section_heat_balance_rows": len(section_balance),
        "run_plan_rows": len(run_plan),
        "result_rows": len(results),
        "path_summary_rows": len(path_summary),
        "best_path_by_mean_abs_Tmean_error": (
            min(path_summary, key=lambda row: float(row["mean_abs_Tmean_error_K"]))["path_id"] if path_summary else ""
        ),
        "radiation_parity_mode": radiation.get("parity_radiation_mode", ""),
        "external_bc_equivalent_status": "contract_only_current_fluid_api_gap",
    }
    output_dir.joinpath("run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, metadata)
    return metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch-table", default=str(DEFAULT_PATCH_TABLE))
    parser.add_argument("--segment-inputs", default=str(DEFAULT_SEGMENTS))
    parser.add_argument("--radiation-decision", default=str(DEFAULT_RADIATION))
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--plan-only", action="store_true", help="Write contracts and run plan without importing Fluid.")
    parser.add_argument("--strict", action="store_true", help="Fail on validation warnings instead of recording them.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    metadata = build_package(args)
    print(f"Wrote patch-boundary fixed-mdot parity package to {args.output_dir}")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
