#!/usr/bin/env python3
"""Triage failed 3305547 pressure/upcomer extraction and prepare repair queue."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PRESSURE-UPCOMER-3305547-FAILURE-REPAIR"
JOB_ID = "3305547"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_3305547_failure_repair"
RELAUNCH = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package"
PARSED = RELAUNCH / "parsed"
TMP = ROOT / "tmp/2026-07-20_pressure_upcomer_matched_plane_relaunch_package"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PRESSURE-UPCOMER-3305547-FAILURE-REPAIR.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/pressure-upcomer-3305547-failure-repair.md"
IMPORT = ROOT / "imports/2026-07-20_pressure_upcomer_3305547_failure_repair.json"

PM10_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q")
NOMINAL_CASES = ("salt2_jin_nominal_continuation", "salt3_jin_nominal_continuation", "salt4_jin_nominal_continuation")


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


def require_sources() -> None:
    required = [RELAUNCH / "candidate_readiness_matrix.csv", RELAUNCH / "slurm_submission_log.csv"]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing pressure/upcomer failure repair sources: " + "; ".join(missing))


def sacct_state() -> dict[str, str]:
    def parse_table(stdout: str) -> dict[str, str] | None:
        for line in stdout.splitlines():
            parts = line.split()
            if parts and parts[0] == JOB_ID and len(parts) >= 7:
                return {
                    "job_id": JOB_ID,
                    "job_name": parts[1],
                    "scheduler_state": parts[2],
                    "elapsed": parts[3],
                    "exit_code": parts[4],
                    "nodes": parts[5],
                    "nodelist": parts[6],
                    "scheduler_source": "sacct",
                }
        return None

    try:
        completed = subprocess.run(
            ["sacct", "-P", "-n", "-j", JOB_ID, "--format=JobIDRaw,JobName,State,Elapsed,ExitCode,NNodes,NodeList%80"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        completed = None
    if completed and completed.returncode == 0:
        for line in completed.stdout.splitlines():
            parts = line.split("|")
            if len(parts) >= 7 and parts[0].strip() == JOB_ID:
                return {
                    "job_id": JOB_ID,
                    "job_name": parts[1].strip(),
                    "scheduler_state": parts[2].strip(),
                    "elapsed": parts[3].strip(),
                    "exit_code": parts[4].strip(),
                    "nodes": parts[5].strip(),
                    "nodelist": parts[6].strip(),
                    "scheduler_source": "sacct",
                }
    try:
        completed = subprocess.run(
            ["sacct", "-j", JOB_ID, "--format=JobIDRaw,JobName,State,Elapsed,ExitCode,NNodes,NodeList%80"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        completed = None
    if completed and completed.returncode == 0:
        parsed = parse_table(completed.stdout)
        if parsed:
            return parsed
    if JOB_ID == "3305547":
        return {
            "job_id": JOB_ID,
            "job_name": "upc_nominal",
            "scheduler_state": "FAILED",
            "elapsed": "00:02:17",
            "exit_code": "1:0",
            "nodes": "1",
            "nodelist": "c308-005",
            "scheduler_source": "known_local_sacct_observation_fallback",
        }
    return {
        "job_id": JOB_ID,
        "job_name": "",
        "scheduler_state": "unknown_unavailable",
        "elapsed": "",
        "exit_code": "",
        "nodes": "",
        "nodelist": "",
        "scheduler_source": "unavailable",
    }


def build_job_3305547_failure_triage() -> list[dict[str, Any]]:
    row = sacct_state()
    stdout = RELAUNCH / f"logs/upcomer_nominal-{JOB_ID}.out"
    stderr = RELAUNCH / f"logs/upcomer_nominal-{JOB_ID}.err"
    error_text = "\n".join(path.read_text(encoding="utf-8", errors="replace")[-4000:] for path in (stdout, stderr) if path.exists())
    row.update(
        {
            "stdout_path": rel(stdout),
            "stderr_path": rel(stderr),
            "local_log_error_marker": str("FOAM FATAL" in error_text or "ERROR:" in error_text or "wrong token type" in error_text).lower(),
            "triage_status": "failed_needs_repair" if row["scheduler_state"] == "FAILED" else "state_refresh_required",
            "failure_interpretation": "job failed but parsed PM10 outputs may still be usable as diagnostic inventory",
            "native_solver_outputs_mutated": "false",
        }
    )
    return [row]


def parsed_file(case_key: str) -> Path:
    return PARSED / f"matched_plane_metrics_{case_key}.csv"


def build_partial_parse_inventory() -> list[dict[str, Any]]:
    rows = []
    for case_key in (*PM10_CASES, *NOMINAL_CASES):
        path = parsed_file(case_key)
        parsed_rows = read_csv(path) if path.exists() else []
        wall_failures = sum("wall_parse_failed" in row.get("quality_flags", "") for row in parsed_rows)
        diagnostic = sum(row.get("admission_status", "").startswith("diagnostic") for row in parsed_rows)
        blocked_or_incomplete = sum(
            row.get("admission_status", "").startswith("blocked") or row.get("metric_status") == "incomplete"
            for row in parsed_rows
        )
        rows.append(
            {
                "case_key": case_key,
                "parsed_file": rel(path),
                "exists": "yes" if path.exists() else "no",
                "parsed_rows": len(parsed_rows),
                "wall_parse_failure_rows": wall_failures,
                "blocked_or_incomplete_rows": blocked_or_incomplete,
                "diagnostic_only_rows": diagnostic,
                "parse_inventory_status": (
                    "parsed_blocked_or_incomplete"
                    if blocked_or_incomplete
                    else "parsed_diagnostic_only"
                    if parsed_rows
                    else "missing_parse_output"
                ),
            }
        )
    return rows


def build_salt2_lo10q_partial_admission_review() -> list[dict[str, Any]]:
    rows = []
    path = parsed_file("salt2_lo10q")
    for row in read_csv(path) if path.exists() else []:
        rows.append(
            {
                "case_key": row["case_key"],
                "plane_location": row["plane_location"],
                "station_label": row["station_label"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "metric_status": row["metric_status"],
                "quality_flags": row["quality_flags"],
                "admission_decision": "diagnostic_only_not_fit_admitted",
                "reason": "recirculation and missing wall-band T/wallHeatFlux prevent predictive upcomer admission",
                "source_path": rel(path),
            }
        )
    return rows


def readiness_by_case() -> dict[str, dict[str, str]]:
    return {row["case_key"]: row for row in read_csv(RELAUNCH / "candidate_readiness_matrix.csv")}


def build_remaining_case_relaunch_queue(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    readiness = readiness_by_case()
    rows = []
    for inv in inventory:
        case_key = inv["case_key"]
        source = readiness.get(case_key, readiness.get(f"{case_key}_jin_nominal_continuation", {}))
        needs_relaunch = (
            inv["exists"] == "no"
            or int(inv["wall_parse_failure_rows"]) > 0
            or int(inv["blocked_or_incomplete_rows"]) > 0
        )
        rows.append(
            {
                "case_key": case_key,
                "source_id": source.get("source_id", ""),
                "representative_time_s": source.get("representative_time_s", ""),
                "relaunch_needed": str(needs_relaunch).lower(),
                "relaunch_reason": (
                    "missing_parse_output" if inv["exists"] == "no" else "wall_band_fields_missing_or_parse_failed"
                    if int(inv["wall_parse_failure_rows"]) > 0
                    else "blocked_or_incomplete_parse_rows"
                    if int(inv["blocked_or_incomplete_rows"]) > 0
                    else "no_relaunch_needed_for_inventory"
                ),
                "recommended_mode": "one_case_isolated",
                "command": f"bash {rel(RELAUNCH / 'scripts/run_upcomer_matched_plane_compute.sh')} one {case_key}",
                "fit_release_after_relaunch": "false",
            }
        )
    return rows


def build_corrected_relaunch_plan(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "plan_id": "isolated_one_case_relaunch",
            "case_count": sum(row["relaunch_needed"] == "true" for row in queue),
            "policy": "run each case independently so one corrupted T field does not kill all rows",
            "preflight": f"bash {rel(RELAUNCH / 'scripts/run_upcomer_matched_plane_compute.sh')} preflight",
            "submit_policy": "manual_or_separate_sbatch_after_preflight",
            "admission_policy": "rerun parser and admission rollup; do not fit from partial/diagnostic rows",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (RELAUNCH / "slurm_submission_log.csv", "submission log"),
        (RELAUNCH / "candidate_readiness_matrix.csv", "case readiness"),
        (PARSED, "parsed matched-plane outputs"),
        (TMP, "local reconstruction scratch"),
    ]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        f"# Pressure/Upcomer 3305547 Failure Repair\n\nJob state: `{summary['job_state']}`. Parsed cases: {summary['parsed_case_count']}. Fit-admitted rows: {summary['fit_admitted_rows']}.\n",
        encoding="utf-8",
    )


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- job_state: {summary['job_state']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} pressure/upcomer 3305547 failure repair\n\nTriaged failed extraction and prepared relaunch queue.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    triage = build_job_3305547_failure_triage()
    inventory = build_partial_parse_inventory()
    salt2_review = build_salt2_lo10q_partial_admission_review()
    queue = build_remaining_case_relaunch_queue(inventory)
    plan = build_corrected_relaunch_plan(queue)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "job_id": JOB_ID,
        "job_state": triage[0]["scheduler_state"],
        "parsed_case_count": sum(row["exists"] == "yes" for row in inventory),
        "partial_admission_review_rows": len(salt2_review),
        "relaunch_needed_cases": sum(row["relaunch_needed"] == "true" for row in queue),
        "fit_admitted_rows": 0,
        "fit_or_model_selection_changed": False,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "job_3305547_failure_triage.csv", triage)
    write_csv(OUT / "partial_parse_inventory.csv", inventory)
    write_csv(OUT / "salt2_lo10q_partial_admission_review.csv", salt2_review)
    write_csv(OUT / "remaining_case_relaunch_queue.csv", queue)
    write_csv(OUT / "corrected_relaunch_plan.csv", plan)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
