#!/usr/bin/env python3
"""Print a bounded brief from generated repo state and blocker docs."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import BLOCKERS, STATE, read_text  # noqa: E402

HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


def extract_sections(text: str, names: set[str]) -> dict[str, list[str]]:
    current = None
    out: dict[str, list[str]] = {name: [] for name in names}
    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group(1).strip()
            current = title if title in names else None
            continue
        if current:
            out[current].append(line)
    return {key: value for key, value in out.items() if value}


def first_nonempty_lines(text: str, limit: int = 20) -> list[str]:
    out = []
    for line in text.splitlines():
        if line.strip():
            out.append(line)
        if len(out) >= limit:
            break
    return out


def blocker_open_table(text: str, limit: int = 40) -> list[str]:
    lines: list[str] = []
    in_open = False
    for line in text.splitlines():
        if line.startswith("## Open"):
            in_open = True
        elif in_open and line.startswith("## "):
            break
        if in_open:
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def build_brief(*, active: bool, blockers: bool, recent: int, tag: str | None) -> dict[str, object]:
    state_text = read_text(STATE) if STATE.exists() else ""
    blocker_text = read_text(BLOCKERS) if BLOCKERS.exists() else ""
    data: dict[str, object] = {
        "state_path": str(STATE),
        "blockers_path": str(BLOCKERS),
        "state_header": first_nonempty_lines(state_text, 12),
    }
    sections = extract_sections(state_text, {"Active Board Tasks", "Recent Activity", "Open Blockers"})
    if active:
        data["active_board_tasks"] = sections.get("Active Board Tasks", [])[:80]
    if recent:
        data["recent_activity"] = sections.get("Recent Activity", [])[:recent]
    if blockers:
        data["open_blockers"] = sections.get("Open Blockers", [])[:40] or blocker_open_table(blocker_text, 40)
    if tag:
        matches = [line for line in state_text.splitlines() if tag.lower() in line.lower()]
        data["tag_matches"] = matches[:80]
        data["tag_match_count"] = len(matches)
    return data


def print_human(data: dict[str, object]) -> None:
    print("state_header:")
    for line in data.get("state_header", []):
        print(f"  {line}")
    for key in ("active_board_tasks", "open_blockers", "recent_activity", "tag_matches"):
        if key not in data:
            continue
        lines = data[key]
        print(f"\n{key}:")
        for line in lines:
            if line.strip():
                print(f"  {line}")
        if key == "tag_matches":
            print(f"  tag_match_count={data.get('tag_match_count', 0)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", action="store_true", help="Include Active Board Tasks from .agent/STATE.md.")
    parser.add_argument("--blockers", action="store_true", help="Include Open Blockers from generated docs.")
    parser.add_argument("--recent", type=int, default=0, help="Include up to N lines of Recent Activity.")
    parser.add_argument("--tag", help="Bounded substring search in .agent/STATE.md.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    include_active = args.active or not any([args.active, args.blockers, args.recent, args.tag])
    include_blockers = args.blockers or not any([args.active, args.blockers, args.recent, args.tag])
    data = build_brief(active=include_active, blockers=include_blockers, recent=max(args.recent, 0), tag=args.tag)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
