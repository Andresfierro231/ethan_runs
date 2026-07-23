#!/usr/bin/env python3
"""Print exact, bounded slices of the live agent board."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.board_summary import parse_section_rows  # noqa: E402
from tools.agent.common import BOARD, BOARD_ARCHIVE, BoardRow  # noqa: E402


def short(text: str, max_chars: int = 180) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def load_entries(*, include_archive: bool = False) -> list[dict[str, object]]:
    entries = parse_section_rows(BOARD)
    if include_archive:
        entries.extend(parse_section_rows(BOARD_ARCHIVE))
    return entries


def filter_entries(
    entries: list[dict[str, object]],
    *,
    task_id: str | None = None,
    query: str | None = None,
    active: bool = False,
    open_only: bool = False,
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    query_l = query.lower() if query else None
    for entry in entries:
        row = entry["row"]
        assert isinstance(row, BoardRow)
        section = str(entry["section"])
        if task_id and row.task_id != task_id:
            continue
        if active and section != "Active":
            continue
        if open_only and not row.is_open:
            continue
        if query_l:
            haystack = " ".join([row.task_id, row.role, row.owner, row.scope, row.goal]).lower()
            if query_l not in haystack:
                continue
        out.append(entry)
    return out


def entry_to_dict(entry: dict[str, object], *, full: bool = False) -> dict[str, object]:
    row = entry["row"]
    assert isinstance(row, BoardRow)
    data: dict[str, object] = {
        "task_id": row.task_id,
        "status": row.status,
        "section": str(entry["section"]),
        "owner": row.owner,
        "role": row.role,
        "line": row.line_no,
        "source": str(row.source_path) if row.source_path else None,
    }
    if full:
        data["scope"] = row.scope
        data["goal"] = row.goal
        data["edit_paths"] = row.edit_paths
        data["readonly_paths"] = row.readonly_paths
    else:
        data["goal"] = short(row.goal)
    return data


def format_entry(entry: dict[str, object], *, full: bool = False) -> list[str]:
    row = entry["row"]
    assert isinstance(row, BoardRow)
    lines = [
        f"{row.task_id} [{row.status}] section={entry['section']} line={row.line_no} owner={row.owner}",
        f"  role: {row.role}",
        f"  goal: {row.goal if full else short(row.goal)}",
    ]
    if full:
        lines.append(f"  scope: {row.scope}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", help="Exact task id to print.")
    parser.add_argument("--query", help="Case-insensitive substring across task, role, owner, scope, and goal.")
    parser.add_argument("--active", action="store_true", help="Limit to rows in the Active section.")
    parser.add_argument("--open", dest="open_only", action="store_true", help="Limit to rows whose status is not complete.")
    parser.add_argument("--include-archive", action="store_true", help="Also search .agent/BOARD_ARCHIVE.md.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print unless --task-id is used.")
    parser.add_argument("--full", action="store_true", help="Print full scope/goal text for matching rows.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    entries = filter_entries(
        load_entries(include_archive=args.include_archive),
        task_id=args.task_id,
        query=args.query,
        active=args.active,
        open_only=args.open_only,
    )
    limited = entries if args.task_id else entries[: max(args.limit, 0)]
    data = {
        "matched_rows": len(entries),
        "printed_rows": len(limited),
        "rows": [entry_to_dict(entry, full=args.full) for entry in limited],
    }
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0 if entries else 1

    print(f"matched_rows={data['matched_rows']} printed_rows={data['printed_rows']}")
    for entry in limited:
        for line in format_entry(entry, full=args.full):
            print(line)
    if not entries:
        return 1
    if len(limited) < len(entries):
        print(f"... {len(entries) - len(limited)} more rows omitted; increase --limit or add --task-id.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
