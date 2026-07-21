#!/usr/bin/env python3
"""Build AGENT-455 closure-QOI / leg-specific Internal-Nu resolution package.

This pass answers the current blocker question with generated evidence:

* the test section is treated as a span inside the upcomer, not a separate
  ordinary-pipe leg;
* each physical leg receives a distinct future Nu/model-form lane;
* current rows are admitted only if geometry, recirculation, residual ownership,
  sign/heat balance, and mesh/GCI gates all pass.

The script is read-only with respect to native CFD outputs, registry/admission
state, scheduler state, and external Fluid sources.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-455"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution")
OUT = ROOT / OUT_REL

BRANCH_MASK = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard"
    / "branch_specific_fit_mask.csv"
)
ORDINARY_ROWS = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard"
    / "ordinary_pipe_candidate_rows.csv"
)
THERMAL_GATE = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate"
    / "thermal_row_admission_gate.csv"
)
CLOSURE_QOI_PUNCH = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_punch_list"
    / "closure_qoi_blocker_punch_list.csv"
)
THERMAL_PARITY_README = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate"
    / "README.md"
)
BRANCH_SCORECARD_README = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard"
    / "README.md"
)
GEOMETRY_MAP = ROOT / "operational_notes/maps/geometry-and-mesh-truth.md"
THERMAL_MAP = ROOT / "operational_notes/maps/thermal-closures-and-internal-nu.md"
FORWARD_MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"

RECIRCULATION_THRESHOLD = 0.20
FORBIDDEN_BLOCKER_TOKENS = {
    "blocked_downcomer_policy",
    "coarse_sign_review_required",
    "fine_sign_review_required",
    "high_recirculation_forward_bulk_used",
    "high_recirculation_interface",
    "high_recirculation_interface_temperature",
    "internal_Nu_residual_absorption_forbidden",
    "large_wallHeatFlux_enthalpy_residual",
    "medium_sign_review_required",
    "missing_or_nonfinite_coarse_medium_or_fine_value",
    "repaired_q_sign_label_conflict",
    "wallHeatFlux_enthalpy_opposed_direction",
}

SOURCE_PATHS = {
    "branch_mask": BRANCH_MASK,
    "ordinary_rows": ORDINARY_ROWS,
    "thermal_gate": THERMAL_GATE,
    "closure_qoi_punch": CLOSURE_QOI_PUNCH,
    "thermal_parity_readme": THERMAL_PARITY_README,
    "branch_scorecard_readme": BRANCH_SCORECARD_README,
    "geometry_map": GEOMETRY_MAP,
    "thermal_map": THERMAL_MAP,
    "forward_map": FORWARD_MAP,
}

GEOMETRY_COLUMNS = [
    "canonical_leg_id",
    "span_or_segment",
    "parent_geometry",
    "upcomer_member",
    "old_or_ambiguous_label",
    "corrected_modeling_lane",
    "nu_fit_lane",
    "basis",
    "source_path",
]
MODEL_FORM_COLUMNS = [
    "canonical_leg_id",
    "leg_role",
    "current_model_form",
    "future_internal_nu_correlation_lane",
    "fit_allowed_now",
    "required_before_fit",
    "litrev_methodology_rule",
    "current_evidence_status",
]
CANDIDATE_COLUMNS = [
    "candidate_id",
    "source_table",
    "case_id",
    "split_role",
    "reported_segment_or_span",
    "canonical_leg_id",
    "upcomer_member",
    "qoi",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "review_admission_class",
    "residual_owner_gate",
    "mesh_gci_gate",
    "sign_heat_balance_gate",
    "recirculation_gate",
    "internal_nu_fit_allowed_now",
    "admission_class",
    "reason",
    "source_path",
]
UPCOMER_COLUMNS = [
    "evidence_id",
    "case_key",
    "reported_location_or_span",
    "corrected_parent_leg",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "allowed_label_now",
    "excluded_single_stream_labels",
    "reason",
    "source_path",
]
SIGN_COLUMNS = [
    "canonical_leg_id",
    "reported_segment",
    "qoi",
    "review_admission_class",
    "sign_heat_balance_gate",
    "blocking_tokens",
    "next_action",
    "source_path",
]
MESH_COLUMNS = [
    "qoi_id",
    "reported_span_or_segment",
    "canonical_leg_id",
    "qoi_family",
    "quantity",
    "current_publication_ready",
    "current_fit_admissible",
    "complete_triplet",
    "gci_status",
    "final_use_decision",
    "resolution_action",
    "source_paths",
]
BLOCKER_COLUMNS = [
    "blocker_id",
    "decision",
    "can_update_blocker_register",
    "resolved_by",
    "resolved_on",
    "criteria_passed",
    "criteria_failed",
    "scientific_interpretation",
    "next_unlock_sequence",
]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: format_value(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "pass"}


def numeric(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def blocker_tokens(blockers: str) -> set[str]:
    return {token.strip() for token in blockers.split(";") if token.strip()}


def canonical_leg(segment_or_span: str) -> str:
    key = segment_or_span.strip()
    mapping = {
        "downcomer": "downcomer_right_vertical",
        "right_leg": "downcomer_right_vertical",
        "lower_leg": "heater_lower_leg",
        "heater": "heater_lower_leg",
        "upper_leg": "cooler_hx_branch",
        "cooler": "cooler_hx_branch",
        "left_lower_leg": "upcomer_left_vertical",
        "left_upper_leg": "upcomer_left_vertical",
        "test_section": "upcomer_left_vertical",
        "test_section_complex": "upcomer_left_vertical",
        "test_section_span": "upcomer_left_vertical",
        "upcomer": "upcomer_left_vertical",
        "upcomer_inlet": "upcomer_left_vertical",
        "upcomer_mid": "upcomer_left_vertical",
        "upcomer_outlet": "upcomer_left_vertical",
    }
    return mapping.get(key, key or "unknown")


def is_upcomer_member(segment_or_span: str, leg: str | None = None) -> bool:
    leg_id = leg or canonical_leg(segment_or_span)
    return leg_id == "upcomer_left_vertical"


def geometry_taxonomy_rows() -> list[dict[str, Any]]:
    source = rel(GEOMETRY_MAP)
    basis = "owner-locked segment map: upcomer = left_lower_leg + test_section_span + left_upper_leg"
    return [
        {
            "canonical_leg_id": "heater_lower_leg",
            "span_or_segment": "lower_leg",
            "parent_geometry": "heated lower/incline leg",
            "upcomer_member": "no",
            "old_or_ambiguous_label": "lower_leg",
            "corrected_modeling_lane": "heater/source-region leg",
            "nu_fit_lane": "distinct source-region Nu only after source/sign/mesh gates",
            "basis": "mesh-truth lower_leg is heater, not probe schematic lower leg",
            "source_path": source,
        },
        {
            "canonical_leg_id": "downcomer_right_vertical",
            "span_or_segment": "right_leg; downcomer",
            "parent_geometry": "right vertical downcomer",
            "upcomer_member": "no",
            "old_or_ambiguous_label": "right_leg/downcomer",
            "corrected_modeling_lane": "ordinary/developing downcomer leg",
            "nu_fit_lane": "distinct downcomer Nu after low-recirculation, sign, and mesh gates",
            "basis": "mesh-truth right_leg is downcomer",
            "source_path": source,
        },
        {
            "canonical_leg_id": "cooler_hx_branch",
            "span_or_segment": "upper_leg",
            "parent_geometry": "upper cooler/HX branch",
            "upcomer_member": "no",
            "old_or_ambiguous_label": "upper_leg",
            "corrected_modeling_lane": "cooler/HX boundary leg",
            "nu_fit_lane": "HX/UA boundary first; internal Nu later only if separable",
            "basis": "setup-only cooler/HX lane is separated from internal Nu",
            "source_path": rel(THERMAL_PARITY_README),
        },
        {
            "canonical_leg_id": "upcomer_left_vertical",
            "span_or_segment": "left_lower_leg",
            "parent_geometry": "upcomer",
            "upcomer_member": "yes",
            "old_or_ambiguous_label": "left_lower_leg",
            "corrected_modeling_lane": "upcomer recirculation/hybrid lane",
            "nu_fit_lane": "section-effective diagnostic; no single-stream fit under recirculation",
            "basis": basis,
            "source_path": source,
        },
        {
            "canonical_leg_id": "upcomer_left_vertical",
            "span_or_segment": "test_section_span",
            "parent_geometry": "upcomer",
            "upcomer_member": "yes",
            "old_or_ambiguous_label": "test_section",
            "corrected_modeling_lane": "upcomer test-section subspan",
            "nu_fit_lane": "upcomer hybrid/onset lane, not separate ordinary-pipe Nu",
            "basis": basis,
            "source_path": source,
        },
        {
            "canonical_leg_id": "upcomer_left_vertical",
            "span_or_segment": "left_upper_leg",
            "parent_geometry": "upcomer",
            "upcomer_member": "yes",
            "old_or_ambiguous_label": "left_upper_leg",
            "corrected_modeling_lane": "upcomer recirculation/hybrid lane",
            "nu_fit_lane": "section-effective diagnostic; no single-stream fit under recirculation",
            "basis": basis,
            "source_path": source,
        },
        {
            "canonical_leg_id": "junction_stub_connector",
            "span_or_segment": "junction/stub/connector",
            "parent_geometry": "named local component",
            "upcomer_member": "no",
            "old_or_ambiguous_label": "junction/stub/connector",
            "corrected_modeling_lane": "named loss/storage/boundary term",
            "nu_fit_lane": "no ordinary-pipe Nu correlation",
            "basis": "not a straight pipe span",
            "source_path": rel(BRANCH_SCORECARD_README),
        },
    ]


def model_form_rows(branch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_branch = {row.get("branch_id", ""): row for row in branch_rows}
    rows = [
        {
            "canonical_leg_id": "heater_lower_leg",
            "leg_role": "source-region leg",
            "current_model_form": "heater source model plus wall/layer loss; setup-only source inputs only",
            "future_internal_nu_correlation_lane": "developing/mixed-convection source-region Nu with source residual separated",
            "fit_allowed_now": "no",
            "required_before_fit": "branch-local sign, enthalpy, source-ownership, residual, and mesh/GCI admission",
            "litrev_methodology_rule": "separate imposed source, wall/layer path, storage, and internal convection",
            "current_evidence_status": by_branch.get("heater_lower_leg", {}).get("ordinary_pipe_fit_allowed_now", "waiting_on_branch_rows"),
        },
        {
            "canonical_leg_id": "downcomer_right_vertical",
            "leg_role": "non-source ordinary/developing leg",
            "current_model_form": "external loss or wall-layer model; no internal Nu fit until heat-balance gate",
            "future_internal_nu_correlation_lane": "downcomer-specific natural/mixed convection Nu after low-recirculation admission",
            "fit_allowed_now": "no",
            "required_before_fit": "downcomer policy, low recirculation, heat-balance/sign, same-QOI triplet/GCI",
            "litrev_methodology_rule": "ordinary-pipe correlations require single-stream control volume and admitted drive temperature",
            "current_evidence_status": by_branch.get("downcomer_right_vertical", {}).get("ordinary_pipe_fit_allowed_now", "waiting_on_branch_rows"),
        },
        {
            "canonical_leg_id": "cooler_hx_branch",
            "leg_role": "HX/boundary leg",
            "current_model_form": "setup-only HX/cooler UA or effectiveness lane",
            "future_internal_nu_correlation_lane": "cooler-side internal Nu only after HX removal and shell/boundary residual are separated",
            "fit_allowed_now": "no",
            "required_before_fit": "active-shell/boundary state, sign/heat-balance, non-leaky runtime inputs, mesh/GCI",
            "litrev_methodology_rule": "do not let internal Nu absorb heat-exchanger duty or external sink residual",
            "current_evidence_status": by_branch.get("cooler_hx_branch", {}).get("ordinary_pipe_fit_allowed_now", "waiting_on_branch_rows"),
        },
        {
            "canonical_leg_id": "upcomer_left_vertical",
            "leg_role": "recirculating upcomer including test section",
            "current_model_form": "throughflow plus recirculation-cell/onset model; not single-stream ordinary pipe",
            "future_internal_nu_correlation_lane": "hybrid recirculation/onset or section-effective diagnostic lane",
            "fit_allowed_now": "no",
            "required_before_fit": "observed/bracketed onset and low-RAF/RMF sublane, or explicit hybrid model validation",
            "litrev_methodology_rule": "use recirculation diagnostics when a single bulk stream is not physically valid",
            "current_evidence_status": by_branch.get("upcomer_left_vertical", {}).get("ordinary_pipe_fit_allowed_now", "no"),
        },
        {
            "canonical_leg_id": "junction_stub_connector",
            "leg_role": "named local component",
            "current_model_form": "named K/reset/development term, not ordinary straight-pipe coefficient",
            "future_internal_nu_correlation_lane": "none unless a physical heat-storage/loss element is separately admitted",
            "fit_allowed_now": "no",
            "required_before_fit": "separate named component contract",
            "litrev_methodology_rule": "do not fit pipe correlations to non-pipe elements",
            "current_evidence_status": by_branch.get("junction_stub_connector", {}).get("ordinary_pipe_fit_allowed_now", "no"),
        },
    ]
    return rows


def recirculation_gate_for(row: dict[str, str], segment: str, leg: str) -> tuple[str, str]:
    raf = numeric(row.get("reverse_area_fraction"))
    rmf = numeric(row.get("reverse_mass_fraction"))
    if is_upcomer_member(segment, leg):
        return "fail", "upcomer/test-section parent is recirculation hybrid lane"
    if raf is not None and raf >= RECIRCULATION_THRESHOLD:
        return "fail", f"reverse_area_fraction >= {RECIRCULATION_THRESHOLD}"
    if rmf is not None and rmf >= RECIRCULATION_THRESHOLD:
        return "fail", f"reverse_mass_fraction >= {RECIRCULATION_THRESHOLD}"
    if raf is None and rmf is None:
        return "unknown", "no branch-local recirculation metric"
    return "pass", "low recirculation metric"


def sign_heat_gate(blockers: str, review_class: str) -> tuple[str, str]:
    tokens = blocker_tokens(blockers)
    hits = sorted(tokens & FORBIDDEN_BLOCKER_TOKENS)
    if hits:
        return "fail", ";".join(hits)
    if review_class.strip().lower() == "fit_admissible":
        return "pass", ""
    if review_class.strip().lower() in {"validation_only", "diagnostic"}:
        return "not_admitted", ""
    return "fail", review_class or "missing_review_class"


def mesh_gate_for_current() -> str:
    # AGENT-450 found zero admitted-only mesh/GCI candidates; current Internal-Nu
    # rows therefore cannot pass a publication mesh/GCI gate today.
    return "fail_no_current_admitted_mesh_gci"


def evaluate_candidate(
    candidate_id: str,
    source_table: str,
    row: dict[str, str],
    segment: str,
    qoi: str,
    source_path: str,
) -> dict[str, Any]:
    leg = canonical_leg(segment)
    blockers = row.get("blockers", "")
    review_class = row.get("review_admission_class") or row.get("admission_class") or row.get("ordinary_pipe_fit_allowed_now", "")
    residual_gate = row.get("residual_owner_gate", "missing")
    sign_gate, sign_reason = sign_heat_gate(blockers, review_class)
    recirc_gate, recirc_reason = recirculation_gate_for(row, segment, leg)
    is_internal_nu_qoi = qoi.strip().lower() == "nu"
    declared_allowed = truthy(row.get("internal_nu_fit_allowed", row.get("internal_nu_fit_allowed_now", "")))
    mesh_gate = mesh_gate_for_current()
    fit_allowed = all(
        [
            is_internal_nu_qoi,
            declared_allowed,
            residual_gate == "pass",
            sign_gate == "pass",
            recirc_gate == "pass",
            mesh_gate == "pass",
            not is_upcomer_member(segment, leg),
        ]
    )
    reasons: list[str] = []
    if not is_internal_nu_qoi:
        reasons.append("not_internal_Nu_qoi")
    if not declared_allowed:
        reasons.append("source_gate_does_not_allow_internal_Nu_fit")
    if residual_gate != "pass":
        reasons.append(f"residual_owner_gate={residual_gate}")
    if sign_gate != "pass":
        reasons.append(f"sign_heat_balance_gate={sign_gate}:{sign_reason}")
    if recirc_gate != "pass":
        reasons.append(f"recirculation_gate={recirc_gate}:{recirc_reason}")
    if mesh_gate != "pass":
        reasons.append(mesh_gate)
    if is_upcomer_member(segment, leg):
        reasons.append("test_section_and_left_spans_are_upcomer_hybrid_lane")

    if fit_allowed:
        admission = "fit_admissible_internal_nu"
        reason = "all gates pass"
    elif is_upcomer_member(segment, leg):
        admission = "hybrid_recirculation_lane_only"
        reason = ";".join(reasons)
    elif "waiting_on_branch_rows" in review_class:
        admission = "waiting_on_branch_rows"
        reason = ";".join(reasons)
    elif review_class == "validation_only":
        admission = "validation_only_nonfit"
        reason = ";".join(reasons)
    else:
        admission = "blocked_or_diagnostic_nonfit"
        reason = ";".join(reasons)

    return {
        "candidate_id": candidate_id,
        "source_table": source_table,
        "case_id": row.get("case_id", row.get("case_key", "")),
        "split_role": row.get("split_role", ""),
        "reported_segment_or_span": segment,
        "canonical_leg_id": leg,
        "upcomer_member": is_upcomer_member(segment, leg),
        "qoi": qoi,
        "reverse_area_fraction": row.get("reverse_area_fraction", ""),
        "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
        "review_admission_class": review_class,
        "residual_owner_gate": residual_gate,
        "mesh_gci_gate": mesh_gate,
        "sign_heat_balance_gate": sign_gate,
        "recirculation_gate": recirc_gate,
        "internal_nu_fit_allowed_now": fit_allowed,
        "admission_class": admission,
        "reason": reason,
        "source_path": source_path,
    }


def candidate_rows(
    thermal_rows: list[dict[str, str]],
    ordinary_rows: list[dict[str, str]],
    branch_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    thermal_source = rel(THERMAL_GATE)
    for row in thermal_rows:
        segment = row.get("segment", "")
        qoi = row.get("qoi", "")
        rows.append(
            evaluate_candidate(
                f"thermal:{row.get('case_id', '')}:{segment}:{qoi}",
                "thermal_row_admission_gate",
                row,
                segment,
                qoi,
                thermal_source,
            )
        )
    ordinary_source = rel(ORDINARY_ROWS)
    for row in ordinary_rows:
        segment = row.get("location_or_span", "") or row.get("branch_id", "")
        qoi = "Nu" if "Nu" in row.get("invalid_single_stream_labels", "") or "Nu" in row.get("allowed_label_now", "") else "ordinary_pipe_label"
        rows.append(
            evaluate_candidate(
                row.get("evidence_id", f"ordinary:{segment}"),
                "ordinary_pipe_candidate_rows",
                row,
                segment,
                qoi,
                ordinary_source,
            )
        )
    branch_source = rel(BRANCH_MASK)
    for row in branch_rows:
        branch_id = row.get("branch_id", "")
        synthetic = {
            "case_id": "branch_level",
            "ordinary_pipe_fit_allowed_now": row.get("ordinary_pipe_fit_allowed_now", ""),
            "review_admission_class": row.get("ordinary_pipe_fit_allowed_now", ""),
            "internal_nu_fit_allowed": "false",
        }
        rows.append(
            evaluate_candidate(
                f"branch:{branch_id}",
                "branch_specific_fit_mask",
                synthetic,
                branch_id,
                "Nu",
                branch_source,
            )
        )
    return rows


def upcomer_exclusion_rows(ordinary_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in ordinary_rows:
        segment = row.get("location_or_span", "") or row.get("branch_id", "")
        leg = canonical_leg(segment)
        if leg != "upcomer_left_vertical":
            continue
        rows.append(
            {
                "evidence_id": row.get("evidence_id", ""),
                "case_key": row.get("case_key", ""),
                "reported_location_or_span": segment,
                "corrected_parent_leg": "upcomer_left_vertical",
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "allowed_label_now": row.get("allowed_label_now", ""),
                "excluded_single_stream_labels": row.get("invalid_single_stream_labels", ""),
                "reason": "test section is an upcomer subspan; material recirculation invalidates single-stream Nu/f_D/K fit",
                "source_path": row.get("source_path", rel(ORDINARY_ROWS)),
            }
        )
    return rows


def sign_heat_balance_rows(thermal_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in thermal_rows:
        segment = row.get("segment", "")
        review_class = row.get("review_admission_class", "")
        sign_gate, reason = sign_heat_gate(row.get("blockers", ""), review_class)
        rows.append(
            {
                "canonical_leg_id": canonical_leg(segment),
                "reported_segment": segment,
                "qoi": row.get("qoi", ""),
                "review_admission_class": review_class,
                "sign_heat_balance_gate": sign_gate,
                "blocking_tokens": reason,
                "next_action": row.get("next_action", ""),
                "source_path": rel(THERMAL_GATE),
            }
        )
    return rows


def final_use_decision(row: dict[str, str]) -> tuple[str, str]:
    span = row.get("span") or row.get("segment")
    leg = canonical_leg(span)
    bucket = row.get("primary_bucket", "")
    if truthy(row.get("current_publication_ready")) and truthy(row.get("current_fit_admissible")):
        return "admitted_final_use", "can enter final closure set"
    if leg == "upcomer_left_vertical":
        return "diagnostic_only_upcomer_hybrid_lane", "do not use for single-stream Nu/f_D/K; use onset/hybrid diagnostics"
    if bucket == "thermal_admission_review_required":
        return "blocked_pending_sign_heat_balance_source_admission", row.get("admission_remaining", "")
    if bucket == "downcomer_policy_blocked":
        return "blocked_pending_downcomer_policy", row.get("admission_remaining", "")
    if bucket == "missing_triplet_extraction_or_reconciliation_required":
        return "blocked_pending_same_qoi_triplet_reconciliation", row.get("extraction_remaining", "")
    if bucket == "gci_failed_no_resolution_without_reextract_or_remesh":
        return "not_publication_gci_current_triplet_exclude_or_reextract", row.get("next_resolution_action", "")
    return "manual_review_required", row.get("next_resolution_action", "")


def mesh_gci_rows(punch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in punch_rows:
        span = row.get("span") or row.get("segment")
        decision, action = final_use_decision(row)
        rows.append(
            {
                "qoi_id": row.get("qoi_id", ""),
                "reported_span_or_segment": span,
                "canonical_leg_id": canonical_leg(span),
                "qoi_family": row.get("qoi_family", ""),
                "quantity": row.get("quantity", ""),
                "current_publication_ready": row.get("current_publication_ready", ""),
                "current_fit_admissible": row.get("current_fit_admissible", ""),
                "complete_triplet": row.get("complete_triplet", ""),
                "gci_status": row.get("gci_status", ""),
                "final_use_decision": decision,
                "resolution_action": action,
                "source_paths": row.get("source_paths", ""),
            }
        )
    return rows


def blocker_decision_rows(candidates: list[dict[str, Any]], mesh_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fit_rows = [row for row in candidates if truthy(row["internal_nu_fit_allowed_now"])]
    admitted_mesh = [row for row in mesh_rows if row["final_use_decision"] == "admitted_final_use"]
    unresolved_mesh = [
        row
        for row in mesh_rows
        if row["final_use_decision"]
        in {
            "blocked_pending_sign_heat_balance_source_admission",
            "blocked_pending_downcomer_policy",
            "blocked_pending_same_qoi_triplet_reconciliation",
            "not_publication_gci_current_triplet_exclude_or_reextract",
            "manual_review_required",
        }
    ]
    criteria_passed = [
        "test_section_span_canonicalized_as_upcomer",
        "per_leg_model_forms_defined",
        "upcomer_rows_excluded_from_single_stream_internal_Nu",
        "residual_owners_kept_separate_from_internal_Nu",
    ]
    criteria_failed = []
    if not fit_rows:
        criteria_failed.append("0_current_fit_admissible_internal_Nu_rows")
    if not admitted_mesh:
        criteria_failed.append("0_current_publication_ready_closure_QOI_GCI_rows")
    if unresolved_mesh:
        criteria_failed.append(f"{len(unresolved_mesh)}_mesh_or_admission_rows_still_unresolved")
    decision = "not_resolved"
    can_update = "yes_narrowing_update_only"
    interpretation = (
        "AGENT-455 removes the taxonomy ambiguity and prevents invalid upcomer/test-section Nu fitting, "
        "but current evidence still has no admitted Internal-Nu fit rows and no publication-ready closure-QOI GCI row."
    )
    return [
        {
            "blocker_id": "closure-qoi-mesh-gci",
            "decision": decision,
            "can_update_blocker_register": can_update,
            "resolved_by": rel(OUT),
            "resolved_on": "",
            "criteria_passed": ";".join(criteria_passed),
            "criteria_failed": ";".join(criteria_failed),
            "scientific_interpretation": interpretation,
            "next_unlock_sequence": (
                "1 correct/lock leg taxonomy; 2 admit branch-local sign/enthalpy/source rows; "
                "3 separate boundary/source/storage residuals; 4 admit same-QOI mesh triplets/GCI; "
                "5 fit distinct leg Nu only on rows that pass all gates"
            ),
        }
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    roles = {
        "branch_mask": "branch-level ordinary-pipe and thermal model-form gate",
        "ordinary_rows": "row-level recirculation and single-stream exclusion evidence",
        "thermal_gate": "thermal residual-owner/sign/heat-balance admission evidence",
        "closure_qoi_punch": "current mesh/GCI closure-QOI punch list",
        "thermal_parity_readme": "narrow parity-resolution interpretation",
        "branch_scorecard_readme": "branch-specific model-form provenance",
        "geometry_map": "canonical geometry taxonomy and test-section parent",
        "thermal_map": "current Internal-Nu status map",
        "forward_map": "predictive model blocker context",
    }
    return [
        {"source_id": key, "path": rel(path), "exists": path.exists(), "role": roles[key]}
        for key, path in SOURCE_PATHS.items()
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(BRANCH_MASK)}
  - {rel(ORDINARY_ROWS)}
  - {rel(THERMAL_GATE)}
  - {rel(CLOSURE_QOI_PUNCH)}
tags: [closure-qoi, mesh-gci, internal-nu, leg-specific-models, blocker-narrowing]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/geometry-and-mesh-truth.md
task: {TASK}
date: {DATE}
role: Coordinator/cfd-pp/Internal-Nu/Implementer/Tester/Writer
type: work_product
status: complete
---
# Closure-QOI Mesh-GCI Resolution and Leg-Specific Internal-Nu Admission

Generated: `{summary["generated_at"]}`

## Decision

`closure-qoi-mesh-gci`: `{summary["blocker_decision"]}`.

The taxonomy blocker is removed: `test_section_span` is part of
`upcomer_left_vertical`, so test-section rows cannot be treated as a separate
non-upcomer ordinary-pipe/Internal-Nu fit lane. The current scientific blocker
is not just upcomer recirculation; it is the absence of rows that pass all
leg-specific admission gates.

## Gate Results

- Leg-specific Internal-Nu candidates reviewed: `{summary["candidate_row_count"]}`.
- Fit-admissible Internal-Nu rows now: `{summary["fit_admissible_internal_nu_rows"]}`.
- Upcomer/test-section rows kept out of single-stream fitting: `{summary["upcomer_single_stream_exclusion_rows"]}`.
- Closure-QOI/GCI rows reviewed: `{summary["mesh_gci_row_count"]}`.
- Current publication-ready Closure-QOI/GCI rows: `{summary["publication_ready_mesh_gci_rows"]}`.
- Mesh/admission rows still unresolved: `{summary["unresolved_mesh_or_admission_rows"]}`.

## Methodology and Assumptions

The LitRev theory is applied as a gate sequence, not as a tuning shortcut:
separate source, boundary, wall/layer, radiation, storage, and branch-mixing
residuals before fitting internal convection. Each physical leg receives its own
model lane. A row can fit a leg-specific Nu correlation only when its geometry,
recirculation, sign/heat-balance, residual-owner, and mesh/GCI gates all pass.

## Outputs

- `geometry_taxonomy_correction.csv`
- `leg_specific_nu_model_form_matrix.csv`
- `leg_specific_internal_nu_candidate_rows.csv`
- `upcomer_exclusion_and_hybrid_lane.csv`
- `sign_heat_balance_gate.csv`
- `mesh_gci_gate_for_admitted_candidates.csv`
- `blocker_unblock_decision.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD solver outputs, registry/admission state, scheduler state, or
external `../cfd-modeling-tools/**` files were mutated.
"""
    (out / "README.md").write_text(readme, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    branch_rows = read_csv(BRANCH_MASK)
    ordinary = read_csv(ORDINARY_ROWS)
    thermal = read_csv(THERMAL_GATE)
    punch = read_csv(CLOSURE_QOI_PUNCH)

    geometry = geometry_taxonomy_rows()
    models = model_form_rows(branch_rows)
    candidates = candidate_rows(thermal, ordinary, branch_rows)
    upcomer = upcomer_exclusion_rows(ordinary)
    sign_rows = sign_heat_balance_rows(thermal)
    mesh_rows = mesh_gci_rows(punch)
    decisions = blocker_decision_rows(candidates, mesh_rows)
    manifest = source_manifest_rows()

    write_csv(out / "geometry_taxonomy_correction.csv", geometry, GEOMETRY_COLUMNS)
    write_csv(out / "leg_specific_nu_model_form_matrix.csv", models, MODEL_FORM_COLUMNS)
    write_csv(out / "leg_specific_internal_nu_candidate_rows.csv", candidates, CANDIDATE_COLUMNS)
    write_csv(out / "upcomer_exclusion_and_hybrid_lane.csv", upcomer, UPCOMER_COLUMNS)
    write_csv(out / "sign_heat_balance_gate.csv", sign_rows, SIGN_COLUMNS)
    write_csv(out / "mesh_gci_gate_for_admitted_candidates.csv", mesh_rows, MESH_COLUMNS)
    write_csv(out / "blocker_unblock_decision.csv", decisions, BLOCKER_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)

    fit_rows = [row for row in candidates if truthy(row["internal_nu_fit_allowed_now"])]
    publication_ready_mesh = [row for row in mesh_rows if row["final_use_decision"] == "admitted_final_use"]
    unresolved_mesh = [
        row
        for row in mesh_rows
        if row["final_use_decision"]
        not in {"admitted_final_use", "diagnostic_only_upcomer_hybrid_lane"}
    ]
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "blocker_decision": decisions[0]["decision"],
        "candidate_row_count": len(candidates),
        "candidate_admission_counts": dict(Counter(row["admission_class"] for row in candidates)),
        "fit_admissible_internal_nu_rows": len(fit_rows),
        "upcomer_single_stream_exclusion_rows": len(upcomer),
        "mesh_gci_row_count": len(mesh_rows),
        "publication_ready_mesh_gci_rows": len(publication_ready_mesh),
        "unresolved_mesh_or_admission_rows": len(unresolved_mesh),
        "mesh_final_use_counts": dict(Counter(row["final_use_decision"] for row in mesh_rows)),
        "test_section_parent_leg": "upcomer_left_vertical",
        "recirculation_threshold": RECIRCULATION_THRESHOLD,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_mutated": False,
    }
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build_package(args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
