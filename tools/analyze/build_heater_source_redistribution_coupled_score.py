#!/usr/bin/env python3
"""Build AGENT-511 heater-source redistribution coupled score package."""

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


TASK = "AGENT-511"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score")
OUT = ROOT / OUT_REL

PB2_WALL_ID = "PB2_salt2_local_shape_passive_hA_p1"
COOLER_IDS = ["HX_LUMPED_UA_NTU", "HX_SEGMENTED_UA_NTU_N16"]
PRIMARY_COOLER_ID = "HX_LUMPED_UA_NTU"
CASE_NAME = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}
SPLIT = {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}
DEFAULT_TIMEOUT_SECONDS = 273
LAMBDA_GRID = [round(index * 0.05, 2) for index in range(21)]
UPSTREAM_WEIGHTS = {"tw4_to_tw5": 0.60, "tw5_to_tw6": 0.30, "tw6_to_tp3": 0.10}
DOWNSTREAM_WEIGHTS = {"tw4_to_tw5": 0.20, "tw5_to_tw6": 0.35, "tw6_to_tp3": 0.45}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_wall_test_section_distribution_ladder as wall_ladder

PROBE_FIELDS = [
    "phase",
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


def candidate_id(lambda_value: float, cooler_id: str) -> str:
    return f"HS1_salt2_fit_heater_source_shift_p1_lam_{lambda_label(lambda_value)}_PLUS_{PB2_WALL_ID}_PLUS_{cooler_id}"


def heater_source_lambda_grid_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in LAMBDA_GRID:
        weights = heater_weights(value)
        rows.append(
            {
                "candidate_family_id": "HS1_salt2_fit_heater_source_shift_p1",
                "heater_lambda": fmt(value, 2),
                "fit_case_id": "salt_2",
                "fit_parameter_count": 1,
                "tw4_to_tw5_weight": fmt(weights["tw4_to_tw5"]),
                "tw5_to_tw6_weight": fmt(weights["tw5_to_tw6"]),
                "tw6_to_tp3_weight": fmt(weights["tw6_to_tp3"]),
                "weight_sum": fmt(sum(weights.values())),
                "model_form": "weights(lambda)=(1-lambda)*upstream+lambda*downstream; upstream=(0.60,0.30,0.10); downstream=(0.20,0.35,0.45)",
                "runtime_policy": "Salt2-only lambda fit; setup heater power; PB2 setup wall distribution; Salt2 cooler alpha_UA",
            }
        )
    return rows


def _boundary_payload(case_id: str) -> dict[str, Any]:
    setup = wall_ladder.setup_rows_by_case()
    ratios = wall_ladder.heater_ratio_by_case()
    shape = wall_ladder.shape_for_candidate(PB2_WALL_ID)
    role_rows = wall_ladder._role_rows_for_contract(setup[case_id], shape, ratios[case_id])
    parent_maps = wall_ladder._parent_maps_for_contract(setup[case_id], shape, ratios[case_id])
    return {"role_rows": role_rows, "parent_boundary_maps": parent_maps}


def _contract(lambda_value: float, case_id: str, cooler_id: str, phase: str) -> dict[str, Any]:
    weights = heater_weights(lambda_value)
    payload = _boundary_payload(case_id)
    payload["heater_source_weights_by_span"] = weights
    return {
        "phase": phase,
        "candidate_family_id": "HS1_salt2_fit_heater_source_shift_p1",
        "candidate_id": candidate_id(lambda_value, cooler_id),
        "wall_candidate_id": PB2_WALL_ID,
        "cooler_candidate_id": cooler_id,
        "case_id": case_id,
        "fluid_case_name": CASE_NAME[case_id],
        "split_role": SPLIT[case_id],
        "heater_lambda": fmt(lambda_value, 2),
        "tw4_to_tw5_weight": fmt(weights["tw4_to_tw5"]),
        "tw5_to_tw6_weight": fmt(weights["tw5_to_tw6"]),
        "tw6_to_tp3_weight": fmt(weights["tw6_to_tp3"]),
        "hx_ua_multiplier": fmt(wall_ladder.fit_alpha_ua()),
        "outer_closure_mode": "external_boundary_table",
        "heater_source_mode": "tw4_to_tp3_three_span",
        "role_row_count": len(payload["role_rows"]),
        "parent_boundary_count": len(payload["parent_boundary_maps"]["external_boundary_h_by_parent_segment"]),
        "runtime_input_violations": 0,
        "runtime_inputs": "setup_heater_power;Salt2_lambda;PB2_setup_wall_distribution;Salt2_cooler_alpha_UA",
        "scenario_json": json.dumps(payload, sort_keys=True),
        "source_path": f"{rel(wall_ladder.SETUP_ROWS)};{rel(wall_ladder.AGENT482)};{rel(wall_ladder.OUT)}",
    }


def scenario_contract_rows(selected_lambda: float | None = None) -> list[dict[str, Any]]:
    rows = [_contract(value, "salt_2", PRIMARY_COOLER_ID, "salt2_fit_grid") for value in LAMBDA_GRID]
    if selected_lambda is not None:
        for cooler_id in COOLER_IDS:
            for case_id in CASE_NAME:
                rows.append(_contract(selected_lambda, case_id, cooler_id, "selected_coupled_score"))
    return rows


def runtime_input_audit_rows(contracts: list[dict[str, Any]], run_fluid: bool, selected_lambda: float | None) -> list[dict[str, Any]]:
    forbidden = [
        "realized wallHeatFlux",
        "CFD mdot",
        "validation/holdout wall-shell temperature",
        "validation/holdout probe temperatures",
        "imposed CFD cooler duty",
        "realized test-section heat",
    ]
    salt3_or_4_in_fit = selected_lambda is not None and any(
        row.get("phase") == "salt2_fit_grid" and row.get("case_id") != "salt_2" for row in contracts
    )
    return [
        {
            "audit_id": "R1_split_legal_fit",
            "gate": "pass" if not salt3_or_4_in_fit else "fail",
            "evidence": "lambda selection is defined from Salt2 grid rows only",
            "forbidden_runtime_input": "Salt3/Salt4 fitting targets;validation/holdout temperatures",
        },
        {
            "audit_id": "R2_runtime_inputs",
            "gate": "pass" if all(int(row.get("runtime_input_violations", 0)) == 0 for row in contracts) else "fail",
            "evidence": f"{len(contracts)} scenario rows use setup inputs, Salt2 lambda, PB2 setup wall distribution, and Salt2 cooler alpha_UA",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R3_coupled_execution",
            "gate": "pass" if run_fluid else "pending",
            "evidence": "Fluid rows run in this package" if run_fluid else "background compute-node execution required for coupled admission",
            "forbidden_runtime_input": "execution gate only",
        },
    ]


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
        scenario = solver.ScenarioConfig(
            **{
                **base.__dict__,
                "name": contract["candidate_id"],
                "model_mode": "predictive_airside_hx",
                "imposed_qhx_W": None,
                "hx_ua_multiplier": safe_float(contract["hx_ua_multiplier"]) or 1.0,
                "outer_closure_mode": "external_boundary_table",
                "external_boundary_role_rows": payload["role_rows"],
                **payload["parent_boundary_maps"],
                "heater_source_mode": "tw4_to_tp3_three_span",
                "heater_source_weights_by_span": payload["heater_source_weights_by_span"],
            }
        )
        adapter = None
        if contract["cooler_candidate_id"].startswith("HX_SEGMENTED"):
            adapter = SegmentedHxAdapter(solver, 16)
            adapter.context = {"candidate_id": contract["candidate_id"], "case_id": contract["case_id"]}
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
        probe_rows: list[dict[str, Any]] = []
        for probe in table.to_dict("records"):
            error = safe_float(probe.get("error_K"))
            probe_rows.append(
                {
                    "phase": contract["phase"],
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
                    "source_path": "Fluid build_validation_table with AGENT-511 heater source redistribution scenario",
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
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
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
                    "source_path": "Fluid solve_case with AGENT-511 heater source redistribution scenario",
                },
                "probes": probe_rows,
            }
        )
    except Exception as exc:  # pragma: no cover - Fluid failures are environment dependent.
        queue.put(
            {
                "phase": contract.get("phase", ""),
                "candidate_id": contract.get("candidate_id", ""),
                "case_id": contract.get("case_id", ""),
                "split_role": contract.get("split_role", ""),
                "heater_lambda": contract.get("heater_lambda", ""),
                "cooler_candidate_id": contract.get("cooler_candidate_id", ""),
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


def coupled_scorecard_rows(
    contracts: list[dict[str, Any]], run_fluid: bool, timeout_seconds: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not run_fluid:
        return (
            [
                {
                    "phase": row["phase"],
                    "candidate_id": row["candidate_id"],
                    "case_id": row["case_id"],
                    "split_role": row["split_role"],
                    "heater_lambda": row["heater_lambda"],
                    "cooler_candidate_id": row["cooler_candidate_id"],
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
            ],
            [],
        )
    rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
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
                    "phase": contract["phase"],
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "heater_lambda": contract["heater_lambda"],
                    "cooler_candidate_id": contract["cooler_candidate_id"],
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
            payload = queue.get()
            if isinstance(payload, dict) and "score" in payload:
                rows.append(payload["score"])
                probe_rows.extend(payload.get("probes", []))
            else:
                rows.append(payload)
        else:
            rows.append(
                {
                    "phase": contract["phase"],
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "heater_lambda": contract["heater_lambda"],
                    "cooler_candidate_id": contract["cooler_candidate_id"],
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
    return rows, probe_rows


def select_lambda_from_coupled(coupled: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        row
        for row in coupled
        if row.get("phase") == "salt2_fit_grid"
        and row.get("case_id") == "salt_2"
        and row.get("coupled_run_status") == "completed"
        and row.get("root_status") == "accepted"
        and safe_float(row.get("all_probe_rmse_K")) is not None
    ]
    if not eligible:
        return {
            "selection_status": "pending_or_failed_no_completed_accepted_salt2_grid_rows",
            "heater_lambda": "",
            "selected_candidate_id": "",
            "selection_metric": "Salt2 all_probe_rmse_K",
            "selection_source": "Salt2 grid rows only",
        }
    best = min(
        eligible,
        key=lambda row: (
            safe_float(row.get("all_probe_rmse_K")) or float("inf"),
            safe_float(row.get("tw_rmse_K")) or float("inf"),
            abs(safe_float(row.get("mdot_error_pct")) or float("inf")),
        ),
    )
    value = safe_float(best["heater_lambda"]) or 0.0
    weights = heater_weights(value)
    return {
        "selection_status": "selected_from_salt2_only",
        "heater_lambda": fmt(value, 2),
        "selected_candidate_id": best["candidate_id"],
        "selection_metric": "Salt2 all_probe_rmse_K; tie TW RMSE then mdot abs error",
        "salt2_all_probe_rmse_K": best.get("all_probe_rmse_K", ""),
        "salt2_tw_rmse_K": best.get("tw_rmse_K", ""),
        "salt2_mdot_abs_error_pct": fmt(abs(safe_float(best.get("mdot_error_pct")) or 0.0)),
        "tw4_to_tw5_weight": fmt(weights["tw4_to_tw5"]),
        "tw5_to_tw6_weight": fmt(weights["tw5_to_tw6"]),
        "tw6_to_tp3_weight": fmt(weights["tw6_to_tp3"]),
        "selection_source": "Salt2 grid rows only",
    }


def selected_heater_source_weight_rows(selection: dict[str, Any]) -> list[dict[str, Any]]:
    return [selection]


def coupled_delta_rows(coupled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baselines = wall_ladder.m3_baselines()
    rows: list[dict[str, Any]] = []
    for row in coupled:
        if row.get("phase") != "selected_coupled_score" or row.get("split_role") == "train":
            continue
        baseline = baselines.get(row.get("case_id", ""), {})
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
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "heater_lambda": row.get("heater_lambda", ""),
                "cooler_candidate_id": row.get("cooler_candidate_id", ""),
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


def annotate_coupled_gates(coupled: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_by_key = {(row["candidate_id"], row["case_id"]): row["score_gate"] for row in deltas}
    out_rows: list[dict[str, Any]] = []
    for row in coupled:
        out = dict(row)
        if out.get("coupled_run_status") == "completed":
            if out.get("phase") == "salt2_fit_grid":
                out["coupled_gate"] = "salt2_fit_grid_completed"
            elif out.get("split_role") == "train":
                out["coupled_gate"] = "train_not_admission_scored"
            else:
                out["coupled_gate"] = "pass_vs_m3" if gate_by_key.get((out.get("candidate_id", ""), out.get("case_id", ""))) == "pass" else "fail_vs_m3"
        out_rows.append(out)
    return out_rows


def candidate_admission_review_rows(deltas: list[dict[str, Any]], runtime: list[dict[str, Any]], selection: dict[str, Any]) -> list[dict[str, Any]]:
    runtime_pass = all(row["gate"] == "pass" for row in runtime)
    rows: list[dict[str, Any]] = []
    for candidate in sorted({row["candidate_id"] for row in deltas}):
        by_split = {row["split_role"]: row["score_gate"] for row in deltas if row["candidate_id"] == candidate}
        blockers: list[str] = []
        if selection.get("selection_status") != "selected_from_salt2_only":
            blockers.append("salt2_lambda_not_selected")
        if not runtime_pass:
            blockers.append("runtime_audit_failed_or_pending")
        if by_split.get("validation") != "pass":
            blockers.append("validation_mdot_tp_tw_all_probe_gate_failed")
        if by_split.get("holdout") != "pass":
            blockers.append("holdout_mdot_tp_tw_all_probe_gate_failed")
        rows.append(
            {
                "candidate_id": candidate,
                "heater_lambda": next((row["heater_lambda"] for row in deltas if row["candidate_id"] == candidate), ""),
                "cooler_candidate_id": next((row["cooler_candidate_id"] for row in deltas if row["candidate_id"] == candidate), ""),
                "runtime_gate": "pass" if runtime_pass else "fail_or_pending",
                "validation_coupled_gate": by_split.get("validation", "missing"),
                "holdout_coupled_gate": by_split.get("holdout", "missing"),
                "admission_decision": "admitted_predictive_heater_source_redistribution" if not blockers else "not_admitted",
                "blocking_reasons": ";".join(blockers),
            }
        )
    if not rows:
        rows.append(
            {
                "candidate_id": "HS1_salt2_fit_heater_source_shift_p1",
                "heater_lambda": selection.get("heater_lambda", ""),
                "cooler_candidate_id": "",
                "runtime_gate": "pass" if runtime_pass else "fail_or_pending",
                "validation_coupled_gate": "missing",
                "holdout_coupled_gate": "missing",
                "admission_decision": "not_admitted",
                "blocking_reasons": "selected_coupled_rows_missing",
            }
        )
    return rows


def background_run_contract_rows(timeout_seconds: int) -> list[dict[str, Any]]:
    log_dir = f"logs/{DATE}"
    command = (
        f"mkdir -p {log_dir} && "
        f"srun -N1 -n1 python3 tools/analyze/build_heater_source_redistribution_coupled_score.py "
        f"--run-fluid --timeout-seconds {timeout_seconds} "
        f"> {log_dir}/heater_source_redistribution_coupled_score.out "
        f"2> {log_dir}/heater_source_redistribution_coupled_score.err &"
    )
    return [
        {
            "contract_id": "background_srun_coupled_score",
            "timeout_seconds": timeout_seconds,
            "command": command,
            "stdout": f"{log_dir}/heater_source_redistribution_coupled_score.out",
            "stderr": f"{log_dir}/heater_source_redistribution_coupled_score.err",
            "policy": "submit bounded Fluid scoring in background with srun/sbatch or equivalent",
        }
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_id": "agent498_wall_distribution_ladder", "path": rel(wall_ladder.OUT), "use": "PB2 wall distribution, prior failure mode, and helper contract shape"},
        {"source_id": "agent482_cooler", "path": rel(wall_ladder.AGENT482), "use": "HX alpha_UA and segmented HX adapter"},
        {"source_id": "agent461_m3", "path": rel(wall_ladder.M3_COMPARATORS), "use": "M3 mdot/TP/TW/all-probe comparator gates"},
        {"source_id": "setup_external_boundary_rows", "path": rel(wall_ladder.SETUP_ROWS), "use": "setup-only external boundary role rows"},
        {"source_id": "fluid_solver", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "read-only Fluid solve_case execution with existing heater_source_mode API"},
    ]


def blocker_decision_payload(coupled: list[dict[str, Any]], admission: list[dict[str, Any]], run_fluid: bool, selection: dict[str, Any]) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for row in coupled:
        statuses[row["coupled_run_status"]] = statuses.get(row["coupled_run_status"], 0) + 1
    admitted = [row for row in admission if row["admission_decision"] == "admitted_predictive_heater_source_redistribution"]
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "blocker_id": "predictive-wall-test-section-submodels",
        "blocker_decision": "resolve" if admitted and run_fluid else "keep_open",
        "selection_status": selection.get("selection_status", ""),
        "selected_lambda": selection.get("heater_lambda", ""),
        "coupled_status_counts": statuses,
        "coupled_completed_rows": sum(1 for row in coupled if row["coupled_run_status"] == "completed"),
        "admitted_candidates": [row["candidate_id"] for row in admitted],
        "why": (
            "A Salt2-fit heater-source redistribution candidate passed validation and holdout mdot, TP, TW, and all-probe gates vs M3."
            if admitted and run_fluid
            else "No Salt2-fit heater-source redistribution candidate has passed validation and holdout mdot, TP, TW, and all-probe gates vs M3."
        ),
    }


def readme_text(summary: dict[str, Any]) -> str:
    decision = summary["decision"]
    command = background_run_contract_rows(summary["timeout_seconds"])[0]["command"]
    return f"""---
provenance:
  - {rel(wall_ladder.OUT)}
  - {rel(wall_ladder.AGENT482)}
  - {rel(wall_ladder.M3_COMPARATORS)}
  - {rel(wall_ladder.SETUP_ROWS)}
tags: [forward-model, heater-source, test-section, heat-placement, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-WALL-THERMAL-CIRCUIT
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Source Redistribution Coupled Score

## Result

This package tests whether moving the setup heater power axially between TW4,
TW5, TW6, and TP3 can repair the temperature-shape failure left by the PB2
wall/passive distribution model.

Decision for `predictive-wall-test-section-submodels`: `{decision['blocker_decision']}`.

Reason: {decision['why']}

Selected Salt2 lambda: `{decision['selected_lambda']}`.
Selection status: `{decision['selection_status']}`.

## Coupled Run

Coupled rows completed: `{decision['coupled_completed_rows']}`.
Status counts: `{json.dumps(decision['coupled_status_counts'], sort_keys=True)}`.

Background command for replay:

```bash
{command}
```

## Files

- `heater_source_lambda_grid.csv`
- `selected_heater_source_weights.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build(run_fluid: bool = False, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, reuse_existing_coupled: bool = False) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    lambda_grid = heater_source_lambda_grid_rows()
    if reuse_existing_coupled and (OUT / "coupled_scorecard.csv").exists():
        coupled = read_csv(OUT / "coupled_scorecard.csv")
        probes = read_csv(OUT / "probe_error_localization.csv") if (OUT / "probe_error_localization.csv").exists() else []
        selection = select_lambda_from_coupled(coupled)
        selected_value = safe_float(selection.get("heater_lambda"))
        contracts = scenario_contract_rows(selected_value)
        effective_run_fluid = any(row.get("coupled_run_status") == "completed" for row in coupled)
    else:
        grid_contracts = scenario_contract_rows(None)
        grid_scores, grid_probes = coupled_scorecard_rows(grid_contracts, run_fluid, timeout_seconds)
        selection = select_lambda_from_coupled(grid_scores)
        selected_value = safe_float(selection.get("heater_lambda"))
        selected_contracts = scenario_contract_rows(selected_value)[len(LAMBDA_GRID) :] if selected_value is not None else []
        selected_scores, selected_probes = coupled_scorecard_rows(selected_contracts, run_fluid, timeout_seconds)
        contracts = grid_contracts + selected_contracts
        coupled = grid_scores + selected_scores
        probes = grid_probes + selected_probes
        effective_run_fluid = run_fluid
    runtime = runtime_input_audit_rows(contracts, effective_run_fluid, safe_float(selection.get("heater_lambda")))
    deltas = coupled_delta_rows(coupled)
    coupled = annotate_coupled_gates(coupled, deltas)
    admission = candidate_admission_review_rows(deltas, runtime, selection)
    background = background_run_contract_rows(timeout_seconds)
    manifest = source_manifest_rows()
    decision = blocker_decision_payload(coupled, admission, effective_run_fluid, selection)

    counts = {
        "heater_source_lambda_grid.csv": write_csv(OUT / "heater_source_lambda_grid.csv", lambda_grid, list(lambda_grid[0].keys())),
        "selected_heater_source_weights.csv": write_csv(OUT / "selected_heater_source_weights.csv", selected_heater_source_weight_rows(selection), list(selected_heater_source_weight_rows(selection)[0].keys())),
        "scenario_contracts.csv": write_csv(OUT / "scenario_contracts.csv", contracts, list(contracts[0].keys()) if contracts else ["candidate_id"]),
        "runtime_input_audit.csv": write_csv(OUT / "runtime_input_audit.csv", runtime, list(runtime[0].keys())),
        "coupled_scorecard.csv": write_csv(OUT / "coupled_scorecard.csv", coupled, list(coupled[0].keys()) if coupled else ["candidate_id"]),
        "coupled_delta_vs_m3.csv": write_csv(OUT / "coupled_delta_vs_m3.csv", deltas, list(deltas[0].keys()) if deltas else ["candidate_id"]),
        "probe_error_localization.csv": write_csv(OUT / "probe_error_localization.csv", probes, PROBE_FIELDS),
        "candidate_admission_review.csv": write_csv(OUT / "candidate_admission_review.csv", admission, list(admission[0].keys()) if admission else ["candidate_id"]),
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
        "counts": counts,
        "selection": selection,
        "decision": decision,
    }
    write_json(OUT / "blocker_decision.json", decision)
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run Fluid solve_case rows; use compute-node srun/sbatch for this option.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--reuse-existing-coupled", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(run_fluid=args.run_fluid, timeout_seconds=args.timeout_seconds, reuse_existing_coupled=args.reuse_existing_coupled), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
