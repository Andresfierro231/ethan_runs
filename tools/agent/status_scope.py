#!/usr/bin/env python3
"""Print git status for explicit paths only."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="One or more explicit paths to inspect.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root.")
    args = parser.parse_args()

    if not args.paths:
        print("ERROR: provide explicit paths; full-repo status is intentionally refused.", file=sys.stderr)
        return 2
    root = Path(args.root)
    cmd = ["git", "-C", str(root), "status", "--short", "--", *args.paths]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
