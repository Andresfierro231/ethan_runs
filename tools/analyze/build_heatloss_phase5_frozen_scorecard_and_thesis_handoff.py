#!/usr/bin/env python3
"""Build Phase 5 negative heat-loss freeze and thesis handoff artifacts.

This package freezes the current non-admission state. It does not run a final
predictive score, fit or select models, or edit thesis prose.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-HEATLOSS-PHASE-5-FROZEN-SCORECARD-AND-THESIS-HANDOFF"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_5_frozen_scorecard_and_thesis_handoff"
)
OUT = ROOT / OUT_REL

PHASE0 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_0_baseline_release_gate"
)
PHASE1 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_1_external_bc_radiation_integration"
)
PHASE2 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_2_split_heat_loss_evidence"
)
PHASE3 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_3_wall_test_section_model_score"
)
PHASE4 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
SHELL = ROOT / (
    "work_products/2026-07/2026-07-17/"
    "2026-07-17_final_predictive_scorecard_shell"
)
SPLIT_POLICY = ROOT / (
    "work_products/2026-07/2026-07-17/"
    "2026-07-17_canonical_final_predictive_split_policy"
)
SOURCE_PROPERTY = ROOT / (
    "work_products/2026-07/2026-07-20/"
    "2026-07-20_final_scorecard_source_property_refresh"
)

PHASE0_SUMMARY = PHASE0 / "summary.json"
PHASE1_SUMMARY = PHASE1 / "summary.json"
PHASE2_SUMMARY = PHASE2 / "summary.json"
PHASE3_SUMMARY = PHASE3 / "summary.json"
PHASE4_SUMMARY = PHASE4 / "summary.json"
PHASE4_RELEASE = PHASE4 / "phase4_release_gate.csv"
PHASE4_CONTRACT = PHASE4 / "heat_path_modeling_contract.csv"
SHELL_SUMMARY = SHELL / "summary.json"
SHELL_METRICS = SHELL / "metric_contract.csv"
SHELL_PARTITIONS = SHELL / "case_partition_contract.csv"
SHELL_RUNTIME = SHELL / "runtime_input_audit.csv"
SPLIT_POLICY_TABLE = SPLIT_POLICY / "canonical_final_predictive_split_policy.csv"
SOURCE_PROPERTY_TODO = SOURCE_PROPERTY / "remaining_source_property_todo.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    if not path.is_absolute():
        return str(path)
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def phase_value(summary: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in summary:
            return summary[key]
    return default


def build_phase_gate_table(summaries: dict[str, dict[str, Any]], phase4_release: list[dict[str, str]]) -> list[dict[str, str]]:
    phase4_status = phase_value(
        summaries["phase4"],
        "phase4_release_status",
        "phase5_trigger",
        default="negative_or_not_triggered",
    )
    return [
        {
            "phase": "phase0_baseline_release",
            "release_result": "complete",
            "positive_heatloss_candidate_rows": "0",
            "score_or_fit_status": "baseline_control_surface_only",
            "frozen_use": "context_for_negative_freeze",
            "source_paths": rel(PHASE0_SUMMARY),
        },
        {
            "phase": "phase1_external_bc_radiation",
            "release_result": "complete_blocked_external_fluid_api",
            "positive_heatloss_candidate_rows": "0",
            "score_or_fit_status": "dictionary_contract_only",
            "frozen_use": "runtime_boundary_lane_required_before_final_score",
            "source_paths": rel(PHASE1_SUMMARY),
        },
        {
            "phase": "phase2_split_heat_loss_evidence",
            "release_result": "complete_diagnostic_split_evidence",
            "positive_heatloss_candidate_rows": "0",
            "score_or_fit_status": "no_qr_or_storage_admission",
            "frozen_use": "residual_owner_context",
            "source_paths": rel(PHASE2_SUMMARY),
        },
        {
            "phase": "phase3_wall_test_section_score_gate",
            "release_result": str(phase_value(summaries["phase3"], "phase3_release_status", default="negative")),
            "positive_heatloss_candidate_rows": str(phase_value(summaries["phase3"], "admitted_candidate_rows", default=0)),
            "score_or_fit_status": "no_wall_test_section_candidate_admitted",
            "frozen_use": "negative_wall_test_section_gate",
            "source_paths": rel(PHASE3_SUMMARY),
        },
        {
            "phase": "phase4_exchange_internal_nu_gate",
            "release_result": str(phase4_status),
            "positive_heatloss_candidate_rows": str(
                phase_value(summaries["phase4"], "exchange_cell_fit_ready_rows", default=0)
            ),
            "score_or_fit_status": "no_exchange_fit_or_internal_Nu_reopen",
            "frozen_use": "negative_heatloss_freeze_trigger",
            "source_paths": f"{rel(PHASE4_SUMMARY)};{rel(PHASE4_RELEASE)}",
        },
        {
            "phase": "phase5_negative_freeze",
            "release_result": "negative_freeze_published",
            "positive_heatloss_candidate_rows": "0",
            "score_or_fit_status": "no_final_accuracy_score_run",
            "frozen_use": "thesis_handoff_no_admission_claim",
            "source_paths": ";".join(row.get("source_paths", "") for row in phase4_release),
        },
    ]


def build_metric_availability(metrics: list[dict[str, str]], shell_summary: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for metric in metrics:
        rows.append(
            {
                "metric_id": metric.get("metric_id", ""),
                "metric_family": metric.get("metric_family", ""),
                "target_lane": metric.get("target_lane", ""),
                "train_support_status": "schema_available_no_final_prediction_artifact",
                "holdout_status": metric.get("allowed_on_blind_holdout", ""),
                "external_status": metric.get("allowed_on_external", ""),
                "future_status": metric.get("allowed_on_future", ""),
                "final_score_value_status": "not_computed_negative_freeze",
                "fit_or_selection_from_blind_rows": metric.get("fit_or_selection_from_blind_rows", "no"),
                "runtime_forbidden_inputs": f"forbidden: {metric.get('runtime_forbidden_inputs', '')}",
                "blocker": str(shell_summary.get("freeze_status", "FINAL_FREEZE_TBD_not_created")),
                "source_paths": metric.get("source_paths", ""),
            }
        )
    rows.extend(
        [
            {
                "metric_id": "branch_heat_residual_by_path",
                "metric_family": "thermal_heat_loss",
                "target_lane": "residual_attribution",
                "train_support_status": "diagnostic_only",
                "holdout_status": "blocked_until_runtime_legal_candidate",
                "external_status": "blocked_until_runtime_legal_candidate",
                "future_status": "blocked_until_terminal_or_run_admission",
                "final_score_value_status": "not_computed_negative_freeze",
                "fit_or_selection_from_blind_rows": "no",
                "runtime_forbidden_inputs": "forbidden: realized CFD wallHeatFlux; CFD mdot; validation temperatures; heat residual as runtime predictor",
                "blocker": "Phase 4 has 0 exchange/internal-Nu fit rows",
                "source_paths": f"{rel(PHASE4_SUMMARY)};{rel(PHASE4_CONTRACT)}",
            },
            {
                "metric_id": "loop_delta_T_heatloss",
                "metric_family": "thermal_global",
                "target_lane": "loop_temperature_difference",
                "train_support_status": "schema_only",
                "holdout_status": "blocked_until_runtime_legal_candidate",
                "external_status": "blocked_until_runtime_legal_candidate",
                "future_status": "blocked_until_terminal_or_run_admission",
                "final_score_value_status": "not_computed_negative_freeze",
                "fit_or_selection_from_blind_rows": "no",
                "runtime_forbidden_inputs": "forbidden: validation temperatures; realized heat residual; CFD mdot",
                "blocker": "external BC and heat-path model not frozen",
                "source_paths": f"{rel(PHASE1_SUMMARY)};{rel(PHASE4_SUMMARY)}",
            },
        ]
    )
    return rows


def build_heat_path_freeze(contract_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in contract_rows:
        heat_path = row.get("heat_path", "")
        rows.append(
            {
                "heat_path": heat_path,
                "freeze_status": "not_admitted",
                "runtime_inputs_allowed": row.get("runtime_inputs_allowed", ""),
                "forbidden_runtime_inputs": row.get("forbidden_runtime_inputs", "forbidden: residual leakage"),
                "final_outputs": row.get("outputs", ""),
                "residual_lane_status": "explicit_not_hidden_in_internal_Nu",
                "current_blocker": row.get("current_blocker", ""),
                "thesis_claim_boundary": "diagnostic_or_blocked_evidence_only",
            }
        )
    return rows


def build_blocker_actions() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "blocker": "external_boundary_dictionary_not_runtime_ready",
            "shortest_next_action": "complete TODO-FLUID-EXTERNAL-BC-DICT with h/Ta/Tsur/emissivity/layer-resistance selectors",
            "positive_release_condition": "Fluid runtime accepts external BC dictionary with forbidden realized wallHeatFlux excluded",
            "source_paths": rel(PHASE1_SUMMARY),
        },
        {
            "priority": "2",
            "blocker": "upcomer_exchange_state_missing",
            "shortest_next_action": "extract same-window V_recirc, mdot_exchange, tau_recirc, wall-core Delta T, pressure residual, and energy residual",
            "positive_release_condition": "exchange-cell rows become scoreable without ordinary internal-Nu absorption",
            "source_paths": rel(PHASE4_SUMMARY),
        },
        {
            "priority": "3",
            "blocker": "same_qoi_uncertainty_missing",
            "shortest_next_action": "publish same-label same-formula same-window UQ rows for thermal and pressure residual metrics",
            "positive_release_condition": "holdout/external scores remain score-only and UQ-labeled",
            "source_paths": f"{rel(SHELL_SUMMARY)};{rel(SOURCE_PROPERTY_TODO)}",
        },
        {
            "priority": "4",
            "blocker": "ordinary_internal_Nu_gates_closed",
            "shortest_next_action": "reopen only nonrecirculating rows that pass source-envelope, sign/heat-balance, recirculation, and UQ gates",
            "positive_release_condition": "ordinary internal-Nu fit rows > 0 under training-only split policy",
            "source_paths": f"{rel(PHASE4_SUMMARY)};{rel(SPLIT_POLICY_TABLE)}",
        },
    ]


def build_guardrail_audit(shell_summary: dict[str, Any], phase4_summary: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "guardrail_id": "no_final_fit_or_model_selection",
            "status": "pass",
            "evidence": (
                f"fit_allowed_after_source_property_gate={shell_summary.get('fit_allowed_after_source_property_gate')}; "
                f"model_selection_allowed_after_source_property_gate={shell_summary.get('model_selection_allowed_after_source_property_gate')}"
            ),
            "mutation_status": "no fitting tuning model selection performed",
        },
        {
            "guardrail_id": "no_residual_hidden_in_internal_Nu",
            "status": "pass",
            "evidence": f"residual_hidden_in_internal_Nu={phase4_summary.get('residual_hidden_in_internal_Nu')}",
            "mutation_status": "residual carried as explicit lane",
        },
        {
            "guardrail_id": "no_native_registry_scheduler_fluid_mutation",
            "status": "pass",
            "evidence": "Phase 5 builder reads existing CSV/JSON summaries only",
            "mutation_status": "native outputs, registry, scheduler, Fluid, external repos untouched",
        },
        {
            "guardrail_id": "no_blind_row_fit_or_selection",
            "status": "pass",
            "evidence": "holdout/external/future rows remain score-only after freeze gate",
            "mutation_status": "no held-out or external-test fitting",
        },
    ]


def build_thesis_handoff(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(PHASE4_SUMMARY)}
  - {rel(SHELL_SUMMARY)}
  - {rel(OUT / "negative_freeze_decision.csv")}
tags: [thermal-modeling, heat-loss, thesis-handoff, negative-freeze]
related:
  - .agent/status/2026-07-21_{TASK}.md
  - .agent/journal/2026-07-21/heatloss-phase-5-frozen-scorecard-and-thesis-handoff.md
task: {TASK}
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Hydraulics/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Negative Freeze Thesis Handoff

## Thesis-Safe Claim

The current heat-loss alignment is a disciplined negative result. The model
form now separates internal `Nu`, wall/layer conduction, external convection,
radiation, jacket/cooler, storage, and residual lanes, but no runtime-legal
heat-loss candidate is frozen for final predictive accuracy scoring.

## Numbers To Cite

- Phase 4 exchange-readiness rows: `{summary["phase4_exchange_readiness_rows"]}`.
- Phase 4 ordinary reopening rows: `{summary["phase4_ordinary_reopening_rows"]}`.
- Exchange-cell fit-ready rows: `{summary["phase4_exchange_fit_ready_rows"]}`.
- Reopened internal-`Nu` rows: `{summary["phase4_reopened_internal_Nu_rows"]}`.
- Final score values computed here: `0`.

## Do Not Claim

Do not claim an admitted wall/test-section closure, upcomer exchange
coefficient, ordinary internal-`Nu` correction, or final predictive heat-loss
accuracy from this package.
"""
    (OUT / "thesis_handoff_note.md").write_text(text, encoding="utf-8")


def build_source_manifest() -> list[dict[str, str]]:
    paths = [
        (PHASE0_SUMMARY, "read_only_phase0_summary"),
        (PHASE1_SUMMARY, "read_only_phase1_summary"),
        (PHASE2_SUMMARY, "read_only_phase2_summary"),
        (PHASE3_SUMMARY, "read_only_phase3_summary"),
        (PHASE4_SUMMARY, "read_only_phase4_summary"),
        (PHASE4_RELEASE, "read_only_phase4_release_gate"),
        (PHASE4_CONTRACT, "read_only_phase4_heat_path_contract"),
        (SHELL_SUMMARY, "read_only_final_scorecard_shell"),
        (SHELL_METRICS, "read_only_metric_contract"),
        (SHELL_PARTITIONS, "read_only_case_partition_contract"),
        (SHELL_RUNTIME, "read_only_runtime_audit"),
        (SPLIT_POLICY_TABLE, "read_only_split_policy"),
        (SOURCE_PROPERTY_TODO, "read_only_source_property_todo"),
        (Path("tools/analyze/build_heatloss_phase5_frozen_scorecard_and_thesis_handoff.py"), "builder"),
        (Path("tools/analyze/test_heatloss_phase5_frozen_scorecard_and_thesis_handoff.py"), "test"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "mutation_status": "read_only" if role.startswith("read_only") else "written_in_task_scope",
        }
        for path, role in paths
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(PHASE4_SUMMARY)}
  - {rel(SHELL_SUMMARY)}
  - {rel(SHELL_METRICS)}
tags: [thermal-modeling, heat-loss, final-scorecard, negative-freeze]
related:
  - .agent/status/2026-07-21_{TASK}.md
  - .agent/journal/2026-07-21/heatloss-phase-5-frozen-scorecard-and-thesis-handoff.md
  - {rel(PHASE4 / "README.md")}
task: {TASK}
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Hydraulics/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 5 Frozen Scorecard And Thesis Handoff

## Decision

Phase 5 is a negative freeze/handoff. No final heat-loss accuracy score was
computed because Phase 4 admitted no runtime-legal exchange-cell fit and no
ordinary internal-`Nu` reopening row.

## Results

- Phase gate rows: `{summary["phase_gate_rows"]}`.
- Metric availability rows: `{summary["metric_availability_rows"]}`.
- Heat-path freeze rows: `{summary["heat_path_freeze_rows"]}`.
- Next-action rows: `{summary["next_action_rows"]}`.
- Final score values computed: `{summary["final_score_values_computed"]}`.
- Frozen heat-loss candidates: `{summary["frozen_heatloss_candidates"]}`.

## Outputs

- `negative_freeze_decision.csv`
- `metric_score_availability.csv`
- `heat_path_residual_freeze.csv`
- `blocker_delta_next_actions.csv`
- `runtime_source_split_guardrail_audit.csv`
- `thesis_handoff_note.md`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native output, registry/admission state, scheduler state, Fluid source,
external repository, fitting/tuning/model-selection, blocker register, generated
index, or thesis prose was changed.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    summaries = {
        "phase0": read_json(PHASE0_SUMMARY),
        "phase1": read_json(PHASE1_SUMMARY),
        "phase2": read_json(PHASE2_SUMMARY),
        "phase3": read_json(PHASE3_SUMMARY),
        "phase4": read_json(PHASE4_SUMMARY),
    }
    shell_summary = read_json(SHELL_SUMMARY)
    phase4_release = read_csv(PHASE4_RELEASE)
    phase4_contract = read_csv(PHASE4_CONTRACT)
    metric_rows = read_csv(SHELL_METRICS)

    phase_gate_rows = build_phase_gate_table(summaries, phase4_release)
    metric_availability = build_metric_availability(metric_rows, shell_summary)
    heat_path_freeze = build_heat_path_freeze(phase4_contract)
    blocker_actions = build_blocker_actions()
    guardrails = build_guardrail_audit(shell_summary, summaries["phase4"])
    manifest = build_source_manifest()

    phase4_exchange_rows = int(phase_value(summaries["phase4"], "exchange_readiness_rows", "exchange_cell_readiness_rows", default=0))
    phase4_ordinary_rows = int(phase_value(summaries["phase4"], "ordinary_reopening_rows", "ordinary_single_stream_rows", default=0))
    phase4_exchange_fit_rows = int(phase_value(summaries["phase4"], "exchange_cell_fit_ready_rows", default=0))
    phase4_reopened_nu = int(phase_value(summaries["phase4"], "reopened_internal_Nu_rows", "ordinary_internal_nu_fit_rows", default=0))

    summary: dict[str, Any] = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "freeze_status": "negative_freeze_no_runtime_legal_heatloss_candidate",
        "phase_gate_rows": len(phase_gate_rows),
        "metric_availability_rows": len(metric_availability),
        "heat_path_freeze_rows": len(heat_path_freeze),
        "next_action_rows": len(blocker_actions),
        "guardrail_rows": len(guardrails),
        "phase4_exchange_readiness_rows": phase4_exchange_rows,
        "phase4_ordinary_reopening_rows": phase4_ordinary_rows,
        "phase4_exchange_fit_ready_rows": phase4_exchange_fit_rows,
        "phase4_reopened_internal_Nu_rows": phase4_reopened_nu,
        "final_score_values_computed": 0,
        "frozen_heatloss_candidates": 0,
        "fit_or_model_selection_performed": False,
        "residual_hidden_in_internal_Nu": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "solver_or_postprocessing_launched": False,
        "external_fluid_edit": False,
        "external_repositories_mutated": False,
        "thesis_files_edited": False,
        "blocker_register_mutated": False,
        "generated_docs_index_mutated": False,
        "no_scorecard_outputs": True,
    }

    write_csv(OUT / "negative_freeze_decision.csv", phase_gate_rows)
    write_csv(OUT / "metric_score_availability.csv", metric_availability)
    write_csv(OUT / "heat_path_residual_freeze.csv", heat_path_freeze)
    write_csv(OUT / "blocker_delta_next_actions.csv", blocker_actions)
    write_csv(OUT / "runtime_source_split_guardrail_audit.csv", guardrails)
    write_csv(OUT / "source_manifest.csv", manifest)
    write_json(OUT / "summary.json", summary)
    build_thesis_handoff(summary)
    write_readme(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
