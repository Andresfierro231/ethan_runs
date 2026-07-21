#!/usr/bin/env python3
"""Build AGENT-529 leave-Salt3-out heater-source redistribution score package."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import math
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-529"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score")
OUT = ROOT / OUT_REL
LOG_DIR = ROOT / "logs/2026-07-17"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_wall_test_section_distribution_ladder as ladder

TRAIN_CASES = ("salt_1", "salt_2", "salt_4")
HOLDOUT_CASES = ("salt_3",)
NOMINAL_CASES = ("salt_1", "salt_2", "salt_3", "salt_4")
BLIND_CASES = ("salt2_lo5q", "salt2_hi5q", "val_salt2")
FUTURE_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q", "new_cfd_pm10_matrix")
CASE_NAME = {"salt_1": "Salt 1", "salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}
CASE_ORDER = {"salt_1": 0, "salt_2": 1, "salt_4": 2, "salt_3": 3}
SPLIT_ROLE = {
    "salt_1": "train_nominal_loso",
    "salt_2": "train_nominal_loso",
    "salt_4": "train_nominal_loso",
    "salt_3": "nominal_holdout_loso",
    "salt2_lo5q": "blind_holdout_pm5q",
    "salt2_hi5q": "blind_holdout_pm5q",
    "val_salt2": "blind_external_val_salt2",
}

BASELINE_LANE = "HS1_BASELINE_LOSO_SALT124"
PB2_LANE = "HS1_PB2_LOSO_SALT124"
PRIMARY_COOLER_ID = "HX_LUMPED_UA_NTU"
DEFAULT_TIMEOUT_SECONDS = 273
DEFAULT_PARALLEL_WORKERS = 8
LAMBDA_GRID = [round(index * 0.05, 2) for index in range(21)]
UPSTREAM_WEIGHTS = {"tw4_to_tw5": 0.60, "tw5_to_tw6": 0.30, "tw6_to_tp3": 0.10}
DOWNSTREAM_WEIGHTS = {"tw4_to_tw5": 0.20, "tw5_to_tw6": 0.35, "tw6_to_tp3": 0.45}

AGENT481 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy"
AGENT511 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score"
AGENT482 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model"
PM5_LEDGER = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger"
VAL_SALT2_PROGRESS = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress"

SCORE_FIELDS = [
    "phase",
    "lane_id",
    "candidate_id",
    "case_id",
    "fluid_case_name",
    "split_role",
    "heater_lambda",
    "cooler_candidate_id",
    "coupled_run_status",
    "elapsed_s",
    "root_status",
    "qhx_total_W",
    "qambient_total_W",
    "mdot_error_pct",
    "tp_rmse_K",
    "tw_rmse_K",
    "all_probe_rmse_K",
    "coupled_gate",
    "source_path",
]

PROBE_FIELDS = [
    "phase",
    "lane_id",
    "candidate_id",
    "case_id",
    "split_role",
    "heater_lambda",
    "cooler_candidate_id",
    "sensor",
    "kind",
    "predicted_K",
    "target_K",
    "error_K",
    "abs_error_K",
    "prediction_source_segment",
    "prediction_source_fraction",
    "validation_excluded",
    "source_path",
]


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


def lambda_label(value: float) -> str:
    return f"{value:.2f}".replace(".", "p")


def heater_weights(lambda_value: float) -> dict[str, float]:
    if lambda_value < -1e-12 or lambda_value > 1.0 + 1e-12:
        raise ValueError(f"lambda must be in [0, 1], got {lambda_value}")
    weights = {
        key: (1.0 - lambda_value) * UPSTREAM_WEIGHTS[key] + lambda_value * DOWNSTREAM_WEIGHTS[key]
        for key in UPSTREAM_WEIGHTS
    }
    total = sum(weights.values())
    return {key: value / total for key, value in weights.items()}


def candidate_id(lambda_value: float, lane_id: str = BASELINE_LANE) -> str:
    return f"{lane_id}_heater_source_lam_{lambda_label(lambda_value)}_PLUS_{PRIMARY_COOLER_ID}"


def _path_exists(path: Path) -> str:
    return "yes" if path.exists() else "no"


def _external_bc_cases() -> set[str]:
    if not ladder.SETUP_ROWS.exists():
        return set()
    return {row.get("case_id", "") for row in read_csv(ladder.SETUP_ROWS)}


def case_split_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in NOMINAL_CASES:
        rows.append(
            {
                "case_id": case_id,
                "fluid_case_name": CASE_NAME[case_id],
                "split_role": SPLIT_ROLE[case_id],
                "fit_allowed": "yes" if case_id in TRAIN_CASES else "no",
                "model_selection_allowed": "yes" if case_id in TRAIN_CASES else "no",
                "score_allowed": "yes",
                "fluid_adapter_status": "executable_nominal_fluid_case",
                "release_gate": "none",
                "source_path": f"{rel(AGENT481)};{rel(FLUID_ROOT / 'tamu_loop_model_v2/config_loader.py')}",
            }
        )
    for case_id in BLIND_CASES:
        rows.append(
            {
                "case_id": case_id,
                "fluid_case_name": "",
                "split_role": SPLIT_ROLE[case_id],
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "score_allowed": "yes",
                "fluid_adapter_status": "blocked_no_fluid_case_adapter",
                "release_gate": "score_pending_no_fluid_case_adapter",
                "source_path": f"{rel(AGENT481)};{rel(PM5_LEDGER)};{rel(VAL_SALT2_PROGRESS)}",
            }
        )
    for case_id in FUTURE_CASES:
        rows.append(
            {
                "case_id": case_id,
                "fluid_case_name": "",
                "split_role": "future_holdout_or_external",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "score_allowed": "deferred",
                "fluid_adapter_status": "future_not_available",
                "release_gate": "future_cfd_or_adapter_not_available",
                "source_path": rel(AGENT481),
            }
        )
    return rows


def case_contract_readiness_rows() -> list[dict[str, Any]]:
    external_cases = _external_bc_cases()
    rows: list[dict[str, Any]] = []
    for case_id in NOMINAL_CASES:
        rows.append(
            {
                "lane_id": BASELINE_LANE,
                "case_id": case_id,
                "required_contract": "Fluid EXPERIMENT_CASES nominal case",
                "readiness": "pass",
                "blocking_reason": "",
                "source_path": rel(FLUID_ROOT / "tamu_loop_model_v2/config_loader.py"),
            }
        )
        rows.append(
            {
                "lane_id": PB2_LANE,
                "case_id": case_id,
                "required_contract": "external_boundary_table role rows",
                "readiness": "pass" if case_id in external_cases else "fail",
                "blocking_reason": "" if case_id in external_cases else "missing Salt1 external-boundary role rows",
                "source_path": rel(ladder.SETUP_ROWS),
            }
        )
    for case_id in BLIND_CASES:
        rows.append(
            {
                "lane_id": BASELINE_LANE,
                "case_id": case_id,
                "required_contract": "Fluid executable perturbation/external adapter",
                "readiness": "fail",
                "blocking_reason": "no Fluid case adapter for this score-only row",
                "source_path": f"{rel(AGENT481)};{rel(PM5_LEDGER)};{rel(VAL_SALT2_PROGRESS)}",
            }
        )
    return rows


def candidate_definition_rows() -> list[dict[str, Any]]:
    return [
        {
            "lane_id": BASELINE_LANE,
            "implementation_status": "executable_now",
            "fit_parameter_count_this_package": 1,
            "fit_parameter_names_this_package": "heater_lambda",
            "fit_cases": ",".join(TRAIN_CASES),
            "holdout_cases": ",".join(HOLDOUT_CASES),
            "frozen_submodels": "Fluid default predictive wall/ambient setup;HX_LUMPED_UA_NTU alpha_UA from prior Salt2-only cooler package",
            "scientific_use": "split-corrected heater-source model-selection and nominal Salt3 holdout screen",
            "source_path": f"{rel(AGENT482)};{rel(FLUID_ROOT / 'tamu_loop_model_v2/solver.py')}",
        },
        {
            "lane_id": PB2_LANE,
            "implementation_status": "blocked_missing_salt1_external_boundary_rows",
            "fit_parameter_count_this_package": 1,
            "fit_parameter_names_this_package": "heater_lambda",
            "fit_cases": ",".join(TRAIN_CASES),
            "holdout_cases": ",".join(HOLDOUT_CASES),
            "frozen_submodels": "PB2 external-boundary distribution;HX_LUMPED_UA_NTU alpha_UA",
            "scientific_use": "same split with PB2 wall distribution after Salt1 boundary contract exists",
            "source_path": rel(ladder.SETUP_ROWS),
        },
    ]


def heater_source_lambda_grid_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in LAMBDA_GRID:
        weights = heater_weights(value)
        rows.append(
            {
                "lane_id": BASELINE_LANE,
                "candidate_id": candidate_id(value),
                "heater_lambda": fmt(value, 2),
                "fit_case_ids": ",".join(TRAIN_CASES),
                "holdout_case_ids": ",".join(HOLDOUT_CASES),
                "fit_parameter_count": 1,
                "tw4_to_tw5_weight": fmt(weights["tw4_to_tw5"]),
                "tw5_to_tw6_weight": fmt(weights["tw5_to_tw6"]),
                "tw6_to_tp3_weight": fmt(weights["tw6_to_tp3"]),
                "weight_sum": fmt(sum(weights.values())),
                "model_form": "weights(lambda)=(1-lambda)*upstream+lambda*downstream; upstream=(0.60,0.30,0.10); downstream=(0.20,0.35,0.45)",
                "runtime_policy": "train/select lambda on Salt1/Salt2/Salt4 only; Salt3 and blind rows score-only",
            }
        )
    return rows


def _contract(lambda_value: float, case_id: str, phase: str) -> dict[str, Any]:
    weights = heater_weights(lambda_value)
    payload = {"heater_source_weights_by_span": weights}
    return {
        "phase": phase,
        "lane_id": BASELINE_LANE,
        "candidate_id": candidate_id(lambda_value),
        "case_id": case_id,
        "fluid_case_name": CASE_NAME[case_id],
        "split_role": SPLIT_ROLE[case_id],
        "heater_lambda": fmt(lambda_value, 2),
        "cooler_candidate_id": PRIMARY_COOLER_ID,
        "tw4_to_tw5_weight": fmt(weights["tw4_to_tw5"]),
        "tw5_to_tw6_weight": fmt(weights["tw5_to_tw6"]),
        "tw6_to_tp3_weight": fmt(weights["tw6_to_tp3"]),
        "hx_ua_multiplier": fmt(ladder.fit_alpha_ua()),
        "outer_closure_mode": "Fluid default predictive_airside_ins_1.0in_rad_0",
        "heater_source_mode": "tw4_to_tp3_three_span",
        "parallel_group": "ag529_heater_source_loso",
        "runtime_input_violations": 0,
        "runtime_inputs": "setup_heater_power;candidate_lambda;Fluid_default_wall_outer_closure;frozen_Salt2_HX_LUMPED_UA_NTU_alpha_UA",
        "fit_allowed_for_this_case": "yes" if case_id in TRAIN_CASES else "no",
        "model_selection_allowed_for_this_case": "yes" if case_id in TRAIN_CASES else "no",
        "scenario_json": json.dumps(payload, sort_keys=True),
        "source_path": f"{rel(AGENT482)};{rel(FLUID_ROOT / 'tamu_loop_model_v2/solver.py')}",
    }


def scenario_contract_rows(selected_lambda: float | None = None) -> list[dict[str, Any]]:
    rows = [
        _contract(value, case_id, "loso_train_grid")
        for value in LAMBDA_GRID
        for case_id in TRAIN_CASES
    ]
    if selected_lambda is not None:
        rows.extend(_contract(selected_lambda, case_id, "selected_nominal_score") for case_id in NOMINAL_CASES)
    return rows


def runtime_input_audit_rows(contracts: list[dict[str, Any]], run_fluid: bool, parallel_workers: int) -> list[dict[str, Any]]:
    train_grid = [row for row in contracts if row.get("phase") == "loso_train_grid"]
    selected = [row for row in contracts if row.get("phase") == "selected_nominal_score"]
    fit_case_ids = {row.get("case_id") for row in train_grid}
    selected_for_fit = {row.get("case_id") for row in selected if row.get("model_selection_allowed_for_this_case") == "yes"}
    forbidden = [
        "Salt3 fitting target",
        "Salt3 model-selection target",
        "Salt2 +/-5Q fitting target",
        "val_salt2 fitting target",
        "CFD mdot",
        "validation/holdout probe temperatures",
        "realized wallHeatFlux",
        "imposed CFD cooler duty",
    ]
    return [
        {
            "audit_id": "R1_training_split",
            "gate": "pass" if fit_case_ids == set(TRAIN_CASES) else "fail",
            "evidence": f"loso_train_grid cases={','.join(sorted(fit_case_ids))}",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R2_no_holdout_or_blind_fit",
            "gate": "pass" if "salt_3" not in fit_case_ids and not (selected_for_fit - set(TRAIN_CASES)) else "fail",
            "evidence": "Salt3, Salt2 +/-5Q, and val_salt2 are absent from fit/model-selection rows",
            "forbidden_runtime_input": "holdout/external leakage into fit or model selection",
        },
        {
            "audit_id": "R3_runtime_inputs",
            "gate": "pass" if all(int(row.get("runtime_input_violations", 0)) == 0 for row in contracts) else "fail",
            "evidence": f"{len(contracts)} executable rows use setup heater power, candidate lambda, Fluid default wall setup, and frozen cooler alpha_UA",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R4_parallel_policy",
            "gate": "pass" if 1 <= parallel_workers <= 16 else "fail",
            "evidence": f"parallel_workers={parallel_workers}; conservative cap is 16",
            "forbidden_runtime_input": "unbounded parallelism;login-node Fluid solve",
        },
        {
            "audit_id": "R5_coupled_execution",
            "gate": "pass" if run_fluid else "pending",
            "evidence": "Fluid rows run in this package" if run_fluid else "bounded sbatch/srun execution required for coupled score",
            "forbidden_runtime_input": "execution gate only",
        },
    ]


def _pending_score(contract: dict[str, Any]) -> dict[str, Any]:
    row = {field: "" for field in SCORE_FIELDS}
    row.update(
        {
            "phase": contract["phase"],
            "lane_id": contract["lane_id"],
            "candidate_id": contract["candidate_id"],
            "case_id": contract["case_id"],
            "fluid_case_name": contract["fluid_case_name"],
            "split_role": contract["split_role"],
            "heater_lambda": contract["heater_lambda"],
            "cooler_candidate_id": contract["cooler_candidate_id"],
            "coupled_run_status": "not_run_submit_background_sbatch",
            "coupled_gate": "pending_background_fluid_score",
        }
    )
    return row


def _fluid_worker(contract: dict[str, Any], queue: Any) -> None:
    started = time.monotonic()
    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        if str(FLUID_ROOT) not in sys.path:
            sys.path.insert(0, str(FLUID_ROOT))
        from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME, default_scenarios
        from tamu_loop_model_v2.reporting import build_validation_table
        from tamu_loop_model_v2 import solver

        cases = {case.name: case for case in EXPERIMENT_CASES}
        base = next(s for s in default_scenarios() if s.name == "predictive_airside_ins_1.0in_rad_0")
        payload = json.loads(contract["scenario_json"])
        scenario = solver.ScenarioConfig(
            **{
                **base.__dict__,
                "name": contract["candidate_id"],
                "model_mode": "predictive_airside_hx",
                "imposed_qhx_W": None,
                "hx_ua_multiplier": safe_float(contract["hx_ua_multiplier"]) or 1.0,
                "heater_source_mode": "tw4_to_tp3_three_span",
                "heater_source_weights_by_span": payload["heater_source_weights_by_span"],
            }
        )
        case = cases[contract["fluid_case_name"]]
        result = solver.solve_case(case, scenario)
        validation = VALIDATION_CASES_BY_NAME.get(case.name)
        table = build_validation_table(result, validation)
        valid = table[~table["validation_excluded"]].copy()
        probe_rows: list[dict[str, Any]] = []
        for probe in table.to_dict("records"):
            error = safe_float(probe.get("error_K"))
            probe_rows.append(
                {
                    "phase": contract["phase"],
                    "lane_id": contract["lane_id"],
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "heater_lambda": contract["heater_lambda"],
                    "cooler_candidate_id": contract["cooler_candidate_id"],
                    "sensor": probe.get("sensor", ""),
                    "kind": probe.get("kind", ""),
                    "predicted_K": fmt(probe.get("predicted_K")),
                    "target_K": fmt(probe.get("measured_K")),
                    "error_K": fmt(error),
                    "abs_error_K": fmt(None if error is None else abs(error)),
                    "prediction_source_segment": probe.get("prediction_source_segment", ""),
                    "prediction_source_fraction": fmt(probe.get("prediction_source_fraction")),
                    "validation_excluded": "yes" if bool(probe.get("validation_excluded")) else "no",
                    "source_path": "Fluid build_validation_table with AGENT-529 LOSO heater-source scenario",
                }
            )
        tp = valid[valid["kind"] == "TP"]["error_K"]
        tw = valid[valid["kind"] == "TW"]["error_K"]
        all_err = valid["error_K"]
        measured_mdot = None if validation is None else validation.measured_mass_flow_rate_kg_s
        mdot_error_pct = None if measured_mdot in (None, 0.0) else 100.0 * (result.mdot_kg_s - measured_mdot) / measured_mdot
        queue.put(
            {
                "score": {
                    "phase": contract["phase"],
                    "lane_id": contract["lane_id"],
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "fluid_case_name": contract["fluid_case_name"],
                    "split_role": contract["split_role"],
                    "heater_lambda": contract["heater_lambda"],
                    "cooler_candidate_id": contract["cooler_candidate_id"],
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
                    "source_path": "Fluid solve_case with AGENT-529 LOSO heater-source scenario",
                },
                "probes": probe_rows,
            }
        )
    except Exception as exc:  # pragma: no cover - Fluid failures are environment dependent.
        row = {field: "" for field in SCORE_FIELDS}
        row.update(
            {
                "phase": contract.get("phase", ""),
                "lane_id": contract.get("lane_id", ""),
                "candidate_id": contract.get("candidate_id", ""),
                "case_id": contract.get("case_id", ""),
                "fluid_case_name": contract.get("fluid_case_name", ""),
                "split_role": contract.get("split_role", ""),
                "heater_lambda": contract.get("heater_lambda", ""),
                "cooler_candidate_id": contract.get("cooler_candidate_id", ""),
                "coupled_run_status": "error",
                "elapsed_s": fmt(time.monotonic() - started),
                "coupled_gate": "fail_solver_error",
                "source_path": f"{type(exc).__name__}: {exc}",
            }
        )
        queue.put({"score": row, "probes": []})


def _run_contract_with_timeout(contract: dict[str, Any], timeout_seconds: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    queue: mp.Queue = mp.Queue()
    process = mp.Process(target=_fluid_worker, args=(contract, queue))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(10)
        row = {field: "" for field in SCORE_FIELDS}
        row.update(
            {
                "phase": contract["phase"],
                "lane_id": contract["lane_id"],
                "candidate_id": contract["candidate_id"],
                "case_id": contract["case_id"],
                "fluid_case_name": contract["fluid_case_name"],
                "split_role": contract["split_role"],
                "heater_lambda": contract["heater_lambda"],
                "cooler_candidate_id": contract["cooler_candidate_id"],
                "coupled_run_status": f"timeout_after_{timeout_seconds}s",
                "elapsed_s": fmt(timeout_seconds),
                "coupled_gate": "fail_solver_timeout",
                "source_path": "bounded Fluid solve_case attempt timed out",
            }
        )
        return row, []
    if not queue.empty():
        payload = queue.get()
        return payload["score"], payload.get("probes", [])
    row = {field: "" for field in SCORE_FIELDS}
    row.update(
        {
            "phase": contract["phase"],
            "lane_id": contract["lane_id"],
            "candidate_id": contract["candidate_id"],
            "case_id": contract["case_id"],
            "fluid_case_name": contract["fluid_case_name"],
            "split_role": contract["split_role"],
            "heater_lambda": contract["heater_lambda"],
            "cooler_candidate_id": contract["cooler_candidate_id"],
            "coupled_run_status": "error_no_worker_result",
            "coupled_gate": "fail_no_worker_result",
            "source_path": "bounded Fluid worker exited without result",
        }
    )
    return row, []


def coupled_scorecard_rows(
    contracts: list[dict[str, Any]], run_fluid: bool, timeout_seconds: int, parallel_workers: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not run_fluid:
        return [_pending_score(row) for row in contracts], []
    max_workers = max(1, min(int(parallel_workers), 16, len(contracts)))
    rows: list[dict[str, Any]] = []
    probes: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_contract_with_timeout, contract, timeout_seconds) for contract in contracts]
        for future in concurrent.futures.as_completed(futures):
            score, probe_rows = future.result()
            rows.append(score)
            probes.extend(probe_rows)
    rows.sort(key=lambda row: (row.get("phase", ""), safe_float(row.get("heater_lambda")) or -1.0, CASE_ORDER.get(row.get("case_id", ""), 99)))
    probes.sort(key=lambda row: (row.get("phase", ""), safe_float(row.get("heater_lambda")) or -1.0, CASE_ORDER.get(row.get("case_id", ""), 99), row.get("kind", ""), row.get("sensor", "")))
    return rows, probes


def _completed_accepted(row: dict[str, Any]) -> bool:
    return (
        row.get("coupled_run_status") == "completed"
        and row.get("root_status") == "accepted"
        and safe_float(row.get("all_probe_rmse_K")) is not None
    )


def _completed_finite(row: dict[str, Any]) -> bool:
    return row.get("coupled_run_status") == "completed" and safe_float(row.get("all_probe_rmse_K")) is not None


def training_objective_by_lambda_rows(coupled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lambda_value in LAMBDA_GRID:
        lambda_text = fmt(lambda_value, 2)
        members = [
            row for row in coupled
            if row.get("phase") == "loso_train_grid" and row.get("heater_lambda") == lambda_text
        ]
        completed = [row for row in members if _completed_accepted(row)]
        finite = [row for row in members if _completed_finite(row)]
        all_cases = {row.get("case_id") for row in completed}
        finite_cases = {row.get("case_id") for row in finite}
        eligible = all_cases == set(TRAIN_CASES)
        diagnostic_eligible = finite_cases == set(TRAIN_CASES)
        mean_all = None
        mean_tw = None
        mean_mdot = None
        if eligible:
            mean_all = sum(safe_float(row.get("all_probe_rmse_K")) or 0.0 for row in completed) / len(completed)
            mean_tw = sum(safe_float(row.get("tw_rmse_K")) or 0.0 for row in completed) / len(completed)
            mean_mdot = sum(abs(safe_float(row.get("mdot_error_pct")) or 0.0) for row in completed) / len(completed)
        diagnostic_mean_all = None
        diagnostic_mean_tw = None
        diagnostic_mean_mdot = None
        if diagnostic_eligible:
            diagnostic_mean_all = sum(safe_float(row.get("all_probe_rmse_K")) or 0.0 for row in finite) / len(finite)
            diagnostic_mean_tw = sum(safe_float(row.get("tw_rmse_K")) or 0.0 for row in finite) / len(finite)
            diagnostic_mean_mdot = sum(abs(safe_float(row.get("mdot_error_pct")) or 0.0) for row in finite) / len(finite)
        rows.append(
            {
                "lane_id": BASELINE_LANE,
                "heater_lambda": lambda_text,
                "candidate_id": candidate_id(lambda_value),
                "completed_accepted_case_count": len(completed),
                "required_train_case_count": len(TRAIN_CASES),
                "completed_accepted_cases": ",".join(sorted(all_cases)),
                "selection_eligible": "yes" if eligible else "no",
                "objective_equal_case_mean_all_probe_rmse_K": fmt(mean_all),
                "tie_break_mean_tw_rmse_K": fmt(mean_tw),
                "tie_break_mean_abs_mdot_error_pct": fmt(mean_mdot),
                "completed_finite_case_count": len(finite),
                "completed_finite_cases": ",".join(sorted(finite_cases)),
                "diagnostic_selection_eligible": "yes" if diagnostic_eligible else "no",
                "diagnostic_equal_case_mean_all_probe_rmse_K": fmt(diagnostic_mean_all),
                "diagnostic_tie_break_mean_tw_rmse_K": fmt(diagnostic_mean_tw),
                "diagnostic_tie_break_mean_abs_mdot_error_pct": fmt(diagnostic_mean_mdot),
                "root_status_policy": "strict selection requires accepted roots for Salt1/Salt2/Salt4; finite rejected roots are diagnostic only",
            }
        )
    eligible_rows = [row for row in rows if row["selection_eligible"] == "yes"]
    eligible_rows.sort(
        key=lambda row: (
            safe_float(row.get("objective_equal_case_mean_all_probe_rmse_K")) or float("inf"),
            safe_float(row.get("tie_break_mean_tw_rmse_K")) or float("inf"),
            safe_float(row.get("tie_break_mean_abs_mdot_error_pct")) or float("inf"),
        )
    )
    rank_by_lambda = {row["heater_lambda"]: index + 1 for index, row in enumerate(eligible_rows)}
    for row in rows:
        row["objective_rank"] = rank_by_lambda.get(row["heater_lambda"], "")
    return rows


def select_lambda_from_training_rows(coupled: list[dict[str, Any]]) -> dict[str, Any]:
    objectives = training_objective_by_lambda_rows(coupled)
    eligible = [row for row in objectives if row["selection_eligible"] == "yes"]
    if not eligible:
        diagnostic = [row for row in objectives if row["diagnostic_selection_eligible"] == "yes"]
        if diagnostic:
            best_diagnostic = min(
                diagnostic,
                key=lambda row: (
                    safe_float(row.get("diagnostic_equal_case_mean_all_probe_rmse_K")) or float("inf"),
                    safe_float(row.get("diagnostic_tie_break_mean_tw_rmse_K")) or float("inf"),
                    safe_float(row.get("diagnostic_tie_break_mean_abs_mdot_error_pct")) or float("inf"),
                ),
            )
            value = safe_float(best_diagnostic["heater_lambda"]) or 0.0
            weights = heater_weights(value)
            return {
                "selection_status": "diagnostic_selected_from_salt1_salt2_salt4_finite_rows_with_root_rejections",
                "lane_id": BASELINE_LANE,
                "heater_lambda": fmt(value, 2),
                "selected_candidate_id": best_diagnostic["candidate_id"],
                "selection_metric": "diagnostic equal-case mean all_probe_rmse_K over finite Salt1/Salt2/Salt4 rows; tie TW then abs mdot",
                "train_objective_all_probe_rmse_K": best_diagnostic["diagnostic_equal_case_mean_all_probe_rmse_K"],
                "train_tie_break_tw_rmse_K": best_diagnostic["diagnostic_tie_break_mean_tw_rmse_K"],
                "train_tie_break_abs_mdot_error_pct": best_diagnostic["diagnostic_tie_break_mean_abs_mdot_error_pct"],
                "tw4_to_tw5_weight": fmt(weights["tw4_to_tw5"]),
                "tw5_to_tw6_weight": fmt(weights["tw5_to_tw6"]),
                "tw6_to_tp3_weight": fmt(weights["tw6_to_tp3"]),
                "selection_source": "Salt1/Salt2/Salt4 finite train rows only; Salt3/blind rows excluded",
                "root_status_policy": "diagnostic only because at least one train case root was rejected",
            }
        return {
            "selection_status": "pending_or_failed_no_complete_train_triplet",
            "lane_id": BASELINE_LANE,
            "heater_lambda": "",
            "selected_candidate_id": "",
            "selection_metric": "equal-case mean all_probe_rmse_K over Salt1/Salt2/Salt4; tie TW then abs mdot",
            "selection_source": "Salt1/Salt2/Salt4 train rows only; Salt3/blind rows excluded",
            "root_status_policy": "strict selection requires completed accepted roots for all three train cases",
        }
    best = min(
        eligible,
        key=lambda row: (
            safe_float(row.get("objective_equal_case_mean_all_probe_rmse_K")) or float("inf"),
            safe_float(row.get("tie_break_mean_tw_rmse_K")) or float("inf"),
            safe_float(row.get("tie_break_mean_abs_mdot_error_pct")) or float("inf"),
        ),
    )
    value = safe_float(best["heater_lambda"]) or 0.0
    weights = heater_weights(value)
    return {
        "selection_status": "selected_from_salt1_salt2_salt4_only",
        "lane_id": BASELINE_LANE,
        "heater_lambda": fmt(value, 2),
        "selected_candidate_id": best["candidate_id"],
        "selection_metric": "equal-case mean all_probe_rmse_K over Salt1/Salt2/Salt4; tie TW then abs mdot",
        "train_objective_all_probe_rmse_K": best["objective_equal_case_mean_all_probe_rmse_K"],
        "train_tie_break_tw_rmse_K": best["tie_break_mean_tw_rmse_K"],
        "train_tie_break_abs_mdot_error_pct": best["tie_break_mean_abs_mdot_error_pct"],
        "tw4_to_tw5_weight": fmt(weights["tw4_to_tw5"]),
        "tw5_to_tw6_weight": fmt(weights["tw5_to_tw6"]),
        "tw6_to_tp3_weight": fmt(weights["tw6_to_tp3"]),
        "selection_source": "Salt1/Salt2/Salt4 train rows only; Salt3/blind rows excluded",
        "root_status_policy": "strict selection used completed accepted roots for all three train cases",
    }


def selected_heater_source_weight_rows(selection: dict[str, Any]) -> list[dict[str, Any]]:
    return [selection]


def salt3_holdout_delta_vs_m3_rows(coupled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baselines = ladder.m3_baselines()
    rows: list[dict[str, Any]] = []
    for row in coupled:
        if row.get("phase") != "selected_nominal_score" or row.get("case_id") != "salt_3":
            continue
        baseline = baselines.get("salt_3", {})
        candidate_mdot = abs(safe_float(row.get("mdot_error_pct")) or float("nan"))
        baseline_mdot = abs(safe_float(baseline.get("mdot_error_pct")) or float("nan"))
        candidate_tp = safe_float(row.get("tp_rmse_K"))
        candidate_tw = safe_float(row.get("tw_rmse_K"))
        candidate_all = safe_float(row.get("all_probe_rmse_K"))
        baseline_tp = safe_float(baseline.get("tp_rmse_K"))
        baseline_tw = safe_float(baseline.get("tw_rmse_K"))
        baseline_all = safe_float(baseline.get("all_probe_rmse_K"))
        mdot_delta = None if not math.isfinite(candidate_mdot) or not math.isfinite(baseline_mdot) else candidate_mdot - baseline_mdot
        tp_delta = None if candidate_tp is None or baseline_tp is None else candidate_tp - baseline_tp
        tw_delta = None if candidate_tw is None or baseline_tw is None else candidate_tw - baseline_tw
        all_delta = None if candidate_all is None or baseline_all is None else candidate_all - baseline_all
        completed = row.get("coupled_run_status") == "completed"
        score_pass = (
            completed
            and mdot_delta is not None
            and tp_delta is not None
            and tw_delta is not None
            and all_delta is not None
            and mdot_delta <= 0.0
            and tp_delta <= 0.0
            and tw_delta <= 0.0
            and all_delta <= 0.0
        )
        rows.append(
            {
                "lane_id": row.get("lane_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "case_id": "salt_3",
                "split_role": row.get("split_role", ""),
                "heater_lambda": row.get("heater_lambda", ""),
                "candidate_mdot_abs_error_pct": fmt(candidate_mdot),
                "m3_mdot_abs_error_pct": fmt(baseline_mdot),
                "candidate_tp_rmse_K": fmt(candidate_tp),
                "m3_tp_rmse_K": fmt(baseline_tp),
                "candidate_tw_rmse_K": fmt(candidate_tw),
                "m3_tw_rmse_K": fmt(baseline_tw),
                "candidate_all_probe_rmse_K": fmt(candidate_all),
                "m3_all_probe_rmse_K": fmt(baseline_all),
                "mdot_delta_vs_m3_pct": fmt(mdot_delta),
                "tp_delta_vs_m3_K": fmt(tp_delta),
                "tw_delta_vs_m3_K": fmt(tw_delta),
                "all_probe_delta_vs_m3_K": fmt(all_delta),
                "score_gate": "pass" if score_pass else "fail",
            }
        )
    return rows


def annotate_coupled_gates(coupled: list[dict[str, Any]], holdout_deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    salt3_gate_by_candidate = {row["candidate_id"]: row["score_gate"] for row in holdout_deltas}
    out_rows: list[dict[str, Any]] = []
    for row in coupled:
        out = dict(row)
        if out.get("coupled_run_status") == "completed":
            if out.get("phase") == "loso_train_grid":
                out["coupled_gate"] = "train_grid_completed_not_holdout_scored"
            elif out.get("case_id") == "salt_3":
                out["coupled_gate"] = "pass_vs_m3" if salt3_gate_by_candidate.get(out.get("candidate_id", "")) == "pass" else "fail_vs_m3"
            else:
                out["coupled_gate"] = "selected_train_case_score_not_admission_gate"
        out_rows.append(out)
    return out_rows


def blind_perturbation_external_scorecard_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in BLIND_CASES:
        rows.append(
            {
                "lane_id": BASELINE_LANE,
                "case_id": case_id,
                "split_role": SPLIT_ROLE[case_id],
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "score_allowed": "yes",
                "prediction_source_status": "missing_fluid_case_adapter_for_loso_heater_source_candidate",
                "score_status": "blocked_pending_prediction_adapter",
                "blocking_reason": "current Fluid API exposes nominal Salt1-4 cases only for this runner",
                "source_path": f"{rel(AGENT481)};{rel(PM5_LEDGER)};{rel(VAL_SALT2_PROGRESS)}",
            }
        )
    return rows


def candidate_admission_review_rows(
    runtime: list[dict[str, Any]],
    selection: dict[str, Any],
    holdout: list[dict[str, Any]],
    blind: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime_pass = all(row["gate"] == "pass" for row in runtime)
    salt3_pass = any(row.get("score_gate") == "pass" for row in holdout)
    blind_ready = all(row.get("score_status") == "scored" for row in blind)
    blockers: list[str] = []
    if selection.get("selection_status") != "selected_from_salt1_salt2_salt4_only":
        blockers.append("strict_accepted_train_triplet_lambda_not_selected")
    if selection.get("selection_status", "").startswith("diagnostic_"):
        blockers.append("diagnostic_selection_uses_finite_rejected_train_root")
    if not runtime_pass:
        blockers.append("runtime_audit_failed_or_pending")
    if not salt3_pass:
        blockers.append("salt3_holdout_mdot_tp_tw_all_probe_gate_failed_or_missing")
    if not blind_ready:
        blockers.append("blind_pm5q_and_val_salt2_score_rows_pending_adapter")
    external_cases = _external_bc_cases()
    pb2_blockers = []
    if "salt_1" not in external_cases:
        pb2_blockers.append("missing_salt1_external_boundary_role_rows")
    return [
        {
            "lane_id": BASELINE_LANE,
            "candidate_id": selection.get("selected_candidate_id", ""),
            "heater_lambda": selection.get("heater_lambda", ""),
            "runtime_gate": "pass" if runtime_pass else "fail_or_pending",
            "salt3_holdout_gate": "pass" if salt3_pass else "fail_or_missing",
            "blind_score_gate": "pass" if blind_ready else "blocked_or_missing",
            "admission_decision": "admitted_heater_source_loso" if not blockers else "not_admitted",
            "blocking_reasons": ";".join(blockers),
        },
        {
            "lane_id": PB2_LANE,
            "candidate_id": "",
            "heater_lambda": selection.get("heater_lambda", ""),
            "runtime_gate": "blocked",
            "salt3_holdout_gate": "not_run",
            "blind_score_gate": "not_run",
            "admission_decision": "not_admitted",
            "blocking_reasons": ";".join(pb2_blockers or ["pb2_lane_not_selected_for_this_package"]),
        },
    ]


def background_run_contract_rows(timeout_seconds: int, parallel_workers: int) -> list[dict[str, Any]]:
    command = (
        f"sbatch {rel(OUT / 'ag529_heater_source_loso.sbatch')} "
        f"# or srun -N1 -n{parallel_workers} python3 tools/analyze/build_heater_source_leave_salt3_out_score.py "
        f"--run-fluid --parallel-workers {parallel_workers} --timeout-seconds {timeout_seconds}"
    )
    return [
        {
            "contract_id": "background_sbatch_coupled_score",
            "timeout_seconds": timeout_seconds,
            "parallel_workers": parallel_workers,
            "command": command,
            "stdout": f"logs/{DATE}/heater_source_leave_salt3_out_score.out",
            "stderr": f"logs/{DATE}/heater_source_leave_salt3_out_score.err",
            "policy": "submit bounded Fluid scoring through sbatch/srun on compute resources; do not run long coupled Fluid rows on login nodes",
        }
    ]


def sbatch_text(timeout_seconds: int, parallel_workers: int) -> str:
    log_dir = f"logs/{DATE}"
    return f"""#!/bin/bash
#SBATCH -J ag529_hs_loso
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy-dev
#SBATCH -N 1
#SBATCH -n {parallel_workers}
#SBATCH -t 02:00:00
#SBATCH -o {log_dir}/heater_source_leave_salt3_out_score.out
#SBATCH -e {log_dir}/heater_source_leave_salt3_out_score.err

set -euo pipefail
cd {ROOT}
mkdir -p {log_dir}
python3 tools/analyze/build_heater_source_leave_salt3_out_score.py --run-fluid --parallel-workers {parallel_workers} --timeout-seconds {timeout_seconds}
python3 tools/analyze/build_heater_source_leave_salt3_out_score.py --reuse-existing-coupled --parallel-workers {parallel_workers} --timeout-seconds {timeout_seconds}
"""


def source_manifest_rows() -> list[dict[str, Any]]:
    return [
        {"source_id": "canonical_split_policy", "path": rel(AGENT481), "exists": _path_exists(AGENT481), "use": "Salt1/Salt2/Salt4 train; Salt3 holdout; PM5 and val_salt2 score-only"},
        {"source_id": "agent511_salt2_only_precursor", "path": rel(AGENT511), "exists": _path_exists(AGENT511), "use": "prior heater-source code pattern and failure context only, not duplicated split"},
        {"source_id": "agent482_cooler", "path": rel(AGENT482), "exists": _path_exists(AGENT482), "use": "frozen constant-UA cooler alpha_UA"},
        {"source_id": "external_boundary_rows", "path": rel(ladder.SETUP_ROWS), "exists": _path_exists(ladder.SETUP_ROWS), "use": "PB2 lane readiness check; no Salt1 rows currently"},
        {"source_id": "m3_comparators", "path": rel(ladder.M3_COMPARATORS), "exists": _path_exists(ladder.M3_COMPARATORS), "use": "Salt3 holdout comparator"},
        {"source_id": "fluid_solver", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "exists": _path_exists(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "read-only solve_case execution"},
    ]


def blocker_decision_payload(
    coupled: list[dict[str, Any]],
    selection: dict[str, Any],
    admission: list[dict[str, Any]],
    run_fluid: bool,
) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for row in coupled:
        statuses[row["coupled_run_status"]] = statuses.get(row["coupled_run_status"], 0) + 1
    admitted = [row for row in admission if row["admission_decision"].startswith("admitted")]
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "blocker_id": "predictive-wall-test-section-submodels",
        "blocker_decision": "keep_open",
        "selection_status": selection.get("selection_status", ""),
        "selected_lambda": selection.get("heater_lambda", ""),
        "coupled_status_counts": statuses,
        "coupled_completed_rows": sum(1 for row in coupled if row["coupled_run_status"] == "completed"),
        "admitted_lanes": [row["lane_id"] for row in admitted],
        "why": (
            "This package corrects the train/holdout split for the heater-source redistribution screen. "
            "The predictive-wall-test-section-submodels blocker remains open until blind PM5Q/val_salt2 adapters exist and the PB2/Salt1 boundary contract is repaired."
        ),
        "run_fluid": run_fluid,
    }


def readme_text(summary: dict[str, Any]) -> str:
    decision = summary["decision"]
    return f"""---
provenance:
  - {rel(AGENT481)}
  - {rel(AGENT511)}
  - {rel(AGENT482)}
  - {rel(ladder.SETUP_ROWS)}
tags: [forward-model, heater-source, validation-split, salt3-holdout]
related:
  - predictive-wall-test-section-submodels
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Source Leave-Salt3-Out Score

This package reruns the heater-source redistribution screen with the corrected
split: Salt1/Salt2/Salt4 are the only fit/model-selection rows, Salt3 is the
nominal holdout, and Salt2 +/-5Q plus `val_salt2` remain blind score-only rows.

Decision for `predictive-wall-test-section-submodels`: `{decision['blocker_decision']}`.

Reason: {decision['why']}

Selected lambda: `{decision['selected_lambda']}`.
Selection status: `{decision['selection_status']}`.
Coupled status counts: `{json.dumps(decision['coupled_status_counts'], sort_keys=True)}`.

## Important Limits

The executable lane uses the current Fluid default predictive wall/outer setup
with the frozen constant-UA cooler from AGENT-482. The PB2 wall-distribution lane
is intentionally blocked here because the available external-boundary role table
has Salt2/Salt3/Salt4 rows but no Salt1 rows. Blind PM5Q and `val_salt2` rows are
not fit/model-selection inputs and remain blocked until an executable Fluid
adapter can produce frozen predictions for those cases.

## Files

- `case_split_contract.csv`
- `case_contract_readiness.csv`
- `candidate_definitions.csv`
- `heater_source_lambda_grid.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `training_objective_by_lambda.csv`
- `selected_heater_source_weights.csv`
- `nominal_coupled_scorecard.csv`
- `salt3_holdout_delta_vs_m3.csv`
- `blind_perturbation_external_scorecard.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `ag529_heater_source_loso.sbatch`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build(
    run_fluid: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    reuse_existing_coupled: bool = False,
    parallel_workers: int = DEFAULT_PARALLEL_WORKERS,
) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    split_rows = case_split_contract_rows()
    readiness = case_contract_readiness_rows()
    candidates = candidate_definition_rows()
    lambda_grid = heater_source_lambda_grid_rows()
    if reuse_existing_coupled and (OUT / "nominal_coupled_scorecard.csv").exists():
        coupled = read_csv(OUT / "nominal_coupled_scorecard.csv")
        probes = read_csv(OUT / "probe_error_localization.csv") if (OUT / "probe_error_localization.csv").exists() else []
        selection = select_lambda_from_training_rows(coupled)
        selected_value = safe_float(selection.get("heater_lambda"))
        contracts = scenario_contract_rows(selected_value)
        selected_contracts = scenario_contract_rows(selected_value)[len(LAMBDA_GRID) * len(TRAIN_CASES) :] if selected_value is not None else []
        existing_selected_keys = {
            (row.get("phase", ""), row.get("case_id", ""), row.get("heater_lambda", ""))
            for row in coupled
            if row.get("phase") == "selected_nominal_score"
        }
        missing_selected = [
            row for row in selected_contracts
            if (row.get("phase", ""), row.get("case_id", ""), row.get("heater_lambda", "")) not in existing_selected_keys
        ]
        if missing_selected:
            if run_fluid:
                selected_scores, selected_probes = coupled_scorecard_rows(missing_selected, True, timeout_seconds, parallel_workers)
                coupled.extend(selected_scores)
                probes.extend(selected_probes)
            else:
                coupled.extend(_pending_score(row) for row in missing_selected)
        effective_run_fluid = any(row.get("coupled_run_status") == "completed" for row in coupled)
    else:
        train_contracts = scenario_contract_rows(None)
        train_scores, train_probes = coupled_scorecard_rows(train_contracts, run_fluid, timeout_seconds, parallel_workers)
        selection = select_lambda_from_training_rows(train_scores)
        selected_value = safe_float(selection.get("heater_lambda"))
        selected_contracts = scenario_contract_rows(selected_value)[len(LAMBDA_GRID) * len(TRAIN_CASES) :] if selected_value is not None else []
        selected_scores, selected_probes = coupled_scorecard_rows(selected_contracts, run_fluid, timeout_seconds, parallel_workers)
        contracts = train_contracts + selected_contracts
        coupled = train_scores + selected_scores
        probes = train_probes + selected_probes
        effective_run_fluid = run_fluid
    objectives = training_objective_by_lambda_rows(coupled)
    runtime = runtime_input_audit_rows(contracts, effective_run_fluid, parallel_workers)
    holdout = salt3_holdout_delta_vs_m3_rows(coupled)
    coupled = annotate_coupled_gates(coupled, holdout)
    blind = blind_perturbation_external_scorecard_rows()
    admission = candidate_admission_review_rows(runtime, selection, holdout, blind)
    background = background_run_contract_rows(timeout_seconds, parallel_workers)
    manifest = source_manifest_rows()
    decision = blocker_decision_payload(coupled, selection, admission, effective_run_fluid)

    counts = {
        "case_split_contract.csv": write_csv(OUT / "case_split_contract.csv", split_rows, list(split_rows[0].keys())),
        "case_contract_readiness.csv": write_csv(OUT / "case_contract_readiness.csv", readiness, list(readiness[0].keys())),
        "candidate_definitions.csv": write_csv(OUT / "candidate_definitions.csv", candidates, list(candidates[0].keys())),
        "heater_source_lambda_grid.csv": write_csv(OUT / "heater_source_lambda_grid.csv", lambda_grid, list(lambda_grid[0].keys())),
        "scenario_contracts.csv": write_csv(OUT / "scenario_contracts.csv", contracts, list(contracts[0].keys()) if contracts else ["candidate_id"]),
        "runtime_input_audit.csv": write_csv(OUT / "runtime_input_audit.csv", runtime, list(runtime[0].keys())),
        "training_objective_by_lambda.csv": write_csv(OUT / "training_objective_by_lambda.csv", objectives, list(objectives[0].keys())),
        "selected_heater_source_weights.csv": write_csv(OUT / "selected_heater_source_weights.csv", selected_heater_source_weight_rows(selection), list(selection.keys())),
        "nominal_coupled_scorecard.csv": write_csv(OUT / "nominal_coupled_scorecard.csv", coupled, SCORE_FIELDS),
        "salt3_holdout_delta_vs_m3.csv": write_csv(OUT / "salt3_holdout_delta_vs_m3.csv", holdout, list(holdout[0].keys()) if holdout else ["candidate_id"]),
        "probe_error_localization.csv": write_csv(OUT / "probe_error_localization.csv", probes, PROBE_FIELDS),
        "blind_perturbation_external_scorecard.csv": write_csv(OUT / "blind_perturbation_external_scorecard.csv", blind, list(blind[0].keys())),
        "candidate_admission_review.csv": write_csv(OUT / "candidate_admission_review.csv", admission, list(admission[0].keys())),
        "background_run_contract.csv": write_csv(OUT / "background_run_contract.csv", background, list(background[0].keys())),
        "source_manifest.csv": write_csv(OUT / "source_manifest.csv", manifest, list(manifest[0].keys())),
    }
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "run_fluid": effective_run_fluid,
        "reuse_existing_coupled": reuse_existing_coupled,
        "timeout_seconds": timeout_seconds,
        "parallel_workers": parallel_workers,
        "counts": counts,
        "selection": selection,
        "decision": decision,
    }
    write_json(OUT / "blocker_decision.json", decision)
    write_json(OUT / "summary.json", summary)
    (OUT / "ag529_heater_source_loso.sbatch").write_text(sbatch_text(timeout_seconds, parallel_workers), encoding="utf-8")
    (OUT / "README.md").write_text(readme_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run Fluid solve_case rows; use compute-node srun/sbatch.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--reuse-existing-coupled", action="store_true")
    parser.add_argument("--parallel-workers", type=int, default=DEFAULT_PARALLEL_WORKERS)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                run_fluid=args.run_fluid,
                timeout_seconds=args.timeout_seconds,
                reuse_existing_coupled=args.reuse_existing_coupled,
                parallel_workers=args.parallel_workers,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
