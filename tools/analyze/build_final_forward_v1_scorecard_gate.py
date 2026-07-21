#!/usr/bin/env python3
"""Build the final forward-v1 scorecard gate from admitted evidence only."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate"
H1_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard"
    / "h1_hydraulic_scorecard.csv"
)
READINESS_BLOCKERS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy"
    / "blockers_to_final_forward_v1.csv"
)
SPLIT_GUARDRAIL = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy"
    / "train_validation_holdout_guardrail.csv"
)
THERMAL_GATE = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate"
    / "summary.json"
)
THERMAL_SEGMENTS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate"
    / "segment_thermal_fit_summary.csv"
)
BOUNDARY_DECISION = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision"
    / "decision_table.csv"
)
FLUID_API_SUMMARY = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_fluid_localized_h1_and_boundary_api"
    / "summary.json"
)
CORRECTED_Q_SUMMARY = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate"
    / "summary.json"
)
SENSOR_MAP_SUMMARY = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract"
    / "summary.json"
)
MATH_REGISTER = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_math_theory_assumptions_results_register"
    / "result_intake_contract.csv"
)
UPCOMER_RECIRC_SUMMARY = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"
    / "summary.json"
)
UPCOMER_RECIRC_CONDITIONS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"
    / "upcomer_recirculation_onset_conditions.csv"
)
UPCOMER_NAMING_RULES = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"
    / "coefficient_naming_rules_for_recirculation.csv"
)
UPCOMER_BLOCKED_METRICS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"
    / "blocked_missing_metrics.csv"
)

GATE_COLUMNS = [
    "gate_id",
    "gate_group",
    "required_before_final_scoring",
    "gate_status",
    "blocks_final_forward_v1",
    "admitted_now",
    "pending_from_agent",
    "required_landing_artifact",
    "pass_criteria",
    "current_evidence",
    "source_artifact",
    "do_not_claim",
]
WAITING_COLUMNS = [
    "input_id",
    "owning_lane_or_agent",
    "required_for",
    "expected_artifact",
    "expected_fields_or_contract",
    "current_status",
    "current_blocker",
    "how_scorecard_will_consume",
    "current_fallback",
    "source_artifact",
]
INTERNAL_NU_DEPENDENCY_COLUMNS = [
    "dependency_id",
    "owning_lane_or_agent",
    "gate_reopen_requirement",
    "current_status",
    "why_it_blocks_internal_nu_fit",
    "required_evidence_before_reopen",
    "scorecard_policy_until_resolved",
    "source_artifact",
]
SCORE_COLUMNS = [
    "case_id",
    "split_assignment",
    "variant_id",
    "score_status",
    "cfd_mdot_kg_s",
    "baseline_mdot_error_vs_cfd_kg_s",
    "h1_mdot_error_vs_cfd_kg_s",
    "h1_abs_mdot_error_pct",
    "mdot_error_reduction_pct",
    "thermal_fit_used",
    "forward_v1_decision",
]
MANIFEST_COLUMNS = ["artifact", "role", "mutation_status", "path"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def corrected_q_status(summary: dict[str, Any]) -> str:
    return str(summary.get("admission_decision") or summary.get("row_classification") or "pending")


def corrected_q_state(summary: dict[str, Any]) -> str:
    return str(summary.get("job_state") or summary.get("top_level_state") or "unknown")


def corrected_q_terminal(summary: dict[str, Any]) -> Any:
    return summary.get("post_exit_gate_passed", summary.get("terminal"))


def h1_score_rows(h1_csv: Path) -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(h1_csv):
        rows.append(
            {
                "case_id": row["case_id"],
                "split_assignment": row["split_assignment"],
                "variant_id": row["h1_variant_id"],
                "score_status": "diagnostic_h1_proxy_not_final_forward_v1",
                "cfd_mdot_kg_s": row["cfd_mdot_kg_s"],
                "baseline_mdot_error_vs_cfd_kg_s": row["baseline_mdot_error_vs_cfd_kg_s"],
                "h1_mdot_error_vs_cfd_kg_s": row["h1_mdot_error_vs_cfd_kg_s"],
                "h1_abs_mdot_error_pct": row["h1_abs_mdot_error_pct"],
                "mdot_error_reduction_pct": row["mdot_error_reduction_pct"],
                "thermal_fit_used": row["thermal_fit_used"],
                "forward_v1_decision": "not_admitted_localized_h1_and_thermal_hx_gates_open",
            }
        )
    return rows


def gate_rows(
    thermal_summary: dict[str, Any],
    fluid_summary: dict[str, Any],
    corrected_q_summary: dict[str, Any],
    sensor_summary: dict[str, Any],
    upcomer_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    blockers = {row["blocker_id"]: row for row in read_csv(READINESS_BLOCKERS)}
    return [
        {
            "gate_id": "input_contract_and_split",
            "gate_group": "input_hygiene",
            "required_before_final_scoring": "yes",
            "gate_status": "pass_locked",
            "blocks_final_forward_v1": "no",
            "admitted_now": "strict input contract; salt_2=train, salt_3=validation, salt_4=holdout",
            "pending_from_agent": "none unless a documented split supersedes current split",
            "required_landing_artifact": "documented split revision only if current split changes",
            "pass_criteria": "No runtime CFD mdot, realized CFD wallHeatFlux, or validation temperatures; no validation/holdout fitting.",
            "current_evidence": "Current split locked and admitted for forward-v0 scoring.",
            "source_artifact": rel(SPLIT_GUARDRAIL),
            "do_not_claim": "Do not revise the split after inspecting validation or holdout residuals.",
        },
        {
            "gate_id": "hydraulic_localized_h1",
            "gate_group": "hydraulics",
            "required_before_final_scoring": "yes",
            "gate_status": "blocked_proxy_only",
            "blocks_final_forward_v1": "yes",
            "admitted_now": "H1 directional/proxy scorecard only",
            "pending_from_agent": "hydraulics / AGENT-318",
            "required_landing_artifact": "Fluid localized named-loss/reset support plus rerun scorecard",
            "pass_criteria": "Localized H1 or successor hydraulic closure is implemented, not aggregate-only, and scored without thermal fitting.",
            "current_evidence": blockers["localized_h1_not_implemented"]["why_it_blocks"],
            "source_artifact": rel(H1_SCORECARD),
            "do_not_claim": "Do not call aggregate fixed-K H1 a final localized closure.",
        },
        {
            "gate_id": "hydraulic_mdot_bias",
            "gate_group": "hydraulics",
            "required_before_final_scoring": "yes",
            "gate_status": "blocked_positive_bias",
            "blocks_final_forward_v1": "yes",
            "admitted_now": "diagnostic/proxy mdot residual movement",
            "pending_from_agent": "hydraulics",
            "required_landing_artifact": "hydraulic scorecard with mdot guardrail decision",
            "pass_criteria": "No systematic mdot overprediction on validation and holdout, or an explicit no-go decision.",
            "current_evidence": blockers["h1_proxy_mdot_still_overpredicts"]["why_it_blocks"],
            "source_artifact": blockers["h1_proxy_mdot_still_overpredicts"]["source_artifact"],
            "do_not_claim": "Do not tune thermal terms while mdot guardrail is unresolved.",
        },
        {
            "gate_id": "thermal_internal_nu",
            "gate_group": "thermal",
            "required_before_final_scoring": "yes_for_thermal_score",
            "gate_status": "blocked_no_fit_rows",
            "blocks_final_forward_v1": "yes_for_thermal_closure_claims",
            "admitted_now": "validation-only or blocked thermal rows; no fit rows; baseline/literature/default internal Nu behavior only",
            "pending_from_agent": "internal-Nu / AGENT-319 plus cfd-pp onset candidates and therm-reconstr matched-plane extraction",
            "required_landing_artifact": "thermal admission/internal-Nu table with fit-admissible rows, cfd-pp onset candidates, and matched-plane thermal/vector extraction",
            "pass_criteria": "Thermal rows pass sign, heat-balance, downcomer policy, recirculation, mesh/admission, cfd-pp onset-candidate, and matched-plane extraction checks.",
            "current_evidence": (
                f"thermal final gate has {thermal_summary['fit_eligible_row_count']} fit rows and "
                f"{thermal_summary['blocked_row_count']} blocked rows; upcomer recirculation gate has "
                f"{upcomer_summary.get('fit_admissible_internal_nu_rows', 0)} fit-admissible internal-Nu rows"
            ),
            "source_artifact": rel(THERMAL_GATE),
            "do_not_claim": "Do not consume fitted internal Nu rows or treat diagnostic thermal rows as final predictive closure evidence.",
        },
        {
            "gate_id": "upcomer_section_effective_nu_diagnostic",
            "gate_group": "thermal",
            "required_before_final_scoring": "yes_for_any_internal_nu_fit_reopen",
            "gate_status": "diagnostic_validation_only_no_fit",
            "blocks_final_forward_v1": "yes_for_internal_nu_fit_reopen_no_for_default_predictive_run",
            "admitted_now": "Nu_section_effective_upcomer_diagnostic as diagnostic/validation-only evidence",
            "pending_from_agent": "cfd-pp onset candidates; therm-reconstr matched-plane extraction",
            "required_landing_artifact": "internal_nu_dependency_blockers.csv dependencies resolved plus a later thermal admission gate admitting specific rows",
            "pass_criteria": "A later gate must show non-recirculating or transition anchors, matched vector/thermal planes, direct wall-bulk/core Delta T, Gz, mesh/time uncertainty, and terminal CFD admission.",
            "current_evidence": (
                f"{upcomer_summary.get('n_onset_rows', 0)} upcomer diagnostic rows span "
                f"Re={upcomer_summary.get('re_min'):.3f}-{upcomer_summary.get('re_max'):.3f}, "
                f"backflow={upcomer_summary.get('backflow_min'):.6f}-{upcomer_summary.get('backflow_max'):.6f}; "
                "all remain recirculating"
            ),
            "source_artifact": rel(UPCOMER_NAMING_RULES),
            "do_not_claim": "Do not rename this diagnostic coefficient as universal Nu, transferable Nu, or trainable internal-Nu closure data.",
        },
        {
            "gate_id": "boundary_hx_wall_radiation",
            "gate_group": "boundary_hx",
            "required_before_final_scoring": "yes",
            "gate_status": "blocked_architecture_only",
            "blocks_final_forward_v1": "yes",
            "admitted_now": "architecture and guardrails only",
            "pending_from_agent": "BC-modeling / AGENT-318",
            "required_landing_artifact": "setup-only boundary/HX model outputs and Fluid API evidence",
            "pass_criteria": "Cooler/HX and external-boundary terms are setup-only and do not consume imposed CFD cooler duty as final evidence.",
            "current_evidence": blockers["predictive_hx_boundary_not_final"]["why_it_blocks"],
            "source_artifact": rel(BOUNDARY_DECISION),
            "do_not_claim": "Do not call imposed cooler duty or realized wallHeatFlux replay final predictive HX.",
        },
        {
            "gate_id": "fluid_api_support",
            "gate_group": "implementation",
            "required_before_final_scoring": "yes",
            "gate_status": "partial_localized_k_only" if fluid_summary.get("localized_fixed_k_hook_added") else "blocked",
            "blocks_final_forward_v1": "yes",
            "admitted_now": "localized fixed-K hook only" if fluid_summary.get("localized_fixed_k_hook_added") else "none",
            "pending_from_agent": "BC-modeling / hydraulics / AGENT-318",
            "required_landing_artifact": "Fluid support for localized H1 reset/redevelopment plus first-class external-boundary/HX dictionaries",
            "pass_criteria": "Fluid can run the selected setup-only forward mode with declared localized losses and boundary inputs.",
            "current_evidence": (
                "localized_fixed_k_hook_added="
                f"{fluid_summary.get('localized_fixed_k_hook_added')}; boundary_api_finalized="
                f"{fluid_summary.get('boundary_api_finalized')}; reset_redevelopment_implemented="
                f"{fluid_summary.get('reset_redevelopment_implemented')}"
            ),
            "source_artifact": rel(FLUID_API_SUMMARY),
            "do_not_claim": "Do not treat partial fixed-K hook as full external-boundary or reset/redevelopment support.",
        },
        {
            "gate_id": "sensor_map_policy",
            "gate_group": "sensors",
            "required_before_final_scoring": "yes_for_complete_sensor_score",
            "gate_status": sensor_summary.get("sensor_temperature_score_claim", "partial_provisional_only"),
            "blocks_final_forward_v1": "yes_for_complete_sensor_claim_no_for_partial_diagnostic_join",
            "admitted_now": f"{sensor_summary.get('n_provisional_diagnostic_score_allowed')} provisional diagnostic labels",
            "pending_from_agent": "sensor-map or scorecard owner",
            "required_landing_artifact": "sensor exclusion or coordinate upgrade policy",
            "pass_criteria": "TP/TW targets join after solve only; blocked labels are excluded or resolved.",
            "current_evidence": f"blocked sensors: {','.join(sensor_summary.get('blocked_sensor_scores', []))}",
            "source_artifact": rel(SENSOR_MAP_SUMMARY),
            "do_not_claim": "Do not use sensor temperatures as runtime inputs or sensor-wise corrections.",
        },
        {
            "gate_id": "cfd_pp_admitted_training_data",
            "gate_group": "cfd_admission",
            "required_before_final_scoring": "yes_if_expanding_training_data",
            "gate_status": corrected_q_status(corrected_q_summary),
            "blocks_final_forward_v1": "no_for_current_salt234_split_yes_for_new_rows",
            "admitted_now": f"{corrected_q_summary.get('corrected_q_rows_admitted', 0)} corrected-Q rows",
            "pending_from_agent": "cfd-pp / AGENT-320",
            "required_landing_artifact": "terminal corrected-Q or CFD admission inventory with BC labels and split eligibility",
            "pass_criteria": "Rows are terminal, admitted, source-labeled, BC-labeled, and explicitly assigned to train/validation/holdout or diagnostic-only.",
            "current_evidence": (
                f"job {corrected_q_summary.get('job_id')} state={corrected_q_state(corrected_q_summary)}; "
                f"terminal_or_post_exit_gate={corrected_q_terminal(corrected_q_summary)}"
            ),
            "source_artifact": rel(CORRECTED_Q_SUMMARY),
            "do_not_claim": "Do not admit corrected-Q rows from live scheduler state alone.",
        },
    ]


def waiting_input_rows(
    thermal_summary: dict[str, Any],
    fluid_summary: dict[str, Any],
    corrected_q_summary: dict[str, Any],
    upcomer_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "input_id": "cfd_pp_admitted_case_inventory",
            "owning_lane_or_agent": "cfd-pp / AGENT-320",
            "required_for": "optional expansion of training/validation/holdout rows beyond current Salt2/3/4 split",
            "expected_artifact": "case/run admission inventory or corrected-Q terminal admission table",
            "expected_fields_or_contract": "case_id; source_id; admission_status; split_eligibility; boundary_condition_labels; target_paths; time_window_status",
            "current_status": corrected_q_status(corrected_q_summary),
            "current_blocker": f"job_state={corrected_q_state(corrected_q_summary)}; terminal_or_post_exit_gate={corrected_q_terminal(corrected_q_summary)}",
            "how_scorecard_will_consume": "Append only rows marked admitted or validation-only; keep salt_2/salt_3/salt_4 split unless a dated split revision supersedes it.",
            "current_fallback": "Use current Salt2 train, Salt3 validation, Salt4 holdout only.",
            "source_artifact": rel(CORRECTED_Q_SUMMARY),
        },
        {
            "input_id": "localized_h1_hydraulic_scorecard",
            "owning_lane_or_agent": "hydraulics / AGENT-318",
            "required_for": "final mdot gate and hydraulic residual attribution",
            "expected_artifact": "localized H1 or successor hydraulic scorecard",
            "expected_fields_or_contract": "case_id; split_role; model_mode; localized_loss_terms; reset_terms; mdot_error_kg_s; pressure_residuals; admission_status; do_not_claim",
            "current_status": "partial_fixed_k_hook" if fluid_summary.get("localized_fixed_k_hook_added") else "pending",
            "current_blocker": f"localized_h1_final_closure_admitted={fluid_summary.get('localized_h1_final_closure_admitted')}; reset_redevelopment_implemented={fluid_summary.get('reset_redevelopment_implemented')}",
            "how_scorecard_will_consume": "Replace H1 proxy rows only if the artifact is not aggregate-only and reports no validation/holdout fitting.",
            "current_fallback": "Keep AGENT-310 H1 rows diagnostic/proxy.",
            "source_artifact": rel(FLUID_API_SUMMARY),
        },
        {
            "input_id": "setup_only_boundary_hx_outputs",
            "owning_lane_or_agent": "BC-modeling / AGENT-318",
            "required_for": "predictive thermal score without imposed cooler duty",
            "expected_artifact": "Fluid run or bridge package for external-boundary/HX/wall/radiation setup-only mode",
            "expected_fields_or_contract": "case_id; split_role; runtime_inputs; forbidden_runtime_inputs_used=false; Q_HX_model_W; Q_passive_W; radiation_policy; heat_residual_W",
            "current_status": "blocked_boundary_api_not_final",
            "current_blocker": f"boundary_api_finalized={fluid_summary.get('boundary_api_finalized')}",
            "how_scorecard_will_consume": "Populate HX/cooler, passive wall, radiation, and heat residual lanes after runtime-input audit passes.",
            "current_fallback": "Report imposed-cooler/HX1 rows as guardrailed proxy only.",
            "source_artifact": rel(FLUID_API_SUMMARY),
        },
        {
            "input_id": "thermal_internal_nu_admission",
            "owning_lane_or_agent": "internal-Nu / AGENT-319",
            "required_for": "thermal closure fit or thermal no-fit decision",
            "expected_artifact": "thermal admission/internal-Nu final table",
            "expected_fields_or_contract": "segment; qoi; admission_status; sign_policy; radiation_policy; fit_eligible; validation_only; blockers; source_paths",
            "current_status": "no_fit_rows",
            "current_blocker": (
                f"fit_eligible_row_count={thermal_summary.get('fit_eligible_row_count')}; "
                f"blocked_row_count={thermal_summary.get('blocked_row_count')}; "
                f"upcomer_fit_admissible_internal_nu_rows={upcomer_summary.get('fit_admissible_internal_nu_rows')}"
            ),
            "how_scorecard_will_consume": "Allow only fit-admissible rows into thermal closure fitting; validation-only rows can be scored after solve.",
            "current_fallback": "No internal Nu/HTC/UA fit; keep rows validation-only or blocked.",
            "source_artifact": rel(THERMAL_GATE),
        },
        {
            "input_id": "upcomer_section_effective_nu_diagnostic",
            "owning_lane_or_agent": "internal-Nu / AGENT-330",
            "required_for": "diagnostic/validation-only upcomer recirculation scoring; not closure fitting",
            "expected_artifact": "Nu_section_effective_upcomer_diagnostic rows plus naming/admission policy",
            "expected_fields_or_contract": "case_id; section; allowed_label=Nu_section_effective_upcomer_diagnostic; admitted_use=diagnostic_validation_only; excluded_use includes fit_closure; recirculation metrics; source_paths",
            "current_status": "diagnostic_validation_only",
            "current_blocker": (
                f"all {upcomer_summary.get('n_onset_rows')} rows are recirculation_cell_observed; "
                f"fit_admissible_internal_nu_rows={upcomer_summary.get('fit_admissible_internal_nu_rows')}"
            ),
            "how_scorecard_will_consume": "Join only as post-solve diagnostic context or validation-only section-effective evidence; never as a fitted Nu/HTC/UA row.",
            "current_fallback": "Use baseline/literature/default internal Nu behavior for predictive runs.",
            "source_artifact": rel(UPCOMER_NAMING_RULES),
        },
        {
            "input_id": "result_intake_contract",
            "owning_lane_or_agent": "all gate-moving agents / AGENT-322",
            "required_for": "scorecard ingestion hygiene",
            "expected_artifact": "result_intake_contract.csv-compatible outputs",
            "expected_fields_or_contract": "task_id; case_id; split_role; model_mode; runtime_inputs; forbidden_runtime_inputs_used; property_mode; equation_ids; fitted_parameters; fit_source_rows; admission_status; source_paths; do_not_claim",
            "current_status": "available",
            "current_blocker": "none for schema; upstream results must fill it",
            "how_scorecard_will_consume": "Reject or downgrade future rows that omit required fields or use forbidden runtime inputs.",
            "current_fallback": "Keep future rows waiting_on_agents until required fields are present.",
            "source_artifact": rel(MATH_REGISTER),
        },
    ]


def internal_nu_dependency_blockers_rows(
    thermal_summary: dict[str, Any],
    corrected_q_summary: dict[str, Any],
    upcomer_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "dependency_id": "no_fit_admissible_internal_nu_rows",
            "owning_lane_or_agent": "internal-Nu / forward-pred",
            "gate_reopen_requirement": "A later dated thermal admission gate must explicitly admit one or more internal-Nu rows.",
            "current_status": (
                f"thermal_fit_rows={thermal_summary.get('fit_eligible_row_count')}; "
                f"upcomer_fit_rows={upcomer_summary.get('fit_admissible_internal_nu_rows')}"
            ),
            "why_it_blocks_internal_nu_fit": "Current thermal and upcomer evidence is validation-only or blocked, so the scorecard has no legal training target for internal Nu.",
            "required_evidence_before_reopen": "Admission table with fit_eligible=yes, split_role=train, no validation/holdout fitting, and source paths to terminal/admitted CFD evidence.",
            "scorecard_policy_until_resolved": "Reject fitted internal Nu rows; run predictive cases with baseline/literature/default internal Nu behavior.",
            "source_artifact": rel(THERMAL_GATE),
        },
        {
            "dependency_id": "nu_section_effective_upcomer_diagnostic_label",
            "owning_lane_or_agent": "internal-Nu / AGENT-330",
            "gate_reopen_requirement": "Recirculating upcomer rows must use section-effective diagnostic names unless a later gate proves ordinary single-stream behavior.",
            "current_status": "Nu_section_effective_upcomer_diagnostic admitted only as diagnostic_validation_only",
            "why_it_blocks_internal_nu_fit": "Material backflow/Ri/recirculation makes universal or transferable single-stream Nu labels invalid for the observed Salt2-4 upcomer rows.",
            "required_evidence_before_reopen": "Naming-rule update plus non-recirculating or transition anchors showing the row is no longer a recirculation-cell diagnostic.",
            "scorecard_policy_until_resolved": "Use this lane only for diagnostic/validation-only residual context, not trainable closure data.",
            "source_artifact": rel(UPCOMER_NAMING_RULES),
        },
        {
            "dependency_id": "cfd_pp_onset_candidates",
            "owning_lane_or_agent": "cfd-pp / onset",
            "gate_reopen_requirement": "Admitted onset candidates must bracket the recirculation transition before any upcomer internal-Nu fit gate reopens.",
            "current_status": (
                f"corrected_q_rows_admitted={corrected_q_summary.get('corrected_q_rows_admitted', 0)}; "
                f"current_Re_range={upcomer_summary.get('re_min'):.3f}-{upcomer_summary.get('re_max'):.3f}; all rows recirculating"
            ),
            "why_it_blocks_internal_nu_fit": "Salt2-4 provide only recirculating points; there is no ordinary-pipe anchor or calibrated onset threshold.",
            "required_evidence_before_reopen": "Terminal/admitted cfd-pp cases near Re 150, 200, 250 plus a non-recirculating or transition anchor if physically present.",
            "scorecard_policy_until_resolved": "Do not extrapolate current monotone recirculation trend into a fitted Nu law.",
            "source_artifact": rel(UPCOMER_RECIRC_CONDITIONS),
        },
        {
            "dependency_id": "therm_reconstr_matched_plane_extraction",
            "owning_lane_or_agent": "therm-reconstr / cfd-pp",
            "gate_reopen_requirement": "Matched thermal/vector planes must exist over the same time window before fitting internal Nu.",
            "current_status": "missing direct wall-bulk/core Delta T, Gz, secondary velocity fraction, and matched plane time-window metadata",
            "why_it_blocks_internal_nu_fit": "Nu/HTC needs a defensible thermal driving temperature and flow state; otherwise it can absorb storage, branch mixing, wall, radiation, heater, or cooler residuals.",
            "required_evidence_before_reopen": "Upcomer inlet/mid/outlet planes with reverse area fraction, reverse mass fraction, secondary velocity fraction, mass-flux-weighted bulk T, area-weighted wall T, wallHeatFlux, Re, Pr, Ri, Ra/Gr, Gz, and exact time window.",
            "scorecard_policy_until_resolved": "Keep upcomer Nu section-effective and validation-only; do not fit HTC/UA/Nu.",
            "source_artifact": rel(UPCOMER_BLOCKED_METRICS),
        },
        {
            "dependency_id": "mesh_time_uncertainty_for_recirculation_metrics",
            "owning_lane_or_agent": "mesh-GCI / therm-reconstr",
            "gate_reopen_requirement": "Recirculation and thermal-driving metrics need mesh/time uncertainty before closure-fit admission.",
            "current_status": "current upcomer evidence is coarse/no-publication-GCI diagnostic evidence",
            "why_it_blocks_internal_nu_fit": "A fitted closure would otherwise learn mesh/time-window artifacts rather than a transferable heat-transfer relation.",
            "required_evidence_before_reopen": "Mesh-family or otherwise admitted uncertainty bounds for recirculation metrics, wallHeatFlux, and driving-temperature extraction.",
            "scorecard_policy_until_resolved": "Keep rows diagnostic or validation-only.",
            "source_artifact": rel(UPCOMER_BLOCKED_METRICS),
        },
        {
            "dependency_id": "thermal_residual_ownership_guardrail",
            "owning_lane_or_agent": "BC-modeling / internal-Nu",
            "gate_reopen_requirement": "Boundary, heater, cooler/HX, wall/radiation, storage, and mixing residual ownership must be separated before internal Nu fitting.",
            "current_status": "internal Nu may not absorb heater, cooler, passive loss, wall storage, junction, recirculation, or radiation residuals",
            "why_it_blocks_internal_nu_fit": "Using internal Nu as a catch-all would hide boundary/HX and recirculation physics and leak diagnostic CFD heat terms into predictive closure.",
            "required_evidence_before_reopen": "Residual attribution table showing which residuals belong to hydraulic, boundary/HX, wall/radiation, storage/mixing, and internal-Nu lanes.",
            "scorecard_policy_until_resolved": "Keep baseline/literature/default internal Nu behavior for predictive runs.",
            "source_artifact": rel(THERMAL_GATE),
        },
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                "  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/h1_hydraulic_scorecard.csv",
                "  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/summary.json",
                "  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/summary.json",
                "  - work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/blockers_to_final_forward_v1.csv",
                "tags: [forward-model, predictive-1d, scorecard, admission-gate]",
                "related:",
                "  - operational_notes/maps/forward-predictive-model.md",
                "  - operational_notes/maps/thermal-closures-and-internal-nu.md",
                "task: AGENT-321",
                "updated_by: AGENT-337",
                "date: 2026-07-14",
                "role: Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Final Forward-v1 Scorecard Gate",
                "",
                "This is the final gate decision for the current evidence set. It is not a new fitted model run.",
                "",
                "## Decision",
                "",
                f"- Final forward-v1 status: `{summary['final_forward_v1_status']}`.",
                "- Current evidence is scored-but-blocked: H1 is still proxy-only, thermal internal Nu has no fit-admissible rows, and boundary/HX/wall/radiation support is not final setup-only evidence.",
                "- No CFD mdot, realized CFD wallHeatFlux, or validation/holdout temperatures are admitted as runtime predictive inputs.",
                "- The active split remains `salt_2=train`, `salt_3=validation`, `salt_4=holdout` unless a new dated split supersedes it.",
                "",
                "## Admitted Now",
                "",
                "- Strict input hygiene and current Salt2/3/4 split discipline.",
                "- Forward-v0 solve_case confirmation as execution evidence.",
                "- H1 aggregate fixed-K rows only as diagnostic/proxy hydraulic evidence.",
                "- Thermal rows only as validation-only or blocked evidence, not fit targets.",
                "- `Nu_section_effective_upcomer_diagnostic` only as diagnostic/validation-only upcomer recirculation evidence.",
                "- Sensor labels only as post-solve validation targets with blocked labels excluded.",
                "",
                "## Math And Assumptions",
                "",
                "- The forward model must map setup inputs to predicted mdot and sensor targets; realized CFD mdot, realized CFD wallHeatFlux, and validation/holdout temperatures are target data only.",
                "- Train/validation/holdout discipline is fixed at `salt_2=train`, `salt_3=validation`, `salt_4=holdout`; fitted parameters can only use admitted training rows.",
                "- Hydraulic residuals are evaluated before thermal closure fitting because mdot bias propagates into advection, residence time, and heat-transfer residuals.",
                "- Thermal closure evidence must pass admission gates before any internal Nu/HTC/UA fit; validation-only rows can score predictions but cannot fit parameters.",
                "- Upcomer recirculation invalidates universal single-stream Nu/f_D/K labels for current Salt2-4 upcomer rows; use section-effective diagnostic names only.",
                "- Predictive runs keep baseline/literature/default internal Nu behavior unless a later dated gate admits a specific row.",
                "- Boundary/HX terms must be setup-only model outputs. Imposed cooler duty and replayed realized wall heat are diagnostic controls, not final predictive boundary evidence.",
                "- Sensor-map rows are post-solve comparisons. They cannot be used as corrections to the forward run.",
                "",
                "## Residual Attribution Plan",
                "",
                "- Hydraulic lane: compare predicted and CFD mdot plus any pressure residuals from localized H1 or successor scorecards.",
                "- Boundary/HX lane: report modeled cooler/HX duty, passive wall/radiation terms, and heat-balance residual from setup-only boundary inputs.",
                "- Thermal lane: report sensor, segment, and `Nu_section_effective_upcomer_diagnostic` residual context only after hydraulic and boundary/HX lanes declare their admissible modes.",
                "- Split lane: summarize train/validation/holdout residuals separately and reject any row whose fit sources include validation or holdout data.",
                "- Internal-Nu fit lane: remain closed until `internal_nu_dependency_blockers.csv` dependencies are resolved and a later thermal gate admits trainable rows.",
                "",
                "## Upcomer Recirculation Impact",
                "",
                "- The upcomer recirculation package reports `0` fit-admissible internal-Nu rows today.",
                "- Current Salt2-4 upcomer evidence spans only recirculating rows, so it supports an admission/naming rule rather than a fitted Nu closure.",
                "- Before reopening internal-Nu fitting, cfd-pp must provide onset candidates and therm-reconstr must provide matched vector/thermal plane extraction.",
                "- Until then, forward-v1 cannot consume fitted internal Nu rows and must keep baseline/literature/default internal Nu behavior for predictive runs.",
                "",
                "## Pending",
                "",
                "- cfd-pp admitted case inventory or corrected-Q terminal admission rows.",
                "- Hydraulics localized H1/reset/redevelopment scorecard with no validation or holdout fitting.",
                "- BC-modeling setup-only HX/external-boundary outputs with runtime-input audit.",
                "- Internal-Nu gate reopening only after cfd-pp onset candidates, therm-reconstr matched-plane extraction, mesh/time uncertainty, and residual-ownership evidence land.",
                "",
                "## Blocked",
                "",
                "- Final forward-v1 scoring remains blocked while the checklist has blocking gates.",
                "- H1 proxy, imposed cooler duty, and diagnostic thermal rows are not final predictive closure evidence.",
                "- `Nu_section_effective_upcomer_diagnostic` cannot be treated as trainable closure data.",
                "",
                "## Files",
                "",
                "- `forward_v1_gate_checklist.csv`",
                "- `scorecard_inputs_waiting_on_agents.csv`",
                "- `internal_nu_dependency_blockers.csv`",
                "- `final_forward_v1_gate_table.csv`",
                "- `forward_v1_score_rows.csv`",
                "- `source_manifest.csv`",
                "- `summary.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_package(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    thermal_summary = read_json(THERMAL_GATE)
    fluid_summary = read_json(FLUID_API_SUMMARY)
    corrected_q_summary = read_json(CORRECTED_Q_SUMMARY)
    sensor_summary = read_json(SENSOR_MAP_SUMMARY)
    upcomer_summary = read_json(UPCOMER_RECIRC_SUMMARY)
    scores = h1_score_rows(H1_SCORECARD)
    gates = gate_rows(thermal_summary, fluid_summary, corrected_q_summary, sensor_summary, upcomer_summary)
    waiting = waiting_input_rows(thermal_summary, fluid_summary, corrected_q_summary, upcomer_summary)
    internal_nu_dependencies = internal_nu_dependency_blockers_rows(thermal_summary, corrected_q_summary, upcomer_summary)
    blockers = [row for row in gates if str(row["blocks_final_forward_v1"]).startswith("yes")]
    status = "blocked_no_go_final_forward_v1_not_admitted" if blockers else "admitted_final_forward_v1"

    write_csv(output_dir / "forward_v1_gate_checklist.csv", gates, GATE_COLUMNS)
    write_csv(output_dir / "final_forward_v1_gate_table.csv", gates, GATE_COLUMNS)
    write_csv(output_dir / "scorecard_inputs_waiting_on_agents.csv", waiting, WAITING_COLUMNS)
    write_csv(output_dir / "internal_nu_dependency_blockers.csv", internal_nu_dependencies, INTERNAL_NU_DEPENDENCY_COLUMNS)
    write_csv(output_dir / "forward_v1_score_rows.csv", scores, SCORE_COLUMNS)
    write_csv(
        output_dir / "source_manifest.csv",
        [
            {"artifact": "h1_hydraulic_scorecard", "role": "source", "mutation_status": "read_only", "path": rel(H1_SCORECARD)},
            {"artifact": "thermal_admission_internal_nu_final_gate", "role": "source", "mutation_status": "read_only", "path": rel(THERMAL_GATE)},
            {"artifact": "boundary_hx_wall_radiation_decision", "role": "source", "mutation_status": "read_only", "path": rel(BOUNDARY_DECISION)},
            {"artifact": "fluid_localized_h1_and_boundary_api", "role": "source", "mutation_status": "read_only", "path": rel(FLUID_API_SUMMARY)},
            {"artifact": "corrected_q_terminal_admission_gate", "role": "source", "mutation_status": "read_only", "path": rel(CORRECTED_Q_SUMMARY)},
            {"artifact": "sensor_map_contract", "role": "source", "mutation_status": "read_only", "path": rel(SENSOR_MAP_SUMMARY)},
            {"artifact": "upcomer_recirculation_internal_nu_admissibility", "role": "source", "mutation_status": "read_only", "path": rel(UPCOMER_RECIRC_SUMMARY)},
            {"artifact": "forward_v1_gate_checklist", "role": "generated", "mutation_status": "new_artifact", "path": rel(output_dir / "forward_v1_gate_checklist.csv")},
            {"artifact": "scorecard_inputs_waiting_on_agents", "role": "generated", "mutation_status": "new_artifact", "path": rel(output_dir / "scorecard_inputs_waiting_on_agents.csv")},
            {"artifact": "internal_nu_dependency_blockers", "role": "generated", "mutation_status": "new_artifact", "path": rel(output_dir / "internal_nu_dependency_blockers.csv")},
            {"artifact": "final_forward_v1_gate_table", "role": "generated_alias", "mutation_status": "new_artifact", "path": rel(output_dir / "final_forward_v1_gate_table.csv")},
        ],
        MANIFEST_COLUMNS,
    )
    summary = {
        "task": "AGENT-321",
        "latest_update_task": "AGENT-337",
        "generated_at_utc": utc_now(),
        "final_forward_v1_status": status,
        "gate_count": len(gates),
        "blocking_gate_count": len(blockers),
        "waiting_input_count": len(waiting),
        "internal_nu_dependency_blocker_count": len(internal_nu_dependencies),
        "score_row_count": len(scores),
        "native_solver_outputs_mutated": False,
        "runtime_leakage_admitted": False,
        "thermal_internal_nu_fit_allowed": bool(thermal_summary["forward_v1_internal_nu_fit_allowed"]),
        "corrected_q_rows_admitted": int(corrected_q_summary.get("corrected_q_rows_admitted", 0)),
        "current_split": "salt_2=train;salt_3=validation;salt_4=holdout",
        "h1_proxy_final_closure_admitted": False,
        "imposed_cooler_final_predictive_evidence_admitted": False,
        "diagnostic_thermal_rows_final_closure_admitted": False,
        "fitted_internal_nu_rows_consumable": False,
        "upcomer_section_effective_nu_label": "Nu_section_effective_upcomer_diagnostic",
        "upcomer_section_effective_nu_use": "diagnostic_validation_only",
        "baseline_literature_default_internal_nu_required": True,
        "cfd_pp_onset_candidates_required_for_internal_nu_reopen": True,
        "therm_reconstr_matched_plane_extraction_required_for_internal_nu_reopen": True,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
