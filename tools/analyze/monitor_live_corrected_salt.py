#!/usr/bin/env python3
"""Read-only live sanity monitor for corrected Salt Q perturbation runs."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations"
DEFAULT_MANIFEST = CAMPAIGN / "corrected_case_manifest.csv"
DEFAULT_SUBMITTED = CAMPAIGN / "submitted_jobs.csv"
DEFAULT_GATE_JOB_ID = "3279646"
DEFAULT_DEPENDENCY = "afterany:3275448:3275449:3275560"

MDOT_MONITOR_DIRS = [
    "mdot_pipeleg_left_04_test_section",
    "mdot_pipeleg_lower_05_straight",
    "mdot_pipeleg_right_02_middle",
    "mdot_pipeleg_upper_05_cooler",
]

SALT_NOMINAL_MDOT = {
    "salt2": -0.01320,
    "salt3": -0.01499,
    "salt4": -0.01712,
}

FATAL_PATTERNS = (
    "FOAM FATAL ERROR",
    "FOAM exiting",
    "Floating point exception",
    "Segmentation fault",
    "SIGSEGV",
    "Traceback",
    "std::bad_alloc",
)

TERMINAL_BAD_STATES = (
    "BOOT_FAIL",
    "CANCELLED",
    "DEADLINE",
    "FAILED",
    "NODE_FAIL",
    "OUT_OF_MEMORY",
    "PREEMPTED",
    "TIMEOUT",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--submitted-jobs", default=str(DEFAULT_SUBMITTED))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--gate-job-id", default=DEFAULT_GATE_JOB_ID)
    parser.add_argument("--dependency", default=DEFAULT_DEPENDENCY)
    parser.add_argument("--squeue-snapshot", help="Optional pipe-delimited squeue snapshot with a header row.")
    parser.add_argument("--sacct-snapshot", help="Optional pipe-delimited sacct snapshot with a header row.")
    parser.add_argument("--no-scheduler", action="store_true", help="Skip squeue/sacct lookup.")
    parser.add_argument("--min-ended-advance-s", type=float, default=1000.0)
    parser.add_argument("--min-ended-advance-frac", type=float, default=0.20)
    parser.add_argument("--move-tolerance", type=float, default=0.5)
    parser.add_argument("--plateau-drift-pct", type=float, default=1.0)
    parser.add_argument("--plateau-amp-pct", type=float, default=2.0)
    parser.add_argument("--log-tail-bytes", type=int, default=8_000_000)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def safe_float(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_submitted_jobs(path: Path) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Parse the campaign's non-quoted submitted_jobs.csv conservatively."""
    case_to_job: dict[str, str] = {}
    jobs: dict[str, dict[str, str]] = {}
    if not path.exists():
        return case_to_job, jobs
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) < 3:
            continue
        group, job_id = parts[0], parts[1]
        jobs[job_id] = {"job_id": job_id, "job_name": group}
        case_keys = [part for part in parts[2:] if re.fullmatch(r"salt[1-4]_jin_.+_corrected", part)]
        for case_key in case_keys:
            case_to_job[case_key] = job_id
    return case_to_job, jobs


def query_squeue(job_ids: list[str]) -> dict[str, dict[str, str]]:
    if not job_ids:
        return {}
    cmd = "squeue -h -j " + shlex.quote(",".join(job_ids)) + " -o '%i|%j|%P|%T|%M|%l|%D|%R'"
    try:
        proc = subprocess.run(["bash", "-lc", cmd], text=True, capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {}
    out: dict[str, dict[str, str]] = {}
    for line in proc.stdout.splitlines():
        parts = line.split("|")
        if len(parts) != 8:
            continue
        job_id, name, partition, state, elapsed, limit, nodes, reason = parts
        out[job_id] = {
            "job_id": job_id,
            "job_name": name,
            "partition": partition,
            "job_state": state,
            "elapsed": elapsed,
            "time_limit": limit,
            "nodes": nodes,
            "node_or_reason": reason,
        }
    return out


def query_sacct(job_ids: list[str]) -> dict[str, dict[str, str]]:
    if not job_ids:
        return {}
    cmd = (
        "sacct -j "
        + shlex.quote(",".join(job_ids))
        + " --format=JobID,JobName%32,Partition,State,ExitCode,Elapsed,Start,End -X --parsable2 --noheader"
    )
    try:
        proc = subprocess.run(["bash", "-lc", cmd], text=True, capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {}
    out: dict[str, dict[str, str]] = {}
    for line in proc.stdout.splitlines():
        parts = line.split("|")
        if len(parts) < 8:
            continue
        job_id = parts[0].split(".")[0]
        out[job_id] = {
            "job_id": job_id,
            "job_name": parts[1].strip(),
            "partition": parts[2].strip(),
            "job_state": parts[3].strip(),
            "exit_code": parts[4].strip(),
            "elapsed": parts[5].strip(),
            "start": parts[6].strip(),
            "end": parts[7].strip(),
        }
    return out


def read_squeue_snapshot(path: str | None) -> dict[str, dict[str, str]]:
    if not path:
        return {}
    snap = Path(path)
    if not snap.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    with snap.open(encoding="utf-8", errors="ignore") as handle:
        rows = list(csv.DictReader(handle, delimiter="|"))
    for row in rows:
        job_id = row.get("JOBID", "")
        if not job_id:
            continue
        out[job_id] = {
            "job_id": job_id,
            "job_name": row.get("NAME", ""),
            "partition": row.get("PARTITION", ""),
            "job_state": row.get("STATE", ""),
            "elapsed": row.get("TIME", ""),
            "time_limit": row.get("TIME_LIMIT", ""),
            "nodes": row.get("NODES", ""),
            "node_or_reason": row.get("NODELIST(REASON)", ""),
        }
    return out


def read_sacct_snapshot(path: str | None) -> dict[str, dict[str, str]]:
    if not path:
        return {}
    snap = Path(path)
    if not snap.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    with snap.open(encoding="utf-8", errors="ignore") as handle:
        rows = list(csv.DictReader(handle, delimiter="|"))
    for row in rows:
        job_id = (row.get("JobID", "") or "").split(".")[0]
        if not job_id:
            continue
        out[job_id] = {
            "job_id": job_id,
            "job_name": row.get("JobName", ""),
            "partition": row.get("Partition", ""),
            "job_state": row.get("State", ""),
            "exit_code": row.get("ExitCode", ""),
            "elapsed": row.get("Elapsed", ""),
            "start": row.get("Start", ""),
            "end": row.get("End", ""),
        }
    return out


def merge_scheduler_info(
    base: dict[str, dict[str, str]], incoming: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    for job_id, values in incoming.items():
        merged = dict(base.get(job_id, {}))
        for key, value in values.items():
            if value != "":
                merged[key] = value
            elif key not in merged:
                merged[key] = value
        base[job_id] = merged
    return base


def parse_control_end_time(case_dir: Path) -> float:
    text = (case_dir / "system/controlDict").read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"(?m)^\s*endTime\s+([-+0-9.eE]+)\s*;", text)
    return safe_float(match.group(1)) if match else math.nan


def read_log_tail(log: Path, tail_bytes: int) -> str:
    size = log.stat().st_size
    with log.open("rb") as handle:
        if tail_bytes > 0 and size > tail_bytes:
            handle.seek(-tail_bytes, 2)
            handle.readline()
        return handle.read().decode("utf-8", errors="ignore")


def parse_log(log: Path, tail_bytes: int) -> dict[str, Any]:
    latest = math.nan
    fatal_count = 0
    warning_count = 0
    ended = False
    converged = False
    last_lines: list[str] = []
    if not log.exists():
        return {
            "latest_solver_time_s": latest,
            "fatal_error_count": 0,
            "warning_count": 0,
            "solver_log_has_end": False,
            "convergence_monitor_triggered": False,
            "log_scan_scope": "missing",
            "log_tail_excerpt": "",
        }
    text = read_log_tail(log, tail_bytes)
    scope = f"tail_bytes:{tail_bytes}" if tail_bytes > 0 and log.stat().st_size > tail_bytes else "full"
    for line in text.splitlines():
        last_lines.append(line)
        if len(last_lines) > 12:
            last_lines.pop(0)
        if line.startswith("Time ="):
            latest = safe_float(line.split("=", 1)[1].strip().rstrip("s"))
        if any(pattern.lower() in line.lower() for pattern in FATAL_PATTERNS):
            fatal_count += 1
        if "warning" in line.lower():
            warning_count += 1
        if line.strip() == "End":
            ended = True
        if "convergenceMonitor: CONVERGED" in line:
            converged = True
    return {
        "latest_solver_time_s": latest,
        "fatal_error_count": fatal_count,
        "warning_count": warning_count,
        "solver_log_has_end": ended,
        "convergence_monitor_triggered": converged,
        "log_scan_scope": scope,
        "log_tail_excerpt": " | ".join(last_lines[-5:]),
    }


def read_mdot_history(case_dir: Path) -> tuple[str, list[tuple[float, float]]]:
    best_monitor = ""
    best_history: list[tuple[float, float]] = []
    for monitor in MDOT_MONITOR_DIRS:
        history: list[tuple[float, float]] = []
        root = case_dir / "postProcessing" / monitor
        if not root.exists():
            continue
        for dat in sorted(root.glob("*/surfaceFieldValue.dat")):
            for line in dat.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                t = safe_float(parts[0])
                value = safe_float(parts[1])
                if math.isfinite(t) and math.isfinite(value):
                    history.append((t, value))
        history = sorted(set(history))
        if history and (not best_history or history[-1][0] > best_history[-1][0] or len(history) > len(best_history)):
            best_monitor = monitor
            best_history = history
    return best_monitor, best_history


def expected_move_frac(q_ratio: float) -> float:
    return abs(q_ratio ** (1.0 / 3.0) - 1.0) if math.isfinite(q_ratio) and q_ratio > 0 else math.nan


def mdot_metrics(case_key: str, q_ratio: float, case_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    monitor, history = read_mdot_history(case_dir)
    salt_match = re.match(r"(salt[1-4])_", case_key)
    salt_key = salt_match.group(1) if salt_match else ""
    nominal = SALT_NOMINAL_MDOT.get(salt_key, math.nan)
    out: dict[str, Any] = {
        "mdot_monitor": monitor,
        "mdot_latest_kg_s": math.nan,
        "nominal_mdot_kg_s": nominal,
        "mdot_moved_pct": math.nan,
        "expected_move_pct": 100.0 * expected_move_frac(q_ratio),
        "moved_enough": False,
        "mdot_direction_ok": False,
        "late_window_drift_pct": math.nan,
        "late_window_amp_pct": math.nan,
        "plateau_like": False,
    }
    if not history:
        return out
    latest_mdot = history[-1][1]
    out["mdot_latest_kg_s"] = latest_mdot
    if math.isfinite(nominal) and abs(nominal) > 1e-30:
        pct = 100.0 * (abs(latest_mdot) - abs(nominal)) / abs(nominal)
        expected_signed = 100.0 * (q_ratio ** (1.0 / 3.0) - 1.0) if math.isfinite(q_ratio) else math.nan
        out["mdot_moved_pct"] = pct
        out["mdot_direction_ok"] = bool(math.isfinite(expected_signed) and pct * expected_signed > 0)
        out["moved_enough"] = bool(
            math.isfinite(pct)
            and math.isfinite(expected_signed)
            and abs(pct) >= args.move_tolerance * abs(expected_signed)
            and pct * expected_signed > 0
        )
    window = history[-200:] if len(history) >= 200 else history
    vals = [abs(value) for _, value in window]
    if vals:
        mean = sum(vals) / len(vals)
        if mean > 0:
            out["late_window_drift_pct"] = 100.0 * (vals[-1] - vals[0]) / mean
            out["late_window_amp_pct"] = 100.0 * (max(vals) - min(vals)) / mean
            out["plateau_like"] = (
                abs(out["late_window_drift_pct"]) <= args.plateau_drift_pct
                and abs(out["late_window_amp_pct"]) <= args.plateau_amp_pct
            )
    return out


def audit_summary(case_dir: Path) -> dict[str, Any]:
    audits = sorted((case_dir / "logs").glob("preflight_patch_audit_*.csv"))
    bad = 0
    rows = 0
    job_ids: list[str] = []
    for audit in audits:
        job_ids.append(audit.stem.rsplit("_", 1)[-1])
        with audit.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows += 1
                for key, value in row.items():
                    if key.lower().endswith("ok") and str(value).lower() not in {"true", "1", "yes"}:
                        bad += 1
    return {"preflight_audit_rows": rows, "preflight_bad_ok_count": bad, "audit_job_ids": ";".join(job_ids)}


def classify(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    reasons: list[str] = []
    job_state = str(row.get("job_state", ""))
    terminal_bad = any(state in job_state.upper() for state in TERMINAL_BAD_STATES)
    if row["fatal_error_count"]:
        reasons.append(f"fatal/error markers={row['fatal_error_count']}")
    if terminal_bad:
        reasons.append(f"terminal/non-success scheduler state={job_state}")
    if row["preflight_bad_ok_count"]:
        reasons.append(f"preflight bad ok count={row['preflight_bad_ok_count']}")
    if not math.isfinite(row["nominal_mdot_kg_s"]):
        reasons.append("missing nominal mdot reference")
    short_advance = (
        not math.isfinite(row["advance_since_restart_s"])
        or row["advance_since_restart_s"] < args.min_ended_advance_s
        or (
            math.isfinite(row["advance_fraction_of_target"])
            and row["advance_fraction_of_target"] < args.min_ended_advance_frac
        )
    )
    if row["solver_log_has_end"] and short_advance:
        reasons.append(
            "ended early after "
            f"{row['advance_since_restart_s']:.3g}s past restart "
            f"({row['advance_fraction_of_target']:.2%} of target extension)"
        )
    elif terminal_bad and short_advance:
        reasons.append(
            "terminal short advance after "
            f"{row['advance_since_restart_s']:.3g}s past restart "
            f"({row['advance_fraction_of_target']:.2%} of target extension)"
        )
    if math.isfinite(row["nominal_mdot_kg_s"]) and not row["mdot_direction_ok"]:
        reasons.append("mdot movement direction is not consistent with Q perturbation")

    special = bool(reasons)
    if row["fatal_error_count"] or row["preflight_bad_ok_count"] or terminal_bad:
        recommendation = "investigate"
    elif special:
        recommendation = "hold_for_coordinator_review"
    elif not row["solver_log_has_end"]:
        recommendation = "hold_running_wait_for_formal_gate"
    elif row["moved_enough"] and row["plateau_like"]:
        recommendation = "admit_candidate_pending_formal_gate"
    else:
        recommendation = "hold_pending_formal_gate"
    return {
        "needs_special_gate_scrutiny": special,
        "scrutiny_reason": "; ".join(reasons),
        "closure_fit_admissible_without_coordinator_review": False if special else False,
        "recommendation": recommendation,
    }


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    manifest_rows = read_manifest(Path(args.manifest))
    case_to_job, submitted_jobs = read_submitted_jobs(Path(args.submitted_jobs))
    job_ids = sorted(set(case_to_job.values()) | {args.gate_job_id})
    scheduler: dict[str, dict[str, str]] = {}
    merge_scheduler_info(scheduler, read_sacct_snapshot(args.sacct_snapshot))
    merge_scheduler_info(scheduler, read_squeue_snapshot(args.squeue_snapshot))
    if not args.no_scheduler:
        live_sacct = query_sacct(job_ids)
        live_squeue = query_squeue(job_ids)
        merge_scheduler_info(scheduler, live_sacct)
        merge_scheduler_info(scheduler, live_squeue)

    rows = []
    for manifest_row in manifest_rows:
        case_key = manifest_row["case_key"]
        case_dir = Path(manifest_row["case_dir"])
        q_ratio = safe_float(manifest_row.get("q_ratio"))
        restart = safe_float(manifest_row.get("parent_restart_time_s"))
        target_end = safe_float(manifest_row.get("target_end_time_s"))
        log = case_dir / "logs/log.foamRun_corrected_q"
        log_metrics = parse_log(log, args.log_tail_bytes)
        latest = safe_float(log_metrics["latest_solver_time_s"])
        advance = latest - restart if math.isfinite(latest) and math.isfinite(restart) else math.nan
        target_extension = target_end - restart if math.isfinite(target_end) and math.isfinite(restart) else math.nan
        advance_frac = advance / target_extension if math.isfinite(advance) and target_extension > 0 else math.nan
        job_id = case_to_job.get(case_key, "")
        job_info = scheduler.get(job_id, submitted_jobs.get(job_id, {}))
        row = {
            "case_key": case_key,
            "case_dir": rel(case_dir),
            "job_id": job_id,
            "job_name": job_info.get("job_name", ""),
            "partition": job_info.get("partition", ""),
            "job_state": job_info.get("job_state", ""),
            "job_elapsed": job_info.get("elapsed", ""),
            "job_time_limit": job_info.get("time_limit", ""),
            "job_node_or_reason": job_info.get("node_or_reason", ""),
            "job_exit_code": job_info.get("exit_code", ""),
            "job_start": job_info.get("start", ""),
            "job_end": job_info.get("end", ""),
            "q_ratio": q_ratio,
            "restart_time_s": restart,
            "target_end_time_s": target_end,
            "control_end_time_s": parse_control_end_time(case_dir),
            "latest_solver_time_s": latest,
            "advance_since_restart_s": advance,
            "advance_fraction_of_target": advance_frac,
            **log_metrics,
            **audit_summary(case_dir),
            **mdot_metrics(case_key, q_ratio, case_dir, args),
            "log_path": rel(log),
        }
        row.update(classify(row, args))
        rows.append(row)
    return rows, scheduler


def write_outputs(rows: list[dict[str, Any]], scheduler: dict[str, dict[str, str]], args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    fields = [
        "case_key",
        "job_id",
        "job_name",
        "partition",
        "job_state",
        "job_elapsed",
        "job_time_limit",
        "job_exit_code",
        "job_start",
        "job_end",
        "q_ratio",
        "restart_time_s",
        "target_end_time_s",
        "control_end_time_s",
        "latest_solver_time_s",
        "advance_since_restart_s",
        "advance_fraction_of_target",
        "remaining_to_control_end_s",
        "solver_log_has_end",
        "convergence_monitor_triggered",
        "fatal_error_count",
        "warning_count",
        "log_scan_scope",
        "preflight_audit_rows",
        "preflight_bad_ok_count",
        "mdot_monitor",
        "mdot_latest_kg_s",
        "nominal_mdot_kg_s",
        "mdot_moved_pct",
        "expected_move_pct",
        "moved_enough",
        "mdot_direction_ok",
        "late_window_drift_pct",
        "late_window_amp_pct",
        "plateau_like",
        "needs_special_gate_scrutiny",
        "scrutiny_reason",
        "closure_fit_admissible_without_coordinator_review",
        "recommendation",
        "log_path",
    ]
    for row in rows:
        latest = safe_float(row["latest_solver_time_s"])
        end_time = safe_float(row["control_end_time_s"])
        row["remaining_to_control_end_s"] = end_time - latest if math.isfinite(latest) and math.isfinite(end_time) else math.nan
    with (output_dir / "live_salt_sanity_monitor.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    gate_info = scheduler.get(args.gate_job_id, {"job_id": args.gate_job_id, "job_state": "unknown"})
    payload = {
        "metadata": {
            "generated_at": generated_at,
            "tool": rel(Path(__file__)),
            "manifest": rel(Path(args.manifest)),
            "submitted_jobs": rel(Path(args.submitted_jobs)),
            "gate_job_id": args.gate_job_id,
            "dependency": args.dependency,
            "admission_policy": (
                "No row is closure-fit admissible from this live monitor. "
                "Rows with needs_special_gate_scrutiny require coordinator review even if a later formal gate looks requalified."
            ),
        },
        "gate_job": gate_info,
        "cases": rows,
        "summary": {
            "case_count": len(rows),
            "running_count": sum(1 for row in rows if row.get("job_state") == "RUNNING"),
            "ended_logs": sum(1 for row in rows if row["solver_log_has_end"]),
            "special_scrutiny_count": sum(1 for row in rows if row["needs_special_gate_scrutiny"]),
            "fatal_error_case_count": sum(1 for row in rows if row["fatal_error_count"]),
            "recommendation_counts": dict(
                (key, sum(1 for row in rows if row["recommendation"] == key))
                for key in sorted({row["recommendation"] for row in rows})
            ),
        },
    }
    (output_dir / "live_salt_sanity_monitor.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    flagged = [row for row in rows if row["needs_special_gate_scrutiny"]]
    lines = [
        "# Live Corrected Salt Sanity Monitor",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Scope",
        "",
        "Read-only inspection of corrected Salt Q solver logs, launch preflight audits, mdot monitors, and Slurm state.",
        "",
        "## Slurm",
        "",
        f"- Formal gate job: `{args.gate_job_id}`",
        f"- Dependency: `{args.dependency}`",
        f"- Gate state: `{gate_info.get('job_state', 'unknown')}`",
        f"- Gate partition: `{gate_info.get('partition', '')}`",
        "",
        "## Summary",
        "",
        f"- Cases scanned: `{len(rows)}`",
        f"- Cases with `needs_special_gate_scrutiny=True`: `{len(flagged)}`",
        f"- Fatal/error-marker cases: `{sum(1 for row in rows if row['fatal_error_count'])}`",
        "",
        "## Case Snapshot",
        "",
        "| case | job | partition | state | latest time s | fatal/error markers | recommendation |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        latest = row["latest_solver_time_s"]
        latest_text = f"{latest:.6g}" if math.isfinite(latest) else ""
        lines.append(
            f"| `{row['case_key']}` | `{row['job_id']}` | `{row['partition']}` | "
            f"`{row['job_state']}` | {latest_text} | {row['fatal_error_count']} | "
            f"`{row['recommendation']}` |"
        )
    lines.extend(
        [
            "",
            "## Admission Rule",
            "",
            "This monitor does not admit closure-fit rows. It can only recommend hold/investigate/admit-candidate-pending-formal-gate. Any row with `needs_special_gate_scrutiny=True` is not closure-fit admissible without coordinator review, even if later postprocessing reports `operating_point_verdict=requalified`.",
            "",
            "## Flagged Rows",
            "",
        ]
    )
    if flagged:
        lines.extend(["| case | recommendation | reason |", "| --- | --- | --- |"])
        for row in flagged:
            lines.append(f"| `{row['case_key']}` | `{row['recommendation']}` | {row['scrutiny_reason']} |")
    else:
        lines.append("No special-scrutiny rows were flagged.")
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `live_salt_sanity_monitor.csv`",
            "- `live_salt_sanity_monitor.json`",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows, scheduler = build_rows(args)
    write_outputs(rows, scheduler, args)
    flagged = sum(1 for row in rows if row["needs_special_gate_scrutiny"])
    print(f"Scanned {len(rows)} corrected Salt cases; special scrutiny flags={flagged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
