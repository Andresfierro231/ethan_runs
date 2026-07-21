#!/usr/bin/env python3
"""Build a consolidated submitted CFD run steady-state table.

This script is intentionally a lightweight evidence joiner, not a CFD
postprocessor.  It reads existing submission ledgers, time-series rollups,
terminal-harvest gates, and admission overlays, then emits a coordinator-facing
table with one label per submitted run:

``steady``
    A final-window detector or time-series rollup found representative series
    steady/quasi-steady.
``needs continuation``
    The row is running, drifting, failed, under-advanced, or has only a prior
    gate that did not establish a terminal current-run steady window.
``not run``
    A submission row exists, but no joined last-window detector output exists.

The label is deliberately separate from closure-fit admission.  A run can be
steady but still blocked by boundary-condition labeling, split policy, pressure
metric extraction, or a Salt-specific operating-point gate.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table"

NORMAL_RELAUNCH_SUBMITTED = REPO_ROOT / "jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/submitted_jobs.csv"
SALT1_NOMINAL_SUBMITTED = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/submitted_jobs.csv"
CORRECTED_SUBMITTED = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/submitted_jobs.csv"
CORRECTED_SELECTED_SUBMITTED = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/selected_submitted_jobs.csv"
TIMESERIES_ROLLUP = REPO_ROOT / "work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/all_timeseries_case_rollup.csv"
PRIMARY_DECISIONS = REPO_ROOT / "work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/primary_cfd_continuation_decisions.csv"
FINAL_WINDOW_METRICS = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv"
CORRECTED_STATUS = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_corrected_q_latest_time_refresh/all_corrected_q_status_table.csv"
CORRECTED_LIVE_GATE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/corrected_q_terminal_gate_rows.csv"
SALT_INVENTORY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/salt_cfd_candidate_inventory.csv"

FINAL_WINDOW_CASE_MAP = {
    "salt1_nominal": "salt1_jin_nominal_continuation_corrected",
    "salt1_lo10q": "salt1_jin_lo10q_corrected",
    "salt1_hi10q": "salt1_jin_hi10q_corrected",
}
MAINLINE_ALIASES = {
    "salt1_jin_nominal_continuation_corrected": "salt1_jin_nominal_continuation",
    "salt2_jin": "salt2_jin_nominal_continuation",
    "salt3_jin": "salt3_jin_nominal_continuation",
    "salt4_jin": "salt4_jin_nominal_continuation",
}
CASE_TOKEN = re.compile(r"^(?:salt|water)[0-9][A-Za-z0-9_]*$")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def _rel(path_or_text: object) -> str:
    text = str(path_or_text)
    try:
        path = Path(text)
    except TypeError:
        return text
    if path.is_absolute():
        try:
            return str(path.relative_to(REPO_ROOT))
        except ValueError:
            return str(path)
    return text


def _add_submission(index: dict[str, dict[str, set[str]]], case_key: str, job_id: str, job_name: str, source: Path) -> None:
    if not case_key or not job_id:
        return
    item = index[case_key]
    item["job_ids"].add(job_id)
    item["job_names"].add(job_name)
    item["submission_sources"].add(_rel(source))


def _submission_index() -> dict[str, dict[str, set[str]]]:
    """Return submitted job ids/names grouped by case key.

    The known submission ledgers do not share one schema.  Normal relaunch rows
    carry two case-key columns, Salt1 nominal uses a single `case_key`, the
    corrected-Q batch ledger is comma-delimited with case tokens before a path,
    and the selected continuation ledger stores semicolon-separated cases.
    This adapter keeps that heterogeneity local so the row builder can operate
    on a single case-key index.
    """
    index: dict[str, dict[str, set[str]]] = defaultdict(lambda: {
        "job_ids": set(),
        "job_names": set(),
        "submission_sources": set(),
    })
    for row in _read_csv(NORMAL_RELAUNCH_SUBMITTED):
        for key in ("case_key_1", "case_key_2"):
            _add_submission(index, row.get(key, ""), row.get("job_id", ""), row.get("job_name", ""), NORMAL_RELAUNCH_SUBMITTED)
    for row in _read_csv(SALT1_NOMINAL_SUBMITTED):
        _add_submission(index, row.get("case_key", ""), row.get("job_id", ""), row.get("job_name", ""), SALT1_NOMINAL_SUBMITTED)
    if CORRECTED_SUBMITTED.exists():
        for line in CORRECTED_SUBMITTED.read_text(encoding="utf-8").splitlines()[1:]:
            if not line.strip():
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            group, job_id = parts[0], parts[1]
            for token in parts[2:]:
                if token.startswith("/"):
                    break
                if CASE_TOKEN.match(token):
                    _add_submission(index, token, job_id, group, CORRECTED_SUBMITTED)
    for row in _read_csv(CORRECTED_SELECTED_SUBMITTED):
        cases = row.get("cases", "")
        for case_key in [item.strip() for item in cases.split(";") if item.strip()]:
            _add_submission(index, case_key, row.get("job_id", ""), row.get("job_name", ""), CORRECTED_SELECTED_SUBMITTED)
    return index


def _query_job_states(job_ids: Iterable[str], query_scheduler: bool) -> dict[str, str]:
    """Query Slurm `sacct` for final job states when requested.

    Tests pass `query_scheduler=False` so the product can be regenerated on
    login shells without live scheduler access.  Scheduler failures are treated
    as missing auxiliary evidence; they do not prevent table generation because
    the durable terminal/steady-state evidence lives in the work products.
    """
    ids = sorted({job_id for job_id in job_ids if job_id})
    if not ids or not query_scheduler:
        return {}
    try:
        result = subprocess.run(
            ["sacct", "-j", ",".join(ids), "--format", "JobID,State", "-P", "-X", "--noheader"],
            check=False,
            capture_output=True,
            encoding="utf-8",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    states: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.split("|")
        if len(parts) >= 2 and "." not in parts[0]:
            states[parts[0]] = parts[1]
    return states


def _final_window_summary() -> dict[str, dict[str, str]]:
    """Collapse explicit stopped-sbatch Salt1 final-window metrics by run key."""
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _read_csv(FINAL_WINDOW_METRICS):
        grouped[row["case_id"]].append(row)
    output: dict[str, dict[str, str]] = {}
    for final_key, case_key in FINAL_WINDOW_CASE_MAP.items():
        rows = grouped.get(final_key, [])
        if not rows:
            continue
        quantities = {row["quantity"]: row for row in rows}
        mdot_drifts = [
            abs(float(row["relative_drift"]))
            for row in rows
            if row["quantity"].startswith("mdot_") and row.get("relative_drift")
        ]
        output[case_key] = {
            "last_window_start_s": rows[0].get("window_start_s", ""),
            "last_window_end_s": rows[0].get("window_end_s", ""),
            "steady_state_detection_status": rows[0].get("decision", ""),
            "mdot_verdict": "steady" if mdot_drifts and max(mdot_drifts) < 1e-5 else "",
            "heat_verdict": "steady" if quantities.get("total_Q_W", {}).get("drift") == "0" else "",
            "steady_label": "steady" if rows[0].get("decision", "").startswith("steady") else "needs continuation",
            "evidence_path": _rel(FINAL_WINDOW_METRICS),
            "notes": rows[0].get("notes", ""),
        }
    return output


def _classify_rollup(row: dict[str, str]) -> tuple[str, str]:
    """Map a time-series rollup row to the public steady/continue label."""
    status = row.get("timeseries_status", "")
    mdot = row.get("mdot_verdict", "")
    heat = row.get("heat_verdict", "")
    if "drifting" in status or "not steady" in mdot or "not steady" in heat:
        return "needs continuation", "last-window detector found drifting series"
    if status in {"all_representative_series_steady", "steady_with_quasi_series"}:
        return "steady", "last-window detector found representative series steady/quasi-steady"
    return "needs continuation", "last-window detector did not establish steady state"


def _variant_for(case_key: str) -> str:
    if "corrected" in case_key:
        match = re.search(r"_(lo|hi)(5|10)q_", case_key)
        return f"{match.group(1)}{match.group(2)}q" if match else "corrected_q"
    if "water" in case_key:
        return "water_continuation"
    if "hi5q" in case_key or "lo5q" in case_key or "hiq" in case_key or "loq" in case_key:
        return "legacy_perturbation"
    if "nominal" in case_key or case_key.endswith("_jin") or "basecont" in case_key:
        return "nominal_or_continuation"
    return "other"


def _family_for(case_key: str, rollup: dict[str, str] | None = None) -> str:
    if rollup and rollup.get("fluid"):
        return rollup["fluid"]
    match = re.search(r"(salt|water)([1-4])", case_key)
    return f"{match.group(1)}{match.group(2)}" if match else ""


def _build_rows(query_scheduler: bool = True) -> list[dict[str, object]]:
    """Join submission, scheduler, rollup, terminal-gate, and inventory rows."""
    submissions = _submission_index()
    rollups = {row["case_label"]: row for row in _read_csv(TIMESERIES_ROLLUP)}
    final_windows = _final_window_summary()
    corrected_status = {row["case_key"]: row for row in _read_csv(CORRECTED_STATUS)}
    live_gate = {row["source_key"]: row for row in _read_csv(CORRECTED_LIVE_GATE)}
    inventory = {row["case_key"]: row for row in _read_csv(SALT_INVENTORY)}
    primary = {row["run_or_group"]: row for row in _read_csv(PRIMARY_DECISIONS)}
    job_ids_for_state = [
        job_id
        for item in submissions.values()
        for job_id in item["job_ids"]
    ]
    job_states = _query_job_states(job_ids_for_state, query_scheduler)

    case_keys = set(submissions) | set(rollups) | set(final_windows)
    rows: list[dict[str, object]] = []
    for case_key in sorted(case_keys):
        rollup = rollups.get(case_key, {})
        final = final_windows.get(case_key)
        inv_key = MAINLINE_ALIASES.get(case_key, case_key.replace("_corrected", ""))
        inv = inventory.get(inv_key, {})
        sub = submissions.get(case_key, {"job_ids": set(), "job_names": set(), "submission_sources": set()})
        job_ids = sorted(sub["job_ids"])
        latest_state = ";".join(
            f"{job_id}:{job_states.get(job_id, '')}" for job_id in job_ids if job_states.get(job_id, "")
        )
        if final:
            detection_run = "yes"
            steady_label = final["steady_label"]
            status = final["steady_state_detection_status"]
            mdot = final["mdot_verdict"]
            heat = final["heat_verdict"]
            reason = "explicit stopped-sbatch final-window flatness decision"
            window_start = final["last_window_start_s"]
            window_end = final["last_window_end_s"]
            evidence = final["evidence_path"]
            note = final["notes"]
        elif case_key in live_gate and live_gate[case_key].get("scheduler_state") == "RUNNING":
            detection_run = "no_current_terminal_window"
            steady_label = "needs continuation"
            status = "running_pending_terminal_last_window"
            mdot = ""
            heat = ""
            reason = "current selected corrected-Q continuation is still running"
            window_start = ""
            window_end = live_gate[case_key].get("latest_live_solver_time_s", "")
            evidence = _rel(CORRECTED_LIVE_GATE)
            note = "terminal harvest/admission gate pending after live job exits"
        elif rollup:
            detection_run = "yes"
            steady_label, reason = _classify_rollup(rollup)
            status = rollup.get("timeseries_status", "")
            mdot = rollup.get("mdot_verdict", "")
            heat = rollup.get("heat_verdict", "")
            window_start = rollup.get("last_window_start_s", "")
            window_end = rollup.get("last_window_end_s", "")
            evidence = _rel(TIMESERIES_ROLLUP)
            note = rollup.get("note", "")
        elif case_key in corrected_status:
            detection_run = "yes_prior_gate"
            steady_label = "needs continuation"
            status = corrected_status[case_key].get("status", "")
            mdot = ""
            heat = ""
            reason = "corrected-Q latest-time/gate table did not admit the row as steady"
            window_start = ""
            window_end = corrected_status[case_key].get("latest_log_time", "")
            evidence = _rel(CORRECTED_STATUS)
            note = corrected_status[case_key].get("status", "")
        else:
            detection_run = "no"
            steady_label = "not run"
            status = "no_last_window_detection_found"
            mdot = ""
            heat = ""
            reason = "submitted job ledger exists but no last-window detector output was found"
            window_start = ""
            window_end = ""
            evidence = ""
            note = ""

        rows.append({
            "run_key": case_key,
            "fluid_family": _family_for(case_key, rollup),
            "variant": _variant_for(case_key),
            "submitted_job_ids": ";".join(job_ids),
            "submitted_job_names": ";".join(sorted(sub["job_names"])),
            "latest_scheduler_state_observed": latest_state,
            "run_root": inv.get("run_root") or corrected_status.get(case_key, {}).get("registry_source_root") or "",
            "last_time_or_window_start_s": window_start,
            "last_time_or_window_end_s": window_end,
            "steady_detection_run": detection_run,
            "steady_state_detection_status": status,
            "mdot_verdict": mdot,
            "heat_verdict": heat,
            "steady_or_needs_continuation": steady_label,
            "needs_continuation_reason": reason if steady_label != "steady" else "",
            "recommended_action": rollup.get("recommended_action") or primary.get(case_key, {}).get("continuation_decision") or inv.get("action_needed", ""),
            "admission_overlay": rollup.get("admission_overlay") or inv.get("admission_verdict", ""),
            "submission_evidence_path": ";".join(sorted(sub["submission_sources"])),
            "steady_evidence_path": evidence,
            "notes": note,
        })
    return rows


def _source_manifest(generated_files: list[Path]) -> list[dict[str, object]]:
    sources = [
        NORMAL_RELAUNCH_SUBMITTED,
        SALT1_NOMINAL_SUBMITTED,
        CORRECTED_SUBMITTED,
        CORRECTED_SELECTED_SUBMITTED,
        TIMESERIES_ROLLUP,
        PRIMARY_DECISIONS,
        FINAL_WINDOW_METRICS,
        CORRECTED_STATUS,
        CORRECTED_LIVE_GATE,
        SALT_INVENTORY,
    ]
    rows = [
        {"artifact": path.name, "role": "read_only_input", "path": _rel(path), "exists": path.exists(), "notes": "input evidence; not mutated"}
        for path in sources
    ]
    rows.extend(
        {"artifact": path.name, "role": "generated_output", "path": _rel(path), "exists": path.exists(), "notes": "generated by build_submitted_cfd_run_steady_state_table.py"}
        for path in generated_files
    )
    return rows


def _write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  task: AGENT-343
  generated_by: tools/analyze/build_submitted_cfd_run_steady_state_table.py
tags: [cfd-pp, cfd-runs, steady-state, corrected-q, continuation]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/all_timeseries_case_rollup.csv
---
# Submitted CFD Run Steady-State Table

## Scope

This package consolidates submitted CFD solver rows from the known submission ledgers and joins them to existing last-window steady-state detection outputs. It includes continuations, water validation rows, legacy diagnostic perturbations, and corrected/perturbed Salt-Q rows.

## Label Rule

- `steady`: an explicit final-window or time-series detector found the representative last window steady/quasi-steady without drifting series.
- `needs continuation`: the row is running, drifting, under-advanced, failed/not accepted, or lacks a terminal current-run steady window.
- `not run`: a submitted/registered row was found but no last-window detector output was found.

Admission is not the same as this label. For example, Salt1 corrected-Q rows can be `steady` by final-window flatness while still diagnostic for fit use until Salt1 policy/admission resolves.

## Results

- Rows: `{summary["row_count"]}`
- Label counts: `{json.dumps(summary["label_counts"], sort_keys=True)}`
- Rows with detector output: `{summary["detector_rows"]}`
- Rows without detector output: `{summary["no_detector_rows"]}`

## Files

- `submitted_cfd_run_steady_state_table.csv`: full table requested by the coordinator.
- `submitted_cfd_run_summary.csv`: counts by fluid, variant, and steady label.
- `source_manifest.csv`: exact input/output paths.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build_submitted_cfd_run_steady_state_table(out_dir: Path | None = None, query_scheduler: bool = True) -> dict[str, object]:
    """Generate the submitted-run steady-state table package.

    Parameters
    ----------
    out_dir:
        Optional output directory.  Tests pass a temporary directory; production
        runs use the dated work-product directory.
    query_scheduler:
        If true, attach current `sacct` state for submitted job ids.  Disable
        this for deterministic offline regeneration.
    """
    out_dir = out_dir or OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = _build_rows(query_scheduler=query_scheduler)
    fields = [
        "run_key",
        "fluid_family",
        "variant",
        "submitted_job_ids",
        "submitted_job_names",
        "latest_scheduler_state_observed",
        "run_root",
        "last_time_or_window_start_s",
        "last_time_or_window_end_s",
        "steady_detection_run",
        "steady_state_detection_status",
        "mdot_verdict",
        "heat_verdict",
        "steady_or_needs_continuation",
        "needs_continuation_reason",
        "recommended_action",
        "admission_overlay",
        "submission_evidence_path",
        "steady_evidence_path",
        "notes",
    ]
    table_path = out_dir / "submitted_cfd_run_steady_state_table.csv"
    _write_csv(table_path, fields, rows)
    label_counts = Counter(row["steady_or_needs_continuation"] for row in rows)
    summary_rows = []
    grouped = Counter((row["fluid_family"], row["variant"], row["steady_or_needs_continuation"]) for row in rows)
    for (family, variant, label), count in sorted(grouped.items()):
        summary_rows.append({"fluid_family": family, "variant": variant, "steady_or_needs_continuation": label, "row_count": count})
    summary_path = out_dir / "submitted_cfd_run_summary.csv"
    _write_csv(summary_path, ["fluid_family", "variant", "steady_or_needs_continuation", "row_count"], summary_rows)
    generated = [table_path, summary_path]
    manifest_path = out_dir / "source_manifest.csv"
    _write_csv(manifest_path, ["artifact", "role", "path", "exists", "notes"], _source_manifest(generated))
    generated.append(manifest_path)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "task": "AGENT-343",
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "detector_rows": sum(1 for row in rows if str(row["steady_detection_run"]).startswith("yes")),
        "no_detector_rows": sum(1 for row in rows if row["steady_detection_run"] in {"no", "no_current_terminal_window"}),
        "native_solver_outputs_mutated": False,
        "required_outputs": ["submitted_cfd_run_steady_state_table.csv", "submitted_cfd_run_summary.csv", "source_manifest.csv", "summary.json", "README.md"],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_readme(out_dir, summary)
    return summary


def main() -> None:
    """CLI entrypoint used by agents and reproducibility checks."""
    print(json.dumps(build_submitted_cfd_run_steady_state_table(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
