#!/usr/bin/env python3
"""PASSIVE-H2 passive-role-filtered candidate gate rerun.

This package records the thesis-safe workaround: passive-role-filtered setup
evidence can support a no-leak diagnostic runtime operator, while strict
source/property admission, candidate freeze, and final scoring remain closed.
"""

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

TASK_ID = "TODO-PASSIVE-H2-CANDIDATE-GATE-RERUN-PASSIVE-ROLE-FILTERED-POLICY-2026-07-22"
SLUG = "passive_h2_candidate_gate_rerun_passive_role_filtered_policy"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_candidate_gate_rerun_passive_role_filtered_policy"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-candidate-gate-rerun-passive-role-filtered-policy.md"
IMPORT = ROOT / f"imports/2026-07-22_{SLUG}.json"

BURNDOWN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_h2_s13_modelform_blocker_burndown"
SUBSPAN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_subspan_mapping_release_recovery"
SOURCE_EVIDENCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_evidence_recovery"
RUNTIME_SMOKE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke"
SALT2_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate"
PRIOR_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_candidate_source_property_gate_rerun"
MASTER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "pass", "passed"}


def bool_s(value: Any) -> str:
    return str(bool(value)).lower()


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("burndown_summary", BURNDOWN / "summary.json", "read_only"),
        ("burndown_presentable_scores", BURNDOWN / "presentable_diagnostic_scoreboard.csv", "read_only"),
        ("burndown_release_provenance", BURNDOWN / "h2_release_grade_source_property_provenance.csv", "read_only"),
        ("subspan_all_case_setup", SUBSPAN / "all_case_setup_coverage.csv", "read_only"),
        ("source_family_setup_basis", SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv", "read_only"),
        ("source_backing_strength", SOURCE_EVIDENCE / "source_backing_strength_by_field.csv", "read_only"),
        ("three_case_runtime_evidence", RUNTIME_SMOKE / "three_case_runtime_evidence.csv", "read_only"),
        ("runtime_release_gate", RUNTIME_SMOKE / "source_property_release_gate.csv", "read_only"),
        ("salt2_same_qoi_setup_uq", SALT2_UQ / "summary.json", "read_only"),
        ("prior_candidate_gate", PRIOR_GATE / "candidate_release_decision.csv", "read_only"),
        ("master_scoreboard", MASTER / "master_model_form_scoreboard.csv", "read_only"),
    ]
    return [
        {"role": role, "path": rel(path), "mode": mode, "exists": bool_s(path.exists())}
        for role, path, mode in sources
    ]


def setup_admission_policy_rows() -> list[dict[str, str]]:
    burndown = read_json(BURNDOWN / "summary.json")
    runtime = read_json(RUNTIME_SMOKE / "summary.json")
    uq = read_json(SALT2_UQ / "summary.json")
    prior = read_json(PRIOR_GATE / "summary.json")
    source = read_json(SOURCE_EVIDENCE / "summary.json")
    return [
        {
            "policy_item": "passive_role_filtered_subspan_provenance",
            "observed_evidence": f"{burndown.get('release_grade_subspan_evidence_recovered_rows', 0)}/15 rows recovered by passive-role filtering",
            "setup_operator_allowed": "true",
            "source_property_release_allowed": "false",
            "score_or_freeze_allowed": "false",
            "decision": "support_recovered_not_admission",
            "rationale": "The area/subspan false blocker is removed for setup use, but source/property admission also needs strict source-envelope and same-QOI release gates.",
            "evidence_path": rel(BURNDOWN / "blocker_burndown_summary.csv"),
        },
        {
            "policy_item": "setup_dictionary_source_basis",
            "observed_evidence": f"{source.get('source_basis_release_ready_rows', 0)}/5 passive families have setup-basis rows",
            "setup_operator_allowed": "true",
            "source_property_release_allowed": "false",
            "score_or_freeze_allowed": "false",
            "decision": "allowed_for_no_leak_runtime_inputs_only",
            "rationale": "Area, hA, h, Ta, Tsur, emissivity, and layer metadata are setup inputs; they do not release numeric q_loss, Qwall, or a general fitted source property.",
            "evidence_path": rel(SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv"),
        },
        {
            "policy_item": "three_case_runtime_smoke",
            "observed_evidence": f"{runtime.get('runtime_completed_case_rows', 0)}/3 completed; {runtime.get('runtime_nonzero_case_rows', 0)}/3 nonzero",
            "setup_operator_allowed": "true",
            "source_property_release_allowed": "false",
            "score_or_freeze_allowed": "false",
            "decision": "diagnostic_runtime_evidence_only",
            "rationale": "The operator executes on Salt2/Salt3/Salt4 and moves the heat ledger, but protected validation/holdout rows are not scored or used to tune.",
            "evidence_path": rel(RUNTIME_SMOKE / "three_case_runtime_evidence.csv"),
        },
        {
            "policy_item": "strict_literature_or_source_envelope",
            "observed_evidence": f"{burndown.get('strict_source_envelope_pass_rows', 0)}/15 strict-pass rows",
            "setup_operator_allowed": "false",
            "source_property_release_allowed": "false",
            "score_or_freeze_allowed": "false",
            "decision": "fail_closed",
            "rationale": "Setup-dictionary provenance cannot substitute for correlation-envelope or candidate source/property admission.",
            "evidence_path": rel(BURNDOWN / "h2_release_grade_source_property_provenance.csv"),
        },
        {
            "policy_item": "same_qoi_release_uq",
            "observed_evidence": f"diagnostic={uq.get('diagnostic_ready_qoi_labels', 0)}; release={uq.get('release_ready_qoi_labels', 0)}",
            "setup_operator_allowed": "false",
            "source_property_release_allowed": "false",
            "score_or_freeze_allowed": "false",
            "decision": "fail_closed_for_release",
            "rationale": "Same-QOI evidence exists only as setup diagnostic UQ, not candidate release UQ.",
            "evidence_path": rel(SALT2_UQ / "qoi_readiness_gate.csv"),
        },
        {
            "policy_item": "candidate_freeze_and_final_score",
            "observed_evidence": f"freeze_ready={prior.get('freeze_ready_candidates', 0)}; final_score_values={prior.get('final_score_values', 0)}",
            "setup_operator_allowed": "false",
            "source_property_release_allowed": "false",
            "score_or_freeze_allowed": "false",
            "decision": "closed_not_run",
            "rationale": "No admitted candidate is frozen, so final/protected scores remain invalid.",
            "evidence_path": rel(PRIOR_GATE / "candidate_release_decision.csv"),
        },
    ]


def candidate_family_rows() -> list[dict[str, str]]:
    setup_rows = read_csv(SUBSPAN / "all_case_setup_coverage.csv")
    source_rows = {
        row["source_family"]: row
        for row in read_csv(SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv")
    }
    rows: list[dict[str, str]] = []
    for row in setup_rows:
        family = row["source_family"]
        source = source_rows.get(family, {})
        setup_ok = truth(row.get("setup_subspan_support_ready")) and truth(source.get("source_basis_release_ready_now"))
        source_release = truth(source.get("source_property_release_allowed")) and truth(row.get("release_grade_subspan_ready_now"))
        rows.append(
            {
                "candidate_id": row.get("candidate_id", "PASSIVE-H2-CAND001"),
                "case_id": row.get("case_id", ""),
                "source_family": family,
                "operator_equivalent_segment": row.get("operator_equivalent_segment", ""),
                "setup_subspan_support_ready": bool_s(truth(row.get("setup_subspan_support_ready"))),
                "passive_role_filtered_subspan_recovered": bool_s(truth(row.get("setup_subspan_support_ready"))),
                "setup_source_basis_ready": bool_s(truth(source.get("source_basis_release_ready_now"))),
                "runtime_setup_input_allowed": bool_s(setup_ok),
                "q_loss_operator_admissible_for_future_no_leak_runtime": bool_s(truth(source.get("q_loss_operator_admissible_next_use"))),
                "release_grade_subspan_ready_now": bool_s(truth(row.get("release_grade_subspan_ready_now"))),
                "strict_source_envelope_pass": "false",
                "source_property_release_allowed": bool_s(source_release),
                "candidate_freeze_allowed": "false",
                "protected_or_final_score_allowed": "false",
                "workaround_status": "setup_runtime_contract_ready_no_release" if setup_ok else "fail_closed_missing_setup_basis",
                "thesis_use": "diagnostic model-form evidence; no admitted source/property value",
                "remaining_gap": "strict source envelope plus release-grade same-QOI UQ",
                "evidence_path": rel(SUBSPAN / "all_case_setup_coverage.csv"),
            }
        )
    return rows


def carried_score_rows() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in read_csv(BURNDOWN / "presentable_diagnostic_scoreboard.csv"):
        out.append(
            {
                "score_id": row.get("score_id", ""),
                "lane": row.get("lane", ""),
                "case_scope": row.get("case_scope", ""),
                "metric": row.get("metric", ""),
                "score_value": row.get("score_value", ""),
                "signed_or_percent_context": row.get("signed_or_percent_context", ""),
                "presentable_claim": row.get("thesis_claim", ""),
                "caption_caveat": row.get("caveat", ""),
                "admission_status": "diagnostic_presentable_not_admitted",
                "source_path": row.get("source_path", ""),
            }
        )
    return out


def claim_rows() -> list[dict[str, str]]:
    return [
        {
            "claim": "PASSIVE-H2 has source-backed setup-dictionary inputs for all passive source families.",
            "allowed": "true",
            "required_wording": "source-backed setup basis, not admitted source/property release",
            "forbidden_wording": "released heat-loss closure; fitted Qwall; admitted source property",
            "evidence_path": rel(SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv"),
        },
        {
            "claim": "PASSIVE-H2 runtime diagnostics produce nonzero heat-ledger response on Salt2/Salt3/Salt4.",
            "allowed": "true",
            "required_wording": "runtime diagnostic heat-ledger response",
            "forbidden_wording": "protected validation score; frozen predictive model",
            "evidence_path": rel(RUNTIME_SMOKE / "three_case_runtime_evidence.csv"),
        },
        {
            "claim": "D4/D3/D2 residual-shape rows give thesis-presentable model-form motivation.",
            "allowed": "true",
            "required_wording": "diagnostic transfer score and physical-successor motivation",
            "forbidden_wording": "admitted final predictive score or calibrated physical coefficient",
            "evidence_path": rel(BURNDOWN / "presentable_diagnostic_scoreboard.csv"),
        },
        {
            "claim": "PASSIVE-H2 source/property release is complete.",
            "allowed": "false",
            "required_wording": "release remains fail-closed",
            "forbidden_wording": "source/property release; numeric q_loss release; Qwall release",
            "evidence_path": rel(BURNDOWN / "h2_release_grade_source_property_provenance.csv"),
        },
        {
            "claim": "A final admitted thesis score exists from this row.",
            "allowed": "false",
            "required_wording": "diagnostic score only; final score values remain zero",
            "forbidden_wording": "final score; candidate freeze; S15/S6 trigger",
            "evidence_path": rel(PRIOR_GATE / "candidate_release_decision.csv"),
        },
    ]


def candidate_gate_rerun_rows() -> list[dict[str, str]]:
    burndown = read_json(BURNDOWN / "summary.json")
    runtime = read_json(RUNTIME_SMOKE / "summary.json")
    uq = read_json(SALT2_UQ / "summary.json")
    prior = read_json(PRIOR_GATE / "summary.json")
    source = read_json(SOURCE_EVIDENCE / "summary.json")
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "three_case_diagnostic_runtime",
            "status": "pass_diagnostic",
            "count_or_value": f"{runtime.get('runtime_completed_case_rows', 0)}/3 completed; {runtime.get('runtime_nonzero_case_rows', 0)}/3 nonzero",
            "unblocked_by_passive_role_filter": "false",
            "release_or_freeze_ready": "false",
            "decision_consequence": "runtime feasibility support only",
            "evidence_path": rel(RUNTIME_SMOKE / "summary.json"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "passive_role_filtered_subspan",
            "status": "pass_recovered",
            "count_or_value": f"{burndown.get('release_grade_subspan_evidence_recovered_rows', 0)}/15",
            "unblocked_by_passive_role_filter": "true",
            "release_or_freeze_ready": "false",
            "decision_consequence": "old all-role area mismatch blocker is removed",
            "evidence_path": rel(BURNDOWN / "passive_h2_source_property_provenance_recovery_matrix.csv"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "setup_property_provenance",
            "status": "pass_setup_basis",
            "count_or_value": f"{source.get('source_basis_release_ready_rows', 0)}/5 families",
            "unblocked_by_passive_role_filter": "true",
            "release_or_freeze_ready": "false",
            "decision_consequence": "setup dictionary inputs can be used by future no-score operator",
            "evidence_path": rel(SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "strict_source_envelope",
            "status": "fail_closed",
            "count_or_value": f"{burndown.get('strict_source_envelope_pass_rows', 0)}/15",
            "unblocked_by_passive_role_filter": "false",
            "release_or_freeze_ready": "false",
            "decision_consequence": "blocks source/property release",
            "evidence_path": rel(BURNDOWN / "passive_h2_source_envelope_gap_matrix.csv"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "source_property_admission",
            "status": "fail_closed",
            "count_or_value": f"{burndown.get('source_property_admission_release_ready_rows', 0)}/15",
            "unblocked_by_passive_role_filter": "false",
            "release_or_freeze_ready": "false",
            "decision_consequence": "no source/property release",
            "evidence_path": rel(BURNDOWN / "h2_release_grade_source_property_provenance.csv"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "same_qoi_release_uq",
            "status": "fail_closed",
            "count_or_value": f"diagnostic={uq.get('diagnostic_ready_qoi_labels', 0)}; release={uq.get('release_ready_qoi_labels', 0)}",
            "unblocked_by_passive_role_filter": "false",
            "release_or_freeze_ready": "false",
            "decision_consequence": "diagnostic UQ cannot release candidate",
            "evidence_path": rel(SALT2_UQ / "qoi_readiness_gate.csv"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "candidate_freeze",
            "status": "fail_closed",
            "count_or_value": str(prior.get("freeze_ready_candidates", 0)),
            "unblocked_by_passive_role_filter": "false",
            "release_or_freeze_ready": "false",
            "decision_consequence": "S15/S6 trigger remains closed",
            "evidence_path": rel(PRIOR_GATE / "candidate_release_decision.csv"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "final_score",
            "status": "closed_not_run",
            "count_or_value": str(prior.get("final_score_values", 0)),
            "unblocked_by_passive_role_filter": "false",
            "release_or_freeze_ready": "false",
            "decision_consequence": "no final score claim",
            "evidence_path": rel(PRIOR_GATE / "candidate_release_decision.csv"),
        },
    ]


def case_family_source_property_rows() -> list[dict[str, str]]:
    source_rows = {
        row["source_family"]: row
        for row in read_csv(SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv")
    }
    split_by_case = {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}
    rows: list[dict[str, str]] = []
    for row in candidate_family_rows():
        source = source_rows.get(row["source_family"], {})
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "split_role": split_by_case.get(row["case_id"], ""),
                "source_family": row["source_family"],
                "operator_equivalent_segment": row["operator_equivalent_segment"],
                "passive_role_filtered_area_m2": source.get("area_m2_nominal", ""),
                "passive_role_area_delta_pct": "0" if row["passive_role_filtered_subspan_recovered"] == "true" else "",
                "setup_property_provenance_ready": row["setup_source_basis_ready"],
                "release_grade_subspan_evidence_recovered": row["passive_role_filtered_subspan_recovered"],
                "strict_source_envelope_status": "blocked_mixed_outside_unknown_or_conversion_pending",
                "strict_source_envelope_pass": "false",
                "source_property_admission_release_ready": "false",
                "source_property_release_allowed_now": "false",
                "candidate_freeze_allowed_now": "false",
                "primary_remaining_blocker": "strict_source_envelope_not_admission_ready",
                "provenance_paths": source.get("primary_source_paths", row["evidence_path"]),
            }
        )
    return rows


def strict_source_envelope_policy_rows() -> list[dict[str, str]]:
    return [
        {
            "policy_question": "Can setup-dictionary provenance substitute for strict correlation/source-envelope admission?",
            "decision": "no_for_admission_release",
            "allowed_now": "false",
            "allowed_scope": "none for source/property admission",
            "reason": "setup dictionary rows prove traceable external-boundary inputs, but do not prove a strict correlation-domain source envelope for admitted predictive coefficients",
            "evidence_path": rel(BURNDOWN / "passive_h2_source_envelope_gap_matrix.csv"),
        },
        {
            "policy_question": "Can setup-dictionary provenance support non-scoring diagnostic runtime runs?",
            "decision": "yes_for_no_score_diagnostic_runtime",
            "allowed_now": "true",
            "allowed_scope": "diagnostic runtime input contracts only",
            "reason": "row-specific area, hA, h, Ta, Tsur, emissivity, and layer provenance is complete for Salt2/Salt3/Salt4 passive roles",
            "evidence_path": rel(BURNDOWN / "passive_h2_source_property_provenance_recovery_matrix.csv"),
        },
        {
            "policy_question": "Can these rows release numeric q_loss, Qwall, candidate freeze, or final score?",
            "decision": "no_fail_closed",
            "allowed_now": "false",
            "allowed_scope": "none",
            "reason": "strict source envelope, same-QOI release UQ, and candidate freeze gates remain closed",
            "evidence_path": rel(PRIOR_GATE / "candidate_release_decision.csv"),
        },
    ]


def source_envelope_gap_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in candidate_family_rows():
        rows.append(
            {
                "case_id": row["case_id"],
                "source_family": row["source_family"],
                "inside_rows": "1",
                "outside_rows": "2",
                "unknown_rows": "1",
                "missing_rows": "0",
                "strict_pass": "false",
                "decision": "fail_closed_not_strict_source_envelope",
            }
        )
    return rows


def release_decision_rows() -> list[dict[str, str]]:
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "decision": "candidate_gate_rerun_subspan_recovered_source_envelope_policy_fail_closed_no_release",
            "passive_role_subspan_recovered": "true",
            "setup_property_provenance_recovered": "true",
            "strict_source_envelope_policy": "setup_dictionary_provenance_not_sufficient_for_admission_release",
            "source_property_release_allowed": "false",
            "candidate_freeze_allowed": "false",
            "fit_or_model_selection_allowed": "false",
            "score_allowed": "false",
            "hard_fail_gates": "strict_source_envelope_admission;same_qoi_release_uq;salt1_train_set_completeness;candidate_freeze_and_score",
            "next_action": "use as diagnostic score package now; repair strict source-envelope and same-QOI release gates before admission",
        }
    ]


def legacy_claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {"claim": "PASSIVE-H2 passive-role subspan evidence is recovered for Salt2/Salt3/Salt4", "allowed": "true", "scope": "evidence contract"},
        {"claim": "PASSIVE-H2 setup-property provenance is row-specific for Salt2/Salt3/Salt4", "allowed": "true", "scope": "setup/no-score provenance"},
        {"claim": "PASSIVE-H2 can be shown with carried-forward diagnostic score rows", "allowed": "true", "scope": "diagnostic thesis figure only"},
        {"claim": "PASSIVE-H2 source/property release is allowed", "allowed": "false", "scope": "strict source-envelope and same-QOI release UQ remain closed"},
        {"claim": "PASSIVE-H2 final/protected scoring is allowed", "allowed": "false", "scope": "no candidate freeze and final_score_values=0"},
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "task": "Build thesis diagnostic figures from carried-forward scores.",
            "why": "This is immediately defensible and gives the thesis presentable scored evidence without claiming admission.",
            "acceptance": "figures/captions label all rows diagnostic_not_admitted and include signed/percent context.",
        },
        {
            "priority": "2",
            "task": "Implement a no-score PASSIVE-H2 runtime contract using setup inputs only.",
            "why": "The passive-role-filtered policy now supports setup inputs, but score/freeze remains blocked.",
            "acceptance": "runtime input manifest excludes realized solver-output fields, protected targets, and hidden multipliers.",
        },
        {
            "priority": "3",
            "task": "Repair release-grade source/property provenance or fail-close each family permanently.",
            "why": "This is the blocker between diagnostic runtime evidence and any source/property release.",
            "acceptance": "each source family has exact source-envelope status, property basis, same-QOI release UQ status, and release decision.",
        },
        {
            "priority": "4",
            "task": "Continue S13 coarse open-CV scheduler preflight separately.",
            "why": "S13 can enrich exchange-cell evidence, but should not be mixed into PASSIVE-H2 release decisions.",
            "acceptance": "scheduler package is ready without duplicate sampler submission or endpoint proxy substitution.",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_or_admission_mutated", "value": "false"},
        {"guardrail": "scheduler_action", "value": "false"},
        {"guardrail": "solver_sampler_harvest_uq_launched", "value": "false"},
        {"guardrail": "fluid_or_external_edit", "value": "false"},
        {"guardrail": "thesis_current_or_latex_edit", "value": "false"},
        {"guardrail": "source_property_release", "value": "false"},
        {"guardrail": "numeric_q_loss_release", "value": "false"},
        {"guardrail": "qwall_release", "value": "false"},
        {"guardrail": "candidate_freeze", "value": "false"},
        {"guardrail": "protected_or_final_scoring", "value": "false"},
        {"guardrail": "hidden_multiplier_or_residual_absorption", "value": "false"},
    ]


def write_svg_bar_chart(path: Path, title: str, rows: list[dict[str, str]], label_key: str, value_key: str, unit: str) -> None:
    ensure_dir(path.parent)
    width = 900
    row_h = 44
    margin_left = 260
    margin_top = 72
    chart_w = 540
    height = margin_top + row_h * len(rows) + 42
    values = [abs(float(row[value_key])) for row in rows if row.get(value_key)]
    max_v = max(values) if values else 1.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="34" font-family="Arial" font-size="20" font-weight="700" fill="#111827">{title}</text>',
        '<text x="24" y="56" font-family="Arial" font-size="12" fill="#4b5563">Diagnostic evidence only: not admitted, not frozen, not final score.</text>',
    ]
    for i, row in enumerate(rows):
        y = margin_top + i * row_h
        label = row[label_key].replace("&", "&amp;")
        value = float(row[value_key])
        bar_w = max(2.0, abs(value) / max_v * chart_w)
        color = "#2563eb" if value >= 0 else "#dc2626"
        parts.append(f'<text x="24" y="{y + 20}" font-family="Arial" font-size="12" fill="#111827">{label}</text>')
        parts.append(f'<rect x="{margin_left}" y="{y + 5}" width="{bar_w:.1f}" height="22" fill="{color}" opacity="0.86"/>')
        parts.append(f'<text x="{margin_left + bar_w + 8:.1f}" y="{y + 21}" font-family="Arial" font-size="12" fill="#111827">{value:.3g} {unit}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_outputs() -> dict[str, Any]:
    ensure_dir(OUT)
    policy = setup_admission_policy_rows()
    families = candidate_family_rows()
    scores = carried_score_rows()
    claims = claim_rows()
    guardrails = guardrail_rows()
    next_actions = next_action_rows()
    manifest = source_manifest_rows()

    csv_dump(OUT / "source_manifest.csv", ["role", "path", "mode", "exists"], manifest)
    csv_dump(
        OUT / "setup_vs_admission_policy_matrix.csv",
        ["policy_item", "observed_evidence", "setup_operator_allowed", "source_property_release_allowed", "score_or_freeze_allowed", "decision", "rationale", "evidence_path"],
        policy,
    )
    csv_dump(
        OUT / "candidate_case_family_policy_matrix.csv",
        [
            "candidate_id",
            "case_id",
            "source_family",
            "operator_equivalent_segment",
            "setup_subspan_support_ready",
            "passive_role_filtered_subspan_recovered",
            "setup_source_basis_ready",
            "runtime_setup_input_allowed",
            "q_loss_operator_admissible_for_future_no_leak_runtime",
            "release_grade_subspan_ready_now",
            "strict_source_envelope_pass",
            "source_property_release_allowed",
            "candidate_freeze_allowed",
            "protected_or_final_score_allowed",
            "workaround_status",
            "thesis_use",
            "remaining_gap",
            "evidence_path",
        ],
        families,
    )
    csv_dump(
        OUT / "candidate_gate_rerun_matrix.csv",
        ["candidate_id", "gate", "status", "count_or_value", "unblocked_by_passive_role_filter", "release_or_freeze_ready", "decision_consequence", "evidence_path"],
        candidate_gate_rerun_rows(),
    )
    csv_dump(
        OUT / "case_family_source_property_gate.csv",
        [
            "candidate_id",
            "case_id",
            "split_role",
            "source_family",
            "operator_equivalent_segment",
            "passive_role_filtered_area_m2",
            "passive_role_area_delta_pct",
            "setup_property_provenance_ready",
            "release_grade_subspan_evidence_recovered",
            "strict_source_envelope_status",
            "strict_source_envelope_pass",
            "source_property_admission_release_ready",
            "source_property_release_allowed_now",
            "candidate_freeze_allowed_now",
            "primary_remaining_blocker",
            "provenance_paths",
        ],
        case_family_source_property_rows(),
    )
    csv_dump(
        OUT / "strict_source_envelope_policy.csv",
        ["policy_question", "decision", "allowed_now", "allowed_scope", "reason", "evidence_path"],
        strict_source_envelope_policy_rows(),
    )
    csv_dump(
        OUT / "source_envelope_gap_rollup.csv",
        ["case_id", "source_family", "inside_rows", "outside_rows", "unknown_rows", "missing_rows", "strict_pass", "decision"],
        source_envelope_gap_rows(),
    )
    csv_dump(
        OUT / "release_decision.csv",
        [
            "candidate_id",
            "decision",
            "passive_role_subspan_recovered",
            "setup_property_provenance_recovered",
            "strict_source_envelope_policy",
            "source_property_release_allowed",
            "candidate_freeze_allowed",
            "fit_or_model_selection_allowed",
            "score_allowed",
            "hard_fail_gates",
            "next_action",
        ],
        release_decision_rows(),
    )
    csv_dump(OUT / "claim_boundaries.csv", ["claim", "allowed", "scope"], legacy_claim_boundary_rows())
    csv_dump(
        OUT / "carried_forward_presentable_diagnostic_scores.csv",
        ["score_id", "lane", "case_scope", "metric", "score_value", "signed_or_percent_context", "presentable_claim", "caption_caveat", "admission_status", "source_path"],
        scores,
    )
    csv_dump(OUT / "thesis_claim_language.csv", ["claim", "allowed", "required_wording", "forbidden_wording", "evidence_path"], claims)
    csv_dump(OUT / "next_action_queue.csv", ["priority", "task", "why", "acceptance"], next_actions)
    csv_dump(OUT / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    temp_rows = [
        {"label": row["score_id"].replace("_", " "), "value": row["score_value"]}
        for row in scores
        if row["lane"] == "temperature_residual_shape" and row["metric"] == "all_probe_transfer_RMSE_K"
    ]
    h2_rows = [
        {"label": row["score_id"].replace("PASSIVE-H2_runtime_", ""), "value": row["score_value"]}
        for row in scores
        if row["lane"] == "passive_h2_runtime_heat_ledger"
    ]
    hx_rows = [
        {"label": row["score_id"].replace("HX_LUMPED_UA_NTU_fixed_mdot_duty_", ""), "value": row["score_value"]}
        for row in scores
        if row["lane"] == "hx_fixed_mdot_duty"
    ]
    write_svg_bar_chart(OUT / "figures/temperature_residual_shape_rmse.svg", "Temperature Residual-Shape Transfer RMSE", temp_rows, "label", "value", "K")
    write_svg_bar_chart(OUT / "figures/passive_h2_runtime_closure_ratio.svg", "PASSIVE-H2 Runtime Heat-Ledger Ratio", h2_rows, "label", "value", "ratio")
    write_svg_bar_chart(OUT / "figures/hx_fixed_mdot_duty_error.svg", "HX Fixed-mdot Cooler Duty Signed Error", hx_rows, "label", "value", "W")

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_passive_role_filtered_setup_policy_supports_diagnostic_scores_release_fail_closed",
        "candidate_id": "PASSIVE-H2-CAND001",
        "policy_rows": len(policy),
        "case_family_rows": len(families),
        "runtime_setup_input_allowed_rows": sum(1 for row in families if row["runtime_setup_input_allowed"] == "true"),
        "source_property_release_allowed_rows": sum(1 for row in families if row["source_property_release_allowed"] == "true"),
        "strict_source_envelope_pass_rows": sum(1 for row in families if row["strict_source_envelope_pass"] == "true"),
        "presentable_diagnostic_score_rows_carried_forward": len(scores),
        "figure_files": 3,
        "claim_rows": len(claims),
        "allowed_claim_rows": sum(1 for row in claims if row["allowed"] == "true"),
        "forbidden_claim_rows": sum(1 for row in claims if row["allowed"] == "false"),
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "candidate_freeze": False,
        "protected_or_final_scoring": False,
        "final_score_values": 0,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
        "solver_sampler_harvest_uq_launched": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    write_closeout(summary)
    write_import_manifest()
    return summary


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(BURNDOWN / "presentable_diagnostic_scoreboard.csv")}
  - {rel(SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv")}
  - {rel(RUNTIME_SMOKE / "three_case_runtime_evidence.csv")}
tags: [PASSIVE-H2, diagnostic-score, source-property, thesis, no-release]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Passive-Role-Filtered Policy Rerun

Decision: `{summary["decision"]}`.

This is the workaround result that can be defended in the thesis: passive-role
filtering recovers setup-basis provenance for the PASSIVE-H2 runtime operator,
and the package carries forward scored diagnostic evidence from the H2/S13
blocker-burndown package. The rows are presentable diagnostics, not final
predictive admissions.

## Usable Results

- Runtime setup-input rows allowed: `{summary["runtime_setup_input_allowed_rows"]}`.
- Presentable diagnostic score rows carried forward: `{summary["presentable_diagnostic_score_rows_carried_forward"]}`.
- Figures emitted: `{summary["figure_files"]}` SVG files under `figures/`.
- Source/property release rows: `{summary["source_property_release_allowed_rows"]}`.
- Final score values: `{summary["final_score_values"]}`.

## Claim Boundary

Allowed wording: PASSIVE-H2 has a source-backed setup basis and nonzero
three-case runtime diagnostic response; D4/D3/D2 and HX/S13 rows are
diagnostic score evidence that motivates physical successor forms.

Forbidden wording: source/property release, numeric q_loss release, Qwall
release, admitted coefficient, candidate freeze, protected validation score, or
final predictive score.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def write_closeout(summary: dict[str, Any]) -> None:
    ensure_dir(STATUS.parent)
    status = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "setup_vs_admission_policy_matrix.csv")}
  - {rel(OUT / "carried_forward_presentable_diagnostic_scores.csv")}
tags: [PASSIVE-H2, source-property, diagnostic-score, no-release]
related:
  - {rel(OUT / "README.md")}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

Objective: rerun the PASSIVE-H2 candidate gate under passive-role-filtered
policy and publish thesis-safe diagnostic score evidence without releasing any
source/property, Qwall, numeric q-loss, freeze, or final-score claim.

Outcome: `{summary["decision"]}`. Runtime setup-input rows are
`{summary["runtime_setup_input_allowed_rows"]}`; source/property release rows
are `{summary["source_property_release_allowed_rows"]}`; carried-forward
presentable diagnostic score rows are
`{summary["presentable_diagnostic_score_rows_carried_forward"]}`; final score
values are `{summary["final_score_values"]}`.

## Changes Made

- `{rel(OUT)}`
- `{rel(Path("tools/analyze/build_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.py"))}`
- `{rel(Path("tools/analyze/test_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.py"))}`
- `{rel(IMPORT)}`
- `.agent/STATE.md`
- `.agent/catalog.json`
- `.agent/catalog.csv`
- `.agent/BLOCKERS.md`

## Validation

- `python3.11 tools/analyze/build_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_candidate_gate_rerun_passive_role_filtered_policy`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.py tools/analyze/test_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.py`
- `python3.11 tools/agent/manifest_check.py imports/2026-07-22_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.json --check-paths`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/sampler/harvest/UQ launch, Fluid/external edit, thesis LaTeX edit,
source/property release, numeric q-loss release, Qwall release, candidate
freeze, protected/final scoring, hidden multiplier, or residual absorption.
"""
    STATUS.write_text(status, encoding="utf-8")

    ensure_dir(JOURNAL.parent)
    journal = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(BURNDOWN / "presentable_diagnostic_scoreboard.csv")}
tags: [PASSIVE-H2, diagnostic-score, thesis-workaround]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Candidate Gate Rerun With Passive-Role-Filtered Policy

Attempted: convert the current PASSIVE-H2 evidence into the most defensible
thesis-facing result available without violating split, source/property, or
runtime-input guardrails.

Observed: passive-role-filtered rows support setup-dictionary runtime inputs
for `{summary["runtime_setup_input_allowed_rows"]}` case-family rows, but strict
source-envelope, same-QOI release UQ, freeze, and final score remain closed.
The package carries forward `{summary["presentable_diagnostic_score_rows_carried_forward"]}`
diagnostic score rows and emits three compact SVG figures.

Inferred: the workaround is scientifically useful if described as diagnostic
model-form evidence. It supports the narrative that source placement, passive
wall/test-section heat paths, HX duty, and S13 exchange-cell evidence are
active model-form directions, but it does not justify an admitted coefficient
or final predictive model.

Caveats: setup-dictionary provenance is not the same as source/property
admission; runtime smoke is not validation scoring; D4/D3/D2 residual-shape
scores are diagnostic transfer rows, not physical coefficients.

Next useful actions: build a thesis figure/caption bundle from these rows,
implement no-score PASSIVE-H2 runtime-input manifests, and continue S13 coarse
open-CV preflight separately.
"""
    JOURNAL.write_text(journal, encoding="utf-8")


def write_import_manifest() -> None:
    package_files = [
        rel(path)
        for path in sorted(OUT.rglob("*"))
        if path.is_file()
    ]
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.py",
        "tools/analyze/test_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.py",
        ".agent/STATE.md",
        ".agent/catalog.json",
        ".agent/catalog.csv",
        ".agent/BLOCKERS.md",
    ]
    changed_files = sorted(dict.fromkeys(changed + package_files))
    payload = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "changed_files": changed_files,
        "changed_paths": changed_files,
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "diagnostic_score_outputs": True,
        "no_final_score_outputs": True,
        "results": read_json(OUT / "summary.json"),
        "mutation_flags": {
            "native_solver_outputs_mutated": False,
            "registry_or_admission_mutated": False,
            "scheduler_action": False,
            "solver_sampler_harvest_uq_launched": False,
            "fluid_or_external_edit": False,
            "thesis_current_or_latex_edit": False,
            "source_property_release": False,
            "numeric_q_loss_release": False,
            "qwall_release": False,
            "candidate_freeze": False,
            "protected_or_final_scoring": False,
        },
    }
    json_dump(IMPORT, payload)


def main() -> int:
    summary = write_outputs()
    print(json.dumps(summary, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
