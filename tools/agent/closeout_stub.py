#!/usr/bin/env python3
"""Create or print status, journal, and import-manifest closeout stubs."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT, find_task, parse_board  # noqa: E402


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "task-closeout"


def manifest_slug(text: str) -> str:
    return slugify(text).replace("-", "_")


def infer_title(task_id: str, title: str | None) -> str:
    if title:
        return title
    row = find_task(task_id, parse_board(include_archive=True))
    if row:
        goal = row.goal.split("Acceptance:", 1)[0].strip()
        if goal:
            return goal[:120]
    return task_id.replace("-", " ").title()


def stub_paths(task_id: str, *, slug: str, today: str) -> dict[str, Path]:
    return {
        "status": REPO_ROOT / ".agent" / "status" / f"{today}_{task_id}.md",
        "journal": REPO_ROOT / ".agent" / "journal" / today / f"{slug}.md",
        "manifest": REPO_ROOT / "imports" / f"{today}_{manifest_slug(slug)}.json",
    }


def status_stub(task_id: str, title: str, today: str, changed_files: list[str], read_only: list[str]) -> str:
    return f"""---
provenance:
  - .agent/BOARD.md
tags: [agent-operations, closeout]
related: []
task: {task_id}
date: {today}
role: Coordinator/Implementer/Tester/Writer
type: status
status: draft
---
# {title}

## Objective

Document the task objective here.

## Outcome

Document the task outcome here.

## Changes Made

{bullet_list(changed_files)}

## Validation

- `python3.11 tools/agent/finish_task.py --task-id {task_id}`: pending

## Unresolved Blockers

- None recorded yet.

## Guardrails

{bullet_list(read_only)}
- Native solver outputs mutated: false
- Registry/admission state mutated: false
- Scheduler action: false
- External Fluid/source tree edited: false
"""


def journal_stub(task_id: str, title: str, today: str) -> str:
    return f"""---
provenance:
  - .agent/BOARD.md
tags: [agent-operations, journal]
related: []
task: {task_id}
date: {today}
role: Coordinator/Implementer/Tester/Writer
type: journal
status: draft
---
# {title}

Task: {task_id}

## Attempted

- Record what was attempted.

## Observed

- Record direct observations.

## Inferred

- Record interpretation separately from observations.

## Caveats

- Record contradictions, uncertainty, or concurrency caveats.

## Next Actions

- Record useful next steps.

## Validation Notes

- Record commands and results.
"""


def manifest_data(task_id: str, title: str, changed_files: list[str], read_only: list[str]) -> dict[str, object]:
    return {
        "task": task_id,
        "task_id": task_id,
        "title": title,
        "changed_files": changed_files,
        "read_only_context": read_only,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "thesis_current_or_latex_edit": False,
        "generated_index_refreshed": False,
        "no_scorecard_outputs": True,
    }


def bullet_list(items: list[str]) -> str:
    if not items:
        return "- Pending."
    return "\n".join(f"- `{item}`" for item in items)


def build_stubs(
    task_id: str,
    *,
    title: str | None = None,
    slug: str | None = None,
    changed_files: list[str] | None = None,
    read_only: list[str] | None = None,
    today: str | None = None,
) -> dict[str, object]:
    today = today or date.today().isoformat()
    title_text = infer_title(task_id, title)
    slug_text = slug or slugify(title_text)
    changed = changed_files or []
    readonly = read_only or [".agent/BOARD.md"]
    paths = stub_paths(task_id, slug=slug_text, today=today)
    return {
        "task_id": task_id,
        "title": title_text,
        "slug": slug_text,
        "paths": {key: str(path.relative_to(REPO_ROOT)) for key, path in paths.items()},
        "contents": {
            "status": status_stub(task_id, title_text, today, changed, readonly),
            "journal": journal_stub(task_id, title_text, today),
            "manifest": json.dumps(manifest_data(task_id, title_text, changed, readonly), indent=2, sort_keys=True) + "\n",
        },
    }


def write_stubs(data: dict[str, object], *, force: bool = False) -> list[str]:
    written: list[str] = []
    paths = data["paths"]
    contents = data["contents"]
    assert isinstance(paths, dict)
    assert isinstance(contents, dict)
    for key, rel_path in paths.items():
        path = REPO_ROOT / str(rel_path)
        if path.exists() and not force:
            raise FileExistsError(f"{rel_path} exists; use --force to overwrite")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(contents[key]), encoding="utf-8")
        written.append(str(rel_path))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--title")
    parser.add_argument("--slug")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--read-only", action="append", default=[])
    parser.add_argument("--write", action="store_true", help="Write files. Default prints paths only.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting existing stubs.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = build_stubs(
        args.task_id,
        title=args.title,
        slug=args.slug,
        changed_files=args.changed_file,
        read_only=args.read_only or None,
    )
    if args.write:
        try:
            data["written"] = write_stubs(data, force=args.force)
        except FileExistsError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if args.json:
        printable = {key: value for key, value in data.items() if key != "contents"}
        print(json.dumps(printable, indent=2, sort_keys=True))
    else:
        mode = "write" if args.write else "dry_run"
        print(f"mode={mode} task_id={data['task_id']}")
        for key, rel_path in data["paths"].items():
            print(f"{key}: {rel_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
