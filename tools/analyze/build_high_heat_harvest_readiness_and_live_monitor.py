#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-485"
DATE = "2026-07-17"
CAMPAIGN = ROOT / "jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe"
OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor"
JOB_IDS = ["3299610", "3299620"]
SCHEDULER_DIAGNOSTICS: list[dict[str, object]] = []


@dataclass(frozen=True)
class CaseRuntime:
    case_key: str
    display_name: str
    job_id: str
    job_name: str
    foam_log: Path
    runtime_preflight: Path
    slurm_stdout: Path
    slurm_stderr: Path


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def tail_text(path: Path, max_bytes: int = 250_000) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return data[-max_bytes:].decode("utf-8", errors="replace")


def run_remote(command: str, timeout: int = 20) -> str:
    diagnostic: dict[str, object] = {"command": f"ssh login1 {command}"}
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
    if completed.returncode != 0:
        return ""
    return completed.stdout


def scheduler_rows(no_scheduler: bool) -> dict[str, dict[str, str]]:
    if no_scheduler:
        return {
            job_id: {
                "job_id": job_id,
                "job_name": "",
                "scheduler_state": "not_checked",
                "elapsed": "",
                "nodes": "",
                "nodelist_or_reason": "",
                "scheduler_source": "disabled",
            }
            for job_id in JOB_IDS
        }

    job_list = ",".join(JOB_IDS)
    rows: dict[str, dict[str, str]] = {}

    sacct = run_remote(
        "sacct -P -n "
        f"-j {job_list} "
        "--format=JobIDRaw,JobName,State,Elapsed,NNodes,NodeList%80"
    )
    for line in sacct.splitlines():
        parts = line.split("|")
        if len(parts) < 6:
            continue
        job_id = parts[0].strip()
        if job_id not in JOB_IDS:
            continue
        rows[job_id] = {
            "job_id": job_id,
            "job_name": parts[1].strip(),
            "scheduler_state": parts[2].strip(),
            "elapsed": parts[3].strip(),
            "nodes": parts[4].strip(),
            "nodelist_or_reason": parts[5].strip(),
            "scheduler_source": "sacct",
        }

    missing = [job_id for job_id in JOB_IDS if job_id not in rows]
    if missing:
        squeue_format = shlex.quote("%i|%j|%T|%M|%D|%R")
        out = run_remote(f"squeue -h -j {','.join(missing)} -o {squeue_format}")
    else:
        out = ""
    for line in out.splitlines():
        if "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) != 6:
            continue
        job_id, job_name, state, elapsed, nodes, reason = [part.strip() for part in parts]
        if job_id not in missing:
            continue
        rows[job_id] = {
            "job_id": job_id,
            "job_name": job_name,
            "scheduler_state": state,
            "elapsed": elapsed,
            "nodes": nodes,
            "nodelist_or_reason": reason,
            "scheduler_source": "squeue",
        }

    for job_id in JOB_IDS:
        rows.setdefault(
            job_id,
            {
                "job_id": job_id,
                "job_name": "",
                "scheduler_state": "unknown_unavailable",
                "elapsed": "",
                "nodes": "",
                "nodelist_or_reason": "",
                "scheduler_source": "unavailable",
            },
        )
    return rows


def load_cases() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(CAMPAIGN / "high_heat_probe_manifest.csv"):
        row = dict(row)
        row["job_id"] = "3299610"
        row["job_name"] = "salt4_q3x_probe"
        row["manifest_source"] = rel(CAMPAIGN / "high_heat_probe_manifest.csv")
        rows.append(row)
    for row in read_csv(CAMPAIGN / "high_heat_bracket_pack_manifest.csv"):
        row = dict(row)
        row["job_id"] = "3299620"
        row["job_name"] = "salt4_heat_pack"
        row["manifest_source"] = rel(CAMPAIGN / "high_heat_bracket_pack_manifest.csv")
        rows.append(row)
    return sorted(rows, key=lambda item: float(item["target_heater_power_W"]))


def runtime_for(row: dict[str, str]) -> CaseRuntime:
    case_dir = Path(row["case_dir"])
    if row["job_id"] == "3299610":
        return CaseRuntime(
            case_key=row["case_key"],
            display_name=row["display_name"],
            job_id=row["job_id"],
            job_name=row["job_name"],
            foam_log=case_dir / "logs/log.foamRun_high_heat_probe",
            runtime_preflight=CAMPAIGN / "logs/runtime_preflight_3299610.csv",
            slurm_stdout=CAMPAIGN / "slurm-salt4_q3x_probe-3299610.out",
            slurm_stderr=CAMPAIGN / "slurm-salt4_q3x_probe-3299610.err",
        )
    return CaseRuntime(
        case_key=row["case_key"],
        display_name=row["display_name"],
        job_id=row["job_id"],
        job_name=row["job_name"],
        foam_log=case_dir / "logs/log.foamRun_high_heat_bracket",
        runtime_preflight=CAMPAIGN / "logs/bracket_runtime_preflight_3299620.csv",
        slurm_stdout=CAMPAIGN / "slurm-salt4_heat_pack-3299620.out",
        slurm_stderr=CAMPAIGN / "slurm-salt4_heat_pack-3299620.err",
    )


def preflight_status(path: Path, case_key: str) -> str:
    if not path.exists():
        return "missing"
    rows = read_csv(path)
    matched = [row for row in rows if row.get("case_key") == case_key]
    if not matched:
        return "missing_case_row"
    row = matched[0]
    if row.get("overall_ok") == "True":
        return "passed"
    return "failed"


def log_phase(runtime: CaseRuntime, preflight: str) -> tuple[str, str, str]:
    slurm = tail_text(runtime.slurm_stdout)
    foam = tail_text(runtime.foam_log)
    if "FOAM FATAL" in foam or "Foam::error" in foam:
        return "solver_failed", latest_time_from_log(foam), "foam fatal/error in log"
    if foam:
        return "foamrun_active_or_recent", latest_time_from_log(foam), "foamRun log exists"
    if preflight == "passed" and "launching" in slurm:
        return "launched_waiting_for_log", "", "launch message found but foamRun log not readable yet"
    if preflight == "passed":
        return "runtime_preflight_passed", "", "restart-level Q preflight passed"
    if "copying processors64" in slurm:
        return "startup_copy_or_patch", "", "copying or patching restart tree"
    return "not_started_or_unknown", "", "no foamRun evidence"


def latest_time_from_log(text: str) -> str:
    times = re.findall(r"Time = ([0-9.]+)s", text)
    return times[-1] if times else ""


def readiness_state(scheduler_state: str, preflight: str, phase: str) -> str:
    terminal_states = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL"}
    if preflight == "failed":
        return "failed_preflight"
    if phase == "solver_failed":
        return "failed_solver"
    if scheduler_state in {"RUNNING", "COMPLETING"}:
        return "running_not_terminal"
    if scheduler_state in terminal_states:
        if scheduler_state == "COMPLETED":
            return "terminal_ready_for_harvest"
        return "terminal_failed_needs_review"
    return "not_ready_scheduler_unknown"


def live_job_status(cases: list[dict[str, str]], sched: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for job_id in JOB_IDS:
        job_cases = [row for row in cases if row["job_id"] == job_id]
        runtime = runtime_for(job_cases[0])
        stdout = tail_text(runtime.slurm_stdout)
        preflight = "passed" if "failures=0" in stdout else ("failed" if "failures=" in stdout else "missing")
        state = sched[job_id]
        rows.append(
            {
                **state,
                "case_count": len(job_cases),
                "case_keys": ";".join(row["case_key"] for row in job_cases),
                "slurm_stdout": rel(runtime.slurm_stdout),
                "slurm_stderr": rel(runtime.slurm_stderr),
                "job_preflight_status": preflight,
                "log_phase": "foamrun_launched" if any(runtime_for(row).foam_log.exists() for row in job_cases) else "startup_or_prelaunch",
            }
        )
    return rows


def case_index(cases: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in cases:
        runtime = runtime_for(row)
        cooler_total = sum(float(row[column]) for column in ["target_cooler_q04_W", "target_cooler_q05_W", "target_cooler_q06_W"])
        rows.append(
            {
                "case_key": row["case_key"],
                "display_name": row["display_name"],
                "job_id": row["job_id"],
                "target_heater_power_W": row["target_heater_power_W"],
                "target_heater_patch_Q_W": row.get("target_heater_patch_Q_W") or f"{float(row['target_heater_power_W']) / 3.0:.12g}",
                "cooler_q04_W": row["target_cooler_q04_W"],
                "cooler_q05_W": row["target_cooler_q05_W"],
                "cooler_q06_W": row["target_cooler_q06_W"],
                "cooler_total_W": f"{cooler_total:.12g}",
                "restart_time_s": row["parent_restart_time_s"],
                "target_end_time_s": row["target_end_time_s"],
                "case_dir": rel(Path(row["case_dir"])),
                "foam_log": rel(runtime.foam_log),
                "manifest_source": row["manifest_source"],
            }
        )
    return rows


def harvest_queue(cases: list[dict[str, str]], sched: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in cases:
        runtime = runtime_for(row)
        preflight = preflight_status(runtime.runtime_preflight, row["case_key"])
        phase, latest_time, note = log_phase(runtime, preflight)
        scheduler_state = sched[row["job_id"]]["scheduler_state"]
        readiness = readiness_state(scheduler_state, preflight, phase)
        rows.append(
            {
                "case_key": row["case_key"],
                "job_id": row["job_id"],
                "scheduler_state": scheduler_state,
                "runtime_preflight_status": preflight,
                "log_phase": phase,
                "latest_log_time_s": latest_time,
                "harvest_readiness": readiness,
                "next_action": next_action(readiness),
                "note": note,
            }
        )
    return rows


def next_action(readiness: str) -> str:
    return {
        "running_not_terminal": "monitor only; do not harvest native outputs yet",
        "terminal_ready_for_harvest": "claim extraction task and run terminal harvest/postprocessing",
        "failed_preflight": "inspect preflight CSV and restart patch audit; do not resubmit automatically",
        "failed_solver": "inspect foamRun log and Slurm stderr; document failed phase before repair",
        "terminal_failed_needs_review": "review sacct state and logs before any repair or rerun",
        "not_ready_scheduler_unknown": "refresh scheduler state from login node",
    }.get(readiness, "review manually")


def required_qoi_contract() -> list[dict[str, object]]:
    rows = [
        ("U", "native field", "sample upcomer inlet/mid/outlet planes plus centerline spans", "velocity vector, throughflow, reverse mask, secondary velocity"),
        ("T", "native field", "same matched planes plus wall-band/core samples", "bulk/core temperature and wall-core Delta T"),
        ("wallHeatFlux", "native wall field/function output", "patch-integrated and wall-band extraction", "source/sink ledger and heat-balance gate"),
        ("Re", "derived", "rho*U_bulk*D_h/mu(T_bulk)", "throughflow coordinate"),
        ("Pr", "derived", "mu(T_bulk)*Cp(T_bulk)/k(T_bulk)", "property coordinate"),
        ("Ri", "derived", "Gr/Re^2 with documented characteristic length", "mixed-convection coordinate"),
        ("Gr", "derived", "g*beta*DeltaT*L^3/nu^2", "buoyancy coordinate"),
        ("Ra", "derived", "Gr*Pr", "thermal-buoyancy coordinate"),
        ("Gz", "derived", "Re*Pr*D_h/x_from_reset", "development coordinate"),
        ("wall_core_deltaT", "derived", "T_wall_band - T_core on each plane", "cell-driving thermal contrast"),
        ("reverse_area_fraction", "derived from U dot n", "area fraction with local reverse axial velocity", "recirculation classifier"),
        ("reverse_mass_fraction", "derived from rho U dot n", "reverse mass flux / total absolute mass flux", "material backflow classifier"),
        ("secondary_velocity_fraction", "derived from U", "transverse speed / axial speed on plane", "recirculation strength proxy"),
        ("steady_window_status", "time-window analysis", "last retained mdot, heat residual, T, wall-T windows", "admission gate"),
        ("mesh_time_uncertainty", "uncertainty plan", "time-window UQ now; mesh/GCI after endpoint selection", "coefficient-fit guardrail"),
    ]
    return [
        {
            "required_output": name,
            "source_type": source,
            "method": method,
            "why_required": why,
            "required_before_scientific_admission": "yes",
        }
        for name, source, method, why in rows
    ]


def failure_modes() -> list[dict[str, object]]:
    return [
        {"failure_mode": "preflight_failed", "detect_by": "runtime_preflight overall_ok false", "action": "inspect patch audit; repair staging logic; no automatic resubmit"},
        {"failure_mode": "solver_crash", "detect_by": "FOAM FATAL or Slurm nonzero exit", "action": "record failed phase and first fatal stack; decide repair separately"},
        {"failure_mode": "running_too_long", "detect_by": "running without retained-window movement", "action": "monitor latest Time and window drift; do not cancel without explicit decision"},
        {"failure_mode": "drifting_terminal_window", "detect_by": "terminal but mdot/heat/T windows drift", "action": "classify diagnostic only; continue or rerun only after admission review"},
        {"failure_mode": "terminal_success", "detect_by": "scheduler completed and logs have final written times", "action": "claim extraction task and harvest required QoIs"},
    ]


def command_plan() -> str:
    return """# Postprocess Command Plan

Do not run these while jobs `3299610` or `3299620` are still running.

1. Refresh scheduler state:

```bash
ssh login1 squeue -j 3299610,3299620
ssh login1 sacct -j 3299610,3299620
```

2. If a job is terminal and successful, claim a new extraction task before any
native-output reads that create postProcessing artifacts.

3. Required extraction products for each case:

- matched upcomer planes: `U`, `T`, `rho`, and wall-band/core samples
- wall/source fields: `wallHeatFlux` and patch-integrated heat ledger
- derived dimensionless rows: `Re`, `Pr`, `Ri`, `Gr`, `Ra`, `Gz`
- recirculation rows: reverse area fraction, reverse mass fraction, secondary velocity fraction
- terminal-window rows: mdot, heat residual, T probes, wall-T probes
- uncertainty rows: time-window UQ immediately; mesh/GCI only after endpoint selection

4. Admission rule:

Rows with material reverse flow remain onset/recirculation evidence. Do not use
them as ordinary single-stream upcomer `Nu`, `f_D`, or component `K` fits.
"""


def source_manifest(cases: list[dict[str, str]]) -> list[dict[str, object]]:
    paths = [
        CAMPAIGN / "high_heat_probe_manifest.csv",
        CAMPAIGN / "high_heat_bracket_pack_manifest.csv",
        CAMPAIGN / "slurm-salt4_q3x_probe-3299610.out",
        CAMPAIGN / "slurm-salt4_heat_pack-3299620.out",
        CAMPAIGN / "logs/runtime_preflight_3299610.csv",
        CAMPAIGN / "logs/bracket_runtime_preflight_3299620.csv",
        ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/required_output_contract.csv",
    ]
    paths.extend(runtime_for(row).foam_log for row in cases)
    return [
        {
            "source_path": rel(path),
            "exists": path.exists(),
            "role": "input_or_live_log",
        }
        for path in paths
    ]


def write_readme(summary: dict[str, object], output_dir: Path = OUT) -> None:
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_probe_manifest.csv
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_bracket_pack_manifest.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/
tags: [high-heat, recirculation, cfd-harvest, live-monitor]
related:
  - .agent/status/2026-07-17_AGENT-485.md
  - .agent/journal/2026-07-17/high-heat-harvest-readiness-and-live-monitor.md
task: {TASK}
date: {DATE}
role: cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# High-Heat Harvest Readiness And Live Monitor

This package indexes the running Salt4 high-heat jobs and defines what to do
when they become terminal. It does not extract native solver outputs and does
not submit, cancel, or stage jobs.

## Current Summary

- Jobs monitored: `{summary["job_count"]}`.
- Cases indexed: `{summary["case_count"]}`.
- Cases harvest-ready now: `{summary["terminal_ready_count"]}`.
- Running/not terminal cases: `{summary["running_not_terminal_count"]}`.
- Scheduler action: `{summary["scheduler_action"]}`.

## Outputs

- `live_job_status.csv`
- `high_heat_case_index.csv`
- `harvest_readiness_queue.csv`
- `required_qoi_contract.csv`
- `postprocess_command_plan.md`
- `failure_modes_and_actions.csv`
- `source_manifest.csv`
- `scheduler_query_diagnostics.json`
- `summary.json`

## Rule

If a case is still `running_not_terminal`, monitor only. Claim a separate
extraction task before running any terminal harvest or postprocessing.
""",
        encoding="utf-8",
    )


def build(no_scheduler: bool = False, output_dir: Path = OUT) -> dict[str, object]:
    SCHEDULER_DIAGNOSTICS.clear()
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = load_cases()
    sched = scheduler_rows(no_scheduler=no_scheduler)
    live_rows = live_job_status(cases, sched)
    index_rows = case_index(cases)
    queue_rows = harvest_queue(cases, sched)
    qoi_rows = required_qoi_contract()

    write_csv(output_dir / "live_job_status.csv", live_rows)
    write_csv(output_dir / "high_heat_case_index.csv", index_rows)
    write_csv(output_dir / "harvest_readiness_queue.csv", queue_rows)
    write_csv(output_dir / "required_qoi_contract.csv", qoi_rows)
    write_csv(output_dir / "failure_modes_and_actions.csv", failure_modes())
    write_csv(output_dir / "source_manifest.csv", source_manifest(cases))
    (output_dir / "postprocess_command_plan.md").write_text(command_plan(), encoding="utf-8")
    (output_dir / "scheduler_query_diagnostics.json").write_text(
        json.dumps(SCHEDULER_DIAGNOSTICS, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "task": TASK,
        "job_count": len(JOB_IDS),
        "case_count": len(cases),
        "terminal_ready_count": sum(row["harvest_readiness"] == "terminal_ready_for_harvest" for row in queue_rows),
        "running_not_terminal_count": sum(row["harvest_readiness"] == "running_not_terminal" for row in queue_rows),
        "scheduler_action": "read_only_status_check" if not no_scheduler else "none_disabled_for_test",
        "native_output_mutation": "none",
        "required_output_count": len(qoi_rows),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary, output_dir)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-scheduler", action="store_true", help="Do not query login-node scheduler state.")
    parser.add_argument("--output-dir", default=str(OUT), help="Directory for generated high-heat monitor artifacts.")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    summary = build(no_scheduler=args.no_scheduler, output_dir=output_dir)
    print(f"Wrote {output_dir}")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
