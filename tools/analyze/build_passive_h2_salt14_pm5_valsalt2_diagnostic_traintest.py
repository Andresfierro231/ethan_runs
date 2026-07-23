#!/usr/bin/env python3
"""Build a guarded PASSIVE-H2 Salt1-4 train / PM5 + val_salt2 test package.

This script intentionally does not fit coefficients unless complete legal
training rows and frozen blind-row predictions already exist in prior artifacts.
Its purpose is to make the requested train/test status explicit and reproducible.
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

TASK_ID = "TODO-PASSIVE-H2-SALT14-PM5-VALSALT2-DIAGNOSTIC-TRAINTEST-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-salt14-pm5-valsalt2-diagnostic-traintest.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.json"

SPLIT_POLICY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv"
SCORECARD = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell"
PASSIVE_PROTO = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_p1d_bulk_cv_h2_train_only_thesis_prototype"
PASSIVE_MULTI = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke"
PASSIVE_RUNTIME_IMPL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
PASSIVE_SMOKE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt34_diagnostic_runtime_smoke"
PASSIVE_SPLIT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_mapping_split_uq_preflight"
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


def yes(value: str | None) -> bool:
    return (value or "").strip().lower() in {"yes", "true", "1"}


def case_split_contract_rows() -> list[dict[str, str]]:
    rows = read_csv(SCORECARD / "case_partition_contract.csv")
    wanted = {
        "salt1_nominal",
        "salt2_jin_nominal",
        "salt3_jin_nominal",
        "salt4_nominal",
        "salt2_lo5q",
        "salt2_hi5q",
        "val_salt2",
    }
    output: list[dict[str, str]] = []
    for row in rows:
        if row.get("case_key") not in wanted:
            continue
        output.append(
            {
                "case_key": row.get("case_key", ""),
                "source_key": row.get("source_key", ""),
                "requested_role": "train" if row.get("final_scorecard_partition") == "train_nominal" else "test_score_only",
                "final_scorecard_partition": row.get("final_scorecard_partition", ""),
                "fit_allowed": row.get("fit_allowed", ""),
                "model_selection_allowed": row.get("model_selection_allowed", ""),
                "score_allowed": row.get("score_allowed", ""),
                "release_gate": row.get("release_gate", ""),
                "shell_score_status": row.get("shell_score_status", ""),
                "target_evidence_status": row.get("target_evidence_status", ""),
                "guardrail": row.get("guardrail", ""),
                "source_property_gate_status": row.get("source_property_gate_status", ""),
                "source_property_gate_reason": row.get("source_property_gate_reason", ""),
            }
        )
    order = {
        "salt1_nominal": 0,
        "salt2_jin_nominal": 1,
        "salt3_jin_nominal": 2,
        "salt4_nominal": 3,
        "salt2_lo5q": 4,
        "salt2_hi5q": 5,
        "val_salt2": 6,
    }
    output.sort(key=lambda item: order[item["case_key"]])
    return output


def passive_runtime_by_case() -> dict[str, dict[str, str]]:
    by_case: dict[str, dict[str, str]] = {}

    for row in read_csv(PASSIVE_MULTI / "case_corrected_radiation_summary.csv"):
        case_key = {
            "salt_2": "salt2_jin_nominal",
            "salt_3": "salt3_jin_nominal",
            "salt_4": "salt4_nominal",
        }.get(row.get("case_id", ""))
        if not case_key:
            continue
        by_case.setdefault(case_key, {}).update(
            {
                "passive_h2_corrected_outer_total_W": row.get("corrected_outer_surface_total_W", ""),
                "passive_h2_radiation_W": row.get("corrected_outer_surface_radiation_W", ""),
                "passive_h2_convection_W": row.get("corrected_outer_surface_convection_W", ""),
                "legacy_qambient_context_W": row.get("baseline_qambient_total_W", ""),
                "mdot_context_kg_s": row.get("mdot_model_kg_s", ""),
                "prediction_source": rel(PASSIVE_MULTI / "case_corrected_radiation_summary.csv"),
                "prediction_kind": "corrected_operator_context_no_score",
            }
        )

    smoke = read_csv(PASSIVE_RUNTIME_IMPL / "runtime_smoke_summary.csv")
    accepted = [
        row
        for row in smoke
        if row.get("run_label") == "passive_h2_role_rad_on"
        and row.get("root_status") == "accepted"
        and row.get("case") == "Salt 2"
    ]
    for row in accepted:
        by_case.setdefault("salt2_jin_nominal", {}).update(
            {
                "fluid_runtime_mdot_kg_s": row.get("mdot_kg_s", ""),
                "fluid_runtime_qambient_W": row.get("qambient_total_W", ""),
                "fluid_runtime_qhx_W": row.get("qhx_total_W", ""),
                "fluid_runtime_start_temperature_K": row.get("start_temperature_K", ""),
                "fluid_runtime_end_temperature_K": row.get("end_temperature_K", ""),
                "fluid_runtime_status": "accepted_non_scoring_train_only_smoke",
                "fluid_runtime_source": rel(PASSIVE_RUNTIME_IMPL / "runtime_smoke_summary.csv"),
            }
        )

    smoke = read_csv(PASSIVE_SMOKE / "runtime_smoke_qoi_rows.csv")
    accepted = [
        row
        for row in smoke
        if row.get("run_label") == "passive_h2_role_rad_on"
        and row.get("root_status") == "accepted"
        and row.get("case_id") in {"salt_3", "salt_4"}
    ]
    for row in accepted:
        case_key = {"salt_3": "salt3_jin_nominal", "salt_4": "salt4_nominal"}[row["case_id"]]
        by_case.setdefault(case_key, {}).update(
            {
                "fluid_runtime_mdot_kg_s": row.get("mdot_kg_s", ""),
                "fluid_runtime_qambient_W": row.get("qambient_total_W", ""),
                "fluid_runtime_qhx_W": row.get("qhx_total_W", ""),
                "fluid_runtime_start_temperature_K": row.get("start_temperature_K", ""),
                "fluid_runtime_end_temperature_K": row.get("end_temperature_K", ""),
                "fluid_runtime_status": "accepted_non_scoring_diagnostic",
                "fluid_runtime_source": rel(PASSIVE_SMOKE / "runtime_smoke_qoi_rows.csv"),
            }
        )

    return by_case


def training_availability_rows() -> list[dict[str, str]]:
    split_rows = [row for row in case_split_contract_rows() if row["requested_role"] == "train"]
    runtime = passive_runtime_by_case()
    preflight_rows = {row.get("case_id"): row for row in read_csv(PASSIVE_SPLIT / "case_split_disposition.csv")}
    output: list[dict[str, str]] = []

    aliases = {
        "salt1_nominal": "salt_1",
        "salt2_jin_nominal": "salt_2",
        "salt3_jin_nominal": "salt_3",
        "salt4_nominal": "salt_4",
    }
    for row in split_rows:
        case_key = row["case_key"]
        evidence = runtime.get(case_key, {})
        split_case = aliases[case_key]
        preflight = preflight_rows.get(split_case, {})
        has_operator = bool(evidence)
        fit_allowed_now = (
            has_operator
            and row["fit_allowed"] == "yes"
            and row["model_selection_allowed"] == "yes"
            and row["source_property_gate_status"] in {"", "pass"}
        )
        if case_key == "salt1_nominal":
            blocker = "missing_passive_h2_runtime_prediction_and_row_specific_source_envelope"
        elif row["fit_allowed"] != "yes":
            blocker = "source_property_policy_blocks_fit"
        elif not has_operator:
            blocker = "missing_passive_h2_runtime_prediction"
        else:
            blocker = "available_as_diagnostic_context_but_not_fit_release_ready"
        output.append(
            {
                "case_key": case_key,
                "case_id": split_case,
                "requested_train": "true",
                "canonical_training_row": "true",
                "passive_h2_prediction_available": str(has_operator).lower(),
                "passive_h2_runtime_evidence_available": str(bool(evidence.get("fluid_runtime_status"))).lower(),
                "fit_allowed_by_scorecard_now": row["fit_allowed"],
                "model_selection_allowed_by_scorecard_now": row["model_selection_allowed"],
                "source_property_gate_status": row["source_property_gate_status"],
                "preflight_disposition": preflight.get("split_disposition", ""),
                "fit_ready_now": str(fit_allowed_now).lower(),
                "blocker_or_status": blocker,
                "passive_h2_corrected_outer_total_W": evidence.get("passive_h2_corrected_outer_total_W", ""),
                "passive_h2_radiation_W": evidence.get("passive_h2_radiation_W", ""),
                "legacy_qambient_context_W": evidence.get("legacy_qambient_context_W", ""),
                "fluid_runtime_mdot_kg_s": evidence.get("fluid_runtime_mdot_kg_s", ""),
                "fluid_runtime_qambient_W": evidence.get("fluid_runtime_qambient_W", ""),
                "evidence_source": evidence.get("fluid_runtime_source") or evidence.get("prediction_source", ""),
            }
        )
    return output


def blind_test_availability_rows() -> list[dict[str, str]]:
    split_rows = [row for row in case_split_contract_rows() if row["requested_role"] == "test_score_only"]
    pm5_metrics = read_csv(PM5 / "salt2_pm5_holdout_metrics.csv")
    pm5_counts = {
        "salt2_lo5q": sum(1 for row in pm5_metrics if row.get("case_key") == "salt2_lo5q"),
        "salt2_hi5q": sum(1 for row in pm5_metrics if row.get("case_key") == "salt2_hi5q"),
    }
    val_targets = read_csv(VAL_SALT2 / "val_salt2_external_score_targets.csv")
    output: list[dict[str, str]] = []
    for row in split_rows:
        case_key = row["case_key"]
        if case_key in pm5_counts:
            target_rows = pm5_counts[case_key]
            target_source = rel(PM5 / "salt2_pm5_holdout_metrics.csv")
            target_status = "pm5_diagnostic_targets_available_score_only"
        else:
            target_rows = len(val_targets)
            target_source = rel(VAL_SALT2 / "val_salt2_external_score_targets.csv")
            target_status = "external_score_targets_available_score_only"
        output.append(
            {
                "case_key": case_key,
                "requested_test": "true",
                "final_scorecard_partition": row["final_scorecard_partition"],
                "fit_allowed": row["fit_allowed"],
                "model_selection_allowed": row["model_selection_allowed"],
                "score_allowed_after_freeze_or_gate": row["score_allowed"],
                "release_gate": row["release_gate"],
                "target_rows_available": str(target_rows),
                "target_status": target_status,
                "passive_h2_frozen_prediction_available": "false",
                "score_ready_now": "false",
                "blocker_or_status": "missing_admitted_final_freeze_and_passive_h2_blind_predictions",
                "target_source": target_source,
                "prediction_source": "",
            }
        )
    return output


def requested_score_shell_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    qois = [
        ("loop_mdot_abs_error_pct", "case_scalar"),
        ("all_probe_temperature_rmse_K", "sensor_temperature"),
        ("tp_sensor_rmse_K", "sensor_temperature"),
        ("tw_sensor_rmse_K", "sensor_temperature"),
        ("pressure_streamwise_rmse_Pa", "pressure_streamwise_map"),
        ("thermal_section_heat_abs_residual_W", "thermal_section_and_junction"),
    ]
    for case in blind_test_availability_rows():
        for qoi, target_type in qois:
            rows.append(
                {
                    "candidate_id": "PASSIVE-H2-CAND001",
                    "case_key": case["case_key"],
                    "final_scorecard_partition": case["final_scorecard_partition"],
                    "qoi": qoi,
                    "target_type": target_type,
                    "prediction_available": "false",
                    "target_available": "true" if int(case["target_rows_available"]) > 0 else "false",
                    "score_emitted": "false",
                    "score_value": "",
                    "claim_scope": "requested_holdout_external_test_shell_no_score",
                    "reason": "blind row requires admitted frozen PASSIVE-H2 predictions before scoring; target rows are score-only and not fit/model-selection inputs",
                }
            )
    return rows


def fit_and_score_decision_rows() -> list[dict[str, str]]:
    train = training_availability_rows()
    blind = blind_test_availability_rows()
    fit_ready = sum(1 for row in train if row["fit_ready_now"] == "true")
    train_predictions = sum(1 for row in train if row["passive_h2_prediction_available"] == "true")
    blind_predictions = sum(1 for row in blind if row["passive_h2_frozen_prediction_available"] == "true")
    decision = "blocked"
    reason = (
        "requested Salt1-4 PASSIVE-H2 training is not legal/complete: Salt1 lacks a PASSIVE-H2 runtime prediction, "
        "all Salt1-4 fit rows are blocked by source/property policy in the final scorecard shell, and Salt2 +/-5Q plus "
        "val_salt2 lack admitted frozen PASSIVE-H2 prediction artifacts"
    )
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "requested_train_cases": "salt1_nominal;salt2_jin_nominal;salt3_jin_nominal;salt4_nominal",
            "requested_test_cases": "salt2_lo5q;salt2_hi5q;val_salt2",
            "train_prediction_rows_available": str(train_predictions),
            "train_fit_ready_rows": str(fit_ready),
            "blind_prediction_rows_available": str(blind_predictions),
            "score_values_emitted": "0",
            "coefficient_fit_performed": "false",
            "protected_rows_used_for_fit_or_selection": "false",
            "decision": decision,
            "reason": reason,
        }
    ]


def leakage_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "input_or_action": "Salt1-4 nominal rows",
            "role": "requested_training",
            "used_for_fit": "false",
            "used_for_model_selection": "false",
            "used_for_score": "false",
            "status": "fit blocked pending complete PASSIVE-H2 runtime evidence and source/property release",
        },
        {
            "input_or_action": "Salt2 +/-5Q PM5 target rows",
            "role": "requested_holdout_test",
            "used_for_fit": "false",
            "used_for_model_selection": "false",
            "used_for_score": "false",
            "status": "target evidence exists, but no admitted frozen PASSIVE-H2 prediction artifact exists",
        },
        {
            "input_or_action": "val_salt2 external target rows",
            "role": "requested_external_test",
            "used_for_fit": "false",
            "used_for_model_selection": "false",
            "used_for_score": "false",
            "status": "external target evidence exists, but no admitted frozen PASSIVE-H2 prediction artifact exists",
        },
        {
            "input_or_action": "CFD mdot, realized wallHeatFlux, validation temperatures, imposed cooler duty, residual fills",
            "role": "forbidden_runtime_inputs",
            "used_for_fit": "false",
            "used_for_model_selection": "false",
            "used_for_score": "false",
            "status": "not consumed by this package",
        },
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "action": "Create Salt1 PASSIVE-H2 setup-only runtime prediction row.",
            "why": "Salt1 is required by the requested Salt1-4 training set but currently has only blocker/source-envelope evidence.",
            "acceptance": "Salt1 appears in the same PASSIVE-H2 runtime/prediction table as Salt2-4 without CFD mdot, realized wallHeatFlux, validation TP/TW, imposed cooler duty, or residual fills.",
        },
        {
            "priority": "2",
            "action": "Resolve Salt1-4 source/property release or mark the train/test run explicitly as non-admitted diagnostic.",
            "why": "The final scorecard shell sets fit_allowed=no for Salt1-4 under the current source/property policy.",
            "acceptance": "A source/property release package changes the gate, or the training run remains labeled diagnostic-only.",
        },
        {
            "priority": "3",
            "action": "Generate frozen PASSIVE-H2 predictions for Salt2 +/-5Q and val_salt2 after train coefficients are frozen.",
            "why": "PM5 and val_salt2 target rows exist, but scoring cannot begin until predictions exist and are frozen before target use.",
            "acceptance": "A manifest records coefficients trained only on Salt1-4 and a prediction file for all blind rows.",
        },
        {
            "priority": "4",
            "action": "Score blind rows once, without coefficient changes, and report holdout and external-test claims separately.",
            "why": "Salt2 +/-5Q and val_salt2 answer different transfer questions and should not be pooled as training evidence.",
            "acceptance": "Separate holdout and external-test scorecards with leakage audit and no post-score retuning.",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("canonical_split_policy", SPLIT_POLICY),
        ("scorecard_case_partition", SCORECARD / "case_partition_contract.csv"),
        ("scorecard_holdout_release_gates", SCORECARD / "holdout_release_gates.csv"),
        ("scorecard_model_freeze_contract", SCORECARD / "model_freeze_contract.csv"),
        ("scorecard_prediction_join_shell", SCORECARD / "prediction_join_shell.csv"),
        ("passive_h2_train_prototype", PASSIVE_PROTO / "train_context_prototype_outputs.csv"),
        ("passive_h2_corrected_radiation_summary", PASSIVE_MULTI / "case_corrected_radiation_summary.csv"),
        ("passive_h2_salt2_runtime_implementation", PASSIVE_RUNTIME_IMPL / "runtime_smoke_summary.csv"),
        ("passive_h2_split_preflight", PASSIVE_SPLIT / "case_split_disposition.csv"),
        ("passive_h2_salt34_runtime_smoke", PASSIVE_SMOKE / "runtime_smoke_qoi_rows.csv"),
        ("passive_h2_salt34_heat_delta", PASSIVE_SMOKE / "heat_ledger_delta_by_case.csv"),
        ("salt2_pm5_holdout_metrics", PM5 / "salt2_pm5_holdout_metrics.csv"),
        ("val_salt2_external_targets", VAL_SALT2 / "val_salt2_external_score_targets.csv"),
    ]
    return [
        {
            "source_label": label,
            "source_path": rel(path),
            "exists": str(path.exists()).lower(),
            "use": "read_only_input",
            "mutated": "false",
        }
        for label, path in sources
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_or_admission_mutated", "value": "false"},
        {"guardrail": "scheduler_action", "value": "false"},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "value": "false"},
        {"guardrail": "Fluid_or_external_edit", "value": "false"},
        {"guardrail": "thesis_current_or_latex_edit", "value": "false"},
        {"guardrail": "protected_row_fitting_or_model_selection", "value": "false"},
        {"guardrail": "source_property_or_qwall_release", "value": "false"},
        {"guardrail": "candidate_freeze", "value": "false"},
        {"guardrail": "final_score_claim", "value": "false"},
        {"guardrail": "runtime_leakage_relaxation", "value": "false"},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py
  task_id: {TASK_ID}
tags: [PASSIVE-H2, predictive-model, train-test, Salt1-4, PM5, val_salt2]
related:
  - {rel(out / "summary.json")}
  - {rel(out / "training_availability.csv")}
  - {rel(out / "blind_test_availability.csv")}
---
# PASSIVE-H2 Salt1-4 / PM5 / val_salt2 Diagnostic Train-Test Package

Decision: `{summary["decision"]}`.

This package implements the requested train/test pass as a strict diagnostic
ledger. It does not fit coefficients, freeze a candidate, or emit holdout /
external scores because the current repository evidence is incomplete for a
runtime-legal admitted PASSIVE-H2 train/test:

- Salt1 is required for the Salt1-4 training set but lacks a PASSIVE-H2 runtime
  prediction row.
- Salt1-4 final-scorecard fit and model-selection gates remain blocked by the
  source/property policy.
- Salt2 +/-5Q and `val_salt2` have target evidence, but no admitted frozen
  PASSIVE-H2 prediction artifact exists for those blind rows.

Tables:

- `case_split_contract.csv`: requested train/test roles and scorecard gates.
- `training_availability.csv`: Salt1-4 PASSIVE-H2 evidence and fit readiness.
- `blind_test_availability.csv`: PM5 / external target evidence and prediction
  readiness.
- `requested_score_shell.csv`: requested QOI rows with no score emitted.
- `split_leakage_audit.csv`: proof that holdout/external rows were not used for
  fit or model selection.
- `next_action_queue.csv`: shortest path to make this train/test executable.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py
  task_id: {TASK_ID}
tags: [status, PASSIVE-H2, train-test]
related:
  - {rel(OUT / "summary.json")}
---
# {TASK_ID}

Task: `{TASK_ID}`

## Objective

Build the user-requested PASSIVE-H2 Salt1-4 train and Salt2 +/-5Q plus
`val_salt2` test diagnostic package.

## Outcome

Decision: `{summary["decision"]}`. The run is blocked for admitted training and
scoring, so the package emits availability ledgers and a score shell rather than
fitted coefficients or score values.

## Changes Made

- `{rel(OUT)}`
- `{rel(Path("tools/analyze/build_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py"))}`
- `{rel(Path("tools/analyze/test_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py"))}`
- `{rel(IMPORT)}`

## Validation

- `python3.11 tools/analyze/test_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py`
- `python3.11 tools/analyze/build_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py`

## Blockers

- Salt1 PASSIVE-H2 runtime prediction is missing.
- Salt1-4 source/property fit gates are closed.
- Salt2 +/-5Q and `val_salt2` lack admitted frozen PASSIVE-H2 predictions.

## Guardrails

Native solver outputs, registry/admission state, scheduler state, Fluid/external
repos, thesis current/LaTeX files, protected-row fitting/model selection,
source/property/Qwall release, coefficient admission, candidate freeze, and
final-score claims were not changed.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py
  task_id: {TASK_ID}
tags: [journal, PASSIVE-H2, predictive-model]
related:
  - {rel(OUT / "summary.json")}
task: {TASK_ID}
---
# PASSIVE-H2 Salt1-4 / PM5 / val_salt2 Diagnostic Train-Test

Task: `{TASK_ID}`

## Attempted

I assembled the requested Salt1-4 training and Salt2 +/-5Q plus `val_salt2`
testing contract from the canonical split policy, final scorecard shell,
completed PASSIVE-H2 prototype/smoke packages, PM5 target package, and
`val_salt2` external target package.

## Observed

- Canonical training rows are Salt1-4 nominal.
- Completed PASSIVE-H2 runtime/prediction evidence exists for Salt2-4 only.
- Salt2 +/-5Q and `val_salt2` target evidence exists, but no admitted frozen
  PASSIVE-H2 prediction artifact exists for those rows.
- The final scorecard shell keeps fit/model selection closed under the current
  source/property policy.

## Inferred

The requested train/test cannot be claimed as an admitted predictive score yet.
The rigorous next step is not to reduce the training set to Salt2-4, because
that would no longer be the requested Salt1-4 fit and would weaken the split
contract.

## Next Useful Actions

1. Generate Salt1 PASSIVE-H2 setup-only runtime prediction evidence.
2. Resolve or explicitly waive source/property release only in a diagnostic
   package.
3. Freeze coefficients from Salt1-4 before creating blind PM5 and `val_salt2`
   PASSIVE-H2 predictions.
4. Score holdout and external-test rows separately with no retuning.

Decision recorded as `{summary["decision"]}`.
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
            rel(Path("tools/analyze/build_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py")),
            rel(Path("tools/analyze/test_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py")),
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
            "thesis_current_or_latex_edit": False,
            "protected_row_fitting_or_model_selection": False,
            "source_property_or_qwall_release": False,
            "candidate_freeze": False,
            "final_score_claim": False,
        },
        "decision": summary["decision"],
    }
    json_dump(IMPORT, payload)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)

    split = case_split_contract_rows()
    train = training_availability_rows()
    blind = blind_test_availability_rows()
    shell = requested_score_shell_rows()
    decision = fit_and_score_decision_rows()
    leakage = leakage_audit_rows()
    actions = next_action_rows()
    sources = source_manifest_rows()
    guardrails = guardrail_rows()

    csv_dump(
        out / "case_split_contract.csv",
        [
            "case_key",
            "source_key",
            "requested_role",
            "final_scorecard_partition",
            "fit_allowed",
            "model_selection_allowed",
            "score_allowed",
            "release_gate",
            "shell_score_status",
            "target_evidence_status",
            "guardrail",
            "source_property_gate_status",
            "source_property_gate_reason",
        ],
        split,
    )
    csv_dump(
        out / "training_availability.csv",
        [
            "case_key",
            "case_id",
            "requested_train",
            "canonical_training_row",
            "passive_h2_prediction_available",
            "passive_h2_runtime_evidence_available",
            "fit_allowed_by_scorecard_now",
            "model_selection_allowed_by_scorecard_now",
            "source_property_gate_status",
            "preflight_disposition",
            "fit_ready_now",
            "blocker_or_status",
            "passive_h2_corrected_outer_total_W",
            "passive_h2_radiation_W",
            "legacy_qambient_context_W",
            "fluid_runtime_mdot_kg_s",
            "fluid_runtime_qambient_W",
            "evidence_source",
        ],
        train,
    )
    csv_dump(
        out / "blind_test_availability.csv",
        [
            "case_key",
            "requested_test",
            "final_scorecard_partition",
            "fit_allowed",
            "model_selection_allowed",
            "score_allowed_after_freeze_or_gate",
            "release_gate",
            "target_rows_available",
            "target_status",
            "passive_h2_frozen_prediction_available",
            "score_ready_now",
            "blocker_or_status",
            "target_source",
            "prediction_source",
        ],
        blind,
    )
    csv_dump(
        out / "requested_score_shell.csv",
        [
            "candidate_id",
            "case_key",
            "final_scorecard_partition",
            "qoi",
            "target_type",
            "prediction_available",
            "target_available",
            "score_emitted",
            "score_value",
            "claim_scope",
            "reason",
        ],
        shell,
    )
    csv_dump(
        out / "fit_and_score_decision.csv",
        [
            "candidate_id",
            "requested_train_cases",
            "requested_test_cases",
            "train_prediction_rows_available",
            "train_fit_ready_rows",
            "blind_prediction_rows_available",
            "score_values_emitted",
            "coefficient_fit_performed",
            "protected_rows_used_for_fit_or_selection",
            "decision",
            "reason",
        ],
        decision,
    )
    csv_dump(
        out / "split_leakage_audit.csv",
        ["input_or_action", "role", "used_for_fit", "used_for_model_selection", "used_for_score", "status"],
        leakage,
    )
    csv_dump(out / "next_action_queue.csv", ["priority", "action", "why", "acceptance"], actions)
    csv_dump(out / "source_manifest.csv", ["source_label", "source_path", "exists", "use", "mutated"], sources)
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "candidate_id": "PASSIVE-H2-CAND001",
        "decision": "passive_h2_salt14_pm5_valsalt2_requested_traintest_blocked_no_fit_no_score",
        "requested_train_rows": len(train),
        "train_prediction_rows_available": sum(row["passive_h2_prediction_available"] == "true" for row in train),
        "train_runtime_rows_available": sum(row["passive_h2_runtime_evidence_available"] == "true" for row in train),
        "train_fit_ready_rows": sum(row["fit_ready_now"] == "true" for row in train),
        "requested_blind_test_rows": len(blind),
        "blind_target_rows_available": sum(int(row["target_rows_available"]) for row in blind),
        "blind_prediction_rows_available": sum(row["passive_h2_frozen_prediction_available"] == "true" for row in blind),
        "requested_score_shell_rows": len(shell),
        "score_values_emitted": 0,
        "coefficient_fit_performed": False,
        "protected_rows_used_for_fit_or_selection": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "source_property_or_qwall_release": False,
        "candidate_freeze": False,
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
