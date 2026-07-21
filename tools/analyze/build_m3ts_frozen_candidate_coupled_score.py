#!/usr/bin/env python3
"""Build AGENT-470 frozen M3+TS coupled candidate score package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import build_coupled_m3ts_test_section_scorecard as base


TASK = "AGENT-470"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score")
OUT = ROOT / OUT_REL

ADMISSION_COLUMNS = [
    "candidate_id",
    "validation_heat_gate",
    "holdout_heat_gate",
    "validation_coupled_gate",
    "holdout_coupled_gate",
    "runtime_gate",
    "admission_decision",
    "blocking_reasons",
]
DELTA_COLUMNS = [
    "candidate_id",
    "case_id",
    "split_role",
    "m3ts_mdot_abs_error_pct",
    "m3_mdot_abs_error_pct",
    "m3ts_all_probe_rmse_K",
    "m3_all_probe_rmse_K",
    "mdot_delta_vs_m3_pct",
    "all_probe_delta_vs_m3_K",
    "score_gate",
]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]
COUPLED_COLUMNS = [
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
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.12g}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: "" if row.get(column) is None else str(row.get(column)) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _solve_one_worker(candidate: dict[str, Any], case_id: str, queue: mp.Queue) -> None:
    try:
        if str(base.FLUID_ROOT) not in sys.path:
            sys.path.insert(0, str(base.FLUID_ROOT))
        from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, VALIDATION_CASES_BY_NAME, default_scenarios
        from tamu_loop_model_v2.reporting import build_validation_table
        from tamu_loop_model_v2.solver import ScenarioConfig, solve_case

        base_scenario = next(s for s in default_scenarios() if s.name == "predictive_airside_ins_1.0in_rad_0")
        cases = {case.name: case for case in EXPERIMENT_CASES}
        case_rows = base.setup_by_case()[case_id]
        maps = base.parent_boundary_maps(case_rows)
        scenario = ScenarioConfig(
            **{
                **base_scenario.__dict__,
                "name": candidate["candidate_id"],
                "outer_closure_mode": "external_boundary_table",
                "external_boundary_role_rows": base.role_rows_for_case(case_rows, candidate["test_section_coverage"]),
                **maps,
            }
        )
        case = cases[base.CASE_NAME[case_id]]
        result = solve_case(case, scenario)
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
                "source_path": "Fluid solve_case bounded worker using setup-only role-row scenario",
            }
        )
    except Exception as exc:  # pragma: no cover - exercised only on solver failures.
        queue.put(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "case_id": case_id,
                "split_role": "",
                "coupled_run_status": "error",
                "root_status": "",
                "mdot_error_pct": "",
                "tp_rmse_K": "",
                "tw_rmse_K": "",
                "all_probe_rmse_K": "",
                "Tmean_error_K": "",
                "loop_delta_error_K": "",
                "coupled_gate": "fail_solver_error",
                "source_path": f"{type(exc).__name__}: {exc}",
            }
        )


def bounded_coupled_rows(timeout_seconds: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in base.candidate_definitions():
        for case_id, case_rows in base.setup_by_case().items():
            split_role = next(row["validation_split_role"] for row in case_rows if row["role"] == "test_section")
            queue: mp.Queue = mp.Queue()
            process = mp.Process(target=_solve_one_worker, args=(candidate, case_id, queue))
            process.start()
            process.join(timeout_seconds)
            if process.is_alive():
                process.terminate()
                process.join(10)
                rows.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "case_id": case_id,
                        "split_role": split_role,
                        "coupled_run_status": f"timeout_after_{timeout_seconds}s",
                        "root_status": "",
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
                row = queue.get()
                if not row.get("split_role"):
                    row["split_role"] = split_role
                rows.append(row)
            else:
                rows.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "case_id": case_id,
                        "split_role": split_role,
                        "coupled_run_status": "error_no_worker_result",
                        "root_status": "",
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
    return rows


def m3_baselines() -> dict[str, dict[str, str]]:
    rows = read_csv(OUT / "m2_m3_comparators.csv")
    return {
        row["case_id"]: row
        for row in rows
        if row.get("mode_id") == "M3_setup_heater_cooler_no_test_section"
    }


def delta_rows() -> list[dict[str, Any]]:
    coupled = read_csv(OUT / "m3ts_coupled_scorecard.csv")
    baselines = m3_baselines()
    rows: list[dict[str, Any]] = []
    for row in coupled:
        if row.get("split_role") == "train":
            continue
        baseline = baselines.get(row.get("case_id", ""), {})
        m3ts_mdot = abs(safe_float(row.get("mdot_error_pct")) or float("nan"))
        m3_mdot = abs(safe_float(baseline.get("mdot_error_pct")) or float("nan"))
        m3ts_rmse = safe_float(row.get("all_probe_rmse_K"))
        m3_rmse = safe_float(baseline.get("all_probe_rmse_K"))
        mdot_delta = None if not math.isfinite(m3ts_mdot) or not math.isfinite(m3_mdot) else m3ts_mdot - m3_mdot
        rmse_delta = None if m3ts_rmse is None or m3_rmse is None else m3ts_rmse - m3_rmse
        completed = row.get("coupled_run_status") == "completed"
        score_pass = completed and mdot_delta is not None and rmse_delta is not None and mdot_delta <= 0.0 and rmse_delta <= 0.0
        rows.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "m3ts_mdot_abs_error_pct": fmt(m3ts_mdot),
                "m3_mdot_abs_error_pct": fmt(m3_mdot),
                "m3ts_all_probe_rmse_K": fmt(m3ts_rmse),
                "m3_all_probe_rmse_K": fmt(m3_rmse),
                "mdot_delta_vs_m3_pct": fmt(mdot_delta),
                "all_probe_delta_vs_m3_K": fmt(rmse_delta),
                "score_gate": "pass" if score_pass else "fail",
            }
        )
    return rows


def admission_rows(deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    heat = read_csv(OUT / "m3ts_heat_loss_gate.csv")
    runtime = read_csv(OUT / "runtime_input_audit.csv")
    candidates = sorted({row["candidate_id"] for row in heat})
    runtime_pass = all(row["gate"] == "pass" for row in runtime if row["audit_id"] != "R3_coupled_score")
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        heat_by_split = {row["split_role"]: row["heat_loss_gate"] for row in heat if row["candidate_id"] == candidate}
        delta_by_split = {row["split_role"]: row["score_gate"] for row in deltas if row["candidate_id"] == candidate}
        validation_heat = heat_by_split.get("validation", "missing")
        holdout_heat = heat_by_split.get("holdout", "missing")
        validation_coupled = delta_by_split.get("validation", "missing")
        holdout_coupled = delta_by_split.get("holdout", "missing")
        blockers = []
        if not runtime_pass:
            blockers.append("runtime_audit_failed")
        if validation_heat != "pass":
            blockers.append("validation_heat_loss_gate_failed")
        if holdout_heat != "pass":
            blockers.append("holdout_heat_loss_gate_failed")
        if validation_coupled != "pass":
            blockers.append("validation_coupled_score_not_improved")
        if holdout_coupled != "pass":
            blockers.append("holdout_coupled_score_not_improved")
        rows.append(
            {
                "candidate_id": candidate,
                "validation_heat_gate": validation_heat,
                "holdout_heat_gate": holdout_heat,
                "validation_coupled_gate": validation_coupled,
                "holdout_coupled_gate": holdout_coupled,
                "runtime_gate": "pass" if runtime_pass else "fail",
                "admission_decision": "admitted_predictive_m3ts_candidate" if not blockers else "not_admitted",
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def blocker_decision(admission: list[dict[str, Any]]) -> dict[str, Any]:
    admitted = [row for row in admission if row["admission_decision"] == "admitted_predictive_m3ts_candidate"]
    return {
        "task": TASK,
        "blocker_id": "predictive-wall-test-section-submodels",
        "decision": "resolve" if admitted else "keep_open",
        "why": "At least one frozen M3+TS candidate passed runtime, heat-loss, and coupled-score gates."
        if admitted
        else "No frozen M3+TS candidate passed runtime, held-out heat-loss, and coupled-score gates.",
        "admitted_candidates": [row["candidate_id"] for row in admitted],
        "evidence": rel(OUT / "m3ts_admission_review.csv"),
        "generated_at": utc_now(),
    }


def source_manifest() -> list[dict[str, Any]]:
    paths = {
        "agent461_builder": ROOT / "tools/analyze/build_coupled_m3ts_test_section_scorecard.py",
        "agent461_package": ROOT / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/README.md",
        "agent458_heat_loss": base.AG458_SUMMARY,
        "m2_m3_comparators": base.M2M3,
        "setup_rows": base.SETUP_ROWS,
    }
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": "input"} for key, path in paths.items()]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(base.SETUP_ROWS)}
  - {rel(base.AG458_SUMMARY)}
  - {rel(base.M2M3)}
tags: [forward-model, m3ts, test-section, coupled-score, runtime-legal]
related:
  - .agent/blockers.yml
  - operational_notes/maps/forward-predictive-model.md
task: {TASK}
date: {DATE}
role: Forward-pred/BC-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# M3+TS Frozen Candidate Coupled Score

Generated: `{summary["generated_at"]}`

## Decision

`predictive-wall-test-section-submodels`: `{summary["blocker_decision"]}`.

This package runs the frozen role-row M3+TS scenario score path and then applies
admission gates. Runtime inputs remain setup-only; realized CFD wallHeatFlux,
CFD mdot, imposed CFD cooler duty, and validation/holdout temperatures are not
runtime inputs.

## Results

- Coupled score rows: `{summary["coupled_rows"]}`.
- Admission candidates reviewed: `{summary["admission_rows"]}`.
- Admitted candidates: `{summary["admitted_candidates"]}`.

## Outputs

- `m3ts_coupled_scorecard.csv`
- `m3ts_admission_review.csv`
- `m2_m3_delta_summary.csv`
- `runtime_input_audit.csv`
- `blocker_decision.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build_package(run_fluid: bool = False, timeout_seconds: int = 90) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    original_out = base.OUT
    try:
        base.OUT = OUT
        if run_fluid:
            scenarios = base.scenario_contract_rows()
            heat = base.static_heat_loss_gate_rows()
            coupled = bounded_coupled_rows(timeout_seconds)
            runtime = base.runtime_audit_rows()
            runtime = [
                {**row, "gate": "pass", "evidence": f"bounded per-case Fluid solve attempts with {timeout_seconds}s timeout"}
                if row["audit_id"] == "R3_coupled_score"
                else row
                for row in runtime
            ]
            base.write_csv(
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
            )
            base.write_csv(
                OUT / "m3ts_heat_loss_gate.csv",
                heat,
                ["candidate_id", "split_role", "prior_static_screen", "abs_error_W", "abs_error_pct", "heat_loss_gate", "source_path"],
            )
            base.write_csv(OUT / "m3ts_coupled_scorecard.csv", coupled, COUPLED_COLUMNS)
            base.write_csv(
                OUT / "m2_m3_comparators.csv",
                base.comparator_rows(),
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
            )
            base.write_csv(OUT / "runtime_input_audit.csv", runtime, ["audit_id", "gate", "evidence", "forbidden_runtime_input"])
        else:
            base.build(run_fluid=False)
    finally:
        base.OUT = original_out
    deltas = delta_rows()
    admission = admission_rows(deltas)
    decision = blocker_decision(admission)
    write_csv(OUT / "m2_m3_delta_summary.csv", deltas, DELTA_COLUMNS)
    write_csv(OUT / "m3ts_admission_review.csv", admission, ADMISSION_COLUMNS)
    write_csv(
        OUT / "blocker_decision.csv",
        [decision],
        ["task", "blocker_id", "decision", "why", "admitted_candidates", "evidence", "generated_at"],
    )
    write_csv(OUT / "source_manifest.csv", source_manifest(), MANIFEST_COLUMNS)
    coupled_rows = read_csv(OUT / "m3ts_coupled_scorecard.csv")
    admitted = [row["candidate_id"] for row in admission if row["admission_decision"] == "admitted_predictive_m3ts_candidate"]
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "run_fluid": run_fluid,
        "timeout_seconds": timeout_seconds if run_fluid else "",
        "blocker_decision": decision["decision"],
        "coupled_rows": len(coupled_rows),
        "coupled_status_counts": dict(Counter(row["coupled_run_status"] for row in coupled_rows)),
        "admission_rows": len(admission),
        "admission_counts": dict(Counter(row["admission_decision"] for row in admission)),
        "admitted_candidates": len(admitted),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_mutated": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run actual Fluid solve_case coupled score; use on compute node.")
    parser.add_argument("--timeout-seconds", type=int, default=90, help="Per candidate/case Fluid solve timeout.")
    args = parser.parse_args()
    print(json.dumps(build_package(run_fluid=args.run_fluid, timeout_seconds=args.timeout_seconds), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
