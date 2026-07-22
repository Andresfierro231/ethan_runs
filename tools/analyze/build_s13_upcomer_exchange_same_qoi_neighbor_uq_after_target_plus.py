#!/usr/bin/env python3
"""Execute S13 same-QOI neighbor-window temporal UQ after target-plus harvest."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SAME-QOI-NEIGHBOR-UQ-AFTER-TARGET-PLUS-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)
TARGET_PLUS_HARVEST = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest"
)
PRE_TARGET_PLUS_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution"
)
UQ_DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_same_window_uq_design"
)
PHASE_B_MESH_GCI = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix"
)
SOURCE_SIDE_HEATFLOW = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq"
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


def parse_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite value: {value}")
    return number


def qoi_labels(rows: list[dict[str, str]]) -> list[str]:
    return sorted({row["qoi_label"] for row in rows})


def temporal_uq_row(row: dict[str, str]) -> dict[str, str]:
    minus = parse_float(row["target_minus_value"])
    target = parse_float(row["target_value"])
    plus = parse_float(row["target_plus_value"])
    delta_minus = target - minus
    delta_plus = plus - target
    max_abs_delta = max(abs(delta_minus), abs(delta_plus))
    half_range = (max(minus, target, plus) - min(minus, target, plus)) / 2.0
    mean_neighbor = (minus + target + plus) / 3.0
    relative_percent = "" if target == 0.0 else f"{100.0 * max_abs_delta / abs(target):.12g}"
    return {
        "case_id": row["case_id"],
        "qoi_label": row["qoi_label"],
        "target_minus_time_window_s": row["target_minus_time_window_s"],
        "target_time_window_s": row["target_time_window_s"],
        "target_plus_time_window_s": row["target_plus_time_window_s"],
        "target_minus_value": row["target_minus_value"],
        "target_value": row["target_value"],
        "target_plus_value": row["target_plus_value"],
        "delta_target_minus_to_target": f"{delta_minus:.12g}",
        "delta_target_to_plus": f"{delta_plus:.12g}",
        "max_abs_neighbor_delta": f"{max_abs_delta:.12g}",
        "half_range_uncertainty": f"{half_range:.12g}",
        "mean_three_window_value": f"{mean_neighbor:.12g}",
        "relative_max_abs_neighbor_delta_percent": relative_percent,
        "finite_triplet": "true",
        "same_label_formula_sign_basis": row["same_label_formula_sign_basis"],
        "neighbor_window_uq_executed": "true",
        "temporal_uq_basis": "max(abs(target-target_minus), abs(target_plus-target)); half_range also reported",
        "production_use_allowed_now": "false",
        "source_basis": row["source_basis"],
    }


def temporal_uq_rows() -> list[dict[str, str]]:
    rows = read_csv(TARGET_PLUS_HARVEST / "same_qoi_neighbor_window_rows.csv")
    out = []
    for row in rows:
        ready = (
            row["neighbor_window_uq_ready"] == "true"
            and row["same_label_formula_sign_basis"] == "true"
            and row["target_minus_status"].startswith("sampled")
            and row["target_plus_status"].startswith("sampled")
            and row["target_status"] in {
                "released_exact_target_window",
                "retained_window_proxy_ready",
                "retained_window_sampled_ready",
            }
        )
        if not ready:
            raise RuntimeError(f"row is not ready for same-QOI UQ: {row['case_id']} {row['qoi_label']}")
        out.append(temporal_uq_row(row))
    return out


def qoi_summary_rows(case_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for qoi_label in qoi_labels(case_rows):
        selected = [row for row in case_rows if row["qoi_label"] == qoi_label]
        max_abs = [parse_float(row["max_abs_neighbor_delta"]) for row in selected]
        half_ranges = [parse_float(row["half_range_uncertainty"]) for row in selected]
        rels = [
            parse_float(row["relative_max_abs_neighbor_delta_percent"])
            for row in selected
            if row["relative_max_abs_neighbor_delta_percent"]
        ]
        ready = len(selected) == 3 and all(row["neighbor_window_uq_executed"] == "true" for row in selected)
        rows.append(
            {
                "qoi_label": qoi_label,
                "case_count": str(len(selected)),
                "finite_triplet_rows": str(sum(1 for row in selected if row["finite_triplet"] == "true")),
                "neighbor_window_uq_executed_rows": str(
                    sum(1 for row in selected if row["neighbor_window_uq_executed"] == "true")
                ),
                "max_abs_temporal_uncertainty": f"{max(max_abs):.12g}",
                "mean_abs_temporal_uncertainty": f"{sum(max_abs) / len(max_abs):.12g}",
                "max_half_range_uncertainty": f"{max(half_ranges):.12g}",
                "max_relative_temporal_uncertainty_percent": f"{max(rels):.12g}" if rels else "",
                "same_qoi_temporal_uq_status": "executed" if ready else "blocked",
                "mesh_gci_gate_input_ready": bool_text(ready),
                "production_use_allowed_now": "false",
                "admission_allowed_now": "false",
                "release_boundary": (
                    "direct_Q_wall_W_temporal_uq_support_not_admission"
                    if qoi_label == "Q_wall_W"
                    else "diagnostic_proxy_temporal_uq_support_not_admission"
                ),
            }
        )
    return rows


def heat_flow_match_rows(case_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Quantify whether the available heat-flow lanes can close the same CV balance."""
    source_rows = {
        row["case_id"]: row
        for row in read_csv(SOURCE_SIDE_HEATFLOW / "case_heatflow_equivalence_basis.csv")
    }
    rows: list[dict[str, str]] = []
    for case_id in sorted(source_rows):
        source = source_rows[case_id]
        qwall_row = next(row for row in case_rows if row["case_id"] == case_id and row["qoi_label"] == "Q_wall_W")
        mdot_row = next(
            row
            for row in case_rows
            if row["case_id"] == case_id and row["qoi_label"] == "mdot_exchange_positive_outward_proxy_kg_s"
        )
        dtemp_row = next(
            row
            for row in case_rows
            if row["case_id"] == case_id and row["qoi_label"] == "wall_core_bulk_temperature_contrast_K"
        )
        qwall = parse_float(qwall_row["target_value"])
        qsource = parse_float(source["Q_source_side_net_static_bc_W"])
        mdot = parse_float(mdot_row["target_value"])
        delta_t = parse_float(dtemp_row["target_value"])
        exchange_scale = abs(mdot * delta_t)
        cp_for_qwall = qwall / exchange_scale if exchange_scale else math.inf
        cp_for_source = qsource / exchange_scale if exchange_scale else math.inf
        cp_for_combined = (qwall + qsource) / exchange_scale if exchange_scale else math.inf
        source_minus_qwall = qsource - qwall
        ratio = qwall / qsource if qsource else math.inf
        rows.append(
            {
                "case_id": case_id,
                "target_time_window_s": qwall_row["target_time_window_s"],
                "Q_wall_W": f"{qwall:.12g}",
                "Q_source_side_net_static_bc_W": f"{qsource:.12g}",
                "source_minus_qwall_W": f"{source_minus_qwall:.12g}",
                "qwall_to_source_side_ratio": f"{ratio:.12g}",
                "mdot_exchange_positive_outward_proxy_kg_s": f"{mdot:.12g}",
                "wall_core_bulk_temperature_contrast_K": f"{delta_t:.12g}",
                "abs_mdot_times_deltaT_kgK_s": f"{exchange_scale:.12g}",
                "cp_required_to_match_Q_wall_J_kg_K": f"{cp_for_qwall:.12g}",
                "cp_required_to_match_source_side_J_kg_K": f"{cp_for_source:.12g}",
                "cp_required_to_match_Qwall_plus_source_side_J_kg_K": f"{cp_for_combined:.12g}",
                "heat_flow_match_status": "not_physical_match_with_current_exchange_scale",
                "interpretation": (
                    "direct Q_wall_W and source-side static heat are different heat lanes; "
                    "current mdot*DeltaT scale would require unphysical cp-scale values, "
                    "so do not tune a coefficient to force agreement"
                ),
                "next_required_action": (
                    "define the production energy residual on the exchange-cell control volume, "
                    "release cp/property basis, and harvest T_recirc/core enthalpy terms on the same mask/time basis"
                ),
            }
        )
    return rows


def production_gate_rows(summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ready_qois = sum(1 for row in summary_rows if row["mesh_gci_gate_input_ready"] == "true")
    return [
        {
            "gate": "target_plus_same_qoi_harvest",
            "status": "complete",
            "ready_for_next_stage": "true",
            "production_harvest_allowed_now": "false",
            "reason": "complete target-minus/target/target-plus table is available",
        },
        {
            "gate": "same_qoi_neighbor_window_temporal_uq",
            "status": "complete" if ready_qois == 4 else "blocked",
            "ready_for_next_stage": bool_text(ready_qois == 4),
            "production_harvest_allowed_now": "false",
            "reason": f"{ready_qois}/4 QOI labels have executed temporal neighbor-window UQ",
        },
        {
            "gate": "mesh_gci_uq",
            "status": "ready_to_claim" if ready_qois == 4 else "blocked",
            "ready_for_next_stage": bool_text(ready_qois == 4),
            "production_harvest_allowed_now": "false",
            "reason": "mesh/GCI remains a separate required gate; do not borrow unrelated GCI",
        },
        {
            "gate": "production_harvest",
            "status": "do_not_run",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "same-QOI temporal UQ is executed, but mesh/GCI UQ and admission gates are not complete",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (TARGET_PLUS_HARVEST / "same_qoi_neighbor_window_rows.csv", "complete target-minus/target/target-plus same-QOI table"),
        (TARGET_PLUS_HARVEST / "same_qoi_neighbor_triplet_matrix.csv", "target-plus harvest triplet readiness matrix"),
        (TARGET_PLUS_HARVEST / "summary.json", "target-plus harvest summary"),
        (SOURCE_SIDE_HEATFLOW / "case_heatflow_equivalence_basis.csv", "source-side static heat-flow comparison"),
        (PRE_TARGET_PLUS_UQ / "summary.json", "historical pre-target-plus fail-closed UQ context"),
        (UQ_DESIGN / "mesh_gci_requirements.csv", "S13 UQ design mesh/GCI requirements"),
        (PHASE_B_MESH_GCI / "mesh_gci_coverage_matrix.csv", "cross-family mesh/GCI evidence matrix"),
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
        "mesh_gci_uq_execution": "false",
        "production_harvest": "false",
        "Qwall_source_property_or_coefficient_release": "false",
        "s11_s12_s13_s15_s6_trigger": "false",
        "residual_absorbed_into_internal_nu": "false",
    }
    return [{"guardrail": key, "value": value} for key, value in flags.items()]


def write_readme(summary: dict[str, object], out: Path = OUT) -> None:
    text = f"""---
provenance:
  - {rel(OUT / "same_qoi_temporal_uq_case_rows.csv")}
  - {rel(OUT / "same_qoi_temporal_uq_summary.csv")}
  - {rel(TARGET_PLUS_HARVEST / "same_qoi_neighbor_window_rows.csv")}
tags: [s13, upcomer-exchange, same-qoi-uq, temporal-uq]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - {rel(TARGET_PLUS_HARVEST / "README.md")}
  - {rel(PHASE_B_MESH_GCI / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Same-QOI Neighbor UQ After Target-Plus

Decision: `{summary["decision"]}`.

This package executes temporal neighbor-window UQ from the complete
target-minus/target/target-plus table. It does not execute mesh/GCI UQ or
production harvest.

- case-level temporal UQ rows: `{summary["case_temporal_uq_rows"]}`
- QOI-level UQ summaries: `{summary["qoi_summary_rows"]}`
- temporal-UQ executed QOI labels: `{summary["same_qoi_temporal_uq_executed_qois"]}`
- mesh/GCI gate input ready: `{str(summary["mesh_gci_gate_input_ready"]).lower()}`
- heat-flow match diagnostic rows: `{summary["heat_flow_match_rows"]}`
- heat-flow match ready rows: `{summary["heat_flow_match_ready_rows"]}`
- production harvest allowed: `false`

The heat-flow match diagnostic compares direct `Q_wall_W` against the
source-side static heat-flow fallback and the current exchange
`mdot_exchange * DeltaT_wall_core` scale. It intentionally does not tune a
coefficient. Current rows show that forcing these heat lanes to agree through
the present exchange scale would require unphysical heat-capacity-scale values;
the next scientific step is a same-mask production energy residual with
released property basis and harvested `T_recirc`/core enthalpy terms.

Next action: claim the S13 Qwall/exchange mesh/GCI UQ gate. That row must use a
same-label mesh family or fail closed; it must not borrow unrelated GCI.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, object]:
    ensure_dir(out)
    case_rows = temporal_uq_rows()
    summary_rows = qoi_summary_rows(case_rows)
    heat_rows = heat_flow_match_rows(case_rows)
    gate_rows = production_gate_rows(summary_rows)
    source_rows = source_manifest_rows()
    guard_rows = guardrail_rows()
    mesh_ready = all(row["mesh_gci_gate_input_ready"] == "true" for row in summary_rows)
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "same_qoi_neighbor_temporal_uq_executed_mesh_gci_ready_to_claim",
        "case_count": 3,
        "qoi_label_count": 4,
        "case_temporal_uq_rows": len(case_rows),
        "qoi_summary_rows": len(summary_rows),
        "heat_flow_match_rows": len(heat_rows),
        "heat_flow_match_ready_rows": sum(
            1 for row in heat_rows if row["heat_flow_match_status"] == "matched_ready_for_production_residual"
        ),
        "same_qoi_temporal_uq_executed_qois": sum(
            1 for row in summary_rows if row["same_qoi_temporal_uq_status"] == "executed"
        ),
        "mesh_gci_gate_input_ready": mesh_ready,
        "mesh_gci_uq_executed": False,
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

    csv_dump(out / "same_qoi_temporal_uq_case_rows.csv", list(case_rows[0]), case_rows)
    csv_dump(out / "same_qoi_temporal_uq_summary.csv", list(summary_rows[0]), summary_rows)
    csv_dump(out / "heat_flow_match_diagnostics.csv", list(heat_rows[0]), heat_rows)
    csv_dump(out / "production_readiness_gate.csv", list(gate_rows[0]), gate_rows)
    csv_dump(out / "source_manifest.csv", list(source_rows[0]), source_rows)
    csv_dump(out / "no_mutation_guardrails.csv", list(guard_rows[0]), guard_rows)
    json_dump(out / "summary.json", summary)
    write_readme(summary, out)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
