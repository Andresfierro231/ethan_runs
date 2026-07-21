#!/usr/bin/env python3
"""Run CFD-informed fixed-mdot 1D thermal replays.

This AGENT-211 harness executes the fixed-mdot solver plan locally in
``ethan_runs`` without editing the externally owned Fluid solver.  It holds the
mass flow at the CFD observation value, solves thermal periodicity through
Fluid's read-only ``pressure_residual(...)`` helper, and reports the pressure
residual only as a diagnostic.  The output is therefore a thermal replay
package, not a predictive hydraulic score.
"""
from __future__ import annotations

import argparse
import csv
import importlib
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


DEFAULT_CONTRACT = REPO_ROOT / "work_products/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv"
DEFAULT_TARGETS = REPO_ROOT / "work_products/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv"
DEFAULT_OUTPUT = REPO_ROOT / "work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs"

CASE_NAME = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}

RUN_PLAN_COLUMNS = [
    "case_id",
    "source_id",
    "path_id",
    "description",
    "fixed_mdot_kg_s",
    "cfd_Tmean_K",
    "cfd_loop_delta_T_K",
    "thermal_input_policy",
    "hydraulic_policy",
    "score_partition",
    "modeling_status",
]

RESULT_COLUMNS = [
    "case_id",
    "source_id",
    "path_id",
    "description",
    "fixed_mdot_kg_s",
    "cfd_mdot_kg_s",
    "mdot_relative_error",
    "thermal_root_found",
    "temperature_root_bracketed",
    "temperature_root_reason",
    "temperature_periodicity_error_K",
    "model_Tmean_K",
    "cfd_Tmean_K",
    "Tmean_error_K",
    "model_loop_delta_T_K",
    "cfd_loop_delta_T_K",
    "loop_delta_T_error_K",
    "qhx_total_W",
    "qambient_total_W",
    "source_total_W",
    "prescribed_loss_total_W",
    "deltaP_buoyancy_Pa",
    "deltaP_losses_Pa",
    "pressure_residual_Pa",
    "pressure_residual_tolerance_Pa",
    "pressure_residual_margin_Pa",
    "pressure_root_policy",
    "reynolds_main",
    "velocity_main_m_s",
    "friction_factor_main",
    "predicted_air_outlet_temperature_K",
    "start_temperature_K",
    "end_temperature_K",
    "thermal_input_policy",
    "hydraulic_policy",
    "score_partition",
    "modeling_status",
]

SUMMARY_COLUMNS = [
    "path_id",
    "case_count",
    "mean_abs_Tmean_error_K",
    "max_abs_Tmean_error_K",
    "mean_abs_loop_delta_T_error_K",
    "max_abs_loop_delta_T_error_K",
    "mean_abs_pressure_residual_Pa",
    "max_abs_pressure_residual_Pa",
    "thermal_gate_pass",
    "pressure_is_diagnostic_not_gate",
    "interpretation",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_float(value: Any) -> float:
    if value in ("", None):
        return math.nan
    return float(value)


def rounded(value: Any, digits: int = 6) -> float | str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(number):
        return ""
    return round(number, digits)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: "" if row.get(col) is None else row.get(col, "") for col in columns})


def pressure_tolerance(S: Any, dp_buoyancy: float, dp_losses: float) -> float:
    abs_tol = float(getattr(S, "PRESSURE_RESIDUAL_ABS_TOL_PA", 0.25))
    rel_tol = float(getattr(S, "PRESSURE_RESIDUAL_REL_TOL", 0.05))
    return max(abs_tol, rel_tol * max(abs(dp_buoyancy), abs(dp_losses)))


def scenario_segments_for_solver(S: Any, segments: list[Any], case: Any, scenario: Any) -> list[Any]:
    """Mirror the non-test-section insulation rewrite in Fluid.solve_case()."""
    insulation_thickness_in = S.effective_insulation_thickness_in(case, scenario)
    scenario_segments = []
    for seg in segments:
        if seg.segment_type == "test_section":
            scenario_segments.append(seg)
            continue
        scenario_segments.append(
            S.Segment(
                name=seg.name,
                start_x_in=seg.start_x_in,
                start_y_in=seg.start_y_in,
                end_x_in=seg.end_x_in,
                end_y_in=seg.end_y_in,
                segment_type=seg.segment_type,
                notes=seg.notes,
                inner_diameter_in=seg.inner_diameter_in,
                outer_diameter_in=seg.outer_diameter_in,
                insulated=(insulation_thickness_in > 0.0),
                has_heater=seg.has_heater,
                has_test_section_heater=seg.has_test_section_heater,
                has_hx=seg.has_hx,
                wall_material=seg.wall_material,
                parent_name=seg.resolved_parent_name,
                parent_start_fraction=seg.parent_start_fraction,
                parent_end_fraction=seg.parent_end_fraction,
                refinement_level=seg.refinement_level,
            )
        )
    return scenario_segments


def import_fluid_cases() -> tuple[Any, Any, Any, dict[str, Any]]:
    S, build_geometry, default_geometry_refinement = deep.import_fluid()
    config_loader = importlib.import_module("tamu_loop_model_v2.config_loader")
    cases = {case.name: case for case in config_loader.load_cases()}
    return S, build_geometry, default_geometry_refinement, cases


def base_scenario(S: Any) -> Any:
    return S.ScenarioConfig(
        name="fixed_mdot_predictive_airside_ins_1.0in_rad_1",
        ambient_temperature_K=300.0,
        insulation_thickness_in=1.0,
        radiation_on=True,
        model_mode="predictive_airside_hx",
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=1.0e-5,
        mdot_search_upper_kg_s=0.2,
    )


def trial_plan_specs() -> list[dict[str, str]]:
    return [
        {
            "path_id": "P0_fixed_mdot_current_1d_contract",
            "description": "Current 1D thermal contract at CFD mdot.",
            "thermal_input_policy": "current Fluid salt contract: heater imposed duty plus 37 W test-section input; predictive air-side HX and internal ambient model",
            "modeling_status": "thermal_replay_baseline_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P1_cfd_cooler_duty_only",
            "description": "Replace predictive air-side HX duty with CFD cooler wallHeatFlux magnitude.",
            "thermal_input_policy": "current Fluid sources; replace predictive air-side HX with CFD cooler wallHeatFlux magnitude",
            "modeling_status": "thermal_replay_cfd_cooler_duty_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P2_heater_wallflux_no_test_source",
            "description": "Use heater interface wallHeatFlux and remove the 37 W 1D test-section source.",
            "thermal_input_policy": "use CFD heater interface wallHeatFlux as the only prescribed source; remove the legacy 37 W test-section input",
            "modeling_status": "thermal_replay_source_contract_probe_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P3_source_plus_test_section_sink",
            "description": "Use heater wallHeatFlux and treat the test section as a negative local source.",
            "thermal_input_policy": "compatibility probe: use CFD heater interface wallHeatFlux and encode net test-section wallHeatFlux as a negative source so current Fluid internal passive-loss models remain active",
            "modeling_status": "thermal_replay_source_and_quartz_sink_probe_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P4_cfd_cooler_plus_heater_wallflux",
            "description": "Combine CFD cooler wallHeatFlux with CFD heater interface wallHeatFlux.",
            "thermal_input_policy": "impose CFD cooler duty and CFD heater interface wallHeatFlux; omit the 37 W test-section source",
            "modeling_status": "thermal_replay_combined_cooler_source_probe_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P5_cfd_cooler_source_plus_test_sink",
            "description": "Combine CFD cooler duty, heater wallHeatFlux, and net test-section passive loss.",
            "thermal_input_policy": "preferred sign-convention probe: impose CFD cooler duty, heater wallHeatFlux as a source, and net test-section wallHeatFlux as a positive passive loss; current Fluid prescribed-loss semantics make other passive losses zero unless explicitly prescribed",
            "modeling_status": "thermal_replay_split_source_loss_contract_probe_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P6_full_patch_ledger_prescribed",
            "description": "Prescribe heater wallHeatFlux plus all CFD patchwise heat losses mapped to 1D parent segments.",
            "thermal_input_policy": "prescribe heater wallHeatFlux and all CFD cooler/passive/test/junction patch losses mapped to Fluid parent segments",
            "modeling_status": "fixed_Q_full_ledger_replay_mean_T_underanchored_without_temperature_dependent_boundary_network",
        },
    ]


def scenario_trials(S: Any, base: Any, terms: dict[str, float], case_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    heater_wall = terms["heater_wall_W"]
    test_sink = terms["test_section_loss_W"]
    cooler_loss = terms["cooler_loss_W"]
    full_losses = deep.loss_map_for_case(case_rows, {"cooler", "test_section", "ambient_wall", "junction_other"})
    return [
        {
            "path_id": "P0_fixed_mdot_current_1d_contract",
            "scenario": base,
            "sources": None,
            "losses": None,
            "thermal_input_policy": "current Fluid salt contract: heater imposed duty plus 37 W test-section input; predictive air-side HX and internal ambient model",
            "description": "Current 1D thermal contract at CFD mdot.",
            "modeling_status": "thermal_replay_baseline_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P1_cfd_cooler_duty_only",
            "scenario": replace(base, name="fixed_mdot_cfd_cooler_duty_only", model_mode="imposed_qhx", imposed_qhx_W=cooler_loss),
            "sources": None,
            "losses": None,
            "thermal_input_policy": "current Fluid sources; replace predictive air-side HX with CFD cooler wallHeatFlux magnitude",
            "description": "Replace predictive air-side HX duty with CFD cooler wallHeatFlux magnitude.",
            "modeling_status": "thermal_replay_cfd_cooler_duty_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P2_heater_wallflux_no_test_source",
            "scenario": base,
            "sources": {"heated_incline": heater_wall},
            "losses": None,
            "thermal_input_policy": "use CFD heater interface wallHeatFlux as the only prescribed source; remove the legacy 37 W test-section input",
            "description": "Use heater interface wallHeatFlux and remove the 37 W 1D test-section source.",
            "modeling_status": "thermal_replay_source_contract_probe_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P3_source_plus_test_section_sink",
            "scenario": base,
            "sources": {"heated_incline": heater_wall, "test_section": -test_sink},
            "losses": None,
            "thermal_input_policy": "compatibility probe: use CFD heater interface wallHeatFlux and encode net test-section wallHeatFlux as a negative source so current Fluid internal passive-loss models remain active",
            "description": "Use heater wallHeatFlux and treat the test section as a negative local source.",
            "modeling_status": "thermal_replay_source_and_quartz_sink_probe_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P4_cfd_cooler_plus_heater_wallflux",
            "scenario": replace(base, name="fixed_mdot_cfd_cooler_plus_heater_wallflux", model_mode="imposed_qhx", imposed_qhx_W=cooler_loss),
            "sources": {"heated_incline": heater_wall},
            "losses": None,
            "thermal_input_policy": "impose CFD cooler duty and CFD heater interface wallHeatFlux; omit the 37 W test-section source",
            "description": "Combine CFD cooler wallHeatFlux with CFD heater interface wallHeatFlux.",
            "modeling_status": "thermal_replay_combined_cooler_source_probe_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P5_cfd_cooler_source_plus_test_sink",
            "scenario": replace(base, name="fixed_mdot_cfd_cooler_source_plus_test_sink", model_mode="imposed_qhx", imposed_qhx_W=cooler_loss),
            "sources": {"heated_incline": heater_wall},
            "losses": {"test_section": test_sink},
            "thermal_input_policy": "preferred sign-convention probe: impose CFD cooler duty, heater wallHeatFlux as a source, and net test-section wallHeatFlux as a positive passive loss; current Fluid prescribed-loss semantics make other passive losses zero unless explicitly prescribed",
            "description": "Combine CFD cooler duty, heater wallHeatFlux, and net test-section passive loss.",
            "modeling_status": "thermal_replay_split_source_loss_contract_probe_not_predictive_hydraulic_score",
        },
        {
            "path_id": "P6_full_patch_ledger_prescribed",
            "scenario": replace(base, name="fixed_mdot_full_patch_ledger_prescribed", model_mode="imposed_qhx", imposed_qhx_W=0.0),
            "sources": {"heated_incline": heater_wall},
            "losses": full_losses,
            "thermal_input_policy": "prescribe heater wallHeatFlux and all CFD cooler/passive/test/junction patch losses mapped to Fluid parent segments",
            "description": "Prescribe heater wallHeatFlux plus all CFD patchwise heat losses mapped to 1D parent segments.",
            "modeling_status": "fixed_Q_full_ledger_replay_mean_T_underanchored_without_temperature_dependent_boundary_network",
        },
    ]


def build_run_plan(targets: list[dict[str, str]], contract_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        for trial in trial_plan_specs():
            rows.append(
                {
                    "case_id": target["case_id"],
                    "source_id": target["source_id"],
                    "path_id": trial["path_id"],
                    "description": trial["description"],
                    "fixed_mdot_kg_s": target["cfd_mdot_kg_s"],
                    "cfd_Tmean_K": target["cfd_Tmean_K"],
                    "cfd_loop_delta_T_K": target["cfd_loop_delta_T_K"],
                    "thermal_input_policy": trial["thermal_input_policy"],
                    "hydraulic_policy": "hold mdot at CFD observation; do not perform pressure root search",
                    "score_partition": "thermal_periodicity_and_temperature_error_only; pressure_residual_diagnostic",
                    "modeling_status": trial["modeling_status"],
                }
            )
    return rows


def run_fixed_mdot_cases(targets: list[dict[str, str]], contract_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    S, build_geometry, default_geometry_refinement, cases = import_fluid_cases()
    base = base_scenario(S)
    segments, sensors = build_geometry(refinement=default_geometry_refinement())
    grouped = deep.group_contract(contract_rows)
    terms_by_case = deep.aggregate_terms(contract_rows)
    results: list[dict[str, Any]] = []

    for target in targets:
        case_id = target["case_id"]
        case = cases[CASE_NAME[case_id]]
        mdot = safe_float(target["cfd_mdot_kg_s"])
        cfd_tmean = safe_float(target["cfd_Tmean_K"])
        cfd_dt = safe_float(target["cfd_loop_delta_T_K"])
        trials = scenario_trials(S, base, terms_by_case[case_id], grouped[case_id])
        for trial in trials:
            scenario = trial["scenario"]
            scenario_segments = scenario_segments_for_solver(S, segments, case, scenario)
            snapshot = S.pressure_residual(
                mdot,
                case,
                scenario_segments,
                sensors,
                scenario,
                S.MinorLosses(),
                warm_start_temperature_K=None,
                prescribed_segment_sources_W=trial["sources"],
                prescribed_segment_losses_W=trial["losses"],
            )
            thermal = snapshot["thermal"]
            tmean = deep.length_weighted_mean(thermal.segment_states)
            dt = deep.loop_delta(thermal.segment_states)
            dp_b = float(snapshot["deltaP_buoyancy_Pa"])
            dp_l = float(snapshot["deltaP_losses_Pa"])
            residual = float(snapshot["pressure_residual_Pa"])
            tol = pressure_tolerance(S, dp_b, dp_l)
            source_total = (
                sum(float(v) for v in trial["sources"].values())
                if trial["sources"] is not None
                else case.heater_power_W + case.test_section_power_W
            )
            loss_total = sum(float(v) for v in trial["losses"].values()) if trial["losses"] is not None else 0.0
            results.append(
                {
                    "case_id": case_id,
                    "source_id": target["source_id"],
                    "path_id": trial["path_id"],
                    "description": trial["description"],
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
                    "thermal_input_policy": trial["thermal_input_policy"],
                    "hydraulic_policy": "hold mdot at CFD observation; do not perform pressure root search",
                    "score_partition": "thermal_periodicity_and_temperature_error_only; pressure_residual_diagnostic",
                    "modeling_status": trial["modeling_status"],
                }
            )
    return results


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
            }
        )
    return sorted(summaries, key=lambda row: str(row["path_id"]))


def interpretation_for_path(path_id: str) -> str:
    return {
        "P0_fixed_mdot_current_1d_contract": "Baseline replay; isolates thermal state from pressure-root mdot changes.",
        "P1_cfd_cooler_duty_only": "Tests whether the cooling-jacket duty magnitude is the dominant missing sink.",
        "P2_heater_wallflux_no_test_source": "Tests source-contract mismatch without changing the cooler model.",
        "P3_source_plus_test_section_sink": "Tests heater wallHeatFlux plus quartz/test-section net sink while retaining internal boundary models.",
        "P4_cfd_cooler_plus_heater_wallflux": "Combines the largest cooler correction with heater-interface heat transfer.",
        "P5_cfd_cooler_source_plus_test_sink": "Uses the preferred source/loss sign convention for the heater and quartz terms, with the caveat that current Fluid prescribed-loss semantics zero unlisted passive losses.",
        "P6_full_patch_ledger_prescribed": "Full fixed-Q patch ledger replay; useful for loop delta T, but absolute mean T is under-anchored without temperature-dependent external boundary reconstruction.",
    }[path_id]


def write_method_note(output_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# CFD-Informed Fixed-mdot 1D Replay Run Package",
        "",
        f"Generated: `{summary['generated_utc']}`",
        "Task: `AGENT-211`",
        "",
        "## Purpose",
        "",
        "These runs execute the fixed-mdot thermal replay proposed by `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_solver_plan.md` while avoiding edits to the externally owned Fluid solver. The goal is to separate thermal boundary-condition replay from predictive hydraulic scoring: the Salt CFD mdot is imposed, thermal periodicity is solved, and the pressure residual is reported but not used to move mdot.",
        "",
        "## Solver Contract",
        "",
        "- 1D solver source: read-only `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`.",
        "- Thermal root: `solve_temperature_periodicity(...)`, called through `pressure_residual(...)`.",
        "- Hydraulic state: `fixed_mdot_kg_s = cfd_mdot_kg_s` from `case_thermal_targets.csv`.",
        "- Pressure diagnostic: `pressure_residual_Pa = deltaP_losses_Pa - deltaP_buoyancy_Pa`; no pressure-root search is performed.",
        "- Geometry: Fluid default refined geometry with the same non-test-section insulation rewrite used in `solve_case()`.",
        "- Minor losses: default `MinorLosses()`; no CFD minor-loss closure is injected in this thermal replay package.",
        "- Radiation: Fluid external radiation switch remains on for internal boundary-model paths, but CFD `qr` is not prescribed because the patchwise ledger reports no exported `qr` field.",
        "",
        "## Scenario Matrix",
        "",
        "`run_plan.csv` contains seven thermal-input paths for Salt 2/3/4. Paths P0-P4 retain temperature-dependent 1D passive loss models except where a CFD cooler duty is imposed. P5 uses the preferred split source/loss sign convention for the quartz test-section sink, but current Fluid prescribed-loss semantics zero unlisted passive losses once a loss map is supplied. P6 prescribes the full patchwise ledger as fixed heat rates; it is a diagnostic energy replay rather than a predictive external-boundary model because fixed-Q losses cannot anchor absolute mean temperature without a temperature-dependent resistance network.",
        "",
        "## Output Files",
        "",
        "- `run_plan.csv`: cases and thermal-input policies submitted to the background run.",
        "- `fixed_mdot_pressure_replay_results.csv`: per-case replay outputs with thermal errors and diagnostic pressure residuals.",
        "- `path_summary.csv`: aggregate thermal and pressure-residual diagnostics by path.",
        "- `run_metadata.json`: command, host, Python, Fluid source, and input provenance.",
        "",
        "## Interpretation Boundary",
        "",
        "These rows are eligible for thermal-state diagnosis and model-form design, not for mdot predictivity claims. A later Fluid-owned implementation of `fixed_mdot_kg_s` in `ScenarioConfig` should reproduce the thermal values here and add first-class result metadata so reporting layers cannot mix fixed-mdot replay scores with predictive hydraulic scores.",
    ]
    output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    contract_rows = deep.read_csv(Path(args.contract))
    target_rows = deep.read_csv(Path(args.targets))
    run_plan = build_run_plan(target_rows, contract_rows)
    write_csv(output_dir / "run_plan.csv", run_plan, RUN_PLAN_COLUMNS)

    results: list[dict[str, Any]] = []
    path_summary: list[dict[str, Any]] = []
    if not args.plan_only:
        results = run_fixed_mdot_cases(target_rows, contract_rows)
        path_summary = summarize_results(results)
        write_csv(output_dir / "fixed_mdot_pressure_replay_results.csv", results, RESULT_COLUMNS)
        write_csv(output_dir / "path_summary.csv", path_summary, SUMMARY_COLUMNS)

    metadata = {
        "generated_utc": utc_now(),
        "task": "AGENT-211",
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""),
        "slurm_step_id": os.environ.get("SLURM_STEP_ID", ""),
        "cwd": str(Path.cwd()),
        "command": " ".join(sys.argv),
        "contract": str(Path(args.contract)),
        "targets": str(Path(args.targets)),
        "fluid_root": str(deep.FLUID_ROOT),
        "ethan_runs_git_revision": git_revision(REPO_ROOT),
        "fluid_git_revision": git_revision(deep.FLUID_ROOT),
        "run_plan_rows": len(run_plan),
        "result_rows": len(results),
        "path_summary_rows": len(path_summary),
        "best_path_by_mean_abs_Tmean_error": (
            min(path_summary, key=lambda row: float(row["mean_abs_Tmean_error_K"]))["path_id"] if path_summary else ""
        ),
        "pressure_policy": "diagnostic_only_not_rooted",
    }
    output_dir.joinpath("run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_method_note(output_dir, metadata)
    return metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--plan-only", action="store_true", help="Write run_plan.csv and metadata without invoking Fluid solves.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_package(args)
    print(f"Wrote CFD-informed fixed-mdot replay package to {args.output_dir}")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
