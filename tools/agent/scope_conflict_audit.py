#!/usr/bin/env python3
"""Audit broad open board scopes and active edit-path conflicts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import BOARD, BoardRow, active_conflicts, parse_board  # noqa: E402


def is_broad_edit_path(path: str) -> bool:
    clean = path.strip().rstrip("/")
    if not clean or clean in {".", "**", "*/"}:
        return True
    if clean.startswith((".agent/status/<date>", ".agent/journal/<date>", "imports/<date>")):
        return False
    if "<date>" in clean or "<TASK>" in clean:
        return True
    parts = [part for part in clean.split("/") if part and part != ".."]
    if clean.endswith("/**") and len(parts) <= 2:
        return True
    if clean.endswith("/"):
        return True
    # Directory-style claims without a file suffix are broad enough to block
    # later narrow helper additions, e.g. tools/analyze/ or reports/foo.
    last = Path(clean).name
    return "." not in last and len(parts) <= 2 and "(own row" not in clean


def _dedupe_conflicts(conflicts: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, str]] = []
    for conflict in conflicts:
        key = (conflict["task_id"], conflict["mine"], conflict["theirs"])
        if key in seen:
            continue
        seen.add(key)
        out.append(conflict)
    return out


def audit_rows(rows: list[BoardRow], *, task_id: str | None = None, limit: int = 30) -> dict[str, object]:
    selected = [row for row in rows if row.is_open]
    if task_id:
        selected = [row for row in selected if row.task_id == task_id]
    broad_rows = []
    conflict_rows = []
    for row in selected:
        broad_paths = [path for path in row.edit_paths if is_broad_edit_path(path)]
        conflicts = _dedupe_conflicts(active_conflicts(row, rows))
        if broad_paths:
            broad_rows.append(
                {
                    "task_id": row.task_id,
                    "status": row.status,
                    "owner": row.owner,
                    "line": row.line_no,
                    "broad_edit_paths": broad_paths,
                }
            )
        if conflicts:
            conflict_rows.append(
                {
                    "task_id": row.task_id,
                    "status": row.status,
                    "owner": row.owner,
                    "line": row.line_no,
                    "conflicts": conflicts,
                }
            )
    return {
        "open_rows_scanned": len(selected),
        "broad_scope_rows_total": len(broad_rows),
        "conflict_rows_total": len(conflict_rows),
        "broad_scope_rows": broad_rows[: max(limit, 0)],
        "conflict_rows": conflict_rows[: max(limit, 0)],
    }


def print_human(data: dict[str, object]) -> None:
    print(
        "open_rows_scanned={open_rows_scanned} broad_scope_rows={broad_scope_rows_total} "
        "conflict_rows={conflict_rows_total}".format(**data)
    )
    if data["broad_scope_rows"]:
        print("broad_scope_rows:")
        for row in data["broad_scope_rows"]:
            print(f"  - {row['task_id']} status={row['status']} owner={row['owner']} line={row['line']}")
            for path in row["broad_edit_paths"]:
                print(f"    path={path}")
    if data["conflict_rows"]:
        print("active_conflicts:")
        for row in data["conflict_rows"]:
            print(f"  - {row['task_id']} status={row['status']} owner={row['owner']} line={row['line']}")
            for conflict in row["conflicts"]:
                print(f"    with={conflict['task_id']} mine={conflict['mine']} theirs={conflict['theirs']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", help="Limit audit to one open task.")
    parser.add_argument("--include-archive", action="store_true", help="Include archived rows for historical checks.")
    parser.add_argument("--limit", type=int, default=30, help="Maximum rows per section.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = parse_board(BOARD, include_archive=args.include_archive)
    data = audit_rows(rows, task_id=args.task_id, limit=args.limit)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 1 if data["conflict_rows_total"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
