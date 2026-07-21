#!/usr/bin/env python3
"""Build the terminal/source readiness package for upcomer exchange evidence.

This package is deliberately no-solver and no-harvest. It consolidates existing
repo artifacts plus a dated read-only scheduler observation into the next
decision surface: wait for terminal evidence, claim a terminal harvest row, or
design a sampler.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-UPCOMER-EXCHANGE-TERMINAL-SOURCE-READINESS-2026-07-21"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_terminal_source_readiness"
)
OUT = ROOT / OUT_REL

PREFLIGHT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_evidence_preflight"
)
PHASE4 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
RECIRC = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_matched_plane_recirc_field_harvest"
)
LOW_RECIRC = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_pressure_corner_low_recirc_anchor_harvest"
)
CORRECTED_Q = ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations"
AGENT_519_STATUS = ROOT / ".agent/status/2026-07-17_AGENT-519.md"
AGENT_576_STATUS = ROOT / ".agent/status/2026-07-21_AGENT-576.md"
FORWARD_MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"

PREFLIGHT_QUEUE = PREFLIGHT / "scoped_sampler_source_queue.csv"
PREFLIGHT_VARIABLES = PREFLIGHT / "exchange_variable_availability.csv"
PREFLIGHT_DECISION = PREFLIGHT / "phase4b_rescore_decision.csv"
PHASE4_UPCOMER = PHASE4 / "upcomer_exchange_cell_readiness.csv"
PHASE4_MISSING = PHASE4 / "missing_exchange_nu_evidence_queue.csv"
RECIRC_READINESS = RECIRC / "recirc_harvest_readiness.csv"
RECIRC_ROWS = RECIRC / "matched_plane_recirc_field_harvest.csv"
LOW_RECIRC_CANDIDATES = LOW_RECIRC / "candidate_terminal_preflight.csv"
LOW_RECIRC_SOURCE_CASES = LOW_RECIRC / "source_case_readiness.csv"
LOW_RECIRC_FIELDS = LOW_RECIRC / "endpoint_field_availability.csv"
CORRECTED_Q_SUBMISSIONS = CORRECTED_Q / "selected_submitted_jobs.csv"
CORRECTED_Q_PREFLIGHT = CORRECTED_Q / "logs/selected_runtime_preflight_3307441.csv"


READ_ONLY_SCHEDULER_OBSERVATION = [
    {
        "job_id": "3307441",
        "job_name": "saltq_sel36_cont",
        "observed_state": "RUNNING",
        "observed_elapsed": "03:04:04",
        "node_or_reason": "c318-020",
        "time_limit": "1-12:00:00",
        "role": "latest_corrected_Q_live_continuation",
        "readiness_effect": "live_running_wait_terminal",
    },
    {
        "job_id": "3299610",
        "job_name": "salt4_q3x_probe",
        "observed_state": "RUNNING",
        "observed_elapsed": "4-18:22:52",
        "node_or_reason": "c318-017",
        "time_limit": "5-00:00:00",
        "role": "high_heat_terminal_gated",
        "readiness_effect": "live_running_wait_terminal",
    },
    {
        "job_id": "3299620",
        "job_name": "salt4_heat_pack",
        "observed_state": "RUNNING",
        "observed_elapsed": "4-18:08:03",
        "node_or_reason": "c318-018",
        "time_limit": "5-00:00:00",
        "role": "high_heat_terminal_gated",
        "readiness_effect": "live_running_wait_terminal",
    },
    {
        "job_id": "3295438",
        "job_name": "saltq_s24_sel_harv",
        "observed_state": "COMPLETED",
        "observed_elapsed": "00:35:41",
        "node_or_reason": "completed_2026-07-18T17:39:54",
        "time_limit": "not_applicable",
        "role": "older_corrected_Q_dependent_harvester",
        "readiness_effect": "completed_but_superseded_by_3307441_latest_continuation",
    },
]

REQUIRED_QOIS = [
    "terminal_state",
    "V_recirc",
    "mdot_exchange",
    "tau_recirc",
    "T_main_T_recirc",
    "wall_core_delta_T",
    "pressure_residual_basis",
    "same_QOI_UQ",
    "RAF_RMF_SVF",
    "energy_residual",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def count_rows(path: Path) -> int:
    return len(read_csv(path))


def terminal_source_family_matrix() -> list[dict[str, Any]]:
    queue = {row["source_family"]: row for row in read_csv(PREFLIGHT_QUEUE)}
    low_recirc_sources = read_csv(LOW_RECIRC_SOURCE_CASES)
    corrected_q_cases = read_csv(CORRECTED_Q_PREFLIGHT)

    return [
        {
            "source_family": "latest_corrected_Q_live_continuation",
            "candidate_role": "future_holdout_exchange_source",
            "current_terminal_state": "live_running_job_3307441",
            "case_count": len(corrected_q_cases),
            "current_artifact_status": "runtime_preflight_passed_but_not_terminal",
            "current_exchange_qoi_status": "missing_until_terminal_harvest_or_sampler",
            "existing_diagnostic_rows": 0,
            "can_provide_raw_fields_after_terminal": "potentially_yes",
            "can_provide_full_exchange_qois_now": "false",
            "source_decision": "wait_terminal_no_duplicate_sampler",
            "next_action": "Monitor 3307441; after terminal success claim corrected-Q terminal harvest/admission row.",
            "source_paths": ";".join(
                [
                    rel(AGENT_576_STATUS),
                    rel(CORRECTED_Q_SUBMISSIONS),
                    rel(CORRECTED_Q_PREFLIGHT),
                    rel(PREFLIGHT_QUEUE),
                ]
            ),
        },
        {
            "source_family": "high_heat_terminal_gated",
            "candidate_role": "low_recirculation_pressure_anchor_not_exchange_source_yet",
            "current_terminal_state": "live_running_jobs_3299610_3299620",
            "case_count": len(low_recirc_sources),
            "current_artifact_status": "runtime_preflight_passed_but_not_terminal",
            "current_exchange_qoi_status": "missing_recirc_fields_and_endpoint_raw_fields",
            "existing_diagnostic_rows": 0,
            "can_provide_raw_fields_after_terminal": "potentially_pressure_endpoint_only",
            "can_provide_full_exchange_qois_now": "false",
            "source_decision": "wait_terminal_no_duplicate_sampler",
            "next_action": "Monitor high-heat jobs; after terminal success claim high-heat harvest/admission row.",
            "source_paths": ";".join(
                [
                    rel(LOW_RECIRC_CANDIDATES),
                    rel(LOW_RECIRC_SOURCE_CASES),
                    rel(LOW_RECIRC_FIELDS),
                    rel(PREFLIGHT_QUEUE),
                ]
            ),
        },
        {
            "source_family": "pm10_pressure_only_target",
            "candidate_role": "fallback_pressure_target",
            "current_terminal_state": "blocked_terminal_failure_review",
            "case_count": 12,
            "current_artifact_status": "not_exchange_sampler_source",
            "current_exchange_qoi_status": "pressure_only_no_exchange_state",
            "existing_diagnostic_rows": 0,
            "can_provide_raw_fields_after_terminal": "not_for_exchange_state",
            "can_provide_full_exchange_qois_now": "false",
            "source_decision": "do_not_use_for_exchange_sampler",
            "next_action": "Keep PM10 in pressure/source-envelope lane unless a later terminal admission row changes status.",
            "source_paths": queue["pm10_pressure_only_target"]["source_paths"],
        },
        {
            "source_family": "two_tap_endpoint_recirc",
            "candidate_role": "existing_pressure_endpoint_diagnostic",
            "current_terminal_state": "existing_artifact",
            "case_count": 3,
            "current_artifact_status": "diagnostic_only",
            "current_exchange_qoi_status": "RAF_RMF_SVF_present_but_no_exchange_state",
            "existing_diagnostic_rows": 3,
            "can_provide_raw_fields_after_terminal": "already_diagnostic_proxy_only",
            "can_provide_full_exchange_qois_now": "false",
            "source_decision": "diagnostic_only_no_new_sampler",
            "next_action": "Use for recirculation guard and pressure context only.",
            "source_paths": queue["two_tap_endpoint_recirc"]["source_paths"],
        },
        {
            "source_family": "upcomer_matched_plane_diagnostic_proxy",
            "candidate_role": "existing_upcomer_recirc_diagnostic",
            "current_terminal_state": "existing_artifact",
            "case_count": 36,
            "current_artifact_status": "diagnostic_only",
            "current_exchange_qoi_status": "RAF_RMF_SVF_and_energy_residual_diagnostic_no_exchange_state",
            "existing_diagnostic_rows": count_rows(PHASE4_UPCOMER),
            "can_provide_raw_fields_after_terminal": "already_proxy_only",
            "can_provide_full_exchange_qois_now": "false",
            "source_decision": "diagnostic_only_no_new_sampler",
            "next_action": "Use for thesis recirculation guard; do not fit exchange or ordinary Nu.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
    ]


def qoi_status_for(source_family: str, qoi: str) -> tuple[str, str, str]:
    if source_family == "upcomer_matched_plane_diagnostic_proxy":
        if qoi in {"RAF_RMF_SVF", "energy_residual"}:
            return ("available_existing_diagnostic", "false", "Use for guard/attribution only.")
        if qoi == "wall_core_delta_T":
            return ("proxy_partial_diagnostic_only", "false", "Require admitted wall/core extraction before scoring.")
        if qoi == "terminal_state":
            return ("existing_artifact_not_terminal_source", "false", "No terminal action needed for existing proxy.")
        return ("missing_exchange_state", "false", "Do not infer exchange state from proxy metrics.")
    if source_family == "two_tap_endpoint_recirc":
        if qoi == "RAF_RMF_SVF":
            return ("available_existing_diagnostic", "false", "Use only for recirculation guard.")
        if qoi == "pressure_residual_basis":
            return ("partial_endpoint_pressure_diagnostic", "false", "Not same-window upcomer exchange pressure basis.")
        if qoi == "terminal_state":
            return ("existing_artifact_not_terminal_source", "false", "No terminal action needed for existing endpoint diagnostic.")
        return ("missing_or_not_applicable", "false", "Not an upcomer exchange-state source.")
    if source_family == "latest_corrected_Q_live_continuation":
        if qoi == "terminal_state":
            return ("live_running_job_3307441", "false", "Wait for terminal success before harvest/admission.")
        if qoi in {"V_recirc", "mdot_exchange", "tau_recirc", "T_main_T_recirc", "wall_core_delta_T", "pressure_residual_basis"}:
            return ("terminal_gated_requires_harvest_or_sampler", "false", "Potential source after terminal success; not available now.")
        if qoi == "same_QOI_UQ":
            return ("missing_requires_same_qoi_plan", "false", "Pair exact exchange QOIs with mesh/time UQ in later row.")
        return ("not_currently_available", "false", "No current diagnostic coverage.")
    if source_family == "high_heat_terminal_gated":
        if qoi == "terminal_state":
            return ("live_running_jobs_3299610_3299620", "false", "Wait for terminal success before any high-heat harvest.")
        if qoi == "pressure_residual_basis":
            return ("terminal_gated_pressure_endpoint_potential", "false", "Potential pressure anchor after terminal endpoint harvest.")
        if qoi == "same_QOI_UQ":
            return ("missing_requires_same_qoi_plan", "false", "Same-QOI UQ absent.")
        return ("not_exchange_source_now", "false", "High heat is pressure/onset anchor first, not full exchange source.")
    if source_family == "pm10_pressure_only_target":
        if qoi == "pressure_residual_basis":
            return ("pressure_only_blocked_terminal_review", "false", "Keep in pressure lane, not exchange sampler.")
        return ("not_exchange_source", "false", "Do not use for exchange-state sampling.")
    return ("unknown", "false", "No decision.")


def required_exchange_qoi_coverage(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        for qoi in REQUIRED_QOIS:
            status, usable, action = qoi_status_for(source["source_family"], qoi)
            rows.append(
                {
                    "source_family": source["source_family"],
                    "required_qoi": qoi,
                    "current_coverage_status": status,
                    "usable_for_phase4b_now": usable,
                    "requires_terminal_success": str("terminal" in status or "live_running" in status).lower(),
                    "requires_sampler_or_harvest": str(
                        status
                        in {
                            "terminal_gated_requires_harvest_or_sampler",
                            "terminal_gated_pressure_endpoint_potential",
                        }
                    ).lower(),
                    "next_action": action,
                    "source_paths": source["source_paths"],
                }
            )
    return rows


def harvest_vs_sampler_decision() -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "terminal_harvest_ready_now",
            "status": "false",
            "evidence": "3307441, 3299610, and 3299620 are running in the read-only scheduler observation.",
            "next_action": "Wait for terminal monitor/admission handoff; do not harvest from this row.",
            "admission_change": "none",
            "source_paths": rel(AGENT_576_STATUS),
        },
        {
            "decision_id": "scoped_sampler_needed_now",
            "status": "false",
            "evidence": "Current live/terminal sources have not been exhausted; preflight forbids duplicate sampler launch.",
            "next_action": "Defer sampler design until terminal sources are terminal or formally unusable.",
            "admission_change": "none",
            "source_paths": rel(PREFLIGHT_DECISION),
        },
        {
            "decision_id": "phase4b_rescore_ready",
            "status": "false",
            "evidence": "No source family currently provides all required exchange QOIs and same-QOI UQ.",
            "next_action": "Keep Phase 4B blocked.",
            "admission_change": "none",
            "source_paths": rel(PREFLIGHT_VARIABLES),
        },
        {
            "decision_id": "phase5_trigger",
            "status": "not_triggered",
            "evidence": "No runtime-legal candidate or formal negative freeze was created by this row.",
            "next_action": "Keep final predictive scorecard trigger-gated.",
            "admission_change": "none",
            "source_paths": rel(PREFLIGHT_DECISION),
        },
        {
            "decision_id": "recommended_next_row",
            "status": "terminal_monitor_then_harvest_if_success",
            "evidence": "Live corrected-Q and high-heat jobs remain the only plausible near-term source-family unlocks.",
            "next_action": "After terminal success, claim a narrow terminal harvest/admission row; otherwise claim sampler design.",
            "admission_change": "none",
            "source_paths": ";".join([rel(AGENT_519_STATUS), rel(AGENT_576_STATUS)]),
        },
    ]


def duplicate_sampler_guard() -> list[dict[str, Any]]:
    return [
        {
            "guard_id": "corrected_q_duplicate_sampler",
            "source_family": "latest_corrected_Q_live_continuation",
            "forbidden_action": "submit_new_corrected_Q_exchange_sampler_or_harvester_now",
            "reason": "3307441 is running and supersedes the older completed 3295438 harvester for latest-state purposes.",
            "allowed_next_action": "read-only monitor until terminal; then separate terminal harvest/admission row",
            "source_paths": rel(CORRECTED_Q_SUBMISSIONS),
        },
        {
            "guard_id": "high_heat_duplicate_sampler",
            "source_family": "high_heat_terminal_gated",
            "forbidden_action": "submit_new_high_heat_sampler_now",
            "reason": "3299610 and 3299620 are still running near their 5-day limit.",
            "allowed_next_action": "read-only monitor until terminal; then separate high-heat harvest/admission row",
            "source_paths": rel(LOW_RECIRC_SOURCE_CASES),
        },
        {
            "guard_id": "diagnostic_proxy_refit_guard",
            "source_family": "upcomer_matched_plane_diagnostic_proxy",
            "forbidden_action": "fit_exchange_cell_or_reopen_ordinary_internal_Nu_from_proxy_metrics",
            "reason": "RAF/RMF/SVF and energy residual are diagnostic only; V_recirc, mdot_exchange, tau_recirc, and same-QOI UQ remain missing.",
            "allowed_next_action": "thesis recirculation guard and residual attribution writing",
            "source_paths": rel(PREFLIGHT_VARIABLES),
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        PREFLIGHT_QUEUE,
        PREFLIGHT_VARIABLES,
        PREFLIGHT_DECISION,
        PHASE4_UPCOMER,
        PHASE4_MISSING,
        RECIRC_READINESS,
        RECIRC_ROWS,
        LOW_RECIRC_CANDIDATES,
        LOW_RECIRC_SOURCE_CASES,
        LOW_RECIRC_FIELDS,
        CORRECTED_Q_SUBMISSIONS,
        CORRECTED_Q_PREFLIGHT,
        AGENT_519_STATUS,
        AGENT_576_STATUS,
        FORWARD_MAP,
    ]
    return [
        {
            "path": rel(path),
            "role": "read_only_input",
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path in paths
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK}
date: 2026-07-21
role: Forward-pred / Hydraulics / Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
tags: [forward-model, upcomer, recirculation, terminal-readiness, no-solver]
related:
  - {rel(PREFLIGHT)}
  - {rel(LOW_RECIRC)}
  - {rel(AGENT_576_STATUS)}
---
# Upcomer Exchange Terminal/Source Readiness

This package implements the next continuation-plan step after the upcomer
exchange preflight: decide whether existing terminal/live source families can
provide missing exchange-state QOIs before launching a sampler.

## Decision

- `terminal_harvest_ready_now`: `{str(summary["terminal_harvest_ready_now"]).lower()}`
- `scoped_sampler_needed_now`: `{str(summary["scoped_sampler_needed_now"]).lower()}`
- `phase4b_ready`: `{str(summary["phase4b_ready"]).lower()}`
- `phase5_trigger`: `{summary["phase5_trigger"]}`
- `recommended_next_action`: `{summary["recommended_next_action"]}`

Read-only scheduler observation found `3307441`, `3299610`, and `3299620`
still running. The older `3295438` harvester completed, but it is superseded
for latest corrected-Q purposes by the new `3307441` continuation.

## Outputs

- `terminal_source_family_matrix.csv`: source-family readiness and source role.
- `required_exchange_qoi_coverage.csv`: per-source coverage of required
  exchange QOIs.
- `harvest_vs_sampler_decision.csv`: go/no-go decisions for harvest, sampler,
  Phase 4B, and Phase 5.
- `duplicate_sampler_guard.csv`: explicit no-duplicate launch constraints.
- `read_only_scheduler_observation.csv`: dated scheduler facts consumed by this
  package.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repositories, or blocker register were mutated. No
solver, postprocessor, sampler, harvest, fitting, model selection, closure
admission, Phase 4B rescore, or Phase 5 trigger was run.
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    source_rows = terminal_source_family_matrix()
    qoi_rows = required_exchange_qoi_coverage(source_rows)
    decision_rows = harvest_vs_sampler_decision()
    guard_rows = duplicate_sampler_guard()
    manifest_rows = source_manifest()

    write_csv(OUT / "terminal_source_family_matrix.csv", source_rows)
    write_csv(OUT / "required_exchange_qoi_coverage.csv", qoi_rows)
    write_csv(OUT / "harvest_vs_sampler_decision.csv", decision_rows)
    write_csv(OUT / "duplicate_sampler_guard.csv", guard_rows)
    write_csv(OUT / "read_only_scheduler_observation.csv", READ_ONLY_SCHEDULER_OBSERVATION)
    write_csv(OUT / "source_manifest.csv", manifest_rows)

    summary = {
        "task": TASK,
        "built_at_utc": utc_now(),
        "source_family_rows": len(source_rows),
        "required_qoi_rows": len(qoi_rows),
        "duplicate_guard_rows": len(guard_rows),
        "live_running_jobs": 3,
        "completed_superseded_jobs": 1,
        "terminal_harvest_ready_now": False,
        "scoped_sampler_needed_now": False,
        "phase4b_ready": False,
        "phase5_trigger": "not_triggered",
        "recommended_next_action": "wait_terminal_monitor_then_claim_harvest_if_success",
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_mutation": False,
        "solver_or_postprocessing_or_sampler_or_harvest_launched": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "phase4b_rescore": False,
        "blocker_register_change": False,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
