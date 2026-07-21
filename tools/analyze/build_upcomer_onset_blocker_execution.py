#!/usr/bin/env python3
"""Build the upcomer onset blocker execution package.

This package operationalizes the current upcomer-only plan:

* keep running high-heat probes in monitor-only state;
* mark the completed PM10 harvest as extraction-ready but not QOI-admitted;
* prepare the Salt3 anchor launch queue without submitting it;
* preserve ordinary Nu/f_D/K guardrails for every current recirculating row.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "AGENT-UPCOMER-ONSET-EXECUTION"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_upcomer_onset_blocker_execution"

PM10_STATUS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission"
    / "selected_salt2_salt4_pm10q_after_3293924/status_table/selected_corrected_q_status_table.csv"
)
PM10_HARVEST_STDOUT = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission"
    / "slurm-saltq_s24_sel_harv-3295438.out"
)
HIGH_HEAT_QUEUE = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor"
    / "harvest_readiness_queue.csv"
)
HIGH_HEAT_LIVE_STATUS = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor"
    / "live_job_status.csv"
)
CURRENT_ONSET = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"
    / "upcomer_recirculation_onset_conditions.csv"
)
BLOCKED_METRICS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"
    / "blocked_missing_metrics.csv"
)
ADMISSION_CRITERIA = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract"
    / "upcomer_nu_admission_criteria.csv"
)
ANCHOR_MATRIX = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"
    / "proposed_cfd_run_matrix.csv"
)
REQUIRED_OUTPUTS = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"
    / "required_output_contract.csv"
)
MATCHED_PLANE_COMPUTE_PACKAGE = (
    ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction"
)
HIGH_HEAT_CAMPAIGN = ROOT / "jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe"

TRACKED_JOB_IDS = ["3299610", "3299620", "3293924", "3295438", "3295492"]

LEDGER_FIELDS = [
    "row_id",
    "case_key",
    "evidence_family",
    "job_id",
    "scheduler_state",
    "terminal_or_harvest_status",
    "representative_time_s",
    "Re",
    "Pr",
    "Ri",
    "Gr",
    "Ra",
    "Gz",
    "backflow_fraction",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "wall_bulk_deltaT_status",
    "wallHeatFlux_status",
    "same_window_consistency_status",
    "mesh_time_uncertainty_status",
    "classification",
    "allowed_use",
    "forbidden_use",
    "ordinary_Nu_fit_allowed",
    "ordinary_f_D_fit_allowed",
    "component_K_fit_allowed",
    "next_action",
    "source_paths",
]

SCHEDULER_FIELDS = [
    "job_id",
    "job_name",
    "scheduler_state",
    "elapsed",
    "exit_code",
    "start",
    "end",
    "source",
]

LAUNCH_FIELDS = [
    "rank",
    "case_key",
    "study_group",
    "salt_anchor",
    "parent_source_id",
    "target_heater_power_W",
    "target_heater_patch_Q_W",
    "q_ratio_vs_salt3_nominal",
    "insulation_mode",
    "passive_insulated_h_multiplier",
    "cooler_policy",
    "priority",
    "launch_status",
    "submit_gate",
    "preflight_checks",
    "required_outputs",
    "scientific_use",
    "no_fit_guardrail",
    "source_paths",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(path: Path | str) -> str:
    raw = Path(path)
    try:
        return str(raw.relative_to(ROOT))
    except ValueError:
        return str(path)


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def source_paths(*paths: Path | str) -> str:
    return ";".join(rel(path) for path in paths if str(path))


def scheduler_rows(no_scheduler: bool) -> list[dict[str, Any]]:
    if no_scheduler:
        return [
            {
                "job_id": job_id,
                "job_name": "",
                "scheduler_state": "not_checked",
                "elapsed": "",
                "exit_code": "",
                "start": "",
                "end": "",
                "source": "disabled_by_no_scheduler",
            }
            for job_id in TRACKED_JOB_IDS
        ]

    job_list = ",".join(TRACKED_JOB_IDS)
    rows: dict[str, dict[str, Any]] = {}

    try:
        running = subprocess.run(
            ["squeue", "-h", "-j", job_list, "-o", "%i|%j|%T|%M|%D|%R"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        running = subprocess.CompletedProcess(args=["squeue"], returncode=124, stdout="", stderr="timeout")
    if running.returncode == 0:
        for line in running.stdout.splitlines():
            parts = line.split("|")
            if len(parts) < 6:
                continue
            job_id = parts[0].strip()
            if job_id not in TRACKED_JOB_IDS:
                continue
            rows[job_id] = {
                "job_id": job_id,
                "job_name": parts[1].strip(),
                "scheduler_state": parts[2].strip(),
                "elapsed": parts[3].strip(),
                "exit_code": "",
                "start": "",
                "end": "",
                "source": "squeue",
            }

    try:
        completed = subprocess.run(
            [
                "sacct",
                "-P",
                "-n",
                "-j",
                job_list,
                "--format=JobIDRaw,JobName,State,Elapsed,ExitCode,Start,End",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        completed = subprocess.CompletedProcess(args=["sacct"], returncode=124, stdout="", stderr="timeout")
    if completed.returncode == 0:
        for line in completed.stdout.splitlines():
            parts = line.split("|")
            if len(parts) < 7:
                continue
            job_id = parts[0].strip()
            if job_id not in TRACKED_JOB_IDS:
                continue
            rows[job_id] = {
                "job_id": job_id,
                "job_name": parts[1].strip(),
                "scheduler_state": parts[2].strip(),
                "elapsed": parts[3].strip(),
                "exit_code": parts[4].strip(),
                "start": parts[5].strip(),
                "end": parts[6].strip(),
                "source": "sacct",
            }

    high_heat_fallback = {row.get("job_id", ""): row for row in read_csv(HIGH_HEAT_LIVE_STATUS)}
    fallback_rows = {
        "3299610": {
            "job_id": "3299610",
            "job_name": high_heat_fallback.get("3299610", {}).get("job_name", "salt4_q3x_probe"),
            "scheduler_state": high_heat_fallback.get("3299610", {}).get("scheduler_state", "RUNNING"),
            "elapsed": high_heat_fallback.get("3299610", {}).get("elapsed", ""),
            "exit_code": "",
            "start": "",
            "end": "",
            "source": f"fallback_after_squeue_rc={running.returncode};{rel(HIGH_HEAT_LIVE_STATUS)}",
        },
        "3299620": {
            "job_id": "3299620",
            "job_name": high_heat_fallback.get("3299620", {}).get("job_name", "salt4_heat_pack"),
            "scheduler_state": high_heat_fallback.get("3299620", {}).get("scheduler_state", "RUNNING"),
            "elapsed": high_heat_fallback.get("3299620", {}).get("elapsed", ""),
            "exit_code": "",
            "start": "",
            "end": "",
            "source": f"fallback_after_squeue_rc={running.returncode};{rel(HIGH_HEAT_LIVE_STATUS)}",
        },
        "3293924": {
            "job_id": "3293924",
            "job_name": "saltq_sel_cont",
            "scheduler_state": "terminal_parent_of_completed_harvest",
            "elapsed": "",
            "exit_code": "",
            "start": "",
            "end": "",
            "source": f"fallback_after_sacct_rc={completed.returncode};pm10_harvest_completed",
        },
        "3295438": {
            "job_id": "3295438",
            "job_name": "saltq_s24_sel_harv",
            "scheduler_state": "COMPLETED",
            "elapsed": "00:35:41",
            "exit_code": "0:0",
            "start": "2026-07-18T17:04:14-05:00",
            "end": "2026-07-18T17:39:54-05:00",
            "source": f"fallback_after_sacct_rc={completed.returncode};{rel(PM10_HARVEST_STDOUT)}",
        },
        "3295492": {
            "job_id": "3295492",
            "job_name": "upc_nominal",
            "scheduler_state": "COMPLETED",
            "elapsed": "",
            "exit_code": "0:0",
            "start": "",
            "end": "",
            "source": f"fallback_after_sacct_rc={completed.returncode};matched_plane_submission_log",
        },
    }

    for job_id in TRACKED_JOB_IDS:
        rows.setdefault(job_id, fallback_rows.get(job_id, {
            "job_id": job_id,
            "job_name": "",
            "scheduler_state": "not_found",
            "elapsed": "",
            "exit_code": "",
            "start": "",
            "end": "",
            "source": f"sacct_rc={completed.returncode};squeue_rc={running.returncode}",
        }))
    return [rows[job_id] for job_id in TRACKED_JOB_IDS]


def current_onset_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in read_csv(CURRENT_ONSET):
        rows.append(
            {
                "row_id": f"current_onset:{raw['label']}",
                "case_key": raw["label"],
                "evidence_family": "current_mainline_recirculation_diagnostic",
                "job_id": "",
                "scheduler_state": "terminal_historical",
                "terminal_or_harvest_status": "admitted_CFD_diagnostic_not_fit",
                "representative_time_s": raw.get("time_window", ""),
                "Re": raw.get("Re_upcomer", ""),
                "Pr": raw.get("Pr_median", ""),
                "Ri": raw.get("Ri_median", ""),
                "Gr": raw.get("Gr_proxy_from_Ra_Pr", ""),
                "Ra": raw.get("Ra_median", ""),
                "Gz": raw.get("Gz", ""),
                "backflow_fraction": raw.get("backflow_fraction", ""),
                "reverse_area_fraction": raw.get("reverse_flow_area_fraction", ""),
                "reverse_mass_fraction": raw.get("reverse_mass_fraction", ""),
                "secondary_velocity_fraction": raw.get("secondary_velocity_fraction", ""),
                "wall_bulk_deltaT_status": raw.get("wall_bulk_delta_T_status", ""),
                "wallHeatFlux_status": "missing",
                "same_window_consistency_status": "partial",
                "mesh_time_uncertainty_status": "missing",
                "classification": "recirculation_diagnostic",
                "allowed_use": "hybrid_onset_diagnostic_and_validity_boundary",
                "forbidden_use": "ordinary_Nu; ordinary_f_D; component_K",
                "ordinary_Nu_fit_allowed": "no",
                "ordinary_f_D_fit_allowed": "no",
                "component_K_fit_allowed": "no",
                "next_action": "keep as recirculation diagnostic; do not promote to ordinary coefficient",
                "source_paths": raw.get("source_paths", rel(CURRENT_ONSET)),
            }
        )
    return rows


def pm10_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in read_csv(PM10_STATUS):
        rows.append(
            {
                "row_id": f"pm10_harvest:{raw['case_key']}",
                "case_key": raw["case_key"],
                "evidence_family": "pm10_completed_harvest_needs_upcomer_qoi_admission",
                "job_id": "3295438",
                "scheduler_state": "COMPLETED",
                "terminal_or_harvest_status": raw.get("status", ""),
                "representative_time_s": raw.get("latest_registered_timestep", "").replace(" s", ""),
                "Re": "",
                "Pr": "",
                "Ri": "",
                "Gr": "",
                "Ra": "",
                "Gz": "",
                "backflow_fraction": "",
                "reverse_area_fraction": "",
                "reverse_mass_fraction": "",
                "secondary_velocity_fraction": "",
                "wall_bulk_deltaT_status": "missing_matched_plane_extraction",
                "wallHeatFlux_status": "missing_matched_plane_extraction",
                "same_window_consistency_status": "terminal_window_available_not_qoi_admitted",
                "mesh_time_uncertainty_status": "missing",
                "classification": "not_admissible_missing_matched_plane_fields",
                "allowed_use": "diagnostic_or_future_extraction_queue",
                "forbidden_use": "ordinary_Nu; ordinary_f_D; component_K",
                "ordinary_Nu_fit_allowed": "no",
                "ordinary_f_D_fit_allowed": "no",
                "component_K_fit_allowed": "no",
                "next_action": "run compute-node upcomer matched-plane extraction and classify with upcomer admission contract",
                "source_paths": source_paths(PM10_STATUS, PM10_HARVEST_STDOUT, raw.get("registry_source_root", "")),
            }
        )
    return rows


def high_heat_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in read_csv(HIGH_HEAT_QUEUE):
        state = raw.get("scheduler_state", "")
        readiness = raw.get("harvest_readiness", "")
        if state == "RUNNING":
            classification = "blocked_running_not_terminal"
            next_action = "monitor only; do not harvest native outputs until terminal"
        elif readiness == "terminal_ready_for_harvest":
            classification = "ready_for_terminal_harvest_not_qoi_admitted"
            next_action = "run terminal harvest then matched-plane admission"
        else:
            classification = "not_admissible_missing_terminal_harvest"
            next_action = raw.get("next_action", "refresh scheduler state")
        rows.append(
            {
                "row_id": f"high_heat:{raw['case_key']}",
                "case_key": raw["case_key"],
                "evidence_family": "high_heat_no_recirc_probe",
                "job_id": raw.get("job_id", ""),
                "scheduler_state": state,
                "terminal_or_harvest_status": readiness,
                "representative_time_s": raw.get("latest_log_time_s", ""),
                "Re": "",
                "Pr": "",
                "Ri": "",
                "Gr": "",
                "Ra": "",
                "Gz": "",
                "backflow_fraction": "",
                "reverse_area_fraction": "",
                "reverse_mass_fraction": "",
                "secondary_velocity_fraction": "",
                "wall_bulk_deltaT_status": "missing_until_terminal_harvest",
                "wallHeatFlux_status": "missing_until_terminal_harvest",
                "same_window_consistency_status": "missing_until_terminal_harvest",
                "mesh_time_uncertainty_status": "missing",
                "classification": classification,
                "allowed_use": "future_anchor_evidence_after_harvest",
                "forbidden_use": "ordinary_Nu; ordinary_f_D; component_K",
                "ordinary_Nu_fit_allowed": "no",
                "ordinary_f_D_fit_allowed": "no",
                "component_K_fit_allowed": "no",
                "next_action": next_action,
                "source_paths": source_paths(HIGH_HEAT_QUEUE, HIGH_HEAT_LIVE_STATUS, HIGH_HEAT_CAMPAIGN),
            }
        )
    return rows


def required_output_names() -> str:
    names = [row["required_output"] for row in read_csv(REQUIRED_OUTPUTS) if row.get("required_for_acceptance") == "yes"]
    return ";".join(names)


def launch_queue_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    required = required_output_names()
    for idx, raw in enumerate(read_csv(ANCHOR_MATRIX), start=1):
        priority = raw.get("priority", "")
        gate = (
            "submit only after PM10/high-heat admission shows no ordinary or transition anchor; "
            "high-heat jobs terminal or explicitly failed; preflight passes restart T, heater Q, insulation, cooler scaling, and source labels"
        )
        rows.append(
            {
                "rank": idx,
                "case_key": raw["case_key"],
                "study_group": raw.get("study_group", ""),
                "salt_anchor": raw.get("salt_anchor", ""),
                "parent_source_id": raw.get("parent_source_id", ""),
                "target_heater_power_W": raw.get("target_heater_power_W", ""),
                "target_heater_patch_Q_W": raw.get("target_heater_patch_Q_W", ""),
                "q_ratio_vs_salt3_nominal": raw.get("q_ratio_vs_salt3_nominal", ""),
                "insulation_mode": raw.get("insulation_mode", ""),
                "passive_insulated_h_multiplier": raw.get("passive_insulated_h_multiplier", ""),
                "cooler_policy": raw.get("cooler_policy", ""),
                "priority": priority,
                "launch_status": "prepared_not_submitted",
                "submit_gate": gate,
                "preflight_checks": (
                    "source case exists; processors64 restart time exists; patched 0/T root and processors64 restart T; "
                    "controlDict restart/endTime/purgeWrite audited; cooler/sink heat ledger refreshed"
                ),
                "required_outputs": required,
                "scientific_use": raw.get("scientific_use", ""),
                "no_fit_guardrail": "not ordinary upcomer Nu/f_D/K fit unless reverse fractions and all admission gates pass",
                "source_paths": source_paths(ANCHOR_MATRIX, REQUIRED_OUTPUTS),
            }
        )
    return rows


def blocker_rows() -> list[dict[str, Any]]:
    rows = []
    for raw in read_csv(BLOCKED_METRICS):
        rows.append(
            {
                "blocker": raw["blocked_metric"],
                "status": raw["current_status"],
                "resolution_signal": raw["next_extraction_request"],
                "why_it_matters": raw["why_it_matters"],
                "source_path": rel(BLOCKED_METRICS),
            }
        )
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""# Upcomer Onset Blocker Execution

Date: {DATE}

Task: {TASK}

## Decision

This package implements the upcomer-only blocker plan without submitting new
CFD. Current high-heat/no-recirculation probes stay monitor-only while running.
The completed PM10 harvest is ready for upcomer matched-plane extraction, but
it is not ordinary Nu/f_D/K evidence until the upcomer QOI admission ledger is
filled with same-window recirculation, thermal, pressure, and uncertainty
metrics.

## Current State

- Current recirculating diagnostic rows: `{summary['current_diagnostic_rows']}`.
- PM10 harvested rows queued for matched-plane extraction: `{summary['pm10_rows']}`.
- High-heat rows still blocked by running/terminal-harvest status: `{summary['high_heat_rows']}`.
- Prepared Salt3 anchor launch rows: `{summary['launch_queue_rows']}`.
- Ordinary upcomer Nu/f_D/K admitted rows now: `0`.

## Execution Order

1. Run the PM10 matched-plane compute extraction using the existing upcomer
   extractor package, then update `upcomer_anchor_admission_ledger.csv`.
2. Keep monitoring `3299610` and `3299620`; harvest only after terminal success.
3. If PM10 and high-heat rows remain recirculating or missing-transition,
   submit the prepared Salt3 sentinel anchors in `launch_preflight_queue.csv`.
4. Keep all recirculating rows section-effective/diagnostic only.

## Outputs

- `scheduler_status.csv`
- `upcomer_anchor_admission_ledger.csv`
- `launch_preflight_queue.csv`
- `blocker_resolution_queue.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build(no_scheduler: bool = False) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    sched = scheduler_rows(no_scheduler)
    ledger = current_onset_rows() + pm10_rows() + high_heat_rows()
    launch = launch_queue_rows()
    blockers = blocker_rows()

    write_csv(OUT / "scheduler_status.csv", sched, SCHEDULER_FIELDS)
    write_csv(OUT / "upcomer_anchor_admission_ledger.csv", ledger, LEDGER_FIELDS)
    write_csv(OUT / "launch_preflight_queue.csv", launch, LAUNCH_FIELDS)
    write_csv(
        OUT / "blocker_resolution_queue.csv",
        blockers,
        ["blocker", "status", "resolution_signal", "why_it_matters", "source_path"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"path": rel(PM10_STATUS), "role": "completed PM10 terminal harvest status"},
            {"path": rel(PM10_HARVEST_STDOUT), "role": "harvest-not-admission guardrail"},
            {"path": rel(HIGH_HEAT_QUEUE), "role": "high-heat runtime harvest queue"},
            {"path": rel(CURRENT_ONSET), "role": "current recirculation diagnostics"},
            {"path": rel(BLOCKED_METRICS), "role": "current upcomer blockers"},
            {"path": rel(ADMISSION_CRITERIA), "role": "upcomer admission criteria"},
            {"path": rel(ANCHOR_MATRIX), "role": "prepared Salt3 anchor matrix"},
            {"path": rel(MATCHED_PLANE_COMPUTE_PACKAGE), "role": "existing compute extraction package to reuse"},
        ],
        ["path", "role"],
    )

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at": now(),
        "status": "execution_package_ready",
        "scheduler_checked": not no_scheduler,
        "current_diagnostic_rows": len(current_onset_rows()),
        "pm10_rows": len(pm10_rows()),
        "high_heat_rows": len(high_heat_rows()),
        "launch_queue_rows": len(launch),
        "ordinary_upcomer_fit_rows_now": 0,
        "decision": "monitor_high_heat_prepare_launches_run_pm10_matched_plane_admission_next",
        "outputs": [
            "scheduler_status.csv",
            "upcomer_anchor_admission_ledger.csv",
            "launch_preflight_queue.csv",
            "blocker_resolution_queue.csv",
            "source_manifest.csv",
            "README.md",
            "summary.json",
        ],
    }
    write_readme(summary)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-scheduler", action="store_true", help="Do not call squeue/sacct; useful for tests.")
    args = parser.parse_args()
    print(json.dumps(build(no_scheduler=args.no_scheduler), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
