#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-493"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness"
POLICY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv"
STEADY_ROOT = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/cases"
PM5_REPAIR = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair"
PM5_HOLDOUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair"
JOBS = ("3293924", "3295438")
SCHEDULER_DIAGNOSTICS: list[dict[str, Any]] = []

CASE_SPECS = [
    {
        "case_key": "salt2_lo10q",
        "source_key": "salt2_jin_lo10q_corrected",
        "fluid": "salt2",
        "q_ratio": "0.90",
        "stage_case": "viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
        "solver_job_id": "3293924",
        "harvest_job_id": "3295438",
    },
    {
        "case_key": "salt2_hi10q",
        "source_key": "salt2_jin_hi10q_corrected",
        "fluid": "salt2",
        "q_ratio": "1.10",
        "stage_case": "viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
        "solver_job_id": "3293924",
        "harvest_job_id": "3295438",
    },
    {
        "case_key": "salt4_lo10q",
        "source_key": "salt4_jin_lo10q_corrected",
        "fluid": "salt4",
        "q_ratio": "0.90",
        "stage_case": "viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "solver_job_id": "3293924",
        "harvest_job_id": "3295438",
    },
    {
        "case_key": "salt4_hi10q",
        "source_key": "salt4_jin_hi10q_corrected",
        "fluid": "salt4",
        "q_ratio": "1.10",
        "stage_case": "viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "solver_job_id": "3293924",
        "harvest_job_id": "3295438",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_absolute() else str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    if not fields:
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_remote(command: str, timeout: int = 20) -> str:
    diagnostic: dict[str, Any] = {"command": f"ssh login1 {command}"}
    SCHEDULER_DIAGNOSTICS.append(diagnostic)
    try:
        completed = subprocess.run(
            ["ssh", "login1", command],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        diagnostic.update({"returncode": "timeout", "stdout_lines": 0, "stderr_tail": ""})
        return ""
    diagnostic.update(
        {
            "returncode": completed.returncode,
            "stdout_lines": len(completed.stdout.splitlines()),
            "stderr_tail": "\n".join(completed.stderr.splitlines()[-6:]),
        }
    )
    return completed.stdout if completed.returncode == 0 else ""


def scheduler_rows(no_scheduler: bool) -> dict[str, dict[str, str]]:
    if no_scheduler:
        return {
            job_id: {
                "job_id": job_id,
                "job_name": "",
                "scheduler_state": "not_checked",
                "exit_code": "",
                "elapsed": "",
                "nodes": "",
                "nodelist": "",
                "scheduler_source": "disabled_for_test",
            }
            for job_id in JOBS
        }

    out = run_remote(
        "sacct -P -n "
        f"-j {','.join(JOBS)} "
        "--format=JobIDRaw,JobName,State,ExitCode,Elapsed,NNodes,NodeList%80"
    )
    rows: dict[str, dict[str, str]] = {}
    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) < 7:
            continue
        job_id = parts[0].strip()
        if job_id not in JOBS:
            continue
        rows[job_id] = {
            "job_id": job_id,
            "job_name": parts[1].strip(),
            "scheduler_state": parts[2].strip(),
            "exit_code": parts[3].strip(),
            "elapsed": parts[4].strip(),
            "nodes": parts[5].strip(),
            "nodelist": parts[6].strip(),
            "scheduler_source": "sacct",
        }
    for job_id in JOBS:
        rows.setdefault(
            job_id,
            {
                "job_id": job_id,
                "job_name": "",
                "scheduler_state": "unknown_unavailable",
                "exit_code": "",
                "elapsed": "",
                "nodes": "",
                "nodelist": "",
                "scheduler_source": "unavailable",
            },
        )
    return rows


def policy_rows() -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(POLICY)
        if row.get("required_before_use") == "TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION"
    ]


def case_dir(spec: dict[str, str]) -> Path:
    return (
        ROOT
        / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs"
        / spec["source_key"]
        / "case_stage"
        / spec["stage_case"]
    )


def stats_path(spec: dict[str, str]) -> Path:
    slug = (
        "modern_runs__2026-07-04_corrected_salt_q_perturbations__"
        f"{spec['source_key']}__{spec['stage_case']}"
    )
    return STEADY_ROOT / slug / "stats.json"


def stats_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "steady_stats_available": "no",
            "representative_mdot_verdict": "",
            "representative_mdot_t_last_s": "",
            "representative_mdot_rel_drift": "",
            "steady_row_count": 0,
            "not_steady_row_count": 0,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    verdict_counts = Counter(str(row.get("verdict", "")) for row in rows)
    rep_mdot = next(
        (
            row
            for row in rows
            if row.get("group") == "mdot" and row.get("representative") is True
        ),
        {},
    )
    return {
        "steady_stats_available": "yes",
        "representative_mdot_verdict": rep_mdot.get("verdict", ""),
        "representative_mdot_t_last_s": rep_mdot.get("t_last", ""),
        "representative_mdot_rel_drift": rep_mdot.get("rel_drift_over_window", ""),
        "steady_row_count": verdict_counts.get("steady", 0),
        "not_steady_row_count": verdict_counts.get("not_steady", 0),
    }


def readiness_state(spec: dict[str, str], sched: dict[str, dict[str, str]]) -> tuple[str, str]:
    solver = sched[spec["solver_job_id"]]["scheduler_state"]
    harvest = sched[spec["harvest_job_id"]]["scheduler_state"]
    if solver == "COMPLETED" and harvest == "COMPLETED":
        return "ready_for_terminal_admission_review", "claim extraction/admission task and run PM10 matched-plane package"
    if solver in {"RUNNING", "PENDING", "CONFIGURING", "COMPLETING"} or harvest in {"RUNNING", "PENDING", "CONFIGURING", "COMPLETING"}:
        return "blocked_live_job", "monitor only; do not run PM10 terminal admission yet"
    if solver in {"FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL"} or harvest in {
        "FAILED",
        "CANCELLED",
        "TIMEOUT",
        "OUT_OF_MEMORY",
        "NODE_FAIL",
    }:
        return "blocked_terminal_failure_review", "inspect failed job logs before postprocessing"
    return "blocked_scheduler_unknown", "refresh scheduler state from login node"


def live_job_status(sched: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    roles = {
        "3293924": "packed Salt2/Salt4 +/-10Q solver continuation",
        "3295438": "dependent Salt2/Salt4 +/-10Q harvest/postprocess job",
    }
    return [{**sched[job_id], "role": roles[job_id]} for job_id in JOBS]


def todo_definition() -> list[dict[str, Any]]:
    return [
        {
            "todo_id": "TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION",
            "meaning": "Terminal admission and PM5-style diagnostic postprocessing for Salt2/Salt4 +/-10Q corrected-Q future holdout candidates.",
            "cases": ";".join(row["case_key"] for row in policy_rows()),
            "must_wait_for_jobs": "3293924;3295438",
            "current_allowed_action": "readiness_monitor_only_until_jobs_terminal",
            "scientific_guardrail": "future holdout candidates; no fitting or model selection before explicit admission.",
            "source": rel(POLICY),
        }
    ]


def pm5_workflow_reference() -> list[dict[str, Any]]:
    return [
        {
            "step": "copy_to_scratch",
            "pm5_action": "AGENT-406 used copied scratch cases, not native solver trees.",
            "pm10_action": "Use a new task-owned scratch tree after terminal completion.",
        },
        {
            "step": "reconstruct_and_sample",
            "pm5_action": "Reconstructed representative-time staged copies and sampled upcomer inlet/mid/outlet planes plus wall-band surfaces.",
            "pm10_action": "Repeat for Salt2/Salt4 +/-10Q terminal representative windows.",
        },
        {
            "step": "field_contract",
            "pm5_action": "Validated U, T, rho, p_rgh, Re, Pr, Ri, Gr, Ra, and wallHeatFlux.",
            "pm10_action": "Require the same fields plus Gz, reverse fractions, secondary velocity, wall-core Delta T, and steady-window metadata.",
        },
        {
            "step": "parse_metrics",
            "pm5_action": "Produced 12 complete matched-plane rows and 12 validation rows; Salt2 holdout package reused 6 of them.",
            "pm10_action": "Produce 12 PM10 rows across four cases and three planes if all fields pass.",
        },
        {
            "step": "admission",
            "pm5_action": "Rows were diagnostic only; Salt2 +/-5Q had 0 fit-admitted rows and the old broken July 14 script was not relaunched.",
            "pm10_action": "Run terminal admission after jobs complete; default stance is holdout diagnostic until gates admit otherwise.",
        },
    ]


def case_readiness(sched: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    policy_by_case = {row["case_key"]: row for row in policy_rows()}
    rows: list[dict[str, Any]] = []
    for spec in CASE_SPECS:
        state, action = readiness_state(spec, sched)
        stats = stats_summary(stats_path(spec))
        policy = policy_by_case.get(spec["case_key"], {})
        rows.append(
            {
                "case_key": spec["case_key"],
                "source_key": spec["source_key"],
                "fluid": spec["fluid"],
                "q_ratio": spec["q_ratio"],
                "split_role": policy.get("split_role", "future_holdout_candidate"),
                "fit_allowed": policy.get("fit_allowed", "no"),
                "model_selection_allowed": policy.get("model_selection_allowed", "no"),
                "score_allowed": policy.get("score_allowed", "yes_after_terminal_admission"),
                "solver_job_id": spec["solver_job_id"],
                "solver_state": sched[spec["solver_job_id"]]["scheduler_state"],
                "harvest_job_id": spec["harvest_job_id"],
                "harvest_state": sched[spec["harvest_job_id"]]["scheduler_state"],
                "readiness_state": state,
                "next_action": action,
                "case_dir": rel(case_dir(spec)),
                "steady_stats": rel(stats_path(spec)),
                **stats,
            }
        )
    return rows


def terminal_admission_contract() -> list[dict[str, str]]:
    required = [
        ("terminal_scheduler_state", "Both `3293924` and `3295438` complete successfully before admission."),
        ("steady_window_status", "Use last retained mdot/heat/T/wall-T windows; reject or label drifting windows."),
        ("U", "Matched upcomer inlet/mid/outlet planes."),
        ("T", "Matched planes plus wall/core samples."),
        ("wallHeatFlux", "Wall-band and patch-integrated heat evidence."),
        ("Re_Pr_Ri_Gr_Ra_Gz", "Derived at the same planes with documented property basis."),
        ("reverse_area_mass_fraction", "Recirculation classifier for holdout diagnostics and fit blocking."),
        ("secondary_velocity_fraction", "Recirculation strength proxy."),
        ("wall_core_delta_T", "Internal-Nu diagnostic, not a runtime input."),
        ("mesh_time_uncertainty", "Time-window UQ now; mesh/GCI remains a final-admission blocker if absent."),
        ("runtime_leakage_audit", "No realized CFD mdot, wallHeatFlux, or fitted holdout data as predictive runtime input."),
    ]
    return [
        {
            "required_item": item,
            "contract": contract,
            "required_before_pm10_terminal_admission": "yes",
        }
        for item, contract in required
    ]


def command_plan() -> str:
    return """# PM10 Terminal Admission Command Plan

Do not run terminal admission while `3293924` is still running or `3295438` is
pending/running.

1. Refresh scheduler state:

```bash
ssh login1 sacct -j 3293924,3295438 --format JobIDRaw,JobName,State,ExitCode,Elapsed,NNodes,NodeList%80 -P -n
```

2. If both parent jobs are `COMPLETED`, claim a new extraction/admission task.

3. Repeat the PM5 pattern, but in a new task-owned scratch tree:

- copy terminal Salt2/Salt4 +/-10Q cases to scratch
- reconstruct representative terminal windows
- sample upcomer inlet/mid/outlet planes and wall-band surfaces
- validate `U`, `T`, `rho`, `p_rgh`, `Re`, `Pr`, `Ri`, `Gr`, `Ra`, `Gz`, and `wallHeatFlux`
- parse reverse area/mass fraction, secondary velocity, wall-core Delta T, and steady-window metadata
- publish admission and runtime-leakage tables

4. Do not relaunch the old broken July 14 PM5 script unchanged. Use the AGENT-406
repair lessons: scratch-only reconstruction, explicit field validation, and
diagnostic-only admission until recirculation/sign/mesh gates pass.
"""


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        POLICY,
        PM5_REPAIR / "README.md",
        PM5_REPAIR / "summary.json",
        PM5_REPAIR / "resampled_pm5_matched_plane_metrics.csv",
        PM5_HOLDOUT / "README.md",
        PM5_HOLDOUT / "summary.json",
        ROOT / "imports/2026-07-13_salt_q_four_row_packed_continuation.json",
        ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_plan_implementation_closeout/latest_scheduler_snapshot.md",
    ]
    paths.extend(stats_path(spec) for spec in CASE_SPECS)
    return [{"source_path": rel(path), "exists": path.exists(), "role": "input_or_context"} for path in paths]


def write_readme(summary: dict[str, Any]) -> None:
    (OUT / "README.md").write_text(
        f"""---
provenance:
  - {rel(POLICY)}
  - {rel(PM5_REPAIR / "README.md")}
  - {rel(PM5_HOLDOUT / "README.md")}
tags: [salt, pm10, terminal-admission, holdout, recirculation]
related:
  - .agent/status/2026-07-17_AGENT-493.md
  - .agent/journal/2026-07-17/salt-pm10-terminal-admission-readiness.md
task: {TASK}
date: {DATE}
role: cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Salt PM10 Terminal Admission Readiness

This package defines `TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION` and captures
why terminal admission cannot be completed yet.

## Current State

- PM10 cases tracked: `{summary["case_count"]}`.
- Jobs tracked: `{summary["job_count"]}`.
- Cases ready for terminal admission now: `{summary["ready_for_terminal_admission_count"]}`.
- Cases blocked by live/non-terminal jobs: `{summary["blocked_live_job_count"]}`.
- Terminal admission performed here: `no`.

## PM5 Reference

PM5 postprocessing means the AGENT-406 scratch-copy matched-plane/wall-band
repair: reconstruct copied cases, sample upcomer planes and wall bands, validate
fields including `wallHeatFlux`, parse recirculation and dimensionless metrics,
and publish diagnostic admission tables. The old broken July 14 PM5 script was
not relaunched unchanged.

## Files

- `todo_definition.csv`
- `live_job_status.csv`
- `pm10_case_readiness.csv`
- `pm5_workflow_reference.csv`
- `terminal_admission_contract.csv`
- `postprocess_command_plan.md`
- `source_manifest.csv`
- `scheduler_query_diagnostics.json`
- `summary.json`
""",
        encoding="utf-8",
    )


def build(no_scheduler: bool = False) -> dict[str, Any]:
    SCHEDULER_DIAGNOSTICS.clear()
    OUT.mkdir(parents=True, exist_ok=True)
    sched = scheduler_rows(no_scheduler)
    jobs = live_job_status(sched)
    readiness = case_readiness(sched)

    write_csv(OUT / "todo_definition.csv", todo_definition())
    write_csv(OUT / "live_job_status.csv", jobs)
    write_csv(OUT / "pm10_case_readiness.csv", readiness)
    write_csv(OUT / "pm5_workflow_reference.csv", pm5_workflow_reference())
    write_csv(OUT / "terminal_admission_contract.csv", terminal_admission_contract())
    write_csv(OUT / "source_manifest.csv", source_manifest())
    (OUT / "postprocess_command_plan.md").write_text(command_plan(), encoding="utf-8")
    (OUT / "scheduler_query_diagnostics.json").write_text(
        json.dumps(SCHEDULER_DIAGNOSTICS, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    states = Counter(row["readiness_state"] for row in readiness)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "case_count": len(readiness),
        "job_count": len(JOBS),
        "ready_for_terminal_admission_count": states.get("ready_for_terminal_admission_review", 0),
        "blocked_live_job_count": states.get("blocked_live_job", 0),
        "blocked_scheduler_unknown_count": states.get("blocked_scheduler_unknown", 0),
        "terminal_admission_performed": "no",
        "native_output_mutation": "none",
        "scheduler_action": "read_only_status_check" if not no_scheduler else "none_disabled_for_test",
        "pm5_postprocessing_reusable_pattern": "yes_after_pm10_terminal_completion",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-scheduler", action="store_true", help="Do not query scheduler state.")
    args = parser.parse_args()
    summary = build(no_scheduler=args.no_scheduler)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
