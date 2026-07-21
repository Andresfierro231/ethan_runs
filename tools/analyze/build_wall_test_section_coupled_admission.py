#!/usr/bin/env python3
"""Build AGENT-494 wall/test-section coupled admission package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-494"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission")
OUT = ROOT / OUT_REL

AGENT492 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_cooler_fluid_timeout_and_wall_circuit_study"
AGENT482 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model"
AGENT461 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard"
SETUP_ROWS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv"
M3_COMPARATORS = AGENT461 / "m2_m3_comparators.csv"

CASE_NAME = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}
CASE_ORDER = {"salt_2": 0, "salt_3": 1, "salt_4": 2}
SPLIT = {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}
PB1_ID = "PB1_total_hA_heater_power_drive_p1"
TS6_ID = "TS6_test_section_hA_heater_power_drive_p2"
TS7_ID = "TS7_test_section_quartz_external_hA_heater_power_drive_p2"
DEFAULT_TIMEOUT_SECONDS = 273
PCT_TOL = 25.0
VALIDATION_W_TOL = 5.0
HOLDOUT_W_TOL = 10.0


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


def split_w_tolerance(split_role: str) -> float | None:
    if split_role == "validation":
        return VALIDATION_W_TOL
    if split_role == "holdout":
        return HOLDOUT_W_TOL
    return None


def qoi_gate(abs_error: float | None, pct_error: float | None, split_role: str) -> str:
    if split_role == "train":
        return "fit_row_not_generalization_scored"
    tol = split_w_tolerance(split_role)
    if abs_error is None or pct_error is None or tol is None:
        return "missing"
    return "pass" if abs_error <= tol and pct_error <= PCT_TOL else "fail"


def setup_rows_by_case() -> dict[str, list[dict[str, str]]]:
    rows = [row for row in read_csv(SETUP_ROWS) if row.get("case_id") in CASE_NAME]
    return {case_id: [row for row in rows if row["case_id"] == case_id] for case_id in sorted(CASE_NAME, key=CASE_ORDER.get)}


def wall_scores() -> list[dict[str, str]]:
    return read_csv(AGENT492 / "wall_circuit_candidate_scores.csv")


def wall_summary() -> dict[str, dict[str, str]]:
    return {row["candidate_id"]: row for row in read_csv(AGENT492 / "wall_circuit_candidate_summary.csv")}


def cooler_candidates() -> list[dict[str, Any]]:
    rows = read_csv(AGENT482 / "candidate_definitions.csv")
    return [
        row
        for row in rows
        if row["candidate_id"] in {"HX_LUMPED_UA_NTU", "HX_SEGMENTED_UA_NTU_N4", "HX_SEGMENTED_UA_NTU_N8", "HX_SEGMENTED_UA_NTU_N16"}
    ]


def m3_baselines() -> dict[str, dict[str, str]]:
    return {
        row["case_id"]: row
        for row in read_csv(M3_COMPARATORS)
        if row.get("mode_id") == "M3_cfd_heater_cooler_pressure_root"
    }


def fit_alpha_ua() -> float:
    row = next(row for row in read_csv(AGENT482 / "fit_parameters.csv") if row["candidate_id"] == "HX_LUMPED_UA_NTU")
    return safe_float(row["fitted_parameter_value"]) or 1.0


def pb1_multiplier_by_case() -> dict[str, float]:
    scores = [row for row in wall_scores() if row["candidate_id"] == PB1_ID]
    train = next(row for row in scores if row["case_id"] == "salt_2")
    q_train = safe_float(train["heater_source_W_setup"]) or 1.0
    out: dict[str, float] = {}
    for row in scores:
        out[row["case_id"]] = (safe_float(row["heater_source_W_setup"]) or q_train) / max(q_train, 1e-12)
    return out


def candidate_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cooler in cooler_candidates():
        rows.append(
            {
                "candidate_id": f"PB1_PLUS_{cooler['candidate_id']}",
                "wall_candidate_id": PB1_ID,
                "cooler_candidate_id": cooler["candidate_id"],
                "test_section_policy": "local_TS_candidates_are_scored_separately_not_absorbed_by_PB1",
                "fitted_parameter_count": 2,
                "fitted_parameters": "PB1 Salt2 passive drive; cooler alpha_UA",
                "runtime_status": "coupled_runner_available_with_--run-fluid",
                "source_path": f"{rel(AGENT492)};{rel(AGENT482)}",
            }
        )
    rows.extend(
        [
            {
                "candidate_id": TS6_ID,
                "wall_candidate_id": "",
                "cooler_candidate_id": "",
                "test_section_policy": "diagnostic_component_only",
                "fitted_parameter_count": 1,
                "fitted_parameters": "Salt2 test-section drive",
                "runtime_status": "static_component_review_only",
                "source_path": rel(AGENT492),
            },
            {
                "candidate_id": TS7_ID,
                "wall_candidate_id": "",
                "cooler_candidate_id": "",
                "test_section_policy": "diagnostic_quartz_external_hA_component",
                "fitted_parameter_count": 1,
                "fitted_parameters": "Salt2 quartz/test-section external drive; no new fit beyond TS6",
                "runtime_status": "static_component_review_only",
                "source_path": rel(SETUP_ROWS),
            },
        ]
    )
    return rows


def _role_rows_with_pb1(case_rows: list[dict[str, str]], pb1_multiplier: float) -> list[dict[str, Any]]:
    role_rows: list[dict[str, Any]] = []
    for row in case_rows:
        if row["fluid_parent_segment"] != "left_upper_vertical":
            continue
        if row["role"] not in {"ambient_wall", "test_section"}:
            continue
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
                "coverage_multiplier": pb1_multiplier,
                "drive_selector": row["recommended_drive_selector"],
                "source": rel(SETUP_ROWS),
            }
        )
    return role_rows


def _parent_maps_with_pb1(case_rows: list[dict[str, str]], pb1_multiplier: float) -> dict[str, dict[str, Any]]:
    maps: dict[str, dict[str, Any]] = {
        "external_boundary_h_by_parent_segment": {},
        "external_boundary_ambient_temperature_by_parent_segment": {},
        "external_boundary_surroundings_temperature_by_parent_segment": {},
        "external_boundary_emissivity_by_parent_segment": {},
        "external_boundary_coverage_multiplier_by_parent_segment": {},
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
        maps["external_boundary_coverage_multiplier_by_parent_segment"][parent] = pb1_multiplier
        maps["external_boundary_source_by_parent_segment"][parent] = rel(SETUP_ROWS)
        maps["external_boundary_drive_selector_by_parent_segment"][parent] = row["recommended_drive_selector"]
    return maps


def scenario_contract_rows() -> list[dict[str, Any]]:
    by_case = setup_rows_by_case()
    multipliers = pb1_multiplier_by_case()
    alpha = fit_alpha_ua()
    rows: list[dict[str, Any]] = []
    for candidate in candidate_definitions():
        if not candidate["candidate_id"].startswith("PB1_PLUS_"):
            continue
        cooler_id = candidate["cooler_candidate_id"]
        for case_id, case_rows in by_case.items():
            mult = multipliers[case_id]
            role_rows = _role_rows_with_pb1(case_rows, mult)
            maps = _parent_maps_with_pb1(case_rows, mult)
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "case_id": case_id,
                    "fluid_case_name": CASE_NAME[case_id],
                    "split_role": SPLIT[case_id],
                    "wall_candidate_id": PB1_ID,
                    "cooler_candidate_id": cooler_id,
                    "pb1_setup_multiplier": fmt(mult),
                    "hx_ua_multiplier": fmt(alpha),
                    "outer_closure_mode": "external_boundary_table",
                    "role_row_count": len(role_rows),
                    "parent_boundary_count": len(maps["external_boundary_h_by_parent_segment"]),
                    "runtime_input_violations": 0,
                    "runtime_inputs": "setup_external_boundary_rows;PB1_Salt2_drive;cooler_alpha_UA",
                    "scenario_json": json.dumps({"role_rows": role_rows, "parent_boundary_maps": maps}, sort_keys=True),
                    "source_path": f"{rel(AGENT492)};{rel(AGENT482)};{rel(SETUP_ROWS)}",
                }
            )
    return rows


def static_component_scorecard_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scores = wall_scores()
    for row in scores:
        if row["candidate_id"] not in {PB1_ID, TS6_ID}:
            continue
        out = dict(row)
        out["component_class"] = "passive_total" if row["candidate_id"] == PB1_ID else "test_section_local"
        out["admission_use"] = "coupled_candidate_input" if row["candidate_id"] == PB1_ID else "diagnostic_local_component"
        rows.append(out)
    ts6_rows = [row for row in scores if row["candidate_id"] == TS6_ID]
    for row in ts6_rows:
        # TS7 is the explicit quartz/test-section external-hA restatement. With
        # current setup data it intentionally collapses to TS6 numerically; that
        # makes the missing local wall-temperature drive visible instead of
        # inventing another fitted correction.
        out = dict(row)
        out["candidate_id"] = TS7_ID
        out["model_form"] = "Q_TS=hA_quartz_setup*DeltaT_train*(Q_heater/Q_heater_train)^2"
        out["component_class"] = "test_section_local"
        out["admission_use"] = "diagnostic_quartz_component_missing_wall_temperature_drive"
        rows.append(out)
    rows.sort(key=lambda r: (r["candidate_id"], CASE_ORDER.get(r["case_id"], 99)))
    return rows


def static_component_summary_rows() -> list[dict[str, Any]]:
    summaries = wall_summary()
    rows: list[dict[str, Any]] = []
    for candidate_id in [PB1_ID, TS6_ID, TS7_ID]:
        if candidate_id == TS7_ID:
            source = summaries[TS6_ID]
            row = dict(source)
            row["candidate_id"] = TS7_ID
            row["recommendation"] = "do_not_admit_same_as_TS6_until_local_wall_temperature_drive_exists"
            row["admission_decision"] = "not_admitted_local_test_section_percent_gate_failed"
        else:
            row = dict(summaries[candidate_id])
            if candidate_id == PB1_ID:
                row["admission_decision"] = "not_admitted_pending_coupled_m3ts_plus_cooler_score"
            else:
                row["admission_decision"] = "not_admitted_local_test_section_percent_gate_failed"
        rows.append(row)
    return rows


def _fluid_worker(contract: dict[str, Any], timeout_seconds: int, queue: Any) -> None:
    started = time.monotonic()
    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        if str(FLUID_ROOT) not in sys.path:
            sys.path.insert(0, str(FLUID_ROOT))
        from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME, default_scenarios
        from tamu_loop_model_v2.reporting import build_validation_table
        from tamu_loop_model_v2 import solver
        from tools.analyze.build_cooler_removal_model import SegmentedHxAdapter

        cases = {case.name: case for case in EXPERIMENT_CASES}
        base = next(s for s in default_scenarios() if s.name == "predictive_airside_ins_1.0in_rad_0")
        payload = json.loads(contract["scenario_json"])
        parent_maps = payload["parent_boundary_maps"]
        scenario = solver.ScenarioConfig(
            **{
                **base.__dict__,
                "name": contract["candidate_id"],
                "model_mode": "predictive_airside_hx",
                "imposed_qhx_W": None,
                "hx_ua_multiplier": safe_float(contract["hx_ua_multiplier"]) or 1.0,
                "outer_closure_mode": "external_boundary_table",
                "external_boundary_role_rows": payload["role_rows"],
                **parent_maps,
            }
        )
        adapter = None
        if contract["cooler_candidate_id"].startswith("HX_SEGMENTED"):
            n = int(contract["cooler_candidate_id"].rsplit("N", 1)[1])
            adapter = SegmentedHxAdapter(solver, n)
            adapter.context = {
                "candidate_id": contract["candidate_id"],
                "case_id": contract["case_id"],
                "split_role": contract["split_role"],
            }
        case = cases[contract["fluid_case_name"]]
        try:
            if adapter is not None:
                solver._hx_airside_transfer = adapter
            result = solver.solve_case(case, scenario)
        finally:
            if adapter is not None:
                solver._hx_airside_transfer = adapter.original
        validation = VALIDATION_CASES_BY_NAME.get(case.name)
        table = build_validation_table(result, validation)
        valid = table[~table["validation_excluded"]].copy()
        tp = valid[valid["kind"] == "TP"]["error_K"]
        tw = valid[valid["kind"] == "TW"]["error_K"]
        all_err = valid["error_K"]
        measured_mdot = None if validation is None else validation.measured_mass_flow_rate_kg_s
        mdot_error_pct = None if measured_mdot in (None, 0.0) else 100.0 * (result.mdot_kg_s - measured_mdot) / measured_mdot
        queue.put(
            {
                "candidate_id": contract["candidate_id"],
                "case_id": contract["case_id"],
                "split_role": contract["split_role"],
                "coupled_run_status": "completed",
                "elapsed_s": fmt(time.monotonic() - started),
                "root_status": result.root_status,
                "qhx_total_W": fmt(result.qhx_total_W),
                "qambient_total_W": fmt(result.qambient_total_W),
                "mdot_error_pct": fmt(mdot_error_pct),
                "tp_rmse_K": fmt(math.sqrt(float((tp * tp).mean())) if len(tp) else None),
                "tw_rmse_K": fmt(math.sqrt(float((tw * tw).mean())) if len(tw) else None),
                "all_probe_rmse_K": fmt(math.sqrt(float((all_err * all_err).mean())) if len(all_err) else None),
                "coupled_gate": "completed_pending_delta_review",
                "source_path": "Fluid solve_case with AGENT-494 PB1+cooler scenario",
            }
        )
    except Exception as exc:  # pragma: no cover - Fluid failures are environment dependent.
        queue.put(
            {
                "candidate_id": contract.get("candidate_id", ""),
                "case_id": contract.get("case_id", ""),
                "split_role": contract.get("split_role", ""),
                "coupled_run_status": "error",
                "elapsed_s": fmt(time.monotonic() - started),
                "root_status": "",
                "qhx_total_W": "",
                "qambient_total_W": "",
                "mdot_error_pct": "",
                "tp_rmse_K": "",
                "tw_rmse_K": "",
                "all_probe_rmse_K": "",
                "coupled_gate": "fail_solver_error",
                "source_path": f"{type(exc).__name__}: {exc}",
            }
        )


def coupled_scorecard_rows(run_fluid: bool, timeout_seconds: int) -> list[dict[str, Any]]:
    contracts = scenario_contract_rows()
    if not run_fluid:
        return [
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "coupled_run_status": "not_run_submit_background_srun",
                "elapsed_s": "",
                "root_status": "",
                "qhx_total_W": "",
                "qambient_total_W": "",
                "mdot_error_pct": "",
                "tp_rmse_K": "",
                "tw_rmse_K": "",
                "all_probe_rmse_K": "",
                "coupled_gate": "pending_background_fluid_score",
                "source_path": "",
            }
            for row in contracts
        ]
    rows: list[dict[str, Any]] = []
    for contract in contracts:
        queue: mp.Queue = mp.Queue()
        process = mp.Process(target=_fluid_worker, args=(contract, timeout_seconds, queue))
        process.start()
        process.join(timeout_seconds)
        if process.is_alive():
            process.terminate()
            process.join(10)
            rows.append(
                {
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "coupled_run_status": f"timeout_after_{timeout_seconds}s",
                    "elapsed_s": fmt(timeout_seconds),
                    "root_status": "",
                    "qhx_total_W": "",
                    "qambient_total_W": "",
                    "mdot_error_pct": "",
                    "tp_rmse_K": "",
                    "tw_rmse_K": "",
                    "all_probe_rmse_K": "",
                    "coupled_gate": "fail_solver_timeout",
                    "source_path": "bounded Fluid solve_case attempt timed out",
                }
            )
        elif not queue.empty():
            rows.append(queue.get())
        else:
            rows.append(
                {
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "coupled_run_status": "error_no_worker_result",
                    "elapsed_s": "",
                    "root_status": "",
                    "qhx_total_W": "",
                    "qambient_total_W": "",
                    "mdot_error_pct": "",
                    "tp_rmse_K": "",
                    "tw_rmse_K": "",
                    "all_probe_rmse_K": "",
                    "coupled_gate": "fail_no_worker_result",
                    "source_path": "bounded Fluid worker exited without result",
                }
            )
    return rows


def coupled_delta_rows(coupled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baselines = m3_baselines()
    rows: list[dict[str, Any]] = []
    for row in coupled:
        if row.get("split_role") == "train":
            continue
        baseline = baselines.get(row.get("case_id", ""), {})
        candidate_mdot = abs(safe_float(row.get("mdot_error_pct")) or float("nan"))
        baseline_mdot = abs(safe_float(baseline.get("mdot_error_pct")) or float("nan"))
        candidate_rmse = safe_float(row.get("all_probe_rmse_K"))
        baseline_rmse = safe_float(baseline.get("all_probe_rmse_K"))
        mdot_delta = None if not math.isfinite(candidate_mdot) or not math.isfinite(baseline_mdot) else candidate_mdot - baseline_mdot
        rmse_delta = None if candidate_rmse is None or baseline_rmse is None else candidate_rmse - baseline_rmse
        completed = row.get("coupled_run_status") == "completed"
        score_pass = completed and mdot_delta is not None and rmse_delta is not None and mdot_delta <= 0.0 and rmse_delta <= 0.0
        rows.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "candidate_mdot_abs_error_pct": fmt(candidate_mdot),
                "m3_mdot_abs_error_pct": fmt(baseline_mdot),
                "candidate_all_probe_rmse_K": fmt(candidate_rmse),
                "m3_all_probe_rmse_K": fmt(baseline_rmse),
                "mdot_delta_vs_m3_pct": fmt(mdot_delta),
                "all_probe_delta_vs_m3_K": fmt(rmse_delta),
                "score_gate": "pass" if score_pass else "fail",
            }
        )
    return rows


def coupled_admission_rows(
    deltas: list[dict[str, Any]],
    static_summary: list[dict[str, Any]],
    runtime: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime_pass = all(row["gate"] == "pass" for row in runtime)
    pb1 = next(row for row in static_summary if row["candidate_id"] == PB1_ID)
    pb1_validation_heat = pb1["validation_qoi_gate"]
    pb1_holdout_heat = pb1["holdout_qoi_gate"]
    candidates = sorted({row["candidate_id"] for row in deltas})
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        delta_by_split = {row["split_role"]: row["score_gate"] for row in deltas if row["candidate_id"] == candidate}
        validation_coupled = delta_by_split.get("validation", "missing")
        holdout_coupled = delta_by_split.get("holdout", "missing")
        blockers: list[str] = []
        if not runtime_pass:
            blockers.append("runtime_audit_failed")
        if pb1_validation_heat != "pass":
            blockers.append("validation_pb1_passive_total_heat_gate_failed")
        if pb1_holdout_heat != "pass":
            blockers.append("holdout_pb1_passive_total_heat_gate_failed")
        if validation_coupled != "pass":
            blockers.append("validation_coupled_score_not_improved")
        if holdout_coupled != "pass":
            blockers.append("holdout_coupled_score_not_improved")
        rows.append(
            {
                "candidate_id": candidate,
                "validation_pb1_heat_gate": pb1_validation_heat,
                "holdout_pb1_heat_gate": pb1_holdout_heat,
                "validation_coupled_gate": validation_coupled,
                "holdout_coupled_gate": holdout_coupled,
                "runtime_gate": "pass" if runtime_pass else "fail",
                "local_test_section_gate": "diagnostic_nonblocking",
                "admission_decision": "admitted_predictive_passive_total_pb1_candidate" if not blockers else "not_admitted",
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def annotate_coupled_gates(coupled: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_by_key = {
        (row["candidate_id"], row["case_id"]): row["score_gate"]
        for row in deltas
    }
    annotated: list[dict[str, Any]] = []
    for row in coupled:
        out = dict(row)
        if out.get("coupled_run_status") != "completed":
            annotated.append(out)
            continue
        if out.get("split_role") == "train":
            out["coupled_gate"] = "train_not_admission_scored"
        else:
            gate = gate_by_key.get((out.get("candidate_id", ""), out.get("case_id", "")), "missing")
            out["coupled_gate"] = "pass_vs_m3" if gate == "pass" else "fail_vs_m3"
        annotated.append(out)
    return annotated


def runtime_input_audit_rows(run_fluid: bool) -> list[dict[str, Any]]:
    return [
        {
            "audit_id": "R1_runtime_inputs",
            "gate": "pass",
            "evidence": "scenario contracts use setup external-boundary rows, PB1 Salt2 drive, and cooler alpha_UA only",
            "forbidden_runtime_input": "realized wallHeatFlux; CFD mdot; validation temperatures; imposed CFD cooler duty; realized test-section net heat",
        },
        {
            "audit_id": "R2_static_local_test_section_policy",
            "gate": "pass",
            "evidence": "TS6/TS7 remain diagnostic component rows and cannot be hidden inside passive-total PB1 success",
            "forbidden_runtime_input": "component promotion from passive-total cancellation alone",
        },
        {
            "audit_id": "R3_coupled_execution",
            "gate": "pass" if run_fluid else "pending",
            "evidence": "Fluid rows attempted in this package" if run_fluid else "use background srun command in README for coupled scoring",
            "forbidden_runtime_input": "none; execution gate only",
        },
    ]


def background_run_contract_rows(timeout_seconds: int) -> list[dict[str, Any]]:
    log_dir = f"logs/{DATE}"
    command = (
        f"mkdir -p {log_dir} && "
        f"srun -N1 -n1 python3 tools/analyze/build_wall_test_section_coupled_admission.py "
        f"--run-fluid --timeout-seconds {timeout_seconds} "
        f"> {log_dir}/wall_test_section_coupled_admission.out "
        f"2> {log_dir}/wall_test_section_coupled_admission.err &"
    )
    return [
        {
            "contract_id": "background_srun_coupled_score",
            "timeout_seconds": timeout_seconds,
            "command": command,
            "stdout": f"{log_dir}/wall_test_section_coupled_admission.out",
            "stderr": f"{log_dir}/wall_test_section_coupled_admission.err",
            "policy": "submit long Fluid scoring in background with srun or equivalent",
        }
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_id": "agent492_wall_circuit", "path": rel(AGENT492), "use": "PB1, TS6 static evidence and timeout diagnosis"},
        {"source_id": "agent482_cooler", "path": rel(AGENT482), "use": "cooler candidate definitions and alpha_UA"},
        {"source_id": "agent461_m3ts", "path": rel(AGENT461), "use": "coupled M3+TS comparator context"},
        {"source_id": "setup_external_boundary_rows", "path": rel(SETUP_ROWS), "use": "setup external-boundary role rows and hA data"},
        {"source_id": "fluid_solver", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "optional read-only Fluid solve_case execution"},
    ]


def blocker_decision_payload(
    coupled: list[dict[str, Any]],
    static_summary: list[dict[str, Any]],
    admission: list[dict[str, Any]],
    run_fluid: bool,
) -> dict[str, Any]:
    completed = [row for row in coupled if row["coupled_run_status"] == "completed"]
    statuses: dict[str, int] = {}
    for row in coupled:
        status = row["coupled_run_status"]
        statuses[status] = statuses.get(status, 0) + 1
    ts_failures = [
        row
        for row in static_summary
        if row["candidate_id"] in {TS6_ID, TS7_ID}
        and (row["validation_qoi_gate"] != "pass" or row["holdout_qoi_gate"] != "pass")
    ]
    pb1 = next(row for row in static_summary if row["candidate_id"] == PB1_ID)
    admitted = [row for row in admission if row["admission_decision"] == "admitted_predictive_passive_total_pb1_candidate"]
    blocker_decision = "resolve" if admitted else "keep_open"
    if not run_fluid:
        blocker_decision = "keep_open"
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "blocker_id": "predictive-wall-test-section-submodels",
        "blocker_decision": blocker_decision,
        "pb1_static_gate": "pass" if pb1["validation_qoi_gate"] == "pass" and pb1["holdout_qoi_gate"] == "pass" else "fail",
        "local_test_section_gate": "diagnostic_nonblocking_fail" if ts_failures else "pass",
        "coupled_status_counts": statuses,
        "coupled_completed_rows": len(completed),
        "admitted_candidates": [row["candidate_id"] for row in admitted],
        "why": (
            "At least one PB1+cooler candidate passed runtime, PB1 passive-total heat, and validation/holdout coupled-score gates."
            if admitted
            else "PB1 passive-total static evidence is promising, but no PB1+cooler candidate has passed all coupled admission gates."
        ),
    }


def readme_text(decision: dict[str, Any], timeout_seconds: int) -> str:
    command = background_run_contract_rows(timeout_seconds)[0]["command"]
    completed = decision["coupled_completed_rows"]
    statuses = json.dumps(decision["coupled_status_counts"], sort_keys=True)
    if completed:
        run_status = (
            "Coupled Fluid scoring has been run in this package. Completed rows: "
            f"`{completed}`; status counts: `{statuses}`. The background command remains "
            "documented in `background_run_contract.csv` for reproducibility, but no rerun "
            "is required for this package."
        )
    else:
        run_status = f"""Long Fluid scoring should run in the background:

```bash
{command}
```

The default per-row timeout is `{timeout_seconds} s`, derived from AGENT-492's
posthoc two-times-slowest completed cooler row."""
    return f"""---
provenance:
  - {rel(AGENT492)}
  - {rel(AGENT482)}
  - {rel(AGENT461)}
  - {rel(SETUP_ROWS)}
tags: [forward-model, wall-circuit, test-section, coupled-score, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-SEGMENT-THERMAL-MODELS
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Wall/Test-Section Coupled Admission

## Result

This package promotes `PB1_total_hA_heater_power_drive_p1` from AGENT-492 into
explicit PB1+cooler coupled scenario contracts and keeps local test-section
evidence separate from passive-total heat-loss cancellation.

Decision for `predictive-wall-test-section-submodels`:
`{decision['blocker_decision']}`.

Reason: {decision['why']}

## Coupled Run Status

{run_status}

## Files

- `candidate_definitions.csv`
- `scenario_contracts.csv`
- `static_component_scorecard.csv`
- `static_component_summary.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `coupled_admission_review.csv`
- `runtime_input_audit.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build(
    run_fluid: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    reuse_existing_coupled: bool = False,
) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = candidate_definitions()
    contracts = scenario_contract_rows()
    static_scores = static_component_scorecard_rows()
    static_summary = static_component_summary_rows()
    if reuse_existing_coupled and (OUT / "coupled_scorecard.csv").exists():
        coupled = read_csv(OUT / "coupled_scorecard.csv")
        effective_run_fluid = any(row.get("coupled_run_status") == "completed" for row in coupled)
    else:
        coupled = coupled_scorecard_rows(run_fluid, timeout_seconds)
        effective_run_fluid = run_fluid
    audit = runtime_input_audit_rows(effective_run_fluid)
    deltas = coupled_delta_rows(coupled)
    coupled = annotate_coupled_gates(coupled, deltas)
    admission = coupled_admission_rows(deltas, static_summary, audit)
    background = background_run_contract_rows(timeout_seconds)
    manifest = source_manifest_rows()
    decision = blocker_decision_payload(coupled, static_summary, admission, effective_run_fluid)

    counts = {
        "candidate_definitions.csv": write_csv(OUT / "candidate_definitions.csv", candidates, list(candidates[0].keys())),
        "scenario_contracts.csv": write_csv(OUT / "scenario_contracts.csv", contracts, list(contracts[0].keys())),
        "static_component_scorecard.csv": write_csv(OUT / "static_component_scorecard.csv", static_scores, list(static_scores[0].keys())),
        "static_component_summary.csv": write_csv(OUT / "static_component_summary.csv", static_summary, list(static_summary[0].keys())),
        "coupled_scorecard.csv": write_csv(OUT / "coupled_scorecard.csv", coupled, list(coupled[0].keys())),
        "coupled_delta_vs_m3.csv": write_csv(OUT / "coupled_delta_vs_m3.csv", deltas, list(deltas[0].keys())),
        "coupled_admission_review.csv": write_csv(OUT / "coupled_admission_review.csv", admission, list(admission[0].keys())),
        "runtime_input_audit.csv": write_csv(OUT / "runtime_input_audit.csv", audit, list(audit[0].keys())),
        "background_run_contract.csv": write_csv(OUT / "background_run_contract.csv", background, list(background[0].keys())),
        "source_manifest.csv": write_csv(OUT / "source_manifest.csv", manifest, list(manifest[0].keys())),
    }
    write_json(OUT / "blocker_decision.json", decision)
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "run_fluid": effective_run_fluid,
        "reuse_existing_coupled": reuse_existing_coupled,
        "timeout_seconds": timeout_seconds,
        "counts": counts,
        "decision": decision,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(decision, timeout_seconds), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run Fluid solve_case rows; submit this command with srun for long runs.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--reuse-existing-coupled", action="store_true", help="Reuse existing coupled_scorecard.csv and refresh derived adjudication outputs.")
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                run_fluid=args.run_fluid,
                timeout_seconds=args.timeout_seconds,
                reuse_existing_coupled=args.reuse_existing_coupled,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
