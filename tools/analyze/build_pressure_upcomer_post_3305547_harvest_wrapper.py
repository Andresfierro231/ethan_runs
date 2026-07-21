#!/usr/bin/env python3
"""Prepare a post-3305547 pressure/upcomer harvest rollup wrapper."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PRESSURE-UPCOMER-POST-3305547-HARVEST-WRAPPER"
JOB_ID = "3305547"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_post_3305547_harvest_wrapper"
RELAUNCH = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package"
TMP = ROOT / "tmp/2026-07-20_pressure_upcomer_matched_plane_relaunch_package"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PRESSURE-UPCOMER-POST-3305547-HARVEST-WRAPPER.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/pressure-upcomer-post-3305547-harvest-wrapper.md"
IMPORT = ROOT / "imports/2026-07-20_pressure_upcomer_post_3305547_harvest_wrapper.json"

TERMINAL_STATES = {"COMPLETED", "FAILED", "TIMEOUT", "CANCELLED", "OUT_OF_MEMORY", "NODE_FAIL"}
SUCCESS_STATES = {"COMPLETED", "COMPLETED+"}


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
    required = [
        RELAUNCH / "slurm_submission_log.csv",
        RELAUNCH / "candidate_readiness_matrix.csv",
        RELAUNCH / "matched_plane_metrics_admission.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing pressure/upcomer wrapper sources: " + "; ".join(missing))


def run_command(args: list[str], timeout: int = 15) -> str:
    try:
        completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout


def scheduler_state() -> dict[str, str]:
    sacct = run_command(["sacct", "-P", "-n", "-j", JOB_ID, "--format=JobIDRaw,JobName,State,Elapsed,NNodes,NodeList%80"])
    for line in sacct.splitlines():
        parts = line.split("|")
        if len(parts) >= 6 and parts[0].strip() == JOB_ID:
            return {
                "job_id": JOB_ID,
                "job_name": parts[1].strip(),
                "scheduler_state": parts[2].strip(),
                "elapsed": parts[3].strip(),
                "nodes": parts[4].strip(),
                "nodelist_or_reason": parts[5].strip(),
                "scheduler_source": "sacct",
            }
    squeue = run_command(["squeue", "-h", "-j", JOB_ID, "-o", "%i|%j|%T|%M|%D|%R"])
    for line in squeue.splitlines():
        parts = line.split("|")
        if len(parts) == 6 and parts[0].strip() == JOB_ID:
            return {
                "job_id": JOB_ID,
                "job_name": parts[1].strip(),
                "scheduler_state": parts[2].strip(),
                "elapsed": parts[3].strip(),
                "nodes": parts[4].strip(),
                "nodelist_or_reason": parts[5].strip(),
                "scheduler_source": "squeue",
            }
    return {
        "job_id": JOB_ID,
        "job_name": "",
        "scheduler_state": "unknown_unavailable",
        "elapsed": "",
        "nodes": "",
        "nodelist_or_reason": "",
        "scheduler_source": "unavailable",
    }


def local_log_status() -> dict[str, str]:
    stdout = RELAUNCH / f"logs/upcomer_nominal-{JOB_ID}.out"
    stderr = RELAUNCH / f"logs/upcomer_nominal-{JOB_ID}.err"
    out_tail = stdout.read_text(encoding="utf-8", errors="replace")[-2000:] if stdout.exists() else ""
    err_tail = stderr.read_text(encoding="utf-8", errors="replace")[-2000:] if stderr.exists() else ""
    return {
        "stdout_exists": str(stdout.exists()).lower(),
        "stderr_exists": str(stderr.exists()).lower(),
        "stdout_tail_has_sampling": str("Sampling matched planes" in out_tail).lower(),
        "stderr_tail_has_error": str("error" in err_tail.lower() or "fatal" in err_tail.lower()).lower(),
        "stdout_path": rel(stdout),
        "stderr_path": rel(stderr),
    }


def build_job_status() -> list[dict[str, Any]]:
    row = scheduler_state()
    row.update(local_log_status())
    state = row["scheduler_state"].split()[0]
    row["terminal_state"] = str(state in TERMINAL_STATES or state in SUCCESS_STATES).lower()
    row["completed_successfully"] = str(state in SUCCESS_STATES).lower()
    row["wrapper_action"] = (
        "parse_available_outputs"
        if state in SUCCESS_STATES
        else "wait_for_terminal_job_state_or_use_existing_local_outputs_as_diagnostic"
    )
    row["submission_log"] = rel(RELAUNCH / "slurm_submission_log.csv")
    return [row]


def output_files_for_case(case_key: str) -> list[Path]:
    root = TMP / "recon" / case_key / "postProcessing"
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def build_matched_plane_parse_status(job_status: list[dict[str, Any]]) -> list[dict[str, Any]]:
    status = job_status[0]
    rows = []
    for candidate in read_csv(RELAUNCH / "candidate_readiness_matrix.csv"):
        if candidate.get("compute_readiness") != "runnable-now" and "lo10q" not in candidate.get("case_key", ""):
            continue
        case_key = candidate["case_key"].replace("_jin_nominal_continuation", "")
        files = output_files_for_case(case_key)
        rows.append(
            {
                "case_key": candidate["case_key"],
                "source_id": candidate["source_id"],
                "candidate_role": candidate["candidate_role"],
                "scheduler_state": status["scheduler_state"],
                "local_recon_dir": rel(TMP / "recon" / case_key),
                "postprocessing_file_count": len(files),
                "parse_status": (
                    "parser_inputs_present"
                    if files
                    else "job_pending_or_parser_outputs_missing"
                ),
                "next_action": (
                    "run matched-plane parser and refresh admission rollup"
                    if files
                    else "wait for 3305547 or rerun compute wrapper"
                ),
            }
        )
    return rows


def build_pressure_upcomer_admission_rollup(parse_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parse_by_case = {row["case_key"]: row for row in parse_rows}
    rows = []
    for metric in read_csv(RELAUNCH / "matched_plane_metrics_admission.csv"):
        parse = parse_by_case.get(metric["case_key"], {})
        parser_ready = parse.get("parse_status") == "parser_inputs_present"
        rows.append(
            {
                "case_key": metric["case_key"],
                "plane_location": metric["plane_location"],
                "station_label": metric["station_label"],
                "case_role": metric["case_role"],
                "pre_wrapper_admission_status": metric["admission_status"],
                "metric_status": metric["metric_status"],
                "parse_status": parse.get("parse_status", "no_wrapper_parse_row"),
                "post_3305547_admission_status": (
                    "blocked_parser_rollup_required"
                    if parser_ready
                    else "blocked_compute_or_parser_outputs_missing"
                ),
                "fit_candidate": "false",
                "source_path": rel(RELAUNCH / "matched_plane_metrics_admission.csv"),
            }
        )
    return rows


def build_fit_candidate_decision(rollup: list[dict[str, Any]]) -> list[dict[str, Any]]:
    admitted = [row for row in rollup if row["post_3305547_admission_status"] == "admitted_predictive_pressure_upcomer"]
    return [
        {
            "decision_id": "post_3305547_pressure_upcomer_fit_gate",
            "decision": "no_fit_candidate_released",
            "admitted_rows": len(admitted),
            "reason": "matched-plane parser/admission rollup has not produced admitted pressure/upcomer rows",
            "fit_or_model_selection_changed": "false",
            "native_solver_outputs_mutated": "false",
            "next_action": "after 3305547 terminal success, run parser and rerun this wrapper",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (RELAUNCH / "slurm_submission_log.csv", "3305547 submission log"),
        (RELAUNCH / "candidate_readiness_matrix.csv", "pressure/upcomer candidate matrix"),
        (RELAUNCH / "matched_plane_metrics_admission.csv", "prior admission rollup"),
        (TMP, "local reconstruction/postProcessing scratch"),
    ]
    return [
        {
            "source_id": path.name,
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "source_role": role,
            "mutation": "read_only",
        }
        for path, role in sources
    ]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "# Pressure/Upcomer Post-3305547 Harvest Wrapper",
                "",
                "This package records whether job 3305547 is ready for matched-plane pressure/upcomer harvest rollup.",
                "It does not submit jobs or mutate solver output.",
                "",
                "Primary outputs:",
                "",
                "- `job_status.csv`",
                "- `matched_plane_parse_status.csv`",
                "- `pressure_upcomer_admission_rollup.csv`",
                "- `fit_candidate_decision.csv`",
                "- `summary.json`",
                "",
                f"Scheduler state: {summary['scheduler_state']}.",
                f"Fit-admitted rows released: {summary['fit_admitted_rows']}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                f"# {TASK}",
                "",
                "- status: complete",
                f"- scheduler_state: {summary['scheduler_state']}",
                f"- parse_ready_rows: {summary['parse_ready_rows']}",
                f"- output: {rel(OUT)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "\n".join(
            [
                f"# {DATE} pressure/upcomer post-3305547 wrapper",
                "",
                "Prepared read-only harvest rollup wrapper for pressure/upcomer matched-plane evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        IMPORT,
        {
            "task": TASK,
            "date": DATE,
            "output_dir": rel(OUT),
            "native_solver_outputs_mutated": False,
            "generated_index_refreshed": False,
            "summary_path": rel(OUT / "summary.json"),
        },
    )


def main() -> dict[str, Any]:
    require_sources()
    job = build_job_status()
    parse = build_matched_plane_parse_status(job)
    rollup = build_pressure_upcomer_admission_rollup(parse)
    decision = build_fit_candidate_decision(rollup)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "job_id": JOB_ID,
        "scheduler_state": job[0]["scheduler_state"],
        "parse_status_rows": len(parse),
        "parse_ready_rows": sum(row["parse_status"] == "parser_inputs_present" for row in parse),
        "rollup_rows": len(rollup),
        "fit_admitted_rows": 0,
        "fit_or_model_selection_changed": False,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }

    write_csv(OUT / "job_status.csv", job)
    write_csv(OUT / "matched_plane_parse_status.csv", parse)
    write_csv(OUT / "pressure_upcomer_admission_rollup.csv", rollup)
    write_csv(OUT / "fit_candidate_decision.csv", decision)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
