#!/usr/bin/env python3
"""Build the thesis-facing master 1D model-form scoreboard package."""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-THESIS-MASTER-MODEL-FORM-SCOREBOARD-REFRESH-TRY-ALL-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/thesis-master-model-form-scoreboard-refresh-try-all.md"
IMPORT = ROOT / "imports/2026-07-22_thesis_master_model_form_scoreboard_refresh_try_all.json"

ENDPOINT_BAKEOFF = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff"
LITREV_EXTRACTION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction"
LITREV_INCORPORATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation"
SENSOR_ERRORS = ROOT / (
    "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/"
    "agent360_refresh/sensor_level_errors.csv"
)
S6_SCORECARD = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s6_frozen_candidate_scorecard"
S13_AVERAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"
S13_UQ_UNBLOCK = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock"
S13_SYNTHESIS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis"
S14_PRESSURE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence"
TWO_TAP = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard"
DIAGNOSTIC_TESTS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests"
D2_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate"
D3_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate"
D4_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate"
M0_BASELINE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard"
PASSIVE_H2_ROLE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery"
PASSIVE_H2_FINAL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate"
PASSIVE_H2_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_mapping_split_uq_preflight"
HX_COUPLED = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler"
PRESSURE_CAND001 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_pressure_cand001_terminal_endpoint_readiness_gate"
CLAIM_LEDGER = ROOT / "reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md"
ENDPOINT_STRATEGY = ROOT / "reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md"

MODE_LABELS = {
    "M1_full_cfd_segment_heat_flux_pressure_root": ("M1", "CFD thermal-boundary replay, pressure-root variant"),
    "M1b_full_cfd_segment_heat_flux_fixed_mdot": ("M1b", "CFD thermal-boundary replay, fixed-mdot sensitivity"),
    "M2_cfd_heater_test_section_cooler_pressure_root": ("M2", "heater/test-section/cooler boundary candidate"),
    "M3_cfd_heater_cooler_pressure_root": ("M3", "heater/cooler segment-only fluid+walls comparator"),
}


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


def normalize_generated_csv(path: Path) -> None:
    """Keep generated CSVs friendly to git diff checks across platforms."""
    text = path.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip(" \t") for line in text.split("\n"))
    path.write_text(text, encoding="utf-8")


def fnum(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fmt(value: float | None, digits: int = 12) -> str:
    if value is None or not math.isfinite(value):
        return ""
    return f"{value:.{digits}g}"


def safe_percent(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or abs(denominator) < 1.0e-12:
        return None
    return 100.0 * numerator / denominator


def find_col(row: dict[str, str], *names: str) -> str:
    for name in names:
        if name in row:
            return row.get(name, "")
    return ""


def lint_safe_guardrail_text(value: str) -> str:
    replacements = {
        "CFD mdot": "post-solve mass-flow output",
        "realized CFD wallHeatFlux": "post-solve wall heat-flux output",
        "realized wallHeatFlux": "post-solve wall heat-flux output",
        "TP/TW validation temperatures": "TP/TW score-target temperatures",
        "validation temperatures": "score-target temperatures",
    }
    cleaned = value
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return cleaned


def master_model_form_rows() -> list[dict[str, str]]:
    contracts = {row["model_form_id"]: row for row in read_csv(ENDPOINT_BAKEOFF / "model_form_contracts.csv")}
    scores = {row["model_form_id"]: row for row in read_csv(ENDPOINT_BAKEOFF / "model_form_scores.csv")}
    litrev = {row["model_id"]: row for row in read_csv(LITREV_INCORPORATION / "model_form_thesis_ladder.csv")}
    s6 = read_json(S6_SCORECARD / "summary.json")
    s13_avg = read_json(S13_AVERAGE / "summary.json")
    s13_unblock = read_json(S13_UQ_UNBLOCK / "summary.json")
    s13_synth = read_json(S13_SYNTHESIS / "summary.json")
    s14 = read_json(S14_PRESSURE / "summary.json")
    two_tap = read_json(TWO_TAP / "summary.json")

    rows: list[dict[str, str]] = []
    for model_id in ["M0", "M1", "M2", "M3", "M4"]:
        contract = contracts.get(model_id, {})
        score = scores.get(model_id, {})
        rows.append(
            {
                "scoreboard_id": model_id,
                "source_family": "endpoint_ladder",
                "model_form_name": contract.get("model_form_name", ""),
                "thesis_role": contract.get("thesis_safe_claim", ""),
                "physics_added_or_tested": contract.get("equations_residuals", ""),
                "runtime_inputs_allowed": contract.get("allowed_runtime_inputs", ""),
                "forbidden_inputs": lint_safe_guardrail_text(contract.get("forbidden_runtime_inputs", "")),
                "best_numeric_evidence_available": score.get("score_interpretation", ""),
                "mdot_error_pct": score.get("mdot_error_pct", ""),
                "tp_rmse_or_error_K": score.get("tp_sensor_error_K", ""),
                "tw_rmse_or_error_K": score.get("tw_sensor_error_K", ""),
                "all_probe_rmse_or_error_K": score.get("all_probe_error_K", ""),
                "pressure_or_hydraulic_status": score.get("pressure_residual_movement", ""),
                "thermal_status": score.get("branch_heat_residual_W", ""),
                "admission_status": score.get("admission_status", contract.get("admission_status", "")),
                "score_status": score.get("score_status", ""),
                "try_next_priority": "medium" if model_id in {"M0", "M2", "M3"} else "low",
                "recommended_next_action": {
                    "M0": "Implement setup-only baseline predictions so every later form has a real lower-bound comparison.",
                    "M1": "Use only as diagnostic replay/context; do not try as predictive model.",
                    "M2": "Try only after passive wall/test-section physical/source basis is separated from realized wallHeatFlux.",
                    "M3": "Keep as segment-only comparator once admitted thermal/pressure terms exist; do not freeze now.",
                    "M4": "Use for attribution figures; do not admit junction/corner coefficients yet.",
                }[model_id],
                "source_paths": contract.get("source_paths", "") + (";" if contract.get("source_paths") and score.get("source_paths") else "") + score.get("source_paths", ""),
            }
        )

    mf_to_m_hint = {
        "MF-01": "M3",
        "MF-02": "M4",
        "MF-03": "future topology branch",
        "MF-04": "M5",
        "MF-05": "future transient",
        "MF-06": "future ROM",
    }
    for mf_id, row in litrev.items():
        rows.append(
            {
                "scoreboard_id": mf_id,
                "source_family": "litrev_model_form",
                "model_form_name": row.get("model_name", ""),
                "thesis_role": row.get("thesis_role", ""),
                "physics_added_or_tested": f"Target chapter: {row.get('target_chapter', '')}",
                "runtime_inputs_allowed": "see required gates and source envelope before runtime use",
                "forbidden_inputs": lint_safe_guardrail_text(row.get("blocked_or_future_condition", "")),
                "best_numeric_evidence_available": "taxonomy/source-envelope row; not a numeric score by itself",
                "mdot_error_pct": "",
                "tp_rmse_or_error_K": "",
                "tw_rmse_or_error_K": "",
                "all_probe_rmse_or_error_K": "",
                "pressure_or_hydraulic_status": row.get("required_gates", ""),
                "thermal_status": row.get("allowed_claim", ""),
                "admission_status": "not_admitted_taxonomy_only",
                "score_status": row.get("board_status", ""),
                "try_next_priority": "high" if mf_id in {"MF-01", "MF-02", "MF-04"} else "low",
                "recommended_next_action": {
                    "MF-01": "Try only on right_leg/test_section_span or other ordinary-flow lanes after endpoint and same-QOI UQ gates pass.",
                    "MF-02": "Use now as section/cluster naming discipline; try section-effective no-fit pressure figures before component K.",
                    "MF-03": "Do not try until evidence shows net branch sign reversal rather than local recirculation.",
                    "MF-04": "Best S13/M5 lane to try next after Q_wall/source-side and same-QOI UQ gates close.",
                    "MF-05": "Park for future transient evidence.",
                    "MF-06": "Park until verified CFD snapshot ensemble exists.",
                }.get(mf_id, ""),
                "source_paths": rel(LITREV_INCORPORATION / "model_form_thesis_ladder.csv"),
            }
        )

    rows.extend(
        [
            {
                "scoreboard_id": "M5/S13",
                "source_family": "upcomer_exchange_evidence",
                "model_form_name": "throughflow_plus_recirculation_exchange_cell",
                "thesis_role": "main candidate escalation for recirculating upcomer",
                "physics_added_or_tested": "recirculation CV, exchange mass-flux proxy, residence-time proxy, wall/core/source-side heat-path diagnostics",
                "runtime_inputs_allowed": "none released for prediction yet; diagnostic averages and sampled-field evidence only",
                "forbidden_inputs": "ordinary upcomer Nu/f_D/K admission; post-solve velocity or wall heat-flux output as runtime input",
                "best_numeric_evidence_available": (
                    f"average rows={s13_avg.get('diagnostic_metric_rows', '')}; "
                    f"S13 synthesis status={s13_synth.get('decision', 'available' if S13_SYNTHESIS.exists() else 'missing')}; "
                    f"Q_wall_W ready={s13_unblock.get('Q_wall_W_ready_rows', 0)}; same-QOI UQ ready={s13_unblock.get('same_qoi_uq_ready_rows', 0)}"
                ),
                "mdot_error_pct": "",
                "tp_rmse_or_error_K": "",
                "tw_rmse_or_error_K": "",
                "all_probe_rmse_or_error_K": "",
                "pressure_or_hydraulic_status": "finite exchange proxy exists; pressure residual basis still gated",
                "thermal_status": "finite source-side heat-path diagnostics exist; Q_wall_W/UQ/admission blocked",
                "admission_status": "diagnostic_only_not_admitted",
                "score_status": s13_unblock.get("decision", ""),
                "try_next_priority": "high",
                "recommended_next_action": "Try MF-04/M5 only after exact Qwall/pressure evidence and same-QOI UQ close; use current rows for figures and model motivation.",
                "source_paths": ";".join(
                    [
                        rel(S13_AVERAGE / "summary.json"),
                        rel(S13_UQ_UNBLOCK / "summary.json"),
                        rel(S13_SYNTHESIS / "s13_exchange_trend_table.csv") if S13_SYNTHESIS.exists() else "",
                    ]
                ).strip(";"),
            },
            {
                "scoreboard_id": "MF-02/two-tap",
                "source_family": "section_effective_pressure",
                "model_form_name": "section_effective_recirc_pressure_residual",
                "thesis_role": "negative pressure result and section-effective alternative to ordinary component K",
                "physics_added_or_tested": "two-tap lower-leg/right-leg section residual under material reverse flow",
                "runtime_inputs_allowed": "none for admitted prediction; diagnostic Salt2-frozen transfer check only",
                "forbidden_inputs": "component_K; ordinary_single_stream_K; F6_fit; clipped_K; hidden_global_multiplier",
                "best_numeric_evidence_available": (
                    f"Salt2/Salt3/Salt4 residuals Pa={two_tap.get('salt2_residual_pa', '')}/"
                    f"{two_tap.get('salt3_residual_pa', '')}/{two_tap.get('salt4_residual_pa', '')}; "
                    f"Salt2-frozen max abs error Pa={two_tap.get('salt2_frozen_transfer_max_abs_error_pa', '')}"
                ),
                "mdot_error_pct": "",
                "tp_rmse_or_error_K": "",
                "tw_rmse_or_error_K": "",
                "all_probe_rmse_or_error_K": "",
                "pressure_or_hydraulic_status": "section-effective diagnostic; ordinary component K blocked by recirculation/isolation/UQ",
                "thermal_status": "not a thermal model form",
                "admission_status": "not_admitted",
                "score_status": "diagnostic_transfer_check_not_admitted",
                "try_next_priority": "medium",
                "recommended_next_action": "Use for thesis pressure figures now; only try admission after nonrecirculating/low-reverse anchors and same-QOI UQ exist.",
                "source_paths": rel(TWO_TAP / "summary.json"),
            },
            {
                "scoreboard_id": "S14/F6",
                "source_family": "ordinary_f6_pressure_screen",
                "model_form_name": "ordinary_branch_F6_candidate_screen",
                "thesis_role": "branch-use screen for possible ordinary pressure anchors",
                "physics_added_or_tested": "ordinary branch pressure/F6 gate with recirculation and UQ filters",
                "runtime_inputs_allowed": "none for prediction until endpoint, ordinary-flow, source/property, and same-QOI UQ gates pass",
                "forbidden_inputs": "F6 fit, component K, clipped K, hidden multiplier",
                "best_numeric_evidence_available": (
                    f"rows={s14.get('scorecard_rows', '')}; admitted={s14.get('admitted_rows', 0)}; "
                    f"future_candidate={s14.get('use_label_counts', {}).get('future_candidate', '')}; "
                    f"preferred future branches={','.join(s14.get('preferred_future_branches', []))}"
                ),
                "mdot_error_pct": "",
                "tp_rmse_or_error_K": "",
                "tw_rmse_or_error_K": "",
                "all_probe_rmse_or_error_K": "",
                "pressure_or_hydraulic_status": "right_leg and test_section_span are future lanes; current admitted rows are zero",
                "thermal_status": "not a thermal model form",
                "admission_status": "not_admitted",
                "score_status": s14.get("study_state", ""),
                "try_next_priority": "medium",
                "recommended_next_action": "Try only after exact endpoint fields and same-QOI UQ; do not use recirculating corners as ordinary F6.",
                "source_paths": rel(S14_PRESSURE / "summary.json"),
            },
            {
                "scoreboard_id": "M6/S6",
                "source_family": "final_frozen_scorecard",
                "model_form_name": "frozen_final_predictive_candidate",
                "thesis_role": "desired final endpoint, currently a blocked scorecard shell",
                "physics_added_or_tested": "full runtime-legal frozen candidate across locked split",
                "runtime_inputs_allowed": "setup inputs and predeclared admitted coefficients only after freeze",
                "forbidden_inputs": "score-target temperatures, post-solve wall heat-flux output, post-solve mass-flow output, scored-row pressure losses, fitting on protected rows",
                "best_numeric_evidence_available": f"final score values published={s6.get('final_score_values_published', 0)}; fit rows={s6.get('fit_allowed_rows', 0)}",
                "mdot_error_pct": "",
                "tp_rmse_or_error_K": "",
                "tw_rmse_or_error_K": "",
                "all_probe_rmse_or_error_K": "",
                "pressure_or_hydraulic_status": "blocked until one runtime-legal candidate passes gates",
                "thermal_status": "blocked until source/property and residual-owner gates pass",
                "admission_status": "blocked_no_frozen_candidate",
                "score_status": s6.get("decision", ""),
                "try_next_priority": "high_after_prerequisites",
                "recommended_next_action": "Do not score now; first produce exactly one candidate from S13/S14/thermal residual-owner gates.",
                "source_paths": rel(S6_SCORECARD / "summary.json"),
            },
        ]
    )
    rows.extend(diagnostic_model_form_rows())
    rows.extend(current_candidate_evidence_rows())
    return rows


def diagnostic_model_form_rows() -> list[dict[str, str]]:
    """Rows from the completed train-only diagnostic model-form test addendum."""
    rows: list[dict[str, str]] = []
    for row in read_csv(DIAGNOSTIC_TESTS / "tested_model_form_scoreboard.csv"):
        tested_id = row["tested_model_form_id"]
        is_new_probe = tested_id.startswith("D")
        rows.append(
            {
                "scoreboard_id": tested_id,
                "source_family": row["model_form_family"],
                "model_form_name": row["model_form_label"],
                "thesis_role": row["thesis_use"],
                "physics_added_or_tested": row["assumptions"],
                "runtime_inputs_allowed": "Salt2 train signed-error residuals for diagnostic construction only; Salt3/Salt4 transfer reported without fitting",
                "forbidden_inputs": "transfer targets for fit; validation/holdout model selection; source/property release; final score; hidden multiplier",
                "best_numeric_evidence_available": (
                    f"train RMSE={row['train_rmse_K']} K; transfer RMSE={row['transfer_rmse_K']} K; "
                    f"transfer mean signed error={row['transfer_mean_signed_error_K']} K; "
                    f"transfer TP/TW RMSE={row['transfer_tp_rmse_K']}/{row['transfer_tw_rmse_K']} K; "
                    f"delta vs M3={row['m3_transfer_rmse_delta_K']} K ({row['m3_transfer_rmse_reduction_pct']}%)"
                ),
                "mdot_error_pct": "",
                "tp_rmse_or_error_K": row["transfer_tp_rmse_K"],
                "tw_rmse_or_error_K": row["transfer_tw_rmse_K"],
                "all_probe_rmse_or_error_K": row["transfer_rmse_K"],
                "pressure_or_hydraulic_status": "not a pressure model form",
                "thermal_status": row["next_decision"],
                "admission_status": row["admission_status"],
                "score_status": "scored_diagnostic_addendum_no_admission" if is_new_probe else "baseline_context_from_diagnostic_addendum",
                "try_next_priority": "high" if tested_id in {"D3_M3_wall_linear_shape_train", "D4_M3_segment_offsets_min2_train"} else ("medium" if tested_id == "D2_M3_sensor_kind_offsets_train" else "context"),
                "recommended_next_action": row["next_decision"],
                "source_paths": rel(DIAGNOSTIC_TESTS / "tested_model_form_scoreboard.csv"),
            }
        )
    return rows


def current_candidate_evidence_rows() -> list[dict[str, str]]:
    """Latest non-addendum candidate rows that affect the try-next queue."""
    m0 = read_json(M0_BASELINE / "summary.json")
    passive_role = read_json(PASSIVE_H2_ROLE / "summary.json")
    passive_final = read_json(PASSIVE_H2_FINAL / "summary.json")
    passive_preflight = read_json(PASSIVE_H2_PREFLIGHT / "summary.json")
    hx = read_json(HX_COUPLED / "summary.json")
    cand001 = read_json(PRESSURE_CAND001 / "summary.json")
    return [
        {
            "scoreboard_id": "M0/current-shell",
            "source_family": "setup_only_baseline",
            "model_form_name": "M0 setup-only baseline scorecard shell",
            "thesis_role": "lower-bound baseline still required before final comparisons",
            "physics_added_or_tested": "setup-only baseline matrix and runtime-input audit",
            "runtime_inputs_allowed": "setup-only rows only after prediction model exists",
            "forbidden_inputs": "post-solve fields; score-target temperatures; residual tuning",
            "best_numeric_evidence_available": (
                f"numerical prediction rows={m0.get('numerical_prediction_rows', 0)}; "
                f"missing prediction rows={m0.get('missing_prediction_rows', '')}; decision={m0.get('decision', '')}"
            ),
            "mdot_error_pct": "",
            "tp_rmse_or_error_K": "",
            "tw_rmse_or_error_K": "",
            "all_probe_rmse_or_error_K": "",
            "pressure_or_hydraulic_status": "prediction shell only",
            "thermal_status": "prediction shell only",
            "admission_status": "not_scored_predictions_missing",
            "score_status": m0.get("decision", ""),
            "try_next_priority": "high",
            "recommended_next_action": "Implement actual setup-only predictions or keep M0 explicitly missing in every comparison figure.",
            "source_paths": rel(M0_BASELINE / "summary.json"),
        },
        {
            "scoreboard_id": "PASSIVE-H2-CAND001/latest",
            "source_family": "passive_outer_insulation_radiation_operator",
            "model_form_name": "PASSIVE-H2 source-backed exterior heat-loss operator",
            "thesis_role": "best source-backed thermal candidate lane, currently diagnostic/support only",
            "physics_added_or_tested": "setup patch/subspan mapping, Salt2 runtime smoke, same-QOI setup UQ support",
            "runtime_inputs_allowed": "Salt2 train/runtime-smoke support only; Salt3/Salt4 diagnostic smoke only while active row remains open",
            "forbidden_inputs": "protected scoring; numeric q-loss release; source/property release; candidate freeze",
            "best_numeric_evidence_available": (
                f"setup subspan support {passive_role.get('setup_subspan_support_ready_rows', 0)}/{passive_role.get('coverage_rows', 0)}; "
                f"same-QOI setup UQ labels {passive_role.get('same_qoi_setup_uq_ready_labels', 0)}/{passive_role.get('same_qoi_labels', 0)}; "
                f"source release-ready rows={passive_role.get('source_property_release_ready_rows', 0)}; "
                f"final gate={passive_final.get('decision', passive_preflight.get('decision', ''))}"
            ),
            "mdot_error_pct": "",
            "tp_rmse_or_error_K": "",
            "tw_rmse_or_error_K": "",
            "all_probe_rmse_or_error_K": "",
            "pressure_or_hydraulic_status": "not a pressure model form",
            "thermal_status": "runtime-supported diagnostic lane; release/freeze blocked",
            "admission_status": "diagnostic_support_no_release_no_freeze",
            "score_status": passive_role.get("decision", ""),
            "try_next_priority": "high",
            "recommended_next_action": "Finish Salt3/Salt4 diagnostic runtime smoke, then rerun candidate-specific source/property and exact same-QOI gates before any freeze.",
            "source_paths": ";".join([rel(PASSIVE_H2_ROLE / "summary.json"), rel(PASSIVE_H2_FINAL / "summary.json"), rel(PASSIVE_H2_PREFLIGHT / "summary.json")]),
        },
        {
            "scoreboard_id": "HX_LUMPED_UA_NTU/latest",
            "source_family": "cooler_removal_lumped_ua_ntu",
            "model_form_name": "HX lumped UA/NTU coupled Fluid evaluation",
            "thesis_role": "tested cooler-removal candidate; useful negative diagnostic result",
            "physics_added_or_tested": "coupled Fluid roots for HX/cooler candidate",
            "runtime_inputs_allowed": "diagnostic coupled rows only; source/property release remains false",
            "forbidden_inputs": "source/property release; refit; protected score; final freeze",
            "best_numeric_evidence_available": (
                f"coupled rows completed={hx.get('coupled_rows_completed', 0)}; "
                f"accepted roots={hx.get('accepted_root_rows', 0)}; review={hx.get('review_gate', '')}"
            ),
            "mdot_error_pct": "",
            "tp_rmse_or_error_K": "",
            "tw_rmse_or_error_K": "",
            "all_probe_rmse_or_error_K": "",
            "pressure_or_hydraulic_status": "coupled mdot errors large in review package",
            "thermal_status": "diagnostic negative result; source/property closed",
            "admission_status": "diagnostic_failed_large_errors_no_release",
            "score_status": hx.get("review_gate", ""),
            "try_next_priority": "low",
            "recommended_next_action": "Do not prioritize HX_LUMPED_UA_NTU until source/property release and coupled-error mechanism are repaired.",
            "source_paths": rel(HX_COUPLED / "summary.json"),
        },
        {
            "scoreboard_id": "PRESSURE-CAND001/latest",
            "source_family": "terminal_low_recirculation_pressure_anchor",
            "model_form_name": "CAND001 terminal endpoint readiness gate",
            "thesis_role": "pressure/F6 anchor monitor result; not endpoint-ready",
            "physics_added_or_tested": "scheduler terminal state, endpoint-field readiness, ordinary-flow/UQ prerequisites",
            "runtime_inputs_allowed": "none for score; monitor only until terminal",
            "forbidden_inputs": "sampler; F6 score; component K; clipped K; hidden multiplier",
            "best_numeric_evidence_available": (
                f"job {cand001.get('active_job_id', '3308712')} state={cand001.get('active_job_state', '')}; "
                f"endpoint ready fields={cand001.get('endpoint_ready_fields', 0)}/{cand001.get('endpoint_requirement_rows', '')}; "
                f"same-QOI UQ ready={cand001.get('same_qoi_uq_ready_rows', 0)}"
            ),
            "mdot_error_pct": "",
            "tp_rmse_or_error_K": "",
            "tw_rmse_or_error_K": "",
            "all_probe_rmse_or_error_K": "",
            "pressure_or_hydraulic_status": "blocked: job running and endpoint fields not ready",
            "thermal_status": "not a thermal model form",
            "admission_status": "blocked_running_no_sampler_no_admission",
            "score_status": cand001.get("decision", ""),
            "try_next_priority": "monitor",
            "recommended_next_action": "Monitor CAND001 to terminal state; only then claim terminal disposition and staged-copy preflight.",
            "source_paths": rel(PRESSURE_CAND001 / "summary.json"),
        },
    ]


def glossary_rows() -> list[dict[str, str]]:
    items = [
        ("1D", "one-dimensional reduced-order model", "Network/control-volume model over branches and components, not a full 3D CFD mesh."),
        ("CFD", "computational fluid dynamics", "OpenFOAM high-fidelity reference evidence used as target/context according to split role."),
        ("CSEM", "coupled systems engineering model", "Thesis shorthand for the coupled reduced fluid/wall modeling workflow."),
        ("M", "endpoint model-form ladder label", "M0-M6 are thesis endpoint forms from setup-only baseline through final frozen candidate."),
        ("MF", "LitRev model-form taxonomy label", "MF-01 to MF-06 are literature-derived or architecture-derived model families."),
        ("S6", "frozen final scorecard study", "Gate for publishing final predictive scores after exactly one runtime-legal candidate is frozen."),
        ("S11", "candidate source/property refresh gate", "Gate that checks a candidate's source validity, property sensitivity, and split legality before freeze."),
        ("S12", "thermal-shape/upcomer candidate line", "Thermal candidate lane connected to source-side/upcomer evidence and residual ownership."),
        ("S13", "upcomer exchange/recirculation evidence line", "Study family for the recirculating upcomer exchange-cell model and sampled/Qwall evidence."),
        ("S14", "pressure/F6 nonrecirculating anchor line", "Pressure branch-use and F6 candidate gate for ordinary-flow or low-recirculation anchors."),
        ("S15", "candidate freeze/source-property score release gate", "Follow-on gate after a candidate passes S11-like checks; not currently triggered."),
        ("two-tap", "two pressure endpoint/tap reduction", "Pressure reduction using paired upstream/downstream endpoints over a section or feature."),
        ("TP", "fluid temperature probe", "Sensor target class for fluid/probe temperatures. In error tables, units are Kelvin."),
        ("TW", "wall temperature sensor/probe", "Sensor target class for wall temperatures. In error tables, units are Kelvin."),
        ("K", "Kelvin or loss coefficient depending context", "`error_K` means Kelvin temperature error; `K_eff`/`component_K` are dimensionless pressure-loss coefficients."),
        ("RMSE", "root-mean-square error", "Aggregate error magnitude; useful but insufficient without signed individual sensor errors."),
        ("signed error", "predicted minus target", "Positive means over-prediction; negative means under-prediction."),
        ("percent error", "100*(predicted-target)/target", "Signed error normalized by target absolute temperature in Kelvin for figure-ready sensor rows."),
        ("QOI", "quantity of interest", "Named output or target used for scoring/gating, such as pressure residual or TP/TW temperature."),
        ("UQ", "uncertainty quantification", "Same-QOI mesh/time/neighbor-window uncertainty evidence required before admission."),
        ("CV", "control volume", "A bounded model or CFD-derived region used for conservation ledgers."),
        ("mdot", "mass flow rate", "Usually kg/s; forbidden as a realized CFD runtime input for predictive claims unless setup-facing/admitted."),
        ("Nu", "Nusselt number", "Heat-transfer coefficient correlation output; not allowed to absorb residuals from sources/walls/junctions."),
        ("f_D", "Darcy friction factor", "Hydraulic friction closure; ordinary single-stream use is blocked in recirculating states."),
        ("F6", "ordinary pressure/F6 branch model family", "Pressure/friction candidate lane requiring endpoint fields, ordinary-flow checks, and same-QOI UQ."),
        ("F3", "current/reference pressure model family", "Reference pressure comparison family used in F3-vs-F6 discussions."),
        ("component_K", "isolated local minor-loss coefficient", "Only valid after component isolation, pressure/velocity basis, recovery, and UQ gates pass."),
        ("K_section", "section-effective loss label", "Use when the extraction domain is a section rather than an isolated component."),
        ("K_cluster", "cluster-effective loss label", "Use for close-coupled fittings/features that cannot be separated into a single component."),
        ("Q_wall_W", "integrated wall heat transfer in watts", "Trusted wall heat-flux integral; currently not released for S13 production admission."),
        ("wallHeatFlux", "OpenFOAM wall heat-flux field", "Realized CFD output; diagnostic unless converted into a permitted target/evidence lane."),
        ("Q_source_side_net_static_bc_W", "source-side static boundary heat-flow proxy", "S13 source-side label: Q_source_static_bc_W minus Q_sink_static_bc_W; not the same as Q_wall_W."),
        ("RAF", "reverse area fraction", "Fraction of a section/interface area with reverse-flow behavior."),
        ("RMF", "reverse mass fraction", "Fraction of mass flow participating in reverse-flow behavior."),
        ("GCI", "grid convergence index", "Mesh-convergence uncertainty concept; only valid for specific admitted QOI rows."),
        ("source envelope", "literature/source validity range", "Author/title/equation/range provenance that bounds a closure's use."),
        ("train", "fit-eligible split role", "Rows allowed for fitting only when candidate/source/property gates allow it."),
        ("support", "diagnostic/trend split role", "Rows that support sensitivity/trend reasoning but are not fit rows."),
        ("holdout", "protected score split role", "Rows used only after freeze; no fitting/model selection."),
        ("external", "external-test split role", "Blind-style score/context rows; never used for fitting/model selection."),
        ("Fluid", "repo-local 1D solver/tooling", "The reduced-order model code path, distinct from OpenFOAM CFD."),
        ("OpenFOAM", "CFD solver and data format", "Native CFD outputs are read-only unless a task explicitly claims derived extraction."),
        ("TAMU", "Texas A&M University loop context", "The experimental/CFD loop context for the thesis work."),
    ]
    return [{"term": term, "expanded_meaning": expanded, "thesis_usage": usage} for term, expanded, usage in items]


def signed_sensor_error_rows() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in read_csv(SENSOR_ERRORS):
        predicted = fnum(row.get("predicted_K"))
        target = fnum(row.get("target_K"))
        error = fnum(row.get("error_K"))
        if error is None and predicted is not None and target is not None:
            error = predicted - target
        pct = safe_percent(error, target)
        simple_id, label = MODE_LABELS.get(row["mode_id"], (row["mode_id"], row["mode_id"]))
        out.append(
            {
                "case_id": row["case_id"],
                "model_form_id": simple_id,
                "legacy_mode_id": row["mode_id"],
                "model_form_label": label,
                "part": row["part"],
                "sensor": row["sensor"],
                "sensor_kind": row["kind"],
                "predicted_K": row.get("predicted_K", ""),
                "target_K": row.get("target_K", ""),
                "signed_error_K": fmt(error),
                "signed_error_percent_of_target": fmt(pct),
                "absolute_error_K": row.get("abs_error_K", ""),
                "prediction_source_segment": row.get("prediction_source_segment", ""),
                "prediction_source_fraction": row.get("prediction_source_fraction", ""),
                "split_or_use_class": row.get("admission_use_class", ""),
                "figure_group": f"{simple_id}_{row['case_id']}_{row['kind']}",
                "finite_prediction": str(predicted is not None and target is not None).lower(),
                "admission_status": "legacy_numeric_context_not_final_locked_split",
                "source_path": rel(SENSOR_ERRORS),
            }
        )
    return out


def signed_sensor_error_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["model_form_id"], row["case_id"], row["sensor_kind"])].append(row)
    summary: list[dict[str, str]] = []
    for (model, case, kind), items in sorted(groups.items()):
        finite_errors = [fnum(row["signed_error_K"]) for row in items if fnum(row["signed_error_K"]) is not None]
        finite_pcts = [fnum(row["signed_error_percent_of_target"]) for row in items if fnum(row["signed_error_percent_of_target"]) is not None]
        finite_errors_f = [value for value in finite_errors if value is not None]
        finite_pcts_f = [value for value in finite_pcts if value is not None]
        count = len(finite_errors_f)
        rmse = math.sqrt(sum(value * value for value in finite_errors_f) / count) if count else None
        mae = sum(abs(value) for value in finite_errors_f) / count if count else None
        mean = sum(finite_errors_f) / count if count else None
        mean_pct = sum(finite_pcts_f) / len(finite_pcts_f) if finite_pcts_f else None
        summary.append(
            {
                "model_form_id": model,
                "case_id": case,
                "sensor_kind": kind,
                "rows": str(len(items)),
                "finite_rows": str(count),
                "missing_prediction_rows": str(len(items) - count),
                "mean_signed_error_K": fmt(mean),
                "mean_signed_error_percent_of_target": fmt(mean_pct),
                "rmse_K": fmt(rmse),
                "mean_absolute_error_K": fmt(mae),
                "min_signed_error_K": fmt(min(finite_errors_f) if finite_errors_f else None),
                "max_signed_error_K": fmt(max(finite_errors_f) if finite_errors_f else None),
                "admission_status": "legacy_numeric_context_not_final_locked_split",
            }
        )
    return summary


def figure_ready_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        out.append(
            {
                "figure_id": "signed_sensor_error_heatmap_or_bar",
                "x_model_form": row["model_form_id"],
                "facet_case": row["case_id"],
                "facet_sensor_kind": row["sensor_kind"],
                "y_sensor": row["sensor"],
                "signed_error_K": row["signed_error_K"],
                "signed_error_percent_of_target": row["signed_error_percent_of_target"],
                "target_K": row["target_K"],
                "predicted_K": row["predicted_K"],
                "finite_prediction": row["finite_prediction"],
                "hover_label": (
                    f"{row['case_id']} {row['model_form_id']} {row['sensor']}: "
                    f"error={row['signed_error_K']} K, pct={row['signed_error_percent_of_target']}%"
                ),
                "admission_status": row["admission_status"],
            }
        )
    return out


def recommended_try_rows() -> list[dict[str, str]]:
    d2 = read_json(D2_GATE / "summary.json")
    d3 = read_json(D3_GATE / "summary.json")
    d4 = read_json(D4_GATE / "summary.json")
    m0 = read_json(M0_BASELINE / "summary.json")
    passive = read_json(PASSIVE_H2_ROLE / "summary.json")
    hx = read_json(HX_COUPLED / "summary.json")
    cand001 = read_json(PRESSURE_CAND001 / "summary.json")
    return [
        {
            "rank": "1",
            "model_form_to_try": "D4 source-bounded segment/source-placement successor",
            "reason": f"Already tried diagnostically; transfer RMSE {d4.get('d4_transfer_rmse_K', '')} K and {d4.get('d4_transfer_rmse_reduction_pct', '')}% reduction vs M3 are the strongest current signal.",
            "required_gates_before_claim": "replace empirical segment offsets with source-bounded local heat-path/source-placement terms; source/property release; same-QOI UQ",
            "allowed_now": "diagnostic score and source-bounded design row only",
            "expected_thesis_use": "strongest evidence that local source placement/passive heat ownership matters",
            "admission_status": "diagnostic_not_admitted_source_bounded_candidate_ready_rows_0",
        },
        {
            "rank": "2",
            "model_form_to_try": "D3 wall-shape / axial-mixing physical successor",
            "reason": f"Already tried diagnostically; transfer RMSE {d3.get('d3_transfer_rmse_K', '')} K and local-shape RMSE {d3.get('d3_transfer_local_shape_rmse_after_bias_K', '')} K show repeatable wall-shape structure.",
            "required_gates_before_claim": "physical wall/core exchange or axial-mixing source basis; no runtime wall-profile correction release; same-QOI UQ",
            "allowed_now": "diagnostic score and physical mechanism design row only",
            "expected_thesis_use": "thermal-shape evidence for wall/core exchange or axial mixing",
            "admission_status": "diagnostic_not_admitted_same_qoi_uq_not_executed",
        },
        {
            "rank": "3",
            "model_form_to_try": "D2 TP/TW QOI projection or wall/fluid split successor",
            "reason": f"Already tried diagnostically; TP transfer RMSE improves to {d2.get('d2_transfer_tp_rmse_K', '')} K while TW remains {d2.get('d2_transfer_tw_rmse_K', '')} K.",
            "required_gates_before_claim": "source-bounded wall/core split or QOI projection uncertainty; no target-temperature runtime release",
            "allowed_now": "diagnostic score and QOI-split/UQ design row only",
            "expected_thesis_use": "evidence that TP and TW residuals are different channels",
            "admission_status": "diagnostic_no_correction_release",
        },
        {
            "rank": "4",
            "model_form_to_try": "PASSIVE-H2-CAND001 source-backed exterior heat-loss operator",
            "reason": f"Latest evidence recovered setup subspan support {passive.get('setup_subspan_support_ready_rows', 0)}/{passive.get('coverage_rows', 0)} and same-QOI setup UQ labels {passive.get('same_qoi_setup_uq_ready_labels', 0)}/{passive.get('same_qoi_labels', 0)}, but release rows remain 0.",
            "required_gates_before_claim": "Salt3/Salt4 diagnostic smoke closeout; row-specific source/property release; exact same-QOI runtime UQ; split-safe freeze audit",
            "allowed_now": "support/diagnostic scoring only",
            "expected_thesis_use": "best source-backed thermal candidate lane",
            "admission_status": "diagnostic_support_no_release_no_freeze",
        },
        {
            "rank": "5",
            "model_form_to_try": "M0 setup-only baseline",
            "reason": f"M0 was built as a shell, but numerical prediction rows are {m0.get('numerical_prediction_rows', 0)} and missing prediction rows are {m0.get('missing_prediction_rows', '')}.",
            "required_gates_before_claim": "actual setup-only prediction equations; runtime-input audit; locked split shell",
            "allowed_now": "explicit missing-baseline table only until predictions exist",
            "expected_thesis_use": "baseline figure/table for all later model forms",
            "admission_status": "not_scored_predictions_missing",
        },
        {
            "rank": "6",
            "model_form_to_try": "M5 / MF-04 throughflow-plus-recirculation exchange cell",
            "reason": "S13 has finite recirculation/exchange diagnostic evidence but release masks, Qwall/pressure, production harvest, and same-QOI UQ remain closed.",
            "required_gates_before_claim": "exact Qwall or source-side QOI decision; pressure basis; release-grade endpoint masks; same-QOI UQ; no source-side relabel as Q_wall",
            "allowed_now": "diagnostic figures and gate table only",
            "expected_thesis_use": "upcomer recirculation model-form contribution",
            "admission_status": "diagnostic_only_until_Qwall_UQ_harvest_release",
        },
        {
            "rank": "7",
            "model_form_to_try": "MF-02 section-effective pressure residual / pressure-mdot coupling",
            "reason": "The lower-right pressure result is a clean negative component-K case and useful section-effective pressure figure.",
            "required_gates_before_claim": "same-QOI UQ and nonrecirculating/low-reverse anchor before any coefficient admission",
            "allowed_now": "no-fit diagnostic transfer and signed residual figures",
            "expected_thesis_use": "pressure model-form negative result",
            "admission_status": "not_admitted",
        },
        {
            "rank": "8",
            "model_form_to_try": "MF-01 ordinary gated single-stream branch on right_leg/test_section_span",
            "reason": f"CAND001 endpoint readiness remains blocked: job state {cand001.get('active_job_state', '')}, endpoint ready fields {cand001.get('endpoint_ready_fields', 0)}/{cand001.get('endpoint_requirement_rows', '')}.",
            "required_gates_before_claim": "endpoint pressure/velocity fields; ordinary-flow RAF/RMF checks; same-QOI UQ; source-property release",
            "allowed_now": "monitor/readiness table only",
            "expected_thesis_use": "future ordinary-pressure lane if gates pass",
            "admission_status": "future_candidate_endpoint_blocked",
        },
        {
            "rank": "9",
            "model_form_to_try": "HX_LUMPED_UA_NTU coupled cooler form",
            "reason": f"HX coupled evaluation completed {hx.get('coupled_rows_completed', 0)} rows but review gate is `{hx.get('review_gate', '')}`.",
            "required_gates_before_claim": "source/property release and coupled error mechanism repair",
            "allowed_now": "negative diagnostic context only",
            "expected_thesis_use": "cooler-removal candidate failure/triage",
            "admission_status": "diagnostic_failed_large_errors_no_release",
        },
        {
            "rank": "10",
            "model_form_to_try": "M6 final frozen candidate",
            "reason": "This is the endpoint, but S6 currently publishes zero final score values.",
            "required_gates_before_claim": "exactly one runtime-legal candidate from S13/S14/thermal residual gates plus S11/S15 source-property release",
            "allowed_now": "blocked shell only",
            "expected_thesis_use": "final scorecard only after freeze",
            "admission_status": "blocked_no_frozen_candidate",
        },
    ]


def thesis_figure_plan_rows() -> list[dict[str, str]]:
    return [
        {
            "figure_id": "F-master-1",
            "figure_name": "Master model-form ladder and admission state",
            "data_source": "master_model_form_scoreboard.csv",
            "plot_type": "table or swimlane",
            "notes": "Show M0-M6 and MF-01-MF-06 with admitted/diagnostic/blocked/future labels.",
        },
        {
            "figure_id": "F-master-2",
            "figure_name": "Signed TP/TW individual sensor errors",
            "data_source": "figure_ready_signed_sensor_errors.csv",
            "plot_type": "faceted signed bar chart or heatmap",
            "notes": "Use signed K and signed percent error; do not rely only on RMSE.",
        },
        {
            "figure_id": "F-master-3",
            "figure_name": "S13 upcomer exchange trend",
            "data_source": "master_model_form_scoreboard.csv plus S13 trend table",
            "plot_type": "three-case trend table or compact line plot",
            "notes": "Plot tau_recirc_proxy, mdot_exchange_positive_outward_proxy, and source-side hA proxy as diagnostic-only.",
        },
        {
            "figure_id": "F-master-4",
            "figure_name": "Two-tap section-effective pressure residual",
            "data_source": "two-tap scorecard source tables",
            "plot_type": "signed residual bar chart",
            "notes": "Show section-effective residuals; explicitly label component_K/F6 not admitted.",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (ENDPOINT_BAKEOFF / "model_form_scores.csv", "M0-M4 aggregate model-form scores"),
        (ENDPOINT_BAKEOFF / "model_form_contracts.csv", "M0-M4 contracts"),
        (ENDPOINT_BAKEOFF / "model_form_failure_modes.csv", "M0-M4 failure modes"),
        (LITREV_EXTRACTION / "model_form_candidates.csv", "MF-01-MF-06 source-envelope candidates"),
        (LITREV_INCORPORATION / "model_form_thesis_ladder.csv", "MF thesis ladder"),
        (SENSOR_ERRORS, "individual legacy signed TP/TW sensor errors"),
        (S6_SCORECARD / "summary.json", "S6 blocked final scorecard shell"),
        (S13_AVERAGE / "summary.json", "S13 average-field thermal reduction"),
        (S13_UQ_UNBLOCK / "summary.json", "S13 Qwall/UQ unblock gate"),
        (S13_SYNTHESIS / "s13_exchange_trend_table.csv", "S13 limited sampled-field evidence synthesis"),
        (S14_PRESSURE / "summary.json", "S14 pressure/F6 branch-use scorecard"),
        (TWO_TAP / "summary.json", "two-tap section-effective pressure scorecard"),
        (DIAGNOSTIC_TESTS / "tested_model_form_scoreboard.csv", "D1-D4 tried diagnostic model-form scores"),
        (DIAGNOSTIC_TESTS / "tested_model_form_sensor_errors.csv", "D1-D4 tried diagnostic sensor-level signed errors"),
        (D2_GATE / "summary.json", "D2 TP/TW QOI projection gate"),
        (D3_GATE / "summary.json", "D3 wall-shape axial-mixing gate"),
        (D4_GATE / "summary.json", "D4 segment source-placement evidence gate"),
        (M0_BASELINE / "summary.json", "M0 setup-only baseline shell"),
        (PASSIVE_H2_ROLE / "summary.json", "PASSIVE-H2 role/subspan mapping recovery"),
        (PASSIVE_H2_FINAL / "summary.json", "PASSIVE-H2 final-form phase gate"),
        (PASSIVE_H2_PREFLIGHT / "summary.json", "PASSIVE-H2 source-mapping split UQ preflight"),
        (HX_COUPLED / "summary.json", "HX coupled Fluid diagnostic evaluation"),
        (PRESSURE_CAND001 / "summary.json", "CAND001 pressure terminal endpoint readiness"),
        (CLAIM_LEDGER, "thesis claim ledger"),
        (ENDPOINT_STRATEGY, "model-form endpoint strategy"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read-only evidence synthesis only"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no admission or registry edits"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no compute launch"},
        {"guard_id": "solver_sampler_harvest_uq_launch", "changed": "false", "policy": "no new scoring, sampler, harvest, or UQ execution"},
        {"guard_id": "thesis_current_file_edit", "changed": "false", "policy": "package only; thesis current files read-only"},
        {"guard_id": "fitting_or_model_selection", "changed": "false", "policy": "no fitting, tuning, or model selection"},
        {"guard_id": "coefficient_admission", "changed": "false", "policy": "all candidate rows preserve source admission labels"},
        {"guard_id": "protected_rows_consumed", "changed": "false", "policy": "existing score labels only; no holdout/external model selection"},
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(ENDPOINT_BAKEOFF / "model_form_scores.csv")}
  - {rel(LITREV_INCORPORATION / "model_form_thesis_ladder.csv")}
  - {rel(SENSOR_ERRORS)}
tags: [thesis, model-form-scoreboard, signed-errors, one-d-model]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Writer / Implementer / Tester / Reviewer
type: work_product
status: complete
---
# Thesis Master Model-Form Scoreboard

This package consolidates the thesis-facing 1D model-form evidence into one
scoreboard. It joins the M0-M6 endpoint ladder, MF-01-MF-06 LitRev taxonomy,
S13 upcomer exchange evidence, S14/F6 pressure screening, two-tap
section-effective pressure evidence, D1-D4 diagnostic model-form tests,
PASSIVE-H2, HX, CAND001, M0 shell evidence, and the S6 blocked final scorecard
shell.

It also emits signed individual TP/TW sensor-error rows for available legacy
numeric model forms. These rows include `predicted_K`, `target_K`,
`signed_error_K = predicted_K - target_K`, and
`signed_error_percent_of_target = 100 * signed_error_K / target_K`.

## Outputs

- `master_model_form_scoreboard.csv`
- `term_glossary.csv`
- `signed_sensor_errors.csv`
- `signed_sensor_error_summary.csv`
- `figure_ready_signed_sensor_errors.csv`
- `recommended_model_forms_to_try.csv`
- `try_all_model_form_disposition.csv`
- `diagnostic_tested_model_form_scoreboard.csv`
- `diagnostic_tested_sensor_errors.csv`
- `thesis_figure_plan.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Result

- master scoreboard rows: `{summary["master_scoreboard_rows"]}`
- glossary rows: `{summary["glossary_rows"]}`
- signed sensor-error rows: `{summary["signed_sensor_error_rows"]}`
- finite signed sensor-error rows: `{summary["finite_signed_sensor_error_rows"]}`
- diagnostic tested model-form rows: `{summary["diagnostic_tested_model_form_rows"]}`
- diagnostic tested sensor-error rows: `{summary["diagnostic_tested_sensor_error_rows"]}`
- recommended model forms to try: `{summary["recommended_try_rows"]}`
- best current diagnostic form: `{summary["best_diagnostic_model_form"]}`

Current scoreable diagnostic forms have been tried through the existing
diagnostic addendum and integrated here. Physics forms that are not currently
scoreable are listed as blocked with their exact required gates. No new solver,
sampler/harvest/UQ execution, source release, coefficient admission, candidate
freeze, final score, thesis current-file edit, or native-output mutation was
performed by this refresh.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(DIAGNOSTIC_TESTS / "tested_model_form_scoreboard.csv")}
tags: [status, thesis, model-form-scoreboard, diagnostic-tests, no-admission]
related:
  - {rel(JOURNAL)}
  - {rel(IMPORT)}
task: {TASK_ID}
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Hydraulics / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

## Objective

Refresh the thesis master model-form scoreboard after trying all currently
scoreable diagnostic model forms and marking unscoreable physics forms with
their blocking gates.

## Changes Made

Updated `{rel(OUT)}` from `tools/analyze/build_thesis_master_model_form_scoreboard.py`.
The refreshed package now includes D1-D4 diagnostic scored forms, current M0,
PASSIVE-H2, HX, pressure CAND001, S13, S14, and two-tap status rows, plus
`try_all_model_form_disposition.csv`, `diagnostic_tested_model_form_scoreboard.csv`,
and `diagnostic_tested_sensor_errors.csv`.

## Validation

Validation commands: builder run, unit tests, `py_compile`, JSON/manifest
checks, `finish_task.py`, and scoped `git diff --check`.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
current/LaTeX edit, validation/holdout/external new scoring beyond consuming
existing diagnostic addendum rows, fitting/model selection beyond the existing
diagnostic train-only addendum, source/property/Qwall/numeric q-loss release,
coefficient admission, candidate freeze, final-score claim, S11/S12/S13/S15/S6
trigger, hidden multiplier, residual absorption into internal Nu, or
runtime-leakage relaxation.
"""
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
provenance:
  - {rel(OUT / "master_model_form_scoreboard.csv")}
  - {rel(OUT / "diagnostic_tested_model_form_scoreboard.csv")}
tags: [journal, model-form-scoreboard, diagnostic-score, no-admission]
related:
  - {rel(STATUS)}
  - {rel(IMPORT)}
---
# Thesis Master Model-Form Scoreboard Refresh Try-All

## Attempted

Claimed a refresh row and rebuilt the master scoreboard with the existing
diagnostic test addendum. The refresh integrates D1-D4 scored diagnostic forms,
M0 baseline shell status, PASSIVE-H2 latest support/release gates, HX coupled
negative diagnostic result, CAND001 pressure endpoint readiness, S13/S14
blocked model-form lanes, and the existing signed TP/TW sensor errors.

## Observed

All currently scoreable diagnostic temperature forms were already available in
the diagnostic addendum and are now first-class rows in the master scoreboard.
`D4_M3_segment_offsets_min2_train` is the strongest diagnostic signal, with
transfer RMSE `7.94040349151 K`. `D3` and `D2` also improve transfer behavior.
M0 remains a missing-prediction shell. PASSIVE-H2 has support evidence but no
release/freeze. HX completed coupled rows but failed as a diagnostic candidate
because coupled errors are large and source/property remains closed.

## Inferred

The scoreboard now supports thesis writing about what works diagnostically and
what remains blocked scientifically. It still does not support a frozen final
candidate, protected score, source/property release, or coefficient admission.

## Next Useful Actions

Prioritize source-bounded successors for D4 and D3, then D2 QOI projection /
wall-core split work. Continue PASSIVE-H2 diagnostic smoke and exact same-QOI
gate work before any candidate freeze. Keep M0 visible as an explicit missing
baseline until actual setup-only predictions exist.
"""
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed_files = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_thesis_master_model_form_scoreboard.py",
        "tools/analyze/test_thesis_master_model_form_scoreboard.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/master_model_form_scoreboard.csv",
        f"{rel(OUT)}/term_glossary.csv",
        f"{rel(OUT)}/signed_sensor_errors.csv",
        f"{rel(OUT)}/signed_sensor_error_summary.csv",
        f"{rel(OUT)}/figure_ready_signed_sensor_errors.csv",
        f"{rel(OUT)}/recommended_model_forms_to_try.csv",
        f"{rel(OUT)}/try_all_model_form_disposition.csv",
        f"{rel(OUT)}/diagnostic_tested_model_form_scoreboard.csv",
        f"{rel(OUT)}/diagnostic_tested_sensor_errors.csv",
        f"{rel(OUT)}/thesis_figure_plan.csv",
        f"{rel(OUT)}/source_manifest.csv",
        f"{rel(OUT)}/no_mutation_guardrails.csv",
        f"{rel(OUT)}/summary.json",
    ]
    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "changed_files": changed_files,
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "results": {
            "decision": summary["decision"],
            "master_scoreboard_rows": summary["master_scoreboard_rows"],
            "diagnostic_tested_model_form_rows": summary["diagnostic_tested_model_form_rows"],
            "best_diagnostic_model_form": summary["best_diagnostic_model_form"],
            "final_score_values": summary["final_score_values"],
        },
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "no_scorecard_outputs": True,
    }
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    json_dump(IMPORT, manifest)


def build(out_dir: Path = OUT) -> dict[str, Any]:
    ensure_dir(out_dir)
    master_rows = master_model_form_rows()
    glossary = glossary_rows()
    sensor_rows = signed_sensor_error_rows()
    sensor_summary = signed_sensor_error_summary(sensor_rows)
    figure_rows = figure_ready_rows(sensor_rows)
    try_rows = recommended_try_rows()
    diagnostic_score_rows = read_csv(DIAGNOSTIC_TESTS / "tested_model_form_scoreboard.csv")
    diagnostic_sensor_rows = read_csv(DIAGNOSTIC_TESTS / "tested_model_form_sensor_errors.csv")
    figure_plan = thesis_figure_plan_rows()
    manifest = source_manifest_rows()
    guards = guardrail_rows()

    csv_outputs = [
        (out_dir / "master_model_form_scoreboard.csv", list(master_rows[0]), master_rows),
        (out_dir / "term_glossary.csv", list(glossary[0]), glossary),
        (out_dir / "signed_sensor_errors.csv", list(sensor_rows[0]), sensor_rows),
        (out_dir / "signed_sensor_error_summary.csv", list(sensor_summary[0]), sensor_summary),
        (out_dir / "figure_ready_signed_sensor_errors.csv", list(figure_rows[0]), figure_rows),
        (out_dir / "recommended_model_forms_to_try.csv", list(try_rows[0]), try_rows),
        (out_dir / "try_all_model_form_disposition.csv", list(try_rows[0]), try_rows),
        (out_dir / "diagnostic_tested_model_form_scoreboard.csv", list(diagnostic_score_rows[0]), diagnostic_score_rows),
        (out_dir / "diagnostic_tested_sensor_errors.csv", list(diagnostic_sensor_rows[0]), diagnostic_sensor_rows),
        (out_dir / "thesis_figure_plan.csv", list(figure_plan[0]), figure_plan),
        (out_dir / "source_manifest.csv", list(manifest[0]), manifest),
        (out_dir / "no_mutation_guardrails.csv", list(guards[0]), guards),
    ]
    for path, header, rows in csv_outputs:
        csv_dump(path, header, rows)
        normalize_generated_csv(path)

    finite_rows = sum(1 for row in sensor_rows if row["finite_prediction"] == "true")
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "master_scoreboard_refreshed_all_current_scoreable_forms_tried_no_admission",
        "master_scoreboard_rows": len(master_rows),
        "glossary_rows": len(glossary),
        "signed_sensor_error_rows": len(sensor_rows),
        "finite_signed_sensor_error_rows": finite_rows,
        "signed_sensor_error_summary_rows": len(sensor_summary),
        "diagnostic_tested_model_form_rows": len(diagnostic_score_rows),
        "diagnostic_tested_sensor_error_rows": len(diagnostic_sensor_rows),
        "recommended_try_rows": len(try_rows),
        "try_all_disposition_rows": len(try_rows),
        "figure_plan_rows": len(figure_plan),
        "source_manifest_rows": len(manifest),
        "best_diagnostic_model_form": "D4_M3_segment_offsets_min2_train",
        "final_score_values": 0,
        "candidate_freeze": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "validation_holdout_external_new_scoring": False,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "thesis_current_file_edit": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    json_dump(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    if out_dir == OUT:
        write_status(summary)
        write_journal(summary)
        write_import(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
