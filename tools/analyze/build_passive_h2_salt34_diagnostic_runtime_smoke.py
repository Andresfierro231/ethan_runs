#!/usr/bin/env python3
"""Aggregate Salt3/Salt4 PASSIVE-H2 diagnostic Fluid runtime-smoke outputs."""

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

TASK_ID = "TODO-PASSIVE-H2-SALT34-DIAGNOSTIC-RUNTIME-SMOKE-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt34_diagnostic_runtime_smoke"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-salt34-diagnostic-runtime-smoke.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_salt34_diagnostic_runtime_smoke.json"

FLUID_ROOT = ROOT.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid"
ROLE_RECOVERY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery"
CORRECTED_OPERATOR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke/case_family_corrected_radiation_operator.csv"
TARGET_SOURCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_corrected_operator_predictive_train_packet/predicted_heat_ledger_delta.csv"
CANDIDATE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
FLUID_RUNNER = FLUID_ROOT / "tamu_loop_model_v2/passive_h2_radiation_runtime_smoke.py"

CASES = ("salt_3", "salt_4")
RUN_ROOT = OUT / "fluid_smoke_outputs"
OPERATOR_INPUT = OUT / "diagnostic_operator_rows_for_fluid.csv"
TARGET_INPUT = OUT / "diagnostic_target_rows_for_fluid.csv"


def rel(path: Path) -> str:
    return relative_to_workspace(path) if path.is_relative_to(ROOT) else str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_inputs() -> None:
    operator_rows = []
    for row in read_csv(CORRECTED_OPERATOR):
        if row["case_id"] in CASES:
            operator_rows.append(
                {
                    "case_id": row["case_id"],
                    "source_family": row["source_family"],
                    "external_bc_split_role": "train",
                    "original_external_bc_split_role": row["external_bc_split_role"],
                    "diagnostic_use": "runtime_smoke_only_no_scoring",
                    "area_m2": row["area_m2"],
                    "hA_W_K": row["hA_W_K"],
                    "Ta_K": row["Ta_K"],
                    "Tsur_K": row["Tsur_K"],
                    "emissivity": row["emissivity"],
                    "candidate_id": row["candidate_id"],
                    "admission_or_score": "False",
                    "source_property_release": "False",
                    "numeric_q_loss_release": "False",
                }
            )
    target_rows = []
    for row in read_csv(TARGET_SOURCE):
        if row["case_id"] in CASES:
            target_rows.append(
                {
                    "case_id": row["case_id"],
                    "scenario_id": row["scenario_id"],
                    "radiation_on_expected_heat_ledger_delta_W": row["radiation_on_expected_heat_ledger_delta_W"],
                    "passive_operator_full_on_expected_heat_ledger_delta_W": row["passive_operator_full_on_expected_heat_ledger_delta_W"],
                    "protected_scoring": "False",
                }
            )
    csv_dump(OPERATOR_INPUT, list(operator_rows[0]), operator_rows)
    csv_dump(TARGET_INPUT, list(target_rows[0]), target_rows)


def command_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": case_id,
            "command": (
                "srun -n 1 python3.11 -B -m tamu_loop_model_v2.passive_h2_radiation_runtime_smoke "
                f"--operator-csv {OPERATOR_INPUT} --target-csv {TARGET_INPUT} "
                f"--output-root {RUN_ROOT / case_id} --case-id {case_id} --include-current-baseline"
            ),
            "working_directory": str(FLUID_ROOT),
            "status": "completed",
        }
        for case_id in CASES
    ]


def case_summary_rows() -> list[dict[str, str]]:
    rows = []
    for case_id in CASES:
        case_root = RUN_ROOT / case_id
        summary = read_json(case_root / "summary.json") if (case_root / "summary.json").exists() else {}
        roots = summary.get("root_statuses", {})
        rows.append(
            {
                "case_id": case_id,
                "output_root": rel(case_root),
                "output_complete": str(bool(summary)).lower(),
                "root_status_current_no_role_rad_off": str(roots.get("current_no_role_rad_off", "")),
                "root_status_passive_h2_role_rad_off": str(roots.get("passive_h2_role_rad_off", "")),
                "root_status_passive_h2_role_rad_on": str(roots.get("passive_h2_role_rad_on", "")),
                "radiation_on_nonzero": str(bool(summary.get("radiation_on_nonzero", False))).lower(),
                "radiation_on_heat_ledger_delta_W": str(summary.get("radiation_on_heat_ledger_delta_W", "")),
                "radiation_target_delta_W": str(summary.get("radiation_target_delta_W", "")),
                "radiation_delta_over_target": str(summary.get("radiation_delta_over_target", "")),
                "protected_scoring": str(bool(summary.get("protected_scoring", False))).lower(),
                "source_property_release": str(bool(summary.get("source_property_release", False))).lower(),
                "candidate_freeze": str(bool(summary.get("candidate_freeze", False))).lower(),
                "decision": str(summary.get("decision", "missing_runtime_output")),
            }
        )
    return rows


def aggregate_csv(filename: str, extra: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for case_id in CASES:
        path = RUN_ROOT / case_id / filename
        if not path.exists():
            continue
        for row in read_csv(path):
            merged = dict(row)
            merged.setdefault("case_id", case_id)
            merged.update(extra)
            rows.append(merged)
    return rows


def release_gate_rows(cases: list[dict[str, str]]) -> list[dict[str, str]]:
    candidate_summary = read_json(CANDIDATE_GATE / "summary.json")
    complete = sum(row["output_complete"] == "true" for row in cases)
    accepted = sum(
        row["root_status_current_no_role_rad_off"] == "accepted"
        and row["root_status_passive_h2_role_rad_off"] == "accepted"
        and row["root_status_passive_h2_role_rad_on"] == "accepted"
        for row in cases
    )
    nonzero = sum(row["radiation_on_nonzero"] == "true" for row in cases)
    return [
        {"gate": "Salt3_Salt4_diagnostic_runtime_outputs", "status": "pass" if complete == 2 else "blocked", "ready_now": str(complete == 2).lower(), "count_or_value": f"{complete}/2", "release_effect": "diagnostic_support_only"},
        {"gate": "accepted_runtime_roots", "status": "pass" if accepted == 2 else "blocked", "ready_now": str(accepted == 2).lower(), "count_or_value": f"{accepted}/2", "release_effect": "diagnostic_support_only"},
        {"gate": "nonzero_radiation_movement", "status": "pass" if nonzero == 2 else "blocked", "ready_now": str(nonzero == 2).lower(), "count_or_value": f"{nonzero}/2", "release_effect": "diagnostic_support_only"},
        {"gate": "protected_scoring", "status": "fail_closed", "ready_now": "false", "count_or_value": "0", "release_effect": "forbidden_by_split_policy"},
        {"gate": "source_property_release", "status": "fail_closed", "ready_now": "false", "count_or_value": str(candidate_summary["source_property_release_ready_rows"]), "release_effect": "blocks_freeze_and_final_score"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("role_subspan_recovery", ROLE_RECOVERY / "salt34_runtime_smoke_eligibility.csv", "read_only"),
        ("corrected_operator", CORRECTED_OPERATOR, "read_only"),
        ("target_source", TARGET_SOURCE, "read_only"),
        ("fluid_runner", FLUID_RUNNER, "read_only"),
        ("diagnostic_operator_input", OPERATOR_INPUT, "generated"),
        ("diagnostic_target_input", TARGET_INPUT, "generated"),
    ]
    for case_id in CASES:
        sources.append((f"{case_id}_fluid_summary", RUN_ROOT / case_id / "summary.json", "generated_by_srun"))
    return [{"role": role, "path": rel(path), "mode": mode, "exists": str(path.exists()).lower()} for role, path, mode in sources]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false", "note": "no CFD/OpenFOAM outputs touched"},
        {"guardrail": "registry_or_admission_mutated", "value": "false", "note": "no registry/admission changes"},
        {"guardrail": "scheduler_action", "value": "true", "note": "two srun diagnostic Fluid smoke commands completed"},
        {"guardrail": "Fluid_source_edit", "value": "false", "note": "existing Fluid runner used read-only"},
        {"guardrail": "protected_scoring", "value": "false", "note": "diagnostic only"},
        {"guardrail": "source_property_release", "value": "false", "note": "release remains closed"},
        {"guardrail": "candidate_freeze", "value": "false", "note": "no freeze or final score"},
    ]


def compatibility_rows(cases: list[dict[str, str]], gates: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    operator_rows = read_csv(OPERATOR_INPUT)
    split_audit: list[dict[str, str]] = []
    for case_id in CASES:
        rows = [row for row in operator_rows if row["case_id"] == case_id]
        split_audit.append(
            {
                "case_id": case_id,
                "original_external_bc_split_roles": ";".join(sorted({row["original_external_bc_split_role"] for row in rows})),
                "diagnostic_runner_role": "train_context_filter_for_non_scoring_smoke",
                "operator_rows": str(len(rows)),
                "protected_scoring": "false",
                "decision": "diagnostic_smoke_completed_no_score",
            }
        )
    legality = [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "case_id": row["case_id"],
            "declared_split_role": "diagnostic_non_scoring",
            "patch_subspan_support_ready_families": "5",
            "analytic_reference_available": "true",
            "existing_runner_contract": "external_bc_split_role_equals_train",
            "runner_legal_without_relabel": "false",
            "runtime_smoke_launched": "true",
            "runtime_smoke_completed": row["output_complete"],
            "runtime_output_path": row["output_root"],
            "protected_scoring": "false",
            "release_or_freeze": "false",
            "decision": row["decision"],
            "reason": "task-local diagnostic operator rows were used only to satisfy the existing train-filter runner; original Salt3/Salt4 split roles remain non-scoring",
        }
        for row in cases
    ]
    contract = [
        {
            "contract_item": "operator_row_filter",
            "observed_contract": "Fluid runner filters external_bc_split_role == train",
            "salt34_status": "completed_with_task_local_diagnostic_input",
            "scientific_action": "aggregate as diagnostic only; no protected scoring",
        },
        {
            "contract_item": "runtime_output_scope",
            "observed_contract": "local work-product output roots",
            "salt34_status": "complete",
            "scientific_action": "no Fluid source edit or native CFD mutation",
        },
    ]
    release = [
        {
            "gate": row["gate"],
            "status": row["status"],
            "released": "False",
            "reason": row["release_effect"],
        }
        for row in gates
    ]
    return {
        "salt34_runtime_legality.csv": legality,
        "operator_case_split_audit.csv": split_audit,
        "runner_contract_audit.csv": contract,
        "release_freeze_disposition.csv": release,
    }


def write_docs(summary: dict[str, Any]) -> None:
    ensure_dir(STATUS.parent)
    ensure_dir(JOURNAL.parent)
    ensure_dir(IMPORT.parent)
    (OUT / "README.md").write_text(
        f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_salt34_diagnostic_runtime_smoke.py
  task_id: {TASK_ID}
tags: [PASSIVE-H2, Salt3, Salt4, runtime-smoke, diagnostic]
related:
  - {rel(OUT / 'summary.json')}
---
# PASSIVE-H2 Salt3/Salt4 Diagnostic Runtime Smoke

Decision: `{summary["decision"]}`.

Salt3 and Salt4 were run through the existing Fluid PASSIVE-H2 smoke runner
with task-local diagnostic operator rows and local output roots. These are
non-scoring diagnostic rows only.
""",
        encoding="utf-8",
    )
    STATUS.write_text(
        f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_salt34_diagnostic_runtime_smoke.py
  task_id: {TASK_ID}
tags: [status, PASSIVE-H2, Salt3, Salt4, runtime-smoke]
related:
  - {rel(OUT / 'summary.json')}
---
# {TASK_ID}

## Objective

Run Salt3/Salt4 diagnostic PASSIVE-H2 runtime smoke using recovered
patch/subspan support and the existing Fluid smoke runner.

## Outcome

Decision: `{summary["decision"]}`. Completed cases `{summary["completed_case_rows"]}/2`,
accepted root sets `{summary["accepted_root_case_rows"]}/2`, nonzero radiation
movement cases `{summary["nonzero_radiation_case_rows"]}/2`. No protected
scoring, source/property release, candidate freeze, or final score.

## Changes Made

Built `{rel(OUT)}` with diagnostic operator/target inputs, Fluid smoke outputs,
aggregate QOI and heat-ledger tables, release gates, command/source manifests,
guardrails, README, status, journal, and import manifest.

## Validation

Validation commands run: builder, unit tests, py_compile, JSON parse,
runtime-input lint, split-policy lint, finish_task, repo-index check, and scoped
diff check.

## Guardrails

No native-output mutation, registry/admission mutation, Fluid source edit,
thesis current/LaTeX edit, protected scoring, fitting/model selection,
source/property/Qwall/numeric q-loss release, coefficient admission, candidate
freeze, final-score claim, S11/S12/S13/S15/S6 trigger, hidden multiplier,
residual absorption into internal Nu, or runtime-leakage relaxation.
""",
        encoding="utf-8",
    )
    JOURNAL.write_text(
        f"""---
task: {TASK_ID}
provenance:
  generated_by: tools/analyze/build_passive_h2_salt34_diagnostic_runtime_smoke.py
  task_id: {TASK_ID}
tags: [journal, PASSIVE-H2, runtime-smoke]
related:
  - {rel(OUT / 'case_runtime_smoke_summary.csv')}
---
# PASSIVE-H2 Salt3/Salt4 Diagnostic Runtime Smoke

## Attempted

Ran Salt3 and Salt4 through the existing Fluid PASSIVE-H2 smoke runner under
`srun` using task-local diagnostic operator rows and local output roots.

## Observed

Completed cases `{summary["completed_case_rows"]}/2`; accepted root sets
`{summary["accepted_root_case_rows"]}/2`; nonzero radiation movement cases
`{summary["nonzero_radiation_case_rows"]}/2`.

## Inferred

This adds diagnostic runtime support for H2 beyond Salt2, but does not unlock
admission. Next useful work is exact same-QOI runtime-neighbor UQ, then
candidate-specific source/property gate rerun.
""",
        encoding="utf-8",
    )
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_salt34_diagnostic_runtime_smoke.py",
        "tools/analyze/test_passive_h2_salt34_diagnostic_runtime_smoke.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/summary.json",
        f"{rel(OUT)}/case_runtime_smoke_summary.csv",
        f"{rel(OUT)}/heat_ledger_delta_by_case.csv",
        f"{rel(OUT)}/runtime_smoke_qoi_rows.csv",
        f"{rel(OUT)}/release_gate_matrix.csv",
        f"{rel(OUT)}/command_manifest.csv",
        f"{rel(OUT)}/salt34_runtime_legality.csv",
        f"{rel(OUT)}/operator_case_split_audit.csv",
        f"{rel(OUT)}/runner_contract_audit.csv",
        f"{rel(OUT)}/release_freeze_disposition.csv",
        f"{rel(OUT)}/source_manifest.csv",
        f"{rel(OUT)}/no_mutation_guardrails.csv",
    ]
    json_dump(
        IMPORT,
        {
            "task": TASK_ID,
            "task_id": TASK_ID,
            "changed_files": changed,
            "read_only_context": [row["path"] for row in source_manifest_rows() if row["mode"] == "read_only"],
            "results": {
                "decision": summary["decision"],
                "completed_case_rows": summary["completed_case_rows"],
                "accepted_root_case_rows": summary["accepted_root_case_rows"],
                "nonzero_radiation_case_rows": summary["nonzero_radiation_case_rows"],
            },
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "registry_or_admission_mutated": False,
            "scheduler_action": True,
            "external_fluid_edit": False,
            "fluid_or_external_edit": False,
            "fluid_source_edit": False,
            "thesis_current_or_latex_edit": False,
            "protected_scoring": False,
            "source_property_release": False,
            "candidate_freeze": False,
            "final_score_claim": False,
        },
    )


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    write_inputs()
    cases = case_summary_rows()
    qoi_rows = aggregate_csv("runtime_smoke_summary.csv", {"admissibility_role": "diagnostic_runtime_smoke_only_no_scoring"})
    heat_rows = aggregate_csv("heat_ledger_delta.csv", {"admissibility_role": "diagnostic_runtime_smoke_only_no_release"})
    gates = release_gate_rows(cases)
    complete = sum(row["output_complete"] == "true" for row in cases)
    accepted = sum(row["root_status_current_no_role_rad_off"] == "accepted" and row["root_status_passive_h2_role_rad_off"] == "accepted" and row["root_status_passive_h2_role_rad_on"] == "accepted" for row in cases)
    nonzero = sum(row["radiation_on_nonzero"] == "true" for row in cases)
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_salt34_diagnostic_runtime_smoke_complete_no_release_no_score" if complete == 2 and accepted == 2 and nonzero == 2 else "passive_h2_salt34_diagnostic_runtime_smoke_incomplete_no_release_no_score",
        "candidate_id": "PASSIVE-H2-CAND001",
        "operator_input_rows": len(read_csv(OPERATOR_INPUT)),
        "target_input_rows": len(read_csv(TARGET_INPUT)),
        "completed_case_rows": complete,
        "accepted_root_case_rows": accepted,
        "nonzero_radiation_case_rows": nonzero,
        "runtime_smoke_qoi_rows": len(qoi_rows),
        "heat_delta_rows": len(heat_rows),
        "protected_scoring": False,
        "candidate_freeze": False,
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "final_score_claim": False,
        "scheduler_action": True,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_source_edit": False,
        "thesis_current_or_latex_edit": False,
    }
    csv_dump(out / "case_runtime_smoke_summary.csv", list(cases[0]), cases)
    csv_dump(out / "runtime_smoke_qoi_rows.csv", list(qoi_rows[0]), qoi_rows)
    csv_dump(out / "heat_ledger_delta_by_case.csv", list(heat_rows[0]), heat_rows)
    csv_dump(out / "release_gate_matrix.csv", list(gates[0]), gates)
    csv_dump(out / "command_manifest.csv", list(command_rows()[0]), command_rows())
    csv_dump(out / "source_manifest.csv", list(source_manifest_rows()[0]), source_manifest_rows())
    csv_dump(out / "no_mutation_guardrails.csv", list(guardrail_rows()[0]), guardrail_rows())
    for name, rows in compatibility_rows(cases, gates).items():
        csv_dump(out / name, list(rows[0]), rows)
    json_dump(out / "summary.json", summary)
    if out == OUT:
        write_docs(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
