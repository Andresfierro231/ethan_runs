#!/usr/bin/env python3
"""Summarize one board task's allowed context without dumping the board."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import (  # noqa: E402
    BOARD,
    REPO_ROOT,
    active_conflicts,
    find_task,
    parse_board,
    task_artifact_globs,
)


LOCAL_HINTS = [
    ("tools/", "tools/AGENTS.override.md"),
    ("tools/", "tools/README.md"),
    ("reports/", "reports/AGENTS.override.md"),
    ("reports/", "reports/README.md"),
    ("operational_notes/", "operational_notes/README.md"),
    ("jadyn_runs/", "jadyn_runs/README.md"),
    ("staging/", "staging/README.md"),
]


def _path_exists(rel_path: str) -> bool:
    return (REPO_ROOT / rel_path).exists()


def instruction_paths(edit_paths: list[str]) -> list[str]:
    paths = ["AGENTS.md", ".agent/BOARD.md", ".agent/FILE_OWNERSHIP.md", ".agent/ROLES.md"]
    for edit in edit_paths:
        clean = edit.replace("**", "").rstrip("/")
        for prefix, candidate in LOCAL_HINTS:
            if clean.startswith(prefix) and candidate not in paths and _path_exists(candidate):
                paths.append(candidate)
        current = REPO_ROOT / clean
        if current.is_file():
            current = current.parent
        for name in ("AGENTS.override.md", "README.md", "TODO.md"):
            candidate = current / name
            if candidate.exists():
                rel = str(candidate.relative_to(REPO_ROOT))
                if rel not in paths:
                    paths.append(rel)
    return paths


def artifact_candidates(task_id: str) -> dict[str, list[str]]:
    return {
        key: [str(path.relative_to(REPO_ROOT)) for path in paths]
        for key, paths in task_artifact_globs(task_id).items()
    }


def build_context(task_id: str, *, include_archive: bool = False) -> dict[str, object]:
    rows = parse_board(include_archive=include_archive)
    row = find_task(task_id, rows)
    if row is None:
        return {
            "task_id": task_id,
            "found": False,
            "source": str(BOARD),
            "hint": "Use board_slice.py --query <text> --include-archive for a bounded search.",
        }
    conflicts = active_conflicts(row, rows)
    return {
        "task_id": row.task_id,
        "found": True,
        "status": row.status,
        "owner": row.owner,
        "role": row.role,
        "line": row.line_no,
        "source": str(row.source_path) if row.source_path else str(BOARD),
        "edit_paths": row.edit_paths,
        "readonly_paths": row.readonly_paths,
        "active_conflicts": conflicts,
        "closeout_artifacts_found": artifact_candidates(task_id),
        "local_instructions_to_read": instruction_paths(row.edit_paths),
        "bounded_followups": [
            f"python3.11 tools/agent/board_slice.py --task-id {task_id}",
            f"python3.11 tools/agent/preflight_task.py --task-id {task_id}",
            f"python3.11 tools/agent/finish_task.py --task-id {task_id}",
        ],
    }


def print_human(data: dict[str, object]) -> None:
    if not data.get("found"):
        print(f"task_id={data['task_id']} found=false")
        print(f"hint: {data['hint']}")
        return
    print(f"task_id={data['task_id']} status={data['status']} owner={data['owner']} line={data['line']}")
    print(f"role: {data['role']}")
    print("edit_paths:")
    for item in data["edit_paths"]:
        print(f"  - {item}")
    print("readonly_paths:")
    readonly = data["readonly_paths"]
    if readonly:
        for item in readonly:
            print(f"  - {item}")
    else:
        print("  - none declared")
    conflicts = data["active_conflicts"]
    print(f"active_conflicts={len(conflicts)}")
    for conflict in conflicts:
        print(f"  - {conflict['task_id']}: {conflict['mine']} overlaps {conflict['theirs']}")
    print("local_instructions_to_read:")
    for item in data["local_instructions_to_read"]:
        print(f"  - {item}")
    print("closeout_artifacts_found:")
    for key, paths in data["closeout_artifacts_found"].items():
        print(f"  - {key}: {len(paths)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--include-archive", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = build_context(args.task_id, include_archive=args.include_archive)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 0 if data.get("found") else 1


if __name__ == "__main__":
    raise SystemExit(main())
