#!/usr/bin/env python3
"""Flag stale final-predictive split language in docs and tables."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT, iter_files  # noqa: E402

STALE_PATTERNS = [
    re.compile(r"Salt2\s+train\s*/\s*Salt3\s+validation\s*/\s*Salt4\s+holdout", re.I),
    re.compile(r"Salt2[- ]train\s*/\s*Salt3[- ]validation\s*/\s*Salt4[- ]holdout", re.I),
    re.compile(r"salt_?2\s*=\s*train.*salt_?3\s*=\s*validation.*salt_?4\s*=\s*holdout", re.I),
]
ALLOW_RE = re.compile(r"\b(historical|superseded|older|old|previous|development|diagnostic)\b|no longer|STATUS:\s*COMPLETE", re.I)


def line_allowed(line: str) -> bool:
    return bool(ALLOW_RE.search(line))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["operational_notes", ".agent/BOARD.md", "README.md", "AGENTS.md"])
    parser.add_argument("--allow-historical", action="store_true", default=True)
    args = parser.parse_args()

    findings: list[str] = []
    for file_path in iter_files([REPO_ROOT / p for p in args.paths], suffixes=(".md", ".csv", ".txt")):
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines, start=1):
            if any(p.search(line) for p in STALE_PATTERNS):
                if args.allow_historical and line_allowed(line):
                    continue
                findings.append(f"{file_path.relative_to(REPO_ROOT)}:{idx}: stale split language: {line.strip()}")
    if findings:
        print("\n".join(findings))
        return 1
    print("split_policy_lint: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
