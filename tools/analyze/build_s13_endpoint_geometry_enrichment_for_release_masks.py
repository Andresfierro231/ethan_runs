#!/usr/bin/env python3
"""Build the S13 endpoint-geometry enrichment gate for release masks.

This package upgrades the previous candidate endpoint-mask pass into an explicit
release-mask preflight. It does not fabricate area vectors, owner cells, or
throughflow residual values from cap face IDs.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-ENDPOINT-GEOMETRY-ENRICHMENT-FOR-RELEASE-MASKS-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_geometry_enrichment_for_release_masks"

ENDPOINT_DERIVATION = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation"
ENDPOINT_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight"
RESIDUAL_CONTRACT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract"
SEEDED_MANIFEST = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"

GUARDRAILS = {
    "native_solver_outputs_mutated": False,
    "registry_or_admission_mutated": False,
    "scheduler_action": False,
    "solver_postprocessing_sampler_harvest_uq_launched": False,
    "fluid_or_external_edit": False,
    "thesis_current_or_latex_edit": False,
    "source_property_release": False,
    "Qwall_release": False,
    "residual_value_release": False,
    "coefficient_fitting_or_admission": False,
    "validation_holdout_external_scoring": False,
    "candidate_freeze": False,
    "final_score_claim": False,
    "s11_s12_s13_s15_s6_trigger": False,
    "endpoint_proxy_substitution": False,
    "hidden_multiplier": False,
    "residual_absorbed_into_internal_Nu": False,
    "runtime_leakage_relaxation": False,
}

MANDATORY_RELEASE_FIELDS = [
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


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


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
        ENDPOINT_DERIVATION / "endpoint_mask_manifest.csv",
        ENDPOINT_DERIVATION / "classified_cap_face_inventory.csv",
        ENDPOINT_DERIVATION / "endpoint_mask_derivation_gate.csv",
        ENDPOINT_PREFLIGHT / "same_window_field_status.csv",
        ENDPOINT_PREFLIGHT / "required_input_status_matrix.csv",
        RESIDUAL_CONTRACT / "throughflow_enthalpy_harvest_contract.csv",
        SEEDED_MANIFEST / "seeded_surface_input_manifest.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 endpoint enrichment inputs: " + "; ".join(missing))


def bool_str(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def cap_face_columns_by_case(inventory_rows: list[dict[str, str]]) -> dict[str, set[str]]:
    columns: dict[str, set[str]] = {}
    for row in inventory_rows:
        case_id = row["case_id"]
        path = ROOT / row["classified_cap_faces_csv"]
        if path.exists():
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                columns[case_id] = set(reader.fieldnames or [])
        else:
            columns[case_id] = set()
    return columns


def manifest_by_case() -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(SEEDED_MANIFEST / "seeded_surface_input_manifest.csv")}


def same_window_status_by_label() -> dict[str, dict[str, str]]:
    return {row["field_or_input"]: row for row in read_csv(ENDPOINT_PREFLIGHT / "same_window_field_status.csv")}


def build_endpoint_rows() -> list[dict[str, Any]]:
    endpoint_rows = read_csv(ENDPOINT_DERIVATION / "endpoint_mask_manifest.csv")
    inventory_rows = read_csv(ENDPOINT_DERIVATION / "classified_cap_face_inventory.csv")
    columns_by_case = cap_face_columns_by_case(inventory_rows)
    seeded_by_case = manifest_by_case()
    rows: list[dict[str, Any]] = []
    for row in endpoint_rows:
        case_id = row["case_id"]
        columns = columns_by_case.get(case_id, set())
        seeded = seeded_by_case[case_id]
        face_id_ready = "face_id" in columns and int(row["candidate_face_count"]) > 0
        source_path_context_ready = "source_paths" in columns
        case_normal_context_ready = bool(seeded["normal_convention"])
        case_positive_mdot_context_ready = bool(seeded["positive_flux_convention"])
        time_window_ready = bool(row["time_window_s"])
        per_face_area_ready = "area_m2" in columns
        per_face_area_vector_ready = {"area_vector_x_m2", "area_vector_y_m2", "area_vector_z_m2"}.issubset(columns)
        owner_cell_ready = "owner_cell" in columns or "owner" in columns
        release_ready = all(
            [
                face_id_ready,
                source_path_context_ready,
                case_normal_context_ready,
                case_positive_mdot_context_ready,
                time_window_ready,
                per_face_area_ready,
                per_face_area_vector_ready,
                owner_cell_ready,
            ]
        )
        missing = []
        if not per_face_area_ready:
            missing.append("area_m2")
        if not per_face_area_vector_ready:
            missing.extend(["area_vector_x_m2", "area_vector_y_m2", "area_vector_z_m2"])
        if not owner_cell_ready:
            missing.append("owner_cell")
        if not source_path_context_ready:
            missing.append("source_path")
        rows.append(
            {
                "case_id": case_id,
                "endpoint_label": row["endpoint_label"],
                "candidate_mask_path": row["candidate_mask_path"],
                "candidate_face_count": row["candidate_face_count"],
                "candidate_face_ids_ready": face_id_ready,
                "case_normal_convention_context": seeded["normal_convention"],
                "case_positive_mdot_convention_context": seeded["positive_flux_convention"],
                "time_window_s": row["time_window_s"],
                "per_face_area_ready": per_face_area_ready,
                "per_face_area_vector_ready": per_face_area_vector_ready,
                "owner_cell_ready": owner_cell_ready,
                "source_path_context_ready": source_path_context_ready,
                "release_mask_ready": release_ready,
                "released_mask_path": "" if not release_ready else row["candidate_mask_path"],
                "harvest_allowed": False,
                "residual_value_release_allowed": False,
                "missing_release_fields": ";".join(missing),
                "decision": "release_ready" if release_ready else "fail_closed_geometry_enrichment_required",
            }
        )
    return rows


def mandatory_field_rows(endpoint_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in endpoint_rows:
        readiness = {
            "case_id": True,
            "endpoint_label": True,
            "face_id": bool_str(row["candidate_face_ids_ready"]),
            "area_m2": bool_str(row["per_face_area_ready"]),
            "area_vector_x_m2": bool_str(row["per_face_area_vector_ready"]),
            "area_vector_y_m2": bool_str(row["per_face_area_vector_ready"]),
            "area_vector_z_m2": bool_str(row["per_face_area_vector_ready"]),
            "owner_cell": bool_str(row["owner_cell_ready"]),
            "normal_convention": bool(row["case_normal_convention_context"]),
            "positive_mdot_convention": bool(row["case_positive_mdot_convention_context"]),
            "time_window_s": bool(row["time_window_s"]),
            "source_path": bool_str(row["source_path_context_ready"]),
        }
        for field in MANDATORY_RELEASE_FIELDS:
            rows.append(
                {
                    "case_id": row["case_id"],
                    "endpoint_label": row["endpoint_label"],
                    "mandatory_field": field,
                    "ready_for_release_mask": readiness[field],
                    "release_role": "required_endpoint_mask_schema",
                    "notes": "case-level convention context only; per-face vectors still required"
                    if field in {"normal_convention", "positive_mdot_convention"} and readiness[field]
                    else "",
                }
            )
    return rows


def residual_harvest_rows(endpoint_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in endpoint_rows:
        grouped[row["case_id"]].append(row)
    same_window = same_window_status_by_label()
    qwall_ready = bool_str(same_window["Q_wall_W"]["release_ready"])
    cp_ready = bool_str(same_window["cp_J_kg_K"]["release_ready"])
    rows: list[dict[str, Any]] = []
    for case_id, rows_for_case in sorted(grouped.items()):
        released = sum(bool_str(row["release_mask_ready"]) for row in rows_for_case)
        missing = sorted(
            {
                field
                for row in rows_for_case
                for field in str(row["missing_release_fields"]).split(";")
                if field
            }
        )
        harvest_ready = released == 2 and qwall_ready and cp_ready
        rows.append(
            {
                "case_id": case_id,
                "released_endpoint_masks": released,
                "required_endpoint_masks": 2,
                "qwall_release_ready": qwall_ready,
                "cp_release_ready": cp_ready,
                "harvest_ready": harvest_ready,
                "residual_value_release_allowed": False,
                "blocking_reason": "release endpoint geometry missing: " + ";".join(missing)
                if not harvest_ready
                else "ready_but_residual_release_requires_separate_admission_row",
            }
        )
    return rows


def regeneration_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "contract_item": "endpoint_release_mask_schema",
            "required_output": ";".join(MANDATORY_RELEASE_FIELDS),
            "acceptance": "one row per endpoint face with no missing mandatory fields",
            "forbidden_substitution": "candidate cap face ids without area vectors or owner cells",
        },
        {
            "contract_item": "normal_and_mdot_sign",
            "required_output": "normal_convention;positive_mdot_convention;inlet_outlet_sign_check;continuity_mismatch",
            "acceptance": "positive mdot convention is explicit and used consistently for inlet/outlet integration",
            "forbidden_substitution": "exchange-interface normal convention as throughflow endpoint convention without endpoint proof",
        },
        {
            "contract_item": "same_window_fields",
            "required_output": "mdot_throughflow_kg_s;T_in_bulk_K;T_out_bulk_K;cp_J_kg_K;Q_wall_W_or_source_side_heat_path",
            "acceptance": "all fields share endpoint masks and target window",
            "forbidden_substitution": "point probes, wall temperatures, exchange mdot proxy, or realized Qwall as runtime input",
        },
    ]


def thesis_claim_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim": "S13 endpoint masks are release-ready",
            "allowed": False,
            "basis": "released endpoint masks = 0",
        },
        {
            "claim": "S13 candidate cap masks exist and are useful for next geometry regeneration",
            "allowed": True,
            "basis": f"candidate endpoint rows = {summary['candidate_endpoint_rows']}",
        },
        {
            "claim": "S13 residual values can be computed now",
            "allowed": False,
            "basis": "harvest-ready cases = 0 and residual value releases = 0",
        },
        {
            "claim": "Missing heat residual can be absorbed into internal Nu",
            "allowed": False,
            "basis": "explicit guardrail; residual remains its own lane",
        },
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [
        ENDPOINT_DERIVATION / "endpoint_mask_manifest.csv",
        ENDPOINT_DERIVATION / "classified_cap_face_inventory.csv",
        ENDPOINT_PREFLIGHT / "same_window_field_status.csv",
        ENDPOINT_PREFLIGHT / "required_input_status_matrix.csv",
        RESIDUAL_CONTRACT / "throughflow_enthalpy_harvest_contract.csv",
        SEEDED_MANIFEST / "seeded_surface_input_manifest.csv",
    ]
    return [
        {"source_path": rel(path), "exists": path.exists(), "read_only": True, "role": "endpoint_geometry_enrichment_input"}
        for path in paths
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(ENDPOINT_DERIVATION / 'summary.json')}
  - {rel(ENDPOINT_DERIVATION / 'endpoint_mask_manifest.csv')}
  - {rel(SEEDED_MANIFEST / 'seeded_surface_input_manifest.csv')}
tags: [work-product, s13, endpoint-geometry, release-mask, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-endpoint-geometry-enrichment-for-release-masks.md
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Endpoint Geometry Enrichment For Release Masks

Decision: `{summary['decision']}`.

This package checks whether the S13 candidate cap masks can be promoted to
release-grade throughflow endpoint masks. They cannot yet: candidate cap face IDs
exist for all six endpoints, but released endpoint masks remain `{summary['released_endpoint_masks']}`
because per-face area vectors and owner-cell provenance are absent.

The case-level seeded normal and positive-flux conventions are useful context,
but they do not replace endpoint-face area vectors, owner cells, and signed
throughflow continuity checks. No sampler, harvest, residual value, source/Qwall
release, coefficient admission, or internal-Nu residual absorption occurred.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    endpoint_rows = build_endpoint_rows()
    mandatory_rows = mandatory_field_rows(endpoint_rows)
    harvest_rows = residual_harvest_rows(endpoint_rows)
    released_endpoint_masks = sum(bool_str(row["release_mask_ready"]) for row in endpoint_rows)
    harvest_ready_cases = sum(bool_str(row["harvest_ready"]) for row in harvest_rows)
    summary = {
        "task_id": TASK_ID,
        "decision": "s13_endpoint_geometry_enrichment_fail_closed_release_masks_zero",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidate_endpoint_rows": len(endpoint_rows),
        "released_endpoint_masks": released_endpoint_masks,
        "harvest_ready_cases": harvest_ready_cases,
        "residual_value_release_rows": 0,
        "mandatory_field_rows": len(mandatory_rows),
        "missing_release_fields": sorted(
            {
                field
                for row in endpoint_rows
                for field in str(row["missing_release_fields"]).split(";")
                if field
            }
        ),
        **GUARDRAILS,
    }
    write_csv(
        OUT / "endpoint_geometry_enrichment_gate.csv",
        endpoint_rows,
        [
            "case_id",
            "endpoint_label",
            "candidate_mask_path",
            "candidate_face_count",
            "candidate_face_ids_ready",
            "case_normal_convention_context",
            "case_positive_mdot_convention_context",
            "time_window_s",
            "per_face_area_ready",
            "per_face_area_vector_ready",
            "owner_cell_ready",
            "source_path_context_ready",
            "release_mask_ready",
            "released_mask_path",
            "harvest_allowed",
            "residual_value_release_allowed",
            "missing_release_fields",
            "decision",
        ],
    )
    write_csv(
        OUT / "mandatory_release_field_matrix.csv",
        mandatory_rows,
        ["case_id", "endpoint_label", "mandatory_field", "ready_for_release_mask", "release_role", "notes"],
    )
    write_csv(
        OUT / "residual_harvest_release_gate.csv",
        harvest_rows,
        [
            "case_id",
            "released_endpoint_masks",
            "required_endpoint_masks",
            "qwall_release_ready",
            "cp_release_ready",
            "harvest_ready",
            "residual_value_release_allowed",
            "blocking_reason",
        ],
    )
    write_csv(
        OUT / "endpoint_regeneration_contract.csv",
        regeneration_contract_rows(),
        ["contract_item", "required_output", "acceptance", "forbidden_substitution"],
    )
    write_csv(OUT / "thesis_claim_ledger.csv", thesis_claim_rows(summary), ["claim", "allowed", "basis"])
    write_csv(OUT / "source_manifest.csv", source_manifest_rows(), ["source_path", "exists", "read_only", "role"])
    write_csv(OUT / "no_mutation_guardrails.csv", [{"guardrail": key, "occurred": value} for key, value in GUARDRAILS.items()], ["guardrail", "occurred"])
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    build()


if __name__ == "__main__":
    main()
