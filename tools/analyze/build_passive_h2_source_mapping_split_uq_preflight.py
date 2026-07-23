#!/usr/bin/env python3
"""Build PASSIVE-H2 source mapping, split, and UQ preflight artifacts."""

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

TASK_ID = "TODO-PASSIVE-H2-SOURCE-MAPPING-SPLIT-UQ-PREFLIGHT-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_mapping_split_uq_preflight"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-source-mapping-split-uq-preflight.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_source_mapping_split_uq_preflight.json"

RUNTIME = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
UQ_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate"
SOURCE_BASIS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"
SPLIT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_extbc_split_conflict_resolution"
CANDIDATE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
NOMINAL_RELEASE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"
P1D = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_p1d_bulk_cv_h2_train_only_thesis_prototype"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bool_text(value: bool) -> str:
    return str(value).lower()


def mapping_rows() -> list[dict[str, str]]:
    source_gate = read_csv(SOURCE_BASIS / "passive_h2_source_release_gate.csv")
    split_rows = read_csv(SPLIT / "case_level_extbc_conflict_table.csv")
    basis_release = all(row["release_allowed"] == "True" for row in source_gate)
    rows: list[dict[str, str]] = []
    for row in split_rows:
        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": row["case_id"],
                "split_role": row["external_bc_split_roles"],
                "source_backed_parent_mapping": bool_text(basis_release),
                "source_backed_subspan_mapping": "partial_setup_dictionary_only",
                "split_conflict": bool_text(row["split_label_conflict"] == "True"),
                "release_status": "fail_closed_candidate_specific_mapping_not_released",
                "evidence": rel(SOURCE_BASIS / "passive_h2_source_release_gate.csv"),
                "reason": (
                    "setup dictionary source gates pass, but the candidate still lacks "
                    "row-specific parent/subspan release plus split-safe Salt3/Salt4 use"
                ),
            }
        )
    return rows


def split_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(SPLIT / "case_level_extbc_conflict_table.csv"):
        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": row["case_id"],
                "split_role": row["external_bc_split_roles"],
                "split_conflict": row["split_label_conflict"].lower(),
                "candidate_use_now": row["allowed_in_future_candidate_preflight"],
                "protected_scoring_allowed": row["protected_scoring_allowed"],
                "numeric_q_loss_release": row["numeric_q_loss_release"],
                "disposition": "train_context_only" if row["case_id"] == "salt_2" else "diagnostic_only_no_protected_scoring",
                "reason": row["source_provenance_decision"],
            }
        )
    return rows


def same_qoi_uq_rows() -> list[dict[str, str]]:
    summary = read_json(UQ_GATE / "summary.json")
    rows = [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "qoi_or_prerequisite": "setup_operator_sensitivity",
            "status": "diagnostic_ready_train_context",
            "count": str(summary["operator_smoke_rows"]),
            "release_effect": "support_only_no_release",
            "evidence": rel(UQ_GATE / "summary.json"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "qoi_or_prerequisite": "same_qoi_train_report_contract",
            "status": "blocked_no_source_property_release",
            "count": "0",
            "release_effect": "blocks_candidate_freeze",
            "evidence": rel(RUNTIME / "same_qoi_train_report_contract.csv"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "qoi_or_prerequisite": "Salt3_validation_split",
            "status": "blocked_split_conflict",
            "count": "0",
            "release_effect": "no_protected_scoring",
            "evidence": rel(SPLIT / "case_level_extbc_conflict_table.csv"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "qoi_or_prerequisite": "Salt4_holdout_split",
            "status": "blocked_split_conflict",
            "count": "0",
            "release_effect": "no_protected_scoring",
            "evidence": rel(SPLIT / "case_level_extbc_conflict_table.csv"),
        },
    ]
    return rows


def release_rows() -> list[dict[str, str]]:
    candidate_rows = read_csv(CANDIDATE_GATE / "candidate_gate_matrix.csv")
    passive = next(row for row in candidate_rows if row["candidate_id"] == "PASSIVE-H2-CAND001")
    runtime_summary = read_json(RUNTIME / "summary.json")
    candidate_summary = read_json(CANDIDATE_GATE / "summary.json")
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "runtime_smoke",
            "status": passive["runtime_legality"],
            "ready_now": "true",
            "count_or_value": str(runtime_summary["runtime_smoke_rows"]),
            "release_effect": "support_only",
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "row_specific_source_property_release",
            "status": passive["row_specific_source_property_release"],
            "ready_now": "false",
            "count_or_value": str(candidate_summary["source_property_release_ready_rows"]),
            "release_effect": "blocks_release_and_freeze",
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "same_qoi_uq",
            "status": passive["uq_residual_prerequisites"],
            "ready_now": "false",
            "count_or_value": "0",
            "release_effect": "blocks_admission",
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "gate": "candidate_freeze",
            "status": passive["fit_or_admission_readiness"],
            "ready_now": "false",
            "count_or_value": str(candidate_summary["freeze_ready_candidates"]),
            "release_effect": "no_final_score",
        },
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "action": "define candidate-specific role-to-parent/subspan mapping",
            "why": "setup dictionary gates pass, but release-grade candidate mapping is not pinned to row-level parent/subspan labels",
            "allowed": "source-ledger preflight only",
            "forbidden": "numeric q-loss release or protected score",
        },
        {
            "priority": "2",
            "action": "resolve Salt3/Salt4 split use as diagnostic-only or exclude from release",
            "why": "external-BC split conflicts make Salt3/Salt4 unusable for candidate freeze in this row",
            "allowed": "split ledger update under a new row",
            "forbidden": "validation/holdout scoring",
        },
        {
            "priority": "3",
            "action": "build same-QOI train-only report contract for Salt2",
            "why": "operator smoke is positive, but same-QOI UQ is not release-ready",
            "allowed": "setup-only UQ preflight",
            "forbidden": "admission/freeze",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_output_mutation", "status": "false", "note": "no native CFD/OpenFOAM outputs touched"},
        {"guardrail": "scheduler_action", "status": "false", "note": "no scheduler query or mutation"},
        {"guardrail": "Fluid_or_external_edit", "status": "false", "note": "no Fluid/external repo edit"},
        {"guardrail": "source_property_release", "status": "false", "note": "candidate-specific release remains fail-closed"},
        {"guardrail": "protected_scoring", "status": "false", "note": "Salt3/Salt4 remain diagnostic-only"},
        {"guardrail": "candidate_freeze", "status": "false", "note": "no candidate freeze or final score"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"role": "runtime_smoke", "path": rel(RUNTIME / "summary.json"), "mode": "read_only"},
        {"role": "runtime_operator_uq", "path": rel(UQ_GATE / "summary.json"), "mode": "read_only"},
        {"role": "source_backed_basis", "path": rel(SOURCE_BASIS / "passive_h2_source_release_gate.csv"), "mode": "read_only"},
        {"role": "split_conflict", "path": rel(SPLIT / "case_level_extbc_conflict_table.csv"), "mode": "read_only"},
        {"role": "candidate_gate", "path": rel(CANDIDATE_GATE / "candidate_gate_matrix.csv"), "mode": "read_only"},
        {"role": "nominal_train_release", "path": rel(NOMINAL_RELEASE / "summary.json"), "mode": "read_only"},
        {"role": "p1d_context", "path": rel(P1D / "summary.json"), "mode": "read_only"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_source_mapping_split_uq_preflight.py
  task_id: {TASK_ID}
tags: [PASSIVE-H2, source-mapping, split, same-QOI-UQ, no-admission]
related:
  - {rel(RUNTIME / "README.md")}
  - {rel(CANDIDATE_GATE / "README.md")}
---
# PASSIVE-H2 Source Mapping Split UQ Preflight

Decision: `{summary["decision"]}`.

This package records that PASSIVE-H2 is still the leading local candidate, but
it is not release-ready. The setup source dictionary and Salt2 train runtime
smoke are useful support evidence. Candidate-specific release remains closed
because parent/subspan mapping is not row-released, Salt3/Salt4 have split
conflicts, and same-QOI UQ is not ready.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_source_mapping_split_uq_preflight.py
  task_id: {TASK_ID}
tags: [status, PASSIVE-H2, source-mapping, split, same-QOI-UQ]
related:
  - {rel(OUT / "summary.json")}
---
# {TASK_ID}

## Objective

Determine whether existing PASSIVE-H2 evidence supports source-backed
role-to-parent/subspan mapping, Salt3/Salt4 split disposition, and same-QOI
setup-only UQ prerequisites.

## Changes Made

Built `{rel(OUT)}` with mapping, split, same-QOI UQ, release/admission,
next-action, guardrail, source-manifest, README, and summary artifacts. Added
task-owned builder/test files plus this status, journal, and import manifest.

## Validation

Validation commands: builder run, unit tests, py_compile, JSON parse,
`finish_task.py`, and scoped `git diff --check`.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
current/LaTeX edit, validation/holdout/external scoring, fitting/model
selection, source/property/Qwall/numeric q-loss release, coefficient admission,
candidate freeze, final-score claim, or runtime-leakage relaxation.
"""
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
provenance:
  generated_by: tools/analyze/build_passive_h2_source_mapping_split_uq_preflight.py
  task_id: {TASK_ID}
tags: [journal, PASSIVE-H2, source-mapping, split, same-QOI-UQ]
related:
  - {rel(OUT / "source_mapping_matrix.csv")}
  - {rel(OUT / "release_admission_readiness.csv")}
---
# PASSIVE-H2 Source Mapping Split UQ Preflight

## Attempted

Read the PASSIVE-H2 runtime smoke, runtime-operator UQ gate, source-backed
basis table, external-BC split conflict package, candidate-specific
source/property gate, nominal-train release preflight, and P1D context.

## Observed

The setup source dictionary has positive support rows and the Salt2 train
runtime smoke is nonzero. The candidate-specific gate still reports zero
source/property release-ready rows and zero freeze-ready candidates. Salt3 and
Salt4 are split-conflict diagnostic rows, not protected scoring rows.

## Inferred

PASSIVE-H2 remains the best next candidate lane, but this row must fail closed:
the repo has support evidence, not a row-specific release. The next useful
work is candidate-specific parent/subspan mapping and same-QOI train-only UQ,
with Salt3/Salt4 kept out of release.

## Next Useful Actions

Claim a narrow parent/subspan mapping release preflight, then a Salt2 same-QOI
UQ preflight. Do not use Salt3/Salt4 for protected scoring or final freeze.
"""
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_source_mapping_split_uq_preflight.py",
        "tools/analyze/test_passive_h2_source_mapping_split_uq_preflight.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/source_mapping_matrix.csv",
        f"{rel(OUT)}/split_disposition_matrix.csv",
        f"{rel(OUT)}/same_qoi_uq_preflight.csv",
        f"{rel(OUT)}/release_admission_readiness.csv",
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
            "source_mapping_release_ready_rows": summary["source_mapping_release_ready_rows"],
            "split_conflict_rows": summary["split_conflict_rows"],
            "same_qoi_release_ready_rows": summary["same_qoi_release_ready_rows"],
        },
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "no_scorecard_outputs": True,
    }
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    json_dump(IMPORT, manifest)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    maps = mapping_rows()
    splits = split_rows()
    uq = same_qoi_uq_rows()
    release = release_rows()
    next_actions = next_action_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_source_mapping_split_uq_preflight_fail_closed_no_release_no_freeze",
        "candidate_id": "PASSIVE-H2-CAND001",
        "mapping_rows": len(maps),
        "source_mapping_support_rows": sum(1 for row in maps if row["source_backed_parent_mapping"] == "true"),
        "source_mapping_release_ready_rows": sum(1 for row in maps if row["release_status"] == "release_ready"),
        "split_rows": len(splits),
        "split_conflict_rows": sum(1 for row in splits if row["split_conflict"] == "true"),
        "same_qoi_rows": len(uq),
        "same_qoi_release_ready_rows": sum(1 for row in uq if row["release_effect"] == "release_ready"),
        "release_ready_rows": sum(1 for row in release if row["ready_now"] == "true" and row["release_effect"] != "support_only"),
        "candidate_freeze": False,
        "protected_scoring": False,
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "final_score_claim": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
    }

    csv_dump(out / "source_mapping_matrix.csv", list(maps[0]), maps)
    csv_dump(out / "split_disposition_matrix.csv", list(splits[0]), splits)
    csv_dump(out / "same_qoi_uq_preflight.csv", list(uq[0]), uq)
    csv_dump(out / "release_admission_readiness.csv", list(release[0]), release)
    csv_dump(out / "next_action_queue.csv", list(next_actions[0]), next_actions)
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
