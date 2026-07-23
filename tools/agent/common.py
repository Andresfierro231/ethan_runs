#!/usr/bin/env python3
"""Shared helpers for repo-local agent coordination tools."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
BOARD = REPO_ROOT / ".agent" / "BOARD.md"
BOARD_ARCHIVE = REPO_ROOT / ".agent" / "BOARD_ARCHIVE.md"
STATE = REPO_ROOT / ".agent" / "STATE.md"
BLOCKERS = REPO_ROOT / ".agent" / "BLOCKERS.md"
CATALOG_JSON = REPO_ROOT / ".agent" / "catalog.json"

TASK_RE = re.compile(r"\b(AGENT-\d+|TODO-[A-Z0-9-]+|T\d+|F\d+)\b")
CODE_SPAN_RE = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class BoardRow:
    task_id: str
    role: str
    owner: str
    scope: str
    goal: str
    line_no: int
    source_path: Path | None = None

    @property
    def status(self) -> str:
        text = self.goal.upper()
        if "STATUS: COMPLETE" in text:
            return "complete"
        if "STATUS: BLOCKED" in text:
            return "blocked"
        if "STATUS: ACTIVE" in text:
            return "active"
        if "STATUS: RUNNING" in text:
            return "running"
        if "STATUS: SUBMITTED" in text:
            return "submitted"
        if "STATUS: PENDING" in text:
            return "pending"
        if self.task_id.startswith("TODO-"):
            return "open"
        return "unknown"

    @property
    def is_open(self) -> bool:
        return self.status in {"active", "running", "submitted", "pending", "blocked", "open"}

    @property
    def edit_paths(self) -> list[str]:
        editable_scope = self.scope.split("READ-ONLY:", 1)[0]
        return [p for p in CODE_SPAN_RE.findall(editable_scope) if p and " " not in p[:2]]

    @property
    def readonly_paths(self) -> list[str]:
        if "READ-ONLY:" not in self.scope:
            return []
        readonly_scope = self.scope.split("READ-ONLY:", 1)[1]
        return CODE_SPAN_RE.findall(readonly_scope)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_json_stdout(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def iter_files(paths: Iterable[Path], suffixes: tuple[str, ...] = (".md", ".csv", ".json", ".py", ".txt")) -> Iterable[Path]:
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix in suffixes:
                yield path
            continue
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
            for name in files:
                p = Path(root) / name
                if p.suffix in suffixes:
                    yield p


def _parse_board_file(path: Path) -> list[BoardRow]:
    rows: list[BoardRow] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.startswith("| "):
            continue
        if line.startswith("| ---") or line.startswith("| Task ID"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        if not TASK_RE.fullmatch(cells[0]):
            continue
        rows.append(BoardRow(cells[0], cells[1], cells[2], cells[3], "|".join(cells[4:]).strip(), line_no, path))
    return rows


def parse_board(path: Path = BOARD, *, include_archive: bool = False) -> list[BoardRow]:
    """Parse board rows.

    By default this reads only the live board. Use ``include_archive=True`` for
    closeout/history checks that must still find rows moved out of the live
    coordination file.
    """
    rows = _parse_board_file(path)
    if include_archive and path == BOARD:
        rows.extend(_parse_board_file(BOARD_ARCHIVE))
    return rows


def find_task(task_id: str, rows: list[BoardRow] | None = None) -> BoardRow | None:
    rows = rows if rows is not None else parse_board()
    for row in rows:
        if row.task_id == task_id:
            return row
    return None


def path_overlaps(a: str, b: str) -> bool:
    if not a or not b:
        return False
    a = a.rstrip("/")
    b = b.rstrip("/")
    if a in {".agent/BOARD.md", "own row only"} or b in {".agent/BOARD.md", "own row only"}:
        return False
    if "**" in a:
        a = a.split("**", 1)[0].rstrip("/")
    if "**" in b:
        b = b.split("**", 1)[0].rstrip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def active_conflicts(row: BoardRow, rows: list[BoardRow] | None = None) -> list[dict[str, str]]:
    rows = rows if rows is not None else parse_board()
    out: list[dict[str, str]] = []
    for other in rows:
        if other.task_id == row.task_id or not other.is_open:
            continue
        for mine in row.edit_paths:
            for theirs in other.edit_paths:
                if path_overlaps(mine, theirs):
                    out.append({"task_id": other.task_id, "mine": mine, "theirs": theirs, "status": other.status})
    return out


def task_artifact_globs(task_id: str) -> dict[str, list[Path]]:
    return {
        "status": sorted((REPO_ROOT / ".agent" / "status").glob(f"*{task_id}.md")),
        "journal": sorted((REPO_ROOT / ".agent" / "journal").glob(f"*/*{task_id.lower()}*.md")),
        "imports": sorted((REPO_ROOT / "imports").glob(f"*{task_id.lower().replace('-', '_')}*.json")),
    }


def contains_task(path: Path, task_id: str) -> bool:
    if not path.exists():
        return False
    return task_id in read_text(path)


def run_check(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def add_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repo root; defaults to this ethan_runs checkout.")
