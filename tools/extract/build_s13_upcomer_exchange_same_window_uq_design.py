#!/usr/bin/env python3
"""Build the S13 upcomer exchange same-window UQ design package.

This is a documentation and gate-design package. It reads existing UQ and
geometry contracts, emits fail-closed downstream tables, and does not launch
sampling, postprocessing, solvers, fitting, or admission.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SAME-WINDOW-UQ-DESIGN-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_same_window_uq_design"
)

S9 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq"
)
PHASE_A = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_a_retained_window_inventory"
)
PHASE_B = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix"
)
PHASE_C = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_c_admission_table"
)
GEOMETRY = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_geometry_contract"
)

SOURCE_FILES = {
    "s9_requirements": S9 / "same_window_uq_requirements.csv",
    "phase_a_retained_inventory": PHASE_A / "qoi_retained_window_inventory.csv",
    "phase_b_mesh_gci_matrix": PHASE_B / "mesh_gci_coverage_matrix.csv",
    "phase_c_admission_table": PHASE_C / "same_qoi_uq_admission_table.csv",
    "geometry_downstream_inputs": GEOMETRY / "downstream_surface_vtk_inputs.csv",
}

TARGET_QOIS = [
    "V_recirc_mdot_exchange_tau_recirc",
    "terminal_source_family_exchange_QOIs",
    "upcomer_exchange_heat_loss_fields",
]
SUPPORT_GATES = [
    "same_qoi_UQ",
    "pressure_basis",
    "thermal_energy_residual",
    "mesh_time_status",
]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_by_qoi(rows: list[dict[str, str]], qoi: str) -> dict[str, str]:
    for row in rows:
        if row.get("qoi_name") == qoi or row.get("qoi_or_gate") == qoi:
            return row
    return {}


def source_manifest() -> list[dict[str, Any]]:
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for role, path in SOURCE_FILES.items()
    ]


def uq_acceptance_contract(
    s9_rows: list[dict[str, str]],
    phase_a_rows: list[dict[str, str]],
    phase_b_rows: list[dict[str, str]],
    phase_c_rows: list[dict[str, str]],
    geometry_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    cell_ready = sorted(
        row["case_id"]
        for row in geometry_rows
        if row.get("input_lane") == "cell_vtk" and row.get("status") == "ready"
    )
    blocked_lanes = sorted(
        {row.get("input_lane", "") for row in geometry_rows if row.get("status") == "blocked"}
    )
    rows: list[dict[str, str]] = []
    for qoi in TARGET_QOIS:
        s9 = find_by_qoi(s9_rows, qoi)
        a = find_by_qoi(phase_a_rows, qoi)
        b = find_by_qoi(phase_b_rows, qoi)
        c = find_by_qoi(phase_c_rows, qoi)
        rows.append(
            {
                "qoi_name": qoi,
                "qoi_family": c.get("qoi_family", a.get("qoi_family", "")),
                "required_same_window_outputs": (
                    "retained_window_value;neighbor_minus_window;"
                    "neighbor_plus_window;same_qoi_mesh_or_gci;source_geometry_release"
                ),
                "retained_time_evidence": a.get(
                    "retained_time_source", b.get("phase_a_retained_time_source", "")
                ),
                "neighbor_window_gate": c.get(
                    "time_window_gate", b.get("phase_a_neighbor_window_status", "")
                ),
                "mesh_gci_gate": c.get("mesh_gci_gate", b.get("phase_b_classification", "")),
                "source_gate": c.get("source_gate", s9.get("current_status", "")),
                "geometry_gate": "blocked:" + ";".join(blocked_lanes),
                "cell_vtk_ready_cases": ";".join(cell_ready),
                "s13_acceptance_status": "blocked",
                "s11_reviewable_now": "false",
                "sampler_or_harvest_allowed_now": "false",
                "decision_rule": (
                    "release only after exact retained same-window value, both neighboring "
                    "windows, accepted same-QOI mesh/GCI, and trusted interface/wall/source "
                    "geometry all pass for the same QOI label/formula/sign/basis"
                ),
                "next_extraction_task": c.get("next_task", s9.get("next_action", "")),
                "source_paths": ";".join(
                    [
                        rel(SOURCE_FILES["s9_requirements"]),
                        rel(SOURCE_FILES["phase_a_retained_inventory"]),
                        rel(SOURCE_FILES["phase_b_mesh_gci_matrix"]),
                        rel(SOURCE_FILES["phase_c_admission_table"]),
                        rel(SOURCE_FILES["geometry_downstream_inputs"]),
                    ]
                ),
            }
        )
    return rows


def neighbor_window_requirements(phase_a_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for qoi in TARGET_QOIS:
        a = find_by_qoi(phase_a_rows, qoi)
        rows.append(
            {
                "qoi_name": qoi,
                "retained_window_requirement": "one retained S13 same-window value per Salt2/Salt3/Salt4 case",
                "neighbor_minus_requirement": "same label/formula/sign/basis sampled in an adjacent earlier retained window",
                "neighbor_plus_requirement": "same label/formula/sign/basis sampled in an adjacent later retained window",
                "current_retained_evidence": a.get("retained_time_source", ""),
                "current_neighbor_status": a.get("neighbor_window_status", "blocked_missing_neighbor_window"),
                "current_drift_status": a.get("drift_status", "not_evaluated"),
                "status": "blocked",
                "next_task": a.get("next_extraction_task", ""),
            }
        )
    return rows


def mesh_gci_requirements(phase_b_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for qoi in TARGET_QOIS:
        b = find_by_qoi(phase_b_rows, qoi)
        rows.append(
            {
                "qoi_name": qoi,
                "mesh_family_requirement": (
                    "same QOI label/formula/sign/basis on a named coarse/medium/fine or accepted "
                    "same-QOI mesh-spread family"
                ),
                "matched_prior_same_qoi_rows": b.get("matched_prior_same_qoi_rows", "0"),
                "mesh_gci_status_summary": b.get("mesh_gci_status_summary", "missing_no_prior_same_qoi_mesh_rows"),
                "phase_b_classification": b.get("phase_b_classification", "blocked"),
                "phase_b_blocker": b.get("phase_b_blocker", "missing_exchange_or_terminal_mesh_family"),
                "accepted_gci_rows": b.get("accepted_gci_rows", "0"),
                "status": "blocked",
                "next_task": b.get("next_task", ""),
            }
        )
    return rows


def qoi_release_decision(
    s9_rows: list[dict[str, str]],
    phase_c_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for gate in SUPPORT_GATES:
        s9 = find_by_qoi(s9_rows, gate)
        rows.append(
            {
                "item": gate,
                "item_type": "support_gate",
                "current_status": s9.get("current_status", "blocked_or_diagnostic"),
                "release_allowed_now": "false",
                "s11_reviewable_candidate_count": "0",
                "reason": s9.get("requirement", ""),
                "next_task": s9.get("next_action", ""),
                "source_paths": s9.get("source_paths", rel(SOURCE_FILES["s9_requirements"])),
            }
        )
    for qoi in TARGET_QOIS:
        c = find_by_qoi(phase_c_rows, qoi)
        rows.append(
            {
                "item": qoi,
                "item_type": "exchange_qoi",
                "current_status": c.get("admission_status", "blocked"),
                "release_allowed_now": "false",
                "s11_reviewable_candidate_count": "0",
                "reason": c.get("blocked_reason", "same-QOI UQ and source geometry blocked"),
                "next_task": c.get("next_task", ""),
                "source_paths": c.get("source_paths", rel(SOURCE_FILES["phase_c_admission_table"])),
            }
        )
    return rows


def guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_output_mutation", "allowed": "false", "observed": "false"},
        {"guardrail": "registry_or_admission_mutation", "allowed": "false", "observed": "false"},
        {"guardrail": "scheduler_action", "allowed": "false", "observed": "false"},
        {"guardrail": "solver_postprocessing_sampler_launch", "allowed": "false", "observed": "false"},
        {"guardrail": "fitting_or_model_selection", "allowed": "false", "observed": "false"},
        {"guardrail": "exchange_cell_admission", "allowed": "false", "observed": "false"},
        {"guardrail": "residual_absorption_into_internal_Nu", "allowed": "false", "observed": "false"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: {Path(__file__).name}
  generated_at: {summary["generated_at"]}
tags:
  - s13
  - upcomer-exchange
  - same-qoi-uq
  - fail-closed
related:
  - {rel(SOURCE_FILES["phase_c_admission_table"])}
  - {rel(SOURCE_FILES["geometry_downstream_inputs"])}
---

# S13 Upcomer Exchange Same-Window UQ Design

This package defines the UQ gate for S13 exchange-cell QOIs before any
production harvest can be used in an S11 candidate review.

Result: fail-closed. The retained-time evidence is not enough: each target QOI
still needs same-label neighboring windows, accepted same-QOI mesh/GCI evidence,
and trusted interface/wall/source geometry. No sampler, postprocessing, solver,
fit, score, or admission step was launched.

Primary outputs:

- `uq_acceptance_contract.csv`
- `neighbor_window_requirements.csv`
- `mesh_gci_requirements.csv`
- `qoi_release_decision.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

The next useful action is to keep this design as the gate for S13 and proceed
only to sampler manifest preflight after the surface/geometry inputs are either
released or explicitly fail-closed.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    ensure_dir(OUT)
    s9_rows = read_csv(SOURCE_FILES["s9_requirements"])
    phase_a_rows = read_csv(SOURCE_FILES["phase_a_retained_inventory"])
    phase_b_rows = read_csv(SOURCE_FILES["phase_b_mesh_gci_matrix"])
    phase_c_rows = read_csv(SOURCE_FILES["phase_c_admission_table"])
    geometry_rows = read_csv(SOURCE_FILES["geometry_downstream_inputs"])

    acceptance = uq_acceptance_contract(s9_rows, phase_a_rows, phase_b_rows, phase_c_rows, geometry_rows)
    neighbors = neighbor_window_requirements(phase_a_rows)
    mesh = mesh_gci_requirements(phase_b_rows)
    decisions = qoi_release_decision(s9_rows, phase_c_rows)
    guards = guardrails()
    sources = source_manifest()

    csv_dump(OUT / "uq_acceptance_contract.csv", list(acceptance[0]), acceptance)
    csv_dump(OUT / "neighbor_window_requirements.csv", list(neighbors[0]), neighbors)
    csv_dump(OUT / "mesh_gci_requirements.csv", list(mesh[0]), mesh)
    csv_dump(OUT / "qoi_release_decision.csv", list(decisions[0]), decisions)
    csv_dump(OUT / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(OUT / "source_manifest.csv", list(sources[0]), sources)

    summary: dict[str, Any] = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "package": rel(OUT),
        "target_qoi_count": len(TARGET_QOIS),
        "support_gate_count": len(SUPPORT_GATES),
        "blocked_target_qoi_count": len([row for row in acceptance if row["s13_acceptance_status"] == "blocked"]),
        "s11_reviewable_candidate_count": 0,
        "uq_release_allowed": False,
        "sampler_or_harvest_allowed": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_action": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    build()
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
