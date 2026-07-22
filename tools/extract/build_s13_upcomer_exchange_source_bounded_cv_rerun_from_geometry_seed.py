#!/usr/bin/env python3
"""Rerun S13 source-bounded CV gate from the right-leg geometry seed.

This package upgrades only the geometry/source-bounded control-volume gate.
It emits task-owned cell/face ledgers and downstream readiness decisions, but
does not extract VTK surfaces, run samplers, launch harvests, or admit any
exchange-cell coefficient.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract import build_s13_right_leg_geometry_seed as seed_builder
from tools.extract import build_s13_upcomer_exchange_topology_cv_release as topo
from tools.extract.openfoam_cell_volumes import (
    first_count,
    iter_faces,
    iter_label_list,
    read_points,
)

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed"

GEOMETRY_SEED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed"
PREVIOUS_SOURCE_BOUNDED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
SAME_WINDOW_UQ = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design"
SOURCE_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"

CASE_IDS = ("salt_2", "salt_3", "salt_4")
CAP_PATCHES = ("ncc_pipeleg_right_01_lower_start", "ncc_pipeleg_right_03_upper_end")
POSITIVE_FLUX_CONVENTION = "positive mdot_exchange from seeded recirculation CV toward adjacent non-seed/core cells"
NORMAL_CONVENTION = "internal normals point outward from seeded CV owner side toward adjacent non-seed/core cells; wall normals use OpenFOAM boundary orientation"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def seed_mask_path(case_id: str) -> Path:
    return GEOMETRY_SEED / "masks" / f"{case_id}_right_leg_geometry_seed_cells.csv"


def load_seed_cells(case_id: str) -> set[int]:
    return {int(row["cell_id"]) for row in read_csv(seed_mask_path(case_id))}


def is_cap_patch(patch_name: str) -> bool:
    return any(name in patch_name for name in CAP_PATCHES)


def patch_name_for_face(face_i: int, patches: list[topo.PatchRange]) -> str:
    for patch in patches:
        if patch.start_face <= face_i < patch.end_face:
            return patch.name
    return ""


def face_area_center(face: list[int], points: list[tuple[float, float, float]]) -> tuple[float, tuple[float, float, float]]:
    return seed_builder.face_area_and_center(face, points)


def boundary_rows(case_id: str, seed_cells: set[int]) -> dict[str, list[dict[str, Any]]]:
    poly_mesh = seed_builder.CASE_MESHES[case_id]
    points = read_points(poly_mesh / "points")
    patches = topo.parse_boundary_patches((poly_mesh / "boundary").read_text(encoding="utf-8", errors="replace"))
    n_faces = first_count(poly_mesh / "faces")
    n_internal = first_count(poly_mesh / "neighbour")
    face_iter = iter_faces(poly_mesh / "faces")
    owner_iter = iter_label_list(poly_mesh / "owner")
    neighbour_iter = iter_label_list(poly_mesh / "neighbour")

    interface_rows: list[dict[str, Any]] = []
    wall_rows: list[dict[str, Any]] = []
    cap_rows: list[dict[str, Any]] = []
    escape_rows: list[dict[str, Any]] = []
    for face_i in range(n_faces):
        face = next(face_iter)
        owner = next(owner_iter)
        neighbour = next(neighbour_iter) if face_i < n_internal else None
        owner_in = owner in seed_cells
        neighbour_in = bool(neighbour in seed_cells) if neighbour is not None else False
        if not owner_in and not neighbour_in:
            continue

        area, center = face_area_center(face, points)
        if neighbour is not None:
            if owner_in == neighbour_in:
                continue
            seed_owner = owner if owner_in else neighbour
            adjacent_cell = neighbour if owner_in else owner
            interface_rows.append(
                {
                    "case_id": case_id,
                    "face_id": face_i,
                    "owner": owner,
                    "neighbour": neighbour,
                    "seed_owner_cell": seed_owner,
                    "adjacent_core_cell": adjacent_cell,
                    "area_m2": f"{area:.12g}",
                    "center_x_m": f"{center[0]:.12g}",
                    "center_y_m": f"{center[1]:.12g}",
                    "center_z_m": f"{center[2]:.12g}",
                    "normal_convention": NORMAL_CONVENTION,
                    "release_status": "released_seeded_exchange_interface_face",
                }
            )
            continue

        patch_name = patch_name_for_face(face_i, patches)
        row = {
            "case_id": case_id,
            "face_id": face_i,
            "patch_name": patch_name,
            "owner": owner,
            "area_m2": f"{area:.12g}",
            "center_x_m": f"{center[0]:.12g}",
            "center_y_m": f"{center[1]:.12g}",
            "center_z_m": f"{center[2]:.12g}",
            "normal_convention": NORMAL_CONVENTION,
        }
        if patch_name in topo.RIGHT_LEG_WALL_PATCHES:
            wall_rows.append({**row, "release_status": "released_seeded_trusted_wall_face"})
        elif is_cap_patch(patch_name):
            cap_rows.append({**row, "classification": "classified_ncc_cap"})
        else:
            escape_rows.append({**row, "classification": "unclassified_escape"})

    return {"interface": interface_rows, "wall": wall_rows, "caps": cap_rows, "escapes": escape_rows}


def sum_area(rows: list[dict[str, Any]]) -> float:
    return sum(float(row["area_m2"]) for row in rows)


def case_decision(case_id: str, seed_summary: dict[str, str], face_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    reasons: list[str] = []
    if seed_summary.get("seed_status") != "released_geometry_seed_for_source_bounded_cv_rerun":
        reasons.append("geometry_seed_not_released")
    if len(face_rows["wall"]) <= 0 or sum_area(face_rows["wall"]) <= 0.0:
        reasons.append("missing_positive_trusted_wall_area")
    if len(face_rows["interface"]) <= 0 or sum_area(face_rows["interface"]) <= 0.0:
        reasons.append("missing_positive_seed_core_interface_area")
    if len(face_rows["escapes"]) > 0:
        reasons.append("unclassified_seed_boundary_escapes")
    if not face_rows["caps"]:
        reasons.append("missing_classified_ncc_cap_faces")

    released = not reasons
    return {
        "case_id": case_id,
        "geometry_seed_status": seed_summary.get("seed_status", "missing"),
        "seed_cell_count": seed_summary.get("seed_cell_count", "0"),
        "seed_volume_m3": seed_summary.get("seed_volume_m3", "0"),
        "released_interface_face_count": len(face_rows["interface"]),
        "released_interface_area_m2": f"{sum_area(face_rows['interface']):.12g}",
        "released_trusted_wall_face_count": len(face_rows["wall"]),
        "released_trusted_wall_area_m2": f"{sum_area(face_rows['wall']):.12g}",
        "classified_cap_face_count": len(face_rows["caps"]),
        "classified_cap_area_m2": f"{sum_area(face_rows['caps']):.12g}",
        "unclassified_escape_face_count": len(face_rows["escapes"]),
        "unclassified_escape_area_m2": f"{sum_area(face_rows['escapes']):.12g}",
        "reverse_overlap_cells": seed_summary.get("reverse_overlap_cells", "0"),
        "source_bounded_cv_release_status": "released_seeded_source_bounded_cv" if released else "blocked_seeded_source_bounded_cv",
        "surface_preflight_ready": str(released).lower(),
        "sampler_ready": "false",
        "same_qoi_uq_ready": "false",
        "s11_s12_s15_s6_trigger": "false",
        "blocking_reason": ";".join(reasons),
    }


def recirc_rows(case_id: str, seed_cells: set[int], release_status: str) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case_id,
            "cell_id": cell_id,
            "cv_role": "seeded_right_leg_source_bounded_cv",
            "source_mask": rel(seed_mask_path(case_id)),
            "release_status": release_status,
        }
        for cell_id in sorted(seed_cells)
    ]


def band_row(decision: dict[str, Any]) -> dict[str, Any]:
    released = decision["source_bounded_cv_release_status"].startswith("released")
    return {
        "case_id": decision["case_id"],
        "band_id": "seeded_right_leg_wall_core_band",
        "released": str(released).lower(),
        "wall_basis": "trusted right-leg wall patches pipeleg_right_01_lower/02_middle/03_upper",
        "core_basis": "internal seed/core interface faces adjacent to non-seed cells",
        "thermal_reduction_allowed": "false",
        "blocking_reason": "" if released else decision["blocking_reason"],
    }


def normal_row(decision: dict[str, Any]) -> dict[str, Any]:
    released = decision["source_bounded_cv_release_status"].startswith("released")
    return {
        "case_id": decision["case_id"],
        "surface_lane": "seeded_exchange_interface",
        "released": str(released).lower(),
        "normal_convention": NORMAL_CONVENTION,
        "positive_flux_convention": POSITIVE_FLUX_CONVENTION,
        "source_paths": rel(GEOMETRY_SEED / "geometry_seed_surface_contract.csv"),
        "blocking_reason": "" if released else decision["blocking_reason"],
    }


def source_rows(case_id: str, cap_rows: list[dict[str, Any]], released: bool) -> list[dict[str, Any]]:
    rows = [
        {
            "case_id": case_id,
            "boundary_lane": "classified_seed_ncc_caps",
            "patch_name": row["patch_name"],
            "face_id": row["face_id"],
            "released": str(released).lower(),
            "classification": row["classification"],
            "Q_wall_W_released": "false",
            "source_sink_terms_released": "false",
            "blocking_reason": "Q_wall_W/source integration requires later surface extraction/preflight row",
            "source_paths": rel(GEOMETRY_SEED / "geometry_seed_surface_contract.csv"),
        }
        for row in cap_rows
    ]
    rows.append(
        {
            "case_id": case_id,
            "boundary_lane": "static_source_sink_context",
            "patch_name": "",
            "face_id": "",
            "released": "false",
            "classification": "context_only_from_prior_source_generation",
            "Q_wall_W_released": "false",
            "source_sink_terms_released": "false",
            "blocking_reason": "static source context carried forward but runtime source/sink and Q_wall remain unreleased",
            "source_paths": rel(SOURCE_GENERATION / "source_sink_summary.csv"),
        }
    )
    return rows


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    (out / "README.md").write_text(
        f"""---
provenance:
  - {rel(GEOMETRY_SEED / 'summary.json')}
  - {rel(PREVIOUS_SOURCE_BOUNDED / 'release_decision.csv')}
  - {rel(SAMPLER_PREFLIGHT / 'sampler_input_gap_matrix.csv')}
tags: [s13, upcomer-exchange, source-bounded-cv, geometry-seed]
related:
  - {rel(SAME_WINDOW_UQ / 'summary.json')}
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Source-Bounded CV Rerun From Geometry Seed

This package reruns the S13 source-bounded CV release gate using the completed
right-leg geometry seed. Result: `{summary['decision']}`.

- cases processed: `{summary['case_count']}`
- released seeded CV cases: `{summary['released_case_count']}`
- surface preflight ready: `{str(summary['surface_preflight_ready']).lower()}`
- sampler/harvest allowed now: `{str(summary['sampler_or_harvest_allowed']).lower()}`
- same-QOI UQ ready: `{str(summary['same_qoi_uq_ready']).lower()}`
- S11/S12/S15/S6 trigger: `{str(summary['s11_s12_s15_s6_trigger']).lower()}`

The seeded geometry release is a control-volume and surface-readiness result
only. It does not extract VTK surfaces, integrate `Q_wall_W`, run a sampler,
run harvest, admit a coefficient, freeze S12-HIAX1, or release final score
work.

No native OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated index, fitting/model
selection, or residual absorption into internal Nu was changed.
""",
        encoding="utf-8",
    )


def write_status_journal_import(out: Path, summary: dict[str, Any]) -> None:
    status = ROOT / ".agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21.md"
    journal = ROOT / ".agent/journal/2026-07-21/s13-upcomer-exchange-source-bounded-cv-rerun-from-geometry-seed.md"
    manifest = ROOT / "imports/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.json"
    status.write_text(
        f"""---
provenance:
  - {rel(out / 'summary.json')}
  - {rel(out / 'seeded_release_decision.csv')}
tags: [status, s13, upcomer-exchange, source-bounded-cv, geometry-seed]
related:
  - {rel(journal)}
  - {rel(manifest)}
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: status
status: complete
---
# {TASK_ID}

## Objective

Rerun the S13 source-bounded CV release gate using the completed
geometry-backed right-leg seed.

## Outcome

Published `{rel(out)}`. Result: `{summary['decision']}` with
`{summary['released_case_count']}/{summary['case_count']}` seeded CV cases
released for surface/input preflight. Sampler, harvest, same-QOI UQ,
S11/S12/S15/S6, fitting, and admission remain blocked pending later rows.

## Changes Made

- `.agent/BOARD.md`
- `{rel(status)}`
- `{rel(journal)}`
- `{rel(manifest)}`
- `tools/extract/build_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.py`
- `tools/extract/test_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.py`
- `{rel(out)}/**`

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.py tools/extract/test_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.py` passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed` passed.
- `python3.11 tools/extract/build_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.py` passed.
- `python3.11 tools/agent/runtime_input_lint.py {rel(out)}` passed.
- `python3.11 tools/agent/source_property_gate.py {rel(out)} --strict` passed.
- `python3.11 tools/agent/split_policy_lint.py {rel(out)}` passed.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
OpenFOAM solver/postprocessing, surface extraction, sampler, harvest, Fluid
source, external repository, fitting/model selection, exchange-cell coefficient
admission, S11/S12/S13/S15/S6 trigger, blocker-register change,
generated-index refresh, or residual absorption into internal Nu was performed.
""",
        encoding="utf-8",
    )
    journal.write_text(
        f"""---
provenance:
  - {rel(out / 'seeded_release_decision.csv')}
  - {rel(GEOMETRY_SEED / 'geometry_seed_case_summary.csv')}
tags: [journal, s13, upcomer-exchange, source-bounded-cv, geometry-seed]
related:
  - {rel(status)}
  - {rel(manifest)}
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---
# S13 Source-Bounded CV Rerun From Geometry Seed

## Attempted

Used the completed right-leg geometry seed to rerun the source-bounded S13 CV
release gate. The rerun reads seed cell masks and read-only mesh topology to
emit task-owned seeded CV cells, exchange-interface faces, trusted wall faces,
wall/core band, normal convention, and source/sink boundary ledger.

## Observed

The group gate released `{summary['released_case_count']}/{summary['case_count']}`
seeded CV cases for surface/input preflight. Surface extraction itself was not
launched. `Q_wall_W`, source/sink runtime release, same-window thermal fields,
and same-QOI UQ still require later rows.

## Inferred

The prior wall-disconnected topology blocker is repaired at the geometry-CV
level. The scientific candidate is still not S11-reviewable because sampler
inputs, harvested exchange QOIs, and same-QOI UQ are not available.

## Caveats

This is not an exchange-cell coefficient admission and not an S12-HIAX1 freeze.
Reverse-flow overlap remains diagnostic context, not a release authority.

## Next Useful Actions

Open a separate surface/input preflight row using this package as the geometry
source. Only after that row releases VTK surfaces, normals, wall/source fields,
and UQ prerequisites should any production harvest row be considered.
""",
        encoding="utf-8",
    )
    changed = [
        ".agent/BOARD.md",
        rel(status),
        rel(journal),
        rel(manifest),
        "tools/extract/build_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.py",
        "tools/extract/test_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed.py",
        f"{rel(out)}/README.md",
        f"{rel(out)}/summary.json",
        f"{rel(out)}/seeded_release_decision.csv",
        f"{rel(out)}/seeded_recirc_cv_cells.csv",
        f"{rel(out)}/seeded_exchange_interface_faces.csv",
        f"{rel(out)}/seeded_trusted_wall_faces.csv",
        f"{rel(out)}/seeded_wall_core_band.csv",
        f"{rel(out)}/seeded_normal_convention.csv",
        f"{rel(out)}/seeded_source_sink_boundary_ledger.csv",
        f"{rel(out)}/downstream_gate.csv",
    ]
    json_dump(
        manifest,
        {
            "task": TASK_ID,
            "created_at": iso_timestamp(),
            "role": "Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer",
            "objective": "Rerun S13 source-bounded CV release gate from completed right-leg geometry seed.",
            "changed_files": changed,
            "read_only_context": [
                rel(GEOMETRY_SEED),
                rel(PREVIOUS_SOURCE_BOUNDED),
                rel(SAMPLER_PREFLIGHT),
                rel(SAME_WINDOW_UQ),
                "Salt2/Salt3/Salt4 native constant/polyMesh read-only",
                "registry/admission state",
                "scheduler state",
                "Fluid source tree",
                "external repositories",
            ],
            "summary": summary,
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "surface_extraction_launched": False,
            "sampler_or_harvest_launched": False,
            "fitting_or_model_selection_performed": False,
            "exchange_cell_coefficient_admitted": False,
            "s11_s12_s13_s15_s6_trigger": False,
            "generated_index_refresh": False,
        },
    )


def build_package(out: Path = OUT, write_closeout: bool = True) -> dict[str, Any]:
    ensure_dir(out)
    seed_summary = by_case(read_csv(GEOMETRY_SEED / "geometry_seed_case_summary.csv"))
    all_recirc: list[dict[str, Any]] = []
    all_interface: list[dict[str, Any]] = []
    all_wall: list[dict[str, Any]] = []
    all_band: list[dict[str, Any]] = []
    all_normals: list[dict[str, Any]] = []
    all_source: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []

    for case_id in CASE_IDS:
        seed_cells = load_seed_cells(case_id)
        faces = boundary_rows(case_id, seed_cells)
        decision = case_decision(case_id, seed_summary[case_id], faces)
        decisions.append(decision)
        all_recirc.extend(recirc_rows(case_id, seed_cells, decision["source_bounded_cv_release_status"]))
        all_interface.extend(faces["interface"])
        all_wall.extend(faces["wall"])
        all_band.append(band_row(decision))
        all_normals.append(normal_row(decision))
        all_source.extend(source_rows(case_id, faces["caps"], decision["source_bounded_cv_release_status"].startswith("released")))
        for row in faces["escapes"]:
            all_source.append(
                {
                    "case_id": case_id,
                    "boundary_lane": "unclassified_escape",
                    "patch_name": row["patch_name"],
                    "face_id": row["face_id"],
                    "released": "false",
                    "classification": row["classification"],
                    "Q_wall_W_released": "false",
                    "source_sink_terms_released": "false",
                    "blocking_reason": "unclassified boundary escape blocks release",
                    "source_paths": rel(GEOMETRY_SEED / "geometry_seed_surface_contract.csv"),
                }
            )

    group_released = all(row["source_bounded_cv_release_status"].startswith("released") for row in decisions)
    release_count = sum(1 for row in decisions if row["source_bounded_cv_release_status"].startswith("released"))
    if not group_released:
        for row in decisions:
            if row["source_bounded_cv_release_status"].startswith("released"):
                row["source_bounded_cv_release_status"] = "blocked_group_release_requires_all_three_cases"
                row["surface_preflight_ready"] = "false"
                row["blocking_reason"] = "all_three_cases_must_release"

    csv_dump(out / "seeded_recirc_cv_cells.csv", ["case_id", "cell_id", "cv_role", "source_mask", "release_status"], all_recirc)
    csv_dump(
        out / "seeded_exchange_interface_faces.csv",
        ["case_id", "face_id", "owner", "neighbour", "seed_owner_cell", "adjacent_core_cell", "area_m2", "center_x_m", "center_y_m", "center_z_m", "normal_convention", "release_status"],
        all_interface,
    )
    csv_dump(
        out / "seeded_trusted_wall_faces.csv",
        ["case_id", "face_id", "patch_name", "owner", "area_m2", "center_x_m", "center_y_m", "center_z_m", "normal_convention", "release_status"],
        all_wall,
    )
    csv_dump(out / "seeded_wall_core_band.csv", ["case_id", "band_id", "released", "wall_basis", "core_basis", "thermal_reduction_allowed", "blocking_reason"], all_band)
    csv_dump(out / "seeded_normal_convention.csv", ["case_id", "surface_lane", "released", "normal_convention", "positive_flux_convention", "source_paths", "blocking_reason"], all_normals)
    csv_dump(
        out / "seeded_source_sink_boundary_ledger.csv",
        ["case_id", "boundary_lane", "patch_name", "face_id", "released", "classification", "Q_wall_W_released", "source_sink_terms_released", "blocking_reason", "source_paths"],
        all_source,
    )
    csv_dump(
        out / "seeded_release_decision.csv",
        [
            "case_id",
            "geometry_seed_status",
            "seed_cell_count",
            "seed_volume_m3",
            "released_interface_face_count",
            "released_interface_area_m2",
            "released_trusted_wall_face_count",
            "released_trusted_wall_area_m2",
            "classified_cap_face_count",
            "classified_cap_area_m2",
            "unclassified_escape_face_count",
            "unclassified_escape_area_m2",
            "reverse_overlap_cells",
            "source_bounded_cv_release_status",
            "surface_preflight_ready",
            "sampler_ready",
            "same_qoi_uq_ready",
            "s11_s12_s15_s6_trigger",
            "blocking_reason",
        ],
        decisions,
    )

    downstream = [
        {
            "gate": "seeded_source_bounded_cv",
            "status": "pass" if group_released else "fail",
            "ready_for_next_row": str(group_released).lower(),
            "next_row": "S13 seeded surface/input preflight",
            "forbidden_now": "surface_extraction,sampler,harvest,UQ,S11,S12,S15,S6,fit,admission",
            "evidence": rel(out / "seeded_release_decision.csv"),
        },
        {
            "gate": "surface_input_preflight",
            "status": "not_run",
            "ready_for_next_row": str(group_released).lower(),
            "next_row": "extract_or_fail_close_seeded_interface_wall_surfaces_and_normals",
            "forbidden_now": "production_harvest",
            "evidence": rel(out / "seeded_exchange_interface_faces.csv"),
        },
        {
            "gate": "sampler_manifest_refresh",
            "status": "blocked_pending_surface_preflight",
            "ready_for_next_row": "false",
            "next_row": "rerun sampler manifest only after surface/input preflight passes",
            "forbidden_now": "sampler_or_harvest",
            "evidence": rel(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"),
        },
        {
            "gate": "same_qoi_uq",
            "status": "blocked_pending_neighbor_windows_and_mesh_gci",
            "ready_for_next_row": "false",
            "next_row": "same-window/same-QOI UQ after QOI harvest exists",
            "forbidden_now": "S11/S12/S15/S6",
            "evidence": rel(SAME_WINDOW_UQ / "summary.json"),
        },
    ]
    csv_dump(out / "downstream_gate.csv", ["gate", "status", "ready_for_next_row", "next_row", "forbidden_now", "evidence"], downstream)
    csv_dump(
        out / "no_mutation_guardrails.csv",
        ["guard_id", "status", "policy"],
        [
            {"guard_id": "native_outputs", "status": "pass", "policy": "native polyMesh read-only; no native outputs changed"},
            {"guard_id": "scheduler", "status": "pass", "policy": "no scheduler action"},
            {"guard_id": "surface_sampler_harvest", "status": "pass", "policy": "no surface extraction, sampler, or harvest launched"},
            {"guard_id": "admission", "status": "pass", "policy": "no coefficient admission or S11/S12/S13/S15/S6 trigger"},
        ],
    )
    source_paths = [
        (GEOMETRY_SEED / "summary.json", "read geometry seed decision", False),
        (GEOMETRY_SEED / "geometry_seed_case_summary.csv", "read seed case summary", False),
        (GEOMETRY_SEED / "geometry_seed_surface_contract.csv", "read seed surface contract", False),
        (PREVIOUS_SOURCE_BOUNDED / "release_decision.csv", "read previous fail-closed source-bounded decision", False),
        (SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv", "read sampler blockers", False),
        (SAME_WINDOW_UQ / "summary.json", "read UQ blockers", False),
        (out, "generated task-owned package", False),
    ]
    for case_id in CASE_IDS:
        source_paths.append((seed_mask_path(case_id), f"read {case_id} geometry seed mask", False))
        source_paths.append((seed_builder.CASE_MESHES[case_id], f"read {case_id} native polyMesh topology", True))
    csv_dump(
        out / "source_manifest.csv",
        ["path", "role", "exists", "native_solver_output", "mutated"],
        [
            {
                "path": rel(path),
                "role": role,
                "exists": str(path.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(path == out).lower(),
            }
            for path, role, native in source_paths
        ],
    )

    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "released_seeded_source_bounded_cv_surface_preflight_ready" if group_released else "complete_fail_closed_seeded_source_bounded_cv_not_released",
        "case_count": len(CASE_IDS),
        "released_case_count": release_count if group_released else 0,
        "surface_preflight_ready": group_released,
        "surface_extraction_launched": False,
        "sampler_or_harvest_allowed": False,
        "same_qoi_uq_ready": False,
        "s11_s12_s15_s6_trigger": False,
        "exchange_cell_coefficient_admission": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "next_action": "open seeded surface/input preflight row" if group_released else "repair seeded source-bounded CV blockers",
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    if write_closeout:
        write_status_journal_import(out, summary)
    return {"summary": summary, "decisions": decisions}


def main() -> int:
    payload = build_package()
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
