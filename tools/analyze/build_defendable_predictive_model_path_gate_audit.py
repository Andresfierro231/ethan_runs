#!/usr/bin/env python3
"""Build a defendable predictive-model path gate audit.

This is a read-only synthesis over current P1D/PASSIVE-H2/S13/source-property
evidence. It does not release inputs, fit, freeze, score, launch compute, or
mutate solver/native/external state.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-DEFENDABLE-PREDICTIVE-MODEL-PATH-GATE-AUDIT-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_defendable_predictive_model_path_gate_audit"

PACKAGES = {
    "p1d_prototype": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_p1d_bulk_cv_h2_train_only_thesis_prototype",
    "candidate_gate": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate",
    "passive_runtime": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation",
    "passive_final_gate": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate",
    "passive_subspan": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery",
    "s13_endpoint_preflight": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight",
    "s13_endpoint_masks": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation",
    "s13_endpoint_geometry": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_geometry_enrichment_for_release_masks",
    "s12_s13_unlock": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_s13_tp_exchange_blocker_unlock",
    "source_exact": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_source_property_exact_field_recovery_salt14",
    "source_recovery": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_strict_row_specific_source_envelope_recovery",
    "hx_scheduler": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler",
}

GUARDRAILS = {
    "native_solver_outputs_mutated": False,
    "registry_or_admission_mutated": False,
    "scheduler_action": False,
    "solver_postprocessing_sampler_harvest_uq_launched": False,
    "fluid_or_external_edit": False,
    "thesis_body_or_latex_edit": False,
    "source_property_release": False,
    "Qwall_release": False,
    "numeric_q_loss_release": False,
    "validation_holdout_external_scoring": False,
    "protected_scoring": False,
    "fitting_or_model_selection": False,
    "coefficient_admission": False,
    "candidate_freeze": False,
    "final_score_claim": False,
    "s11_s12_s13_s15_s6_trigger": False,
    "hidden_multiplier": False,
    "residual_absorbed_into_internal_Nu": False,
    "endpoint_proxy_substitution": False,
    "runtime_leakage_relaxation": False,
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def require_inputs() -> None:
    required = [
        PACKAGES["p1d_prototype"] / "summary.json",
        PACKAGES["candidate_gate"] / "summary.json",
        PACKAGES["candidate_gate"] / "candidate_priority_ranking.csv",
        PACKAGES["candidate_gate"] / "next_unblock_sequence.csv",
        PACKAGES["passive_runtime"] / "summary.json",
        PACKAGES["passive_final_gate"] / "summary.json",
        PACKAGES["passive_subspan"] / "summary.json",
        PACKAGES["passive_subspan"] / "release_gate_matrix.csv",
        PACKAGES["passive_subspan"] / "source_family_patch_subspan_coverage.csv",
        PACKAGES["passive_subspan"] / "same_qoi_setup_uq_readiness.csv",
        PACKAGES["passive_subspan"] / "salt34_runtime_smoke_eligibility.csv",
        PACKAGES["s13_endpoint_preflight"] / "summary.json",
        PACKAGES["s13_endpoint_masks"] / "summary.json",
        PACKAGES["s13_endpoint_geometry"] / "summary.json",
        PACKAGES["source_exact"] / "summary.json",
        PACKAGES["source_recovery"] / "summary.json",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing defendable model gate-audit inputs: " + "; ".join(missing))


def bool_pass(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "pass", "pass_diagnostic_only"}


def load_summaries() -> dict[str, dict[str, Any]]:
    return {name: read_json(path / "summary.json") for name, path in PACKAGES.items() if (path / "summary.json").exists()}


def evidence_snapshot(s: dict[str, dict[str, Any]]) -> dict[str, Any]:
    coverage_rows = read_csv(PACKAGES["passive_subspan"] / "source_family_patch_subspan_coverage.csv")
    same_qoi_rows = read_csv(PACKAGES["passive_subspan"] / "same_qoi_setup_uq_readiness.csv")
    smoke_rows = read_csv(PACKAGES["passive_subspan"] / "salt34_runtime_smoke_eligibility.csv")

    setup_support_rows = sum(1 for row in coverage_rows if bool_pass(row.get("setup_subspan_support_ready")))
    release_grade_subspan_rows = sum(1 for row in coverage_rows if bool_pass(row.get("release_grade_subspan_ready_now")))
    same_qoi_setup_available_labels = sum(1 for row in same_qoi_rows if bool_pass(row.get("same_qoi_setup_only_uq_available")))
    same_qoi_release_ready_labels = sum(1 for row in same_qoi_rows if bool_pass(row.get("admission_release_ready")))
    smoke_eligible_rows = sum(1 for row in smoke_rows if bool_pass(row.get("runtime_smoke_eligible_next_row")))

    return {
        "passive_h2_setup_subspan_support_rows": setup_support_rows,
        "passive_h2_setup_subspan_total_rows": len(coverage_rows),
        "passive_h2_release_grade_subspan_rows": release_grade_subspan_rows,
        "passive_h2_same_qoi_setup_uq_available_labels": same_qoi_setup_available_labels,
        "passive_h2_same_qoi_total_labels": len(same_qoi_rows),
        "passive_h2_same_qoi_release_ready_labels": same_qoi_release_ready_labels,
        "passive_h2_salt34_runtime_smoke_eligible_rows": smoke_eligible_rows,
        "passive_h2_salt34_runtime_smoke_total_rows": len(smoke_rows),
        "source_property_release_ready_rows": s["candidate_gate"]["source_property_release_ready_rows"],
        "strict_source_envelope_pass_rows": s["candidate_gate"]["strict_source_envelope_pass_rows"],
        "released_endpoint_masks": s["s13_endpoint_geometry"].get(
            "released_endpoint_masks",
            s["s13_endpoint_masks"].get("released_endpoint_masks", 0),
        ),
        "release_grade_endpoint_rows": s["s13_endpoint_geometry"].get("release_grade_endpoint_rows", 0),
        "same_basis_residual_computable_cases": s["s13_endpoint_preflight"]["same_basis_residual_computable_cases"],
        "freeze_ready_candidates": s["candidate_gate"]["freeze_ready_candidates"],
        "final_score_values": s["passive_final_gate"]["final_score_values"],
    }


def build_gate_matrix(s: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    e = evidence_snapshot(s)
    return [
        {
            "order": 1,
            "gate": "working_no_fit_prototype",
            "status": "pass_prototype_only",
            "pass_now": True,
            "evidence": f"P1D nonzero passive rows={s['p1d_prototype']['nonzero_passive_h2_rows']}",
            "blocks_defendable_prediction": False,
            "next_action": "use as architecture and train-context diagnostic artifact",
        },
        {
            "order": 2,
            "gate": "PASSIVE_H2_runtime_support",
            "status": "pass_train_salt2_runtime",
            "pass_now": True,
            "evidence": (
                f"radiation movement cases={s['p1d_prototype']['passive_h2_radiation_movement_nonzero_cases']}; "
                f"runtime delta={s['passive_final_gate']['runtime_radiation_delta_W']} W"
            ),
            "blocks_defendable_prediction": False,
            "next_action": "extend Salt3/Salt4 runtime-smoke only under separate no-score row",
        },
        {
            "order": 3,
            "gate": "PASSIVE_H2_subspan_and_same_QOI_UQ",
            "status": "pass_diagnostic_only_release_closed",
            "pass_now": False,
            "evidence": (
                f"setup patch/subspan support={e['passive_h2_setup_subspan_support_rows']}/"
                f"{e['passive_h2_setup_subspan_total_rows']}; "
                f"Salt3/Salt4 smoke eligible={e['passive_h2_salt34_runtime_smoke_eligible_rows']}/"
                f"{e['passive_h2_salt34_runtime_smoke_total_rows']}; "
                f"diagnostic same-QOI setup UQ={e['passive_h2_same_qoi_setup_uq_available_labels']}/"
                f"{e['passive_h2_same_qoi_total_labels']}; "
                f"release-grade subspan={e['passive_h2_release_grade_subspan_rows']}; "
                f"release-ready same-QOI labels={e['passive_h2_same_qoi_release_ready_labels']}"
            ),
            "blocks_defendable_prediction": True,
            "next_action": "run Salt3/Salt4 diagnostic smoke and exact same-QOI runtime UQ rows; keep release closed",
        },
        {
            "order": 4,
            "gate": "candidate_source_property_release",
            "status": "fail_closed",
            "pass_now": False,
            "evidence": (
                f"candidate-gate release-ready rows={s['candidate_gate']['source_property_release_ready_rows']}; "
                f"strict source-envelope pass rows={s['candidate_gate']['strict_source_envelope_pass_rows']}"
            ),
            "blocks_defendable_prediction": True,
            "next_action": "rerun candidate-specific gate only after row-specific source/property evidence is repaired",
        },
        {
            "order": 5,
            "gate": "S13_endpoint_masks_and_open_CV_residual",
            "status": "fail_closed",
            "pass_now": False,
            "evidence": (
                f"candidate endpoint rows={s['s13_endpoint_geometry'].get('candidate_endpoint_rows_audited', s['s13_endpoint_masks']['candidate_endpoint_masks_written'])}; "
                f"released endpoint masks={e['released_endpoint_masks']}; "
                f"release-grade endpoint rows={e['release_grade_endpoint_rows']}; "
                f"same-basis residual cases={s['s13_endpoint_preflight']['same_basis_residual_computable_cases']}"
            ),
            "blocks_defendable_prediction": True,
            "next_action": "regenerate exact endpoint geometry fields before same-window sampler/cp/storage/loss harvest",
        },
        {
            "order": 6,
            "gate": "freeze_exactly_one_candidate",
            "status": "closed",
            "pass_now": False,
            "evidence": (
                f"freeze-ready candidates={s['candidate_gate']['freeze_ready_candidates']}; "
                f"final score values={s['passive_final_gate']['final_score_values']}"
            ),
            "blocks_defendable_prediction": True,
            "next_action": "open S11/S15/S6 only after prior gates pass",
        },
    ]


def build_minimum_evidence_chain() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "milestone": "Salt3/Salt4 PASSIVE-H2 diagnostic runtime smoke",
            "why_needed": "checks whether the runtime-supported H2 form remains executable beyond Salt2 train support before release work",
            "minimum_evidence": "Salt3/Salt4 no-score smoke rows with forbidden runtime inputs false and split labels preserved",
            "current_state": "eligible only; not launched by this audit",
            "owner_status": "claim TODO-PASSIVE-H2-SALT3-SALT4-DIAGNOSTIC-RUNTIME-SMOKE-2026-07-22",
        },
        {
            "rank": 2,
            "milestone": "exact same-QOI train-only runtime UQ",
            "why_needed": "turn existing diagnostic delta evidence into an explicit train-only uncertainty envelope for the candidate",
            "minimum_evidence": "target-minus/target/target-plus rows for Qwall, exchange, recirculation, wall-core contrast, TP, TW, and mdot",
            "current_state": "diagnostic same-QOI setup UQ exists for 6/6 labels but release-ready labels remain zero",
            "owner_status": "claim exact-row UQ compute/documentation row",
        },
        {
            "rank": 3,
            "milestone": "S13 endpoint/open-CV residual release inputs",
            "why_needed": "defendability requires named pressure/thermal residual ownership, not hidden calibration",
            "minimum_evidence": "endpoint masks with area vectors, owner cells, positive-mdot convention, T_bulk, cp, storage, and named losses",
            "current_state": "candidate masks exist; release-grade endpoint rows and residual-computable cases remain zero",
            "owner_status": "claim endpoint geometry regeneration/exact-field recovery row",
        },
        {
            "rank": 4,
            "milestone": "row-specific source/property release rerun",
            "why_needed": "freeze and residual accounting require source/property evidence independent of target data",
            "minimum_evidence": "strict source envelope pass, cp/property family, split permission, and runtime legality for one candidate",
            "current_state": "candidate gate reports zero release-ready and zero S11-open-ready candidates",
            "owner_status": "rerun only after milestones 1-3 publish evidence",
        },
        {
            "rank": 5,
            "milestone": "freeze then protected score",
            "why_needed": "defendable prediction requires predeclared frozen model before protected evidence",
            "minimum_evidence": "frozen manifest, runtime audit, train-only UQ, then held-out/protected score",
            "current_state": "freeze-ready candidates zero; final score values zero",
            "owner_status": "trigger-gated S11/S15/S6 rows",
        },
    ]


def build_candidate_status(s: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = read_csv(PACKAGES["candidate_gate"] / "candidate_priority_ranking.csv")
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "rank": row.get("rank", ""),
                "current_status": row.get("current_status", row.get("status", "")),
                "thesis_use_now": row.get("thesis_use_now", "diagnostic_or_blocked_evidence"),
                "freeze_ready_now": False,
                "reason": row.get("reason", "source/property and release gates remain closed"),
            }
        )
    if not out:
        out.append(
            {
                "candidate_id": "P1D-BULK-CV-H2-CAND001",
                "rank": 1,
                "current_status": s["p1d_prototype"]["decision"],
                "thesis_use_now": s["p1d_prototype"]["thesis_use"],
                "freeze_ready_now": False,
                "reason": "source/property release and residual-complete gates remain closed",
            }
        )
    return out


def build_action_queue() -> list[dict[str, Any]]:
    candidate_actions = read_csv(PACKAGES["candidate_gate"] / "next_unblock_sequence.csv")
    h2_actions = read_csv(PACKAGES["passive_subspan"] / "next_action_queue.csv")
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            "priority": 1,
            "action": "claim PASSIVE-H2 Salt3/Salt4 diagnostic runtime-smoke row",
            "source": rel(PACKAGES["passive_subspan"] / "next_action_queue.csv"),
            "done_when": "Salt3/Salt4 smoke rows complete or fail cleanly; forbidden runtime inputs remain false; no protected scoring",
            "can_launch_from_audit": False,
        }
    )
    rows.append(
        {
            "priority": 2,
            "action": "claim exact same-QOI runtime UQ rows for PASSIVE-H2",
            "source": rel(PACKAGES["passive_subspan"] / "same_qoi_setup_uq_readiness.csv"),
            "done_when": "Qwall, exchange, recirculation, wall-core contrast, TP/TW/mdot rows have explicit target-minus/target/target-plus provenance; release remains false",
            "can_launch_from_audit": False,
        }
    )
    rows.append(
        {
            "priority": 3,
            "action": "claim S13 endpoint geometry regeneration/exact-field recovery",
            "source": rel(PACKAGES["s13_endpoint_geometry"] / "summary.json"),
            "done_when": "released endpoint masks become nonzero or field-level blocker matrix names remaining missing geometry fields",
            "can_launch_from_audit": False,
        }
    )
    for row in h2_actions:
        if row.get("action") in {
            "claim Salt3/Salt4 diagnostic runtime-smoke row",
            "promote setup-only UQ from deltas to exact target-minus/target/target-plus rows",
        }:
            continue
        rows.append(
            {
                "priority": len(rows) + 1,
                "action": row["action"],
                "source": "PASSIVE-H2 subspan recovery next-action queue",
                "done_when": row["acceptance"],
                "can_launch_from_audit": False,
            }
        )
    offset = len(rows)
    for idx, row in enumerate(candidate_actions, start=offset + 1):
        rows.append(
            {
                "priority": idx,
                "action": row["task"],
                "source": "candidate-specific source/property gate next-unblock sequence",
                "done_when": row["done_when"],
                "can_launch_from_audit": False,
            }
        )
    return rows


def build_split_claim_contract() -> list[dict[str, Any]]:
    return [
        {
            "split": "train_support",
            "used_by_this_audit": True,
            "claim_allowed_now": "diagnostic architecture and gate evidence only",
            "claim_forbidden_now": "frozen coefficients, admitted candidate, protected score, final thesis predictive accuracy",
            "next_legal_use": "run/support no-score smoke and exact train-only UQ rows",
        },
        {
            "split": "validation",
            "used_by_this_audit": False,
            "claim_allowed_now": "none for model selection or scoring",
            "claim_forbidden_now": "coefficient choice, model-form selection, score improvement claim",
            "next_legal_use": "evaluate once a frozen manifest exists",
        },
        {
            "split": "holdout",
            "used_by_this_audit": False,
            "claim_allowed_now": "none for model selection or scoring",
            "claim_forbidden_now": "candidate repair, tuning, or residual ownership inference",
            "next_legal_use": "single protected score after freeze",
        },
        {
            "split": "external_test",
            "used_by_this_audit": False,
            "claim_allowed_now": "none for model selection or scoring",
            "claim_forbidden_now": "fit, freeze, score, or claim transfer performance before frozen model",
            "next_legal_use": "external transfer report after frozen holdout protocol is complete",
        },
    ]


def build_thesis_claims() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "DEF-PRED-001",
            "allowed_now": True,
            "claim": "A working no-fit train-context P1D heat-ledger prototype exists.",
            "evidence": "P1D prototype summary and generated candidate kernel",
            "boundary": "prototype and diagnostic failure localization only",
        },
        {
            "claim_id": "DEF-PRED-002",
            "allowed_now": True,
            "claim": "PASSIVE-H2 is the most mature physical submodel path because runtime radiation movement exists.",
            "evidence": "PASSIVE-H2 runtime/final-form/subspan packets",
            "boundary": "not release-grade or frozen until subspan/source/property gates pass",
        },
        {
            "claim_id": "DEF-PRED-003",
            "allowed_now": False,
            "claim": "A defendable frozen predictive model exists.",
            "evidence": "freeze-ready candidates remain zero",
            "boundary": "requires candidate-specific release, UQ, freeze manifest, then protected score",
        },
        {
            "claim_id": "DEF-PRED-004",
            "allowed_now": False,
            "claim": "The residual is closed or explained quantitatively.",
            "evidence": "same-basis residual-computable cases remain zero",
            "boundary": "requires endpoint/cp/storage/loss evidence",
        },
        {
            "claim_id": "DEF-PRED-005",
            "allowed_now": True,
            "claim": "The shortest rigorous path is now a gate sequence, not a broad model-form search.",
            "evidence": "next_action_queue.csv and minimum_evidence_chain.csv",
            "boundary": "does not authorize launch, release, freeze, or protected scoring",
        },
    ]


def build_freeze_protocol() -> list[dict[str, Any]]:
    return [
        {
            "phase": "pre_freeze",
            "required": "select exactly one candidate from released evidence",
            "must_be_true": "source/property release-ready > 0; runtime audit pass; train-only UQ complete",
            "forbidden": "no validation/holdout/external score; no tuning from protected rows",
        },
        {
            "phase": "freeze",
            "required": "write frozen candidate manifest with model form, inputs, coefficients, split labels, and code hash",
            "must_be_true": "all runtime inputs legal and all residual lanes explicit",
            "forbidden": "no global fitted multiplier; no residual absorption into internal Nu",
        },
        {
            "phase": "post_freeze_score",
            "required": "run protected score exactly once from frozen manifest",
            "must_be_true": "score script consumes frozen manifest and emits immutable scorecard",
            "forbidden": "no candidate replacement or retuning after viewing protected score",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    files = [
        PACKAGES["p1d_prototype"] / "summary.json",
        PACKAGES["candidate_gate"] / "summary.json",
        PACKAGES["candidate_gate"] / "candidate_priority_ranking.csv",
        PACKAGES["candidate_gate"] / "next_unblock_sequence.csv",
        PACKAGES["passive_runtime"] / "summary.json",
        PACKAGES["passive_final_gate"] / "summary.json",
        PACKAGES["passive_subspan"] / "summary.json",
        PACKAGES["passive_subspan"] / "release_gate_matrix.csv",
        PACKAGES["passive_subspan"] / "source_family_patch_subspan_coverage.csv",
        PACKAGES["passive_subspan"] / "same_qoi_setup_uq_readiness.csv",
        PACKAGES["passive_subspan"] / "salt34_runtime_smoke_eligibility.csv",
        PACKAGES["s13_endpoint_preflight"] / "summary.json",
        PACKAGES["s13_endpoint_masks"] / "summary.json",
        PACKAGES["s13_endpoint_geometry"] / "summary.json",
        PACKAGES["source_exact"] / "summary.json",
        PACKAGES["source_recovery"] / "summary.json",
    ]
    return [{"source_path": rel(path), "exists": path.exists(), "use": "read-only gate evidence"} for path in files]


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_p1d_bulk_cv_h2_train_only_thesis_prototype/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery/release_gate_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_geometry_enrichment_for_release_masks/summary.json
tags: [work-product, predictive-1d, defendability, freeze-gate, no-score]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/defendable-predictive-model-path-gate-audit.md
task: {TASK_ID}
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Hydraulics / Writer / Reviewer / Tester
type: work_product
status: complete
---
# Defendable Predictive Model Path Gate Audit

Decision: `{summary["decision"]}`.

This packet walks the route from the current P1D prototype to a defendable
predictive model. The result is not a frozen model: it is a gate-by-gate
execution surface showing what now works, what remains blocked, and what must
happen before a protected score can be used in the thesis.

Current thesis-safe model statement: the P1D/PASSIVE-H2 path is a working
train-context prototype with runtime-supported passive radiation and recovered
diagnostic setup patch/subspan support. A defendable prediction does not exist
yet because release-grade source/property evidence, release-grade endpoint
residual inputs, exact train-only runtime UQ, a frozen manifest, and protected
scoring remain closed.

Shortest rigorous next action:
`claim PASSIVE-H2 Salt3/Salt4 diagnostic runtime-smoke row`. The audit itself
does not authorize compute launch, fitting, release, freeze, or protected
scoring. It keeps train/support, validation, holdout, and external-test claims
separate in `split_claim_contract.csv`.
"""


def main() -> int:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = load_summaries()

    gate_matrix = build_gate_matrix(summaries)
    evidence_chain = build_minimum_evidence_chain()
    candidate_status = build_candidate_status(summaries)
    action_queue = build_action_queue()
    split_claim_contract = build_split_claim_contract()
    thesis_claims = build_thesis_claims()
    freeze_protocol = build_freeze_protocol()

    write_csv(
        OUT / "defendability_gate_matrix.csv",
        gate_matrix,
        ["order", "gate", "status", "pass_now", "evidence", "blocks_defendable_prediction", "next_action"],
    )
    write_csv(
        OUT / "minimum_evidence_chain.csv",
        evidence_chain,
        ["rank", "milestone", "why_needed", "minimum_evidence", "current_state", "owner_status"],
    )
    write_csv(
        OUT / "current_candidate_status.csv",
        candidate_status,
        ["candidate_id", "rank", "current_status", "thesis_use_now", "freeze_ready_now", "reason"],
    )
    write_csv(
        OUT / "next_action_queue.csv",
        action_queue,
        ["priority", "action", "source", "done_when", "can_launch_from_audit"],
    )
    write_csv(
        OUT / "thesis_claim_boundaries.csv",
        thesis_claims,
        ["claim_id", "allowed_now", "claim", "evidence", "boundary"],
    )
    write_csv(
        OUT / "split_claim_contract.csv",
        split_claim_contract,
        ["split", "used_by_this_audit", "claim_allowed_now", "claim_forbidden_now", "next_legal_use"],
    )
    write_csv(
        OUT / "freeze_and_score_protocol.csv",
        freeze_protocol,
        ["phase", "required", "must_be_true", "forbidden"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        source_manifest(),
        ["source_path", "exists", "use"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [{"guardrail": key, "pass": value is False, "value": value} for key, value in GUARDRAILS.items()],
        ["guardrail", "pass", "value"],
    )

    blocking_rows = [row for row in gate_matrix if row["blocks_defendable_prediction"]]
    passing_rows = [row for row in gate_matrix if bool_pass(row["pass_now"])]
    e = evidence_snapshot(summaries)
    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "defendable_predictive_model_not_yet_available_path_now_explicit",
        "defendable_predictive_model_exists_now": False,
        "working_prototype_exists_now": True,
        "candidate_to_carry_forward": "P1D-BULK-CV-H2-CAND001",
        "pass_now_gates": len(passing_rows),
        "blocking_gates": len(blocking_rows),
        "top_blockers": [
            "candidate_source_property_release",
            "S13_endpoint_masks_and_open_CV_residual",
            "PASSIVE_H2_subspan_and_same_QOI_UQ",
        ],
        "shortest_path_next_action": "claim PASSIVE-H2 Salt3/Salt4 diagnostic runtime-smoke row",
        "freeze_ready_candidates": e["freeze_ready_candidates"],
        "final_score_values": e["final_score_values"],
        "source_property_release_ready_rows": e["source_property_release_ready_rows"],
        "strict_source_envelope_pass_rows": e["strict_source_envelope_pass_rows"],
        "released_endpoint_masks": e["released_endpoint_masks"],
        "release_grade_endpoint_rows": e["release_grade_endpoint_rows"],
        "same_basis_residual_computable_cases": e["same_basis_residual_computable_cases"],
        "passive_h2_setup_subspan_support_rows": e["passive_h2_setup_subspan_support_rows"],
        "passive_h2_setup_subspan_total_rows": e["passive_h2_setup_subspan_total_rows"],
        "passive_h2_release_grade_subspan_rows": e["passive_h2_release_grade_subspan_rows"],
        "passive_h2_same_qoi_setup_uq_available_labels": e["passive_h2_same_qoi_setup_uq_available_labels"],
        "passive_h2_same_qoi_total_labels": e["passive_h2_same_qoi_total_labels"],
        "passive_h2_same_qoi_release_ready_labels": e["passive_h2_same_qoi_release_ready_labels"],
        "passive_h2_salt34_runtime_smoke_eligible_rows": e["passive_h2_salt34_runtime_smoke_eligible_rows"],
        "passive_h2_salt34_runtime_smoke_total_rows": e["passive_h2_salt34_runtime_smoke_total_rows"],
        "train_support_claims_only": True,
        "validation_claims_used": False,
        "holdout_claims_used": False,
        "external_test_claims_used": False,
        **GUARDRAILS,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
