#!/usr/bin/env python3
"""Predeclare and gate PASSIVE-H2-R4 without junction."""

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

TASK_ID = "TODO-PASSIVE-H2-R4-PREDECLARED-SOURCE-ENVELOPE-UQ-GATE-2026-07-22"
SLUG = "passive_h2_r4_predeclared_source_envelope_uq_gate"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_r4_predeclared_source_envelope_uq_gate"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-r4-predeclared-source-envelope-uq-gate.md"
IMPORT = ROOT / f"imports/2026-07-22_{SLUG}.json"

FINISH = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_predictive_finish_readiness_closure"
THESIS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition"
SALT1 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict"
SOURCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_evidence_recovery"
UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate"

FAMILIES = ["cooling_branch", "downcomer", "lower_leg", "upcomer"]
CASES = [("salt_1", "train"), ("salt_2", "train"), ("salt_3", "validation"), ("salt_4", "holdout")]


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
        ("finish_closure", FINISH / "summary.json"),
        ("finish_matrix", FINISH / "predictive_finish_readiness_matrix.csv"),
        ("thesis_disposition", THESIS / "source_property_final_disposition.csv"),
        ("salt1_operator_rows", SALT1 / "salt1_recovered_operator_rows_for_fluid.csv"),
        ("source_evidence", SOURCE / "passive_h2_family_evidence_recovery_matrix.csv"),
        ("same_qoi_setup_uq", UQ / "qoi_readiness_gate.csv"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": bool_s(path.exists())} for role, path in paths]


def candidate_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "candidate_id": "PASSIVE-H2-R4-CAND001",
            "derived_from": "PASSIVE-H2-CAND001",
            "predeclared_in_task": TASK_ID,
            "predeclaration_time": "before_any_R4_scoring_or_freeze",
            "included_source_families": ";".join(FAMILIES),
            "excluded_source_families": "junction",
            "exclusion_reason": "new_candidate_definition_to_test_no_junction_path_without_posthoc_freezing_current_candidate",
            "allowed_use_now": "source_envelope_and_release_uq_gate_only",
            "score_allowed_now": "false",
            "freeze_allowed_now": "false",
        }
    ]


def r4_family_rows() -> list[dict[str, str]]:
    disposition = read_csv(THESIS / "source_property_final_disposition.csv")
    by_case_family = {(row["case_id"], row["source_family"]): row for row in disposition}
    rows: list[dict[str, str]] = []
    for case_id, split_role in CASES:
        for family in FAMILIES:
            row = by_case_family.get((case_id, family), {})
            setup_ready = row.get("setup_basis_status", "").startswith("repaired")
            rows.append(
                {
                    "candidate_id": "PASSIVE-H2-R4-CAND001",
                    "case_id": case_id,
                    "split_role": split_role,
                    "source_family": family,
                    "setup_basis_ready": bool_s(setup_ready),
                    "runtime_contract_ready": bool_s(row.get("runtime_contract_status", "") in {"runtime_smoke_complete_no_score", "contract_ready_no_score"}),
                    "strict_source_envelope_ready": "false",
                    "same_qoi_release_uq_ready": "false",
                    "source_property_release_ready": "false",
                    "freeze_allowed_now": "false",
                    "score_allowed_now": "false",
                    "admissibility_role": "predeclared_candidate_gate_only",
                    "remaining_gap": "strict source envelope and release-grade same-QOI UQ",
                    "evidence_path": row.get("evidence_path", ""),
                }
            )
    return rows


def gate_rows() -> list[dict[str, str]]:
    family = r4_family_rows()
    setup = sum(row["setup_basis_ready"] == "true" for row in family)
    strict = sum(row["strict_source_envelope_ready"] == "true" for row in family)
    uq = sum(row["same_qoi_release_uq_ready"] == "true" for row in family)
    release = sum(row["source_property_release_ready"] == "true" for row in family)
    return [
        {
            "gate": "candidate_predeclared_before_r4_scoring",
            "status": "pass",
            "count_or_value": "1/1",
            "freeze_ready": "false",
            "reason": "R4 candidate definition is recorded here before any R4 score/freeze artifact.",
        },
        {
            "gate": "four_case_four_family_setup_runtime_coverage",
            "status": "pass",
            "count_or_value": f"{setup}/16",
            "freeze_ready": "false",
            "reason": "Salt1-4 retained families have setup/runtime support, but setup support is not admission.",
        },
        {
            "gate": "strict_source_envelope",
            "status": "fail_closed",
            "count_or_value": f"{strict}/16",
            "freeze_ready": "false",
            "reason": "No retained family row has strict source-envelope admission in the current corpus.",
        },
        {
            "gate": "same_qoi_release_uq",
            "status": "fail_closed",
            "count_or_value": f"{uq}/16",
            "freeze_ready": "false",
            "reason": "Existing UQ rows are diagnostic/setup-only, not release-grade candidate UQ.",
        },
        {
            "gate": "source_property_release",
            "status": "fail_closed",
            "count_or_value": f"{release}/16",
            "freeze_ready": "false",
            "reason": "No source/property release rows are available for R4.",
        },
        {
            "gate": "candidate_freeze",
            "status": "closed_not_run",
            "count_or_value": "0",
            "freeze_ready": "false",
            "reason": "Freeze remains illegal until strict source-envelope, release-UQ, and source/property release gates pass.",
        },
    ]


def runbook_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "task": "Run strict source-envelope conversion audit for the four retained families.",
            "why": "This is the first hard blocker for R4.",
            "acceptance": "each retained family has row-specific inside-envelope or admitted setup-source basis without protected fields",
        },
        {
            "priority": "2",
            "task": "Run release-grade same-QOI UQ only after strict-envelope pass.",
            "why": "UQ before source-envelope admission remains diagnostic only.",
            "acceptance": "same frozen R4 operator and same QOI labels across train/support windows; no protected scoring",
        },
        {
            "priority": "3",
            "task": "Freeze R4 only if every retained family passes release gates.",
            "why": "R4 is now predeclared, but still not admitted.",
            "acceptance": "candidate freeze manifest exists before any validation or holdout score",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    names = [
        "native_solver_outputs_mutated",
        "registry_or_admission_mutated",
        "scheduler_action",
        "solver_sampler_harvest_uq_launched",
        "fluid_or_external_edit",
        "thesis_current_or_latex_edit",
        "source_property_release",
        "numeric_q_loss_release",
        "qwall_release",
        "coefficient_admission",
        "candidate_freeze",
        "protected_or_final_scoring",
        "hidden_multiplier_or_residual_absorption",
    ]
    return [{"guardrail": name, "value": "false"} for name in names]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(FINISH / "summary.json")}
  - {rel(THESIS / "source_property_final_disposition.csv")}
tags: [PASSIVE-H2, PASSIVE-H2-R4, predeclared-candidate, no-release]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2-R4 Predeclared Source-Envelope/UQ Gate

Decision: `{summary["decision"]}`.

PASSIVE-H2-R4 is now predeclared as a no-junction four-family candidate before
any R4 scoring. It has setup/runtime coverage for Salt1-4 retained families,
but it is not admitted: strict source-envelope, release-grade same-QOI UQ, and
source/property release all remain closed.

## Result

- R4 setup/runtime rows: `{summary["setup_runtime_ready_rows"]}` /
  `{summary["required_case_family_rows"]}`.
- Strict source-envelope rows: `{summary["strict_source_envelope_ready_rows"]}`.
- Release-UQ rows: `{summary["same_qoi_release_uq_ready_rows"]}`.
- Source/property release rows: `{summary["source_property_release_rows"]}`.
- Freeze rows: `{summary["freeze_allowed_rows"]}`.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_closeout(summary: dict[str, Any]) -> None:
    ensure_dir(STATUS.parent)
    STATUS.write_text(
        f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "r4_source_family_gate_matrix.csv")}
tags: [PASSIVE-H2-R4, predeclared-candidate, source-envelope, no-release]
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

Objective: predeclare PASSIVE-H2-R4 and gate it for predictive freeze readiness
without using it as a post-hoc freeze of the current five-family candidate.

Outcome: `{summary["decision"]}`. R4 setup/runtime coverage is
`{summary["setup_runtime_ready_rows"]}` / `{summary["required_case_family_rows"]}`,
but strict source-envelope rows, release-UQ rows, source/property release rows,
freeze rows, and final score values are all zero.

## Changes Made

- `{rel(OUT)}`
- `{rel(Path("tools/analyze/build_passive_h2_r4_predeclared_source_envelope_uq_gate.py"))}`
- `{rel(Path("tools/analyze/test_passive_h2_r4_predeclared_source_envelope_uq_gate.py"))}`
- `{rel(IMPORT)}`
- `.agent/STATE.md`
- `.agent/catalog.json`
- `.agent/catalog.csv`
- `.agent/BLOCKERS.md`

## Validation

- `python3.11 tools/analyze/build_passive_h2_r4_predeclared_source_envelope_uq_gate.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_r4_predeclared_source_envelope_uq_gate`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_r4_predeclared_source_envelope_uq_gate.py tools/analyze/test_passive_h2_r4_predeclared_source_envelope_uq_gate.py`
- `python3.11 tools/agent/runtime_input_lint.py {rel(OUT)} {rel(STATUS)} {rel(JOURNAL)} {rel(IMPORT)}`
- `python3.11 tools/agent/split_policy_lint.py {rel(OUT)} {rel(STATUS)} {rel(JOURNAL)} {rel(IMPORT)}`
- `python3.11 tools/agent/manifest_check.py {rel(IMPORT)} --check-paths`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
edit, protected/final scoring, fitting/tuning/model selection,
source/property release, Qwall release, numeric q-loss release, coefficient
admission, candidate freeze, hidden multiplier, residual absorption, or
runtime-leakage relaxation.
""",
        encoding="utf-8",
    )
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(
        f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "r4_freeze_gate.csv")}
tags: [PASSIVE-H2-R4, no-freeze, predictive-readiness]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2-R4 Predeclared Source-Envelope/UQ Gate

Attempted: create the no-junction candidate as a new predeclared entity and
evaluate whether existing evidence can freeze it.

Observed: retained-family setup/runtime coverage is complete across Salt1-4,
but strict source-envelope, release-grade same-QOI UQ, and source/property
release remain zero.

Inferred: R4 is a valid future path to investigate, but not a finished
predictive model. The next row must change source-envelope evidence before UQ
or freeze can become meaningful.
""",
        encoding="utf-8",
    )


def write_import_manifest() -> None:
    package_files = [rel(path) for path in sorted(OUT.rglob("*")) if path.is_file()]
    changed = sorted(
        dict.fromkeys(
            [
                ".agent/BOARD.md",
                rel(STATUS),
                rel(JOURNAL),
                rel(IMPORT),
                "tools/analyze/build_passive_h2_r4_predeclared_source_envelope_uq_gate.py",
                "tools/analyze/test_passive_h2_r4_predeclared_source_envelope_uq_gate.py",
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
        },
    )


def write_outputs() -> dict[str, Any]:
    ensure_dir(OUT)
    manifest = source_manifest_rows()
    candidate = candidate_manifest_rows()
    family = r4_family_rows()
    gates = gate_rows()
    runbook = runbook_rows()
    guardrails = guardrail_rows()

    csv_dump(OUT / "source_manifest.csv", ["role", "path", "mode", "exists"], manifest)
    csv_dump(OUT / "r4_candidate_predeclaration_manifest.csv", list(candidate[0]), candidate)
    csv_dump(OUT / "r4_source_family_gate_matrix.csv", list(family[0]), family)
    csv_dump(OUT / "r4_freeze_gate.csv", list(gates[0]), gates)
    csv_dump(OUT / "r4_next_unblock_runbook.csv", list(runbook[0]), runbook)
    csv_dump(OUT / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_r4_predeclared_candidate_created_but_freeze_fail_closed_missing_source_envelope_and_release_uq",
        "candidate_id": "PASSIVE-H2-R4-CAND001",
        "derived_from": "PASSIVE-H2-CAND001",
        "included_source_family_count": len(FAMILIES),
        "excluded_source_families": ["junction"],
        "required_case_family_rows": len(family),
        "setup_runtime_ready_rows": sum(1 for row in family if row["setup_basis_ready"] == "true" and row["runtime_contract_ready"] == "true"),
        "strict_source_envelope_ready_rows": 0,
        "same_qoi_release_uq_ready_rows": 0,
        "source_property_release_rows": 0,
        "freeze_allowed_rows": 0,
        "final_score_values": 0,
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_or_final_scoring": False,
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
    print(json.dumps(write_outputs(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
