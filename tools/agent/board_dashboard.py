#!/usr/bin/env python3
"""Print a compact board/dashboard summary for coordinators."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import parse_board  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    rows = parse_board()
    open_rows = [r for r in rows if r.is_open]
    active = [r for r in open_rows if r.status in {"active", "running", "submitted", "pending"} and r.task_id.startswith("AGENT-")]
    todos = [r for r in open_rows if r.task_id.startswith("TODO-")]

    print(f"board_rows={len(rows)} open_rows={len(open_rows)} active_or_live_agents={len(active)} open_todos={len(todos)}")
    print("\nActive/live agents:")
    for row in active[: args.limit]:
        print(f"  - {row.task_id} [{row.status}] {row.role}")
    print("\nOpen TODOs:")
    for row in todos[: args.limit]:
        print(f"  - {row.task_id} [{row.status}] {row.role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

