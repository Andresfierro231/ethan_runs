#!/usr/bin/env python3
"""Create dry-run or written scaffolding for a new board task."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import BOARD, REPO_ROOT, find_task, parse_board  # noqa: E402


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "agent-task"


def _frontmatter(task_id: str, title: str, doc_type: str, status: str) -> str:
    today = dt.date.today().isoformat()
    return (
        "---\n"
        "provenance:\n"
        "  - .agent/BOARD.md\n"
        "tags: [agent-operations, task-handoff]\n"
        "related:\n"
        f"  - imports/{today}_{slugify(title).replace('-', '_')}.json\n"
        f"task: {task_id}\n"
        f"date: {today}\n"
        "role: Coordinator/Implementer/Tester/Writer\n"
        f"type: {doc_type}\n"
        f"status: {status}\n"
        "---\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--role", default="Coordinator / Implementer / Tester / Writer")
    parser.add_argument("--owner", default="codex")
    parser.add_argument("--scope", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--write-board-row", action="store_true")
    args = parser.parse_args()

    if find_task(args.task_id, parse_board()) is not None:
        print(f"ERROR: {args.task_id} already exists on board", file=sys.stderr)
        return 2

    today = dt.date.today().isoformat()
    slug = slugify(args.title)
    row = f"| {args.task_id} | {args.role} | {args.owner} | {args.scope} | {args.goal} STATUS: ACTIVE {today}. |"
    paths = {
        "status": REPO_ROOT / ".agent" / "status" / f"{today}_{args.task_id}.md",
        "journal": REPO_ROOT / ".agent" / "journal" / today / f"{slug}.md",
        "import": REPO_ROOT / "imports" / f"{today}_{slug.replace('-', '_')}.json",
        "work_product": REPO_ROOT / "work_products" / today[:7] / today / f"{today}_{slug}",
    }

    print(row)
    for key, path in paths.items():
        print(f"{key}: {path.relative_to(REPO_ROOT)}")
    if not args.write:
        return 0

    paths["status"].parent.mkdir(parents=True, exist_ok=True)
    paths["journal"].parent.mkdir(parents=True, exist_ok=True)
    paths["import"].parent.mkdir(parents=True, exist_ok=True)
    paths["work_product"].mkdir(parents=True, exist_ok=True)
    paths["status"].write_text(_frontmatter(args.task_id, args.title, "status", "active") + f"# {args.task_id} Status\n\n", encoding="utf-8")
    paths["journal"].write_text(_frontmatter(args.task_id, args.title, "journal", "active") + f"# {args.title}\n\n", encoding="utf-8")
    paths["import"].write_text(json.dumps({"task": args.task_id, "date": today, "type": "coordination_manifest", "changed_files": []}, indent=2) + "\n", encoding="utf-8")

    if args.write_board_row:
        text = BOARD.read_text(encoding="utf-8")
        marker = "| --- | --- | --- | --- | --- |\n"
        BOARD.write_text(text.replace(marker, marker + row + "\n", 1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

