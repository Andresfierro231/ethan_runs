#!/usr/bin/env python3.11
"""Build the PASSIVE-H2 release-grade subspan evidence gate."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-PASSIVE-H2-ROLE-SUBSPAN-RELEASE-EVIDENCE-2026-07-22"
DATE = "2026-07-22"
SLUG = "passive_h2_role_subspan_release_evidence"
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_release_evidence"
STATUS_PATH = REPO / f".agent/status/{DATE}_{TASK_ID}.md"
JOURNAL_PATH = REPO / f".agent/journal/{DATE}/passive-h2-role-subspan-release-evidence.md"
IMPORT_PATH = REPO / f"imports/{DATE}_{SLUG}.json"

RECOVERY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery"
SOURCE_PREFLIGHT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_mapping_split_uq_preflight"
RUNTIME_IMPL = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
PATCH_ROLE_TABLE = REPO / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def truth(value: str) -> bool:
    return str(value).strip().lower() == "true"


def nonblank(value: str) -> bool:
    return str(value).strip() not in {"", "nan", "None", "none"}


def build_release_rows() -> list[dict[str, object]]:
    family_rows = read_csv(RECOVERY / "family_subspan_recovery_matrix.csv")
    coverage_rows = read_csv(RECOVERY / "source_family_patch_subspan_coverage.csv")
    coverage_by_key = {
        (row["case_id"], row["source_family"]): row
        for row in coverage_rows
    }
    rows: list[dict[str, object]] = []
    for row in family_rows:
        key = (row["case_id"], row["source_family"])
        coverage = coverage_by_key.get(key, {})
        setup_scalars_ready = all(nonblank(row.get(field, "")) for field in ("area_m2", "hA_W_K"))
        ambient_scalars_ready = all(nonblank(row.get(field, "")) for field in ("Ta_K", "Tsur_K", "emissivity"))
        exact_same_qoi_uq_ready = False
        case_row_source_property_ready = False
        release_grade = (
            truth(row["parent_segment_mapping_ready"])
            and truth(row["subspan_mapping_ready"])
            and setup_scalars_ready
            and ambient_scalars_ready
            and exact_same_qoi_uq_ready
            and case_row_source_property_ready
        )
        missing = []
        if not ambient_scalars_ready:
            missing.append("Ta_K/Tsur_K/emissivity")
        if not exact_same_qoi_uq_ready:
            missing.append("exact_same_qoi_uq")
        if not case_row_source_property_ready:
            missing.append("case_row_source_property_release")
        if coverage and coverage.get("area_match_support") != "true":
            missing.append("operator_patch_area_match")
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "source_family": row["source_family"],
                "fluid_parent_segment": row["fluid_parent_segment"],
                "required_patch_or_span_basis": row["required_patch_or_span_basis"],
                "parent_segment_mapping_ready": row["parent_segment_mapping_ready"],
                "setup_subspan_mapping_ready": row["subspan_mapping_ready"],
                "setup_scalars_ready": str(setup_scalars_ready),
                "ambient_scalar_release_ready": str(ambient_scalars_ready),
                "operator_patch_area_match": coverage.get("area_match_support", "unknown"),
                "exact_same_qoi_uq_ready": str(exact_same_qoi_uq_ready),
                "case_row_source_property_release_ready": str(case_row_source_property_ready),
                "release_grade_now": str(release_grade),
                "missing_release_fields": ";".join(missing) if missing else "",
                "decision": "setup_evidence_only_no_release",
                "source_path": rel(RECOVERY / "family_subspan_recovery_matrix.csv"),
            }
        )
    return rows


def write_docs(summary: dict[str, object], changed_files: list[str]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        f"""---
provenance:
  - {rel(OUT_DIR / 'summary.json')}
  - {rel(OUT_DIR / 'release_grade_subspan_evidence_matrix.csv')}
tags: [thermal, passive-h2, source-property, release-gate]
related:
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

## Changes Made

Built a release-grade PASSIVE-H2 subspan evidence gate from the recovered
family/subspan package. The package separates setup support from release
eligibility and keeps every source family evidence-only.

## Validation

Run `python3.11 -m pytest -q tools/analyze/test_passive_h2_role_subspan_release_evidence.py`.
The expected disposition is `0` release-grade rows and `5` evidence-only family
rows.

## Guardrails

Native solver outputs mutated: false. Registry mutated: false. Scheduler
action: false. External Fluid edit: false. No protected scoring, fit, source or
property release, Qwall/numeric q-loss release, coefficient admission,
candidate freeze, final score, hidden multiplier, residual absorption, or
runtime-leakage relaxation was performed.
""",
        encoding="utf-8",
    )
    JOURNAL_PATH.write_text(
        f"""---
provenance:
  - {rel(OUT_DIR / 'summary.json')}
  - {rel(RECOVERY / 'family_subspan_recovery_matrix.csv')}
tags: [thermal, passive-h2, release-evidence]
related:
  - {rel(STATUS_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Role/Subspan Release Evidence

Task: `{TASK_ID}`

Observed: PASSIVE-H2 has useful setup support for five Salt2 source families:
parent segment mapping and setup subspan mapping are present.

Observed: release-grade evidence is still absent. The recovered family table
does not carry complete release-ready ambient/source-property fields, exact
same-QOI UQ remains unavailable, and several area matches are support-only.

Inferred: PASSIVE-H2 is scientifically useful as an evidence path for external
loss modeling, but it is not a source/property release or freeze candidate.

Next useful action: build exact same-QOI setup-UQ rows and recover independent
case-row source/property labels before any candidate-specific release gate is
reopened.
""",
        encoding="utf-8",
    )
    write_json(
        IMPORT_PATH,
        {
            "task": TASK_ID,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "changed_files": changed_files,
            "read_only_context": [
                rel(RECOVERY / "family_subspan_recovery_matrix.csv"),
                rel(RECOVERY / "source_family_patch_subspan_coverage.csv"),
                rel(SOURCE_PREFLIGHT / "summary.json"),
                rel(RUNTIME_IMPL / "summary.json"),
                rel(PATCH_ROLE_TABLE),
            ],
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "no_scorecard_outputs": True,
            "provenance_flags": {
                "source_property_release": False,
                "qwall_release": False,
                "candidate_freeze": False,
                "final_score_claim": False,
            },
        },
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_release_rows()
    blockers = []
    for row in rows:
        blockers.append(
            {
                "case_id": row["case_id"],
                "source_family": row["source_family"],
                "blocking_fields": row["missing_release_fields"],
                "release_grade_now": row["release_grade_now"],
                "next_unlock": "exact_same_qoi_uq_and_case_row_source_property_release",
            }
        )
    runtime_matrix = [
        {"runtime_item": "setup patch/subspan mapping", "legal_runtime_input": "True", "release_ready": "False", "reason": "setup support only"},
        {"runtime_item": "case-row area/hA/Ta/Tsur/emissivity", "legal_runtime_input": "conditional", "release_ready": "False", "reason": "source/property release not established"},
        {"runtime_item": "realized CFD wallHeatFlux/Qwall", "legal_runtime_input": "False", "release_ready": "False", "reason": "diagnostic output, not runtime input"},
        {"runtime_item": "validation/holdout temperatures", "legal_runtime_input": "False", "release_ready": "False", "reason": "protected targets"},
    ]
    guardrails = [
        {"guardrail": "no_source_property_release", "status": "preserved"},
        {"guardrail": "no_numeric_q_loss_release", "status": "preserved"},
        {"guardrail": "no_candidate_freeze", "status": "preserved"},
        {"guardrail": "no_protected_scoring", "status": "preserved"},
    ]
    source_manifest = [
        {"source_path": rel(RECOVERY / "family_subspan_recovery_matrix.csv"), "exists": "True", "mutated": "False", "use": "family release evidence"},
        {"source_path": rel(RECOVERY / "source_family_patch_subspan_coverage.csv"), "exists": "True", "mutated": "False", "use": "patch/subspan support audit"},
        {"source_path": rel(SOURCE_PREFLIGHT / "summary.json"), "exists": str((SOURCE_PREFLIGHT / "summary.json").exists()), "mutated": "False", "use": "split/source-property preflight context"},
        {"source_path": rel(RUNTIME_IMPL / "summary.json"), "exists": str((RUNTIME_IMPL / "summary.json").exists()), "mutated": "False", "use": "runtime implementation context"},
        {"source_path": rel(PATCH_ROLE_TABLE), "exists": str(PATCH_ROLE_TABLE.exists()), "mutated": "False", "use": "setup patch role table provenance"},
    ]
    write_csv(OUT_DIR / "release_grade_subspan_evidence_matrix.csv", rows)
    write_csv(OUT_DIR / "release_blocker_ledger.csv", blockers)
    write_csv(OUT_DIR / "runtime_legality_matrix.csv", runtime_matrix)
    write_csv(OUT_DIR / "source_manifest.csv", source_manifest)
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrails)
    release_ready_rows = [row for row in rows if row["release_grade_now"] == "True"]
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "passive_h2_role_subspan_release_evidence_fail_closed_setup_only",
        "family_rows": len(rows),
        "setup_mapping_ready_rows": len([row for row in rows if row["setup_subspan_mapping_ready"] == "true"]),
        "release_grade_rows": len(release_ready_rows),
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "candidate_freeze": False,
        "final_score_claim": False,
    }
    write_json(OUT_DIR / "summary.json", summary)
    (OUT_DIR / "README.md").write_text(
        f"""---
provenance:
  - {rel(OUT_DIR / 'summary.json')}
  - {rel(OUT_DIR / 'release_grade_subspan_evidence_matrix.csv')}
tags: [thermal, passive-h2, release-gate]
related:
  - {rel(STATUS_PATH)}
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Role/Subspan Release Evidence

Decision: `passive_h2_role_subspan_release_evidence_fail_closed_setup_only`.

The five PASSIVE-H2 Salt2 source families have setup-level parent/subspan
support, but none is release-grade. Missing gates are exact same-QOI UQ,
case-row source/property release, and complete release-ready ambient/source
fields. This package preserves PASSIVE-H2 as evidence-only and does not release
numeric q-loss, Qwall, coefficients, a frozen candidate, or a final score.
""",
        encoding="utf-8",
    )
    changed_files = [
        rel(OUT_DIR / name)
        for name in [
            "README.md",
            "release_grade_subspan_evidence_matrix.csv",
            "release_blocker_ledger.csv",
            "runtime_legality_matrix.csv",
            "source_manifest.csv",
            "no_mutation_guardrails.csv",
            "summary.json",
        ]
    ] + [
        rel(Path("tools/analyze/build_passive_h2_role_subspan_release_evidence.py")),
        rel(Path("tools/analyze/test_passive_h2_role_subspan_release_evidence.py")),
        rel(STATUS_PATH),
        rel(JOURNAL_PATH),
        rel(IMPORT_PATH),
    ]
    write_docs(summary, changed_files)


if __name__ == "__main__":
    main()
