#!/usr/bin/env python3
"""Summarize git status without dumping thousands of paths."""
from __future__ import annotations

import argparse
import collections
import subprocess
from pathlib import Path


def repo_root() -> Path:
    out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True)
    return Path(out.strip())


def status_entries(untracked: str) -> list[tuple[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", f"--untracked-files={untracked}"],
        text=False,
        stdout=subprocess.PIPE,
        check=True,
    )
    parts = [p.decode("utf-8", "replace") for p in proc.stdout.split(b"\0") if p]
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(parts):
        item = parts[i]
        code = item[:2]
        path = item[3:]
        entries.append((code, path))
        if code.startswith("R") or code.startswith("C"):
            i += 2
        else:
            i += 1
    return entries


def top_dirs(paths: list[str], depth: int) -> list[tuple[str, int]]:
    counts: collections.Counter[str] = collections.Counter()
    for path in paths:
        parts = path.split("/")
        key = "/".join(parts[: min(depth, len(parts))])
        counts[key] += 1
    return counts.most_common()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--untracked", choices=["all", "normal", "no"], default="all")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--dir-depth", type=int, default=3)
    args = parser.parse_args()

    root = repo_root()
    entries = status_entries(args.untracked)
    counts = collections.Counter(code for code, _path in entries)
    untracked_paths = [path for code, path in entries if code == "??"]

    print(f"repo={root}")
    print(f"entries={len(entries)} untracked={len(untracked_paths)}")
    print("status_counts:")
    for code, count in sorted(counts.items()):
        print(f"  - {code!r}: {count}")
    if untracked_paths:
        print("top_untracked_dirs:")
        for path, count in top_dirs(untracked_paths, args.dir_depth)[: args.limit]:
            print(f"  - {path}: {count}")
    print("examples:")
    for code, path in entries[: args.limit]:
        print(f"  - {code} {path}")
    if len(entries) > args.limit:
        print(f"... {len(entries) - args.limit} more entries omitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
