#!/usr/bin/env python3
"""Build the S13 throughflow endpoint-mask derivation package.

This pass addresses the blocker left by the S13 throughflow enthalpy preflight:
open-CV throughflow endpoint face masks. It audits the trusted seeded cap-face
artifacts and writes candidate start/end masks only as unreleased diagnostic
artifacts. It does not sample native OpenFOAM fields, compute areas/normals,
launch scheduler work, harvest mdot/T_bulk, or release an energy residual.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-THROUGHFLOW-ENDPOINT-MASK-DERIVATION-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation"

SURFACE_MANIFEST = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/"
    "seeded_surface_input_manifest.csv"
)
ENDPOINT_PREFLIGHT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_throughflow_enthalpy_endpoint_preflight"
)
RESIDUAL_CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_residual_complete_open_cv_energy_balance_contract"
)


CASE_WINDOWS = {"salt_2": "7915", "salt_3": "7618", "salt_4": "10000"}
ENDPOINT_LABEL_BY_SUFFIX = {
    "_start": "open_cv_throughflow_inlet_candidate",
    "_end": "open_cv_throughflow_outlet_candidate",
}
REQUIRED_RELEASE_COLUMNS = [
    "case_id",
    "endpoint_label",
    "face_id",
    "area_m2",
    "area_vector_x_m2",
    "area_vector_y_m2",
    "area_vector_z_m2",
    "owner_cell",
    "normal_convention",
    "positive_mdot_convention",
    "time_window_s",
    "source_path",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
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


def require_inputs() -> None:
    required = [
        SURFACE_MANIFEST,
        ENDPOINT_PREFLIGHT / "endpoint_mask_contract.csv",
        ENDPOINT_PREFLIGHT / "next_action_queue.csv",
        ENDPOINT_PREFLIGHT / "summary.json",
        RESIDUAL_CONTRACT / "throughflow_enthalpy_harvest_contract.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing endpoint-mask derivation inputs: " + "; ".join(missing))


def boolish(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y"}


def cap_endpoint_label(patch_name: str) -> str:
    for suffix, label in ENDPOINT_LABEL_BY_SUFFIX.items():
        if patch_name.endswith(suffix):
            return label
    return "unclassified_seed_cap"


def compact_counts(counter: Counter[str]) -> str:
    return ";".join(f"{key}:{counter[key]}" for key in sorted(counter))


def write_candidate_mask(case_id: str, endpoint_label: str, rows: list[dict[str, str]], source_path: Path) -> Path:
    safe_label = endpoint_label.replace("open_cv_throughflow_", "").replace("_candidate", "")
    path = OUT / "masks" / f"{case_id}_{safe_label}_candidate_face_mask.csv"
    out_rows = []
    for row in rows:
        out_rows.append(
            {
                "case_id": case_id,
                "endpoint_label": endpoint_label,
                "patch_name": row.get("patch_name", ""),
                "face_id": row.get("face_id", ""),
                "candidate_only": "true",
                "release_ready": "false",
                "normal_convention": "",
                "positive_mdot_convention": "",
                "time_window_s": CASE_WINDOWS.get(case_id, ""),
                "source_path": rel(source_path),
                "blocking_reason": (
                    "seed cap faces lack area vectors/normals/owner cells and an admitted "
                    "throughflow endpoint sign convention"
                ),
            }
        )
    write_csv(
        path,
        out_rows,
        [
            "case_id",
            "endpoint_label",
            "patch_name",
            "face_id",
            "candidate_only",
            "release_ready",
            "normal_convention",
            "positive_mdot_convention",
            "time_window_s",
            "source_path",
            "blocking_reason",
        ],
    )
    return path


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    manifest_rows = read_csv(SURFACE_MANIFEST)
    inventory_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    mask_manifest_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []

    manifest_by_case = {row.get("case_id", ""): row for row in manifest_rows}
    for case_id in ["salt_2", "salt_3", "salt_4"]:
        manifest = manifest_by_case.get(case_id, {})
        cap_path = ROOT / manifest.get("classified_cap_faces_csv", "")
        exists = cap_path.exists()
        cap_rows = read_csv(cap_path) if exists else []
        columns = list(cap_rows[0].keys()) if cap_rows else []
        patch_counts = Counter(row.get("patch_name", "") for row in cap_rows)
        endpoint_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in cap_rows:
            endpoint_groups[cap_endpoint_label(row.get("patch_name", ""))].append(row)

        has_basic_face_ids = bool(cap_rows) and {"case_id", "patch_name", "face_id"}.issubset(columns)
        has_release_columns = set(REQUIRED_RELEASE_COLUMNS).issubset(columns)
        has_two_cap_groups = {
            "open_cv_throughflow_inlet_candidate",
            "open_cv_throughflow_outlet_candidate",
        }.issubset(endpoint_groups)
        candidate_paths: dict[str, Path] = {}
        if exists and has_basic_face_ids and has_two_cap_groups:
            for endpoint_label in [
                "open_cv_throughflow_inlet_candidate",
                "open_cv_throughflow_outlet_candidate",
            ]:
                candidate_paths[endpoint_label] = write_candidate_mask(
                    case_id, endpoint_label, endpoint_groups[endpoint_label], cap_path
                )

        missing_release_columns = [column for column in REQUIRED_RELEASE_COLUMNS if column not in columns]
        blocking_reason = (
            "candidate start/end seed cap masks written, but release blocked: "
            "missing area vectors/normals/owner cells and no admitted throughflow "
            "endpoint sign convention"
            if candidate_paths
            else "trusted cap face file missing or cannot be split into start/end candidate endpoints"
        )
        if missing_release_columns:
            blocking_reason += "; missing columns: " + ";".join(missing_release_columns)

        inventory_rows.append(
            {
                "case_id": case_id,
                "classified_cap_faces_csv": rel(cap_path),
                "exists": str(exists).lower(),
                "row_count": len(cap_rows),
                "columns": ";".join(columns),
                "patch_counts": compact_counts(patch_counts),
                "basic_face_ids_present": str(has_basic_face_ids).lower(),
                "start_end_groups_present": str(has_two_cap_groups).lower(),
                "release_columns_present": str(has_release_columns).lower(),
                "missing_release_columns": ";".join(missing_release_columns),
                "source_release_flag": manifest.get("ready_for_surface_extraction", ""),
                "harvest_allowed_in_source_manifest": manifest.get("harvest_allowed", ""),
                "status": "candidate_cap_faces_available_not_released" if candidate_paths else "blocked_no_candidate_masks",
            }
        )
        gate_rows.append(
            {
                "case_id": case_id,
                "cap_faces_available": str(exists and bool(cap_rows)).lower(),
                "candidate_endpoint_masks_written": len(candidate_paths),
                "released_endpoint_masks": 0,
                "normal_release_ready": "false",
                "area_release_ready": "false",
                "owner_cell_release_ready": "false",
                "throughflow_sign_convention_released": "false",
                "same_window_sampler_ready": "false",
                "harvest_allowed": "false",
                "residual_value_release_allowed": "false",
                "decision": "fail_closed_candidate_masks_only_no_harvest_no_residual",
                "blocking_reason": blocking_reason,
            }
        )
        for endpoint_label in [
            "open_cv_throughflow_inlet_candidate",
            "open_cv_throughflow_outlet_candidate",
        ]:
            rows = endpoint_groups.get(endpoint_label, [])
            mask_manifest_rows.append(
                {
                    "case_id": case_id,
                    "endpoint_label": endpoint_label.replace("_candidate", ""),
                    "candidate_mask_path": rel(candidate_paths[endpoint_label]) if endpoint_label in candidate_paths else "",
                    "candidate_face_count": len(rows),
                    "released_mask_path": "",
                    "released": "false",
                    "normal_convention": "",
                    "positive_mdot_convention": "",
                    "time_window_s": CASE_WINDOWS.get(case_id, ""),
                    "basis": "seeded ncc cap patch face ids only; diagnostic candidate, not a released throughflow endpoint mask",
                    "blocking_reason": blocking_reason,
                }
            )

        source_rows.append(
            {
                "artifact": f"{case_id}_classified_seed_cap_faces",
                "path": rel(cap_path),
                "exists": str(exists).lower(),
                "read_only": "true",
                "native_output_mutated": "false",
                "scheduler_action": "false",
            }
        )

    unblock_rows = [
        {
            "rank": 1,
            "needed_artifact": "released_open_cv_endpoint_face_masks",
            "exact_requirement": (
                "one inlet and one outlet row/file per Salt2/Salt3/Salt4 with face_id, "
                "area_m2, area_vector components, owner_cell, endpoint_label, normal "
                "convention, positive mdot convention, and time_window_s"
            ),
            "why_needed": "defines the same-CV throughflow surfaces for mdot_throughflow and bulk enthalpy sampling",
            "scheduler_required": "not_for_mask_contract_if_geometry_tables_exist; likely_for_field_sampling_after_masks",
            "release_condition": "all required columns present and traceable to seeded CV/open-CV geometry, not proxy planes",
        },
        {
            "rank": 2,
            "needed_artifact": "endpoint_sampler_smoke_salt2",
            "exact_requirement": "dry or one-case native sampler row for rho,U,T on the released endpoint masks",
            "why_needed": "checks mdot sign, area-vector orientation, and mass continuity before all-case harvest",
            "scheduler_required": "likely",
            "release_condition": "field extraction uses released masks and same terminal window",
        },
        {
            "rank": 3,
            "needed_artifact": "same_window_all_case_endpoint_harvest",
            "exact_requirement": "mdot_throughflow_kg_s, T_in_bulk_K, T_out_bulk_K, cp basis, and quality flags for Salt2/Salt3/Salt4",
            "why_needed": "unlocks diagnostic open-CV energy residual support",
            "scheduler_required": "likely",
            "release_condition": "same-QOI UQ and mesh/GCI disposition exist before strong claims",
        },
    ]

    write_csv(
        OUT / "classified_cap_face_inventory.csv",
        inventory_rows,
        [
            "case_id",
            "classified_cap_faces_csv",
            "exists",
            "row_count",
            "columns",
            "patch_counts",
            "basic_face_ids_present",
            "start_end_groups_present",
            "release_columns_present",
            "missing_release_columns",
            "source_release_flag",
            "harvest_allowed_in_source_manifest",
            "status",
        ],
    )
    write_csv(
        OUT / "endpoint_mask_derivation_gate.csv",
        gate_rows,
        [
            "case_id",
            "cap_faces_available",
            "candidate_endpoint_masks_written",
            "released_endpoint_masks",
            "normal_release_ready",
            "area_release_ready",
            "owner_cell_release_ready",
            "throughflow_sign_convention_released",
            "same_window_sampler_ready",
            "harvest_allowed",
            "residual_value_release_allowed",
            "decision",
            "blocking_reason",
        ],
    )
    write_csv(
        OUT / "endpoint_mask_manifest.csv",
        mask_manifest_rows,
        [
            "case_id",
            "endpoint_label",
            "candidate_mask_path",
            "candidate_face_count",
            "released_mask_path",
            "released",
            "normal_convention",
            "positive_mdot_convention",
            "time_window_s",
            "basis",
            "blocking_reason",
        ],
    )
    write_csv(
        OUT / "next_unblock_contract.csv",
        unblock_rows,
        ["rank", "needed_artifact", "exact_requirement", "why_needed", "scheduler_required", "release_condition"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        source_rows
        + [
            {
                "artifact": "seeded_surface_input_manifest",
                "path": rel(SURFACE_MANIFEST),
                "exists": "true",
                "read_only": "true",
                "native_output_mutated": "false",
                "scheduler_action": "false",
            },
            {
                "artifact": "endpoint_preflight",
                "path": rel(ENDPOINT_PREFLIGHT),
                "exists": "true",
                "read_only": "true",
                "native_output_mutated": "false",
                "scheduler_action": "false",
            },
        ],
        ["artifact", "path", "exists", "read_only", "native_output_mutated", "scheduler_action"],
    )

    candidate_mask_count = sum(int(row["candidate_endpoint_masks_written"]) for row in gate_rows)
    summary = {
        "task": TASK_ID,
        "decision": "s13_throughflow_endpoint_masks_fail_closed_candidate_seed_cap_masks_only",
        "case_rows": len(gate_rows),
        "candidate_endpoint_masks_written": candidate_mask_count,
        "released_endpoint_masks": 0,
        "harvest_allowed_rows": 0,
        "residual_value_release_rows": 0,
        "native_output_mutated": False,
        "scheduler_action": False,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_json(OUT / "summary.json", summary)

    readme = f"""---
provenance:
  - {rel(SURFACE_MANIFEST)}
  - {rel(ENDPOINT_PREFLIGHT / 'endpoint_mask_contract.csv')}
  - {rel(RESIDUAL_CONTRACT / 'throughflow_enthalpy_harvest_contract.csv')}
tags: [work-product, s13, throughflow, endpoint-mask, open-cv, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-throughflow-endpoint-mask-derivation.md
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Throughflow Endpoint Mask Derivation

Decision: `s13_throughflow_endpoint_masks_fail_closed_candidate_seed_cap_masks_only`.

The trusted seeded surface manifest contains classified non-conformal cap face
IDs for Salt2/Salt3/Salt4. This pass split those cap faces into start/end
candidate masks, but did not release them as throughflow endpoint masks. The
cap-face rows provide `case_id`, `patch_name`, and `face_id`; they do not carry
area vectors, normals, owner cells, or an admitted positive-mdot convention for
the open-CV throughflow endpoints.

Current outcome:

- Candidate endpoint mask files written: `{candidate_mask_count}`.
- Released endpoint masks: `0`.
- Harvest-ready rows: `0`.
- Residual value releases: `0`.

Next exact action: enrich or regenerate the open-CV endpoint geometry table so
each Salt2/Salt3/Salt4 inlet/outlet mask has face IDs, area vectors, owner
cells, normal convention, positive mdot convention, and terminal time window.
Only after that should endpoint field sampling or residual harvest be run.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
