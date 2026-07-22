#!/usr/bin/env python3
"""Build the S13 source-side conservation, neighbor-window, and UQ gate."""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SOURCE-SIDE-CONSERVATION-NEIGHBOR-UQ-GATE-2026-07-22"
QOI_LABEL = "Q_source_side_net_static_bc_W"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate"
)
SOURCE_SIDE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq"
)
UNBLOCK = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock"
)
UQ_DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_same_window_uq_design"
)
EXACT_QWALL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
)


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def bool_text(value: bool) -> str:
    return str(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return read_json(path)


def existing_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [item for item in path.rglob("*") if item.is_file()]


def qoi_contract_row() -> dict[str, str]:
    rows = read_csv(SOURCE_SIDE / "source_side_qoi_contract.csv")
    if len(rows) != 1:
        raise RuntimeError("expected exactly one source-side QOI contract row")
    return rows[0]


def case_basis_rows() -> list[dict[str, str]]:
    return read_csv(SOURCE_SIDE / "case_heatflow_equivalence_basis.csv")


def prereq_rows() -> list[dict[str, str]]:
    return read_csv(SOURCE_SIDE / "conservation_source_property_prerequisites.csv")


def source_side_uq_requirement_rows() -> list[dict[str, str]]:
    return read_csv(SOURCE_SIDE / "same_qoi_uq_requirement_matrix.csv")


def exact_qwall_status_rows() -> list[dict[str, str]]:
    files = existing_files(EXACT_QWALL)
    summary = optional_json(EXACT_QWALL / "summary.json")
    qwall_rows = str(summary.get("Q_wall_W_released_rows", summary.get("Q_wall_W_ready_rows", 0))) if summary else "0"
    pressure_rows = (
        str(summary.get("pressure_basis_released_rows", summary.get("pressure_basis_ready_rows", 0)))
        if summary
        else "0"
    )
    status = "completed_outputs_present" if files else "active_or_empty_no_outputs"
    return [
        {
            "path": rel(EXACT_QWALL),
            "file_count": str(len(files)),
            "status": status,
            "Q_wall_W_ready_rows": qwall_rows,
            "pressure_basis_ready_rows": pressure_rows,
            "consume_for_production_gate": bool_text(bool(files) and qwall_rows != "0"),
            "decision": (
                "direct_Q_wall_W_path_available_read_only"
                if bool(files) and qwall_rows != "0"
                else "direct_Q_wall_W_path_unavailable_continue_source_side_fail_closed"
            ),
        }
    ]


def source_property_conservation_release_rows() -> list[dict[str, str]]:
    contract = qoi_contract_row()
    prereqs = {row["gate_id"]: row for row in prereq_rows()}
    rows: list[dict[str, str]] = []
    for basis in case_basis_rows():
        arithmetic_ready = basis["source_side_context_ready"] == "true"
        source_property_ready = basis["source_property_release_allowed_now"] == "true"
        residual_ready = (
            prereqs["SRC-02"]["status"] == "pass"
            and prereqs["SRC-03"]["status"] == "pass"
            and source_property_ready
        )
        release_ready = arithmetic_ready and residual_ready
        rows.append(
            {
                "case_id": basis["case_id"],
                "time_window_s": basis["time_window_s"],
                "qoi_label": contract["qoi_label"],
                "formula": contract["formula"],
                "sign_convention": contract["sign_convention"],
                "Q_source_static_bc_W": basis["Q_source_static_bc_W"],
                "Q_sink_static_bc_W": basis["Q_sink_static_bc_W"],
                "Q_source_side_net_static_bc_W": basis["Q_source_side_net_static_bc_W"],
                "arithmetic_source_sink_status": "pass" if arithmetic_ready else "fail",
                "cp_J_kg_K_status": "missing",
                "source_validity_envelope_status": "missing",
                "source_use_category_status": "missing",
                "pressure_enthalpy_basis_status": "missing",
                "energy_residual_equation_status": "defined_placeholder_not_released",
                "source_property_release_allowed_now": "false",
                "conservation_release_allowed_now": bool_text(release_ready),
                "production_release_allowed_now": "false",
                "next_required_action": (
                    "release cp_J_kg_K, source validity envelope, source use category, "
                    "pressure/enthalpy basis, and residual equation sign before production use"
                ),
            }
        )
    return rows


def neighbor_window_inventory_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for requirement in source_side_uq_requirement_rows():
        qoi = requirement["qoi_name"]
        retained_status = requirement["retained_window_status"]
        rows.append(
            {
                "qoi_label": qoi,
                "target_case_count": str(len(case_basis_rows())),
                "target_window_status": retained_status,
                "neighbor_minus_window_status": requirement["neighbor_minus_status"],
                "neighbor_plus_window_status": requirement["neighbor_plus_status"],
                "same_label_formula_sign_basis": requirement["same_formula_sign_basis_required"],
                "neighbor_window_values_generated_now": "false",
                "release_allowed_now": "false",
                "reason": (
                    "retained target context exists but exact same-label neighbor windows are missing"
                    if retained_status.startswith("retained")
                    else "retained target QOI is not fully defined"
                ),
                "next_required_action": requirement["next_required_action"],
            }
        )
    return rows


def same_qoi_uq_matrix_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in neighbor_window_inventory_rows():
        mesh_status = "missing"
        source_status = (
            "needs_source_property_release"
            if item["qoi_label"] in {QOI_LABEL, "E_source_side_residual_W"}
            else "not_applicable_or_missing"
        )
        uq_ready = (
            item["neighbor_minus_window_status"] == "ready"
            and item["neighbor_plus_window_status"] == "ready"
            and mesh_status == "ready"
            and source_status not in {"needs_source_property_release"}
        )
        rows.append(
            {
                "qoi_label": item["qoi_label"],
                "target_window_status": item["target_window_status"],
                "neighbor_minus_window_status": item["neighbor_minus_window_status"],
                "neighbor_plus_window_status": item["neighbor_plus_window_status"],
                "same_qoi_mesh_gci_status": mesh_status,
                "source_property_status": source_status,
                "same_formula_sign_basis_required": item["same_label_formula_sign_basis"],
                "same_qoi_uq_ready": bool_text(uq_ready),
                "production_use_allowed_now": "false",
                "blocking_reason": (
                    "missing exact same-QOI neighbor windows, same-QOI mesh/GCI, and/or source-property release"
                ),
            }
        )
    return rows


def production_readiness_gate_rows() -> list[dict[str, str]]:
    conservation = source_property_conservation_release_rows()
    uq = same_qoi_uq_matrix_rows()
    exact = exact_qwall_status_rows()[0]
    source_heat_ready = any(row["conservation_release_allowed_now"] == "true" for row in conservation)
    qoi_uq_ready = all(row["same_qoi_uq_ready"] == "true" for row in uq)
    direct_qwall_ready = exact["consume_for_production_gate"] == "true"
    pressure_ready = exact["pressure_basis_ready_rows"] != "0"
    gates = [
        (
            "source_side_heat_flow_basis",
            "blocked_missing_source_property_conservation",
            source_heat_ready,
            "source-side QOI is labeled and finite but not source/property or conservation released",
        ),
        (
            "direct_Q_wall_W_basis",
            "blocked_or_unavailable",
            direct_qwall_ready,
            (
                "active exact-Qwall row released target-window Q_wall_W read-only"
                if direct_qwall_ready
                else "active exact-Qwall row has no consumable completed Q_wall_W output"
            ),
        ),
        (
            "exchange_flux",
            "diagnostic_proxy_only",
            False,
            "retained-window mdot proxy exists but neighbor/UQ and production release are absent",
        ),
        (
            "residence_time",
            "diagnostic_proxy_only",
            False,
            "retained-window tau proxy exists but neighbor/UQ and production release are absent",
        ),
        (
            "thermal_contrast",
            "diagnostic_ready_not_uq_released",
            False,
            "retained sampled wall/core contrast exists but no same-QOI UQ",
        ),
        (
            "pressure_energy_residual_support",
            "partial_pressure_released_cp_residual_blocked",
            False,
            (
                "target-window pressure basis is released but cp/source-property and energy residual "
                "equation release are absent"
                if pressure_ready
                else "pressure/enthalpy/cp and residual equation release are absent"
            ),
        ),
        (
            "same_qoi_uq",
            "blocked_missing_neighbor_windows_and_mesh_gci",
            qoi_uq_ready,
            "same-QOI UQ matrix has no ready rows",
        ),
        (
            "production_harvest",
            "blocked",
            False,
            (
                "target-window heat-flow basis exists, but same-QOI UQ and residual/source-property release are missing"
                if direct_qwall_ready
                else "no released heat-flow basis plus same-QOI UQ exists"
            ),
        ),
        (
            "coefficient_or_S11_admission",
            "blocked",
            False,
            "production harvest is blocked; no candidate/admission trigger allowed",
        ),
    ]
    return [
        {
            "gate": gate,
            "status": status if not ready else "ready",
            "release_allowed_now": bool_text(ready),
            "production_harvest_allowed_now": "false",
            "reason": reason,
        }
        for gate, status, ready, reason in gates
    ]


def harvest_admission_decision_rows() -> list[dict[str, str]]:
    return [
        {
            "decision_id": "S13_production_harvest",
            "decision": "do_not_run",
            "allowed_now": "false",
            "reason": "production gate did not release heat-flow, pressure/energy residual support, or same-QOI UQ",
            "next_row": "source/property and neighbor-window generation for exact source-side QOI, or consume completed exact-Qwall row if it lands",
        },
        {
            "decision_id": "S13_clean_negative_result",
            "decision": "available_if_no_new_inputs_land",
            "allowed_now": "true",
            "reason": "current retained-window evidence supports a documented blocked/diagnostic result without overclaiming",
            "next_row": "thesis evidence synthesis can cite this fail-closed gate",
        },
    ]


def step_sequence_rows() -> list[dict[str, str]]:
    return [
        {
            "step": "source_property_conservation_release",
            "status": "executed_fail_closed",
            "output": "source_property_conservation_release.csv",
        },
        {
            "step": "same_label_neighbor_window_inventory",
            "status": "executed_missing_neighbors",
            "output": "neighbor_window_inventory.csv",
        },
        {
            "step": "same_qoi_uq_matrix",
            "status": "executed_fail_closed",
            "output": "same_qoi_uq_matrix.csv",
        },
        {
            "step": "production_readiness_gate",
            "status": "executed_blocked",
            "output": "production_readiness_gate.csv",
        },
        {
            "step": "harvest_admission_decision",
            "status": "do_not_run_harvest",
            "output": "harvest_admission_decision.csv",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read-only completed artifacts"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry/admission edit"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no scheduler action"},
        {"guard_id": "solver_sampler_harvest_uq_launch", "changed": "false", "policy": "gate only"},
        {"guard_id": "Q_wall_W_release", "changed": "false", "policy": "not released by this row"},
        {"guard_id": "source_property_release", "changed": "false", "policy": "requirements only"},
        {"guard_id": "source_side_relabel_as_Q_wall", "changed": "false", "policy": "forbidden"},
        {"guard_id": "S11_S12_S13_S15_S6_trigger", "changed": "false", "policy": "forbidden"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "changed": "false", "policy": "forbidden"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (SOURCE_SIDE / "source_side_qoi_contract.csv", "read exact source-side QOI label/formula/sign"),
        (SOURCE_SIDE / "case_heatflow_equivalence_basis.csv", "read retained-window case heat-flow basis"),
        (SOURCE_SIDE / "conservation_source_property_prerequisites.csv", "read conservation/source-property blockers"),
        (SOURCE_SIDE / "same_qoi_uq_requirement_matrix.csv", "read source-side same-QOI requirements"),
        (UNBLOCK / "production_readiness_table.csv", "read prior post-extraction readiness"),
        (UQ_DESIGN / "neighbor_window_requirements.csv", "read same-window UQ design"),
        (EXACT_QWALL, "read-only check for active exact pressure/Qwall outputs"),
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
  - {rel(SOURCE_SIDE / "source_side_qoi_contract.csv")}
  - {rel(SOURCE_SIDE / "case_heatflow_equivalence_basis.csv")}
  - {rel(SOURCE_SIDE / "same_qoi_uq_requirement_matrix.csv")}
tags: [s13, upcomer-exchange, source-side-heat-flow, same-qoi-uq, production-gate, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Source-Side Conservation / Neighbor / UQ Gate

Decision: `{summary["decision"]}`.

This package executes the remaining source-side path gates from existing
evidence only. It preserves the exact source-side label `{QOI_LABEL}`, consumes
the exact pressure/Qwall package read-only when present, and keeps
source/property release, same-QOI UQ, production harvest, and admission closed.

- source/property conservation release rows: `{summary["source_property_conservation_rows"]}`
- conservation release-ready rows: `{summary["conservation_release_ready_rows"]}`
- neighbor-window QOI rows: `{summary["neighbor_window_qoi_rows"]}`
- same-QOI UQ ready rows: `{summary["same_qoi_uq_ready_rows"]}`
- production-ready gates: `{summary["production_ready_gate_rows"]}`
- harvest decision: `do_not_run`

The exact pressure/Qwall competing path was checked read-only. It had
`{summary["exact_qwall_file_count"]}` files and `{summary["exact_qwall_ready_rows"]}`
ready `Q_wall_W` rows at package build time. Exact pressure basis rows available:
`{summary["exact_pressure_basis_ready_rows"]}`.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    conservation = source_property_conservation_release_rows()
    neighbors = neighbor_window_inventory_rows()
    uq = same_qoi_uq_matrix_rows()
    production = production_readiness_gate_rows()
    harvest = harvest_admission_decision_rows()
    exact = exact_qwall_status_rows()
    steps = step_sequence_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "source_side_path_executed_fail_closed_production_harvest_not_ready",
        "qoi_label": QOI_LABEL,
        "source_property_conservation_rows": len(conservation),
        "conservation_release_ready_rows": sum(
            1 for row in conservation if row["conservation_release_allowed_now"] == "true"
        ),
        "neighbor_window_qoi_rows": len(neighbors),
        "neighbor_window_ready_rows": sum(
            1
            for row in neighbors
            if row["neighbor_minus_window_status"] == "ready" and row["neighbor_plus_window_status"] == "ready"
        ),
        "same_qoi_uq_ready_rows": sum(1 for row in uq if row["same_qoi_uq_ready"] == "true"),
        "production_ready_gate_rows": sum(1 for row in production if row["release_allowed_now"] == "true"),
        "harvest_allowed": False,
        "admission_allowed": False,
        "exact_qwall_file_count": int(exact[0]["file_count"]),
        "exact_qwall_ready_rows": int(exact[0]["Q_wall_W_ready_rows"]),
        "exact_pressure_basis_ready_rows": int(exact[0]["pressure_basis_ready_rows"]),
        "exact_qwall_inputs_released_read_only": exact[0]["consume_for_production_gate"] == "true",
        "Q_wall_W_released": False,
        "source_property_release": False,
        "source_side_relabel_as_Q_wall": False,
        "same_qoi_uq_executed": False,
        "production_harvest_launched": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "residual_absorbed_into_internal_nu": False,
    }
    csv_dump(out / "source_property_conservation_release.csv", list(conservation[0]), conservation)
    csv_dump(out / "neighbor_window_inventory.csv", list(neighbors[0]), neighbors)
    csv_dump(out / "same_qoi_uq_matrix.csv", list(uq[0]), uq)
    csv_dump(out / "production_readiness_gate.csv", list(production[0]), production)
    csv_dump(out / "harvest_admission_decision.csv", list(harvest[0]), harvest)
    csv_dump(out / "exact_qwall_competing_path_status.csv", list(exact[0]), exact)
    csv_dump(out / "step_sequence_status.csv", list(steps[0]), steps)
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
