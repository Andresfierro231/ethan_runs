#!/usr/bin/env python3.11
"""Build the M0 setup-only baseline prediction scorecard shell.

M0 is a lower-bound baseline. This task does not run Fluid, does not fit or
select coefficients, and does not consume protected target values. If no
runtime-legal frozen prediction artifact exists, every scorecard target must
carry an explicit missing-prediction reason.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22"
SLUG = "m0_setup_only_baseline_prediction_scorecard"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard"

FINAL_SHELL = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/prediction_join_shell.csv"
CASE_PARTITIONS = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/case_partition_contract.csv"
S6_SHELL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s6_frozen_candidate_scorecard/split_role_scorecard_shell.csv"
STARTER_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/baseline_model_contract.csv"
EXECUTION_PLAN = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_predictive_model_execution_path/staged_implementation_plan.csv"
BOUNDARY_ADMISSION = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/submodel_admission_summary.csv"
SOURCE_RELEASE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s5_source_property_split_release/source_property_release_ledger.csv"
BLOCKED_SCORECARD_SHELL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/blocked_scorecard_visual_table.csv"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def bool_str(value: bool) -> str:
    return "true" if value else "false"


def aggregate_counter(rows: list[dict[str, str]], key: str) -> Counter[str]:
    return Counter(row.get(key, "") or "blank" for row in rows)


def build_prediction_matrix(shell_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in shell_rows:
        prediction_status = row.get("prediction_source_status", "")
        m0_status = "missing_no_frozen_runtime_legal_runner"
        reason = (
            "M0 can publish the setup-only scorecard schema, but no frozen "
            "runtime-legal prediction artifact exists for this target. The row "
            "is retained as an explicit missing prediction rather than scored."
        )
        if prediction_status and prediction_status != "no_final_frozen_prediction_artifact":
            reason = f"Existing shell status `{prediction_status}` is preserved; no M0 value was generated."
        rows.append(
            {
                "model_id": "M0_setup_only_baseline",
                "freeze_id": "M0_BASELINE_NO_FREEZE",
                "case_key": row.get("case_key", ""),
                "case_id": row.get("case_id", ""),
                "final_scorecard_partition": row.get("final_scorecard_partition", ""),
                "metric_id": row.get("metric_id", ""),
                "target_lane": row.get("target_lane", ""),
                "section_or_segment": row.get("section_or_segment", ""),
                "required_prediction_fields": row.get("required_prediction_fields", ""),
                "m0_prediction_status": m0_status,
                "m0_prediction_value": "",
                "m0_residual_status": "not_computed_no_prediction",
                "blocked_or_missing_reason": reason,
                "score_aggregate_allowed_after_freeze": row.get("score_aggregate_allowed", ""),
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "source_property_gate_status": row.get("source_property_gate_status", ""),
                "source_property_gate_reason": row.get("source_property_gate_reason", ""),
                "property_mode": row.get("property_mode", ""),
                "source_validity_envelope_status": row.get("source_validity_envelope_status", ""),
                "source_use_category": row.get("source_use_category", ""),
                "source_paths": row.get("source_paths", ""),
            }
        )
    return rows


def build_runtime_input_audit() -> list[dict[str, object]]:
    return [
        {
            "input_or_action": "setup_geometry_and_case_identity",
            "runtime_role": "allowed_schema_input",
            "used_by_m0": True,
            "status": "pass_schema_only",
            "reason": "Case keys, partitions, metric IDs, and required prediction fields are scorecard schema, not protected target values.",
        },
        {
            "input_or_action": "property_mode_label",
            "runtime_role": "allowed_label_only",
            "used_by_m0": True,
            "status": "pass_label_only",
            "reason": "Property mode and source-envelope labels are copied as provenance/gates; no property coefficient is fit.",
        },
        {
            "input_or_action": "CFD_mdot",
            "runtime_role": "forbidden_runtime_input",
            "used_by_m0": False,
            "status": "pass_absent",
            "reason": "No CFD mass-flow value is used to generate a prediction.",
        },
        {
            "input_or_action": "realized_CFD_wallHeatFlux",
            "runtime_role": "forbidden_runtime_input",
            "used_by_m0": False,
            "status": "pass_absent",
            "reason": "No realized wall heat-flux value is used as a predictor.",
        },
        {
            "input_or_action": "imposed_CFD_cooler_duty",
            "runtime_role": "forbidden_runtime_input",
            "used_by_m0": False,
            "status": "pass_absent",
            "reason": "No imposed cooler duty is used as a setup-only prediction term.",
        },
        {
            "input_or_action": "validation_holdout_external_temperatures",
            "runtime_role": "forbidden_runtime_input",
            "used_by_m0": False,
            "status": "pass_absent",
            "reason": "Target temperatures are not consumed; M0 emits missing rows rather than residuals.",
        },
        {
            "input_or_action": "scored_pressure_losses_or_protected_residuals",
            "runtime_role": "forbidden_runtime_input",
            "used_by_m0": False,
            "status": "pass_absent",
            "reason": "No scored pressure loss, target residual, or hidden multiplier is used.",
        },
        {
            "input_or_action": "Fluid_or_OpenFOAM_solver",
            "runtime_role": "not_launched",
            "used_by_m0": False,
            "status": "pass_not_run",
            "reason": "This package is a read-only scorecard-shell baseline; no solver was launched.",
        },
    ]


def build_setup_input_coverage(shell_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_metric = aggregate_counter(shell_rows, "metric_id")
    rows: list[dict[str, object]] = []
    rows.append(
        {
            "input_group": "scorecard_schema",
            "coverage_status": "available",
            "covered_rows": len(shell_rows),
            "missing_rows": 0,
            "evidence": rel(FINAL_SHELL),
            "m0_use": "defines targets and required prediction fields only",
        }
    )
    rows.append(
        {
            "input_group": "case_split_contract",
            "coverage_status": "available",
            "covered_rows": len(read_csv(CASE_PARTITIONS)),
            "missing_rows": 0,
            "evidence": rel(CASE_PARTITIONS),
            "m0_use": "separates train/support/holdout/external/future roles",
        }
    )
    rows.append(
        {
            "input_group": "frozen_prediction_artifact",
            "coverage_status": "missing",
            "covered_rows": 0,
            "missing_rows": len(shell_rows),
            "evidence": rel(STARTER_CONTRACT),
            "m0_use": "blocks numerical M0 predictions and residual scores",
        }
    )
    rows.append(
        {
            "input_group": "runtime_source_property_release",
            "coverage_status": "not_released_for_fit_or_final_score",
            "covered_rows": 0,
            "missing_rows": len(shell_rows),
            "evidence": rel(SOURCE_RELEASE),
            "m0_use": "labels rows; no source/property release performed",
        }
    )
    for metric_id, count in sorted(by_metric.items()):
        rows.append(
            {
                "input_group": f"metric::{metric_id}",
                "coverage_status": "schema_available_prediction_missing",
                "covered_rows": count,
                "missing_rows": count,
                "evidence": rel(FINAL_SHELL),
                "m0_use": "metric retained in comparison-ready shell",
            }
        )
    return rows


def build_split_role_ledger(shell_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in shell_rows:
        groups[(row.get("case_key", ""), row.get("final_scorecard_partition", ""))].append(row)
    rows: list[dict[str, object]] = []
    for (case_key, partition), entries in sorted(groups.items()):
        rows.append(
            {
                "case_key": case_key,
                "final_scorecard_partition": partition,
                "target_rows": len(entries),
                "fit_allowed_rows": sum(1 for row in entries if row.get("fit_allowed") == "yes"),
                "model_selection_allowed_rows": sum(1 for row in entries if row.get("model_selection_allowed") == "yes"),
                "m0_score_status": "all_predictions_missing_no_freeze",
                "split_guardrail": "no fitting or model selection; holdout/external/future rows score only after freeze",
            }
        )
    return rows


def build_source_property_status(shell_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in shell_rows:
        key = (
            row.get("source_property_gate_status", "") or "blank",
            row.get("source_use_category", "") or "blank",
            row.get("source_validity_envelope_status", "") or "blank",
        )
        groups[key] += 1
    rows: list[dict[str, object]] = []
    for (gate, use_category, envelope), count in sorted(groups.items()):
        rows.append(
            {
                "source_property_gate_status": gate,
                "source_use_category": use_category,
                "source_validity_envelope_status": envelope,
                "scorecard_rows": count,
                "m0_action": "carry_label_no_release_no_fit_no_score",
            }
        )
    return rows


def write_docs(summary: dict[str, object], validation_status: str = "pending") -> None:
    generated_at = str(summary["generated_at_utc"])
    readme = f"""---
provenance:
  generated_by: tools/analyze/build_m0_setup_only_baseline_prediction_scorecard.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - M0
  - setup-only
  - scorecard
  - forward-prediction
related:
  - {rel(FINAL_SHELL)}
  - {rel(STARTER_CONTRACT)}
  - {rel(EXECUTION_PLAN)}
---

# M0 Setup-Only Baseline Prediction Scorecard

## Decision

M0 is publishable as a lower-bound setup-only scorecard shell, but not as a
numerical final prediction. The current evidence has no frozen runtime-legal
prediction artifact, so every target row is retained with an explicit
`missing_no_frozen_runtime_legal_runner` label.

## Result

- Scorecard target rows: `{summary['scorecard_target_rows']}`.
- Cases represented: `{summary['case_rows']}`.
- Metrics represented: `{summary['metric_rows']}`.
- Numerical prediction rows: `{summary['numerical_prediction_rows']}`.
- Missing prediction rows: `{summary['missing_prediction_rows']}`.
- Runtime leakage failures: `{summary['runtime_leakage_failures']}`.

## Scientific Use

Use this package as the comparison baseline for later model forms. It prevents
future analyses from silently omitting targets, mixing split roles, or using
protected CFD/validation quantities at runtime. It does not claim an admitted
closure, final score, or predictive accuracy.

## Guardrails

No Fluid/OpenFOAM solve, scheduler action, fitting, model selection,
source/property release, final score claim, native-output mutation, registry
mutation, external edit, S11/S12/S13/S15/S6 trigger, hidden multiplier, or
residual absorption into internal Nu was performed.
"""
    write_text(OUT_DIR / "README.md", readme)

    status = f"""---
provenance:
  generated_by: tools/analyze/build_m0_setup_only_baseline_prediction_scorecard.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - status
  - M0
  - setup-only
related:
  - {rel(OUT_DIR)}
---

# {TASK_ID}

## Objective

Produce an M0 setup-only lower-bound baseline scorecard or an explicit
missing-prediction matrix while preserving runtime legality and split roles.

## Outcome

Decision: `{summary['decision']}`. M0 is comparison-ready as a shell with
`{summary['scorecard_target_rows']}` target rows and `{summary['missing_prediction_rows']}`
explicit missing predictions. No numerical score was produced because no frozen
runtime-legal prediction artifact exists.

## Changes Made

- Wrote `{rel(OUT_DIR / 'm0_prediction_matrix.csv')}`.
- Wrote `{rel(OUT_DIR / 'runtime_input_audit.csv')}`.
- Wrote `{rel(OUT_DIR / 'setup_input_coverage_table.csv')}`.
- Wrote `{rel(OUT_DIR / 'split_role_ledger.csv')}`.
- Wrote `{rel(OUT_DIR / 'source_property_status.csv')}`.
- Wrote `{rel(OUT_DIR / 'comparison_ready_scorecard_shell.csv')}`, README,
  summary, status, journal, and import manifest.

## Validation

{validation_status}

## Guardrails

- Fluid/external edit: false.
- Solver/scheduler launch: false.
- Validation/holdout/external-test scoring: false.
- Fitting/tuning/model selection: false.
- Source/property release or coefficient admission: false.
- Final score claim or S11/S12/S13/S15/S6 trigger: false.
- Native-output or registry/admission mutation: false.
- Hidden multiplier/runtime leakage/residual-internal-Nu absorption: false.
"""
    write_text(ROOT / f".agent/status/2026-07-22_{TASK_ID}.md", status)

    journal = f"""---
provenance:
  generated_by: tools/analyze/build_m0_setup_only_baseline_prediction_scorecard.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - journal
  - M0
  - setup-only
related:
  - {rel(OUT_DIR)}
---

# M0 setup-only baseline prediction scorecard

## Attempted

Claimed the M0 board row and built a read-only package from the final
scorecard shell, predictive final model starter, predictive execution path, and
source/property ledgers.

## Observed

The scorecard schema is available for `{summary['scorecard_target_rows']}` target
rows across `{summary['case_rows']}` cases and `{summary['metric_rows']}` metrics.
The starter contract still reports `FINAL_FREEZE_TBD`; no frozen runtime-legal
prediction artifact exists.

## Inferred

The scientifically correct M0 result is not a numerical baseline. It is a
comparison-ready missing-prediction matrix that locks the target list, split
roles, source/property labels, and runtime-leakage guardrails before later
candidate models are tried.

## Contradictions or Caveats

M0 should not be described as predictive accuracy evidence. It is a null/lower
bound for publication tables and later model-form comparisons. Any later M1-M6
row must improve on this by providing legal predictions under its own source,
property, split, and UQ gates.

## Next Useful Actions

Use this M0 package when comparing the S13 exchange-cell path, MF02
pressure-mdot diagnostic, M2 passive/test-section repair gate, or future
runtime-legal freeze candidates. Do not fill the missing M0 prediction cells
from CFD mdot, realized wallHeatFlux, imposed cooler duty, protected target
temperatures, pressure losses, or residuals.
"""
    write_text(ROOT / ".agent/journal/2026-07-22/m0-setup-only-baseline-prediction-scorecard.md", journal)


def build() -> dict[str, object]:
    generated_at = now_utc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shell_rows = read_csv(FINAL_SHELL)
    matrix_rows = build_prediction_matrix(shell_rows)
    runtime_rows = build_runtime_input_audit()
    coverage_rows = build_setup_input_coverage(shell_rows)
    split_rows = build_split_role_ledger(shell_rows)
    source_rows = build_source_property_status(shell_rows)

    write_csv(OUT_DIR / "m0_prediction_matrix.csv", matrix_rows)
    write_csv(OUT_DIR / "comparison_ready_scorecard_shell.csv", matrix_rows)
    write_csv(OUT_DIR / "runtime_input_audit.csv", runtime_rows)
    write_csv(OUT_DIR / "setup_input_coverage_table.csv", coverage_rows)
    write_csv(OUT_DIR / "split_role_ledger.csv", split_rows)
    write_csv(OUT_DIR / "source_property_status.csv", source_rows)

    fit_allowed_rows = sum(1 for row in matrix_rows if row["fit_allowed"] == "yes")
    model_selection_allowed_rows = sum(1 for row in matrix_rows if row["model_selection_allowed"] == "yes")
    runtime_failures = sum(1 for row in runtime_rows if not str(row["status"]).startswith("pass"))
    missing_predictions = sum(1 for row in matrix_rows if row["m0_prediction_status"] != "predicted")
    metric_ids = {row["metric_id"] for row in matrix_rows}
    cases = {row["case_key"] for row in matrix_rows}

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": generated_at,
        "decision": "m0_setup_only_baseline_shell_ready_all_predictions_explicitly_missing",
        "scorecard_target_rows": len(matrix_rows),
        "case_rows": len(cases),
        "metric_rows": len(metric_ids),
        "numerical_prediction_rows": len(matrix_rows) - missing_predictions,
        "missing_prediction_rows": missing_predictions,
        "fit_allowed_rows": fit_allowed_rows,
        "model_selection_allowed_rows": model_selection_allowed_rows,
        "runtime_leakage_failures": runtime_failures,
        "fluid_or_external_edit": False,
        "solver_or_scheduler_launch": False,
        "validation_holdout_external_scoring": False,
        "fitting_tuning_model_selection": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "final_score_claim": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "hidden_multiplier": False,
        "residual_internal_nu_absorption": False,
        "source_context": [
            rel(FINAL_SHELL),
            rel(CASE_PARTITIONS),
            rel(S6_SHELL),
            rel(STARTER_CONTRACT),
            rel(EXECUTION_PLAN),
            rel(BOUNDARY_ADMISSION),
            rel(SOURCE_RELEASE),
            rel(BLOCKED_SCORECARD_SHELL),
        ],
    }
    write_text(OUT_DIR / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_docs(summary)

    manifest = {
        "task": TASK_ID,
        "generated_at_utc": generated_at,
        "changed_files": [
            rel(OUT_DIR / "README.md"),
            rel(OUT_DIR / "summary.json"),
            rel(OUT_DIR / "m0_prediction_matrix.csv"),
            rel(OUT_DIR / "comparison_ready_scorecard_shell.csv"),
            rel(OUT_DIR / "runtime_input_audit.csv"),
            rel(OUT_DIR / "setup_input_coverage_table.csv"),
            rel(OUT_DIR / "split_role_ledger.csv"),
            rel(OUT_DIR / "source_property_status.csv"),
            f".agent/status/2026-07-22_{TASK_ID}.md",
            ".agent/journal/2026-07-22/m0-setup-only-baseline-prediction-scorecard.md",
            f"imports/2026-07-22_{SLUG}.json",
            "tools/analyze/build_m0_setup_only_baseline_prediction_scorecard.py",
            "tools/analyze/test_m0_setup_only_baseline_prediction_scorecard.py",
            ".agent/BOARD.md",
        ],
        "read_only_context": summary["source_context"]
        + [
            "native CFD/OpenFOAM outputs",
            "registry/admission state",
            "scheduler state",
            "Fluid source tree",
            "external repos",
            "blocker register",
            "generated docs index files",
            "thesis current/LaTeX files",
        ],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": "none",
        "external_fluid_edit": False,
        "mutation_flags": {
            "fluid_or_external_edit": False,
            "solver_or_scheduler_launch": False,
            "protected_scoring": False,
            "fitting_tuning_model_selection": False,
            "source_property_release": False,
            "coefficient_admission": False,
            "native_output_mutation": False,
            "registry_or_admission_mutation": False,
        },
    }
    write_text(ROOT / f"imports/2026-07-22_{SLUG}.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
