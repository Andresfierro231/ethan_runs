#!/usr/bin/env python3
"""Add bounded report links to standard agent discovery files."""
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ is None or __package__ == "":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT, rel  # noqa: E402


TARGETS = {
    "start": REPO_ROOT / "operational_notes" / "START_HERE_FOR_AGENTS.md",
    "maps": REPO_ROOT / "operational_notes" / "maps" / "README.md",
    "litrev": REPO_ROOT / "operational_notes" / "maps" / "literature-synthesis-and-gates.md",
    "forward": REPO_ROOT / "operational_notes" / "maps" / "forward-predictive-model.md",
    "thesis": REPO_ROOT / "reports" / "thesis_dossier" / "README.md",
}


def _insert_after(text: str, anchor: str, block: str) -> str:
    if block.strip() in text:
        return text
    idx = text.find(anchor)
    if idx == -1:
        return text.rstrip() + "\n\n" + block.rstrip() + "\n"
    end = idx + len(anchor)
    return text[:end].rstrip() + "\n\n" + block.rstrip() + "\n" + text[end:].lstrip("\n")


def update_target(path: Path, report_rel: str, title: str) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if report_rel in text:
        return False, text
    if path.name == "README.md" and "Topic Maps" in text:
        block = f"| {title} | `../../{report_rel}` | #report #model-forms #source-gates |"
        return True, _insert_after(text, "| Literature synthesis & gates | `literature-synthesis-and-gates.md` | #litrev-synthesis #closure-ledger |", block)
    if "START_HERE_FOR_AGENTS" in str(path):
        block = f"Latest linked report: `{report_rel}`.\nOpen it before related follow-up work."
        return True, _insert_after(text, "## Before Editing", block)
    block = f"Linked report: `{report_rel}`.\nUse it before related follow-up work."
    return True, _insert_after(text, "## Current status", block)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--title", default="Linked report")
    parser.add_argument("--targets", default="start,maps,litrev,forward,thesis")
    parser.add_argument("--write", action="store_true", help="Write changes. Default is dry-run.")
    args = parser.parse_args()

    report = args.report
    report_rel = rel(report if report.is_absolute() else REPO_ROOT / report)
    target_names = [item.strip() for item in args.targets.split(",") if item.strip()]
    unknown = [item for item in target_names if item not in TARGETS]
    if unknown:
        print(f"ERROR: unknown targets: {', '.join(unknown)}")
        return 2

    changed: list[str] = []
    for name in target_names:
        path = TARGETS[name]
        did_change, new_text = update_target(path, report_rel, args.title)
        if did_change:
            changed.append(rel(path))
            if args.write:
                path.write_text(new_text, encoding="utf-8")
    mode = "wrote" if args.write else "would_write"
    if changed:
        print(f"{mode}:")
        for item in changed:
            print(f"  - {item}")
    else:
        print("no changes needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
