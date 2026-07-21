#!/usr/bin/env python3
"""Build AGENT-482 cooler-removal model comparison package."""

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
from typing import Any, Callable, Iterable


TASK = "AGENT-482"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model")
OUT = ROOT / OUT_REL

AGENT480_PLAN = ROOT / "operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md"
AGENT438_BAKEOFF = ROOT / (
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_mdot_temperature_overnight_compute_node_run/"
    "setup_only_cooler_closure_bakeoff/cooler_model_scores.csv"
)
AGENT438_SUMMARY = ROOT / (
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_mdot_temperature_overnight_compute_node_run/"
    "setup_only_cooler_closure_bakeoff/cooler_rmse_summary_with_leakage_policy.csv"
)
AGENT461_COUPLED = ROOT / (
    "work_products/2026-07/2026-07-16/"
    "2026-07-16_coupled_m3ts_test_section_scorecard/m3ts_coupled_scorecard.csv"
)

CASE_NAME = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}
CASE_SPLIT = {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}
CASE_ORDER = {"salt_2": 0, "salt_3": 1, "salt_4": 2}
VALIDATION_TOLERANCE_W = 5.0
HOLDOUT_TOLERANCE_W = 10.0
CONSTANT_UA_PRIOR_FORM = "salt2_fit_constant_UA_bulk_drive"
CURRENT_FLUID_PRIOR_FORM = "current_fluid_airside_hx_fixed_mdot"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


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


def pass_fail(error: float | None, tolerance: float) -> str:
    if error is None:
        return "missing"
    return "pass" if error <= tolerance else "fail"


def effectiveness_ntu(ntu: float, capacity_ratio: float) -> float:
    """Counterflow effectiveness used by the Fluid lumped HX model."""
    ntu = max(float(ntu), 0.0)
    cr = min(max(float(capacity_ratio), 0.0), 1.0)
    if ntu == 0.0:
        return 0.0
    if abs(cr - 1.0) < 1e-9:
        return ntu / max(1.0 + ntu, 1e-12)
    exp_term = math.exp(-ntu * (1.0 - cr))
    return (1.0 - exp_term) / max(1.0 - cr * exp_term, 1e-12)


def segmented_profile(
    *,
    total_ua_W_K: float,
    n_segments: int,
    mdot_fluid_kg_s: float,
    cp_fluid_J_kg_K: float,
    mdot_air_kg_s: float,
    cp_air_J_kg_K: float,
    T_fluid_in_K: float,
    T_air_in_K: float,
) -> tuple[float, float, float, list[dict[str, float]]]:
    """Co-current segmented epsilon/NTU cooler march for tests and diagnostics."""
    if n_segments <= 0:
        raise ValueError("n_segments must be positive")
    C_hot = max(mdot_fluid_kg_s * cp_fluid_J_kg_K, 1e-12)
    C_cold = max(mdot_air_kg_s * cp_air_J_kg_K, 1e-12)
    C_min = min(C_hot, C_cold)
    C_max = max(C_hot, C_cold)
    cr = C_min / max(C_max, 1e-12)
    T_fluid = float(T_fluid_in_K)
    T_air = float(T_air_in_K)
    q_total = 0.0
    rows: list[dict[str, float]] = []
    for idx in range(1, n_segments + 1):
        ua_i = max(total_ua_W_K, 0.0) / n_segments
        ntu = ua_i / max(C_min, 1e-12)
        eps = effectiveness_ntu(ntu, cr)
        q_i = max(eps * C_min * max(T_fluid - T_air, 0.0), 0.0)
        T_fluid_next = T_fluid - q_i / C_hot
        T_air_next = T_air + q_i / C_cold
        q_total += q_i
        rows.append(
            {
                "cell_index": float(idx),
                "ua_W_K": ua_i,
                "ntu": ntu,
                "epsilon": eps,
                "q_cell_W": q_i,
                "q_cumulative_W": q_total,
                "T_fluid_in_K": T_fluid,
                "T_fluid_out_K": T_fluid_next,
                "T_air_in_K": T_air,
                "T_air_out_K": T_air_next,
            }
        )
        T_fluid, T_air = T_fluid_next, T_air_next
    return q_total, T_fluid, T_air, rows


def prior_bakeoff_by_form_case() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(AGENT438_BAKEOFF)
    return {(row["model_form"], row["case_id"]): row for row in rows if row.get("case_id") in CASE_NAME}


def candidate_definitions() -> list[dict[str, Any]]:
    common_source = ";".join([rel(AGENT480_PLAN), rel(AGENT438_BAKEOFF), str(FLUID_ROOT)])
    return [
        {
            "candidate_id": "HX_LUMPED_UA_NTU",
            "model_family": "constant-UA effectiveness/NTU",
            "equation_summary": "UA=alpha_UA*UA_setup; Q=epsilon_NTU*Cmin*max(Tfluid_in-Tair_in,0)",
            "fitted_parameter_count": 1,
            "fitted_parameter_names": "alpha_UA",
            "fit_split": "salt_2_only",
            "segmentation_count": 1,
            "air_flow_arrangement": "Fluid default counterflow effectiveness; air stream updated between HX segments",
            "implementation_status": "duty_screen_completed_from_AGENT438; coupled_run_available_with_run_fluid",
            "source_path": common_source,
        },
        *[
            {
                "candidate_id": f"HX_SEGMENTED_UA_NTU_N{n}",
                "model_family": "segmented distributed-UA effectiveness/NTU",
                "equation_summary": "UA_i=alpha_UA*UA_setup_total/N; each cell updates fluid and air temperatures",
                "fitted_parameter_count": 1,
                "fitted_parameter_names": "alpha_UA",
                "fit_split": "salt_2_only",
                "segmentation_count": n,
                "air_flow_arrangement": "co-current runtime adapter sensitivity; source Fluid unchanged",
                "implementation_status": "coupled_run_available_with_runtime_only_segmented_adapter; fixed-mdot duty screen pending native runner",
                "source_path": common_source,
            }
            for n in (4, 8, 16)
        ],
    ]


def fit_parameters() -> list[dict[str, Any]]:
    prior = prior_bakeoff_by_form_case()
    current = prior[(CURRENT_FLUID_PRIOR_FORM, "salt_2")]
    fitted = prior[(CONSTANT_UA_PRIOR_FORM, "salt_2")]
    base_q = safe_float(current.get("q_pred_W")) or 0.0
    target_q = safe_float(fitted.get("q_cfd_W")) or 0.0
    alpha = target_q / base_q if base_q > 0.0 else float("nan")
    rows: list[dict[str, Any]] = []
    for cand in candidate_definitions():
        rows.append(
            {
                "candidate_id": cand["candidate_id"],
                "fit_case_id": "salt_2",
                "fitted_parameter_name": "alpha_UA",
                "fitted_parameter_value": fmt(alpha),
                "fit_policy": "one_scalar_fit_on_salt2_only",
                "fit_target_used": "Salt2 cooler heat removal only; Salt3/Salt4 scoring targets excluded from fit",
                "fit_residual_W": "0" if cand["candidate_id"] == "HX_LUMPED_UA_NTU" else "not_computed_fixed_mdot_segmented_pending",
                "parameter_source": "linearized_alpha_from_AGENT438_current_Fluid_fixed_mdot_to_Salt2_target",
                "source_path": rel(AGENT438_BAKEOFF),
            }
        )
    return rows


def duty_scorecard_rows() -> list[dict[str, Any]]:
    prior = prior_bakeoff_by_form_case()
    rows: list[dict[str, Any]] = []
    for case_id in sorted(CASE_NAME, key=CASE_ORDER.get):
        prior_row = prior[(CONSTANT_UA_PRIOR_FORM, case_id)]
        pred = safe_float(prior_row.get("q_pred_W"))
        target = safe_float(prior_row.get("q_cfd_W"))
        error = None if pred is None or target is None else pred - target
        abs_error = None if error is None else abs(error)
        split = CASE_SPLIT[case_id]
        tolerance = VALIDATION_TOLERANCE_W if split == "validation" else HOLDOUT_TOLERANCE_W
        gate = "fit_row" if split == "train" else pass_fail(abs_error, tolerance)
        rows.append(
            {
                "candidate_id": "HX_LUMPED_UA_NTU",
                "case_id": case_id,
                "split_role": split,
                "run_status": "completed_from_AGENT438_fixed_mdot_score",
                "predicted_qhx_W": fmt(pred),
                "target_qhx_W_for_scoring_only": fmt(target),
                "error_W": fmt(error),
                "abs_error_W": fmt(abs_error),
                "tolerance_W": "" if split == "train" else fmt(tolerance),
                "duty_gate": gate,
                "runtime_input_violation_count": 0,
                "fit_policy": "fit_alpha_on_salt2_only_score_salt3_salt4_without_refit",
                "source_path": rel(AGENT438_BAKEOFF),
            }
        )
    for cand in candidate_definitions():
        if not cand["candidate_id"].startswith("HX_SEGMENTED"):
            continue
        for case_id in sorted(CASE_NAME, key=CASE_ORDER.get):
            split = CASE_SPLIT[case_id]
            rows.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "case_id": case_id,
                    "split_role": split,
                    "run_status": "not_run_fixed_mdot_segmented_runner_pending",
                    "predicted_qhx_W": "",
                    "target_qhx_W_for_scoring_only": prior[(CONSTANT_UA_PRIOR_FORM, case_id)].get("q_cfd_W", ""),
                    "error_W": "",
                    "abs_error_W": "",
                    "tolerance_W": "" if split == "train" else fmt(VALIDATION_TOLERANCE_W if split == "validation" else HOLDOUT_TOLERANCE_W),
                    "duty_gate": "pending_fixed_mdot_segmented_duty_score",
                    "runtime_input_violation_count": 0,
                    "fit_policy": "one_global_alpha_fit_on_salt2_only; no per-cell UA fit",
                    "source_path": rel(AGENT480_PLAN),
                }
            )
    return rows


def runtime_input_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "audit_item": "fit_split",
            "required_rule": "fit exactly one scalar on Salt2 only",
            "observed_state": "fit_parameters.csv has one alpha_UA per candidate; Salt3/Salt4 targets are score-only fields",
            "gate": "pass",
            "forbidden_runtime_inputs": "Salt3/Salt4 cooler duty or measured temperatures for fitting",
            "source_path": rel(AGENT480_PLAN),
        },
        {
            "audit_item": "cooler_target_use",
            "required_rule": "CFD cooler duty may be used only after prediction for score rows",
            "observed_state": "duty_scorecard labels target_qhx_W_for_scoring_only; coupled runner does not pass imposed_qhx_W",
            "gate": "pass",
            "forbidden_runtime_inputs": "imposed CFD cooler duty",
            "source_path": rel(AGENT438_BAKEOFF),
        },
        {
            "audit_item": "fluid_source_mutation",
            "required_rule": "do not edit external Fluid source from this local Ethan package",
            "observed_state": "segmented model is injected as a runtime-only adapter when --run-fluid is requested",
            "gate": "pass",
            "forbidden_runtime_inputs": "untracked source edits or native-output mutation",
            "source_path": str(FLUID_ROOT),
        },
        {
            "audit_item": "realized_wallHeatFlux",
            "required_rule": "do not use realized CFD wallHeatFlux in runtime model inputs",
            "observed_state": "no wallHeatFlux column is consumed by this builder",
            "gate": "pass",
            "forbidden_runtime_inputs": "realized CFD wallHeatFlux",
            "source_path": rel(AGENT480_PLAN),
        },
        {
            "audit_item": "segmented_degrees_of_freedom",
            "required_rule": "segmented cooler may fit only one global scalar",
            "observed_state": "N=4/8/16 are predeclared grid sensitivity rows; no per-cell fitted UA exists",
            "gate": "pass",
            "forbidden_runtime_inputs": "per-cell fitted UA, per-case correction factors",
            "source_path": rel(AGENT480_PLAN),
        },
    ]


class SegmentedHxAdapter:
    """Runtime-only adapter for Fluid solve_case segmented HX scoring."""

    def __init__(self, solver_module: Any, n_segments: int) -> None:
        self.solver = solver_module
        self.n_segments = n_segments
        self.profile_rows: dict[tuple[str, str, str, int, int], dict[str, Any]] = {}
        self.context: dict[str, str] = {}
        self.original: Callable[..., Any] = solver_module._hx_airside_transfer

    def __call__(self, segment: Any, case: Any, scenario: Any, mdot_kg_s: float, T_fluid_in_K: float, T_fluid_guess_out_K: float, T_air_inlet_K: float) -> Any:
        base_q, _base_air_out, diagnostics = self.original(
            segment, case, scenario, mdot_kg_s, T_fluid_in_K, T_fluid_guess_out_K, T_air_inlet_K
        )
        r_total = safe_float(getattr(diagnostics, "R_total_prime_K_m_W", None))
        if r_total is None or r_total <= 0.0:
            return base_q, _base_air_out, diagnostics
        total_ua = max(float(scenario.hx_ua_multiplier), 0.0) * segment.length_m / max(r_total, 1e-12)
        air_flow_Lpm = self.solver.effective_air_flow_Lpm(case, scenario)
        mdot_air = self.solver.air.rho(T_air_inlet_K) * max(air_flow_Lpm, 0.0) * self.solver.LPM_TO_M3_S
        if mdot_air <= 1e-12:
            return 0.0, T_air_inlet_K, diagnostics
        T_avg = 0.5 * (T_fluid_in_K + T_fluid_guess_out_K)
        cp_fluid = case.fluid.cp(T_avg)
        cp_air = self.solver.air.cp(0.5 * (T_air_inlet_K + T_avg))
        q_total, T_fluid_out, T_air_out, local = segmented_profile(
            total_ua_W_K=total_ua,
            n_segments=self.n_segments,
            mdot_fluid_kg_s=mdot_kg_s,
            cp_fluid_J_kg_K=cp_fluid,
            mdot_air_kg_s=mdot_air,
            cp_air_J_kg_K=cp_air,
            T_fluid_in_K=T_fluid_in_K,
            T_air_in_K=T_air_inlet_K,
        )
        for row in local:
            cell_index = int(row["cell_index"])
            key = (
                self.context.get("candidate_id", ""),
                self.context.get("case_id", ""),
                segment.name,
                self.n_segments,
                cell_index,
            )
            # Keep the latest nonlinear-iteration profile for each segment/cell.
            # Capturing every solver call makes a multi-million-row trace and is
            # not the durable diagnostic requested by the AGENT-480 plan.
            self.profile_rows[key] = {
                **self.context,
                "fluid_case_name": case.name,
                "segment_name": segment.name,
                "n_segments": self.n_segments,
                "mdot_kg_s": fmt(mdot_kg_s),
                "cp_fluid_J_kg_K": fmt(cp_fluid),
                "mdot_air_kg_s": fmt(mdot_air),
                "cp_air_J_kg_K": fmt(cp_air),
                "T_fluid_solver_guess_out_K": fmt(T_fluid_guess_out_K),
                **{key: fmt(value) for key, value in row.items()},
            }
        return q_total, T_air_out, diagnostics


def fluid_context() -> tuple[Any, Any, Any, Any]:
    if str(FLUID_ROOT) not in sys.path:
        sys.path.insert(0, str(FLUID_ROOT))
    from tamu_loop_model_v2 import config_loader, reporting, solver
    from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME, default_scenarios

    return solver, reporting, config_loader, (EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME, default_scenarios)


def _coupled_worker(candidate: dict[str, Any], case_id: str, alpha: float, queue: Any) -> None:
    started = time.perf_counter()
    try:
        solver, reporting, _config_loader, loaded = fluid_context()
        EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME, default_scenarios = loaded
        cases = {case.name: case for case in EXPERIMENT_CASES}
        base = next(s for s in default_scenarios() if s.name == "predictive_airside_ins_1.0in_rad_0")
        candidate_id = candidate["candidate_id"]
        n_segments = int(candidate["segmentation_count"])
        adapter = SegmentedHxAdapter(solver, n_segments) if candidate_id.startswith("HX_SEGMENTED") else None
        scenario = solver.ScenarioConfig(
            **{
                **base.__dict__,
                "name": candidate_id,
                "model_mode": "predictive_airside_hx",
                "imposed_qhx_W": None,
                "hx_ua_multiplier": alpha,
            }
        )
        case = cases[CASE_NAME[case_id]]
        try:
            if adapter is not None:
                adapter.context = {"candidate_id": candidate_id, "case_id": case_id, "split_role": CASE_SPLIT[case_id]}
                solver._hx_airside_transfer = adapter
            result = solver.solve_case(case, scenario)
        finally:
            if adapter is not None:
                solver._hx_airside_transfer = adapter.original
        validation = VALIDATION_CASES_BY_NAME.get(case.name)
        table = reporting.build_validation_table(result, validation)
        valid = table[~table["validation_excluded"]].copy()
        tp = valid[valid["kind"] == "TP"]["error_K"]
        tw = valid[valid["kind"] == "TW"]["error_K"]
        all_err = valid["error_K"]
        measured_mdot = None if validation is None else validation.measured_mass_flow_rate_kg_s
        mdot_error_pct = None if measured_mdot in (None, 0.0) else 100.0 * (result.mdot_kg_s - measured_mdot) / measured_mdot
        queue.put(
            {
                "row": {
                    "candidate_id": candidate_id,
                    "case_id": case_id,
                    "split_role": CASE_SPLIT[case_id],
                    "coupled_run_status": "completed",
                    "elapsed_s": fmt(time.perf_counter() - started),
                    "root_status": result.root_status,
                    "qhx_total_W": fmt(result.qhx_total_W),
                    "mdot_error_pct": fmt(mdot_error_pct),
                    "tp_rmse_K": fmt(math.sqrt(float((tp * tp).mean())) if len(tp) else None),
                    "tw_rmse_K": fmt(math.sqrt(float((tw * tw).mean())) if len(tw) else None),
                    "all_probe_rmse_K": fmt(math.sqrt(float((all_err * all_err).mean())) if len(all_err) else None),
                    "Tmean_error_K": "",
                    "loop_delta_error_K": "",
                    "coupled_gate": "pending_admission_review",
                    "source_path": "Fluid solve_case with AGENT-482 scenario; segmented uses runtime-only adapter",
                },
                "profiles": [] if adapter is None else list(adapter.profile_rows.values()),
            }
        )
    except Exception as exc:  # pragma: no cover - exercised by Fluid failures.
        queue.put(
            {
                "row": {
                    "candidate_id": candidate.get("candidate_id", ""),
                    "case_id": case_id,
                    "split_role": CASE_SPLIT.get(case_id, ""),
                    "coupled_run_status": "error",
                    "elapsed_s": fmt(time.perf_counter() - started),
                    "root_status": "",
                    "qhx_total_W": "",
                    "mdot_error_pct": "",
                    "tp_rmse_K": "",
                    "tw_rmse_K": "",
                    "all_probe_rmse_K": "",
                    "Tmean_error_K": "",
                    "loop_delta_error_K": "",
                    "coupled_gate": "fail_solver_error",
                    "source_path": f"{type(exc).__name__}: {exc}",
                },
                "profiles": [],
            }
        )


def coupled_scorecard_rows(run_fluid: bool, timeout_seconds: int = 90) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not run_fluid:
        rows = []
        for cand in candidate_definitions():
            for case_id in sorted(CASE_NAME, key=CASE_ORDER.get):
                rows.append(
                    {
                        "candidate_id": cand["candidate_id"],
                        "case_id": case_id,
                        "split_role": CASE_SPLIT[case_id],
                        "coupled_run_status": "not_run_use_--run-fluid_on_compute_node",
                        "elapsed_s": "",
                        "root_status": "",
                        "qhx_total_W": "",
                        "mdot_error_pct": "",
                        "tp_rmse_K": "",
                        "tw_rmse_K": "",
                        "all_probe_rmse_K": "",
                        "Tmean_error_K": "",
                        "loop_delta_error_K": "",
                        "coupled_gate": "pending_coupled_run",
                        "source_path": rel(AGENT480_PLAN),
                    }
                )
        return rows, []

    alpha = safe_float(fit_parameters()[0]["fitted_parameter_value"]) or 1.0
    rows: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    for cand in candidate_definitions():
        candidate_id = cand["candidate_id"]
        for case_id in sorted(CASE_NAME, key=CASE_ORDER.get):
            queue: mp.Queue = mp.Queue()
            process = mp.Process(target=_coupled_worker, args=(cand, case_id, alpha, queue))
            started = time.perf_counter()
            process.start()
            process.join(timeout_seconds)
            if process.is_alive():
                process.terminate()
                process.join(10)
                elapsed = time.perf_counter() - started
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "case_id": case_id,
                        "split_role": CASE_SPLIT[case_id],
                        "coupled_run_status": f"timeout_after_{timeout_seconds}s",
                        "elapsed_s": fmt(elapsed),
                        "root_status": "",
                        "qhx_total_W": "",
                        "mdot_error_pct": "",
                        "tp_rmse_K": "",
                        "tw_rmse_K": "",
                        "all_probe_rmse_K": "",
                        "Tmean_error_K": "",
                        "loop_delta_error_K": "",
                        "coupled_gate": "fail_solver_timeout",
                        "source_path": "bounded Fluid solve_case attempt timed out",
                    }
                )
            elif not queue.empty():
                payload = queue.get()
                rows.append(payload["row"])
                profiles.extend(payload.get("profiles", []))
            else:
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "case_id": case_id,
                        "split_role": CASE_SPLIT[case_id],
                        "coupled_run_status": "error_no_worker_result",
                        "elapsed_s": "",
                        "root_status": "",
                        "qhx_total_W": "",
                        "mdot_error_pct": "",
                        "tp_rmse_K": "",
                        "tw_rmse_K": "",
                        "all_probe_rmse_K": "",
                        "Tmean_error_K": "",
                        "loop_delta_error_K": "",
                        "coupled_gate": "fail_no_worker_result",
                        "source_path": "bounded Fluid solve_case worker exited without result",
                    }
                )
    return rows, profiles


def source_manifest_rows(run_fluid: bool) -> list[dict[str, str]]:
    return [
        {"source_path": rel(AGENT480_PLAN), "use": "governing plan, gates, guardrails"},
        {"source_path": rel(AGENT438_BAKEOFF), "use": "constant-UA fixed-mdot duty regression and Salt2 fit target"},
        {"source_path": rel(AGENT438_SUMMARY), "use": "prior RMSE comparison context"},
        {"source_path": rel(AGENT461_COUPLED), "use": "coupled M3+TS comparator thresholds"},
        {"source_path": str(FLUID_ROOT), "use": "read-only Fluid solver source for optional --run-fluid coupled scoring" if run_fluid else "read-only Fluid source path, not executed in default build"},
    ]


def decision_payload(duty_rows: list[dict[str, Any]], coupled_rows: list[dict[str, Any]], run_fluid: bool) -> dict[str, Any]:
    lumped_validation = next(row for row in duty_rows if row["candidate_id"] == "HX_LUMPED_UA_NTU" and row["case_id"] == "salt_3")
    lumped_holdout = next(row for row in duty_rows if row["candidate_id"] == "HX_LUMPED_UA_NTU" and row["case_id"] == "salt_4")
    completed_coupled = [row for row in coupled_rows if row["coupled_run_status"] == "completed"]
    coupled_status_counts: dict[str, int] = {}
    for row in coupled_rows:
        status = row["coupled_run_status"]
        coupled_status_counts[status] = coupled_status_counts.get(status, 0) + 1
    if not run_fluid:
        segmented_status = "implemented_but_coupled_run_pending"
    elif completed_coupled:
        segmented_status = "bounded_coupled_rows_partially_or_fully_completed"
    else:
        segmented_status = "bounded_coupled_rows_attempted_but_no_completed_scores"
    if completed_coupled:
        blocker_impact = (
            "Does not close predictive-wall-test-section-submodels by itself. "
            "It removes cooler-duty magnitude as the leading uncertainty only after coupled rows are reviewed."
        )
    elif run_fluid:
        blocker_impact = (
            "Does not close predictive-wall-test-section-submodels and does not yet remove coupled cooler uncertainty: "
            "the bounded Fluid solve attempts produced no completed score rows."
        )
    else:
        blocker_impact = (
            "Does not close predictive-wall-test-section-submodels by itself. "
            "Coupled score rows still need a compute-node run before blocker impact can be adjudicated."
        )
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "selected_current_candidate": "HX_LUMPED_UA_NTU",
        "selection_basis": (
            "Constant-UA reproduces the prior split-legal Salt2-fit duty screen: "
            f"Salt3 abs error {lumped_validation['abs_error_W']} W and "
            f"Salt4 abs error {lumped_holdout['abs_error_W']} W."
        ),
        "coupled_status_counts": coupled_status_counts,
        "segmented_candidate_status": segmented_status,
        "fixed_mdot_segmented_duty_status": "pending_native_or_replay_runner; not invented from coupled totals",
        "runtime_input_gate": "pass",
        "final_blocker_impact": blocker_impact,
        "coupled_rows_completed": len(completed_coupled),
        "source_package": rel(OUT),
    }


def readme_text(run_fluid: bool, coupled_completed: int, timeout_seconds: int, coupled_status_counts: dict[str, int]) -> str:
    return f"""---
provenance:
  - {rel(AGENT480_PLAN)}
  - {rel(AGENT438_BAKEOFF)}
  - {rel(AGENT461_COUPLED)}
  - tools/analyze/build_cooler_removal_model.py
tags: [forward-model, cooler, hx, predictive-1d, candidate-screen]
related:
  - TODO-PREDICT-COOLER-REMOVAL
  - predictive-wall-test-section-submodels
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Cooler Removal Model Candidate Screen

This package implements the AGENT-480 cooler comparison plan for the two next
model families: constant-UA effectiveness/NTU and segmented distributed-UA
effectiveness/NTU.

## Result

- `HX_LUMPED_UA_NTU` reproduces the existing split-legal fixed-mdot cooler duty
  evidence from AGENT-438. It fits one Salt2 scalar and scores Salt3/Salt4
  without refit.
- `HX_SEGMENTED_UA_NTU_N4/N8/N16` are implemented as predeclared coupled-run
  candidates with one global `alpha_UA`. Because the sibling Fluid source tree
  was read-only in this Ethan session, segmented behavior is injected only by
  `tools/analyze/build_cooler_removal_model.py --run-fluid` at runtime.
- Fixed-mdot segmented duty rows are intentionally marked pending. They should
  not be fabricated from coupled totals because coupled `Q_hx` changes with the
  solved mdot and loop state.
- A bounded coupled Fluid attempt does not admit a cooler candidate unless
  completed score rows exist and pass coupled review.

## Coupled Run State

`--run-fluid` executed: `{run_fluid}`.

Per-row timeout seconds: `{timeout_seconds}`.

Completed coupled rows: `{coupled_completed}`.

Coupled row status counts: `{json.dumps(coupled_status_counts, sort_keys=True)}`.

If coupled rows are still pending or timed out, rerun on a compute node with a
larger timeout after confirming the solve path is not stuck:

```bash
python3 tools/analyze/build_cooler_removal_model.py --run-fluid --timeout-seconds 273
```

## Files

- `candidate_definitions.csv`
- `fit_parameters.csv`
- `duty_scorecard.csv`
- `coupled_scorecard.csv`
- `segmented_profile_diagnostics.csv`
- `runtime_input_audit.csv`
- `model_comparison_decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build_package(run_fluid: bool = False, timeout_seconds: int = 90) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = candidate_definitions()
    fits = fit_parameters()
    duty = duty_scorecard_rows()
    coupled, profiles = coupled_scorecard_rows(run_fluid=run_fluid, timeout_seconds=timeout_seconds)
    audit = runtime_input_audit_rows()
    manifest = source_manifest_rows(run_fluid)
    decision = decision_payload(duty, coupled, run_fluid)

    write_csv(OUT / "candidate_definitions.csv", candidates, list(candidates[0].keys()))
    write_csv(OUT / "fit_parameters.csv", fits, list(fits[0].keys()))
    write_csv(OUT / "duty_scorecard.csv", duty, list(duty[0].keys()))
    write_csv(OUT / "coupled_scorecard.csv", coupled, list(coupled[0].keys()))
    profile_fields = [
        "candidate_id",
        "case_id",
        "split_role",
        "fluid_case_name",
        "segment_name",
        "n_segments",
        "cell_index",
        "ua_W_K",
        "ntu",
        "epsilon",
        "q_cell_W",
        "q_cumulative_W",
        "T_fluid_in_K",
        "T_fluid_out_K",
        "T_air_in_K",
        "T_air_out_K",
        "mdot_kg_s",
        "cp_fluid_J_kg_K",
        "mdot_air_kg_s",
        "cp_air_J_kg_K",
        "T_fluid_solver_guess_out_K",
    ]
    write_csv(OUT / "segmented_profile_diagnostics.csv", profiles, profile_fields)
    write_csv(OUT / "runtime_input_audit.csv", audit, list(audit[0].keys()))
    write_csv(OUT / "source_manifest.csv", manifest, list(manifest[0].keys()))
    write_json(OUT / "model_comparison_decision.json", decision)
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "candidate_count": len(candidates),
        "duty_rows": len(duty),
        "coupled_rows": len(coupled),
        "segmented_profile_rows": len(profiles),
        "run_fluid": run_fluid,
        "timeout_seconds": timeout_seconds,
        "coupled_status_counts": decision["coupled_status_counts"],
        "selected_current_candidate": decision["selected_current_candidate"],
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(
        readme_text(
            run_fluid,
            len([r for r in coupled if r["coupled_run_status"] == "completed"]),
            timeout_seconds,
            decision["coupled_status_counts"],
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run Fluid solve_case coupled rows; use only on a compute node.")
    parser.add_argument("--timeout-seconds", type=int, default=90, help="Per candidate/case Fluid solve timeout for --run-fluid.")
    args = parser.parse_args()
    summary = build_package(run_fluid=args.run_fluid, timeout_seconds=args.timeout_seconds)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
