#!/usr/bin/env python3
"""Summarize git diffs without printing full hunks by default."""
from __future__ import annotations

import argparse
import collections
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiffSummary:
    mode: str
    paths: list[str]
    changed_files: list[str]
    untracked_files: list[str]
    stat_lines: list[str]
    name_status: list[str]


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode not in {0, 1}:
        raise SystemExit(proc.stdout.strip() or f"git {' '.join(args)} failed with {proc.returncode}")
    return proc.stdout


def repo_root() -> Path:
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())


def path_args(paths: list[str]) -> list[str]:
    return ["--", *paths] if paths else []


def diff_base_args(mode: str) -> list[str]:
    if mode == "staged":
        return ["diff", "--cached"]
    if mode == "unstaged":
        return ["diff"]
    if mode == "head":
        return ["diff", "HEAD"]
    raise ValueError(mode)


def collect_summary(mode: str, paths: list[str]) -> DiffSummary:
    base = diff_base_args(mode)
    suffix = path_args(paths)
    name_status = [line for line in run_git([*base, "--name-status", *suffix]).splitlines() if line.strip()]
    stat_lines = [line for line in run_git([*base, "--stat", "--compact-summary", *suffix]).splitlines() if line.strip()]
    untracked_files = [line for line in run_git(["ls-files", "--others", "--exclude-standard", *suffix]).splitlines() if line.strip()]
    changed_files: list[str] = []
    for line in name_status:
        parts = line.split("\t")
        if len(parts) >= 2:
            changed_files.append(parts[-1])
    return DiffSummary(
        mode=mode,
        paths=paths,
        changed_files=changed_files,
        untracked_files=untracked_files,
        stat_lines=stat_lines,
        name_status=name_status,
    )


def top_dirs(paths: list[str], depth: int) -> list[tuple[str, int]]:
    counts: collections.Counter[str] = collections.Counter()
    for path in paths:
        parts = path.split("/")
        key = "/".join(parts[: min(depth, len(parts))])
        counts[key] += 1
    return counts.most_common()


def print_summary(
    summary: DiffSummary,
    *,
    limit: int,
    dir_depth: int,
    include_stat: bool,
    include_names: bool,
    include_untracked: bool,
) -> None:
    root = repo_root()
    print(f"repo={root}")
    print(f"mode={summary.mode}")
    print(f"path_scope={' '.join(summary.paths) if summary.paths else '(repo-wide)'}")
    print(f"changed_files={len(summary.changed_files)}")
    if include_untracked:
        print(f"untracked_files={len(summary.untracked_files)}")
    if summary.changed_files:
        print("top_dirs:")
        for path, count in top_dirs(summary.changed_files, dir_depth)[:limit]:
            print(f"  - {path}: {count}")
    if include_untracked and summary.untracked_files:
        print("untracked_examples:")
        for path in summary.untracked_files[:limit]:
            print(f"  - {path}")
        if len(summary.untracked_files) > limit:
            print(f"  ... {len(summary.untracked_files) - limit} more untracked paths omitted")
    if include_stat and summary.stat_lines:
        print("stat:")
        for line in summary.stat_lines[:limit]:
            print(f"  {line}")
        if len(summary.stat_lines) > limit:
            print(f"  ... {len(summary.stat_lines) - limit} more stat lines omitted")
    if include_names and summary.name_status:
        print("name_status:")
        for line in summary.name_status[:limit]:
            print(f"  {line}")
        if len(summary.name_status) > limit:
            print(f"  ... {len(summary.name_status) - limit} more paths omitted")
    if not summary.changed_files and (not include_untracked or not summary.untracked_files):
        print("diff: clean for selected mode/path scope")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Optional path scope passed after git --.")
    parser.add_argument("--mode", choices=["unstaged", "staged", "head"], default="unstaged")
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--dir-depth", type=int, default=3)
    parser.add_argument("--names", action="store_true", help="Print bounded name-status lines.")
    parser.add_argument("--no-stat", action="store_true", help="Suppress bounded git diff --stat output.")
    parser.add_argument("--no-untracked", action="store_true", help="Suppress bounded untracked-file examples.")
    parser.add_argument("--require-paths", action="store_true", help="Fail instead of running repo-wide.")
    args = parser.parse_args()

    if args.require_paths and not args.paths:
        raise SystemExit("--require-paths was set but no paths were provided")
    summary = collect_summary(args.mode, args.paths)
    print_summary(
        summary,
        limit=args.limit,
        dir_depth=args.dir_depth,
        include_stat=not args.no_stat,
        include_names=args.names,
        include_untracked=not args.no_untracked,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
