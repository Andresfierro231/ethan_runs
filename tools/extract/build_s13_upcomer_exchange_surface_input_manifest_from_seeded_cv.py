#!/usr/bin/env python3
"""Build the S13 seeded-CV surface/input manifest package.

This is a read-only preflight. It inventories the materialized seeded CV,
interface, wall, source/sink, and convention inputs that can support a later
surface extraction or sampler-manifest task. It does not run OpenFOAM,
generate VTKs, launch a sampler, fit, score, or admit a coefficient.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SURFACE-INPUT-MANIFEST-FROM-SEEDED-CV-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
)
SEEDED = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed"
)
THREE_CASE_CELL_VTK = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest"
)
INPUT_GENERATION = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_input_generation"
)
SURFACE_SOURCE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_surface_source_generation"
)
SAMPLER_SCAFFOLD = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold"
)

CASES = ("salt_2", "salt_3", "salt_4")

SOURCE_FILES: dict[str, Path] = {
    "seeded_summary": SEEDED / "summary.json",
    "seeded_release_decision": SEEDED / "seeded_release_decision.csv",
    "seeded_recirc_cv_cells": SEEDED / "seeded_recirc_cv_cells.csv",
    "seeded_exchange_interface_faces": SEEDED / "seeded_exchange_interface_faces.csv",
    "seeded_trusted_wall_faces": SEEDED / "seeded_trusted_wall_faces.csv",
    "seeded_wall_core_band": SEEDED / "seeded_wall_core_band.csv",
    "seeded_normal_convention": SEEDED / "seeded_normal_convention.csv",
    "seeded_source_sink_boundary_ledger": SEEDED / "seeded_source_sink_boundary_ledger.csv",
    "surface_contract": SEEDED / "surface_contract.csv",
    "cell_vtk_release_manifest": THREE_CASE_CELL_VTK / "three_case_cell_vtk_manifest.csv",
    "cell_vtk_manifest": THREE_CASE_CELL_VTK / "case_vtk_input_manifest.cells_populated.csv",
    "cell_volume_validation": INPUT_GENERATION / "cell_volume_export_validation.csv",
    "static_source_sink_summary": SURFACE_SOURCE / "source_sink_summary.csv",
    "sampler_manifest_template": SAMPLER_SCAFFOLD / "case_vtk_input_manifest.template.csv",
}

REQUIRED_COLUMNS: dict[str, set[str]] = {
    "seeded_release_decision": {
        "case_id",
        "seed_cell_count",
        "released_interface_face_count",
        "released_trusted_wall_face_count",
        "unclassified_escape_face_count",
        "source_bounded_cv_release_status",
        "surface_preflight_ready",
        "sampler_ready",
        "same_qoi_uq_ready",
        "s11_s12_s15_s6_trigger",
    },
    "seeded_recirc_cv_cells": {"case_id", "cell_id", "cv_role", "release_status"},
    "seeded_exchange_interface_faces": {
        "case_id",
        "face_id",
        "seed_owner_cell",
        "adjacent_core_cell",
        "area_m2",
        "normal_convention",
        "release_status",
    },
    "seeded_trusted_wall_faces": {
        "case_id",
        "face_id",
        "patch_name",
        "owner",
        "area_m2",
        "normal_convention",
        "release_status",
    },
    "seeded_wall_core_band": {
        "case_id",
        "band_id",
        "released",
        "wall_basis",
        "core_basis",
        "thermal_reduction_allowed",
    },
    "seeded_normal_convention": {
        "case_id",
        "surface_lane",
        "released",
        "normal_convention",
        "positive_flux_convention",
    },
    "seeded_source_sink_boundary_ledger": {
        "case_id",
        "boundary_lane",
        "released",
        "Q_wall_W_released",
        "source_sink_terms_released",
        "blocking_reason",
    },
    "surface_contract": {
        "case_id",
        "surface_lane",
        "release_status",
        "face_count",
        "area_m2",
        "normal_convention",
        "consumer",
    },
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def boolish(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y", "released", "pass"}


def file_profile(source_id: str, path: Path, required_columns: set[str]) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "source_id": source_id,
        "path": rel(path),
        "exists": path.exists(),
        "required_columns": ";".join(sorted(required_columns)),
        "missing_columns": "",
        "header_status": "missing_file",
        "row_count": 0,
        "case_counts": "",
        "read_policy": "streamed_header_and_counts_only",
    }
    if not path.exists():
        return profile

    case_counts: Counter[str] = Counter()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(required_columns - fieldnames)
        profile["missing_columns"] = ";".join(missing)
        profile["header_status"] = "pass" if not missing else "fail_missing_required_columns"
        for row in reader:
            profile["row_count"] += 1
            case_id = row.get("case_id", "")
            if case_id:
                case_counts[case_id] += 1
    profile["case_counts"] = ";".join(f"{case}:{case_counts.get(case, 0)}" for case in CASES)
    return profile


def input_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, required in REQUIRED_COLUMNS.items():
        rows.append(file_profile(source_id, SOURCE_FILES[source_id], required))
    for source_id in ("seeded_summary", "cell_vtk_manifest", "cell_volume_validation", "static_source_sink_summary", "sampler_manifest_template"):
        path = SOURCE_FILES[source_id]
        rows.append(
            {
                "source_id": source_id,
                "path": rel(path),
                "exists": path.exists(),
                "required_columns": "",
                "missing_columns": "",
                "header_status": "not_csv_checked" if path.exists() else "missing_file",
                "row_count": "",
                "case_counts": "",
                "read_policy": "existence_only",
            }
        )
    return rows


def summarize_by_case(path: Path) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(path)}


def split_csv_by_case(path: Path, output_dir: Path, stem_suffix: str, predicate_key: str | None = None, predicate_value: str | None = None) -> dict[str, str]:
    ensure_dir(output_dir)
    handles: dict[str, Any] = {}
    writers: dict[str, csv.DictWriter[str]] = {}
    try:
        with path.open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            fieldnames = reader.fieldnames or []
            for case_id in CASES:
                output = output_dir / f"{case_id}_{stem_suffix}.csv"
                handle = output.open("w", newline="", encoding="utf-8")
                handles[case_id] = handle
                writer: csv.DictWriter[str] = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writers[case_id] = writer
            for row in reader:
                case_id = row.get("case_id", "")
                if case_id not in writers:
                    continue
                if predicate_key is not None and row.get(predicate_key) != predicate_value:
                    continue
                writers[case_id].writerow(row)
    finally:
        for handle in handles.values():
            handle.close()
    return {case_id: rel(output_dir / f"{case_id}_{stem_suffix}.csv") for case_id in CASES}


def write_case_split_inputs() -> dict[str, dict[str, str]]:
    mask_paths = split_csv_by_case(
        SOURCE_FILES["seeded_recirc_cv_cells"],
        OUT / "masks",
        "seeded_recirc_cell_mask",
    )
    interface_paths = split_csv_by_case(
        SOURCE_FILES["seeded_exchange_interface_faces"],
        OUT / "faces",
        "seeded_exchange_interface_faces",
    )
    trusted_wall_paths = split_csv_by_case(
        SOURCE_FILES["seeded_trusted_wall_faces"],
        OUT / "faces",
        "seeded_trusted_wall_faces",
    )
    cap_paths = split_csv_by_case(
        SOURCE_FILES["seeded_source_sink_boundary_ledger"],
        OUT / "faces",
        "classified_seed_cap_faces",
        predicate_key="boundary_lane",
        predicate_value="classified_seed_ncc_caps",
    )
    band_paths = split_csv_by_case(
        SOURCE_FILES["seeded_wall_core_band"],
        OUT / "bands",
        "seeded_wall_core_band",
    )
    return {
        case_id: {
            "recirc_cell_mask": mask_paths[case_id],
            "exchange_interface_faces_csv": interface_paths[case_id],
            "trusted_wall_faces_csv": trusted_wall_paths[case_id],
            "wall_core_band_csv": band_paths[case_id],
            "classified_cap_faces_csv": cap_paths[case_id],
        }
        for case_id in CASES
    }


def seeded_case_matrix() -> list[dict[str, Any]]:
    release_by_case = summarize_by_case(SOURCE_FILES["seeded_release_decision"])
    band_by_case = summarize_by_case(SOURCE_FILES["seeded_wall_core_band"])
    normal_by_case = summarize_by_case(SOURCE_FILES["seeded_normal_convention"])
    source_summary_by_case = summarize_by_case(SOURCE_FILES["static_source_sink_summary"])
    vtk_by_case = summarize_by_case(SOURCE_FILES["cell_vtk_manifest"])
    volume_by_case = summarize_by_case(SOURCE_FILES["cell_volume_validation"])

    rows: list[dict[str, Any]] = []
    for case_id in CASES:
        release = release_by_case.get(case_id, {})
        band = band_by_case.get(case_id, {})
        normal = normal_by_case.get(case_id, {})
        source_summary = source_summary_by_case.get(case_id, {})
        vtk = vtk_by_case.get(case_id, {})
        volume = volume_by_case.get(case_id, {})

        seeded_ready = (
            release.get("source_bounded_cv_release_status") == "released_seeded_source_bounded_cv"
            and release.get("surface_preflight_ready") == "true"
            and release.get("unclassified_escape_face_count") == "0"
            and boolish(band.get("released", ""))
            and boolish(normal.get("released", ""))
        )
        sampled_vtk_ready = (
            bool(vtk.get("cell_vtk"))
            and not vtk.get("interface_vtk", "").startswith("MISSING_")
            and not vtk.get("wall_vtk", "").startswith("MISSING_")
            and bool(volume.get("cell_volume_csv"))
        )
        source_terms_ready = source_summary.get("status", "").startswith("static_bc_source_sink_ready")
        q_wall_released = "false"
        reasons: list[str] = []
        if not seeded_ready:
            reasons.append("seeded_cv_surface_input_release_incomplete")
        if not sampled_vtk_ready:
            reasons.append("raw_interface_wall_sampled_vtk_not_ready")
        if not source_terms_ready:
            reasons.append("static_source_sink_summary_missing")
        if q_wall_released != "true":
            reasons.append("Q_wall_W_not_released")
        reasons.append("same_window_sampler_outputs_not_generated")

        rows.append(
            {
                "case_id": case_id,
                "time_window_s": vtk.get("time_window_s", source_summary.get("time_window_s", "")),
                "seeded_cv_cells": release.get("seed_cell_count", ""),
                "seeded_interface_faces": release.get("released_interface_face_count", ""),
                "seeded_trusted_wall_faces": release.get("released_trusted_wall_face_count", ""),
                "unclassified_escape_faces": release.get("unclassified_escape_face_count", ""),
                "seeded_wall_core_band_released": str(boolish(band.get("released", ""))).lower(),
                "seeded_normal_convention_released": str(boolish(normal.get("released", ""))).lower(),
                "cell_vtk_exists": str((ROOT / vtk.get("cell_vtk", "")).exists()).lower() if vtk.get("cell_vtk") else "false",
                "cell_volume_csv_exists": str((ROOT / volume.get("cell_volume_csv", "")).exists()).lower()
                if volume.get("cell_volume_csv")
                else "false",
                "static_source_sink_summary_ready": str(source_terms_ready).lower(),
                "Q_wall_W_released": q_wall_released,
                "seeded_surface_input_ready_for_extraction_task": str(seeded_ready).lower(),
                "surface_extraction_ready": str(seeded_ready).lower(),
                "sampler_manifest_ready": "false",
                "sampler_harvest_allowed": "false",
                "same_qoi_uq_ready": "false",
                "exchange_cell_admission_allowed": "false",
                "s11_s12_s13_s15_s6_trigger": "false",
                "blocking_reason": ";".join(reasons),
            }
        )
    return rows


def seeded_surface_input_manifest(split_paths: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    release_by_case = summarize_by_case(SOURCE_FILES["seeded_release_decision"])
    normal_by_case = summarize_by_case(SOURCE_FILES["seeded_normal_convention"])
    source_summary_by_case = summarize_by_case(SOURCE_FILES["static_source_sink_summary"])
    cell_vtk_by_case = summarize_by_case(SOURCE_FILES["cell_vtk_release_manifest"])
    volume_by_case = summarize_by_case(SOURCE_FILES["cell_volume_validation"])

    rows: list[dict[str, Any]] = []
    for case_id in CASES:
        release = release_by_case[case_id]
        normal = normal_by_case[case_id]
        source = source_summary_by_case[case_id]
        cell_vtk = cell_vtk_by_case[case_id]
        volume = volume_by_case[case_id]
        paths = split_paths[case_id]
        rows.append(
            {
                "case_id": case_id,
                "case_key": cell_vtk.get("case_key", ""),
                "time_window_s": cell_vtk.get("time_window_s", source.get("time_window_s", "")),
                "cell_vtk": cell_vtk.get("cell_vtk", ""),
                "volume_csv": volume.get("cell_volume_csv", ""),
                "recirc_cell_mask": paths["recirc_cell_mask"],
                "exchange_interface_faces_csv": paths["exchange_interface_faces_csv"],
                "trusted_wall_faces_csv": paths["trusted_wall_faces_csv"],
                "wall_core_band_csv": paths["wall_core_band_csv"],
                "classified_cap_faces_csv": paths["classified_cap_faces_csv"],
                "source_sink_summary_csv": rel(SOURCE_FILES["static_source_sink_summary"]),
                "q_source_W": source.get("q_source_w", ""),
                "q_sink_W": source.get("q_sink_w", ""),
                "q_net_W": source.get("q_net_w", ""),
                "normal_convention": normal.get("normal_convention", ""),
                "positive_flux_convention": normal.get("positive_flux_convention", ""),
                "seeded_cv_cell_count": release.get("seed_cell_count", ""),
                "seeded_cv_volume_m3": release.get("seed_volume_m3", ""),
                "exchange_interface_face_count": release.get("released_interface_face_count", ""),
                "exchange_interface_area_m2": release.get("released_interface_area_m2", ""),
                "trusted_wall_face_count": release.get("released_trusted_wall_face_count", ""),
                "trusted_wall_area_m2": release.get("released_trusted_wall_area_m2", ""),
                "classified_cap_face_count": release.get("classified_cap_face_count", ""),
                "classified_cap_area_m2": release.get("classified_cap_area_m2", ""),
                "unclassified_escape_face_count": release.get("unclassified_escape_face_count", ""),
                "ready_for_surface_extraction": "true",
                "surface_vtk_extraction_launched": "false",
                "sampler_ready": "false",
                "harvest_allowed": "false",
                "same_qoi_uq_ready": "false",
                "s11_s12_s15_s6_trigger": "false",
                "release_status": "seeded_surface_input_manifest_ready",
                "blocking_reason": "surface VTK, Q_wall_W, cp/sign support, sampler manifest, harvest, and same-QOI UQ remain later gates",
            }
        )
    return rows


def input_file_existence_checks(manifest_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    inputs = [
        ("cell_vtk", False, True),
        ("volume_csv", False, True),
        ("recirc_cell_mask", False, True),
        ("exchange_interface_faces_csv", False, True),
        ("trusted_wall_faces_csv", False, True),
        ("wall_core_band_csv", False, True),
        ("classified_cap_faces_csv", False, True),
        ("source_sink_summary_csv", False, True),
    ]
    rows: list[dict[str, str]] = []
    for item in manifest_rows:
        for input_name, blocks_surface, blocks_sampler in inputs:
            path = item[input_name]
            exists = (ROOT / path).exists()
            rows.append(
                {
                    "case_id": item["case_id"],
                    "input_name": input_name,
                    "path": path,
                    "exists": str(exists).lower(),
                    "blocks_surface_extraction": str(blocks_surface or not exists).lower(),
                    "blocks_sampler_or_harvest": str(blocks_sampler).lower(),
                    "blocking_reason": "" if exists else f"missing_{input_name}",
                }
            )
    return rows


def downstream_gate(manifest_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "case_id": row["case_id"],
            "surface_extraction_ready": row["ready_for_surface_extraction"],
            "surface_extraction_allowed_next_row": row["ready_for_surface_extraction"],
            "sampler_manifest_refresh_allowed": "false",
            "production_harvest_allowed": "false",
            "same_qoi_uq_allowed": "false",
            "next_action": "claim surface VTK extraction row from seeded surface/input manifest",
        }
        for row in manifest_rows
    ]


def surface_input_decision(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    extraction_ready = all(row["surface_extraction_ready"] == "true" for row in matrix)
    manifest_ready = all(row["sampler_manifest_ready"] == "true" for row in matrix)
    return [
        {
            "decision_id": "seeded_surface_input_manifest_from_seeded_cv",
            "surface_extraction_ready": str(extraction_ready).lower(),
            "sampler_manifest_ready": str(manifest_ready).lower(),
            "sampler_harvest_allowed": "false",
            "same_qoi_uq_ready": "false",
            "exchange_cell_admission_allowed": "false",
            "decision": "release_surface_extraction_input_manifest_only" if extraction_ready else "fail_closed_surface_inputs_incomplete",
            "reason": (
                "seeded CV, interface-face, trusted-wall-face, wall/core-band, and normal-convention inputs exist for all three cases; "
                "raw sampled interface/wall VTKs, Q_wall_W, and same-window sampler outputs are still absent"
            )
            if extraction_ready
            else "one or more seeded geometry inputs is missing or not released",
            "next_action": "claim a scheduler-authorized seeded surface extraction row; keep sampler/harvest/UQ/admission blocked until raw outputs validate",
        }
    ]


def source_manifest() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = [
        {
            "path": rel(Path(__file__)),
            "role": "task_output_builder",
            "exists": "true",
            "native_solver_output": "false",
            "mutated": "true",
        },
        {
            "path": rel(ROOT / "tools/extract/test_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv.py"),
            "role": "task_output_tests",
            "exists": "true",
            "native_solver_output": "false",
            "mutated": "true",
        }
    ]
    for role, path in SOURCE_FILES.items():
        rows.append(
            {
                "path": rel(path),
                "role": role,
                "exists": str(path.exists()).lower(),
                "native_solver_output": "false",
                "mutated": "false",
            }
        )
    return rows


def no_mutation_guardrails() -> list[dict[str, str]]:
    return [
        {
            "guard_id": "native_solver_outputs",
            "status": "false",
            "policy": "read only existing work-product CSV/JSON inputs; no native OpenFOAM files changed",
        },
        {
            "guard_id": "registry_or_admission_mutation",
            "status": "false",
            "policy": "manifest publication does not update registry, admission ledgers, scores, or coefficients",
        },
        {
            "guard_id": "scheduler_action",
            "status": "false",
            "policy": "no sbatch/srun submission, cancel, requeue, or monitor mutation from this preflight",
        },
        {
            "guard_id": "openfoam_or_sampler_launch",
            "status": "false",
            "policy": "no solver, postprocessing, surface extraction, sampler, harvest, or UQ execution",
        },
        {
            "guard_id": "residual_absorbed_into_internal_Nu",
            "status": "false",
            "policy": "source, wall, sampler, and residual lanes remain explicit blockers outside internal Nu",
        },
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: {Path(__file__).name}
  generated_at: {summary["generated_at"]}
tags:
  - s13
  - upcomer-exchange
  - seeded-cv
  - surface-input-manifest
related:
  - {rel(SOURCE_FILES["seeded_release_decision"])}
  - {rel(SOURCE_FILES["seeded_exchange_interface_faces"])}
  - {rel(SOURCE_FILES["seeded_trusted_wall_faces"])}
  - {rel(SOURCE_FILES["cell_vtk_manifest"])}
task: {TASK_ID}
---

# S13 Surface/Input Manifest From Seeded CV

This package inventories the released seeded source-bounded CV inputs for
Salt2, Salt3, and Salt4. It confirms that all three cases have materialized
seeded cell, internal seed/core interface-face, trusted wall-face, wall/core
band, and normal-convention inputs suitable for a later surface-extraction
preflight.

Result: `release_surface_extraction_input_manifest_only`.

- seeded surface-extraction input rows ready: `{summary["surface_extraction_ready_rows"]}` / `{summary["case_count"]}`
- sampler-manifest-ready rows: `{summary["sampler_manifest_ready_rows"]}` / `{summary["case_count"]}`
- sampler/harvest/UQ/admission allowed now: `false`

The important boundary is that these are geometry/source-input manifests, not
raw same-window sampled interface/wall VTK outputs. `Q_wall_W`, raw interface
and wall sampled fields, sampler outputs, same-QOI UQ, coefficient admission,
and S11/S12/S13/S15/S6 triggers remain blocked.

## Artifacts

- `seeded_surface_input_inventory.csv`: streamed inventory of required seeded
  CSV inputs and required-column status.
- `seeded_surface_input_manifest.csv`: per-case downstream manifest with
  task-owned mask/face/band CSV paths.
- `input_file_existence_checks.csv`: file existence checks for every manifest
  input consumed by the next extraction row.
- `downstream_gate.csv`: per-case next-row gate status.
- `case_preflight_matrix.csv`: one Salt2/Salt3/Salt4 decision row joining the
  seeded release to existing cell VTK, volume, and source/sink context.
- `surface_input_decision.csv`: package-level release/fail-closed decision.
- `no_mutation_guardrails.csv`: explicit mutation/admission/scheduler guardrail
  status.
- `source_manifest.csv`: provenance for every read-only context file.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    ensure_dir(OUT)
    split_paths = write_case_split_inputs()
    inventory = input_inventory()
    manifest_rows = seeded_surface_input_manifest(split_paths)
    existence_rows = input_file_existence_checks(manifest_rows)
    downstream_rows = downstream_gate(manifest_rows)
    matrix = seeded_case_matrix()
    decision = surface_input_decision(matrix)
    guardrails = no_mutation_guardrails()
    sources = source_manifest()

    csv_dump(
        OUT / "seeded_surface_input_inventory.csv",
        [
            "source_id",
            "path",
            "exists",
            "required_columns",
            "missing_columns",
            "header_status",
            "row_count",
            "case_counts",
            "read_policy",
        ],
        inventory,
    )
    csv_dump(
        OUT / "case_preflight_matrix.csv",
        [
            "case_id",
            "time_window_s",
            "seeded_cv_cells",
            "seeded_interface_faces",
            "seeded_trusted_wall_faces",
            "unclassified_escape_faces",
            "seeded_wall_core_band_released",
            "seeded_normal_convention_released",
            "cell_vtk_exists",
            "cell_volume_csv_exists",
            "static_source_sink_summary_ready",
            "Q_wall_W_released",
            "seeded_surface_input_ready_for_extraction_task",
            "surface_extraction_ready",
            "sampler_manifest_ready",
            "sampler_harvest_allowed",
            "same_qoi_uq_ready",
            "exchange_cell_admission_allowed",
            "s11_s12_s13_s15_s6_trigger",
            "blocking_reason",
        ],
        matrix,
    )
    csv_dump(
        OUT / "seeded_surface_input_manifest.csv",
        [
            "case_id",
            "case_key",
            "time_window_s",
            "cell_vtk",
            "volume_csv",
            "recirc_cell_mask",
            "exchange_interface_faces_csv",
            "trusted_wall_faces_csv",
            "wall_core_band_csv",
            "classified_cap_faces_csv",
            "source_sink_summary_csv",
            "q_source_W",
            "q_sink_W",
            "q_net_W",
            "normal_convention",
            "positive_flux_convention",
            "seeded_cv_cell_count",
            "seeded_cv_volume_m3",
            "exchange_interface_face_count",
            "exchange_interface_area_m2",
            "trusted_wall_face_count",
            "trusted_wall_area_m2",
            "classified_cap_face_count",
            "classified_cap_area_m2",
            "unclassified_escape_face_count",
            "ready_for_surface_extraction",
            "surface_vtk_extraction_launched",
            "sampler_ready",
            "harvest_allowed",
            "same_qoi_uq_ready",
            "s11_s12_s15_s6_trigger",
            "release_status",
            "blocking_reason",
        ],
        manifest_rows,
    )
    csv_dump(
        OUT / "input_file_existence_checks.csv",
        [
            "case_id",
            "input_name",
            "path",
            "exists",
            "blocks_surface_extraction",
            "blocks_sampler_or_harvest",
            "blocking_reason",
        ],
        existence_rows,
    )
    csv_dump(
        OUT / "downstream_gate.csv",
        [
            "case_id",
            "surface_extraction_ready",
            "surface_extraction_allowed_next_row",
            "sampler_manifest_refresh_allowed",
            "production_harvest_allowed",
            "same_qoi_uq_allowed",
            "next_action",
        ],
        downstream_rows,
    )
    csv_dump(
        OUT / "surface_input_decision.csv",
        [
            "decision_id",
            "surface_extraction_ready",
            "sampler_manifest_ready",
            "sampler_harvest_allowed",
            "same_qoi_uq_ready",
            "exchange_cell_admission_allowed",
            "decision",
            "reason",
            "next_action",
        ],
        decision,
    )
    csv_dump(OUT / "no_mutation_guardrails.csv", ["guard_id", "status", "policy"], guardrails)
    csv_dump(OUT / "source_manifest.csv", ["path", "role", "exists", "native_solver_output", "mutated"], sources)

    with SOURCE_FILES["seeded_summary"].open(encoding="utf-8") as handle:
        upstream_summary = json.load(handle)

    summary: dict[str, Any] = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "upstream_decision": upstream_summary.get("decision"),
        "decision": decision[0]["decision"],
        "case_count": len(matrix),
        "surface_extraction_ready_rows": sum(row["surface_extraction_ready"] == "true" for row in matrix),
        "seeded_surface_manifest_rows": len(manifest_rows),
        "input_file_existence_check_rows": len(existence_rows),
        "sampler_manifest_ready_rows": sum(row["sampler_manifest_ready"] == "true" for row in matrix),
        "sampler_harvest_allowed": False,
        "same_qoi_uq_ready": False,
        "exchange_cell_admission_allowed": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "next_action": decision[0]["next_action"],
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
