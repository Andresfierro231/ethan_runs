#!/usr/bin/env python3
"""Gate S13 Qwall/exchange QOIs against same-label mesh/GCI requirements."""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-QWALL-MESH-GCI-UQ-GATE-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate"
)
TEMPORAL_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)
TARGET_PLUS_HARVEST = ROOT / (
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
EXACT_QWALL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
)

MESH_FAMILY_MAP = {
    "Q_wall_W": {
        "required_family": "upcomer_exchange_heat_loss_fields",
        "phase_b_qoi_name": "upcomer_exchange_heat_loss_fields",
        "required_quantity": "same-label Q_wall_W on a named coarse/medium/fine or accepted mesh-spread family",
    },
    "mdot_exchange_positive_outward_proxy_kg_s": {
        "required_family": "V_recirc_mdot_exchange_tau_recirc",
        "phase_b_qoi_name": "V_recirc_mdot_exchange_tau_recirc",
        "required_quantity": "same-label exchange mdot proxy on a named coarse/medium/fine or accepted mesh-spread family",
    },
    "tau_recirc_proxy_s": {
        "required_family": "V_recirc_mdot_exchange_tau_recirc",
        "phase_b_qoi_name": "V_recirc_mdot_exchange_tau_recirc",
        "required_quantity": "same-label residence-time proxy on a named coarse/medium/fine or accepted mesh-spread family",
    },
    "wall_core_bulk_temperature_contrast_K": {
        "required_family": "upcomer_exchange_heat_loss_fields",
        "phase_b_qoi_name": "upcomer_exchange_heat_loss_fields",
        "required_quantity": "same-label wall/core/bulk temperature contrast on a named coarse/medium/fine or accepted mesh-spread family",
    },
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def bool_text(value: bool) -> str:
    return str(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def phase_b_rows_by_name() -> dict[str, dict[str, str]]:
    return {row["qoi_name"]: row for row in read_csv(PHASE_B_MESH_GCI / "mesh_gci_coverage_matrix.csv")}


def temporal_rows_by_label() -> dict[str, dict[str, str]]:
    return {row["qoi_label"]: row for row in read_csv(TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv")}


def mesh_gate_matrix_rows() -> list[dict[str, str]]:
    phase_b = phase_b_rows_by_name()
    temporal = temporal_rows_by_label()
    rows: list[dict[str, str]] = []
    for qoi_label, mapping in MESH_FAMILY_MAP.items():
        temporal_row = temporal[qoi_label]
        phase_row = phase_b[mapping["phase_b_qoi_name"]]
        temporal_ready = temporal_row["same_qoi_temporal_uq_status"] == "executed"
        same_label_mesh_rows = 0
        accepted_gci_rows = int(phase_row["accepted_gci_rows"])
        same_label_mesh_ready = same_label_mesh_rows > 0 and accepted_gci_rows > 0
        rows.append(
            {
                "qoi_label": qoi_label,
                "required_mesh_family": mapping["required_family"],
                "required_quantity": mapping["required_quantity"],
                "temporal_uq_status": temporal_row["same_qoi_temporal_uq_status"],
                "temporal_uq_max_abs": temporal_row["max_abs_temporal_uncertainty"],
                "temporal_uq_max_relative_percent": temporal_row["max_relative_temporal_uncertainty_percent"],
                "phase_b_qoi_name": mapping["phase_b_qoi_name"],
                "phase_b_classification": phase_row["phase_b_classification"],
                "phase_b_blocker": phase_row["phase_b_blocker"],
                "phase_b_status_summary": phase_row["mesh_gci_status_summary"],
                "phase_b_matched_prior_rows": phase_row["matched_prior_same_qoi_rows"],
                "same_label_mesh_family_rows": str(same_label_mesh_rows),
                "accepted_same_label_gci_rows": str(accepted_gci_rows if same_label_mesh_ready else 0),
                "same_label_mesh_gci_ready": bool_text(same_label_mesh_ready),
                "mesh_gci_gate_executed": "true",
                "mesh_gci_uq_status": "accepted" if same_label_mesh_ready else "blocked_missing_same_label_mesh_family",
                "move_to_production_harvest_allowed_now": "false",
                "admission_allowed_now": "false",
                "blocking_or_next_reason": (
                    "same-QOI temporal UQ exists, but no same-label mesh family/GCI row exists for this QOI"
                    if temporal_ready and not same_label_mesh_ready
                    else "temporal UQ missing or mesh/GCI not accepted"
                ),
                "source_paths": ";".join(
                    [
                        rel(TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv"),
                        rel(PHASE_B_MESH_GCI / "mesh_gci_coverage_matrix.csv"),
                    ]
                ),
            }
        )
    return rows


def missing_mesh_family_rows(matrix_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in matrix_rows:
        if row["same_label_mesh_gci_ready"] == "true":
            continue
        rows.append(
            {
                "qoi_label": row["qoi_label"],
                "missing_requirement": row["required_quantity"],
                "temporal_uq_available": bool_text(row["temporal_uq_status"] == "executed"),
                "phase_b_blocker": row["phase_b_blocker"],
                "production_consequence": "blocks_production_harvest_and_admission",
                "next_evidence_needed": "generate or locate same-label coarse/medium/fine mesh-family rows with identical formula/sign/basis",
                "source_paths": row["source_paths"],
            }
        )
    return rows


def production_consequence_rows(matrix_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    accepted = sum(1 for row in matrix_rows if row["same_label_mesh_gci_ready"] == "true")
    return [
        {
            "gate": "same_qoi_neighbor_window_temporal_uq",
            "status": "complete",
            "ready_for_next_stage": "true",
            "production_harvest_allowed_now": "false",
            "reason": "after-target-plus temporal UQ executed for all four labels",
        },
        {
            "gate": "same_label_mesh_gci_uq",
            "status": "blocked_missing_same_label_mesh_family",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": f"{accepted}/4 QOI labels have accepted same-label mesh/GCI rows",
        },
        {
            "gate": "source_property_release",
            "status": "not_reached_mesh_gci_blocked",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "do not release source/property or coefficient rows while mesh/GCI is missing",
        },
        {
            "gate": "production_harvest",
            "status": "do_not_run",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "temporal UQ passed but same-label mesh/GCI support is absent",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (TEMPORAL_UQ / "summary.json", "after-target-plus temporal UQ summary"),
        (TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv", "temporal UQ QOI-level input"),
        (TARGET_PLUS_HARVEST / "same_qoi_neighbor_window_rows.csv", "complete temporal triplet table"),
        (UQ_DESIGN / "mesh_gci_requirements.csv", "S13 mesh/GCI requirement contract"),
        (PHASE_B_MESH_GCI / "mesh_gci_coverage_matrix.csv", "existing mesh/GCI evidence matrix"),
        (EXACT_QWALL / "trusted_wall_Q_wall_summary.csv", "direct Q_wall_W provenance"),
    ]
    return [
        {"path": rel(path), "role": role, "exists": bool_text(path.exists()), "mutation": "read_only"}
        for path, role in paths
    ]


def guardrail_rows() -> list[dict[str, str]]:
    flags = {
        "native_output_mutation": "false",
        "staged_output_mutation": "false",
        "registry_or_admission_mutation": "false",
        "scheduler_action": "false",
        "solver_or_sampler_launch": "false",
        "production_harvest": "false",
        "Qwall_source_property_or_coefficient_release": "false",
        "s11_s12_s13_s15_s6_trigger": "false",
        "residual_absorbed_into_internal_nu": "false",
    }
    return [{"guardrail": key, "value": value} for key, value in flags.items()]


def write_readme(out: Path, summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - {rel(out / "qwall_exchange_mesh_gci_gate_matrix.csv")}
  - {rel(out / "missing_mesh_family_blocker_table.csv")}
  - {rel(TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv")}
tags: [s13, upcomer-exchange, qwall, mesh-gci, same-qoi-uq]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - {rel(TEMPORAL_UQ / "README.md")}
  - {rel(PHASE_B_MESH_GCI / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Qwall Mesh/GCI UQ Gate

Decision: `{summary["decision"]}`.

Same-QOI temporal neighbor-window UQ is now executed, but the mesh/GCI gate
fails closed because no same-label mesh family exists for the S13 Qwall/exchange
QOI labels.

- QOI labels reviewed: `{summary["qoi_label_count"]}`
- temporal-UQ complete labels: `{summary["temporal_uq_complete_qois"]}`
- accepted same-label mesh/GCI labels: `{summary["accepted_same_label_mesh_gci_qois"]}`
- missing mesh-family blocker rows: `{summary["missing_mesh_family_blocker_rows"]}`
- production harvest allowed: `false`

Next action: generate or locate same-label coarse/medium/fine mesh-family rows
for these exact QOI labels. Until then, keep S13 as temporally supported
diagnostic evidence, not an admitted production exchange coefficient.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, object]:
    ensure_dir(out)
    matrix_rows = mesh_gate_matrix_rows()
    blocker_rows = missing_mesh_family_rows(matrix_rows)
    consequence_rows = production_consequence_rows(matrix_rows)
    source_rows = source_manifest_rows()
    guard_rows = guardrail_rows()
    temporal_ready = sum(1 for row in matrix_rows if row["temporal_uq_status"] == "executed")
    accepted_mesh = sum(1 for row in matrix_rows if row["same_label_mesh_gci_ready"] == "true")
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "fail_closed_missing_same_label_mesh_gci_family_after_temporal_uq",
        "qoi_label_count": len(matrix_rows),
        "temporal_uq_complete_qois": temporal_ready,
        "mesh_gci_gate_executed_qois": len(matrix_rows),
        "accepted_same_label_mesh_gci_qois": accepted_mesh,
        "missing_mesh_family_blocker_rows": len(blocker_rows),
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "native_output_mutation": False,
        "staged_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Q_wall_W_production_release": False,
        "source_property_release": False,
        "source_side_relabel_as_Q_wall": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    csv_dump(out / "qwall_exchange_mesh_gci_gate_matrix.csv", list(matrix_rows[0]), matrix_rows)
    csv_dump(out / "missing_mesh_family_blocker_table.csv", list(blocker_rows[0]), blocker_rows)
    csv_dump(out / "production_harvest_consequence.csv", list(consequence_rows[0]), consequence_rows)
    csv_dump(out / "source_manifest.csv", list(source_rows[0]), source_rows)
    csv_dump(out / "no_mutation_guardrails.csv", list(guard_rows[0]), guard_rows)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
