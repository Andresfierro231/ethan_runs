#!/usr/bin/env python3
"""Build S13/S14 recirculation control-volume segmentation preflight."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from array import array
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-S14-RECIRC-CV-SEGMENTATION-PREFLIGHT-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight"
SALT2_CELL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke"
SALT34_CELL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix"
GEOMETRY_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract"
S14 = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence"

CASE_VTKS = {
    "salt_2": SALT2_CELL / "vtk/salt_2_cell_fields.vtk",
    "salt_3": SALT34_CELL / "vtk/salt_3_cell_fields.vtk",
    "salt_4": SALT34_CELL / "vtk/salt_4_cell_fields.vtk",
}
EXPECTED_CELLS = 2166996
RIGHT_LEG_X_FRACTION_MIN = 0.72
REVERSE_SPEED_FRACTION = 0.02
MIN_COMPONENT_FRACTION_FOR_RELEASE = 0.80

SUMMARY_FIELDS = [
    "case_id",
    "cell_vtk",
    "observed_cells",
    "domain_x_min",
    "domain_x_max",
    "right_leg_x_min",
    "right_leg_roi_cells",
    "throughflow_axis",
    "dominant_axis_sign",
    "reverse_candidate_cells",
    "largest_component_cells",
    "largest_component_fraction",
    "mask_csv",
    "release_status",
    "blocking_reason",
]
COMPONENT_FIELDS = [
    "case_id",
    "component_id",
    "cell_count",
    "fraction_of_reverse_candidates",
    "cx_min",
    "cx_max",
    "cy_min",
    "cy_max",
    "cz_min",
    "cz_max",
    "mean_uy",
    "status",
]
MASK_FIELDS = [
    "cell_id",
    "cx",
    "cy",
    "cz",
    "ux",
    "uy",
    "uz",
    "speed",
    "component_id",
    "mask_role",
]
INTERFACE_FIELDS = [
    "case_id",
    "recirc_mask_status",
    "exchange_interface_status",
    "normal_convention",
    "required_next_input",
    "blocking_reason",
]
WALL_CORE_FIELDS = [
    "case_id",
    "recirc_mask_status",
    "wall_core_status",
    "q_wall_w_status",
    "required_next_input",
    "blocking_reason",
]
S14_FIELDS = [
    "candidate_family",
    "branch_or_feature",
    "dominant_use_label",
    "admitted_rows",
    "future_candidate_rows",
    "recirc_cv_dependency",
    "f3_shah_apparent_comparison_status",
    "current_decision",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


@dataclass(frozen=True)
class RoiCell:
    cell_id: int
    cx: float
    cy: float
    cz: float
    point_ids: tuple[int, ...]


@dataclass
class CandidateCell:
    cell_id: int
    cx: float
    cy: float
    cz: float
    ux: float
    uy: float
    uz: float
    speed: float
    component_id: int = -1


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def token_lines(handle: Iterable[str]) -> Iterable[str]:
    for line in handle:
        for token in line.split():
            yield token


def consume_tokens(tokens: Iterable[str], count: int) -> list[str]:
    out: list[str] = []
    iterator = iter(tokens)
    for _ in range(count):
        out.append(next(iterator))
    return out


def parse_points(handle: Any, header: str) -> tuple[array, array, array, int]:
    parts = header.split()
    if len(parts) < 3 or parts[0] != "POINTS":
        raise ValueError(f"Expected POINTS header, got: {header!r}")
    n_points = int(parts[1])
    xs = array("f")
    ys = array("f")
    zs = array("f")
    need = n_points * 3
    seen = 0
    while seen < need:
        line = handle.readline()
        if not line:
            raise ValueError("Unexpected EOF while reading POINTS")
        for token in line.split():
            value = float(token)
            coord = seen % 3
            if coord == 0:
                xs.append(value)
            elif coord == 1:
                ys.append(value)
            else:
                zs.append(value)
            seen += 1
            if seen == need:
                break
    return xs, ys, zs, n_points


def parse_cells_for_right_leg_roi(
    handle: Any,
    header: str,
    xs: array,
    ys: array,
    zs: array,
    *,
    x_fraction_min: float = RIGHT_LEG_X_FRACTION_MIN,
) -> tuple[list[RoiCell], int, float, float, float]:
    parts = header.split()
    if len(parts) < 3 or parts[0] != "CELLS":
        raise ValueError(f"Expected CELLS header, got: {header!r}")
    n_cells = int(parts[1])
    x_min = min(xs)
    x_max = max(xs)
    right_leg_x_min = x_min + x_fraction_min * (x_max - x_min)
    roi: list[RoiCell] = []
    tokens = iter(token_lines(handle))
    for cell_id in range(n_cells):
        try:
            n_ids = int(next(tokens))
            point_ids = tuple(int(next(tokens)) for _ in range(n_ids))
        except StopIteration as exc:
            raise ValueError("Unexpected EOF while reading CELLS") from exc
        if n_ids == 0:
            continue
        cx = sum(xs[idx] for idx in point_ids) / n_ids
        cy = sum(ys[idx] for idx in point_ids) / n_ids
        cz = sum(zs[idx] for idx in point_ids) / n_ids
        if cx >= right_leg_x_min:
            roi.append(RoiCell(cell_id=cell_id, cx=cx, cy=cy, cz=cz, point_ids=point_ids))
    return roi, n_cells, float(x_min), float(x_max), float(right_leg_x_min)


def skip_cell_types(handle: Any, header: str) -> None:
    parts = header.split()
    if len(parts) < 2 or parts[0] != "CELL_TYPES":
        raise ValueError(f"Expected CELL_TYPES header, got: {header!r}")
    remaining = int(parts[1])
    while remaining > 0:
        line = handle.readline()
        if not line:
            raise ValueError("Unexpected EOF while reading CELL_TYPES")
        remaining -= len(line.split())


def skip_field_values(handle: Any, n_values: int) -> None:
    remaining = n_values
    while remaining > 0:
        line = handle.readline()
        if not line:
            raise ValueError("Unexpected EOF while skipping FIELD values")
        remaining -= len(line.split())


def read_u_candidates(
    handle: Any,
    n_cells: int,
    roi_by_cell: dict[int, RoiCell],
) -> tuple[list[CandidateCell], int, int]:
    line = handle.readline()
    while line and not line.startswith("CELL_DATA"):
        line = handle.readline()
    if not line:
        raise ValueError("CELL_DATA not found")
    cell_data_count = int(line.split()[1])
    if cell_data_count != n_cells:
        raise ValueError(f"CELL_DATA count {cell_data_count} differs from CELLS count {n_cells}")
    field = handle.readline().split()
    if len(field) < 3 or field[0] != "FIELD":
        raise ValueError("Expected FIELD attributes after CELL_DATA")
    n_arrays = int(field[2])
    roi_uy_sum = 0.0
    roi_seen = 0
    candidates: list[CandidateCell] = []
    for _ in range(n_arrays):
        header = handle.readline().split()
        while not header:
            header = handle.readline().split()
        name = header[0]
        ncomp = int(header[1])
        ntuples = int(header[2])
        if name != "U":
            skip_field_values(handle, ncomp * ntuples)
            continue
        if ncomp != 3 or ntuples != n_cells:
            raise ValueError(f"Unexpected U array shape ncomp={ncomp} ntuples={ntuples}")
        cell_id = 0
        pending: list[float] = []
        while cell_id < n_cells:
            while len(pending) < 3:
                line = handle.readline()
                if not line:
                    raise ValueError("Unexpected EOF while reading U")
                pending.extend(float(token) for token in line.split())
            ux, uy, uz = pending[:3]
            del pending[:3]
            roi = roi_by_cell.get(cell_id)
            if roi is not None:
                roi_uy_sum += uy
                roi_seen += 1
                speed = math.sqrt(ux * ux + uy * uy + uz * uz)
                candidates.append(
                    CandidateCell(
                        cell_id=cell_id,
                        cx=roi.cx,
                        cy=roi.cy,
                        cz=roi.cz,
                        ux=ux,
                        uy=uy,
                        uz=uz,
                        speed=speed,
                    )
                )
            cell_id += 1
        return candidates, roi_seen, 1 if roi_uy_sum >= 0.0 else -1
    raise ValueError("U field not found")


def find_next_header(handle: Any, expected: str) -> str:
    line = handle.readline()
    while line and not line.startswith(expected):
        line = handle.readline()
    if not line:
        raise ValueError(f"{expected} header not found")
    return line.strip()


def read_vtk_right_leg_candidates(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8", errors="strict") as handle:
        points_header = find_next_header(handle, "POINTS")
        xs, ys, zs, _ = parse_points(handle, points_header)
        cells_header = find_next_header(handle, "CELLS")
        roi, n_cells, x_min, x_max, right_leg_x_min = parse_cells_for_right_leg_roi(handle, cells_header, xs, ys, zs)
        cell_types_header = find_next_header(handle, "CELL_TYPES")
        skip_cell_types(handle, cell_types_header)
        roi_by_cell = {cell.cell_id: cell for cell in roi}
        roi_velocity_cells, roi_seen, dominant_sign = read_u_candidates(handle, n_cells, roi_by_cell)
    reverse_candidates = [
        cell
        for cell in roi_velocity_cells
        if cell.speed > 0.0 and cell.uy * dominant_sign < -REVERSE_SPEED_FRACTION * cell.speed
    ]
    components = label_point_connected_components(reverse_candidates, roi_by_cell)
    return {
        "n_cells": n_cells,
        "x_min": x_min,
        "x_max": x_max,
        "right_leg_x_min": right_leg_x_min,
        "roi_cells": roi_seen,
        "dominant_sign": dominant_sign,
        "candidates": reverse_candidates,
        "components": components,
    }


def label_point_connected_components(
    candidates: list[CandidateCell],
    roi_by_cell: dict[int, RoiCell],
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    candidate_ids = {cell.cell_id for cell in candidates}
    point_to_cells: dict[int, list[int]] = defaultdict(list)
    for cell in candidates:
        for point_id in roi_by_cell[cell.cell_id].point_ids:
            point_to_cells[point_id].append(cell.cell_id)
    adjacency: dict[int, set[int]] = {cell.cell_id: set() for cell in candidates}
    for cell_ids in point_to_cells.values():
        if len(cell_ids) < 2:
            continue
        for cell_id in cell_ids:
            adjacency[cell_id].update(other for other in cell_ids if other != cell_id and other in candidate_ids)
    by_id = {cell.cell_id: cell for cell in candidates}
    seen: set[int] = set()
    components: list[dict[str, Any]] = []
    for cell in candidates:
        if cell.cell_id in seen:
            continue
        component_id = len(components)
        queue: deque[int] = deque([cell.cell_id])
        seen.add(cell.cell_id)
        ids: list[int] = []
        while queue:
            current = queue.popleft()
            ids.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        for cell_id in ids:
            by_id[cell_id].component_id = component_id
        component_cells = [by_id[cell_id] for cell_id in ids]
        components.append(component_summary(component_id, component_cells, len(candidates)))
    components.sort(key=lambda row: int(row["cell_count"]), reverse=True)
    rank_map = {int(row["component_id"]): rank for rank, row in enumerate(components)}
    for cell in candidates:
        cell.component_id = rank_map[cell.component_id]
    for rank, row in enumerate(components):
        row["component_id"] = rank
        row["status"] = "largest_component" if rank == 0 else "stray_component"
    return components


def component_summary(component_id: int, cells: list[CandidateCell], total: int) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "cell_count": len(cells),
        "fraction_of_reverse_candidates": len(cells) / total if total else 0.0,
        "cx_min": min(cell.cx for cell in cells),
        "cx_max": max(cell.cx for cell in cells),
        "cy_min": min(cell.cy for cell in cells),
        "cy_max": max(cell.cy for cell in cells),
        "cz_min": min(cell.cz for cell in cells),
        "cz_max": max(cell.cz for cell in cells),
        "mean_uy": sum(cell.uy for cell in cells) / len(cells),
        "status": "",
    }


def write_mask(path: Path, candidates: list[CandidateCell]) -> None:
    rows = []
    for cell in candidates:
        rows.append(
            {
                "cell_id": cell.cell_id,
                "cx": f"{cell.cx:.9g}",
                "cy": f"{cell.cy:.9g}",
                "cz": f"{cell.cz:.9g}",
                "ux": f"{cell.ux:.9g}",
                "uy": f"{cell.uy:.9g}",
                "uz": f"{cell.uz:.9g}",
                "speed": f"{cell.speed:.9g}",
                "component_id": cell.component_id,
                "mask_role": "largest_candidate_component" if cell.component_id == 0 else "stray_candidate_component",
            }
        )
    csv_dump(path, MASK_FIELDS, rows)


def case_segmentation(case_id: str, vtk_path: Path, output_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = read_vtk_right_leg_candidates(vtk_path)
    candidates: list[CandidateCell] = payload["candidates"]
    components: list[dict[str, Any]] = payload["components"]
    mask_path = output_dir / "masks" / f"{case_id}_right_leg_reverse_flow_candidate_mask.csv"
    write_mask(mask_path, candidates)
    largest = int(components[0]["cell_count"]) if components else 0
    fraction = float(components[0]["fraction_of_reverse_candidates"]) if components else 0.0
    if not candidates:
        release_status = "blocked_no_reverse_flow_candidate_in_right_leg_roi"
        reason = "velocity topology did not identify a reverse-flow candidate in the right-leg ROI"
    elif fraction < MIN_COMPONENT_FRACTION_FOR_RELEASE:
        release_status = "blocked_fragmented_velocity_topology"
        reason = "reverse-flow candidates are fragmented; no single connected component dominates"
    else:
        release_status = "candidate_mask_generated_not_released"
        reason = "largest velocity-connected candidate exists, but VTK-only point connectivity does not prove a face-closed recirculation control volume or wall/interface ownership"
    summary = {
        "case_id": case_id,
        "cell_vtk": rel(vtk_path),
        "observed_cells": payload["n_cells"],
        "domain_x_min": f"{payload['x_min']:.9g}",
        "domain_x_max": f"{payload['x_max']:.9g}",
        "right_leg_x_min": f"{payload['right_leg_x_min']:.9g}",
        "right_leg_roi_cells": payload["roi_cells"],
        "throughflow_axis": "y",
        "dominant_axis_sign": payload["dominant_sign"],
        "reverse_candidate_cells": len(candidates),
        "largest_component_cells": largest,
        "largest_component_fraction": f"{fraction:.9g}",
        "mask_csv": rel(mask_path),
        "release_status": release_status,
        "blocking_reason": reason,
    }
    component_rows = [{"case_id": case_id, **row} for row in components]
    return summary, component_rows


def interface_preflight_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for row in summary_rows:
        released = row["release_status"] == "released_face_closed_recirc_cv"
        rows.append(
            {
                "case_id": row["case_id"],
                "recirc_mask_status": row["release_status"],
                "exchange_interface_status": "ready_for_internal_face_derivation" if released else "blocked",
                "normal_convention": "positive mdot_exchange from recirculation cell to main throughflow",
                "required_next_input": "face-neighbor topology proving a closed internal boundary between mask cells and main-flow cells",
                "blocking_reason": "" if released else "recirculation mask is diagnostic/preflight only, not a released face-closed control volume",
            }
        )
    return rows


def wall_core_preflight_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for row in summary_rows:
        released = row["release_status"] == "released_face_closed_recirc_cv"
        rows.append(
            {
                "case_id": row["case_id"],
                "recirc_mask_status": row["release_status"],
                "wall_core_status": "ready_for_wall_patch_intersection" if released else "blocked",
                "q_wall_w_status": "ready_after_wall_band" if released else "blocked",
                "required_next_input": "wall-face adjacency for the released recirculation control volume plus area-weighting convention",
                "blocking_reason": "" if released else "wall/core band cannot be released from a diagnostic mask",
            }
        )
    return rows


def s14_linkage_rows() -> list[dict[str, str]]:
    branch_rows = read_csv(S14 / "f6_branch_decision_table.csv")
    comparison = read_csv(S14 / "f3_vs_f6_comparison_readiness.csv")[0]
    rows = []
    for row in branch_rows:
        branch = row["branch_or_feature"]
        if branch == "right_leg":
            dependency = "recirc_cv_needed_to_separate_low_recirc_anchor_from_exchange_cell_region"
        elif branch == "test_section_span":
            dependency = "recirc_cv_needed_as_negative_control_context; endpoint_and_same_qoi_uq_still_primary"
        elif "corner" in branch:
            dependency = "recirc_cv_context_only; current corner rows remain section_effective_or_do_not_use"
        else:
            dependency = "no_direct_release_from_recirc_cv_preflight"
        rows.append(
            {
                "candidate_family": row["candidate_family"],
                "branch_or_feature": branch,
                "dominant_use_label": row["dominant_use_label"],
                "admitted_rows": row["admitted_rows"],
                "future_candidate_rows": row["future_candidate_rows"],
                "recirc_cv_dependency": dependency,
                "f3_shah_apparent_comparison_status": comparison["comparison_status"],
                "current_decision": row["decision"],
            }
        )
    return rows


def guard_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_outputs", "status": "pass_read_only", "policy": "read validated task-owned VTK exports only"},
        {"guard_id": "surface_extraction", "status": "blocked", "policy": "no interface or wall VTK extraction from diagnostic masks"},
        {"guard_id": "harvest", "status": "blocked", "policy": "no exchange-cell harvest until a face-closed recirculation volume and surface lanes exist"},
        {"guard_id": "pressure_f6", "status": "blocked_no_admission", "policy": "S14 remains diagnostic/future-candidate only; no component K or F6 fit"},
        {"guard_id": "residual_lane", "status": "pass", "policy": "do not absorb pressure or energy residual into internal Nu"},
    ]


def manifest_rows(output_dir: Path) -> list[dict[str, str]]:
    paths = [
        Path("tools/extract/build_s13_s14_recirc_cv_segmentation_preflight.py"),
        Path("tools/extract/test_s13_s14_recirc_cv_segmentation_preflight.py"),
        SALT2_CELL,
        SALT34_CELL,
        GEOMETRY_CONTRACT,
        S14,
        output_dir,
    ]
    rows = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        relative = rel(full)
        task_output = (
            full == output_dir
            or relative.startswith("tools/extract/build_s13_s14_recirc_cv_segmentation_preflight")
            or relative.startswith("tools/extract/test_s13_s14_recirc_cv_segmentation_preflight")
        )
        rows.append(
            {
                "path": relative,
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(relative.startswith("jadyn_runs/")).lower(),
                "mutated": str(task_output).lower(),
            }
        )
    return rows


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: {summary["status"]}
tags: [upcomer, recirculation, control-volume, segmentation, s13, s14, no-admission]
related:
  - {rel(GEOMETRY_CONTRACT)}
  - {rel(S14)}
---
# S13/S14 Recirculation Control-Volume Segmentation Preflight

This package implements the first recovery step after the geometry contract
failed closed. It reads the validated whole-mesh cell VTKs, builds right-leg
velocity-topology reverse-flow candidate masks, and decides whether those masks
are strong enough to release the exchange interface and wall/core lanes.

## Decision

- cases processed: `{summary["case_count"]}`
- candidate masks generated: `{summary["candidate_masks_generated"]}`
- released recirculation control volumes: `{summary["released_recirc_cv_rows"]}`
- exchange-interface rows released: `{summary["released_exchange_interface_rows"]}`
- wall/core rows released: `{summary["released_wall_core_rows"]}`
- S14 F6/component-K admissions: `0`
- surface extraction launched: `false`
- exchange-cell harvest launched: `false`

The masks are useful diagnostic starting points, but they are not released as
face-closed recirculation control volumes. A future row must derive face
neighbors/internal faces from mesh topology before `mdot_exchange`, `Q_wall_W`,
or wall/core thermal contrast can be computed.

## Outputs

- `recirc_segmentation_case_summary.csv`
- `recirc_component_summary.csv`
- `masks/*_right_leg_reverse_flow_candidate_mask.csv`
- `exchange_interface_derivation_preflight.csv`
- `wall_core_band_derivation_preflight.csv`
- `s14_pressure_anchor_recirc_linkage.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native solver outputs, registry/admission state, scheduler state, Fluid or
external source, surface VTK extraction, sampler/harvest, fitting, component
`K`, F6 admission, S11/S15 trigger, or residual absorption into internal `Nu`
is changed by this package.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir / "masks")
    summary_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    for case_id, vtk_path in CASE_VTKS.items():
        case_summary, case_components = case_segmentation(case_id, vtk_path, output_dir)
        summary_rows.append(case_summary)
        component_rows.extend(case_components)
    interface_rows = interface_preflight_rows(summary_rows)
    wall_core_rows = wall_core_preflight_rows(summary_rows)
    s14_rows = s14_linkage_rows()
    guards = guard_rows()
    manifest = manifest_rows(output_dir)
    released_cv = sum(1 for row in summary_rows if row["release_status"] == "released_face_closed_recirc_cv")
    generated_masks = sum(1 for row in summary_rows if int(row["reverse_candidate_cells"]) > 0)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete_fail_closed_diagnostic_masks",
        "case_count": len(summary_rows),
        "candidate_masks_generated": generated_masks,
        "released_recirc_cv_rows": released_cv,
        "released_exchange_interface_rows": 0,
        "released_wall_core_rows": 0,
        "surface_vtk_extraction_launched": False,
        "exchange_cell_harvest_launched": False,
        "s14_component_k_or_f6_admitted_rows": 0,
        "f3_shah_apparent_comparison_performed": False,
        "native_output_mutation": False,
        "scheduler_action": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    csv_dump(output_dir / "recirc_segmentation_case_summary.csv", SUMMARY_FIELDS, summary_rows)
    csv_dump(output_dir / "recirc_component_summary.csv", COMPONENT_FIELDS, component_rows)
    csv_dump(output_dir / "exchange_interface_derivation_preflight.csv", INTERFACE_FIELDS, interface_rows)
    csv_dump(output_dir / "wall_core_band_derivation_preflight.csv", WALL_CORE_FIELDS, wall_core_rows)
    csv_dump(output_dir / "s14_pressure_anchor_recirc_linkage.csv", S14_FIELDS, s14_rows)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {"summary": summary, "case_summary": summary_rows, "components": component_rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(PACKAGE_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(Path(args.output_dir))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
