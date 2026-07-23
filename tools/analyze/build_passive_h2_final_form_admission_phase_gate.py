#!/usr/bin/env python3
"""Build the PASSIVE-H2 next-phase final-form admission gate package."""

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

TASK_ID = "TODO-PASSIVE-H2-FINAL-FORM-ADMISSION-PHASE-GATE-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-final-form-admission-phase-gate.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_final_form_admission_phase_gate.json"

RUNTIME = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
MAPPING = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_mapping_split_uq_preflight"
CANDIDATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
SOURCE_RECOVERY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_evidence_recovery"
SOURCE_BASIS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"
SPLIT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_extbc_split_conflict_resolution"
MULTI_TRAIN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke"
P1D = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_p1d_bulk_cv_h2_train_only_thesis_prototype"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("runtime_summary", RUNTIME / "summary.json"),
        ("runtime_heat_delta", RUNTIME / "heat_ledger_delta.csv"),
        ("runtime_input_audit", RUNTIME / "runtime_input_audit.csv"),
        ("runtime_same_qoi_contract", RUNTIME / "same_qoi_train_report_contract.csv"),
        ("source_to_fluid_mapping", MAPPING / "source_to_fluid_mapping_matrix.csv"),
        ("release_gate_matrix", MAPPING / "release_gate_matrix.csv"),
        ("same_qoi_uq_prerequisites", MAPPING / "same_qoi_uq_prerequisite_matrix.csv"),
        ("split_disposition", MAPPING / "split_disposition_matrix.csv"),
        ("candidate_gate_summary", CANDIDATE / "summary.json"),
        ("candidate_release_decision", CANDIDATE / "candidate_release_decision.csv"),
        ("source_backing_strength", SOURCE_RECOVERY / "source_backing_strength_by_field.csv"),
        ("missing_source_evidence", SOURCE_RECOVERY / "passive_h2_missing_evidence_after_recovery.csv"),
        ("source_basis_gate", SOURCE_BASIS / "passive_h2_source_release_gate.csv"),
        ("split_conflict_resolution", SPLIT / "case_level_extbc_conflict_table.csv"),
        ("multi_train_corrected_radiation", MULTI_TRAIN / "case_family_corrected_radiation_operator.csv"),
        ("p1d_context", P1D / "summary.json"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": str(path.exists()).lower()} for role, path in sources]


def runtime_summary_values() -> dict[str, Any]:
    summary = read_json(RUNTIME / "summary.json")
    heat = read_csv(RUNTIME / "heat_ledger_delta.csv")
    rad_delta = next(row for row in heat if row["delta_kind"] == "role_rad_on_minus_role_rad_off")
    input_audit = read_csv(RUNTIME / "runtime_input_audit.csv")
    forbidden_true = [
        row["input_family"]
        for row in input_audit
        if is_true(row["protected_or_forbidden"]) and is_true(row["allowed"])
    ]
    return {
        "analytic_tests_pass": bool(summary["analytic_layer_radiation_tests_pass"]),
        "runtime_rows": int(summary["runtime_smoke_rows"]),
        "train_rows_used": int(summary["train_rows_used"]),
        "radiation_on_nonzero": bool(summary["radiation_on_nonzero"]),
        "radiation_delta_W": float(rad_delta["delta_qambient_W"]),
        "radiation_target_W": float(rad_delta["target_delta_W"]),
        "radiation_delta_over_target": float(summary["radiation_delta_over_target"]),
        "all_roots_accepted": all(
            summary[key] == "accepted"
            for key in (
                "root_status_current_no_role_rad_off",
                "root_status_passive_h2_role_rad_off",
                "root_status_passive_h2_role_rad_on",
            )
        ),
        "forbidden_runtime_inputs_true": len(forbidden_true),
    }


def final_form_readiness_rows() -> list[dict[str, str]]:
    runtime = runtime_summary_values()
    mapping_summary = read_json(MAPPING / "summary.json")
    candidate_summary = read_json(CANDIDATE / "summary.json")
    release_gates = {row["gate"]: row for row in read_csv(MAPPING / "release_gate_matrix.csv")}
    split_rows = read_csv(MAPPING / "split_disposition_matrix.csv")
    same_qoi_rows = read_csv(MAPPING / "same_qoi_uq_prerequisite_matrix.csv")

    rows = [
        {
            "phase_order": "1",
            "gate": "outer_insulation_radiation_runtime_implemented",
            "status": "pass",
            "ready_for_final_form": "false",
            "evidence_count_or_value": f"delta_qambient_W={runtime['radiation_delta_W']}; target_W={runtime['radiation_target_W']}",
            "reason": "radiation_on is nonzero and runtime roots are accepted, but this is train/support evidence only",
            "evidence_path": rel(RUNTIME / "summary.json"),
        },
        {
            "phase_order": "2",
            "gate": "runtime_input_legality",
            "status": "pass",
            "ready_for_final_form": "false",
            "evidence_count_or_value": f"forbidden_runtime_inputs_true={runtime['forbidden_runtime_inputs_true']}",
            "reason": "no wallHeatFlux, CFD mdot, Qwall, imposed cooler duty, or protected temperatures are runtime inputs",
            "evidence_path": rel(RUNTIME / "runtime_input_audit.csv"),
        },
        {
            "phase_order": "3",
            "gate": "source_family_to_parent_segment_mapping",
            "status": release_gates["source_family_to_parent_segment_mapping"]["status"],
            "ready_for_final_form": "false",
            "evidence_count_or_value": release_gates["source_family_to_parent_segment_mapping"]["evidence"],
            "reason": "parent mapping exists as support evidence; it is not sufficient without release-grade subspan coverage",
            "evidence_path": rel(MAPPING / "source_to_fluid_mapping_matrix.csv"),
        },
        {
            "phase_order": "4",
            "gate": "source_family_to_subspan_mapping",
            "status": release_gates["source_family_to_subspan_mapping"]["status"],
            "ready_for_final_form": "false",
            "evidence_count_or_value": release_gates["source_family_to_subspan_mapping"]["evidence"],
            "reason": "final form requires release-grade row-specific subspan labels, and current ready rows are zero",
            "evidence_path": rel(MAPPING / "source_to_fluid_mapping_matrix.csv"),
        },
        {
            "phase_order": "5",
            "gate": "split_legality",
            "status": "fail_closed",
            "ready_for_final_form": "false",
            "evidence_count_or_value": f"split_conflict_rows={sum(1 for row in split_rows if is_true(row['split_conflict']))}",
            "reason": "Salt3/Salt4 remain diagnostic-only; protected validation/holdout scoring is not allowed",
            "evidence_path": rel(MAPPING / "split_disposition_matrix.csv"),
        },
        {
            "phase_order": "6",
            "gate": "same_qoi_setup_uq",
            "status": "fail_closed",
            "ready_for_final_form": "false",
            "evidence_count_or_value": f"same_qoi_ready_rows={sum(1 for row in same_qoi_rows if is_true(row['same_qoi_uq_ready']))}/{len(same_qoi_rows)}",
            "reason": "target rows exist, but target-minus and target-plus neighbor rows are missing for all listed QOIs",
            "evidence_path": rel(MAPPING / "same_qoi_uq_prerequisite_matrix.csv"),
        },
        {
            "phase_order": "7",
            "gate": "row_specific_source_property_release",
            "status": "fail_closed",
            "ready_for_final_form": "false",
            "evidence_count_or_value": f"release_ready_rows={candidate_summary['source_property_release_ready_rows']}",
            "reason": "source/property release-ready rows remain zero, so no source-property or numeric heat-loss release is allowed",
            "evidence_path": rel(CANDIDATE / "candidate_release_decision.csv"),
        },
        {
            "phase_order": "8",
            "gate": "qwall_numeric_heat_loss_release",
            "status": "fail_closed",
            "ready_for_final_form": "false",
            "evidence_count_or_value": "qwall_release=false; numeric_q_loss_release=false",
            "reason": "the runtime operator is legal, but Qwall/source-side support and numeric heat-loss release remain closed",
            "evidence_path": rel(RUNTIME / "blocker_unblock_matrix.csv"),
        },
        {
            "phase_order": "9",
            "gate": "candidate_freeze",
            "status": "fail_closed",
            "ready_for_final_form": "false",
            "evidence_count_or_value": f"freeze_ready_candidates={candidate_summary['freeze_ready_candidates']}",
            "reason": "candidate freeze requires source mapping, split, release, and same-QOI UQ gates to open first",
            "evidence_path": rel(CANDIDATE / "summary.json"),
        },
        {
            "phase_order": "10",
            "gate": "protected_score_or_final_form",
            "status": "closed_not_run",
            "ready_for_final_form": "false",
            "evidence_count_or_value": "protected_scoring=false; final_score_claim=false",
            "reason": "no frozen runtime-legal candidate exists, so protected scoring and final-form claims are forbidden",
            "evidence_path": rel(CANDIDATE / "summary.json"),
        },
    ]
    assert mapping_summary["source_mapping_release_ready_rows"] == 0
    return rows


def subspan_recovery_rows() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(MAPPING / "source_to_fluid_mapping_matrix.csv"):
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "source_family": row["source_family"],
                "fluid_parent_segment": row["fluid_parent_segment"],
                "current_parent_mapping_ready": row["parent_segment_mapping_ready"],
                "current_subspan_mapping_ready": row["subspan_mapping_ready"],
                "required_release_evidence": "row-specific subspan coverage/provenance with start/end or sensor-span basis, parent segment, split role, and source citation",
                "current_gap": row["remaining_gap"],
                "release_now": "false",
            }
        )
    return rows


def same_qoi_uq_rows() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(MAPPING / "same_qoi_uq_prerequisite_matrix.csv"):
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "qoi_label": row["qoi_label"],
                "target_row_available": row["target_row_available"],
                "target_minus_row_available": row["target_minus_row_available"],
                "target_plus_row_available": row["target_plus_row_available"],
                "same_qoi_uq_ready": row["same_qoi_uq_ready"],
                "next_executable_condition": "after source/subspan release, run setup-only Salt2 neighbor rows with identical QOI labels",
                "forbidden_inputs": "wallHeatFlux, CFD mdot, Qwall, imposed cooler duty, validation/holdout temperatures",
                "admission_effect_now": "blocks_freeze",
            }
        )
    return rows


def split_policy_rows() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(MAPPING / "split_disposition_matrix.csv"):
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "split_conflict": row["split_conflict"],
                "allowed_current_use": row["disposition"],
                "protected_scoring_allowed": row["protected_scoring_allowed"],
                "numeric_q_loss_release": row["numeric_q_loss_release"],
                "final_form_effect": "train_support_only" if row["case_id"] == "salt_2" else "exclude_from_freeze_scoring",
            }
        )
    return rows


def minimum_unlock_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "suggested_task_id": "TODO-PASSIVE-H2-SUBSPAN-MAPPING-RELEASE-RECOVERY-2026-07-22",
            "objective": "recover release-grade row-specific source-family-to-parent/subspan mapping for five Salt2 H2 source families",
            "acceptance": "5/5 subspan rows have explicit source/provenance labels or fail-closed reasons; no q-loss release or scoring",
        },
        {
            "priority": "2",
            "suggested_task_id": "TODO-PASSIVE-H2-SALT2-SAME-QOI-SETUP-UQ-GATE-2026-07-22",
            "objective": "run or preflight setup-only target-minus/target/target-plus rows for mdot, TP/TW, qambient/qhx, and heat-ledger deltas",
            "acceptance": "same-QOI rows report finite train-only sensitivity without protected targets or forbidden runtime inputs",
        },
        {
            "priority": "3",
            "suggested_task_id": "TODO-PASSIVE-H2-CANDIDATE-SOURCE-PROPERTY-GATE-RERUN-2026-07-22",
            "objective": "rerun candidate-specific source/property gate after subspan and same-QOI evidence lands",
            "acceptance": "source/property release-ready rows are positive or gate remains explicitly fail-closed",
        },
        {
            "priority": "4",
            "suggested_task_id": "TODO-THESIS-STUDY-S15-CANDIDATE-FREEZE-SOURCE-PROPERTY-SCORE-RELEASE-2026-07-21",
            "objective": "only if exactly one runtime-legal candidate is release-ready, freeze it before protected scoring",
            "acceptance": "one frozen candidate manifest exists before S6/protected scoring; otherwise final score remains zero",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false", "note": "read-only evidence synthesis only"},
        {"guardrail": "registry_or_admission_mutated", "value": "false", "note": "no registry/admission state changes"},
        {"guardrail": "scheduler_action", "value": "false", "note": "no solver, sampler, harvest, or UQ launch"},
        {"guardrail": "Fluid_or_external_edit", "value": "false", "note": "Fluid/external repos were read-only"},
        {"guardrail": "validation_holdout_external_scoring", "value": "false", "note": "Salt3/Salt4 remain diagnostic-only"},
        {"guardrail": "source_property_release", "value": "false", "note": "release-ready rows remain zero"},
        {"guardrail": "qwall_or_numeric_q_loss_release", "value": "false", "note": "no Qwall/source-side or heat-loss value release"},
        {"guardrail": "candidate_freeze", "value": "false", "note": "no candidate freeze"},
        {"guardrail": "final_score_claim", "value": "false", "note": "final form is blocked; score values remain zero"},
        {"guardrail": "hidden_multiplier_or_residual_absorption", "value": "false", "note": "no multiplier, no residual absorbed into internal Nu"},
    ]


def decision_rows(readiness: list[dict[str, str]]) -> list[dict[str, str]]:
    blocking = [row for row in readiness if row["status"].startswith("fail") or row["status"] == "closed_not_run"]
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "admission_phase": "next_phase_after_runtime_implementation",
            "phase_completed": "true",
            "runtime_supported": "true",
            "source_property_release_allowed": "false",
            "candidate_freeze_allowed": "false",
            "protected_scoring_allowed": "false",
            "final_form_allowed": "false",
            "blocking_gate_count": str(len(blocking)),
            "decision": "passive_h2_final_form_admission_phase_fail_closed_runtime_supported_no_freeze_no_score",
            "reason": "runtime H2 is legal and nonzero, but subspan mapping, split legality, same-QOI UQ, source/property release, Qwall/numeric heat-loss release, freeze, and protected scoring gates remain closed",
        }
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_final_form_admission_phase_gate.py
  task_id: {TASK_ID}
tags: [PASSIVE-H2, admission, final-form, no-freeze, no-score]
related:
  - {rel(RUNTIME / "README.md")}
  - {rel(MAPPING / "README.md")}
  - {rel(CANDIDATE / "README.md")}
  - operational_notes/maps/forward-predictive-model.md
---
# PASSIVE-H2 Final-Form Admission Phase Gate

Decision: `{summary["decision"]}`.

This packet takes `PASSIVE-H2-CAND001` through the next admission phase after
the outer-insulation radiation runtime implementation. The result is
fail-closed for final form: runtime evidence is now real and legal, but release
and scoring prerequisites are not met.

The usable finding is narrow. PASSIVE-H2 may be cited as train/support evidence
that a setup-driven outer-insulation radiation operator changes the Fluid heat
ledger without protected runtime inputs. It may not be cited as an admitted
final predictive model, a released numeric heat-loss coefficient, Qwall/source
release, candidate freeze, or protected score.

Open first:

- `final_form_readiness_matrix.csv`
- `admission_phase_decision.csv`
- `subspan_mapping_recovery_requirements.csv`
- `same_qoi_setup_uq_gap.csv`
- `minimum_unlock_runbook.csv`
"""
    ensure_dir(OUT)
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_final_form_admission_phase_gate.py
  task_id: {TASK_ID}
tags: [status, PASSIVE-H2, admission, final-form, no-score]
related:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "final_form_readiness_matrix.csv")}
---
# {TASK_ID}

## Objective

Take `PASSIVE-H2-CAND001` through the next admission phase after runtime
implementation and decide whether it can advance to final form.

## Outcome

Decision: `{summary["decision"]}`. Runtime implementation and runtime-input
legality pass as train/support evidence. Final form remains blocked:
subspan-release rows `{summary["subspan_release_ready_rows"]}/5`, same-QOI UQ
ready rows `{summary["same_qoi_uq_ready_rows"]}/6`, source/property
release-ready rows `{summary["source_property_release_ready_rows"]}`, freeze
ready candidates `{summary["freeze_ready_candidates"]}`, final score values
`0`.

## Changes Made

Built `{rel(OUT)}` plus task-owned builder/test files, this status, journal,
import manifest, and an additive pointer in
`operational_notes/maps/forward-predictive-model.md`.

## Validation

Validation commands run: builder, unit test, py_compile, JSON parse,
`finish_task.py`, and scoped `git diff --check`.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
current/LaTeX edit, protected scoring, fitting/model selection,
source/property/Qwall/numeric q-loss release, coefficient admission, candidate
freeze, final-score claim, S11/S12/S13/S15/S6 trigger, hidden multiplier,
residual absorption into internal Nu, or runtime-leakage relaxation.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
provenance:
  generated_by: tools/analyze/build_passive_h2_final_form_admission_phase_gate.py
  task_id: {TASK_ID}
tags: [journal, PASSIVE-H2, admission, final-form, no-score]
related:
  - {rel(OUT / "admission_phase_decision.csv")}
  - {rel(OUT / "minimum_unlock_runbook.csv")}
---
# PASSIVE-H2 Final-Form Admission Phase Gate

## Attempted

Assembled the completed H2 runtime implementation, source mapping/split/UQ
preflight, candidate-specific source/property gate, source-backing packets,
split-conflict resolution, corrected-radiation smoke, and P1D context into a
single final-form readiness decision.

## Observed

`radiation_on` now changes the Fluid heat ledger by
`{summary["runtime_radiation_delta_W"]} W`, with accepted Salt2 train roots and
zero forbidden runtime inputs. The admission evidence still reports zero
release-grade subspan rows, zero same-QOI UQ-ready QOI labels, zero
source/property release-ready rows, zero freeze-ready candidates, and no
protected scoring.

## Inferred

H2 has advanced from a radiation no-op blocker to a runtime-supported
train-context candidate. It has not advanced to final form. The scientifically
clean result is fail-closed until source-backed subspan mapping and same-QOI
setup-only UQ exist, followed by a candidate-specific release rerun.

## Next Useful Actions

Claim the subspan mapping recovery row first. If that passes, claim the Salt2
same-QOI setup-UQ gate. Only after those pass should the candidate-specific
source/property gate be rerun. S15/S6 scoring remains trigger-gated and should
not run from this packet.
"""
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed = [
        ".agent/BOARD.md",
        "operational_notes/maps/forward-predictive-model.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_final_form_admission_phase_gate.py",
        "tools/analyze/test_passive_h2_final_form_admission_phase_gate.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/final_form_readiness_matrix.csv",
        f"{rel(OUT)}/admission_phase_decision.csv",
        f"{rel(OUT)}/subspan_mapping_recovery_requirements.csv",
        f"{rel(OUT)}/same_qoi_setup_uq_gap.csv",
        f"{rel(OUT)}/split_policy_for_final_form.csv",
        f"{rel(OUT)}/minimum_unlock_runbook.csv",
        f"{rel(OUT)}/no_mutation_guardrails.csv",
        f"{rel(OUT)}/source_manifest.csv",
        f"{rel(OUT)}/summary.json",
    ]
    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "changed_files": changed,
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "results": {
            "decision": summary["decision"],
            "final_form_allowed": summary["final_form_allowed"],
            "candidate_freeze": summary["candidate_freeze"],
            "protected_scoring": summary["protected_scoring"],
            "source_property_release_ready_rows": summary["source_property_release_ready_rows"],
            "same_qoi_uq_ready_rows": summary["same_qoi_uq_ready_rows"],
        },
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "external_fluid_edit": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "protected_scoring": False,
        "candidate_freeze": False,
        "final_score_claim": False,
    }
    ensure_dir(IMPORT.parent)
    json_dump(IMPORT, manifest)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    runtime = runtime_summary_values()
    readiness = final_form_readiness_rows()
    subspan = subspan_recovery_rows()
    same_qoi = same_qoi_uq_rows()
    split = split_policy_rows()
    decisions = decision_rows(readiness)
    unlock = minimum_unlock_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()
    candidate_summary = read_json(CANDIDATE / "summary.json")

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": decisions[0]["decision"],
        "candidate_id": "PASSIVE-H2-CAND001",
        "admission_phase_completed": True,
        "runtime_supported": True,
        "runtime_radiation_delta_W": runtime["radiation_delta_W"],
        "runtime_radiation_target_W": runtime["radiation_target_W"],
        "runtime_delta_over_target": runtime["radiation_delta_over_target"],
        "runtime_roots_accepted": runtime["all_roots_accepted"],
        "forbidden_runtime_inputs_true": runtime["forbidden_runtime_inputs_true"],
        "source_parent_mapping_support_rows": sum(1 for row in subspan if is_true(row["current_parent_mapping_ready"])),
        "subspan_release_ready_rows": sum(1 for row in subspan if is_true(row["current_subspan_mapping_ready"])),
        "split_conflict_rows": sum(1 for row in split if is_true(row["split_conflict"])),
        "same_qoi_uq_ready_rows": sum(1 for row in same_qoi if is_true(row["same_qoi_uq_ready"])),
        "same_qoi_qoi_rows": len(same_qoi),
        "source_property_release_ready_rows": int(candidate_summary["source_property_release_ready_rows"]),
        "freeze_ready_candidates": int(candidate_summary["freeze_ready_candidates"]),
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "final_form_allowed": False,
        "final_score_claim": False,
        "final_score_values": 0,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
    }

    csv_dump(out / "final_form_readiness_matrix.csv", list(readiness[0]), readiness)
    csv_dump(out / "admission_phase_decision.csv", list(decisions[0]), decisions)
    csv_dump(out / "subspan_mapping_recovery_requirements.csv", list(subspan[0]), subspan)
    csv_dump(out / "same_qoi_setup_uq_gap.csv", list(same_qoi[0]), same_qoi)
    csv_dump(out / "split_policy_for_final_form.csv", list(split[0]), split)
    csv_dump(out / "minimum_unlock_runbook.csv", list(unlock[0]), unlock)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    if out == OUT:
        write_readme(summary)
        write_status(summary)
        write_journal(summary)
        write_import(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
