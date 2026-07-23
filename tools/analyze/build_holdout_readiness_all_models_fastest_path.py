#!/usr/bin/env python3
"""Build the all-model holdout-readiness and fastest-path audit package."""

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

TASK_ID = "TODO-HOLDOUT-READINESS-ALL-MODELS-FASTEST-PATH-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_holdout_readiness_all_models_fastest_path"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/holdout-readiness-all-models-fastest-path.md"
IMPORT = ROOT / "imports/2026-07-22_holdout_readiness_all_models_fastest_path.json"

SPLIT_POLICY = ROOT / "operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md"
SCORECARD = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell"
H2_SALT1 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict"
H2_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_candidate_gate_rerun_passive_role_filtered_policy"
H2_BURNDOWN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_h2_s13_modelform_blocker_burndown"
PM5_REPAIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair"
VAL_SALT2 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger"
PM5_SPLIT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing"
PM10 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission"
MASTER_SCOREBOARD = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"
MODEL_BAKEOFF = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_model_form_bakeoff"
HEATER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_heater_fluid_fraction_model"
COOLER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_cooler_removal_model"
WALL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predict_wall_thermal_circuit"
TEST_SECTION = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_test_section_heat_loss_model"
S13_DIRECT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain"
UPCOMER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_upcomer_onset"
M0_BASELINE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard"
D2_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def bool_text(value: bool) -> str:
    return "yes" if value else "no"


def summary_decision(summary: dict[str, Any], fallback: str) -> str:
    value = summary.get("decision", fallback)
    if isinstance(value, dict):
        nested = value.get("decision") or value.get("status") or value.get("why")
        return str(nested) if nested else fallback
    if value in (None, ""):
        return fallback
    return str(value)


def case_family_rows() -> list[dict[str, Any]]:
    """Classify holdout/external/future case families without scoring them."""

    source_common = f"{rel(SPLIT_POLICY)};{rel(SCORECARD / 'case_partition_contract.csv')}"
    rows: list[dict[str, Any]] = [
        {
            "case_key": "salt1_lo10q",
            "case_family": "salt1_pm10",
            "canonical_role": "training_support_excluded_support_diagnostic",
            "target_evidence_status": "support_evidence_only_not_holdout_target",
            "terminal_or_ledger_status": "available_as_support_context",
            "model_prediction_status": "not_generated_for_final_holdout",
            "score_ready_now": False,
            "fit_allowed": False,
            "model_selection_allowed": False,
            "runtime_input_allowed": False,
            "holdout_use_after_freeze": "no_without_predeclared_split_policy_change",
            "fastest_path": "Do not use as current holdout. Keep as train-support sensitivity unless a new split-freeze policy reclassifies it before any tuning.",
            "blockers": "canonical policy excludes support perturbations from final scorecard; prior exposure risk if treated as blind later",
            "source_paths": source_common,
        },
        {
            "case_key": "salt1_hi10q",
            "case_family": "salt1_pm10",
            "canonical_role": "training_support_excluded_support_diagnostic",
            "target_evidence_status": "support_evidence_only_not_holdout_target",
            "terminal_or_ledger_status": "available_as_support_context",
            "model_prediction_status": "not_generated_for_final_holdout",
            "score_ready_now": False,
            "fit_allowed": False,
            "model_selection_allowed": False,
            "runtime_input_allowed": False,
            "holdout_use_after_freeze": "no_without_predeclared_split_policy_change",
            "fastest_path": "Do not use as current holdout. If urgently needed, open a separate split-policy row before any model choice touches it.",
            "blockers": "canonical policy excludes support perturbations from final scorecard; not legally blind under current corpus",
            "source_paths": source_common,
        },
        {
            "case_key": "salt4_lo5q",
            "case_family": "salt4_pm5",
            "canonical_role": "holdout_family_sensitivity_or_support_diagnostic",
            "target_evidence_status": "terminal_harvested_heat_role_context_available",
            "terminal_or_ledger_status": "terminal_harvested",
            "model_prediction_status": "no_frozen_candidate_prediction",
            "score_ready_now": False,
            "fit_allowed": False,
            "model_selection_allowed": False,
            "runtime_input_allowed": False,
            "holdout_use_after_freeze": "conditional_after_freeze_and_holdout_family_use_policy",
            "fastest_path": "Use after Salt1-4 candidate freeze only as a separate holdout-family sensitivity score; keep out of model selection.",
            "blockers": "post-freeze use policy still needed; no frozen prediction artifact",
            "source_paths": f"{rel(PM5_SPLIT / 'corrected_q_pm5_split_admission_matrix.csv')};{source_common}",
        },
        {
            "case_key": "salt4_hi5q",
            "case_family": "salt4_pm5",
            "canonical_role": "holdout_family_sensitivity_or_support_diagnostic",
            "target_evidence_status": "terminal_harvested_heat_role_context_available",
            "terminal_or_ledger_status": "terminal_harvested",
            "model_prediction_status": "no_frozen_candidate_prediction",
            "score_ready_now": False,
            "fit_allowed": False,
            "model_selection_allowed": False,
            "runtime_input_allowed": False,
            "holdout_use_after_freeze": "conditional_after_freeze_and_holdout_family_use_policy",
            "fastest_path": "Use after Salt1-4 candidate freeze only as a separate holdout-family sensitivity score; keep out of model selection.",
            "blockers": "post-freeze use policy still needed; no frozen prediction artifact",
            "source_paths": f"{rel(PM5_SPLIT / 'corrected_q_pm5_split_admission_matrix.csv')};{source_common}",
        },
        {
            "case_key": "salt2_lo5q",
            "case_family": "salt2_pm5",
            "canonical_role": "current_blind_holdout_testing",
            "target_evidence_status": "holdout_target_repaired_and_ready",
            "terminal_or_ledger_status": "field_validation_pass_metric_complete",
            "model_prediction_status": "no_frozen_candidate_prediction",
            "score_ready_now": False,
            "fit_allowed": False,
            "model_selection_allowed": False,
            "runtime_input_allowed": False,
            "holdout_use_after_freeze": "yes_score_only_after_candidate_freeze",
            "fastest_path": "First score target once a candidate is frozen. Generate frozen predictions, then score once with fit/model-selection locked.",
            "blockers": "corrected split freeze missing; candidate not admitted/frozen; no prediction artifact",
            "source_paths": f"{rel(PM5_REPAIR / 'salt2_pm5_admission_table.csv')};{rel(PM5_REPAIR / 'salt2_pm5_runtime_leakage_audit.csv')};{source_common}",
        },
        {
            "case_key": "salt2_hi5q",
            "case_family": "salt2_pm5",
            "canonical_role": "current_blind_holdout_testing",
            "target_evidence_status": "holdout_target_repaired_and_ready",
            "terminal_or_ledger_status": "field_validation_pass_metric_complete",
            "model_prediction_status": "no_frozen_candidate_prediction",
            "score_ready_now": False,
            "fit_allowed": False,
            "model_selection_allowed": False,
            "runtime_input_allowed": False,
            "holdout_use_after_freeze": "yes_score_only_after_candidate_freeze",
            "fastest_path": "First score target once a candidate is frozen. Generate frozen predictions, then score once with fit/model-selection locked.",
            "blockers": "corrected split freeze missing; candidate not admitted/frozen; no prediction artifact",
            "source_paths": f"{rel(PM5_REPAIR / 'salt2_pm5_admission_table.csv')};{rel(PM5_REPAIR / 'salt2_pm5_runtime_leakage_audit.csv')};{source_common}",
        },
        {
            "case_key": "val_salt2",
            "case_family": "external_val_salt2",
            "canonical_role": "external_test",
            "target_evidence_status": "external_test_ledger_ready_training_forbidden",
            "terminal_or_ledger_status": "target_ledger_ready",
            "model_prediction_status": "no_frozen_candidate_prediction",
            "score_ready_now": False,
            "fit_allowed": False,
            "model_selection_allowed": False,
            "runtime_input_allowed": False,
            "holdout_use_after_freeze": "yes_external_scorecard_after_candidate_freeze",
            "fastest_path": "Score after Salt2 +/-5Q or alongside it as an external-test ledger, never as fit/model-selection input.",
            "blockers": "matching heat-loss/admission package and frozen prediction artifact still required",
            "source_paths": f"{rel(VAL_SALT2 / 'val_salt2_external_admission_decision.csv')};{rel(VAL_SALT2 / 'val_salt2_external_runtime_input_audit.csv')};{source_common}",
        },
    ]

    for case_key in ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"):
        rows.append(
            {
                "case_key": case_key,
                "case_family": case_key.rsplit("_", 1)[0] + "_pm10",
                "canonical_role": "future_holdout_candidate",
                "target_evidence_status": "terminal_evidence_admitted_future_holdout_only",
                "terminal_or_ledger_status": "terminal_available_mdot_steady_total_Q_drifting",
                "model_prediction_status": "no_frozen_candidate_prediction",
                "score_ready_now": False,
                "fit_allowed": False,
                "model_selection_allowed": False,
                "runtime_input_allowed": False,
                "holdout_use_after_freeze": "yes_future_score_only_after_terminal_admission_and_candidate_freeze",
                "fastest_path": "Use after current Salt2 +/-5Q/val_salt2 sequence and only with total-Q drift caveat carried in the scorecard.",
                "blockers": "candidate freeze missing; prediction artifact missing; total_Q drift caveat for thermal heat-ledger interpretation",
                "source_paths": f"{rel(PM10 / 'pm10_split_use_decision.csv')};{rel(PM10 / 'pm10_steadiness_metric_context.csv')};{source_common}",
            }
        )
    return rows


def all_model_gate_rows() -> list[dict[str, Any]]:
    """Summarize every current model lane against holdout admission gates."""

    h2_summary = read_json(H2_SALT1 / "summary.json")
    h2_gate = read_json(H2_GATE / "summary.json")
    burndown = read_json(H2_BURNDOWN / "summary.json")
    heater = read_json(HEATER / "summary.json")
    cooler = read_json(COOLER / "summary.json")
    wall = read_json(WALL / "summary.json")
    test_section = read_json(TEST_SECTION / "summary.json")
    s13 = read_json(S13_DIRECT / "summary.json")
    upcomer = read_json(UPCOMER / "summary.json")
    m0 = read_json(M0_BASELINE / "summary.json")
    d2 = read_json(D2_GATE / "summary.json")

    rows = [
        {
            "model_lane": "PASSIVE-H2-CAND001",
            "evidence_class": "setup-only passive heat operator candidate",
            "current_best_evidence": (
                f"Salt1-4 runtime diagnostic gate={h2_summary.get('salt1_4_runtime_gate_status', 'pass_diagnostic')}; "
                f"Salt1 radiation delta={h2_summary.get('salt1_radiation_on_heat_ledger_delta_W', '14.54824255615921')} W; "
                f"strict source-envelope pass rows={h2_summary.get('strict_source_envelope_pass_rows', 0)}"
            ),
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "source/property admission release rows 0; strict source envelope 0/15; Salt1 source-family coverage 4/5; no admitted coefficient lock",
            "fastest_unblock": "Finish H2 release-or-permanent-fail-close row, then same-QOI train-only UQ, then immutable Salt1-4 freeze and prediction generation.",
            "source_paths": f"{rel(H2_SALT1 / 'summary.json')};{rel(H2_GATE / 'candidate_gate_rerun_matrix.csv')};{rel(H2_BURNDOWN / 'blocker_decision_matrix.csv')}",
        },
        {
            "model_lane": "D4 physical successor",
            "evidence_class": "best diagnostic thermal residual successor",
            "current_best_evidence": "diagnostic transfer RMSE 7.94040349151 K; strongest residual-shape signal, but empirical offsets are not admitted physics",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "must replace segment offsets with source-bounded heat placement/passive terms; source/property release and same-QOI UQ missing",
            "fastest_unblock": "Parallel preflight: convert D4 into a source-bounded physical candidate without touching blind rows.",
            "source_paths": f"{rel(MASTER_SCOREBOARD / 'diagnostic_tested_model_form_scoreboard.csv')};{rel(H2_BURNDOWN / 'd4_d3_d2_physical_successor_preflight.csv')}",
        },
        {
            "model_lane": "D3 physical successor",
            "evidence_class": "wall-shape or axial-mixing diagnostic successor",
            "current_best_evidence": "diagnostic transfer RMSE 8.38846755024 K; local shape evidence persists after bias",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "physical wall/core exchange or axial-mixing source basis missing; same-QOI UQ missing",
            "fastest_unblock": "Keep behind D4/H2 unless D4 cannot be made physical; then claim a D3 wall/core source-basis row.",
            "source_paths": f"{rel(MASTER_SCOREBOARD / 'recommended_model_forms_to_try.csv')};{rel(H2_BURNDOWN / 'd4_d3_d2_physical_successor_preflight.csv')}",
        },
        {
            "model_lane": "D2 source-bounded projection",
            "evidence_class": "sensor/QOI projection diagnostic successor",
            "current_best_evidence": "diagnostic transfer RMSE 10.5253939442 K; projection uncertainty work exists, admission remains closed",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "source-bounded projection admission and holdout/external score gate not released",
            "fastest_unblock": "Use only if H2/D4 fail; preserve as physical projection fallback.",
            "source_paths": f"{rel(D2_GATE / 'summary.json')};{rel(H2_BURNDOWN / 'd4_d3_d2_physical_successor_preflight.csv')}",
        },
        {
            "model_lane": "M0 setup-only baseline",
            "evidence_class": "lower-bound predictive baseline",
            "current_best_evidence": f"summary decision={summary_decision(m0, 'shell_or_diagnostic_baseline_only')}",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "baseline predictions are useful as a reference but do not constitute a final admitted model form",
            "fastest_unblock": "Keep as scorecard comparator once final freeze machinery exists; do not let it select/tune the candidate.",
            "source_paths": f"{rel(M0_BASELINE / 'summary.json')};{rel(MASTER_SCOREBOARD / 'master_model_form_scoreboard.csv')}",
        },
        {
            "model_lane": "M1/M2/M3 legacy numeric comparators",
            "evidence_class": "historical and diagnostic comparators",
            "current_best_evidence": "M3 is best legacy thermal comparator but all legacy scoreboard rows remain diagnostic_not_admitted",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "uses replay/legacy assumptions or lacks final locked split; no admitted freeze",
            "fastest_unblock": "Use for publication context and residual-shape motivation, not as holdout candidate.",
            "source_paths": f"{rel(MASTER_SCOREBOARD / 'master_model_form_scoreboard.csv')};{rel(MASTER_SCOREBOARD / 'diagnostic_tested_model_form_scoreboard.csv')}",
        },
        {
            "model_lane": "F3/F4 hydraulic model-form bakeoff",
            "evidence_class": "pressure/mdot diagnostic closure lane",
            "current_best_evidence": "F3_shah_apparent mean absolute mdot error 2.6685710918497882% in current bakeoff; thermal mismatch is separate",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "not a complete thermal predictive model; ordinary-flow/upcomer admission still constrained",
            "fastest_unblock": "Carry as pressure-root component inside a later frozen full model, not as standalone holdout score.",
            "source_paths": f"{rel(MODEL_BAKEOFF / 'summary.json')};{rel(UPCOMER / 'summary.json')}",
        },
        {
            "model_lane": "HF2 heater source fraction",
            "evidence_class": "heater boundary/source lane",
            "current_best_evidence": f"decision={summary_decision(heater, 'heater candidate diagnostic only')}",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "boundary-lane evidence only; wallflux score not a full-model legal runtime/freeze",
            "fastest_unblock": "Use as internal component only after full-model freeze policy admits the source term.",
            "source_paths": rel(HEATER / "summary.json"),
        },
        {
            "model_lane": "HX_LUMPED_UA_NTU cooler",
            "evidence_class": "cooler/removal submodel lane",
            "current_best_evidence": f"decision={summary_decision(cooler, 'cooler candidate diagnostic/pending')}",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "coupled Fluid/full-model rerun not admitted; fixed-mdot duty screen is component evidence",
            "fastest_unblock": "Fold into H2/D4 full-model candidate only after component runtime contract is legal.",
            "source_paths": rel(COOLER / "summary.json"),
        },
        {
            "model_lane": "wall/test-section thermal circuit",
            "evidence_class": "passive wall and test-section heat-loss lanes",
            "current_best_evidence": f"wall={summary_decision(wall, 'contract ready no numeric release')}; test_section={summary_decision(test_section, 'diagnostic or contract only')}",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "numeric q-loss/source-property release not open; residual cannot be hidden in internal Nu",
            "fastest_unblock": "Use as source-bounded implementation basis for H2/D4, not as standalone scored model.",
            "source_paths": f"{rel(WALL / 'summary.json')};{rel(TEST_SECTION / 'summary.json')}",
        },
        {
            "model_lane": "S13/upcomer exchange",
            "evidence_class": "exchange-cell and recirculation diagnostic lane",
            "current_best_evidence": f"direct_coarse={summary_decision(s13, 'fail_closed_no_admission')}; upcomer={summary_decision(upcomer, 'no coefficient admission')}",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "same-window endpoint/GCI/UQ admission not released; ordinary upcomer coefficient rows 0",
            "fastest_unblock": "Keep as a parallel source-recovery lane; do not block Salt2 +/-5Q holdout readiness on S13 unless candidate explicitly needs it.",
            "source_paths": f"{rel(S13_DIRECT / 'summary.json')};{rel(UPCOMER / 'summary.json')}",
        },
        {
            "model_lane": "Model-form family aggregate",
            "evidence_class": "all current lanes",
            "current_best_evidence": f"best diagnostic form={burndown.get('best_temperature_diagnostic', 'D4_M3_segment_offsets_min2_train')}; final admitted score rows={burndown.get('final_admitted_score_rows', 0)}",
            "can_generate_holdout_predictions_now": False,
            "can_score_holdout_now": False,
            "candidate_admitted_or_frozen": False,
            "fit_allowed": False,
            "source_property_release_ready": False,
            "blocks": "no current model lane has admitted/frozen predictions for holdout rows",
            "fastest_unblock": "Pick one candidate lane for legal admission; fastest current candidate is H2 if source-envelope release can be resolved, otherwise D4 physical successor.",
            "source_paths": f"{rel(H2_BURNDOWN / 'summary.json')};{rel(MASTER_SCOREBOARD / 'summary.json')}",
        },
    ]
    if h2_gate:
        rows[0]["current_best_evidence"] += f"; passive-role-filtered rows={h2_gate.get('case_family_rows', 15)}"
    return rows


def fastest_sequence_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "phase": "Freeze split and scoring law",
            "objective": "Declare the legal order: Salt1-4 nominal train only; Salt2 +/-5Q first blind holdout; val_salt2 external; Salt4 +/-5Q conditional sensitivity; Salt2/Salt4 +/-10Q future.",
            "ready_now": True,
            "outputs_needed": "split-freeze decision table; no-fit/no-model-selection assertion; scorecard partitions",
            "forbidden_actions": "do not add support rows to training; do not peek-score before candidate freeze",
            "candidate_task_id": "TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22",
        },
        {
            "rank": 2,
            "phase": "Candidate admission gate",
            "objective": "Resolve whether PASSIVE-H2 can be admitted or must fail closed; preserve D4 physical successor as parallel fallback.",
            "ready_now": True,
            "outputs_needed": "source-envelope release-or-fail-close table; same-QOI train-only UQ preflight; coefficient-lock eligibility",
            "forbidden_actions": "do not use Salt2 +/-5Q, val_salt2, Salt4 +/-5Q, or PM10 rows for tuning",
            "candidate_task_id": "TODO-PASSIVE-H2-SOURCE-ENVELOPE-RELEASE-OR-PERMANENT-FAILCLOSE-2026-07-22",
        },
        {
            "rank": 3,
            "phase": "Train-only UQ and immutable freeze",
            "objective": "For the chosen candidate, run Salt1-4 same-QOI train-only UQ using legal runtime inputs, then freeze exact code/data/coefficient manifest.",
            "ready_now": False,
            "outputs_needed": "train mdot/TP/TW/heat-ledger UQ; runtime-input audit; freeze manifest",
            "forbidden_actions": "no protected-row fitting, no source/property release shortcut, no hidden multiplier",
            "candidate_task_id": "TODO-CANDIDATE-SAME-QOI-TRAIN-UQ-IMMUTABLE-FREEZE-2026-07-22",
        },
        {
            "rank": 4,
            "phase": "Blind prediction generation",
            "objective": "Generate frozen predictions for Salt2 +/-5Q and val_salt2 first; do not score during generation.",
            "ready_now": False,
            "outputs_needed": "prediction artifact with mdot, TP, TW, heat-ledger QOIs and runtime-input audit",
            "forbidden_actions": "no target reads during prediction generation except immutable target ledger metadata",
            "candidate_task_id": "TODO-FROZEN-PREDICTION-GENERATOR-SALT2PM5-VALSALT2-2026-07-22",
        },
        {
            "rank": 5,
            "phase": "Score once",
            "objective": "Score Salt2 +/-5Q and val_salt2 after frozen predictions exist; keep external score separate.",
            "ready_now": False,
            "outputs_needed": "blind scorecard; external scorecard; no-refit proof; publication-ready uncertainty table",
            "forbidden_actions": "no model selection based on holdout outcome; no re-freeze after seeing scores",
            "candidate_task_id": "TODO-HOLDOUT-SCORE-ONCE-SALT2PM5-VALSALT2-2026-07-22",
        },
        {
            "rank": 6,
            "phase": "Future/sensitivity holdouts",
            "objective": "After the primary score, decide Salt4 +/-5Q and Salt2/Salt4 +/-10Q score use under predeclared policies.",
            "ready_now": False,
            "outputs_needed": "Salt4 PM5 sensitivity policy; PM10 total-Q caveat; secondary scorecard",
            "forbidden_actions": "no retrospective reclassification to improve the paper narrative",
            "candidate_task_id": "TODO-SALT4-PM5-PM10-POSTFREEZE-HOLDOUT-SENSITIVITY-SCORE-2026-07-22",
        },
    ]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {"claim": "Salt2 +/-5Q is the first current holdout target family", "status": "allowed", "basis": "canonical split policy plus repaired extraction package", "guardrail": "score-only after freeze; no fit/model selection"},
        {"claim": "val_salt2 is external-test ready", "status": "allowed_with_gate", "basis": "external ledger ready and training forbidden", "guardrail": "requires matching frozen predictions and separate external scorecard"},
        {"claim": "Salt1 +/-10Q is current holdout", "status": "forbidden_now", "basis": "canonical policy classifies as training_support/excluded_support_diagnostic", "guardrail": "needs predeclared split-policy change before use"},
        {"claim": "Salt4 +/-5Q is immediately scoreable", "status": "forbidden_now", "basis": "terminal harvested support/sensitivity evidence but no freeze/use policy", "guardrail": "conditional post-freeze sensitivity only"},
        {"claim": "Salt2/Salt4 +/-10Q is future holdout evidence", "status": "allowed_after_freeze", "basis": "PM10 terminal admission package", "guardrail": "total-Q drift caveat and no fit/model selection"},
        {"claim": "Any current model can be holdout-scored today", "status": "forbidden_now", "basis": "all-model gate matrix shows no admitted/frozen candidate predictions", "guardrail": "must admit and freeze before prediction/scoring"},
        {"claim": "PASSIVE-H2 is thesis-useful now", "status": "allowed_as_diagnostic_only", "basis": "runtime and radiation implementation are documented, release gates fail closed", "guardrail": "no coefficient admission or final score"},
        {"claim": "D4 is the best current predictive direction", "status": "allowed_as_design_priority", "basis": "best diagnostic transfer RMSE among tried forms", "guardrail": "must become source-bounded before admission"},
    ]


def next_task_queue_rows() -> list[dict[str, Any]]:
    return [
        {"priority": 1, "task_id": "TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22", "purpose": "Lock the holdout/external/future sequence before any scoring.", "ready_to_claim": True, "depends_on": "this audit package", "allowed_scope_hint": "policy table/docs only; no score"},
        {"priority": 2, "task_id": "TODO-PASSIVE-H2-SOURCE-ENVELOPE-RELEASE-OR-PERMANENT-FAILCLOSE-2026-07-22", "purpose": "Decide whether H2 can proceed to admitted freeze or must remain diagnostic.", "ready_to_claim": False, "depends_on": "active H2 thesis diagnostic bundle must clear or hand off", "allowed_scope_hint": "H2 source/property evidence; no blind rows"},
        {"priority": 3, "task_id": "TODO-D4-PHYSICAL-SUCCESSOR-HOLDOUT-PREFLIGHT-2026-07-22", "purpose": "Prepare fallback/source-bounded successor if H2 fails closed.", "ready_to_claim": True, "depends_on": "master model-form scoreboard and D4/D3/D2 preflight", "allowed_scope_hint": "design/preflight only; no fitting on holdout"},
        {"priority": 4, "task_id": "TODO-CANDIDATE-SAME-QOI-TRAIN-UQ-IMMUTABLE-FREEZE-2026-07-22", "purpose": "Run same-QOI Salt1-4 train-only UQ and freeze one admitted candidate.", "ready_to_claim": False, "depends_on": "candidate source/property admission", "allowed_scope_hint": "train-only runtime/UQ/freeze"},
        {"priority": 5, "task_id": "TODO-FROZEN-PREDICTION-GENERATOR-SALT2PM5-VALSALT2-2026-07-22", "purpose": "Generate protected predictions without target scoring.", "ready_to_claim": False, "depends_on": "immutable candidate freeze", "allowed_scope_hint": "prediction artifact only; no score"},
        {"priority": 6, "task_id": "TODO-HOLDOUT-SCORE-ONCE-SALT2PM5-VALSALT2-2026-07-22", "purpose": "Produce the first publication-safe holdout/external scorecards.", "ready_to_claim": False, "depends_on": "frozen predictions and score law", "allowed_scope_hint": "score once; no tuning"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (SPLIT_POLICY, "canonical split and guardrail policy"),
        (SCORECARD / "summary.json", "final scorecard shell state"),
        (SCORECARD / "case_partition_contract.csv", "case partition contract"),
        (H2_SALT1 / "summary.json", "latest H2 runtime/freeze/blind status"),
        (H2_GATE / "candidate_gate_rerun_matrix.csv", "H2 release/fail-closed gates"),
        (H2_BURNDOWN / "blocker_decision_matrix.csv", "H2/S13/model-form blocker synthesis"),
        (PM5_REPAIR / "salt2_pm5_admission_table.csv", "Salt2 +/-5Q repaired holdout targets"),
        (VAL_SALT2 / "val_salt2_external_admission_decision.csv", "external val_salt2 ledger"),
        (PM5_SPLIT / "corrected_q_pm5_split_admission_matrix.csv", "Salt4 +/-5Q and perturbation split context"),
        (PM10 / "pm10_split_use_decision.csv", "Salt2/Salt4 +/-10Q future holdout status"),
        (MASTER_SCOREBOARD / "master_model_form_scoreboard.csv", "all current model-form lanes"),
        (MODEL_BAKEOFF / "summary.json", "F3/F4 model-form bakeoff context"),
        (HEATER / "summary.json", "heater component lane"),
        (COOLER / "summary.json", "cooler component lane"),
        (WALL / "summary.json", "wall circuit lane"),
        (TEST_SECTION / "summary.json", "test-section heat-loss lane"),
        (S13_DIRECT / "summary.json", "S13 endpoint/GCI/UQ direct coarse status"),
        (UPCOMER / "summary.json", "upcomer/recirculation lane"),
        (M0_BASELINE / "summary.json", "setup-only baseline lane"),
        (D2_GATE / "summary.json", "D2 projection gate lane"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": bool_text(path.exists()),
            "read_only": "yes",
        }
        for path, role in paths
    ]


def no_mutation_guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "status": "false", "reason": "read-only package synthesis"},
        {"guardrail": "registry_or_admission_mutated", "status": "false", "reason": "no global admission or registry writes"},
        {"guardrail": "scheduler_action", "status": "false", "reason": "no sbatch/srun/sacct/squeue action required"},
        {"guardrail": "protected_or_final_scoring", "status": "false", "reason": "readiness and gating only"},
        {"guardrail": "fitting_tuning_or_model_selection", "status": "false", "reason": "holdout rows remain fit-forbidden"},
        {"guardrail": "source_property_or_qwall_release", "status": "false", "reason": "release readiness audited but not changed"},
        {"guardrail": "candidate_freeze", "status": "false", "reason": "no candidate currently admitted/frozen here"},
        {"guardrail": "runtime_leakage_relaxation", "status": "false", "reason": "forbidden runtime fields remain forbidden"},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""# Holdout Readiness / All Models / Fastest Path

Generated: `{summary['generated_at']}`

## Decision

No current model lane is ready for legal holdout scoring today. The holdout
targets closest to use are `salt2_lo5q`, `salt2_hi5q`, and `val_salt2`, because
their target/ledger packages are ready and fit-forbidden. They still cannot be
scored until one model candidate is admitted, frozen from legal train-only
evidence, and used to emit frozen predictions.

The fastest safe path is:

1. Freeze the split/use law.
2. Resolve PASSIVE-H2 source-envelope release or fail it closed.
3. If H2 fails, move D4 into a source-bounded physical successor preflight.
4. Run same-QOI Salt1-4 train-only UQ for the chosen admitted candidate.
5. Freeze exactly once, generate Salt2 +/-5Q and val_salt2 predictions, then
   score once without tuning.

## Outputs

- `case_family_holdout_readiness.csv`: every relevant holdout/external/future
  case family and the fastest legal use path.
- `all_model_holdout_gate_matrix.csv`: all current model lanes and why each is
  or is not ready for holdout use.
- `fastest_safe_holdout_sequence.csv`: executable phase order.
- `claim_boundaries.csv`: what can and cannot be said now.
- `next_task_queue.csv`: next board rows to claim.
- `source_manifest.csv`: read-only evidence used.

## Publication Boundary

This package is publication-safe as a readiness and governance result. It is
not a model-performance scorecard, not a candidate freeze, not a source/property
release, and not an admission decision.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_closeout_docs(summary: dict[str, Any], changed_files: list[str]) -> None:
    status = f"""---
provenance:
  generated_by: codex
  task_id: {TASK_ID}
  date: 2026-07-22
tags:
  - holdout
  - predictive-model
  - split-policy
  - readiness
related:
  - {rel(OUT)}
---

# {TASK_ID}

## Objective

Audit all available holdout/external/future-test case families and all current
model lanes to determine the fastest legally safe route to holdout scoring.

## Outcome

No model lane can be scored on holdout today. Salt2 +/-5Q and val_salt2 are the
closest usable test targets, but only after an independently admitted/frozen
candidate emits predictions. PASSIVE-H2 is the fastest candidate if its source
envelope can be released; otherwise D4 physical successor is the best fallback
direction.

## Changes Made

{chr(10).join(f'- `{path}`' for path in changed_files)}

## Validation

- `python3.11 -m unittest tools.analyze.test_holdout_readiness_all_models_fastest_path`
- `python3.11 tools/analyze/build_holdout_readiness_all_models_fastest_path.py`

## Guardrails

No native solver output mutation, registry/admission mutation, scheduler action,
Fluid/external edit, thesis current/LaTeX edit, protected/final scoring,
fitting/tuning/model selection, source/property/Qwall release, candidate freeze,
or runtime-leakage relaxation occurred.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(status, encoding="utf-8")

    journal = f"""---
provenance:
  generated_by: codex
  task_id: {TASK_ID}
  date: 2026-07-22
tags:
  - holdout
  - model-form
  - readiness
related:
  - {rel(OUT / 'case_family_holdout_readiness.csv')}
  - {rel(OUT / 'all_model_holdout_gate_matrix.csv')}
---

# Holdout Readiness All Models Fastest Path

Task: `{TASK_ID}`

## Attempted

I consolidated the canonical split policy, final scorecard shell, PASSIVE-H2
runtime/release packages, Salt2 +/-5Q repair, val_salt2 external ledger, PM5
and PM10 perturbation disposition packages, and the current model-form
scoreboards into one readiness audit.

## Observed

Salt2 +/-5Q has repaired holdout target evidence and val_salt2 has an external
test ledger. Salt2/Salt4 +/-10Q now has terminal future-holdout evidence, with
thermal total-Q drift caveats. Salt1 +/-10Q remains support/excluded diagnostic
under the canonical policy. Every current model lane lacks an admitted/frozen
prediction artifact for these rows.

## Inferred

The blocker is not primarily missing holdout target data. The blocker is model
admission/freeze: PASSIVE-H2 has the most direct runtime path but remains
source-envelope fail-closed; D4 is the strongest diagnostic residual successor
but needs source-bounded physics before admission.

## Caveats

This task did not score, fit, launch jobs, mutate native outputs, or change the
global admission registry. The active H2 thesis bundle remains the owner of its
own release/disposition files.

## Next Useful Actions

1. Claim a split-freeze policy row.
2. Resolve PASSIVE-H2 source-envelope release or permanent fail-close after the
   active H2 row clears.
3. Prepare D4 physical successor as the parallel fallback.
4. Freeze one admitted candidate before any Salt2 +/-5Q or val_salt2 score.
"""
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(journal, encoding="utf-8")

    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "changed_files": changed_files,
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "thesis_current_edit": False,
        "protected_or_final_scoring": False,
        "fitting_tuning_or_model_selection": False,
        "source_property_or_qwall_release": False,
        "candidate_freeze": False,
        "runtime_leakage_relaxation": False,
        "provenance_flags": {
            "linked_cases_used_as_provenance": False,
            "native_output_mutation": False,
            "generated_from_script": rel(Path(__file__)),
        },
    }
    json_dump(IMPORT, manifest)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    case_rows = case_family_rows()
    model_rows = all_model_gate_rows()
    sequence_rows = fastest_sequence_rows()
    boundary_rows = claim_boundary_rows()
    queue_rows = next_task_queue_rows()
    manifest_rows = source_manifest_rows()
    guard_rows = no_mutation_guardrail_rows()

    csv_dump(
        out / "case_family_holdout_readiness.csv",
        [
            "case_key",
            "case_family",
            "canonical_role",
            "target_evidence_status",
            "terminal_or_ledger_status",
            "model_prediction_status",
            "score_ready_now",
            "fit_allowed",
            "model_selection_allowed",
            "runtime_input_allowed",
            "holdout_use_after_freeze",
            "fastest_path",
            "blockers",
            "source_paths",
        ],
        case_rows,
    )
    csv_dump(
        out / "all_model_holdout_gate_matrix.csv",
        [
            "model_lane",
            "evidence_class",
            "current_best_evidence",
            "can_generate_holdout_predictions_now",
            "can_score_holdout_now",
            "candidate_admitted_or_frozen",
            "fit_allowed",
            "source_property_release_ready",
            "blocks",
            "fastest_unblock",
            "source_paths",
        ],
        model_rows,
    )
    csv_dump(
        out / "fastest_safe_holdout_sequence.csv",
        ["rank", "phase", "objective", "ready_now", "outputs_needed", "forbidden_actions", "candidate_task_id"],
        sequence_rows,
    )
    csv_dump(out / "claim_boundaries.csv", ["claim", "status", "basis", "guardrail"], boundary_rows)
    csv_dump(
        out / "next_task_queue.csv",
        ["priority", "task_id", "purpose", "ready_to_claim", "depends_on", "allowed_scope_hint"],
        queue_rows,
    )
    csv_dump(out / "source_manifest.csv", ["path", "role", "exists", "read_only"], manifest_rows)
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "status", "reason"], guard_rows)

    score_ready_now = sum(1 for row in case_rows if row["score_ready_now"])
    current_first_targets_after_freeze = [
        row["case_key"]
        for row in case_rows
        if row["holdout_use_after_freeze"] in {"yes_score_only_after_candidate_freeze", "yes_external_scorecard_after_candidate_freeze"}
    ]
    model_score_ready_now = sum(1 for row in model_rows if row["can_score_holdout_now"])
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "holdout_targets_ready_but_no_model_lane_admitted_or_frozen",
        "case_family_rows": len(case_rows),
        "current_score_ready_case_rows": score_ready_now,
        "current_first_targets_after_freeze": current_first_targets_after_freeze,
        "current_first_targets_after_freeze_count": len(current_first_targets_after_freeze),
        "model_lane_rows": len(model_rows),
        "model_lanes_score_ready_now": model_score_ready_now,
        "fastest_candidate_lane": "PASSIVE-H2-CAND001_if_source_envelope_released_else_D4_physical_successor",
        "salt2_pm5_target_ready": True,
        "val_salt2_external_ledger_ready": True,
        "salt1_pm10_current_holdout_allowed": False,
        "protected_or_final_scoring": False,
        "fitting_tuning_or_model_selection": False,
        "candidate_freeze": False,
        "source_property_or_qwall_release": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "runtime_leakage_relaxation": False,
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)

    changed_files = [
        rel(Path(__file__)),
        rel(ROOT / "tools/analyze/test_holdout_readiness_all_models_fastest_path.py"),
        rel(out / "README.md"),
        rel(out / "summary.json"),
        rel(out / "case_family_holdout_readiness.csv"),
        rel(out / "all_model_holdout_gate_matrix.csv"),
        rel(out / "fastest_safe_holdout_sequence.csv"),
        rel(out / "claim_boundaries.csv"),
        rel(out / "next_task_queue.csv"),
        rel(out / "source_manifest.csv"),
        rel(out / "no_mutation_guardrails.csv"),
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
    ]
    write_closeout_docs(summary, changed_files)
    return summary


def main() -> None:
    summary = build(OUT)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
