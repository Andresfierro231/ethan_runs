#!/usr/bin/env python3
"""Run git diff --check on staged files while skipping noisy generated outputs."""
from __future__ import annotations

import argparse
import fnmatch
import subprocess
from pathlib import Path

DEFAULT_SKIP = [
    ".agent/catalog.csv",
    ".agent/catalog.json",
    "work_products/**/*.csv",
    "work_products/**/*.json",
    "figures_rendered/**/*",
]


def staged_paths() -> list[str]:
    proc = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"], stdout=subprocess.PIPE, check=True)
    return [p.decode("utf-8", "replace") for p in proc.stdout.split(b"\0") if p]


def should_skip(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-generated", action="store_true")
    parser.add_argument("--max-output-lines", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    paths = staged_paths()
    skip_patterns = [] if args.include_generated else DEFAULT_SKIP
    checked = [p for p in paths if not should_skip(p, skip_patterns)]
    skipped = [p for p in paths if should_skip(p, skip_patterns)]

    output_lines: list[str] = []
    code = 0
    for batch in chunks(checked, args.batch_size):
        proc = subprocess.run(["git", "diff", "--cached", "--check", "--", *batch], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode:
            code = proc.returncode
        output_lines.extend(proc.stdout.splitlines())

    print(f"staged_files={len(paths)} checked={len(checked)} skipped_generated={len(skipped)}")
    if skipped:
        print("skipped_examples:")
        for path in skipped[:10]:
            print(f"  - {path}")
    if output_lines:
        print("diff_check_output:")
        for line in output_lines[: args.max_output_lines]:
            print(line)
        if len(output_lines) > args.max_output_lines:
            print(f"... {len(output_lines) - args.max_output_lines} more lines omitted")
    else:
        print("diff_check: OK")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
