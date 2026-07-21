#!/usr/bin/env python3
"""Monitor pressure/upcomer relaunch QOS retry readiness."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PRESSURE-UPCOMER-QOS-RETRY-MONITOR"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_qos_retry_monitor"
RELAUNCH = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_isolated_relaunch_submission_package"
HIGH_HEAT_STATUS = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_high_heat_status_refresh/updated_live_job_status.csv"
SBATCH = RELAUNCH / "scripts/submit_pressure_upcomer_isolated_relaunch.sbatch"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PRESSURE-UPCOMER-QOS-RETRY-MONITOR.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/pressure-upcomer-qos-retry-monitor.md"
IMPORT = ROOT / "imports/2026-07-20_pressure_upcomer_qos_retry_monitor.json"


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


def require_sources() -> None:
    required = [RELAUNCH / "summary.json", RELAUNCH / "submission_attempt.csv", RELAUNCH / "preflight_gate.csv", SBATCH]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing pressure/upcomer QOS retry sources: " + "; ".join(missing))


def parse_squeue(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("JOBID"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        rows.append(
            {
                "job_id": parts[0],
                "partition": parts[1],
                "job_name": parts[2],
                "user": parts[3],
                "state": parts[4],
                "elapsed": parts[5],
                "nodes": parts[6],
                "nodelist_or_reason": parts[7],
            }
        )
    return rows


def scheduler_rows() -> list[dict[str, str]]:
    try:
        completed = subprocess.run(
            ["squeue", "-u", "andresfierro231"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if completed.returncode == 0:
        parsed = parse_squeue(completed.stdout)
        if parsed:
            return parsed
    if HIGH_HEAT_STATUS.exists():
        rows = []
        for row in read_csv(HIGH_HEAT_STATUS):
            if row.get("scheduler_state", "").startswith("RUNNING"):
                rows.append(
                    {
                        "job_id": row["job_id"],
                        "partition": "fallback_high_heat",
                        "job_name": row.get("job_name", "") or row["job_id"],
                        "user": "andresfierro231",
                        "state": "R",
                        "elapsed": row.get("elapsed", ""),
                        "nodes": row.get("nodes", ""),
                        "nodelist_or_reason": row.get("nodelist_or_reason", "local_foam_log_fallback"),
                    }
                )
        return rows
    return []


def build_active_scheduler_pressure(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "job_id": row["job_id"],
            "partition": row["partition"],
            "job_name": row["job_name"],
            "state": row["state"],
            "elapsed": row["elapsed"],
            "nodes": row["nodes"],
            "nodelist_or_reason": row["nodelist_or_reason"],
            "contributes_to_submit_pressure": str(row["state"] in {"R", "PD", "RUNNING", "PENDING"}).lower(),
        }
        for row in rows
    ]


def build_qos_submit_window(active_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_count = sum(row["contributes_to_submit_pressure"] == "true" for row in active_rows)
    summary = read_json(RELAUNCH / "summary.json")
    ready = bool(summary.get("submit_allowed")) and summary.get("submit_status") == "submit_attempt_blocked_by_QOSMaxSubmitJobPerUserLimit"
    retry_now = ready and active_count == 0
    return [
        {
            "preflight_clean": str(bool(summary.get("submit_allowed"))).lower(),
            "prior_submit_status": summary.get("submit_status", ""),
            "active_submit_pressure_jobs": active_count,
            "retry_now": str(retry_now).lower(),
            "retry_reason": "capacity_window_clear" if retry_now else "wait_for_existing_jobs_or_submit_limit_to_clear",
            "submit_command": f"ssh login1 \"cd {ROOT} && sbatch {rel(SBATCH)}\"",
        }
    ]


def attempt_submit_if_allowed(qos_rows: list[dict[str, Any]], do_submit: bool = False) -> dict[str, Any]:
    if qos_rows[0]["retry_now"] != "true":
        return {
            "attempted": False,
            "return_code": "",
            "stdout": "",
            "stderr": "",
            "result": "not_attempted_retry_window_blocked",
            "job_id": "",
        }
    if not do_submit:
        return {
            "attempted": False,
            "return_code": "",
            "stdout": "",
            "stderr": "",
            "result": "not_attempted_dry_monitor_only",
            "job_id": "",
        }
    completed = subprocess.run(
        ["ssh", "login1", f"cd {ROOT} && sbatch {rel(SBATCH)}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    match = re.search(r"Submitted batch job (\d+)", completed.stdout)
    return {
        "attempted": True,
        "return_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "result": "submitted" if match else "submit_failed",
        "job_id": match.group(1) if match else "",
    }


def build_submission_retry_log(attempt: dict[str, Any]) -> list[dict[str, Any]]:
    prior = read_csv(RELAUNCH / "submission_attempt.csv")
    next_id = len(prior) + 1
    return [
        {
            "attempt_id": next_id,
            "attempt_context": "qos_retry_monitor",
            "command": f"ssh login1 \"cd {ROOT} && sbatch {rel(SBATCH)}\"",
            "return_code": attempt["return_code"],
            "submission_result": attempt["result"],
            "job_id": attempt["job_id"],
            "next_action": "monitor_array" if attempt["job_id"] else "retry_after_submit_limit_clears_or_existing_jobs_complete",
        }
    ]


def build_post_submit_monitor_queue(attempt: dict[str, Any]) -> list[dict[str, Any]]:
    job_id = attempt.get("job_id", "")
    cases = read_csv(RELAUNCH / "isolated_relaunch_case_matrix.csv")
    return [
        {
            "case_key": row["case_key"],
            "array_job_id": job_id,
            "array_index": row["array_index"],
            "monitor_status": "pending_submission" if not job_id else "submitted_monitor_terminal_state",
            "post_exit_action": "run isolated relaunch post-exit rollup after terminal state",
        }
        for row in cases
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (RELAUNCH / "summary.json", "isolated relaunch summary"),
        (RELAUNCH / "submission_attempt.csv", "prior submission attempts"),
        (RELAUNCH / "preflight_gate.csv", "preflight gate"),
        (SBATCH, "sbatch script"),
    ]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(f"# Pressure/Upcomer QOS Retry Monitor\n\nRetry now: {summary['retry_now']}. Submission result: {summary['submission_result']}.\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- retry_now: {summary['retry_now']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} pressure/upcomer QOS retry monitor\n\nRecorded scheduler pressure and retry state.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main(do_submit: bool = False) -> dict[str, Any]:
    require_sources()
    active = build_active_scheduler_pressure(scheduler_rows())
    qos = build_qos_submit_window(active)
    attempt = attempt_submit_if_allowed(qos, do_submit=do_submit)
    retry_log = build_submission_retry_log(attempt)
    monitor = build_post_submit_monitor_queue(attempt)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "active_submit_pressure_jobs": qos[0]["active_submit_pressure_jobs"],
        "retry_now": qos[0]["retry_now"] == "true",
        "submission_attempted": attempt["attempted"],
        "submission_result": attempt["result"],
        "submitted_job_id": attempt["job_id"],
        "fit_rows_released_now": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "active_scheduler_pressure.csv", active)
    write_csv(OUT / "qos_submit_window.csv", qos)
    write_csv(OUT / "submission_retry_log.csv", retry_log)
    write_csv(OUT / "post_submit_monitor_queue.csv", monitor)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(do_submit=False), indent=2, sort_keys=True))
