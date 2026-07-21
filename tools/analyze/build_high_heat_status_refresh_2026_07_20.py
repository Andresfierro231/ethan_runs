#!/usr/bin/env python3
"""Refresh high-heat running job status while preserving diagnostic-only policy."""

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
TASK = "TODO-HIGH-HEAT-STATUS-REFRESH-2026-07-20"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_high_heat_status_refresh"
CAMPAIGN = ROOT / "jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-HIGH-HEAT-STATUS-REFRESH.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/high-heat-status-refresh.md"
IMPORT = ROOT / "imports/2026-07-20_high_heat_status_refresh.json"

JOB_IDS = ("3299610", "3299620")


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


def tail_text(path: Path, max_bytes: int = 200_000) -> str:
    if not path.exists():
        return ""
    return path.read_bytes()[-max_bytes:].decode("utf-8", errors="replace")


def require_sources() -> None:
    required = [CAMPAIGN / "high_heat_probe_manifest.csv", CAMPAIGN / "high_heat_bracket_pack_manifest.csv"]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing high-heat refresh sources: " + "; ".join(missing))


def scheduler_rows() -> dict[str, dict[str, str]]:
    try:
        completed = subprocess.run(
            f"squeue -h -j {','.join(JOB_IDS)} -o '%i|%j|%T|%M|%D|%R'",
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
            shell=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        completed = None
    rows: dict[str, dict[str, str]] = {}
    if completed and completed.returncode == 0:
        for line in completed.stdout.splitlines():
            parts = line.split("|")
            if len(parts) == 6:
                job_id, name, state, elapsed, nodes, reason = [part.strip() for part in parts]
                rows[job_id] = {"job_id": job_id, "job_name": name, "scheduler_state": state, "elapsed": elapsed, "nodes": nodes, "nodelist_or_reason": reason, "scheduler_source": "squeue"}
    for job_id in JOB_IDS:
        rows.setdefault(job_id, {"job_id": job_id, "job_name": "", "scheduler_state": "not_in_squeue", "elapsed": "", "nodes": "", "nodelist_or_reason": "", "scheduler_source": "squeue"})
    return rows


def load_cases() -> list[dict[str, str]]:
    rows = []
    for path, job_id, job_name in [
        (CAMPAIGN / "high_heat_probe_manifest.csv", "3299610", "salt4_q3x_probe"),
        (CAMPAIGN / "high_heat_bracket_pack_manifest.csv", "3299620", "salt4_heat_pack"),
    ]:
        for row in read_csv(path):
            row = dict(row)
            row["job_id"] = job_id
            row["job_name"] = job_name
            row["manifest_source"] = rel(path)
            rows.append(row)
    return rows


def foam_log_for(row: dict[str, str]) -> Path:
    suffix = "log.foamRun_high_heat_probe" if row["job_id"] == "3299610" else "log.foamRun_high_heat_bracket"
    return Path(row["case_dir"]) / "logs" / suffix


def latest_time(path: Path) -> str:
    text = tail_text(path)
    matches = re.findall(r"Time = ([0-9.]+)s", text)
    return matches[-1] if matches else ""


def build_live_job_status(sched: dict[str, dict[str, str]], cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for job_id in JOB_IDS:
        job_cases = [row for row in cases if row["job_id"] == job_id]
        latest_times = [latest_time(foam_log_for(row)) for row in job_cases]
        latest_times = [time for time in latest_times if time]
        state = sched[job_id]
        scheduler_state = state["scheduler_state"]
        scheduler_source = state["scheduler_source"]
        if scheduler_state == "not_in_squeue" and latest_times:
            scheduler_state = "RUNNING_INFERRED_FROM_FOAM_LOG"
            scheduler_source = "local_foam_log_fallback"
        rows.append(
            {
                **state,
                "scheduler_state": scheduler_state,
                "scheduler_source": scheduler_source,
                "case_count": len(job_cases),
                "latest_solver_time_s": max((float(time) for time in latest_times), default=0.0),
                "target_end_time_s": max((float(row["target_end_time_s"]) for row in job_cases), default=0.0),
                "diagnostic_use_policy": "diagnostic_only_until_terminal_steady_window_admission",
            }
        )
    return rows


def build_walltime_risk(live: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in live:
        latest = float(row["latest_solver_time_s"])
        target = float(row["target_end_time_s"])
        rows.append(
            {
                "job_id": row["job_id"],
                "scheduler_state": row["scheduler_state"],
                "latest_solver_time_s": latest,
                "target_end_time_s": target,
                "remaining_solver_time_s": max(target - latest, 0.0),
                "walltime_risk": "high" if str(row["scheduler_state"]).startswith("RUNNING") and target > latest else "terminal_or_unknown",
                "admitted_evidence_now": "false",
            }
        )
    return rows


def build_post_exit_harvest_command_plan() -> list[dict[str, Any]]:
    return [
        {
            "condition": "job_terminal_completed",
            "action": "run terminal harvest/readiness package before any admission",
            "fit_use": "forbidden_until_terminal_steady_window_pass",
        },
        {
            "condition": "job_failed_or_timeout",
            "action": "triage solver logs; classify diagnostic or repair before relaunch",
            "fit_use": "forbidden",
        },
    ]


def build_diagnostic_use_policy(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "case_key": row["case_key"],
            "job_id": row["job_id"],
            "current_use": "diagnostic_recirculation_onset_probe",
            "predictive_fit_use": "forbidden",
            "release_condition": "terminal steady retained window plus admission review",
        }
        for row in cases
    ]


def build_source_manifest(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    paths = [CAMPAIGN / "high_heat_probe_manifest.csv", CAMPAIGN / "high_heat_bracket_pack_manifest.csv"]
    paths.extend(foam_log_for(row) for row in cases)
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": "input_or_live_log", "mutation": "read_only"} for path in paths]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(f"# High-Heat Status Refresh\n\nRunning jobs: {summary['running_job_count']}. Admitted rows now: {summary['admitted_rows_now']}.\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- running_job_count: {summary['running_job_count']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} high-heat status refresh\n\nRefreshed high-heat jobs as diagnostic-only evidence.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    cases = load_cases()
    live = build_live_job_status(scheduler_rows(), cases)
    risk = build_walltime_risk(live)
    commands = build_post_exit_harvest_command_plan()
    policy = build_diagnostic_use_policy(cases)
    sources = build_source_manifest(cases)
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "job_count": len(JOB_IDS),
        "case_count": len(cases),
        "running_job_count": sum(str(row["scheduler_state"]).startswith("RUNNING") for row in live),
        "admitted_rows_now": 0,
        "fit_or_model_selection_changed": False,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "updated_live_job_status.csv", live)
    write_csv(OUT / "projected_walltime_risk.csv", risk)
    write_csv(OUT / "post_exit_harvest_command_plan.csv", commands)
    write_csv(OUT / "diagnostic_only_use_policy.csv", policy)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
