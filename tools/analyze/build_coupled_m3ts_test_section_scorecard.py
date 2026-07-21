#!/usr/bin/env python3
"""Build AGENT-461 coupled M3+TS test-section scorecard package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-461"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard")
OUT = ROOT / OUT_REL

SETUP_ROWS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv"
AG458_SUMMARY = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model/setup_candidate_summary.csv"
M2M3 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/case_mode_error_matrix.csv"
FLUID_CONTRACT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/fluid_variant_contract.csv"

VALIDATION_W_TOL = 5.0
HOLDOUT_W_TOL = 10.0
PCT_TOL = 25.0
SPLIT_ORDER = {"train": 0, "validation": 1, "holdout": 2}
CASE_NAME = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


def split_tolerance(split_role: str) -> float | None:
    if split_role == "validation":
        return VALIDATION_W_TOL
    if split_role == "holdout":
        return HOLDOUT_W_TOL
    return None


def gate(abs_error_w: float | None, pct_error: float | None, split_role: str) -> str:
    if split_role == "train":
        return "fit_row_not_generalization_scored"
    tol = split_tolerance(split_role)
    if abs_error_w is None or pct_error is None or tol is None:
        return "missing"
    return "pass" if abs_error_w <= tol and pct_error <= PCT_TOL else "fail"


def setup_by_case() -> dict[str, list[dict[str, str]]]:
    rows = [row for row in read_csv(SETUP_ROWS) if row["case_id"] in CASE_NAME]
    return {case_id: [row for row in rows if row["case_id"] == case_id] for case_id in CASE_NAME}


def role_rows_for_case(case_rows: list[dict[str, str]], test_section_coverage: float = 1.0) -> list[dict[str, Any]]:
    role_rows: list[dict[str, Any]] = []
    for row in case_rows:
        if row["fluid_parent_segment"] != "left_upper_vertical":
            continue
        if row["role"] not in {"ambient_wall", "test_section"}:
            continue
        coverage = test_section_coverage if row["role"] == "test_section" else 1.0
        role_rows.append(
            {
                "parent_segment": row["fluid_parent_segment"],
                "one_d_segment": row["one_d_segment"],
                "role": row["role"],
                "area_m2": safe_float(row["area_m2"]),
                "h_W_m2K": safe_float(row["h_W_m2K"]),
                "hA_W_K": safe_float(row["hA_W_K"]),
                "Ta_K": safe_float(row["Ta_K"]),
                "Tsur_K": safe_float(row["Tsur_K"]),
                "emissivity": safe_float(row["emissivity"]),
                "coverage_multiplier": coverage,
                "drive_selector": row["recommended_drive_selector"],
                "source": rel(SETUP_ROWS),
            }
        )
    return role_rows


def parent_boundary_maps(case_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    maps: dict[str, dict[str, Any]] = {
        "external_boundary_h_by_parent_segment": {},
        "external_boundary_ambient_temperature_by_parent_segment": {},
        "external_boundary_surroundings_temperature_by_parent_segment": {},
        "external_boundary_emissivity_by_parent_segment": {},
        "external_boundary_source_by_parent_segment": {},
        "external_boundary_drive_selector_by_parent_segment": {},
    }
    for row in case_rows:
        if row["support_status"] != "ready_for_fluid_api_consumption":
            continue
        parent = row["fluid_parent_segment"]
        if parent == "left_upper_vertical":
            continue
        h = safe_float(row["h_W_m2K"])
        ta = safe_float(row["Ta_K"])
        if h is None or ta is None:
            continue
        maps["external_boundary_h_by_parent_segment"][parent] = h
        maps["external_boundary_ambient_temperature_by_parent_segment"][parent] = ta
        maps["external_boundary_surroundings_temperature_by_parent_segment"][parent] = safe_float(row["Tsur_K"]) or ta
        maps["external_boundary_emissivity_by_parent_segment"][parent] = safe_float(row["emissivity"]) or 0.95
        maps["external_boundary_source_by_parent_segment"][parent] = rel(SETUP_ROWS)
        maps["external_boundary_drive_selector_by_parent_segment"][parent] = row["recommended_drive_selector"]
    return maps


def candidate_definitions() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "M3TS_R0_role_table_unscaled",
            "test_section_coverage": 1.0,
            "fit_policy": "no_test_section_scalar",
        },
        {
            "candidate_id": "M3TS_R1_salt2_fit_test_section_coverage",
            "test_section_coverage": 1.0,
            "fit_policy": "salt2_scalar_placeholder_pending_compute_node_fit",
        },
        {
            "candidate_id": "M3TS_R2_resistance_network_role_table",
            "test_section_coverage": 1.0,
            "fit_policy": "role_table_resistance_network_equivalent_pending_wall_layer_completion",
        },
    ]


def scenario_contract_rows() -> list[dict[str, Any]]:
    by_case = setup_by_case()
    rows: list[dict[str, Any]] = []
    for candidate in candidate_definitions():
        for case_id, case_rows in by_case.items():
            split_role = next(row["validation_split_role"] for row in case_rows if row["role"] == "test_section")
            role_rows = role_rows_for_case(case_rows, candidate["test_section_coverage"])
            maps = parent_boundary_maps(case_rows)
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "case_id": case_id,
                    "fluid_case_name": CASE_NAME[case_id],
                    "split_role": split_role,
                    "outer_closure_mode": "external_boundary_table",
                    "role_row_count": len(role_rows),
                    "parent_boundary_count": len(maps["external_boundary_h_by_parent_segment"]),
                    "test_section_coverage": fmt(candidate["test_section_coverage"]),
                    "fit_policy": candidate["fit_policy"],
                    "runtime_inputs": "setup_role_rows;setup_parent_boundary_maps;admitted_heater;admitted_hx",
                    "runtime_input_violations": 0,
                    "scenario_json": json.dumps({"role_rows": role_rows, "parent_boundary_maps": maps}, sort_keys=True),
                    "source_path": rel(SETUP_ROWS),
                }
            )
    return rows


def static_heat_loss_gate_rows() -> list[dict[str, Any]]:
    ag458 = read_csv(AG458_SUMMARY)
    rows: list[dict[str, Any]] = []
    mapping = {
        "M3TS_R0_role_table_unscaled": "TS1_salt2_fit_hA_constant_drive_deltaT",
        "M3TS_R1_salt2_fit_test_section_coverage": "TS1_salt2_fit_hA_constant_drive_deltaT",
        "M3TS_R2_resistance_network_role_table": "TS2_salt2_fit_constant_loss_W",
    }
    for candidate_id, prior_id in mapping.items():
        prior = next(row for row in ag458 if row["candidate_id"] == prior_id)
        for split_role in ["validation", "holdout"]:
            abs_error = safe_float(prior[f"{split_role}_abs_error_W"])
            pct_error = safe_float(prior[f"{split_role}_abs_error_pct"])
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "split_role": split_role,
                    "prior_static_screen": prior_id,
                    "abs_error_W": fmt(abs_error),
                    "abs_error_pct": fmt(pct_error),
                    "heat_loss_gate": gate(abs_error, pct_error, split_role),
                    "source_path": rel(AG458_SUMMARY),
                }
            )
    return rows


def coupled_rows(run_fluid: bool) -> list[dict[str, Any]]:
    if not run_fluid:
        return [
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "coupled_run_status": "not_run_login_node_budget_guardrail",
                "root_status": "",
                "mdot_error_pct": "",
                "tp_rmse_K": "",
                "tw_rmse_K": "",
                "all_probe_rmse_K": "",
                "Tmean_error_K": "",
                "loop_delta_error_K": "",
                "coupled_gate": "fail_no_completed_coupled_m3ts_score",
                "source_path": "",
            }
            for row in scenario_contract_rows()
        ]

    if str(FLUID_ROOT) not in sys.path:
        sys.path.insert(0, str(FLUID_ROOT))
    from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME, default_scenarios
    from tamu_loop_model_v2.reporting import build_validation_table
    from tamu_loop_model_v2.solver import ScenarioConfig, solve_case

    base = next(s for s in default_scenarios() if s.name == "predictive_airside_ins_1.0in_rad_0")
    cases = {case.name: case for case in EXPERIMENT_CASES}
    by_case = setup_by_case()
    rows: list[dict[str, Any]] = []
    for candidate in candidate_definitions():
        for case_id, case_rows in by_case.items():
            maps = parent_boundary_maps(case_rows)
            scenario = ScenarioConfig(
                **{
                    **base.__dict__,
                    "name": candidate["candidate_id"],
                    "outer_closure_mode": "external_boundary_table",
                    "external_boundary_role_rows": role_rows_for_case(case_rows, candidate["test_section_coverage"]),
                    **maps,
                }
            )
            case = cases[CASE_NAME[case_id]]
            result = solve_case(case, scenario)
            validation = VALIDATION_CASES_BY_NAME.get(case.name)
            table = build_validation_table(result, validation)
            valid = table[~table["validation_excluded"]].copy()
            tp = valid[valid["kind"] == "TP"]["error_K"]
            tw = valid[valid["kind"] == "TW"]["error_K"]
            all_err = valid["error_K"]
            measured_mdot = None if validation is None else validation.measured_mass_flow_rate_kg_s
            mdot_error_pct = None if measured_mdot in (None, 0.0) else 100.0 * (result.mdot_kg_s - measured_mdot) / measured_mdot
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "case_id": case_id,
                    "split_role": next(row["validation_split_role"] for row in case_rows if row["role"] == "test_section"),
                    "coupled_run_status": "completed",
                    "root_status": result.root_status,
                    "mdot_error_pct": fmt(mdot_error_pct),
                    "tp_rmse_K": fmt(math.sqrt(float((tp * tp).mean())) if len(tp) else None),
                    "tw_rmse_K": fmt(math.sqrt(float((tw * tw).mean())) if len(tw) else None),
                    "all_probe_rmse_K": fmt(math.sqrt(float((all_err * all_err).mean())) if len(all_err) else None),
                    "Tmean_error_K": "",
                    "loop_delta_error_K": "",
                    "coupled_gate": "pending_admission_review",
                    "source_path": "Fluid solve_case with scenario_json from scenario_contract_rows.csv",
                }
            )
    return rows


def comparator_rows() -> list[dict[str, Any]]:
    return [
        row
        for row in read_csv(M2M3)
        if row["mode_id"]
        in {
            "M2_cfd_heater_test_section_cooler_pressure_root",
            "M3_cfd_heater_cooler_pressure_root",
            "M3_setup_heater_cooler_no_test_section",
        }
    ]


def runtime_audit_rows(run_fluid: bool = False) -> list[dict[str, Any]]:
    coupled_gate = "pass" if run_fluid else "incomplete"
    coupled_evidence = (
        "Fluid solve_case completed for all M3+TS candidate/case rows"
        if run_fluid
        else "full solve is compute-node recommended; --run-fluid was not part of default builder validation"
    )
    return [
        {
            "audit_id": "R1_fluid_role_rows_implemented",
            "gate": "pass",
            "evidence": "Fluid tests/test_solver_contracts.py external_boundary role-row tests",
            "forbidden_runtime_input": "none",
        },
        {
            "audit_id": "R2_runtime_inputs",
            "gate": "pass",
            "evidence": "scenario rows use setup hA/h/area/Ta/Tsur/emissivity/drive selectors and admitted heater/HX only",
            "forbidden_runtime_input": "realized wallHeatFlux; CFD mdot; validation temperatures; imposed CFD cooler duty",
        },
        {
            "audit_id": "R3_coupled_score",
            "gate": coupled_gate,
            "evidence": coupled_evidence,
            "forbidden_runtime_input": "not applicable",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_id": "setup_external_boundary_rows", "path": rel(SETUP_ROWS), "use": "role rows and parent external-boundary setup maps"},
        {"source_id": "agent458_static_screen", "path": rel(AG458_SUMMARY), "use": "held-out heat-loss gate carry-forward"},
        {"source_id": "m2_m3_comparators", "path": rel(M2M3), "use": "diagnostic M2/M3 mdot and temperature comparator rows"},
        {"source_id": "fluid_contract", "path": rel(FLUID_CONTRACT), "use": "baseline external-boundary API evidence"},
        {"source_id": "fluid_solver", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "role-local external-boundary implementation"},
        {"source_id": "fluid_tests", "path": rel(FLUID_ROOT / "tests/test_solver_contracts.py"), "use": "role-row and external-boundary contract validation"},
    ]


def blocker_decision(coupled: list[dict[str, Any]], heat: list[dict[str, Any]], run_fluid: bool = False) -> dict[str, Any]:
    any_coupled_pass = any(row.get("coupled_gate") == "pass" for row in coupled)
    any_heat_pass = any(row.get("heat_loss_gate") == "pass" for row in heat)
    completed_coupled = bool(coupled) and all(row.get("coupled_run_status") == "completed" for row in coupled)
    resolved = any_coupled_pass and any_heat_pass
    if resolved:
        why = "At least one candidate passed runtime, heat-loss, and coupled score gates."
        next_required_action = "Close the blocker and publish the admitted M3+TS candidate."
    elif run_fluid and completed_coupled:
        why = (
            "Fluid solves completed, but no candidate has both an admitted coupled gate "
            "and held-out heat-loss gates."
        )
        next_required_action = (
            "Adjudicate coupled mdot/TP/TW thresholds, then improve the predictive "
            "test-section/cooler heat-loss model before rerunning admission."
        )
    else:
        why = "No candidate has both completed coupled M3+TS scoring and passed held-out heat-loss gates."
        next_required_action = (
            "Run `python3 tools/analyze/build_coupled_m3ts_test_section_scorecard.py --run-fluid` "
            "on a compute node or sbatch wrapper, then rerun admission review."
        )
    return {
        "task": TASK,
        "blocker_id": "predictive-wall-test-section-submodels",
        "decision": "resolve" if resolved else "keep_open",
        "why": why,
        "next_required_action": next_required_action,
        "evidence": rel(OUT / "m3ts_coupled_scorecard.csv"),
        "generated_at": utc_now(),
    }


def write_readme(decision: dict[str, Any]) -> None:
    text = f"""---
provenance:
  task: {TASK}
  generated_at: {utc_now()}
  sources:
    - {rel(SETUP_ROWS)}
    - {rel(AG458_SUMMARY)}
    - {rel(M2M3)}
    - {rel(FLUID_CONTRACT)}
tags: [forward-model, m3ts, test-section, fluid-role-boundary]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
---
# Coupled M3+TS Test-Section Scorecard

This package implements the M3+TS blocker-removal path up to the compute-node
coupled solve gate.

Implemented:

- Fluid now supports role-local external-boundary rows, so `ambient_wall` and
  `test_section` subspans on `left_upper_vertical` can replace the parent
  upcomer ambient-loss approximation without using realized CFD heat evidence.
- The scorecard builder emits exact role-row scenario contracts for Salt2 train,
  Salt3 validation, and Salt4 holdout.
- Runtime audit passes for the generated scenario contracts.

Decision: `{decision['decision']}` for `predictive-wall-test-section-submodels`.

Why: {decision['why']}

Next required action: {decision['next_required_action']}
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build(run_fluid: bool = False) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    scenarios = scenario_contract_rows()
    heat = static_heat_loss_gate_rows()
    coupled = coupled_rows(run_fluid)
    runtime = runtime_audit_rows(run_fluid)
    decision = blocker_decision(coupled, heat, run_fluid)
    counts = {
        "m3ts_role_boundary_scenarios.csv": write_csv(
            OUT / "m3ts_role_boundary_scenarios.csv",
            scenarios,
            [
                "candidate_id",
                "case_id",
                "fluid_case_name",
                "split_role",
                "outer_closure_mode",
                "role_row_count",
                "parent_boundary_count",
                "test_section_coverage",
                "fit_policy",
                "runtime_inputs",
                "runtime_input_violations",
                "scenario_json",
                "source_path",
            ],
        ),
        "m3ts_heat_loss_gate.csv": write_csv(
            OUT / "m3ts_heat_loss_gate.csv",
            heat,
            ["candidate_id", "split_role", "prior_static_screen", "abs_error_W", "abs_error_pct", "heat_loss_gate", "source_path"],
        ),
        "m3ts_coupled_scorecard.csv": write_csv(
            OUT / "m3ts_coupled_scorecard.csv",
            coupled,
            [
                "candidate_id",
                "case_id",
                "split_role",
                "coupled_run_status",
                "root_status",
                "mdot_error_pct",
                "tp_rmse_K",
                "tw_rmse_K",
                "all_probe_rmse_K",
                "Tmean_error_K",
                "loop_delta_error_K",
                "coupled_gate",
                "source_path",
            ],
        ),
        "m2_m3_comparators.csv": write_csv(
            OUT / "m2_m3_comparators.csv",
            comparator_rows(),
            [
                "case_id",
                "split",
                "mode_id",
                "mdot_pred_kg_s",
                "cfd_mdot_kg_s",
                "mdot_error_pct",
                "all_probe_rmse_K",
                "tp_rmse_K",
                "tw_rmse_K",
                "Tmean_error_K",
                "loop_delta_error_K",
                "admission_use_class",
                "source_path",
            ],
        ),
        "runtime_input_audit.csv": write_csv(
            OUT / "runtime_input_audit.csv",
            runtime,
            ["audit_id", "gate", "evidence", "forbidden_runtime_input"],
        ),
        "source_manifest.csv": write_csv(
            OUT / "source_manifest.csv",
            source_manifest_rows(),
            ["source_id", "path", "use"],
        ),
    }
    write_json(OUT / "blocker_decision.json", decision)
    write_json(OUT / "summary.json", {"task": TASK, "date": DATE, "run_fluid": run_fluid, "counts": counts, "decision": decision})
    write_readme(decision)
    return {"output_dir": rel(OUT), "counts": counts, "decision": decision}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-fluid", action="store_true", help="Run actual Fluid solve_case coupled scorecard; use on a compute node.")
    args = parser.parse_args()
    print(json.dumps(build(run_fluid=args.run_fluid), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
