#!/usr/bin/env python3
"""Refresh the forward-v1 gate state after Fluid API and audit evidence."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits"

FINAL_GATE_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/summary.json"
FINAL_GATE_CHECKLIST = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/forward_v1_gate_checklist.csv"
PM5_DELTA_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_forward_v1_pm5_hydraulic_delta/summary.json"
FLUID_API_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_fluid_reset_development_api/summary.json"
MDOT_AUDIT_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/summary.json"
SALT1_PM5_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/summary.json"
SALT1_TRAINING = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/salt1_training_admission_update.csv"
PM5_JOB_STATUS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/pm5_upcomer_job_harvest_status.csv"

SOURCES = [
    FINAL_GATE_SUMMARY,
    FINAL_GATE_CHECKLIST,
    PM5_DELTA_SUMMARY,
    FLUID_API_SUMMARY,
    MDOT_AUDIT_SUMMARY,
    SALT1_PM5_SUMMARY,
    SALT1_TRAINING,
    PM5_JOB_STATUS,
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def pm5_terminal(job_rows: list[dict[str, str]]) -> bool:
    terminal = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY"}
    return bool(job_rows) and all(row.get("sacct_state", "").split()[0] in terminal for row in job_rows)


def build_gate_rows() -> list[dict[str, Any]]:
    final = read_json(FINAL_GATE_SUMMARY)
    fluid = read_json(FLUID_API_SUMMARY)
    mdot = read_json(MDOT_AUDIT_SUMMARY)
    pm5_delta = read_json(PM5_DELTA_SUMMARY)
    salt1 = read_json(SALT1_PM5_SUMMARY)
    job_rows = read_csv(PM5_JOB_STATUS)
    terminal = pm5_terminal(job_rows)
    pm5_state = job_rows[0]["sacct_state"] if job_rows else "unknown"

    return [
        {
            "gate_id": "input_contract_and_split",
            "gate_group": "input_hygiene",
            "refreshed_status": "pass_locked",
            "blocks_final_forward_v1": "no",
            "admitted_now": final["current_split"],
            "required_landing_artifact": "documented split revision only if current split changes",
            "current_evidence": "Strict input contract remains active; no validation/holdout fitting.",
            "source_artifact": rel(FINAL_GATE_SUMMARY),
            "do_not_claim": "Do not revise split after inspecting validation or holdout residuals.",
        },
        {
            "gate_id": "fluid_reset_development_api",
            "gate_group": "implementation",
            "refreshed_status": "api_implemented_evidence_blocked",
            "blocks_final_forward_v1": "yes",
            "admitted_now": fluid["api_added"],
            "required_landing_artifact": "reset_development_pressure_scorecard.csv",
            "current_evidence": "Fluid can accept reset/development K separately, but no admitted reset/development pressure evidence exists.",
            "source_artifact": rel(FLUID_API_SUMMARY),
            "do_not_claim": "Do not call H1 launchable from API support alone.",
        },
        {
            "gate_id": "hydraulic_h1_pressure_evidence",
            "gate_group": "hydraulics",
            "refreshed_status": "blocked_zero_fit_rows",
            "blocks_final_forward_v1": "yes",
            "admitted_now": "diagnostic hydraulic tap refresh only",
            "required_landing_artifact": "fit-admissible component/cluster K or F6 pressure scorecard",
            "current_evidence": f"component_fit_admissible_rows={pm5_delta['component_fit_admissible_rows']}; h1_faithful_launchable={pm5_delta['h1_faithful_launchable']}",
            "source_artifact": rel(PM5_DELTA_SUMMARY),
            "do_not_claim": "Do not tune thermal terms while mdot/hydraulic guardrail is unresolved.",
        },
        {
            "gate_id": "mdot_temperature_residual_audit",
            "gate_group": "residual_attribution",
            "refreshed_status": "diagnostic_evidence_landed",
            "blocks_final_forward_v1": "no",
            "admitted_now": "residual attribution evidence only",
            "required_landing_artifact": "forward_v1_residual_attribution_scorecard.csv",
            "current_evidence": f"model_result_rows={mdot['model_result_rows']}; sensor_error_rows={mdot['sensor_error_rows']}; heat_score_rows={mdot['heat_score_rows']}",
            "source_artifact": rel(MDOT_AUDIT_SUMMARY),
            "do_not_claim": "Do not treat CFD-informed heat-flux modes as setup-only predictive closure.",
        },
        {
            "gate_id": "salt1_training_conflict_resolution",
            "gate_group": "cfd_admission",
            "refreshed_status": "resolved_context_training_evidence",
            "blocks_final_forward_v1": "no",
            "admitted_now": "Salt1 hi10q conflict removed; Salt1 remains outside current Salt2/Salt3/Salt4 score split",
            "required_landing_artifact": "documented split revision before Salt1 affects final scorecard rows",
            "current_evidence": f"salt1_hi10q_conflict_removed={salt1['salt1_hi10q_conflict_removed']}; salt1_patch_rows={salt1['salt1_patch_rows']}",
            "source_artifact": rel(SALT1_PM5_SUMMARY),
            "do_not_claim": "Do not collapse perturbed-Q Salt1 rows into nominal Salt1 or Salt2/Salt3/Salt4 split rows.",
        },
        {
            "gate_id": "pm5_matched_pressure_upcomer_metrics",
            "gate_group": "cfd_pp_hydraulic_thermal",
            "refreshed_status": "pending_terminal" if not terminal else "terminal_needs_admission_review",
            "blocks_final_forward_v1": "yes",
            "admitted_now": "none",
            "required_landing_artifact": "pm5_corrected_q_matched_pressure_upcomer_metrics.csv",
            "current_evidence": f"job 3295901 sacct_state={pm5_state}; parsed_files_present={salt1['pm5_parsed_files_present']}",
            "source_artifact": rel(PM5_JOB_STATUS),
            "do_not_claim": "Do not infer F6, onset, or internal-Nu evidence from terminal harvest alone.",
        },
        {
            "gate_id": "perturbation_split_policy",
            "gate_group": "split_policy",
            "refreshed_status": "blocked_pending_policy",
            "blocks_final_forward_v1": "yes_if_expanding_training_data",
            "admitted_now": "0 independent +/-5Q training expansion rows",
            "required_landing_artifact": "perturbation_split_policy_update.csv",
            "current_evidence": f"pm5_harvest_rows={pm5_delta['pm5_harvest_rows']}; independent_training_expansion_rows={pm5_delta['independent_training_expansion_rows']}",
            "source_artifact": rel(PM5_DELTA_SUMMARY),
            "do_not_claim": "Do not add +/-5Q rows as independent training rows.",
        },
        {
            "gate_id": "thermal_internal_nu",
            "gate_group": "thermal",
            "refreshed_status": "blocked_no_fit_rows",
            "blocks_final_forward_v1": "yes_for_thermal_closure_claims",
            "admitted_now": "baseline/literature/default internal Nu only",
            "required_landing_artifact": "thermal admission gate with fit-admissible rows plus matched-plane extraction",
            "current_evidence": "Final gate still rejects fitted internal-Nu consumption; diagnostic upcomer Nu remains validation-only.",
            "source_artifact": rel(FINAL_GATE_SUMMARY),
            "do_not_claim": "Do not fit or consume diagnostic internal-Nu rows as closure data.",
        },
        {
            "gate_id": "boundary_hx_wall_radiation",
            "gate_group": "boundary_hx",
            "refreshed_status": "blocked_setup_only_outputs_missing",
            "blocks_final_forward_v1": "yes",
            "admitted_now": "architecture, diagnostics, and score targets only",
            "required_landing_artifact": "setup_only_boundary_hx_outputs.csv",
            "current_evidence": "Imposed cooler duty and realized wallHeatFlux remain diagnostic/runtime-disallowed for final predictive HX.",
            "source_artifact": rel(FINAL_GATE_CHECKLIST),
            "do_not_claim": "Do not call imposed cooler duty or realized wallHeatFlux replay final predictive HX.",
        },
        {
            "gate_id": "sensor_map_policy",
            "gate_group": "sensors",
            "refreshed_status": "partial_provisional_only",
            "blocks_final_forward_v1": "yes_for_complete_sensor_claim",
            "admitted_now": "diagnostic post-solve sensor residuals only",
            "required_landing_artifact": "sensor exclusion or coordinate upgrade policy",
            "current_evidence": "AGENT-360 produced sensor residual audit; sensor temperatures are still targets only.",
            "source_artifact": rel(MDOT_AUDIT_SUMMARY),
            "do_not_claim": "Do not use sensor temperatures as runtime inputs or sensor-wise corrections.",
        },
    ]


def build_input_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "lane": "cfd_admission",
            "current_status": "partial_progress",
            "admitted_use_now": "Salt2/Salt3/Salt4 original split plus Salt1 context/training evidence outside final split",
            "pending_or_blocked": "PM5 matched pressure/upcomer job 3295901 pending terminal harvest",
            "required_landing_artifact": "pm5_corrected_q_matched_pressure_upcomer_metrics.csv",
            "scorecard_use_when_landed": "may support F6/onset/admission rows after explicit admission review",
            "runtime_input_guardrail": "CFD metrics join after solve; no runtime leakage",
        },
        {
            "lane": "hydraulics",
            "current_status": "api_ready_evidence_blocked",
            "admitted_use_now": "Fluid reset/development API implemented; tap-length diagnostics citeable",
            "pending_or_blocked": "0 fit-admissible component/cluster K rows; no admitted reset/development pressure evidence",
            "required_landing_artifact": "reset_development_pressure_scorecard.csv or f6_phi_re_hydraulic_scorecard.csv",
            "scorecard_use_when_landed": "mdot primary score and hydraulic residual attribution",
            "runtime_input_guardrail": "no thermal fitting to repair mdot",
        },
        {
            "lane": "boundary_hx",
            "current_status": "score_targets_only",
            "admitted_use_now": "+/-5Q heat targets and diagnostic heat-loss placement",
            "pending_or_blocked": "setup-only HX/external-boundary outputs missing",
            "required_landing_artifact": "setup_only_boundary_hx_outputs.csv",
            "scorecard_use_when_landed": "boundary/HX heat residuals without CFD duty runtime input",
            "runtime_input_guardrail": "no imposed CFD cooler duty or realized wallHeatFlux at runtime",
        },
        {
            "lane": "thermal_internal_nu",
            "current_status": "blocked_no_fit_rows",
            "admitted_use_now": "baseline/literature/default internal Nu behavior only",
            "pending_or_blocked": "recirculation, mesh/GCI, matched-plane, sign, and heat-balance gates",
            "required_landing_artifact": "thermal_internal_nu_admission_refresh.csv",
            "scorecard_use_when_landed": "thermal residual attribution and possible closure row only if admitted",
            "runtime_input_guardrail": "diagnostic Nu rows cannot become fitted closure data",
        },
        {
            "lane": "sensors",
            "current_status": "diagnostic_postsolve",
            "admitted_use_now": "AGENT-360 TP/TW residual audit",
            "pending_or_blocked": "blocked/provisional labels need exclusion or coordinate upgrade policy",
            "required_landing_artifact": "sensor_map_policy_refresh.csv",
            "scorecard_use_when_landed": "complete sensor score with exclusions documented",
            "runtime_input_guardrail": "sensor temperatures are validation targets only",
        },
        {
            "lane": "forward_v1_final_score",
            "current_status": "blocked_no_go",
            "admitted_use_now": "scorecard skeleton and no-go attribution",
            "pending_or_blocked": "upstream cfd/hydraulic/boundary/thermal gates",
            "required_landing_artifact": "forward_v1_residual_attribution_scorecard.csv",
            "scorecard_use_when_landed": "final admitted score only if all blocking gates pass",
            "runtime_input_guardrail": "fail closed on any blocked required gate",
        },
    ]


def build_burndown_rows(gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in gate_rows:
        if row["blocks_final_forward_v1"] in {"yes", "yes_if_expanding_training_data", "yes_for_thermal_closure_claims", "yes_for_complete_sensor_claim"}:
            rows.append(
                {
                    "blocker_id": row["gate_id"],
                    "severity": "high" if row["blocks_final_forward_v1"] == "yes" else "medium",
                    "current_status": row["refreshed_status"],
                    "evidence_now": row["current_evidence"],
                    "required_landing_artifact": row["required_landing_artifact"],
                    "owner_lane": row["gate_group"],
                    "allowed_current_use": row["admitted_now"],
                    "do_not_claim": row["do_not_claim"],
                }
            )
    return rows


def build_residual_rows() -> list[dict[str, Any]]:
    return [
        {
            "residual_lane": "hydraulic_mdot",
            "formula": "e_mdot = mdot_1d - mdot_cfd",
            "current_input_status": "api_ready_evidence_blocked",
            "score_status": "blocked",
            "admitted_inputs_now": "Fluid reset/development API; diagnostic mdot audit",
            "pending_inputs": "admitted pressure-loss rows and reset/development or F6 scorecard",
            "output_columns_to_fill": "case_id,split,mdot_1d,mdot_cfd,e_mdot,e_mdot_pct,hydraulic_model_id",
            "do_not_claim": "Do not repair mdot with thermal tuning.",
        },
        {
            "residual_lane": "boundary_hx_heat",
            "formula": "e_Q(role) = Q_1d(role) - Q_cfd_reference(role)",
            "current_input_status": "diagnostic_score_targets_only",
            "score_status": "blocked",
            "admitted_inputs_now": "+/-5Q heat-role targets; heat-loss discrepancy diagnostics",
            "pending_inputs": "setup-only boundary/HX outputs",
            "output_columns_to_fill": "case_id,split,role,Q_1d_W,Q_reference_W,e_Q_W,runtime_input_policy",
            "do_not_claim": "Do not use CFD cooler duty or realized wallHeatFlux as predictive runtime inputs.",
        },
        {
            "residual_lane": "sensor_temperature",
            "formula": "e_T(sensor) = T_1d(sensor) - T_cfd(sensor)",
            "current_input_status": "diagnostic_postsolve",
            "score_status": "partial",
            "admitted_inputs_now": "AGENT-360 residual audit rows",
            "pending_inputs": "sensor exclusion/coordinate upgrade policy for complete claim",
            "output_columns_to_fill": "case_id,split,sensor_id,T_1d_K,T_cfd_K,e_T_K,scoreable_flag",
            "do_not_claim": "Do not use sensor temperatures as fitted inputs.",
        },
        {
            "residual_lane": "internal_nu_thermal",
            "formula": "e_T_section = T_1d_section - T_cfd_section",
            "current_input_status": "blocked_no_fit_rows",
            "score_status": "blocked",
            "admitted_inputs_now": "default/literature internal Nu only",
            "pending_inputs": "matched-plane extraction and thermal admission gate",
            "output_columns_to_fill": "case_id,section,Nu_model_id,T_1d_K,T_cfd_K,e_T_section_K,admission_status",
            "do_not_claim": "Do not consume diagnostic upcomer Nu as trainable closure data.",
        },
        {
            "residual_lane": "cfd_admission_uncertainty",
            "formula": "e_metric = metric_candidate - metric_reference",
            "current_input_status": "pending_terminal_pm5_metrics",
            "score_status": "pending",
            "admitted_inputs_now": "terminal harvest and Salt1 BC conflict resolution only",
            "pending_inputs": "PM5 matched pressure/upcomer metrics and perturbation split policy",
            "output_columns_to_fill": "case_id,variant,metric,split_policy,admission_status,uncertainty_note",
            "do_not_claim": "Do not expand training rows before a dated perturbation split policy.",
        },
    ]


def build_perturbation_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "row_id": "salt2_lo5q",
            "family": "corrected_q_pm5",
            "current_split_relationship": "salt2_train_family_sensitivity",
            "current_use": "terminal-harvested sensitivity/admission evidence",
            "independent_training_expansion_now": "no",
            "required_before_reclassification": "dated perturbation split policy plus matched pressure/upcomer metric admission",
            "do_not_claim": "Do not add as independent train row.",
        },
        {
            "row_id": "salt2_hi5q",
            "family": "corrected_q_pm5",
            "current_split_relationship": "salt2_train_family_sensitivity",
            "current_use": "terminal-harvested sensitivity/admission evidence",
            "independent_training_expansion_now": "no",
            "required_before_reclassification": "dated perturbation split policy plus matched pressure/upcomer metric admission",
            "do_not_claim": "Do not add as independent train row.",
        },
        {
            "row_id": "salt4_lo5q",
            "family": "corrected_q_pm5",
            "current_split_relationship": "salt4_holdout_family_sensitivity",
            "current_use": "holdout-family sensitivity/admission evidence",
            "independent_training_expansion_now": "no",
            "required_before_reclassification": "dated perturbation split policy plus matched pressure/upcomer metric admission",
            "do_not_claim": "Do not use for model selection.",
        },
        {
            "row_id": "salt4_hi5q",
            "family": "corrected_q_pm5",
            "current_split_relationship": "salt4_holdout_family_sensitivity",
            "current_use": "holdout-family sensitivity/admission evidence",
            "independent_training_expansion_now": "no",
            "required_before_reclassification": "dated perturbation split policy plus matched pressure/upcomer metric admission",
            "do_not_claim": "Do not use for model selection.",
        },
    ]
    for source in read_csv(SALT1_TRAINING):
        rows.append(
            {
                "row_id": source["case_id"],
                "family": "salt1_training_context",
                "current_split_relationship": source["split_role"],
                "current_use": source["admission_decision"],
                "independent_training_expansion_now": "outside_current_salt234_final_score_split",
                "required_before_reclassification": "documented split revision before Salt1 affects final Salt2/Salt3/Salt4 scorecard",
                "do_not_claim": source["remaining_guardrail"],
            }
        )
    return rows


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(FINAL_GATE_SUMMARY)}
  - {rel(FLUID_API_SUMMARY)}
  - {rel(MDOT_AUDIT_SUMMARY)}
  - {rel(SALT1_PM5_SUMMARY)}
  - {rel(PM5_DELTA_SUMMARY)}
tags: [forward-model, forward-v1, scorecard, hydraulics, boundary-conditions]
related:
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-366
date: 2026-07-14
role: Forward-pred/Scientific-closure/Implementer/Tester/Writer
type: work_product
status: complete
---
# Forward-v1 Gate Refresh After Fluid API And Audits

## Decision

Final forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted`.

This package refreshes the final-gate state after three gate-moving updates:
Fluid reset/development API support landed, the mdot/TP/TW audit landed, and
Salt1 terminal BC conflict evidence landed. These are real progress, but none
admits final forward-v1.

## What Changed

- Fluid can now accept `MinorLosses.reset_development_k_by_segment`, but H1 is
  still blocked by missing admitted pressure/reset-development evidence.
- The mdot/temperature audit adds residual-attribution evidence:
  `{summary['mdot_model_result_rows']}` model result rows and
  `{summary['sensor_error_rows']}` sensor error rows.
- Salt1 hi10q's stale conflict is resolved as perturbed-Q training evidence,
  but Salt1 does not silently enter the current Salt2/Salt3/Salt4 final split.
- PM5 matched pressure/upcomer metrics remain pending because job `3295901` is
  `{summary['pm5_job_state']}` with `{summary['pm5_parsed_files_present']}`
  parsed metric files present.

## Current Blocking State

- Gate rows refreshed: `{summary['gate_rows']}`.
- Blocking rows: `{summary['blocking_rows']}`.
- Final forward-v1 admitted: `{str(summary['forward_v1_admitted']).lower()}`.
- Current split: `{summary['current_split']}`.

## Runtime Input Rules

- No CFD mdot as a model input.
- No realized CFD `wallHeatFlux` as a predictive runtime input.
- No imposed CFD cooler duty as final predictive HX evidence.
- No validation or holdout temperatures used for fitting.
- No diagnostic internal Nu row consumed as trainable closure data.

## Files

- `forward_v1_gate_checklist_refreshed.csv`
- `forward_v1_scorecard_input_contract_next.csv`
- `forward_v1_blocking_gate_burndown.csv`
- `forward_v1_residual_attribution_skeleton.csv`
- `perturbation_split_policy_next.csv`
- `math_assumptions_theory.md`
- `source_manifest.csv`
- `summary.json`

## Documentation Note

The forward-model map and thesis README are intentionally not edited here
because AGENT-365 currently owns those additive link paths. Add cross-links
after that lane closes.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_math_note(out: Path) -> None:
    text = """---
provenance:
  - source_manifest.csv
tags: [forward-model, math, assumptions, residual-attribution]
related:
  - README.md
task: AGENT-366
date: 2026-07-14
role: Forward-pred/Scientific-closure
type: method_note
status: complete
---
# Math, Assumptions, Theory, And Results

## Purpose

Forward-v1 predicts loop mass flow and TP/TW temperatures from setup-level
inputs only. CFD observations are joined after the solve for scoring and
residual attribution.

## Residual Definitions

- Mass-flow residual: `e_mdot = mdot_1d - mdot_cfd`.
- Sensor residual: `e_T(sensor) = T_1d(sensor) - T_cfd(sensor)`.
- Role heat residual: `e_Q(role) = Q_1d(role) - Q_cfd_reference(role)`.
- Section thermal residual: `e_T_section = T_1d_section - T_cfd_section`.

## Attribution Lanes

- `hydraulic_mdot`: friction, localized loss, reset/development, and pressure
  evidence.
- `boundary_hx_heat`: setup-only cooler/HX and external-wall heat removal.
- `sensor_temperature`: post-solve TP/TW comparison only.
- `internal_nu_thermal`: internal heat-transfer closure; currently blocked for
  fitting.
- `cfd_admission_uncertainty`: terminal state, split policy, and metric
  admission quality.

## Assumptions

- The active final split remains `salt_2=train`, `salt_3=validation`,
  `salt_4=holdout`.
- Fluid reset/development API support is implemented, but this is not pressure
  evidence.
- Salt1 terminal BC rows are training-context evidence only until a dated split
  revision admits them to a final scorecard population.
- +/-5Q corrected-Q rows are sensitivity/admission evidence only; they add zero
  independent training rows today.
- CFD `rcExternalTemperature` embeds radiation metadata; do not add a separate
  radiation correction on top of CFD wallHeatFlux-derived diagnostics.

## Results From This Refresh

- Final forward-v1 remains blocked.
- Scorecard-ready input lanes are now explicit.
- Residual-attribution output columns are predefined for the next runnable
  scorecard.
- PM5 matched pressure/upcomer metrics remain the first pending gate.
"""
    (out / "math_assumptions_theory.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    final = read_json(FINAL_GATE_SUMMARY)
    fluid = read_json(FLUID_API_SUMMARY)
    mdot = read_json(MDOT_AUDIT_SUMMARY)
    salt1 = read_json(SALT1_PM5_SUMMARY)
    job_rows = read_csv(PM5_JOB_STATUS)
    gate_rows = build_gate_rows()
    input_rows = build_input_contract_rows()
    burndown_rows = build_burndown_rows(gate_rows)
    residual_rows = build_residual_rows()
    perturbation_rows = build_perturbation_rows()

    write_csv(
        out / "forward_v1_gate_checklist_refreshed.csv",
        gate_rows,
        [
            "gate_id",
            "gate_group",
            "refreshed_status",
            "blocks_final_forward_v1",
            "admitted_now",
            "required_landing_artifact",
            "current_evidence",
            "source_artifact",
            "do_not_claim",
        ],
    )
    write_csv(
        out / "forward_v1_scorecard_input_contract_next.csv",
        input_rows,
        [
            "lane",
            "current_status",
            "admitted_use_now",
            "pending_or_blocked",
            "required_landing_artifact",
            "scorecard_use_when_landed",
            "runtime_input_guardrail",
        ],
    )
    write_csv(
        out / "forward_v1_blocking_gate_burndown.csv",
        burndown_rows,
        [
            "blocker_id",
            "severity",
            "current_status",
            "evidence_now",
            "required_landing_artifact",
            "owner_lane",
            "allowed_current_use",
            "do_not_claim",
        ],
    )
    write_csv(
        out / "forward_v1_residual_attribution_skeleton.csv",
        residual_rows,
        [
            "residual_lane",
            "formula",
            "current_input_status",
            "score_status",
            "admitted_inputs_now",
            "pending_inputs",
            "output_columns_to_fill",
            "do_not_claim",
        ],
    )
    write_csv(
        out / "perturbation_split_policy_next.csv",
        perturbation_rows,
        [
            "row_id",
            "family",
            "current_split_relationship",
            "current_use",
            "independent_training_expansion_now",
            "required_before_reclassification",
            "do_not_claim",
        ],
    )
    write_csv(
        out / "source_manifest.csv",
        [{"artifact": path.name, "role": "source", "path": rel(path)} for path in SOURCES],
        ["artifact", "role", "path"],
    )

    summary = {
        "task": "AGENT-366",
        "generated_at_utc": utc_now(),
        "final_forward_v1_status": final["final_forward_v1_status"],
        "forward_v1_admitted": False,
        "current_split": final["current_split"],
        "gate_rows": len(gate_rows),
        "blocking_rows": len(burndown_rows),
        "fluid_reset_development_api_implemented": bool(fluid["api_added"]),
        "h1_launchable_after_fluid_api": fluid["h1_launchable_after_this_slice"],
        "mdot_model_result_rows": mdot["model_result_rows"],
        "sensor_error_rows": mdot["sensor_error_rows"],
        "salt1_hi10q_conflict_removed": salt1["salt1_hi10q_conflict_removed"],
        "salt1_affects_current_salt234_score_split": False,
        "pm5_job_state": job_rows[0]["sacct_state"] if job_rows else "unknown",
        "pm5_job_terminal": pm5_terminal(job_rows),
        "pm5_parsed_files_present": salt1["pm5_parsed_files_present"],
        "pm5_independent_training_expansion_rows": read_json(PM5_DELTA_SUMMARY)["independent_training_expansion_rows"],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_modified_by_this_task": False,
        "map_links_deferred_due_active_agent365": True,
    }

    write_math_note(out)
    write_readme(out, summary)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build_package(args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
