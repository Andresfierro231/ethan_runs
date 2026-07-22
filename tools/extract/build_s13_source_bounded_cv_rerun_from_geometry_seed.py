#!/usr/bin/env python3
"""Rerun the S13 source-bounded CV gate from the geometry seed package."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_source_bounded_cv_rerun_from_geometry_seed"

SEED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed"
SOURCE_BOUNDED_PRIOR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition"
ROI_AUDIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit"
TOPOLOGY_FORENSICS = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv"
GEOMETRY_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract"
SURFACE_DISPOSITION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_extraction"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
SOURCE_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
SAME_WINDOW_UQ = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design"

CASE_IDS = ("salt_2", "salt_3", "salt_4")

DECISION_FIELDS = [
    "case_id",
    "seed_status",
    "seed_cell_count",
    "trusted_wall_face_count",
    "trusted_wall_area_m2",
    "internal_seed_core_interface_face_count",
    "internal_seed_core_interface_area_m2",
    "classified_cap_face_count",
    "classified_cap_area_m2",
    "unclassified_escape_face_count",
    "source_bounded_cv_release_status",
    "surface_extraction_ready",
    "sampler_ready",
    "s12_hiax1_unlocked",
    "blocking_reason",
]
SURFACE_FIELDS = [
    "case_id",
    "surface_lane",
    "source_lane",
    "face_count",
    "area_m2",
    "normal_vector_convention",
    "release_status",
    "consumer",
    "blocking_reason",
]
BOUNDARY_FIELDS = [
    "case_id",
    "boundary_class",
    "patch_name",
    "face_count",
    "area_m2",
    "source_bounded_role",
    "release_status",
    "blocking_reason",
]
DOWNSTREAM_FIELDS = [
    "case_id",
    "downstream_lane",
    "status",
    "required_input",
    "available_input",
    "blocking_reason",
]
S12_FIELDS = ["gate", "status", "effect_on_s12", "evidence", "next_action"]
GUARD_FIELDS = ["guard_id", "status", "policy"]
SOURCE_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def parse_float(value: str) -> float:
    return float(value) if str(value).strip() else 0.0


def parse_int(value: str) -> int:
    return int(float(value)) if str(value).strip() else 0


def seed_case_releasable(row: dict[str, str]) -> tuple[bool, str]:
    reasons: list[str] = []
    if row.get("seed_status") != "released_geometry_seed_for_source_bounded_cv_rerun":
        reasons.append("geometry_seed_status_not_released")
    if parse_int(row.get("seed_cell_count", "0")) <= 0:
        reasons.append("empty_geometry_seed")
    if parse_int(row.get("trusted_wall_face_count", "0")) <= 0 or parse_float(row.get("trusted_wall_area_m2", "0")) <= 0.0:
        reasons.append("missing_positive_trusted_wall_faces_or_area")
    if parse_int(row.get("internal_seed_core_interface_face_count", "0")) <= 0 or parse_float(row.get("internal_seed_core_interface_area_m2", "0")) <= 0.0:
        reasons.append("missing_positive_internal_seed_core_interface")
    if parse_int(row.get("classified_cap_face_count", "0")) <= 0:
        reasons.append("missing_classified_cap_faces")
    if parse_int(row.get("unclassified_escape_face_count", "0")) != 0 or parse_float(row.get("unclassified_escape_area_m2", "0")) != 0.0:
        reasons.append("unclassified_boundary_escape_present")
    if not parse_bool(row.get("source_bounded_cv_rerun_ready", "false")):
        reasons.append("source_bounded_cv_rerun_not_ready")
    return not reasons, ";".join(reasons)


def build_decision_rows(seed_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    local = {row["case_id"]: seed_case_releasable(row) for row in seed_rows}
    group_release = all(ready for ready, _ in local.values()) and len(local) == len(CASE_IDS)
    for row in seed_rows:
        ready, reason = local[row["case_id"]]
        release_status = "released_seed_source_bounded_cv_geometry" if ready and group_release else "blocked_seed_source_bounded_cv_geometry"
        if ready and not group_release:
            reason = "all_three_cases_required_for_group_release"
        rows.append(
            {
                "case_id": row["case_id"],
                "seed_status": row["seed_status"],
                "seed_cell_count": row["seed_cell_count"],
                "trusted_wall_face_count": row["trusted_wall_face_count"],
                "trusted_wall_area_m2": row["trusted_wall_area_m2"],
                "internal_seed_core_interface_face_count": row["internal_seed_core_interface_face_count"],
                "internal_seed_core_interface_area_m2": row["internal_seed_core_interface_area_m2"],
                "classified_cap_face_count": row["classified_cap_face_count"],
                "classified_cap_area_m2": row["classified_cap_area_m2"],
                "unclassified_escape_face_count": row["unclassified_escape_face_count"],
                "source_bounded_cv_release_status": release_status,
                "surface_extraction_ready": str(ready and group_release).lower(),
                "sampler_ready": "false",
                "s12_hiax1_unlocked": "false",
                "blocking_reason": reason,
            }
        )
    return rows


def surface_contract_rows(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in decision_rows:
        released = row["source_bounded_cv_release_status"] == "released_seed_source_bounded_cv_geometry"
        common_normal = (
            "positive outward from geometry seed toward adjacent non-seed cell for internal interface; "
            "wall normals use OpenFOAM owner-side boundary orientation"
        )
        for lane, source_lane, face_key, area_key, consumer in (
            ("trusted_wall_faces", "trusted_right_leg_wall", "trusted_wall_face_count", "trusted_wall_area_m2", "wall/core band and future Q_wall_W integration"),
            ("exchange_interface_candidate", "internal_seed_core_interface", "internal_seed_core_interface_face_count", "internal_seed_core_interface_area_m2", "future exchange interface surface extraction"),
            ("classified_ncc_caps", "classified_ncc_cap", "classified_cap_face_count", "classified_cap_area_m2", "cap classification audit"),
        ):
            rows.append(
                {
                    "case_id": row["case_id"],
                    "surface_lane": lane,
                    "source_lane": source_lane,
                    "face_count": row[face_key],
                    "area_m2": row[area_key],
                    "normal_vector_convention": common_normal,
                    "release_status": "ready_for_surface_contract" if released else "blocked_geometry_cv_not_released",
                    "consumer": consumer,
                    "blocking_reason": row["blocking_reason"],
                }
            )
        rows.append(
            {
                "case_id": row["case_id"],
                "surface_lane": "surface_vtk_extraction",
                "source_lane": "downstream_surface",
                "face_count": "0",
                "area_m2": "0",
                "normal_vector_convention": common_normal,
                "release_status": "ready_for_separate_surface_extraction_row" if released else "blocked_geometry_cv_not_released",
                "consumer": "sampler manifest",
                "blocking_reason": "surface VTK extraction not launched in this row",
            }
        )
    return rows


def boundary_ledger_rows(patch_rows: list[dict[str, str]], group_released: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in patch_rows:
        classification = row["classification"]
        if classification == "trusted_right_leg_wall":
            role = "trusted_wall"
            release = "released_boundary_class" if group_released else "blocked_group_release"
            reason = ""
        elif classification == "classified_ncc_cap":
            role = "classified_cap"
            release = "released_context_class" if group_released else "blocked_group_release"
            reason = ""
        else:
            role = "unclassified_escape"
            release = "blocked_unclassified_escape"
            reason = "unclassified boundary class is not permitted"
        rows.append(
            {
                "case_id": row["case_id"],
                "boundary_class": classification,
                "patch_name": row["patch_name"],
                "face_count": row["face_count"],
                "area_m2": row["area_m2"],
                "source_bounded_role": role,
                "release_status": release,
                "blocking_reason": reason,
            }
        )
    return rows


def downstream_rows(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in decision_rows:
        released = row["source_bounded_cv_release_status"] == "released_seed_source_bounded_cv_geometry"
        for lane, status, required, available, blocker in (
            (
                "surface_extraction",
                "ready_for_separate_surface_extraction_row" if released else "blocked",
                "released seed source-bounded CV geometry with wall/interface/cap lanes",
                "seed wall/interface/cap surface contract" if released else "",
                "" if released else row["blocking_reason"],
            ),
            (
                "sampler_manifest_refresh",
                "blocked",
                "surface VTKs, normals, Q_wall_W/source lane, same-window thermal fields",
                "geometry-only seed CV; surface extraction not yet run",
                "requires separate surface/source/Q_wall/same-window rows",
            ),
            (
                "production_harvest",
                "blocked",
                "3/3 sampler-ready rows",
                "",
                "sampler manifest is not ready",
            ),
            (
                "same_qoi_uq",
                "blocked",
                "same-QOI mesh/time uncertainty for exact exchange QOIs",
                "",
                "same-window UQ remains blocked/missing",
            ),
            (
                "S11_S12_S15_S6_trigger",
                "blocked",
                "runtime-legal candidate after sampler harvest, source/property, split, and UQ gates",
                "",
                "geometry-only release is insufficient for candidate trigger",
            ),
        ):
            rows.append(
                {
                    "case_id": row["case_id"],
                    "downstream_lane": lane,
                    "status": status,
                    "required_input": required,
                    "available_input": available,
                    "blocking_reason": blocker,
                }
            )
    return rows


def s12_rows(output_dir: Path, group_released: bool) -> list[dict[str, Any]]:
    return [
        {
            "gate": "s13_seed_source_bounded_cv_geometry",
            "status": "pass" if group_released else "fail",
            "effect_on_s12": "permits surface/source preflight only" if group_released else "blocks S12-HIAX1 exchange-state QOI basis",
            "evidence": rel(output_dir / "seed_cv_release_decision.csv"),
            "next_action": "claim separate surface/source manifest refresh row" if group_released else "repair seed CV geometry before S12 work",
        },
        {
            "gate": "s13_sampler_manifest_refresh",
            "status": "blocked",
            "effect_on_s12": "still blocks S12-HIAX1 until exchange-state QOIs release",
            "evidence": rel(output_dir / "seed_cv_downstream_gate.csv"),
            "next_action": "publish surface VTKs, Q_wall_W/source release, same-window thermal fields, and same-QOI UQ before harvest",
        },
        {
            "gate": "s12_hiax1_implementation",
            "status": "blocked",
            "effect_on_s12": "no Fluid implementation unlock from geometry-only release",
            "evidence": rel(SOURCE_BOUNDED_PRIOR / "s12_unlock_gate.csv"),
            "next_action": "wait for harvested exchange-state QOIs and UQ",
        },
    ]


def source_manifest(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        (Path("tools/extract/build_s13_source_bounded_cv_rerun_from_geometry_seed.py"), "task-owned builder", False, True),
        (Path("tools/extract/test_s13_source_bounded_cv_rerun_from_geometry_seed.py"), "task-owned test", False, True),
        (SEED / "geometry_seed_case_summary.csv", "read seed release summary", False, False),
        (SEED / "geometry_seed_surface_contract.csv", "read seed surface lanes", False, False),
        (SEED / "geometry_seed_patch_classification.csv", "read seed boundary classes", False, False),
        (SEED / "downstream_release_gate.csv", "read seed downstream gate", False, False),
        (SOURCE_BOUNDED_PRIOR / "release_decision.csv", "read prior source-bounded CV failure", False, False),
        (ROI_AUDIT / "summary.json", "read ROI/patch alignment audit", False, False),
        (TOPOLOGY_FORENSICS / "alternate_cv_release_gate.csv", "read alternate-CV forensics", False, False),
        (GEOMETRY_CONTRACT / "interface_geometry_contract.csv", "read original geometry contract", False, False),
        (SURFACE_DISPOSITION / "summary.json", "read surface disposition state", False, False),
        (SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv", "read sampler gap matrix", False, False),
        (SOURCE_GENERATION / "source_sink_summary.csv", "read static source context", False, False),
        (SAME_WINDOW_UQ / "qoi_release_decision.csv", "read UQ design state", False, False),
        (output_dir, "generated task-owned package", False, True),
    ]
    rows: list[dict[str, Any]] = []
    for path, role, native, mutated in paths:
        full = path if path.is_absolute() else ROOT / path
        rows.append(
            {
                "path": rel(full),
                "role": role,
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(mutated).lower(),
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
tags: [s13, upcomer-exchange, source-bounded-cv, geometry-seed]
related:
  - {rel(SEED)}
  - {rel(SOURCE_BOUNDED_PRIOR)}
---
# S13 Source-Bounded CV Rerun From Geometry Seed

This package reruns the S13 source-bounded CV release gate using the completed
geometry-backed right-leg/upcomer seed. It only decides whether the geometry is
ready for a later surface/source preflight row.

## Decision

- cases processed: `{summary["case_count"]}`
- geometry CV rows released: `{summary["released_seed_cv_rows"]}`
- surface extraction ready rows: `{summary["surface_extraction_ready_rows"]}`
- sampler-ready rows: `{summary["sampler_ready_rows"]}`
- S12-HIAX1 unlocked: `{str(summary["s12_hiax1_unlocked"]).lower()}`

The geometry seed releases all three source-bounded CV geometry rows, but this
row does not generate VTK surfaces, integrate `Q_wall_W`, run samplers, harvest
exchange QOIs, perform UQ, admit a coefficient, or trigger S11/S12/S15/S6.

## Outputs

- `seed_cv_release_decision.csv`
- `seed_cv_surface_contract.csv`
- `seed_cv_boundary_ledger.csv`
- `seed_cv_downstream_gate.csv`
- `s12_unlock_impact.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
surface extraction, sampler/harvest, Fluid/external source, fitting/model
selection, exchange-cell coefficient admission, S11/S12/S13/S15/S6 trigger,
blocker register, generated index, or residual absorption into internal `Nu`
was changed.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    ensure_dir(output_dir)
    seed_rows = read_csv(SEED / "geometry_seed_case_summary.csv")
    patch_rows = read_csv(SEED / "geometry_seed_patch_classification.csv")
    decision_rows = build_decision_rows(seed_rows)
    group_released = len(decision_rows) == len(CASE_IDS) and all(
        row["source_bounded_cv_release_status"] == "released_seed_source_bounded_cv_geometry"
        for row in decision_rows
    )
    surface_rows = surface_contract_rows(decision_rows)
    boundary_rows = boundary_ledger_rows(patch_rows, group_released)
    down_rows = downstream_rows(decision_rows)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete_geometry_cv_released" if group_released else "complete_fail_closed_seed_cv_not_released",
        "case_count": len(decision_rows),
        "released_seed_cv_rows": sum(1 for row in decision_rows if row["source_bounded_cv_release_status"] == "released_seed_source_bounded_cv_geometry"),
        "surface_extraction_ready_rows": sum(1 for row in decision_rows if row["surface_extraction_ready"] == "true"),
        "sampler_ready_rows": 0,
        "s12_hiax1_unlocked": False,
        "surface_extraction_launched": False,
        "sampler_or_harvest_launched": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "exchange_cell_coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "residual_absorbed_into_internal_Nu": False,
        "next_action": "claim surface/source manifest refresh row" if group_released else "repair geometry CV before surface work",
    }
    csv_dump(output_dir / "seed_cv_release_decision.csv", DECISION_FIELDS, decision_rows)
    csv_dump(output_dir / "seed_cv_surface_contract.csv", SURFACE_FIELDS, surface_rows)
    csv_dump(output_dir / "seed_cv_boundary_ledger.csv", BOUNDARY_FIELDS, boundary_rows)
    csv_dump(output_dir / "seed_cv_downstream_gate.csv", DOWNSTREAM_FIELDS, down_rows)
    csv_dump(output_dir / "s12_unlock_impact.csv", S12_FIELDS, s12_rows(output_dir, group_released))
    csv_dump(
        output_dir / "no_mutation_guardrails.csv",
        GUARD_FIELDS,
        [
            {"guard_id": "native_outputs", "status": "pass", "policy": "read existing work-product CSVs only"},
            {"guard_id": "surface_sampler_harvest", "status": "pass", "policy": "no surface extraction, sampler, or harvest launched"},
            {"guard_id": "admission", "status": "pass", "policy": "no coefficient admission or S11/S12/S13/S15/S6 trigger"},
            {"guard_id": "residual_internal_Nu", "status": "pass", "policy": "no residual absorbed into internal Nu"},
        ],
    )
    csv_dump(output_dir / "source_manifest.csv", SOURCE_FIELDS, source_manifest(output_dir))
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return {"summary": summary, "decision_rows": decision_rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(args.output_dir)
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
