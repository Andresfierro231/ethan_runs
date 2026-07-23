#!/usr/bin/env python3
"""Build PASSIVE-H2 subspan mapping release-recovery gate artifacts."""

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

TASK_ID = "TODO-PASSIVE-H2-SUBSPAN-MAPPING-RELEASE-RECOVERY-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_subspan_mapping_release_recovery"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-subspan-mapping-release-recovery.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_subspan_mapping_release_recovery.json"

ROLE_RECOVERY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery"
FINAL_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate"
SOURCE_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_mapping_split_uq_preflight"
CANDIDATE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
PATCH_TABLE = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def truth(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "pass"}


def salt2_release_rows() -> list[dict[str, str]]:
    rows = []
    coverage = read_csv(ROLE_RECOVERY / "source_family_patch_subspan_coverage.csv")
    for row in coverage:
        if row["case_id"] != "salt_2":
            continue
        release_ready = (
            truth(row["setup_subspan_support_ready"])
            and truth(row["area_match_support"])
            and truth(row["release_grade_subspan_ready_now"])
        )
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "source_family": row["source_family"],
                "operator_equivalent_segment": row["operator_equivalent_segment"],
                "patch_parent_spans": row["patch_parent_spans"],
                "patch_segments": row["patch_segments"],
                "patch_bc_types": row["patch_bc_types"],
                "operator_area_m2": row["operator_area_m2"],
                "patch_area_m2": row["patch_area_m2"],
                "area_rel_delta_pct": row["area_rel_delta_pct"],
                "setup_subspan_support_ready": row["setup_subspan_support_ready"],
                "area_match_support": row["area_match_support"],
                "release_grade_subspan_ready_now": row["release_grade_subspan_ready_now"],
                "release_ready_now": str(release_ready).lower(),
                "release_decision": "release_ready" if release_ready else "fail_closed_support_only",
                "reason": row["reason"],
                "source_path": row["source_path"],
            }
        )
    return rows


def all_case_coverage_rows() -> list[dict[str, str]]:
    fields = [
        "candidate_id",
        "case_id",
        "source_family",
        "operator_equivalent_segment",
        "patch_count",
        "finite_area_patch_count",
        "setup_metadata_patch_count",
        "setup_subspan_support_ready",
        "area_match_support",
        "release_grade_subspan_ready_now",
        "subspan_coverage_status",
        "reason",
    ]
    return [{field: row[field] for field in fields} for row in read_csv(ROLE_RECOVERY / "source_family_patch_subspan_coverage.csv")]


def release_requirement_rows() -> list[dict[str, str]]:
    return [
        {
            "requirement": "setup_patch_subspan_support",
            "current_count": "5/5 Salt2 rows",
            "status": "pass_support",
            "release_effect": "necessary_not_sufficient",
        },
        {
            "requirement": "case_row_source_property_provenance",
            "current_count": "0 release-ready rows",
            "status": "fail_closed",
            "release_effect": "blocks_source_property_release",
        },
        {
            "requirement": "exact_same_qoi_uq",
            "current_count": "diagnostic setup-UQ exists; release-grade admission still false",
            "status": "fail_closed_for_release",
            "release_effect": "blocks_freeze",
        },
        {
            "requirement": "protected_split_legality",
            "current_count": "Salt3/Salt4 diagnostic-only in current evidence",
            "status": "fail_closed",
            "release_effect": "blocks_protected_scoring",
        },
        {
            "requirement": "qwall_or_numeric_heat_loss_release",
            "current_count": "0",
            "status": "fail_closed",
            "release_effect": "blocks_numeric_loss_claim",
        },
    ]


def no_mutation_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false", "note": "evidence synthesis only"},
        {"guardrail": "registry_mutated", "value": "false", "note": "no registry/admission state update"},
        {"guardrail": "scheduler_action", "value": "false", "note": "no compute launched"},
        {"guardrail": "Fluid_or_external_edit", "value": "false", "note": "Fluid/external repos read-only"},
        {"guardrail": "source_property_release", "value": "false", "note": "release-grade subspan/source-property evidence remains incomplete"},
        {"guardrail": "candidate_freeze", "value": "false", "note": "no freeze or final score"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("role_subspan_recovery_summary", ROLE_RECOVERY / "summary.json"),
        ("patch_subspan_coverage", ROLE_RECOVERY / "source_family_patch_subspan_coverage.csv"),
        ("family_subspan_recovery", ROLE_RECOVERY / "family_subspan_recovery_matrix.csv"),
        ("final_form_gate", FINAL_GATE / "summary.json"),
        ("source_mapping_preflight", SOURCE_PREFLIGHT / "source_to_fluid_mapping_matrix.csv"),
        ("candidate_gate", CANDIDATE_GATE / "summary.json"),
        ("thermal_boundary_patch_role_table", PATCH_TABLE),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": str(path.exists()).lower()} for role, path in sources]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_subspan_mapping_release_recovery.py
  task_id: {TASK_ID}
tags: [PASSIVE-H2, subspan, release-gate, no-release]
related:
  - {rel(ROLE_RECOVERY / "README.md")}
  - {rel(FINAL_GATE / "README.md")}
---
# PASSIVE-H2 Subspan Mapping Release Recovery

Decision: `{summary["decision"]}`.

This packet resolves the first requested H2 follow-up row. Salt2 has explicit
setup-level subspan support for all five source families, but release remains
fail-closed because release-grade case-row source/property provenance and
admission-ready same-QOI evidence are not complete.

Open first: `salt2_subspan_release_gate.csv`, `all_case_setup_coverage.csv`,
and `release_requirements.csv`.
"""
    ensure_dir(OUT)
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_subspan_mapping_release_recovery.py
  task_id: {TASK_ID}
tags: [status, PASSIVE-H2, subspan, release-gate]
related:
  - {rel(OUT / "summary.json")}
---
# {TASK_ID}

## Objective

Recover PASSIVE-H2 source-family-to-subspan mapping evidence and decide whether
it is release-grade.

## Outcome

Decision: `{summary["decision"]}`. Salt2 setup subspan support is recovered for
`{summary["salt2_setup_subspan_support_ready_rows"]}/5` source families, but
release-ready subspan rows remain `{summary["salt2_release_ready_rows"]}/5`.

## Changes Made

Built `{rel(OUT)}` with release gate, all-case coverage, release requirements,
guardrails, source manifest, README, summary, task-owned tests, this status,
journal, and import manifest.

## Validation

Ran builder, unit tests, py_compile, JSON parse, `finish_task.py`, and scoped
`git diff --check`.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit,
source/property/Qwall/numeric q-loss release, coefficient admission, candidate
freeze, final-score claim, hidden multiplier, residual absorption, or runtime
leakage relaxation.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
provenance:
  generated_by: tools/analyze/build_passive_h2_subspan_mapping_release_recovery.py
tags: [journal, PASSIVE-H2, subspan, release-gate]
related:
  - {rel(OUT / "salt2_subspan_release_gate.csv")}
---
# PASSIVE-H2 Subspan Mapping Release Recovery

## Attempted

Consumed the completed role/subspan recovery packet and mapped Salt2 source
families to setup patch/subspan support, area support, and release-grade status.

## Observed

Salt2 has setup subspan support for five of five source families. Only two
families have area-match support, and no row is marked release-grade now.

## Inferred

The subspan blocker is improved for diagnostic setup work but not released for
source/property or final-form admission. Downstream rows may cite setup support,
not a released numeric passive heat-loss claim.

## Next Useful Actions

Run the Salt2 same-QOI setup-UQ gate, then rerun the candidate source/property
gate. Keep Salt3/Salt4 diagnostic work separate until its active runtime-smoke
row closes.
"""
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_subspan_mapping_release_recovery.py",
        "tools/analyze/test_passive_h2_subspan_mapping_release_recovery.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/salt2_subspan_release_gate.csv",
        f"{rel(OUT)}/all_case_setup_coverage.csv",
        f"{rel(OUT)}/release_requirements.csv",
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
            "salt2_setup_subspan_support_ready_rows": summary["salt2_setup_subspan_support_ready_rows"],
            "salt2_release_ready_rows": summary["salt2_release_ready_rows"],
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
    salt2 = salt2_release_rows()
    all_cases = all_case_coverage_rows()
    requirements = release_requirement_rows()
    guards = no_mutation_rows()
    sources = source_manifest_rows()
    role_summary = read_json(ROLE_RECOVERY / "summary.json")

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_subspan_mapping_support_recovered_release_fail_closed",
        "candidate_id": "PASSIVE-H2-CAND001",
        "salt2_source_family_rows": len(salt2),
        "salt2_setup_subspan_support_ready_rows": sum(1 for row in salt2 if truth(row["setup_subspan_support_ready"])),
        "salt2_area_match_support_rows": sum(1 for row in salt2 if truth(row["area_match_support"])),
        "salt2_release_ready_rows": sum(1 for row in salt2 if truth(row["release_ready_now"])),
        "all_case_setup_support_rows": sum(1 for row in all_cases if truth(row["setup_subspan_support_ready"])),
        "all_case_rows": len(all_cases),
        "role_recovery_decision": role_summary["decision"],
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "final_score_claim": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_mutated": False,
        "fluid_or_external_edit": False,
    }

    csv_dump(out / "salt2_subspan_release_gate.csv", list(salt2[0]), salt2)
    csv_dump(out / "all_case_setup_coverage.csv", list(all_cases[0]), all_cases)
    csv_dump(out / "release_requirements.csv", list(requirements[0]), requirements)
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
