#!/usr/bin/env python3
"""Build the S13 right-leg geometry seed package."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract import build_s13_upcomer_exchange_topology_cv_release as topo
from tools.extract.openfoam_cell_volumes import (
    INT_RE,
    face_center_and_area_vector,
    first_count,
    iter_faces,
    iter_list_payload_lines,
    iter_label_list,
    norm,
    read_points,
)

TASK_ID = "TODO-S13-RIGHT-LEG-GEOMETRY-SEED-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed"

SEGMENTATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight"
INPUT_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"
ROI_AUDIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit"
SOURCE_BOUNDED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition"
DIAGNOSTIC_BRIDGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge"

CASE_IDS = ("salt_2", "salt_3", "salt_4")
TRUSTED_WALL_PATCHES = topo.RIGHT_LEG_WALL_PATCHES
CAP_PATCHES = ("ncc_pipeleg_right_01_lower_start", "ncc_pipeleg_right_03_upper_end")
ENVELOPE_TOLERANCE_M = 0.002

CASE_MESHES = {
    "salt_2": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/constant/polyMesh",
    "salt_3": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation/constant/polyMesh",
    "salt_4": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/constant/polyMesh",
}
VOLUME_CSVS = {
    case_id: INPUT_GENERATION / f"cell_volumes/{case_id}_cell_volumes.csv"
    for case_id in CASE_IDS
}

SEED_CELL_FIELDS = [
    "case_id",
    "cell_id",
    "seed_role",
    "volume_m3",
    "reverse_flow_candidate",
]
FACE_LANE_FIELDS = [
    "case_id",
    "face_id",
    "lane",
    "patch_name",
    "owner",
    "neighbour",
    "area_m2",
    "center_x_m",
    "center_y_m",
    "center_z_m",
]
SUMMARY_FIELDS = [
    "case_id",
    "seed_cell_count",
    "seed_volume_m3",
    "trusted_wall_face_count",
    "trusted_wall_area_m2",
    "internal_interface_face_count",
    "internal_interface_area_m2",
    "cap_face_count",
    "cap_area_m2",
    "escape_face_count",
    "escape_area_m2",
    "reverse_flow_seed_cells",
    "reverse_flow_occupancy_fraction",
    "geometry_seed_release_status",
    "blocking_reason",
]
OCCUPANCY_FIELDS = [
    "case_id",
    "reverse_candidate_cells",
    "geometry_seed_cells",
    "reverse_flow_seed_cells",
    "reverse_flow_occupancy_fraction",
    "diagnostic_only",
    "selection_authority",
]
RERUN_FIELDS = [
    "case_id",
    "geometry_seed_ready_for_source_bounded_rerun",
    "required_next_step",
    "forbidden_downstream_action",
    "blocking_reason",
]
PATCH_CLASS_FIELDS = ["case_id", "patch_name", "classification", "face_count", "area_m2", "trusted_patch", "seed_boundary_role"]
SURFACE_CONTRACT_FIELDS = [
    "case_id",
    "surface_lane",
    "classification",
    "face_count",
    "area_m2",
    "release_status",
    "normal_vector_convention",
    "consumer",
    "blocking_reason",
]
DOWNSTREAM_FIELDS = ["case_id", "downstream_lane", "status", "required_input", "available_input", "blocking_reason"]
S12_FIELDS = ["gate", "status", "effect_on_s12", "evidence", "next_action"]
GUARD_FIELDS = ["guard_id", "status", "policy"]
SOURCE_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


@dataclass(frozen=True)
class Bounds:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float

    def expanded(self, tolerance: float) -> "Bounds":
        return Bounds(
            self.x_min - tolerance,
            self.x_max + tolerance,
            self.y_min - tolerance,
            self.y_max + tolerance,
            self.z_min - tolerance,
            self.z_max + tolerance,
        )

    def contains(self, point: tuple[float, float, float]) -> bool:
        x, y, z = point
        return (
            self.x_min <= x <= self.x_max
            and self.y_min <= y <= self.y_max
            and self.z_min <= z <= self.z_max
        )


@dataclass
class CaseSeed:
    case_id: str
    bounds: Bounds
    wall_seed_cells: set[int] = field(default_factory=set)
    seed_cells: set[int] = field(default_factory=set)
    trusted_wall_face_count: int = 0
    trusted_wall_area_m2: float = 0.0
    internal_interface_face_count: int = 0
    internal_interface_area_m2: float = 0.0
    cap_face_count: int = 0
    cap_area_m2: float = 0.0
    escape_face_count: int = 0
    escape_area_m2: float = 0.0
    lane_rows: list[dict[str, Any]] = field(default_factory=list)
    reverse_candidate_cells: set[int] = field(default_factory=set)
    reverse_flow_seed_cells: set[int] = field(default_factory=set)
    seed_volume_m3: float = 0.0


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def patch_name_for_face(face_i: int, patches: list[topo.PatchRange]) -> str:
    for patch in patches:
        if patch.start_face <= face_i < patch.end_face:
            return patch.name
    return ""


def patch_lookup(patches: list[topo.PatchRange]) -> dict[int, str]:
    lookup: dict[int, str] = {}
    for patch in patches:
        for face_i in range(patch.start_face, patch.end_face):
            lookup[face_i] = patch.name
    return lookup


def is_cap_patch(patch_name: str) -> bool:
    return any(name in patch_name for name in CAP_PATCHES)


def face_area_and_center(
    face: list[int], points: list[tuple[float, float, float]]
) -> tuple[float, tuple[float, float, float]]:
    center, area_vector = face_center_and_area_vector(face, points)
    return norm(area_vector), center


def parse_face_line(line: str, path: Path) -> list[int]:
    values = [int(value) for value in INT_RE.findall(line)]
    if not values or values[0] != len(values) - 1:
        raise ValueError(f"bad face line in {path}: {line}")
    return values[1:]


def selected_face_geometry(
    poly_mesh: Path,
    selected_face_ids: set[int],
    points: list[tuple[float, float, float]],
) -> dict[int, tuple[float, tuple[float, float, float]]]:
    if not selected_face_ids:
        return {}
    out: dict[int, tuple[float, tuple[float, float, float]]] = {}
    faces_path = poly_mesh / "faces"
    for face_i, line in enumerate(iter_list_payload_lines(faces_path)):
        if face_i not in selected_face_ids:
            continue
        out[face_i] = face_area_and_center(parse_face_line(line, faces_path), points)
        if len(out) == len(selected_face_ids):
            break
    missing = selected_face_ids - set(out)
    if missing:
        raise ValueError(f"missing selected face geometry rows: {len(missing)}")
    return out


def bounds_from_values(values: Iterable[tuple[float, float, float]]) -> Bounds:
    points = list(values)
    if not points:
        raise ValueError("cannot build bounds from no points")
    return Bounds(
        min(point[0] for point in points),
        max(point[0] for point in points),
        min(point[1] for point in points),
        max(point[1] for point in points),
        min(point[2] for point in points),
        max(point[2] for point in points),
    )


def trusted_patch_bounds(
    poly_mesh: Path,
    face_patches: dict[int, str],
    points: list[tuple[float, float, float]],
) -> tuple[Bounds, int, float]:
    trusted_face_ids = {
        face_i for face_i, patch_name in face_patches.items()
        if patch_name in TRUSTED_WALL_PATCHES
    }
    centers: list[tuple[float, float, float]] = []
    area_m2 = 0.0
    for area, center in selected_face_geometry(poly_mesh, trusted_face_ids, points).values():
        centers.append(center)
        area_m2 += area
    return bounds_from_values(centers).expanded(ENVELOPE_TOLERANCE_M), len(trusted_face_ids), area_m2


def load_reverse_candidates(case_id: str) -> set[int]:
    summary = {row["case_id"]: row for row in read_csv(SEGMENTATION / "recirc_segmentation_case_summary.csv")}
    mask_path = ROOT / summary[case_id]["mask_csv"]
    return {int(row["cell_id"]) for row in read_csv(mask_path)}


def read_selected_volumes(path: Path, selected: set[int]) -> dict[int, float]:
    volumes: dict[int, float] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cell_id = int(row["cell_id"])
            if cell_id in selected:
                volumes[cell_id] = float(row["cellVolume_m3"])
    return volumes


def collect_wall_seed_cells(
    case_id: str,
    poly_mesh: Path,
    face_patches: dict[int, str],
) -> set[int]:
    wall_seed_cells: set[int] = set()
    n_faces = first_count(poly_mesh / "faces")
    n_internal = first_count(poly_mesh / "neighbour")
    owner_iter = iter_label_list(poly_mesh / "owner")
    neighbour_iter = iter_label_list(poly_mesh / "neighbour")
    for face_i in range(n_faces):
        owner = next(owner_iter)
        neighbour = next(neighbour_iter) if face_i < n_internal else None
        patch_name = "" if neighbour is not None else face_patches.get(face_i, "")
        if neighbour is None:
            if patch_name in TRUSTED_WALL_PATCHES:
                wall_seed_cells.add(owner)
            continue
    if not wall_seed_cells:
        raise ValueError(f"{case_id} has no wall-adjacent cells for trusted patches")
    return wall_seed_cells


def grow_seed(wall_seed_cells: set[int], adjacency: dict[int, set[int]]) -> set[int]:
    selected: set[int] = set(wall_seed_cells)
    queue: deque[int] = deque(sorted(wall_seed_cells))
    while queue:
        current = queue.popleft()
        for neighbour in adjacency.get(current, set()):
            if neighbour in selected:
                continue
            selected.add(neighbour)
            queue.append(neighbour)
    return selected


def lane_row(
    case_id: str,
    face_i: int,
    lane: str,
    patch_name: str,
    owner: int,
    neighbour: int | None,
    area: float,
    center: tuple[float, float, float],
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "face_id": face_i,
        "lane": lane,
        "patch_name": patch_name,
        "owner": owner,
        "neighbour": "" if neighbour is None else neighbour,
        "area_m2": f"{area:.12g}",
        "center_x_m": f"{center[0]:.12g}",
        "center_y_m": f"{center[1]:.12g}",
        "center_z_m": f"{center[2]:.12g}",
    }


def classify_seed_faces(
    seed: CaseSeed,
    poly_mesh: Path,
    face_patches: dict[int, str],
    points: list[tuple[float, float, float]],
) -> None:
    n_faces = first_count(poly_mesh / "faces")
    n_internal = first_count(poly_mesh / "neighbour")
    owner_iter = iter_label_list(poly_mesh / "owner")
    neighbour_iter = iter_label_list(poly_mesh / "neighbour")
    touched: list[tuple[int, str, str, int, int | None]] = []
    selected_face_ids: set[int] = set()
    for face_i in range(n_faces):
        owner = next(owner_iter)
        neighbour = next(neighbour_iter) if face_i < n_internal else None
        owner_in = owner in seed.seed_cells
        neighbour_in = neighbour in seed.seed_cells if neighbour is not None else False
        if not owner_in and not neighbour_in:
            continue
        patch_name = "" if neighbour is not None else face_patches.get(face_i, "")
        if neighbour is not None:
            if owner_in == neighbour_in:
                continue
            lane = "internal_interface"
        elif patch_name in TRUSTED_WALL_PATCHES:
            lane = "trusted_wall"
        elif is_cap_patch(patch_name):
            lane = "cap_or_open_boundary"
        else:
            lane = "escape_untrusted_boundary"
        touched.append((face_i, lane, patch_name, owner, neighbour))
        selected_face_ids.add(face_i)
    geometry = selected_face_geometry(poly_mesh, selected_face_ids, points)
    for face_i, lane, patch_name, owner, neighbour in touched:
        area, center = geometry[face_i]
        if lane == "internal_interface":
            seed.internal_interface_face_count += 1
            seed.internal_interface_area_m2 += area
        elif lane == "trusted_wall":
            seed.trusted_wall_face_count += 1
            seed.trusted_wall_area_m2 += area
        elif lane == "cap_or_open_boundary":
            seed.cap_face_count += 1
            seed.cap_area_m2 += area
        else:
            seed.escape_face_count += 1
            seed.escape_area_m2 += area
        seed.lane_rows.append(lane_row(seed.case_id, face_i, lane, patch_name, owner, neighbour, area, center))


def release_decision(seed: CaseSeed) -> tuple[str, str]:
    reasons: list[str] = []
    if not seed.seed_cells:
        reasons.append("empty_geometry_seed")
    if seed.seed_volume_m3 <= 0.0:
        reasons.append("missing_positive_seed_volume")
    if seed.trusted_wall_face_count <= 0 or seed.trusted_wall_area_m2 <= 0.0:
        reasons.append("missing_positive_trusted_wall_area")
    if seed.internal_interface_face_count <= 0 or seed.internal_interface_area_m2 <= 0.0:
        reasons.append("missing_positive_internal_interface_area")
    if seed.escape_face_count > 0:
        reasons.append("seed_touches_untrusted_boundary_escape")
    if reasons:
        return "blocked_geometry_seed_not_ready", ";".join(reasons)
    return "released_geometry_seed_ready_for_source_bounded_rerun", ""


def build_case_seed(case_id: str) -> CaseSeed:
    poly_mesh = CASE_MESHES[case_id]
    points = read_points(poly_mesh / "points")
    patches = topo.parse_boundary_patches((poly_mesh / "boundary").read_text(encoding="utf-8", errors="replace"))
    missing = set(TRUSTED_WALL_PATCHES) - {patch.name for patch in patches}
    if missing:
        raise ValueError(f"{case_id} missing trusted wall patches: {sorted(missing)}")
    face_patches = patch_lookup(patches)
    bounds, _, _ = trusted_patch_bounds(poly_mesh, face_patches, points)
    wall_seed_cells = collect_wall_seed_cells(case_id, poly_mesh, face_patches)
    seed = CaseSeed(case_id=case_id, bounds=bounds, wall_seed_cells=wall_seed_cells)
    seed.seed_cells = set(wall_seed_cells)
    seed.reverse_candidate_cells = load_reverse_candidates(case_id)
    seed.reverse_flow_seed_cells = seed.seed_cells & seed.reverse_candidate_cells
    volumes = read_selected_volumes(VOLUME_CSVS[case_id], seed.seed_cells)
    missing_volume = seed.seed_cells - set(volumes)
    if missing_volume:
        raise ValueError(f"{case_id} missing {len(missing_volume)} seed-cell volume rows")
    seed.seed_volume_m3 = sum(volumes.values())
    classify_seed_faces(seed, poly_mesh, face_patches, points)
    seed._volumes = volumes  # type: ignore[attr-defined]
    return seed


def seed_cell_rows(seed: CaseSeed) -> list[dict[str, Any]]:
    volumes: dict[int, float] = seed._volumes  # type: ignore[attr-defined]
    return [
        {
            "case_id": seed.case_id,
            "cell_id": cell_id,
            "seed_role": "wall_seed" if cell_id in seed.wall_seed_cells else "geometry_grown_seed",
            "volume_m3": f"{volumes[cell_id]:.12g}",
            "reverse_flow_candidate": str(cell_id in seed.reverse_candidate_cells).lower(),
        }
        for cell_id in sorted(seed.seed_cells)
    ]


def summary_row(seed: CaseSeed, group_ready: bool) -> dict[str, Any]:
    local_status, reason = release_decision(seed)
    status = local_status if group_ready else "blocked_group_seed_release_requires_all_three_cases"
    blocking_reason = reason if reason else ("" if group_ready else "all_three_cases_must_release")
    occupancy = len(seed.reverse_flow_seed_cells) / len(seed.seed_cells) if seed.seed_cells else 0.0
    return {
        "case_id": seed.case_id,
        "seed_cell_count": len(seed.seed_cells),
        "seed_volume_m3": f"{seed.seed_volume_m3:.12g}",
        "trusted_wall_face_count": seed.trusted_wall_face_count,
        "trusted_wall_area_m2": f"{seed.trusted_wall_area_m2:.12g}",
        "internal_interface_face_count": seed.internal_interface_face_count,
        "internal_interface_area_m2": f"{seed.internal_interface_area_m2:.12g}",
        "cap_face_count": seed.cap_face_count,
        "cap_area_m2": f"{seed.cap_area_m2:.12g}",
        "escape_face_count": seed.escape_face_count,
        "escape_area_m2": f"{seed.escape_area_m2:.12g}",
        "reverse_flow_seed_cells": len(seed.reverse_flow_seed_cells),
        "reverse_flow_occupancy_fraction": f"{occupancy:.12g}",
        "geometry_seed_release_status": status,
        "blocking_reason": blocking_reason,
    }


def aggregate_lanes(seed: CaseSeed) -> dict[str, tuple[int, float]]:
    grouped: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
    for row in seed.lane_rows:
        key = row["lane"] if row["lane"] == "internal_interface" else row["patch_name"]
        count, area = grouped[key]
        grouped[key] = (count + 1, area + float(row["area_m2"]))
    return grouped


def patch_classification_rows(seeds: list[CaseSeed]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        grouped = aggregate_lanes(seed)
        for key, (count, area) in sorted(grouped.items()):
            if key == "internal_interface":
                continue
            trusted = key in TRUSTED_WALL_PATCHES
            cap = is_cap_patch(key)
            rows.append(
                {
                    "case_id": seed.case_id,
                    "patch_name": key,
                    "classification": "trusted_right_leg_wall" if trusted else ("classified_ncc_cap" if cap else "untrusted_boundary_escape"),
                    "face_count": count,
                    "area_m2": f"{area:.12g}",
                    "trusted_patch": str(trusted).lower(),
                    "seed_boundary_role": "wall" if trusted else ("cap" if cap else "escape"),
                }
            )
    return rows


def surface_contract_rows(seeds: list[CaseSeed], group_ready: bool) -> list[dict[str, Any]]:
    normal = "positive outward from geometry seed toward adjacent non-seed cell for internal interface; wall normals use OpenFOAM owner-side boundary orientation"
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        status, reason = release_decision(seed)
        ready = group_ready and status.startswith("released_")
        rows.extend(
            [
                {
                    "case_id": seed.case_id,
                    "surface_lane": "trusted_wall_faces",
                    "classification": "trusted_right_leg_wall",
                    "face_count": seed.trusted_wall_face_count,
                    "area_m2": f"{seed.trusted_wall_area_m2:.12g}",
                    "release_status": "seed_ready" if ready else "blocked",
                    "normal_vector_convention": normal,
                    "consumer": "source-bounded CV wall seed",
                    "blocking_reason": "" if ready else reason,
                },
                {
                    "case_id": seed.case_id,
                    "surface_lane": "classified_ncc_caps",
                    "classification": "classified_ncc_cap",
                    "face_count": seed.cap_face_count,
                    "area_m2": f"{seed.cap_area_m2:.12g}",
                    "release_status": "seed_ready" if ready else "blocked",
                    "normal_vector_convention": normal,
                    "consumer": "future cap classification audit",
                    "blocking_reason": "" if ready else reason,
                },
                {
                    "case_id": seed.case_id,
                    "surface_lane": "internal_seed_core_interface",
                    "classification": "seed_core_interface",
                    "face_count": seed.internal_interface_face_count,
                    "area_m2": f"{seed.internal_interface_area_m2:.12g}",
                    "release_status": "seed_ready" if ready else "blocked",
                    "normal_vector_convention": normal,
                    "consumer": "future exchange/interface candidate search",
                    "blocking_reason": "" if ready else reason,
                },
                {
                    "case_id": seed.case_id,
                    "surface_lane": "surface_vtk_extraction",
                    "classification": "downstream_surface",
                    "face_count": 0,
                    "area_m2": "0",
                    "release_status": "blocked",
                    "normal_vector_convention": normal,
                    "consumer": "sampler manifest",
                    "blocking_reason": "surface extraction requires later source-bounded CV release",
                },
            ]
        )
    return rows


def downstream_rows(seeds: list[CaseSeed], group_ready: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lanes = [
        ("source_bounded_cv_rerun", "ready" if group_ready else "blocked", "3/3 geometry seed rows with positive wall/interface and no unclassified escapes", "geometry-backed right-leg wall seed" if group_ready else "", "geometry seed must release 3/3 cases"),
        ("surface_extraction", "blocked", "released source-bounded CV with exchange-interface/wall/core/normal lanes", "", "downstream gate requires later source-bounded CV release"),
        ("sampler_manifest_refresh", "blocked", "released surface VTKs, normals, Q_wall_W/source lane, same-window thermal fields", "", "downstream gate requires later source-bounded CV release"),
        ("production_harvest", "blocked", "3/3 sampler-ready rows", "", "downstream gate requires later source-bounded CV release"),
        ("S11_S12_S15_S6_trigger", "blocked", "admitted runtime-legal candidate after UQ/source-property release", "", "downstream gate requires later source-bounded CV release"),
    ]
    for seed in seeds:
        for lane, status, required, available, reason in lanes:
            rows.append(
                {
                    "case_id": seed.case_id,
                    "downstream_lane": lane,
                    "status": status,
                    "required_input": required,
                    "available_input": available,
                    "blocking_reason": "" if lane == "source_bounded_cv_rerun" and group_ready else reason,
                }
            )
    return rows


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    ensure_dir(output_dir)
    seeds = [build_case_seed(case_id) for case_id in CASE_IDS]
    local_decisions = {seed.case_id: release_decision(seed) for seed in seeds}
    group_ready = all(status.startswith("released_") for status, _ in local_decisions.values())

    all_cell_rows: list[dict[str, Any]] = []
    all_face_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    occupancy_rows: list[dict[str, Any]] = []
    rerun_rows: list[dict[str, Any]] = []
    for seed in seeds:
        all_cell_rows.extend(seed_cell_rows(seed))
        all_face_rows.extend(seed.lane_rows)
        row = summary_row(seed, group_ready)
        summary_rows.append(row)
        occupancy_rows.append(
            {
                "case_id": seed.case_id,
                "reverse_candidate_cells": len(seed.reverse_candidate_cells),
                "geometry_seed_cells": len(seed.seed_cells),
                "reverse_flow_seed_cells": len(seed.reverse_flow_seed_cells),
                "reverse_flow_occupancy_fraction": row["reverse_flow_occupancy_fraction"],
                "diagnostic_only": "true",
                "selection_authority": "none_reverse_flow_does_not_control_geometry_seed_release",
            }
        )
        ready = group_ready and row["geometry_seed_release_status"].startswith("released_")
        rerun_rows.append(
            {
                "case_id": seed.case_id,
                "geometry_seed_ready_for_source_bounded_rerun": str(ready).lower(),
                "required_next_step": "rerun_source_bounded_cv_release_with_geometry_seed" if ready else "repair_geometry_seed_before_source_bounded_rerun",
                "forbidden_downstream_action": "surface_sampler_harvest_uq_s12_s11_s15_s6_trigger",
                "blocking_reason": row["blocking_reason"],
            }
        )

    s12_rows = [
        {
            "gate": "s13_geometry_seed",
            "status": "pass" if group_ready else "fail",
            "effect_on_s12": "permits_source_bounded_cv_rerun_only" if group_ready else "blocks_source_bounded_cv_rerun_and_s12_hiax1",
            "evidence": rel(output_dir / "geometry_seed_case_summary.csv"),
            "next_action": "rerun source-bounded CV release with this geometry seed" if group_ready else "repair geometry seed before any S12 implementation",
        },
        {
            "gate": "s13_source_bounded_cv_rerun",
            "status": "blocked_pending_new_row",
            "effect_on_s12": "still blocks S12-HIAX1 until source-bounded QOIs release",
            "evidence": rel(SOURCE_BOUNDED / "s12_unlock_gate.csv"),
            "next_action": "claim a separate source-bounded rerun row if geometry seed passes",
        },
    ]

    csv_dump(output_dir / "geometry_seed_cells.csv", SEED_CELL_FIELDS, all_cell_rows)
    csv_dump(output_dir / "geometry_seed_face_lanes.csv", FACE_LANE_FIELDS, all_face_rows)
    csv_dump(output_dir / "geometry_seed_case_summary.csv", SUMMARY_FIELDS, summary_rows)
    csv_dump(output_dir / "reverse_flow_occupancy_diagnostics.csv", OCCUPANCY_FIELDS, occupancy_rows)
    csv_dump(output_dir / "reverse_occupancy_diagnostics.csv", OCCUPANCY_FIELDS, occupancy_rows)
    csv_dump(output_dir / "geometry_seed_patch_classification.csv", PATCH_CLASS_FIELDS, patch_classification_rows(seeds))
    csv_dump(output_dir / "geometry_seed_surface_contract.csv", SURFACE_CONTRACT_FIELDS, surface_contract_rows(seeds, group_ready))
    csv_dump(output_dir / "downstream_release_gate.csv", DOWNSTREAM_FIELDS, downstream_rows(seeds, group_ready))
    csv_dump(output_dir / "source_bounded_rerun_readiness.csv", RERUN_FIELDS, rerun_rows)
    csv_dump(output_dir / "s12_unlock_impact.csv", S12_FIELDS, s12_rows)
    csv_dump(
        output_dir / "no_mutation_guardrails.csv",
        GUARD_FIELDS,
        [
            {"guard_id": "native_outputs", "status": "pass", "policy": "read-only polyMesh/cell-volume/mask inputs only"},
            {"guard_id": "admission", "status": "pass", "policy": "no exchange-cell coefficient, S11, S12, S13, S15, or S6 admission"},
            {"guard_id": "scheduler", "status": "pass", "policy": "no scheduler action, sampler, harvest, or surface extraction"},
        ],
    )
    manifest_paths = [
        (Path("tools/extract/build_s13_right_leg_geometry_seed.py"), "task-owned builder", False, True),
        (SEGMENTATION / "recirc_segmentation_case_summary.csv", "read reverse-flow mask provenance", False, False),
        (ROI_AUDIT / "summary.json", "read prior ROI alignment blocker", False, False),
        (SOURCE_BOUNDED / "release_decision.csv", "read prior source-bounded blocker", False, False),
        (DIAGNOSTIC_BRIDGE / "diagnostic_roi_average_bridge.csv", "read diagnostic-only proxy context", False, False),
    ]
    for case_id in CASE_IDS:
        manifest_paths.append((CASE_MESHES[case_id], f"read {case_id} polyMesh topology", True, False))
        manifest_paths.append((VOLUME_CSVS[case_id], f"read {case_id} cell volumes", False, False))
    manifest_paths.append((output_dir, "generated task-owned package", False, True))
    csv_dump(
        output_dir / "source_manifest.csv",
        SOURCE_FIELDS,
        [
            {
                "path": rel(path if path.is_absolute() else ROOT / path),
                "role": role,
                "exists": str((path if path.is_absolute() else ROOT / path).exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(mutated).lower(),
            }
            for path, role, native, mutated in manifest_paths
        ],
    )

    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "released_geometry_seed_ready_for_source_bounded_rerun" if group_ready else "complete_fail_closed_geometry_seed_not_ready",
        "case_count": len(CASE_IDS),
        "geometry_seed_ready_case_count": sum(1 for row in summary_rows if row["geometry_seed_release_status"].startswith("released_")),
        "geometry_seed_ready_for_source_bounded_rerun": group_ready,
        "surface_extraction_allowed": False,
        "sampler_or_harvest_allowed": False,
        "s12_hiax1_unlocked": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "reverse_flow_selection_authority": "diagnostic_only",
        "next_action": "claim source-bounded CV rerun row using geometry seed" if group_ready else "repair geometry seed envelope before source-bounded CV rerun",
    }
    json_dump(output_dir / "summary.json", summary)
    mask_dir = ensure_dir(output_dir / "masks")
    for seed in seeds:
        csv_dump(mask_dir / f"{seed.case_id}_right_leg_geometry_seed_cells.csv", SEED_CELL_FIELDS, seed_cell_rows(seed))
    write_readme(output_dir, summary)
    return {"summary": summary, "case_rows": summary_rows}


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - {rel(ROI_AUDIT / 'summary.json')}
  - {rel(SOURCE_BOUNDED / 'release_decision.csv')}
  - {rel(SEGMENTATION / 'recirc_segmentation_case_summary.csv')}
tags: [s13, upcomer-exchange, geometry-seed, right-leg, s12]
related:
  - {rel(SOURCE_BOUNDED / 's12_unlock_gate.csv')}
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Right-Leg Geometry Seed

This package builds a predeclared geometry-backed right-leg/upcomer seed from
trusted wall patches `pipeleg_right_01_lower`, `pipeleg_right_02_middle`, and
`pipeleg_right_03_upper`. The seed is the conservative wall-adjacent owner-cell
set for those patches; internal faces from those cells are classified as the
candidate interface lane for the next source-bounded CV rerun.

Decision: `{summary['decision']}`.

Reverse-flow occupancy is diagnostic only. It is reported to compare the new
geometry seed with prior velocity masks, but it does not select, release, or
fit the seed.

This package does not run surface extraction, sampler refresh, harvest,
same-QOI UQ, Fluid/S12 implementation, S11/S15/S6 trigger, fitting, model
selection, registry/admission mutation, scheduler action, native-output
mutation, or residual absorption into internal Nu.
""",
        encoding="utf-8",
    )


def main() -> int:
    payload = build_package()
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
