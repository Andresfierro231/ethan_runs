#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    get_registry_row,
    iso_timestamp,
    load_case_metadata,
    load_workspace_config,
    path_lookup,
    resolve_workspace_path,
    slugify,
    source_size_bytes,
    upsert_registry_row,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register a local CFD case source.")
    parser.add_argument("--source-path", required=True, help="Absolute or relative source case path.")
    parser.add_argument("--source-id", help="Stable source identifier. Defaults to the source directory name.")
    parser.add_argument("--case-id", help="Case identifier override.")
    parser.add_argument("--source-owner", help="Source ownership label override.")
    parser.add_argument("--link-name", help="Local symlink name override.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_workspace_config()
    source_path = Path(args.source_path).expanduser().resolve()
    if not source_path.exists() or not source_path.is_dir():
        raise SystemExit(f"Source path does not exist or is not a directory: {source_path}")

    metadata = load_case_metadata(source_path)
    case_id = args.case_id or path_lookup(metadata, "operating_point.case_id", source_path.name)
    source_id = args.source_id or slugify(source_path.name)
    source_owner = args.source_owner or config["default_source_owner"]

    link_root = resolve_workspace_path(config["local_link_root"])
    link_name = args.link_name or source_id
    link_path = link_root / link_name
    if link_path.exists() or link_path.is_symlink():
        if not link_path.is_symlink() or link_path.resolve() != source_path:
            raise SystemExit(f"Refusing to overwrite existing non-matching link target: {link_path}")
    else:
        link_path.symlink_to(source_path, target_is_directory=True)

    row = {
        "source_id": source_id,
        "case_id": str(case_id),
        "source_owner": str(source_owner),
        "source_root": str(source_path),
        "local_link_path": str(link_path),
        "registered_at": iso_timestamp(),
        "size_bytes": str(source_size_bytes(source_path)),
        "status": "registered",
    }
    registry_path = WORKSPACE_ROOT / "registry" / "case_registry.csv"
    upsert_registry_row(registry_path, row)

    summary = get_registry_row(registry_path, source_id)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
