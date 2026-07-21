#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION"
DATE = "2026-07-20"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification"

HARVEST = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission"
    / "selected_salt2_salt4_pm10q_after_3293924"
)
STATUS = HARVEST / "status_table/selected_corrected_q_status_table.csv"
MONITOR = HARVEST / "terminal_monitor_after_3293924/live_salt_sanity_monitor.csv"
PREFLIGHT = HARVEST / "corrected_salt_preflight_audit.csv"
HARVEST_MANIFEST = HARVEST / "harvest_job_manifest.csv"
POLICY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv"
PM5_ROLLUP = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification/pm5_matched_pressure_upcomer_evidence_rollup.csv"

SOLVER_OUT = ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.out"
SOLVER_ERR = ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.err"
HARVEST_OUT = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission"
    / "slurm-saltq_s24_sel_harv-3295438.out"
)
HARVEST_ERR = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission"
    / "slurm-saltq_s24_sel_harv-3295438.err"
)

JOBS = ("3293924", "3295438")
CASE_SPECS = [
    {
        "case_key": "salt2_lo10q",
        "source_key": "salt2_jin_lo10q_corrected",
        "fluid": "salt2",
        "q_ratio": "0.90",
        "aggregate_rel": "registry/extended_salt/corrected_salt_q_sensitivity/salt_test_2_jin_corrected_q_lo10q/salt2_jin_lo10q_corrected/aggregates",
    },
    {
        "case_key": "salt2_hi10q",
        "source_key": "salt2_jin_hi10q_corrected",
        "fluid": "salt2",
        "q_ratio": "1.10",
        "aggregate_rel": "registry/extended_salt/corrected_salt_q_sensitivity/salt_test_2_jin_corrected_q_hi10q/salt2_jin_hi10q_corrected/aggregates",
    },
    {
        "case_key": "salt4_lo10q",
        "source_key": "salt4_jin_lo10q_corrected",
        "fluid": "salt4",
        "q_ratio": "0.90",
        "aggregate_rel": "registry/extended_salt/corrected_salt_q_sensitivity/salt_test_4_jin_corrected_q_lo10q/salt4_jin_lo10q_corrected/aggregates",
    },
    {
        "case_key": "salt4_hi10q",
        "source_key": "salt4_jin_hi10q_corrected",
        "fluid": "salt4",
        "q_ratio": "1.10",
        "aggregate_rel": "registry/extended_salt/corrected_salt_q_sensitivity/salt_test_4_jin_corrected_q_hi10q/salt4_jin_hi10q_corrected/aggregates",
    },
]


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def index(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", str(value))
    if not match:
        return None
    return float(match.group(0))


def safe_float(value: str | None) -> float | None:
    if value in (None, "", "nan"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fallback_scheduler_rows() -> dict[str, dict[str, str]]:
    return {
        "3293924": {
            "job_id": "3293924",
            "job_name": "saltq_sel_cont",
            "scheduler_state": "TIMEOUT",
            "exit_code": "0:0",
            "elapsed": "5-00:00:06",
            "timelimit": "5-00:00:00",
            "start": "2026-07-13T17:03:56",
            "end": "2026-07-18T17:04:02",
            "evidence_source": f"{rel(SOLVER_OUT)};{rel(SOLVER_ERR)}",
        },
        "3295438": {
            "job_id": "3295438",
            "job_name": "saltq_s24_sel_harv",
            "scheduler_state": "COMPLETED",
            "exit_code": "0:0",
            "elapsed": "00:35:41",
            "timelimit": "02:00:00",
            "start": "2026-07-18T17:04:13",
            "end": "2026-07-18T17:39:54",
            "evidence_source": f"{rel(HARVEST_OUT)};{rel(HARVEST_ERR)};{rel(HARVEST_MANIFEST)}",
        },
    }


def scheduler_rows(no_scheduler: bool = False) -> list[dict[str, str]]:
    fallback = fallback_scheduler_rows()
    if no_scheduler:
        return [{**fallback[job_id], "scheduler_query": "disabled_local_evidence"} for job_id in JOBS]

    cmd = [
        "sacct",
        "-j",
        ",".join(JOBS),
        "--format=JobIDRaw,JobName%30,State,ExitCode,Elapsed,Timelimit,Start,End",
        "-P",
        "-n",
    ]
    try:
        completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=20, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return [{**fallback[job_id], "scheduler_query": "fallback_local_evidence"} for job_id in JOBS]

    rows: dict[str, dict[str, str]] = {}
    if completed.returncode == 0:
        for line in completed.stdout.splitlines():
            parts = line.split("|")
            if len(parts) < 8 or parts[0] not in JOBS:
                continue
            rows[parts[0]] = {
                "job_id": parts[0],
                "job_name": parts[1].strip(),
                "scheduler_state": parts[2].strip(),
                "exit_code": parts[3].strip(),
                "elapsed": parts[4].strip(),
                "timelimit": parts[5].strip(),
                "start": parts[6].strip(),
                "end": parts[7].strip(),
                "evidence_source": fallback[parts[0]]["evidence_source"],
                "scheduler_query": "sacct",
            }
    for job_id in JOBS:
        rows.setdefault(job_id, {**fallback[job_id], "scheduler_query": "fallback_local_evidence"})
    return [rows[job_id] for job_id in JOBS]


STRICT_FATAL_PATTERNS = (
    re.compile(r"\bFOAM FATAL ERROR\b"),
    re.compile(r"\bTraceback \(most recent call last\):"),
    re.compile(r"\bSegmentation fault\b", re.I),
    re.compile(r"\bFloating point exception\b", re.I),
)


def strict_log_markers(log_path: Path, tail_bytes: int = 8_000_000) -> dict[str, Any]:
    if not log_path.exists():
        return {
            "strict_log_path": rel(log_path),
            "strict_log_exists": "no",
            "strict_fatal_count": 1,
            "strict_fatal_examples": "missing log",
        }
    with log_path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - tail_bytes))
        text = handle.read().decode("utf-8", errors="replace")

    examples: list[str] = []
    for line in text.splitlines():
        if any(pattern.search(line) for pattern in STRICT_FATAL_PATTERNS):
            examples.append(line.strip())
            if len(examples) >= 3:
                break
    return {
        "strict_log_path": rel(log_path),
        "strict_log_exists": "yes",
        "strict_fatal_count": len(examples),
        "strict_fatal_examples": " | ".join(examples),
    }


def heat_review_row(spec: dict[str, str], monitor: dict[str, str]) -> dict[str, Any]:
    aggregate_dir = ROOT / spec["aggregate_rel"]
    grouped = aggregate_dir / "wall_heat_flux_grouped.csv"
    summary_path = aggregate_dir / "case_summary.csv"
    if not grouped.exists():
        return {
            "case_key": spec["case_key"],
            "source_key": spec["source_key"],
            "heat_ledger_status": "missing_registered_wall_heat_flux_grouped",
            "latest_time_s": "",
            "terminal_sample_count": 0,
            "latest_total_Q_postProc_w": "",
            "terminal_total_Q_first_w": "",
            "terminal_total_Q_latest_w": "",
            "terminal_total_Q_drift_w": "",
            "section_heater_net_q_w": "",
            "section_cooling_branch_net_q_w": "",
            "section_junctions_net_q_w": "",
            "source_path": rel(grouped),
        }

    rows = read_csv(grouped)
    if not rows:
        status = "empty_registered_wall_heat_flux_grouped"
        last: dict[str, str] = {}
        window: list[dict[str, str]] = []
    else:
        latest = max(safe_float(row.get("time_s")) or float("-inf") for row in rows)
        start = latest - 300.0
        window = [row for row in rows if (safe_float(row.get("time_s")) or 0.0) >= start]
        last = rows[-1]
        status = "registered_terminal_heat_ledger_available"
    first_q = safe_float(window[0].get("total_Q_postProc")) if window else None
    last_q = safe_float(last.get("total_Q_postProc")) if last else None
    drift = None if first_q is None or last_q is None else last_q - first_q
    return {
        "case_key": spec["case_key"],
        "source_key": spec["source_key"],
        "heat_ledger_status": status,
        "latest_time_s": last.get("time_s", ""),
        "terminal_window_start_s": window[0].get("time_s", "") if window else "",
        "terminal_window_end_s": last.get("time_s", ""),
        "terminal_sample_count": len(window),
        "latest_total_Q_postProc_w": last.get("total_Q_postProc", ""),
        "terminal_total_Q_first_w": "" if first_q is None else first_q,
        "terminal_total_Q_latest_w": "" if last_q is None else last_q,
        "terminal_total_Q_drift_w": "" if drift is None else drift,
        "section_heater_net_q_w": last.get("section_heater_net_q_w", ""),
        "section_cooling_branch_net_q_w": last.get("section_cooling_branch_net_q_w", ""),
        "section_upcomer_net_q_w": last.get("section_upcomer_net_q_w", ""),
        "section_test_section_net_q_w": last.get("section_test_section_net_q_w", ""),
        "section_junctions_net_q_w": last.get("section_junctions_net_q_w", ""),
        "monitor_late_window_drift_pct": monitor.get("late_window_drift_pct", ""),
        "monitor_late_window_amp_pct": monitor.get("late_window_amp_pct", ""),
        "summary_path": rel(summary_path),
        "source_path": rel(grouped),
    }


def terminal_drift_rows() -> list[dict[str, Any]]:
    status_by_case = index(read_csv(STATUS), "case_key")
    monitor_by_source = index(read_csv(MONITOR), "case_key")
    preflight_by_source = index(read_csv(PREFLIGHT), "case_key")
    rows: list[dict[str, Any]] = []
    for spec in CASE_SPECS:
        status = status_by_case[spec["case_key"]]
        monitor = monitor_by_source[spec["source_key"]]
        preflight = preflight_by_source[spec["source_key"]]
        log_markers = strict_log_markers(ROOT / monitor["log_path"])
        strict_log_status = "pass" if int(log_markers["strict_fatal_count"]) == 0 else "fail"
        drift_ok = monitor.get("plateau_like") == "True" and monitor.get("moved_enough") == "True" and monitor.get("mdot_direction_ok") == "True"
        rows.append(
            {
                "case_key": spec["case_key"],
                "source_key": spec["source_key"],
                "fluid": spec["fluid"],
                "q_ratio": spec["q_ratio"],
                "solver_job_id": "3293924",
                "harvest_job_id": "3295438",
                "gate_latest_solver_time": status["gate_latest_solver_time"],
                "latest_registered_timestep": status["latest_registered_timestep"],
                "latest_log_time": status["latest_log_time"],
                "post_restart_advance_so_far": status["post_restart_advance_so_far"],
                "restart_time_s": monitor["restart_time_s"],
                "target_end_time_s": monitor["target_end_time_s"],
                "latest_solver_time_s": monitor["latest_solver_time_s"],
                "advance_since_restart_s": monitor["advance_since_restart_s"],
                "advance_fraction_of_target": monitor["advance_fraction_of_target"],
                "mdot_latest_kg_s": monitor["mdot_latest_kg_s"],
                "nominal_mdot_kg_s": monitor["nominal_mdot_kg_s"],
                "mdot_moved_pct": monitor["mdot_moved_pct"],
                "expected_move_pct": monitor["expected_move_pct"],
                "moved_enough": monitor["moved_enough"],
                "mdot_direction_ok": monitor["mdot_direction_ok"],
                "late_window_drift_pct": monitor["late_window_drift_pct"],
                "late_window_amp_pct": monitor["late_window_amp_pct"],
                "plateau_like": monitor["plateau_like"],
                "preflight_overall_ok": preflight["overall_ok"],
                "preflight_processor_frame_error_count": preflight["processor_frame_error_count"],
                "legacy_monitor_fatal_error_count": monitor["fatal_error_count"],
                "legacy_monitor_scrutiny_reason": monitor["scrutiny_reason"],
                "strict_log_status": strict_log_status,
                **log_markers,
                "terminal_drift_status": "pass" if drift_ok and strict_log_status == "pass" and preflight["overall_ok"] == "True" else "review",
                "status_table_verdict": status["status"],
            }
        )
    return rows


def pressure_upcomer_rows() -> list[dict[str, Any]]:
    pm5_exists = PM5_ROLLUP.exists()
    rows: list[dict[str, Any]] = []
    for spec in CASE_SPECS:
        rows.append(
            {
                "case_key": spec["case_key"],
                "source_key": spec["source_key"],
                "matched_plane_metric_rows": 0,
                "pressure_upcomer_status": "diagnostic_blocked_pending_pm10_matched_plane_extraction",
                "fit_eligible": "no",
                "f6_fit_admitted_rows": 0,
                "upcomer_hybrid_fit_admitted_rows": 0,
                "blockers": "pm10_matched_plane_metrics_absent;coarse_only_no_mesh_gci;orientation_straight_loss_recirc_admission_pending",
                "reference_pm5_rollup_exists": "yes" if pm5_exists else "no",
                "reference_pm5_rollup": rel(PM5_ROLLUP),
            }
        )
    return rows


def policy_for_cases() -> dict[str, dict[str, str]]:
    return {row["case_key"]: row for row in read_csv(POLICY)}


def split_decision_rows() -> list[dict[str, Any]]:
    policy = policy_for_cases()
    rows: list[dict[str, Any]] = []
    for spec in CASE_SPECS:
        row = policy.get(spec["case_key"], {})
        rows.append(
            {
                "case_key": spec["case_key"],
                "source_key": spec["source_key"],
                "canonical_split_role": row.get("split_role", "future_holdout_pm10"),
                "classification_split_role": "future_holdout_pm10_score_only_after_final_freeze",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "score_allowed": "yes_after_terminal_admission_and_final_freeze",
                "final_training_envelope": "Salt1-4 nominal only",
                "decision": "holdout_testing_not_training",
                "guardrail": "PM10 rows may score a frozen model only; they must not change fit, candidate choice, or runtime inputs.",
                "policy_source": rel(POLICY),
            }
        )
    return rows


def terminal_admission_rows(
    drift_rows: list[dict[str, Any]],
    heat_rows: list[dict[str, Any]],
    pressure_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    heat_by_case = {row["case_key"]: row for row in heat_rows}
    pressure_by_case = {row["case_key"]: row for row in pressure_rows}
    split_by_case = {row["case_key"]: row for row in split_rows}
    rows: list[dict[str, Any]] = []
    for row in drift_rows:
        heat = heat_by_case[row["case_key"]]
        pressure = pressure_by_case[row["case_key"]]
        split = split_by_case[row["case_key"]]
        terminal_ok = (
            row["terminal_drift_status"] == "pass"
            and heat["heat_ledger_status"] == "registered_terminal_heat_ledger_available"
            and split["fit_allowed"] == "no"
        )
        rows.append(
            {
                "case_key": row["case_key"],
                "source_key": row["source_key"],
                "terminal_scheduler_context": "solver_timeout_harvest_completed",
                "terminal_drift_status": row["terminal_drift_status"],
                "heat_ledger_status": heat["heat_ledger_status"],
                "pressure_upcomer_status": pressure["pressure_upcomer_status"],
                "split_decision": split["decision"],
                "terminal_holdout_classification": "admitted_for_future_holdout_scoring_after_final_freeze" if terminal_ok else "blocked_pending_terminal_review",
                "fit_admission": "not_fit_admitted",
                "model_selection_admission": "not_model_selection_admitted",
                "runtime_input_admission": "not_runtime_input_admitted",
                "reason": (
                    "terminal drift/preflight/strict-log checks pass and registered heat ledger exists; "
                    "pressure/upcomer remains diagnostic; final split forbids fitting"
                    if terminal_ok
                    else "one or more terminal drift, heat ledger, or split checks require review"
                ),
            }
        )
    return rows


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        STATUS,
        MONITOR,
        PREFLIGHT,
        HARVEST_MANIFEST,
        SOLVER_OUT,
        SOLVER_ERR,
        HARVEST_OUT,
        HARVEST_ERR,
        POLICY,
        PM5_ROLLUP,
    ]
    for spec in CASE_SPECS:
        aggregate_dir = ROOT / spec["aggregate_rel"]
        paths.extend(
            [
                aggregate_dir / "case_summary.csv",
                aggregate_dir / "wall_heat_flux_grouped.csv",
                aggregate_dir / "postprocessing_case_long.csv",
                aggregate_dir / "postprocessing.sqlite",
            ]
        )
    return [{"source_path": rel(path), "exists": path.exists(), "role": "input"} for path in paths]


def write_readme(summary: dict[str, Any]) -> None:
    (OUT / "README.md").write_text(
        f"""---
provenance:
  - {rel(STATUS)}
  - {rel(MONITOR)}
  - {rel(POLICY)}
tags: [salt, pm10, terminal-admission, holdout, cfd-pp]
task: {TASK}
date: {DATE}
role: cfd-pp/Scheduler/Tester/Writer
type: work_product
status: complete
---
# Salt PM10 Terminal Admission Classification

This package classifies Salt2/Salt4 +/-10Q corrected-Q rows using the
`3293924` walltime stop and `3295438` completed harvest evidence. It performs
no model fitting and changes no registry or native CFD output.

## Summary

- PM10 rows classified: `{summary["case_count"]}`.
- Future holdout scoring rows: `{summary["future_holdout_scoring_rows"]}`.
- Fit-admitted rows: `{summary["fit_admitted_rows"]}`.
- Pressure/upcomer fit-admitted rows: `{summary["pressure_upcomer_fit_admitted_rows"]}`.
- Native output mutation: `{summary["native_output_mutation"]}`.

## Files

- `scheduler_evidence.csv`
- `pm10_terminal_drift.csv`
- `pm10_heat_ledger_review.csv`
- `pm10_pressure_upcomer_review.csv`
- `pm10_split_decisions.csv`
- `pm10_terminal_admission_rows.csv`
- `source_manifest.csv`
- `summary.json`
""",
        encoding="utf-8",
    )


def build(no_scheduler: bool = False) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    scheduler = scheduler_rows(no_scheduler=no_scheduler)
    drift = terminal_drift_rows()
    monitor_by_source = index(read_csv(MONITOR), "case_key")
    heat = [heat_review_row(spec, monitor_by_source[spec["source_key"]]) for spec in CASE_SPECS]
    pressure = pressure_upcomer_rows()
    split = split_decision_rows()
    admission = terminal_admission_rows(drift, heat, pressure, split)
    manifest = source_manifest()

    write_csv(OUT / "scheduler_evidence.csv", scheduler)
    write_csv(OUT / "pm10_terminal_drift.csv", drift)
    write_csv(OUT / "pm10_heat_ledger_review.csv", heat)
    write_csv(OUT / "pm10_pressure_upcomer_review.csv", pressure)
    write_csv(OUT / "pm10_split_decisions.csv", split)
    write_csv(OUT / "pm10_terminal_admission_rows.csv", admission)
    write_csv(OUT / "source_manifest.csv", manifest)

    admission_counts = Counter(row["terminal_holdout_classification"] for row in admission)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "case_count": len(CASE_SPECS),
        "solver_job_id": "3293924",
        "solver_job_state": next(row["scheduler_state"] for row in scheduler if row["job_id"] == "3293924"),
        "harvest_job_id": "3295438",
        "harvest_job_state": next(row["scheduler_state"] for row in scheduler if row["job_id"] == "3295438"),
        "future_holdout_scoring_rows": admission_counts.get("admitted_for_future_holdout_scoring_after_final_freeze", 0),
        "blocked_terminal_review_rows": admission_counts.get("blocked_pending_terminal_review", 0),
        "fit_admitted_rows": sum(row["fit_admission"] != "not_fit_admitted" for row in admission),
        "pressure_upcomer_fit_admitted_rows": sum(row["fit_eligible"] == "yes" for row in pressure),
        "model_fitting_performed": "no",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_source": "sacct_or_local_evidence" if not no_scheduler else "local_evidence_only",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-scheduler", action="store_true", help="Use local Slurm log evidence instead of querying sacct.")
    args = parser.parse_args()
    print(json.dumps(build(no_scheduler=args.no_scheduler), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
