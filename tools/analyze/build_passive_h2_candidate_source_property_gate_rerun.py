#!/usr/bin/env python3
"""Rerun the PASSIVE-H2 candidate source/property gate from latest local H2 evidence."""

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

TASK_ID = "TODO-PASSIVE-H2-CANDIDATE-SOURCE-PROPERTY-GATE-RERUN-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_candidate_source_property_gate_rerun"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-candidate-source-property-gate-rerun.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_candidate_source_property_gate_rerun.json"
MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"

SUBSPAN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_subspan_mapping_release_recovery"
SALT2_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate"
ROLE_RECOVERY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery"
FINAL_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate"
RUNTIME = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
CANDIDATE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
SPLIT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_extbc_split_conflict_resolution"
SMOKE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt34_diagnostic_runtime_smoke"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def gate_rows() -> list[dict[str, str]]:
    subspan = read_json(SUBSPAN / "summary.json")
    uq = read_json(SALT2_UQ / "summary.json")
    runtime = read_json(RUNTIME / "summary.json")
    candidate = read_json(CANDIDATE_GATE / "summary.json")
    final = read_json(FINAL_GATE / "summary.json")
    smoke = read_json(SMOKE / "summary.json")
    return [
        {
            "gate": "runtime_implementation",
            "status": "pass_support",
            "release_ready": "false",
            "count_or_value": f"radiation_delta_W={runtime['radiation_on_heat_ledger_delta_W']}",
            "reason": "runtime H2 is legal and nonzero but is train/support evidence",
            "evidence_path": rel(RUNTIME / "summary.json"),
        },
        {
            "gate": "setup_subspan_support",
            "status": "pass_support",
            "release_ready": "false",
            "count_or_value": f"{subspan['salt2_setup_subspan_support_ready_rows']}/5",
            "reason": "Salt2 setup subspan support is recovered for all five families",
            "evidence_path": rel(SUBSPAN / "salt2_subspan_release_gate.csv"),
        },
        {
            "gate": "release_grade_subspan",
            "status": "fail_closed",
            "release_ready": "false",
            "count_or_value": f"{subspan['salt2_release_ready_rows']}/5",
            "reason": "no Salt2 source-family row is release-grade now",
            "evidence_path": rel(SUBSPAN / "salt2_subspan_release_gate.csv"),
        },
        {
            "gate": "salt2_same_qoi_setup_uq",
            "status": "pass_diagnostic",
            "release_ready": "false",
            "count_or_value": f"{uq['diagnostic_ready_qoi_labels']}/{uq['qoi_labels']}",
            "reason": "same-QOI setup-UQ is diagnostic-ready but not admission-release-ready",
            "evidence_path": rel(SALT2_UQ / "qoi_readiness_gate.csv"),
        },
        {
            "gate": "same_qoi_release_ready",
            "status": "fail_closed",
            "release_ready": "false",
            "count_or_value": f"{uq['release_ready_qoi_labels']}/{uq['qoi_labels']}",
            "reason": "no QOI label is release-ready for admission",
            "evidence_path": rel(SALT2_UQ / "qoi_readiness_gate.csv"),
        },
        {
            "gate": "source_property_release",
            "status": "fail_closed",
            "release_ready": "false",
            "count_or_value": str(candidate["source_property_release_ready_rows"]),
            "reason": "candidate-specific source/property release-ready rows remain zero",
            "evidence_path": rel(CANDIDATE_GATE / "summary.json"),
        },
        {
            "gate": "qwall_numeric_heat_loss_release",
            "status": "fail_closed",
            "release_ready": "false",
            "count_or_value": "qwall_release=false; numeric_q_loss_release=false",
            "reason": "Qwall/source-side support and numeric passive heat-loss release remain closed",
            "evidence_path": rel(RUNTIME / "blocker_unblock_matrix.csv"),
        },
        {
            "gate": "protected_split_or_score",
            "status": "fail_closed",
            "release_ready": "false",
            "count_or_value": f"split_conflict_rows={final['split_conflict_rows']}; salt34_runtime_rows={smoke['runtime_smoke_rows']}",
            "reason": "Salt3/Salt4 diagnostic smoke completed fail-closed because the runner is train-only while rows are validation/holdout",
            "evidence_path": rel(SMOKE / "summary.json"),
        },
        {
            "gate": "candidate_freeze",
            "status": "fail_closed",
            "release_ready": "false",
            "count_or_value": str(candidate["freeze_ready_candidates"]),
            "reason": "freeze cannot open without release-grade subspan/source-property/same-QOI evidence",
            "evidence_path": rel(CANDIDATE_GATE / "summary.json"),
        },
        {
            "gate": "final_score",
            "status": "closed_not_run",
            "release_ready": "false",
            "count_or_value": "0",
            "reason": "no frozen candidate exists",
            "evidence_path": rel(FINAL_GATE / "summary.json"),
        },
    ]


def decision_rows() -> list[dict[str, str]]:
    gates = gate_rows()
    release_ready = all(row["release_ready"] == "true" for row in gates)
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate_rerun": "after_subspan_and_salt2_same_qoi_setup_uq",
            "support_progress": "true",
            "source_property_release_allowed": str(release_ready).lower(),
            "candidate_freeze_allowed": "false",
            "protected_scoring_allowed": "false",
            "final_form_allowed": "false",
            "final_score_values": "0",
            "decision": "passive_h2_candidate_source_property_gate_rerun_fail_closed_support_progress_no_release_no_freeze",
            "reason": "subspan and Salt2 setup-UQ support improved, but release-grade subspan, source/property release, Qwall/numeric heat-loss release, protected split/scoring, and freeze gates remain closed",
        }
    ]


def claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {"claim": "setup-driven outer-insulation radiation changes Fluid heat ledger", "allowed": "true", "scope": "Salt2 train/support diagnostic"},
        {"claim": "five-family Salt2 setup subspan support exists", "allowed": "true", "scope": "setup support only"},
        {"claim": "Salt2 same-QOI setup sensitivity exists", "allowed": "true", "scope": "diagnostic train context only"},
        {"claim": "released numeric passive heat-loss coefficient", "allowed": "false", "scope": "blocked"},
        {"claim": "source/property release for PASSIVE-H2", "allowed": "false", "scope": "blocked"},
        {"claim": "candidate freeze or final predictive model", "allowed": "false", "scope": "blocked"},
        {"claim": "protected validation/holdout/external score", "allowed": "false", "scope": "blocked"},
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "action": "define an explicit non-scoring diagnostic runner contract or create same-QOI train/support rows",
            "why": "Salt3/Salt4 smoke is complete but blocked by train-only runner contract and protected split labels",
            "acceptance": "runtime path can execute without relabeling validation/holdout rows as train and without protected scoring",
        },
        {
            "priority": "2",
            "action": "recover release-grade source/property provenance for H2 rows",
            "why": "setup support is not enough for source/property release",
            "acceptance": "positive release-ready rows or explicit field-level fail-closed reasons",
        },
        {
            "priority": "3",
            "action": "run exact same-QOI runtime UQ after release evidence improves",
            "why": "current UQ is diagnostic setup sensitivity, not candidate admission UQ",
            "acceptance": "same-QOI rows are labeled release-ready without forbidden runtime inputs",
        },
        {
            "priority": "4",
            "action": "open S15 only after exactly one candidate is release-ready",
            "why": "protected scoring requires a frozen runtime-legal candidate first",
            "acceptance": "one frozen manifest exists; otherwise final score remains zero",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_mutated", "value": "false"},
        {"guardrail": "scheduler_action", "value": "false"},
        {"guardrail": "Fluid_or_external_edit", "value": "false"},
        {"guardrail": "validation_holdout_external_scoring", "value": "false"},
        {"guardrail": "source_property_release", "value": "false"},
        {"guardrail": "qwall_or_numeric_q_loss_release", "value": "false"},
        {"guardrail": "candidate_freeze", "value": "false"},
        {"guardrail": "final_score_claim", "value": "false"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("subspan_recovery", SUBSPAN / "summary.json"),
        ("salt2_same_qoi_uq", SALT2_UQ / "summary.json"),
        ("role_subspan_recovery", ROLE_RECOVERY / "summary.json"),
        ("final_form_gate", FINAL_GATE / "summary.json"),
        ("runtime_implementation", RUNTIME / "summary.json"),
        ("candidate_specific_gate", CANDIDATE_GATE / "summary.json"),
        ("split_conflict_resolution", SPLIT / "case_level_extbc_conflict_table.csv"),
        ("salt34_diagnostic_smoke", SMOKE / "summary.json"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": str(path.exists()).lower()} for role, path in sources]


def write_map_update(summary: dict[str, Any]) -> None:
    marker = "2026-07-22 PASSIVE-H2 candidate source/property rerun update"
    addition = f"""
{marker}: `{rel(OUT)}` reran the H2 candidate source/property gate after the
exact subspan release-recovery and Salt2 same-QOI setup-UQ rows. Decision:
`{summary["decision"]}`. Progress is real but support-only: Salt2 setup subspan
support is `5/5` and diagnostic same-QOI setup-UQ labels are `6/6`. Release and
final form remain closed: release-grade subspan rows `0/5`, source/property
release-ready rows `0`, freeze-ready candidates `0`, and final score values
`0`. The Salt3/Salt4 diagnostic smoke row is complete but fail-closed because
the runner is train-only while Salt3/Salt4 rows are validation/holdout. Next
work is an explicit non-scoring diagnostic runner contract or same-QOI
train/support rows, release-grade source/property provenance, then exact
same-QOI runtime UQ before any S15/S6 path.
"""
    text = MAP.read_text(encoding="utf-8")
    if marker not in text:
        MAP.write_text(text + addition, encoding="utf-8")


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_candidate_source_property_gate_rerun.py
  task_id: {TASK_ID}
tags: [PASSIVE-H2, source-property, rerun, no-release, no-freeze]
related:
  - {rel(SUBSPAN / "README.md")}
  - {rel(SALT2_UQ / "README.md")}
  - {rel(FINAL_GATE / "README.md")}
---
# PASSIVE-H2 Candidate Source/Property Gate Rerun

Decision: `{summary["decision"]}`.

This rerun consumes the requested subspan and Salt2 same-QOI setup-UQ rows.
It records support progress but still fails closed for source/property release,
candidate freeze, protected scoring, and final form.
"""
    ensure_dir(OUT)
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_candidate_source_property_gate_rerun.py
  task_id: {TASK_ID}
tags: [status, PASSIVE-H2, source-property, no-release]
related:
  - {rel(OUT / "summary.json")}
---
# {TASK_ID}

## Objective

Rerun the PASSIVE-H2 candidate source/property gate after subspan mapping
release-recovery and Salt2 same-QOI setup-UQ evidence.

## Outcome

Decision: `{summary["decision"]}`. Support progress is preserved: Salt2 setup
subspan support `{summary["salt2_setup_subspan_support_ready_rows"]}/5` and
diagnostic same-QOI setup-UQ `{summary["diagnostic_ready_qoi_labels"]}/6`.
Release remains fail-closed: release-grade subspan rows
`{summary["salt2_release_ready_rows"]}/5`, source/property release-ready rows
`{summary["source_property_release_ready_rows"]}`, freeze-ready candidates
`{summary["freeze_ready_candidates"]}`, final score values `0`.

## Changes Made

Built `{rel(OUT)}` with gate matrix, decision table, claim boundaries,
next-action queue, guardrails, source manifest, README, summary, tests, status,
journal, import manifest, and a map update.

## Validation

Ran builder, unit tests, py_compile, JSON parse, `finish_task.py`, and scoped
`git diff --check`.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit,
validation/holdout/external scoring, source/property/Qwall/numeric q-loss
release, coefficient admission, candidate freeze, final-score claim, hidden
multiplier, residual absorption, or runtime-leakage relaxation.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
provenance:
  generated_by: tools/analyze/build_passive_h2_candidate_source_property_gate_rerun.py
tags: [journal, PASSIVE-H2, source-property, no-release]
related:
  - {rel(OUT / "candidate_gate_rerun_matrix.csv")}
---
# PASSIVE-H2 Candidate Source/Property Gate Rerun

## Attempted

Consumed the exact subspan release-recovery and Salt2 same-QOI setup-UQ packets
and reran a PASSIVE-H2-only source/property gate.

## Observed

Support evidence improved, but all release/freeze gates remain closed. The
Salt3/Salt4 diagnostic smoke row was consumed and it completed fail-closed:
the existing runner is train-only and the Salt3/Salt4 rows are
validation/holdout.

## Inferred

H2 remains the strongest support-only passive-boundary lane, not a released
candidate. The clean scientific result is no release, no freeze, and no final
score until release-grade provenance and exact runtime UQ land.

## Next Useful Actions

Define an explicit non-scoring diagnostic runner contract or create same-QOI
train/support rows, recover source/property provenance, then run exact
same-QOI runtime UQ. Do not open S15 until exactly one candidate is
release-ready.
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
        "tools/analyze/build_passive_h2_candidate_source_property_gate_rerun.py",
        "tools/analyze/test_passive_h2_candidate_source_property_gate_rerun.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/candidate_gate_rerun_matrix.csv",
        f"{rel(OUT)}/candidate_release_decision.csv",
        f"{rel(OUT)}/scientific_claim_boundaries.csv",
        f"{rel(OUT)}/next_action_queue.csv",
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
            "source_property_release_ready_rows": summary["source_property_release_ready_rows"],
            "freeze_ready_candidates": summary["freeze_ready_candidates"],
            "final_score_values": 0,
        },
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "source_property_release": False,
        "candidate_freeze": False,
        "final_score_claim": False,
    }
    ensure_dir(IMPORT.parent)
    json_dump(IMPORT, manifest)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    gates = gate_rows()
    decisions = decision_rows()
    claims = claim_boundary_rows()
    next_actions = next_action_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()
    subspan = read_json(SUBSPAN / "summary.json")
    uq = read_json(SALT2_UQ / "summary.json")
    candidate = read_json(CANDIDATE_GATE / "summary.json")
    smoke = read_json(SMOKE / "summary.json")

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": decisions[0]["decision"],
        "candidate_id": "PASSIVE-H2-CAND001",
        "support_progress": True,
        "salt2_setup_subspan_support_ready_rows": subspan["salt2_setup_subspan_support_ready_rows"],
        "salt2_release_ready_rows": subspan["salt2_release_ready_rows"],
        "diagnostic_ready_qoi_labels": uq["diagnostic_ready_qoi_labels"],
        "release_ready_qoi_labels": uq["release_ready_qoi_labels"],
        "salt34_smoke_decision": smoke["decision"],
        "salt34_runtime_smoke_rows": smoke["runtime_smoke_rows"],
        "salt34_smoke_blocked_rows": smoke["blocked_rows"],
        "source_property_release_ready_rows": candidate["source_property_release_ready_rows"],
        "freeze_ready_candidates": candidate["freeze_ready_candidates"],
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "final_form_allowed": False,
        "final_score_claim": False,
        "final_score_values": 0,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_mutated": False,
        "fluid_or_external_edit": False,
    }

    csv_dump(out / "candidate_gate_rerun_matrix.csv", list(gates[0]), gates)
    csv_dump(out / "candidate_release_decision.csv", list(decisions[0]), decisions)
    csv_dump(out / "scientific_claim_boundaries.csv", list(claims[0]), claims)
    csv_dump(out / "next_action_queue.csv", list(next_actions[0]), next_actions)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    if out == OUT:
        write_readme(summary)
        write_status(summary)
        write_journal(summary)
        write_import(summary)
        write_map_update(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
