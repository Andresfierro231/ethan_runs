#!/usr/bin/env python3
"""Run ripgrep with broad-search guardrails and bounded total output."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT  # noqa: E402


BROAD_PATHS = {".", str(REPO_ROOT), ""}


def _is_broad(paths: list[str]) -> bool:
    if not paths:
        return True
    return any(path in BROAD_PATHS for path in paths)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern")
    parser.add_argument("paths", nargs="*", default=["."], help="Paths to search.")
    parser.add_argument("--glob", action="append", default=[], help="rg glob; repeatable.")
    parser.add_argument("--type", dest="types", action="append", default=[], help="rg file type; repeatable.")
    parser.add_argument("--max-count", type=int, default=20, help="Maximum matches per file.")
    parser.add_argument("--max-lines", type=int, default=200, help="Maximum total output lines before stopping rg.")
    parser.add_argument("--context", type=int, default=0)
    parser.add_argument("--allow-broad", action="store_true", help="Allow searching . without --glob or --type.")
    parser.add_argument("--files-with-matches", action="store_true")
    args = parser.parse_args()

    if not args.pattern:
        print("ERROR: pattern must not be empty", file=sys.stderr)
        return 2
    if args.max_count < 1 or args.max_lines < 1:
        print("ERROR: --max-count and --max-lines must be positive", file=sys.stderr)
        return 2
    if _is_broad(args.paths) and not args.allow_broad and not args.glob and not args.types:
        print(
            "ERROR: broad search refused. Add a path/glob/type or pass --allow-broad deliberately.",
            file=sys.stderr,
        )
        return 2

    cmd = ["rg", "-n", "--max-count", str(args.max_count)]
    if args.context:
        cmd.extend(["--context", str(args.context)])
    if args.files_with_matches:
        cmd.append("--files-with-matches")
    for item in args.glob:
        cmd.extend(["--glob", item])
    for item in args.types:
        cmd.extend(["--type", item])
    cmd.append(args.pattern)
    cmd.extend(args.paths)

    proc = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    line_count = 0
    truncated = False
    for line in proc.stdout:
        if line_count >= args.max_lines:
            truncated = True
            proc.kill()
            break
        print(line, end="")
        line_count += 1
    _, stderr = proc.communicate()
    if stderr:
        print(stderr, end="", file=sys.stderr)
    if truncated:
        print(f"safe_rg: stopped after --max-lines={args.max_lines}", file=sys.stderr)
        return 3
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
