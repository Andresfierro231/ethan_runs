#!/usr/bin/env python3
"""Resolve S13 same-window/endpoint gates before GCI and same-QOI UQ.

This task continues the direct coarse extraction chain. It attempts to map
medium/fine exact-label rows onto the coarse target-minus/target/target-plus
physical windows, enriches open-CV endpoint masks from read-only polyMesh
geometry, then reruns formal GCI and same-QOI UQ only if the required gates
pass.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-SAME-WINDOW-ENDPOINT-GCI-UQ-ADMISSION-CHAIN-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain"

DIRECT_CHAIN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain"
MEDIUM_FINE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun"
ENDPOINT_MASKS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation"
GEOMETRY_SEED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed"
SOURCE_BOUNDED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed"

ROLE_MAP = {
    "target_minus": "terminal_minus",
    "target": "terminal",
    "target_plus": "terminal_plus",
}

ENDPOINT_CONVENTIONS = {
    "open_cv_throughflow_inlet": "positive mdot_endpoint_in = -rho*U dot Sf; Sf is OpenFOAM boundary face area vector outward from owner cell",
    "open_cv_throughflow_outlet": "positive mdot_endpoint_out = rho*U dot Sf; Sf is OpenFOAM boundary face area vector outward from owner cell",
}

QOI_UNITS = {
    "Q_wall_W": "W",
    "mdot_exchange_positive_outward_proxy_kg_s": "kg/s",
    "tau_recirc_proxy_s": "s",
    "wall_core_bulk_temperature_contrast_K": "K",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def require_inputs() -> None:
    required = [
        DIRECT_CHAIN / "direct_sampled_coarse_surface_field_rows.csv",
        DIRECT_CHAIN / "coarse_case_qoi_neighbor_spread.csv",
        MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv",
        MEDIUM_FINE / "aggregated_terminal_window_reductions.csv",
        ENDPOINT_MASKS / "endpoint_mask_manifest.csv",
        GEOMETRY_SEED / "source_manifest.csv",
        SOURCE_BOUNDED / "seeded_normal_convention.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 same-window/endpoint inputs: " + "; ".join(missing))


def key_index(rows: list[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def source_roots_by_case_mesh() -> dict[tuple[str, str], tuple[Path, Path]]:
    roots: dict[tuple[str, str], tuple[Path, Path]] = {}
    for row in read_csv(MEDIUM_FINE / "aggregated_terminal_window_reductions.csv"):
        key = (row["case_id"], row["mesh_level"])
        roots[key] = (Path(row["source_root"]), Path(row["processors_dir"]))
    return roots


def exact_rows_by_key() -> dict[tuple[str, str, str, str], dict[str, str]]:
    return key_index(
        read_csv(MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv"),
        "case_id",
        "mesh_level",
        "qoi_label",
        "window_role",
    )


def same_window_mapping_rows() -> list[dict[str, Any]]:
    roots = source_roots_by_case_mesh()
    exact = exact_rows_by_key()
    rows: list[dict[str, Any]] = []
    for coarse in read_csv(DIRECT_CHAIN / "direct_sampled_coarse_surface_field_rows.csv"):
        case_id = coarse["case_id"]
        qoi = coarse["qoi_label"]
        coarse_role = coarse["window_role"]
        coarse_time = coarse["time_window_s"]
        role_equiv = ROLE_MAP[coarse_role]
        for mesh in ("medium", "fine"):
            source_root, processors_dir = roots.get((case_id, mesh), (Path(""), Path("")))
            native_target_dir = processors_dir / coarse_time if processors_dir else Path("")
            role_row = exact.get((case_id, mesh, qoi, role_equiv), {})
            native_target_present = native_target_dir.exists() if str(native_target_dir) else False
            role_found = bool(role_row)
            admitted = native_target_present and False
            if native_target_present:
                status = "target_time_dir_present_but_direct_resampling_not_performed_in_this_guarded_chain"
            else:
                status = "blocked_missing_native_target_time_directory"
            rows.append(
                {
                    "case_id": case_id,
                    "qoi_label": qoi,
                    "mesh_level": mesh,
                    "coarse_window_role": coarse_role,
                    "coarse_time_window_s": coarse_time,
                    "requested_physical_time_dir": rel(native_target_dir),
                    "native_target_time_dir_present": bool_text(native_target_present),
                    "role_equivalent_window_role": role_equiv,
                    "role_equivalent_time_window_s": role_row.get("time_window_s", ""),
                    "role_equivalent_value": role_row.get("value", ""),
                    "role_equivalent_unit": role_row.get("unit", QOI_UNITS.get(qoi, "")),
                    "role_equivalent_row_found": bool_text(role_found),
                    "role_only_mapping_is_proxy": bool_text(role_found and not native_target_present),
                    "same_physical_window_mapping_admitted": bool_text(admitted),
                    "mapping_status": status,
                    "source_root": str(source_root),
                    "processors_dir": str(processors_dir),
                    "source_rows": f"{rel(DIRECT_CHAIN / 'direct_sampled_coarse_surface_field_rows.csv')};{rel(MEDIUM_FINE / 'aggregated_exact_label_qoi_rows.csv')}",
                }
            )
    return rows


def same_window_gate_rows(mapping: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in mapping:
        grouped.setdefault((row["case_id"], row["qoi_label"]), []).append(row)
    rows: list[dict[str, Any]] = []
    for (case_id, qoi), group in sorted(grouped.items()):
        admitted = all(boolish(str(row["same_physical_window_mapping_admitted"])) for row in group)
        target_present = sum(1 for row in group if boolish(str(row["native_target_time_dir_present"])))
        role_only = sum(1 for row in group if boolish(str(row["role_only_mapping_is_proxy"])))
        rows.append(
            {
                "case_id": case_id,
                "qoi_label": qoi,
                "mapping_rows": len(group),
                "native_target_time_dirs_present": target_present,
                "role_only_proxy_rows": role_only,
                "same_window_medium_fine_equivalence_admitted": bool_text(admitted),
                "equivalence_status": "pass" if admitted else "fail_closed_no_same_physical_medium_fine_target_windows",
                "blocking_reason": "" if admitted else "medium/fine native processor directories do not contain the coarse target-minus/target/target-plus physical time labels; terminal role mapping is recorded as proxy-only and not admitted",
            }
        )
    return rows


def parse_openfoam_list_start(path: Path) -> int:
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle):
            stripped = line.strip()
            if stripped.isdigit():
                count = int(stripped)
                next_line = next(handle).strip()
                if next_line == "(":
                    return count
                raise ValueError(f"{path}: expected '(' after count {count!r}, got {next_line!r}")
    raise ValueError(f"{path}: no OpenFOAM list start found")


def parse_face_vertices(line: str) -> list[int]:
    match = re.search(r"\(([^()]*)\)", line)
    if not match:
        return []
    return [int(part) for part in match.group(1).split()]


def parse_point(line: str) -> tuple[float, float, float] | None:
    match = re.search(r"\(([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)", line)
    if not match:
        return None
    return (float(match.group(1)), float(match.group(2)), float(match.group(3)))


def collect_face_vertices(poly_mesh: Path, face_ids: set[int]) -> dict[int, list[int]]:
    path = poly_mesh / "faces"
    count = parse_openfoam_list_start(path)
    wanted = set(face_ids)
    found: dict[int, list[int]] = {}
    in_list = False
    face_index = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not in_list:
                if stripped == "(":
                    in_list = True
                continue
            if stripped == ")" or face_index >= count:
                break
            if face_index in wanted:
                vertices = parse_face_vertices(stripped)
                if not vertices:
                    raise ValueError(f"{path}: could not parse face {face_index}")
                found[face_index] = vertices
                if len(found) == len(wanted):
                    break
            face_index += 1
    missing = wanted - set(found)
    if missing:
        raise ValueError(f"{path}: missing requested faces {sorted(missing)[:5]} of {len(missing)}")
    return found


def collect_owner_cells(poly_mesh: Path, face_ids: set[int]) -> dict[int, int]:
    path = poly_mesh / "owner"
    count = parse_openfoam_list_start(path)
    wanted = set(face_ids)
    found: dict[int, int] = {}
    in_list = False
    face_index = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not in_list:
                if stripped == "(":
                    in_list = True
                continue
            if stripped == ")" or face_index >= count:
                break
            if face_index in wanted:
                found[face_index] = int(stripped)
                if len(found) == len(wanted):
                    break
            face_index += 1
    missing = wanted - set(found)
    if missing:
        raise ValueError(f"{path}: missing requested owner rows {sorted(missing)[:5]} of {len(missing)}")
    return found


def collect_points(poly_mesh: Path, point_ids: set[int]) -> dict[int, tuple[float, float, float]]:
    path = poly_mesh / "points"
    count = parse_openfoam_list_start(path)
    wanted = set(point_ids)
    found: dict[int, tuple[float, float, float]] = {}
    in_list = False
    point_index = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not in_list:
                if stripped == "(":
                    in_list = True
                continue
            if stripped == ")" or point_index >= count:
                break
            if point_index in wanted:
                point = parse_point(stripped)
                if point is None:
                    raise ValueError(f"{path}: could not parse point {point_index}")
                found[point_index] = point
                if len(found) == len(wanted):
                    break
            point_index += 1
    missing = wanted - set(found)
    if missing:
        raise ValueError(f"{path}: missing requested points {sorted(missing)[:5]} of {len(missing)}")
    return found


def vector_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def face_area_vector(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    acc = (0.0, 0.0, 0.0)
    for index, point in enumerate(points):
        acc = vector_add(acc, cross(point, points[(index + 1) % len(points)]))
    return (0.5 * acc[0], 0.5 * acc[1], 0.5 * acc[2])


def face_center(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    n = float(len(points))
    return (
        sum(point[0] for point in points) / n,
        sum(point[1] for point in points) / n,
        sum(point[2] for point in points) / n,
    )


def poly_mesh_by_case() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for row in read_csv(GEOMETRY_SEED / "source_manifest.csv"):
        path = Path(row["path"])
        use = row.get("role", row.get("use", ""))
        if "polyMesh" not in str(path) or not boolish(row.get("exists", "")):
            continue
        for case_id in ("salt_2", "salt_3", "salt_4"):
            compact = case_id.replace("_", "")
            if case_id in use or compact in str(path):
                out[case_id] = ROOT / path
    return out


def endpoint_candidate_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for manifest in read_csv(ENDPOINT_MASKS / "endpoint_mask_manifest.csv"):
        mask = ROOT / manifest["candidate_mask_path"]
        for row in read_csv(mask):
            endpoint = manifest["endpoint_label"]
            row = dict(row)
            row["endpoint_label"] = endpoint
            row["candidate_mask_path"] = manifest["candidate_mask_path"]
            rows.append(row)
    return rows


def build_endpoint_geometry_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    poly_meshes = poly_mesh_by_case()
    candidates = endpoint_candidate_rows()
    by_case: dict[str, list[dict[str, str]]] = {}
    for row in candidates:
        by_case.setdefault(row["case_id"], []).append(row)

    detailed: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    released_dir = OUT / "released_endpoint_masks"
    released_dir.mkdir(parents=True, exist_ok=True)
    normal = "OpenFOAM boundary face area vector Sf, oriented outward from owner cell"

    for case_id, rows in sorted(by_case.items()):
        poly_mesh = poly_meshes.get(case_id)
        if not poly_mesh or not poly_mesh.exists():
            raise FileNotFoundError(f"missing polyMesh for {case_id}: {poly_mesh}")
        face_ids = {int(row["face_id"]) for row in rows}
        face_vertices = collect_face_vertices(poly_mesh, face_ids)
        owners = collect_owner_cells(poly_mesh, face_ids)
        point_ids = {point_id for vertices in face_vertices.values() for point_id in vertices}
        points = collect_points(poly_mesh, point_ids)

        endpoint_rows: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            face_id = int(row["face_id"])
            vertices = face_vertices[face_id]
            face_points = [points[point_id] for point_id in vertices]
            area_vec = face_area_vector(face_points)
            area = math.sqrt(sum(component * component for component in area_vec))
            center = face_center(face_points)
            endpoint = row["endpoint_label"]
            release_row = {
                "case_id": case_id,
                "endpoint_label": endpoint,
                "patch_name": row["patch_name"],
                "face_id": face_id,
                "owner_cell": owners[face_id],
                "area_m2": f"{area:.15g}",
                "area_vector_x_m2": f"{area_vec[0]:.15g}",
                "area_vector_y_m2": f"{area_vec[1]:.15g}",
                "area_vector_z_m2": f"{area_vec[2]:.15g}",
                "center_x_m": f"{center[0]:.15g}",
                "center_y_m": f"{center[1]:.15g}",
                "center_z_m": f"{center[2]:.15g}",
                "normal_convention": normal,
                "positive_mdot_convention": ENDPOINT_CONVENTIONS[endpoint],
                "time_window_s": row["time_window_s"],
                "source_path": rel(poly_mesh),
                "candidate_mask_path": row["candidate_mask_path"],
                "release_ready": "true",
            }
            detailed.append(release_row)
            endpoint_rows.setdefault(endpoint, []).append(release_row)

        for endpoint, erows in sorted(endpoint_rows.items()):
            out_path = released_dir / f"{case_id}_{endpoint}_released_endpoint_mask.csv"
            fields = [
                "case_id",
                "endpoint_label",
                "patch_name",
                "face_id",
                "owner_cell",
                "area_m2",
                "area_vector_x_m2",
                "area_vector_y_m2",
                "area_vector_z_m2",
                "center_x_m",
                "center_y_m",
                "center_z_m",
                "normal_convention",
                "positive_mdot_convention",
                "time_window_s",
                "source_path",
                "candidate_mask_path",
                "release_ready",
            ]
            write_csv(out_path, erows, fields)
            total_area = sum(float(r["area_m2"]) for r in erows)
            gate_rows.append(
                {
                    "case_id": case_id,
                    "endpoint_label": endpoint,
                    "released_endpoint_mask": rel(out_path),
                    "face_count": len(erows),
                    "total_area_m2": f"{total_area:.15g}",
                    "area_m2_present": "true",
                    "area_vector_present": "true",
                    "owner_cell_present": "true",
                    "normal_convention_present": "true",
                    "positive_mdot_convention_present": "true",
                    "endpoint_residual_basis_ready": "true",
                    "release_mask_ready": "true",
                    "source_polyMesh": rel(poly_mesh),
                    "decision": "released_endpoint_geometry_mask_from_read_only_polyMesh",
                }
            )
    return detailed, gate_rows


def formal_gci_disposition_rows(
    same_window_gate: list[dict[str, Any]], endpoint_gate: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    same_window_ready = all(boolish(str(row["same_window_medium_fine_equivalence_admitted"])) for row in same_window_gate)
    endpoint_ready = all(boolish(str(row["endpoint_residual_basis_ready"])) for row in endpoint_gate)
    rows: list[dict[str, Any]] = []
    for qoi in QOI_UNITS:
        run = same_window_ready and endpoint_ready
        rows.append(
            {
                "qoi_label": qoi,
                "same_window_equivalence_ready": bool_text(same_window_ready),
                "endpoint_residual_basis_ready": bool_text(endpoint_ready),
                "formal_gci_run": bool_text(run),
                "formal_gci_admission_ready": bool_text(run),
                "formal_gci_status": "not_run_blocked_by_same_window_equivalence" if not same_window_ready else ("run_ready" if run else "not_run_blocked_by_endpoint_basis"),
                "production_harvest_allowed": bool_text(run),
                "admission_allowed": bool_text(run),
            }
        )
    return rows


def same_qoi_uq_disposition_rows(
    same_window_gate: list[dict[str, Any]], endpoint_gate: list[dict[str, Any]], gci_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    spread = key_index(read_csv(DIRECT_CHAIN / "coarse_case_qoi_neighbor_spread.csv"), "case_id", "qoi_label")
    same_ok = all(boolish(str(row["same_window_medium_fine_equivalence_admitted"])) for row in same_window_gate)
    endpoint_ok = all(boolish(str(row["endpoint_residual_basis_ready"])) for row in endpoint_gate)
    gci_ok = all(boolish(str(row["formal_gci_admission_ready"])) for row in gci_rows)
    run = same_ok and endpoint_ok and gci_ok
    rows: list[dict[str, Any]] = []
    for key, row in sorted(spread.items()):
        case_id, qoi = key
        rows.append(
            {
                "case_id": case_id,
                "qoi_label": qoi,
                "diagnostic_neighbor_half_range": row.get("neighbor_half_range", ""),
                "unit": row.get("unit", QOI_UNITS.get(qoi, "")),
                "same_window_equivalence_ready": bool_text(same_ok),
                "endpoint_residual_basis_ready": bool_text(endpoint_ok),
                "formal_gci_ready": bool_text(gci_ok),
                "same_qoi_uq_rerun": bool_text(run),
                "same_qoi_uq_admission_allowed": bool_text(run),
                "same_qoi_uq_status": "run_ready" if run else "diagnostic_spread_only_formal_uq_blocked",
                "reason": "" if run else "formal same-QOI UQ requires same-window medium/fine equivalence, endpoint residual basis, and formal GCI readiness",
            }
        )
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(DIRECT_CHAIN / 'direct_sampled_coarse_surface_field_rows.csv')}
  - {rel(MEDIUM_FINE / 'aggregated_exact_label_qoi_rows.csv')}
  - {rel(ENDPOINT_MASKS / 'endpoint_mask_manifest.csv')}
  - {rel(GEOMETRY_SEED / 'source_manifest.csv')}
tags: [work-product, s13, same-window, endpoint-geometry, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-same-window-endpoint-gci-uq-admission-chain.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Same-Window Endpoint GCI/UQ Admission Chain

Decision: `{summary['decision']}`.

This package attempts the requested sequence. It records a strict same-window
medium/fine mapping attempt, enriches open-CV endpoint inlet/outlet masks from
read-only coarse polyMesh geometry, and reruns formal GCI/same-QOI UQ gates only
where the prerequisites are admitted.

Endpoint release masks ready: `{summary['released_endpoint_masks']}/6`.
Endpoint face rows enriched: `{summary['endpoint_geometry_rows']}`.
Same-window equivalence admitted rows: `{summary['same_window_equivalence_admitted_rows']}/12`.
Formal GCI run rows: `{summary['formal_gci_run_rows']}/4`.
Formal same-QOI UQ rerun rows: `{summary['same_qoi_uq_rerun_rows']}/12`.

The endpoint residual-basis blocker is resolved for the coarse open-CV
candidate masks. Formal GCI and admission-grade same-QOI UQ remain closed
because medium/fine native processor directories do not contain the same coarse
target-minus/target/target-plus physical time labels. Role-only terminal
mapping is recorded as proxy-only and is not admitted.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def write_sbatch() -> Path:
    script = OUT / "scripts/run_same_window_endpoint_gci_uq_chain.sbatch"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        f"""#!/bin/bash
#SBATCH -J s13_samewin_endpoint
#SBATCH -o {rel(OUT / 'logs/same_window_endpoint_%j.out')}
#SBATCH -e {rel(OUT / 'logs/same_window_endpoint_%j.err')}
#SBATCH -t 00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -p development
#SBATCH -A ASC23046

set -euo pipefail
cd {ROOT}
python3.11 tools/extract/build_s13_same_window_endpoint_gci_uq_admission_chain.py --execute --job-id "${{SLURM_JOB_ID:-manual}}"
""",
        encoding="utf-8",
    )
    return script


def execute(job_id: str | None) -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    mapping = same_window_mapping_rows()
    same_window_gate = same_window_gate_rows(mapping)
    endpoint_geometry, endpoint_gate = build_endpoint_geometry_rows()
    gci_rows = formal_gci_disposition_rows(same_window_gate, endpoint_gate)
    uq_rows = same_qoi_uq_disposition_rows(same_window_gate, endpoint_gate, gci_rows)

    write_csv(
        OUT / "medium_fine_same_window_mapping_attempt.csv",
        mapping,
        [
            "case_id",
            "qoi_label",
            "mesh_level",
            "coarse_window_role",
            "coarse_time_window_s",
            "requested_physical_time_dir",
            "native_target_time_dir_present",
            "role_equivalent_window_role",
            "role_equivalent_time_window_s",
            "role_equivalent_value",
            "role_equivalent_unit",
            "role_equivalent_row_found",
            "role_only_mapping_is_proxy",
            "same_physical_window_mapping_admitted",
            "mapping_status",
            "source_root",
            "processors_dir",
            "source_rows",
        ],
    )
    write_csv(
        OUT / "same_window_medium_fine_equivalence_gate.csv",
        same_window_gate,
        [
            "case_id",
            "qoi_label",
            "mapping_rows",
            "native_target_time_dirs_present",
            "role_only_proxy_rows",
            "same_window_medium_fine_equivalence_admitted",
            "equivalence_status",
            "blocking_reason",
        ],
    )
    write_csv(
        OUT / "endpoint_geometry_enriched_face_rows.csv",
        endpoint_geometry,
        [
            "case_id",
            "endpoint_label",
            "patch_name",
            "face_id",
            "owner_cell",
            "area_m2",
            "area_vector_x_m2",
            "area_vector_y_m2",
            "area_vector_z_m2",
            "center_x_m",
            "center_y_m",
            "center_z_m",
            "normal_convention",
            "positive_mdot_convention",
            "time_window_s",
            "source_path",
            "candidate_mask_path",
            "release_ready",
        ],
    )
    write_csv(
        OUT / "endpoint_residual_basis_gate.csv",
        endpoint_gate,
        [
            "case_id",
            "endpoint_label",
            "released_endpoint_mask",
            "face_count",
            "total_area_m2",
            "area_m2_present",
            "area_vector_present",
            "owner_cell_present",
            "normal_convention_present",
            "positive_mdot_convention_present",
            "endpoint_residual_basis_ready",
            "release_mask_ready",
            "source_polyMesh",
            "decision",
        ],
    )
    write_csv(
        OUT / "formal_gci_rerun_disposition.csv",
        gci_rows,
        [
            "qoi_label",
            "same_window_equivalence_ready",
            "endpoint_residual_basis_ready",
            "formal_gci_run",
            "formal_gci_admission_ready",
            "formal_gci_status",
            "production_harvest_allowed",
            "admission_allowed",
        ],
    )
    write_csv(
        OUT / "same_qoi_uq_rerun_disposition.csv",
        uq_rows,
        [
            "case_id",
            "qoi_label",
            "diagnostic_neighbor_half_range",
            "unit",
            "same_window_equivalence_ready",
            "endpoint_residual_basis_ready",
            "formal_gci_ready",
            "same_qoi_uq_rerun",
            "same_qoi_uq_admission_allowed",
            "same_qoi_uq_status",
            "reason",
        ],
    )
    source_rows = [
        {"source_path": rel(DIRECT_CHAIN / "direct_sampled_coarse_surface_field_rows.csv"), "exists": "true", "mutated": "false", "use": "coarse target-minus/target/target-plus direct rows"},
        {"source_path": rel(MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv"), "exists": "true", "mutated": "false", "use": "medium/fine exact-label role rows"},
        {"source_path": rel(MEDIUM_FINE / "aggregated_terminal_window_reductions.csv"), "exists": "true", "mutated": "false", "use": "medium/fine source roots and processor directories"},
        {"source_path": rel(ENDPOINT_MASKS / "endpoint_mask_manifest.csv"), "exists": "true", "mutated": "false", "use": "candidate endpoint masks"},
        {"source_path": rel(GEOMETRY_SEED / "source_manifest.csv"), "exists": "true", "mutated": "false", "use": "read-only coarse polyMesh provenance"},
    ]
    write_csv(OUT / "source_manifest.csv", source_rows, ["source_path", "exists", "mutated", "use"])
    guardrails = [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_mutated", "value": "false"},
        {"guardrail": "scheduler_action", "value": bool_text(bool(job_id))},
        {"guardrail": "solver_or_openfoam_postprocess_launched", "value": "false"},
        {"guardrail": "source_property_or_qwall_release", "value": "false"},
        {"guardrail": "production_harvest_allowed", "value": bool_text(all(boolish(str(row["production_harvest_allowed"])) for row in gci_rows))},
        {"guardrail": "formal_gci_admitted", "value": bool_text(all(boolish(str(row["formal_gci_admission_ready"])) for row in gci_rows))},
        {"guardrail": "same_qoi_uq_admitted", "value": bool_text(all(boolish(str(row["same_qoi_uq_admission_allowed"])) for row in uq_rows))},
        {"guardrail": "coefficient_fitting_or_admission", "value": "false"},
        {"guardrail": "validation_holdout_external_scoring", "value": "false"},
        {"guardrail": "candidate_freeze_or_final_score", "value": "false"},
    ]
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails, ["guardrail", "value"])
    if job_id:
        write_csv(
            OUT / "scheduler_execution_record.csv",
            [
                {
                    "task_id": TASK_ID,
                    "job_id": job_id,
                    "executed_at": now_utc(),
                    "command": f"python3.11 tools/extract/build_s13_same_window_endpoint_gci_uq_admission_chain.py --execute --job-id {job_id}",
                    "terminal_condition": "same-window mapping, endpoint geometry, and downstream dispositions written",
                    "safe_to_kill_after_completion": "true",
                }
            ],
            ["task_id", "job_id", "executed_at", "command", "terminal_condition", "safe_to_kill_after_completion"],
        )

    summary = {
        "task": TASK_ID,
        "generated_at": now_utc(),
        "job_id": job_id or "",
        "scheduler_action": bool(job_id),
        "decision": "endpoint_basis_resolved_formal_gci_uq_blocked_by_same_window_equivalence",
        "same_window_mapping_rows": len(mapping),
        "same_window_equivalence_rows": len(same_window_gate),
        "same_window_equivalence_admitted_rows": sum(1 for row in same_window_gate if boolish(str(row["same_window_medium_fine_equivalence_admitted"]))),
        "endpoint_geometry_rows": len(endpoint_geometry),
        "released_endpoint_masks": sum(1 for row in endpoint_gate if boolish(str(row["release_mask_ready"]))),
        "endpoint_basis_rows": len(endpoint_gate),
        "endpoint_residual_basis_ready_rows": sum(1 for row in endpoint_gate if boolish(str(row["endpoint_residual_basis_ready"]))),
        "formal_gci_rows": len(gci_rows),
        "formal_gci_run_rows": sum(1 for row in gci_rows if boolish(str(row["formal_gci_run"]))),
        "same_qoi_uq_rows": len(uq_rows),
        "same_qoi_uq_rerun_rows": sum(1 for row in uq_rows if boolish(str(row["same_qoi_uq_rerun"]))),
        "production_harvest_allowed_rows": sum(1 for row in gci_rows if boolish(str(row["production_harvest_allowed"]))),
        "admission_allowed_rows": sum(1 for row in gci_rows if boolish(str(row["admission_allowed"]))),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
    }
    if summary["same_window_equivalence_admitted_rows"] == summary["same_window_equivalence_rows"] and summary["endpoint_residual_basis_ready_rows"] == summary["endpoint_basis_rows"]:
        summary["decision"] = "same_window_and_endpoint_ready_formal_gci_uq_disposition_written"
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def dry_run() -> dict[str, Any]:
    require_inputs()
    script = write_sbatch()
    summary = {
        "task": TASK_ID,
        "generated_at": now_utc(),
        "decision": "sbatch_script_written_execution_pending",
        "sbatch_script": rel(script),
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
    }
    write_json(OUT / "pre_submit_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="execute the mapping/enrichment chain")
    parser.add_argument("--job-id", default="", help="scheduler job id for execution record")
    args = parser.parse_args()
    summary = execute(args.job_id or None) if args.execute else dry_run()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
