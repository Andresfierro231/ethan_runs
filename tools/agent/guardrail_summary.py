#!/usr/bin/env python3
"""Run a noisy validation command and print a bounded pass/fail summary."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

SUMMARY_RE = re.compile(r"\b(PASS|FAIL|ERROR|WARNING|WARN|NOTE|OK)\b|== .+ ==")


def summarize(lines: list[str], *, limit: int) -> list[str]:
    selected: list[str] = []
    for line in lines:
        if SUMMARY_RE.search(line):
            selected.append(line)
    if not selected and lines:
        selected = lines[: min(limit, len(lines))]
    return selected[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--verbose", action="store_true", help="Print full command output after the summary.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run, preceded by -- when needed.")
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("usage: guardrail_summary.py [--limit N] [--verbose] -- <command> [args...]")

    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = proc.stdout.splitlines()
    summary = summarize(lines, limit=args.limit)

    print(f"command={' '.join(command)}")
    print(f"exit_code={proc.returncode}")
    print(f"output_lines={len(lines)}")
    print("summary:")
    for line in summary:
        print(line)
    if len(summary) == args.limit and len(lines) > args.limit:
        print(f"... summary limited to {args.limit} lines; use --verbose for full output")
    if args.verbose:
        print("full_output:")
        sys.stdout.write(proc.stdout)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
