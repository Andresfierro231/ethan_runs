#!/usr/bin/env python3
"""Quietly validate JSON import manifests without pretty-printing them."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--check-paths", action="store_true", help="Require every changed_files path to exist.")
    parser.add_argument("--quiet", action="store_true", help="Print nothing on success.")
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: {args.manifest}: invalid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print(f"ERROR: {args.manifest}: top-level JSON must be an object", file=sys.stderr)
        return 1

    errors: list[str] = []
    changed = data.get("changed_files", [])
    if args.check_paths:
        if not isinstance(changed, list):
            errors.append("changed_files must be a list when --check-paths is used")
        else:
            for item in changed:
                if not isinstance(item, str):
                    errors.append(f"changed_files item is not a string: {item!r}")
                    continue
                if not (REPO_ROOT / item).exists():
                    errors.append(f"changed file does not exist: {item}")

    if errors:
        for error in errors:
            print(f"ERROR: {args.manifest}: {error}", file=sys.stderr)
        return 1

    if not args.quiet:
        changed_count = len(changed) if isinstance(changed, list) else 0
        print(f"OK {args.manifest} changed_files={changed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
