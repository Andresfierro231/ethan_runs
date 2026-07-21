#!/usr/bin/env python3
"""Build a compact lineage-collapsed submitted CFD run table.

This consumes the full AGENT-343 table and reports only the latest row within a
same-Q continuation lineage. Changed-Q rows remain separate physical runs.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table"
FULL_TABLE = OUT_DIR / "submitted_cfd_run_steady_state_table.csv"
COMPACT_TABLE = OUT_DIR / "submitted_cfd_run_compact_lineage_table.csv"
SUMMARY_PATH = OUT_DIR / "compact_lineage_summary.json"

FIELDNAMES = [
    "lineage_group",
    "q_variant",
    "latest_run_key",
    "collapsed_from_run_keys",
    "superseded_run_keys",
    "collapsed_row_count",
    "fluid_family",
    "latest_variant",
    "steady_or_needs_continuation",
    "steady_detection_run",
    "last_time_or_window_start_s",
    "last_time_or_window_end_s",
    "mdot_verdict",
    "heat_verdict",
    "steady_state_detection_status",
    "recommended_action",
    "admission_overlay",
    "needs_continuation_reason",
    "submitted_job_ids",
    "submitted_job_names",
    "latest_scheduler_state_observed",
    "run_root",
    "submission_evidence_path",
    "steady_evidence_path",
    "notes",
    "collapse_policy",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _number(text: str) -> float:
    try:
        return float(text)
    except (TypeError, ValueError):
        return float("-inf")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _base_case(run_key: str, fluid_family: str) -> str:
    salt_match = re.match(r"^(salt[1-4]_jin)", run_key)
    if salt_match:
        return salt_match.group(1)
    water_match = re.match(r"^(water[1-4])$", run_key)
    if water_match:
        return water_match.group(1)
    if run_key == "kirst_continuation_candidate":
        return "salt1_kirst"
    if fluid_family:
        return f"{fluid_family}:{run_key}"
    return run_key


def _q_variant(run_key: str, variant: str) -> str:
    for token in ("lo10q", "hi10q", "lo5q", "hi5q"):
        if f"_{token}_" in run_key or run_key.endswith(f"_{token}"):
            return token
    if "_loq_" in run_key or run_key.endswith("_loq"):
        return "loq"
    if "_hiq_" in run_key or run_key.endswith("_hiq"):
        return "hiq"
    if variant in {"lo10q", "hi10q", "lo5q", "hi5q"}:
        return variant
    if variant == "water_continuation":
        return "nominal"
    if variant == "nominal_or_continuation" or "nominal_continuation_corrected" in run_key:
        return "nominal"
    return "nominal"


def _scenario_suffix(run_key: str) -> str:
    """Return non-Q setup differences that should not be collapsed together."""
    base_match = re.match(r"^salt[1-4]_jin_?(.*)$", run_key)
    if not base_match:
        return "native"
    suffix = base_match.group(1)
    suffix = suffix.replace("_job3246562_failed_missing_system_controlDict", "")
    suffix = suffix.replace("nominal_continuation_corrected", "mainline")
    for q_token in ("lo10q", "hi10q", "lo5q", "hi5q", "loq", "hiq"):
        suffix = suffix.replace(q_token, "")
    suffix = suffix.replace("corrected", "")
    suffix = re.sub(r"_+", "_", suffix).strip("_")
    if not suffix or suffix in {"basecont", "mainline"}:
        return "mainline"
    return suffix


def lineage_group_for(row: dict[str, str]) -> tuple[str, str]:
    run_key = row["run_key"]
    variant = row.get("variant", "")
    base = _base_case(run_key, row.get("fluid_family", ""))
    q_variant = _q_variant(run_key, variant)
    scenario = _scenario_suffix(run_key)
    if base.startswith("salt") and scenario == "mainline" and q_variant == "nominal":
        return f"{base}::nominal", q_variant
    if base.startswith("salt"):
        return f"{base}::{q_variant}::{scenario}", q_variant
    return f"{base}::{q_variant}", q_variant


def _latest_key(row: dict[str, str]) -> tuple[float, float, str]:
    return (
        _number(row.get("last_time_or_window_end_s", "")),
        _number(row.get("last_time_or_window_start_s", "")),
        row.get("run_key", ""),
    )


def _join_unique(rows: list[dict[str, str]], key: str) -> str:
    values: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for item in (row.get(key) or "").split(";"):
            item = item.strip()
            if item and item not in seen:
                seen.add(item)
                values.append(item)
    return ";".join(values)


def build_compact_lineage_table(out_dir: Path = OUT_DIR) -> dict[str, object]:
    rows = _read_csv(FULL_TABLE)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    q_by_group: dict[str, str] = {}
    for row in rows:
        group, q_variant = lineage_group_for(row)
        grouped[group].append(row)
        q_by_group[group] = q_variant

    compact_rows: list[dict[str, object]] = []
    for group in sorted(grouped):
        lineage_rows = sorted(grouped[group], key=_latest_key)
        latest = lineage_rows[-1]
        all_keys = [row["run_key"] for row in lineage_rows]
        superseded = all_keys[:-1]
        compact_rows.append({
            "lineage_group": group,
            "q_variant": q_by_group[group],
            "latest_run_key": latest["run_key"],
            "collapsed_from_run_keys": ";".join(all_keys),
            "superseded_run_keys": ";".join(superseded),
            "collapsed_row_count": len(lineage_rows),
            "fluid_family": latest.get("fluid_family", ""),
            "latest_variant": latest.get("variant", ""),
            "steady_or_needs_continuation": latest.get("steady_or_needs_continuation", ""),
            "steady_detection_run": latest.get("steady_detection_run", ""),
            "last_time_or_window_start_s": latest.get("last_time_or_window_start_s", ""),
            "last_time_or_window_end_s": latest.get("last_time_or_window_end_s", ""),
            "mdot_verdict": latest.get("mdot_verdict", ""),
            "heat_verdict": latest.get("heat_verdict", ""),
            "steady_state_detection_status": latest.get("steady_state_detection_status", ""),
            "recommended_action": latest.get("recommended_action", ""),
            "admission_overlay": latest.get("admission_overlay", ""),
            "needs_continuation_reason": latest.get("needs_continuation_reason", ""),
            "submitted_job_ids": _join_unique(lineage_rows, "submitted_job_ids"),
            "submitted_job_names": _join_unique(lineage_rows, "submitted_job_names"),
            "latest_scheduler_state_observed": latest.get("latest_scheduler_state_observed", ""),
            "run_root": latest.get("run_root", ""),
            "submission_evidence_path": _join_unique(lineage_rows, "submission_evidence_path"),
            "steady_evidence_path": _join_unique(lineage_rows, "steady_evidence_path"),
            "notes": latest.get("notes", ""),
            "collapse_policy": "latest_same_q_lineage;changed_q_kept_separate",
        })

    out_table = out_dir / COMPACT_TABLE.name
    _write_csv(out_table, compact_rows)

    summary = {
        "task": "AGENT-346",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_table": str(FULL_TABLE.relative_to(REPO_ROOT)),
        "output_table": _display_path(out_table),
        "input_row_count": len(rows),
        "compact_row_count": len(compact_rows),
        "collapsed_row_count": len(rows) - len(compact_rows),
        "label_counts": dict(Counter(row["steady_or_needs_continuation"] for row in compact_rows)),
        "q_variant_counts": dict(Counter(row["q_variant"] for row in compact_rows)),
        "lineages_with_superseded_rows": sum(1 for row in compact_rows if row["superseded_run_keys"]),
        "native_solver_outputs_mutated": False,
    }
    summary_path = out_dir / SUMMARY_PATH.name
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build_compact_lineage_table(), indent=2, sort_keys=True))
