#!/usr/bin/env python3
"""Build the S13 source-bounded recirculation CV definition package."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract.build_s13_upcomer_exchange_topology_cv_release import (
    POLY_MESH,
    RIGHT_LEG_WALL_PATCHES,
    CASE_IDS,
    PatchRange,
    parse_boundary_patches,
    patch_name_for_face,
)
from tools.extract.openfoam_cell_volumes import (
    face_center_and_area_vector,
    first_count,
    iter_faces,
    iter_label_list,
    norm,
    read_points,
)

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition"
TOPOLOGY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release"
RECOVERY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery"
SEGMENTATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight"
GEOMETRY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract"
SURFACE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_extraction"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
SURFACE_SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
SAME_WINDOW_UQ = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design"

RECIRC_CV_FIELDS = [
    "case_id",
    "cell_id",
    "cv_role",
    "source_mask_csv",
    "release_status",
]
INTERFACE_FACE_FIELDS = [
    "case_id",
    "face_id",
    "owner_cell",
    "neighbour_cell",
    "selected_side",
    "adjacent_side",
    "area_m2",
    "normal_x",
    "normal_y",
    "normal_z",
    "normal_convention",
    "release_status",
]
WALL_FACE_FIELDS = [
    "case_id",
    "face_id",
    "owner_cell",
    "patch_name",
    "area_m2",
    "wall_role",
    "trusted_wall",
    "release_status",
]
WALL_CORE_FIELDS = [
    "case_id",
    "band_id",
    "wall_face_count",
    "wall_area_m2",
    "core_cell_count",
    "wall_patch_names",
    "band_definition",
    "q_wall_w_ready",
    "release_status",
    "blocking_reason",
]
NORMAL_FIELDS = [
    "case_id",
    "normal_basis",
    "orientation_rule",
    "positive_mdot_exchange",
    "interface_face_count",
    "finite_normals",
    "release_status",
    "blocking_reason",
]
BOUNDARY_LEDGER_FIELDS = [
    "case_id",
    "boundary_class",
    "patch_name",
    "face_count",
    "area_m2",
    "trusted_source_bounded",
    "source_sink_role",
    "release_status",
    "blocking_reason",
]
DECISION_FIELDS = [
    "case_id",
    "selected_cv_cells",
    "exchange_interface_faces",
    "exchange_interface_area_m2",
    "trusted_wall_faces",
    "trusted_wall_area_m2",
    "untrusted_boundary_faces",
    "untrusted_boundary_area_m2",
    "finite_normals",
    "source_bounded",
    "face_closed",
    "trusted_wall_faces_available",
    "release_status",
    "blocking_reason",
]
NEXT_FIELDS = ["step_id", "next_step", "trigger", "acceptance", "guardrail"]
GUARD_FIELDS = ["guard_id", "status", "policy"]
SOURCE_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


@dataclass
class CaseAccum:
    interface_faces: list[dict[str, Any]]
    wall_faces: list[dict[str, Any]]
    boundary_by_patch: dict[tuple[str, str], tuple[int, float]]
    interface_area_m2: float = 0.0
    wall_area_m2: float = 0.0
    untrusted_boundary_area_m2: float = 0.0
    untrusted_boundary_faces: int = 0
    finite_normals: bool = True


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_selected_cells(case_id: str) -> tuple[set[int], Path]:
    mask = TOPOLOGY / "masks" / f"{case_id}_selected_face_connected_recirc_cv_mask.csv"
    rows = read_csv(mask)
    cells = {int(row["cell_id"]) for row in rows}
    if not cells:
        raise ValueError(f"empty selected CV mask: {rel(mask)}")
    return cells, mask


def patch_ranges(poly_mesh: Path = POLY_MESH) -> list[PatchRange]:
    return parse_boundary_patches((poly_mesh / "boundary").read_text(encoding="utf-8", errors="replace"))


def unit(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    magnitude = norm(vector)
    if magnitude <= 0.0:
        return (0.0, 0.0, 0.0)
    return (vector[0] / magnitude, vector[1] / magnitude, vector[2] / magnitude)


def outward_normal(
    area_vector: tuple[float, float, float],
    owner_selected: bool,
    neighbour_selected: bool,
) -> tuple[float, float, float]:
    if owner_selected and not neighbour_selected:
        return unit(area_vector)
    if neighbour_selected and not owner_selected:
        return unit((-area_vector[0], -area_vector[1], -area_vector[2]))
    return (0.0, 0.0, 0.0)


def boundary_class(patch_name: str) -> tuple[str, bool, str, str]:
    if patch_name in RIGHT_LEG_WALL_PATCHES:
        return ("trusted_right_leg_wall", True, "wall_heat_boundary", "")
    return (
        "untrusted_boundary_escape",
        False,
        "unreleased_source_or_sink_boundary",
        "selected_cv_touches_non_wall_or_unreleased_boundary_faces",
    )


def record_boundary(
    accum: CaseAccum,
    patch_name: str,
    classification: str,
    trusted: bool,
    area: float,
) -> None:
    key = (classification, patch_name or "unclassified_boundary")
    count, total = accum.boundary_by_patch[key]
    accum.boundary_by_patch[key] = (count + 1, total + area)
    if not trusted:
        accum.untrusted_boundary_faces += 1
        accum.untrusted_boundary_area_m2 += area


def scan_mesh(
    selected_by_case: dict[str, set[int]],
    poly_mesh: Path = POLY_MESH,
) -> dict[str, CaseAccum]:
    points = read_points(poly_mesh / "points")
    n_faces = first_count(poly_mesh / "faces")
    n_internal = first_count(poly_mesh / "neighbour")
    patches = patch_ranges(poly_mesh)
    accum = {
        case_id: CaseAccum([], [], defaultdict(lambda: (0, 0.0)))
        for case_id in CASE_IDS
    }
    face_iter = iter_faces(poly_mesh / "faces")
    owner_iter = iter_label_list(poly_mesh / "owner")
    neighbour_iter = iter_label_list(poly_mesh / "neighbour")

    for face_id in range(n_faces):
        face = next(face_iter)
        owner = next(owner_iter)
        neighbour = next(neighbour_iter) if face_id < n_internal else None
        patch_name = "" if neighbour is not None else patch_name_for_face(face_id, patches)
        crossing_cases: list[tuple[str, bool, bool]] = []
        boundary_cases: list[str] = []
        for case_id, selected in selected_by_case.items():
            owner_selected = owner in selected
            neighbour_selected = neighbour in selected if neighbour is not None else False
            if neighbour is not None and owner_selected != neighbour_selected:
                crossing_cases.append((case_id, owner_selected, neighbour_selected))
            elif neighbour is None and owner_selected:
                boundary_cases.append(case_id)
        if not crossing_cases and not boundary_cases:
            continue
        _, area_vector = face_center_and_area_vector(face, points)
        area = norm(area_vector)
        for case_id, owner_selected, neighbour_selected in crossing_cases:
            item = accum[case_id]
            normal = outward_normal(area_vector, owner_selected, neighbour_selected)
            finite = norm(normal) > 0.0 and area > 0.0
            item.finite_normals = item.finite_normals and finite
            selected_side = "owner" if owner_selected else "neighbour"
            adjacent_side = "neighbour" if owner_selected else "owner"
            item.interface_area_m2 += area
            item.interface_faces.append(
                {
                    "case_id": case_id,
                    "face_id": face_id,
                    "owner_cell": owner,
                    "neighbour_cell": neighbour,
                    "selected_side": selected_side,
                    "adjacent_side": adjacent_side,
                    "area_m2": f"{area:.12g}",
                    "normal_x": f"{normal[0]:.12g}",
                    "normal_y": f"{normal[1]:.12g}",
                    "normal_z": f"{normal[2]:.12g}",
                    "normal_convention": "outward from selected recirculation CV toward adjacent main-flow cell; positive mdot_exchange recirc_to_main",
                    "release_status": "candidate_only",
                }
            )
        for case_id in boundary_cases:
            item = accum[case_id]
            classification, trusted, source_role, reason = boundary_class(patch_name)
            record_boundary(item, patch_name, classification, trusted, area)
            if trusted:
                item.wall_area_m2 += area
                item.wall_faces.append(
                    {
                        "case_id": case_id,
                        "face_id": face_id,
                        "owner_cell": owner,
                        "patch_name": patch_name,
                        "area_m2": f"{area:.12g}",
                        "wall_role": source_role,
                        "trusted_wall": "true",
                        "release_status": "candidate_only",
                    }
                )
            elif reason:
                item.finite_normals = item.finite_normals and area > 0.0
    return accum


def decision_for_case(case_id: str, selected_cells: set[int], accum: CaseAccum) -> dict[str, Any]:
    reasons: list[str] = []
    if not selected_cells:
        reasons.append("empty_selected_control_volume")
    if not accum.interface_faces or accum.interface_area_m2 <= 0.0:
        reasons.append("missing_positive_exchange_interface_area")
    if not accum.wall_faces or accum.wall_area_m2 <= 0.0:
        reasons.append("missing_positive_trusted_right_leg_wall_faces_or_area")
    if accum.untrusted_boundary_faces > 0:
        reasons.append("selected_cv_touches_non_wall_or_unreleased_boundary_faces")
    if not accum.finite_normals:
        reasons.append("nonfinite_or_zero_interface_normals")
    release = not reasons
    return {
        "case_id": case_id,
        "selected_cv_cells": len(selected_cells),
        "exchange_interface_faces": len(accum.interface_faces),
        "exchange_interface_area_m2": f"{accum.interface_area_m2:.12g}",
        "trusted_wall_faces": len(accum.wall_faces),
        "trusted_wall_area_m2": f"{accum.wall_area_m2:.12g}",
        "untrusted_boundary_faces": accum.untrusted_boundary_faces,
        "untrusted_boundary_area_m2": f"{accum.untrusted_boundary_area_m2:.12g}",
        "finite_normals": str(accum.finite_normals).lower(),
        "source_bounded": str(accum.untrusted_boundary_faces == 0 and bool(accum.wall_faces)).lower(),
        "face_closed": str(accum.untrusted_boundary_faces == 0).lower(),
        "trusted_wall_faces_available": str(bool(accum.wall_faces)).lower(),
        "release_status": "released_source_bounded_cv" if release else "blocked_source_bounded_cv_not_released",
        "blocking_reason": ";".join(reasons),
    }


def recirc_rows(selected_by_case: dict[str, set[int]], mask_path_by_case: dict[str, Path], release_by_case: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        for cell_id in sorted(selected_by_case[case_id]):
            rows.append(
                {
                    "case_id": case_id,
                    "cell_id": cell_id,
                    "cv_role": "selected_largest_face_connected_reverse_flow_component",
                    "source_mask_csv": rel(mask_path_by_case[case_id]),
                    "release_status": release_by_case[case_id],
                }
            )
    return rows


def wall_core_rows(accum_by_case: dict[str, CaseAccum], decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decision_by_case = {row["case_id"]: row for row in decision_rows}
    rows: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        decision = decision_by_case[case_id]
        accum = accum_by_case[case_id]
        blocked = decision["release_status"] != "released_source_bounded_cv"
        rows.append(
            {
                "case_id": case_id,
                "band_id": "right_leg_recirc_wall_core_band_candidate",
                "wall_face_count": len(accum.wall_faces),
                "wall_area_m2": f"{accum.wall_area_m2:.12g}",
                "core_cell_count": decision["selected_cv_cells"],
                "wall_patch_names": ";".join(RIGHT_LEG_WALL_PATCHES),
                "band_definition": "selected recirculation CV cells plus adjacent trusted right-leg wall boundary faces",
                "q_wall_w_ready": "false",
                "release_status": "blocked" if blocked else "released_wall_core_band_geometry_only",
                "blocking_reason": decision["blocking_reason"] if blocked else "Q_wall_W still requires wallHeatFlux/source integration in a separate row",
            }
        )
    return rows


def normal_rows(accum_by_case: dict[str, CaseAccum], decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decision_by_case = {row["case_id"]: row for row in decision_rows}
    rows: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        decision = decision_by_case[case_id]
        accum = accum_by_case[case_id]
        rows.append(
            {
                "case_id": case_id,
                "normal_basis": "OpenFOAM face area vector, flipped when the selected CV cell is the neighbour",
                "orientation_rule": "normal points outward from selected recirculation CV toward adjacent main-flow cell",
                "positive_mdot_exchange": "recirc_to_main",
                "interface_face_count": len(accum.interface_faces),
                "finite_normals": str(accum.finite_normals).lower(),
                "release_status": "released_geometry_normal_convention" if decision["release_status"] == "released_source_bounded_cv" else "blocked_cv_not_released",
                "blocking_reason": decision["blocking_reason"],
            }
        )
    return rows


def boundary_rows(accum_by_case: dict[str, CaseAccum], decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decision_by_case = {row["case_id"]: row for row in decision_rows}
    rows: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        decision = decision_by_case[case_id]
        for (classification, patch_name), (face_count, area) in sorted(accum_by_case[case_id].boundary_by_patch.items()):
            trusted = classification == "trusted_right_leg_wall"
            rows.append(
                {
                    "case_id": case_id,
                    "boundary_class": classification,
                    "patch_name": patch_name,
                    "face_count": face_count,
                    "area_m2": f"{area:.12g}",
                    "trusted_source_bounded": str(trusted).lower(),
                    "source_sink_role": "wall_heat_boundary" if trusted else "unreleased_source_or_sink_boundary",
                    "release_status": "released_boundary_class" if trusted and decision["release_status"] == "released_source_bounded_cv" else "blocked_or_context_only",
                    "blocking_reason": "" if trusted else "selected_cv_touches_non_wall_or_unreleased_boundary_faces",
                }
            )
    return rows


def next_rows(group_released: bool) -> list[dict[str, str]]:
    if group_released:
        return [
            {
                "step_id": "S13-SBCV-NEXT-001",
                "next_step": "Claim wall/source Q_wall_W release row.",
                "trigger": "3/3 source-bounded CV rows released",
                "acceptance": "wallHeatFlux/source integration over released trusted wall faces with sign convention",
                "guardrail": "no sampler or S11 claim from geometry alone",
            },
            {
                "step_id": "S13-SBCV-NEXT-002",
                "next_step": "Rerun S13 sampler manifest preflight.",
                "trigger": "Q_wall_W and source/sink release pass",
                "acceptance": "3/3 sampler-ready rows",
                "guardrail": "preflight only; no harvest without separate row",
            },
        ]
    return [
        {
            "step_id": "S13-SBCV-NEXT-001",
            "next_step": "Do not rerun sampler preflight.",
            "trigger": "0/3 source-bounded CV rows released",
            "acceptance": "new geometry rule or source boundary definition that removes untrusted escapes and yields positive trusted wall faces",
            "guardrail": "no surface extraction, sampler, harvest, UQ, or S11/S12/S13 claim from blocked geometry",
        },
        {
            "step_id": "S13-SBCV-NEXT-002",
            "next_step": "Open a separate geometry-method row only if a defensible source-bounded wall/control-volume rule is proposed.",
            "trigger": "current largest reverse-flow components remain fragmented and wall-disconnected",
            "acceptance": "reproducible source-bounded CV definition passes before wall/source work",
            "guardrail": "do not substitute loop mdot planes or outlet proxies for exchange interface",
        },
    ]


def guardrails() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "status": "false", "policy": "read-only polyMesh and prior package consumption"},
        {"guard_id": "registry_or_admission_mutation", "status": "false", "policy": "geometry definition only; no admission state"},
        {"guard_id": "scheduler_action", "status": "false", "policy": "no Slurm or solver/postprocessing action"},
        {"guard_id": "surface_vtk_extraction", "status": "false", "policy": "no surface files generated"},
        {"guard_id": "sampler_or_harvest_launch", "status": "false", "policy": "blocked unless future geometry and source rows release"},
        {"guard_id": "fit_or_model_selection", "status": "false", "policy": "no K values, no closure fit, no candidate ranking"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "status": "false", "policy": "pressure and energy residual lanes remain separate"},
    ]


def source_manifest(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py"),
        Path("tools/extract/test_s13_upcomer_exchange_source_bounded_cv_definition.py"),
        TOPOLOGY / "summary.json",
        TOPOLOGY / "topology_cv_case_summary.csv",
        TOPOLOGY / "masks",
        RECOVERY / "summary.json",
        SEGMENTATION / "recirc_segmentation_case_summary.csv",
        GEOMETRY / "README.md",
        SURFACE / "surface_input_disposition.csv",
        SAMPLER_PREFLIGHT / "s13_readiness_gate.csv",
        SURFACE_SOURCE / "source_sink_summary.csv",
        SAME_WINDOW_UQ / "qoi_release_decision.csv",
        POLY_MESH,
        output_dir,
    ]
    rows = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        rel_path = rel(full)
        task_output = rel_path.startswith("tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition") or rel_path.startswith(
            "tools/extract/test_s13_upcomer_exchange_source_bounded_cv_definition"
        ) or full == output_dir
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


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: {summary["status"]}
tags: [s13, upcomer, exchange-cell, source-bounded-cv, fail-closed]
related:
  - {rel(TOPOLOGY)}
  - {rel(RECOVERY)}
---
# S13 Source-Bounded Recirculation CV Definition

This package tests whether the existing S13 reverse-flow/topology evidence can
define a source-bounded, face-closed recirculation control volume with trusted
exchange-interface faces and trusted right-leg wall faces.

## Decision

- cases processed: `{summary["case_count"]}`
- source-bounded CV releases: `{summary["released_source_bounded_cv_rows"]}`
- exchange-interface face rows: `{summary["exchange_interface_face_rows"]}`
- trusted wall face rows: `{summary["trusted_wall_face_rows"]}`
- untrusted boundary face rows: `{summary["untrusted_boundary_faces"]}`
- sampler preflight rerun allowed: `{str(summary["sampler_preflight_rerun_allowed"]).lower()}`

The result is fail-closed unless every case has finite interface area,
finite outward normals, no untrusted boundary escapes, and positive trusted
right-leg wall faces/area. Current evidence does not meet that standard.

## Outputs

- `recirc_cv_cells.csv`
- `exchange_interface_faces.csv`
- `trusted_wall_faces.csv`
- `wall_core_band.csv`
- `normal_convention.csv`
- `source_sink_boundary_ledger.csv`
- `release_decision.csv`
- `next_task_queue.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

This row does not mutate native CFD/OpenFOAM outputs, registry/admission state,
scheduler state, Fluid/external sources, blocker register, or generated docs.
It launches no solver, postprocessor, surface extraction, sampler, harvest,
fit, model selection, S11/S12/S13/S15/S6 trigger, or residual absorption into
internal `Nu`.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    selected_by_case: dict[str, set[int]] = {}
    mask_path_by_case: dict[str, Path] = {}
    for case_id in CASE_IDS:
        selected_by_case[case_id], mask_path_by_case[case_id] = load_selected_cells(case_id)
    accum_by_case = scan_mesh(selected_by_case)
    decision_rows = [decision_for_case(case_id, selected_by_case[case_id], accum_by_case[case_id]) for case_id in CASE_IDS]
    group_released = all(row["release_status"] == "released_source_bounded_cv" for row in decision_rows)
    release_by_case = {
        row["case_id"]: "released_source_bounded_cv" if group_released else "blocked_group_release_requires_all_three_cases"
        for row in decision_rows
    }
    for row in decision_rows:
        if not group_released and row["release_status"] == "released_source_bounded_cv":
            row["release_status"] = "blocked_group_release_requires_all_three_cases"
            row["blocking_reason"] = "all_three_cases_required_for_group_release"
        elif not group_released and row["release_status"] != "released_source_bounded_cv":
            row["release_status"] = "blocked_group_release_requires_all_three_cases"

    recirc = recirc_rows(selected_by_case, mask_path_by_case, release_by_case)
    interface = [item for case_id in CASE_IDS for item in accum_by_case[case_id].interface_faces]
    walls = [item for case_id in CASE_IDS for item in accum_by_case[case_id].wall_faces]
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete_released" if group_released else "complete_fail_closed_source_bounded_cv",
        "case_count": len(CASE_IDS),
        "released_source_bounded_cv_rows": len(CASE_IDS) if group_released else 0,
        "recirc_cv_cell_rows": len(recirc),
        "exchange_interface_face_rows": len(interface),
        "trusted_wall_face_rows": len(walls),
        "untrusted_boundary_faces": sum(accum.untrusted_boundary_faces for accum in accum_by_case.values()),
        "sampler_preflight_rerun_allowed": group_released,
        "wall_source_q_wall_w_release_allowed": group_released,
        "harvest_or_uq_allowed": False,
        "s11_s12_s13_candidate_claim_allowed": False,
        "native_solver_output_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "surface_extraction_launched": False,
        "sampler_or_harvest_launched": False,
        "fit_or_model_selection": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    csv_dump(output_dir / "recirc_cv_cells.csv", RECIRC_CV_FIELDS, recirc)
    csv_dump(output_dir / "exchange_interface_faces.csv", INTERFACE_FACE_FIELDS, interface)
    csv_dump(output_dir / "trusted_wall_faces.csv", WALL_FACE_FIELDS, walls)
    csv_dump(output_dir / "wall_core_band.csv", WALL_CORE_FIELDS, wall_core_rows(accum_by_case, decision_rows))
    csv_dump(output_dir / "normal_convention.csv", NORMAL_FIELDS, normal_rows(accum_by_case, decision_rows))
    csv_dump(output_dir / "source_sink_boundary_ledger.csv", BOUNDARY_LEDGER_FIELDS, boundary_rows(accum_by_case, decision_rows))
    csv_dump(output_dir / "release_decision.csv", DECISION_FIELDS, decision_rows)
    csv_dump(output_dir / "next_task_queue.csv", NEXT_FIELDS, next_rows(group_released))
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guardrails())
    csv_dump(output_dir / "source_manifest.csv", SOURCE_FIELDS, source_manifest(output_dir))
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return {
        "summary": summary,
        "decision_rows": decision_rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(args.output_dir)
    print(json.dumps(payload["summary"], indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
