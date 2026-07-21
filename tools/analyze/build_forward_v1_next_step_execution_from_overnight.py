#!/usr/bin/env python3
"""Build the July 15 forward-v1 next-step execution package.

This is a read-only intake/triage builder. It consumes already-created
work products and Slurm accounting state, then writes a forward-v1 action
package. It does not mutate native CFD solver outputs, registry/admission
state, or the external Fluid repository.
"""

from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-15/"
    / "2026-07-15_forward_v1_next_step_execution_from_overnight"
)

AG391 = (
    ROOT
    / "work_products/2026-07/2026-07-14/"
    / "2026-07-14_mdot_temperature_overnight_compute_node_run"
)
AG392 = (
    ROOT
    / "work_products/2026-07/2026-07-14/"
    / "2026-07-14_thermal_overnight_compute_node_rescue"
)
AG373 = (
    ROOT
    / "work_products/2026-07/2026-07-14/"
    / "2026-07-14_hydraulic_overnight_dependent_chain"
)

SCHEDULER_JOB_IDS = [
    "3293924",
    "3295438",
    "3295989",
    "3295990",
    "3295991",
    "3295120",
    "3295901",
]

LEGACY_OUTPUT_FILES = [
    "cooler_hx_candidate_decision.csv",
    "current_state_triage.csv",
    "forward_v1_work_queue.csv",
    "overnight_result_decision_table.csv",
    "pressure_root_qa_summary.csv",
    "reference_state_diagnostic_summary.csv",
    "test_section_boundary_decision.csv",
]


@dataclass(frozen=True)
class PackageSummary:
    final_forward_v1_status: str
    admitted_evidence_now: list[str]
    diagnostic_evidence_now: list[str]
    still_blocked_by: list[str]
    top_next_actions: list[str]
    native_cfd_outputs_mutated: bool = False
    registry_or_admission_state_mutated: bool = False
    external_cfd_modeling_tools_mutated: bool = False
    scheduler_mutated: bool = False


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def collect_scheduler_rows() -> list[dict[str, str]]:
    command = [
        "sacct",
        "-j",
        ",".join(SCHEDULER_JOB_IDS),
        "--format=JobID,JobName%24,State,ExitCode,Elapsed,Submit,Start,End,NodeList",
        "-P",
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return [
            {
                "JobID": "sacct_unavailable",
                "JobName": "scheduler_snapshot",
                "State": "UNKNOWN",
                "ExitCode": str(result.returncode),
                "Elapsed": "",
                "Submit": "",
                "Start": "",
                "End": "",
                "NodeList": "",
                "interpretation": result.stderr.strip(),
            }
        ]
    reader = csv.DictReader(result.stdout.splitlines(), delimiter="|")
    return list(reader)


def interpret_job(job_id: str, state: str) -> tuple[str, str, str]:
    base = job_id.split(".", 1)[0]
    mapping = {
        "3293924": (
            "corrected_q_continuation",
            "Corrected-Q Salt2/Salt4 continuation is still running; downstream harvest cannot admit it yet.",
            "wait_for_terminal_then_harvest",
        ),
        "3295438": (
            "corrected_q_dependency_harvest",
            "Dependency-held corrected-Q harvester is not yet terminal.",
            "wait_for_3293924_then_harvest",
        ),
        "3295989": (
            "hydraulic_raw_two_tap_stage",
            "AGENT-373 hydraulic chain stage 1 is pending dependency.",
            "wait_for_dependency_chain",
        ),
        "3295990": (
            "hydraulic_f6_gate_stage",
            "AGENT-373 hydraulic chain stage 2 waits on stage 1 success.",
            "wait_for_stage_1_success",
        ),
        "3295991": (
            "hydraulic_reset_k_stage",
            "AGENT-373 hydraulic chain stage 3 waits on stage 2 success.",
            "wait_for_stage_2_success",
        ),
        "3295120": (
            "current_compute_node_allocation",
            "Compute node allocation is running; prior shell substeps include two failed probes and one completed probe.",
            "read_only_monitor_only",
        ),
        "3295901": (
            "pm5_matched_pressure_upcomer",
            "PM5 matched-pressure/upcomer job was cancelled before producing admissible evidence.",
            "diagnose_and_relaunch_under_cfd_pp_claim",
        ),
    }
    role, interpretation, next_action = mapping.get(
        base,
        (
            "unclassified_scheduler_row",
            "Scheduler row is included for completeness.",
            "inspect_if_relevant",
        ),
    )
    if "RUNNING" in state:
        next_action = "monitor_until_terminal"
    elif "PENDING" in state:
        next_action = "wait_on_dependency"
    elif "CANCELLED" in state:
        next_action = "diagnose_cancelled_job_before_relaunch"
    elif "COMPLETED" in state and base in {"3295120"}:
        next_action = "intake_completed_probe_if_relevant"
    return role, interpretation, next_action


def build_scheduler_table(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    table: list[dict[str, object]] = []
    for row in rows:
        role, interpretation, next_action = interpret_job(
            row.get("JobID", ""), row.get("State", "")
        )
        table.append(
            {
                "job_id": row.get("JobID", ""),
                "job_name": row.get("JobName", ""),
                "state": row.get("State", ""),
                "exit_code": row.get("ExitCode", ""),
                "elapsed": row.get("Elapsed", ""),
                "submit": row.get("Submit", ""),
                "start": row.get("Start", ""),
                "end": row.get("End", ""),
                "node_list": row.get("NodeList", ""),
                "forward_v1_role": role,
                "interpretation": row.get("interpretation", interpretation),
                "next_action": next_action,
            }
        )
    return table


def ag392_status() -> tuple[str, str, int, int]:
    summary = read_json(AG392 / "run_summary.json")
    stage_rows = read_csv(AG392 / "stage_status.csv")
    failed = sum(1 for row in stage_rows if row.get("exit_code") not in {"", "0"})
    if summary.get("overall_status"):
        return str(summary["overall_status"]), "run_summary.json", len(stage_rows), failed
    if stage_rows and failed == 0 and len(stage_rows) >= 8:
        return "complete_no_summary", "stage_status.csv", len(stage_rows), failed
    if stage_rows:
        return "partial_or_running", "stage_status.csv", len(stage_rows), failed
    return "missing", "no_stage_status", 0, 0


def build_output_tables(output_dir: Path, scheduler_rows: list[dict[str, str]] | None) -> PackageSummary:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in LEGACY_OUTPUT_FILES:
        stale_path = output_dir / filename
        if stale_path.exists():
            stale_path.unlink()

    ag391_summary = read_json(AG391 / "summary.json")
    ag392_summary = read_json(AG392 / "run_summary.json")
    hx_summary = read_json(AG392 / "results/predictive_hx_fit_setup_only_refresh/summary.json")
    external_bc_summary = read_json(
        AG392 / "results/external_bc_thermal_profile_parity_refresh/summary.json"
    )
    ag392_overall, ag392_source, ag392_stage_count, ag392_failed_count = ag392_status()

    if scheduler_rows is None:
        scheduler_rows = collect_scheduler_rows()
    scheduler_table = build_scheduler_table(scheduler_rows)
    write_csv(
        output_dir / "current_scheduler_state.csv",
        [
            "job_id",
            "job_name",
            "state",
            "exit_code",
            "elapsed",
            "submit",
            "start",
            "end",
            "node_list",
            "forward_v1_role",
            "interpretation",
            "next_action",
        ],
        scheduler_table,
    )

    overnight_rows = [
        {
            "artifact_id": "AGENT-391-mdot-temperature-run",
            "owner": "AGENT-391",
            "path": rel(AG391),
            "status": ag391_summary.get("status", "unknown"),
            "evidence_class": "diagnostic_compute_node_fluid_sweeps",
            "admissible_for_forward_v1": "no_direct_admission",
            "math_or_assumption_signal": "Pressure-root rows solve mdot where model pressure residual crosses zero; temperature rows compare sensor residuals under declared model modes.",
            "forward_v1_impact": "Provides quantitative candidate evidence for mdot/temperature/sensor policy, but does not close hydraulic or HX gates.",
            "next_action": "Use as input to sensor-map policy refresh and residual-attribution table.",
        },
        {
            "artifact_id": "setup-only-cooler-closure-bakeoff",
            "owner": "AGENT-391",
            "path": rel(AG391 / "setup_only_cooler_closure_bakeoff"),
            "status": "complete",
            "evidence_class": "candidate_setup_only_cooler_screen",
            "admissible_for_forward_v1": "candidate_only",
            "math_or_assumption_signal": "Salt2 scalar fit is scored on Salt3 validation and Salt4 holdout; imposed/realized CFD cooler rows are leakage diagnostics only.",
            "forward_v1_impact": "Useful for HX/cooler residual attribution; not a final HX closure admission.",
            "next_action": "Compare against AGENT-392 setup-only HX fit and decide one candidate lane for final scorecard input.",
        },
        {
            "artifact_id": "test-section-boundary-form-bakeoff",
            "owner": "AGENT-391",
            "path": rel(AG391 / "test_section_boundary_form_bakeoff"),
            "status": "complete",
            "evidence_class": "diagnostic_boundary_form_screen",
            "admissible_for_forward_v1": "no",
            "math_or_assumption_signal": "Forms compare zero, negative-source compatibility, prescribed loss, and half-loss test-section representations.",
            "forward_v1_impact": "Constrains where residuals appear; negative source remains a compatibility diagnostic, not a physical boundary proof.",
            "next_action": "Keep diagnostic-only unless BC-modeling admits a physical test-section boundary form.",
        },
        {
            "artifact_id": "AGENT-392-thermal-rescue",
            "owner": "AGENT-392",
            "path": rel(AG392),
            "status": ag392_overall,
            "evidence_class": "diagnostic_thermal_and_setup_contract_refresh",
            "admissible_for_forward_v1": "no_direct_admission",
            "math_or_assumption_signal": f"{ag392_stage_count} stages recorded, {ag392_failed_count} failed, status source {ag392_source}.",
            "forward_v1_impact": "Removes ambiguity about the overnight thermal runner and supplies setup/HX and boundary refresh artifacts.",
            "next_action": "Intake outputs by lane; do not call the refreshed rows final forward-v1 evidence.",
        },
        {
            "artifact_id": "setup-only-predictive-hx-fit-refresh",
            "owner": "AGENT-392",
            "path": rel(AG392 / "results/predictive_hx_fit_setup_only_refresh"),
            "status": hx_summary.get("strict_status", "unknown"),
            "evidence_class": "setup_only_hx_candidate_screen",
            "admissible_for_forward_v1": "candidate_pending_gate",
            "math_or_assumption_signal": "Primary split remains Salt2=train, Salt3=validation, Salt4=holdout; violations table is empty.",
            "forward_v1_impact": "Best immediate HX/cooler candidate lane, but final score still waits on hydraulic and cfd-pp admitted training data.",
            "next_action": "Use as ready input once final scorecard gates land.",
        },
        {
            "artifact_id": "external-bc-thermal-profile-parity-refresh",
            "owner": "AGENT-392",
            "path": rel(AG392 / "results/external_bc_thermal_profile_parity_refresh"),
            "status": "complete",
            "evidence_class": external_bc_summary.get(
                "evidence_class", "diagnostic_model_form_and_setup_contract"
            ),
            "admissible_for_forward_v1": "setup_contract_only",
            "math_or_assumption_signal": "CFD wallHeatFlux includes inseparable rcExternalTemperature radiation; realized heat-flux replay is diagnostic only.",
            "forward_v1_impact": "Clarifies external BC/radiation policy and segment heat-loss residuals without admitting predictive heat-loss rows.",
            "next_action": "Use setup metadata and residual attribution, not realized CFD heat flux, in forward-v1 package.",
        },
        {
            "artifact_id": "AGENT-373-hydraulic-dependent-chain",
            "owner": "AGENT-373",
            "path": rel(AG373),
            "status": "submitted_pending_dependencies",
            "evidence_class": "pending_hydraulic_gate",
            "admissible_for_forward_v1": "not_available_yet",
            "math_or_assumption_signal": "Raw two-tap, F6 gate, and reset-K diagnostic stages are queued behind active corrected-Q/current-node dependencies.",
            "forward_v1_impact": "Main blocker for final hydraulic residual attribution and final forward-v1 scorecard.",
            "next_action": "Monitor 3295989 -> 3295990 -> 3295991 and intake only terminal outputs.",
        },
    ]
    write_csv(
        output_dir / "overnight_output_intake.csv",
        [
            "artifact_id",
            "owner",
            "path",
            "status",
            "evidence_class",
            "admissible_for_forward_v1",
            "math_or_assumption_signal",
            "forward_v1_impact",
            "next_action",
        ],
        overnight_rows,
    )

    blocker_rows = [
        {
            "blocker_id": "hydraulic_h1_final_gate",
            "pre_triage_state": "blocked",
            "new_evidence": "AGENT-373 dependency chain exists but jobs remain pending.",
            "current_state": "blocked_waiting_on_terminal_hydraulic_chain",
            "why_not_unblocked": "No terminal raw two-tap/F6/reset-K output is available for admission.",
            "next_unblock_artifact": "AGENT-373 stage outputs and summaries after jobs 3295989-3295991 finish.",
            "owner_or_dependency": "AGENT-373 plus Slurm dependencies 3295120 and 3295438.",
        },
        {
            "blocker_id": "corrected_q_cfd_pp_admitted_training_data",
            "pre_triage_state": "blocked",
            "new_evidence": "3293924 is running and 3295438 is pending.",
            "current_state": "blocked_waiting_on_corrected_q_terminal_harvest",
            "why_not_unblocked": "Continuation and harvest are not terminal, so no new admitted cfd-pp training data exists.",
            "next_unblock_artifact": "Corrected-Q terminal harvest/admission package.",
            "owner_or_dependency": "cfd-pp/scheduler.",
        },
        {
            "blocker_id": "pm5_matched_pressure_upcomer",
            "pre_triage_state": "blocked",
            "new_evidence": "3295901 was cancelled before running.",
            "current_state": "blocked_cancelled_job_needs_diagnosis_or_relaunch",
            "why_not_unblocked": "Cancelled PM5 job produced no matched pressure/upcomer output.",
            "next_unblock_artifact": "Relaunched PM5 matched-plane extraction under a cfd-pp claim.",
            "owner_or_dependency": "cfd-pp/therm-reconstr.",
        },
        {
            "blocker_id": "predictive_hx_boundary_evidence",
            "pre_triage_state": "partially_blocked",
            "new_evidence": "AGENT-391 cooler screen and AGENT-392 setup-only HX fit landed with no HX-fit violations.",
            "current_state": "candidate_ready_not_final",
            "why_not_unblocked": "Candidates still need final gate intake alongside hydraulic and admitted cfd-pp data; imposed/realized cooler rows remain leakage diagnostics.",
            "next_unblock_artifact": "Final scorecard input manifest selecting the admissible HX/cooler lane.",
            "owner_or_dependency": "forward-pred/BC-modeling.",
        },
        {
            "blocker_id": "sensor_map_policy_refresh",
            "pre_triage_state": "open_action",
            "new_evidence": "AGENT-391 produced sensor error, reference-state, and boundary-form outputs.",
            "current_state": "unblocked_for_documentation_work",
            "why_not_unblocked": "Policy refresh artifact still needs to be written; evidence exists but is not yet packaged as a scorecard contract.",
            "next_unblock_artifact": "Sensor-map policy refresh table with train/validation/holdout row roles.",
            "owner_or_dependency": "forward-pred.",
        },
        {
            "blocker_id": "internal_nu_fit_gate",
            "pre_triage_state": "blocked",
            "new_evidence": "No admitted internal-Nu rows landed; upcomer diagnostic rows remain validation-only.",
            "current_state": "blocked",
            "why_not_unblocked": "Forward-v1 must not consume fitted internal Nu rows until cfd-pp onset candidates and matched-plane extraction reopen the gate.",
            "next_unblock_artifact": "Thermal admission internal-Nu final gate update after matched-plane/onset evidence.",
            "owner_or_dependency": "thermal-admission/cfd-pp/therm-reconstr.",
        },
        {
            "blocker_id": "closure_qoi_mesh_gci",
            "pre_triage_state": "blocked",
            "new_evidence": "No new GCI/mesh family terminal evidence landed in this intake.",
            "current_state": "blocked",
            "why_not_unblocked": "Final closure uncertainty still needs admitted mesh/GCI evidence.",
            "next_unblock_artifact": "Closure-QOI mesh/GCI admission package.",
            "owner_or_dependency": "cfd-pp/scientific-closure.",
        },
    ]
    write_csv(
        output_dir / "forward_v1_blocker_delta.csv",
        [
            "blocker_id",
            "pre_triage_state",
            "new_evidence",
            "current_state",
            "why_not_unblocked",
            "next_unblock_artifact",
            "owner_or_dependency",
        ],
        blocker_rows,
    )

    action_rows = [
        {
            "priority": "P0",
            "action_id": "freeze_final_forward_v1_no_go",
            "can_start_now": "yes",
            "collision_risk": "none",
            "inputs": "This AGENT-394 package.",
            "deliverable": "Declare final forward-v1 still blocked until hydraulic/cfd-pp gates land.",
            "success_condition": "No scorecard is labeled final forward-v1 from diagnostic or setup-only rows.",
        },
        {
            "priority": "P1",
            "action_id": "write_sensor_map_policy_refresh",
            "can_start_now": "yes",
            "collision_risk": "low",
            "inputs": "AGENT-391 sensor/error/reference-state/test-section outputs plus existing sensor map contract.",
            "deliverable": "Scorecard-ready sensor-map policy table.",
            "success_condition": "Train/validation/holdout roles are explicit and leakage rows are labeled diagnostic.",
        },
        {
            "priority": "P1",
            "action_id": "select_setup_only_hx_candidate_lane",
            "can_start_now": "yes",
            "collision_risk": "low",
            "inputs": "AGENT-391 cooler bakeoff and AGENT-392 predictive_hx_fit_setup_only_refresh.",
            "deliverable": "HX/cooler candidate lane decision table.",
            "success_condition": "One setup-only lane is ready for the next scorecard and imposed/realized CFD cooler lanes are excluded.",
        },
        {
            "priority": "P2",
            "action_id": "monitor_corrected_q_and_hydraulic_chain",
            "can_start_now": "yes_read_only",
            "collision_risk": "none",
            "inputs": "Slurm jobs 3293924, 3295438, 3295989, 3295990, 3295991.",
            "deliverable": "Terminal-state intake once jobs finish.",
            "success_condition": "No duplicate jobs; only terminal outputs are consumed.",
        },
        {
            "priority": "P2",
            "action_id": "diagnose_pm5_cancelled_job",
            "can_start_now": "yes_under_new_cfd_pp_claim",
            "collision_risk": "medium",
            "inputs": "AGENT-357 PM5 package and sacct row 3295901.",
            "deliverable": "Relaunch/no-relaunch decision for matched pressure/upcomer extraction.",
            "success_condition": "PM5 blocker has either terminal output or a documented scheduler reason for cancellation.",
        },
        {
            "priority": "P3",
            "action_id": "rerun_forward_scorecard_after_gates",
            "can_start_now": "no",
            "collision_risk": "none_until_gates_land",
            "inputs": "Admitted cfd-pp/hydraulics/BC-modeling gate outputs.",
            "deliverable": "Final forward-v1 scorecard with residual attribution.",
            "success_condition": "All score rows use admitted inputs and declared Salt2/Salt3/Salt4 split discipline.",
        },
    ]
    write_csv(
        output_dir / "today_action_queue.csv",
        [
            "priority",
            "action_id",
            "can_start_now",
            "collision_risk",
            "inputs",
            "deliverable",
            "success_condition",
        ],
        action_rows,
    )

    hx_action_rows = [
        {
            "lane_id": "AGENT-392_setup_only_hx_fit",
            "result_path": rel(AG392 / "results/predictive_hx_fit_setup_only_refresh"),
            "mathematical_form": "Compare model-predicted cooler duty and mean temperature errors by split; Salt2 train, Salt3 validation, Salt4 holdout.",
            "admission_status": "candidate_pending_final_gate",
            "do_not_use_if": "Any row consumes realized or imposed CFD cooler duty at predictive runtime.",
            "next_scorecard_use": "Preferred setup-only HX/cooler candidate when final gates reopen.",
        },
        {
            "lane_id": "AGENT-391_salt2_fit_constant_UA_bulk_drive",
            "result_path": rel(
                AG391
                / "setup_only_cooler_closure_bakeoff/cooler_rmse_summary_with_leakage_policy.csv"
            ),
            "mathematical_form": "Fit one scalar UA on Salt2; score Salt3 validation and Salt4 holdout without refitting.",
            "admission_status": "candidate_screen_not_final",
            "do_not_use_if": "It is mixed with imposed_cfd_cooler_upper_bound or salt2_fit_cooler_imposed_ratio leakage rows.",
            "next_scorecard_use": "Cross-check against AGENT-392 setup-only HX lane.",
        },
        {
            "lane_id": "AGENT-391_test_section_boundary_forms",
            "result_path": rel(AG391 / "test_section_boundary_form_bakeoff"),
            "mathematical_form": "Score temperature residuals under zero, negative-source compatibility, prescribed-loss, and half-loss test-section forms.",
            "admission_status": "diagnostic_only",
            "do_not_use_if": "A negative source is being treated as a physical boundary proof.",
            "next_scorecard_use": "Residual attribution only unless a physical BC-modeling gate admits a form.",
        },
        {
            "lane_id": "AGENT-392_external_bc_segment_equivalents",
            "result_path": rel(
                AG392
                / "results/external_bc_thermal_profile_parity_refresh/external_bc_segment_equivalents.csv"
            ),
            "mathematical_form": "Segment-level heat-loss equivalence with radiation included in CFD wallHeatFlux; no separate radiation add-on.",
            "admission_status": "setup_contract_and_diagnostic_residuals",
            "do_not_use_if": "Realized CFD wallHeatFlux is inserted as a predictive runtime heat-loss closure.",
            "next_scorecard_use": "Boundary metadata and residual attribution.",
        },
    ]
    write_csv(
        output_dir / "setup_only_hx_and_test_section_action_table.csv",
        [
            "lane_id",
            "result_path",
            "mathematical_form",
            "admission_status",
            "do_not_use_if",
            "next_scorecard_use",
        ],
        hx_action_rows,
    )

    source_rows = [
        {
            "source_id": "AGENT-391-summary",
            "path": rel(AG391 / "summary.json"),
            "exists": (AG391 / "summary.json").exists(),
            "use": "Completed mdot/temperature overnight queue counts and guardrails.",
        },
        {
            "source_id": "AGENT-391-cooler-bakeoff",
            "path": rel(AG391 / "setup_only_cooler_closure_bakeoff"),
            "exists": (AG391 / "setup_only_cooler_closure_bakeoff").exists(),
            "use": "Setup-only cooler candidate and leakage policy.",
        },
        {
            "source_id": "AGENT-391-test-section-bakeoff",
            "path": rel(AG391 / "test_section_boundary_form_bakeoff"),
            "exists": (AG391 / "test_section_boundary_form_bakeoff").exists(),
            "use": "Diagnostic test-section boundary-form screen.",
        },
        {
            "source_id": "AGENT-392-run-summary",
            "path": rel(AG392 / "run_summary.json"),
            "exists": (AG392 / "run_summary.json").exists(),
            "use": "Thermal rescue completion state.",
        },
        {
            "source_id": "AGENT-392-hx-fit",
            "path": rel(AG392 / "results/predictive_hx_fit_setup_only_refresh/summary.json"),
            "exists": (AG392 / "results/predictive_hx_fit_setup_only_refresh/summary.json").exists(),
            "use": "Setup-only predictive HX fit summary.",
        },
        {
            "source_id": "AGENT-392-external-bc",
            "path": rel(AG392 / "results/external_bc_thermal_profile_parity_refresh/summary.json"),
            "exists": (
                AG392 / "results/external_bc_thermal_profile_parity_refresh/summary.json"
            ).exists(),
            "use": "External BC/radiation diagnostic parity summary.",
        },
        {
            "source_id": "AGENT-373-readme",
            "path": rel(AG373 / "README.md"),
            "exists": (AG373 / "README.md").exists(),
            "use": "Hydraulic dependent-chain definition and expected outputs.",
        },
        {
            "source_id": "slurm-accounting",
            "path": "sacct -j " + ",".join(SCHEDULER_JOB_IDS),
            "exists": bool(scheduler_table),
            "use": "Live read-only scheduler/accounting snapshot.",
        },
    ]
    write_csv(output_dir / "source_manifest.csv", ["source_id", "path", "exists", "use"], source_rows)

    summary = PackageSummary(
        final_forward_v1_status="blocked_no_final_score",
        admitted_evidence_now=[
            "AGENT-392 run completion status as diagnostic/setup artifact",
            "AGENT-391 completed mdot/temperature evidence as diagnostic/candidate input",
        ],
        diagnostic_evidence_now=[
            "setup-only cooler/HX candidate screens",
            "test-section boundary-form bakeoff",
            "external BC/radiation parity residual attribution",
            "pressure-root solver quality audit",
        ],
        still_blocked_by=[
            "AGENT-373 hydraulic chain not terminal",
            "corrected-Q cfd-pp continuation/harvest not terminal",
            "PM5 matched-pressure/upcomer extraction cancelled",
            "sensor-map policy refresh not yet packaged",
            "internal-Nu and closure-QOI mesh/GCI gates remain closed",
        ],
        top_next_actions=[
            "write_sensor_map_policy_refresh",
            "select_setup_only_hx_candidate_lane",
            "monitor_corrected_q_and_hydraulic_chain",
            "diagnose_pm5_cancelled_job",
        ],
    )

    summary_json = {
        "task": "AGENT-394",
        "date": "2026-07-15",
        "package": rel(output_dir),
        "final_forward_v1_status": summary.final_forward_v1_status,
        "ag391_status": ag391_summary.get("status", "unknown"),
        "ag392_status": ag392_overall,
        "ag392_stage_count": ag392_stage_count,
        "ag392_failed_stage_count": ag392_failed_count,
        "hx_fit_strict_status": hx_summary.get("strict_status", "unknown"),
        "hx_fit_primary_split_id": hx_summary.get("primary_split_id", ""),
        "external_bc_predictive_hx_admitted": external_bc_summary.get("predictive_hx_admitted"),
        "external_bc_internal_nu_closure_admitted": external_bc_summary.get(
            "internal_nu_closure_admitted"
        ),
        "admitted_evidence_now": summary.admitted_evidence_now,
        "diagnostic_evidence_now": summary.diagnostic_evidence_now,
        "still_blocked_by": summary.still_blocked_by,
        "top_next_actions": summary.top_next_actions,
        "scheduler_rows": len(scheduler_table),
        "native_cfd_outputs_mutated": summary.native_cfd_outputs_mutated,
        "registry_or_admission_state_mutated": summary.registry_or_admission_state_mutated,
        "external_cfd_modeling_tools_mutated": summary.external_cfd_modeling_tools_mutated,
        "scheduler_mutated": summary.scheduler_mutated,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary_json, indent=2) + "\n")

    readme = f"""# Forward-v1 Next-Step Execution From Overnight

Date: 2026-07-15

Task: AGENT-394

## Result

Final forward-v1 remains **blocked**. The overnight work made useful progress:
AGENT-391 completed its mdot/temperature queue, and AGENT-392 completed all
eight thermal rescue stages with zero failed stages. These rows are evidence
for candidate selection, residual attribution, and setup contracts; they are
not a final forward-v1 score.

## What Is Admitted Now

- The completion/status facts for AGENT-391 and AGENT-392 are admitted as
  operational evidence.
- AGENT-392 external-boundary metadata may be used as setup-contract evidence.
- AGENT-391/392 cooler and HX rows may be consumed as candidate-screen inputs
  by the next gate package.

No final predictive HX, fitted internal Nu, realized wallHeatFlux, imposed
cooler duty, or diagnostic test-section negative-source row is admitted as a
predictive closure.

## What Is Pending

- AGENT-373 hydraulic dependent chain: jobs `3295989 -> 3295990 -> 3295991`.
- Corrected-Q continuation and harvest: `3293924` running, `3295438` pending at
  package generation time.
- PM5 matched pressure/upcomer extraction: `3295901` was cancelled and needs a
  cfd-pp/therm-reconstr relaunch decision.
- Sensor-map policy refresh: evidence exists from AGENT-391 but the policy
  table still needs to be written.

## Math, Assumptions, And Theory

- Train/validation/holdout discipline is unchanged: `salt_2=train`,
  `salt_3=validation`, and `salt_4=holdout`.
- Cooler/HX candidate screens are split-aware. A Salt2 scalar fit can only be
  scored on Salt3 and Salt4 without refitting; imposed or realized CFD cooler
  heat remains leakage/diagnostic evidence.
- Pressure-root diagnostics solve for mdot where the 1D pressure residual
  crosses zero. They explain hydraulic sensitivity but do not replace the
  pending H1/F6 hydraulic gate.
- External-boundary parity treats CFD wallHeatFlux as already including
  rcExternalTemperature radiation. Adding separate radiation would double-count
  heat loss; realized wallHeatFlux replay is diagnostic only.
- Test-section negative-source compatibility rows are mathematical residual
  probes, not physical boundary-condition proof.
- Internal Nu fitting remains closed. Upcomer diagnostic/effective Nu rows are
  validation-only until cfd-pp onset candidates and matched-plane extraction
  reopen the admission gate.

## Files

- `current_scheduler_state.csv`: read-only Slurm snapshot with interpretation.
- `overnight_output_intake.csv`: what landed and how each artifact can be used.
- `forward_v1_blocker_delta.csv`: blocker-by-blocker delta after overnight
  intake.
- `today_action_queue.csv`: collision-aware next work.
- `setup_only_hx_and_test_section_action_table.csv`: candidate/diagnostic lane
  table for cooler, HX, external BC, and test-section rows.
- `source_manifest.csv`: package inputs.
- `summary.json`: machine-readable package summary.

## Guardrails

This package did not mutate native CFD solver outputs, registry/admission
state, scheduler state, or external `../cfd-modeling-tools`.
"""
    (output_dir / "README.md").write_text(readme)

    math_doc = """# Math, Assumptions, Theory, And Results Register

## Split Discipline

The active split remains Salt2 train, Salt3 validation, Salt4 holdout. Any
candidate fitted on Salt2 must be scored on Salt3 and Salt4 without refitting.
Perturbation and diagnostic rows do not become independent training rows unless
a later admission package documents a new split.

## Cooler/HX Screens

The relevant quantity is the residual between modeled cooler heat removal or
temperature response and the CFD/reference target. Candidate rows are useful
only when runtime inputs are setup-only. Rows using imposed CFD cooler heat or
realized CFD cooler heat are diagnostics and leakage checks.

## Hydraulic Root Diagnostics

For pressure-root rows, mdot is varied until the model pressure residual is
near zero. This locates whether thermal/source assumptions imply a different
hydraulic operating point, but the result cannot replace raw two-tap/F6/reset-K
evidence from the pending hydraulic chain.

## Boundary And Radiation Policy

CFD wallHeatFlux under rcExternalTemperature includes convection and radiation
in one total flux. The forward model may use boundary metadata for setup, but
must not replay realized wallHeatFlux as predictive closure or add a second
radiation term on top of realized flux.

## Internal Nu Policy

No fitted internal Nu row is available for predictive scoring. Effective
upcomer Nu evidence remains diagnostic/validation-only until onset candidates
and matched-plane extraction reopen the fitting gate.

## Current Result

AGENT-391 and AGENT-392 landed useful candidate and diagnostic evidence, but
final forward-v1 remains blocked by non-terminal hydraulics/cfd-pp gates and a
cancelled PM5 matched-plane/upcomer job.
"""
    (output_dir / "math_assumptions_theory_and_results.md").write_text(math_doc)

    return summary


def build_package(
    output_dir: Path = OUT_DIR, scheduler_rows: list[dict[str, str]] | None = None
) -> PackageSummary:
    return build_output_tables(output_dir, scheduler_rows)


def main() -> None:
    build_package()


if __name__ == "__main__":
    main()
