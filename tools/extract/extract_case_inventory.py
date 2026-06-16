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
    csv_dump,
    get_registry_row,
    iso_timestamp,
    json_dump,
    load_case_metadata,
    path_lookup,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract case inventory from a registered source.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry_path = WORKSPACE_ROOT / "registry" / "case_registry.csv"
    row = get_registry_row(registry_path, args.source_id)
    source_root = Path(row["source_root"]).resolve()
    metadata = load_case_metadata(source_root)

    inventory = {
        "generated_at": iso_timestamp(),
        "source_id": row["source_id"],
        "case_id": row["case_id"],
        "source_root": row["source_root"],
        "fluid": path_lookup(metadata, "fluid"),
        "turbulence_model": path_lookup(metadata, "turbulence_model"),
        "nprocs": path_lookup(metadata, "nprocs"),
        "scale_to_meters": path_lookup(metadata, "scale_to_meters"),
        "walltime": path_lookup(metadata, "walltime"),
        "top_level_entries": sorted(item.name for item in source_root.iterdir()),
        "core_case_paths": {
            "zero_dir": str(source_root / "0") if (source_root / "0").exists() else "",
            "constant_dir": str(source_root / "constant") if (source_root / "constant").exists() else "",
            "system_dir": str(source_root / "system") if (source_root / "system").exists() else "",
            "post_processing_dir": str(source_root / "postProcessing") if (source_root / "postProcessing").exists() else "",
        },
        "operating_point": {
            "heater_power_W": path_lookup(metadata, "operating_point.heater_power_W"),
            "cooling_power_W": path_lookup(metadata, "operating_point.cooling_power_W"),
            "T_init_K": path_lookup(metadata, "operating_point.T_init_K"),
        },
        "mesh_summary": {
            "mesh_group_id": path_lookup(metadata, "mesh_group_id"),
            "kernel_factor": path_lookup(metadata, "mesh_settings.kernel_factor"),
            "kernel_blend": path_lookup(metadata, "mesh_settings.kernel_blend"),
            "core_ratio": path_lookup(metadata, "mesh_settings.core_ratio"),
            "first_cell_size": path_lookup(metadata, "mesh_settings.inflation.first_cell_size"),
            "bulk_cell_size": path_lookup(metadata, "mesh_settings.inflation.bulk_cell_size"),
        },
        "convergence_summary": {
            "enabled": path_lookup(metadata, "convergence.enabled"),
            "check_interval": path_lookup(metadata, "convergence.check_interval"),
            "min_iterations": path_lookup(metadata, "convergence.min_iterations"),
            "qoi_rtol": path_lookup(metadata, "convergence.qoi.rtol"),
            "qoi_window": path_lookup(metadata, "convergence.qoi.window"),
        },
    }

    output_root = WORKSPACE_ROOT / "work_products" / row["source_id"]
    json_dump(output_root / "case_inventory.json", inventory)
    csv_dump(
        output_root / "case_inventory.csv",
        [
            "source_id",
            "case_id",
            "fluid",
            "turbulence_model",
            "nprocs",
            "scale_to_meters",
            "heater_power_W",
            "cooling_power_W",
            "T_init_K",
            "mesh_group_id",
        ],
        [
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "fluid": inventory["fluid"],
                "turbulence_model": inventory["turbulence_model"],
                "nprocs": inventory["nprocs"],
                "scale_to_meters": inventory["scale_to_meters"],
                "heater_power_W": inventory["operating_point"]["heater_power_W"],
                "cooling_power_W": inventory["operating_point"]["cooling_power_W"],
                "T_init_K": inventory["operating_point"]["T_init_K"],
                "mesh_group_id": inventory["mesh_summary"]["mesh_group_id"],
            }
        ],
    )
    print(json.dumps({"source_id": row["source_id"], "output_root": str(output_root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
