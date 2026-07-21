#!/usr/bin/env python3
"""Refresh high-heat terminal watch and two-tap CAND-001 readiness."""

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
TASK = "TODO-HIGH-HEAT-TERMINAL-WATCH-TWO-TAP-UPDATE"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_high_heat_terminal_watch_two_tap_update"
HIGH_HEAT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_high_heat_status_refresh"
SOURCE_FAMILY = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_source_family_refresh"
CAMPAIGN = ROOT / "jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-HIGH-HEAT-TERMINAL-WATCH-TWO-TAP-UPDATE.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/high-heat-terminal-watch-two-tap-update.md"
IMPORT = ROOT / "imports/2026-07-20_high_heat_terminal_watch_two_tap_update.json"

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


def tail_text(path: Path, max_bytes: int = 120_000) -> str:
    if not path.exists():
        return ""
    return path.read_bytes()[-max_bytes:].decode("utf-8", errors="replace")


def require_sources() -> None:
    required = [HIGH_HEAT / "updated_live_job_status.csv", SOURCE_FAMILY / "source_family_readiness.csv"]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing high-heat/two-tap watch sources: " + "; ".join(missing))


def parse_squeue(text: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("JOBID"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        if parts[0] in JOB_IDS:
            rows[parts[0]] = {"job_id": parts[0], "job_name": parts[2], "scheduler_state": parts[4], "elapsed": parts[5], "nodes": parts[6], "nodelist_or_reason": parts[7], "scheduler_source": "squeue"}
    return rows


def scheduler_rows() -> dict[str, dict[str, str]]:
    try:
        completed = subprocess.run(["squeue", "-j", ",".join(JOB_IDS)], cwd=ROOT, text=True, capture_output=True, timeout=15, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        completed = None
    parsed = parse_squeue(completed.stdout) if completed and completed.returncode == 0 else {}
    for job_id in JOB_IDS:
        parsed.setdefault(job_id, {"job_id": job_id, "job_name": "", "scheduler_state": "unknown_unavailable", "elapsed": "", "nodes": "", "nodelist_or_reason": "", "scheduler_source": "unavailable"})
    return parsed


def load_cases() -> list[dict[str, str]]:
    rows = []
    for path, job_id in [(CAMPAIGN / "high_heat_probe_manifest.csv", "3299610"), (CAMPAIGN / "high_heat_bracket_pack_manifest.csv", "3299620")]:
        if not path.exists():
            continue
        for row in read_csv(path):
            row = dict(row)
            row["job_id"] = job_id
            rows.append(row)
    return rows


def foam_log_for(row: dict[str, str]) -> Path:
    suffix = "log.foamRun_high_heat_probe" if row["job_id"] == "3299610" else "log.foamRun_high_heat_bracket"
    return Path(row["case_dir"]) / "logs" / suffix


def latest_time_s(path: Path) -> str:
    text = tail_text(path)
    times = re.findall(r"Time = ([0-9.]+)s", text)
    return times[-1] if times else ""


def build_high_heat_terminal_watch() -> list[dict[str, Any]]:
    sched = scheduler_rows()
    cases = load_cases()
    prior = {row["job_id"]: row for row in read_csv(HIGH_HEAT / "updated_live_job_status.csv")} if (HIGH_HEAT / "updated_live_job_status.csv").exists() else {}
    rows = []
    for job_id in JOB_IDS:
        job_cases = [row for row in cases if row["job_id"] == job_id]
        latest = max((float(t) for t in (latest_time_s(foam_log_for(row)) for row in job_cases) if t), default=0.0)
        target = max((float(row.get("target_end_time_s", "0") or 0) for row in job_cases), default=0.0)
        state = sched[job_id]
        if state["scheduler_state"] == "unknown_unavailable" and prior.get(job_id, {}).get("scheduler_state", "").startswith("RUNNING"):
            state = {
                **state,
                "scheduler_state": "R",
                "scheduler_source": "prior_high_heat_status_fallback",
                "elapsed": prior[job_id].get("elapsed", ""),
                "nodelist_or_reason": prior[job_id].get("nodelist_or_reason", "local_foam_log_fallback"),
            }
        terminal = state["scheduler_state"] in {"COMPLETED", "FAILED", "TIMEOUT", "CANCELLED", "OUT_OF_MEMORY", "NODE_FAIL"}
        rows.append(
            {
                **state,
                "case_count": len(job_cases),
                "latest_solver_time_s": latest,
                "target_end_time_s": target,
                "remaining_solver_time_s": max(target - latest, 0.0),
                "terminal_state": str(terminal).lower(),
                "admitted_evidence_now": "false",
                "diagnostic_policy": "diagnostic_only_until_terminal_steady_window_admission",
            }
        )
    return rows


def build_two_tap_cand001_readiness_update(watch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    any_running = any(row["scheduler_state"] in {"R", "RUNNING"} for row in watch)
    all_terminal = all(row["terminal_state"] == "true" for row in watch)
    if any_running:
        status = "terminal_gated_running"
        next_action = "continue monitoring high-heat jobs"
    elif all_terminal:
        status = "terminal_review_required"
        next_action = "run high-heat terminal harvest and low-reverse review"
    else:
        status = "scheduler_state_unknown"
        next_action = "refresh scheduler state"
    return [
        {
            "candidate_id": "CAND-001",
            "source_family": "Salt4 high-heat/no-recirculation probes",
            "readiness_status": status,
            "launch_allowed_now": "false",
            "component_k_status": "blocked_current_rows_diagnostic_only",
            "next_action": next_action,
        }
    ]


def build_post_exit_harvest_gate(watch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "job_id": row["job_id"],
            "scheduler_state": row["scheduler_state"],
            "terminal_state": row["terminal_state"],
            "harvest_gate": "ready_for_terminal_review" if row["terminal_state"] == "true" else "blocked_running_or_unknown",
            "required_before_two_tap_source_release": "terminal success;steady window;RAF/RMF low-reverse evidence;same-QOI sampler contract",
        }
        for row in watch
    ]


def build_source_family_next_action(cand: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": cand[0]["candidate_id"],
            "next_action": cand[0]["next_action"],
            "fallback_now": "false",
            "fallback_condition": "CAND-001 terminal review fails to provide usable low-reverse source",
            "auto_submit": "false",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [(HIGH_HEAT / "updated_live_job_status.csv", "prior high-heat status"), (SOURCE_FAMILY / "source_family_readiness.csv", "two-tap source-family state")]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(f"# High-Heat Terminal Watch And Two-Tap Update\n\nCAND-001 status: {summary['cand001_status']}.\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- cand001_status: {summary['cand001_status']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} high-heat terminal watch two-tap update\n\nRefreshed high-heat terminal gates for two-tap CAND-001.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    watch = build_high_heat_terminal_watch()
    cand = build_two_tap_cand001_readiness_update(watch)
    harvest = build_post_exit_harvest_gate(watch)
    next_action = build_source_family_next_action(cand)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "watched_jobs": len(watch),
        "running_jobs": sum(row["scheduler_state"] in {"R", "RUNNING"} for row in watch),
        "terminal_jobs": sum(row["terminal_state"] == "true" for row in watch),
        "cand001_status": cand[0]["readiness_status"],
        "two_tap_launch_allowed_now": False,
        "admitted_rows_now": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "high_heat_terminal_watch.csv", watch)
    write_csv(OUT / "two_tap_cand001_readiness_update.csv", cand)
    write_csv(OUT / "post_exit_harvest_gate.csv", harvest)
    write_csv(OUT / "source_family_next_action.csv", next_action)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
