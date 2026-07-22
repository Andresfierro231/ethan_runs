#!/usr/bin/env python3
"""Inventory S13 same-label mesh-family evidence and write the generation contract."""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SAME-LABEL-MESH-FAMILY-INVENTORY-AND-GENERATION-CONTRACT-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_inventory_and_generation_contract"
)

TEMPORAL_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)
MESH_GATE = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate"
)
TARGET_PLUS = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest"
)
UQ_DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_same_window_uq_design"
)
PHASE_B_MESH_GCI = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix"
)
CELL_VTK_MANIFEST = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest"
)
SEEDED_QWALL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_seeded_heat_path_lane_release"
)
SAMPLED_QWALL_UNBLOCK = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock"
)
SOURCE_SIDE_EQUIVALENCE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq"
)
EXACT_QWALL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
)

QOI_SPECS = {
    "Q_wall_W": {
        "required_mesh_family": "upcomer_exchange_heat_loss_fields",
        "formula_sign_basis": (
            "integral of sampled wallHeatFlux over trusted_wall faces; positive Q_wall_W adds heat "
            "to the recirculation/exchange control-volume fluid"
        ),
        "field_inputs_required": "wallHeatFlux on trusted_wall faces at target-minus/target/target-plus windows",
        "geometry_inputs_required": "trusted_wall_vtk, wall face areas, wall provenance, and face normals",
        "property_basis_required": "wallHeatFlux units and sign convention from same solver/source family",
        "acceptance_signal": "coarse/medium/fine or accepted same-label spread rows for Q_wall_W with identical wall mask",
    },
    "mdot_exchange_positive_outward_proxy_kg_s": {
        "required_mesh_family": "V_recirc_mdot_exchange_tau_recirc",
        "formula_sign_basis": (
            "surface integral of max(rho * U dot n_outward, 0) over the trusted exchange interface; "
            "positive is outward from the recirculation CV"
        ),
        "field_inputs_required": "rho and U on the trusted exchange interface at target-minus/target/target-plus windows",
        "geometry_inputs_required": "exchange_interface_vtk, interface areas, normals, and CV provenance",
        "property_basis_required": "rho from the same sampled window and solver output used in the flux integral",
        "acceptance_signal": "coarse/medium/fine or accepted same-label spread rows for the positive-outward mdot proxy",
    },
    "tau_recirc_proxy_s": {
        "required_mesh_family": "V_recirc_mdot_exchange_tau_recirc",
        "formula_sign_basis": (
            "proxy residence time from recirculation CV inventory divided by the same positive-outward exchange "
            "flux basis; no alternative flux label may be substituted"
        ),
        "field_inputs_required": "CV volume or mass inventory plus mdot_exchange_positive_outward_proxy_kg_s on the same mask",
        "geometry_inputs_required": "recirculation CV cells, exchange interface, interface normals, and cell volumes",
        "property_basis_required": "density/mass basis documented consistently with the mdot proxy",
        "acceptance_signal": "coarse/medium/fine or accepted same-label spread rows for tau_recirc_proxy_s",
    },
    "wall_core_bulk_temperature_contrast_K": {
        "required_mesh_family": "upcomer_exchange_heat_loss_fields",
        "formula_sign_basis": (
            "same-mask wall/core/bulk temperature contrast in K; wall, core, and bulk averaging weights must "
            "match the target-window temporal UQ rows"
        ),
        "field_inputs_required": "T, rho, and cell/face weights for wall band, core band, and bulk CV",
        "geometry_inputs_required": "trusted wall band, core band, bulk CV cells, and averaging provenance",
        "property_basis_required": "temperature in K with any density/volume weighting declared",
        "acceptance_signal": "coarse/medium/fine or accepted same-label spread rows for wall_core_bulk_temperature_contrast_K",
    },
}

CURATED_ARTIFACTS = [
    TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv",
    TEMPORAL_UQ / "same_qoi_temporal_uq_case_rows.csv",
    TARGET_PLUS / "same_qoi_neighbor_window_rows.csv",
    MESH_GATE / "qwall_exchange_mesh_gci_gate_matrix.csv",
    MESH_GATE / "missing_mesh_family_blocker_table.csv",
    UQ_DESIGN / "mesh_gci_requirements.csv",
    PHASE_B_MESH_GCI / "mesh_gci_coverage_matrix.csv",
    CELL_VTK_MANIFEST / "three_case_cell_vtk_manifest.csv",
    SEEDED_QWALL / "qwall_contract.csv",
    SAMPLED_QWALL_UNBLOCK / "qwall_or_source_side_path_decision.csv",
    SAMPLED_QWALL_UNBLOCK / "qwall_basis_gate.csv",
    SOURCE_SIDE_EQUIVALENCE / "neighbor_window_mesh_gci_prereq.csv",
    EXACT_QWALL / "trusted_wall_Q_wall_summary.csv",
]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def bool_text(value: bool) -> str:
    return str(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def artifact_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def phase_b_rows_by_name() -> dict[str, dict[str, str]]:
    return {row["qoi_name"]: row for row in read_csv(PHASE_B_MESH_GCI / "mesh_gci_coverage_matrix.csv")}


def temporal_rows_by_label() -> dict[str, dict[str, str]]:
    return {row["qoi_label"]: row for row in read_csv(TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv")}


def mesh_gate_rows_by_label() -> dict[str, dict[str, str]]:
    return {row["qoi_label"]: row for row in read_csv(MESH_GATE / "qwall_exchange_mesh_gci_gate_matrix.csv")}


def exact_label_hit_paths(qoi_label: str) -> list[str]:
    hits = []
    for path in CURATED_ARTIFACTS:
        if qoi_label in artifact_text(path):
            hits.append(rel(path))
    return hits


def related_family_hit_paths(required_family: str) -> list[str]:
    hits = []
    for path in CURATED_ARTIFACTS:
        if required_family in artifact_text(path):
            hits.append(rel(path))
    return hits


def same_label_mesh_family_inventory_rows() -> list[dict[str, str]]:
    temporal = temporal_rows_by_label()
    mesh_gate = mesh_gate_rows_by_label()
    phase_b = phase_b_rows_by_name()
    rows: list[dict[str, str]] = []
    for qoi_label, spec in QOI_SPECS.items():
        exact_hits = exact_label_hit_paths(qoi_label)
        family_hits = related_family_hit_paths(spec["required_mesh_family"])
        gate_row = mesh_gate[qoi_label]
        phase_row = phase_b[spec["required_mesh_family"]]
        temporal_ready = temporal[qoi_label]["same_qoi_temporal_uq_status"] == "executed"
        same_label_mesh_rows = int(gate_row["same_label_mesh_family_rows"])
        accepted_same_label_mesh_rows = int(gate_row["accepted_same_label_gci_rows"])
        ready = same_label_mesh_rows > 0 and accepted_same_label_mesh_rows > 0
        rows.append(
            {
                "qoi_label": qoi_label,
                "required_mesh_family": spec["required_mesh_family"],
                "temporal_uq_available": bool_text(temporal_ready),
                "max_temporal_uncertainty": temporal[qoi_label]["max_abs_temporal_uncertainty"],
                "max_relative_temporal_uncertainty_percent": temporal[qoi_label][
                    "max_relative_temporal_uncertainty_percent"
                ],
                "exact_label_artifact_hits": str(len(exact_hits)),
                "related_family_artifact_hits": str(len(family_hits)),
                "existing_same_label_mesh_family_rows": str(same_label_mesh_rows),
                "accepted_same_label_mesh_gci_rows": str(accepted_same_label_mesh_rows),
                "phase_b_mesh_gci_status": phase_row["mesh_gci_status_summary"],
                "phase_b_blocker": phase_row["phase_b_blocker"],
                "inventory_decision": (
                    "same_label_mesh_family_ready"
                    if ready
                    else "missing_same_label_mesh_family_generate_contract"
                ),
                "production_use_allowed_now": bool_text(ready),
                "next_required_action": (
                    "production harvest may be claimed only after source/property gates are separately released"
                    if ready
                    else "generate or locate same-label coarse/medium/fine mesh-family rows with identical formula/sign/basis"
                ),
                "exact_label_source_paths": ";".join(exact_hits),
                "related_family_source_paths": ";".join(family_hits),
            }
        )
    return rows


def generation_contract_rows() -> list[dict[str, str]]:
    rows = []
    for qoi_label, spec in QOI_SPECS.items():
        rows.append(
            {
                "qoi_label": qoi_label,
                "required_mesh_family": spec["required_mesh_family"],
                "required_cases": "salt_2;salt_3;salt_4",
                "required_time_windows_s": (
                    "salt_2:7914,7915,7916; salt_3:7617,7618,7619; salt_4:9999,10000,10001"
                ),
                "minimum_mesh_levels": "coarse;medium;fine or an already accepted same-label mesh-spread family",
                "field_inputs_required": spec["field_inputs_required"],
                "geometry_inputs_required": spec["geometry_inputs_required"],
                "formula_sign_basis_required": spec["formula_sign_basis"],
                "property_or_source_basis_required": spec["property_basis_required"],
                "same_qoi_rule": "exact label, formula, sign convention, geometry mask, time window, and source family",
                "acceptance_signal": spec["acceptance_signal"],
                "forbidden_shortcuts": (
                    "do not substitute source-side static heat for Q_wall_W; do not relabel average-field proxies "
                    "as production; do not admit coefficient rows without temporal plus mesh/GCI support"
                ),
            }
        )
    return rows


def next_compute_row_skeleton_rows() -> list[dict[str, str]]:
    task = "TODO-S13-UPCOMER-EXCHANGE-SAME-LABEL-MESH-FAMILY-GENERATION-2026-07-22"
    return [
        {
            "task_id": task,
            "role": "Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer",
            "scope": (
                ".agent/BOARD.md own row; task-owned status/journal/import; task-owned extract/analyze scripts; "
                "task-owned work product under work_products/2026-07/2026-07-22/"
                "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation/**"
            ),
            "read_only_context": (
                f"{rel(OUT / 'same_label_mesh_family_inventory.csv')};"
                f"{rel(OUT / 'generation_contract.csv')};"
                f"{rel(TEMPORAL_UQ / 'same_qoi_temporal_uq_case_rows.csv')};"
                f"{rel(MESH_GATE / 'qwall_exchange_mesh_gci_gate_matrix.csv')};"
                f"{rel(CELL_VTK_MANIFEST / 'three_case_cell_vtk_manifest.csv')}"
            ),
            "allowed_actions": (
                "locate or produce same-label coarse/medium/fine mesh-family rows for the four S13 QOI labels "
                "using staged/local copies only and compute-node execution if sampling is required"
            ),
            "forbidden_actions": (
                "native-output mutation, registry/admission mutation, source/property release, coefficient admission, "
                "production harvest, final score, S11/S12/S13/S15/S6 trigger, or replacing exact labels with proxies"
            ),
            "acceptance_signal": (
                "mesh-family table with exact labels for all four QOIs, named mesh levels, formula/sign/basis "
                "provenance, temporal window coverage, validation logs, and explicit mesh/GCI-ready or fail-closed decision"
            ),
        }
    ]


def production_gate_rows(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    ready_count = sum(row["inventory_decision"] == "same_label_mesh_family_ready" for row in inventory)
    return [
        {
            "gate": "same_qoi_neighbor_window_temporal_uq",
            "status": "complete",
            "ready": "true",
            "production_harvest_allowed_now": "false",
            "reason": "all four exact QOI labels have target-minus/target/target-plus temporal UQ",
        },
        {
            "gate": "same_label_mesh_family_inventory",
            "status": "complete",
            "ready": "true",
            "production_harvest_allowed_now": "false",
            "reason": "inventory executed over curated S13 and same-QOI mesh/GCI evidence artifacts",
        },
        {
            "gate": "same_label_mesh_gci_uq",
            "status": "blocked_missing_same_label_mesh_family",
            "ready": "false",
            "production_harvest_allowed_now": "false",
            "reason": f"{ready_count}/4 QOI labels have accepted same-label mesh/GCI rows",
        },
        {
            "gate": "next_compute_contract",
            "status": "ready_to_claim",
            "ready": "true",
            "production_harvest_allowed_now": "false",
            "reason": "exact labels, signs, source/property basis, windows, and mesh-family requirements are specified",
        },
        {
            "gate": "production_harvest_or_admission",
            "status": "do_not_run",
            "ready": "false",
            "production_harvest_allowed_now": "false",
            "reason": "mesh/GCI support remains absent after inventory",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "path": rel(path),
            "role": "curated evidence artifact searched for exact labels and mesh-family status",
            "exists": bool_text(path.exists()),
            "mutation": "read_only",
        }
        for path in CURATED_ARTIFACTS
    ]


def guardrail_rows() -> list[dict[str, str]]:
    flags = {
        "native_output_mutation": "false",
        "staged_output_mutation": "false",
        "registry_or_admission_mutation": "false",
        "scheduler_action": "false",
        "solver_postprocessing_sampler_or_uq_launch": "false",
        "mesh_gci_computation": "false",
        "production_harvest": "false",
        "Qwall_source_property_or_coefficient_release": "false",
        "s11_s12_s13_s15_s6_trigger": "false",
        "residual_absorbed_into_internal_nu": "false",
    }
    return [{"guardrail": key, "value": value} for key, value in flags.items()]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(out / "same_label_mesh_family_inventory.csv")}
  - {rel(out / "generation_contract.csv")}
  - {rel(MESH_GATE / "qwall_exchange_mesh_gci_gate_matrix.csv")}
tags: [s13, upcomer-exchange, qwall, mesh-gci, same-qoi-uq, contract]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - {rel(TEMPORAL_UQ / "README.md")}
  - {rel(MESH_GATE / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Same-Label Mesh-Family Inventory And Generation Contract

Decision: `{summary["decision"]}`.

The S13 same-QOI temporal UQ row is complete, but the current durable evidence
still contains no accepted same-label mesh-family/GCI rows for the four S13
exchange labels.

- QOI labels inventoried: `{summary["qoi_label_count"]}`
- exact-label source artifacts found: `{summary["total_exact_label_artifact_hits"]}`
- same-label mesh-family rows accepted now: `{summary["accepted_same_label_mesh_gci_rows"]}`
- generation-contract rows: `{summary["generation_contract_rows"]}`
- production harvest allowed: `{str(summary["production_harvest_allowed"]).lower()}`

Next action: claim the compute/generation row named in
`next_compute_row_skeleton.csv`. It must produce or locate named
coarse/medium/fine evidence for the exact labels, masks, signs, windows, and
source/property bases in `generation_contract.csv`.

Do not use source-side static heat as `Q_wall_W`, do not relabel average-field
proxies as production evidence, and do not run S13 production harvest or
admission until same-label mesh/GCI passes.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    inventory = same_label_mesh_family_inventory_rows()
    contract = generation_contract_rows()
    next_row = next_compute_row_skeleton_rows()
    production = production_gate_rows(inventory)
    manifest = source_manifest_rows()
    guardrails = guardrail_rows()

    summary: dict[str, Any] = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "same_label_mesh_family_absent_generation_contract_ready",
        "qoi_label_count": len(inventory),
        "temporal_uq_complete_qois": sum(row["temporal_uq_available"] == "true" for row in inventory),
        "total_exact_label_artifact_hits": sum(int(row["exact_label_artifact_hits"]) for row in inventory),
        "same_label_mesh_family_rows": sum(int(row["existing_same_label_mesh_family_rows"]) for row in inventory),
        "accepted_same_label_mesh_gci_rows": sum(int(row["accepted_same_label_mesh_gci_rows"]) for row in inventory),
        "generation_contract_rows": len(contract),
        "next_compute_contract_ready": True,
        "production_harvest_allowed": False,
        "admission_allowed": False,
    }

    csv_dump(out / "same_label_mesh_family_inventory.csv", list(inventory[0]), inventory)
    csv_dump(out / "generation_contract.csv", list(contract[0]), contract)
    csv_dump(out / "next_compute_row_skeleton.csv", list(next_row[0]), next_row)
    csv_dump(out / "production_gate.csv", list(production[0]), production)
    csv_dump(out / "source_manifest.csv", list(manifest[0]), manifest)
    csv_dump(out / "no_mutation_guardrails.csv", list(guardrails[0]), guardrails)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
