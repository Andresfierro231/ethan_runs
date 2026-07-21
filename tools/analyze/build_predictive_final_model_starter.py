#!/usr/bin/env python3
"""Build stage-0 artifacts for approaching the final predictive model.

This runner implements the first repo-local part of the predictive execution
plan. It consumes existing contracts and emits the baseline/study-readiness
surface that later model-specific rows should use before any solver run,
fitting, model selection, or closure admission.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-PRED-FINAL-MODEL-STARTER-IMPLEMENTATION-2026-07-21"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter")
OUT = ROOT / OUT_REL

EXECUTION_PATH = (
    ROOT / "work_products/2026-07/2026-07-21/2026-07-21_predictive_model_execution_path"
)
FINAL_SHELL = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell"
)
AMX1_PHYSICS = (
    ROOT / "work_products/2026-07/2026-07-21/2026-07-21_amx1_physics_revision_smoke_intake"
)
UPCOMER_ONSET = (
    ROOT / "work_products/2026-07/2026-07-20/2026-07-20_upcomer_onset_anchor_design"
)
F6_ANCHOR = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan"

STAGED_PLAN = EXECUTION_PATH / "staged_implementation_plan.csv"
SPLIT_BOUNDARIES = EXECUTION_PATH / "split_claim_boundaries.csv"
RESIDUAL_CONTRACT = EXECUTION_PATH / "residual_attribution_contract.csv"
SCORECARD_OUTPUT_CONTRACT = EXECUTION_PATH / "scorecard_output_contract.csv"

CASE_PARTITION = FINAL_SHELL / "case_partition_contract.csv"
PREDICTION_SHELL = FINAL_SHELL / "prediction_join_shell.csv"
ADMISSION_GATES = FINAL_SHELL / "admission_gate_shell.csv"
RUNTIME_AUDIT = FINAL_SHELL / "runtime_input_audit.csv"
RELEASE_GATES = FINAL_SHELL / "holdout_release_gates.csv"
FINAL_SHELL_SUMMARY = FINAL_SHELL / "summary.json"

BLOCKERS = ROOT / ".agent/BLOCKERS.md"

OPEN_BLOCKER_IDS = (
    "predictive-wall-test-section-submodels",
    "upcomer-onset-data-sparsity",
    "f6-friction-re-correction",
    "two-tap-corner-lower-right-component-isolation-fails",
    "two-tap-corner-lower-right-same-qoi-uq-missing",
    "two-tap-corner-lower-right-material-reverse-flow",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def blocker_is_open(blocker_text: str, blocker_id: str) -> bool:
    return f"| `{blocker_id}` |" in blocker_text.split("## Resolved / superseded")[0]


def baseline_model_contract(
    shell_summary: dict[str, Any],
    case_rows: list[dict[str, str]],
    prediction_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    partitions = Counter(row["final_scorecard_partition"] for row in case_rows)
    join_statuses = Counter(row["join_status"] for row in prediction_rows)
    return [
        {
            "contract_id": "B0_current_scorecard_shell",
            "implementation_status": "implemented_by_existing_shell",
            "model_freeze_id": "FINAL_FREEZE_TBD",
            "prediction_status": shell_summary["score_status"],
            "case_count": len(case_rows),
            "prediction_placeholder_rows": shell_summary["prediction_placeholder_rows"],
            "fit_allowed_rows_after_source_property_gate": shell_summary[
                "fit_allowed_after_source_property_gate"
            ],
            "model_selection_allowed_rows_after_source_property_gate": shell_summary[
                "model_selection_allowed_after_source_property_gate"
            ],
            "runtime_audit_failures": shell_summary["runtime_audit_failures"],
            "next_action": "keep as baseline; do not promote to final freeze without admitted candidate",
            "source_paths": rel(FINAL_SHELL_SUMMARY),
        },
        {
            "contract_id": "B1_split_partitions",
            "implementation_status": "implemented_by_existing_shell",
            "model_freeze_id": "FINAL_FREEZE_TBD",
            "prediction_status": "split_contract_ready",
            "case_count": len(case_rows),
            "prediction_placeholder_rows": len(prediction_rows),
            "fit_allowed_rows_after_source_property_gate": 0,
            "model_selection_allowed_rows_after_source_property_gate": 0,
            "runtime_audit_failures": 0,
            "next_action": (
                f"train={partitions['train_nominal']}; "
                f"holdout={partitions['blind_holdout_pm5q']}; "
                f"external={partitions['blind_external_val_salt2']}; "
                f"future={partitions['future_holdout_pm10'] + partitions['future_external_new_cfd']}"
            ),
            "source_paths": rel(CASE_PARTITION),
        },
        {
            "contract_id": "B2_missing_predictions_explicit",
            "implementation_status": "implemented_by_existing_shell",
            "model_freeze_id": "FINAL_FREEZE_TBD",
            "prediction_status": "no_final_frozen_prediction_artifact",
            "case_count": len(case_rows),
            "prediction_placeholder_rows": len(prediction_rows),
            "fit_allowed_rows_after_source_property_gate": 0,
            "model_selection_allowed_rows_after_source_property_gate": 0,
            "runtime_audit_failures": 0,
            "next_action": "; ".join(f"{key}={value}" for key, value in sorted(join_statuses.items())),
            "source_paths": rel(PREDICTION_SHELL),
        },
    ]


def runtime_and_split_gate_audit(
    runtime_rows: list[dict[str, str]],
    case_rows: list[dict[str, str]],
    release_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    bad_blind_fit = [
        row
        for row in case_rows
        if row["final_scorecard_partition"] != "train_nominal"
        and (row["fit_allowed"] == "yes" or row["model_selection_allowed"] == "yes")
    ]
    bad_release = [
        row
        for row in release_rows
        if row["fit_allowed_after_release"] != "no"
        or row["model_selection_allowed_after_release"] != "no"
    ]
    rows: list[dict[str, Any]] = []
    rows.extend(
        {
            "audit_id": f"shell_{row['audit_item']}",
            "status": row["status"],
            "details": row["details"],
            "source_paths": rel(RUNTIME_AUDIT),
        }
        for row in runtime_rows
    )
    rows.extend(
        [
            {
                "audit_id": "starter_blind_rows_score_only",
                "status": "pass" if not bad_blind_fit else "fail",
                "details": f"bad_rows={len(bad_blind_fit)}",
                "source_paths": rel(CASE_PARTITION),
            },
            {
                "audit_id": "starter_release_never_enables_fit_or_selection",
                "status": "pass" if not bad_release else "fail",
                "details": f"bad_rows={len(bad_release)}",
                "source_paths": rel(RELEASE_GATES),
            },
        ]
    )
    return rows


def residual_lane_readiness(
    residual_rows: list[dict[str, str]],
    blocker_text: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in residual_rows:
        lane = row["lane"]
        if lane in {"buoyancy_drive", "heater_transfer", "cooler_hx_removal"}:
            status = "baseline_or_boundary_evidence_available"
            blocker = ""
            next_action = "carry as baseline lane and score residuals after freeze"
        elif row["residual_family"] == "pressure":
            status = "blocked_diagnostic_only"
            blocker = (
                "f6-friction-re-correction;"
                "two-tap-corner-lower-right-component-isolation-fails;"
                "two-tap-corner-lower-right-same-qoi-uq-missing;"
                "two-tap-corner-lower-right-material-reverse-flow"
            )
            next_action = "run pressure source-envelope/basis recovery audit before fitting"
        elif lane in {"passive_wall_external", "test_section_source_loss", "junction_stub_heat"}:
            status = "blocked_or_diagnostic_until_heat_loss_network_gate"
            blocker = "predictive-wall-test-section-submodels"
            next_action = "build heat-loss network alignment and setup-only candidate contract"
        elif lane == "internal_nu_htc":
            status = "reference_or_diagnostic_only"
            blocker = "predictive-wall-test-section-submodels;upcomer-onset-data-sparsity"
            next_action = "keep Nu from absorbing heat-loss residuals until source/sign/UQ gates pass"
        else:
            status = "diagnostic_residual_lane"
            blocker = "predictive-wall-test-section-submodels"
            next_action = "retain explicit residual owner in scorecard"
        rows.append(
            {
                "residual_family": row["residual_family"],
                "lane": lane,
                "readiness_status": status,
                "open_blocker_ids": blocker,
                "next_action": next_action,
                "scorecard_columns": row["scorecard_columns"],
                "guardrail": row["guardrail"],
                "source_paths": rel(RESIDUAL_CONTRACT),
            }
        )
    for blocker_id in OPEN_BLOCKER_IDS:
        if not blocker_is_open(blocker_text, blocker_id):
            rows.append(
                {
                    "residual_family": "blocker_audit",
                    "lane": blocker_id,
                    "readiness_status": "warning_expected_open_blocker_not_found",
                    "open_blocker_ids": blocker_id,
                    "next_action": "review blocker register before interpreting this package",
                    "scorecard_columns": "",
                    "guardrail": "do not resolve blockers from starter package",
                    "source_paths": rel(BLOCKERS),
                }
            )
    return rows


def next_study_queue(stage_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    details = {
        "baseline_current_model": (
            "complete_stage0_with_this_runner",
            "Use starter outputs as the common baseline for later study rows.",
            "no",
            "",
        ),
        "external_bc_dictionary": (
            "next_repo_local_contract",
            "Refresh external BC dictionary coverage against fluid+walls roles before Fluid edits.",
            "no",
            "TODO-FLUID-EXTERNAL-BC-DICT",
        ),
        "pressure_source_envelope": (
            "next_hydraulic_gate",
            "Run pressure basis/recovery/source-envelope audit before F6 or K fitting.",
            "no",
            "f6-friction-re-correction",
        ),
        "heat_loss_network": (
            "next_thermal_gate",
            "Align heat-loss network and wall/test-section candidate contracts before coupled grids.",
            "no",
            "predictive-wall-test-section-submodels",
        ),
        "recirculation_guard": (
            "next_hybrid_gate",
            "Build single-stream disable table and throughflow-plus-recirculation interface.",
            "no",
            "upcomer-onset-data-sparsity;f6-friction-re-correction",
        ),
        "final_scorecard": (
            "blocked_until_candidate_freeze",
            "Join predictions only after an admitted frozen candidate exists.",
            "no",
            "FINAL_FREEZE_TBD absent",
        ),
    }
    rows = []
    for row in stage_rows:
        status, study, launch_now, blocker = details[row["stage_name"]]
        rows.append(
            {
                "priority": row["stage_id"],
                "stage_name": row["stage_name"],
                "lane": row["lane"],
                "implementation_status": status,
                "study_to_perform": study,
                "launch_now": launch_now,
                "blocking_condition": blocker,
                "acceptance_signal": row["acceptance_signal"],
                "guardrails": row["guardrails"],
                "source_paths": rel(STAGED_PLAN),
            }
        )
    return rows


def freeze_readiness_matrix(
    stage_queue: list[dict[str, Any]],
    admission_rows: list[dict[str, str]],
    shell_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    gate_by_id = {row["gate_id"]: row for row in admission_rows}
    rows = [
        {
            "gate_id": "baseline_contract_ready",
            "current_state": "pass",
            "required_for_freeze": "yes",
            "evidence": rel(OUT / "baseline_model_contract.csv"),
            "next_action": "use as starting point for later model-specific rows",
        },
        {
            "gate_id": "source_property_fit_release",
            "current_state": "fail",
            "required_for_freeze": "yes",
            "evidence": rel(FINAL_SHELL_SUMMARY),
            "next_action": (
                "fit_allowed_after_source_property_gate="
                f"{shell_summary['fit_allowed_after_source_property_gate']}"
            ),
        },
    ]
    for gate_id in (
        "corrected_split_freeze_exists",
        "candidate_admitted",
        "blind_rows_excluded_from_fit",
        "pm10_terminal_admission",
        "new_cfd_admission",
    ):
        gate = gate_by_id[gate_id]
        rows.append(
            {
                "gate_id": gate_id,
                "current_state": gate["current_state"],
                "required_for_freeze": gate["required_to_score"],
                "evidence": gate["evidence"],
                "next_action": gate["next_action"],
            }
        )
    for item in stage_queue:
        if item["implementation_status"] != "complete_stage0_with_this_runner":
            rows.append(
                {
                    "gate_id": f"stage_{item['stage_name']}",
                    "current_state": item["implementation_status"],
                    "required_for_freeze": "yes",
                    "evidence": item["source_paths"],
                    "next_action": item["study_to_perform"],
                }
            )
    return rows


def scorecard_release_guardrails(
    split_rows: list[dict[str, str]],
    release_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    def current_permission(value: str) -> str:
        if value == "no":
            return "no"
        if value == "blocked_until_release":
            return value
        return "blocked_until_source_property_and_candidate_release"

    rows = [
        {
            "guardrail_id": f"split_{row['claim_class']}",
            "row_family": row["row_family"],
            "fit_allowed": current_permission(row["fit_allowed"]),
            "model_selection_allowed": current_permission(row["model_selection_allowed"]),
            "score_allowed": row["score_allowed"],
            "release_or_gate": row["required_release_gate"],
            "forbidden_use": row["forbidden_use"],
            "source_property_gate_status": "blocked_starter_current_no_fit_or_selection",
            "property_mode": "see_case_partition_contract",
            "property_sensitivity_label": "see_case_partition_contract",
            "source_validity_envelope_status": "source_property_release_required",
            "source_use_category": "guardrail_not_fit_candidate",
            "provenance_author_title": "TODO-PRED-ENDTOEND-SCORE execution-path split contract",
            "source_paths": rel(SPLIT_BOUNDARIES),
        }
        for row in split_rows
    ]
    rows.extend(
        {
            "guardrail_id": f"release_{row['case_key']}",
            "row_family": row["case_key"],
            "fit_allowed": row["fit_allowed_after_release"],
            "model_selection_allowed": row["model_selection_allowed_after_release"],
            "score_allowed": row["score_allowed_after_release"],
            "release_or_gate": row["gate_inputs_required"],
            "forbidden_use": row["guardrail"],
            "source_property_gate_status": "blocked_or_score_only_no_fit",
            "property_mode": "see_case_partition_contract",
            "property_sensitivity_label": "see_case_partition_contract",
            "source_validity_envelope_status": "score_only_or_future_release",
            "source_use_category": "guardrail_not_fit_candidate",
            "provenance_author_title": row["source_paths"],
            "source_paths": rel(RELEASE_GATES),
        }
        for row in release_rows
    )
    return rows


def source_manifest() -> list[dict[str, str]]:
    paths = [
        STAGED_PLAN,
        SPLIT_BOUNDARIES,
        RESIDUAL_CONTRACT,
        SCORECARD_OUTPUT_CONTRACT,
        CASE_PARTITION,
        PREDICTION_SHELL,
        ADMISSION_GATES,
        RUNTIME_AUDIT,
        RELEASE_GATES,
        FINAL_SHELL_SUMMARY,
        BLOCKERS,
        AMX1_PHYSICS / "README.md",
        UPCOMER_ONSET / "README.md",
        F6_ANCHOR / "README.md",
    ]
    return [
        {
            "path": rel(path),
            "role_in_package": "read input contract or current evidence",
            "mutation_status": "read_only",
        }
        for path in paths
        if path.exists()
    ] + [
        {
            "path": rel(OUT),
            "role_in_package": "generated starter package",
            "mutation_status": "modified",
        }
    ]


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(STAGED_PLAN)}
  - {rel(CASE_PARTITION)}
  - {rel(PREDICTION_SHELL)}
  - {rel(ADMISSION_GATES)}
  - {rel(BLOCKERS)}
tags: [forward-model, predictive-1d, starter-runner, scorecard, residual-attribution]
related:
  - operational_notes/maps/forward-predictive-model.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_model_execution_path/README.md
task: {TASK}
date: 2026-07-21
role: Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Predictive Final Model Starter

This package implements the repo-local stage-0 starter surface for approaching
the final predictive model. It does not run Fluid or OpenFOAM, does not fit or
select coefficients, and does not admit a new closure.

## Result

- Baseline contract rows: `{summary['baseline_contract_rows']}`.
- Next-study queue rows: `{summary['next_study_queue_rows']}`.
- Residual-lane readiness rows: `{summary['residual_lane_readiness_rows']}`.
- Freeze-readiness gate rows: `{summary['freeze_readiness_rows']}`.
- Runtime/split gate failures: `{summary['runtime_split_gate_failures']}`.
- Final fit-enabled rows after source/property gate: `{summary['fit_allowed_after_source_property_gate']}`.

The decision is `{summary['decision']}`. The next implementation rows should
start from `next_study_queue.csv` and `freeze_readiness_matrix.csv`.

## Files

- `baseline_model_contract.csv`
- `runtime_and_split_gate_audit.csv`
- `residual_lane_readiness.csv`
- `next_study_queue.csv`
- `freeze_readiness_matrix.csv`
- `scorecard_release_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
external Fluid source, blocker register, fitting/model-selection state, or
scientific admission state were changed.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    shell_summary = read_json(FINAL_SHELL_SUMMARY)
    case_rows = read_csv(CASE_PARTITION)
    prediction_rows = read_csv(PREDICTION_SHELL)
    runtime_rows = read_csv(RUNTIME_AUDIT)
    release_rows = read_csv(RELEASE_GATES)
    stage_rows = read_csv(STAGED_PLAN)
    residual_rows = read_csv(RESIDUAL_CONTRACT)
    split_rows = read_csv(SPLIT_BOUNDARIES)
    admission_rows = read_csv(ADMISSION_GATES)
    blocker_text = BLOCKERS.read_text(encoding="utf-8", errors="replace")

    baseline_rows = baseline_model_contract(shell_summary, case_rows, prediction_rows)
    runtime_gate_rows = runtime_and_split_gate_audit(runtime_rows, case_rows, release_rows)
    residual_ready_rows = residual_lane_readiness(residual_rows, blocker_text)
    study_rows = next_study_queue(stage_rows)
    freeze_rows = freeze_readiness_matrix(study_rows, admission_rows, shell_summary)
    release_guard_rows = scorecard_release_guardrails(split_rows, release_rows)
    manifest_rows = source_manifest()

    write_csv(OUT / "baseline_model_contract.csv", baseline_rows)
    write_csv(OUT / "runtime_and_split_gate_audit.csv", runtime_gate_rows)
    write_csv(OUT / "residual_lane_readiness.csv", residual_ready_rows)
    write_csv(OUT / "next_study_queue.csv", study_rows)
    write_csv(OUT / "freeze_readiness_matrix.csv", freeze_rows)
    write_csv(OUT / "scorecard_release_guardrails.csv", release_guard_rows)
    write_csv(OUT / "source_manifest.csv", manifest_rows)

    runtime_failures = sum(1 for row in runtime_gate_rows if not row["status"].startswith("pass"))
    blocked_freeze = sum(1 for row in freeze_rows if str(row["current_state"]).startswith("fail"))
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "decision": "starter_implemented_final_freeze_still_blocked",
        "baseline_contract_rows": len(baseline_rows),
        "runtime_split_gate_rows": len(runtime_gate_rows),
        "runtime_split_gate_failures": runtime_failures,
        "residual_lane_readiness_rows": len(residual_ready_rows),
        "next_study_queue_rows": len(study_rows),
        "freeze_readiness_rows": len(freeze_rows),
        "freeze_blocking_gate_rows": blocked_freeze,
        "scorecard_release_guardrail_rows": len(release_guard_rows),
        "fit_allowed_after_source_property_gate": shell_summary[
            "fit_allowed_after_source_property_gate"
        ],
        "model_selection_allowed_after_source_property_gate": shell_summary[
            "model_selection_allowed_after_source_property_gate"
        ],
        "prediction_placeholder_rows": shell_summary["prediction_placeholder_rows"],
        "new_admissions": 0,
        "solver_or_scheduler_actions": 0,
        "native_output_mutation": False,
        "registry_mutation": False,
        "fluid_source_mutation": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
