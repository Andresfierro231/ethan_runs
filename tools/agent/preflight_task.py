#!/usr/bin/env python3
"""Read-only preflight for an assigned board task."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import active_conflicts, find_task, parse_board, write_json_stdout  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    rows = parse_board()
    row = find_task(args.task_id, rows)
    if row is None:
        print(f"ERROR: task {args.task_id} not found on .agent/BOARD.md", file=sys.stderr)
        return 2

    conflicts = active_conflicts(row, rows)
    result = {
        "task_id": row.task_id,
        "status": row.status,
        "role": row.role,
        "owner": row.owner,
        "line_no": row.line_no,
        "edit_paths": row.edit_paths,
        "readonly_paths": row.readonly_paths,
        "conflicts": conflicts,
        "required_handoff": [
            ".agent/status/<date>_<task>.md",
            ".agent/journal/<date>/<slug>.md",
            "imports/<date>_<slug>.json",
        ],
        "index_refresh": "required for significant sessions unless another active row owns generated index files",
    }
    if args.json:
        write_json_stdout(result)
    else:
        print(f"Task: {row.task_id} ({row.status})")
        print(f"Role: {row.role}; owner: {row.owner}; board line: {row.line_no}")
        print("Editable paths:")
        for path in row.edit_paths:
            print(f"  - {path}")
        print("Read-only paths:")
        for path in row.readonly_paths:
            print(f"  - {path}")
        if conflicts:
            print("Conflicts:")
            for item in conflicts:
                print(f"  - {item['task_id']}: {item['mine']} overlaps {item['theirs']} ({item['status']})")
        else:
            print("Conflicts: none detected")
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())

