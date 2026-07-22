#!/usr/bin/env python3
"""Build an additive scoreboard supplement and training roster for thesis model forms."""

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

TASK_ID = "TODO-THESIS-MODEL-FORM-SCOREBOARD-TRAINING-ROSTER-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_model_form_scoreboard_training_roster"

MASTER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"
MF12 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate"
MF15 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf15_runtime_wall_profile_basis_gate"
MF16 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate"
MF17 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf17_same_qoi_wall_core_exchange_uq_execution"
MF07 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis"
MF08 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches"
MF10 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf10_entrance_wallflux_train_only_variant_bakeoff"
RECIRC = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract"
SETUP_UQ_RUNBOOK = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_runbook"
SETUP_UQ_EXEC = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution"
SUGGESTED = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests"
PASSIVE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate"
PRESSURE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf02_pressure_mdot_coupling_diagnostic"
S14 = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence"


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


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def master_scoreboard_ids() -> set[str]:
    return {row.get("scoreboard_id", "") for row in read_csv(MASTER / "master_model_form_scoreboard.csv")}


def recommended_names() -> set[str]:
    return {row.get("model_form_to_try", "") for row in read_csv(MASTER / "recommended_model_forms_to_try.csv")}


def training_roster_rows() -> list[dict[str, Any]]:
    mf16_summary = read_json(MF16 / "summary.json")
    mf17_summary = read_json(MF17 / "summary.json")
    setup_exec_summary = read_json(SETUP_UQ_EXEC / "summary.json")

    common_forbidden = (
        "CFD mdot; realized wallHeatFlux; validation/holdout/external-test TP/TW; "
        "post-solve pressure losses; hidden global multipliers; residual fills"
    )
    rows: list[dict[str, Any]] = [
        {
            "rank": 1,
            "model_form_id": "M0_setup_only_baseline",
            "family": "endpoint_baseline",
            "model_form_name": "setup-only pressure and thermal baseline",
            "mdot_path": "pressure root from geometry/property/setup BCs",
            "temperature_path": "segment energy balances with setup-known heater/cooler/passive inputs only",
            "pressure_path": "current Fluid pressure envelope, no fitted section correction",
            "train_status": "next_train_only_lower_bound_once active setup-UQ execution closes",
            "validation_holdout_status": "not_scored",
            "runtime_legality_status": "legal_contract_exists_but execution still closing",
            "source_property_status": "blocked_by_MF16_no_release",
            "uq_status": "setup_UQ_smoke_running_or_pending_closeout",
            "admission_status": "not_admitted",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "active setup-UQ execution and source/property exact-field release are not closed",
            "next_action": "monitor/close active train-only setup-UQ smoke, then emit M0 train-only diagnostic scores only",
            "scoreboard_presence": "present_in_master_scoreboard",
            "source_paths": ";".join([rel(MASTER / "master_model_form_scoreboard.csv"), rel(SETUP_UQ_EXEC / "summary.json")]),
        },
        {
            "rank": 2,
            "model_form_id": "M3_segment_only_fluid_walls",
            "family": "endpoint_comparator",
            "model_form_name": "segment-only fluid+walls comparator",
            "mdot_path": "segment pressure root with current admitted terms",
            "temperature_path": "finite segment energy balances and wall/material stacks",
            "pressure_path": "segment pressure residual attribution",
            "train_status": "diagnostic train-only comparator after M0 lower bound",
            "validation_holdout_status": "legacy Salt3/Salt4 diagnostic transfer only; not compatible with Salt1-4 training claim",
            "runtime_legality_status": "partially legal; completed packages include diagnostic numeric context",
            "source_property_status": "blocked_by_MF16_no_release",
            "uq_status": "needs source/property and same-QOI UQ for admissible freeze",
            "admission_status": "diagnostic_not_admitted",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "full predictive candidate freeze missing",
            "next_action": "use as comparator in Salt1-4 nominal train-only diagnostics; do not freeze before source/property release",
            "scoreboard_presence": "present_in_master_scoreboard",
            "source_paths": rel(MASTER / "master_model_form_scoreboard.csv"),
        },
        {
            "rank": 3,
            "model_form_id": "MF12_signed_source_memory_bulk_to_TP",
            "family": "thermal_projection",
            "model_form_name": "signed source-memory bulk-to-TP projection",
            "mdot_path": "inherits predicted mdot from chosen hydraulic base",
            "temperature_path": "TP = bulk plus signed upstream source/reset/Graetz projection",
            "pressure_path": "none added; pair with M0/M3/MF02/M5 pressure lane",
            "train_status": "predeclare formula family; no coefficient fit until source basis is released",
            "validation_holdout_status": "locked",
            "runtime_legality_status": "conceptually setup-only but missing released source/property fields",
            "source_property_status": "fail_closed_no_release",
            "uq_status": "needs TP projection UQ and source/property conservation",
            "admission_status": "diagnostic_only_needs_source_basis",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "runtime legal q_setup/cp/source envelope not released",
            "next_action": "repair source-property exact-field gate, then run train-only formula ablation on Salt1-4 nominal",
            "scoreboard_presence": "scoreboard_supplement_required",
            "source_paths": rel(MF12 / "candidate_bulk_to_tp_formulas.csv"),
        },
        {
            "rank": 4,
            "model_form_id": "MF15_wall_core_exchange_operator",
            "family": "thermal_wall_core_exchange",
            "model_form_name": "source-bounded wall/core exchange operator",
            "mdot_path": "inherits predicted throughflow plus optional exchange proxy after release",
            "temperature_path": "wall/core contrast and Qwall-supported exchange shape",
            "pressure_path": "none added directly",
            "train_status": "diagnostic only; no coefficient basis released",
            "validation_holdout_status": "locked",
            "runtime_legality_status": "blocked by runtime wall/profile and Qwall production release",
            "source_property_status": "fail_closed",
            "uq_status": "MF17 temporal UQ executed; mesh/GCI and heat-flow match not complete",
            "admission_status": "diagnostic_signal_only",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "predicted wall state and source-bounded exchange coefficient basis missing",
            "next_action": "finish same-label mesh/GCI and heat-flow match before any coefficient training",
            "scoreboard_presence": "scoreboard_supplement_required",
            "source_paths": ";".join([rel(MF15 / "runtime_operator_requirement_matrix.csv"), rel(MF17 / "summary.json")]),
        },
        {
            "rank": 5,
            "model_form_id": "MF15_axial_mixing_operator",
            "family": "thermal_axial_mixing",
            "model_form_name": "recirculation-supported axial redistribution operator",
            "mdot_path": "throughflow plus guarded recirculation/exchange state after MF04/M5 release",
            "temperature_path": "source-bounded axial redistribution with residence/exchange evidence",
            "pressure_path": "compatible with MF02 or M5 pressure residual lane",
            "train_status": "diagnostic only",
            "validation_holdout_status": "locked",
            "runtime_legality_status": "blocked by recirculation source basis and wall/core release",
            "source_property_status": "fail_closed",
            "uq_status": "MF17 temporal UQ executed; production and mesh/GCI still closed",
            "admission_status": "diagnostic_signal_only",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "exchange proxy cannot be used as an admitted runtime coefficient yet",
            "next_action": "after S13 exact-label repair, build exchange/recirculation source-bounded coefficient gate",
            "scoreboard_presence": "scoreboard_supplement_required",
            "source_paths": ";".join([rel(MF15 / "runtime_operator_requirement_matrix.csv"), rel(RECIRC / "recirculation_switch_lane_contract.csv")]),
        },
        {
            "rank": 6,
            "model_form_id": "M5_MF04_throughflow_recirculation_exchange_cell",
            "family": "recirculating_upcomer",
            "model_form_name": "throughflow plus recirculation exchange cell",
            "mdot_path": "throughflow branch plus guarded exchange cell",
            "temperature_path": "separate throughflow/core and recirculating cell energy exchange",
            "pressure_path": "section-effective pressure residual lane, not ordinary upcomer K",
            "train_status": "high-value next candidate after S13 exact-label/source gates",
            "validation_holdout_status": "locked",
            "runtime_legality_status": "dry contract ready; quantitative Qwall/source-property release not ready",
            "source_property_status": "fail_closed",
            "uq_status": "temporal UQ executed; mesh/GCI and production harvest blocked",
            "admission_status": "not_admitted",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "exact Qwall/source-side and same-label mesh/GCI gates",
            "next_action": "complete S13 sampler repair, then train only a predeclared exchange-cell structure on Salt1-4 nominal",
            "scoreboard_presence": "present_in_master_scoreboard_as_M5/S13_and_MF-04",
            "source_paths": ";".join([rel(MASTER / "master_model_form_scoreboard.csv"), rel(RECIRC / "summary.json")]),
        },
        {
            "rank": 7,
            "model_form_id": "M2_passive_wall_test_section_source_bounded_repair",
            "family": "thermal_source_basis",
            "model_form_name": "passive wall/test-section physical-basis repair",
            "mdot_path": "inherits base pressure root",
            "temperature_path": "independent passive hA/source-family envelope; no global multiplier",
            "pressure_path": "none added",
            "train_status": "not train-ready; physical basis package found no repair-run release",
            "validation_holdout_status": "locked",
            "runtime_legality_status": "passive family source basis remains weak",
            "source_property_status": "fail_closed",
            "uq_status": "needs source basis before UQ",
            "admission_status": "blocked_no_repair",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "passive hA/source provenance traces through wallHeatFlux or lacks independent basis",
            "next_action": "do not use global 0.5x hA as fit; admit only a physical source-bounded repair if provenance improves",
            "scoreboard_presence": "present_in_master_recommendations",
            "source_paths": rel(PASSIVE / "repair_no_repair_gate.csv"),
        },
        {
            "rank": 8,
            "model_form_id": "MF07_MF08_MF10_development_reset_signed_wallflux",
            "family": "entrance_development",
            "model_form_name": "development/reset plus signed wall-flux branch variants",
            "mdot_path": "hydraulic development/reset variants after ordinary-flow gates",
            "temperature_path": "negative cooler/downcomer cooling development; positive heater development; guarded upcomer handling",
            "pressure_path": "ordinary-flow-only hydraulic development lane",
            "train_status": "predeclared variants exist but smoke-ready rows are zero",
            "validation_holdout_status": "locked",
            "runtime_legality_status": "promising but source basis and reset/Graetz gates incomplete",
            "source_property_status": "fail_closed",
            "uq_status": "not executed as train-only Fluid model",
            "admission_status": "diagnostic_only",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "source basis, reset/Graetz, and upcomer guard inputs not released",
            "next_action": "after source release, train MF10d/MF10e variants on Salt1-4 nominal with upcomer guard predeclared",
            "scoreboard_presence": "scoreboard_supplement_required",
            "source_paths": ";".join([rel(MF07 / "candidate_gate.csv"), rel(MF08 / "candidate_gate.csv"), rel(MF10 / "variant_bakeoff_matrix.csv")]),
        },
        {
            "rank": 9,
            "model_form_id": "MF02_two_tap_section_effective_pressure",
            "family": "hydraulic_pressure",
            "model_form_name": "section-effective pressure residual / two-tap",
            "mdot_path": "section-effective pressure residual candidate",
            "temperature_path": "none; hydraulic residual attribution only",
            "pressure_path": "two-tap lower-leg/right-leg section residual",
            "train_status": "diagnostic no-fit pressure context only",
            "validation_holdout_status": "locked for coefficient admission",
            "runtime_legality_status": "usable for naming/negative result; coefficient not admitted",
            "source_property_status": "not_applicable_to_thermal_source_release",
            "uq_status": "needs low-recirculation anchors and same-QOI UQ",
            "admission_status": "not_admitted",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "nonrecirculating/low-reverse anchors and exact pressure endpoint evidence",
            "next_action": "keep as pressure residual owner while thermal forms train; do not fit component K on recirculating rows",
            "scoreboard_presence": "present_in_master_scoreboard",
            "source_paths": ";".join([rel(MASTER / "master_model_form_scoreboard.csv"), rel(PRESSURE / "summary.json")]),
        },
        {
            "rank": 10,
            "model_form_id": "MF01_ordinary_gated_single_stream_F6",
            "family": "hydraulic_pressure",
            "model_form_name": "ordinary gated single-stream F6 branch",
            "mdot_path": "ordinary branch fD/K/F6 only where RAF/RMF/SVF gates pass",
            "temperature_path": "none directly",
            "pressure_path": "right_leg/test_section_span ordinary candidates only",
            "train_status": "future candidate; no admitted rows now",
            "validation_holdout_status": "locked",
            "runtime_legality_status": "legal only after ordinary-flow and endpoint gates",
            "source_property_status": "not_applicable_to_thermal_source_release",
            "uq_status": "same-QOI UQ and endpoint pressure fields needed",
            "admission_status": "future_candidate",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "ordinary-flow gate and source endpoint evidence",
            "next_action": "try only on ordinary lanes after exact endpoint and same-QOI UQ; exclude recirculating upcomer",
            "scoreboard_presence": "present_in_master_scoreboard",
            "source_paths": ";".join([rel(MASTER / "recommended_model_forms_to_try.csv"), rel(S14 / "summary.json")]),
        },
        {
            "rank": 11,
            "model_form_id": "D1_D4_bias_correction_diagnostic_family",
            "family": "diagnostic_bias_shape",
            "model_form_name": "reduced-degree offset/shape corrections for discrepancy discovery",
            "mdot_path": "inherits M3 or chosen hydraulic base",
            "temperature_path": "global, sensor-kind, wall-shape, or segment offset correction as diagnostic only",
            "pressure_path": "none added",
            "train_status": "already tried as Salt2-train legacy diagnostic; can be reformulated as Salt1-4 nominal train-only after freeze protocol",
            "validation_holdout_status": "legacy Salt3/Salt4 transfer only; canonical protected scoring still locked",
            "runtime_legality_status": "forbidden as final unless coefficients are replaced by physical source-bounded closures",
            "source_property_status": "not a source-property release",
            "uq_status": "not sufficient for admission",
            "admission_status": "diagnostic_not_admitted",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "empirical residual corrections are not a physical predictive closure",
            "next_action": "use best D3/D4 shape as hypothesis generator for MF12/MF15, not as final model",
            "scoreboard_presence": "present_in_diagnostic_append_not_master",
            "source_paths": rel(SUGGESTED / "model_form_scoreboard_append.csv"),
        },
        {
            "rank": 12,
            "model_form_id": "M6_final_frozen_candidate",
            "family": "endpoint_scorecard",
            "model_form_name": "single frozen predictive candidate",
            "mdot_path": "frozen pressure model chosen before protected scoring",
            "temperature_path": "frozen thermal model chosen before protected scoring",
            "pressure_path": "pressure residual attribution emitted with model score",
            "train_status": "not created",
            "validation_holdout_status": "locked until exactly one candidate is frozen",
            "runtime_legality_status": "requires all runtime inputs and coefficients to be frozen from train/support only",
            "source_property_status": "blocked_by_MF16_no_release",
            "uq_status": "requires final uncertainty and leakage audit",
            "admission_status": "blocked_no_frozen_candidate",
            "can_train_now": False,
            "can_score_validation_now": False,
            "primary_blocker": "no runtime-legal frozen candidate",
            "next_action": "after Salt1-4 nominal training and gate release, freeze one candidate then score validation/holdout exactly once",
            "scoreboard_presence": "present_in_master_scoreboard",
            "source_paths": rel(MASTER / "master_model_form_scoreboard.csv"),
        },
    ]

    # Surface current gate states without letting them change the conservative booleans.
    for row in rows:
        row["forbidden_inputs"] = common_forbidden
        row["mf16_decision"] = mf16_summary.get("decision", "missing")
        row["mf17_decision"] = mf17_summary.get("decision", "missing")
        row["setup_uq_execution_decision"] = setup_exec_summary.get("decision", "running_or_missing")
    return rows


def scoreboard_presence_rows(roster: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = master_scoreboard_ids()
    names = recommended_names()
    checks = [
        ("M0", "M0_setup_only_baseline", "master_scoreboard"),
        ("M3", "M3_segment_only_fluid_walls", "master_scoreboard"),
        ("M5/S13", "M5_MF04_throughflow_recirculation_exchange_cell", "master_scoreboard"),
        ("MF-04", "M5_MF04_throughflow_recirculation_exchange_cell", "master_scoreboard"),
        ("MF-02/two-tap", "MF02_two_tap_section_effective_pressure", "master_scoreboard"),
        ("MF-01", "MF01_ordinary_gated_single_stream_F6", "master_scoreboard"),
        ("M6/S6", "M6_final_frozen_candidate", "master_scoreboard"),
        ("MF12", "MF12_signed_source_memory_bulk_to_TP", "supplement_only"),
        ("MF15_wall_core", "MF15_wall_core_exchange_operator", "supplement_only"),
        ("MF15_axial", "MF15_axial_mixing_operator", "supplement_only"),
        ("MF07/MF08/MF10", "MF07_MF08_MF10_development_reset_signed_wallflux", "supplement_only"),
        ("D1-D4", "D1_D4_bias_correction_diagnostic_family", "diagnostic_append"),
    ]
    roster_ids = {row["model_form_id"] for row in roster}
    rows: list[dict[str, Any]] = []
    for scoreboard_key, roster_id, expected_location in checks:
        in_master = scoreboard_key in ids or any(scoreboard_key in name for name in names)
        rows.append(
            {
                "scoreboard_key": scoreboard_key,
                "roster_model_form_id": roster_id,
                "present_in_master_scoreboard": in_master,
                "present_in_training_roster": roster_id in roster_ids,
                "expected_location": expected_location,
                "action": "covered" if (in_master or expected_location != "master_scoreboard") and roster_id in roster_ids else "needs_scoreboard_followup",
            }
        )
    return rows


def split_plan_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in ["salt_1_nominal", "salt_2_nominal", "salt_3_nominal", "salt_4_nominal"]:
        rows.append(
            {
                "case_or_family": case,
                "split_role": "train_nominal",
                "train_role_allowed": True,
                "coefficient_fit_allowed_now": False,
                "model_selection_allowed_now": False,
                "coefficient_fit_allowed_after_source_property_release": True,
                "score_claim_allowed": "train_support_execution_evidence_only",
                "claim_boundary": "Salt1-4 nominal training support for later coefficient discovery/freeze; current fitting remains locked until source/property release",
            }
        )
    for case in ["salt_1_minus10Q", "salt_1_plus10Q", "salt_4_minus5Q", "salt_4_plus5Q"]:
        rows.append(
            {
                "case_or_family": case,
                "split_role": "support_stress_or_sensitivity",
                "train_role_allowed": False,
                "coefficient_fit_allowed_now": False,
                "model_selection_allowed_now": False,
                "coefficient_fit_allowed_after_source_property_release": False,
                "score_claim_allowed": "support_diagnostic_only_after_train_freeze",
                "claim_boundary": "may audit robustness after coefficients are frozen; cannot tune coefficients",
            }
        )
    for case in ["salt_2_minus5Q", "salt_2_plus5Q"]:
        rows.append(
            {
                "case_or_family": case,
                "split_role": "holdout_testing",
                "train_role_allowed": False,
                "coefficient_fit_allowed_now": False,
                "model_selection_allowed_now": False,
                "coefficient_fit_allowed_after_source_property_release": False,
                "score_claim_allowed": "holdout_once_after_freeze_only",
                "claim_boundary": "protected holdout; no fitting, residual-owner tuning, or model-form selection",
            }
        )
    rows.append(
        {
            "case_or_family": "val_salt2",
            "split_role": "external_test",
            "train_role_allowed": False,
            "coefficient_fit_allowed_now": False,
            "model_selection_allowed_now": False,
            "coefficient_fit_allowed_after_source_property_release": False,
            "score_claim_allowed": "external_test_once_after_freeze_only",
            "claim_boundary": "external test; no tuning or rescue after looking",
        }
    )
    rows.append(
        {
            "case_or_family": "legacy_salt3_salt4_transfer_packages",
            "split_role": "legacy_diagnostic_context",
            "train_role_allowed": False,
            "coefficient_fit_allowed_now": False,
            "model_selection_allowed_now": False,
            "coefficient_fit_allowed_after_source_property_release": False,
            "score_claim_allowed": "cannot_be_combined_with_salt1_4_training_as_validation",
            "claim_boundary": "If Salt1-4 nominal are used for training, older Salt3/Salt4 transfer labels are historical diagnostics only.",
        }
    )
    return rows


def gate_rows(roster: list[dict[str, Any]]) -> list[dict[str, Any]]:
    can_train_count = sum(1 for row in roster if as_bool(str(row["can_train_now"])))
    can_score_count = sum(1 for row in roster if as_bool(str(row["can_score_validation_now"])))
    return [
        {
            "gate": "scoreboard_coverage",
            "status": "pass_for_roster",
            "evidence": f"{len(roster)} model-form rows in additive training roster; master scoreboard left unmutated",
            "next_required_action": "later scoring agent can consume model_form_training_roster.csv",
        },
        {
            "gate": "train_on_salt1_4_nominal",
            "status": "allowed_after_active_execution_close_for_diagnostic_training",
            "evidence": "canonical split table marks Salt1-4 nominal as train_nominal",
            "next_required_action": "do not read protected validation/holdout/external targets during coefficient discovery",
        },
        {
            "gate": "validation_holdout_scoring",
            "status": "locked",
            "evidence": f"can_score_validation_now rows={can_score_count}; no frozen candidate exists",
            "next_required_action": "freeze exactly one runtime-legal candidate before protected scoring",
        },
        {
            "gate": "runtime_source_property_release",
            "status": "fail_closed",
            "evidence": read_json(MF16 / "summary.json").get("decision", "missing"),
            "next_required_action": "recover strict source-property exact fields or keep thermal models diagnostic",
        },
        {
            "gate": "diagnostic_training_now",
            "status": "blocked_or_defer_to_active_setup_uq",
            "evidence": f"roster can_train_now rows={can_train_count}; active setup-UQ execution owns current train-only run",
            "next_required_action": "do not duplicate active train-only Fluid execution",
        },
    ]


def next_training_sequence_rows() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "phase": "close_active_train_only_setup_uq",
            "action": "Monitor and close TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION before interpreting M0/M3 setup-only train evidence.",
            "outputs_required": "scenario status, runtime leakage audit, train-only mdot/pressure/thermal residuals",
            "protected_rows": "validation/holdout/external not used",
        },
        {
            "step": 2,
            "phase": "source_property_recovery",
            "action": "Resolve MF16 blockers for q_setup, cp/property sensitivity, strict row-specific source envelope, and wall/profile conservation.",
            "outputs_required": "release matrix with nominal rows release-ready or explicit fail-closed evidence",
            "protected_rows": "no protected target temperatures",
        },
        {
            "step": 3,
            "phase": "predeclare_key_forms",
            "action": "Select 3-5 train-only forms from the roster before fitting: M0, M3, MF12, MF15/M5 exchange, and MF07/MF08/MF10 development/reset if gates pass.",
            "outputs_required": "fixed formula/parameter count/runtime input table",
            "protected_rows": "no validation/holdout scoring",
        },
        {
            "step": 4,
            "phase": "train_salt1_4_nominal",
            "action": "Train only on Salt1-4 nominal rows using setup/runtime-legal inputs and predeclared parameter families.",
            "outputs_required": "train residual table, pressure residual attribution, thermal residual attribution, parameter provenance",
            "protected_rows": "validation/holdout/external targets unread",
        },
        {
            "step": 5,
            "phase": "freeze_one_candidate",
            "action": "Choose exactly one candidate using train evidence and release gates; write freeze manifest before protected scoring.",
            "outputs_required": "frozen coefficient file, model form equation set, runtime leakage audit",
            "protected_rows": "still no protected scoring until manifest exists",
        },
        {
            "step": 6,
            "phase": "validation_holdout_external_once",
            "action": "Score validation/support, holdout, and external-test rows exactly once without changing coefficients.",
            "outputs_required": "separate train, support/validation, holdout, and external-test scorecards",
            "protected_rows": "no post-score tuning or rescue model selection",
        },
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [
        MASTER / "master_model_form_scoreboard.csv",
        MASTER / "recommended_model_forms_to_try.csv",
        MF12 / "candidate_bulk_to_tp_formulas.csv",
        MF15 / "runtime_operator_requirement_matrix.csv",
        MF16 / "summary.json",
        MF17 / "summary.json",
        MF07 / "candidate_gate.csv",
        MF08 / "candidate_gate.csv",
        MF10 / "variant_bakeoff_matrix.csv",
        RECIRC / "recirculation_switch_lane_contract.csv",
        SETUP_UQ_RUNBOOK / "split_and_runtime_guardrails.csv",
        SETUP_UQ_EXEC / "summary.json",
        SUGGESTED / "model_form_scoreboard_append.csv",
        PASSIVE / "repair_no_repair_gate.csv",
        PRESSURE / "summary.json",
        S14 / "summary.json",
    ]
    return [
        {
            "source_path": rel(path),
            "exists": path.exists(),
            "use": "read_only_context",
            "mutation_allowed": False,
        }
        for path in paths
    ]


def guardrail_rows() -> list[dict[str, Any]]:
    return [
        {"guardrail": "native_solver_outputs", "status": "not_mutated"},
        {"guardrail": "registry_or_admission_state", "status": "not_mutated"},
        {"guardrail": "scheduler_or_solver_launch", "status": "not_used"},
        {"guardrail": "Fluid_or_external_repo", "status": "not_mutated"},
        {"guardrail": "validation_holdout_external_scoring", "status": "not_performed"},
        {"guardrail": "fitting_or_model_selection", "status": "not_performed"},
        {"guardrail": "source_property_or_Qwall_release", "status": "not_released"},
        {"guardrail": "coefficient_admission_or_candidate_freeze", "status": "not_performed"},
        {"guardrail": "legacy_Salt3_Salt4_transfer_as_validation_after_Salt1_4_training", "status": "forbidden"},
    ]


def thesis_insert_text(summary: dict[str, Any]) -> str:
    return f"""# Thesis Model-Form Training Roster Insert

Generated: `{summary["generated_at"]}`  
Task: `{TASK_ID}`  
Decision: `{summary["decision"]}`

This package extends the master model-form scoreboard with the current trainable-form roster. It does not replace the master scoreboard and does not score validation, holdout, or external-test rows.

## Split Discipline

The next training step may use Salt1-4 nominal rows as `train_nominal`. Support, holdout, and external-test rows remain separate. Older Salt3/Salt4 transfer packages are historical diagnostics only if Salt1-4 nominal are used for training.

## Priority Forms

The first rigorous training wave should predeclare a small set: M0 setup-only baseline, M3 segment-only comparator, MF12 signed source-memory projection, MF15/M5 wall-core or recirculation exchange, and MF07/MF08/MF10 development/reset variants only if their source-basis gates open.

## Current Gate

Validation and holdout scoring remain locked. The strongest blocker is still runtime-legal source/property release, followed by exact Qwall/exchange/source-side production evidence and same-label mesh/GCI support.
"""


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  task_id: {TASK_ID}
  generated_at: {summary["generated_at"]}
tags:
  - thesis
  - model-form-scoreboard
  - train-validation-holdout
  - predictive-1d
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate/README.md
---
# Thesis Model-Form Scoreboard Training Roster

Decision: `{summary["decision"]}`.

This is an additive scoreboard supplement for the next modeling phase. It enumerates the model forms that should be tried, checks whether each family is already represented in the master scoreboard or needs this supplement, and defines the split contract for training on Salt1-4 nominal rows while keeping support, holdout, and external-test claims separate.

Key outputs:

- `model_form_training_roster.csv`: model forms, physics lanes, trainability gates, and next actions.
- `scoreboard_presence_audit.csv`: coverage against the master scoreboard and diagnostic appendices.
- `canonical_train_validation_holdout_plan.csv`: strict train/support/holdout/external-test split claims.
- `trainability_gate.csv`: current gating status before protected scoring.
- `next_training_sequence.csv`: order for later scoring agents.
- `thesis_model_form_training_roster_insert.md`: thesis-facing summary.

No fitting, model selection, validation scoring, holdout scoring, external-test scoring, source/property release, Qwall release, coefficient admission, candidate freeze, solver launch, scheduler action, native-output mutation, or registry/admission mutation was performed.
"""


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    roster = training_roster_rows()
    presence = scoreboard_presence_rows(roster)
    split = split_plan_rows()
    gates = gate_rows(roster)
    sequence = next_training_sequence_rows()
    manifest = source_manifest_rows()
    guardrails = guardrail_rows()

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "scoreboard_training_roster_complete_no_training_or_protected_scoring",
        "model_form_rows": len(roster),
        "scoreboard_presence_rows": len(presence),
        "train_nominal_rows": sum(1 for row in split if row["split_role"] == "train_nominal"),
        "support_rows": sum(1 for row in split if row["split_role"] == "support_stress_or_sensitivity"),
        "holdout_rows": sum(1 for row in split if row["split_role"] == "holdout_testing"),
        "external_test_rows": sum(1 for row in split if row["split_role"] == "external_test"),
        "can_train_now_rows": sum(1 for row in roster if row["can_train_now"]),
        "can_score_validation_now_rows": sum(1 for row in roster if row["can_score_validation_now"]),
        "source_property_release": "false",
        "qwall_release": "false",
        "candidate_freeze": "false",
        "validation_holdout_external_scoring_performed": "false",
    }

    roster_fields = [
        "rank",
        "model_form_id",
        "family",
        "model_form_name",
        "mdot_path",
        "temperature_path",
        "pressure_path",
        "train_status",
        "validation_holdout_status",
        "runtime_legality_status",
        "source_property_status",
        "uq_status",
        "admission_status",
        "can_train_now",
        "can_score_validation_now",
        "primary_blocker",
        "next_action",
        "scoreboard_presence",
        "forbidden_inputs",
        "mf16_decision",
        "mf17_decision",
        "setup_uq_execution_decision",
        "source_paths",
    ]
    csv_dump(out / "model_form_training_roster.csv", roster_fields, roster)
    csv_dump(
        out / "scoreboard_presence_audit.csv",
        ["scoreboard_key", "roster_model_form_id", "present_in_master_scoreboard", "present_in_training_roster", "expected_location", "action"],
        presence,
    )
    csv_dump(
        out / "canonical_train_validation_holdout_plan.csv",
        [
            "case_or_family",
            "split_role",
            "train_role_allowed",
            "coefficient_fit_allowed_now",
            "model_selection_allowed_now",
            "coefficient_fit_allowed_after_source_property_release",
            "score_claim_allowed",
            "claim_boundary",
        ],
        split,
    )
    csv_dump(out / "trainability_gate.csv", ["gate", "status", "evidence", "next_required_action"], gates)
    csv_dump(out / "next_training_sequence.csv", ["step", "phase", "action", "outputs_required", "protected_rows"], sequence)
    csv_dump(out / "source_manifest.csv", ["source_path", "exists", "use", "mutation_allowed"], manifest)
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "status"], guardrails)
    json_dump(out / "summary.json", summary)
    (out / "README.md").write_text(readme_text(summary), encoding="utf-8")
    (out / "thesis_model_form_training_roster_insert.md").write_text(thesis_insert_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
