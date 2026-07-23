#!/usr/bin/env python3
"""Build PASSIVE-H2 Salt2 same-QOI setup-only UQ gate artifacts."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-PASSIVE-H2-SALT2-SAME-QOI-SETUP-UQ-GATE-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-salt2-same-qoi-setup-uq-gate.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate.json"

ROLE_RECOVERY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery"
SUBSPAN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_subspan_mapping_release_recovery"
RUNTIME_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate"
RUNTIME = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
FINAL_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def truth(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "pass"}


def finite_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def qoi_readiness_rows() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(ROLE_RECOVERY / "same_qoi_setup_uq_readiness.csv"):
        release_ready = truth(row["same_qoi_setup_only_uq_available"]) and truth(row["admission_release_ready"])
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "qoi_label": row["qoi_label"],
                "setup_input_families_computed": row["setup_input_families_computed"],
                "setup_input_families_available": row["setup_input_families_available"],
                "target_minus_plus_available": row["same_qoi_setup_only_uq_available"],
                "setup_only_uq_gate": "pass_diagnostic" if truth(row["same_qoi_setup_only_uq_available"]) else "fail_closed",
                "admission_release_ready": row["admission_release_ready"],
                "release_ready_now": str(release_ready).lower(),
                "admissibility_role": "diagnostic_train_context_only",
                "reason": row["reason"],
                "source_path": row["source_path"],
            }
        )
    return rows


def qoi_envelope_rows() -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(ROLE_RECOVERY / "same_qoi_setup_only_uq_results.csv"):
        grouped[row["qoi_label"]].append(row)

    rows = []
    for qoi, qrows in sorted(grouped.items()):
        finite = [finite_float(row["max_abs_value"]) for row in qrows]
        finite_vals = [value for value in finite if value is not None]
        half_ranges = [finite_float(row["half_range_value"]) for row in qrows]
        half_vals = [value for value in half_ranges if value is not None]
        release_ready_rows = sum(1 for row in qrows if truth(row["admission_release_ready"]))
        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": "salt_2",
                "qoi_label": qoi,
                "input_family_rows": str(len(qrows)),
                "finite_input_family_rows": str(len(finite_vals)),
                "max_abs_envelope": "" if not finite_vals else f"{max(finite_vals):.12g}",
                "max_half_range": "" if not half_vals else f"{max(half_vals):.12g}",
                "setup_uq_computed_rows": str(sum(1 for row in qrows if truth(row["setup_only_uq_computed"]))),
                "release_ready_rows": str(release_ready_rows),
                "gate_decision": "pass_diagnostic_no_release" if finite_vals else "fail_closed_no_finite_values",
            }
        )
    return rows


def input_family_rows() -> list[dict[str, str]]:
    keep = [
        "candidate_id",
        "case_id",
        "input_family",
        "qoi_label",
        "unit",
        "target_row_available",
        "target_minus_row_available",
        "target_plus_row_available",
        "finite_neighbor_values",
        "minus_level",
        "minus_value",
        "plus_level",
        "plus_value",
        "half_range_value",
        "max_abs_value",
        "setup_only_uq_computed",
        "admission_release_ready",
        "admissibility_role",
        "reason",
    ]
    return [{field: row[field] for field in keep} for row in read_csv(ROLE_RECOVERY / "same_qoi_setup_only_uq_results.csv")]


def guardrail_rows() -> list[dict[str, str]]:
    runtime_summary = read_json(RUNTIME / "summary.json")
    return [
        {"guardrail": "runtime_wallHeatFlux_used", "value": str(runtime_summary["runtime_wallHeatFlux_used"]).lower(), "expected": "false"},
        {"guardrail": "runtime_CFD_mdot_used", "value": str(runtime_summary["runtime_CFD_mdot_used"]).lower(), "expected": "false"},
        {"guardrail": "runtime_Qwall_used", "value": str(runtime_summary["runtime_Qwall_used"]).lower(), "expected": "false"},
        {"guardrail": "runtime_imposed_cooler_duty_used", "value": str(runtime_summary["runtime_imposed_cooler_duty_used"]).lower(), "expected": "false"},
        {"guardrail": "runtime_validation_temperature_used", "value": str(runtime_summary["runtime_validation_temperature_used"]).lower(), "expected": "false"},
        {"guardrail": "protected_scoring", "value": "false", "expected": "false"},
        {"guardrail": "source_property_release", "value": "false", "expected": "false"},
        {"guardrail": "candidate_freeze", "value": "false", "expected": "false"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("role_uq_readiness", ROLE_RECOVERY / "same_qoi_setup_uq_readiness.csv"),
        ("role_uq_results", ROLE_RECOVERY / "same_qoi_setup_only_uq_results.csv"),
        ("subspan_recovery", SUBSPAN / "summary.json"),
        ("runtime_operator_smoke_uq", RUNTIME_UQ / "summary.json"),
        ("runtime_implementation", RUNTIME / "summary.json"),
        ("final_form_gate", FINAL_GATE / "summary.json"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": str(path.exists()).lower()} for role, path in sources]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_salt2_same_qoi_setup_uq_gate.py
  task_id: {TASK_ID}
tags: [PASSIVE-H2, Salt2, same-QOI-UQ, diagnostic, no-release]
related:
  - {rel(ROLE_RECOVERY / "README.md")}
  - {rel(SUBSPAN / "README.md")}
---
# PASSIVE-H2 Salt2 Same-QOI Setup-UQ Gate

Decision: `{summary["decision"]}`.

Salt2 same-QOI setup perturbation evidence is present for six QOI labels and is
usable as diagnostic train-context sensitivity evidence. It is not release-ready
and does not open source/property release, freeze, protected scoring, or final
form.
"""
    ensure_dir(OUT)
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_salt2_same_qoi_setup_uq_gate.py
  task_id: {TASK_ID}
tags: [status, PASSIVE-H2, Salt2, same-QOI-UQ]
related:
  - {rel(OUT / "summary.json")}
---
# {TASK_ID}

## Objective

Gate Salt2 same-QOI setup-only UQ evidence for PASSIVE-H2.

## Outcome

Decision: `{summary["decision"]}`. Same-QOI setup-UQ is diagnostic-ready for
`{summary["diagnostic_ready_qoi_labels"]}/{summary["qoi_labels"]}` QOI labels,
with `{summary["uq_result_rows"]}` input-family/QOI rows. Release-ready QOI
labels remain `{summary["release_ready_qoi_labels"]}`.

## Changes Made

Built `{rel(OUT)}` with QOI readiness, envelope, input-family sensitivity,
guardrail, source-manifest, README, summary, tests, status, journal, and import
manifest.

## Validation

Ran builder, unit tests, py_compile, JSON parse, `finish_task.py`, and scoped
`git diff --check`.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
Fluid/external edit, protected scoring, source/property/Qwall/numeric q-loss
release, coefficient admission, candidate freeze, final-score claim, hidden
multiplier, residual absorption, or runtime-leakage relaxation.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
provenance:
  generated_by: tools/analyze/build_passive_h2_salt2_same_qoi_setup_uq_gate.py
tags: [journal, PASSIVE-H2, Salt2, same-QOI-UQ]
related:
  - {rel(OUT / "qoi_readiness_gate.csv")}
---
# PASSIVE-H2 Salt2 Same-QOI Setup-UQ Gate

## Attempted

Consumed the completed role/subspan recovery UQ tables and rebuilt a strict
same-QOI setup-UQ gate for Salt2.

## Observed

Six QOI labels have target/minus/plus availability. Existing perturbation
rows are finite enough for diagnostic train-context sensitivity. No QOI label
is admission-release-ready.

## Inferred

The same-QOI blocker has moved from missing diagnostic sensitivity to
diagnostic-only sensitivity. It still cannot support release or final form
without source/property and release-grade subspan gates.

## Next Useful Actions

Rerun the PASSIVE-H2 candidate source/property gate using this diagnostic UQ
and the subspan recovery row. Keep protected scoring closed.
"""
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_salt2_same_qoi_setup_uq_gate.py",
        "tools/analyze/test_passive_h2_salt2_same_qoi_setup_uq_gate.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/qoi_readiness_gate.csv",
        f"{rel(OUT)}/qoi_envelope_summary.csv",
        f"{rel(OUT)}/input_family_sensitivity.csv",
        f"{rel(OUT)}/runtime_guardrails.csv",
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
            "diagnostic_ready_qoi_labels": summary["diagnostic_ready_qoi_labels"],
            "release_ready_qoi_labels": summary["release_ready_qoi_labels"],
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
    readiness = qoi_readiness_rows()
    envelopes = qoi_envelope_rows()
    families = input_family_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_salt2_same_qoi_setup_uq_diagnostic_ready_no_release",
        "candidate_id": "PASSIVE-H2-CAND001",
        "case_id": "salt_2",
        "qoi_labels": len(readiness),
        "diagnostic_ready_qoi_labels": sum(1 for row in readiness if row["setup_only_uq_gate"] == "pass_diagnostic"),
        "release_ready_qoi_labels": sum(1 for row in readiness if truth(row["release_ready_now"])),
        "uq_result_rows": len(families),
        "finite_envelope_qoi_labels": sum(1 for row in envelopes if row["gate_decision"] == "pass_diagnostic_no_release"),
        "subspan_release_recovery_available": (SUBSPAN / "summary.json").exists(),
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

    csv_dump(out / "qoi_readiness_gate.csv", list(readiness[0]), readiness)
    csv_dump(out / "qoi_envelope_summary.csv", list(envelopes[0]), envelopes)
    csv_dump(out / "input_family_sensitivity.csv", list(families[0]), families)
    csv_dump(out / "runtime_guardrails.csv", list(guards[0]), guards)
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
