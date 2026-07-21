#!/usr/bin/env python3
"""Consolidate current CFD admission blockers and next progress lanes."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-NEXT-PROGRESS-BLOCKER-ANALYSIS"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_next_progress_blocker_analysis"
M2_SCORE = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_score_release_decision_packet"
SALT1_SUPPORT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_salt1_support_closeout"
PRESSURE_QOS = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_qos_retry_monitor"
PRESSURE_ROLLUP = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_isolated_relaunch_post_exit_rollup"
HIGH_HEAT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_high_heat_terminal_watch_two_tap_update"
RUNBOOK = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_forward_blocker_unlock_runbook"
FRONTIER = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_max_analysis_advance_frontier"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-NEXT-PROGRESS-BLOCKER-ANALYSIS.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/next-progress-blocker-analysis.md"
IMPORT = ROOT / "imports/2026-07-20_next_progress_blocker_analysis.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def required_sources() -> list[Path]:
    return [
        M2_SCORE / "summary.json",
        M2_SCORE / "holdout_rows_still_blocked.csv",
        SALT1_SUPPORT / "summary.json",
        PRESSURE_QOS / "summary.json",
        PRESSURE_QOS / "qos_submit_window.csv",
        PRESSURE_ROLLUP / "summary.json",
        HIGH_HEAT / "summary.json",
        HIGH_HEAT / "two_tap_cand001_readiness_update.csv",
        RUNBOOK / "blocker_unlock_runbook.csv",
        FRONTIER / "blocker_frontier_ledger.csv",
    ]


def require_sources() -> None:
    missing = [rel(path) for path in required_sources() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing next-progress blocker analysis sources: " + "; ".join(missing))


def load_state() -> dict[str, Any]:
    return {
        "m2_score": read_json(M2_SCORE / "summary.json"),
        "salt1_support": read_json(SALT1_SUPPORT / "summary.json"),
        "pressure_qos": read_json(PRESSURE_QOS / "summary.json"),
        "pressure_rollup": read_json(PRESSURE_ROLLUP / "summary.json"),
        "high_heat": read_json(HIGH_HEAT / "summary.json"),
        "holdout_blocked": read_csv(M2_SCORE / "holdout_rows_still_blocked.csv"),
        "qos_window": read_csv(PRESSURE_QOS / "qos_submit_window.csv"),
        "two_tap": read_csv(HIGH_HEAT / "two_tap_cand001_readiness_update.csv"),
        "frontier": read_csv(FRONTIER / "blocker_frontier_ledger.csv"),
    }


def build_active_blocker_ledger(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "blocker_id": "salt1_m2_cooler_hx_support",
            "severity": "critical",
            "current_state": state["m2_score"]["decision"],
            "current_evidence": f"Salt1 support closeout: {state['salt1_support']['salt1_cooler_hx_projection_status']}",
            "blocked_downstream_work": "M2 holdout scoring; PM5; PM10; val_salt2; new-CFD score release",
            "release_condition": "row-specific supported Salt1 cooler/HX scorecard source or explicit approved three-row score-only exception",
            "forbidden_shortcut": "do not fabricate Salt1 cooler/HX support; do not score holdouts before M2 score release",
            "next_owner_action": "audit source candidates for real Salt1 cooler/HX support; otherwise keep blocked ledger closed_nonfabricated",
        },
        {
            "blocker_id": "pressure_upcomer_qos_submission",
            "severity": "high",
            "current_state": state["pressure_qos"]["submission_result"],
            "current_evidence": f"{state['pressure_qos']['active_submit_pressure_jobs']} active submit-pressure jobs; retry_now={state['pressure_qos']['retry_now']}",
            "blocked_downstream_work": "six-row isolated pressure/upcomer relaunch; hydraulic admission evidence",
            "release_condition": "QOS submit window clear and relaunch sbatch accepted",
            "forbidden_shortcut": "do not release pressure/upcomer fit rows from preflight-only evidence",
            "next_owner_action": "rerun QOS retry monitor and submit only when active submit pressure clears",
        },
        {
            "blocker_id": "pressure_upcomer_fit_release",
            "severity": "high",
            "current_state": "blocked_no_fit_release",
            "current_evidence": f"{state['pressure_rollup']['admission_grade_candidate_rows']} admission-grade rows; {state['pressure_rollup']['blocked_or_diagnostic_rows']} blocked/diagnostic rows",
            "blocked_downstream_work": "hydraulic model fitting and pressure/upcomer admission",
            "release_condition": "post-exit rollup reports terminal, finite, same-window admission-grade rows",
            "forbidden_shortcut": "do not admit diagnostic, missing, or reverse-flow-contaminated rows",
            "next_owner_action": "after relaunch exits, rerun post-exit parse rollup and fit release decision",
        },
        {
            "blocker_id": "high_heat_terminal_two_tap_source",
            "severity": "high",
            "current_state": state["high_heat"]["cand001_status"],
            "current_evidence": f"{state['high_heat']['running_jobs']} running jobs; {state['high_heat']['terminal_jobs']} terminal jobs",
            "blocked_downstream_work": "two-tap CAND-001 source release and same-QOI endpoint sampler launch",
            "release_condition": "jobs 3299610/3299620 terminal, harvestable, and low-reverse source review passes",
            "forbidden_shortcut": "no harvest from running jobs; no two-tap component-K launch from current recirculating rows",
            "next_owner_action": "continue terminal watch; run post-exit harvest immediately after terminal state",
        },
        {
            "blocker_id": "two_tap_component_k_uq_reverse_flow",
            "severity": "high",
            "current_state": "component_K_blocked_current_rows_diagnostic_only",
            "current_evidence": "current lower-right rows remain reverse-flow/component-isolation/same-QOI-UQ blocked",
            "blocked_downstream_work": "ordinary component-K admission and F6 two-tap fitting",
            "release_condition": "low-reverse source row plus consistent endpoint labels, pressure basis, straight-leg subtraction, and same-QOI time/mesh UQ",
            "forbidden_shortcut": "no K clipping, hidden multiplier, or apparent-cluster promotion to component_K",
            "next_owner_action": "keep apparent_cluster_loss diagnostic; wait for terminal low-reverse source before component-K repair",
        },
    ]


def build_progress_priority_matrix(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "lane": "m2_salt1_cooler_hx_resolution",
            "expected_unlock_value": "very_high",
            "dependency_risk": "medium",
            "scheduler_dependency": "none",
            "immediate_actionability": "high",
            "recommended_next_action": "complete source audit for row-specific Salt1 cooler/HX support or record final no-release decision",
            "why_ranked_here": "only lane that can unblock holdout scoring without waiting on running jobs",
        },
        {
            "rank": 2,
            "lane": "pressure_upcomer_qos_retry",
            "expected_unlock_value": "high",
            "dependency_risk": "high",
            "scheduler_dependency": "QOS submit pressure",
            "immediate_actionability": "medium",
            "recommended_next_action": "rerun QOS retry monitor; submit relaunch when active submit-pressure jobs are zero",
            "why_ranked_here": "preflight is clean, but evidence production is blocked outside analysis code",
        },
        {
            "rank": 3,
            "lane": "high_heat_post_exit_harvest",
            "expected_unlock_value": "high",
            "dependency_risk": "high",
            "scheduler_dependency": "running jobs 3299610/3299620",
            "immediate_actionability": "medium",
            "recommended_next_action": "keep terminal watch and prepare harvest classification for timeout or completion",
            "why_ranked_here": "could unlock low-reverse source family for two-tap, but terminal evidence has not landed",
        },
        {
            "rank": 4,
            "lane": "two_tap_component_k_repair",
            "expected_unlock_value": "medium",
            "dependency_risk": "high",
            "scheduler_dependency": "depends on high-heat or successor source",
            "immediate_actionability": "low",
            "recommended_next_action": "maintain diagnostic apparent-cluster path; do not launch component-K until low-reverse same-QOI source exists",
            "why_ranked_here": "current rows cannot be repaired into clean component-K evidence without new source data",
        },
    ]


def build_unlock_sequence(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "action_id": "m2_salt1_support_audit_closeout",
            "entry_condition": "M2 score release remains blocked_missing_salt1_cooler_hx",
            "action_class": "read-only evidence audit",
            "exact_next_action": "search existing admitted cooler/HX scorecard rows for Salt1-specific supported projection; if absent, preserve blocked decision",
            "expected_artifact": "updated M2 Salt1 support closeout or unchanged blocked score release packet",
            "stop_condition": "row-specific Salt1 support found or source audit proves none exists",
        },
        {
            "step": 2,
            "action_id": "pressure_upcomer_qos_retry",
            "entry_condition": "active_submit_pressure_jobs equals 0",
            "action_class": "scheduler retry",
            "exact_next_action": state["qos_window"][0].get("submit_command", ""),
            "expected_artifact": "submitted pressure/upcomer isolated relaunch array job id",
            "stop_condition": "sbatch accepted or QOSMaxSubmitJobPerUserLimit recurs",
        },
        {
            "step": 3,
            "action_id": "pressure_upcomer_post_exit_rollup",
            "entry_condition": "isolated relaunch array reaches terminal state",
            "action_class": "postprocessing/admission rollup",
            "exact_next_action": "rerun pressure_upcomer_isolated_relaunch_post_exit_rollup after parsed outputs exist",
            "expected_artifact": "pressure_upcomer_admission_rollup.csv and fit_release_decision.csv",
            "stop_condition": "fit rows released or all rows classified blocked/diagnostic",
        },
        {
            "step": 4,
            "action_id": "high_heat_terminal_harvest",
            "entry_condition": "jobs 3299610 and 3299620 are terminal",
            "action_class": "post-exit harvest",
            "exact_next_action": "harvest high-heat QOIs and classify steady-window, RAF/RMF, and low-reverse source readiness",
            "expected_artifact": "high-heat terminal harvest and two-tap source-family update",
            "stop_condition": "CAND-001 source released or successor CAND-002 required",
        },
        {
            "step": 5,
            "action_id": "two_tap_same_qoi_component_k_repair",
            "entry_condition": "low-reverse source exists and same-QOI endpoint sampler can run",
            "action_class": "admission repair",
            "exact_next_action": "build same-label/same-formula endpoint family and component isolation ledger without clipping K",
            "expected_artifact": "updated two_tap_corner_lower_right_admission_repair package",
            "stop_condition": "component_K admitted, or row remains apparent_cluster_only with documented UQ/reverse-flow failure",
        },
    ]


def build_holdout_fit_boundary_guard(state: dict[str, Any]) -> list[dict[str, Any]]:
    families = [
        ("Salt1-4 nominal", "fit/model_selection", "allowed_only_from_final_freeze_manifest"),
        ("PM5", "holdout_score", "blocked_until_M2_score_artifact_released"),
        ("PM10", "holdout_score", "blocked_until_M2_score_artifact_released"),
        ("val_salt2", "holdout_score", "blocked_until_M2_score_artifact_released"),
        ("new-CFD", "holdout_score", "blocked_until_M2_score_artifact_released"),
        ("pressure/upcomer", "diagnostic_or_future_fit", "blocked_until_admission_rollup_releases_fit_rows"),
        ("two-tap", "diagnostic_or_future_fit", "blocked_until_reverse_flow_component_isolation_same_qoi_uq_pass"),
    ]
    m2_released = state["m2_score"]["decision"] == "release_4row_score_ready"
    return [
        {
            "row_family": family,
            "permitted_use_now": use if family == "Salt1-4 nominal" else ("holdout_score" if m2_released and "blocked_until_M2" in guard else "not_for_fit_or_model_selection"),
            "guard_status": "pass" if family == "Salt1-4 nominal" else "blocked",
            "guard_reason": guard,
            "fit_rows_added_now": 0,
            "model_selection_rows_added_now": 0,
        }
        for family, use, guard in families
    ]


def build_scheduler_wait_queue(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "queue_id": "pressure_upcomer_isolated_relaunch",
            "scheduler_state": state["pressure_qos"]["submission_result"],
            "active_submit_pressure_jobs": state["pressure_qos"]["active_submit_pressure_jobs"],
            "retry_now": str(state["pressure_qos"]["retry_now"]).lower(),
            "next_action": "retry sbatch when active submit pressure clears",
            "downstream_artifact": "pressure/upcomer isolated relaunch post-exit rollup",
        },
        {
            "queue_id": "high_heat_jobs_3299610_3299620",
            "scheduler_state": state["high_heat"]["cand001_status"],
            "active_submit_pressure_jobs": "",
            "retry_now": "false",
            "next_action": "monitor until terminal then harvest",
            "downstream_artifact": "two-tap low-reverse source-family update",
        },
    ]


def build_analysis_decision_summary(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "next_progress_default",
            "best_next_move": "m2_salt1_cooler_hx_resolution",
            "second_move": "pressure_upcomer_qos_retry_after_submit_window_clears",
            "third_move": "high_heat_terminal_harvest_after_jobs_exit",
            "reason": "M2 has no scheduler dependency and blocks all holdout scoring; pressure/upcomer and two-tap evidence are waiting on scheduler/terminal conditions.",
            "fit_rows_added_now": 0,
            "holdout_rows_scored_now": state["m2_score"]["holdout_rows_scored_now"],
            "admitted_rows_now": 0,
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "source_role": "input_to_next_progress_blocker_analysis",
            "mutation": "read_only",
        }
        for path in required_sources()
    ]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Next Progress Blocker Analysis\n\n"
        f"Best next move: `{summary['best_next_move']}`.\n"
        f"Active blockers: {summary['active_blockers']}.\n"
        f"Fit rows added now: {summary['fit_rows_added_now']}.\n",
        encoding="utf-8",
    )


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        f"# {TASK}\n\n"
        "- status: complete\n"
        f"- best_next_move: {summary['best_next_move']}\n"
        f"- output: {rel(OUT)}\n",
        encoding="utf-8",
    )
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        f"# {DATE} next progress blocker analysis\n\n"
        "Consolidated current CFD admission blockers and next unlock sequence without fitting, scoring, or scheduler submission.\n",
        encoding="utf-8",
    )
    write_json(
        IMPORT,
        {
            "task": TASK,
            "date": DATE,
            "output_dir": rel(OUT),
            "native_solver_outputs_mutated": False,
            "summary_path": rel(OUT / "summary.json"),
        },
    )


def main() -> dict[str, Any]:
    require_sources()
    state = load_state()
    blockers = build_active_blocker_ledger(state)
    priorities = build_progress_priority_matrix(state)
    unlock = build_unlock_sequence(state)
    guard = build_holdout_fit_boundary_guard(state)
    scheduler = build_scheduler_wait_queue(state)
    decision = build_analysis_decision_summary(state)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "best_next_move": decision[0]["best_next_move"],
        "active_blockers": len(blockers),
        "holdout_rows_blocked": state["m2_score"]["holdout_rows_blocked"],
        "holdout_rows_scored_now": state["m2_score"]["holdout_rows_scored_now"],
        "fit_rows_added_now": 0,
        "model_selection_rows_added_now": 0,
        "pressure_upcomer_retry_now": state["pressure_qos"]["retry_now"],
        "high_heat_terminal_jobs": state["high_heat"]["terminal_jobs"],
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
        "scheduler_action": "none",
    }
    write_csv(OUT / "active_blocker_ledger.csv", blockers)
    write_csv(OUT / "progress_priority_matrix.csv", priorities)
    write_csv(OUT / "unlock_sequence.csv", unlock)
    write_csv(OUT / "holdout_fit_boundary_guard.csv", guard)
    write_csv(OUT / "scheduler_wait_queue.csv", scheduler)
    write_csv(OUT / "analysis_decision_summary.csv", decision)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
