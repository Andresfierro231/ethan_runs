#!/usr/bin/env python3
"""Build the S13 upcomer exchange surface VTK disposition package.

The current geometry contract releases cell VTKs only. This script turns that
state into downstream manifests without launching a surface extraction job.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-EXTRACTION-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_vtk_extraction"
)
GEOMETRY = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_geometry_contract"
)

SOURCE_FILES = {
    "geometry_readme": GEOMETRY / "README.md",
    "downstream_surface_vtk_inputs": GEOMETRY / "downstream_surface_vtk_inputs.csv",
    "interface_geometry_contract": GEOMETRY / "interface_geometry_contract.csv",
    "wall_core_band_contract": GEOMETRY / "wall_core_band_contract.csv",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_manifest() -> list[dict[str, Any]]:
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for role, path in SOURCE_FILES.items()
    ]


def surface_input_disposition(downstream: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in downstream:
        status = row.get("status", "")
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "input_lane": row.get("input_lane", ""),
                "release_status": status,
                "required_input": row.get("required_input", ""),
                "available_input": row.get("available_input", ""),
                "surface_vtk_path": row.get("available_input", "") if status == "ready" else "",
                "field_or_face_count_status": "2166996_cells_reported_by_geometry_contract" if row.get("input_lane") == "cell_vtk" else "not_available",
                "consumer": row.get("consumer", ""),
                "blocking_reason": row.get("blocking_reason", ""),
                "extraction_action": "none_cell_vtk_already_released" if row.get("input_lane") == "cell_vtk" else "fail_closed_no_trusted_surface_input",
            }
        )
    return rows


def blocked_surface_manifest(disposition: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "case_id": row["case_id"],
            "blocked_lane": row["input_lane"],
            "blocking_reason": row["blocking_reason"],
            "required_input": row["required_input"],
            "next_release_condition": "trusted geometry/source row releases this lane with provenance",
            "scheduler_action": "false",
        }
        for row in disposition
        if row["release_status"] == "blocked"
    ]


def released_surface_manifest(disposition: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "case_id": row["case_id"],
            "released_lane": row["input_lane"],
            "path": row["surface_vtk_path"],
            "release_basis": "existing geometry contract",
            "surface_extraction_job": "none",
        }
        for row in disposition
        if row["release_status"] == "ready" and row["input_lane"] != "cell_vtk"
    ]


def normal_vector_provenance(interface_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in interface_rows:
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "release_status": row.get("release_status", ""),
                "future_positive_mdot_exchange": "recirculation_cell_to_main_throughflow",
                "current_normal_vector": "",
                "normal_vector_source": "",
                "normal_vector_status": "blocked_no_trusted_exchange_interface",
                "basis_note": row.get("normal_vector_convention", ""),
                "blocking_reason": row.get("blocking_reason", ""),
            }
        )
    return rows


def downstream_manifest_fragment(downstream: list[dict[str, str]]) -> list[dict[str, str]]:
    cases = sorted({row.get("case_id", "") for row in downstream if row.get("case_id")})
    rows: list[dict[str, str]] = []
    for case_id in cases:
        by_lane = {row.get("input_lane", ""): row for row in downstream if row.get("case_id") == case_id}
        rows.append(
            {
                "case_id": case_id,
                "cell_vtk": by_lane.get("cell_vtk", {}).get("available_input", ""),
                "interface_vtk": "MISSING_EXCHANGE_INTERFACE_VTK",
                "wall_vtk": "MISSING_WALL_VTK",
                "q_wall_w": "MISSING_Q_WALL_W",
                "surface_release_status": "blocked_no_interface_or_wall_core_surface",
                "harvest_allowed": "false",
                "source_paths": rel(SOURCE_FILES["downstream_surface_vtk_inputs"]),
            }
        )
    return rows


def guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_output_mutation", "allowed": "false", "observed": "false"},
        {"guardrail": "scheduler_action", "allowed": "false", "observed": "false"},
        {"guardrail": "solver_or_postprocessing_or_sampler_launch", "allowed": "false", "observed": "false"},
        {"guardrail": "registry_or_admission_mutation", "allowed": "false", "observed": "false"},
        {"guardrail": "surface_vtk_extraction", "allowed": "false", "observed": "false"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: {Path(__file__).name}
  generated_at: {summary["generated_at"]}
tags:
  - s13
  - upcomer-exchange
  - surface-vtk
  - fail-closed
related:
  - {rel(SOURCE_FILES["downstream_surface_vtk_inputs"])}
  - {rel(SOURCE_FILES["interface_geometry_contract"])}
  - {rel(SOURCE_FILES["wall_core_band_contract"])}
---

# S13 Upcomer Exchange Surface VTK Disposition

This package applies the completed S13 geometry contract to the surface VTK
lane. Salt2, Salt3, and Salt4 have whole-mesh cell VTK inputs ready, but no
trusted exchange-interface surface, wall/core band surface, or same-window
`Q_wall_W` measurement is released.

Result: fail-closed. No scheduler job, surface extraction, sampler, harvest, or
native-output mutation occurred. The downstream manifest fragment keeps the
cell VTK paths visible while marking interface and wall inputs as missing.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    ensure_dir(OUT)
    downstream = read_csv(SOURCE_FILES["downstream_surface_vtk_inputs"])
    interface_rows = read_csv(SOURCE_FILES["interface_geometry_contract"])

    disposition = surface_input_disposition(downstream)
    released = released_surface_manifest(disposition)
    blocked = blocked_surface_manifest(disposition)
    normals = normal_vector_provenance(interface_rows)
    fragment = downstream_manifest_fragment(downstream)
    guards = guardrails()
    sources = source_manifest()

    csv_dump(OUT / "surface_input_disposition.csv", list(disposition[0]), disposition)
    csv_dump(
        OUT / "released_surface_manifest.csv",
        ["case_id", "released_lane", "path", "release_basis", "surface_extraction_job"],
        released,
    )
    csv_dump(OUT / "blocked_surface_manifest.csv", list(blocked[0]), blocked)
    csv_dump(OUT / "normal_vector_provenance.csv", list(normals[0]), normals)
    csv_dump(OUT / "downstream_manifest_fragment.csv", list(fragment[0]), fragment)
    csv_dump(OUT / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(OUT / "source_manifest.csv", list(sources[0]), sources)

    summary: dict[str, Any] = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "package": rel(OUT),
        "cell_vtk_ready_rows": len([row for row in disposition if row["input_lane"] == "cell_vtk" and row["release_status"] == "ready"]),
        "released_surface_rows": len(released),
        "blocked_surface_rows": len(blocked),
        "surface_vtk_extraction_allowed": False,
        "harvest_allowed": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "closure_admission_change": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    build()
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
