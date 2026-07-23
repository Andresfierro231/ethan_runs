#!/usr/bin/env python3
"""Print compact open-blocker state without dumping blocker notes."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import BLOCKERS, rel  # noqa: E402


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_open_blockers(text: str) -> list[dict[str, str]]:
    """Parse the generated ``.agent/BLOCKERS.md`` open-blocker table."""
    rows: list[dict[str, str]] = []
    in_open = False
    headers: list[str] = []
    for line in text.splitlines():
        if line.startswith("## Open"):
            in_open = True
            continue
        if in_open and line.startswith("## "):
            break
        if not in_open or not line.startswith("| "):
            continue
        cells = _split_row(line)
        if cells and all(set(cell) <= {"-", " "} for cell in cells):
            continue
        if cells and cells[0] == "id":
            headers = cells
            continue
        if not headers or len(cells) < len(headers):
            continue
        row = dict(zip(headers, cells))
        row["id"] = row.get("id", "").strip("`")
        row["evidence"] = row.get("evidence", "").strip("`")
        rows.append(row)
    return rows


def build_report(path: Path = BLOCKERS, *, limit: int = 20) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    blockers = parse_open_blockers(text)[: max(limit, 0)]
    return {
        "path": rel(path),
        "open_count": len(parse_open_blockers(text)),
        "shown": len(blockers),
        "blockers": blockers,
    }


def print_human(data: dict[str, object], *, show_evidence: bool = True) -> None:
    print(f"open_blockers={data['open_count']} shown={data['shown']} source={data['path']}")
    for row in data["blockers"]:
        parts = [
            f"id={row.get('id', '')}",
            f"severity={row.get('severity', '')}",
            f"blocks={row.get('blocks', '')}",
            f"reviewed={row.get('last reviewed', '')}",
        ]
        print("  - " + " ".join(parts))
        if show_evidence:
            print(f"    evidence={row.get('evidence', '')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=str(BLOCKERS), help="Generated BLOCKERS.md path.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum open blockers to print.")
    parser.add_argument("--no-evidence", action="store_true", help="Omit evidence paths in human output.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"missing blocker file: {path}", file=sys.stderr)
        return 1
    data = build_report(path, limit=args.limit)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data, show_evidence=not args.no_evidence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
