#!/usr/bin/env python3
"""Build the S13 limited sampled-field thesis evidence package."""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-EVIDENCE-SYNTHESIS-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis"
)
LIMITED = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction"
)
AVERAGE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"
)
CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk"
)
UNBLOCK = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock"
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


def finite(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return number == number and number not in (float("inf"), float("-inf"))


def bool_text(value: bool) -> str:
    return str(value).lower()


def exchange_trend_rows() -> list[dict[str, str]]:
    sampled = by_case(read_csv(LIMITED / "sampled_field_summary.csv"))
    average = by_case(read_csv(AVERAGE / "diagnostic_average_exchange_metrics.csv"))
    rows: list[dict[str, str]] = []
    for case_id in sorted(sampled):
        srow = sampled[case_id]
        arow = average[case_id]
        finite_fields = [
            srow["mdot_exchange_net_proxy_kg_s"],
            srow["mdot_exchange_positive_outward_proxy_kg_s"],
            srow["mdot_exchange_negative_inward_proxy_kg_s"],
            srow["trusted_wall_T_area_avg_K"],
            srow["interface_core_T_area_avg_K"],
            srow["seeded_cv_T_volume_avg_K"],
            arow["tau_recirc_proxy_s"],
            arow["hA_source_side_proxy_W_K"],
        ]
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": srow["time_window_s"],
                "interface_area_m2": srow["interface_area_m2"],
                "trusted_wall_area_m2": srow["trusted_wall_area_m2"],
                "seeded_cv_volume_m3": arow["seeded_cv_volume_m3"],
                "mdot_exchange_net_proxy_kg_s": srow["mdot_exchange_net_proxy_kg_s"],
                "mdot_exchange_positive_outward_proxy_kg_s": srow[
                    "mdot_exchange_positive_outward_proxy_kg_s"
                ],
                "mdot_exchange_negative_inward_proxy_kg_s": srow[
                    "mdot_exchange_negative_inward_proxy_kg_s"
                ],
                "tau_recirc_proxy_s": arow["tau_recirc_proxy_s"],
                "trusted_wall_T_area_avg_K": srow["trusted_wall_T_area_avg_K"],
                "interface_core_T_area_avg_K": srow["interface_core_T_area_avg_K"],
                "seeded_cv_T_volume_avg_K": srow["seeded_cv_T_volume_avg_K"],
                "delta_T_wall_minus_core_K": srow["delta_T_wall_minus_core_K"],
                "delta_T_core_minus_seed_K": srow["delta_T_core_minus_seed_K"],
                "source_side_q_net_W": arow["q_net_W"],
                "hA_source_side_proxy_W_K": arow["hA_source_side_proxy_W_K"],
                "finite_required_metrics": bool_text(all(finite(value) for value in finite_fields)),
                "evidence_role": "diagnostic_thesis_evidence_only",
                "production_harvest_allowed": "false",
                "coefficient_admission_allowed": "false",
            }
        )
    return rows


def sampled_field_gate_rows() -> list[dict[str, str]]:
    sampled = by_case(read_csv(LIMITED / "sampled_field_summary.csv"))
    availability = read_csv(CONTRACT / "field_availability.csv")
    field_status: dict[tuple[str, str], str] = {}
    for row in availability:
        field_status[(row["case_id"], row["field_or_property"])] = row["contract_status"]
    rows: list[dict[str, str]] = []
    gate_specs = [
        ("interface_U", "U", "ready_diagnostic", "true", "false"),
        ("interface_T", "T", "ready_diagnostic", "true", "false"),
        ("interface_rho", "rho", "ready_diagnostic", "true", "false"),
        ("wall_T", "T", "ready_diagnostic", "true", "false"),
        ("core_T", "T", "ready_diagnostic", "true", "false"),
        ("Q_wall_W", "wallHeatFlux", "blocked_missing_wall_heat_basis", "false", "true"),
        ("pressure", "p_or_p_rgh", "blocked_missing_pressure_basis", "false", "true"),
        ("viscosity", "mu_or_nu", "blocked_missing_property_basis", "false", "true"),
        ("cp", "cp", "blocked_missing_source_property_release", "false", "true"),
        ("same_qoi_uq", "same_qoi_uq", "blocked_missing_neighbor_window_and_mesh_gci", "false", "true"),
    ]
    for case_id in sorted(sampled):
        for gate, source_field, status, diagnostic_ready, blocks_production in gate_specs:
            rows.append(
                {
                    "case_id": case_id,
                    "time_window_s": sampled[case_id]["time_window_s"],
                    "gate": gate,
                    "source_field_or_property": source_field,
                    "input_contract_status": field_status.get((case_id, source_field), status),
                    "diagnostic_ready": diagnostic_ready,
                    "production_ready": "false",
                    "blocks_production": blocks_production,
                    "required_next_action": next_action_for_gate(gate),
                }
            )
    return rows


def next_action_for_gate(gate: str) -> str:
    return {
        "interface_U": "keep as diagnostic evidence and preserve source path",
        "interface_T": "keep as diagnostic evidence and preserve source path",
        "interface_rho": "keep as diagnostic evidence and preserve source path",
        "wall_T": "keep as diagnostic evidence and preserve source path",
        "core_T": "keep as diagnostic evidence and preserve source path",
        "Q_wall_W": "use exact pressure and trusted-wall heat-flux compute row before release",
        "pressure": "consume exact pressure compute row after terminal closeout",
        "viscosity": "release property basis with source/property labels",
        "cp": "release cp basis with source/property labels",
        "same_qoi_uq": "run same-label neighbor-window and mesh/GCI UQ after exact QOI contract",
    }[gate]


def predictive_path_status_rows() -> list[dict[str, str]]:
    return [
        {
            "path_step": "runtime_input_contract",
            "status": "ready_for_diagnostic_reporting",
            "thesis_use": "state what inputs are allowed and what remains forbidden",
            "blocks_prediction": "false",
            "evidence_path": rel(UNBLOCK / "production_readiness_table.csv"),
        },
        {
            "path_step": "train_validation_holdout_external_test_separation",
            "status": "policy_ready_no_scores_released_here",
            "thesis_use": "show split discipline before any future freeze",
            "blocks_prediction": "false",
            "evidence_path": rel(ROOT / "reports/thesis_dossier/README.md"),
        },
        {
            "path_step": "pressure_gate",
            "status": "blocked_pending_exact_pressure_row",
            "thesis_use": "negative result and next-unblock lane",
            "blocks_prediction": "true",
            "evidence_path": rel(UNBLOCK / "blocker_unlock_matrix.csv"),
        },
        {
            "path_step": "thermal_gate",
            "status": "diagnostic_wall_core_temperatures_ready_Q_wall_blocked",
            "thesis_use": "wall/core residual ownership evidence without heat-flow admission",
            "blocks_prediction": "true",
            "evidence_path": rel(LIMITED / "sampled_field_summary.csv"),
        },
        {
            "path_step": "recirculation_exchange_gate",
            "status": "diagnostic_exchange_ready_same_qoi_uq_blocked",
            "thesis_use": "finite exchange field evidence and fail-closed admission boundary",
            "blocks_prediction": "true",
            "evidence_path": rel(AVERAGE / "diagnostic_average_exchange_metrics.csv"),
        },
        {
            "path_step": "negative_results_as_scientific_evidence",
            "status": "ready_for_thesis_insert",
            "thesis_use": "document why the coefficient is not admitted",
            "blocks_prediction": "false",
            "evidence_path": rel(UNBLOCK / "downstream_decision.csv"),
        },
    ]


def claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {
            "claim_id": "S13-C1",
            "claim_text": "Limited sampled-field extraction produced finite interface U/T/rho and wall/core temperature diagnostics for Salt2, Salt3, and Salt4.",
            "claim_allowed": "true",
            "claim_role": "diagnostic_thesis_evidence",
            "supporting_artifact": rel(LIMITED / "sampled_field_summary.csv"),
        },
        {
            "claim_id": "S13-C2",
            "claim_text": "The source-side heat-flow path is the smallest remaining unblock path, but it must remain a distinct QOI.",
            "claim_allowed": "true",
            "claim_role": "next_step_decision",
            "supporting_artifact": rel(UNBLOCK / "qwall_or_source_side_path_decision.csv"),
        },
        {
            "claim_id": "S13-X1",
            "claim_text": "The S13 exchange coefficient, Q_wall_W, production harvest, and source/property release are admitted.",
            "claim_allowed": "false",
            "claim_role": "forbidden_overclaim",
            "supporting_artifact": rel(UNBLOCK / "downstream_decision.csv"),
        },
        {
            "claim_id": "S13-X2",
            "claim_text": "The S13 diagnostic rows may trigger S11/S12/S13/S15/S6 scoring or freeze.",
            "claim_allowed": "false",
            "claim_role": "forbidden_downstream_trigger",
            "supporting_artifact": rel(UNBLOCK / "no_mutation_guardrails.csv"),
        },
    ]


def next_unblock_rows() -> list[dict[str, str]]:
    return [
        {
            "rank": "1",
            "task_lane": "consume_exact_pressure_Q_wall_compute_after_closeout",
            "reason": "active exact pressure/Qwall row owns the missing production fields",
            "allowed_now_from_this_package": "false",
            "expected_decision": "release_or_keep_blocked_Q_wall_W_and_pressure_basis",
        },
        {
            "rank": "2",
            "task_lane": "source_side_heat_flow_QOI_contract",
            "reason": "q_net exists but cannot be renamed as Q_wall_W",
            "allowed_now_from_this_package": "false",
            "expected_decision": "distinct_source_side_QOI_ready_for_UQ_or_blocked",
        },
        {
            "rank": "3",
            "task_lane": "same_qoi_neighbor_window_and_mesh_UQ",
            "reason": "production release requires same label, formula, sign, and basis",
            "allowed_now_from_this_package": "false",
            "expected_decision": "UQ_ready_or_fail_closed",
        },
        {
            "rank": "4",
            "task_lane": "S8_S12_thermal_residual_ownership_gate",
            "reason": "wall/test-section thermal residual ownership must be attributed before S12 freeze",
            "allowed_now_from_this_package": "false",
            "expected_decision": "exactly_one_train_repair_or_fail_closed",
        },
        {
            "rank": "5",
            "task_lane": "hybrid_pressure_no_fit_bakeoff",
            "reason": "pressure negative result can become thesis evidence without coefficient tuning",
            "allowed_now_from_this_package": "false",
            "expected_decision": "thesis_evidence_only_or_candidate_reviewable",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read completed packages only"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry/admission edit"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no scheduler action"},
        {"guard_id": "solver_sampler_harvest_uq_launch", "changed": "false", "policy": "no launch from this package"},
        {"guard_id": "thesis_current_file_edit", "changed": "false", "policy": "insert-ready package only"},
        {"guard_id": "Q_wall_W_release", "changed": "false", "policy": "Q_wall_W remains blocked"},
        {"guard_id": "source_property_release", "changed": "false", "policy": "no source/property promotion"},
        {"guard_id": "downstream_trigger", "changed": "false", "policy": "no S11/S12/S13/S15/S6 trigger"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "changed": "false", "policy": "no residual absorption"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (LIMITED / "sampled_field_summary.csv", "finite sampled-field metrics"),
        (LIMITED / "summary.json", "limited extraction summary"),
        (AVERAGE / "diagnostic_average_exchange_metrics.csv", "thermal and tau proxy metrics"),
        (CONTRACT / "field_availability.csv", "field/property availability gates"),
        (UNBLOCK / "production_readiness_table.csv", "post-extraction readiness decision"),
        (UNBLOCK / "blocker_unlock_matrix.csv", "blocker matrix"),
        (UNBLOCK / "qwall_or_source_side_path_decision.csv", "Qwall/source-side path decision"),
        (UQ_DESIGN / "qoi_release_decision.csv", "same-QOI UQ release design"),
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


def write_predictive_path_svg(out: Path, rows: list[dict[str, str]]) -> str:
    svg_dir = ensure_dir(out / "figures" / "svg")
    path = svg_dir / "s13_predictive_path_status.svg"
    x0 = 40
    y0 = 45
    box_w = 265
    box_h = 52
    gap = 18
    height = y0 * 2 + len(rows) * (box_h + gap)
    colors = {
        "true": ("#f8d7da", "#842029"),
        "false": ("#d1e7dd", "#0f5132"),
    }
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}">',
        '<rect width="720" height="100%" fill="#ffffff"/>',
        '<text x="40" y="28" font-family="Arial, sans-serif" font-size="18" font-weight="700">S13 predictive path status</text>',
    ]
    for index, row in enumerate(rows):
        y = y0 + index * (box_h + gap)
        fill, stroke = colors[row["blocks_prediction"]]
        parts.append(f'<rect x="{x0}" y="{y}" width="{box_w}" height="{box_h}" rx="4" fill="{fill}" stroke="{stroke}"/>')
        parts.append(
            f'<text x="{x0 + 12}" y="{y + 22}" font-family="Arial, sans-serif" font-size="13" font-weight="700">{row["path_step"]}</text>'
        )
        parts.append(
            f'<text x="{x0 + 12}" y="{y + 40}" font-family="Arial, sans-serif" font-size="12">{row["status"][:42]}</text>'
        )
        if index < len(rows) - 1:
            parts.append(f'<line x1="{x0 + box_w / 2:.1f}" y1="{y + box_h}" x2="{x0 + box_w / 2:.1f}" y2="{y + box_h + gap}" stroke="#555" stroke-width="1.5"/>')
            parts.append(f'<polygon points="{x0 + box_w / 2 - 5:.1f},{y + box_h + gap - 7} {x0 + box_w / 2 + 5:.1f},{y + box_h + gap - 7} {x0 + box_w / 2:.1f},{y + box_h + gap}" fill="#555"/>')
        parts.append(
            f'<text x="340" y="{y + 24}" font-family="Arial, sans-serif" font-size="13">{row["thesis_use"]}</text>'
        )
        parts.append(
            f'<text x="340" y="{y + 43}" font-family="Arial, sans-serif" font-size="11" fill="#555">{row["evidence_path"]}</text>'
        )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return rel(path)


def write_thesis_insert(out: Path, summary: dict[str, Any], svg_path: str) -> None:
    text = f"""---
provenance:
  - {rel(LIMITED / "sampled_field_summary.csv")}
  - {rel(AVERAGE / "diagnostic_average_exchange_metrics.csv")}
  - {rel(UNBLOCK / "production_readiness_table.csv")}
tags: [s13, thesis-analysis, upcomer-exchange, predictive-gates]
related:
  - {rel(out / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Writer / Reviewer
type: report
status: complete
---
# Thesis Insert Package: S13 Limited Sampled-Field Evidence

Use this package as Ch. 6/7 insert-ready material after thesis-file ownership is
clear. It is not a production harvest and it does not release an exchange
coefficient.

## Table Set

- `s13_exchange_trend_table.csv`: finite Salt2/Salt3/Salt4 exchange and thermal
  diagnostics.
- `s13_sampled_field_gate_matrix.csv`: fields ready for diagnostic reporting and
  fields that still block production.
- `predictive_path_status_table.csv`: runtime contract, split policy, pressure,
  thermal, recirculation, and negative-result status.
- `s13_thesis_claim_boundary.csv`: allowed thesis claims and forbidden
  overclaims.

## Figure

Figure source: `{svg_path}`.

Caption: S13 predictive-path status for the upcomer exchange lane. Interface
velocity, temperature, density, and wall/core temperature diagnostics are finite
for the retained Salt2/Salt3/Salt4 windows, but pressure, trusted-wall heat-flow,
property, and same-QOI uncertainty gates remain closed. The result is therefore
scientific evidence about the path and blockers, not an admitted predictive
coefficient.

## Chapter Placement

Place the diagnostic field table near the upcomer recirculation/exchange
discussion in Ch. 6. Place the path-status figure in Ch. 7 where the thesis
explains why the predictive scorecard remains blocked until train-only full
solve, attribution, freeze, validation, holdout, and external-test gates are
separated.

## Closeout

Decision: `{summary["decision"]}`.

No thesis-current files were edited in this task because existing active rows
already own Ch. 6/7 paths.
"""
    (out / "thesis_insert_package.md").write_text(text, encoding="utf-8")


def write_readme(out: Path, summary: dict[str, Any], svg_path: str) -> None:
    text = f"""---
provenance:
  - {rel(LIMITED / "sampled_field_summary.csv")}
  - {rel(AVERAGE / "diagnostic_average_exchange_metrics.csv")}
  - {rel(CONTRACT / "field_availability.csv")}
  - {rel(UNBLOCK / "production_readiness_table.csv")}
tags: [s13, upcomer-exchange, sampled-fields, thesis-analysis, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - operational_notes/07-26/22/2026-07-22_S13_UPCOMER_EXCHANGE_LIMITED_SAMPLED_FIELD_EVIDENCE_SYNTHESIS.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Limited Sampled-Field Evidence Synthesis

Decision: `{summary["decision"]}`.

This package consolidates completed S13 sampled-field work into thesis-ready
diagnostic evidence. It keeps production harvest and coefficient admission
closed.

- cases synthesized: `{summary["case_count"]}`
- finite exchange rows: `{summary["finite_exchange_rows"]}`
- diagnostic-ready gate rows: `{summary["diagnostic_ready_gate_rows"]}`
- production-ready gate rows: `{summary["production_ready_gate_rows"]}`
- blocked production gate rows: `{summary["blocked_production_gate_rows"]}`
- figure: `{svg_path}`

Use `thesis_insert_package.md` for chapter-facing prose, tables, and caption
text after thesis-file ownership is clear.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    trend = exchange_trend_rows()
    gates = sampled_field_gate_rows()
    path_status = predictive_path_status_rows()
    claims = claim_boundary_rows()
    next_steps = next_unblock_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()
    svg_path = write_predictive_path_svg(out, path_status)
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "diagnostic_only_thesis_ready_production_harvest_blocked",
        "case_count": len(trend),
        "finite_exchange_rows": sum(1 for row in trend if row["finite_required_metrics"] == "true"),
        "diagnostic_ready_gate_rows": sum(1 for row in gates if row["diagnostic_ready"] == "true"),
        "production_ready_gate_rows": sum(1 for row in gates if row["production_ready"] == "true"),
        "blocked_production_gate_rows": sum(1 for row in gates if row["blocks_production"] == "true"),
        "production_harvest_allowed_rows": 0,
        "coefficient_admission_allowed_rows": 0,
        "thesis_current_file_edit": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "source_property_release": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
        "figure_svg": svg_path,
    }
    csv_dump(out / "s13_exchange_trend_table.csv", list(trend[0]), trend)
    csv_dump(out / "s13_sampled_field_gate_matrix.csv", list(gates[0]), gates)
    csv_dump(out / "predictive_path_status_table.csv", list(path_status[0]), path_status)
    csv_dump(out / "s13_thesis_claim_boundary.csv", list(claims[0]), claims)
    csv_dump(out / "s13_next_unblock_queue.csv", list(next_steps[0]), next_steps)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    write_thesis_insert(out, summary, svg_path)
    write_readme(out, summary, svg_path)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
