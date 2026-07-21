#!/usr/bin/env python3
"""Build the S13 upcomer exchange topology control-volume release package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract.openfoam_cell_volumes import (
    face_center_and_area_vector,
    first_count,
    iter_faces,
    iter_label_list,
    norm,
    read_points,
)

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-CV-RELEASE-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release"
SEGMENTATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight"
CANDIDATE_RECOVERY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_candidate_uq_s13_geometry_recovery"
THREE_CASE_MANIFEST = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest"
SURFACE_SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
POLY_MESH = ROOT / (
    "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/"
    "runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/"
    "constant/polyMesh"
)
CASE_IDS = ("salt_2", "salt_3", "salt_4")
RIGHT_LEG_WALL_PATCHES = ("pipeleg_right_01_lower", "pipeleg_right_02_middle", "pipeleg_right_03_upper")
MIN_DOMINANT_COMPONENT_FRACTION = 0.75

CASE_FIELDS = [
    "case_id",
    "candidate_mask_cells",
    "point_largest_component_cells",
    "point_largest_component_fraction",
    "face_component_count",
    "largest_face_component_cells",
    "largest_face_component_fraction",
    "selected_cv_cells",
    "interface_face_count",
    "interface_area_m2",
    "right_leg_wall_face_count",
    "right_leg_wall_area_m2",
    "boundary_escape_face_count",
    "topology_release_status",
    "blocking_reason",
]
FACE_COMPONENT_FIELDS = [
    "case_id",
    "face_component_id",
    "cell_count",
    "fraction_of_reverse_candidates",
    "selected_cv_component",
]
SELECTED_MASK_FIELDS = [
    "cell_id",
    "face_component_id",
    "mask_role",
    "source_mask_csv",
]
INTERFACE_FIELDS = [
    "case_id",
    "release_status",
    "interface_source",
    "surface_definition",
    "interface_face_count",
    "interface_area_m2",
    "normal_vector_convention",
    "mdot_exchange_ready",
    "blocking_reason",
]
BOUNDARY_FIELDS = [
    "case_id",
    "patch_name",
    "face_count",
    "area_m2",
    "classification",
]
WALL_FIELDS = [
    "case_id",
    "release_status",
    "recirculation_cell_volume_source",
    "wall_band_source",
    "wall_patch_candidates",
    "wall_face_count",
    "wall_area_m2",
    "q_wall_w_ready",
    "blocking_reason",
]
DOWNSTREAM_FIELDS = [
    "case_id",
    "input_lane",
    "status",
    "required_input",
    "available_input",
    "consumer",
    "blocking_reason",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
SOURCE_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]
BOUNDARY_RE = re.compile(
    r"(?P<name>[A-Za-z0-9_]+)\s*\{(?P<body>.*?)\}",
    re.DOTALL,
)


@dataclass(frozen=True)
class PatchRange:
    name: str
    start_face: int
    n_faces: int

    @property
    def end_face(self) -> int:
        return self.start_face + self.n_faces


@dataclass
class TopologyStats:
    interface_face_count: int = 0
    interface_area_m2: float = 0.0
    wall_face_count: int = 0
    wall_area_m2: float = 0.0
    boundary_escape_face_count: int = 0
    boundary_escape_area_m2: float = 0.0
    boundary_by_patch: dict[str, tuple[int, float]] | None = None


@dataclass
class FaceComponentResult:
    component_by_cell: dict[int, int]
    components: list[set[int]]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_boundary_patches(text: str) -> list[PatchRange]:
    patches: list[PatchRange] = []
    for match in BOUNDARY_RE.finditer(text):
        body = match.group("body")
        n_faces = re.search(r"\bnFaces\s+(\d+)\s*;", body)
        start_face = re.search(r"\bstartFace\s+(\d+)\s*;", body)
        if n_faces and start_face:
            patches.append(PatchRange(match.group("name"), int(start_face.group(1)), int(n_faces.group(1))))
    return patches


def right_leg_patch_ranges(poly_mesh: Path = POLY_MESH) -> list[PatchRange]:
    patches = parse_boundary_patches((poly_mesh / "boundary").read_text(encoding="utf-8", errors="replace"))
    selected = [patch for patch in patches if patch.name in RIGHT_LEG_WALL_PATCHES]
    missing = sorted(set(RIGHT_LEG_WALL_PATCHES) - {patch.name for patch in selected})
    if missing:
        raise ValueError(f"Missing right-leg wall patches in boundary: {missing}")
    return selected


def patch_name_for_face(face_i: int, patches: list[PatchRange]) -> str:
    for patch in patches:
        if patch.start_face <= face_i < patch.end_face:
            return patch.name
    return ""


def load_mask_cells(mask_csv: Path) -> tuple[set[int], set[int]]:
    all_cells: set[int] = set()
    largest_cells: set[int] = set()
    for row in read_csv(mask_csv):
        cell_id = int(row["cell_id"])
        all_cells.add(cell_id)
        if row.get("mask_role") in {"largest_component", "largest_candidate_component"}:
            largest_cells.add(cell_id)
    if not all_cells:
        raise ValueError(f"empty mask CSV: {rel(mask_csv)}")
    if not largest_cells:
        raise ValueError(f"mask CSV has no largest_component rows: {rel(mask_csv)}")
    return all_cells, largest_cells


def component_metrics() -> dict[str, dict[str, str]]:
    rows = read_csv(SEGMENTATION / "recirc_segmentation_case_summary.csv")
    selected = {row["case_id"]: row for row in rows if row["case_id"] in CASE_IDS}
    missing = sorted(set(CASE_IDS) - set(selected))
    if missing:
        raise ValueError(f"Missing segmentation summary rows: {missing}")
    return selected


def mask_inputs() -> dict[str, dict[str, Any]]:
    metrics = component_metrics()
    out: dict[str, dict[str, Any]] = {}
    for case_id in CASE_IDS:
        mask_path = ROOT / metrics[case_id]["mask_csv"]
        all_cells, largest_cells = load_mask_cells(mask_path)
        out[case_id] = {
            "mask_csv": mask_path,
            "all_cells": all_cells,
            "selected_cells": largest_cells,
            "metrics": metrics[case_id],
        }
    return out


def build_face_component_results(
    mask_by_case: dict[str, dict[str, Any]],
    poly_mesh: Path = POLY_MESH,
) -> dict[str, FaceComponentResult]:
    adjacency: dict[str, dict[int, list[int]]] = {
        case_id: {cell_id: [] for cell_id in payload["all_cells"]}
        for case_id, payload in mask_by_case.items()
    }
    candidate_sets = {case_id: payload["all_cells"] for case_id, payload in mask_by_case.items()}
    n_internal = first_count(poly_mesh / "neighbour")
    owner_iter = iter_label_list(poly_mesh / "owner")
    neighbour_iter = iter_label_list(poly_mesh / "neighbour")
    for _ in range(n_internal):
        owner = next(owner_iter)
        neighbour = next(neighbour_iter)
        for case_id, candidates in candidate_sets.items():
            if owner in candidates and neighbour in candidates:
                adjacency[case_id][owner].append(neighbour)
                adjacency[case_id][neighbour].append(owner)

    results: dict[str, FaceComponentResult] = {}
    for case_id, graph in adjacency.items():
        component_by_cell: dict[int, int] = {}
        components: list[set[int]] = []
        for cell_id in graph:
            if cell_id in component_by_cell:
                continue
            component_id = len(components) + 1
            component_cells: set[int] = set()
            queue: deque[int] = deque([cell_id])
            component_by_cell[cell_id] = component_id
            while queue:
                current = queue.popleft()
                component_cells.add(current)
                for neighbour in graph[current]:
                    if neighbour not in component_by_cell:
                        component_by_cell[neighbour] = component_id
                        queue.append(neighbour)
            components.append(component_cells)
        components.sort(key=lambda cells: (-len(cells), min(cells)))
        remapped: dict[int, int] = {}
        for new_id, cells in enumerate(components, start=1):
            for cell_id in cells:
                remapped[cell_id] = new_id
        results[case_id] = FaceComponentResult(component_by_cell=remapped, components=components)
    return results


def attach_face_components(mask_by_case: dict[str, dict[str, Any]], output_dir: Path) -> list[dict[str, Any]]:
    results = build_face_component_results(mask_by_case)
    rows: list[dict[str, Any]] = []
    mask_dir = ensure_dir(output_dir / "masks")
    for case_id, result in results.items():
        payload = mask_by_case[case_id]
        candidate_count = len(payload["all_cells"])
        selected_cells = result.components[0] if result.components else set()
        payload["face_component_result"] = result
        payload["selected_cells"] = selected_cells
        payload["face_component_count"] = len(result.components)
        payload["largest_face_component_cells"] = len(selected_cells)
        payload["largest_face_component_fraction"] = len(selected_cells) / candidate_count if candidate_count else 0.0
        for component_id, cells in enumerate(result.components, start=1):
            rows.append(
                {
                    "case_id": case_id,
                    "face_component_id": component_id,
                    "cell_count": len(cells),
                    "fraction_of_reverse_candidates": f"{(len(cells) / candidate_count if candidate_count else 0.0):.9g}",
                    "selected_cv_component": str(component_id == 1).lower(),
                }
            )
        selected_rows = [
            {
                "cell_id": cell_id,
                "face_component_id": 1,
                "mask_role": "selected_largest_face_connected_reverse_flow_component",
                "source_mask_csv": rel(payload["mask_csv"]),
            }
            for cell_id in sorted(selected_cells)
        ]
        csv_dump(
            mask_dir / f"{case_id}_selected_face_connected_recirc_cv_mask.csv",
            SELECTED_MASK_FIELDS,
            selected_rows,
        )
    return rows


def face_area(face: list[int], points: list[tuple[float, float, float]]) -> float:
    _, area_vector = face_center_and_area_vector(face, points)
    return norm(area_vector)


def accumulate_topology(mask_by_case: dict[str, dict[str, Any]], poly_mesh: Path = POLY_MESH) -> dict[str, TopologyStats]:
    points = read_points(poly_mesh / "points")
    n_faces = first_count(poly_mesh / "faces")
    n_internal = first_count(poly_mesh / "neighbour")
    all_patches = parse_boundary_patches((poly_mesh / "boundary").read_text(encoding="utf-8", errors="replace"))
    right_leg_patch_ranges(poly_mesh)
    stats = {case_id: TopologyStats() for case_id in CASE_IDS}
    for item in stats.values():
        item.boundary_by_patch = defaultdict(lambda: (0, 0.0))
    face_iter = iter_faces(poly_mesh / "faces")
    owner_iter = iter_label_list(poly_mesh / "owner")
    neighbour_iter = iter_label_list(poly_mesh / "neighbour")

    for face_i in range(n_faces):
        face = next(face_iter)
        owner = next(owner_iter)
        neighbour = next(neighbour_iter) if face_i < n_internal else None
        patch_name = "" if face_i < n_internal else patch_name_for_face(face_i, all_patches)

        needs_area = False
        crossing: list[str] = []
        wall_owner: list[str] = []
        escape_owner: list[str] = []
        for case_id, payload in mask_by_case.items():
            selected: set[int] = payload["selected_cells"]
            owner_in = owner in selected
            if neighbour is not None:
                neigh_in = neighbour in selected
                if owner_in != neigh_in:
                    crossing.append(case_id)
                    needs_area = True
            elif owner_in:
                if patch_name in RIGHT_LEG_WALL_PATCHES:
                    wall_owner.append(case_id)
                    needs_area = True
                else:
                    escape_owner.append(case_id)
                    needs_area = True
        if not needs_area and not escape_owner:
            continue
        area = face_area(face, points) if needs_area else 0.0
        for case_id in crossing:
            stats[case_id].interface_face_count += 1
            stats[case_id].interface_area_m2 += area
        for case_id in wall_owner:
            stats[case_id].wall_face_count += 1
            stats[case_id].wall_area_m2 += area
        for case_id in escape_owner:
            stats[case_id].boundary_escape_face_count += 1
            stats[case_id].boundary_escape_area_m2 += area
            if stats[case_id].boundary_by_patch is not None:
                count, patch_area = stats[case_id].boundary_by_patch[patch_name or "unclassified_boundary"]
                stats[case_id].boundary_by_patch[patch_name or "unclassified_boundary"] = (count + 1, patch_area + area)
    return stats


def release_decision(mask_payload: dict[str, Any], stats: TopologyStats) -> tuple[str, str]:
    reasons: list[str] = []
    largest_fraction = float(mask_payload["largest_face_component_fraction"])
    selected = len(mask_payload["selected_cells"])
    if largest_fraction < MIN_DOMINANT_COMPONENT_FRACTION:
        reasons.append(f"largest_face_component_fraction_below_{MIN_DOMINANT_COMPONENT_FRACTION:g}")
    if selected <= 0:
        reasons.append("empty_selected_control_volume")
    if stats.interface_face_count <= 0 or stats.interface_area_m2 <= 0.0:
        reasons.append("missing_positive_interface_faces_or_area")
    if stats.wall_face_count <= 0 or stats.wall_area_m2 <= 0.0:
        reasons.append("missing_positive_right_leg_wall_faces_or_area")
    if stats.boundary_escape_face_count > 0:
        reasons.append("selected_cv_touches_non_wall_or_unreleased_boundary_faces")
    if reasons:
        return "blocked_topology_cv_not_released", ";".join(reasons)
    return "released_topology_cv", ""


def build_rows(mask_by_case: dict[str, dict[str, Any]], stats_by_case: dict[str, TopologyStats]) -> dict[str, list[dict[str, Any]]]:
    case_rows: list[dict[str, Any]] = []
    interface_rows: list[dict[str, Any]] = []
    wall_rows: list[dict[str, Any]] = []
    downstream_rows: list[dict[str, Any]] = []
    boundary_rows: list[dict[str, Any]] = []
    all_released = True
    decisions: dict[str, tuple[str, str]] = {}

    for case_id in CASE_IDS:
        payload = mask_by_case[case_id]
        stats = stats_by_case[case_id]
        status, reason = release_decision(payload, stats)
        decisions[case_id] = (status, reason)
        all_released = all_released and status == "released_topology_cv"

    group_release = all_released
    for case_id in CASE_IDS:
        payload = mask_by_case[case_id]
        stats = stats_by_case[case_id]
        local_status, local_reason = decisions[case_id]
        status = local_status if group_release else "blocked_group_release_requires_all_three_cases"
        reason = local_reason if local_reason else ("all_cases_release_required" if not group_release else "")
        metrics = payload["metrics"]
        case_rows.append(
            {
                "case_id": case_id,
                "candidate_mask_cells": len(payload["all_cells"]),
                "point_largest_component_cells": metrics["largest_component_cells"],
                "point_largest_component_fraction": metrics["largest_component_fraction"],
                "face_component_count": payload.get("face_component_count", ""),
                "largest_face_component_cells": payload.get("largest_face_component_cells", ""),
                "largest_face_component_fraction": f"{float(payload.get('largest_face_component_fraction', 0.0)):.9g}",
                "selected_cv_cells": len(payload["selected_cells"]),
                "interface_face_count": stats.interface_face_count,
                "interface_area_m2": f"{stats.interface_area_m2:.12g}",
                "right_leg_wall_face_count": stats.wall_face_count,
                "right_leg_wall_area_m2": f"{stats.wall_area_m2:.12g}",
                "boundary_escape_face_count": stats.boundary_escape_face_count,
                "topology_release_status": status,
                "blocking_reason": reason,
            }
        )
        released = status == "released_topology_cv"
        interface_rows.append(
            {
                "case_id": case_id,
                "release_status": "released" if released else "blocked",
                "interface_source": rel(payload["mask_csv"]) if released else "",
                "surface_definition": "internal owner/neighbour faces with exactly one selected recirculation-cell neighbor" if released else "not_released",
                "interface_face_count": stats.interface_face_count,
                "interface_area_m2": f"{stats.interface_area_m2:.12g}",
                "normal_vector_convention": "face-normal oriented from selected recirculation cell toward adjacent main cell; positive mdot_exchange recirc_to_main",
                "mdot_exchange_ready": str(released).lower(),
                "blocking_reason": "" if released else reason,
            }
        )
        wall_rows.append(
            {
                "case_id": case_id,
                "release_status": "released" if released else "blocked",
                "recirculation_cell_volume_source": rel(payload["mask_csv"]) if released else "",
                "wall_band_source": rel(POLY_MESH / "boundary") if released else "",
                "wall_patch_candidates": ";".join(RIGHT_LEG_WALL_PATCHES),
                "wall_face_count": stats.wall_face_count,
                "wall_area_m2": f"{stats.wall_area_m2:.12g}",
                "q_wall_w_ready": "false",
                "blocking_reason": "Q_wall_W still requires wallHeatFlux integration over released wall faces" if released else reason,
            }
        )
        for lane, available, consumer in (
            ("exchange_interface_vtk", "", "mdot_exchange integration"),
            ("wall_core_vtk", "", "wall/core thermal contrast and Q_wall_W integration"),
            ("Q_wall_W", "", "energy residual"),
            ("surface_vtk_extraction", "", "downstream sampler manifest"),
        ):
            downstream_rows.append(
                {
                    "case_id": case_id,
                    "input_lane": lane,
                    "status": "ready_for_surface_extraction" if released and lane != "Q_wall_W" else "blocked",
                    "required_input": "released topology CV with face ids, areas, normals, and wall-band ownership",
                    "available_input": available,
                    "consumer": consumer,
                    "blocking_reason": "" if released and lane != "Q_wall_W" else reason or "Q_wall_W requires separate wallHeatFlux integration",
                }
            )
        if stats.boundary_by_patch:
            for patch_name, (face_count, area) in sorted(stats.boundary_by_patch.items()):
                boundary_rows.append(
                    {
                        "case_id": case_id,
                        "patch_name": patch_name,
                        "face_count": face_count,
                        "area_m2": f"{area:.12g}",
                        "classification": "selected_cv_boundary_escape_not_released_wall_band",
                    }
                )
    return {
        "case_rows": case_rows,
        "interface_rows": interface_rows,
        "wall_rows": wall_rows,
        "downstream_rows": downstream_rows,
        "boundary_rows": boundary_rows,
    }


def source_manifest(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/build_s13_upcomer_exchange_topology_cv_release.py"),
        Path("tools/extract/test_s13_upcomer_exchange_topology_cv_release.py"),
        SEGMENTATION / "recirc_segmentation_case_summary.csv",
        SEGMENTATION / "recirc_component_summary.csv",
        SEGMENTATION / "masks",
        CANDIDATE_RECOVERY / "geometry_source_recovery_decision.csv",
        THREE_CASE_MANIFEST / "three_case_cell_vtk_manifest.csv",
        SURFACE_SOURCE / "source_sink_summary.csv",
        SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv",
        POLY_MESH,
        output_dir,
    ]
    rows = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        task_output = full == output_dir or str(path).startswith("tools/extract/build_s13_upcomer_exchange_topology_cv_release") or str(path).startswith("tools/extract/test_s13_upcomer_exchange_topology_cv_release")
        rel_path = rel(full)
        native = rel_path.startswith("jadyn_runs/")
        rows.append(
            {
                "path": rel_path,
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(task_output and full != output_dir).lower(),
            }
        )
    return rows


def guardrails() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "status": "false", "policy": "read polyMesh and prior masks only"},
        {"guard_id": "scheduler_action", "status": "false", "policy": "topology release is local metadata/mesh parsing only"},
        {"guard_id": "surface_vtk_extraction", "status": "false", "policy": "no surface VTKs are generated in this row"},
        {"guard_id": "sampler_or_harvest_launch", "status": "false", "policy": "topology release must pass before sampler work"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "status": "false", "policy": "energy residual and Q_wall_W remain separate lanes"},
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: {summary["status"]}
tags: [upcomer, exchange-cell, topology, control-volume, fail-closed]
related:
  - {rel(SEGMENTATION)}
  - {rel(CANDIDATE_RECOVERY)}
---
# S13 Upcomer Exchange Topology Control-Volume Release

This package uses the completed right-leg reverse-flow diagnostic masks and
OpenFOAM owner/neighbour topology to decide whether a face-connected
recirculation control volume can release the S13 exchange-interface and wall
lanes.

## Decision

- cases processed: `{summary["case_count"]}`
- topology CV rows released: `{summary["released_topology_cv_rows"]}`
- exchange-interface rows released: `{summary["released_exchange_interface_rows"]}`
- wall/core rows released: `{summary["released_wall_core_rows"]}`
- surface extraction allowed: `{str(summary["surface_extraction_allowed"]).lower()}`
- scheduler action: `false`
- sampler/harvest launched: `false`

The topology pass relabels the right-leg reverse-flow candidates into
face-connected components from OpenFOAM `owner/neighbour`, then derives
interface and wall face counts/areas for the largest face-connected component.
It still fails closed unless the same physical topology source yields a
dominant component, positive interface area, positive trusted wall-band area,
and no unclassified boundary escape. Therefore this package does not release
`exchange_interface_vtk`, `wall_vtk`, or `Q_wall_W` unless those gates all pass
for Salt2/Salt3/Salt4 together.

## Outputs

- `topology_cv_case_summary.csv`
- `face_connected_component_summary.csv`
- `boundary_escape_by_patch.csv`
- `masks/*_selected_face_connected_recirc_cv_mask.csv`
- `exchange_interface_topology_contract.csv`
- `wall_core_topology_contract.csv`
- `downstream_surface_extraction_gate.csv`
- `no_mutation_guardrails.csv`, `source_manifest.csv`, and `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated docs index, surface
VTK extraction, sampler/harvest, fit, score, model selection, S11/S15/S6
trigger, or internal-Nu residual absorption is changed by this package.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(output_dir: Path = PACKAGE_DIR, compute_topology: bool = True) -> dict[str, Any]:
    ensure_dir(output_dir)
    masks = mask_inputs()
    face_component_rows = attach_face_components(masks, output_dir) if compute_topology else []
    if not compute_topology:
        for payload in masks.values():
            payload["selected_cells"] = set()
            payload["face_component_count"] = ""
            payload["largest_face_component_cells"] = ""
            payload["largest_face_component_fraction"] = 0.0
    stats = accumulate_topology(masks) if compute_topology else {case_id: TopologyStats() for case_id in CASE_IDS}
    rows = build_rows(masks, stats)
    released = [row for row in rows["case_rows"] if row["topology_release_status"] == "released_topology_cv"]
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete_released" if len(released) == len(CASE_IDS) else "complete_fail_closed_topology",
        "case_count": len(CASE_IDS),
        "released_topology_cv_rows": len(released),
        "released_exchange_interface_rows": sum(1 for row in rows["interface_rows"] if row["release_status"] == "released"),
        "released_wall_core_rows": sum(1 for row in rows["wall_rows"] if row["release_status"] == "released"),
        "surface_extraction_allowed": len(released) == len(CASE_IDS),
        "scheduler_action": False,
        "surface_vtk_extraction_launched": False,
        "exchange_cell_harvest_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "exchange_cell_admission": False,
        "residual_absorbed_into_internal_Nu": False,
        "dominance_gate": MIN_DOMINANT_COMPONENT_FRACTION,
    }
    csv_dump(output_dir / "topology_cv_case_summary.csv", CASE_FIELDS, rows["case_rows"])
    csv_dump(output_dir / "face_connected_component_summary.csv", FACE_COMPONENT_FIELDS, face_component_rows)
    csv_dump(output_dir / "boundary_escape_by_patch.csv", BOUNDARY_FIELDS, rows["boundary_rows"])
    csv_dump(output_dir / "exchange_interface_topology_contract.csv", INTERFACE_FIELDS, rows["interface_rows"])
    csv_dump(output_dir / "wall_core_topology_contract.csv", WALL_FIELDS, rows["wall_rows"])
    csv_dump(output_dir / "downstream_surface_extraction_gate.csv", DOWNSTREAM_FIELDS, rows["downstream_rows"])
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guardrails())
    csv_dump(output_dir / "source_manifest.csv", SOURCE_FIELDS, source_manifest(output_dir))
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return {**rows, "summary": summary}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR)
    parser.add_argument("--no-topology", action="store_true", help="Build package shell without streaming polyMesh topology.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(args.output_dir, compute_topology=not args.no_topology)
    print(json.dumps(payload["summary"], indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
