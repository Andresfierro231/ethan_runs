#!/usr/bin/env python3
"""Audit staged files for size, generated-output risk, and active-path overlap."""
from __future__ import annotations

import argparse
import collections
import fnmatch
import subprocess
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import BOARD, BoardRow  # noqa: E402
from tools.agent.board_summary import parse_section_rows  # noqa: E402

DEFAULT_HEAVY_PATTERNS = [
    "work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/**/*.svg",
    "work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation*/**/*.svg",
    "work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation*/**/*.png",
    "work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/**/*",
    "work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/**/*",
    "figures_rendered/**/*",
]


def repo_root() -> Path:
    out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True)
    return Path(out.strip())


def staged_paths() -> list[str]:
    proc = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"], stdout=subprocess.PIPE, check=True)
    return [p.decode("utf-8", "replace") for p in proc.stdout.split(b"\0") if p]


def path_size(root: Path, rel: str) -> int:
    path = root / rel
    return path.stat().st_size if path.exists() and path.is_file() else 0


def active_edit_patterns() -> dict[str, list[str]]:
    patterns: dict[str, list[str]] = {}
    for entry in parse_section_rows(BOARD):
        if entry["section"] != "Active":
            continue
        row = entry["row"]
        assert isinstance(row, BoardRow)
        if not row.is_open:
            continue
        patterns[row.task_id] = row.edit_paths
    return patterns


def matches(pattern: str, path: str) -> bool:
    pattern = pattern.strip()
    if not pattern:
        return False
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3].rstrip("/") + "/")
    return fnmatch.fnmatch(path, pattern) or path == pattern.rstrip("/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--forbid-prefix", action="append", default=[])
    args = parser.parse_args()

    root = repo_root()
    paths = staged_paths()
    sizes = [(rel, path_size(root, rel)) for rel in paths]
    total = sum(size for _rel, size in sizes)
    ext_counts = collections.Counter(Path(rel).suffix.lower() or "(none)" for rel in paths)

    print(f"staged_files={len(paths)} staged_bytes={total} staged_mib={total / (1024 * 1024):.2f}")
    print("extension_counts:")
    for ext, count in ext_counts.most_common():
        print(f"  - {ext}: {count}")
    print("largest_staged_files:")
    for rel, size in sorted(sizes, key=lambda item: item[1], reverse=True)[: args.limit]:
        print(f"  - {size / (1024 * 1024):8.2f} MiB  {rel}")

    heavy_hits = [rel for rel in paths if any(fnmatch.fnmatch(rel, pat) for pat in DEFAULT_HEAVY_PATTERNS)]
    if heavy_hits:
        print("known_generated_heavy_hits:")
        for rel in heavy_hits[: args.limit]:
            print(f"  - {rel}")
        if len(heavy_hits) > args.limit:
            print(f"  ... {len(heavy_hits) - args.limit} more")

    forbid_hits = [rel for rel in paths if any(rel.startswith(prefix.rstrip("/") + "/") or rel == prefix.rstrip("/") for prefix in args.forbid_prefix)]
    if forbid_hits:
        print("forbid_prefix_hits:")
        for rel in forbid_hits[: args.limit]:
            print(f"  - {rel}")

    active_patterns = active_edit_patterns()
    overlaps: list[tuple[str, str]] = []
    for rel in paths:
        for task_id, patterns in active_patterns.items():
            if any(matches(pattern, rel) for pattern in patterns):
                overlaps.append((task_id, rel))
                break
    if overlaps:
        print("active_scope_hits:")
        for task_id, rel in overlaps[: args.limit]:
            print(f"  - {task_id}: {rel}")
        if len(overlaps) > args.limit:
            print(f"  ... {len(overlaps) - args.limit} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
