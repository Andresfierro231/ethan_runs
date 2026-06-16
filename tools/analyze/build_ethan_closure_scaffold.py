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
    ensure_dir,
    get_registry_row,
    iso_timestamp,
    json_dump,
    load_case_metadata,
    path_lookup,
)


DEFAULT_SOURCE_IDS = [
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build closure-analysis and steady-state visualization scaffolding.")
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Registered source identifier. Repeat to override the default list.",
    )
    return parser.parse_args()


def maybe_qoi_summary(source_id: str) -> dict[str, object]:
    qoi_path = WORKSPACE_ROOT / "work_products" / source_id / "qoi_summary.json"
    if not qoi_path.exists():
        return {}
    with qoi_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def latest_processor_time(processor_root: Path) -> str:
    if not processor_root.exists():
        return ""
    times = sorted(
        path.name
        for path in processor_root.iterdir()
        if path.is_dir() and path.name.replace(".", "", 1).isdigit()
    )
    return times[-1] if times else ""


def case_row(source_id: str) -> dict[str, object]:
    registry_row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)
    source_root = Path(registry_row["source_root"]).resolve()
    metadata = load_case_metadata(source_root)
    qoi = maybe_qoi_summary(source_id)

    post_root = source_root / "postProcessing"
    processor_root = source_root / "processors64"
    latest_time = latest_processor_time(processor_root)
    convergence_reached = qoi.get("convergence_reached", "")
    run_status = qoi.get("run_status", "")

    if convergence_reached is True and run_status == "completed":
        readiness = "candidate_now"
    elif convergence_reached is True:
        readiness = "candidate_with_review"
    elif source_id == "val_salt_test_2_coarse_mesh_laminar":
        readiness = "active_continuation"
    else:
        readiness = "wait_for_convergence_audit"

    row = {
        "source_id": source_id,
        "case_id": registry_row["case_id"],
        "source_root": str(source_root),
        "fluid": path_lookup(metadata, "fluid", ""),
        "turbulence_model": path_lookup(metadata, "turbulence_model", ""),
        "readiness": readiness,
        "run_status": run_status,
        "convergence_reached": convergence_reached,
        "latest_processor_time": latest_time,
        "geometry_dir": str(source_root / "constant" / "geometry") if (source_root / "constant" / "geometry").exists() else "",
        "temperature_probe_file": str(post_root / "temperature_probes" / "0" / "T"),
        "wall_heat_file": str(post_root / "total_Q.dat"),
        "piv_slab_file": str(post_root / "piv_slab_velocity" / "0" / "volFieldValue.dat"),
        "mdot_monitor_root": str(post_root),
        "probe_location_csv": str(
            WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "tp_tw_probe_locations.csv"
        )
        if source_id == "val_salt_test_2_coarse_mesh_laminar"
        else "",
        "closure_next_step": (
            "derive axial/sectional reduction operators and candidate closure summaries from converged fields"
            if readiness.startswith("candidate")
            else "wait for continued run or convergence audit before deriving closure terms"
        ),
        "visualization_next_step": (
            "prepare steady-state field renders and section cuts from latest converged/writeable time"
            if readiness.startswith("candidate")
            else "delay steady-state visualization until continuation or audit resolves stability"
        ),
    }
    return row


def write_readme(output_dir: Path, rows: list[dict[str, object]]) -> None:
    ready = [row["source_id"] for row in rows if str(row["readiness"]).startswith("candidate")]
    active = [row["source_id"] for row in rows if row["readiness"] == "active_continuation"]

    lines = [
        "# Ethan Closure And Visualization Scaffold",
        "",
        "This report is a durable staging layer for later closure-term derivation,",
        "2D comparison reduction, and steady-state visualization work.",
        "",
        "## Readiness",
        "",
        f"- Closure/visualization candidates now: `{', '.join(ready) if ready else 'none'}`",
        f"- Actively continuing: `{', '.join(active) if active else 'none'}`",
        "",
        "## Intended downstream work",
        "",
        "- Derive reduced-order closure summaries from converged 3D fields and monitored section data.",
        "- Compare those reduced quantities against 2D and later 1D abstractions.",
        "- Prepare steady-state field figures, section cuts, and probe overlays only after runtime/audit readiness is sufficient.",
        "",
        "## Current limitation",
        "",
        "- Most Ethan rows still need continuation or convergence audit before closure extraction should be treated as defensible.",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = args.source_ids or DEFAULT_SOURCE_IDS
    rows = [case_row(source_id) for source_id in source_ids]
    output_dir = WORKSPACE_ROOT / "reports" / "2026-06-02_ethan_closure_and_visualization_scaffold"
    csv_dump(output_dir / "closure_scaffold.csv", list(rows[0].keys()), rows)
    json_dump(output_dir / "closure_scaffold.json", {"generated_at": iso_timestamp(), "source_ids": source_ids, "rows": rows})
    write_readme(output_dir, rows)
    print(json.dumps({"output_dir": str(output_dir), "row_count": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
