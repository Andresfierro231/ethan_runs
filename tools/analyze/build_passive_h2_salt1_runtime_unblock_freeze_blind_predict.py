#!/usr/bin/env python3
"""Recover Salt1 PASSIVE-H2 rows, harvest runtime smoke, and rerun freeze gates."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-PASSIVE-H2-SALT1-RUNTIME-UNBLOCK-FREEZE-BLIND-PREDICT-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-salt1-runtime-unblock-freeze-blind-predict.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict.json"

FLUID_ROOT = ROOT.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid"
RUNTIME_OUTPUT = OUT / "fluid_smoke_outputs/salt_1"

SALT1_RECOVERY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_salt1_train_external_bc_recovery_freeze_gate"
SALT14_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_diagnostic_freeze_and_blind_predictions"
TRAINTEST = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest"
RUNTIME_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke"
ROLE_FILTERED_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_candidate_gate_rerun_passive_role_filtered_policy"
PM5 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair"
VAL_SALT2 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def recovered_operator_rows() -> list[dict[str, Any]]:
    rows = read_csv(SALT1_RECOVERY / "augmented_fluid_external_boundary_runtime_dictionary.csv")
    selected = [
        row
        for row in rows
        if row.get("case_id") == "salt_1"
        and row.get("mode") == "predictive"
        and row.get("physical_role") == "ambient_wall"
        and row.get("convection_active") == "true"
        and row.get("radiation_active") == "true"
    ]
    out: list[dict[str, Any]] = []
    for row in selected:
        area = as_float(row.get("area_m2", ""))
        h = as_float(row.get("h_W_m2_K", ""))
        out.append(
            {
                "case_id": "salt_1",
                "source_family": row.get("segment_id", ""),
                "external_bc_split_role": "train",
                "original_external_bc_split_role": row.get("validation_split_role", "train"),
                "diagnostic_use": "salt1_runtime_smoke_train_only_no_scoring",
                "area_m2": area,
                "hA_W_K": area * h if math.isfinite(area) and math.isfinite(h) else "",
                "Ta_K": row.get("Ta_K", ""),
                "Tsur_K": row.get("Tsur_K", ""),
                "emissivity": row.get("emissivity", ""),
                "candidate_id": "PASSIVE-H2-CAND001",
                "admission_or_score": False,
                "source_property_release": False,
                "numeric_q_loss_release": False,
                "runtime_CFD_mdot_used": False,
                "runtime_Qwall_used": False,
                "runtime_validation_temperature_used": False,
                "runtime_wallHeatFlux_used": False,
                "source_paths": row.get("source_paths", ""),
            }
        )
    out.sort(key=lambda item: str(item["source_family"]))
    return out


def salt1_target_rows() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "salt_1",
            "scenario_id": "salt_1__V00__nominal",
            "radiation_on_expected_heat_ledger_delta_W": "",
            "passive_operator_full_on_expected_heat_ledger_delta_W": "",
            "protected_scoring": False,
            "target_status": "not_available_without_using_forbidden_wallHeatFlux_or_fit_residual",
        }
    ]


def recovery_provenance_rows() -> list[dict[str, Any]]:
    operator = recovered_operator_rows()
    families = {str(row["source_family"]) for row in operator}
    expected = {"cooling_branch", "downcomer", "junction", "lower_leg", "upcomer"}
    return [
        {
            "evidence_item": "salt1_recovered_operator_rows",
            "status": "pass_diagnostic" if len(operator) >= 4 else "fail_closed",
            "count_or_value": str(len(operator)),
            "release_ready": False,
            "reason": "Recovered from setup external-boundary dictionary rows; runtime wallHeatFlux remains forbidden context only.",
            "evidence_path": rel(SALT1_RECOVERY / "augmented_fluid_external_boundary_runtime_dictionary.csv"),
        },
        {
            "evidence_item": "passive_source_family_coverage",
            "status": "partial",
            "count_or_value": f"{len(families)}/5",
            "release_ready": False,
            "reason": "Salt1 recovered rows omit junction; sufficient for a diagnostic smoke attempt only, not PASSIVE-H2 release.",
            "evidence_path": rel(SALT1_RECOVERY / "salt1_external_bc_recovery_rows.csv"),
        },
        {
            "evidence_item": "forbidden_runtime_inputs",
            "status": "pass",
            "count_or_value": "0",
            "release_ready": False,
            "reason": "Recovered operator rows set CFD mdot, Qwall, validation temperature, and wallHeatFlux runtime-use flags false.",
            "evidence_path": rel(OUT / "salt1_recovered_operator_rows_for_fluid.csv"),
        },
        {
            "evidence_item": "target_heat_delta",
            "status": "not_available",
            "count_or_value": "0",
            "release_ready": False,
            "reason": "No numeric Salt1 PASSIVE-H2 target emitted because using recovered diagnostic wallHeatFlux or residual filling would leak.",
            "evidence_path": rel(OUT / "salt1_runtime_target_context.csv"),
        },
    ]


def command_rows() -> list[dict[str, str]]:
    cmd = (
        "srun -n 1 python3.11 -B -m tamu_loop_model_v2.passive_h2_radiation_runtime_smoke "
        f"--operator-csv {OUT / 'salt1_recovered_operator_rows_for_fluid.csv'} "
        f"--target-csv {OUT / 'salt1_runtime_target_context.csv'} "
        f"--output-root {RUNTIME_OUTPUT} --case-id salt_1 --include-current-baseline"
    )
    return [
        {
            "case_id": "salt_1",
            "working_directory": str(FLUID_ROOT),
            "command": cmd,
            "status": "completed" if (RUNTIME_OUTPUT / "summary.json").exists() else "not_run_yet",
            "scheduler_job_step": "3307325.6" if (RUNTIME_OUTPUT / "summary.json").exists() else "",
            "stdout_log": rel(OUT / "salt1_runtime_smoke.stdout"),
            "stderr_log": rel(OUT / "salt1_runtime_smoke.stderr"),
        }
    ]


def runtime_status_rows() -> list[dict[str, Any]]:
    summary = read_json(RUNTIME_OUTPUT / "summary.json")
    if not summary:
        return [
            {
                "case_id": "salt_1",
                "output_root": rel(RUNTIME_OUTPUT),
                "output_complete": False,
                "root_status_current_no_role_rad_off": "",
                "root_status_passive_h2_role_rad_off": "",
                "root_status_passive_h2_role_rad_on": "",
                "radiation_on_nonzero": False,
                "radiation_on_heat_ledger_delta_W": "",
                "radiation_target_delta_W": "",
                "protected_scoring": False,
                "source_property_release": False,
                "candidate_freeze": False,
                "decision": "not_run_yet",
            }
        ]
    roots = summary.get("root_statuses", {})
    return [
        {
            "case_id": "salt_1",
            "output_root": rel(RUNTIME_OUTPUT),
            "output_complete": True,
            "root_status_current_no_role_rad_off": roots.get("current_no_role_rad_off", ""),
            "root_status_passive_h2_role_rad_off": roots.get("passive_h2_role_rad_off", ""),
            "root_status_passive_h2_role_rad_on": roots.get("passive_h2_role_rad_on", ""),
            "radiation_on_nonzero": bool(summary.get("radiation_on_nonzero", False)),
            "radiation_on_heat_ledger_delta_W": summary.get("radiation_on_heat_ledger_delta_W", ""),
            "radiation_target_delta_W": summary.get("radiation_target_delta_W", ""),
            "protected_scoring": False,
            "source_property_release": False,
            "candidate_freeze": False,
            "decision": summary.get("decision", ""),
        }
    ]


def four_case_runtime_evidence_rows() -> list[dict[str, Any]]:
    previous = read_csv(RUNTIME_GATE / "three_case_runtime_evidence.csv")
    rows: list[dict[str, Any]] = []
    for row in previous:
        rows.append(dict(row))
    salt1 = runtime_status_rows()[0]
    rows.append(
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "case_id": "salt_1",
            "split_role": "train",
            "runtime_evidence_source": "Salt1 recovered external-boundary runtime smoke",
            "runtime_completed": str(bool(salt1["output_complete"])).lower(),
            "accepted_roots": str(
                salt1["root_status_current_no_role_rad_off"] == "accepted"
                and salt1["root_status_passive_h2_role_rad_off"] == "accepted"
                and salt1["root_status_passive_h2_role_rad_on"] == "accepted"
            ).lower(),
            "radiation_on_nonzero": str(bool(salt1["radiation_on_nonzero"])).lower(),
            "radiation_on_heat_ledger_delta_W": salt1["radiation_on_heat_ledger_delta_W"],
            "radiation_target_delta_W": salt1["radiation_target_delta_W"],
            "radiation_delta_over_target": "",
            "protected_scoring": "false",
            "source_property_release": "false",
            "candidate_freeze": "false",
            "admissibility_role": "train_runtime_diagnostic_no_release",
            "evidence_path": rel(RUNTIME_OUTPUT / "summary.json") if salt1["output_complete"] else "",
        }
    )
    return rows


def freeze_gate_rows() -> list[dict[str, Any]]:
    runtime_rows = four_case_runtime_evidence_rows()
    train_case_ids = {"salt_1", "salt_2", "salt_3", "salt_4"}
    runtime_complete = {
        row["case_id"]
        for row in runtime_rows
        if row.get("case_id") in train_case_ids
        and str(row.get("runtime_completed", "")).lower() == "true"
        and str(row.get("accepted_roots", "")).lower() == "true"
    }
    role_gate = read_json(ROLE_FILTERED_GATE / "summary.json")
    source_gate = read_json(RUNTIME_GATE / "summary.json")
    return [
        {
            "gate": "salt1_4_runtime_smoke_complete",
            "status": "pass_diagnostic" if runtime_complete == train_case_ids else "fail_closed",
            "count_or_value": f"{len(runtime_complete)}/4",
            "freeze_ready": False,
            "reason": "All Salt1-4 runtime rows must complete before any diagnostic lock can be discussed.",
        },
        {
            "gate": "source_family_coverage",
            "status": "fail_closed",
            "count_or_value": "Salt1=4/5",
            "freeze_ready": False,
            "reason": "Salt1 recovered external-boundary rows omit junction; this blocks PASSIVE-H2 release-grade family coverage.",
        },
        {
            "gate": "strict_source_envelope_policy",
            "status": "fail_closed",
            "count_or_value": str(role_gate.get("strict_source_envelope_pass_rows", 0)),
            "freeze_ready": False,
            "reason": "Passive-role filtered subspan/setup provenance is recovered, but strict source-envelope substitution is still not admitted.",
        },
        {
            "gate": "source_property_admission_release",
            "status": "fail_closed",
            "count_or_value": str(role_gate.get("source_property_admission_release_ready_rows", source_gate.get("source_property_release_ready_rows", 0))),
            "freeze_ready": False,
            "reason": "Source/property release-ready rows remain zero.",
        },
        {
            "gate": "candidate_freeze",
            "status": "closed_not_run",
            "count_or_value": "0",
            "freeze_ready": False,
            "reason": "No admitted or final PASSIVE-H2 coefficient freeze is allowed until upstream release gates pass.",
        },
    ]


def coefficient_lock_rows() -> list[dict[str, Any]]:
    runtime_pass = freeze_gate_rows()[0]["status"] == "pass_diagnostic"
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "lock_id": "PASSIVE_H2_SALT14_FINAL_LOCK_TBD",
            "requested_train_cases": "salt1_nominal;salt2_jin_nominal;salt3_jin_nominal;salt4_nominal",
            "salt1_4_runtime_smoke_complete": runtime_pass,
            "diagnostic_runtime_lock_created": False,
            "admitted_final_freeze_created": False,
            "coefficient_names": "none_emitted",
            "coefficient_values": "",
            "reason": "runtime evidence can support diagnostics only; source-family coverage and source/property admission gates remain closed",
        }
    ]


def blind_prediction_rows() -> list[dict[str, Any]]:
    qois = ["mdot_kg_s", "pressure_residual_Pa", "qambient_total_W", "qhx_total_W", "TP_temperature_K", "TW_temperature_K"]
    blind = read_csv(TRAINTEST / "blind_test_availability.csv")
    rows: list[dict[str, Any]] = []
    for case in blind:
        for qoi in qois:
            rows.append(
                {
                    "candidate_id": "PASSIVE-H2-CAND001",
                    "lock_id": "PASSIVE_H2_SALT14_FINAL_LOCK_TBD",
                    "case_key": case["case_key"],
                    "final_scorecard_partition": case["final_scorecard_partition"],
                    "prediction_qoi": qoi,
                    "prediction_available": False,
                    "prediction_value": "",
                    "score_emitted": False,
                    "reason": "no admitted Salt1-4 PASSIVE-H2 freeze and no blind-row setup operator/prediction artifact",
                    "target_rows_available": case["target_rows_available"],
                }
            )
    return rows


def leakage_audit_rows() -> list[dict[str, str]]:
    return [
        {"item": "Salt1 recovered operator rows", "role": "train_runtime_input", "used_for_fit": "false", "used_for_model_selection": "false", "used_for_score": "false", "status": "setup h/area/Ta/Tsur/emissivity used; diagnostic wallHeatFlux remains forbidden"},
        {"item": "Salt2-4 existing runtime evidence", "role": "train_support_context", "used_for_fit": "false", "used_for_model_selection": "false", "used_for_score": "false", "status": "read-only context for four-case evidence table"},
        {"item": "Salt2 +/-5Q and val_salt2 targets", "role": "blind_test_context", "used_for_fit": "false", "used_for_model_selection": "false", "used_for_score": "false", "status": "availability only; no predictions or scores emitted"},
        {"item": "CFD mdot / realized wallHeatFlux / validation TP-TW / imposed cooler duty / residual fills", "role": "forbidden_runtime_inputs", "used_for_fit": "false", "used_for_model_selection": "false", "used_for_score": "false", "status": "not consumed by runtime runner or gate builder"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("salt1_augmented_runtime_dictionary", SALT1_RECOVERY / "augmented_fluid_external_boundary_runtime_dictionary.csv"),
        ("salt1_recovery_rows", SALT1_RECOVERY / "salt1_external_bc_recovery_rows.csv"),
        ("prior_salt14_freeze_attempt", SALT14_PREFLIGHT / "summary.json"),
        ("prior_train_test_gate", TRAINTEST / "summary.json"),
        ("prior_three_case_runtime_gate", RUNTIME_GATE / "three_case_runtime_evidence.csv"),
        ("passive_role_filtered_gate", ROLE_FILTERED_GATE / "summary.json"),
        ("fluid_runner", FLUID_ROOT / "tamu_loop_model_v2/passive_h2_radiation_runtime_smoke.py"),
        ("pm5_targets", PM5 / "salt2_pm5_holdout_metrics.csv"),
        ("val_salt2_targets", VAL_SALT2 / "val_salt2_external_score_targets.csv"),
    ]
    return [{"source_label": label, "source_path": rel(path), "exists": str(path.exists()).lower(), "use": "read_only_input", "mutated": "false"} for label, path in sources]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_or_admission_mutated", "value": "false"},
        {"guardrail": "Fluid_or_external_source_edit", "value": "false"},
        {"guardrail": "source_property_or_qwall_release", "value": "false"},
        {"guardrail": "admitted_final_candidate_freeze", "value": "false"},
        {"guardrail": "protected_row_fitting_or_model_selection", "value": "false"},
        {"guardrail": "final_score_claim", "value": "false"},
        {"guardrail": "runtime_leakage_relaxation", "value": "false"},
    ]


def write_runtime_script(out: Path) -> None:
    command = command_rows()[0]["command"]
    script = f"""#!/usr/bin/env bash
set -euo pipefail
cd {FLUID_ROOT}
{command}
"""
    path = out / "run_salt1_runtime_smoke.sh"
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
provenance:
  - {rel(out / "summary.json")}
tags: [PASSIVE-H2, Salt1, runtime-smoke, predictive-model]
---
# PASSIVE-H2 Salt1 Runtime Unblock / Freeze / Blind Prediction Attempt

Decision: `{summary["decision"]}`.

This package recovers Salt1 setup-only PASSIVE-H2 operator rows from the July 21
Salt1 external-BC recovery package, runs or prepares the same Fluid runtime
smoke path used for Salt2-4, then reruns the Salt1-4 freeze and blind-prediction
decision.

The Salt1 recovered operator is diagnostic, not release-ready: it has four
passive source families and omits junction. Runtime evidence may therefore
support blocker burn-down, but not final coefficient admission or blind scoring.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: status
status: complete
provenance:
  - {rel(OUT / "summary.json")}
tags: [PASSIVE-H2, Salt1, runtime-smoke]
---
# {TASK_ID}

Task: `{TASK_ID}`

## Objective

Recover Salt1 external-boundary/operator rows, run Salt1 through the same
PASSIVE-H2 runtime-smoke path used for Salt2-4 under scheduler accounting, then
rerun Salt1-4 freeze and blind-prediction gates.

## Outcome

Decision: `{summary["decision"]}`.

## Changes Made

- `{rel(OUT)}`
- `{rel(Path("tools/analyze/build_passive_h2_salt1_runtime_unblock_freeze_blind_predict.py"))}`
- `{rel(Path("tools/analyze/test_passive_h2_salt1_runtime_unblock_freeze_blind_predict.py"))}`
- `{rel(IMPORT)}`

## Validation

- `python3.11 tools/analyze/test_passive_h2_salt1_runtime_unblock_freeze_blind_predict.py`
- `python3.11 tools/analyze/build_passive_h2_salt1_runtime_unblock_freeze_blind_predict.py`

## Guardrails

No native outputs, registry/admission state, Fluid/external source files, thesis
current/LaTeX files, source/property/Qwall release, admitted/final freeze,
protected-row fitting/model selection, final score, hidden multiplier, residual
absorption, or runtime-leakage boundary were changed.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
provenance:
  - {rel(OUT / "summary.json")}
tags: [PASSIVE-H2, Salt1, predictive-model]
---
# PASSIVE-H2 Salt1 Runtime Unblock / Freeze / Blind Prediction

Task: `{TASK_ID}`

## Attempted

Recovered Salt1 PASSIVE-H2 runtime operator rows from the July 21 Salt1 external
BC recovery package, prepared the Fluid runtime-smoke command, and reran the
Salt1-4 freeze/blind-prediction decision from the resulting evidence state.

## Observed

Salt1 recovered rows cover cooling branch, downcomer, lower leg, and upcomer.
Junction is still absent from Salt1. The strict source-envelope/source-property
gate remains fail-closed with zero admission-release rows.

## Inferred

Salt1 runtime smoke can burn down the missing-runtime blocker, but it does not
by itself justify PASSIVE-H2 coefficient admission, final freeze, or blind-row
numeric predictions.

## Next Useful Actions

Recover Salt1 junction operator/source-envelope evidence and blind-row setup
operator rows before attempting a final Salt1-4 freeze and Salt2 +/-5Q /
`val_salt2` predictions.
"""
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    payload = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "changed_files": [
            rel(OUT),
            rel(Path("tools/analyze/build_passive_h2_salt1_runtime_unblock_freeze_blind_predict.py")),
            rel(Path("tools/analyze/test_passive_h2_salt1_runtime_unblock_freeze_blind_predict.py")),
            rel(STATUS),
            rel(JOURNAL),
            rel(IMPORT),
        ],
        "read_only_context": source_manifest_rows(),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": bool((RUNTIME_OUTPUT / "summary.json").exists()),
        "external_fluid_edit": False,
        "mutation_flags": {
            "native_solver_outputs_mutated": False,
            "registry_or_admission_mutated": False,
            "fluid_or_external_source_edit": False,
            "source_property_or_qwall_release": False,
            "admitted_final_candidate_freeze": False,
            "final_score_claim": False,
        },
        "decision": summary["decision"],
    }
    json_dump(IMPORT, payload)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    operator = recovered_operator_rows()
    targets = salt1_target_rows()
    recovery = recovery_provenance_rows()
    commands = command_rows()
    runtime = runtime_status_rows()
    four_case = four_case_runtime_evidence_rows()
    freeze = freeze_gate_rows()
    lock = coefficient_lock_rows()
    blind = blind_prediction_rows()

    csv_dump(out / "salt1_recovered_operator_rows_for_fluid.csv", ["case_id", "source_family", "external_bc_split_role", "original_external_bc_split_role", "diagnostic_use", "area_m2", "hA_W_K", "Ta_K", "Tsur_K", "emissivity", "candidate_id", "admission_or_score", "source_property_release", "numeric_q_loss_release", "runtime_CFD_mdot_used", "runtime_Qwall_used", "runtime_validation_temperature_used", "runtime_wallHeatFlux_used", "source_paths"], operator)
    csv_dump(out / "salt1_runtime_target_context.csv", ["case_id", "scenario_id", "radiation_on_expected_heat_ledger_delta_W", "passive_operator_full_on_expected_heat_ledger_delta_W", "protected_scoring", "target_status"], targets)
    csv_dump(out / "salt1_recovery_provenance_gate.csv", ["evidence_item", "status", "count_or_value", "release_ready", "reason", "evidence_path"], recovery)
    csv_dump(out / "command_manifest.csv", ["case_id", "working_directory", "command", "status", "scheduler_job_step", "stdout_log", "stderr_log"], commands)
    write_runtime_script(out)
    csv_dump(out / "salt1_runtime_smoke_status.csv", ["case_id", "output_root", "output_complete", "root_status_current_no_role_rad_off", "root_status_passive_h2_role_rad_off", "root_status_passive_h2_role_rad_on", "radiation_on_nonzero", "radiation_on_heat_ledger_delta_W", "radiation_target_delta_W", "protected_scoring", "source_property_release", "candidate_freeze", "decision"], runtime)
    csv_dump(out / "four_case_runtime_evidence.csv", ["candidate_id", "case_id", "split_role", "runtime_evidence_source", "runtime_completed", "accepted_roots", "radiation_on_nonzero", "radiation_on_heat_ledger_delta_W", "radiation_target_delta_W", "radiation_delta_over_target", "protected_scoring", "source_property_release", "candidate_freeze", "admissibility_role", "evidence_path"], four_case)
    csv_dump(out / "post_runtime_freeze_gate.csv", ["gate", "status", "count_or_value", "freeze_ready", "reason"], freeze)
    csv_dump(out / "coefficient_lock_manifest.csv", ["candidate_id", "lock_id", "requested_train_cases", "salt1_4_runtime_smoke_complete", "diagnostic_runtime_lock_created", "admitted_final_freeze_created", "coefficient_names", "coefficient_values", "reason"], lock)
    csv_dump(out / "blind_prediction_artifact.csv", ["candidate_id", "lock_id", "case_key", "final_scorecard_partition", "prediction_qoi", "prediction_available", "prediction_value", "score_emitted", "reason", "target_rows_available"], blind)
    csv_dump(out / "split_leakage_audit.csv", ["item", "role", "used_for_fit", "used_for_model_selection", "used_for_score", "status"], leakage_audit_rows())
    csv_dump(out / "source_manifest.csv", ["source_label", "source_path", "exists", "use", "mutated"], source_manifest_rows())
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrail_rows())

    runtime_complete = bool(runtime[0]["output_complete"])
    freeze_gate = freeze[0]["status"]
    decision = (
        "passive_h2_salt1_runtime_smoke_complete_freeze_blind_predictions_blocked_by_release_gates"
        if runtime_complete
        else "passive_h2_salt1_operator_recovered_runtime_smoke_ready_not_yet_run"
    )
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "candidate_id": "PASSIVE-H2-CAND001",
        "decision": decision,
        "salt1_operator_rows": len(operator),
        "salt1_source_family_coverage": f"{len({row['source_family'] for row in operator})}/5",
        "salt1_runtime_smoke_complete": runtime_complete,
        "salt1_runtime_roots_accepted": str(runtime[0]["root_status_current_no_role_rad_off"]) == "accepted"
        and str(runtime[0]["root_status_passive_h2_role_rad_off"]) == "accepted"
        and str(runtime[0]["root_status_passive_h2_role_rad_on"]) == "accepted",
        "salt1_radiation_on_heat_ledger_delta_W": runtime[0]["radiation_on_heat_ledger_delta_W"],
        "salt1_4_runtime_gate_status": freeze_gate,
        "strict_source_envelope_pass_rows": read_json(ROLE_FILTERED_GATE / "summary.json").get("strict_source_envelope_pass_rows", 0),
        "source_property_admission_release_ready_rows": read_json(ROLE_FILTERED_GATE / "summary.json").get("source_property_admission_release_ready_rows", 0),
        "diagnostic_runtime_lock_created": False,
        "admitted_final_freeze_created": False,
        "blind_prediction_rows": len(blind),
        "blind_numeric_prediction_rows_available": 0,
        "score_values_emitted": 0,
        "scheduler_action": runtime_complete,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "fluid_or_external_source_edit": False,
        "source_property_or_qwall_release": False,
        "final_score_claim": False,
        "runtime_leakage_relaxation": False,
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    write_status(summary)
    write_journal(summary)
    write_import(summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
