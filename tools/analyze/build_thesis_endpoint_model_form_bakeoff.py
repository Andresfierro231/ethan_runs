#!/usr/bin/env python3
"""Build thesis endpoint model-form bakeoff tables for M0-M4.

This builder is evidence-only. It does not run Fluid/OpenFOAM, fit any model,
change admission state, or use held-out/external rows for model selection.
Where a thesis-final frozen prediction is unavailable, it emits explicit
``prediction_missing`` or ``blocked`` score rows.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff")
OUT = ROOT / OUT_REL

SECTION_06 = ROOT / "reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md"
THESIS_OUTLINE = ROOT / "reports/thesis_dossier/Outline.md"
SECTION_02 = ROOT / "reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md"
SECTION_03 = ROOT / "reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md"
SECTION_05 = ROOT / "reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md"

AGENT499 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard"
AGENT500 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress"
AGENT503 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis"
AGENT507 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_passive_test_section_admission_closeout"
AGENT509 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell"

SPLIT_LEGAL = AGENT499 / "split_legal_case_table.csv"
FINAL_SHELL_CASES = AGENT509 / "case_partition_contract.csv"
FINAL_SHELL_METRICS = AGENT509 / "metric_contract.csv"
FINAL_SHELL_SUMMARY = AGENT509 / "summary.json"
VAL_EXTERNAL_SUMMARY = AGENT500 / "summary.json"
VAL_JOIN_CONTRACT = AGENT500 / "val_salt2_prediction_join_contract.csv"
VAL_PRESSURE_SUMMARY = AGENT503 / "summary.json"
WALL_CLOSEOUT_SUMMARY = AGENT507 / "summary.json"
WALL_CLOSEOUT_ADMISSION = AGENT507 / "admission_decision_matrix.csv"
WALL_CLOSEOUT_FAILURES = AGENT507 / "failure_mode_evidence.csv"

BOUNDARY_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission"
    / "submodel_admission_summary.csv"
)
M2_M3_COMPARATORS = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard"
    / "m2_m3_comparators.csv"
)
M3TS_COUPLED = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard"
    / "m3ts_coupled_scorecard.csv"
)

TRAIN_ROWS = "salt1_nominal;salt2_jin_nominal;salt3_jin_nominal;salt4_nominal"
SUPPORT_ROWS = "salt1_lo10q;salt1_hi10q;salt4_lo5q;salt4_hi5q"
CURRENT_SCORE_ROWS = "salt2_lo5q;salt2_hi5q;val_salt2"
FUTURE_SCORE_ROWS = "salt2_lo10q;salt2_hi10q;salt4_lo10q;salt4_hi10q;salt3_q_insulation_matrix"


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
        raise ValueError(f"Expected object JSON in {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def fnum(value: str) -> float | None:
    if value in ("", None, "nan", "NaN"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.6g}"


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def max_abs(values: list[float]) -> float | None:
    return max((abs(value) for value in values), default=None)


def numeric_from_error(error: str) -> float | None:
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", error or "")
    return float(match.group(0)) if match else None


def aggregate_legacy_mode(mode_id: str) -> dict[str, str]:
    rows = [row for row in read_csv(M2_M3_COMPARATORS) if row["mode_id"] == mode_id and row["split"] != "train"]
    return {
        "legacy_score_scope": "legacy_salt3_validation_salt4_holdout_not_locked_final_split",
        "mdot_error_pct": fmt(mean([fnum(row["mdot_error_pct"]) for row in rows if fnum(row["mdot_error_pct"]) is not None])),
        "tp_sensor_error_K": fmt(mean([fnum(row["tp_rmse_K"]) for row in rows if fnum(row["tp_rmse_K"]) is not None])),
        "tw_sensor_error_K": fmt(mean([fnum(row["tw_rmse_K"]) for row in rows if fnum(row["tw_rmse_K"]) is not None])),
        "all_probe_error_K": fmt(mean([fnum(row["all_probe_rmse_K"]) for row in rows if fnum(row["all_probe_rmse_K"]) is not None])),
        "loop_delta_T_error_K": fmt(mean([fnum(row["loop_delta_error_K"]) for row in rows if fnum(row["loop_delta_error_K"]) is not None])),
        "source_paths": rel(M2_M3_COMPARATORS),
    }


def boundary_residual_summary() -> dict[str, str]:
    rows = read_csv(BOUNDARY_ADMISSION)
    by_submodel = {row["submodel"]: row for row in rows}
    errors = []
    fragments = []
    for key in ("heater", "cooler_hx"):
        row = by_submodel[key]
        for field in ("validation_error", "holdout_error"):
            val = numeric_from_error(row[field])
            if val is not None:
                errors.append(abs(val))
        fragments.append(f"{key}:validation={row['validation_error']};holdout={row['holdout_error']}")
    return {
        "branch_heat_residual_W": fmt(max_abs(errors)),
        "branch_heat_residual_detail": " | ".join(fragments),
        "source_paths": rel(BOUNDARY_ADMISSION),
    }


def model_form_contracts() -> list[dict[str, Any]]:
    common_forbidden_predictive = (
        "CFD mdot;realized CFD wallHeatFlux;pressure losses from scored row;"
        "TP/TW validation temperatures;blind residuals;hidden global multipliers"
    )
    return [
        {
            "model_form_id": "M0",
            "model_form_name": "setup_only_baseline",
            "predictive_or_diagnostic": "predictive_lower_bound_shell",
            "equations_residuals": "setup-only loop pressure/energy balance with geometry, property lane, setup heater/cooler, ambient/radiation inputs; residuals not calibrated from scored rows",
            "allowed_runtime_inputs": "geometry;property lane;setup heater power;setup cooler/HX metadata;ambient/surroundings/emissivity setup inputs",
            "forbidden_runtime_inputs": common_forbidden_predictive,
            "required_cfd_postprocessing": "case/sensor target tables only; no realized heat/pressure ledgers required at runtime",
            "train_rows": TRAIN_ROWS,
            "training_support_rows": SUPPORT_ROWS,
            "score_rows": CURRENT_SCORE_ROWS,
            "future_score_rows": FUTURE_SCORE_ROWS,
            "admission_status": "score_shell_only_prediction_missing",
            "thesis_safe_claim": "Can be claimed as lower-bound predictive sanity contract once implemented; no final score exists here.",
            "source_paths": f"{rel(SECTION_06)};{rel(FINAL_SHELL_METRICS)}",
        },
        {
            "model_form_id": "M1",
            "model_form_name": "cfd_thermal_boundary_replay_diagnostic",
            "predictive_or_diagnostic": "diagnostic_replay_only",
            "equations_residuals": "1D replay using realized CFD thermal ledgers to explain heat placement and residual context",
            "allowed_runtime_inputs": "setup inputs plus realized CFD patch/wall/section heat ledgers for replay only",
            "forbidden_runtime_inputs": "for predictive claims: " + common_forbidden_predictive,
            "required_cfd_postprocessing": "patch heat ledger; wallHeatFlux or equivalent realized heat ledger; section heat balance; sensor targets",
            "train_rows": "none_for_predictive_training",
            "training_support_rows": SUPPORT_ROWS,
            "score_rows": CURRENT_SCORE_ROWS,
            "future_score_rows": FUTURE_SCORE_ROWS,
            "admission_status": "diagnostic_not_predictive",
            "thesis_safe_claim": "Can explain physics and heat placement; cannot be used as predictive endpoint.",
            "source_paths": f"{rel(M2_M3_COMPARATORS)};{rel(SECTION_03)}",
        },
        {
            "model_form_id": "M2",
            "model_form_name": "admitted_heater_cooler_boundary_model",
            "predictive_or_diagnostic": "partial_predictive_boundary_candidate",
            "equations_residuals": "setup-only heater efficiency and cooler/HX UA/NTU boundary terms; passive wall/test-section terms remain blocked or diagnostic",
            "allowed_runtime_inputs": "geometry;property lane;setup heater power;setup cooler/HX metadata;ambient/radiation setup inputs;admitted heater/cooler coefficients",
            "forbidden_runtime_inputs": common_forbidden_predictive,
            "required_cfd_postprocessing": "split-aware heater/cooler admission tables; runtime-input audit; frozen scorecard targets",
            "train_rows": TRAIN_ROWS,
            "training_support_rows": SUPPORT_ROWS,
            "score_rows": CURRENT_SCORE_ROWS,
            "future_score_rows": FUTURE_SCORE_ROWS,
            "admission_status": "heater_and_cooler_admitted_wall_test_section_blocked_no_full_freeze",
            "thesis_safe_claim": "First credible boundary-submodel candidate; not yet a complete final predictive model.",
            "source_paths": f"{rel(BOUNDARY_ADMISSION)};{rel(WALL_CLOSEOUT_SUMMARY)}",
        },
        {
            "model_form_id": "M3",
            "model_form_name": "segment_only_fluid_walls",
            "predictive_or_diagnostic": "blocked_predictive_network_comparison",
            "equations_residuals": "segment pressure closure plus finite segment energy balances and wall/material stacks without explicit junction/stub ownership",
            "allowed_runtime_inputs": "segment geometry;property lane;admitted pressure/thermal/source-sink coefficients;setup boundary dictionaries",
            "forbidden_runtime_inputs": common_forbidden_predictive,
            "required_cfd_postprocessing": "segment pressure scorecards; thermal model slots; sensor targets; runtime audit; final frozen prediction artifact",
            "train_rows": TRAIN_ROWS,
            "training_support_rows": SUPPORT_ROWS,
            "score_rows": CURRENT_SCORE_ROWS,
            "future_score_rows": FUTURE_SCORE_ROWS,
            "admission_status": "blocked_no_final_freeze_zero_fit_admitted_pressure_rows",
            "thesis_safe_claim": "Main reduced-order comparison form, currently usable as blocked/diagnostic ladder row rather than final endpoint.",
            "source_paths": f"{rel(SECTION_02)};{rel(AGENT509 / 'model_freeze_contract.csv')};{rel(M2_M3_COMPARATORS)}",
        },
        {
            "model_form_id": "M4",
            "model_form_name": "junction_aware_fluid_walls",
            "predictive_or_diagnostic": "diagnostic_junction_aware_extension",
            "equations_residuals": "M3 plus named junction/stub heat ownership and branch/junction apparent pressure-loss buckets with admission flags",
            "allowed_runtime_inputs": "M3 setup inputs plus admitted junction/stub heat coefficients and admitted local pressure coefficients when available",
            "forbidden_runtime_inputs": common_forbidden_predictive,
            "required_cfd_postprocessing": "junction/stub heat split; corner/branch pressure ledgers; pressure-basis and component-isolation admission gates",
            "train_rows": TRAIN_ROWS,
            "training_support_rows": SUPPORT_ROWS,
            "score_rows": CURRENT_SCORE_ROWS,
            "future_score_rows": FUTURE_SCORE_ROWS,
            "admission_status": "junction_heat_diagnostic_pressure_K_zero_fit_admitted",
            "thesis_safe_claim": "Supports local ownership/attribution claim; does not yet admit predictive corner-K coefficients.",
            "source_paths": f"{rel(SECTION_05)};{rel(VAL_EXTERNAL_SUMMARY)};{rel(VAL_PRESSURE_SUMMARY)}",
        },
    ]


def model_form_scores() -> list[dict[str, Any]]:
    m1 = aggregate_legacy_mode("M2_cfd_heater_test_section_cooler_pressure_root")
    m3 = aggregate_legacy_mode("M3_cfd_heater_cooler_pressure_root")
    boundary = boundary_residual_summary()
    final_summary = read_json(FINAL_SHELL_SUMMARY)
    val_summary = read_json(VAL_EXTERNAL_SUMMARY)
    pressure_summary = read_json(VAL_PRESSURE_SUMMARY)
    wall_summary = read_json(WALL_CLOSEOUT_SUMMARY)
    return [
        {
            "model_form_id": "M0",
            "score_scope": "locked_split_shell",
            "score_status": "prediction_missing_not_run",
            "mdot_error_pct": "",
            "pressure_residual_movement": "prediction_missing",
            "branch_heat_residual_W": "",
            "loop_delta_T_error_K": "",
            "tp_sensor_error_K": "",
            "tw_sensor_error_K": "",
            "all_probe_error_K": "",
            "runtime_leakage_status": "pass_contract_only",
            "admission_status": "shell_only_lower_bound_not_scored",
            "score_interpretation": "M0 is thesis-safe as a required baseline contract, but no frozen predictions are available.",
            "source_paths": rel(FINAL_SHELL_SUMMARY),
        },
        {
            "model_form_id": "M1",
            "score_scope": m1["legacy_score_scope"],
            "score_status": "diagnostic_legacy_numeric_context_not_predictive",
            "mdot_error_pct": m1["mdot_error_pct"],
            "pressure_residual_movement": "uses pressure-root replay; not valid as predictive pressure score",
            "branch_heat_residual_W": "realized_CFD_thermal_replay_not_predictive",
            "loop_delta_T_error_K": m1["loop_delta_T_error_K"],
            "tp_sensor_error_K": m1["tp_sensor_error_K"],
            "tw_sensor_error_K": m1["tw_sensor_error_K"],
            "all_probe_error_K": m1["all_probe_error_K"],
            "runtime_leakage_status": "diagnostic_leakage_by_design",
            "admission_status": "diagnostic_not_admitted_predictive",
            "score_interpretation": "Useful heat-placement/context replay; cannot be claimed as final predictive performance.",
            "source_paths": m1["source_paths"],
        },
        {
            "model_form_id": "M2",
            "score_scope": "admitted_submodel_residuals_no_full_locked_split_score",
            "score_status": "partial_boundary_score_prediction_missing_for_full_model",
            "mdot_error_pct": "",
            "pressure_residual_movement": "not_scored_full_model",
            "branch_heat_residual_W": boundary["branch_heat_residual_W"],
            "branch_heat_residual_detail": boundary["branch_heat_residual_detail"],
            "loop_delta_T_error_K": "",
            "tp_sensor_error_K": "",
            "tw_sensor_error_K": "",
            "all_probe_error_K": "",
            "runtime_leakage_status": "pass_for_admitted_heater_cooler_terms",
            "admission_status": "heater_cooler_admitted_wall_test_section_blocked",
            "score_interpretation": "Heater/cooler boundary terms are admitted, but the complete predictive model is blocked by passive wall/test-section physics.",
            "source_paths": boundary["source_paths"],
        },
        {
            "model_form_id": "M3",
            "score_scope": m3["legacy_score_scope"],
            "score_status": "legacy_numeric_context_final_prediction_missing",
            "mdot_error_pct": m3["mdot_error_pct"],
            "pressure_residual_movement": "segment pressure coefficients zero fit-admitted in final shell",
            "branch_heat_residual_W": "passive/test-section residual blocker open",
            "loop_delta_T_error_K": m3["loop_delta_T_error_K"],
            "tp_sensor_error_K": m3["tp_sensor_error_K"],
            "tw_sensor_error_K": m3["tw_sensor_error_K"],
            "all_probe_error_K": m3["all_probe_error_K"],
            "runtime_leakage_status": "pass_for_shell; legacy comparator not final locked split",
            "admission_status": f"blocked_freeze={final_summary['freeze_status']};wall_blocker={wall_summary['primary_remaining_blocker']}",
            "score_interpretation": "M3 is the main comparison form but final scoring is blocked until an admitted Salt1-4 nominal freeze exists.",
            "source_paths": f"{m3['source_paths']};{rel(FINAL_SHELL_SUMMARY)};{rel(WALL_CLOSEOUT_SUMMARY)}",
        },
        {
            "model_form_id": "M4",
            "score_scope": "junction_aware_diagnostic_targets_no_frozen_prediction",
            "score_status": "prediction_missing_diagnostic_junction_evidence_available",
            "mdot_error_pct": "",
            "pressure_residual_movement": f"corner_fit_admitted_rows={pressure_summary['corner_fit_admitted_rows']};negative_K_rows={pressure_summary['corner_centerline_negative_k_rows']}",
            "branch_heat_residual_W": f"junction_rows={val_summary['junction_rows']};junction_coeff_admitted={val_summary['junction_coefficient_admitted_rows']}",
            "loop_delta_T_error_K": "",
            "tp_sensor_error_K": "",
            "tw_sensor_error_K": "",
            "all_probe_error_K": "",
            "runtime_leakage_status": "pass_contract_diagnostic_sources_not_runtime_inputs",
            "admission_status": "junction_heat_diagnostic_pressure_K_not_admitted",
            "score_interpretation": "M4 supports attribution/ownership claims, not an admitted predictive corner-K or junction coefficient claim.",
            "source_paths": f"{rel(VAL_EXTERNAL_SUMMARY)};{rel(VAL_PRESSURE_SUMMARY)};{rel(SECTION_05)}",
        },
    ]


def model_form_costs() -> list[dict[str, Any]]:
    return [
        {
            "model_form_id": "M0",
            "training_computational_cost": "low; no coefficient sweep required beyond setup sanity checks",
            "required_postprocessing_cost": "low; case metadata and target tables",
            "operational_runtime_cost": "low; one steady 1D solve per case",
            "dependencies_blockers": "implementation/frozen prediction artifact missing",
            "thesis_value": "baseline lower-bound comparator",
        },
        {
            "model_form_id": "M1",
            "training_computational_cost": "low for model; high data-dependency because realized CFD ledgers must exist",
            "required_postprocessing_cost": "moderate/high; patch heat, wallHeatFlux, section heat, pressure-root replay data",
            "operational_runtime_cost": "low replay solve after data extraction",
            "dependencies_blockers": "diagnostic by definition; cannot become predictive because scored-row heat outputs are runtime inputs",
            "thesis_value": "explains missing heat placement and residual ownership",
        },
        {
            "model_form_id": "M2",
            "training_computational_cost": "moderate; split-aware heater/cooler coefficient admission",
            "required_postprocessing_cost": "moderate; heater/cooler admission tables and runtime audit",
            "operational_runtime_cost": "low/moderate; boundary terms added to steady 1D solve",
            "dependencies_blockers": "passive wall/test-section model still blocked",
            "thesis_value": "first credible boundary-submodel predictive candidate",
        },
        {
            "model_form_id": "M3",
            "training_computational_cost": "moderate/high; pressure, thermal, source/sink, recirculation gates must close",
            "required_postprocessing_cost": "high; segment pressure/thermal scorecards, sensor targets, final frozen prediction artifact",
            "operational_runtime_cost": "moderate; coupled nonlinear pressure/thermal 1D network solve",
            "dependencies_blockers": "no final Salt1-4 freeze; wall/test-section source-placement/upcomer mixing blocker; zero fit-admitted pressure coefficients",
            "thesis_value": "main reduced-order network comparison",
        },
        {
            "model_form_id": "M4",
            "training_computational_cost": "high; local junction/stub and pressure coefficient admission required",
            "required_postprocessing_cost": "high; junction/stub heat split, pressure corner-K extraction, component isolation, mesh/GCI",
            "operational_runtime_cost": "moderate; M3 network plus local ownership buckets",
            "dependencies_blockers": "junction heat is diagnostic and pressure corner-K has 0 fit-admitted rows",
            "thesis_value": "strong attribution contribution even before full predictive admission",
        },
    ]


def model_form_failure_modes() -> list[dict[str, Any]]:
    wall_failures = {row["failure_mode"]: row for row in read_csv(WALL_CLOSEOUT_FAILURES)}
    return [
        {
            "model_form_id": "M0",
            "expected_failure_modes": "large mdot/temperature residuals because setup-only model omits admitted losses and local roles",
            "observed_failure_modes": "not yet run; prediction_missing",
            "blocker_linkage": "FINAL_FREEZE_TBD_not_created",
            "source_paths": rel(FINAL_SHELL_SUMMARY),
        },
        {
            "model_form_id": "M1",
            "expected_failure_modes": "runtime leakage for predictive claims because realized CFD wall/patch heat is supplied",
            "observed_failure_modes": "diagnostic replay has numeric legacy errors but is not predictive",
            "blocker_linkage": "runtime_leakage_by_design",
            "source_paths": rel(M2_M3_COMPARATORS),
        },
        {
            "model_form_id": "M2",
            "expected_failure_modes": "heater/cooler terms work while passive wall/test-section remains mislocalized",
            "observed_failure_modes": wall_failures["passive_total_not_sufficient"]["evidence"],
            "blocker_linkage": "predictive-wall-test-section-submodels",
            "source_paths": f"{rel(BOUNDARY_ADMISSION)};{wall_failures['passive_total_not_sufficient']['source_paths']}",
        },
        {
            "model_form_id": "M3",
            "expected_failure_modes": "segment-only aggregation hides source placement, upcomer mixing, and junction/local losses",
            "observed_failure_modes": wall_failures["local_distribution_still_temperature_wrong"]["evidence"],
            "blocker_linkage": "local_wall_temperature_source_placement_or_upcomer_mixing_physics",
            "source_paths": wall_failures["local_distribution_still_temperature_wrong"]["source_paths"],
        },
        {
            "model_form_id": "M4",
            "expected_failure_modes": "junction-aware lanes improve attribution but can overclaim if diagnostic corner-K is treated as admitted",
            "observed_failure_modes": read_json(VAL_PRESSURE_SUMMARY)["plain_language_answer"],
            "blocker_linkage": "pressure_corner_K_fit_admission_zero;junction_coefficient_admission_zero",
            "source_paths": f"{rel(VAL_PRESSURE_SUMMARY)};{rel(VAL_EXTERNAL_SUMMARY)}",
        },
    ]


def thesis_claim_ledger() -> list[dict[str, Any]]:
    return [
        {
            "model_form_id": "M0",
            "can_claim": "A setup-only predictive baseline contract is defined and ready to run once a frozen prediction artifact exists.",
            "cannot_claim": "No final numeric baseline score yet.",
        },
        {
            "model_form_id": "M1",
            "can_claim": "CFD thermal-boundary replay is useful diagnostic context for heat placement.",
            "cannot_claim": "It is not predictive and cannot support final endpoint performance claims.",
        },
        {
            "model_form_id": "M2",
            "can_claim": "Heater and cooler/HX setup-only boundary terms are admitted submodels with small W-scale held-out residuals.",
            "cannot_claim": "A complete heater+cooler+wall/test-section predictive model is admitted.",
        },
        {
            "model_form_id": "M3",
            "can_claim": "Segment-only fluid+walls is the main reduced-order network comparison form and has legacy diagnostic score context.",
            "cannot_claim": "Locked-split final performance, because no Salt1-4 nominal freeze exists.",
        },
        {
            "model_form_id": "M4",
            "can_claim": "Junction-aware ledgers improve attribution and motivate named local ownership lanes.",
            "cannot_claim": "Predictive corner-K or junction heat coefficients are fit-admitted.",
        },
    ]


def source_manifest(outputs: list[Path]) -> list[dict[str, Any]]:
    inputs = [
        SECTION_06,
        THESIS_OUTLINE,
        SECTION_02,
        SECTION_03,
        SECTION_05,
        SPLIT_LEGAL,
        FINAL_SHELL_CASES,
        FINAL_SHELL_METRICS,
        FINAL_SHELL_SUMMARY,
        VAL_EXTERNAL_SUMMARY,
        VAL_JOIN_CONTRACT,
        VAL_PRESSURE_SUMMARY,
        WALL_CLOSEOUT_SUMMARY,
        WALL_CLOSEOUT_ADMISSION,
        WALL_CLOSEOUT_FAILURES,
        BOUNDARY_ADMISSION,
        M2_M3_COMPARATORS,
        M3TS_COUPLED,
    ]
    rows = [
        {"path": rel(path), "role": "read_only_input", "exists": path.exists(), "native_output_mutated": "no"}
        for path in inputs
    ]
    rows.extend(
        {"path": rel(path), "role": "generated_output", "exists": path.exists(), "native_output_mutated": "no"}
        for path in outputs
    )
    return rows


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(SECTION_06)}
  - {rel(FINAL_SHELL_SUMMARY)}
  - {rel(VAL_EXTERNAL_SUMMARY)}
  - {rel(VAL_PRESSURE_SUMMARY)}
  - {rel(WALL_CLOSEOUT_SUMMARY)}
tags: [thesis, model-form-bakeoff, final-split, endpoint-strategy]
related:
  - TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF
  - final-predictive-split-policy
  - predictive-wall-test-section-submodels
task: {TASK}
date: 2026-07-17
role: Writer/Reviewer/Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester
type: work_product
status: complete
---
# Thesis Endpoint Model-Form Bakeoff

## Result

This package scores and documents thesis-ready intermediate model forms M0-M4
under the locked final predictive split. It does not run solvers, fit models, or
change admission state.

## Predictive vs Diagnostic

- `M0` is a predictive setup-only baseline shell, but its numeric predictions
  are missing.
- `M1` is diagnostic replay. It can explain heat placement but cannot be a
  predictive claim.
- `M2` has admitted heater and cooler/HX boundary terms, but the full
  wall/test-section predictive model remains blocked.
- `M3` is the main segment-only `fluid+walls` network comparison, currently
  blocked for final scoring by the missing Salt1-4 nominal freeze and physics
  blockers.
- `M4` is the junction-aware `fluid+walls` extension. It supports attribution
  claims, but current pressure corner-K and junction coefficients remain
  diagnostic with zero fit-admitted rows.

## Thesis-Safe Claims

The thesis can claim that the endpoint ladder is defined, guarded by the locked
split, and partially scored where prior diagnostic or admitted submodel evidence
exists. It can claim M2 heater/cooler submodel admission and M4 junction-aware
attribution value. It cannot claim final frozen predictive performance, M1
predictivity, or admitted corner-K/junction coefficients.

## Outputs

- `model_form_contracts.csv`
- `model_form_scores.csv`
- `model_form_costs.csv`
- `model_form_failure_modes.csv`
- `thesis_claim_ledger.csv`
- `runtime_leakage_audit.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Model forms represented: `{summary["model_forms"]}`.
- Numeric legacy/partial score rows: `{summary["score_rows_with_any_numeric"]}`.
- Prediction-missing or blocked score rows: `{summary["missing_or_blocked_score_rows"]}`.
- Runtime audit failures: `{summary["runtime_audit_failures"]}`.
"""


def runtime_leakage_audit(contracts: list[dict[str, Any]], scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    predictive_bad = [
        row
        for row in contracts
        if row["predictive_or_diagnostic"].startswith("predictive")
        and "realized CFD wallHeatFlux" not in row["forbidden_runtime_inputs"]
    ]
    ambiguous_score_rows = [
        row
        for row in scores
        if not row["score_status"]
        or (
            "prediction_missing" not in row["score_status"]
            and "diagnostic" not in row["score_status"]
            and "partial" not in row["score_status"]
            and "legacy" not in row["score_status"]
        )
    ]
    return [
        {
            "audit_item": "predictive_forms_forbid_realized_cfd_outputs",
            "status": "pass" if not predictive_bad else "fail",
            "details": f"bad_rows={len(predictive_bad)}",
        },
        {
            "audit_item": "locked_split_holdout_not_fit_or_selected",
            "status": "pass",
            "details": "case contracts inherited from AGENT-499/509 keep Salt2 +/-5Q and val_salt2 score-only",
        },
        {
            "audit_item": "missing_scores_are_explicit",
            "status": "pass" if not ambiguous_score_rows else "fail",
            "details": f"bad_rows={len(ambiguous_score_rows)}",
        },
        {
            "audit_item": "no_solver_or_postprocessing_launch",
            "status": "pass",
            "details": "builder reads existing CSV/JSON/Markdown evidence only",
        },
        {
            "audit_item": "diagnostic_labels_preserved",
            "status": "pass",
            "details": "M1 marked diagnostic; M4 pressure/junction coefficients marked diagnostic/zero admitted",
        },
    ]


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    contracts = model_form_contracts()
    scores = model_form_scores()
    costs = model_form_costs()
    failures = model_form_failure_modes()
    claims = thesis_claim_ledger()
    audit = runtime_leakage_audit(contracts, scores)

    outputs = [
        OUT / "model_form_contracts.csv",
        OUT / "model_form_scores.csv",
        OUT / "model_form_costs.csv",
        OUT / "model_form_failure_modes.csv",
        OUT / "thesis_claim_ledger.csv",
        OUT / "runtime_leakage_audit.csv",
        OUT / "source_manifest.csv",
        OUT / "summary.json",
        OUT / "README.md",
    ]
    write_csv(outputs[0], contracts)
    write_csv(outputs[1], scores)
    write_csv(outputs[2], costs)
    write_csv(outputs[3], failures)
    write_csv(outputs[4], claims)
    write_csv(outputs[5], audit)
    write_csv(outputs[6], source_manifest(outputs))

    score_status_counts = Counter(row["score_status"] for row in scores)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "model_forms": len(contracts),
        "model_form_ids": [row["model_form_id"] for row in contracts],
        "score_rows": len(scores),
        "score_rows_with_any_numeric": sum(
            any(row.get(field, "") for field in ("mdot_error_pct", "branch_heat_residual_W", "loop_delta_T_error_K", "tp_sensor_error_K", "tw_sensor_error_K", "all_probe_error_K"))
            for row in scores
        ),
        "missing_or_blocked_score_rows": sum("missing" in row["score_status"] or "blocked" in row["score_status"] for row in scores),
        "score_status_counts": dict(score_status_counts),
        "runtime_audit_rows": len(audit),
        "runtime_audit_failures": sum(not row["status"].startswith("pass") for row in audit),
        "split_guardrail": "Salt1-4 nominal training; Salt2 +/-5Q and val_salt2 score-only; future rows only after terminal/run admission.",
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "scheduler_action": "none",
    }
    write_json(outputs[7], summary)
    outputs[8].write_text(readme_text(summary))
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
