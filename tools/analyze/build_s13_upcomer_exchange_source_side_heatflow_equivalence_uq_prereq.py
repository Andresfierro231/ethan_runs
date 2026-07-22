#!/usr/bin/env python3
"""Build the S13 source-side heat-flow equivalence/UQ prerequisite package."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SOURCE-SIDE-HEATFLOW-EQUIVALENCE-UQ-PREREQ-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq"
UNBLOCK = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock"
AVERAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"
LIMITED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction"
QWALL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release"
CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk"
UQ_DESIGN = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design"

DECISION = "contract_defined_same_qoi_uq_prereq_blocked_no_production_release"
CLAIM_BOUNDARY = "read-only source-side QOI contract; no Q_wall_W relabel; no UQ execution; no admission"
QOI_LABEL = "Q_source_side_net_static_bc_W"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def bool_text(value: bool) -> str:
    return str(value).lower()


def source_side_qoi_contract() -> list[dict[str, object]]:
    return [
        {
            "qoi_label": QOI_LABEL,
            "qoi_role": "distinct source-side heat-flow support for S13 exchange-cell diagnostics",
            "formula": "Q_source_side_net_static_bc_W = Q_source_static_bc_W - Q_sink_static_bc_W over the released source/sink support for the same retained window",
            "sign_convention": "positive adds heat to the seeded recirculation/exchange control volume fluid",
            "units": "W",
            "not_a_substitute_for": "Q_wall_W",
            "source_side_relabel_as_Q_wall": "false",
            "current_contract_status": "defined_as_distinct_qoi_not_released_for_production",
            "source_property_release_allowed_now": "false",
            "same_qoi_uq_required": "true",
            "production_use_allowed_now": "false",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    ]


def case_heatflow_equivalence_basis() -> list[dict[str, object]]:
    readiness = by_case(read_csv(UNBLOCK / "production_readiness_table.csv"))
    average = by_case(read_csv(AVERAGE / "diagnostic_average_exchange_metrics.csv"))
    qwall = by_case(read_csv(QWALL / "qwall_contract.csv"))
    limited = by_case(read_csv(LIMITED / "sampled_field_summary.csv"))
    rows: list[dict[str, object]] = []
    for case_id in sorted(readiness):
        avg = average[case_id]
        qw = qwall[case_id]
        lim = limited[case_id]
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": readiness[case_id]["time_window_s"],
                QOI_LABEL: avg["q_net_W"],
                "Q_source_static_bc_W": avg["q_source_W"],
                "Q_sink_static_bc_W": avg["q_sink_W"],
                "source_minus_sink_closure": "Q_source_static_bc_W_minus_Q_sink_static_bc_W",
                "trusted_wall_T_area_avg_K": lim["trusted_wall_T_area_avg_K"],
                "interface_core_T_area_avg_K": lim["interface_core_T_area_avg_K"],
                "delta_T_wall_minus_core_K": lim["delta_T_wall_minus_core_K"],
                "Q_wall_W_released": qw["Q_wall_W_released"],
                "wall_heat_flux_available": qw["wallHeatFlux_source_exists"],
                "source_side_context_ready": "true",
                "source_property_release_allowed_now": "false",
                "same_qoi_uq_ready": "false",
                "production_release_allowed_now": "false",
                "reason": "finite retained-window source-side heat context exists, but source/property release and same-QOI UQ are missing",
                "source_path": qw["source_path"],
            }
        )
    return rows


def conservation_source_property_prerequisites() -> list[dict[str, object]]:
    return [
        {
            "gate_id": "SRC-01",
            "gate": "distinct_qoi_label_and_formula",
            "status": "pass",
            "release_allowed_now": "false",
            "evidence": "Q_source_side_net_static_bc_W is defined separately from Q_wall_W using Q_source_static_bc_W - Q_sink_static_bc_W",
            "next_required": "carry this exact label/formula into same-QOI UQ rows",
        },
        {
            "gate_id": "SRC-02",
            "gate": "sign_and_conservation_basis",
            "status": "partial",
            "release_allowed_now": "false",
            "evidence": "positive sign convention is documented, but source/sink conservation still needs source/property release",
            "next_required": "publish source-term provenance and conservation checks for the retained windows",
        },
        {
            "gate_id": "SRC-03",
            "gate": "source_property_basis",
            "status": "fail",
            "release_allowed_now": "false",
            "evidence": "cp/source-property basis is not released for production heat-flow closure",
            "next_required": "release cp_J_kg_K, source validity envelope, and source use category",
        },
        {
            "gate_id": "SRC-04",
            "gate": "same_qoi_neighbor_windows",
            "status": "fail",
            "release_allowed_now": "false",
            "evidence": "neighbor-minus and neighbor-plus windows are missing for Q_source_side_net_static_bc_W",
            "next_required": "generate same-label, same-formula, same-sign neighbor-window values",
        },
        {
            "gate_id": "SRC-05",
            "gate": "mesh_or_gci_basis",
            "status": "fail",
            "release_allowed_now": "false",
            "evidence": "accepted mesh/GCI evidence is absent for Q_source_side_net_static_bc_W",
            "next_required": "pair retained-window and neighbor-window values with accepted mesh/GCI evidence",
        },
        {
            "gate_id": "SRC-06",
            "gate": "overall_source_side_release",
            "status": "blocked",
            "release_allowed_now": "false",
            "evidence": "contract exists, but source/property release and same-QOI UQ remain missing",
            "next_required": "claim a compute/source row only after exact QOI/UQ inputs are ready",
        },
    ]


def same_qoi_uq_requirement_matrix() -> list[dict[str, object]]:
    existing = {row["qoi_name"]: row for row in read_csv(UNBLOCK / "same_qoi_uq_prerequisite_table.csv")}
    qois = [
        (QOI_LABEL, "retained_window_source_context_ready_distinct_qoi_contract"),
        ("mdot_exchange_positive_outward_proxy_kg_s", existing["mdot_exchange_positive_outward_proxy_kg_s"]["retained_window_status"]),
        ("tau_recirc_proxy_s", existing["tau_recirc_proxy_s"]["retained_window_status"]),
        ("wall_core_bulk_temperature_contrast_K", existing["wall_core_bulk_temperature_contrast_K"]["retained_window_status"]),
    ]
    rows: list[dict[str, object]] = []
    for qoi, status in qois:
        rows.append(
            {
                "qoi_name": qoi,
                "retained_window_status": status,
                "neighbor_minus_status": "missing",
                "neighbor_plus_status": "missing",
                "same_formula_sign_basis_required": "true",
                "mesh_or_gci_status": "missing",
                "source_property_status": "needs_source_property_release" if qoi == QOI_LABEL else "not_applicable_or_missing",
                "uq_release_allowed_now": "false",
                "production_use_allowed_now": "false",
                "next_required_action": "generate same-QOI neighbor windows and accepted mesh/GCI evidence before production use",
            }
        )
    return rows


def production_admission_gate() -> list[dict[str, object]]:
    return [
        {
            "gate": "source_side_contract_publication",
            "status": "pass",
            "allowed": "true",
            "reason": "the package may publish Q_source_side_net_static_bc_W as a distinct, nonproduction QOI contract",
        },
        {
            "gate": "source_property_release",
            "status": "blocked",
            "allowed": "false",
            "reason": "source validity, source use category, and cp/property basis are not released",
        },
        {
            "gate": "same_qoi_uq_execution",
            "status": "blocked",
            "allowed": "false",
            "reason": "neighbor windows and mesh/GCI evidence are absent",
        },
        {
            "gate": "production_harvest",
            "status": "blocked",
            "allowed": "false",
            "reason": "Q_source_side_net_static_bc_W is contracted but not source/property/UQ released",
        },
        {
            "gate": "coefficient_or_s11_s15_s6_admission",
            "status": "blocked",
            "allowed": "false",
            "reason": "production evidence and UQ are absent",
        },
    ]


def s11_s15_s6_consequence() -> list[dict[str, object]]:
    return [
        {
            "decision_id": "S13-SOURCE-SIDE-UQ-PREREQ",
            "s11_unblocked": "false",
            "s12_unblocked": "false",
            "s13_unblocked": "false",
            "s15_unblocked": "false",
            "s6_unblocked": "false",
            "decision": DECISION,
            "candidate_count_released": 0,
            "rationale": "Q_source_side_net_static_bc_W contract is defined, but no source/property release, same-QOI UQ, production harvest, or coefficient admission exists.",
        }
    ]


def no_mutation_guardrails() -> list[dict[str, object]]:
    return [
        {"guardrail": "native_output_mutation", "value": "false"},
        {"guardrail": "registry_or_admission_mutation", "value": "false"},
        {"guardrail": "scheduler_action", "value": "false"},
        {"guardrail": "solver_sampler_harvest_uq_launched", "value": "false"},
        {"guardrail": "Q_wall_W_released", "value": "false"},
        {"guardrail": "source_side_relabel_as_Q_wall", "value": "false"},
        {"guardrail": "source_property_release", "value": "false"},
        {"guardrail": "coefficient_admission_allowed", "value": "false"},
        {"guardrail": "s11_s12_s13_s15_s6_trigger", "value": "false"},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": "false"},
    ]


def source_manifest() -> list[dict[str, object]]:
    paths = [
        (UNBLOCK / "production_readiness_table.csv", "source-side readiness and current blockers"),
        (UNBLOCK / "same_qoi_uq_prerequisite_table.csv", "existing same-QOI prerequisite rows"),
        (AVERAGE / "diagnostic_average_exchange_metrics.csv", "q_source/q_sink/q_net retained-window context"),
        (LIMITED / "sampled_field_summary.csv", "sampled retained-window temperature and exchange context"),
        (QWALL / "qwall_contract.csv", "Q_wall versus source-side distinction"),
        (CONTRACT / "sign_cp_convention_contract.csv", "sign and cp release status"),
        (UQ_DESIGN / "qoi_release_decision.csv", "same-window UQ design status"),
    ]
    return [
        {
            "path": str(path.relative_to(ROOT)),
            "role": role,
            "exists": path.exists(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock/production_readiness_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/diagnostic_average_exchange_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release/qwall_contract.csv
tags: [s13, upcomer-exchange, source-side-heatflow, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Source-Side Heat-Flow Equivalence UQ Prerequisite

Decision: `{summary["decision"]}`.

This package defines `Q_source_side_net_static_bc_W` as a distinct source-side
heat-flow QOI: `Q_source_static_bc_W - Q_sink_static_bc_W`, positive when heat
is added to the seeded recirculation/exchange control-volume fluid.

It does not release `Q_wall_W`, does not relabel source-side context as wall
heat, does not execute same-QOI UQ, and does not open production harvest or
admission.

## Outputs

- `source_side_qoi_contract.csv`
- `case_heatflow_equivalence_basis.csv`
- `conservation_source_property_prerequisites.csv`
- `same_qoi_uq_requirement_matrix.csv`
- `production_admission_gate.csv`
- `s11_s15_s6_consequence.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    case_rows = case_heatflow_equivalence_basis()
    same_qoi_rows = same_qoi_uq_requirement_matrix()
    gate_rows = production_admission_gate()
    summary = {
        "task_id": TASK_ID,
        "status": "complete",
        "decision": DECISION,
        "case_count": len(case_rows),
        "source_side_contract_rows": 1,
        "case_heatflow_rows": len(case_rows),
        "same_qoi_requirement_rows": len(same_qoi_rows),
        "Q_source_side_net_static_bc_W_defined": True,
        "Q_wall_W_released": False,
        "source_side_relabel_as_Q_wall": False,
        "source_property_release": False,
        "same_qoi_uq_executed": False,
        "same_qoi_uq_release_allowed": False,
        "production_harvest_allowed": False,
        "coefficient_admission_allowed": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "residual_absorbed_into_internal_nu": False,
    }
    write_csv(OUT / "source_side_qoi_contract.csv", source_side_qoi_contract(), ["qoi_label", "qoi_role", "formula", "sign_convention", "units", "not_a_substitute_for", "source_side_relabel_as_Q_wall", "current_contract_status", "source_property_release_allowed_now", "same_qoi_uq_required", "production_use_allowed_now", "claim_boundary"])
    write_csv(OUT / "case_heatflow_equivalence_basis.csv", case_rows, ["case_id", "time_window_s", QOI_LABEL, "Q_source_static_bc_W", "Q_sink_static_bc_W", "source_minus_sink_closure", "trusted_wall_T_area_avg_K", "interface_core_T_area_avg_K", "delta_T_wall_minus_core_K", "Q_wall_W_released", "wall_heat_flux_available", "source_side_context_ready", "source_property_release_allowed_now", "same_qoi_uq_ready", "production_release_allowed_now", "reason", "source_path"])
    write_csv(OUT / "conservation_source_property_prerequisites.csv", conservation_source_property_prerequisites(), ["gate_id", "gate", "status", "release_allowed_now", "evidence", "next_required"])
    write_csv(OUT / "same_qoi_uq_requirement_matrix.csv", same_qoi_rows, ["qoi_name", "retained_window_status", "neighbor_minus_status", "neighbor_plus_status", "same_formula_sign_basis_required", "mesh_or_gci_status", "source_property_status", "uq_release_allowed_now", "production_use_allowed_now", "next_required_action"])
    write_csv(OUT / "production_admission_gate.csv", gate_rows, ["gate", "status", "allowed", "reason"])
    write_csv(OUT / "s11_s15_s6_consequence.csv", s11_s15_s6_consequence(), ["decision_id", "s11_unblocked", "s12_unblocked", "s13_unblocked", "s15_unblocked", "s6_unblocked", "decision", "candidate_count_released", "rationale"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation_guardrails(), ["guardrail", "value"])
    write_csv(OUT / "source_manifest.csv", source_manifest(), ["path", "role", "exists", "native_solver_output", "mutated"])
    write_json(OUT / "summary.json", summary)
    write_readme(summary)


if __name__ == "__main__":
    main()
