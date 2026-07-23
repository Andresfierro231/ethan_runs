#!/usr/bin/env python3
"""Print a bounded summary of live board state."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import BOARD, BOARD_ARCHIVE, BoardRow, TASK_RE  # noqa: E402

HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


def parse_section_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not path.exists():
        return rows
    section = "(preamble)"
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        heading = HEADING_RE.match(line)
        if heading:
            section = heading.group(1)
            continue
        if not line.startswith("| "):
            continue
        if line.startswith("| ---") or line.startswith("| Task ID"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not TASK_RE.fullmatch(cells[0]):
            continue
        row = BoardRow(cells[0], cells[1], cells[2], cells[3], "|".join(cells[4:]).strip(), line_no, path)
        rows.append({"section": section, "row": row})
    return rows


def _short(text: str, max_chars: int = 170) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def summarize(include_archive: bool = False) -> dict[str, object]:
    entries = parse_section_rows(BOARD)
    if include_archive:
        entries.extend(parse_section_rows(BOARD_ARCHIVE))
    section_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for entry in entries:
        row = entry["row"]
        assert isinstance(row, BoardRow)
        section_counts[str(entry["section"])][row.status] += 1
    active_complete = [
        e for e in entries
        if e["section"] == "Active" and isinstance(e["row"], BoardRow) and e["row"].status == "complete"
    ]
    active_open = [
        e for e in entries
        if e["section"] == "Active" and isinstance(e["row"], BoardRow) and e["row"].status != "complete"
    ]
    return {
        "source_files": [str(BOARD), str(BOARD_ARCHIVE)] if include_archive else [str(BOARD)],
        "total_rows": len(entries),
        "sections": {k: dict(v) for k, v in sorted(section_counts.items())},
        "active_open_rows": len(active_open),
        "complete_rows_still_in_active": len(active_complete),
        "active_open": entries_to_dicts(active_open),
        "active_complete": entries_to_dicts(active_complete),
    }


def filter_entries(
    entries: list[dict[str, object]],
    *,
    task_filter: str | None = None,
    owner_filter: str | None = None,
    status_filter: str | None = None,
    section_filter: str | None = None,
    active_only: bool = False,
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for entry in entries:
        row = entry["row"]
        assert isinstance(row, BoardRow)
        section = str(entry["section"])
        haystack = " ".join([row.task_id, row.role, row.owner, row.scope, row.goal]).lower()
        if task_filter and task_filter.lower() not in haystack:
            continue
        if owner_filter and owner_filter.lower() not in row.owner.lower():
            continue
        if status_filter and status_filter.lower() != row.status.lower():
            continue
        if section_filter and section_filter.lower() not in section.lower():
            continue
        if active_only and section != "Active":
            continue
        out.append(entry)
    return out


def entries_to_dicts(entries: list[dict[str, object]]) -> list[dict[str, str]]:
    out = []
    for entry in entries:
        row = entry["row"]
        assert isinstance(row, BoardRow)
        out.append(
            {
                "task_id": row.task_id,
                "status": row.status,
                "owner": row.owner,
                "role": row.role,
                "section": str(entry["section"]),
                "line": str(row.line_no),
                "goal": _short(row.goal),
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-archive", action="store_true")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--task-filter", help="Case-insensitive text filter across task, role, owner, scope, and goal.")
    parser.add_argument("--owner-filter", help="Case-insensitive owner filter.")
    parser.add_argument("--status-filter", help="Exact row status filter, such as active, open, complete.")
    parser.add_argument("--section-filter", help="Case-insensitive board section filter.")
    parser.add_argument("--active-only", action="store_true", help="Only show rows from the Active section.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = summarize(include_archive=args.include_archive)
    raw_entries = parse_section_rows(BOARD)
    if args.include_archive:
        raw_entries.extend(parse_section_rows(BOARD_ARCHIVE))
    filtered_entries = filter_entries(
        raw_entries,
        task_filter=args.task_filter,
        owner_filter=args.owner_filter,
        status_filter=args.status_filter,
        section_filter=args.section_filter,
        active_only=args.active_only,
    )
    if any([args.task_filter, args.owner_filter, args.status_filter, args.section_filter, args.active_only]):
        data["filtered_rows"] = entries_to_dicts(filtered_entries)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    if "filtered_rows" in data:
        print(f"filtered_rows={len(data['filtered_rows'])} total_rows={data['total_rows']}")
        for item in data["filtered_rows"][: args.limit]:
            print(f"  - {item['task_id']} [{item['status']}] {item['owner']} :: {item['role']} :: {item['goal']}")
        return 0

    print(f"rows={data['total_rows']} active_open={data['active_open_rows']} complete_still_in_active={data['complete_rows_still_in_active']}")
    print("sections:")
    sections = data["sections"]
    assert isinstance(sections, dict)
    for section, counts in sections.items():
        count_text = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        print(f"  - {section}: {count_text}")

    print("\nActive rows needing attention:")
    for item in data["active_open"][: args.limit]:
        print(f"  - {item['task_id']} [{item['status']}] {item['owner']} :: {item['role']}")

    if data["complete_rows_still_in_active"]:
        print("\nComplete rows still in Active:")
        for item in data["active_complete"][: args.limit]:
            print(f"  - {item['task_id']} line={item['line']} owner={item['owner']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
