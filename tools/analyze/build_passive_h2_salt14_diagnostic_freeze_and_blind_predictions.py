#!/usr/bin/env python3
"""Attempt PASSIVE-H2 Salt1-4 diagnostic freeze and blind prediction handoff."""

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

TASK_ID = "TODO-PASSIVE-H2-SALT14-DIAGNOSTIC-FREEZE-AND-BLIND-PREDICTIONS-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_diagnostic_freeze_and_blind_predictions"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-salt14-diagnostic-freeze-and-blind-predictions.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_salt14_diagnostic_freeze_and_blind_predictions.json"

PREVIOUS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest"
SOURCE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke"
SOURCE_BASIS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"
SOURCE_PROPERTY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_source_property_exact_field_recovery_salt14"
NOMINAL_RELEASE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"
SCORECARD = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell"
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


def training_rows() -> list[dict[str, str]]:
    return read_csv(PREVIOUS / "training_availability.csv")


def blind_rows() -> list[dict[str, str]]:
    return read_csv(PREVIOUS / "blind_test_availability.csv")


def salt1_prediction_attempt_rows() -> list[dict[str, str]]:
    basis_rows = read_csv(SOURCE_BASIS / "passive_h2_source_backed_basis_table.csv")
    source_property_rows = read_csv(SOURCE_PROPERTY / "salt14_row_specific_release_matrix.csv")
    salt1_sp = next((row for row in source_property_rows if row.get("case_key") == "salt1_nominal"), {})
    train = {row["case_key"]: row for row in training_rows()}
    salt1_train = train.get("salt1_nominal", {})
    required = [
        (
            "case_row_passive_h2_operator",
            "false",
            "No Salt1 row exists in PASSIVE-H2 corrected operator or runtime-smoke outputs.",
            rel(PREVIOUS / "training_availability.csv"),
        ),
        (
            "row_specific_source_envelope",
            "false",
            salt1_sp.get("blocker", "missing row-specific Salt1 branch source-envelope evidence"),
            rel(SOURCE_PROPERTY / "salt14_row_specific_release_matrix.csv"),
        ),
        (
            "source_backed_family_basis",
            "false",
            f"source-backed family basis covers {len(basis_rows)} Salt2-4 aggregate family rows, not a Salt1 case row",
            rel(SOURCE_BASIS / "passive_h2_source_backed_basis_table.csv"),
        ),
        (
            "setup_only_runtime_result",
            salt1_train.get("passive_h2_runtime_evidence_available", "false"),
            salt1_train.get("blocker_or_status", "missing Salt1 setup-only runtime prediction"),
            rel(PREVIOUS / "training_availability.csv"),
        ),
    ]
    return [
        {
            "case_key": "salt1_nominal",
            "candidate_id": "PASSIVE-H2-CAND001",
            "required_evidence": name,
            "available": available,
            "status": "blocked" if available != "true" else "available",
            "reason": reason,
            "evidence_path": path,
        }
        for name, available, reason, path in required
    ]


def diagnostic_train_roster_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in training_rows():
        rows.append(
            {
                "case_key": row["case_key"],
                "case_id": row["case_id"],
                "candidate_id": "PASSIVE-H2-CAND001",
                "requested_training_row": "true",
                "numeric_passive_h2_prediction_available": row["passive_h2_prediction_available"],
                "setup_only_runtime_prediction_available": row["passive_h2_runtime_evidence_available"],
                "fit_ready_now": row["fit_ready_now"],
                "source_property_gate_status": row["source_property_gate_status"],
                "blocker_or_status": row["blocker_or_status"],
                "passive_h2_corrected_outer_total_W": row["passive_h2_corrected_outer_total_W"],
                "fluid_runtime_mdot_kg_s": row["fluid_runtime_mdot_kg_s"],
                "fluid_runtime_qambient_W": row["fluid_runtime_qambient_W"],
                "evidence_source": row["evidence_source"],
            }
        )
    return rows


def coefficient_lock_rows() -> list[dict[str, str]]:
    train = diagnostic_train_roster_rows()
    missing_prediction = [row["case_key"] for row in train if row["numeric_passive_h2_prediction_available"] != "true"]
    fit_blocked = [row["case_key"] for row in train if row["fit_ready_now"] != "true"]
    release_summary = read_json(SOURCE_GATE / "summary.json")
    can_lock = not missing_prediction and not fit_blocked and release_summary.get("freeze_ready_candidates") == 1
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "lock_id": "PASSIVE_H2_SALT14_DIAGNOSTIC_LOCK_TBD",
            "requested_train_cases": "salt1_nominal;salt2_jin_nominal;salt3_jin_nominal;salt4_nominal",
            "coefficient_family": "passive_h2_outer_boundary_operator",
            "coefficient_names": "none_emitted",
            "coefficient_values": "",
            "salt1_4_only_training": "true",
            "diagnostic_lock_created": str(can_lock).lower(),
            "admitted_final_freeze_created": "false",
            "reason": (
                "blocked: missing Salt1 PASSIVE-H2 setup-only prediction and source/property/freezing gates remain closed"
                if not can_lock
                else "all inputs available for diagnostic lock"
            ),
            "missing_prediction_cases": ";".join(missing_prediction),
            "fit_blocked_cases": ";".join(fit_blocked),
            "source_property_release_ready_rows": str(release_summary.get("source_property_release_ready_rows", 0)),
            "freeze_ready_candidates": str(release_summary.get("freeze_ready_candidates", 0)),
        }
    ]


def blind_prediction_rows() -> list[dict[str, str]]:
    qois = [
        "mdot_kg_s",
        "pressure_residual_Pa",
        "qambient_total_W",
        "qhx_total_W",
        "all_probe_temperature_rmse_K_proxy",
        "tp_temperature_rows",
        "tw_temperature_rows",
    ]
    lock_created = coefficient_lock_rows()[0]["diagnostic_lock_created"] == "true"
    rows: list[dict[str, str]] = []
    for case in blind_rows():
        for qoi in qois:
            rows.append(
                {
                    "candidate_id": "PASSIVE-H2-CAND001",
                    "lock_id": "PASSIVE_H2_SALT14_DIAGNOSTIC_LOCK_TBD",
                    "case_key": case["case_key"],
                    "final_scorecard_partition": case["final_scorecard_partition"],
                    "prediction_qoi": qoi,
                    "prediction_available": "false" if not lock_created else "true",
                    "prediction_value": "",
                    "prediction_units": "",
                    "target_rows_available": case["target_rows_available"],
                    "target_status": case["target_status"],
                    "score_emitted": "false",
                    "reason": "no Salt1-4 coefficient lock exists; blind prediction is intentionally blocked",
                    "target_source": case["target_source"],
                }
            )
    return rows


def leakage_audit_rows() -> list[dict[str, str]]:
    return [
        {"item": "Salt1-4 nominal", "role": "training_contract", "used_for_fit": "false", "used_for_model_selection": "false", "used_for_score": "false", "status": "no fit performed because Salt1 and gates are incomplete"},
        {"item": "Salt2 +/-5Q", "role": "blind_holdout_prediction_target", "used_for_fit": "false", "used_for_model_selection": "false", "used_for_score": "false", "status": "target rows read only for availability; no prediction or score emitted"},
        {"item": "val_salt2", "role": "external_test_prediction_target", "used_for_fit": "false", "used_for_model_selection": "false", "used_for_score": "false", "status": "target rows read only for availability; no prediction or score emitted"},
        {"item": "CFD mdot / realized wallHeatFlux / validation TP-TW / imposed cooler duty / residual fills", "role": "forbidden_runtime_inputs", "used_for_fit": "false", "used_for_model_selection": "false", "used_for_score": "false", "status": "not consumed"},
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "action": "Recover Salt1 row-specific external-boundary source envelope and PASSIVE-H2 operator rows.",
            "acceptance": "Salt1 has five source-family rows with area, hA, Ta/Tsur, emissivity/layer basis, and parent-segment mapping from setup sources.",
        },
        {
            "priority": "2",
            "action": "Run Salt1 through the same PASSIVE-H2 runtime-smoke path used for Salt2-4 under a scheduler-authorized row.",
            "acceptance": "Accepted Salt1 roots and qambient/qhx/mdot outputs exist with forbidden runtime-input flags false.",
        },
        {
            "priority": "3",
            "action": "Rerun source/property and same-QOI release gates on Salt1-4.",
            "acceptance": "Fit-ready rows are nonzero and the diagnostic/final lock decision can be revisited without protected rows.",
        },
        {
            "priority": "4",
            "action": "Freeze coefficients from Salt1-4 only, then generate blind PM5 and val_salt2 predictions before opening targets for scoring.",
            "acceptance": "One immutable coefficient manifest and one prediction artifact exist; holdout and external scores are reported separately with no retuning.",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("previous_train_test_gate", PREVIOUS / "summary.json"),
        ("previous_training_availability", PREVIOUS / "training_availability.csv"),
        ("previous_blind_availability", PREVIOUS / "blind_test_availability.csv"),
        ("source_property_gate_rerun", SOURCE_GATE / "summary.json"),
        ("source_property_release_gate", SOURCE_GATE / "source_property_release_gate.csv"),
        ("source_backed_basis", SOURCE_BASIS / "passive_h2_source_backed_basis_table.csv"),
        ("source_property_exact_recovery", SOURCE_PROPERTY / "salt14_row_specific_release_matrix.csv"),
        ("nominal_train_release_preflight", NOMINAL_RELEASE / "nominal_train_release_audit.csv"),
        ("scorecard_freeze_contract", SCORECARD / "model_freeze_contract.csv"),
        ("pm5_targets", PM5 / "salt2_pm5_holdout_metrics.csv"),
        ("val_salt2_targets", VAL_SALT2 / "val_salt2_external_score_targets.csv"),
    ]
    return [{"source_label": label, "source_path": rel(path), "exists": str(path.exists()).lower(), "use": "read_only_input", "mutated": "false"} for label, path in sources]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_or_admission_mutated", "value": "false"},
        {"guardrail": "scheduler_action", "value": "false"},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "value": "false"},
        {"guardrail": "Fluid_or_external_edit", "value": "false"},
        {"guardrail": "thesis_current_or_latex_edit", "value": "false"},
        {"guardrail": "admitted_final_coefficient_admission", "value": "false"},
        {"guardrail": "admitted_final_candidate_freeze", "value": "false"},
        {"guardrail": "source_property_or_qwall_release", "value": "false"},
        {"guardrail": "protected_row_fitting_or_model_selection", "value": "false"},
        {"guardrail": "final_score_claim", "value": "false"},
        {"guardrail": "runtime_leakage_relaxation", "value": "false"},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
provenance:
  - {rel(out / "summary.json")}
tags: [PASSIVE-H2, Salt1-4, diagnostic-freeze, blind-predictions]
---
# PASSIVE-H2 Salt1-4 Diagnostic Freeze And Blind Prediction Attempt

Decision: `{summary["decision"]}`.

The requested sequence was attempted in the strict order:

1. Generate missing Salt1 setup-only PASSIVE-H2 prediction.
2. Freeze a Salt1-4-only coefficient set.
3. Produce Salt2 +/-5Q and `val_salt2` blind predictions.

It stops at step 1. Existing evidence has Salt2-4 PASSIVE-H2 runtime/support
rows, but no Salt1 PASSIVE-H2 operator/runtime row and no Salt1 row-specific
source-envelope release. Because the four-row training set is incomplete, no
coefficient values are emitted and no blind numeric predictions are produced.

Tables:

- `salt1_setup_prediction_attempt.csv`
- `diagnostic_train_roster.csv`
- `coefficient_lock_manifest.csv`
- `blind_prediction_artifact.csv`
- `split_leakage_audit.csv`
- `next_unblock_actions.csv`
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
tags: [PASSIVE-H2, diagnostic-freeze]
---
# {TASK_ID}

Task: `{TASK_ID}`

## Objective

Generate the missing Salt1 PASSIVE-H2 setup-only runtime prediction, then freeze
a Salt1-4-only coefficient set before producing Salt2 +/-5Q and `val_salt2`
predictions.

## Outcome

Decision: `{summary["decision"]}`. The sequence is blocked before coefficient
freeze because Salt1 lacks a PASSIVE-H2 setup-only prediction/operator row and
source/property release remains closed.

## Changes Made

- `{rel(OUT)}`
- `{rel(Path("tools/analyze/build_passive_h2_salt14_diagnostic_freeze_and_blind_predictions.py"))}`
- `{rel(Path("tools/analyze/test_passive_h2_salt14_diagnostic_freeze_and_blind_predictions.py"))}`
- `{rel(IMPORT)}`

## Validation

- `python3.11 tools/analyze/test_passive_h2_salt14_diagnostic_freeze_and_blind_predictions.py`
- `python3.11 tools/analyze/build_passive_h2_salt14_diagnostic_freeze_and_blind_predictions.py`

## Guardrails

No native outputs, registry/admission state, scheduler state, Fluid/external
repos, thesis current/LaTeX, source/property/Qwall release, admitted coefficient
freeze, protected-row fitting/model selection, final score, or runtime-leakage
rules were changed.
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
tags: [PASSIVE-H2, Salt1, blind-prediction]
---
# PASSIVE-H2 Salt1-4 Diagnostic Freeze And Blind Prediction Attempt

Task: `{TASK_ID}`

## Attempted

I tried to advance the requested sequence from the completed train/test gate:
fill Salt1, lock Salt1-4 coefficients, then emit blind PM5 and `val_salt2`
predictions.

## Observed

Salt2-4 have PASSIVE-H2 prediction/runtime evidence. Salt1 has only source
property blocker evidence: it lacks row-specific source-envelope evidence and
does not appear in the PASSIVE-H2 corrected operator or runtime-smoke outputs.
The latest source/property rerun reports `0` source-property release-ready rows
and `0` freeze-ready candidates.

## Inferred

A Salt1-4 coefficient freeze cannot be made rigorous from the current evidence.
Fitting on Salt2-4 would not satisfy the requested training set and would create
a misleading blind prediction artifact.

## Next Useful Actions

Recover Salt1 setup/operator rows, run Salt1 through the same PASSIVE-H2 runtime
smoke path as Salt2-4 under an explicit compute row, rerun source/property and
same-QOI gates, then freeze and predict blind rows once before scoring.
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
            rel(Path("tools/analyze/build_passive_h2_salt14_diagnostic_freeze_and_blind_predictions.py")),
            rel(Path("tools/analyze/test_passive_h2_salt14_diagnostic_freeze_and_blind_predictions.py")),
            rel(STATUS),
            rel(JOURNAL),
            rel(IMPORT),
        ],
        "read_only_context": source_manifest_rows(),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "mutation_flags": {
            "native_solver_outputs_mutated": False,
            "registry_or_admission_mutated": False,
            "scheduler_action": False,
            "fluid_or_external_edit": False,
            "source_property_or_qwall_release": False,
            "admitted_final_candidate_freeze": False,
            "final_score_claim": False,
        },
        "decision": summary["decision"],
    }
    json_dump(IMPORT, payload)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    salt1_attempt = salt1_prediction_attempt_rows()
    train = diagnostic_train_roster_rows()
    lock = coefficient_lock_rows()
    blind = blind_prediction_rows()
    leakage = leakage_audit_rows()
    actions = next_action_rows()
    sources = source_manifest_rows()
    guardrails = guardrail_rows()

    csv_dump(out / "salt1_setup_prediction_attempt.csv", ["case_key", "candidate_id", "required_evidence", "available", "status", "reason", "evidence_path"], salt1_attempt)
    csv_dump(out / "diagnostic_train_roster.csv", ["case_key", "case_id", "candidate_id", "requested_training_row", "numeric_passive_h2_prediction_available", "setup_only_runtime_prediction_available", "fit_ready_now", "source_property_gate_status", "blocker_or_status", "passive_h2_corrected_outer_total_W", "fluid_runtime_mdot_kg_s", "fluid_runtime_qambient_W", "evidence_source"], train)
    csv_dump(out / "coefficient_lock_manifest.csv", ["candidate_id", "lock_id", "requested_train_cases", "coefficient_family", "coefficient_names", "coefficient_values", "salt1_4_only_training", "diagnostic_lock_created", "admitted_final_freeze_created", "reason", "missing_prediction_cases", "fit_blocked_cases", "source_property_release_ready_rows", "freeze_ready_candidates"], lock)
    csv_dump(out / "blind_prediction_artifact.csv", ["candidate_id", "lock_id", "case_key", "final_scorecard_partition", "prediction_qoi", "prediction_available", "prediction_value", "prediction_units", "target_rows_available", "target_status", "score_emitted", "reason", "target_source"], blind)
    csv_dump(out / "split_leakage_audit.csv", ["item", "role", "used_for_fit", "used_for_model_selection", "used_for_score", "status"], leakage)
    csv_dump(out / "next_unblock_actions.csv", ["priority", "action", "acceptance"], actions)
    csv_dump(out / "source_manifest.csv", ["source_label", "source_path", "exists", "use", "mutated"], sources)
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "candidate_id": "PASSIVE-H2-CAND001",
        "decision": "passive_h2_salt14_freeze_and_blind_predictions_blocked_missing_salt1_no_lock_no_predictions",
        "salt1_required_evidence_rows": len(salt1_attempt),
        "salt1_available_required_evidence_rows": sum(row["available"] == "true" for row in salt1_attempt),
        "requested_train_rows": len(train),
        "train_numeric_prediction_rows_available": sum(row["numeric_passive_h2_prediction_available"] == "true" for row in train),
        "train_setup_runtime_rows_available": sum(row["setup_only_runtime_prediction_available"] == "true" for row in train),
        "train_fit_ready_rows": sum(row["fit_ready_now"] == "true" for row in train),
        "diagnostic_lock_created": False,
        "admitted_final_freeze_created": False,
        "blind_prediction_rows": len(blind),
        "blind_numeric_prediction_rows_available": 0,
        "score_values_emitted": 0,
        "source_property_release": False,
        "qwall_release": False,
        "candidate_freeze": False,
        "final_score_claim": False,
        "protected_rows_used_for_fit_or_selection": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
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
