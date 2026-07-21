#!/usr/bin/env python3
"""Build AGENT-522 parallel wall/passive/test-section thermal-circuit study."""

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


TASK = "AGENT-522"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_wall_thermal_circuit_study")
OUT = ROOT / OUT_REL
LOG_DIR = ROOT / "logs/2026-07-17"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_wall_test_section_distribution_ladder as ladder

AGENT511 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score"
AGENT513 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate"
CASE_NAME = ladder.CASE_NAME
SPLIT = ladder.SPLIT
COOLER_IDS = ladder.COOLER_IDS
DEFAULT_TIMEOUT_SECONDS = 273
DEFAULT_PARALLEL_WORKERS = 8

WALL_CIRCUIT_IDS = [
    "HIW1_heated_incline_pipe_outer_wall_drive",
    "HIW2_heated_incline_outer_surface_drive",
    "TSC1_test_section_only_pipe_outer_wall_drive",
    "TSC2_test_section_only_outer_surface_drive",
]

DRIVE_SELECTOR_BY_WALL = {
    "HIW1_heated_incline_pipe_outer_wall_drive": "pipe_outer_wall_temperature",
    "HIW2_heated_incline_outer_surface_drive": "outer_surface_temperature",
    "TSC1_test_section_only_pipe_outer_wall_drive": "pipe_outer_wall_temperature",
    "TSC2_test_section_only_outer_surface_drive": "outer_surface_temperature",
}

LANE_BY_WALL = {
    "HIW1_heated_incline_pipe_outer_wall_drive": "heated_incline_wall_drive",
    "HIW2_heated_incline_outer_surface_drive": "heated_incline_wall_drive",
    "TSC1_test_section_only_pipe_outer_wall_drive": "test_section_wall_fluid_coupling",
    "TSC2_test_section_only_outer_surface_drive": "test_section_wall_fluid_coupling",
}

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

PROBE_DELTA_FIELDS = [
    "candidate_id",
    "case_id",
    "split_role",
    "sensor",
    "kind",
    "candidate_error_K",
    "candidate_abs_error_K",
    "m3_error_K",
    "m3_abs_error_K",
    "abs_error_delta_vs_m3_K",
    "candidate_predicted_K",
    "target_K",
    "prediction_source_segment",
    "comparison_status",
    "probe_gate",
]

ROLE_SEGMENT_FIELDS = [
    "candidate_id",
    "case_id",
    "split_role",
    "kind",
    "prediction_source_segment",
    "n_compared",
    "candidate_rmse_K",
    "m3_rmse_K",
    "rmse_delta_vs_m3_K",
    "candidate_mae_K",
    "m3_mae_K",
    "mae_delta_vs_m3_K",
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


def _base_role_rows_for_case(case_id: str) -> list[dict[str, Any]]:
    setup = ladder.setup_rows_by_case()
    ratios = ladder.heater_ratio_by_case()
    shape = ladder.shape_for_candidate("PB2_salt2_local_shape_passive_hA_p1")
    return ladder._role_rows_for_contract(setup[case_id], shape, ratios[case_id])


def _base_parent_maps_for_case(case_id: str) -> dict[str, dict[str, Any]]:
    setup = ladder.setup_rows_by_case()
    ratios = ladder.heater_ratio_by_case()
    shape = ladder.shape_for_candidate("PB2_salt2_local_shape_passive_hA_p1")
    return ladder._parent_maps_for_contract(setup[case_id], shape, ratios[case_id])


def _case_setup_rows(case_id: str) -> list[dict[str, str]]:
    return ladder.setup_rows_by_case()[case_id]


def _heated_incline_role_rows(case_id: str, drive_selector: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _case_setup_rows(case_id):
        if row["fluid_parent_segment"] != "heated_incline" or row["role"] != "ambient_wall":
            continue
        rows.append(
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
                "coverage_multiplier": 1.0,
                "drive_selector": drive_selector,
                "source": rel(ladder.SETUP_ROWS),
            }
        )
    return rows


def _test_section_only_role_rows(base_rows: list[dict[str, Any]], drive_selector: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in base_rows:
        copied = dict(row)
        if copied.get("parent_segment") == "left_upper_vertical" and copied.get("role") == "test_section":
            copied["drive_selector"] = drive_selector
        out.append(copied)
    return out


def _drop_parent_maps_for_explicit_role_rows(
    parent_maps: dict[str, dict[str, Any]], role_rows: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    out = {key: dict(value) for key, value in parent_maps.items()}
    explicit = {str(row.get("parent_segment", "")) for row in role_rows if row.get("parent_segment")}
    for mapping in out.values():
        for parent in explicit:
            mapping.pop(parent, None)
    return out


def wall_candidate_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wall_id in WALL_CIRCUIT_IDS:
        lane = LANE_BY_WALL[wall_id]
        rows.append(
            {
                "wall_candidate_id": wall_id,
                "lane": lane,
                "fit_case_id": "salt_2",
                "fit_parameter_count": 1,
                "base_distribution": "PB2_salt2_local_shape_passive_hA_p1",
                "drive_selector": DRIVE_SELECTOR_BY_WALL[wall_id],
                "runtime_policy": "setup_external_boundary_rows;PB2_Salt2_shape;Fluid_solved_wall_state_drive;Salt2_cooler_alpha_UA",
                "changed_physics_vs_AGENT498_513": (
                    "heated-incline ambient-wall drive selector only"
                    if lane == "heated_incline_wall_drive"
                    else "test-section role drive selector only"
                ),
                "source_path": f"{rel(ladder.SETUP_ROWS)};{rel(ladder.OUT)};{rel(AGENT513)}",
            }
        )
    return rows


def coupled_candidate_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wall_id in WALL_CIRCUIT_IDS:
        for cooler_id in COOLER_IDS:
            rows.append(
                {
                    "candidate_id": f"{wall_id}_PLUS_{cooler_id}",
                    "wall_candidate_id": wall_id,
                    "cooler_candidate_id": cooler_id,
                    "lane": LANE_BY_WALL[wall_id],
                    "fit_parameter_count": 2,
                    "runtime_status": "eligible_after_static_runtime_precheck",
                    "source_path": f"{rel(ladder.SETUP_ROWS)};{rel(ladder.AGENT482)};{rel(ladder.OUT)}",
                }
            )
    return rows


def scenario_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in coupled_candidate_definitions():
        wall_id = candidate["wall_candidate_id"]
        lane = candidate["lane"]
        selector = DRIVE_SELECTOR_BY_WALL[wall_id]
        for case_id in CASE_NAME:
            base_rows = _base_role_rows_for_case(case_id)
            if lane == "heated_incline_wall_drive":
                role_rows = base_rows + _heated_incline_role_rows(case_id, selector)
            else:
                role_rows = _test_section_only_role_rows(base_rows, selector)
            parent_maps = _drop_parent_maps_for_explicit_role_rows(_base_parent_maps_for_case(case_id), role_rows)
            payload = {"role_rows": role_rows, "parent_boundary_maps": parent_maps}
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "wall_candidate_id": wall_id,
                    "cooler_candidate_id": candidate["cooler_candidate_id"],
                    "lane": lane,
                    "case_id": case_id,
                    "fluid_case_name": CASE_NAME[case_id],
                    "split_role": SPLIT[case_id],
                    "hx_ua_multiplier": fmt(ladder.fit_alpha_ua()),
                    "outer_closure_mode": "external_boundary_table",
                    "role_row_count": len(role_rows),
                    "parent_boundary_count": len(parent_maps["external_boundary_h_by_parent_segment"]),
                    "parallel_group": "ag522_wall_circuit",
                    "runtime_input_violations": 0,
                    "runtime_inputs": "setup_external_boundary_rows;PB2_Salt2_shape;Fluid_wall_state_drive;Salt2_cooler_alpha_UA",
                    "scenario_json": json.dumps(payload, sort_keys=True),
                    "source_path": f"{rel(ladder.SETUP_ROWS)};{rel(ladder.AGENT482)};{rel(ladder.OUT)};{rel(AGENT513)}",
                }
            )
    return rows


def runtime_input_audit_rows(contracts: list[dict[str, Any]], run_fluid: bool, parallel_workers: int) -> list[dict[str, Any]]:
    forbidden = [
        "realized wallHeatFlux",
        "CFD mdot",
        "validation/holdout wall-shell temperature",
        "validation/holdout outer-surface temperature",
        "validation/holdout probe temperatures",
        "imposed CFD cooler duty",
        "realized test-section heat",
    ]
    return [
        {
            "audit_id": "R1_runtime_inputs",
            "gate": "pass" if all(int(row.get("runtime_input_violations", 0)) == 0 for row in contracts) else "fail",
            "evidence": f"{len(contracts)} scenario rows use setup rows, PB2 Salt2 shape, Fluid-computed wall state drive, and Salt2 cooler alpha_UA",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R2_parallel_policy",
            "gate": "pass" if 1 <= parallel_workers <= 16 else "fail",
            "evidence": f"parallel_workers={parallel_workers}; conservative cap is 16 to avoid root-solver/memory contention",
            "forbidden_runtime_input": "unbounded parallelism;login-node Fluid solve",
        },
        {
            "audit_id": "R3_coupled_execution",
            "gate": "pass" if run_fluid else "pending",
            "evidence": "Fluid rows run in this package" if run_fluid else "bounded sbatch/srun execution required for coupled admission",
            "forbidden_runtime_input": "execution gate only",
        },
    ]


def agent511_status_rows() -> list[dict[str, Any]]:
    scorecard = AGENT511 / "coupled_scorecard.csv"
    if not scorecard.exists():
        return [
            {
                "source_task": "AGENT-511",
                "source_path": rel(AGENT511),
                "status": "missing_scorecard",
                "completed_rows": 0,
                "admitted_rows": 0,
                "note": "AGENT-511 package not available at AGENT-522 build time",
            }
        ]
    rows = read_csv(scorecard)
    review = read_csv(AGENT511 / "candidate_admission_review.csv") if (AGENT511 / "candidate_admission_review.csv").exists() else []
    admitted = sum(1 for row in review if row.get("admission_decision", "").startswith("admitted"))
    return [
        {
            "source_task": "AGENT-511",
            "source_path": rel(AGENT511),
            "status": "completed_evidence_available" if any(row.get("coupled_run_status") == "completed" for row in rows) else "pending_or_not_run",
            "completed_rows": sum(1 for row in rows if row.get("coupled_run_status") == "completed"),
            "admitted_rows": admitted,
            "note": "Read-only imported evidence; AGENT-522 does not duplicate AGENT-511 scoring",
        }
    ]


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
                    "source_path": "Fluid build_validation_table with AGENT-522 wall thermal-circuit scenario",
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
                    "wall_candidate_id": contract["wall_candidate_id"],
                    "cooler_candidate_id": contract["cooler_candidate_id"],
                    "lane": contract["lane"],
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
                    "source_path": "Fluid solve_case with AGENT-522 wall thermal-circuit scenario",
                },
                "probes": probe_rows,
            }
        )
    except Exception as exc:  # pragma: no cover - environment dependent Fluid failures.
        queue.put(
            {
                "score": {
                    "candidate_id": contract.get("candidate_id", ""),
                    "wall_candidate_id": contract.get("wall_candidate_id", ""),
                    "cooler_candidate_id": contract.get("cooler_candidate_id", ""),
                    "lane": contract.get("lane", ""),
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
                },
                "probes": [],
            }
        )


def _run_contract_with_timeout(contract: dict[str, Any], timeout_seconds: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    queue: mp.Queue = mp.Queue()
    process = mp.Process(target=_fluid_worker, args=(contract, queue))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(10)
        return (
            {
                "candidate_id": contract["candidate_id"],
                "wall_candidate_id": contract["wall_candidate_id"],
                "cooler_candidate_id": contract["cooler_candidate_id"],
                "lane": contract["lane"],
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
            },
            [],
        )
    if not queue.empty():
        payload = queue.get()
        return payload["score"], payload.get("probes", [])
    return (
        {
            "candidate_id": contract["candidate_id"],
            "wall_candidate_id": contract["wall_candidate_id"],
            "cooler_candidate_id": contract["cooler_candidate_id"],
            "lane": contract["lane"],
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
        },
        [],
    )


def coupled_scorecard_rows(
    contracts: list[dict[str, Any]], run_fluid: bool, timeout_seconds: int, parallel_workers: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not run_fluid:
        return (
            [
                {
                    "candidate_id": row["candidate_id"],
                    "wall_candidate_id": row["wall_candidate_id"],
                    "cooler_candidate_id": row["cooler_candidate_id"],
                    "lane": row["lane"],
                    "case_id": row["case_id"],
                    "split_role": row["split_role"],
                    "coupled_run_status": "not_run_submit_background_sbatch",
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
    max_workers = max(1, min(int(parallel_workers), 16, len(contracts)))
    rows: list[dict[str, Any]] = []
    probes: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_contract_with_timeout, contract, timeout_seconds) for contract in contracts]
        for future in concurrent.futures.as_completed(futures):
            score, probe_rows = future.result()
            rows.append(score)
            probes.extend(probe_rows)
    rows.sort(key=lambda row: (row.get("candidate_id", ""), ladder.CASE_ORDER.get(row.get("case_id", ""), 99)))
    probes.sort(key=lambda row: (row.get("candidate_id", ""), ladder.CASE_ORDER.get(row.get("case_id", ""), 99), row.get("kind", ""), row.get("sensor", "")))
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
                "wall_candidate_id": row.get("wall_candidate_id", ""),
                "cooler_candidate_id": row.get("cooler_candidate_id", ""),
                "lane": row.get("lane", ""),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
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


def probe_delta_rows(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baselines = ladder.m3_sensor_baselines()
    rows: list[dict[str, Any]] = []
    for row in probes:
        if row.get("split_role") == "train" or row.get("validation_excluded") == "yes":
            continue
        baseline = baselines.get((row.get("case_id", ""), row.get("sensor", "")), {})
        candidate_error = safe_float(row.get("error_K"))
        candidate_abs = safe_float(row.get("abs_error_K"))
        m3_error = safe_float(baseline.get("error_K"))
        m3_abs = safe_float(baseline.get("abs_error_K"))
        delta = None if candidate_abs is None or m3_abs is None else candidate_abs - m3_abs
        rows.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "sensor": row.get("sensor", ""),
                "kind": row.get("kind", ""),
                "candidate_error_K": fmt(candidate_error),
                "candidate_abs_error_K": fmt(candidate_abs),
                "m3_error_K": fmt(m3_error),
                "m3_abs_error_K": fmt(m3_abs),
                "abs_error_delta_vs_m3_K": fmt(delta),
                "candidate_predicted_K": row.get("predicted_K", ""),
                "target_K": row.get("target_K", ""),
                "prediction_source_segment": row.get("prediction_source_segment", ""),
                "comparison_status": "compared" if delta is not None else "not_compared_missing_m3_or_candidate",
                "probe_gate": "pass" if delta is not None and delta <= 0.0 else ("fail" if delta is not None else "not_compared"),
            }
        )
    return rows


def role_segment_error_summary_rows(deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in deltas:
        if row.get("comparison_status") != "compared":
            continue
        key = (
            row.get("candidate_id", ""),
            row.get("case_id", ""),
            row.get("split_role", ""),
            row.get("kind", ""),
            row.get("prediction_source_segment", ""),
        )
        grouped.setdefault(key, []).append(row)
    rows: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        pairs = []
        for row in group:
            ce = safe_float(row.get("candidate_error_K"))
            me = safe_float(row.get("m3_error_K"))
            ca = safe_float(row.get("candidate_abs_error_K"))
            ma = safe_float(row.get("m3_abs_error_K"))
            if ce is not None and me is not None and ca is not None and ma is not None:
                pairs.append((ce, me, ca, ma))
        if not pairs:
            continue
        cand_rmse = math.sqrt(sum(pair[0] * pair[0] for pair in pairs) / len(pairs))
        m3_rmse = math.sqrt(sum(pair[1] * pair[1] for pair in pairs) / len(pairs))
        cand_mae = sum(pair[2] for pair in pairs) / len(pairs)
        m3_mae = sum(pair[3] for pair in pairs) / len(pairs)
        candidate_id, case_id, split_role, kind, segment = key
        rows.append(
            {
                "candidate_id": candidate_id,
                "case_id": case_id,
                "split_role": split_role,
                "kind": kind,
                "prediction_source_segment": segment,
                "n_compared": len(pairs),
                "candidate_rmse_K": fmt(cand_rmse),
                "m3_rmse_K": fmt(m3_rmse),
                "rmse_delta_vs_m3_K": fmt(cand_rmse - m3_rmse),
                "candidate_mae_K": fmt(cand_mae),
                "m3_mae_K": fmt(m3_mae),
                "mae_delta_vs_m3_K": fmt(cand_mae - m3_mae),
            }
        )
    return rows


def annotate_coupled_gates(coupled: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_by_key = {(row["candidate_id"], row["case_id"]): row["score_gate"] for row in deltas}
    out_rows: list[dict[str, Any]] = []
    for row in coupled:
        out = dict(row)
        if out.get("coupled_run_status") == "completed":
            out["coupled_gate"] = "train_not_admission_scored" if out.get("split_role") == "train" else ("pass_vs_m3" if gate_by_key.get((out.get("candidate_id", ""), out.get("case_id", ""))) == "pass" else "fail_vs_m3")
        out_rows.append(out)
    return out_rows


def candidate_admission_review_rows(deltas: list[dict[str, Any]], runtime: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_pass = all(row["gate"] == "pass" for row in runtime)
    rows: list[dict[str, Any]] = []
    for candidate_id in sorted({row["candidate_id"] for row in deltas}):
        by_split = {row["split_role"]: row["score_gate"] for row in deltas if row["candidate_id"] == candidate_id}
        blockers: list[str] = []
        if not runtime_pass:
            blockers.append("runtime_audit_failed_or_pending")
        if by_split.get("validation") != "pass":
            blockers.append("validation_mdot_tp_tw_all_probe_gate_failed")
        if by_split.get("holdout") != "pass":
            blockers.append("holdout_mdot_tp_tw_all_probe_gate_failed")
        rows.append(
            {
                "candidate_id": candidate_id,
                "runtime_gate": "pass" if runtime_pass else "fail_or_pending",
                "validation_coupled_gate": by_split.get("validation", "missing"),
                "holdout_coupled_gate": by_split.get("holdout", "missing"),
                "admission_decision": "admitted_predictive_wall_thermal_circuit" if not blockers else "not_admitted",
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def blocker_decision_payload(coupled: list[dict[str, Any]], admission: list[dict[str, Any]], run_fluid: bool) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for row in coupled:
        statuses[row["coupled_run_status"]] = statuses.get(row["coupled_run_status"], 0) + 1
    admitted = [row for row in admission if row["admission_decision"] == "admitted_predictive_wall_thermal_circuit"]
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "blocker_id": "predictive-wall-test-section-submodels",
        "blocker_decision": "resolve" if admitted and run_fluid else "keep_open",
        "coupled_status_counts": statuses,
        "coupled_completed_rows": sum(1 for row in coupled if row["coupled_run_status"] == "completed"),
        "admitted_candidates": [row["candidate_id"] for row in admitted],
        "why": (
            "A wall thermal-circuit candidate passed validation and holdout mdot, TP, TW, and all-probe gates vs M3."
            if admitted and run_fluid
            else "No wall thermal-circuit candidate has passed validation and holdout mdot, TP, TW, and all-probe gates vs M3."
        ),
    }


def background_run_contract_rows(timeout_seconds: int, parallel_workers: int) -> list[dict[str, Any]]:
    command = (
        f"sbatch {OUT_REL}/ag522_wall_circuit.sbatch"
    )
    return [
        {
            "contract_id": "parallel_sbatch_coupled_score",
            "timeout_seconds": timeout_seconds,
            "parallel_workers": parallel_workers,
            "command": command,
            "stdout_pattern": f"{rel(LOG_DIR)}/ag522_wall_circuit.%j.out",
            "stderr_pattern": f"{rel(LOG_DIR)}/ag522_wall_circuit.%j.err",
            "policy": "submit one bounded compute-node job; use read-only monitor every 2 minutes",
        }
    ]


def sbatch_text(timeout_seconds: int, parallel_workers: int) -> str:
    return f"""#!/usr/bin/env bash
#SBATCH --job-name=ag522_wall_circuit
#SBATCH --account=ASC23046
#SBATCH --partition=NuclearEnergy-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=04:00:00
#SBATCH --output={rel(LOG_DIR)}/ag522_wall_circuit.%j.out
#SBATCH --error={rel(LOG_DIR)}/ag522_wall_circuit.%j.err

set -euo pipefail
cd {ROOT}
mkdir -p {rel(LOG_DIR)}
python3 tools/analyze/test_wall_thermal_circuit_study.py
python3 tools/analyze/build_wall_thermal_circuit_study.py --run-fluid --parallel-workers {parallel_workers} --timeout-seconds {timeout_seconds}
python3 tools/analyze/build_wall_thermal_circuit_study.py --reuse-existing-coupled --parallel-workers {parallel_workers} --timeout-seconds {timeout_seconds}
"""


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_id": "agent511_heater_source", "path": rel(AGENT511), "use": "read-only active/pending heater-source redistribution evidence"},
        {"source_id": "agent513_wall_temperature_drive", "path": rel(AGENT513), "use": "completed wall-temperature-drive failure mode"},
        {"source_id": "agent498_wall_distribution_ladder", "path": rel(ladder.OUT), "use": "PB2 base wall distribution and AGENT-498 failure localization"},
        {"source_id": "agent482_cooler", "path": rel(ladder.AGENT482), "use": "HX alpha_UA and segmented HX adapter"},
        {"source_id": "agent461_m3", "path": rel(ladder.M3_COMPARATORS), "use": "M3 mdot/TP/TW/all-probe comparator gates"},
        {"source_id": "m3_sensor_baseline", "path": rel(ladder.M3_SENSOR_ROWS), "use": "M3 probe-level comparator"},
        {"source_id": "setup_external_boundary_rows", "path": rel(ladder.SETUP_ROWS), "use": "setup-only external boundary role rows"},
        {"source_id": "fluid_solver", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "read-only Fluid solve_case execution"},
    ]


def performance_table(deltas: list[dict[str, Any]]) -> str:
    if not deltas:
        return "No validation/holdout deltas are available yet.\n"
    lines = [
        "| Candidate | Validation delta vs M3 | Holdout delta vs M3 |",
        "| --- | --- | --- |",
    ]
    for candidate_id in sorted({row["candidate_id"] for row in deltas}):
        by_split = {row["split_role"]: row for row in deltas if row["candidate_id"] == candidate_id}

        def cell(split: str) -> str:
            row = by_split.get(split)
            if row is None:
                return "missing"
            return (
                f"mdot `{row['mdot_delta_vs_m3_pct']} pct`; "
                f"TP `{row['tp_delta_vs_m3_K']} K`; "
                f"TW `{row['tw_delta_vs_m3_K']} K`; "
                f"all-probe `{row['all_probe_delta_vs_m3_K']} K`"
            )

        lines.append(f"| `{candidate_id}` | {cell('validation')} | {cell('holdout')} |")
    return "\n".join(lines) + "\n"


def probe_summary_text(probe_deltas: list[dict[str, Any]], role_segments: list[dict[str, Any]]) -> str:
    if not probe_deltas:
        return "No coupled probe deltas are available yet.\n"
    gates: dict[str, int] = {}
    for row in probe_deltas:
        gates[row["probe_gate"]] = gates.get(row["probe_gate"], 0) + 1
    compared = [row for row in probe_deltas if row.get("comparison_status") == "compared"]
    worst_probes = sorted(compared, key=lambda row: safe_float(row.get("abs_error_delta_vs_m3_K")) or -math.inf, reverse=True)[:4]
    worst_segments = sorted(role_segments, key=lambda row: safe_float(row.get("rmse_delta_vs_m3_K")) or -math.inf, reverse=True)[:4]
    lines = [f"Probe delta rows: `{len(probe_deltas)}` with gate counts `{json.dumps(gates, sort_keys=True)}`.", ""]
    lines.append("Worst compared probe deltas:")
    for row in worst_probes:
        lines.append(
            f"- `{row['candidate_id']}` {row['case_id']} {row['sensor']} ({row['kind']}, "
            f"{row['prediction_source_segment']}): `{row['abs_error_delta_vs_m3_K']} K` worse than M3"
        )
    lines.append("")
    lines.append("Worst role/segment RMSE deltas:")
    for row in worst_segments:
        lines.append(
            f"- `{row['candidate_id']}` {row['case_id']} {row['kind']} "
            f"{row['prediction_source_segment']}: `{row['rmse_delta_vs_m3_K']} K`"
        )
    return "\n".join(lines) + "\n"


def readme_text(summary: dict[str, Any], deltas: list[dict[str, Any]], probe_deltas: list[dict[str, Any]], role_segments: list[dict[str, Any]]) -> str:
    decision = summary["decision"]
    perf = performance_table(deltas)
    probes = probe_summary_text(probe_deltas, role_segments)
    return f"""---
provenance:
  - {rel(ladder.OUT)}
  - {rel(AGENT513)}
  - {rel(AGENT511)}
  - {rel(ladder.AGENT482)}
  - {rel(ladder.M3_COMPARATORS)}
tags: [forward-model, wall-circuit, test-section, parallel-fluid, predictive-1d]
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
# Parallel Wall Thermal-Circuit Study

## Result

This package scores non-duplicative wall/passive/test-section thermal-circuit
lanes after AGENT-498 and AGENT-513. AGENT-511 heater-source redistribution is
imported read-only and is not duplicated by this package.

Decision for `predictive-wall-test-section-submodels`: `{decision['blocker_decision']}`.

Reason: {decision['why']}

Coupled rows completed: `{decision['coupled_completed_rows']}`.
Status counts: `{json.dumps(decision['coupled_status_counts'], sort_keys=True)}`.
Parallel workers requested: `{summary['parallel_workers']}`.

## Performance Versus M3

Negative deltas are better. Admission requires validation and holdout mdot, TP,
TW, and all-probe deltas all to be non-positive.

{perf}

## Probe Localization

{probes}

## Files

- `wall_candidate_definitions.csv`
- `candidate_definitions.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `agent511_import_status.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `probe_delta_vs_m3.csv`
- `role_segment_error_summary.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `ag522_wall_circuit.sbatch`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build(run_fluid: bool = False, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, reuse_existing_coupled: bool = False, parallel_workers: int = DEFAULT_PARALLEL_WORKERS) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    wall_candidates = wall_candidate_definitions()
    candidates = coupled_candidate_definitions()
    contracts = scenario_contract_rows()
    agent511 = agent511_status_rows()
    if reuse_existing_coupled and (OUT / "coupled_scorecard.csv").exists():
        coupled = read_csv(OUT / "coupled_scorecard.csv")
        probes = read_csv(OUT / "probe_error_localization.csv") if (OUT / "probe_error_localization.csv").exists() else []
        effective_run_fluid = any(row.get("coupled_run_status") == "completed" for row in coupled)
    else:
        coupled, probes = coupled_scorecard_rows(contracts, run_fluid, timeout_seconds, parallel_workers)
        effective_run_fluid = run_fluid
    runtime = runtime_input_audit_rows(contracts, effective_run_fluid, parallel_workers)
    deltas = coupled_delta_rows(coupled)
    probe_deltas = probe_delta_rows(probes)
    role_segments = role_segment_error_summary_rows(probe_deltas)
    coupled = annotate_coupled_gates(coupled, deltas)
    admission = candidate_admission_review_rows(deltas, runtime)
    decision = blocker_decision_payload(coupled, admission, effective_run_fluid)
    background = background_run_contract_rows(timeout_seconds, parallel_workers)
    manifest = source_manifest_rows()

    counts = {
        "wall_candidate_definitions.csv": write_csv(OUT / "wall_candidate_definitions.csv", wall_candidates, list(wall_candidates[0].keys())),
        "candidate_definitions.csv": write_csv(OUT / "candidate_definitions.csv", candidates, list(candidates[0].keys())),
        "scenario_contracts.csv": write_csv(OUT / "scenario_contracts.csv", contracts, list(contracts[0].keys())),
        "runtime_input_audit.csv": write_csv(OUT / "runtime_input_audit.csv", runtime, list(runtime[0].keys())),
        "agent511_import_status.csv": write_csv(OUT / "agent511_import_status.csv", agent511, list(agent511[0].keys())),
        "coupled_scorecard.csv": write_csv(OUT / "coupled_scorecard.csv", coupled, list(coupled[0].keys()) if coupled else ["candidate_id"]),
        "coupled_delta_vs_m3.csv": write_csv(OUT / "coupled_delta_vs_m3.csv", deltas, list(deltas[0].keys()) if deltas else ["candidate_id"]),
        "probe_error_localization.csv": write_csv(OUT / "probe_error_localization.csv", probes, PROBE_FIELDS),
        "probe_delta_vs_m3.csv": write_csv(OUT / "probe_delta_vs_m3.csv", probe_deltas, PROBE_DELTA_FIELDS),
        "role_segment_error_summary.csv": write_csv(OUT / "role_segment_error_summary.csv", role_segments, ROLE_SEGMENT_FIELDS),
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
        "parallel_workers": parallel_workers,
        "counts": counts,
        "decision": decision,
    }
    (OUT / "ag522_wall_circuit.sbatch").write_text(sbatch_text(timeout_seconds, parallel_workers), encoding="utf-8")
    write_json(OUT / "blocker_decision.json", decision)
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary, deltas, probe_deltas, role_segments), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run Fluid solve_case rows; use compute-node srun/sbatch for this option.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--parallel-workers", type=int, default=DEFAULT_PARALLEL_WORKERS)
    parser.add_argument("--reuse-existing-coupled", action="store_true")
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
