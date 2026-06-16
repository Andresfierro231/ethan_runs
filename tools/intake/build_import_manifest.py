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
    date_stamp,
    get_registry_row,
    iso_timestamp,
    json_dump,
    load_case_metadata,
    load_workspace_config,
    path_lookup,
    relative_to_workspace,
    resolve_workspace_path,
    top_level_key_files,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an import manifest for a registered case.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    parser.add_argument(
        "--provenance-note",
        default="Read-only import manifest for Ethan case intake.",
        help="Human-readable provenance note.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry_path = WORKSPACE_ROOT / "registry" / "case_registry.csv"
    row = get_registry_row(registry_path, args.source_id)
    config = load_workspace_config()
    source_root = Path(row["source_root"]).resolve()
    metadata = load_case_metadata(source_root)
    stage_root = resolve_workspace_path(config["local_staging_root"])

    local_stage_root = ""
    try:
        source_root.relative_to(stage_root)
        local_stage_root = str(source_root)
    except ValueError:
        local_stage_root = ""

    manifest = {
        "generated_at": iso_timestamp(),
        "source_id": row["source_id"],
        "source_owner": row["source_owner"],
        "source_root": row["source_root"],
        "local_stage_root": local_stage_root,
        "local_link_path": row["local_link_path"],
        "case_id": row["case_id"],
        "ingested_at": row["registered_at"],
        "size_bytes": int(row["size_bytes"]),
        "key_files": top_level_key_files(source_root),
        "native_outputs_policy": config["native_outputs_policy"],
        "provenance_note": args.provenance_note,
        "case_summary": {
            "fluid": path_lookup(metadata, "fluid"),
            "turbulence_model": path_lookup(metadata, "turbulence_model"),
            "heater_power_W": path_lookup(metadata, "operating_point.heater_power_W"),
            "cooling_power_W": path_lookup(metadata, "operating_point.cooling_power_W"),
            "T_init_K": path_lookup(metadata, "operating_point.T_init_K"),
            "nprocs": path_lookup(metadata, "nprocs"),
        },
    }
    output_path = WORKSPACE_ROOT / "imports" / f"{date_stamp()}_{row['source_id']}_import.json"
    json_dump(output_path, manifest)

    print(
        json.dumps(
            {
                "manifest_path": relative_to_workspace(output_path),
                "source_id": row["source_id"],
                "case_id": row["case_id"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
