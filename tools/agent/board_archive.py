#!/usr/bin/env python3
"""Move archived board sections out of .agent/BOARD.md."""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import BOARD, BOARD_ARCHIVE, REPO_ROOT  # noqa: E402

HEADING_RE = re.compile(r"^## .*$", re.MULTILINE)


@dataclass(frozen=True)
class Section:
    heading: str | None
    text: str


def split_sections(text: str) -> list[Section]:
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [Section(None, text)] if text else []
    sections: list[Section] = []
    if matches[0].start() > 0:
        sections.append(Section(None, text[: matches[0].start()]))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[match.start() : end]
        sections.append(Section(match.group(0).strip(), section_text))
    return sections


def is_archived_section(section: Section) -> bool:
    return bool(section.heading and section.heading.startswith("## Archived"))


def is_archive_pointer(section: Section) -> bool:
    return section.heading == "## Archive"


def archive_pointer() -> str:
    return (
        "## Archive\n\n"
        "Historical archived board rows live in `.agent/BOARD_ARCHIVE.md`.\n"
        "Do not append completed archive blocks to the live board; run "
        "`python3.11 tools/agent/board_archive.py --apply` after board hygiene.\n"
    )


def archive_header() -> str:
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    return (
        "# Board Archive\n\n"
        "Managed by `tools/agent/board_archive.py`.\n\n"
        "- Source live board: `.agent/BOARD.md`\n"
        "- Last updated: `%s`\n"
        "- Purpose: keep historical completed rows searchable without forcing every agent to read them at startup.\n\n"
        "Use `python3.11 tools/agent/board_summary.py --include-archive` when historical rows are needed.\n\n"
        % now
    )


def _section_key(section_text: str) -> str:
    return "\n".join(line.rstrip() for line in section_text.strip().splitlines())


def _combine_archive_sections(existing_text: str, moved_sections: list[Section]) -> list[str]:
    existing_sections = [s.text for s in split_sections(existing_text) if is_archived_section(s)]
    out: list[str] = []
    seen: set[str] = set()
    for text in existing_sections + [s.text for s in moved_sections]:
        key = _section_key(text)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(text.strip() + "\n")
    return out


def build_task_archive_section(task_id: str, row_line: str) -> str:
    today = dt.date.today().isoformat()
    title = task_id.replace("TODO-", "").replace("AGENT-", "AGENT-").replace("-", " ").title()
    return (
        f"## Archived Complete - {today} {title}\n\n"
        "Row moved from the live board after closeout validation. It remains "
        "parser-readable here for `finish_task.py` and historical audits.\n\n"
        f"### Parser-Readable Completed Rows - {today} {title}\n\n"
        "| Task ID | Role | Owner | Scope | Goal |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{row_line.rstrip()}\n"
    )


def archive_task(board_text: str, archive_text: str, task_id: str) -> tuple[str, str]:
    if task_id in archive_text:
        raise ValueError(f"{task_id} already appears in {BOARD_ARCHIVE.relative_to(REPO_ROOT)}")
    lines = board_text.splitlines()
    kept: list[str] = []
    matched: str | None = None
    for line in lines:
        if line.startswith(f"| {task_id} |"):
            matched = line
            continue
        kept.append(line)
    if matched is None:
        raise ValueError(f"{task_id} not found in {BOARD.relative_to(REPO_ROOT)}")
    upper = matched.upper()
    if "STATUS: COMPLETE" not in upper and "STATUS: BLOCKED" not in upper:
        raise ValueError(f"{task_id} is not complete or blocked")
    task_section = Section(f"## Archived Complete - {task_id}", build_task_archive_section(task_id, matched))
    archive_sections = _combine_archive_sections(archive_text, [task_section])
    new_archive = archive_header() + "\n".join(archive_sections)
    return "\n".join(kept).rstrip() + "\n", new_archive


def build_outputs(board_text: str, archive_text: str) -> tuple[str, str, int]:
    sections = split_sections(board_text)
    moved_sections = [s for s in sections if is_archived_section(s)]
    live_sections = [s for s in sections if not is_archived_section(s) and not is_archive_pointer(s)]

    pointer = archive_pointer()
    new_board_parts: list[str] = []
    inserted_pointer = False
    for section in live_sections:
        if section.heading == "## Board Rules" and not inserted_pointer:
            new_board_parts.append(pointer)
            inserted_pointer = True
        new_board_parts.append(section.text.strip() + "\n")
    if not inserted_pointer:
        new_board_parts.append(pointer)

    archive_sections = _combine_archive_sections(archive_text, moved_sections)
    new_archive = archive_header() + "\n".join(archive_sections)
    new_board = "\n".join(part.rstrip() for part in new_board_parts if part.strip()) + "\n"
    return new_board, new_archive, len(moved_sections)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Rewrite BOARD.md and BOARD_ARCHIVE.md.")
    parser.add_argument("--check", action="store_true", help="Fail if archived sections remain on the live board.")
    parser.add_argument("--archive-task", help="Move one COMPLETE/BLOCKED live board row directly into the archive.")
    args = parser.parse_args()

    board_text = BOARD.read_text(encoding="utf-8", errors="replace") if BOARD.exists() else ""
    archive_text = BOARD_ARCHIVE.read_text(encoding="utf-8", errors="replace") if BOARD_ARCHIVE.exists() else ""
    if args.archive_task:
        try:
            new_board, new_archive = archive_task(board_text, archive_text, args.archive_task)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"archive_task={args.archive_task}")
        if not args.apply:
            print("dry_run=true; pass --apply to rewrite files")
            return 0
        BOARD.write_text(new_board, encoding="utf-8")
        BOARD_ARCHIVE.write_text(new_archive, encoding="utf-8")
        print("applied=true")
        return 0

    new_board, new_archive, moved = build_outputs(board_text, archive_text)

    remaining = [s.heading for s in split_sections(board_text) if is_archived_section(s)]
    if args.check:
        errors = []
        if remaining:
            errors.append(f"archived sections remain on live board: {len(remaining)}")
        if not BOARD_ARCHIVE.exists():
            errors.append(f"missing archive file: {BOARD_ARCHIVE.relative_to(REPO_ROOT)}")
        if errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
            return 1
        print("board_archive: OK")
        return 0

    print(f"live_board={BOARD.relative_to(REPO_ROOT)} archive={BOARD_ARCHIVE.relative_to(REPO_ROOT)} archived_sections_to_move={moved}")
    if not args.apply:
        print("dry_run=true; pass --apply to rewrite files")
        return 0

    BOARD.write_text(new_board, encoding="utf-8")
    BOARD_ARCHIVE.write_text(new_archive, encoding="utf-8")
    print("applied=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
