#!/usr/bin/env python3
"""Audit active board rows and forward-v1 work readiness.

This is a coordination/readiness package. It parses the active board and local
status files only; it does not inspect scheduler state live or mutate generated
indexes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / ".agent/BOARD.md"
BLOCKERS = ROOT / ".agent/BLOCKERS.md"
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_active_row_cleanup_and_forward_work_readiness"

STATUS_RE = re.compile(r"STATUS:\s*([^|]+?)(?:\.|$)")
TASK_RE = re.compile(r"AGENT-\d+")

STATUS_COLUMNS = [
    "task_id",
    "row_index",
    "role",
    "owner",
    "board_status",
    "status_file",
    "status_file_exists",
    "duplicate_active_id",
    "has_active_like_status",
    "scope_contains_scheduler",
    "scope_contains_external_fluid",
    "goal_summary",
    "cleanup_recommendation",
]

WORK_COLUMNS = [
    "work_area",
    "claimed_by_active_tasks",
    "safe_to_claim_now",
    "reason",
    "recommended_next_action",
]

QUEUE_COLUMNS = [
    "priority",
    "next_work",
    "claim_status",
    "depends_on",
    "recommended_scope",
    "acceptance_signal",
]

ISSUE_COLUMNS = [
    "issue_id",
    "severity",
    "issue_type",
    "affected_tasks",
    "evidence",
    "recommended_resolution",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def active_table_lines(board_text: str) -> list[str]:
    lines = board_text.splitlines()
    in_active = False
    rows: list[str] = []
    for line in lines:
        if line.strip() == "## Active":
            in_active = True
            continue
        if in_active and line.startswith("## "):
            break
        if in_active and line.startswith("| AGENT-"):
            rows.append(line)
    return rows


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [part.strip() for part in stripped.split("|")]


def parse_active_rows(board_text: str) -> list[dict[str, str]]:
    rows = []
    for index, line in enumerate(active_table_lines(board_text), start=1):
        parts = split_markdown_row(line)
        if len(parts) < 5:
            continue
        task_id, role, owner, scope, goal = parts[:5]
        status_match = STATUS_RE.search(goal)
        rows.append(
            {
                "task_id": task_id,
                "row_index": str(index),
                "role": role,
                "owner": owner,
                "scope": scope,
                "goal": goal,
                "board_status": status_match.group(1).strip() if status_match else "unknown",
            }
        )
    return rows


def status_path(task_id: str) -> Path:
    return ROOT / f".agent/status/2026-07-15_{task_id}.md"


def fallback_status_path(task_id: str) -> Path:
    return ROOT / f".agent/status/2026-07-14_{task_id}.md"


def active_like(status: str) -> bool:
    normalized = status.lower()
    return any(token in normalized for token in ("active", "running", "progress", "submitted", "pending"))


def cleanup_recommendation(row: dict[str, str], duplicate: bool, exists: bool) -> str:
    status = row["board_status"].lower()
    if duplicate:
        return "Resolve duplicate active task ID before new work depends on this row."
    if not exists and active_like(status):
        return "Create or locate missing task status file; active row cannot be trusted without closeout/status."
    if not active_like(status):
        return "Move completed row out of Active during next board cleanup."
    return "Leave active; avoid overlapping scope."


def build_status_rows(active_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts = Counter(row["task_id"] for row in active_rows)
    out: list[dict[str, Any]] = []
    for row in active_rows:
        task_id = row["task_id"]
        primary = status_path(task_id)
        fallback = fallback_status_path(task_id)
        existing = primary if primary.exists() else fallback
        exists = existing.exists()
        duplicate = counts[task_id] > 1
        scope = row["scope"].lower()
        out.append(
            {
                "task_id": task_id,
                "row_index": row["row_index"],
                "role": row["role"],
                "owner": row["owner"],
                "board_status": row["board_status"],
                "status_file": rel(existing) if exists else rel(primary),
                "status_file_exists": exists,
                "duplicate_active_id": duplicate,
                "has_active_like_status": active_like(row["board_status"]),
                "scope_contains_scheduler": "scheduler" in scope or "squeue" in scope or "sacct" in scope,
                "scope_contains_external_fluid": "../cfd-modeling-tools" in scope and "external" in scope,
                "goal_summary": row["goal"][:240],
                "cleanup_recommendation": cleanup_recommendation(row, duplicate, exists),
            }
        )
    return out


def claim_map(active_rows: list[dict[str, str]]) -> dict[str, list[str]]:
    areas = {
        "setup_only_cooler_hx_synthesis": ("cooler", "hx", "boundary"),
        "sensor_policy_refresh": ("sensor",),
        "hydraulic_h1_f6": ("hydraulic", "h1", "f6"),
        "corrected_q_terminal_harvest": ("corrected-q", "corrected", "saltq", "3293924", "3295438"),
        "pm5_matched_plane_recovery": ("pm5", "matched", "upcomer", "3295901"),
        "thermal_overnight_rescue": ("thermal", "external-bc", "heat-loss"),
        "docs_index_refresh": ("generated index", ".agent/state", ".agent/blockers", "catalog"),
    }
    claims: dict[str, list[str]] = defaultdict(list)
    for row in active_rows:
        if row["task_id"] == "AGENT-401":
            continue
        haystack = f"{row['role']} {row['scope']} {row['goal']}".lower()
        if not active_like(row["board_status"]):
            continue
        for area, needles in areas.items():
            if any(needle in haystack for needle in needles):
                claims[area].append(row["task_id"])
    return claims


def build_work_rows(active_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    claims = claim_map(active_rows)
    specs = [
        (
            "setup_only_cooler_hx_synthesis",
            "AGENT-394 or AGENT-392 currently overlaps cooler/HX/boundary evidence.",
            "Wait for claimed rows to complete, then synthesize/admit setup-only cooler candidate if still missing.",
        ),
        (
            "sensor_policy_refresh",
            "AGENT-393/394 scopes include sensor policy or scorecard inputs.",
            "Consume completed sensor-policy package; only open new work if no final table exists.",
        ),
        (
            "hydraulic_h1_f6",
            "AGENT-373/393 scopes cover hydraulic chain or relaunch readiness.",
            "Wait for dependency-held jobs and completed hydraulic package before H1/F6 scoring.",
        ),
        (
            "corrected_q_terminal_harvest",
            "Corrected-Q job remains scheduler-dependent.",
            "Watch terminal state only; build harvest/admission after 3293924 and 3295438 finish.",
        ),
        (
            "pm5_matched_plane_recovery",
            "PM5 recovery/relaunch readiness is already covered by active/completed forward-v1 unblock packages.",
            "Do not relaunch without a dedicated row and diagnosis of cancelled jobs.",
        ),
        (
            "thermal_overnight_rescue",
            "AGENT-392 owns thermal overnight runner status.",
            "Close out or consume AGENT-392 only after runner completes and status is updated.",
        ),
        (
            "docs_index_refresh",
            "Generated index refresh should wait for active rows to settle.",
            "Run repo index only after board cleanup avoids stale/duplicate active state.",
        ),
    ]
    rows = []
    for area, blocked_reason, action in specs:
        claimed = sorted(set(claims.get(area, [])))
        rows.append(
            {
                "work_area": area,
                "claimed_by_active_tasks": ";".join(claimed),
                "safe_to_claim_now": "no" if claimed else ("yes" if area not in {"corrected_q_terminal_harvest", "docs_index_refresh"} else "conditional"),
                "reason": blocked_reason if claimed else "No active claim detected by keyword scan.",
                "recommended_next_action": action,
            }
        )
    return rows


def build_issue_rows(status_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    duplicates = defaultdict(list)
    for row in status_rows:
        if row["duplicate_active_id"]:
            duplicates[row["task_id"]].append(str(row["row_index"]))
    for task_id, row_indices in sorted(duplicates.items()):
        issues.append(
            {
                "issue_id": f"duplicate_{task_id}",
                "severity": "high",
                "issue_type": "duplicate_active_task_id",
                "affected_tasks": task_id,
                "evidence": "active row indices " + ";".join(row_indices),
                "recommended_resolution": "Assign unique IDs or retire the stale duplicate rows before claiming dependent work.",
            }
        )
    missing = [row for row in status_rows if row["has_active_like_status"] and not row["status_file_exists"]]
    for row in missing:
        issues.append(
            {
                "issue_id": f"missing_status_{row['task_id']}_{row['row_index']}",
                "severity": "medium",
                "issue_type": "active_row_missing_status",
                "affected_tasks": row["task_id"],
                "evidence": row["status_file"],
                "recommended_resolution": "Create/locate status file or mark row complete if work already landed.",
            }
        )
    completed_in_active = [row for row in status_rows if not row["has_active_like_status"]]
    if completed_in_active:
        issues.append(
            {
                "issue_id": "completed_rows_still_in_active",
                "severity": "medium",
                "issue_type": "board_hygiene",
                "affected_tasks": ";".join(row["task_id"] for row in completed_in_active[:20]),
                "evidence": f"{len(completed_in_active)} active-table rows have non-active board status",
                "recommended_resolution": "Move completed rows out of Active during board cleanup; do not infer active ownership from them.",
            }
        )
    return issues


def build_queue_rows(work_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_area = {row["work_area"]: row for row in work_rows}
    return [
        {
            "priority": "P1",
            "next_work": "Consume AGENT-394 or AGENT-393 cooler/HX outputs after completion.",
            "claim_status": "blocked_by_active_claim" if by_area["setup_only_cooler_hx_synthesis"]["claimed_by_active_tasks"] else "ready",
            "depends_on": by_area["setup_only_cooler_hx_synthesis"]["claimed_by_active_tasks"],
            "recommended_scope": "new dated setup-only cooler/HX admission package only if no completed package exists",
            "acceptance_signal": "runtime-leakage-free cooler candidate admitted or explicitly no-go under Salt2/Salt3/Salt4 split",
        },
        {
            "priority": "P2",
            "next_work": "Close out AGENT-392 thermal runner or consume its finished outputs.",
            "claim_status": "blocked_by_active_claim" if by_area["thermal_overnight_rescue"]["claimed_by_active_tasks"] else "ready",
            "depends_on": by_area["thermal_overnight_rescue"]["claimed_by_active_tasks"],
            "recommended_scope": "status refresh/read-only summary if runner has stopped",
            "acceptance_signal": "stage_status and status file agree; no live process ambiguity",
        },
        {
            "priority": "P3",
            "next_work": "Watch corrected-Q terminal state and harvester dependency.",
            "claim_status": "scheduler_dependent",
            "depends_on": "3293924;3295438",
            "recommended_scope": "read-only scheduler snapshot until terminal, then admission package",
            "acceptance_signal": "terminal corrected-Q rows receive split/admission labels",
        },
        {
            "priority": "P4",
            "next_work": "Regenerate repo index after active rows settle.",
            "claim_status": "defer",
            "depends_on": "board cleanup and active-row closeouts",
            "recommended_scope": "generated index refresh only after duplicate/stale rows are resolved",
            "acceptance_signal": ".agent/STATE.md and .agent/BLOCKERS.md no longer lag active board state",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_path": rel(BOARD), "exists": str(BOARD.exists()).lower(), "use": "active row parsing"},
        {"source_path": rel(BLOCKERS), "exists": str(BLOCKERS.exists()).lower(), "use": "blocker context"},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(BOARD)}
  - {rel(BLOCKERS)}
tags: [coordination, forward-v1, board-hygiene, active-rows]
related:
  - operational_notes/07-26/14/2026-07-14_TOMORROW_FORWARD_V1_FULL_CONTEXT_AND_OVERNIGHT_PLAN.md
task: AGENT-401
date: 2026-07-15
role: Coordinator/Forward-pred/Tester/Writer
type: work_product
status: complete
---
# Active Row Cleanup And Forward Work Readiness

## Decision

This package implements the active-row cleanup/readiness slice of the July 15
plan. It does not claim cooler/HX, sensor, hydraulic, corrected-Q, PM5, or
thermal runner scopes that are already active elsewhere. It identifies which
lanes are currently unsafe to duplicate and what should be picked up after the
active rows close.

## Headline

- Active rows parsed: `{summary['active_rows']}`.
- Duplicate active task IDs: `{summary['duplicate_task_ids']}`.
- Active-like rows missing status files: `{summary['active_like_missing_status_rows']}`.
- Completed/non-active rows still in Active: `{summary['completed_rows_still_in_active']}`.
- Final forward-v1 admission changed: `false`.

## Files

- `active_row_status_audit.csv`
- `forward_work_claim_matrix.csv`
- `safe_next_work_queue.csv`
- `coordination_issues.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrail

The highest-value scientific task remains setup-only cooler/HX admission, but
it is already claimed by active rows. Do not duplicate that package until the
active claims close or are explicitly retired.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    board_text = read_text(BOARD)
    active_rows = parse_active_rows(board_text)
    status_rows = build_status_rows(active_rows)
    work_rows = build_work_rows(active_rows)
    issue_rows = build_issue_rows(status_rows)
    queue_rows = build_queue_rows(work_rows)
    manifest = source_manifest_rows()

    duplicate_ids = sorted({row["task_id"] for row in status_rows if row["duplicate_active_id"]})
    active_missing = [row for row in status_rows if row["has_active_like_status"] and not row["status_file_exists"]]
    completed_in_active = [row for row in status_rows if not row["has_active_like_status"]]
    summary = {
        "task": "AGENT-401",
        "generated_at": utc_now(),
        "active_rows": len(active_rows),
        "duplicate_task_ids": duplicate_ids,
        "duplicate_task_id_count": len(duplicate_ids),
        "active_like_missing_status_rows": len(active_missing),
        "completed_rows_still_in_active": len(completed_in_active),
        "coordination_issue_rows": len(issue_rows),
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "generated_indexes_mutated": False,
        "external_fluid_modified": False,
    }

    write_csv(out / "active_row_status_audit.csv", status_rows, STATUS_COLUMNS)
    write_csv(out / "forward_work_claim_matrix.csv", work_rows, WORK_COLUMNS)
    write_csv(out / "safe_next_work_queue.csv", queue_rows, QUEUE_COLUMNS)
    write_csv(out / "coordination_issues.csv", issue_rows, ISSUE_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, ["source_path", "exists", "use"])
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
