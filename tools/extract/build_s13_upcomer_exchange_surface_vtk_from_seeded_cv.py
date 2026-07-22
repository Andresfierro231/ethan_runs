#!/usr/bin/env python3
"""Write geometry-only seeded S13 interface/wall VTK surfaces.

The output VTKs are derived from released seeded face IDs and OpenFOAM
polyMesh topology. They intentionally do not contain sampled CFD fields,
wallHeatFlux, or harvested exchange QOIs.
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
from tools.extract import build_s13_right_leg_geometry_seed as seed_builder
from tools.extract.openfoam_cell_volumes import iter_faces, read_points


TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-FROM-SEEDED-CV-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv"
)
SEEDED = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed"
)
SURFACE_INPUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
)

CASES = ("salt_2", "salt_3", "salt_4")
SURFACES = {
    "exchange_interface": {
        "source": SEEDED / "seeded_exchange_interface_faces.csv",
        "release_status": "released_seeded_exchange_interface_face",
    },
    "trusted_wall": {
        "source": SEEDED / "seeded_trusted_wall_faces.csv",
        "release_status": "released_seeded_trusted_wall_face",
    },
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def group_surface_rows(path: Path) -> dict[str, list[dict[str, str]]]:
    grouped = {case_id: [] for case_id in CASES}
    for row in read_csv(path):
        case_id = row["case_id"]
        if case_id in grouped:
            grouped[case_id].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda item: int(item["face_id"]))
    return grouped


def selected_face_vertices(poly_mesh: Path, face_ids: set[int]) -> dict[int, list[int]]:
    selected: dict[int, list[int]] = {}
    for face_i, vertices in enumerate(iter_faces(poly_mesh / "faces")):
        if face_i in face_ids:
            selected[face_i] = vertices
            if len(selected) == len(face_ids):
                break
    missing = face_ids - set(selected)
    if missing:
        raise ValueError(f"missing selected faces from {poly_mesh}: {len(missing)}")
    return selected


def point_map_for_faces(face_vertices: list[list[int]]) -> tuple[list[int], dict[int, int]]:
    ordered: list[int] = []
    mapping: dict[int, int] = {}
    for vertices in face_vertices:
        for point_id in vertices:
            if point_id not in mapping:
                mapping[point_id] = len(ordered)
                ordered.append(point_id)
    return ordered, mapping


def write_vtk(
    path: Path,
    title: str,
    metadata_rows: list[dict[str, str]],
    face_vertices_by_id: dict[int, list[int]],
    points: list[tuple[float, float, float]],
) -> dict[str, Any]:
    ensure_dir(path.parent)
    face_vertices = [face_vertices_by_id[int(row["face_id"])] for row in metadata_rows]
    point_ids, point_map = point_map_for_faces(face_vertices)
    polygon_size = sum(len(vertices) + 1 for vertices in face_vertices)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# vtk DataFile Version 3.0\n")
        handle.write(f"{title}\n")
        handle.write("ASCII\n")
        handle.write("DATASET POLYDATA\n")
        handle.write(f"POINTS {len(point_ids)} float\n")
        for point_id in point_ids:
            x, y, z = points[point_id]
            handle.write(f"{x:.12g} {y:.12g} {z:.12g}\n")
        handle.write(f"POLYGONS {len(face_vertices)} {polygon_size}\n")
        for vertices in face_vertices:
            local = [str(point_map[point_id]) for point_id in vertices]
            handle.write(f"{len(local)} {' '.join(local)}\n")
        handle.write(f"CELL_DATA {len(metadata_rows)}\n")
        write_scalar(handle, "face_id", "int", [row["face_id"] for row in metadata_rows])
        write_scalar(handle, "owner", "int", [row.get("owner", "-1") for row in metadata_rows])
        write_scalar(handle, "neighbour", "int", [row.get("neighbour", "-1") or "-1" for row in metadata_rows])
        write_scalar(handle, "area_m2", "float", [row["area_m2"] for row in metadata_rows])
    return {
        "vtk_points": len(point_ids),
        "vtk_polygons": len(face_vertices),
        "vtk_polygon_size": polygon_size,
        "area_m2": sum(float(row["area_m2"]) for row in metadata_rows),
    }


def write_scalar(handle: Any, name: str, vtk_type: str, values: list[str]) -> None:
    handle.write(f"SCALARS {name} {vtk_type} 1\n")
    handle.write("LOOKUP_TABLE default\n")
    for value in values:
        handle.write(f"{value}\n")


def source_manifest() -> list[dict[str, str]]:
    rows = [
        {
            "path": rel(SURFACE_INPUT / "summary.json"),
            "role": "read seeded surface/input manifest decision",
            "exists": str((SURFACE_INPUT / "summary.json").exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
    ]
    for surface in SURFACES.values():
        path = surface["source"]
        rows.append(
            {
                "path": rel(path),
                "role": "read seeded face list",
                "exists": str(path.exists()).lower(),
                "native_solver_output": "false",
                "mutated": "false",
            }
        )
    for case_id in CASES:
        mesh = seed_builder.CASE_MESHES[case_id]
        rows.append(
            {
                "path": rel(mesh),
                "role": f"read {case_id} native polyMesh topology",
                "exists": str(mesh.exists()).lower(),
                "native_solver_output": "true",
                "mutated": "false",
            }
        )
    return rows


def build() -> dict[str, Any]:
    ensure_dir(OUT)
    vtk_dir = ensure_dir(OUT / "vtk")
    interface_rows = group_surface_rows(SURFACES["exchange_interface"]["source"])
    wall_rows = group_surface_rows(SURFACES["trusted_wall"]["source"])

    surface_manifest: list[dict[str, str]] = []
    validation_rows: list[dict[str, str]] = []
    for case_id in CASES:
        poly_mesh = seed_builder.CASE_MESHES[case_id]
        points = read_points(poly_mesh / "points")
        for surface_kind, rows in (
            ("exchange_interface", interface_rows[case_id]),
            ("trusted_wall", wall_rows[case_id]),
        ):
            face_ids = {int(row["face_id"]) for row in rows}
            vertices = selected_face_vertices(poly_mesh, face_ids)
            vtk_path = vtk_dir / f"{case_id}_{surface_kind}.vtk"
            stats = write_vtk(
                vtk_path,
                f"{case_id} seeded {surface_kind} geometry only",
                rows,
                vertices,
                points,
            )
            expected_area = sum(float(row["area_m2"]) for row in rows)
            surface_manifest.append(
                {
                    "case_id": case_id,
                    "surface_kind": surface_kind,
                    "vtk_path": rel(vtk_path),
                    "source_face_csv": rel(SURFACES[surface_kind]["source"]),
                    "face_count": str(len(rows)),
                    "area_m2": f"{expected_area:.12g}",
                    "geometry_only": "true",
                    "sampled_fields_present": "false",
                    "Q_wall_W_released": "false",
                    "sampler_ready": "false",
                    "release_status": f"released_seeded_{surface_kind}_geometry_vtk",
                }
            )
            validation_rows.append(
                {
                    "case_id": case_id,
                    "surface_kind": surface_kind,
                    "vtk_path": rel(vtk_path),
                    "vtk_exists": str(vtk_path.exists()).lower(),
                    "expected_face_count": str(len(rows)),
                    "vtk_polygons": str(stats["vtk_polygons"]),
                    "vtk_points": str(stats["vtk_points"]),
                    "expected_area_m2": f"{expected_area:.12g}",
                    "vtk_area_m2": f"{stats['area_m2']:.12g}",
                    "count_check": str(stats["vtk_polygons"] == len(rows)).lower(),
                    "area_check": str(abs(stats["area_m2"] - expected_area) < 1e-12).lower(),
                    "field_sampling_check": "geometry_only_no_sampled_fields",
                }
            )

    csv_dump(OUT / "released_surface_vtk_manifest.csv", list(surface_manifest[0]), surface_manifest)
    csv_dump(OUT / "surface_vtk_validation.csv", list(validation_rows[0]), validation_rows)

    downstream = [
        {
            "gate": "sampler_manifest_refresh",
            "status": "blocked",
            "allowed_next": "false",
            "reason": "geometry-only VTKs lack sampled U/T/rho/p/wallHeatFlux fields and Q_wall_W",
            "next_action": "build sampled interface/wall field extraction or sampler manifest only after field/Q_wall contract is available",
        },
        {
            "gate": "production_harvest",
            "status": "blocked",
            "allowed_next": "false",
            "reason": "sampler-ready rows remain zero and same-QOI UQ is absent",
            "next_action": "refresh sampler manifest after sampled fields exist",
        },
        {
            "gate": "same_qoi_uq_or_admission",
            "status": "blocked",
            "allowed_next": "false",
            "reason": "no harvested exchange QOIs or same-window UQ exist",
            "next_action": "run only after production harvest produces QOIs",
        },
    ]
    csv_dump(OUT / "downstream_gate.csv", list(downstream[0]), downstream)

    guardrails = [
        {"guardrail": "native_output_mutation", "changed": "false"},
        {"guardrail": "registry_or_admission_mutation", "changed": "false"},
        {"guardrail": "scheduler_action", "changed": "false"},
        {"guardrail": "openfoam_solver_or_postprocessing_launch", "changed": "false"},
        {"guardrail": "sampler_or_harvest_launch", "changed": "false"},
        {"guardrail": "fluid_or_external_repo_mutation", "changed": "false"},
        {"guardrail": "fit_model_selection_or_admission", "changed": "false"},
        {"guardrail": "s11_s12_s13_s15_s6_trigger", "changed": "false"},
        {"guardrail": "residual_absorbed_into_internal_Nu", "changed": "false"},
    ]
    csv_dump(OUT / "no_mutation_guardrails.csv", list(guardrails[0]), guardrails)
    sources = source_manifest()
    csv_dump(OUT / "source_manifest.csv", list(sources[0]), sources)

    ready_rows = len([row for row in validation_rows if row["count_check"] == "true" and row["area_check"] == "true"])
    summary: dict[str, Any] = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "package": rel(OUT),
        "case_count": len(CASES),
        "surface_vtk_rows": len(surface_manifest),
        "validated_surface_vtk_rows": ready_rows,
        "geometry_only_surface_vtk_released": ready_rows == len(surface_manifest),
        "sampled_fields_present": False,
        "Q_wall_W_released": False,
        "sampler_ready_rows": 0,
        "sampler_or_harvest_allowed": False,
        "same_qoi_uq_ready": False,
        "exchange_cell_coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "openfoam_solver_or_postprocessing_launch": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SURFACES["exchange_interface"]["source"])}
  - {rel(SURFACES["trusted_wall"]["source"])}
  - {rel(SURFACE_INPUT / "summary.json")}
tags: [s13, upcomer-exchange, seeded-cv, surface-vtk, geometry-only]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-FROM-SEEDED-CV-2026-07-21.md
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_geometry_surface_vtk
---
# S13 Seeded-CV Geometry Surface VTK

This package writes geometry-only VTK surfaces from released seeded face IDs
and read-only OpenFOAM `constant/polyMesh` topology. It emits one seeded
exchange-interface VTK and one trusted-wall VTK for each of Salt2, Salt3, and
Salt4.

Decision: `geometry_only_surface_vtk_released`.

- cases processed: `{summary["case_count"]}`
- VTK surface rows: `{summary["surface_vtk_rows"]}`
- validated VTK surface rows: `{summary["validated_surface_vtk_rows"]}`
- sampled CFD fields present: `false`
- `Q_wall_W` released: `false`
- sampler/harvest allowed: `false`
- same-QOI UQ ready: `false`
- S11/S12/S15/S6 trigger: `false`

These VTKs are suitable as trusted geometry inputs for the next field-sampling
or sampler-manifest design row. They are not production harvest outputs and do
not admit an exchange-cell coefficient.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    summary = build()
    print(
        f"wrote {rel(OUT)} "
        f"validated_surface_vtk_rows={summary['validated_surface_vtk_rows']}/{summary['surface_vtk_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
