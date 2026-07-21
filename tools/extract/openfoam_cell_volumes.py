#!/usr/bin/env python3
"""Compute OpenFOAM polyMesh cell volumes from ASCII mesh files.

The implementation is intentionally independent of OpenFOAM so it can be unit
tested without scheduler access. For production-scale meshes, run it on a
compute node and treat the emitted CSV as diagnostic/sample support only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-UPCOMER-EXCHANGE-CELL-VOLUME-PARSER-2026-07-21"
PACKAGE_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser"
)
INT_RE = re.compile(r"-?\d+")
FLOAT_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")

CASE_MESHES = [
    {
        "case_id": "salt_2",
        "case_key": "salt2_jin_nominal_continuation",
        "time_window_s": "7915",
        "poly_mesh": (
            "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/"
            "runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/"
            "constant/polyMesh"
        ),
    },
    {
        "case_id": "salt_3",
        "case_key": "salt3_jin_nominal_continuation",
        "time_window_s": "7618",
        "poly_mesh": (
            "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/"
            "runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation/"
            "constant/polyMesh"
        ),
    },
    {
        "case_id": "salt_4",
        "case_key": "salt4_jin_nominal_continuation",
        "time_window_s": "10000",
        "poly_mesh": (
            "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/"
            "runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/"
            "constant/polyMesh"
        ),
    },
]

META_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "poly_mesh",
    "points_exists",
    "faces_exists",
    "owner_exists",
    "neighbour_exists",
    "header_n_points",
    "header_n_cells",
    "header_n_faces",
    "header_n_internal_faces",
    "parser_status",
    "production_policy",
]
VALIDATION_FIELDS = ["check_id", "status", "value", "expected", "basis"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0].strip()


def first_count(path: Path) -> int:
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = strip_line_comment(raw)
        if re.fullmatch(r"\d+", line):
            return int(line)
    raise ValueError(f"could not find OpenFOAM list count in {path}")


def header_note_counts(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")[:4096]
    note = re.search(
        r"nPoints:(?P<n_points>\d+)\s+nCells:(?P<n_cells>\d+)\s+"
        r"nFaces:(?P<n_faces>\d+)\s+nInternalFaces:(?P<n_internal_faces>\d+)",
        text,
    )
    if not note:
        return {}
    return {name: int(value) for name, value in note.groupdict().items()}


def iter_list_payload_lines(path: Path) -> Iterable[str]:
    count_seen = False
    payload = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = strip_line_comment(raw)
            if not line:
                continue
            if not count_seen:
                if re.fullmatch(r"\d+", line):
                    count_seen = True
                continue
            if not payload:
                if line == "(":
                    payload = True
                continue
            if line == ")":
                return
            yield line


def read_label_list(path: Path) -> list[int]:
    return [int(line) for line in iter_list_payload_lines(path)]


def iter_label_list(path: Path) -> Iterable[int]:
    for line in iter_list_payload_lines(path):
        yield int(line)


def read_points(path: Path) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    for line in iter_list_payload_lines(path):
        vals = [float(value) for value in FLOAT_RE.findall(line)]
        if len(vals) != 3:
            raise ValueError(f"bad point line in {path}: {line}")
        points.append((vals[0], vals[1], vals[2]))
    return points


def read_faces(path: Path) -> list[list[int]]:
    faces: list[list[int]] = []
    for line in iter_list_payload_lines(path):
        values = [int(value) for value in INT_RE.findall(line)]
        if not values or values[0] != len(values) - 1:
            raise ValueError(f"bad face line in {path}: {line}")
        faces.append(values[1:])
    return faces


def iter_faces(path: Path) -> Iterable[list[int]]:
    for line in iter_list_payload_lines(path):
        values = [int(value) for value in INT_RE.findall(line)]
        if not values or values[0] != len(values) - 1:
            raise ValueError(f"bad face line in {path}: {line}")
        yield values[1:]


def sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a: tuple[float, float, float], s: float) -> tuple[float, float, float]:
    return (a[0] * s, a[1] * s, a[2] * s)


def norm(a: tuple[float, float, float]) -> float:
    return math.sqrt(dot(a, a))


def face_center_and_area_vector(
    point_ids: list[int], points: list[tuple[float, float, float]]
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if len(point_ids) < 3:
        raise ValueError("face has fewer than three points")
    p0 = points[point_ids[0]]
    area_vector = (0.0, 0.0, 0.0)
    centroid_weighted = (0.0, 0.0, 0.0)
    area_weight = 0.0
    for idx in range(1, len(point_ids) - 1):
        p1 = points[point_ids[idx]]
        p2 = points[point_ids[idx + 1]]
        tri_area_vector = scale(cross(sub(p1, p0), sub(p2, p0)), 0.5)
        tri_area = norm(tri_area_vector)
        tri_centroid = scale(add(add(p0, p1), p2), 1.0 / 3.0)
        area_vector = add(area_vector, tri_area_vector)
        centroid_weighted = add(centroid_weighted, scale(tri_centroid, tri_area))
        area_weight += tri_area
    if area_weight <= 0.0:
        raise ValueError("zero-area face")
    return scale(centroid_weighted, 1.0 / area_weight), area_vector


def compute_cell_volumes_from_mesh(poly_mesh: Path) -> tuple[list[float], dict[str, Any]]:
    points = read_points(poly_mesh / "points")
    faces = read_faces(poly_mesh / "faces")
    owner = read_label_list(poly_mesh / "owner")
    neighbour = read_label_list(poly_mesh / "neighbour")
    if len(owner) != len(faces):
        raise ValueError("owner count must match face count")
    max_cell = max(max(owner), max(neighbour) if neighbour else -1)
    volumes = [0.0 for _ in range(max_cell + 1)]
    for face_i, face in enumerate(faces):
        center, area_vector = face_center_and_area_vector(face, points)
        contribution = dot(center, area_vector) / 3.0
        volumes[owner[face_i]] += contribution
        if face_i < len(neighbour):
            volumes[neighbour[face_i]] -= contribution
    negative = sum(1 for value in volumes if value < -1e-14)
    summary = {
        "n_points": len(points),
        "n_faces": len(faces),
        "n_internal_faces": len(neighbour),
        "n_cells": len(volumes),
        "negative_volume_cells": negative,
        "zero_or_negative_volume_cells": sum(1 for value in volumes if value <= 0.0),
        "min_raw_volume_m3": min(volumes) if volumes else math.nan,
        "max_raw_volume_m3": max(volumes) if volumes else math.nan,
        "sum_raw_volume_m3": sum(volumes),
    }
    return volumes, summary


def compute_cell_volumes_streaming_from_mesh(poly_mesh: Path) -> tuple[list[float], dict[str, Any]]:
    points = read_points(poly_mesh / "points")
    n_faces = first_count(poly_mesh / "faces")
    n_owner = first_count(poly_mesh / "owner")
    n_neighbour = first_count(poly_mesh / "neighbour")
    if n_owner != n_faces:
        raise ValueError("owner count must match face count")
    counts = header_note_counts(poly_mesh / "owner")
    if not counts.get("n_cells"):
        return compute_cell_volumes_from_mesh(poly_mesh)
    volumes = [0.0 for _ in range(counts["n_cells"])]
    face_iter = iter_faces(poly_mesh / "faces")
    owner_iter = iter_label_list(poly_mesh / "owner")
    neighbour_iter = iter_label_list(poly_mesh / "neighbour")
    for face_i in range(n_faces):
        try:
            face = next(face_iter)
            owner = next(owner_iter)
        except StopIteration as exc:
            raise ValueError("faces or owner ended before declared count") from exc
        center, area_vector = face_center_and_area_vector(face, points)
        contribution = dot(center, area_vector) / 3.0
        volumes[owner] += contribution
        if face_i < n_neighbour:
            try:
                neighbour = next(neighbour_iter)
            except StopIteration as exc:
                raise ValueError("neighbour ended before declared count") from exc
            volumes[neighbour] -= contribution
    negative = sum(1 for value in volumes if value < -1e-14)
    summary = {
        "n_points": len(points),
        "n_faces": n_faces,
        "n_internal_faces": n_neighbour,
        "n_cells": len(volumes),
        "negative_volume_cells": negative,
        "zero_or_negative_volume_cells": sum(1 for value in volumes if value <= 0.0),
        "min_raw_volume_m3": min(volumes) if volumes else math.nan,
        "max_raw_volume_m3": max(volumes) if volumes else math.nan,
        "sum_raw_volume_m3": sum(volumes),
        "algorithm": "streaming_faces_owner_neighbour",
    }
    return volumes, summary


def write_cell_volume_csv(path: Path, volumes: list[float]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cell_id", "cellVolume_m3"])
        for idx, volume in enumerate(volumes):
            writer.writerow([idx, f"{volume:.17g}"])


def mesh_metadata_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in CASE_MESHES:
        mesh = ROOT / item["poly_mesh"]
        counts = header_note_counts(mesh / "owner") if (mesh / "owner").exists() else {}
        rows.append(
            {
                **item,
                "poly_mesh": rel(mesh),
                "points_exists": str((mesh / "points").exists()).lower(),
                "faces_exists": str((mesh / "faces").exists()).lower(),
                "owner_exists": str((mesh / "owner").exists()).lower(),
                "neighbour_exists": str((mesh / "neighbour").exists()).lower(),
                "header_n_points": counts.get("n_points", ""),
                "header_n_cells": counts.get("n_cells", ""),
                "header_n_faces": counts.get("n_faces", ""),
                "header_n_internal_faces": counts.get("n_internal_faces", ""),
                "parser_status": "production_scale_mesh_not_parsed_on_login_node",
                "production_policy": "run full volume export on a compute node before sampler launch",
            }
        )
    return rows


def validation_rows() -> list[dict[str, Any]]:
    return [
        {
            "check_id": "parser_algorithm",
            "status": "pass_unit_tested",
            "value": "owner_neighbour_oriented_divergence_theorem",
            "expected": "cell volume from closed oriented face flux",
            "basis": "synthetic cube and two-cell tests exercise owner and neighbour signs",
        },
        {
            "check_id": "native_mutation",
            "status": "pass_no_mutation",
            "value": "false",
            "expected": "false",
            "basis": "parser reads polyMesh files and writes only package outputs",
        },
        {
            "check_id": "production_mesh_policy",
            "status": "blocked_until_scheduler_row",
            "value": "full Salt meshes are multi-million-cell",
            "expected": "compute_node_execution",
            "basis": "do not run heavy full-mesh parsing on login node",
        },
    ]


def source_manifest(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/openfoam_cell_volumes.py"),
        Path("tools/extract/test_openfoam_cell_volumes.py"),
        Path("tools/extract/sample_upcomer_exchange_cell.py"),
        Path("tools/extract/test_sample_upcomer_exchange_cell.py"),
        output_dir,
    ]
    paths.extend(Path(item["poly_mesh"]) for item in CASE_MESHES)
    rows = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        task_output = (
            full == output_dir
            or str(path).startswith("tools/extract/openfoam_cell_volumes")
            or str(path).startswith("tools/extract/test_openfoam_cell_volumes")
            or str(path).startswith("tools/extract/sample_upcomer_exchange_cell")
            or str(path).startswith("tools/extract/test_sample_upcomer_exchange_cell")
        )
        native = str(path).startswith("jadyn_runs/")
        rows.append(
            {
                "path": rel(full),
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(task_output and full != output_dir).lower(),
            }
        )
    return rows


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, recirculation, exchange-cell, cell-volume, parser]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/README.md
---
# Upcomer Exchange Cell-Volume Parser

This package implements the missing cell-volume path that blocked the
exchange-cell sampler. The parser computes OpenFOAM cell volumes from ASCII
`constant/polyMesh` files using the oriented owner/neighbour face-flux identity.

## Decision

- queued production meshes inventoried: `{summary["mesh_rows"]}`
- parser validation rows: `{summary["validation_rows"]}`
- full production mesh volume export run here: `false`
- scheduler action: `false`
- fit/admission changed: `false`

The source meshes are multi-million-cell meshes, so this row does not run full
production parsing on the login node. The parser and exchange-cell CSV fallback
are unit-tested and ready for a scheduler-authorized extraction row.

## Outputs

- `mesh_volume_parser_readiness.csv`: queued Salt2/Salt3/Salt4 mesh metadata.
- `parser_validation_checks.csv`: validation and guardrail checks.
- `source_manifest.csv`: provenance and mutation flags.
- `summary.json`: package summary.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
Fluid source, external repository, blocker register, or generated docs index was
mutated. No OpenFOAM command, solver, postprocessor, sampler, fitting, model
selection, exchange-cell admission, Phase 4B rescore, Phase 5, or S6 trigger was
run.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    metadata = mesh_metadata_rows()
    checks = validation_rows()
    manifest = source_manifest(output_dir)
    csv_dump(output_dir / "mesh_volume_parser_readiness.csv", META_FIELDS, metadata)
    csv_dump(output_dir / "parser_validation_checks.csv", VALIDATION_FIELDS, checks)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "mesh_rows": len(metadata),
        "validation_rows": len(checks),
        "production_volume_export_run": False,
        "scheduler_action": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {"summary": summary, "metadata": metadata, "checks": checks}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poly-mesh", default="", help="OpenFOAM constant/polyMesh directory to parse.")
    parser.add_argument("--output-csv", default="", help="Write cell_id,cellVolume_m3 CSV.")
    parser.add_argument("--summary-json", default="", help="Write parser summary JSON.")
    parser.add_argument("--package", action="store_true", help="Build the task package instead of parsing a mesh.")
    parser.add_argument("--output-dir", default=str(PACKAGE_DIR), help="Package output directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.package or not args.poly_mesh:
        payload = build_package(Path(args.output_dir))
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))
        return 0
    volumes, summary = compute_cell_volumes_streaming_from_mesh(Path(args.poly_mesh))
    if args.output_csv:
        write_cell_volume_csv(Path(args.output_csv), volumes)
    if args.summary_json:
        json_dump(Path(args.summary_json), summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
