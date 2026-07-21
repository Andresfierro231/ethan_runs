#!/usr/bin/env python3
"""Build a run-status and frozen-window inventory for recent CFD jobs.

This is the reusable version of the July 4 manual triage:

1. Read packed-job Slurm stdout lines of the form
   ``Prepared <label> from <case_dir> at restart time <time>``.
2. Run the monitor-based convergence assessor on each case directory.
3. Apply the operating-point movement gate for Salt Q perturbations.
4. Emit per-case and per-job recommendations for post-processing.

The script is read-only with respect to case directories. It reads native
``postProcessing`` monitor histories and writes a small report under
``work_products/``.
"""
from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.analyze import assess_time_convergence as atc

DEFAULT_OUTPUT_DIR = ROOT / "work_products/2026-07-04_postprocessing_run_status_and_next_steps"
DEFAULT_JOB_LOGS = [
    ROOT / "tmp/2026-06-26_nuclearenergy_repack_followon/slurm-ethan_s34mid_ne5d-3265969.out",
    ROOT / "tmp/2026-06-26_nuclearenergy_repack_followon/slurm-ethan_w1234_ne5d-3265970.out",
    ROOT / "tmp/2026-06-26_nuclearenergy_repack_followon/slurm-ethan_s41lo2mid_ne5d-3265971.out",
    ROOT / "tmp/2026-06-26_nuclearenergy_repack_followon/slurm-ethan_s123hi_ne5d-3265972.out",
]

# Baselines recorded in .agent/journal/2026-07-01/T3-perturbation-requalification.md.
SALT_NOMINAL_MDOT = {
    "salt1": -0.01124,
    "salt2": -0.01320,
    "salt3": -0.01499,
    "salt4": -0.01712,
}
SALT_NOMINAL_Q_W = {
    "salt1": 232.3,
    "salt2": 265.7,
    "salt3": 297.5,
    "salt4": 337.6,
}

PREPARED_RE = re.compile(r"^Prepared\s+(\S+)\s+from\s+(.+?)\s+at restart time\s+(\S+)\s*$")
JOB_RE = re.compile(r"slurm-(?P<name>.+)-(?P<jobid>\d+)\.out$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--job-log",
        action="append",
        default=[],
        help="Packed-job stdout log. May be supplied multiple times. Defaults to the June 26 repack logs.",
    )
    parser.add_argument("--no-sacct", action="store_true", help="Skip sacct state lookup.")
    parser.add_argument(
        "--job-state",
        action="append",
        default=[],
        metavar="JOBID=STATE",
        help="Override scheduler state for a job, useful when sacct is unavailable inside Python.",
    )
    parser.add_argument(
        "--tau-thermal",
        type=float,
        default=5000.0,
        help="Thermal time constant used only for advance/tau reporting in the operating-point gate.",
    )
    return parser.parse_args()


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def safe_float(value: Any, default: float = math.nan) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def parse_job_identity(path: Path) -> tuple[str, str]:
    match = JOB_RE.search(path.name)
    if not match:
        return "", path.stem
    return match.group("jobid"), match.group("name")


def parse_prepared_cases(path: Path) -> list[dict[str, Any]]:
    job_id, job_name = parse_job_identity(path)
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = PREPARED_RE.match(line)
        if not match:
            continue
        label, case_dir, restart = match.groups()
        rows.append(
            {
                "job_id": job_id,
                "job_name": job_name,
                "slurm_stdout": relative_to_workspace(path),
                "case_label": label,
                "case_dir": str(Path(case_dir)),
                "restart_time_s": safe_float(restart),
            }
        )
    return rows


def query_sacct(job_ids: list[str]) -> dict[str, dict[str, str]]:
    if not job_ids:
        return {}
    cmd = [
        "sacct",
        "-j",
        ",".join(job_ids),
        "--format=JobID,JobName%40,State,ExitCode,Start,End,Elapsed,NodeList",
        "-X",
        "--parsable2",
        "--noheader",
    ]
    try:
        proc = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if proc.returncode != 0:
        return {}
    out: dict[str, dict[str, str]] = {}
    for line in proc.stdout.splitlines():
        parts = line.split("|")
        if len(parts) < 8:
            continue
        job_id = parts[0].split(".")[0]
        out[job_id] = {
            "job_name_sacct": parts[1].strip(),
            "job_state": parts[2].strip(),
            "exit_code": parts[3].strip(),
            "job_start": parts[4].strip(),
            "job_end": parts[5].strip(),
            "job_elapsed": parts[6].strip(),
            "node_list": parts[7].strip(),
        }
    return out


def parse_job_state_overrides(items: list[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for item in items:
        if "=" not in item:
            continue
        job_id, state = item.split("=", 1)
        out[job_id.strip()] = {"job_state": state.strip()}
    return out


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_case_config(case_dir: Path) -> dict[str, Any]:
    text = read_text(case_dir / "case_config.yaml")
    out: dict[str, Any] = {"heater_power_w": math.nan, "insulated_h": math.nan}
    patterns = {
        "heater_power_w": r"(?m)^\s*heater_power_W:\s*([-+0-9.eE]+)",
        "insulated_h": r"(?m)^\s*insulated:\s*\n\s*h:\s*([-+0-9.eE]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            out[key] = safe_float(match.group(1))
    out["has_insulation_perturbation_block"] = "insulation_perturbation:" in text
    return out


def parse_end_time(case_dir: Path) -> float:
    text = read_text(case_dir / "system" / "controlDict")
    match = re.search(r"(?m)^\s*endTime\s+([-+0-9.eE]+)\s*;", text)
    return safe_float(match.group(1)) if match else math.nan


def salt_key(label: str, case_dir: str) -> str:
    match = re.search(r"salt([1-4])", f"{label} {case_dir}")
    return f"salt{match.group(1)}" if match else ""


def run_family(label: str, case_dir: str, config: dict[str, Any]) -> str:
    if "water" in label.lower() or "water" in case_dir.lower():
        return "water_continuation"
    if config.get("has_insulation_perturbation_block") or re.search(r"(hiins|loins).*(loH|hiH)", label):
        return "salt_true_insulation_perturbation"
    if re.search(r"(hiq|loq|hi5q|lo5q|hiins|loins|balq)", label):
        return "salt_q_perturbation"
    if "basecont" in label or "continuation" in case_dir:
        return "nominal_or_continuation"
    return "unclassified"


def monitor_ref(result: dict[str, Any]) -> dict[str, Any]:
    for monitor in result.get("monitors", []):
        if (
            monitor.get("monitor") == "mdot::mdot_pipeleg_left_04_test_section"
            and monitor.get("status") == "assessed"
        ):
            return monitor
    for monitor in result.get("monitors", []):
        if monitor.get("role") == "hydraulic" and monitor.get("status") == "assessed":
            return monitor
    return {}


def assess_row(row: dict[str, Any], tau_thermal: float) -> dict[str, Any]:
    case_dir = Path(row["case_dir"])
    config = parse_case_config(case_dir)
    family = run_family(row["case_label"], row["case_dir"], config)
    skey = salt_key(row["case_label"], row["case_dir"])
    q_ratio = math.nan
    if skey in SALT_NOMINAL_Q_W and finite(config.get("heater_power_w")):
        q_ratio = float(config["heater_power_w"]) / SALT_NOMINAL_Q_W[skey]

    args = argparse.Namespace(
        source_id=row["case_label"],
        window_frac=0.25,
        stationary_drift=0.01,
        stationary_amp=0.02,
        quasi_drift=0.05,
        quasi_amp=0.10,
        require_moved_from=None,
        expected_q_ratio=None,
        expected_move_frac=None,
        move_tolerance=0.5,
        tau_thermal=tau_thermal,
        min_tau_advance=3.0,
    )
    if family == "salt_q_perturbation" and skey in SALT_NOMINAL_MDOT and finite(q_ratio) and abs(q_ratio - 1.0) > 0.005:
        args.require_moved_from = SALT_NOMINAL_MDOT[skey]
        args.expected_q_ratio = q_ratio

    result = atc.assess_case(row["case_label"], case_dir, args)
    mdot = monitor_ref(result)
    op = result.get("operating_point", {})
    latest = safe_float(mdot.get("t_end_s"))
    restart = safe_float(row.get("restart_time_s"))
    advance = latest - restart if finite(latest) and finite(restart) else math.nan
    end_time = parse_end_time(case_dir)

    op_verdict = op.get("verdict", "")
    pct_moved = safe_float(op.get("pct_moved")) * 100.0 if op else math.nan
    expected_move_pct = safe_float(op.get("expected_move_frac")) * 100.0 if op else math.nan

    admissible = "no"
    recommendation = "investigate"
    reason = ""
    if family == "salt_q_perturbation":
        if op_verdict == "requalified":
            admissible = "yes"
            recommendation = "postprocess_for_closure"
            reason = "Q perturbation moved and re-plateaued."
        else:
            admissible = "no"
            recommendation = "document_only_false_steady"
            reason = f"Q perturbation operating-point gate = {op_verdict or 'not_applied'}."
    elif family == "water_continuation":
        admissible = "provisional" if result.get("case_verdict") in ("stationary", "quasi_stationary") else "no"
        recommendation = "wait_for_job_exit_then_freeze" if row.get("job_state") == "RUNNING" else "freeze_and_postprocess_water"
        reason = "Water continuation is useful after final window is frozen."
    elif family == "nominal_or_continuation":
        admissible = "yes" if result.get("case_verdict") in ("stationary", "quasi_stationary") else "provisional"
        recommendation = "postprocess_if_needed"
        reason = "Nominal/continuation case; use with stated convergence caveat."
    elif family == "salt_true_insulation_perturbation":
        admissible = "provisional"
        recommendation = "apply_insulation_specific_gate"
        reason = "Insulation perturbation needs moved-vs-baseline and wall-delta-T gate."
    else:
        reason = "Unclassified run family."

    assessed = {
        **row,
        "case_dir": relative_to_workspace(case_dir),
        "run_family": family,
        "salt_key": skey,
        "heater_power_w": config.get("heater_power_w"),
        "q_ratio_vs_nominal": q_ratio,
        "end_time_s": end_time,
        "latest_monitor_time_s": latest,
        "advance_since_restart_s": advance,
        "case_verdict": result.get("case_verdict", ""),
        "hydraulic_verdict": result.get("hydraulic_verdict", ""),
        "thermal_verdict": result.get("thermal_verdict", ""),
        "mdot_window_mean": mdot.get("window_mean", math.nan),
        "mdot_drift_pct": safe_float(mdot.get("drift_frac_of_mean")) * 100.0,
        "mdot_amp_pct": safe_float(mdot.get("amp_frac_of_mean")) * 100.0,
        "gross_wall_duty_w": result.get("gross_wall_duty_w", math.nan),
        "heat_closure_net_over_gross_pct": safe_float(result.get("heat_closure_net_over_gross")) * 100.0,
        "operating_point_verdict": op_verdict,
        "mdot_moved_pct": pct_moved,
        "expected_move_pct": expected_move_pct,
        "advance_over_tau": op.get("advance_over_tau", math.nan),
        "closure_fit_admissible": admissible,
        "recommendation": recommendation,
        "recommendation_reason": reason,
    }
    return assessed


def build_markdown(rows: list[dict[str, Any]], job_rows: list[dict[str, Any]]) -> str:
    counts = Counter(row["recommendation"] for row in rows)
    lines = [
        "# Post-Processing Run Status Inventory",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## Job Summary",
        "",
        "| job | state | cases | job recommendation |",
        "| --- | --- | ---: | --- |",
    ]
    for job in job_rows:
        lines.append(
            f"| `{job['job_id']}` `{job['job_name']}` | `{job.get('job_state', 'unknown')}` | "
            f"{job['case_count']} | `{job['job_recommendation']}` |"
        )
    lines.extend(["", "## Recommendation Counts", ""])
    for key, value in sorted(counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Salt Q perturbations are closure-fit admissible only when the operating-point gate returns `requalified`.",
            "- Running Water cases should be frozen and reprocessed after the Slurm job exits.",
            "- This inventory is monitor-based; field reconstruction/extraction remains a separate Slurm/dev-node workflow.",
        ]
    )
    return "\n".join(lines) + "\n"


def summarize_jobs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["job_id"]].append(row)
    out: list[dict[str, Any]] = []
    for job_id, items in sorted(grouped.items()):
        recs = Counter(item["recommendation"] for item in items)
        state = items[0].get("job_state", "unknown")
        if all(item["recommendation"] == "document_only_false_steady" for item in items):
            job_rec = "no_more_runtime_needed_document_only"
        elif any(item["run_family"] == "water_continuation" for item in items):
            if state == "RUNNING":
                job_rec = "let_water_finish_then_freeze"
            else:
                job_rec = "freeze_and_postprocess_water"
        elif (
            any(item["recommendation"] == "postprocess_if_needed" for item in items)
            and any(item["recommendation"] == "document_only_false_steady" for item in items)
        ):
            job_rec = "postprocess_nominal_only_document_false_steady"
        elif any(item["recommendation"] == "postprocess_for_closure" for item in items):
            job_rec = "postprocess_requalified_cases"
        else:
            job_rec = "review_case_mix"
        out.append(
            {
                "job_id": job_id,
                "job_name": items[0].get("job_name", ""),
                "job_state": state,
                "case_count": len(items),
                "recommendation_counts": dict(recs),
                "job_recommendation": job_rec,
            }
        )
    return out


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    logs = [Path(item) for item in args.job_log] if args.job_log else DEFAULT_JOB_LOGS

    prepared: list[dict[str, Any]] = []
    for log in logs:
        prepared.extend(parse_prepared_cases(log))
    job_ids = sorted({row["job_id"] for row in prepared if row.get("job_id")})
    sacct = {} if args.no_sacct else query_sacct(job_ids)
    overrides = parse_job_state_overrides(args.job_state)
    for row in prepared:
        row.update(sacct.get(row["job_id"], {}))
        row.update(overrides.get(row["job_id"], {}))
        row.setdefault("job_state", "unknown")

    assessed = [assess_row(row, args.tau_thermal) for row in prepared]
    job_summary = summarize_jobs(assessed)

    fields = [
        "job_id",
        "job_name",
        "job_state",
        "case_label",
        "run_family",
        "salt_key",
        "case_dir",
        "restart_time_s",
        "latest_monitor_time_s",
        "advance_since_restart_s",
        "end_time_s",
        "case_verdict",
        "hydraulic_verdict",
        "thermal_verdict",
        "mdot_window_mean",
        "mdot_drift_pct",
        "mdot_amp_pct",
        "gross_wall_duty_w",
        "heat_closure_net_over_gross_pct",
        "heater_power_w",
        "q_ratio_vs_nominal",
        "operating_point_verdict",
        "mdot_moved_pct",
        "expected_move_pct",
        "advance_over_tau",
        "closure_fit_admissible",
        "recommendation",
        "recommendation_reason",
        "slurm_stdout",
    ]
    csv_dump(output_dir / "run_status_inventory.csv", fields, assessed)
    csv_dump(
        output_dir / "job_status_summary.csv",
        ["job_id", "job_name", "job_state", "case_count", "recommendation_counts", "job_recommendation"],
        job_summary,
    )
    json_dump(
        output_dir / "run_status_inventory.json",
        {
            "generated_at": iso_timestamp(),
            "method": "packed Slurm stdout + assess_time_convergence monitor gate + Salt Q operating-point gate",
            "job_logs": [relative_to_workspace(path) for path in logs],
            "cases": assessed,
            "jobs": job_summary,
        },
    )
    (output_dir / "README.md").write_text(build_markdown(assessed, job_summary), encoding="utf-8")

    print(f"Wrote {relative_to_workspace(output_dir / 'run_status_inventory.csv')}")
    for job in job_summary:
        print(f"{job['job_id']} {job['job_name']}: {job['job_recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
