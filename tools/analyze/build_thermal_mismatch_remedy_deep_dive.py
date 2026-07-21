#!/usr/bin/env python3
"""Quantify four thermal-mismatch remedy paths against the July 8 contracts."""
from __future__ import annotations

import argparse
import csv
import importlib
import json
import math
import sys
import types
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = REPO_ROOT.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid"
DEFAULT_CONTRACT = REPO_ROOT / "work_products/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv"
DEFAULT_TARGETS = REPO_ROOT / "work_products/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv"
DEFAULT_OUTPUT = REPO_ROOT / "work_products/2026-07-08_thermal_mismatch_remedy_deep_dive"

CASE_NAME = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}
SOURCE_TO_CASE = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "salt_2",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "salt_3",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "salt_4",
}

FLUID_PARENT_BY_SPAN = {
    "lower_leg": "heated_incline",
    "upcomer": "left_upper_vertical",
    "downcomer": "right_vertical",
    "cooling_branch": "cooled_incline_hx_active",
    "junction": "top_horizontal_exit",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: csv_value(row.get(col, "")) for col in columns})


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return value


def fnum(value: Any) -> float:
    if value in ("", None):
        return math.nan
    return float(value)


def r3(value: float) -> float | str:
    if not math.isfinite(value):
        return ""
    return round(value, 3)


def length_weighted_mean(segment_states: list[Any]) -> float:
    total_l = 0.0
    total_tl = 0.0
    for state in segment_states:
        length = float(state.s_end_m) - float(state.s_start_m)
        total_l += length
        total_tl += float(state.T_avg_K) * length
    return total_tl / total_l


def loop_delta(segment_states: list[Any]) -> float:
    values = [float(state.T_avg_K) for state in segment_states]
    return max(values) - min(values)


def group_contract(contract_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in contract_rows:
        grouped.setdefault(row["case_id"], []).append(row)
    return grouped


def build_heater_values(contract_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in contract_rows:
        if row["patch_group"] != "heater":
            continue
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "heater_imposed_duty_W": r3(fnum(row["heater_imposed_duty_W"])),
                "heater_wallHeatFlux_input_W": r3(fnum(row["wallHeatFlux_integral_W"])),
                "imposed_minus_wallHeatFlux_W": r3(fnum(row["imposed_Q_minus_wallHeatFlux_W"])),
                "patch_names": row["patch_names"],
                "bc_type": row["bc_type"],
            }
        )
    return sorted(rows, key=lambda item: item["case_id"])


def aggregate_terms(contract_rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    terms: dict[str, dict[str, float]] = {}
    for case_id, rows in group_contract(contract_rows).items():
        record = {
            "heater_imposed_W": 0.0,
            "heater_wall_W": 0.0,
            "cooler_loss_W": 0.0,
            "test_section_loss_W": 0.0,
            "ambient_loss_W": 0.0,
            "junction_loss_W": 0.0,
            "total_prescribed_loss_W": 0.0,
        }
        for row in rows:
            patch = row["patch_group"]
            wall = fnum(row["wallHeatFlux_integral_W"])
            heat_to_fluid = wall if math.isfinite(wall) else 0.0
            if patch == "heater":
                record["heater_imposed_W"] = fnum(row["heater_imposed_duty_W"])
                record["heater_wall_W"] = heat_to_fluid
            elif patch == "cooler":
                record["cooler_loss_W"] += max(-heat_to_fluid, 0.0)
            elif patch == "test_section":
                record["test_section_loss_W"] += max(-heat_to_fluid, 0.0)
            elif patch == "ambient_wall":
                record["ambient_loss_W"] += max(-heat_to_fluid, 0.0)
            elif patch == "junction_other":
                record["junction_loss_W"] += max(-heat_to_fluid, 0.0)
        record["total_prescribed_loss_W"] = (
            record["cooler_loss_W"]
            + record["test_section_loss_W"]
            + record["ambient_loss_W"]
            + record["junction_loss_W"]
        )
        terms[case_id] = record
    return terms


def build_energy_defect_rows(
    targets: list[dict[str, str]],
    terms: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        case_id = target["case_id"]
        t = terms[case_id]
        prior_qhx = fnum(target["prior_1d_qhx_duty_W"])
        cooler_extra = t["cooler_loss_W"] - prior_qhx
        source_reduce = (t["heater_imposed_W"] - t["heater_wall_W"]) + 37.0
        test_sink_extra = t["test_section_loss_W"]
        known_leverage = cooler_extra + source_reduce + test_sink_extra
        rows.append(
            {
                "case_id": case_id,
                "prior_1d_Tmean_error_K": target["prior_1d_Tmean_error_K"],
                "prior_1d_qhx_duty_W": target["prior_1d_qhx_duty_W"],
                "cfd_cooler_loss_W": r3(t["cooler_loss_W"]),
                "cooler_extra_removal_vs_1d_W": r3(cooler_extra),
                "heater_imposed_minus_wall_W": r3(t["heater_imposed_W"] - t["heater_wall_W"]),
                "remove_1d_test_section_source_W": 37.0,
                "cfd_test_section_net_sink_W": r3(test_sink_extra),
                "known_first_order_correction_W": r3(known_leverage),
                "apparent_K_per_known_correction_W": r3(fnum(target["prior_1d_Tmean_error_K"]) / known_leverage),
                "passive_ambient_loss_W": r3(t["ambient_loss_W"]),
                "junction_grouped_loss_W": r3(t["junction_loss_W"]),
            }
        )
    return rows


def import_fluid():
    package_name = "tamu_loop_model_v2"
    package_path = FLUID_ROOT / package_name
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(package_path)]  # type: ignore[attr-defined]
        sys.modules[package_name] = package
    S = importlib.import_module(f"{package_name}.solver")
    geometry = importlib.import_module(f"{package_name}.geometry")

    return S, geometry.build_geometry, geometry.default_geometry_refinement


def loss_map_for_case(rows: list[dict[str, str]], include: set[str]) -> dict[str, float]:
    losses: dict[str, float] = {}
    for row in rows:
        if row["patch_group"] not in include:
            continue
        parent = FLUID_PARENT_BY_SPAN.get(row["span"])
        if not parent:
            continue
        wall = fnum(row["wallHeatFlux_integral_W"])
        if not math.isfinite(wall):
            continue
        loss = max(-wall, 0.0)
        if loss <= 0.0:
            continue
        losses[parent] = losses.get(parent, 0.0) + loss
    return losses


def run_fixed_mdot_replays(
    targets: list[dict[str, str]],
    contract_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    S, build_geometry, default_geometry_refinement = import_fluid()
    cases = {
        "Salt 2": S.ExperimentCase(
            name="Salt 2",
            fluid_name="salt",
            heater_power_W=265.7,
            test_section_power_W=37.0,
            air_T_inlet_K=299.19,
            air_flow_Lpm=37.0,
            provenance="manual reconstruction from Fluid configs/cases.yaml for AGENT-209",
        ),
        "Salt 3": S.ExperimentCase(
            name="Salt 3",
            fluid_name="salt",
            heater_power_W=297.5,
            test_section_power_W=37.0,
            air_T_inlet_K=299.79,
            air_flow_Lpm=37.0,
            provenance="manual reconstruction from Fluid configs/cases.yaml for AGENT-209",
        ),
        "Salt 4": S.ExperimentCase(
            name="Salt 4",
            fluid_name="salt",
            heater_power_W=337.6,
            test_section_power_W=37.0,
            air_T_inlet_K=299.97,
            air_flow_Lpm=37.0,
            provenance="manual reconstruction from Fluid configs/cases.yaml for AGENT-209",
        ),
    }
    base_scenario = S.ScenarioConfig(
        name="predictive_airside_ins_1.0in_rad_1",
        ambient_temperature_K=300.0,
        insulation_thickness_in=1.0,
        radiation_on=True,
        model_mode="predictive_airside_hx",
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=1.0e-5,
        mdot_search_upper_kg_s=0.2,
    )
    segments, sensors = build_geometry(refinement=default_geometry_refinement())
    rows_by_case = group_contract(contract_rows)
    terms = aggregate_terms(contract_rows)

    results: list[dict[str, Any]] = []
    for target in targets:
        case_id = target["case_id"]
        case = cases[CASE_NAME[case_id]]
        mdot = fnum(target["cfd_mdot_kg_s"])
        cfd_tmean = fnum(target["cfd_Tmean_K"])
        cfd_dt = fnum(target["cfd_loop_delta_T_K"])
        t = terms[case_id]
        crows = rows_by_case[case_id]

        trials = [
            {
                "path_id": "P0_fixed_mdot_current_1d_contract",
                "scenario": base_scenario,
                "sources": None,
                "losses": None,
                "description": "Current 1D thermal contract at CFD mdot.",
            },
            {
                "path_id": "P1_cfd_cooler_duty_only",
                "scenario": replace(
                    base_scenario,
                    name="fixed_mdot_cfd_cooler_duty_only",
                    model_mode="imposed_qhx",
                    imposed_qhx_W=t["cooler_loss_W"],
                ),
                "sources": None,
                "losses": None,
                "description": "Replace predictive air-side HX duty with CFD cooler wallHeatFlux magnitude.",
            },
            {
                "path_id": "P2_heater_wallflux_no_test_source",
                "scenario": base_scenario,
                "sources": {"heated_incline": t["heater_wall_W"]},
                "losses": None,
                "description": "Use heater interface wallHeatFlux and remove the 37 W 1D test-section source.",
            },
            {
                "path_id": "P3_source_plus_test_section_sink",
                "scenario": base_scenario,
                "sources": {"heated_incline": t["heater_wall_W"], "test_section": -t["test_section_loss_W"]},
                "losses": None,
                "description": "Use heater wallHeatFlux and treat the test section as a negative local source so internal ambient losses remain active.",
            },
            {
                "path_id": "P4_full_patch_ledger_prescribed",
                "scenario": replace(
                    base_scenario,
                    name="fixed_mdot_full_patch_ledger_prescribed",
                    model_mode="imposed_qhx",
                    imposed_qhx_W=0.0,
                ),
                "sources": {"heated_incline": t["heater_wall_W"]},
                "losses": loss_map_for_case(crows, {"cooler", "test_section", "ambient_wall", "junction_other"}),
                "description": "Prescribe heater wallHeatFlux plus all CFD patchwise heat losses mapped to 1D parent segments.",
            },
        ]

        for trial in trials:
            thermal = S.solve_temperature_periodicity(
                case,
                segments,
                sensors,
                mdot,
                trial["scenario"],
                prescribed_segment_sources_W=trial["sources"],
                prescribed_segment_losses_W=trial["losses"],
            )
            tmean = length_weighted_mean(thermal.segment_states)
            dt = loop_delta(thermal.segment_states)
            results.append(
                {
                    "case_id": case_id,
                    "path_id": trial["path_id"],
                    "description": trial["description"],
                    "fixed_mdot_kg_s": mdot,
                    "root_found": thermal.root_found,
                    "temperature_periodicity_error_K": r3(thermal.temperature_periodicity_error_K),
                    "model_Tmean_K": r3(tmean),
                    "cfd_Tmean_K": r3(cfd_tmean),
                    "Tmean_error_K": r3(tmean - cfd_tmean),
                    "model_loop_delta_T_K": r3(dt),
                    "cfd_loop_delta_T_K": r3(cfd_dt),
                    "loop_delta_T_error_K": r3(dt - cfd_dt),
                    "qhx_total_W": r3(thermal.qhx_total_W),
                    "qambient_total_W": r3(thermal.qambient_total_W),
                    "source_total_W": r3(sum(trial["sources"].values()) if trial["sources"] else case.heater_power_W + case.test_section_power_W),
                    "prescribed_loss_total_W": r3(sum(trial["losses"].values()) if trial["losses"] else 0.0),
                    "modeling_status": modeling_status_for_path(trial["path_id"]),
                }
            )
    return results


def build_path_summary(replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in replay_rows:
        grouped.setdefault(row["path_id"], []).append(row)
    summary: list[dict[str, Any]] = []
    for path_id, rows in grouped.items():
        t_errors = [abs(fnum(row["Tmean_error_K"])) for row in rows]
        dt_errors = [abs(fnum(row["loop_delta_T_error_K"])) for row in rows]
        summary.append(
            {
                "path_id": path_id,
                "mean_abs_Tmean_error_K": r3(sum(t_errors) / len(t_errors)),
                "mean_abs_loop_delta_T_error_K": r3(sum(dt_errors) / len(dt_errors)),
                "max_abs_Tmean_error_K": r3(max(t_errors)),
                "max_abs_loop_delta_T_error_K": r3(max(dt_errors)),
                "passes_thermal_gate": all(err <= 2.0 for err in t_errors) and all(err <= 1.0 for err in dt_errors),
                "interpretation": interpretation_for_path(path_id),
            }
        )
    return sorted(summary, key=lambda item: item["path_id"])


def interpretation_for_path(path_id: str) -> str:
    return {
        "P0_fixed_mdot_current_1d_contract": "Baseline fixed-mdot replay; isolates thermal state from pressure root search.",
        "P1_cfd_cooler_duty_only": "Tests whether the cooling-jacket duty magnitude is the dominant missing sink.",
        "P2_heater_wallflux_no_test_source": "Tests heat-source contract mismatch without changing cooler model.",
        "P3_source_plus_test_section_sink": "Tests the quartz/test-section role as a net sink without disabling the internal ambient-loss model.",
        "P4_full_patch_ledger_prescribed": "Fixed-Q full-ledger replay; loop delta T is informative, but absolute mean T is under-anchored without temperature-dependent boundary losses.",
    }[path_id]


def modeling_status_for_path(path_id: str) -> str:
    if path_id == "P4_full_patch_ledger_prescribed":
        return "fixed_Q_full_ledger_replay_mean_T_indeterminate_without_temperature_dependent_boundary_network"
    return "lightweight_fixed_mdot_thermal_replay_not_full_hydraulic_solution"


def write_agent_prompts(output_dir: Path) -> None:
    text = """# Parallel Agent Prompts

## Agent A: Cooler/HX Duty Audit

Prompt:
You are AGENT-HX. In ethan_runs, claim a new board task scoped to a cooler/HX audit. Read AGENTS.md, .agent/BOARD.md, the AGENT-209 package, and the Fluid solver HX implementation. Compare CFD cooler wallHeatFlux for Salt 2/3/4 against Fluid predictive qhx_total_W and the P1 replay. Audit air-flow units, shell hydraulic diameter, annulus area, active HX length, counterflow/parallel assumptions, and whether reducer patches should contribute to the cooling-jacket duty. Write a dated operational note with exact source lines, equations, and a recommended Fluid patch or no-patch decision.

## Agent B: Source/Test-Section Contract Audit

Prompt:
You are AGENT-SOURCE. In ethan_runs, claim a new board task scoped to source and test-section thermal contract. Read the AGENT-209 package, patchwise heat ledger, and Fluid cases.yaml/solver source distribution. Verify whether Salt 2/3/4 should use heater imposed duty, heater interface wallHeatFlux, or a split solid/fluid heater contract. Audit the 37 W quartz test-section source against CFD net test-section wallHeatFlux, including radiation/emissivity implications. Produce a table of proposed Fluid source/loss inputs and tests.

## Agent C: Radiation/qr Reconstruction

Prompt:
You are AGENT-QR. In ethan_runs, claim a new board task scoped to radiation semantics. Read the scenario contract, patchwise heat ledger, and OpenFOAM boundary files for Salt 2/3/4. Determine exactly why `qr` is absent despite emissivity metadata, whether `rcExternalTemperature` is computing radiative exchange implicitly or only using metadata, and what post-processing or solver changes would be required to export a patchwise radiation term. Document how to separate convection, conduction, and radiation without double counting.

## Agent D: Fixed-mdot Fluid Solver Design

Prompt:
You are AGENT-FROZEN. In the Fluid repo, claim a task scoped to fixed-mdot/frozen-hydraulics thermal replay. Read AGENT-208 and AGENT-209 outputs plus solver.py. Design and implement, or produce a precise patch plan for, a fixed_mdot_kg_s mode that solves thermal periodicity at prescribed mdot without pressure root search while still reporting pressure residual separately. Include tests proving solve_case fixed-mdot equals solve_temperature_periodicity at the target mdot and that model-form bakeoff cannot mix fixed-mdot thermal replay scores with predictive mdot scores.
"""
    output_dir.joinpath("parallel_agent_prompts.md").write_text(text, encoding="utf-8")


def write_fixed_mdot_plan(output_dir: Path) -> None:
    text = """# Fixed-mdot / Frozen-hydraulics Solver Plan

## Issue

The current Fluid `solve_case()` always searches mdot to close the pressure residual. That is correct for predictive hydraulic mode, but it confounds the thermal mismatch investigation: changing thermal losses changes density, viscosity, buoyancy, pressure losses, mdot, Re, and temperature at the same time.

For the thermal replay we need a mode that holds mdot at the CFD target and solves only thermal periodicity. The pressure residual should still be reported, but not used to move mdot.

## Proposed API

Add to `ScenarioConfig`:

```python
fixed_mdot_kg_s: Optional[float] = None
hydraulic_solution_mode: str = "predictive_pressure_root"  # or "fixed_mdot_thermal_replay"
```

or equivalently add a separate `solve_case_fixed_mdot(...)` wrapper if we want to avoid expanding the public scenario schema immediately.

## Algorithm

1. Build geometry and scenario segments exactly as `solve_case()` does.
2. Resolve optional 3D source/loss contracts exactly as `solve_case()` does.
3. Set `mdot = fixed_mdot_kg_s`.
4. Call `solve_temperature_periodicity(...)`.
5. Compute buoyancy and distributed/minor pressure terms using the resulting thermal state.
6. Return a `ModelResult` with:
   - `mdot_kg_s = fixed_mdot_kg_s`
   - `pressure_residual_Pa` reported but not rooted
   - `root_status` indicating thermal periodicity status, not pressure-root acceptance
   - an explicit metadata flag such as `hydraulic_solution_mode=fixed_mdot_thermal_replay`

## Assumptions

- CFD mdot is the target hydraulic state for the replay.
- Thermal periodicity remains the proper steady 1D thermal closure.
- Pressure residual is diagnostic in this mode.
- This mode is not a predictive mdot model and must not be scored as such.

## Limitations

- It does not prove the hydraulic closure is correct.
- It may suppress real coupling between thermal losses and buoyancy-driven flow.
- It depends on the CFD mdot/admission quality.
- If prescribed patch losses are mapped coarsely to parent segments, local temperatures can still be wrong even if loop mean is improved.

## Required Tests

1. Fixed-mdot result uses the exact requested mdot.
2. Fixed-mdot thermal state matches direct `solve_temperature_periodicity()` at the same mdot.
3. Pressure residual is reported and nonzero cases remain accepted only as thermal replay, not predictive hydraulics.
4. Scenario validation rejects `fixed_mdot_kg_s <= 0`.
5. Reporting layer separates predictive mdot scores from fixed-mdot thermal scores.
"""
    output_dir.joinpath("fixed_mdot_solver_plan.md").write_text(text, encoding="utf-8")


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Thermal Mismatch Remedy Deep Dive",
        "",
        f"Generated: `{summary['generated_utc']}`",
        "Task: `AGENT-209`",
        "",
        "## Scope",
        "",
        "This package answers the follow-up questions on the Salt 2/3/4 1D thermal-state mismatch using bounded fixed-mdot thermal replays against existing July 8 CFD contracts.",
        "",
        "## Main Result",
        "",
        "The strongest single issue is the cooler/HX path: the current prior 1D comparison removes only 46-54 W through the cooling jacket, while the CFD cooler wallHeatFlux removes 136-169 W.",
        "",
        "## Files",
        "",
        "- `heater_values.csv`: exact heater imposed duty versus heater wallHeatFlux.",
        "- `energy_defect_budget.csv`: first-order heat-defect accounting.",
        "- `fixed_mdot_replay_results.csv`: four remedy paths tried at CFD mdot plus baseline.",
        "- `remedy_path_summary.csv`: aggregate gate results by path.",
        "- `parallel_agent_prompts.md`: ready prompts for helper agents.",
        "- `fixed_mdot_solver_plan.md`: proposed Fluid fixed-mdot/frozen-hydraulics design.",
        "- `summary.json`: machine-readable summary.",
        "",
        "## Caveat",
        "",
        "These are fixed-mdot thermal replays using existing Fluid functions, not committed Fluid solver changes and not full predictive hydraulic solutions.",
    ]
    output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    contract_rows = read_csv(Path(args.contract))
    target_rows = read_csv(Path(args.targets))
    terms = aggregate_terms(contract_rows)
    heater_values = build_heater_values(contract_rows)
    energy_rows = build_energy_defect_rows(target_rows, terms)
    replay_rows = [] if args.skip_fluid_replays else run_fixed_mdot_replays(target_rows, contract_rows)
    path_summary = build_path_summary(replay_rows) if replay_rows else []

    write_csv(
        output_dir / "heater_values.csv",
        heater_values,
        ["case_id", "source_id", "heater_imposed_duty_W", "heater_wallHeatFlux_input_W", "imposed_minus_wallHeatFlux_W", "patch_names", "bc_type"],
    )
    write_csv(
        output_dir / "energy_defect_budget.csv",
        energy_rows,
        [
            "case_id",
            "prior_1d_Tmean_error_K",
            "prior_1d_qhx_duty_W",
            "cfd_cooler_loss_W",
            "cooler_extra_removal_vs_1d_W",
            "heater_imposed_minus_wall_W",
            "remove_1d_test_section_source_W",
            "cfd_test_section_net_sink_W",
            "known_first_order_correction_W",
            "apparent_K_per_known_correction_W",
            "passive_ambient_loss_W",
            "junction_grouped_loss_W",
        ],
    )
    if replay_rows:
        write_csv(
            output_dir / "fixed_mdot_replay_results.csv",
            replay_rows,
            [
                "case_id",
                "path_id",
                "description",
                "fixed_mdot_kg_s",
                "root_found",
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
                "modeling_status",
            ],
        )
        write_csv(
            output_dir / "remedy_path_summary.csv",
            path_summary,
            [
                "path_id",
                "mean_abs_Tmean_error_K",
                "mean_abs_loop_delta_T_error_K",
                "max_abs_Tmean_error_K",
                "max_abs_loop_delta_T_error_K",
                "passes_thermal_gate",
                "interpretation",
            ],
        )
    write_agent_prompts(output_dir)
    write_fixed_mdot_plan(output_dir)
    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "heater_rows": len(heater_values),
        "energy_defect_rows": len(energy_rows),
        "fixed_mdot_replay_rows": len(replay_rows),
        "best_path_by_mean_abs_Tmean_error": min(path_summary, key=lambda row: fnum(row["mean_abs_Tmean_error_K"]))["path_id"] if path_summary else "",
        "thermal_gate_paths": [row["path_id"] for row in path_summary if row["passes_thermal_gate"]],
        "contract": str(Path(args.contract)),
        "targets": str(Path(args.targets)),
    }
    output_dir.joinpath("summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--skip-fluid-replays", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_package(args)
    print(f"Wrote thermal mismatch remedy deep dive to {args.output_dir}")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
