#!/usr/bin/env python3
"""Build PASSIVE-H2 predictive finish readiness closure.

This package asks whether the current PASSIVE-H2 evidence can legally advance
from diagnostic runtime evidence to predictive freeze/admission. It also tests
the tempting reduced four-family path and records why that is not a shortcut to
freezing the current candidate.
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

TASK_ID = "TODO-PASSIVE-H2-PREDICTIVE-FINISH-READINESS-CLOSURE-2026-07-22"
SLUG = "passive_h2_predictive_finish_readiness_closure"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_predictive_finish_readiness_closure"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-predictive-finish-readiness-closure.md"
IMPORT = ROOT / f"imports/2026-07-22_{SLUG}.json"

POLICY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_candidate_gate_rerun_passive_role_filtered_policy"
THESIS_BUNDLE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition"
SALT1 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict"
BURNDOWN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_h2_s13_modelform_blocker_burndown"
SOURCE_EVIDENCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_evidence_recovery"
SALT2_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate"
FINAL_FORM = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate"

FAMILIES = ["cooling_branch", "downcomer", "junction", "lower_leg", "upcomer"]
REDUCED_FAMILIES = ["cooling_branch", "downcomer", "lower_leg", "upcomer"]


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
    paths = [
        ("policy_summary", POLICY / "summary.json"),
        ("policy_gate_matrix", POLICY / "candidate_gate_rerun_matrix.csv"),
        ("thesis_bundle_summary", THESIS_BUNDLE / "summary.json"),
        ("thesis_source_disposition", THESIS_BUNDLE / "source_property_final_disposition.csv"),
        ("salt1_summary", SALT1 / "summary.json"),
        ("salt1_operator_rows", SALT1 / "salt1_recovered_operator_rows_for_fluid.csv"),
        ("burndown_release_provenance", BURNDOWN / "h2_release_grade_source_property_provenance.csv"),
        ("burndown_source_envelope_gap", BURNDOWN / "passive_h2_source_envelope_gap_matrix.csv"),
        ("source_evidence_matrix", SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv"),
        ("same_qoi_setup_uq", SALT2_UQ / "qoi_readiness_gate.csv"),
        ("final_form_split_policy", FINAL_FORM / "split_policy_for_final_form.csv"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": bool_s(path.exists())} for role, path in paths]


def salt1_coverage_rows() -> list[dict[str, str]]:
    rows = read_csv(SALT1 / "salt1_recovered_operator_rows_for_fluid.csv")
    present = {row["source_family"]: row for row in rows}
    out: list[dict[str, str]] = []
    for family in FAMILIES:
        row = present.get(family, {})
        out.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": "salt_1",
                "source_family": family,
                "operator_row_present": bool_s(family in present),
                "setup_basis_status": "present_setup_runtime_only" if family in present else "missing_case_family_coverage",
                "area_m2": row.get("area_m2", ""),
                "hA_W_K": row.get("hA_W_K", ""),
                "release_allowed": "false",
                "freeze_allowed": "false",
                "reason": "Salt1 setup row exists but remains no-score/no-release" if family in present else "Salt1 junction row is absent from recovered operator rows",
                "evidence_path": rel(SALT1 / "salt1_recovered_operator_rows_for_fluid.csv") if family in present else rel(SALT1 / "summary.json"),
            }
        )
    return out


def strict_gate_counts(families: list[str]) -> dict[str, int]:
    disposition = read_csv(THESIS_BUNDLE / "source_property_final_disposition.csv")
    relevant = [row for row in disposition if row.get("source_family") in families]
    return {
        "rows": len(relevant),
        "setup_ready": sum(row.get("setup_basis_status", "").startswith("repaired") for row in relevant),
        "release": sum(truth(row.get("release_allowed_now")) for row in relevant),
        "freeze": sum(truth(row.get("freeze_allowed_now")) for row in relevant),
        "score": sum(truth(row.get("score_allowed_now")) for row in relevant),
        "source_envelope": sum(row.get("strict_source_envelope_status") == "admitted" for row in relevant),
        "same_qoi_uq": sum(row.get("same_qoi_release_uq_status") == "release_ready" for row in relevant),
    }


def readiness_rows() -> list[dict[str, str]]:
    salt1_present = {row["source_family"] for row in read_csv(SALT1 / "salt1_recovered_operator_rows_for_fluid.csv")}
    options = [
        (
            "full_five_family_current_candidate",
            FAMILIES,
            "current PASSIVE-H2-CAND001 as defined by the five passive source families",
            False,
        ),
        (
            "reduced_four_family_no_junction_candidate",
            REDUCED_FAMILIES,
            "post-hoc reduced operator excluding junction",
            True,
        ),
    ]
    rows: list[dict[str, str]] = []
    for option_id, families, definition, changes_definition in options:
        counts = strict_gate_counts(families)
        salt1_ok = all(family in salt1_present for family in families)
        strict_ok = counts["source_envelope"] == counts["rows"] and counts["rows"] > 0
        uq_ok = counts["same_qoi_uq"] == counts["rows"] and counts["rows"] > 0
        release_ok = counts["release"] == counts["rows"] and counts["rows"] > 0
        freeze_ok = salt1_ok and strict_ok and uq_ok and release_ok and not changes_definition
        hard_fails = []
        if not salt1_ok:
            hard_fails.append("salt1_family_coverage")
        if changes_definition:
            hard_fails.append("posthoc_candidate_definition_change")
        if not strict_ok:
            hard_fails.append("strict_source_envelope")
        if not uq_ok:
            hard_fails.append("same_qoi_release_uq")
        if not release_ok:
            hard_fails.append("source_property_release")
        rows.append(
            {
                "candidate_option": option_id,
                "candidate_definition": definition,
                "families": ";".join(families),
                "salt1_family_coverage_ready": bool_s(salt1_ok),
                "strict_source_envelope_ready": bool_s(strict_ok),
                "same_qoi_release_uq_ready": bool_s(uq_ok),
                "source_property_release_ready": bool_s(release_ok),
                "changes_current_candidate_definition": bool_s(changes_definition),
                "predictive_freeze_allowed_now": bool_s(freeze_ok),
                "protected_or_final_score_allowed_now": bool_s(False),
                "hard_fail_gates": ";".join(hard_fails) if hard_fails else "none",
                "decision": "freeze_allowed" if freeze_ok else "fail_closed_no_freeze",
                "next_step": "freeze and score" if freeze_ok else "predeclare new candidate or repair release gates before freeze",
            }
        )
    return rows


def source_gap_rows() -> list[dict[str, str]]:
    source_rows = {row["source_family"]: row for row in read_csv(SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv")}
    salt1_present = {row["source_family"] for row in read_csv(SALT1 / "salt1_recovered_operator_rows_for_fluid.csv")}
    out: list[dict[str, str]] = []
    for family in FAMILIES:
        source = source_rows.get(family, {})
        out.append(
            {
                "source_family": family,
                "salt1_setup_row_present": bool_s(family in salt1_present),
                "salt2_4_setup_basis_ready": bool_s(truth(source.get("source_basis_release_ready_now"))),
                "strict_source_envelope_status": "not_admitted",
                "same_qoi_release_uq_status": "missing_release_grade",
                "source_property_release_status": "fail_closed",
                "reduced_four_family_membership": bool_s(family in REDUCED_FAMILIES),
                "repairability": "repairable_by_recovering_salt1_junction_plus_strict_envelope_and_uq" if family == "junction" else "repairable_by_strict_envelope_and_uq_only",
                "minimal_evidence_needed": "recover Salt1 junction setup row; admit strict source envelope; run release-grade same-QOI UQ" if family == "junction" else "admit strict source envelope; run release-grade same-QOI UQ",
                "evidence_path": rel(SOURCE_EVIDENCE / "passive_h2_family_evidence_recovery_matrix.csv"),
            }
        )
    return out


def reduced_policy_rows() -> list[dict[str, str]]:
    return [
        {
            "policy_question": "Can the current five-family PASSIVE-H2 candidate freeze now?",
            "decision": "no",
            "reason": "Salt1 lacks junction coverage and all source-envelope/UQ/release gates remain closed.",
            "allowed_next_action": "repair missing evidence or publish diagnostic-only thesis result",
        },
        {
            "policy_question": "Can a four-family no-junction subset be frozen as the current candidate?",
            "decision": "no",
            "reason": "Dropping junction after observing the evidence gap changes the model definition and would be post-hoc selection.",
            "allowed_next_action": "predeclare a new reduced PASSIVE-H2-R4 candidate before any scoring or protected comparison",
        },
        {
            "policy_question": "Can a reduced four-family candidate be opened as a future path?",
            "decision": "yes_as_new_predeclared_no_score_candidate_only",
            "reason": "Salt1 has setup rows for the four retained families, but strict source-envelope and same-QOI release UQ still must pass before freeze.",
            "allowed_next_action": "claim a new PASSIVE-H2-R4 source-envelope/UQ row with no scoring until release gates pass",
        },
    ]


def runbook_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "row_to_claim": "TODO-PASSIVE-H2-R4-PREDECLARED-SOURCE-ENVELOPE-UQ-GATE-2026-07-22",
            "purpose": "Open a new four-family no-junction candidate before any scoring.",
            "acceptance": "candidate definition frozen before evidence use; strict source-envelope rows and release-UQ rows decide freeze.",
            "stop_condition": "if any retained family lacks strict source-envelope or release-UQ, no freeze",
        },
        {
            "priority": "2",
            "row_to_claim": "TODO-PASSIVE-H2-SALT1-JUNCTION-SETUP-ROW-RECOVERY-2026-07-22",
            "purpose": "Try to restore full five-family current-candidate coverage.",
            "acceptance": "Salt1 junction operator row has area/hA/h/Ta/Tsur/emissivity/layer provenance and passes runtime-input lint.",
            "stop_condition": "if no non-leaky junction setup row exists, full five-family candidate remains permanently blocked in current corpus",
        },
        {
            "priority": "3",
            "row_to_claim": "TODO-PASSIVE-H2-RELEASE-GRADE-SAME-QOI-UQ-ONLY-AFTER-ENVELOPE-2026-07-22",
            "purpose": "Run release-grade UQ only after strict source-envelope rows pass.",
            "acceptance": "same QOI labels, same frozen operator, train/support only until freeze, no protected target use",
            "stop_condition": "do not run if strict source-envelope remains 0-pass",
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
        {"guardrail": "coefficient_admission", "value": "false"},
        {"guardrail": "candidate_freeze", "value": "false"},
        {"guardrail": "protected_or_final_scoring", "value": "false"},
        {"guardrail": "hidden_multiplier_or_residual_absorption", "value": "false"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(POLICY / "summary.json")}
  - {rel(THESIS_BUNDLE / "source_property_final_disposition.csv")}
  - {rel(SALT1 / "salt1_recovered_operator_rows_for_fluid.csv")}
tags: [PASSIVE-H2, predictive-readiness, freeze-gate, no-release]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Predictive Finish Readiness Closure

Decision: `{summary["decision"]}`.

The current PASSIVE-H2 candidate cannot be finished as an admitted predictive
model from the available corpus. Salt1 runtime support now exists for four
families, but the five-family candidate still lacks Salt1 junction coverage and
both the full and reduced options fail strict source-envelope, same-QOI release
UQ, and source/property release gates.

## Result

- Full five-family freeze allowed now: `false`.
- Reduced four-family freeze as current candidate: `false`.
- Reduced four-family future path: allowed only as a new predeclared no-score
  candidate row.
- Source/property release rows: `{summary["source_property_release_rows"]}`.
- Candidate freeze rows: `{summary["freeze_allowed_rows"]}`.
- Final score values emitted: `{summary["final_score_values"]}`.

## Finish Policy

Use PASSIVE-H2 now as thesis diagnostic evidence and runtime-contract evidence.
Do not claim predictive admission until a predeclared candidate has complete
train/support coverage, strict source-envelope admission, release-grade
same-QOI UQ, and a freeze before protected scoring.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_closeout(summary: dict[str, Any]) -> None:
    ensure_dir(STATUS.parent)
    status = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "predictive_finish_readiness_matrix.csv")}
  - {rel(OUT / "reduced_family_freeze_policy.csv")}
tags: [PASSIVE-H2, predictive-readiness, freeze-gate, no-release]
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

Objective: evaluate the shortest path to finish PASSIVE-H2 as a predictive
model using the completed Salt1-4 setup/runtime/source evidence, including the
reduced four-family no-junction option.

Outcome: `{summary["decision"]}`. Full five-family freeze is not allowed, and
the four-family no-junction path cannot be frozen as the current candidate
because it changes the model definition after observing the evidence gap.
Release/freeze/final-score rows remain `{summary["source_property_release_rows"]}`
/ `{summary["freeze_allowed_rows"]}` / `{summary["final_score_values"]}`.

## Changes Made

- `{rel(OUT)}`
- `{rel(Path("tools/analyze/build_passive_h2_predictive_finish_readiness_closure.py"))}`
- `{rel(Path("tools/analyze/test_passive_h2_predictive_finish_readiness_closure.py"))}`
- `{rel(IMPORT)}`
- `.agent/STATE.md`
- `.agent/catalog.json`
- `.agent/catalog.csv`
- `.agent/BLOCKERS.md`

## Validation

- `python3.11 tools/analyze/build_passive_h2_predictive_finish_readiness_closure.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_predictive_finish_readiness_closure`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_predictive_finish_readiness_closure.py tools/analyze/test_passive_h2_predictive_finish_readiness_closure.py`
- `python3.11 tools/agent/runtime_input_lint.py {rel(OUT)} {rel(STATUS)} {rel(JOURNAL)} {rel(IMPORT)}`
- `python3.11 tools/agent/split_policy_lint.py {rel(OUT)} {rel(STATUS)} {rel(JOURNAL)} {rel(IMPORT)}`
- `python3.11 tools/agent/manifest_check.py {rel(IMPORT)} --check-paths`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
LaTeX edit, protected/final scoring, fitting/tuning/model selection,
source/property release, Qwall release, numeric q-loss release, coefficient
admission, candidate freeze, hidden multiplier, residual absorption, or
runtime-leakage relaxation.
"""
    STATUS.write_text(status, encoding="utf-8")

    ensure_dir(JOURNAL.parent)
    journal = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "source_envelope_uq_gap_ledger.csv")}
tags: [PASSIVE-H2, predictive-readiness, no-freeze]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Predictive Finish Readiness Closure

Attempted: use all available Salt1-4 PASSIVE-H2 evidence to determine whether
the model can be finished as a predictive candidate now, including a reduced
four-family path that excludes the missing Salt1 junction row.

Observed: Salt1 now supports cooling_branch, downcomer, lower_leg, and upcomer
setup-runtime rows, but not junction. Existing Salt2-4 setup evidence is
complete for five families. Strict source-envelope admission remains closed for
all families, same-QOI release UQ remains missing, and no source/property
release rows exist.

Inferred: the current five-family candidate cannot freeze. The reduced
four-family subset is plausible as a future predeclared candidate, but it
cannot be used as a shortcut to freeze the current candidate after observing
the missing junction evidence.

Next useful action: if an admitted H2 model is still needed, choose one branch:
recover Salt1 junction for the five-family candidate, or predeclare PASSIVE-H2-R4
as a new no-score candidate, then perform strict source-envelope and release-UQ
gates before any freeze.
"""
    JOURNAL.write_text(journal, encoding="utf-8")


def write_import_manifest() -> None:
    package_files = [rel(path) for path in sorted(OUT.rglob("*")) if path.is_file()]
    changed = sorted(
        dict.fromkeys(
            [
                ".agent/BOARD.md",
                rel(STATUS),
                rel(JOURNAL),
                rel(IMPORT),
                "tools/analyze/build_passive_h2_predictive_finish_readiness_closure.py",
                "tools/analyze/test_passive_h2_predictive_finish_readiness_closure.py",
                ".agent/STATE.md",
                ".agent/catalog.json",
                ".agent/catalog.csv",
                ".agent/BLOCKERS.md",
                *package_files,
            ]
        )
    )
    json_dump(
        IMPORT,
        {
            "task": TASK_ID,
            "task_id": TASK_ID,
            "generated_at": iso_timestamp(),
            "changed_files": changed,
            "changed_paths": changed,
            "read_only_context": [row["path"] for row in source_manifest_rows()],
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "no_scorecard_outputs": True,
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
                "coefficient_admission": False,
                "candidate_freeze": False,
                "protected_or_final_scoring": False,
            },
        },
    )


def write_outputs() -> dict[str, Any]:
    ensure_dir(OUT)
    manifest = source_manifest_rows()
    coverage = salt1_coverage_rows()
    readiness = readiness_rows()
    gaps = source_gap_rows()
    reduced = reduced_policy_rows()
    runbook = runbook_rows()
    guardrails = guardrail_rows()

    csv_dump(OUT / "source_manifest.csv", ["role", "path", "mode", "exists"], manifest)
    csv_dump(OUT / "salt1_family_coverage_gap.csv", list(coverage[0]), coverage)
    csv_dump(OUT / "predictive_finish_readiness_matrix.csv", list(readiness[0]), readiness)
    csv_dump(OUT / "source_envelope_uq_gap_ledger.csv", list(gaps[0]), gaps)
    csv_dump(OUT / "reduced_family_freeze_policy.csv", list(reduced[0]), reduced)
    csv_dump(OUT / "smallest_unblock_runbook.csv", list(runbook[0]), runbook)
    csv_dump(OUT / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_predictive_finish_fail_closed_current_candidate_no_freeze_reduced_path_requires_new_predeclared_candidate",
        "candidate_id": "PASSIVE-H2-CAND001",
        "full_five_family_freeze_allowed": False,
        "reduced_four_family_freeze_as_current_candidate_allowed": False,
        "reduced_four_family_future_candidate_allowed": True,
        "salt1_setup_rows_present": sum(1 for row in coverage if row["operator_row_present"] == "true"),
        "salt1_required_family_rows": len(coverage),
        "salt1_missing_family_rows": sum(1 for row in coverage if row["operator_row_present"] == "false"),
        "strict_source_envelope_ready_rows": sum(1 for row in gaps if row["strict_source_envelope_status"] == "admitted"),
        "same_qoi_release_uq_ready_rows": sum(1 for row in gaps if row["same_qoi_release_uq_status"] == "release_ready"),
        "source_property_release_rows": 0,
        "freeze_allowed_rows": sum(1 for row in readiness if row["predictive_freeze_allowed_now"] == "true"),
        "final_score_values": 0,
        "protected_or_final_scoring": False,
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    write_closeout(summary)
    write_import_manifest()
    return summary


def main() -> int:
    print(json.dumps(write_outputs(), indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
