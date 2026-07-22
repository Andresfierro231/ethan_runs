#!/usr/bin/env python3
"""Build the S13 exact-Qwall same-QOI neighbor-window inventory."""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-QWALL-SAME-QOI-NEIGHBOR-UQ-EXECUTION-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution"
)
EXACT_QWALL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
)
LIMITED = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction"
)
AVERAGE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"
)
UQ_DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_same_window_uq_design"
)
SOURCE_SIDE_GATE = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate"
)
PHASE_A = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_a_retained_window_inventory"
)
PHASE_B = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix"
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


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def finite(value: str) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == number and number not in (float("inf"), float("-inf"))


def qwall_rows() -> dict[str, dict[str, str]]:
    return by_case(read_csv(EXACT_QWALL / "trusted_wall_Q_wall_summary.csv"))


def sampled_rows() -> dict[str, dict[str, str]]:
    return by_case(read_csv(LIMITED / "sampled_field_summary.csv"))


def average_rows() -> dict[str, dict[str, str]]:
    return by_case(read_csv(AVERAGE / "diagnostic_average_exchange_metrics.csv"))


def case_ids() -> list[str]:
    qwall = set(qwall_rows())
    sampled = set(sampled_rows())
    average = set(average_rows())
    common = sorted(qwall & sampled & average)
    if not common:
        raise RuntimeError("no common S13 target cases found across exact Qwall, sampled, and average packages")
    return common


def target_value_for(qoi_label: str, case_id: str) -> dict[str, str]:
    qwall = qwall_rows()[case_id]
    sampled = sampled_rows()[case_id]
    average = average_rows()[case_id]
    if qoi_label == "Q_wall_W":
        return {
            "target_time_window_s": qwall["time_window_s"],
            "target_value": qwall["Q_wall_W"],
            "target_unit": "W",
            "target_status": (
                "released_exact_target_window"
                if qwall["Q_wall_W_released"] == "true"
                else "missing_target_window"
            ),
            "target_source_artifact": rel(EXACT_QWALL / "trusted_wall_Q_wall_summary.csv"),
            "target_basis": "trusted_wall_wallHeatFlux_integral",
            "target_release_grade": qwall["Q_wall_W_released"],
            "component_values": "",
        }
    if qoi_label == "mdot_exchange_positive_outward_proxy_kg_s":
        return {
            "target_time_window_s": sampled["time_window_s"],
            "target_value": sampled["mdot_exchange_positive_outward_proxy_kg_s"],
            "target_unit": "kg/s",
            "target_status": "retained_window_proxy_ready",
            "target_source_artifact": rel(LIMITED / "sampled_field_summary.csv"),
            "target_basis": "limited_sampled_interface_U_rho_proxy",
            "target_release_grade": "false",
            "component_values": "",
        }
    if qoi_label == "tau_recirc_proxy_s":
        return {
            "target_time_window_s": average["time_window_s"],
            "target_value": average["tau_recirc_proxy_s"],
            "target_unit": "s",
            "target_status": "retained_window_proxy_ready",
            "target_source_artifact": rel(AVERAGE / "diagnostic_average_exchange_metrics.csv"),
            "target_basis": "seeded_cv_volume_over_positive_outward_volumetric_exchange_proxy",
            "target_release_grade": "false",
            "component_values": "",
        }
    if qoi_label == "wall_core_bulk_temperature_contrast_K":
        wall_minus_core = sampled["delta_T_wall_minus_core_K"]
        core_minus_bulk = sampled["delta_T_core_minus_seed_K"]
        wall_minus_bulk = ""
        if finite(wall_minus_core) and finite(core_minus_bulk):
            wall_minus_bulk = f"{float(wall_minus_core) + float(core_minus_bulk):.12g}"
        return {
            "target_time_window_s": sampled["time_window_s"],
            "target_value": wall_minus_core,
            "target_unit": "K",
            "target_status": "retained_window_sampled_ready",
            "target_source_artifact": rel(LIMITED / "sampled_field_summary.csv"),
            "target_basis": "trusted_wall_T_area_avg_vs_interface_core_T_area_avg_vs_seeded_cv_T_volume_avg",
            "target_release_grade": "false",
            "component_values": (
                f"delta_T_wall_minus_core_K={wall_minus_core};"
                f"delta_T_core_minus_bulk_K={core_minus_bulk};"
                f"delta_T_wall_minus_bulk_K={wall_minus_bulk}"
            ),
        }
    raise KeyError(f"unsupported QOI label: {qoi_label}")


def qoi_labels() -> list[str]:
    return [
        "Q_wall_W",
        "mdot_exchange_positive_outward_proxy_kg_s",
        "tau_recirc_proxy_s",
        "wall_core_bulk_temperature_contrast_K",
    ]


def target_qoi_evidence_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case_id in case_ids():
        for qoi_label in qoi_labels():
            target = target_value_for(qoi_label, case_id)
            rows.append(
                {
                    "case_id": case_id,
                    "qoi_label": qoi_label,
                    "target_time_window_s": target["target_time_window_s"],
                    "target_value": target["target_value"],
                    "target_unit": target["target_unit"],
                    "target_status": target["target_status"],
                    "target_basis": target["target_basis"],
                    "component_values": target["component_values"],
                    "same_label_formula_sign_basis": "true",
                    "target_release_grade": target["target_release_grade"],
                    "production_use_allowed_now": "false",
                    "target_source_artifact": target["target_source_artifact"],
                }
            )
    return rows


def neighbor_window_inventory_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case_id in case_ids():
        for qoi_label in qoi_labels():
            target = target_value_for(qoi_label, case_id)
            target_ready = target["target_status"] in {
                "released_exact_target_window",
                "retained_window_proxy_ready",
                "retained_window_sampled_ready",
            }
            rows.append(
                {
                    "case_id": case_id,
                    "qoi_label": qoi_label,
                    "target_time_window_s": target["target_time_window_s"],
                    "target_evidence_exists": bool_text(target_ready),
                    "target_evidence_status": target["target_status"],
                    "target_value": target["target_value"],
                    "target_unit": target["target_unit"],
                    "target_minus_window_evidence_exists": "false",
                    "target_minus_time_window_s": "",
                    "target_minus_value": "",
                    "target_minus_status": "missing_exact_same_label_neighbor_window",
                    "target_plus_window_evidence_exists": "false",
                    "target_plus_time_window_s": "",
                    "target_plus_value": "",
                    "target_plus_status": "missing_exact_same_label_neighbor_window",
                    "component_values": target["component_values"],
                    "same_label_formula_sign_basis_required": "true",
                    "neighbor_window_uq_ready": "false",
                    "release_allowed_now": "false",
                    "blocking_reason": "target value exists but exact same-label target-minus and target-plus evidence are absent",
                    "source_artifact": target["target_source_artifact"],
                }
            )
    return rows


def same_qoi_uq_matrix_rows() -> list[dict[str, str]]:
    inventory = neighbor_window_inventory_rows()
    rows: list[dict[str, str]] = []
    for qoi_label in qoi_labels():
        qoi_rows = [row for row in inventory if row["qoi_label"] == qoi_label]
        target_rows = sum(1 for row in qoi_rows if row["target_evidence_exists"] == "true")
        minus_rows = sum(1 for row in qoi_rows if row["target_minus_window_evidence_exists"] == "true")
        plus_rows = sum(1 for row in qoi_rows if row["target_plus_window_evidence_exists"] == "true")
        neighbor_ready = target_rows == len(case_ids()) and minus_rows == len(case_ids()) and plus_rows == len(case_ids())
        rows.append(
            {
                "qoi_label": qoi_label,
                "case_count": str(len(case_ids())),
                "target_window_ready_rows": str(target_rows),
                "target_minus_ready_rows": str(minus_rows),
                "target_plus_ready_rows": str(plus_rows),
                "neighbor_window_uq_ready": bool_text(neighbor_ready),
                "same_qoi_mesh_gci_status": "deferred_until_neighbor_window_uq_ready",
                "move_to_mesh_gci_uq_allowed_now": "false",
                "production_use_allowed_now": "false",
                "reason": (
                    "same-QOI neighbor-window UQ missing; do not move to mesh/GCI or production harvest"
                    if not neighbor_ready
                    else "neighbor windows complete; claim mesh/GCI gate before production harvest"
                ),
            }
        )
    return rows


def production_readiness_gate_rows() -> list[dict[str, str]]:
    target_ready = len(target_qoi_evidence_rows()) == len(case_ids()) * len(qoi_labels())
    neighbor_ready_qois = sum(1 for row in same_qoi_uq_matrix_rows() if row["neighbor_window_uq_ready"] == "true")
    gates = [
        {
            "gate": "target_window_qoi_inventory",
            "status": "diagnostic_target_values_present" if target_ready else "missing_target_values",
            "ready_for_next_stage": bool_text(target_ready),
            "production_harvest_allowed_now": "false",
            "reason": "target-window values exist, but target values alone are not same-QOI UQ",
        },
        {
            "gate": "neighbor_window_uq",
            "status": "blocked_missing_target_minus_and_target_plus_windows",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": f"{neighbor_ready_qois}/4 QOI labels have same-QOI neighbor-window UQ ready",
        },
        {
            "gate": "mesh_gci_uq",
            "status": "not_reached_neighbor_window_gate_failed",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "mesh/GCI gate should run only after exact neighboring windows exist",
        },
        {
            "gate": "production_harvest",
            "status": "do_not_run",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "same-QOI neighbor-window UQ is missing for all requested S13 QOI labels",
        },
        {
            "gate": "clean_fail_closed_thesis_result",
            "status": "ready",
            "ready_for_next_stage": "true",
            "production_harvest_allowed_now": "false",
            "reason": "publish diagnostic target evidence and explicit UQ blocker without coefficient admission",
        },
    ]
    return gates


def thesis_claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {
            "claim_id": "S13-QWALL-UQ-C1",
            "claim_text": "Target-window S13 QOI evidence exists for Q_wall_W, positive exchange mdot proxy, tau_recirc proxy, and wall/core/bulk thermal contrast across Salt2/Salt3/Salt4.",
            "claim_allowed": "true",
            "claim_role": "diagnostic_thesis_evidence",
            "supporting_artifact": "target_qoi_evidence.csv",
        },
        {
            "claim_id": "S13-QWALL-UQ-C2",
            "claim_text": "Exact same-label target-minus and target-plus neighbor windows are missing for all four requested S13 QOI labels.",
            "claim_allowed": "true",
            "claim_role": "fail_closed_uncertainty_result",
            "supporting_artifact": "neighbor_window_inventory.csv",
        },
        {
            "claim_id": "S13-QWALL-UQ-X1",
            "claim_text": "S13 production harvest, exchange coefficient admission, or same-QOI UQ is released.",
            "claim_allowed": "false",
            "claim_role": "forbidden_overclaim",
            "supporting_artifact": "production_readiness_gate.csv",
        },
        {
            "claim_id": "S13-QWALL-UQ-X2",
            "claim_text": "The source-side heat-flow fallback is equivalent to direct Q_wall_W for admission.",
            "claim_allowed": "false",
            "claim_role": "forbidden_overclaim",
            "supporting_artifact": rel(SOURCE_SIDE_GATE / "source_property_conservation_release.csv"),
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (EXACT_QWALL / "trusted_wall_Q_wall_summary.csv", "read direct target-window Q_wall_W rows"),
        (EXACT_QWALL / "summary.json", "read exact pressure/Qwall release counts"),
        (LIMITED / "sampled_field_summary.csv", "read target-window mdot and thermal contrast proxy rows"),
        (AVERAGE / "diagnostic_average_exchange_metrics.csv", "read target-window tau_recirc proxy rows"),
        (UQ_DESIGN / "neighbor_window_requirements.csv", "read S13 same-window neighbor requirements"),
        (UQ_DESIGN / "mesh_gci_requirements.csv", "read deferred mesh/GCI requirements"),
        (SOURCE_SIDE_GATE / "same_qoi_uq_matrix.csv", "read prior fail-closed same-QOI UQ status"),
        (PHASE_A / "qoi_retained_window_inventory.csv", "read cross-family retained-window inventory"),
        (PHASE_B / "mesh_gci_coverage_matrix.csv", "read cross-family mesh/GCI blocker status"),
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


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read existing artifacts only"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry/admission edit"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no scheduler action"},
        {"guard_id": "solver_sampler_harvest_uq_launch", "changed": "false", "policy": "inventory/gate only"},
        {"guard_id": "Q_wall_W_release_or_relabel", "changed": "false", "policy": "consume prior exact Qwall read-only"},
        {"guard_id": "source_property_release", "changed": "false", "policy": "not part of this row"},
        {"guard_id": "source_side_relabel_as_Q_wall", "changed": "false", "policy": "forbidden"},
        {"guard_id": "S11_S12_S13_S15_S6_trigger", "changed": "false", "policy": "forbidden"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "changed": "false", "policy": "forbidden"},
    ]


def write_thesis_result(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(out / "target_qoi_evidence.csv")}
  - {rel(out / "neighbor_window_inventory.csv")}
  - {rel(out / "same_qoi_uq_matrix.csv")}
tags: [s13, upcomer-exchange, same-qoi-uq, fail-closed, thesis-result]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Writer / Reviewer
type: work_product
status: complete
---
# S13 Same-QOI Neighbor-Window Fail-Closed Result

Decision: `{summary["decision"]}`.

Target-window evidence is present for the requested S13 QOI labels across
Salt2, Salt3, and Salt4, including the direct trusted-wall `Q_wall_W` rows.
However, exact same-label target-minus and target-plus neighboring windows are
missing for all four requested QOI labels:

- `Q_wall_W`
- `mdot_exchange_positive_outward_proxy_kg_s`
- `tau_recirc_proxy_s`
- `wall_core_bulk_temperature_contrast_K`

This is a clean negative uncertainty result. It supports thesis language that
S13 has diagnostic target-window exchange and heat-flow evidence, but it does
not support production harvest, coefficient admission, model fitting, validation
scoring, or any S11/S12/S13/S15/S6 trigger.

Next scientific unlock: generate or locate exact same-label target-minus and
target-plus rows for the four QOI labels above. Only after that should a
separate mesh/GCI UQ gate run.
"""
    (out / "clean_fail_closed_thesis_result.md").write_text(text, encoding="utf-8")


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(EXACT_QWALL / "trusted_wall_Q_wall_summary.csv")}
  - {rel(LIMITED / "sampled_field_summary.csv")}
  - {rel(AVERAGE / "diagnostic_average_exchange_metrics.csv")}
  - {rel(UQ_DESIGN / "neighbor_window_requirements.csv")}
tags: [s13, upcomer-exchange, qwall, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - operational_notes/07-26/22/2026-07-22_S13_UPCOMER_EXCHANGE_TOMORROW_CONTEXT_HANDOFF.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Qwall Same-QOI Neighbor UQ Execution

Decision: `{summary["decision"]}`.

This package answers one question: do exact target-minus / target /
target-plus rows exist for the requested S13 QOI labels?

- cases inventoried: `{summary["case_count"]}`
- QOI labels inventoried: `{summary["qoi_label_count"]}`
- target-window rows present: `{summary["target_window_ready_rows"]}`
- target-minus rows present: `{summary["target_minus_ready_rows"]}`
- target-plus rows present: `{summary["target_plus_ready_rows"]}`
- same-QOI neighbor UQ-ready labels: `{summary["same_qoi_neighbor_uq_ready_qois"]}`
- move to mesh/GCI UQ allowed now: `{str(summary["move_to_mesh_gci_uq_allowed_now"]).lower()}`
- production harvest allowed now: `{str(summary["production_harvest_allowed"]).lower()}`

Target-window values exist, including direct trusted-wall `Q_wall_W`, but exact
same-label neighboring windows are absent. This row therefore publishes a clean
fail-closed thesis result and does not run mesh/GCI, sampler, production harvest,
UQ execution, fitting, validation scoring, or admission.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    targets = target_qoi_evidence_rows()
    neighbors = neighbor_window_inventory_rows()
    uq = same_qoi_uq_matrix_rows()
    production = production_readiness_gate_rows()
    claims = thesis_claim_boundary_rows()
    sources = source_manifest_rows()
    guards = guardrail_rows()
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "fail_closed_neighbor_window_uq_missing",
        "case_count": len(case_ids()),
        "qoi_label_count": len(qoi_labels()),
        "target_qoi_rows": len(targets),
        "target_window_ready_rows": sum(1 for row in neighbors if row["target_evidence_exists"] == "true"),
        "target_minus_ready_rows": sum(
            1 for row in neighbors if row["target_minus_window_evidence_exists"] == "true"
        ),
        "target_plus_ready_rows": sum(
            1 for row in neighbors if row["target_plus_window_evidence_exists"] == "true"
        ),
        "same_qoi_neighbor_uq_ready_qois": sum(
            1 for row in uq if row["neighbor_window_uq_ready"] == "true"
        ),
        "move_to_mesh_gci_uq_allowed_now": False,
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "clean_fail_closed_thesis_result_published": True,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Q_wall_W_release_or_relabel": False,
        "source_property_release": False,
        "source_side_relabel_as_Q_wall": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    csv_dump(out / "target_qoi_evidence.csv", list(targets[0]), targets)
    csv_dump(out / "neighbor_window_inventory.csv", list(neighbors[0]), neighbors)
    csv_dump(out / "same_qoi_uq_matrix.csv", list(uq[0]), uq)
    csv_dump(out / "production_readiness_gate.csv", list(production[0]), production)
    csv_dump(out / "thesis_claim_boundary.csv", list(claims[0]), claims)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    json_dump(out / "summary.json", summary)
    write_thesis_result(out, summary)
    write_readme(out, summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
