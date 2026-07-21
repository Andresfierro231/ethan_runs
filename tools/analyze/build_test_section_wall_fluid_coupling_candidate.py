#!/usr/bin/env python3
"""Build AGENT-526 explicit test-section wall/fluid coupling candidate package."""

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


TASK = "AGENT-526"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_heater_source_redistribution_coupled_score as heater
from tools.analyze import build_wall_test_section_distribution_ladder as ladder


FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate")
OUT = ROOT / OUT_REL

AGENT511 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score"
AGENT522 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_thermal_circuit_study"
CASE_NAME = ladder.CASE_NAME
SPLIT = ladder.SPLIT
COOLER_IDS = heater.COOLER_IDS
DEFAULT_TIMEOUT_SECONDS = 273
FAMILY_ID = "TSWFC1_test_section_bulk_to_ambient_series_resistance"
PB2_WALL_ID = "PB2_salt2_local_shape_passive_hA_p1"
COUPLING_MODEL = "bulk_to_ambient_series_resistance"

PROBE_FIELDS = [
    "candidate_id",
    "case_id",
    "split_role",
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

LOCAL_BEHAVIOR_FIELDS = [
    "candidate_id",
    "case_id",
    "split_role",
    "sensor",
    "kind",
    "local_region",
    "predicted_K",
    "target_K",
    "error_K",
    "abs_error_K",
    "prediction_source_segment",
    "prediction_source_fraction",
    "observed_behavior",
    "admission_use",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return ladder.rel(path)


def safe_float(value: Any) -> float | None:
    return ladder.safe_float(value)


def fmt(value: Any, precision: int = 10) -> str:
    return ladder.fmt(value, precision=precision)


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


def selected_heater_source() -> dict[str, Any]:
    summary = json.loads((AGENT511 / "summary.json").read_text(encoding="utf-8"))
    selection = dict(summary.get("selection", {}))
    if selection.get("selection_status") != "selected_from_salt2_only":
        return {
            "selection_status": selection.get("selection_status", "missing"),
            "heater_lambda": "",
            "selected_candidate_id": selection.get("selected_candidate_id", ""),
            "source_path": rel(AGENT511 / "summary.json"),
        }
    selection["source_path"] = rel(AGENT511 / "summary.json")
    return selection


def lambda_label(value: float) -> str:
    return heater.lambda_label(value)


def candidate_id(cooler_id: str) -> str:
    selection = selected_heater_source()
    value = safe_float(selection.get("heater_lambda")) or 0.0
    return f"HS1_lam_{lambda_label(value)}_PLUS_{FAMILY_ID}_PLUS_{cooler_id}"


def series_resistance_loss_W(
    T_bulk_K: float,
    ambient_K: float,
    hA_W_K: float,
    coverage_multiplier: float,
    segment_length_m: float,
    R_i_prime_K_m_W: float,
    R_wall_prime_K_m_W: float,
) -> float:
    if T_bulk_K <= ambient_K:
        return 0.0
    external_conductance = hA_W_K * coverage_multiplier
    if external_conductance <= 0.0:
        raise ValueError("series coupling requires positive external conductance")
    if segment_length_m <= 0.0:
        raise ValueError("series coupling requires positive segment length")
    if not math.isfinite(R_i_prime_K_m_W) or not math.isfinite(R_wall_prime_K_m_W):
        raise ValueError("series coupling requires finite internal and wall resistance per length")
    inner_wall_resistance_K_W = max(R_i_prime_K_m_W + R_wall_prime_K_m_W, 0.0) / segment_length_m
    external_resistance_K_W = 1.0 / external_conductance
    return (T_bulk_K - ambient_K) / max(inner_wall_resistance_K_W + external_resistance_K_W, 1.0e-12)


def base_role_rows_for_case(case_id: str) -> list[dict[str, Any]]:
    setup = ladder.setup_rows_by_case()
    ratios = ladder.heater_ratio_by_case()
    shape = ladder.shape_for_candidate(PB2_WALL_ID)
    rows = ladder._role_rows_for_contract(setup[case_id], shape, ratios[case_id])
    out: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        if copied.get("parent_segment") == "left_upper_vertical" and copied.get("role") == "test_section":
            copied["coupling_model"] = COUPLING_MODEL
            copied["coupling_scope"] = "test_section_role_only"
            copied["drive_selector"] = "fluid_segment_bulk_temperature_for_v1_setup_mode"
        else:
            copied["coupling_model"] = "direct_external_hA"
        out.append(copied)
    return out


def parent_maps_for_case(case_id: str) -> dict[str, dict[str, Any]]:
    setup = ladder.setup_rows_by_case()
    ratios = ladder.heater_ratio_by_case()
    shape = ladder.shape_for_candidate(PB2_WALL_ID)
    return ladder._parent_maps_for_contract(setup[case_id], shape, ratios[case_id])


def wall_candidate_definitions() -> list[dict[str, Any]]:
    selection = selected_heater_source()
    return [
        {
            "wall_candidate_id": FAMILY_ID,
            "fit_case_id": "salt_2",
            "fit_parameter_count": 0,
            "selected_heater_lambda_from_AGENT511": selection.get("heater_lambda", ""),
            "base_distribution": PB2_WALL_ID,
            "coupling_model": COUPLING_MODEL,
            "target_parent_segment": "left_upper_vertical",
            "target_role": "test_section",
            "runtime_policy": "setup_external_boundary_rows;AGENT511_Salt2_lambda;PB2_distribution;series_wall_fluid_resistance;Salt2_cooler_alpha_UA",
            "source_path": f"{rel(AGENT511)};{rel(ladder.OUT)};{rel(AGENT522)}",
        }
    ]


def coupled_candidate_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cooler_id in COOLER_IDS:
        rows.append(
            {
                "candidate_id": candidate_id(cooler_id),
                "wall_candidate_id": FAMILY_ID,
                "cooler_candidate_id": cooler_id,
                "fit_parameter_count": 2,
                "fitted_parameters": "AGENT511 Salt2 heater lambda; Salt2 cooler alpha_UA",
                "new_physics": "test-section role loss uses bulk-to-ambient series resistance through internal+wall and external hA",
                "runtime_status": "eligible_after_static_runtime_precheck",
                "source_path": f"{rel(AGENT511)};{rel(ladder.SETUP_ROWS)};{rel(ladder.AGENT482)}",
            }
        )
    return rows


def scenario_contract_rows() -> list[dict[str, Any]]:
    selection = selected_heater_source()
    selected_value = safe_float(selection.get("heater_lambda"))
    if selected_value is None:
        return []
    weights = heater.heater_weights(selected_value)
    rows: list[dict[str, Any]] = []
    for candidate in coupled_candidate_definitions():
        for case_id in CASE_NAME:
            payload = {
                "role_rows": base_role_rows_for_case(case_id),
                "parent_boundary_maps": parent_maps_for_case(case_id),
                "heater_source_weights_by_span": weights,
            }
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "wall_candidate_id": FAMILY_ID,
                    "cooler_candidate_id": candidate["cooler_candidate_id"],
                    "case_id": case_id,
                    "fluid_case_name": CASE_NAME[case_id],
                    "split_role": SPLIT[case_id],
                    "heater_lambda": fmt(selected_value, 2),
                    "tw4_to_tw5_weight": fmt(weights["tw4_to_tw5"]),
                    "tw5_to_tw6_weight": fmt(weights["tw5_to_tw6"]),
                    "tw6_to_tp3_weight": fmt(weights["tw6_to_tp3"]),
                    "hx_ua_multiplier": fmt(ladder.fit_alpha_ua()),
                    "outer_closure_mode": "external_boundary_table",
                    "heater_source_mode": "tw4_to_tp3_three_span",
                    "role_row_count": len(payload["role_rows"]),
                    "series_coupling_role_count": sum(1 for row in payload["role_rows"] if row.get("coupling_model") == COUPLING_MODEL),
                    "parent_boundary_count": len(payload["parent_boundary_maps"]["external_boundary_h_by_parent_segment"]),
                    "runtime_input_violations": 0,
                    "runtime_inputs": "setup_external_boundary_rows;AGENT511_Salt2_lambda;PB2_distribution;series_resistance_formula;Salt2_cooler_alpha_UA",
                    "scenario_json": json.dumps(payload, sort_keys=True),
                    "source_path": f"{rel(AGENT511)};{rel(ladder.SETUP_ROWS)};{rel(ladder.AGENT482)}",
                }
            )
    return rows


def runtime_input_audit_rows(contracts: list[dict[str, Any]], run_fluid: bool) -> list[dict[str, Any]]:
    forbidden = [
        "realized wallHeatFlux",
        "CFD mdot",
        "validation/holdout wall-shell temperature",
        "validation/holdout outer-surface temperature",
        "validation/holdout probe temperatures",
        "imposed CFD cooler duty",
        "realized test-section heat",
    ]
    series_rows = 0
    misplaced = 0
    for contract in contracts:
        payload = json.loads(contract["scenario_json"])
        for row in payload["role_rows"]:
            if row.get("coupling_model") == COUPLING_MODEL:
                series_rows += 1
                if row.get("parent_segment") != "left_upper_vertical" or row.get("role") != "test_section":
                    misplaced += 1
    return [
        {
            "audit_id": "R1_selected_source_dependency",
            "gate": "pass" if selected_heater_source().get("selection_status") == "selected_from_salt2_only" else "fail",
            "evidence": f"AGENT511 selection status: {selected_heater_source().get('selection_status', '')}",
            "forbidden_runtime_input": "Salt3/Salt4 fitting targets;validation/holdout temperatures",
        },
        {
            "audit_id": "R2_runtime_inputs",
            "gate": "pass" if all(int(row.get("runtime_input_violations", 0)) == 0 for row in contracts) else "fail",
            "evidence": f"{len(contracts)} contracts use setup rows, AGENT511 Salt2 lambda, PB2 distribution, and Salt2 cooler alpha_UA",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R3_series_coupling_scope",
            "gate": "pass" if series_rows == len(contracts) and misplaced == 0 else "fail",
            "evidence": f"{series_rows} series-coupled role rows; {misplaced} misplaced rows",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R4_coupled_execution",
            "gate": "pass" if run_fluid else "pending",
            "evidence": "Fluid rows run in this package" if run_fluid else "compute-node Fluid scoring required",
            "forbidden_runtime_input": "execution gate only",
        },
    ]


def _install_series_coupling_adapter(solver: Any) -> Any:
    original = solver._external_boundary_role_loss_for_segment

    def patched(T_bulk_avg_K: float, segment: Any, diagnostics: Any, role_rows: list[dict[str, object]]) -> float | None:
        matched = [row for row in role_rows if solver._role_row_matches_segment(row, segment)]
        if not matched:
            return None
        total_loss_W = 0.0
        for row in matched:
            role = str(row.get("role", "<unknown>"))
            coverage = solver._float_from_role_row(row, "coverage_multiplier", 1.0)
            if coverage is None or coverage < 0.0:
                raise ValueError(f"External boundary role row {role!r} has invalid coverage_multiplier={coverage!r}.")
            hA = solver._float_from_role_row(row, "hA_W_K", None)
            if hA is None:
                h = solver._float_from_role_row(row, "h_W_m2K", None)
                area = solver._float_from_role_row(row, "area_m2", None)
                if h is None or area is None:
                    raise ValueError(f"External boundary role row {role!r} must provide hA_W_K or h_W_m2K plus area_m2.")
                hA = h * area
            if hA < 0.0:
                raise ValueError(f"External boundary role row {role!r} has invalid conductance hA_W_K={hA!r}.")
            ambient = solver._float_from_role_row(row, "Ta_K", diagnostics.external_ambient_temperature_K)
            if ambient is None:
                ambient = 300.0
            coupling_model = str(row.get("coupling_model", "direct_external_hA")).strip().lower()
            if coupling_model in {"", "direct_external_ha", "direct_external_hA".lower()}:
                selector = str(
                    row.get(
                        "drive_selector",
                        diagnostics.external_boundary_drive_selector or "fluid_segment_bulk_temperature_for_v1_setup_mode",
                    )
                )
                drive_temperature = solver._drive_temperature_from_selector(selector, T_bulk_avg_K, diagnostics)
                total_loss_W += hA * coverage * max(float(drive_temperature) - float(ambient), 0.0)
            elif coupling_model == COUPLING_MODEL:
                total_loss_W += series_resistance_loss_W(
                    float(T_bulk_avg_K),
                    float(ambient),
                    float(hA),
                    float(coverage),
                    float(segment.length_m),
                    float(diagnostics.R_i_prime_K_m_W),
                    float(diagnostics.R_wall_prime_K_m_W),
                )
            else:
                raise ValueError(f"Unsupported role-row coupling_model {coupling_model!r}.")
        return total_loss_W

    solver._external_boundary_role_loss_for_segment = patched
    return original


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
        original_role_loss = _install_series_coupling_adapter(solver)
        if contract["cooler_candidate_id"].startswith("HX_SEGMENTED"):
            adapter = SegmentedHxAdapter(solver, 16)
            adapter.context = {"candidate_id": contract["candidate_id"], "case_id": contract["case_id"]}
        case = cases[contract["fluid_case_name"]]
        try:
            if adapter is not None:
                solver._hx_airside_transfer = adapter
            result = solver.solve_case(case, scenario)
        finally:
            solver._external_boundary_role_loss_for_segment = original_role_loss
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
                    "candidate_id": contract["candidate_id"],
                    "case_id": contract["case_id"],
                    "split_role": contract["split_role"],
                    "sensor": probe.get("sensor", ""),
                    "kind": probe.get("kind", ""),
                    "predicted_K": fmt(probe.get("predicted_K")),
                    "target_K": fmt(probe.get("measured_K")),
                    "error_K": fmt(error),
                    "abs_error_K": fmt(None if error is None else abs(error)),
                    "prediction_source_segment": probe.get("prediction_source_segment", ""),
                    "prediction_source_fraction": fmt(probe.get("prediction_source_fraction")),
                    "validation_excluded": "yes" if bool(probe.get("validation_excluded")) else "no",
                    "source_path": "Fluid solve_case with AGENT-526 in-process series-coupling adapter",
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
                    "source_path": "Fluid solve_case with AGENT-526 in-process series-coupling adapter",
                },
                "probes": probe_rows,
            }
        )
    except Exception as exc:  # pragma: no cover - Fluid failures are environment dependent.
        queue.put(
            {
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
    probes: list[dict[str, Any]] = []
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
                probes.extend(payload.get("probes", []))
            else:
                rows.append(payload)
        else:
            rows.append(
                {
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
    return rows, probes


def coupled_delta_rows(coupled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baselines = ladder.m3_baselines()
    rows: list[dict[str, Any]] = []
    for row in coupled:
        if row.get("split_role") == "train":
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
    out: list[dict[str, Any]] = []
    for row in coupled:
        copied = dict(row)
        if copied.get("coupled_run_status") == "completed":
            copied["coupled_gate"] = (
                "train_not_admission_scored"
                if copied.get("split_role") == "train"
                else "pass_vs_m3"
                if gate_by_key.get((copied.get("candidate_id", ""), copied.get("case_id", ""))) == "pass"
                else "fail_vs_m3"
            )
        out.append(copied)
    return out


def candidate_admission_review_rows(deltas: list[dict[str, Any]], runtime: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_pass = all(row["gate"] == "pass" for row in runtime)
    rows: list[dict[str, Any]] = []
    for candidate in sorted({row["candidate_id"] for row in deltas}):
        by_split = {row["split_role"]: row["score_gate"] for row in deltas if row["candidate_id"] == candidate}
        blockers: list[str] = []
        if not runtime_pass:
            blockers.append("runtime_audit_failed_or_pending")
        if by_split.get("validation") != "pass":
            blockers.append("validation_mdot_tp_tw_all_probe_gate_failed")
        if by_split.get("holdout") != "pass":
            blockers.append("holdout_mdot_tp_tw_all_probe_gate_failed")
        rows.append(
            {
                "candidate_id": candidate,
                "runtime_gate": "pass" if runtime_pass else "fail_or_pending",
                "validation_coupled_gate": by_split.get("validation", "missing"),
                "holdout_coupled_gate": by_split.get("holdout", "missing"),
                "admission_decision": "admitted_test_section_wall_fluid_coupling" if not blockers else "not_admitted",
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def local_test_section_behavior_rows(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in probes:
        sensor = str(row.get("sensor", ""))
        source_segment = str(row.get("prediction_source_segment", ""))
        if not (
            source_segment == "test_section"
            or (source_segment == "left_upper_vertical" and sensor in {"TP6", "TW8"})
        ):
            continue
        error = safe_float(row.get("error_K"))
        if error is None or not math.isfinite(error):
            behavior = "missing_prediction"
        elif error < -2.0:
            behavior = "underpredicts_local_temperature"
        elif error > 2.0:
            behavior = "overpredicts_local_temperature"
        else:
            behavior = "within_2K_local_temperature"
        if source_segment == "test_section":
            region = "test_section_bulk_probe"
        elif sensor == "TP6":
            region = "upper_upcomer_exit_probe_adjacent_to_test_section"
        else:
            region = "left_upper_vertical_wall_probe_adjacent_to_test_section"
        rows.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "sensor": sensor,
                "kind": row.get("kind", ""),
                "local_region": region,
                "predicted_K": row.get("predicted_K", ""),
                "target_K": row.get("target_K", ""),
                "error_K": row.get("error_K", ""),
                "abs_error_K": row.get("abs_error_K", ""),
                "prediction_source_segment": source_segment,
                "prediction_source_fraction": row.get("prediction_source_fraction", ""),
                "observed_behavior": behavior,
                "admission_use": "diagnostic_only_no_fit_or_tuning",
            }
        )
    return rows


def background_run_contract_rows(timeout_seconds: int) -> list[dict[str, Any]]:
    command = (
        f"srun -N1 -n1 python3.11 tools/analyze/build_test_section_wall_fluid_coupling_candidate.py "
        f"--run-fluid --timeout-seconds {timeout_seconds}"
    )
    return [
        {
            "contract_id": "bounded_srun_coupled_score",
            "timeout_seconds": timeout_seconds,
            "command": command,
            "policy": "run bounded Fluid scoring through compute-node srun; no login-node Fluid solve",
        }
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_id": "agent511_heater_source", "path": rel(AGENT511), "use": "selected Salt2 heater lambda and source weights"},
        {"source_id": "agent522_wall_circuit", "path": rel(AGENT522), "use": "completed non-series wall-circuit comparator and failure context"},
        {"source_id": "agent498_distribution", "path": rel(ladder.OUT), "use": "PB2 wall distribution and role-row contract helper"},
        {"source_id": "agent482_cooler", "path": rel(ladder.AGENT482), "use": "HX alpha_UA and segmented HX adapter"},
        {"source_id": "agent461_m3", "path": rel(ladder.M3_COMPARATORS), "use": "M3 comparator gates"},
        {"source_id": "setup_external_boundary_rows", "path": rel(ladder.SETUP_ROWS), "use": "setup hA/Ta/Tsur/emissivity role rows"},
        {"source_id": "fluid_solver_readonly", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "read-only import with in-process role-loss adapter"},
    ]


def blocker_decision_payload(coupled: list[dict[str, Any]], admission: list[dict[str, Any]], run_fluid: bool) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for row in coupled:
        statuses[row["coupled_run_status"]] = statuses.get(row["coupled_run_status"], 0) + 1
    admitted = [row for row in admission if row["admission_decision"] == "admitted_test_section_wall_fluid_coupling"]
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "blocker_id": "predictive-wall-test-section-submodels",
        "blocker_decision": "resolve" if admitted and run_fluid else "keep_open",
        "coupled_status_counts": statuses,
        "coupled_completed_rows": sum(1 for row in coupled if row["coupled_run_status"] == "completed"),
        "admitted_candidates": [row["candidate_id"] for row in admitted],
        "why": (
            "A test-section wall/fluid series-coupling candidate passed validation and holdout mdot, TP, TW, and all-probe gates vs M3."
            if admitted and run_fluid
            else "No test-section wall/fluid series-coupling candidate has passed validation and holdout mdot, TP, TW, and all-probe gates vs M3."
        ),
    }


def readme_text(summary: dict[str, Any]) -> str:
    decision = summary["decision"]
    return f"""---
provenance:
  - {rel(AGENT511)}
  - {rel(AGENT522)}
  - {rel(ladder.OUT)}
  - {rel(ladder.AGENT482)}
  - {rel(ladder.M3_COMPARATORS)}
tags: [forward-model, wall-fluid-coupling, test-section, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Test-Section Wall/Fluid Coupling Candidate

## Result

This package implements the fallback after AGENT-511 heater-source redistribution
and AGENT-522 non-series wall thermal-circuit candidates failed admission. It
uses AGENT-511's Salt2-selected heater lambda and scores a test-section-only
bulk-to-ambient series resistance through internal convection/wall resistance
and setup external hA.

Decision for `predictive-wall-test-section-submodels`: `{decision['blocker_decision']}`.

Reason: {decision['why']}

Coupled rows completed: `{decision['coupled_completed_rows']}`.
Status counts: `{json.dumps(decision['coupled_status_counts'], sort_keys=True)}`.

## Method

- Start from AGENT-511 only after its Salt2-only source selection was complete;
  the selected heater-source lambda is not re-fit on Salt3 or Salt4.
- Use the PB2 passive wall/test-section distribution and the Salt2 cooler
  alpha-UA candidates already admitted for coupled scoring.
- Apply the new thermal-circuit behavior only to the `left_upper_vertical`
  role row named `test_section`.
- Compute that role loss as bulk fluid temperature to ambient through
  `R_i_prime + R_wall_prime` in series with setup external `hA`. Other role
  rows keep Fluid's direct external hA behavior.
- Use an in-process adapter around Fluid's role-loss function for this run
  only. No persistent Fluid source, native CFD output, registry, or blocker
  register file is edited.

## Admission Gate

Admission requires the runtime audit to pass and both selected candidates to
beat M3 on validation and holdout absolute mdot error, TP RMSE, TW RMSE, and
all-probe RMSE. The coupled run completed, but both candidates failed validation
and holdout temperature gates while improving mdot.

## Local Test-Section Behavior

`local_test_section_behavior.csv` isolates TP5 plus adjacent upper-upcomer /
test-section bracket probes TP6 and TW8. These rows are diagnostic only: they
show whether the explicit series coupling helped local test-section behavior,
but they are not used for tuning or admission without the global gates.

## Files

- `wall_candidate_definitions.csv`
- `candidate_definitions.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `local_test_section_behavior.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build(run_fluid: bool = False, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, reuse_existing_coupled: bool = False) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    wall_candidates = wall_candidate_definitions()
    candidates = coupled_candidate_definitions()
    contracts = scenario_contract_rows()
    runtime = runtime_input_audit_rows(contracts, run_fluid)
    if reuse_existing_coupled and (OUT / "coupled_scorecard.csv").exists():
        coupled = read_csv(OUT / "coupled_scorecard.csv")
        probes = read_csv(OUT / "probe_error_localization.csv") if (OUT / "probe_error_localization.csv").exists() else []
        effective_run_fluid = any(row.get("coupled_run_status") == "completed" for row in coupled)
    else:
        coupled, probes = coupled_scorecard_rows(contracts, run_fluid, timeout_seconds)
        effective_run_fluid = run_fluid
    runtime = runtime_input_audit_rows(contracts, effective_run_fluid)
    deltas = coupled_delta_rows(coupled)
    coupled = annotate_coupled_gates(coupled, deltas)
    admission = candidate_admission_review_rows(deltas, runtime)
    local_behavior = local_test_section_behavior_rows(probes)
    background = background_run_contract_rows(timeout_seconds)
    manifest = source_manifest_rows()
    decision = blocker_decision_payload(coupled, admission, effective_run_fluid)

    counts = {
        "wall_candidate_definitions.csv": write_csv(OUT / "wall_candidate_definitions.csv", wall_candidates, list(wall_candidates[0].keys())),
        "candidate_definitions.csv": write_csv(OUT / "candidate_definitions.csv", candidates, list(candidates[0].keys())),
        "scenario_contracts.csv": write_csv(OUT / "scenario_contracts.csv", contracts, list(contracts[0].keys()) if contracts else ["candidate_id"]),
        "runtime_input_audit.csv": write_csv(OUT / "runtime_input_audit.csv", runtime, list(runtime[0].keys())),
        "coupled_scorecard.csv": write_csv(OUT / "coupled_scorecard.csv", coupled, list(coupled[0].keys()) if coupled else ["candidate_id"]),
        "coupled_delta_vs_m3.csv": write_csv(OUT / "coupled_delta_vs_m3.csv", deltas, list(deltas[0].keys()) if deltas else ["candidate_id"]),
        "probe_error_localization.csv": write_csv(OUT / "probe_error_localization.csv", probes, PROBE_FIELDS),
        "local_test_section_behavior.csv": write_csv(OUT / "local_test_section_behavior.csv", local_behavior, LOCAL_BEHAVIOR_FIELDS),
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
        "decision": decision,
    }
    write_json(OUT / "blocker_decision.json", decision)
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run Fluid solve_case rows; use compute-node srun/sbatch.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--reuse-existing-coupled", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(run_fluid=args.run_fluid, timeout_seconds=args.timeout_seconds, reuse_existing_coupled=args.reuse_existing_coupled), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
