#!/usr/bin/env python3
"""Build terminal harvest/admission review tables for ended steady Salt1 jobs.

Reusable entry point:

    python3.11 tools/analyze/build_terminal_harvest_admission_review.py

The script consumes the AGENT-280 final-window metrics and inspects staged case
directories read-only for logs and postProcessing coverage. It does not mutate
solver outputs or submit postprocessing work.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "AGENT-283"
DEFAULT_INPUT = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_salt1_terminal_harvest_admission_review"
)
TARGET_CASES = ("salt1_nominal", "salt1_lo10q", "salt1_hi10q")
EXCLUDED_CASES = {"salt4_hi10q": "not steady in AGENT-280; continued in packed job 3293441"}
REQUIRED_POSTPROCESSING = (
    "mdot_pipeleg_left_04_test_section",
    "mdot_pipeleg_lower_05_straight",
    "mdot_pipeleg_right_02_middle",
    "mdot_pipeleg_upper_05_cooler",
    "temperature_probes",
    "wall_temperature_probes",
)
ADMIT_MDOT_REL_DRIFT_MAX = 5.0e-6
ADMIT_TEMP_DRIFT_MAX_K = 1.0e-9
ADMIT_TOTAL_Q_ABS_DRIFT_MAX_W = 1.0e-9


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_value(row.get(key)) for key in fieldnames})


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def number(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def group_by_case(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_id"]].append(row)
    return dict(grouped)


def case_root(rows: list[dict[str, str]]) -> Path:
    if not rows:
        raise ValueError("Cannot infer case root from empty metric rows")
    return ROOT / rows[0]["source_case_path"]


def tail_lines(path: Path, max_lines: int = 80) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-max_lines:]


def terminal_hint(lines: list[str]) -> str:
    text = "\n".join(lines).lower()
    if "finalising parallel run" in text or "end" in text and "executiontime" in text:
        return "openfoam_terminal_tail"
    if "cancel" in text or "signal" in text:
        return "cancel_or_signal_tail"
    if any("executiontime" in line.lower() for line in lines):
        return "solver_progress_tail"
    return "no_terminal_token_seen"


def find_slurm_logs(case_id: str, job_step: str, case_path: Path) -> list[Path]:
    job_id = job_step.split(".", 1)[0]
    roots = [case_path]
    roots.extend(case_path.parents[:5])
    matches: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for pattern in (f"*{job_id}*.out", f"*{job_id}*.err", f"slurm-*{job_id}*"):
            matches.extend(path for path in root.glob(pattern) if path.is_file())
    return sorted(set(matches))


def build_scheduler_review(grouped: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_id in TARGET_CASES:
        metrics = grouped.get(case_id, [])
        if not metrics:
            rows.append({"case_id": case_id, "review_status": "missing_final_window_metrics"})
            continue
        first = metrics[0]
        stop_state = first["stop_state"]
        terminal = stop_state.startswith("CANCELLED") or stop_state in {"COMPLETED", "FAILED", "TIMEOUT"}
        rows.append(
            {
                "case_id": case_id,
                "slurm_job_or_step": first["slurm_job_or_step"],
                "recorded_stop_state": stop_state,
                "terminal_state_recorded": "yes" if terminal else "no",
                "decision_from_agent280": first["decision"],
                "scheduler_review": "terminal_recorded_from_agent280" if terminal else "not_terminal_in_agent280",
                "source": "AGENT-280 final_window_metrics.csv",
            }
        )
    return rows


def build_log_review(grouped: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_id in TARGET_CASES:
        metrics = grouped.get(case_id, [])
        if not metrics:
            rows.append({"case_id": case_id, "log_status": "missing_final_window_metrics"})
            continue
        root = case_root(metrics)
        log_dir = root / "logs"
        local_logs = sorted(log_dir.glob("log.*")) if log_dir.exists() else []
        slurm_logs = find_slurm_logs(case_id, metrics[0]["slurm_job_or_step"], root)
        reviewed = local_logs + slurm_logs
        if not reviewed:
            rows.append(
                {
                    "case_id": case_id,
                    "source_case_path": rel(root),
                    "log_status": "no_logs_found",
                    "log_file_count": 0,
                    "terminal_hint": "not_checked",
                }
            )
            continue
        for path in reviewed:
            lines = tail_lines(path)
            last_nonempty = next((line for line in reversed(lines) if line.strip()), "")
            rows.append(
                {
                    "case_id": case_id,
                    "slurm_job_or_step": metrics[0]["slurm_job_or_step"],
                    "source_case_path": rel(root),
                    "log_path": rel(path),
                    "log_file_count": len(reviewed),
                    "line_tail_count": len(lines),
                    "terminal_hint": terminal_hint(lines),
                    "last_nonempty_tail_line": last_nonempty[:240],
                    "log_status": "reviewed",
                }
            )
    return rows


def numeric_child_dirs(path: Path) -> list[float]:
    values: list[float] = []
    if not path.exists():
        return values
    for child in path.iterdir():
        if not child.is_dir():
            continue
        try:
            values.append(float(child.name))
        except ValueError:
            continue
    return sorted(values)


def build_postprocessing_review(grouped: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_id in TARGET_CASES:
        metrics = grouped.get(case_id, [])
        if not metrics:
            rows.append({"case_id": case_id, "postprocessing_status": "missing_final_window_metrics"})
            continue
        root = case_root(metrics)
        pp = root / "postProcessing"
        present = {child.name for child in pp.iterdir() if child.is_dir()} if pp.exists() else set()
        missing = [name for name in REQUIRED_POSTPROCESSING if name not in present]
        top_count = len(present)
        latest_family_time = ""
        latest_values: list[float] = []
        for family in present:
            latest_values.extend(numeric_child_dirs(pp / family))
        if latest_values:
            latest_family_time = f"{max(latest_values):.12g}"
        rows.append(
            {
                "case_id": case_id,
                "slurm_job_or_step": metrics[0]["slurm_job_or_step"],
                "source_case_path": rel(root),
                "postprocessing_path": rel(pp),
                "postprocessing_exists": "yes" if pp.exists() else "no",
                "top_level_family_count": top_count,
                "required_families_present": "yes" if not missing and pp.exists() else "no",
                "missing_required_families": ";".join(missing),
                "latest_numeric_family_time_s": latest_family_time,
                "postprocessing_status": "harvest_inputs_present" if not missing and pp.exists() else "incomplete_review",
                "families_present": ";".join(sorted(present)),
            }
        )
    return rows


def aggregate_final_window(rows: list[dict[str, str]]) -> dict[str, object]:
    metrics = {row["quantity"]: row for row in rows}
    total_q_drift = number(metrics.get("total_Q_W", {}).get("drift")) or 0.0
    mdot_rel_drifts = [
        abs(value)
        for row in rows
        if row["quantity"].startswith("mdot_")
        for value in [number(row.get("relative_drift"))]
        if value is not None
    ]
    mdot_rel_spans = [
        abs(value)
        for row in rows
        if row["quantity"].startswith("mdot_")
        for value in [number(row.get("relative_span"))]
        if value is not None
    ]
    temp_drift = abs(number(metrics.get("temperature_probes_max_abs_drift_K", {}).get("drift")) or 0.0)
    wall_drift = abs(number(metrics.get("wall_temperature_probes_max_abs_drift_K", {}).get("drift")) or 0.0)
    return {
        "window_start_s": number(rows[0].get("window_start_s")),
        "window_end_s": number(rows[0].get("window_end_s")),
        "total_Q_drift_W": total_q_drift,
        "max_mdot_relative_drift": max(mdot_rel_drifts) if mdot_rel_drifts else None,
        "max_mdot_relative_span": max(mdot_rel_spans) if mdot_rel_spans else None,
        "temperature_probe_max_abs_drift_K": temp_drift,
        "wall_temperature_probe_max_abs_drift_K": wall_drift,
    }


def admission_label(agg: dict[str, object]) -> tuple[str, str]:
    mdot_ok = (agg["max_mdot_relative_drift"] is not None) and (
        float(agg["max_mdot_relative_drift"]) <= ADMIT_MDOT_REL_DRIFT_MAX
    )
    total_q_ok = abs(float(agg["total_Q_drift_W"])) <= ADMIT_TOTAL_Q_ABS_DRIFT_MAX_W
    temp_ok = float(agg["temperature_probe_max_abs_drift_K"]) <= ADMIT_TEMP_DRIFT_MAX_K
    wall_ok = float(agg["wall_temperature_probe_max_abs_drift_K"]) <= ADMIT_TEMP_DRIFT_MAX_K
    if mdot_ok and total_q_ok and temp_ok and wall_ok:
        return (
            "terminal_window_stationary_cancelled",
            "terminal_harvest_complete_context_only",
        )
    return ("not_admitted_missing_evidence", "not_admitted_missing_evidence")


def build_final_window_review(grouped: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_id in TARGET_CASES:
        metrics = grouped.get(case_id, [])
        if not metrics:
            rows.append({"case_id": case_id, "stationarity_label": "not_admitted_missing_evidence"})
            continue
        agg = aggregate_final_window(metrics)
        stationarity_label, harvest_label = admission_label(agg)
        rows.append(
            {
                "case_id": case_id,
                "slurm_job_or_step": metrics[0]["slurm_job_or_step"],
                "source_case_path": metrics[0]["source_case_path"],
                "window_start_s": agg["window_start_s"],
                "window_end_s": agg["window_end_s"],
                "total_Q_drift_W": agg["total_Q_drift_W"],
                "max_mdot_relative_drift": agg["max_mdot_relative_drift"],
                "max_mdot_relative_span": agg["max_mdot_relative_span"],
                "temperature_probe_max_abs_drift_K": agg["temperature_probe_max_abs_drift_K"],
                "wall_temperature_probe_max_abs_drift_K": agg["wall_temperature_probe_max_abs_drift_K"],
                "stationarity_label": stationarity_label,
                "harvest_label": harvest_label,
                "closure_fit_admission": "not_changed_by_this_review",
                "notes": metrics[0].get("notes", ""),
            }
        )
    return rows


def build_decision_table(
    scheduler_rows: list[dict[str, object]],
    pp_rows: list[dict[str, object]],
    window_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    scheduler = {row["case_id"]: row for row in scheduler_rows}
    pp = {row["case_id"]: row for row in pp_rows}
    window = {row["case_id"]: row for row in window_rows}
    rows: list[dict[str, object]] = []
    for case_id in TARGET_CASES:
        w = window.get(case_id, {})
        p = pp.get(case_id, {})
        s = scheduler.get(case_id, {})
        terminal_ok = s.get("terminal_state_recorded") == "yes"
        pp_ok = p.get("postprocessing_status") == "harvest_inputs_present"
        stationary_ok = w.get("stationarity_label") == "terminal_window_stationary_cancelled"
        if terminal_ok and pp_ok and stationary_ok:
            decision = "terminal_harvest_complete_context_only"
        else:
            decision = "not_admitted_missing_evidence"
        rows.append(
            {
                "case_id": case_id,
                "slurm_job_or_step": s.get("slurm_job_or_step", w.get("slurm_job_or_step", "")),
                "terminal_state_recorded": s.get("terminal_state_recorded", "no"),
                "postprocessing_status": p.get("postprocessing_status", ""),
                "stationarity_label": w.get("stationarity_label", ""),
                "admission_decision": decision,
                "closure_fit_admission": "not_changed_by_this_review",
                "recommended_use": "use as terminal steady-state context; closure-fit admission still needs Salt1 policy",
            }
        )
    for case_id, reason in sorted(EXCLUDED_CASES.items()):
        rows.append(
            {
                "case_id": case_id,
                "admission_decision": "excluded_not_steady_or_live",
                "closure_fit_admission": "not_changed_by_this_review",
                "recommended_use": reason,
            }
        )
    return rows


def make_readme(summary: dict[str, object]) -> str:
    return f"""# Salt1 Terminal Harvest Admission Review

Task: `{TASK_ID}`

Generated: `{summary['generated_at']}`

## Purpose

This package performs the terminal scheduler/log/postProcessing/admission review
for ended Salt1 rows that AGENT-280 found essentially steady. It is a harvest
review, not a registry or closure-fit promotion.

## Scope

Included rows: `salt1_nominal`, `salt1_lo10q`, and `salt1_hi10q`.

Excluded row: `salt4_hi10q`, because AGENT-280 found it not steady and AGENT-274
continued it in packed job `3293441`.

## Outputs

- `scheduler_terminal_review.csv`: terminal state recorded from AGENT-280.
- `log_tail_review.csv`: read-only local solver/slurm log inventory and tail
  hints.
- `postprocessing_availability.csv`: postProcessing family coverage and latest
  numeric family time.
- `final_window_admission_review.csv`: final-window drift metrics collapsed to
  one row per Salt1 case.
- `admission_decision_table.csv`: compact harvest/admission decision table.
- `summary.json`: counts, thresholds, and source paths.

## Decision Boundary

`terminal_harvest_complete_context_only` means the ended row has terminal state,
postProcessing coverage, and a stationary final window. It does not change
closure-fit admission, registry state, or the Salt1 policy caveat.

## Reproduce

```bash
python3.11 tools/analyze/build_terminal_harvest_admission_review.py
python3.11 -m unittest tools.analyze.test_terminal_harvest_admission_review
```
"""


def build_package(input_path: Path, output_dir: Path) -> dict[str, object]:
    source_rows = read_csv(input_path)
    grouped_all = group_by_case(source_rows)
    grouped = {case_id: grouped_all.get(case_id, []) for case_id in TARGET_CASES}

    scheduler_rows = build_scheduler_review(grouped)
    log_rows = build_log_review(grouped)
    pp_rows = build_postprocessing_review(grouped)
    window_rows = build_final_window_review(grouped)
    decision_rows = build_decision_table(scheduler_rows, pp_rows, window_rows)

    write_csv(
        output_dir / "scheduler_terminal_review.csv",
        scheduler_rows,
        [
            "case_id",
            "slurm_job_or_step",
            "recorded_stop_state",
            "terminal_state_recorded",
            "decision_from_agent280",
            "scheduler_review",
            "source",
        ],
    )
    write_csv(
        output_dir / "log_tail_review.csv",
        log_rows,
        [
            "case_id",
            "slurm_job_or_step",
            "source_case_path",
            "log_path",
            "log_file_count",
            "line_tail_count",
            "terminal_hint",
            "last_nonempty_tail_line",
            "log_status",
        ],
    )
    write_csv(
        output_dir / "postprocessing_availability.csv",
        pp_rows,
        [
            "case_id",
            "slurm_job_or_step",
            "source_case_path",
            "postprocessing_path",
            "postprocessing_exists",
            "top_level_family_count",
            "required_families_present",
            "missing_required_families",
            "latest_numeric_family_time_s",
            "postprocessing_status",
            "families_present",
        ],
    )
    write_csv(
        output_dir / "final_window_admission_review.csv",
        window_rows,
        [
            "case_id",
            "slurm_job_or_step",
            "source_case_path",
            "window_start_s",
            "window_end_s",
            "total_Q_drift_W",
            "max_mdot_relative_drift",
            "max_mdot_relative_span",
            "temperature_probe_max_abs_drift_K",
            "wall_temperature_probe_max_abs_drift_K",
            "stationarity_label",
            "harvest_label",
            "closure_fit_admission",
            "notes",
        ],
    )
    write_csv(
        output_dir / "admission_decision_table.csv",
        decision_rows,
        [
            "case_id",
            "slurm_job_or_step",
            "terminal_state_recorded",
            "postprocessing_status",
            "stationarity_label",
            "admission_decision",
            "closure_fit_admission",
            "recommended_use",
        ],
    )

    counts = Counter(row["admission_decision"] for row in decision_rows)
    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input": rel(input_path),
        "output_dir": rel(output_dir),
        "target_cases": list(TARGET_CASES),
        "excluded_cases": EXCLUDED_CASES,
        "thresholds": {
            "max_mdot_relative_drift": ADMIT_MDOT_REL_DRIFT_MAX,
            "max_total_Q_abs_drift_W": ADMIT_TOTAL_Q_ABS_DRIFT_MAX_W,
            "max_temperature_abs_drift_K": ADMIT_TEMP_DRIFT_MAX_K,
        },
        "decision_counts": dict(sorted(counts.items())),
        "terminal_harvest_complete_context_only_count": counts["terminal_harvest_complete_context_only"],
        "native_solver_outputs_mutated": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(make_readme(summary), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_package(Path(args.input), Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
