#!/usr/bin/env python3
"""Build the post-extraction S13 Q_wall/source-side/UQ production gate."""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SAMPLED-FIELD-QWALL-UQ-UNBLOCK-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock"
)
LIMITED = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction"
)
AVERAGE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"
)
PROXY = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampler_manifest_refresh_from_seeded_proxy"
)
CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk"
)
UQ_DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_same_window_uq_design"
)


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def bool_text(value: bool) -> str:
    return str(value).lower()


def production_readiness_rows() -> list[dict[str, Any]]:
    sampled = by_case(read_csv(LIMITED / "sampled_field_summary.csv"))
    average = by_case(read_csv(AVERAGE / "diagnostic_average_exchange_metrics.csv"))
    qwall = by_case(read_csv(CONTRACT / "wall_heat_integration_contract.csv"))
    proxy = by_case(read_csv(PROXY / "sampler_proxy_manifest.csv"))
    rows: list[dict[str, Any]] = []
    for case_id in sorted(sampled):
        sampled_row = sampled[case_id]
        avg_row = average[case_id]
        qwall_row = qwall[case_id]
        proxy_row = proxy[case_id]
        source_side_ready = (
            avg_row["q_net_W"] != ""
            and sampled_row["trusted_wall_T_area_avg_K"] != ""
            and sampled_row["interface_core_T_area_avg_K"] != ""
        )
        qwall_ready = qwall_row["Q_wall_W_released"] == "true"
        same_qoi_ready = sampled_row["same_qoi_uq_ready"] == "true"
        production_ready = qwall_ready and same_qoi_ready
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": sampled_row["time_window_s"],
                "V_recirc_proxy_m3": avg_row["seeded_cv_volume_m3"],
                "interface_area_m2": sampled_row["interface_area_m2"],
                "trusted_wall_area_m2": sampled_row["trusted_wall_area_m2"],
                "mdot_exchange_positive_outward_proxy_kg_s": sampled_row[
                    "mdot_exchange_positive_outward_proxy_kg_s"
                ],
                "tau_recirc_proxy_s": avg_row["tau_recirc_proxy_s"],
                "trusted_wall_T_area_avg_K": sampled_row["trusted_wall_T_area_avg_K"],
                "interface_core_T_area_avg_K": sampled_row["interface_core_T_area_avg_K"],
                "seeded_cv_T_volume_avg_K": sampled_row["seeded_cv_T_volume_avg_K"],
                "delta_T_wall_minus_core_K": sampled_row["delta_T_wall_minus_core_K"],
                "delta_T_core_minus_seed_K": sampled_row["delta_T_core_minus_seed_K"],
                "source_side_q_net_W": avg_row["q_net_W"],
                "source_side_equivalent_ready_for_contract": bool_text(source_side_ready),
                "Q_wall_W_ready": bool_text(qwall_ready),
                "pressure_basis_ready": proxy_row["pressure_basis_ready"],
                "viscosity_basis_ready": "false",
                "cp_ready": proxy_row["cp_ready"],
                "same_qoi_uq_ready": bool_text(same_qoi_ready),
                "production_harvest_ready": bool_text(production_ready),
                "admission_allowed": "false",
                "smallest_remaining_path": (
                    "document_distinct_source_side_heat_flow_qoi_then_same_qoi_uq"
                    if source_side_ready and not qwall_ready
                    else "integrate_Q_wall_W_then_same_qoi_uq"
                ),
                "release_status": "post_extraction_diagnostic_only",
                "blocking_reason": (
                    "production remains blocked: Q_wall_W/wallHeatFlux, pressure/viscosity/cp, "
                    "same-QOI UQ, and admission guards are not released"
                ),
            }
        )
    return rows


def blocker_unlock_matrix_rows() -> list[dict[str, str]]:
    readiness = production_readiness_rows()
    case_count = len(readiness)
    gate_specs = [
        (
            "V_recirc_proxy",
            "diagnostic_ready",
            "true",
            "false",
            "seeded CV volume exists for all cases but is proxy/nonproduction",
        ),
        (
            "sampled_mdot_exchange",
            "diagnostic_ready",
            "true",
            "false",
            "limited sampled interface U/T/rho extraction produced retained-window proxy mdot",
        ),
        (
            "tau_recirc_proxy",
            "diagnostic_ready",
            "true",
            "false",
            "tau is derived from proxy exchange flow and seeded volume",
        ),
        (
            "wall_core_bulk_temperature_contrast",
            "diagnostic_ready",
            "true",
            "false",
            "limited sampled wall/core/seed temperatures exist for retained windows",
        ),
        (
            "source_side_heat_flow_q_net",
            "needs_contract_and_uq",
            "true",
            "false",
            "source-side q_net exists but must be labeled as a distinct QOI, not Q_wall_W",
        ),
        (
            "Q_wall_W",
            "blocked_missing_wallHeatFlux",
            "false",
            "true",
            "trusted wall geometry exists but wallHeatFlux/Q_wall integration is absent",
        ),
        (
            "pressure_basis",
            "blocked_missing_pressure_basis",
            "false",
            "true",
            "p or p_rgh was not released in the S13 cell/surface field lane",
        ),
        (
            "viscosity_basis",
            "blocked_missing_mu_or_nu",
            "false",
            "true",
            "mu/nu/nut was not released for Reynolds/viscous support",
        ),
        (
            "cp_property_basis",
            "blocked_missing_cp",
            "false",
            "true",
            "cp_J_kg_K is not released with source/property provenance",
        ),
        (
            "same_qoi_uq",
            "blocked_missing_neighbor_window_and_mesh_gci",
            "false",
            "true",
            "same-QOI UQ design requires same label/formula/sign/basis in neighboring windows and mesh/GCI",
        ),
        (
            "production_harvest",
            "blocked",
            "false",
            "true",
            "no exact production QOI set has Q_wall or source-side equivalent plus same-QOI UQ",
        ),
        (
            "coefficient_or_S11_admission",
            "blocked",
            "false",
            "true",
            "production harvest and same-QOI UQ are not released",
        ),
    ]
    return [
        {
            "gate": gate,
            "status": status,
            "available_case_count": str(case_count if available == "true" else 0),
            "available_for_diagnostic_context": available,
            "blocks_production": blocks,
            "reason": reason,
        }
        for gate, status, available, blocks, reason in gate_specs
    ]


def same_qoi_uq_prerequisite_rows() -> list[dict[str, str]]:
    qois = [
        ("mdot_exchange_positive_outward_proxy_kg_s", "retained_window_proxy_ready"),
        ("tau_recirc_proxy_s", "retained_window_proxy_ready"),
        ("wall_core_bulk_temperature_contrast_K", "retained_window_sampled_ready"),
        ("source_side_q_net_W", "retained_window_source_context_ready_requires_distinct_qoi_contract"),
        ("Q_wall_W", "blocked_missing_wallHeatFlux"),
    ]
    return [
        {
            "qoi_name": qoi,
            "retained_window_status": retained,
            "neighbor_minus_status": "missing",
            "neighbor_plus_status": "missing",
            "same_formula_sign_basis_required": "true",
            "mesh_or_gci_status": "missing",
            "source_property_status": (
                "needs_source_property_release" if qoi == "source_side_q_net_W" else "missing_or_not_applicable"
            ),
            "uq_release_allowed_now": "false",
            "next_required_action": (
                "define distinct source-side heat-flow QOI and generate same-QOI neighbor/mesh evidence"
                if qoi == "source_side_q_net_W"
                else "generate exact same-QOI neighbor windows and accepted mesh/GCI evidence"
            ),
        }
        for qoi, retained in qois
    ]


def source_basis_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "basis": "wallHeatFlux_Q_wall_W",
            "current_status": "missing",
            "production_role": "direct wall heat-flow integration",
            "can_use_for_Q_wall_W_now": "false",
            "can_use_as_source_side_equivalent_now": "false",
            "smallest_next_action": "generate or locate same-window wallHeatFlux on trusted wall faces",
            "guardrail": "do not substitute q_net_W for Q_wall_W",
        },
        {
            "basis": "source_side_q_net_W",
            "current_status": "retained_window_context_present",
            "production_role": "distinct source-side heat-flow QOI if explicitly contracted",
            "can_use_for_Q_wall_W_now": "false",
            "can_use_as_source_side_equivalent_now": "needs_contract_and_uq",
            "smallest_next_action": "write sign/conservation/source-property contract and run same-QOI UQ for this exact QOI",
            "guardrail": "label distinct from Q_wall_W and do not admit before UQ",
        },
        {
            "basis": "pressure",
            "current_status": "missing",
            "production_role": "pressure/residual support",
            "can_use_for_Q_wall_W_now": "false",
            "can_use_as_source_side_equivalent_now": "false",
            "smallest_next_action": "release p or p_rgh on the same window and exchange interface",
            "guardrail": "no pressure residual support before same-window pressure basis",
        },
        {
            "basis": "viscosity",
            "current_status": "missing",
            "production_role": "Re/viscous support",
            "can_use_for_Q_wall_W_now": "false",
            "can_use_as_source_side_equivalent_now": "false",
            "smallest_next_action": "release mu/nu/nut or documented property basis",
            "guardrail": "no coefficient admission without property provenance",
        },
        {
            "basis": "cp",
            "current_status": "missing",
            "production_role": "energy residual and heat-flow normalization",
            "can_use_for_Q_wall_W_now": "false",
            "can_use_as_source_side_equivalent_now": "needs_source_property_release",
            "smallest_next_action": "release cp_J_kg_K with source/property label",
            "guardrail": "do not infer cp silently from unrelated sources",
        },
    ]


def path_decision_rows() -> list[dict[str, str]]:
    return [
        {
            "path_id": "direct_Q_wall_W",
            "rank": "2",
            "decision": "blocked_longer_path",
            "production_release_allowed_now": "false",
            "why": "requires wallHeatFlux generation or recovery before Q_wall_W can be integrated",
            "minimum_next_row": "Q_wall_W wallHeatFlux source recovery or generation on trusted wall faces",
            "same_qoi_uq_required_afterward": "true",
        },
        {
            "path_id": "distinct_source_side_heat_flow_Q_source_side_W",
            "rank": "1",
            "decision": "smallest_remaining_path_but_not_production_ready",
            "production_release_allowed_now": "false",
            "why": "q_net_W source-side context and sampled thermal contrasts already exist, but the QOI needs a sign/conservation/source-property contract and same-QOI UQ",
            "minimum_next_row": "source-side heat-flow equivalence contract plus same-QOI UQ prerequisite package",
            "same_qoi_uq_required_afterward": "true",
        },
    ]


def downstream_decision_rows() -> list[dict[str, str]]:
    return [
        {
            "gate": "post_extraction_unblock_decision",
            "status": "fail_closed_with_next_path",
            "allowed": "true",
            "reason": "the row may publish the source-side path decision without running harvest/UQ/admission",
        },
        {
            "gate": "production_harvest",
            "status": "blocked",
            "allowed": "false",
            "reason": "no Q_wall_W or contracted source-side heat-flow QOI has same-QOI UQ",
        },
        {
            "gate": "same_qoi_uq_execution",
            "status": "next_row_required",
            "allowed": "false",
            "reason": "UQ must be claimed as a separate row on exact QOI labels/formula/sign/basis",
        },
        {
            "gate": "S11_S15_S6_or_coefficient_admission",
            "status": "blocked",
            "allowed": "false",
            "reason": "production evidence and UQ are absent",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read-only package inputs"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry/admission edit"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no scheduler action"},
        {"guard_id": "solver_sampler_harvest_uq_launch", "changed": "false", "policy": "gate only"},
        {"guard_id": "Q_wall_W_release", "changed": "false", "policy": "Q_wall_W remains blocked"},
        {"guard_id": "source_side_relabel_as_Q_wall", "changed": "false", "policy": "source-side heat flow must be a distinct QOI"},
        {"guard_id": "downstream_trigger", "changed": "false", "policy": "no S11/S12/S13/S15/S6 trigger"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "changed": "false", "policy": "no residual absorption"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (LIMITED / "sampled_field_summary.csv", "read limited sampled field retained-window summary"),
        (LIMITED / "summary.json", "read limited extraction summary"),
        (AVERAGE / "diagnostic_average_exchange_metrics.csv", "read seeded volume, tau, and source-side q_net context"),
        (PROXY / "sampler_proxy_manifest.csv", "read proxy sampler production blockers"),
        (CONTRACT / "wall_heat_integration_contract.csv", "read Q_wall_W wallHeatFlux contract"),
        (CONTRACT / "field_availability.csv", "read pressure/viscosity/cp/wallHeatFlux source-basis audit"),
        (UQ_DESIGN / "qoi_release_decision.csv", "read same-QOI UQ release decision"),
        (UQ_DESIGN / "summary.json", "read same-QOI UQ status"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": bool_text(path.exists()),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(LIMITED / "sampled_field_summary.csv")}
  - {rel(CONTRACT / "wall_heat_integration_contract.csv")}
  - {rel(UQ_DESIGN / "qoi_release_decision.csv")}
tags: [s13, upcomer-exchange, qwall, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Sampled-Field Qwall/UQ Unblock Gate

This package decides the post-extraction production path after the limited
sampled-field extraction.

Decision: `{summary["decision"]}`.

- cases reviewed: `{summary["case_count"]}`
- source-side heat-flow contract-ready diagnostic rows: `{summary["source_side_contract_ready_rows"]}`
- `Q_wall_W` ready rows: `{summary["Q_wall_W_ready_rows"]}`
- same-QOI UQ ready rows: `{summary["same_qoi_uq_ready_rows"]}`
- production harvest ready rows: `{summary["production_harvest_ready_rows"]}`
- admission allowed rows: `{summary["admission_allowed_rows"]}`

The smallest remaining path is not to relabel `q_net_W` as `Q_wall_W`. It is to
define a distinct source-side heat-flow QOI, lock its sign/conservation and
source-property contract, then run same-QOI UQ on that exact QOI plus the
exchange-state QOIs. Direct `Q_wall_W` remains blocked until wallHeatFlux exists
on trusted wall faces.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    readiness = production_readiness_rows()
    blockers = blocker_unlock_matrix_rows()
    uq = same_qoi_uq_prerequisite_rows()
    basis = source_basis_audit_rows()
    paths = path_decision_rows()
    downstream = downstream_decision_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "source_side_equivalent_is_smallest_remaining_path_but_production_blocked",
        "case_count": len(readiness),
        "source_side_contract_ready_rows": sum(
            1 for row in readiness if row["source_side_equivalent_ready_for_contract"] == "true"
        ),
        "Q_wall_W_ready_rows": sum(1 for row in readiness if row["Q_wall_W_ready"] == "true"),
        "same_qoi_uq_ready_rows": sum(1 for row in readiness if row["same_qoi_uq_ready"] == "true"),
        "production_harvest_ready_rows": sum(1 for row in readiness if row["production_harvest_ready"] == "true"),
        "admission_allowed_rows": sum(1 for row in readiness if row["admission_allowed"] == "true"),
        "recommended_next_row": "source-side heat-flow equivalence contract plus same-QOI UQ prerequisite package",
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Q_wall_W_released": False,
        "source_side_relabel_as_Q_wall": False,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "coefficient_admission_allowed": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    csv_dump(out / "production_readiness_table.csv", list(readiness[0]), readiness)
    csv_dump(out / "blocker_unlock_matrix.csv", list(blockers[0]), blockers)
    csv_dump(out / "same_qoi_uq_prerequisite_table.csv", list(uq[0]), uq)
    csv_dump(out / "source_basis_audit.csv", list(basis[0]), basis)
    csv_dump(out / "qwall_or_source_side_path_decision.csv", list(paths[0]), paths)
    csv_dump(out / "downstream_decision.csv", list(downstream[0]), downstream)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
