#!/usr/bin/env python3
"""Build the S12/S13 TP-exchange blocker unlock package.

This is a local evidence-join pass. It consumes completed S12 TP-first and S13
upcomer-exchange packages, quantifies the retained-window diagnostic evidence,
and emits exact next-action contracts. It does not run native sampling, mutate
solver outputs, release source/property/Qwall values, fit coefficients, freeze a
candidate, or score protected splits.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S12-S13-TP-EXCHANGE-BLOCKER-UNLOCK-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_s13_tp_exchange_blocker_unlock"

S12_TP = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate"
S12_FREEZE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_s12_thermal_source_property_freeze_gate"
S13_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
S13_MESH = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation"
S13_ENDPOINT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation"
MF16_SOURCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def fnum(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def require_inputs() -> None:
    required = [
        S12_TP / "s12_tp_priority_context.csv",
        S12_TP / "s12_tp_exchange_evidence_table.csv",
        S12_TP / "s12_tp_unlock_gate_matrix.csv",
        S12_FREEZE / "candidate_freeze_gate_matrix.csv",
        S12_FREEZE / "next_board_queue.csv",
        S13_UQ / "same_qoi_temporal_uq_case_rows.csv",
        S13_UQ / "same_qoi_temporal_uq_summary.csv",
        S13_MESH / "candidate_triplet_reconciliation.csv",
        S13_MESH / "qoi_reconciliation_summary.csv",
        S13_ENDPOINT / "endpoint_mask_derivation_gate.csv",
        MF16_SOURCE / "row_level_release_candidate_matrix.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S12/S13 blocker-unlock inputs: " + "; ".join(missing))


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("case_id", ""): row for row in rows}


def by_case_qoi(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row.get("case_id", ""), row.get("qoi_label", "")): row for row in rows}


def build_tp_join() -> list[dict[str, Any]]:
    tp_context = by_case(read_csv(S12_TP / "s12_tp_priority_context.csv"))
    exchange = by_case(read_csv(S12_TP / "s12_tp_exchange_evidence_table.csv"))
    uq_case = by_case_qoi(read_csv(S13_UQ / "same_qoi_temporal_uq_case_rows.csv"))
    source_rows = {
        row.get("normalized_case_id", ""): row for row in read_csv(MF16_SOURCE / "row_level_release_candidate_matrix.csv")
    }

    rows: list[dict[str, Any]] = []
    for case_id in ["salt_2", "salt_3", "salt_4"]:
        tp = tp_context[case_id]
        ex = exchange[case_id]
        qwall = uq_case[(case_id, "Q_wall_W")]
        mdot = uq_case[(case_id, "mdot_exchange_positive_outward_proxy_kg_s")]
        tau = uq_case[(case_id, "tau_recirc_proxy_s")]
        contrast = uq_case[(case_id, "wall_core_bulk_temperature_contrast_K")]
        source = source_rows[case_id]

        qwall_target = fnum(qwall.get("target_value"))
        source_q = fnum(ex.get("source_side_q_net_W"))
        qwall_to_source = qwall_target / source_q if qwall_target is not None and source_q not in (None, 0.0) else None
        source_minus_qwall = source_q - qwall_target if source_q is not None and qwall_target is not None else None

        rows.append(
            {
                "case_id": case_id,
                "tp_rmse_K": tp.get("tp_rmse_K", ""),
                "tw_rmse_K": tp.get("tw_rmse_K", ""),
                "tp_mean_signed_error_K": tp.get("tp_mean_signed_error_K", ""),
                "retained_window_s": ex.get("time_window_s", ""),
                "Q_wall_W_target": qwall.get("target_value", ""),
                "Q_wall_temporal_rel_unc_percent": qwall.get("relative_max_abs_neighbor_delta_percent", ""),
                "source_side_q_net_W": ex.get("source_side_q_net_W", ""),
                "Q_wall_over_source_side_q": fmt(qwall_to_source),
                "source_side_minus_Q_wall_W": fmt(source_minus_qwall),
                "mdot_exchange_positive_outward_proxy_kg_s": ex.get("mdot_exchange_positive_outward_proxy_kg_s", ""),
                "mdot_temporal_rel_unc_percent": mdot.get("relative_max_abs_neighbor_delta_percent", ""),
                "tau_recirc_proxy_s": ex.get("tau_recirc_proxy_s", ""),
                "tau_temporal_rel_unc_percent": tau.get("relative_max_abs_neighbor_delta_percent", ""),
                "wall_core_bulk_temperature_contrast_K": contrast.get("target_value", ""),
                "contrast_temporal_rel_unc_percent": contrast.get("relative_max_abs_neighbor_delta_percent", ""),
                "source_property_release_ready": source.get("release_ready", ""),
                "source_property_primary_blocker": source.get("primary_blocker", ""),
                "claim_status": "diagnostic_join_complete_no_release_no_freeze",
            }
        )
    return rows


def build_source_overlay() -> list[dict[str, Any]]:
    source_rows = read_csv(MF16_SOURCE / "row_level_release_candidate_matrix.csv")
    freeze_rows = read_csv(S12_FREEZE / "candidate_freeze_gate_matrix.csv")
    s13_freeze = next(row for row in freeze_rows if row.get("candidate_family") == "S13_upcomer_exchange_cell")
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        case_id = row.get("normalized_case_id", "")
        if case_id not in {"salt_2", "salt_3", "salt_4"}:
            continue
        rows.append(
            {
                "case_id": case_id,
                "property_mode": row.get("property_mode", ""),
                "source_validity_envelope_status": row.get("source_validity_envelope_status", ""),
                "source_use_category": row.get("source_use_category", ""),
                "source_property_gate_status": row.get("source_property_gate_status", ""),
                "release_ready": row.get("release_ready", ""),
                "protected_row_release": row.get("protected_row_release", ""),
                "final_fit_allowed": row.get("final_fit_allowed", ""),
                "final_model_selection_allowed": row.get("final_model_selection_allowed", ""),
                "s12_s13_freeze_ready": s13_freeze.get("freeze_ready", ""),
                "combined_release_decision": "fail_closed_no_source_property_release",
                "primary_blocker": row.get("primary_blocker", ""),
                "next_action": row.get("next_action", ""),
            }
        )
    return rows


def build_s13_disposition() -> list[dict[str, Any]]:
    uq_summary = read_csv(S13_UQ / "same_qoi_temporal_uq_summary.csv")
    mesh_summary = read_csv(S13_MESH / "qoi_reconciliation_summary.csv")
    endpoint_gate = read_csv(S13_ENDPOINT / "endpoint_mask_derivation_gate.csv")

    temporal_ready = sum(1 for row in uq_summary if row.get("same_qoi_temporal_uq_status") == "executed")
    mesh_ready = sum(1 for row in mesh_summary if row.get("admission_allowed") == "True")
    endpoint_released = sum(int(row.get("released_endpoint_masks", "0") or 0) for row in endpoint_gate)
    qwall_mesh = next(row for row in mesh_summary if row.get("qoi_label") == "Q_wall_W")

    return [
        {
            "blocker": "s13_same_qoi_temporal_uq",
            "current_status": "diagnostic_pass",
            "evidence_count": temporal_ready,
            "release_ready": "false",
            "production_use_allowed": "false",
            "why": "same-QOI temporal neighbor UQ executed for 4 labels, but admission remains closed",
            "next_action": "use as uncertainty support after mesh/GCI and source/property gates pass",
        },
        {
            "blocker": "s13_same_label_mesh_gci",
            "current_status": "blocked_coarse_equivalence_not_admitted",
            "evidence_count": mesh_ready,
            "release_ready": "false",
            "production_use_allowed": "false",
            "why": "candidate coarse/medium/fine rows are quantified, but admitted same-label coarse rows are 0",
            "next_action": "resolve strict same-label coarse equivalence or run clean same-label sampler family",
        },
        {
            "blocker": "s13_qwall_low_spread_not_release",
            "current_status": "diagnostic_support_only",
            "evidence_count": 3,
            "release_ready": "false",
            "production_use_allowed": "false",
            "why": (
                "Q_wall_W has low medium/fine spread "
                f"{qwall_mesh.get('max_medium_fine_relative_percent_vs_fine')} percent, "
                "but coarse equivalence/source-property gates are not admitted"
            ),
            "next_action": "keep Q_wall_W as strongest diagnostic lane; do not fit exchange coefficient yet",
        },
        {
            "blocker": "s13_throughflow_endpoint_geometry",
            "current_status": "blocked_candidate_masks_only",
            "evidence_count": endpoint_released,
            "release_ready": "false",
            "production_use_allowed": "false",
            "why": "candidate endpoint masks exist, but released endpoint masks with area vectors/normals/owner cells are 0",
            "next_action": "enrich/regenerate endpoint geometry table before mdot/T_bulk endpoint harvest",
        },
        {
            "blocker": "s13_s12_source_property_cp",
            "current_status": "blocked_no_nominal_train_source_property_release",
            "evidence_count": 0,
            "release_ready": "false",
            "production_use_allowed": "false",
            "why": "MF16 reports release-ready nominal source/property rows 0/4",
            "next_action": "recover row-specific strict source-envelope and cp/mu/k/source labels before S11/S15/S12 freeze",
        },
    ]


def build_next_actions() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "lane": "S12",
            "action": "TP-first retained-window join",
            "status_after_this_packet": "completed_diagnostic_join",
            "local_or_compute": "local_complete",
            "required_output": "s12_tp_retained_window_exchange_join.csv",
            "forbidden": "no protected scoring; no coefficient fit; no source-side Q relabel as wallHeatFlux",
        },
        {
            "rank": 2,
            "lane": "S13",
            "action": "Endpoint geometry enrichment",
            "status_after_this_packet": "next_blocker",
            "local_or_compute": "local_if_geometry_tables_exist_else_compute",
            "required_output": "released inlet/outlet endpoint masks with face_id, area vector, owner cell, normal convention, positive mdot convention",
            "forbidden": "no proxy planes; no endpoint harvest until release-grade masks exist",
        },
        {
            "rank": 3,
            "lane": "S13",
            "action": "Clean same-label sampler rerun or strict coarse-equivalence resolution",
            "status_after_this_packet": "compute_or_strict_audit_required",
            "local_or_compute": "scheduler_for_sampler; local_for_equivalence_audit_if evidence exists",
            "required_output": "accepted same-label coarse/medium/fine rows for Q_wall_W and exchange labels",
            "forbidden": "do not borrow unrelated GCI or use cancelled partial outputs as production evidence",
        },
        {
            "rank": 4,
            "lane": "S12/S13",
            "action": "Row-specific source/property/cp release recovery",
            "status_after_this_packet": "blocked_no_release",
            "local_or_compute": "local_evidence_recovery_first",
            "required_output": "strict-pass source envelope, cp/mu/k mode, pressure/enthalpy basis, runtime-use permission per case",
            "forbidden": "no broad release; no protected-row release; no hidden multiplier",
        },
        {
            "rank": 5,
            "lane": "S12",
            "action": "Freeze review",
            "status_after_this_packet": "closed",
            "local_or_compute": "local_only_after_gates_pass",
            "required_output": "runtime-legal candidate with production harvest, source/property release, same-QOI UQ, and split permission",
            "forbidden": "no final score or freeze from diagnostic TP/exchange evidence",
        },
    ]


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    tp_join = build_tp_join()
    source_overlay = build_source_overlay()
    s13_disposition = build_s13_disposition()
    next_actions = build_next_actions()

    write_csv(
        OUT / "s12_tp_retained_window_exchange_join.csv",
        tp_join,
        [
            "case_id",
            "tp_rmse_K",
            "tw_rmse_K",
            "tp_mean_signed_error_K",
            "retained_window_s",
            "Q_wall_W_target",
            "Q_wall_temporal_rel_unc_percent",
            "source_side_q_net_W",
            "Q_wall_over_source_side_q",
            "source_side_minus_Q_wall_W",
            "mdot_exchange_positive_outward_proxy_kg_s",
            "mdot_temporal_rel_unc_percent",
            "tau_recirc_proxy_s",
            "tau_temporal_rel_unc_percent",
            "wall_core_bulk_temperature_contrast_K",
            "contrast_temporal_rel_unc_percent",
            "source_property_release_ready",
            "source_property_primary_blocker",
            "claim_status",
        ],
    )
    write_csv(
        OUT / "source_property_legality_overlay.csv",
        source_overlay,
        [
            "case_id",
            "property_mode",
            "source_validity_envelope_status",
            "source_use_category",
            "source_property_gate_status",
            "release_ready",
            "protected_row_release",
            "final_fit_allowed",
            "final_model_selection_allowed",
            "s12_s13_freeze_ready",
            "combined_release_decision",
            "primary_blocker",
            "next_action",
        ],
    )
    write_csv(
        OUT / "s13_blocker_disposition.csv",
        s13_disposition,
        ["blocker", "current_status", "evidence_count", "release_ready", "production_use_allowed", "why", "next_action"],
    )
    write_csv(
        OUT / "next_action_contract.csv",
        next_actions,
        ["rank", "lane", "action", "status_after_this_packet", "local_or_compute", "required_output", "forbidden"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native_solver_outputs_mutated", "value": "false"},
            {"guardrail": "registry_mutated", "value": "false"},
            {"guardrail": "scheduler_action", "value": "false"},
            {"guardrail": "source_property_or_qwall_release", "value": "false"},
            {"guardrail": "residual_value_release", "value": "false"},
            {"guardrail": "coefficient_fit_or_admission", "value": "false"},
            {"guardrail": "protected_or_final_scoring", "value": "false"},
            {"guardrail": "candidate_freeze", "value": "false"},
            {"guardrail": "s11_s12_s13_s15_s6_trigger", "value": "false"},
        ],
        ["guardrail", "value"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"source_path": rel(S12_TP / "s12_tp_priority_context.csv"), "exists": "true", "use": "read-only S12 TP context"},
            {"source_path": rel(S12_TP / "s12_tp_exchange_evidence_table.csv"), "exists": "true", "use": "read-only S12 exchange retained-window context"},
            {"source_path": rel(S13_UQ / "same_qoi_temporal_uq_case_rows.csv"), "exists": "true", "use": "read-only S13 same-QOI temporal UQ"},
            {"source_path": rel(S13_MESH / "qoi_reconciliation_summary.csv"), "exists": "true", "use": "read-only S13 mesh/GCI blocker context"},
            {"source_path": rel(S13_ENDPOINT / "endpoint_mask_derivation_gate.csv"), "exists": "true", "use": "read-only S13 endpoint geometry blocker context"},
            {"source_path": rel(MF16_SOURCE / "row_level_release_candidate_matrix.csv"), "exists": "true", "use": "read-only source/property legality"},
        ],
        ["source_path", "exists", "use"],
    )

    summary = {
        "task": TASK_ID,
        "decision": "s12_s13_blocker_progress_diagnostic_join_complete_release_gates_closed",
        "s12_tp_join_rows": len(tp_join),
        "source_property_overlay_rows": len(source_overlay),
        "s13_blocker_rows": len(s13_disposition),
        "next_action_rows": len(next_actions),
        "source_property_release_ready_rows": sum(1 for row in source_overlay if row.get("release_ready") == "True"),
        "s13_production_ready_blockers": sum(1 for row in s13_disposition if row.get("production_use_allowed") == "true"),
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "residual_value_release_rows": 0,
        "candidate_freeze_rows": 0,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_json(OUT / "summary.json", summary)

    readme = f"""---
provenance:
  - {rel(S12_TP / 's12_tp_exchange_evidence_table.csv')}
  - {rel(S13_UQ / 'same_qoi_temporal_uq_case_rows.csv')}
  - {rel(S13_MESH / 'qoi_reconciliation_summary.csv')}
  - {rel(MF16_SOURCE / 'row_level_release_candidate_matrix.csv')}
tags: [work-product, s12, s13, tp-first, upcomer-exchange, blocker-unlock, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s12-s13-tp-exchange-blocker-unlock.md
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Implementer / Tester / Writer
type: work_product
status: complete
---
# S12/S13 TP-Exchange Blocker Unlock

Decision: `s12_s13_blocker_progress_diagnostic_join_complete_release_gates_closed`.

This package completes the local S12 TP-first retained-window join against S13
exchange/Qwall temporal-UQ evidence. It also overlays source/property legality
and reduces the remaining S13 blockers to exact next actions.

What moved:

- S12 TP retained-window exchange join rows: `{len(tp_join)}`.
- Source/property legality overlay rows: `{len(source_overlay)}`.
- S13 blocker disposition rows: `{len(s13_disposition)}`.
- Release-ready source/property rows: `0`.
- S13 production-ready blocker rows: `0`.

The strongest diagnostic fact remains: retained-window `Q_wall_W` has very low
temporal uncertainty and low medium/fine spread, but this is not enough for a
production exchange-cell model. Coarse equivalence, endpoint geometry,
row-specific source/property/cp, and residual-complete energy accounting remain
closed.

Next action: enrich S13 endpoint geometry or resolve strict same-label
coarse/medium/fine evidence, then revisit source/property release before any
S12 freeze or S13 harvest/admission step.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
