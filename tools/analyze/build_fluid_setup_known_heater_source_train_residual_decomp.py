#!/usr/bin/env python3
"""Run train-only residual decomposition for setup-known heater redistribution."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import signal
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp"
TASK_ID = "TODO-FLUID-SETUP-KNOWN-HEATER-SOURCE-TRAIN-RESIDUAL-DECOMP-2026-07-21"
FLUID_ROOT = ROOT.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid"
PHASE_E = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve"
FJ = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics"
CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract"
CASE_NAME = "Salt 2"
CASE_ID = "salt_2"
SCENARIO_NAME = "setup_known_lower_leg_heater_tw4_to_tp3_train_only"
TIMEOUT_SECONDS = 180


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def as_float(value: Any, default: float = float("nan")) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def finite(value: Any) -> bool:
    numeric = as_float(value)
    return math.isfinite(numeric)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or ["empty"])
        writer.writeheader()
        writer.writerows(rows)


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [jsonable(v) for v in value]
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return None
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def import_fluid() -> dict[str, Any]:
    sys.path.insert(0, str(FLUID_ROOT))
    from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME  # type: ignore
    from tamu_loop_model_v2.reporting import build_validation_table, summarize_result  # type: ignore
    from tamu_loop_model_v2.solver import ScenarioConfig, solve_case  # type: ignore

    return {
        "EXPERIMENT_CASES": EXPERIMENT_CASES,
        "VALIDATION_CASES_BY_NAME": VALIDATION_CASES_BY_NAME,
        "build_validation_table": build_validation_table,
        "summarize_result": summarize_result,
        "ScenarioConfig": ScenarioConfig,
        "solve_case": solve_case,
    }


def role_rows_from_phase_e() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(PHASE_E / "role_row_ledger.csv"):
        rows.append(
            {
                "parent_segment": row["parent_segment"],
                "role": row["role"],
                "mode": row["mode"],
                "h_W_m2K": as_float(row["h_W_m2K"]),
                "area_m2": as_float(row["area_m2"]),
                "coverage_multiplier": as_float(row["coverage_multiplier"], 1.0),
                "Ta_K": as_float(row["Ta_K"]),
                "Tsur_K": as_float(row["Tsur_K"]),
                "emissivity": as_float(row["emissivity"]),
                "drive_selector": row["drive_selector"],
                "source": row["source"],
                "source_case_id": row["source_case_id"],
                "source_segment_id": row["source_segment_id"],
                "patch_group": row["patch_group"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def sensor_metrics(sensor_rows: list[dict[str, Any]]) -> dict[str, Any]:
    all_errors = [as_float(row.get("error_K")) for row in sensor_rows if finite(row.get("error_K"))]
    tp_errors = [as_float(row.get("error_K")) for row in sensor_rows if row.get("kind") == "TP" and finite(row.get("error_K"))]
    tw_errors = [as_float(row.get("error_K")) for row in sensor_rows if row.get("kind") == "TW" and finite(row.get("error_K"))]

    def mae(values: list[float]) -> float:
        return sum(abs(value) for value in values) / len(values) if values else float("nan")

    def rmse(values: list[float]) -> float:
        return math.sqrt(sum(value * value for value in values) / len(values)) if values else float("nan")

    return {
        "all_probe_count": len(all_errors),
        "tp_count": len(tp_errors),
        "tw_count": len(tw_errors),
        "all_mae_K": mae(all_errors),
        "tp_mae_K": mae(tp_errors),
        "tw_mae_K": mae(tw_errors),
        "all_rmse_K": rmse(all_errors),
        "tp_rmse_K": rmse(tp_errors),
        "tw_rmse_K": rmse(tw_errors),
        "max_abs_error_K": max((abs(value) for value in all_errors), default=float("nan")),
    }


def run_worker(output_path: Path) -> None:
    try:
        fluid = import_fluid()
        scenario = fluid["ScenarioConfig"](
            name=SCENARIO_NAME,
            outer_closure_mode="external_boundary_table",
            external_boundary_role_rows=role_rows_from_phase_e(),
            heater_source_mode="tw4_to_tp3_three_span",
        )
        case = next(case for case in fluid["EXPERIMENT_CASES"] if case.name == CASE_NAME)
        result = fluid["solve_case"](case, scenario)
        validation_record = fluid["VALIDATION_CASES_BY_NAME"][CASE_NAME]
        sensor_rows = fluid["build_validation_table"](result, validation_record).to_dict("records")
        summary_df = fluid["summarize_result"](
            result,
            validation_record=None,
            run_metadata={
                "task_id": TASK_ID,
                "split_role": "train",
                "runtime_input_contract": "setup_known_lower_leg_heater_source_plus_setup_external_boundary_dictionary",
                "validation_holdout_external_scoring": "not_run_by_policy",
            },
        )
        payload = {
            "status": "pass",
            "root_status": result.root_status,
            "root_rejection_reason": result.root_rejection_reason,
            "mdot_kg_s": result.mdot_kg_s,
            "pressure_residual_Pa": result.pressure_residual_Pa,
            "qambient_total_W": result.qambient_total_W,
            "qhx_total_W": result.qhx_total_W,
            "temperature_periodicity_error_K": result.temperature_periodicity_error_K,
            "metrics": sensor_metrics(sensor_rows),
            "sensor_rows": sensor_rows,
            "segment_rows": result.segment_df.to_dict("records"),
            "summary_rows": summary_df.to_dict("records"),
        }
    except Exception as exc:
        payload = {
            "status": "fail",
            "failure_or_timeout": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
    write_json(output_path, payload)


def baseline_sensor_rows() -> list[dict[str, str]]:
    return read_csv(FJ / "phase_f_thermal_residual_decomposition/sensor_segment_residuals.csv")


def baseline_metrics() -> dict[str, float]:
    summary = json.loads((FJ / "summary.json").read_text(encoding="utf-8"))
    return {
        "all_mae_K": as_float(summary.get("baseline_all_mae_K")),
        "tp_mae_K": as_float(summary.get("baseline_tp_mae_K")),
        "tw_mae_K": as_float(summary.get("baseline_tw_mae_K")),
    }


def response_class(delta_abs_residual_K: float) -> str:
    if not math.isfinite(delta_abs_residual_K):
        return "not_evaluable"
    if delta_abs_residual_K < -1.0:
        return "improves"
    if delta_abs_residual_K > 1.0:
        return "worsens"
    return "insensitive"


def build_sensor_delta_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_by_sensor = {row["sensor"]: row for row in baseline_sensor_rows()}
    candidate_by_sensor = {str(row["sensor"]): row for row in payload.get("sensor_rows", [])}
    rows: list[dict[str, Any]] = []
    for sensor, baseline in baseline_by_sensor.items():
        candidate = candidate_by_sensor.get(sensor, {})
        base_resid = as_float(baseline.get("residual_K"))
        cand_resid = as_float(candidate.get("error_K"))
        base_abs = abs(base_resid) if math.isfinite(base_resid) else float("nan")
        cand_abs = abs(cand_resid) if math.isfinite(cand_resid) else float("nan")
        delta = cand_resid - base_resid if math.isfinite(base_resid) and math.isfinite(cand_resid) else float("nan")
        delta_abs = cand_abs - base_abs if math.isfinite(base_abs) and math.isfinite(cand_abs) else float("nan")
        rows.append(
            {
                "case_id": CASE_ID,
                "sensor": sensor,
                "sensor_kind": baseline.get("sensor_kind", ""),
                "prediction_source_segment": baseline.get("prediction_source_segment", ""),
                "baseline_residual_K": base_resid if math.isfinite(base_resid) else "",
                "candidate_residual_K": cand_resid if math.isfinite(cand_resid) else "",
                "delta_residual_K": delta if math.isfinite(delta) else "",
                "baseline_abs_residual_K": base_abs if math.isfinite(base_abs) else "",
                "candidate_abs_residual_K": cand_abs if math.isfinite(cand_abs) else "",
                "delta_abs_residual_K": delta_abs if math.isfinite(delta_abs) else "",
                "response_class": response_class(delta_abs),
                "claim_boundary": "train-only source-lane residual delta; not validation/holdout/external scoring",
            }
        )
    return rows


def build_metric_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base = baseline_metrics()
    metrics = payload.get("metrics", {})
    rows = []
    for metric in ["all_mae_K", "tp_mae_K", "tw_mae_K", "all_rmse_K", "tp_rmse_K", "tw_rmse_K", "max_abs_error_K"]:
        candidate = as_float(metrics.get(metric))
        baseline = as_float(base.get(metric))
        rows.append(
            {
                "metric": metric,
                "baseline_value": baseline if math.isfinite(baseline) else "",
                "candidate_value": candidate if math.isfinite(candidate) else "",
                "delta_candidate_minus_baseline": candidate - baseline if math.isfinite(candidate) and math.isfinite(baseline) else "",
                "claim_boundary": "train-only comparison; no fitting, freeze, admission, validation, holdout, or external scoring",
            }
        )
    return rows


def decision_from_rows(sensor_rows: list[dict[str, Any]], payload: dict[str, Any]) -> str:
    if payload.get("status") != "pass" or payload.get("root_status") != "accepted":
        return "source_lane_no_material_improvement_fail_closed"
    tw_focus = [row for row in sensor_rows if row["sensor"] in {"TW4", "TW5", "TW6"}]
    improvements = [
        as_float(row.get("delta_abs_residual_K"))
        for row in tw_focus
        if row.get("response_class") == "improves"
    ]
    if len(improvements) >= 2 and sum(improvements) / len(improvements) < -5.0:
        return "source_lane_improves_and_candidate_ready_for_source_property_review"
    if improvements:
        return "source_lane_partial_improvement_model_form_still_needed"
    return "source_lane_no_material_improvement_fail_closed"


def run_bounded_worker(timeout_seconds: int = TIMEOUT_SECONDS) -> tuple[dict[str, Any], str]:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    worker_path = PACKAGE / "worker_result.json"
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", str(worker_path)]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        env=env,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        timeout = False
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
        timeout = True
    (PACKAGE / "worker_stdout.txt").write_text(stdout or "", encoding="utf-8")
    (PACKAGE / "worker_stderr.txt").write_text(stderr or "", encoding="utf-8")
    if timeout:
        payload = {
            "status": "timeout",
            "failure_or_timeout": f"worker exceeded {timeout_seconds} s timeout and was killed",
        }
    elif worker_path.exists():
        payload = json.loads(worker_path.read_text(encoding="utf-8"))
    else:
        payload = {
            "status": "fail",
            "failure_or_timeout": f"worker exited {proc.returncode} without worker_result.json",
        }
    return payload, "timeout" if timeout else ("pass" if proc.returncode == 0 and payload.get("status") == "pass" else "fail")


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(PHASE_E / 'train_solve_summary.csv')}
  - {rel(FJ / 'phase_f_thermal_residual_decomposition/sensor_segment_residuals.csv')}
  - {rel(CONTRACT / 'setup_known_source_contract.csv')}
tags: [fluid, setup-known-source, heater-source, train-only, residual-decomposition]
related:
  - {rel(CONTRACT)}
task: {TASK_ID}
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
---
# Setup-Known Heater Source Train Residual Decomposition

This package runs one bounded local Fluid `solve_case` for Salt2 train/support
using the existing `heater_source_mode=tw4_to_tp3_three_span` source lane.

Decision: `{summary['decision']}`.

- worker status: `{summary['worker_status']}`
- root status: `{summary.get('root_status', '')}`
- validation/holdout/external rows consumed: `0/0/0`
- freeze/admission/fitting: `false`

The output is train-only diagnostic evidence. It does not release S11, S15, S6,
or final predictive scores.
"""
    (PACKAGE / "README.md").write_text(readme, encoding="utf-8")


def build(timeout_seconds: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    payload, worker_status = run_bounded_worker(timeout_seconds)
    sensor_delta_rows = build_sensor_delta_rows(payload) if payload.get("status") == "pass" else []
    metric_rows = build_metric_rows(payload) if payload.get("status") == "pass" else []
    decision = decision_from_rows(sensor_delta_rows, payload)

    write_csv(PACKAGE / "train_metric_comparison.csv", metric_rows)
    write_csv(PACKAGE / "sensor_residual_delta.csv", sensor_delta_rows)
    write_csv(PACKAGE / "tw4_tw6_focus.csv", [row for row in sensor_delta_rows if row.get("sensor") in {"TW4", "TW5", "TW6"}])
    write_csv(PACKAGE / "candidate_sensor_rows.csv", payload.get("sensor_rows", []))
    write_csv(PACKAGE / "candidate_segment_states.csv", payload.get("segment_rows", []))
    write_csv(PACKAGE / "candidate_train_solve_summary.csv", payload.get("summary_rows", []))
    write_csv(
        PACKAGE / "decision_table.csv",
        [
            {
                "decision": decision,
                "worker_status": worker_status,
                "root_status": payload.get("root_status", ""),
                "basis": "TW4-TW6 train-only residual response to deterministic setup-known heater source redistribution",
                "s11_trigger": False,
                "s15_trigger": False,
                "s6_trigger": False,
                "claim_boundary": "no candidate freeze, no source/property release, no validation/holdout/external scoring",
            }
        ],
    )
    write_csv(
        PACKAGE / "runtime_leakage_audit.csv",
        [
            {"check_id": "RT-001", "item": "validation TP/TW temperatures", "runtime_used": False, "status": "post_solve_reference_only"},
            {"check_id": "RT-002", "item": "holdout/external temperatures", "runtime_used": False, "status": "not_consumed"},
            {"check_id": "RT-003", "item": "realized CFD wallHeatFlux", "runtime_used": False, "status": "forbidden_not_used"},
            {"check_id": "RT-004", "item": "CFD mdot", "runtime_used": False, "status": "forbidden_not_used"},
            {"check_id": "RT-005", "item": "hidden residual/internal Nu absorption", "runtime_used": False, "status": "forbidden_not_used"},
        ],
    )
    write_csv(
        PACKAGE / "source_manifest.csv",
        [
            {"source_id": "phase_e_role_rows", "path": rel(PHASE_E / "role_row_ledger.csv"), "use": "baseline setup external-boundary role rows", "mutation": False},
            {"source_id": "phase_e_baseline", "path": rel(PHASE_E / "train_solve_summary.csv"), "use": "baseline train metrics", "mutation": False},
            {"source_id": "fj_sensor_residuals", "path": rel(FJ / "phase_f_thermal_residual_decomposition/sensor_segment_residuals.csv"), "use": "baseline sensor residuals", "mutation": False},
            {"source_id": "source_contract", "path": rel(CONTRACT / "setup_known_source_contract.csv"), "use": "setup-known heater source contract", "mutation": False},
            {"source_id": "fluid_solver", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "local Fluid solve_case execution", "mutation": False},
        ],
        ["source_id", "path", "use", "mutation"],
    )
    summary = {
        "task_id": TASK_ID,
        "date": "2026-07-21",
        "status": "complete",
        "worker_status": worker_status,
        "root_status": payload.get("root_status", ""),
        "decision": decision,
        "validation_rows_consumed": 0,
        "holdout_rows_consumed": 0,
        "external_test_rows_consumed": 0,
        "fit_or_model_selection": False,
        "freeze_or_admission_decision": False,
        "source_property_release": False,
        "native_output_mutation": False,
        "external_fluid_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "s11_trigger": False,
        "s15_trigger": False,
        "s6_trigger": False,
    }
    write_json(PACKAGE / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=TIMEOUT_SECONDS)
    args = parser.parse_args()
    if args.worker:
        run_worker(args.worker)
        return
    summary = build(timeout_seconds=args.timeout_seconds)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
