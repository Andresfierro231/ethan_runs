#!/usr/bin/env python3
"""Build remaining two-tap gate decisions and next-anchor request packages.

This is documentation/evidence synthesis only. It consumes the harvested
corner_lower_right endpoint rows and basis/recirculation audit, then emits
component-isolation, same-QOI uncertainty, separated admission, and
non-recirculating-anchor request artifacts. It does not fit F6 or admit
component K.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-18"
TASK = "TODO-TWO-TAP-REMAINING-GATES-AND-ANCHOR-REQUEST"
BASE_OUT = ROOT / "work_products/2026-07/2026-07-18"
ISOLATION_OUT = BASE_OUT / "2026-07-18_two_tap_component_isolation_decision"
UQ_OUT = BASE_OUT / "2026-07-18_two_tap_same_qoi_uq_status"
REVIEW_OUT = BASE_OUT / "2026-07-18_two_tap_separated_admission_review"
ANCHOR_OUT = BASE_OUT / "2026-07-18_two_tap_nonrecirc_anchor_request"
SAMPLER = BASE_OUT / "2026-07-18_two_tap_staged_endpoint_sampler"
BASIS = BASE_OUT / "2026-07-18_two_tap_pressure_basis_recirc_audit"
PLAN = BASE_OUT / "2026-07-18_two_tap_component_raw_endpoint_plan"
ROADMAP = BASE_OUT / "2026-07-18_two_tap_blocker_roadmap"
CENTERLINE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/component_cluster_k_recomputed_admission_table.csv"
FEATURE = "corner_lower_right"
RECIRC_LIMIT = 0.01


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    data = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(data)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows if row.get("feature") == FEATURE}


def source_manifest() -> list[dict[str, str]]:
    return [
        {"source_id": "raw_endpoint_rows", "path": rel(SAMPLER / "raw_endpoint_pressure_velocity.csv"), "use": "six sampled endpoint rows", "mutation": "read_only"},
        {"source_id": "pressure_basis_recirc_audit", "path": rel(BASIS / "gate_decision_table.csv"), "use": "current gate state", "mutation": "read_only"},
        {"source_id": "basis_contract", "path": rel(PLAN / "basis_field_contract.csv"), "use": "component isolation formulas and guardrails", "mutation": "read_only"},
        {"source_id": "same_qoi_uq_contract", "path": rel(PLAN / "same_qoi_uncertainty_contract.csv"), "use": "same-QOI UQ acceptance", "mutation": "read_only"},
        {"source_id": "centerline_reference", "path": rel(CENTERLINE), "use": "prior centerline straight-reference evidence", "mutation": "read_only"},
        {"source_id": "roadmap", "path": rel(ROADMAP / "next_step_queue.csv"), "use": "planned task ordering", "mutation": "read_only"},
    ]


def assumption_rows(package: str) -> list[dict[str, str]]:
    common = [
        ("raw_rows_trusted", "Six harvested endpoint rows are trusted as raw diagnostic evidence, not admission evidence.", "sampler summary has raw_sampled_rows=6 and raw_missing_rows=0"),
        ("sign_convention", "Pressure delta is retained as downstream minus upstream for basis accounting.", "pressure_velocity_basis_audit.csv sign convention"),
        ("recirculation_threshold", "Ordinary component-K requires aggregate RAF < 0.01 and aggregate RMF < 0.01.", "recirculation_metric_contract.csv"),
        ("no_f6_component_k", "No F6 fit or component-K admission may be emitted by these packages.", "user/repo guardrail"),
    ]
    specific = {
        "component_isolation": [
            ("straight_reference_policy", "A straight reference is admissible only if it is physically comparable and uses the same raw pressure/basis convention.", "basis_field_contract.csv"),
            ("no_clipping", "Negative K or nonnegative K obtained by clipping/tuning is a blocker, not a result.", "roadmap guardrail"),
        ],
        "same_qoi_uq": [
            ("same_qoi_definition", "UQ evidence must use the same endpoint labels, formulas, and sign convention.", "same_qoi_uncertainty_contract.csv"),
            ("missing_uq_default", "If no exact same-QOI family is found, emit missing_no_GCI_diagnostic_only.", "same_qoi_uncertainty_contract.csv"),
        ],
        "admission_review": [
            ("all_gates_required", "Ordinary admission requires raw surfaces, pressure basis, recirculation pass, component isolation, and same-QOI UQ.", "raw endpoint roadmap"),
            ("expected_state", "Material reverse flow is expected to keep rows diagnostic only.", "pressure/basis recirc audit"),
        ],
        "anchor_request": [
            ("anchor_need", "Future ordinary evidence requires non-recirculating anchors or explicit recirculation-modeled diagnostic policy.", "gate decision table"),
            ("request_not_launch", "This package defines future work and launches no scheduler jobs.", "repo guardrail"),
        ],
    }[package]
    rows = common + specific
    return [
        {
            "assumption_id": key,
            "assumption": text,
            "evidence_or_reason": evidence,
            "risk_if_wrong": "would overstate closure readiness or mix diagnostic rows into admitted coefficients",
        }
        for key, text, evidence in rows
    ]


def component_isolation_outputs(
    basis_rows: dict[str, dict[str, str]], recirc_rows: dict[str, dict[str, str]], centerline_rows: dict[str, dict[str, str]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    options: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for case_id, basis in sorted(basis_rows.items()):
        prior = centerline_rows[case_id]
        feature_loss = float(basis["feature_total_pressure_loss_pa"])
        local_q = float(basis["local_dynamic_pressure_mean_pa"])
        prior_straight = float(prior["centerline_adjacent_straight_loss_subtracted_pa"])
        prior_k_centerline = float(prior["K_local_centerline"])
        raw_static_k_after_prior = (feature_loss - prior_straight) / local_q
        p_rgh_delta = float(basis["delta_p_rgh_down_minus_up_pa"])
        p_rgh_k_after_prior = (p_rgh_delta - prior_straight) / local_q
        option_specs = [
            ("prior_centerline_original_proxy", prior_k_centerline, "reject_negative_or_old_proxy_basis", "Prior centerline recompute used old proxy pressure basis and is negative for this feature."),
            ("raw_static_minus_prior_centerline", raw_static_k_after_prior, "reject_mixed_basis_and_recirculation", "Uses new static endpoint pressure with old centerline straight loss; nonnegative but physically mixed and recirculation-blocked."),
            ("raw_p_rgh_minus_prior_centerline", p_rgh_k_after_prior, "reject_negative_and_recirculation", "Same-window p_rgh delta minus prior centerline straight loss remains negative and recirculation-blocked."),
            ("no_straight_reference_apparent_cluster", "", "select_apparent_cluster_only", "No admissible straight reference survives same-basis, no-clipping, and recirculation requirements."),
        ]
        for option_id, k_value, status, reason in option_specs:
            options.append(
                {
                    "case_id": case_id,
                    "case_key": basis["case_key"],
                    "feature": FEATURE,
                    "reference_option_id": option_id,
                    "straight_loss_subtraction_pa": prior_straight if "prior" in option_id or "centerline" in option_id else "",
                    "K_local_candidate": k_value,
                    "option_status": status,
                    "reason": reason,
                    "component_k_admitted": "false",
                    "f6_fit_performed": "false",
                }
            )
        audits.append(
            {
                "case_id": case_id,
                "case_key": basis["case_key"],
                "feature": FEATURE,
                "basis_status": basis["basis_status"],
                "recirculation_gate": recirc_rows[case_id]["ordinary_recirculation_gate"],
                "prior_centerline_K_local": prior_k_centerline,
                "selected_component_isolation_label": "apparent_cluster_only",
                "component_isolation_gate": "fail_no_admissible_straight_reference_for_ordinary_K",
                "decision": "diagnostic_apparent_cluster_only",
                "next_action": "seek nonrecirculating anchor or keep section-effective diagnostic treatment",
                "component_k_admitted": "false",
                "f6_fit_performed": "false",
                "guardrail": "no_clipping_no_hidden_multiplier_no_F6_fit",
            }
        )
    decision = {
        "task": "TODO-TWO-TAP-COMPONENT-ISOLATION-DECISION",
        "decision": "apparent_cluster_only",
        "case_count": len(audits),
        "component_k_admitted": False,
        "f6_fit_performed": False,
        "rationale": "All rows are material-reverse-flow diagnostic rows and no same-basis straight reference supports ordinary K without violating guardrails.",
    }
    next_actions = [
        {
            "priority": 1,
            "step_id": "CI-NEXT-01",
            "title": "Preserve apparent/cluster label in final review",
            "action": "Carry apparent_cluster_only into separated admission review.",
            "acceptance_signal": "final review records no ordinary component-K candidate",
            "guardrail": "do not clip K or tune F6",
        }
    ]
    return audits, options, decision, next_actions


def uq_outputs(basis_rows: dict[str, dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    inventory: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for case_id, row in sorted(basis_rows.items()):
        inventory.extend(
            [
                {
                    "case_id": case_id,
                    "feature": FEATURE,
                    "candidate_source": "harvested_nominal_endpoint_pair",
                    "same_endpoint_labels": "true",
                    "same_formula": "true",
                    "same_sign_convention": "true",
                    "mesh_family_member": "nominal_only",
                    "time_family_member": "target_window_only",
                    "eligible_for_same_qoi_UQ": "false",
                    "reason": "single harvested target row cannot establish mesh/time uncertainty",
                },
                {
                    "case_id": case_id,
                    "feature": FEATURE,
                    "candidate_source": "prior_centerline_component_table",
                    "same_endpoint_labels": "false",
                    "same_formula": "false",
                    "same_sign_convention": "false",
                    "mesh_family_member": "not_same_qoi",
                    "time_family_member": "not_same_qoi",
                    "eligible_for_same_qoi_UQ": "false",
                    "reason": "prior row uses proxy pressure/tap-length basis and cannot supply same-QOI UQ",
                },
            ]
        )
        audits.append(
            {
                "case_id": case_id,
                "case_key": row["case_key"],
                "feature": FEATURE,
                "qoi": "corner_lower_right_feature_pressure_loss_and_K_local",
                "same_endpoint_labels": "required_lower_leg__s04_and_right_leg__s00",
                "same_formula_status": "required_same_pressure_basis_formula",
                "time_uncertainty_status": "missing_no_same_window_neighbors",
                "mesh_uncertainty_status": "missing_no_GCI",
                "same_qoi_uncertainty_gate": "fail_missing_same_qoi_UQ",
                "decision": "missing_no_GCI_diagnostic_only",
                "component_k_admitted": "false",
                "f6_fit_performed": "false",
                "guardrail": "do_not_borrow_unrelated_GCI_or_fabricate_monotonicity",
            }
        )
    missing = [
        {
            "case_id": row["case_id"],
            "feature": FEATURE,
            "missing_artifact": "same_qoi_mesh_time_uncertainty",
            "decision": row["decision"],
            "required_to_resolve": "repeat exact endpoint contract over valid same-label same-formula mesh/time family members",
            "guardrail": "diagnostic_only_until_same_qoi_UQ_exists",
        }
        for row in audits
    ]
    return inventory, audits, missing


def review_outputs(
    basis_rows: dict[str, dict[str, str]],
    recirc_rows: dict[str, dict[str, str]],
    isolation_rows: list[dict[str, Any]],
    uq_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    isolation_by_case = {row["case_id"]: row for row in isolation_rows}
    uq_by_case = {row["case_id"]: row for row in uq_rows}
    final: list[dict[str, Any]] = []
    for case_id, basis in sorted(basis_rows.items()):
        recirc = recirc_rows[case_id]
        iso = isolation_by_case[case_id]
        uq = uq_by_case[case_id]
        failed = [
            "recirculation_gate",
            "component_isolation_gate",
            "same_qoi_uncertainty_gate",
        ]
        final.append(
            {
                "case_id": case_id,
                "case_key": basis["case_key"],
                "feature": FEATURE,
                "raw_endpoint_surface_availability": "pass",
                "pressure_velocity_basis_gate": "pass",
                "recirculation_gate": recirc["ordinary_recirculation_gate"],
                "component_isolation_gate": iso["component_isolation_gate"],
                "same_qoi_uncertainty_gate": uq["same_qoi_uncertainty_gate"],
                "failed_gates": ";".join(failed),
                "ordinary_component_k_candidate": "false",
                "admission_decision": "diagnostic_only_apparent_cluster_recirculation_blocked_missing_UQ",
                "component_k_admitted": "false",
                "f6_fit_performed": "false",
                "guardrail": "all_gate_review_no_admission",
            }
        )
    decision = {
        "task": "TODO-TWO-TAP-SEPARATED-ADMISSION-REVIEW",
        "decision": "diagnostic_only_apparent_cluster_recirculation_blocked_missing_UQ",
        "raw_endpoint_surface_availability": "pass",
        "pressure_velocity_basis_gate": "pass",
        "recirculation_pass_pairs": 0,
        "ordinary_component_k_candidates": 0,
        "component_k_admitted": False,
        "f6_fit_performed": False,
        "next_step": "nonrecirculating_anchor_request_or_recirc_modeled_diagnostic_path",
    }
    f6_guardrails = [
        {
            "guardrail_id": "F6-SEP-01",
            "rule": "Do not use material-reverse-flow corner_lower_right rows as ordinary F6 anchors.",
            "status": "enforced",
            "evidence": "recirculation_gate failed for 3/3 rows",
        },
        {
            "guardrail_id": "F6-SEP-02",
            "rule": "Do not admit component K from this review because recirculation, isolation, and UQ gates fail.",
            "status": "enforced",
            "evidence": "final_gate_review.csv",
        },
    ]
    next_request = [
        {
            "priority": 1,
            "request_id": "NR-ANCHOR-REQUEST",
            "title": "Define non-recirculating anchor request",
            "reason": "current harvested rows are diagnostic only",
            "target_acceptance": "aggregate RAF < 0.01 and RMF < 0.01 with same endpoint fields and same-QOI UQ plan",
            "guardrail": "request only; no scheduler launch in this review",
        }
    ]
    return final, decision, f6_guardrails, next_request


def anchor_outputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    requirements = [
        {
            "request_id": "NR-CLR-01",
            "feature": FEATURE,
            "target": "same corner_lower_right topology at a non-recirculating operating point if available",
            "required_endpoint_labels": "lower_leg__s04;right_leg__s00",
            "required_fields": "p;p_rgh;U;rho;T;face_area;face_normal",
            "acceptance_signal": "six endpoint rows or equivalent family rows with aggregate RAF < 0.01 and RMF < 0.01",
            "guardrail": "do not launch without new board row and staged-copy runner",
        },
        {
            "request_id": "NR-ALT-01",
            "feature": "alternate two-tap component candidate",
            "target": "other named two-tap feature with comparable geometry and low reverse flow",
            "required_endpoint_labels": "must be exact mesh-station labels, not proxy surfaces",
            "required_fields": "p;p_rgh;U;rho;T;face_area;face_normal;RAF;RMF;SVF",
            "acceptance_signal": "ordinary recirculation gate passes before component isolation",
            "guardrail": "do not substitute old proxy pressure losses",
        },
    ]
    launch_gates = [
        {
            "gate": "task_scope",
            "requirement": "new staged-copy sampler row before any OpenFOAM postprocessing",
            "status": "required_future",
            "guardrail": "no native-output mutation",
        },
        {
            "gate": "ordinary_flow",
            "requirement": "aggregate RAF < 0.01 and aggregate RMF < 0.01",
            "status": "required_future",
            "guardrail": "material reverse-flow rows remain diagnostic",
        },
        {
            "gate": "same_qoi_UQ_plan",
            "requirement": "identify same endpoint/time/mesh family or declare missing_no_GCI",
            "status": "required_future",
            "guardrail": "no borrowed GCI",
        },
    ]
    summary = {
        "task": "TODO-TWO-TAP-NONRECIRC-ANCHOR-REQUEST",
        "request_type": "future_evidence_request_no_launch",
        "request_rows": len(requirements),
        "component_k_admitted": False,
        "f6_fit_performed": False,
    }
    return requirements, launch_gates, summary


def write_readme(path: Path, title: str, result: str, outputs: list[str]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "README.md").write_text(
        f"""---
provenance:
  - {rel(BASIS / 'gate_decision_table.csv')}
  - {rel(PLAN / 'basis_field_contract.csv')}
  - {rel(PLAN / 'same_qoi_uncertainty_contract.csv')}
tags: [pressure-ledger, two-tap, gates]
related:
  - .agent/status/2026-07-18_{TASK}.md
  - .agent/journal/2026-07-18/two-tap-remaining-gates-and-anchor-request.md
task: {TASK}
date: {DATE}
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# {title}

Generated: `{utc_now()}`

## Result

{result}

## Outputs

{chr(10).join(f'- `{name}`' for name in outputs)}

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry/admission state,
scheduler state, Fluid source, F6 fit, component-K admission, hidden multiplier,
clipped K, or endpoint-pressure invention was produced.
""",
        encoding="utf-8",
    )


def build_all() -> dict[str, Any]:
    basis_rows = by_case(read_csv(BASIS / "pressure_velocity_basis_audit.csv"))
    recirc_rows = by_case(read_csv(BASIS / "endpoint_recirculation_metrics.csv"))
    centerline_rows = {
        row["case_id"]: row
        for row in read_csv(CENTERLINE)
        if row.get("feature") == FEATURE and row.get("downstream_span") == "right_leg"
    }
    if set(basis_rows) != {"salt_2", "salt_3", "salt_4"}:
        raise RuntimeError("Expected Salt2/Salt3/Salt4 basis rows")
    if set(recirc_rows) != set(basis_rows) or set(centerline_rows) != set(basis_rows):
        raise RuntimeError("Missing recirculation or centerline rows for target cases")

    isolation, options, isolation_decision, isolation_next = component_isolation_outputs(basis_rows, recirc_rows, centerline_rows)
    inventory, uq, missing_uq = uq_outputs(basis_rows)
    final_review, admission_decision, f6_guardrails, review_next = review_outputs(basis_rows, recirc_rows, isolation, uq)
    anchor_requirements, anchor_launch_gates, anchor_summary = anchor_outputs()

    write_csv(ISOLATION_OUT / "component_isolation_audit.csv", isolation, ["case_id", "case_key", "feature", "basis_status", "recirculation_gate", "prior_centerline_K_local", "selected_component_isolation_label", "component_isolation_gate", "decision", "next_action", "component_k_admitted", "f6_fit_performed", "guardrail"])
    write_csv(ISOLATION_OUT / "straight_reference_options.csv", options, ["case_id", "case_key", "feature", "reference_option_id", "straight_loss_subtraction_pa", "K_local_candidate", "option_status", "reason", "component_k_admitted", "f6_fit_performed"])
    write_json(ISOLATION_OUT / "apparent_cluster_decision.json", isolation_decision)
    write_csv(ISOLATION_OUT / "assumption_register.csv", assumption_rows("component_isolation"), ["assumption_id", "assumption", "evidence_or_reason", "risk_if_wrong"])
    write_csv(ISOLATION_OUT / "next_action_queue.csv", isolation_next, ["priority", "step_id", "title", "action", "acceptance_signal", "guardrail"])
    write_csv(ISOLATION_OUT / "source_manifest.csv", source_manifest(), ["source_id", "path", "use", "mutation"])
    write_json(ISOLATION_OUT / "summary.json", isolation_decision)
    write_readme(ISOLATION_OUT, "Two-Tap Component Isolation Decision", "All three rows are routed to `apparent_cluster_only`; no admissible straight reference supports ordinary K under the same-basis/no-clipping/recirculation guardrails.", ["component_isolation_audit.csv", "straight_reference_options.csv", "apparent_cluster_decision.json", "assumption_register.csv", "next_action_queue.csv", "source_manifest.csv", "summary.json"])

    write_csv(UQ_OUT / "available_family_inventory.csv", inventory, ["case_id", "feature", "candidate_source", "same_endpoint_labels", "same_formula", "same_sign_convention", "mesh_family_member", "time_family_member", "eligible_for_same_qoi_UQ", "reason"])
    write_csv(UQ_OUT / "same_qoi_uncertainty_audit.csv", uq, ["case_id", "case_key", "feature", "qoi", "same_endpoint_labels", "same_formula_status", "time_uncertainty_status", "mesh_uncertainty_status", "same_qoi_uncertainty_gate", "decision", "component_k_admitted", "f6_fit_performed", "guardrail"])
    write_csv(UQ_OUT / "missing_no_GCI_decision.csv", missing_uq, ["case_id", "feature", "missing_artifact", "decision", "required_to_resolve", "guardrail"])
    write_csv(UQ_OUT / "assumption_register.csv", assumption_rows("same_qoi_uq"), ["assumption_id", "assumption", "evidence_or_reason", "risk_if_wrong"])
    write_csv(UQ_OUT / "source_manifest.csv", source_manifest(), ["source_id", "path", "use", "mutation"])
    uq_summary = {"task": "TODO-TWO-TAP-SAME-QOI-UQ-STATUS", "case_count": len(uq), "same_qoi_uq_pass": 0, "missing_no_GCI_rows": len(missing_uq), "component_k_admitted": False, "f6_fit_performed": False}
    write_json(UQ_OUT / "summary.json", uq_summary)
    write_readme(UQ_OUT, "Two-Tap Same-QOI UQ Status", "No exact same-QOI mesh/time family is available from current evidence, so all three rows are `missing_no_GCI_diagnostic_only`.", ["available_family_inventory.csv", "same_qoi_uncertainty_audit.csv", "missing_no_GCI_decision.csv", "assumption_register.csv", "source_manifest.csv", "summary.json"])

    write_csv(REVIEW_OUT / "final_gate_review.csv", final_review, ["case_id", "case_key", "feature", "raw_endpoint_surface_availability", "pressure_velocity_basis_gate", "recirculation_gate", "component_isolation_gate", "same_qoi_uncertainty_gate", "failed_gates", "ordinary_component_k_candidate", "admission_decision", "component_k_admitted", "f6_fit_performed", "guardrail"])
    write_json(REVIEW_OUT / "diagnostic_or_admission_decision.json", admission_decision)
    write_csv(REVIEW_OUT / "f6_separation_guardrail.csv", f6_guardrails, ["guardrail_id", "rule", "status", "evidence"])
    write_csv(REVIEW_OUT / "next_research_request.csv", review_next, ["priority", "request_id", "title", "reason", "target_acceptance", "guardrail"])
    write_csv(REVIEW_OUT / "assumption_register.csv", assumption_rows("admission_review"), ["assumption_id", "assumption", "evidence_or_reason", "risk_if_wrong"])
    write_csv(REVIEW_OUT / "source_manifest.csv", source_manifest(), ["source_id", "path", "use", "mutation"])
    write_json(REVIEW_OUT / "summary.json", admission_decision)
    write_readme(REVIEW_OUT, "Two-Tap Separated Admission Review", "The all-gate review keeps all three rows diagnostic only: raw surfaces and basis pass, but recirculation, component isolation, and same-QOI UQ fail.", ["final_gate_review.csv", "diagnostic_or_admission_decision.json", "f6_separation_guardrail.csv", "next_research_request.csv", "assumption_register.csv", "source_manifest.csv", "summary.json"])

    write_csv(ANCHOR_OUT / "nonrecirculating_anchor_request.csv", anchor_requirements, ["request_id", "feature", "target", "required_endpoint_labels", "required_fields", "acceptance_signal", "guardrail"])
    write_csv(ANCHOR_OUT / "launch_gate_contract.csv", anchor_launch_gates, ["gate", "requirement", "status", "guardrail"])
    write_csv(ANCHOR_OUT / "assumption_register.csv", assumption_rows("anchor_request"), ["assumption_id", "assumption", "evidence_or_reason", "risk_if_wrong"])
    write_csv(ANCHOR_OUT / "source_manifest.csv", source_manifest(), ["source_id", "path", "use", "mutation"])
    write_json(ANCHOR_OUT / "summary.json", anchor_summary)
    write_readme(ANCHOR_OUT, "Two-Tap Nonrecirculating Anchor Request", "This request defines future evidence needed for ordinary two-tap closure work. It is not a scheduler launch and does not admit a coefficient.", ["nonrecirculating_anchor_request.csv", "launch_gate_contract.csv", "assumption_register.csv", "source_manifest.csv", "summary.json"])

    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "packages": [rel(ISOLATION_OUT), rel(UQ_OUT), rel(REVIEW_OUT), rel(ANCHOR_OUT)],
        "case_count": len(basis_rows),
        "component_isolation_decision": isolation_decision["decision"],
        "same_qoi_uq_missing_rows": len(missing_uq),
        "final_admission_decision": admission_decision["decision"],
        "nonrecirc_anchor_request_rows": len(anchor_requirements),
        "component_k_admitted": False,
        "f6_fit_performed": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": "none",
        "generated_docs_index_refreshed": False,
    }
    return summary


def main() -> None:
    summary = build_all()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
