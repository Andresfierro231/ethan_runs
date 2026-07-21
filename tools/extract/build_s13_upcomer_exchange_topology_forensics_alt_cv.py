#!/usr/bin/env python3
"""Build S13 upcomer exchange topology forensics and alternate-CV package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract import build_s13_upcomer_exchange_topology_cv_release as topo
from tools.extract.openfoam_cell_volumes import (
    face_center_and_area_vector,
    first_count,
    iter_faces,
    iter_label_list,
    norm,
    read_points,
)

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv"
SEGMENTATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight"
TOPOLOGY_RELEASE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release"
INTERFACE_RECOVERY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
INPUT_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"

CASE_IDS = ("salt_2", "salt_3", "salt_4")
RIGHT_LEG_WALL_PATCHES = topo.RIGHT_LEG_WALL_PATCHES
MIN_DOMINANT_COMPONENT_FRACTION = topo.MIN_DOMINANT_COMPONENT_FRACTION

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

COMPONENT_FIELDS = [
    "case_id",
    "face_component_id",
    "cell_count",
    "fraction_of_reverse_candidates",
    "volume_m3",
    "x_min",
    "x_max",
    "y_min",
    "y_max",
    "z_min",
    "z_max",
    "mean_speed_m_s",
    "interface_face_count",
    "interface_area_m2",
    "right_leg_wall_face_count",
    "right_leg_wall_area_m2",
    "boundary_escape_face_count",
    "boundary_escape_area_m2",
    "release_status",
    "blocking_reason",
    "alternate_cv_selected",
    "selection_basis",
]
CASE_FIELDS = [
    "case_id",
    "reverse_candidate_cells",
    "face_component_count",
    "wall_adjacent_component_count",
    "largest_component_id",
    "largest_component_cells",
    "largest_component_fraction",
    "selected_alt_component_id",
    "selected_alt_cells",
    "selected_alt_fraction",
    "selected_alt_volume_m3",
    "selected_alt_interface_face_count",
    "selected_alt_interface_area_m2",
    "selected_alt_wall_face_count",
    "selected_alt_wall_area_m2",
    "selected_alt_boundary_escape_face_count",
    "selected_alt_release_status",
    "blocking_reason",
]
SURFACE_FIELDS = [
    "case_id",
    "surface_lane",
    "release_status",
    "face_source",
    "face_count",
    "area_m2",
    "normal_vector_convention",
    "consumer",
    "blocking_reason",
]
BOUNDARY_FIELDS = [
    "case_id",
    "face_component_id",
    "patch_name",
    "face_count",
    "area_m2",
    "alternate_cv_selected",
    "classification",
]
OCCUPANCY_FIELDS = [
    "case_id",
    "diagnostic_lane",
    "value",
    "units",
    "status",
    "basis",
]
DOWNSTREAM_FIELDS = [
    "case_id",
    "downstream_lane",
    "status",
    "required_input",
    "available_input",
    "blocking_reason",
]
MASK_FIELDS = ["cell_id", "face_component_id", "mask_role", "source_mask_csv"]
GUARD_FIELDS = ["guard_id", "status", "policy"]
SOURCE_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


@dataclass
class ComponentStats:
    case_id: str
    component_id: int
    cells: set[int]
    total_reverse_cells: int
    source_mask_csv: Path
    volume_m3: float = 0.0
    x_min: float = math.inf
    x_max: float = -math.inf
    y_min: float = math.inf
    y_max: float = -math.inf
    z_min: float = math.inf
    z_max: float = -math.inf
    speed_sum: float = 0.0
    speed_count: int = 0
    interface_face_count: int = 0
    interface_area_m2: float = 0.0
    right_leg_wall_face_count: int = 0
    right_leg_wall_area_m2: float = 0.0
    boundary_escape_face_count: int = 0
    boundary_escape_area_m2: float = 0.0
    boundary_by_patch: dict[str, tuple[int, float]] = field(default_factory=dict)
    selected_alt: bool = False
    selection_basis: str = ""

    @property
    def fraction(self) -> float:
        return len(self.cells) / self.total_reverse_cells if self.total_reverse_cells else 0.0

    @property
    def mean_speed(self) -> float:
        return self.speed_sum / self.speed_count if self.speed_count else 0.0


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def face_area(face: list[int], points: list[tuple[float, float, float]]) -> float:
    _, area_vector = face_center_and_area_vector(face, points)
    return norm(area_vector)


def load_mask_rows(mask_csv: Path) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    for row in read_csv(mask_csv):
        rows[int(row["cell_id"])] = row
    if not rows:
        raise ValueError(f"empty mask CSV: {rel(mask_csv)}")
    return rows


def mask_payloads() -> dict[str, dict[str, Any]]:
    metrics = topo.component_metrics()
    payloads: dict[str, dict[str, Any]] = {}
    for case_id in CASE_IDS:
        mask_path = ROOT / metrics[case_id]["mask_csv"]
        rows = load_mask_rows(mask_path)
        payloads[case_id] = {
            "mask_csv": mask_path,
            "rows": rows,
            "all_cells": set(rows),
            "metrics": metrics[case_id],
        }
    return payloads


def component_stats_from_masks(payloads: dict[str, dict[str, Any]]) -> dict[str, dict[int, ComponentStats]]:
    component_results = topo.build_face_component_results(payloads)
    stats_by_case: dict[str, dict[int, ComponentStats]] = {}
    for case_id, result in component_results.items():
        payload = payloads[case_id]
        total = len(payload["all_cells"])
        stats_by_component: dict[int, ComponentStats] = {}
        for component_id, cells in enumerate(result.components, start=1):
            stats_by_component[component_id] = ComponentStats(
                case_id=case_id,
                component_id=component_id,
                cells=set(cells),
                total_reverse_cells=total,
                source_mask_csv=payload["mask_csv"],
            )
        for cell_id, row in payload["rows"].items():
            component_id = result.component_by_cell[cell_id]
            stats = stats_by_component[component_id]
            cx = float(row["cx"])
            cy = float(row["cy"])
            cz = float(row["cz"])
            stats.x_min = min(stats.x_min, cx)
            stats.x_max = max(stats.x_max, cx)
            stats.y_min = min(stats.y_min, cy)
            stats.y_max = max(stats.y_max, cy)
            stats.z_min = min(stats.z_min, cz)
            stats.z_max = max(stats.z_max, cz)
            stats.speed_sum += float(row["speed"])
            stats.speed_count += 1
        payload["face_component_result"] = result
        stats_by_case[case_id] = stats_by_component
    return stats_by_case


def attach_volumes(stats_by_case: dict[str, dict[int, ComponentStats]]) -> None:
    cell_to_component: dict[str, dict[int, int]] = {}
    for case_id, stats_by_component in stats_by_case.items():
        mapping: dict[int, int] = {}
        for component_id, stats in stats_by_component.items():
            for cell_id in stats.cells:
                mapping[cell_id] = component_id
        cell_to_component[case_id] = mapping
    for case_id, path in VOLUME_CSVS.items():
        mapping = cell_to_component[case_id]
        for row in read_csv(path):
            cell_id = int(row["cell_id"])
            component_id = mapping.get(cell_id)
            if component_id is not None:
                stats_by_case[case_id][component_id].volume_m3 += float(row["cellVolume_m3"])


def patch_name_for_face(face_i: int, patches: list[topo.PatchRange]) -> str:
    for patch in patches:
        if patch.start_face <= face_i < patch.end_face:
            return patch.name
    return ""


def add_boundary(stats: ComponentStats, patch_name: str, area: float) -> None:
    key = patch_name or "unclassified_boundary"
    count, existing_area = stats.boundary_by_patch.get(key, (0, 0.0))
    stats.boundary_by_patch[key] = (count + 1, existing_area + area)


def attach_topology(stats_by_case: dict[str, dict[int, ComponentStats]], payloads: dict[str, dict[str, Any]]) -> None:
    for case_id in CASE_IDS:
        poly_mesh = CASE_MESHES[case_id]
        points = read_points(poly_mesh / "points")
        n_faces = first_count(poly_mesh / "faces")
        n_internal = first_count(poly_mesh / "neighbour")
        all_patches = topo.parse_boundary_patches((poly_mesh / "boundary").read_text(encoding="utf-8", errors="replace"))
        missing = set(RIGHT_LEG_WALL_PATCHES) - {patch.name for patch in all_patches}
        if missing:
            raise ValueError(f"{case_id} missing right-leg wall patches: {sorted(missing)}")
        component_by_cell = payloads[case_id]["face_component_result"].component_by_cell
        face_iter = iter_faces(poly_mesh / "faces")
        owner_iter = iter_label_list(poly_mesh / "owner")
        neighbour_iter = iter_label_list(poly_mesh / "neighbour")
        for face_i in range(n_faces):
            face = next(face_iter)
            owner = next(owner_iter)
            neighbour = next(neighbour_iter) if face_i < n_internal else None
            owner_component = component_by_cell.get(owner)
            neighbour_component = component_by_cell.get(neighbour) if neighbour is not None else None
            touched = owner_component is not None or neighbour_component is not None
            if not touched:
                continue
            if neighbour is not None:
                if owner_component == neighbour_component:
                    continue
                area = face_area(face, points)
                for component_id in (owner_component, neighbour_component):
                    if component_id is None:
                        continue
                    stats = stats_by_case[case_id][component_id]
                    stats.interface_face_count += 1
                    stats.interface_area_m2 += area
            elif owner_component is not None:
                patch_name = patch_name_for_face(face_i, all_patches)
                area = face_area(face, points)
                stats = stats_by_case[case_id][owner_component]
                if patch_name in RIGHT_LEG_WALL_PATCHES:
                    stats.right_leg_wall_face_count += 1
                    stats.right_leg_wall_area_m2 += area
                else:
                    stats.boundary_escape_face_count += 1
                    stats.boundary_escape_area_m2 += area
                    add_boundary(stats, patch_name, area)


def release_reasons(stats: ComponentStats) -> list[str]:
    reasons: list[str] = []
    if stats.fraction < MIN_DOMINANT_COMPONENT_FRACTION:
        reasons.append(f"component_fraction_below_{MIN_DOMINANT_COMPONENT_FRACTION:g}")
    if len(stats.cells) <= 0:
        reasons.append("empty_component")
    if stats.interface_face_count <= 0 or stats.interface_area_m2 <= 0.0:
        reasons.append("missing_positive_interface_faces_or_area")
    if stats.right_leg_wall_face_count <= 0 or stats.right_leg_wall_area_m2 <= 0.0:
        reasons.append("missing_positive_right_leg_wall_faces_or_area")
    if stats.boundary_escape_face_count > 0:
        reasons.append("component_touches_non_wall_or_unreleased_boundary_faces")
    return reasons


def release_status(stats: ComponentStats) -> tuple[str, str]:
    reasons = release_reasons(stats)
    if reasons:
        return "blocked_alt_cv_not_released", ";".join(reasons)
    return "released_alt_cv", ""


def choose_alternate_component(stats_by_component: dict[int, ComponentStats]) -> ComponentStats:
    releasable = [stats for stats in stats_by_component.values() if not release_reasons(stats)]
    if releasable:
        chosen = sorted(releasable, key=lambda item: (-len(item.cells), item.component_id))[0]
        chosen.selection_basis = "largest_component_passing_existing_release_gates"
        return chosen
    wall_adjacent = [stats for stats in stats_by_component.values() if stats.right_leg_wall_face_count > 0]
    if wall_adjacent:
        chosen = sorted(
            wall_adjacent,
            key=lambda item: (-item.right_leg_wall_area_m2, -len(item.cells), item.component_id),
        )[0]
        chosen.selection_basis = "largest_right_leg_wall_area_reverse_component_but_gate_blocked"
        return chosen
    chosen = sorted(stats_by_component.values(), key=lambda item: (-len(item.cells), item.component_id))[0]
    chosen.selection_basis = "largest_reverse_component_no_wall_adjacent_reverse_component_found"
    return chosen


def component_row(stats: ComponentStats) -> dict[str, Any]:
    status, reason = release_status(stats)
    return {
        "case_id": stats.case_id,
        "face_component_id": stats.component_id,
        "cell_count": len(stats.cells),
        "fraction_of_reverse_candidates": f"{stats.fraction:.9g}",
        "volume_m3": f"{stats.volume_m3:.12g}",
        "x_min": f"{stats.x_min:.12g}",
        "x_max": f"{stats.x_max:.12g}",
        "y_min": f"{stats.y_min:.12g}",
        "y_max": f"{stats.y_max:.12g}",
        "z_min": f"{stats.z_min:.12g}",
        "z_max": f"{stats.z_max:.12g}",
        "mean_speed_m_s": f"{stats.mean_speed:.12g}",
        "interface_face_count": stats.interface_face_count,
        "interface_area_m2": f"{stats.interface_area_m2:.12g}",
        "right_leg_wall_face_count": stats.right_leg_wall_face_count,
        "right_leg_wall_area_m2": f"{stats.right_leg_wall_area_m2:.12g}",
        "boundary_escape_face_count": stats.boundary_escape_face_count,
        "boundary_escape_area_m2": f"{stats.boundary_escape_area_m2:.12g}",
        "release_status": status,
        "blocking_reason": reason,
        "alternate_cv_selected": str(stats.selected_alt).lower(),
        "selection_basis": stats.selection_basis,
    }


def build_rows(
    stats_by_case: dict[str, dict[int, ComponentStats]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, ComponentStats]]:
    selected: dict[str, ComponentStats] = {}
    component_rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    surface_rows: list[dict[str, Any]] = []
    boundary_rows: list[dict[str, Any]] = []
    occupancy_rows: list[dict[str, Any]] = []
    downstream_rows: list[dict[str, Any]] = []

    for case_id in CASE_IDS:
        chosen = choose_alternate_component(stats_by_case[case_id])
        chosen.selected_alt = True
        selected[case_id] = chosen

    group_release = all(release_status(stats)[0] == "released_alt_cv" for stats in selected.values())
    for case_id in CASE_IDS:
        stats_by_component = stats_by_case[case_id]
        chosen = selected[case_id]
        for stats in sorted(stats_by_component.values(), key=lambda item: item.component_id):
            component_rows.append(component_row(stats))
            for patch_name, (face_count, area) in sorted(stats.boundary_by_patch.items()):
                boundary_rows.append(
                    {
                        "case_id": case_id,
                        "face_component_id": stats.component_id,
                        "patch_name": patch_name,
                        "face_count": face_count,
                        "area_m2": f"{area:.12g}",
                        "alternate_cv_selected": str(stats.selected_alt).lower(),
                        "classification": "reverse_component_boundary_escape_not_released_wall_band",
                    }
                )
        local_status, local_reason = release_status(chosen)
        selected_status = local_status if group_release else "blocked_group_release_requires_all_three_cases"
        reason = local_reason or ("" if group_release else "all_three_cases_must_release_before_downstream_extraction")
        largest = sorted(stats_by_component.values(), key=lambda item: (-len(item.cells), item.component_id))[0]
        wall_adjacent_count = sum(1 for item in stats_by_component.values() if item.right_leg_wall_face_count > 0)
        case_rows.append(
            {
                "case_id": case_id,
                "reverse_candidate_cells": chosen.total_reverse_cells,
                "face_component_count": len(stats_by_component),
                "wall_adjacent_component_count": wall_adjacent_count,
                "largest_component_id": largest.component_id,
                "largest_component_cells": len(largest.cells),
                "largest_component_fraction": f"{largest.fraction:.9g}",
                "selected_alt_component_id": chosen.component_id,
                "selected_alt_cells": len(chosen.cells),
                "selected_alt_fraction": f"{chosen.fraction:.9g}",
                "selected_alt_volume_m3": f"{chosen.volume_m3:.12g}",
                "selected_alt_interface_face_count": chosen.interface_face_count,
                "selected_alt_interface_area_m2": f"{chosen.interface_area_m2:.12g}",
                "selected_alt_wall_face_count": chosen.right_leg_wall_face_count,
                "selected_alt_wall_area_m2": f"{chosen.right_leg_wall_area_m2:.12g}",
                "selected_alt_boundary_escape_face_count": chosen.boundary_escape_face_count,
                "selected_alt_release_status": selected_status,
                "blocking_reason": reason,
            }
        )
        released = selected_status == "released_alt_cv"
        for lane, face_count, area, consumer in (
            ("exchange_interface_faces", chosen.interface_face_count, chosen.interface_area_m2, "mdot_exchange integration"),
            ("right_leg_wall_faces", chosen.right_leg_wall_face_count, chosen.right_leg_wall_area_m2, "wall/core thermal contrast and Q_wall_W integration"),
            ("surface_vtk_extraction", 0, 0.0, "downstream sampler manifest"),
        ):
            surface_rows.append(
                {
                    "case_id": case_id,
                    "surface_lane": lane,
                    "release_status": "released" if released and lane != "surface_vtk_extraction" else ("ready" if released else "blocked"),
                    "face_source": "OpenFOAM owner/neighbour plus selected alternate face component" if released else "",
                    "face_count": face_count,
                    "area_m2": f"{area:.12g}",
                    "normal_vector_convention": "positive mdot_exchange from selected recirculation component toward adjacent main-throughflow cell",
                    "consumer": consumer,
                    "blocking_reason": "" if released else reason,
                }
            )
        occupancy_rows.extend(
            [
                {
                    "case_id": case_id,
                    "diagnostic_lane": "selected_reverse_component_fraction",
                    "value": f"{chosen.fraction:.9g}",
                    "units": "fraction",
                    "status": "diagnostic_only",
                    "basis": "selected alternate CV is still a reverse-flow component, not an admitted physical heat-loss closure",
                },
                {
                    "case_id": case_id,
                    "diagnostic_lane": "selected_reverse_component_volume",
                    "value": f"{chosen.volume_m3:.12g}",
                    "units": "m3",
                    "status": "diagnostic_only",
                    "basis": "volume from task-owned cell-volume CSV restricted to selected reverse-flow component",
                },
                {
                    "case_id": case_id,
                    "diagnostic_lane": "wall_adjacent_reverse_component_count",
                    "value": str(wall_adjacent_count),
                    "units": "count",
                    "status": "diagnostic_only",
                    "basis": "components with at least one owner face on right-leg wall patches",
                },
            ]
        )
        for lane, required in (
            ("surface_extraction", "3/3 released alternate CVs with positive interface and wall areas and zero unclassified escapes"),
            ("sampler_manifest_refresh", "released exchange_interface_vtk, wall_vtk, normals, and Q_wall_W/source lane"),
            ("production_harvest", "3/3 sampler-ready rows"),
            ("same_qoi_uq", "released production QOIs in same time/mesh window"),
            ("S11_S15_S6_trigger", "one runtime-legal candidate after UQ/source-property release"),
        ):
            downstream_rows.append(
                {
                    "case_id": case_id,
                    "downstream_lane": lane,
                    "status": "ready" if released and lane == "surface_extraction" else "blocked",
                    "required_input": required,
                    "available_input": "released alternate topology CV" if released and lane == "surface_extraction" else "",
                    "blocking_reason": "" if released and lane == "surface_extraction" else reason or "upstream gate not reached",
                }
            )
    return (
        {
            "component_rows": component_rows,
            "case_rows": case_rows,
            "surface_rows": surface_rows,
            "boundary_rows": boundary_rows,
            "occupancy_rows": occupancy_rows,
            "downstream_rows": downstream_rows,
        },
        selected,
    )


def write_selected_masks(output_dir: Path, selected: dict[str, ComponentStats]) -> None:
    mask_dir = ensure_dir(output_dir / "masks")
    for case_id, stats in selected.items():
        rows = [
            {
                "cell_id": cell_id,
                "face_component_id": stats.component_id,
                "mask_role": "selected_alternate_reverse_component_diagnostic_only",
                "source_mask_csv": rel(stats.source_mask_csv),
            }
            for cell_id in sorted(stats.cells)
        ]
        csv_dump(mask_dir / f"{case_id}_selected_alternate_cv_mask.csv", MASK_FIELDS, rows)


def source_manifest(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py"),
        Path("tools/extract/test_s13_upcomer_exchange_topology_forensics_alt_cv.py"),
        SEGMENTATION / "recirc_segmentation_case_summary.csv",
        SEGMENTATION / "masks",
        TOPOLOGY_RELEASE / "topology_cv_case_summary.csv",
        TOPOLOGY_RELEASE / "face_connected_component_summary.csv",
        INTERFACE_RECOVERY / "s13_unblock_decision.csv",
        SAMPLER_PREFLIGHT / "next_evidence_actions.csv",
        INPUT_GENERATION / "cell_volume_export_validation.csv",
        INPUT_GENERATION / "cell_volumes",
        *[CASE_MESHES[case_id] for case_id in CASE_IDS],
        output_dir,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        rel_path = rel(full)
        task_output = full == output_dir or rel_path.startswith("tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv") or rel_path.startswith("tools/extract/test_s13_upcomer_exchange_topology_forensics_alt_cv")
        rows.append(
            {
                "path": rel_path,
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(rel_path.startswith("jadyn_runs/")).lower(),
                "mutated": str(task_output and full != output_dir).lower(),
            }
        )
    return rows


def guardrails() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "status": "false", "policy": "read-only polyMesh access; no OpenFOAM output writes"},
        {"guard_id": "scheduler_action", "status": "false", "policy": "local topology/CSV analysis only"},
        {"guard_id": "surface_vtk_extraction", "status": "false", "policy": "surface extraction remains downstream and gated"},
        {"guard_id": "sampler_or_harvest_launch", "status": "false", "policy": "no sampler or production harvest in forensics row"},
        {"guard_id": "threshold_relaxation", "status": "false", "policy": "dominance/wall/interface/escape gates are unchanged"},
        {"guard_id": "proxy_interface_admission", "status": "false", "policy": "no loop-mdot or outlet proxy substituted for exchange interface"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "status": "false", "policy": "heat residual, Q_wall_W, and internal Nu remain separate lanes"},
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: {summary["status"]}
tags: [s13, upcomer, exchange-cell, topology, forensics, alternate-cv, fail-closed]
related:
  - {rel(SEGMENTATION)}
  - {rel(TOPOLOGY_RELEASE)}
---
# S13 Upcomer Exchange Topology Forensics and Alternate CV

This package diagnoses why the prior S13 topology CV release failed and tests
one conservative alternate selection from the same reverse-flow evidence. The
alternate selector prefers a reverse-flow face component with right-leg wall
contact if one exists, but it keeps the existing release gates: dominant
component fraction, positive interface area, positive right-leg wall area, and
zero unclassified boundary escapes.

## Decision

- cases processed: `{summary["case_count"]}`
- component forensic rows: `{summary["component_forensic_rows"]}`
- selected alternate CV rows released: `{summary["released_alt_cv_rows"]}`
- surface extraction allowed: `{str(summary["surface_extraction_allowed"]).lower()}`
- scheduler action: `false`
- sampler/harvest launched: `false`

Result: `{summary["status"]}`. Reverse-flow evidence remains diagnostic unless
all three cases release together under the unchanged topology gates.

## Outputs

- `component_topology_forensics.csv`
- `alternate_cv_case_summary.csv`
- `alternate_cv_surface_contract.csv`
- `alternate_cv_boundary_escape_by_patch.csv`
- `reverse_occupancy_diagnostics.csv`
- `downstream_release_gate.csv`
- `masks/*_selected_alternate_cv_mask.csv`
- `no_mutation_guardrails.csv`, `source_manifest.csv`, and `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated documentation index,
surface VTK extraction, sampler/harvest, fit, score, model selection,
S11/S15/S6 trigger, threshold relaxation, proxy-interface admission, or
internal-Nu residual absorption is changed by this package.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(output_dir: Path = PACKAGE_DIR, compute_topology: bool = True) -> dict[str, Any]:
    ensure_dir(output_dir)
    payloads = mask_payloads()
    stats_by_case = component_stats_from_masks(payloads)
    if compute_topology:
        attach_volumes(stats_by_case)
        attach_topology(stats_by_case, payloads)
    rows, selected = build_rows(stats_by_case)
    write_selected_masks(output_dir, selected)
    released = [row for row in rows["case_rows"] if row["selected_alt_release_status"] == "released_alt_cv"]
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete_released" if len(released) == len(CASE_IDS) else "complete_fail_closed_alt_cv",
        "case_count": len(CASE_IDS),
        "component_forensic_rows": len(rows["component_rows"]),
        "released_alt_cv_rows": len(released),
        "surface_extraction_allowed": len(released) == len(CASE_IDS),
        "scheduler_action": False,
        "surface_vtk_extraction_launched": False,
        "exchange_cell_harvest_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "threshold_relaxation": False,
        "proxy_interface_admission": False,
        "exchange_cell_admission": False,
        "residual_absorbed_into_internal_Nu": False,
        "dominance_gate": MIN_DOMINANT_COMPONENT_FRACTION,
    }
    csv_dump(output_dir / "component_topology_forensics.csv", COMPONENT_FIELDS, rows["component_rows"])
    csv_dump(output_dir / "alternate_cv_case_summary.csv", CASE_FIELDS, rows["case_rows"])
    csv_dump(output_dir / "alternate_cv_surface_contract.csv", SURFACE_FIELDS, rows["surface_rows"])
    csv_dump(output_dir / "alternate_cv_boundary_escape_by_patch.csv", BOUNDARY_FIELDS, rows["boundary_rows"])
    csv_dump(output_dir / "reverse_occupancy_diagnostics.csv", OCCUPANCY_FIELDS, rows["occupancy_rows"])
    csv_dump(output_dir / "downstream_release_gate.csv", DOWNSTREAM_FIELDS, rows["downstream_rows"])
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guardrails())
    csv_dump(output_dir / "source_manifest.csv", SOURCE_FIELDS, source_manifest(output_dir))
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return {**rows, "summary": summary}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR)
    parser.add_argument("--no-topology", action="store_true", help="Build shell without streaming case polyMesh topology.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(args.output_dir, compute_topology=not args.no_topology)
    print(json.dumps(payload["summary"], indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
