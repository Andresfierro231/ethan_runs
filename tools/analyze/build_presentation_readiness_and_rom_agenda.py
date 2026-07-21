#!/usr/bin/env python3
"""Build the July 1 presentation-readiness and ROM agenda package.

The package is a reproducible rollup from existing reports and work products.
It does not run OpenFOAM, mutate solver outputs, or edit older report packages.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump

DEFAULT_REPORT_DIR = ROOT / "reports/2026-07/2026-07-01/2026-07-01_presentation_readiness_and_rom_agenda"
DEFAULT_WORK_DIR = ROOT / "work_products/2026-07-01_presentation_readiness_and_rom_agenda"

BAKEOFF_DIR = ROOT / "reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff"
VALIDATION_DIR = ROOT / "reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation"
PRESSURE_PREDICTIVITY_DIR = ROOT / "reports/2026-06/2026-06-29/2026-06-29_ethan_salt_pressure_drop_predictivity"
CLOSURE_RESULTS_DIR = ROOT / "reports/2026-06/2026-06-30/2026-06-30_claude_closure_results"
CORRECTNESS_DIR = ROOT / "reports/2026-07/2026-07-01/2026-07-01_rom_postprocessing_correctness_validation"
CORRECTNESS_WORK = ROOT / "work_products/2026-07-01_rom_postprocessing_correctness_validation"
MODEL_FORM_DRAFT = ROOT / "reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/README.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK_DIR))
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def as_float(row: dict[str, Any], key: str, default: float | None = None) -> float | None:
    try:
        value = row.get(key, "")
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def find_attempt(replay_rows: list[dict[str, str]], attempt: str) -> dict[str, str]:
    for row in replay_rows:
        if row.get("attempt_name") == attempt:
            return row
    return {}


def find_surface(surface_rows: list[dict[str, str]], label: str) -> dict[str, str]:
    for row in surface_rows:
        if row.get("surface_label") == label:
            return row
    return {}


def figure_inventory() -> list[dict[str, str]]:
    figures = [
        (
            "1d_bakeoff_full_coverage_case_metrics",
            BAKEOFF_DIR / "figures/png/best_full_coverage_case_metrics.png",
            "Current best full-coverage 1D case metrics.",
            "paper_ready_with_context",
            "ROM status / model performance",
        ),
        (
            "1d_bakeoff_branch_thermal_development",
            BAKEOFF_DIR / "figures/png/branch_thermal_development.png",
            "Branch thermal-development comparison across model scenarios.",
            "meeting_ready",
            "Thermal closure behavior",
        ),
        (
            "1d_bakeoff_observable_leaderboard",
            BAKEOFF_DIR / "figures/png/observable_leaderboard.png",
            "Observable leaderboard from the June 23 bakeoff.",
            "meeting_ready",
            "Model-form ranking",
        ),
        (
            "frozen_validation_energy_partition",
            VALIDATION_DIR / "figures/png/primary_best_energy_partition.png",
            "Best defended scenario energy-partition error.",
            "paper_ready_with_context",
            "Energy balance",
        ),
        (
            "frozen_validation_mass_flow",
            VALIDATION_DIR / "figures/png/primary_best_mass_flow.png",
            "Best defended scenario mass-flow comparison.",
            "paper_ready_with_context",
            "Mass-flow validation",
        ),
        (
            "frozen_validation_sensor_parity",
            VALIDATION_DIR / "figures/png/primary_best_sensor_parity.png",
            "Sensor parity for the best defended scenario.",
            "paper_ready_with_context",
            "Temperature validation",
        ),
        (
            "frozen_validation_branch_development",
            VALIDATION_DIR / "figures/png/primary_branch_development.png",
            "Branch development state in the defended scenario.",
            "meeting_ready",
            "Development / assumptions",
        ),
        (
            "frozen_validation_metric_heatmap",
            VALIDATION_DIR / "figures/png/primary_scenario_metric_heatmap.png",
            "Scenario metric heatmap.",
            "meeting_ready",
            "Model-form selection",
        ),
    ]
    rows: list[dict[str, str]] = []
    for figure_id, path, use, readiness, slide in figures:
        rows.append(
            {
                "figure_id": figure_id,
                "path": rel(path),
                "exists": str(path.exists()),
                "readiness": readiness,
                "suggested_slide": slide,
                "use": use,
                "provenance": "existing generated figure; do not hand-edit",
                "limitation": "Current CFD reference is coarse mesh and not experiment-ground-truth.",
            }
        )
    return rows


def paper_readiness_rows(
    surface: dict[str, str],
    pressure_probe: dict[str, str],
    pressure_major: dict[str, str],
    pressure_endpoint: dict[str, str],
    correctness: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "item_id": "geometry_provenance_mesh_centerlines",
            "category": "methods",
            "readiness": "paper_ready_methods_after_final_crosscheck",
            "claim": "The ROM should use mesh-derived geometry and station provenance, not schematic probe CSV endpoints, for loopwise closure extraction.",
            "evidence": "AGENT-162 mesh-centerline work; correctness validation geometry_reference.csv",
            "key_number": "90 geometry rows normalized",
            "limitations": "Endpoint/fitting stations remain excluded from straight-friction fits.",
            "next_action": "Keep mesh-centerline provenance in every pressure and thermal table.",
        },
        {
            "item_id": "pressure_friction_audit",
            "category": "postprocessing_correctness",
            "readiness": "meeting_ready_not_final_closure",
            "claim": "`p_rgh` and section pressure gradients are now classified by physical role before use in the ROM.",
            "evidence": rel(CORRECTNESS_WORK / "pressure_friction_audit.csv"),
            "key_number": f"{correctness.get('pressure_friction_rows', 36)} pressure/friction rows; 6 direct-friction candidates; 12 buoyancy-contaminated apparent-resistance rows",
            "limitations": "Variable-density buoyancy decomposition is not implemented yet.",
            "next_action": "Add mechanical-loss balance before fitting Darcy f in heated/cooled legs.",
        },
        {
            "item_id": "thermal_htc_uaprime",
            "category": "thermal_closure",
            "readiness": "near_paper_ready_with_GCI_caveat",
            "claim": "HTC, UA', R', and Nu were extracted for Salt 2/3/4 mainline Jin continuations using OF13-reconstructed T.",
            "evidence": rel(CLOSURE_RESULTS_DIR / "README.md"),
            "key_number": "lower-leg HTC 252/269/288 W/m2-K; upcomer Nu 3.11/4.06/4.99",
            "limitations": "Coarse mesh; sign convention and property-temperature review remain required.",
            "next_action": "Carry UA' as primary energy closure and Nu as diagnostic/correlation candidate.",
        },
        {
            "item_id": "upcomer_recirculation",
            "category": "buoyancy_flow_structure",
            "readiness": "meeting_ready_mechanism",
            "claim": "The upcomer is not ordinary straight-pipe friction; it contains a buoyancy-driven recirculation/convection cell.",
            "evidence": rel(CLOSURE_RESULTS_DIR / "README.md"),
            "key_number": "15-33 percent backflow; Ri >> 1",
            "limitations": "Only three current mainline points; converged Salt-Q perturbation rows can now expand the operating range.",
            "next_action": "Use converged Salt-Q perturbation rows for closure fitting; keep failed/cancelled rows excluded.",
        },
        {
            "item_id": "current_1d_validation",
            "category": "ROM_validation",
            "readiness": "meeting_ready_diagnostic",
            "claim": "The defended June 23 1D scenario is useful but not yet predictive enough to present as final.",
            "evidence": rel(BAKEOFF_DIR / "surface_summary.csv"),
            "key_number": f"best energy error {surface.get('best_primary_mean_energy_error_pct_of_heater', '11.27')} percent; mass-flow relative error {surface.get('best_primary_mean_mass_flow_relative_error_pct_vs_cfd', '26.69')} percent",
            "limitations": "CFD reference is latest-window/coarse-mesh; scenario form may be compensating errors.",
            "next_action": "Score model forms against mdot, pressure distribution, heat balance, and sensor temperatures together.",
        },
        {
            "item_id": "local_hydraulic_replay",
            "category": "hydraulic_resistance",
            "readiness": "meeting_ready_diagnostic",
            "claim": "Local hydraulic replay shows that resistance bookkeeping can match mdot only when the CFD drive is held fixed.",
            "evidence": rel(PRESSURE_PREDICTIVITY_DIR / "local_hydraulic_replay_summary.csv"),
            "key_number": f"probe replay mean |mdot error| {pressure_probe.get('mean_mdot_abs_error_kg_s', '0.000255')} kg/s; major-only {pressure_major.get('mean_mdot_abs_error_kg_s', '0.554')} kg/s; endpoint {pressure_endpoint.get('mean_mdot_abs_error_kg_s', '0.484')} kg/s",
            "limitations": "Local replay is not a coupled predictive loop solve.",
            "next_action": "Use it as a resistance sanity check, not as full ROM validation.",
        },
        {
            "item_id": "mesh_independence_gci",
            "category": "uncertainty",
            "readiness": "blocked",
            "claim": "No mesh-independence uncertainty bound is currently available.",
            "evidence": ".agent/journal/2026-07-01/T6-mesh-independence-gci.md",
            "key_number": "single delivered mesh level only",
            "limitations": "External mesh generator is missing.",
            "next_action": "Obtain generator/refinement plan before claiming GCI bounds.",
        },
        {
            "item_id": "insulation_true_steady_runs",
            "category": "new_data",
            "readiness": "running_background",
            "claim": "Two true-steady insulation variants are running under AGENT-164 and should expand closure support if they converge.",
            "evidence": ".agent/status/2026-07-01_AGENT-164.md",
            "key_number": "2 OF13 runs on interactive node c318-008",
            "limitations": "Do not touch active case directory; results not available yet.",
            "next_action": "Check run status tomorrow and admit only converged true-steady windows.",
        },
        {
            "item_id": "experimental_validation",
            "category": "future_validation",
            "readiness": "required_future_work",
            "claim": "A real predictive 1D model ultimately needs validation against experimental data, not only CFD replay.",
            "evidence": rel(DEFAULT_REPORT_DIR / "experimental_validation_next_steps.md"),
            "key_number": "planned, not yet executed",
            "limitations": "Requires measured uncertainties and sensor-to-model station mapping.",
            "next_action": "Prepare experiment-data contract and calibration/validation split.",
        },
    ]


def model_form_rows(surface: dict[str, str], replay_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    probe = find_attempt(replay_rows, "major_plus_feature_probe_baseline")
    endpoint = find_attempt(replay_rows, "major_plus_feature_endpoint_baseline")
    major = find_attempt(replay_rows, "major_only_baseline")
    return [
        {
            "model_id": "F0",
            "name": "zero_loss",
            "driving": "buoyancy",
            "major_friction": "none",
            "minor_losses": "none",
            "thermal_model": "current 1D default",
            "geometry": "not meaningful",
            "solve_type": "diagnostic local",
            "primary_metric": "[TRIAL]",
            "current_status": "future_trial",
            "credibility": "diagnostic lower-bound resistance only",
            "source": rel(MODEL_FORM_DRAFT),
        },
        {
            "model_id": "F1",
            "name": "major_only",
            "driving": "buoyancy_or_local_replay",
            "major_friction": "straight-pipe major losses",
            "minor_losses": "none",
            "thermal_model": "not isolated in local replay",
            "geometry": "schematic/probe depending on run",
            "solve_type": "local replay diagnostic",
            "primary_metric": f"mean |mdot error| {major.get('mean_mdot_abs_error_kg_s', '')} kg/s",
            "current_status": "failed_as_predictive_form",
            "credibility": "useful negative control; omits first-order compact-loop losses",
            "source": rel(PRESSURE_PREDICTIVITY_DIR / "local_hydraulic_replay_summary.csv"),
        },
        {
            "model_id": "F2",
            "name": "major_plus_minor_default_K",
            "driving": "buoyancy",
            "major_friction": "1D default friction/multiplier",
            "minor_losses": "textbook/default K values",
            "thermal_model": "baseline defended scenario",
            "geometry": "1D model default",
            "solve_type": "coupled full 1D loop",
            "primary_metric": f"energy error {surface.get('best_primary_mean_energy_error_pct_of_heater', '')} percent; mass-flow error {surface.get('best_primary_mean_mass_flow_relative_error_pct_vs_cfd', '')} percent",
            "current_status": "current_defended_baseline_but_not_final",
            "credibility": "full-loop comparison, but agreement may be compensating physics",
            "source": rel(BAKEOFF_DIR / "surface_summary.csv"),
        },
        {
            "model_id": "F3",
            "name": "major_plus_minor_CFD_closures",
            "driving": "buoyancy",
            "major_friction": "buoyancy-corrected f_D target; current apparent f not yet fully decomposed",
            "minor_losses": "CFD bend/feature K target",
            "thermal_model": "UA' and/or Nu closures from latest OF13 T extraction",
            "geometry": "mesh-corrected",
            "solve_type": "planned coupled full 1D loop",
            "primary_metric": "[TRIAL]",
            "current_status": "highest_value_next_model_form",
            "credibility": "scientifically honest target, blocked by pressure decomposition and current closure uncertainty",
            "source": f"{rel(CORRECTNESS_DIR / 'README.md')}; {rel(CLOSURE_RESULTS_DIR / 'README.md')}",
        },
        {
            "model_id": "F4",
            "name": "local_hydraulic_replay_probe",
            "driving": "CFD pressure drive held fixed",
            "major_friction": "CFD-derived local resistance",
            "minor_losses": "CFD feature resistance",
            "thermal_model": "not coupled",
            "geometry": "probe path",
            "solve_type": "local replay",
            "primary_metric": f"mean |mdot error| {probe.get('mean_mdot_abs_error_kg_s', '')} kg/s",
            "current_status": "good_resistance_sanity_check",
            "credibility": "not predictive because drive side is prescribed",
            "source": rel(PRESSURE_PREDICTIVITY_DIR / "local_hydraulic_replay_summary.csv"),
        },
        {
            "model_id": "F5",
            "name": "local_hydraulic_replay_endpoint",
            "driving": "CFD pressure drive held fixed",
            "major_friction": "CFD-derived local resistance",
            "minor_losses": "CFD feature resistance",
            "thermal_model": "not coupled",
            "geometry": "endpoint/schematic",
            "solve_type": "local replay",
            "primary_metric": f"mean |mdot error| {endpoint.get('mean_mdot_abs_error_kg_s', '')} kg/s",
            "current_status": "geometry_provenance_failure",
            "credibility": "use only as cautionary evidence against endpoint/probe geometry",
            "source": rel(PRESSURE_PREDICTIVITY_DIR / "local_hydraulic_replay_summary.csv"),
        },
    ]


def coefficient_rows(replay_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [
        ("Salt 2 Jin", "lower_leg", "HTC", "252", "W/m2-K", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 2 Jin", "lower_leg", "UA_prime", "16.6", "W/m-K", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 2 Jin", "lower_leg", "R_prime", "0.060", "m-K/W", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 2 Jin", "upcomer", "HTC", "77", "W/m2-K", "OF13 thermal extraction", "diagnostic_mixed_convection"),
        ("Salt 2 Jin", "upcomer", "Nu", "3.11", "-", "OF13 thermal extraction", "diagnostic_mixed_convection"),
        ("Salt 2 Jin", "upcomer", "R_prime", "0.196", "m-K/W", "OF13 thermal extraction", "diagnostic_mixed_convection"),
        ("Salt 3 Jin", "lower_leg", "HTC", "269", "W/m2-K", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 3 Jin", "lower_leg", "UA_prime", "17.7", "W/m-K", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 3 Jin", "lower_leg", "R_prime", "0.057", "m-K/W", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 3 Jin", "upcomer", "HTC", "102", "W/m2-K", "OF13 thermal extraction", "diagnostic_mixed_convection"),
        ("Salt 3 Jin", "upcomer", "Nu", "4.06", "-", "OF13 thermal extraction", "diagnostic_mixed_convection"),
        ("Salt 3 Jin", "upcomer", "R_prime", "0.149", "m-K/W", "OF13 thermal extraction", "diagnostic_mixed_convection"),
        ("Salt 4 Jin", "lower_leg", "HTC", "288", "W/m2-K", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 4 Jin", "lower_leg", "UA_prime", "18.9", "W/m-K", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 4 Jin", "lower_leg", "R_prime", "0.053", "m-K/W", "OF13 thermal extraction", "near_paper_ready_with_GCI_caveat"),
        ("Salt 4 Jin", "upcomer", "HTC", "126", "W/m2-K", "OF13 thermal extraction", "diagnostic_mixed_convection"),
        ("Salt 4 Jin", "upcomer", "Nu", "4.99", "-", "OF13 thermal extraction", "diagnostic_mixed_convection"),
        ("Salt 4 Jin", "upcomer", "R_prime", "0.121", "m-K/W", "OF13 thermal extraction", "diagnostic_mixed_convection"),
    ]
    out = [
        {
            "case_or_form": case,
            "segment": segment,
            "coefficient": coeff,
            "value": value,
            "units": units,
            "source_method": method,
            "credibility": credibility,
            "provenance": rel(CLOSURE_RESULTS_DIR / "README.md"),
            "limitation": "Coarse mesh; no GCI; property and sign-convention review remain open.",
        }
        for case, segment, coeff, value, units, method, credibility in rows
    ]
    for attempt in (
        "major_plus_feature_probe_baseline",
        "major_plus_feature_endpoint_baseline",
        "major_only_baseline",
    ):
        replay = find_attempt(replay_rows, attempt)
        out.append(
            {
                "case_or_form": attempt,
                "segment": "loop",
                "coefficient": "mean_mdot_abs_error",
                "value": replay.get("mean_mdot_abs_error_kg_s", ""),
                "units": "kg/s",
                "source_method": "local hydraulic replay",
                "credibility": "diagnostic resistance check",
                "provenance": rel(PRESSURE_PREDICTIVITY_DIR / "local_hydraulic_replay_summary.csv"),
                "limitation": "CFD pressure drive is prescribed; this is not coupled ROM predictivity.",
            }
        )
    return out


def future_model_rows() -> list[dict[str, str]]:
    return [
        {
            "candidate_id": "M1",
            "model_form": "buoyancy_corrected_mechanical_loss",
            "purpose": "Separate true wall/friction loss from `p_rgh` gradients and local buoyancy source terms.",
            "data_needed": "Section means, density/temperature profile, streamwise gravity projection, mesh centerlines.",
            "fit_target": "Darcy f_D or excess f/f_lam for clean spans.",
            "uncertainty_plan": "Propagate station choice, pressure noise, mesh/GCI, and property uncertainty.",
            "priority": "highest",
        },
        {
            "candidate_id": "M2",
            "model_form": "low_Re_bend_K_or_KRe",
            "purpose": "Represent compact-loop minor losses that are first-order at Re 60-135.",
            "data_needed": "Bend/feature pressure budgets after corrected geometry.",
            "fit_target": "K, K/Re, or equivalent resistance per bend family.",
            "uncertainty_plan": "Compare probe, mesh-centerline, and endpoint exclusions; bootstrap across cases.",
            "priority": "high",
        },
        {
            "candidate_id": "M3",
            "model_form": "development_redevelopment_multiplier",
            "purpose": "Capture entrance, bend-exit, and short-leg redevelopment losses beyond fully-developed laminar theory.",
            "data_needed": "Branch development metrics, local Re, distance since feature.",
            "fit_target": "f multiplier or additive pressure-loss term.",
            "uncertainty_plan": "Gate by clean-station support and exclude fitting endpoints.",
            "priority": "high",
        },
        {
            "candidate_id": "M4",
            "model_form": "UA_prime_constant_or_power_law",
            "purpose": "Use UA' directly as the ROM energy closure instead of overclaiming a universal Nu law.",
            "data_needed": "Lower-leg and upcomer HTC/UA' tables, q', T_wall, T_bulk.",
            "fit_target": "UA'(Re), UA'(Ra), or segment-specific constant UA'.",
            "uncertainty_plan": "Report parameter covariance and leave Pr collinearity explicit.",
            "priority": "high",
        },
        {
            "candidate_id": "M5",
            "model_form": "upcomer_recirculation_onset",
            "purpose": "Replace upcomer friction with a mixed/natural-convection-cell closure.",
            "data_needed": "Backflow fraction, Ri/Ra/Gr/Re/Pr, true-steady insulation/Q variants.",
            "fit_target": "recirculation strength or effective thermal/hydraulic resistance.",
            "uncertainty_plan": "Do not admit false-steady perturbations; use censored/onset model if data remain sparse.",
            "priority": "high_after_T2_results",
        },
        {
            "candidate_id": "M6",
            "model_form": "experiment_validated_uncertainty_layer",
            "purpose": "Move from CFD replay to real predictive credibility.",
            "data_needed": "Experimental mdot, powers, wall/fluid temperatures, ambient/insulation, geometry, uncertainty.",
            "fit_target": "Prediction intervals for mdot, heat loss, and sensor temperatures.",
            "uncertainty_plan": "Use calibration/validation split; do not tune and test on the same experiment.",
            "priority": "future_required",
        },
    ]


def run_inventory_rows() -> list[dict[str, str]]:
    return [
        {
            "run_or_package": "mainline Salt 2/3/4 Jin continuations",
            "type": "CFD reference",
            "current_use": "closure-grade thermal and pressure context",
            "status": "usable_with_coarse_mesh_caveat",
            "source": rel(CLOSURE_RESULTS_DIR / "README.md"),
        },
        {
            "run_or_package": "Salt 1 Jin",
            "type": "CFD reference",
            "current_use": "provisional only",
            "status": "excluded_from_closure_grade",
            "source": rel(CLOSURE_RESULTS_DIR / "README.md"),
        },
        {
            "run_or_package": "Q/insulation perturbation runs",
            "type": "sensitivity data",
            "current_use": "closure-fit when converged",
            "status": "row_quality_dependent",
            "source": ".agent/status/2026-07-01_AGENT-166.md",
        },
        {
            "run_or_package": "true-steady insulation variants",
            "type": "new CFD runs",
            "current_use": "future upcomer/insulation correlation support",
            "status": "running",
            "source": ".agent/status/2026-07-01_AGENT-164.md",
        },
        {
            "run_or_package": "scaling study jobs",
            "type": "compute performance",
            "current_use": "postponed",
            "status": "not submitted/resubmission deferred per user note",
            "source": "operational_notes/07-26/01/2026-07-01_scaling_study_resume_later.md",
        },
    ]


def write_experimental_validation_note(report_dir: Path) -> None:
    text = f"""# Experimental Validation Next Steps

Date: `2026-07-01`

The current 1D ROM evidence is CFD-replay evidence. That is useful for mechanism
identification and post-processing QA, but it is not yet proof that the model is
predictive in the physical experiment.

## Required Data Contract

- Experimental mass flow with uncertainty and calibration history.
- Heater power, wall heat loss, ambient temperature, insulation state, and their
  uncertainties.
- Wall and fluid temperature sensor locations mapped to CFD/1D stations.
- Loop geometry, pipe IDs, bend/fitting definitions, and material/insulation
  properties as installed.
- Run windows that are demonstrably steady or assigned transient uncertainty.

## Validation Protocol

1. Freeze a model form and coefficient set before looking at held-out experiments.
2. Run the 1D model with the experimental boundary conditions and geometry.
3. Compare mass flow, heat balance, wall/fluid temperatures, and pressure-drop
   proxies where available.
4. Quantify error with signed bias, MAE/RMSE, normalized error, and uncertainty
   intervals, not only best-case plots.
5. Calibrate only on a declared calibration subset; report held-out validation
   separately.

## Current Credibility Boundary

Until this is done, the honest claim is: the ROM is being made consistent with
CFD-derived closure physics and post-processing provenance. It is not yet
experiment-validated as a real-world predictor.
"""
    (report_dir / "experimental_validation_next_steps.md").write_text(text, encoding="utf-8")


def write_readme(report_dir: Path, work_dir: Path, summary: dict[str, Any]) -> None:
    energy_error = f"{summary['best_energy_error_pct']:.2f}" if summary["best_energy_error_pct"] is not None else "unknown"
    mass_flow_error = f"{summary['best_mass_flow_error_pct']:.2f}" if summary["best_mass_flow_error_pct"] is not None else "unknown"
    probe_error = f"{summary['probe_mdot_error_kg_s']:.6f}" if summary["probe_mdot_error_kg_s"] is not None else "unknown"
    text = f"""# Presentation Readiness and ROM Agenda

Date: `2026-07-01`  
Task: `AGENT-169`  
Status: generated from existing reports; no OpenFOAM execution

## Purpose

This package collects what can be shown in tomorrow's meeting and separates it
from what still needs more work before it becomes paper-ready. It also creates
reusable comparison tables for future 1D model forms, coefficients, figures,
and experimental-validation planning.

Work products: `{rel(work_dir)}`

## Meeting-Ready Headline

- The post-processing pipeline now has explicit geometry, pressure/friction,
  and thermal-audit tables instead of mixing `p_rgh`, apparent resistance, and
  closure-grade quantities.
- OF13 T reconstruction unlocked thermal closures for Salt 2/3/4 Jin: lower-leg
  HTC rises from 252 to 288 W/m2-K; upcomer Nu rises from 3.11 to 4.99.
- Current 1D validation is useful but not final: the defended baseline gives
  about {energy_error} percent mean energy error and
  {mass_flow_error} percent mass-flow relative error against
  the CFD latest-window reference.
- Local hydraulic replay is a strong diagnostic but not a predictive result:
  probe replay is near {probe_error} kg/s mean mdot error,
  while major-only and endpoint forms fail by orders of magnitude.

## Generated Tables

- `paper_readiness_matrix.csv`: what is paper-ready, meeting-ready, blocked, or
  future validation.
- `figure_inventory.csv`: figures that can be used in the meeting and their
  readiness caveats.
- `model_form_inventory.csv`: current and future 1D model forms with assumptions,
  metrics, and credibility boundaries.
- `coefficient_inventory.csv`: thermal coefficients and diagnostic hydraulic
  replay metrics that can be compared against future fits.
- `future_model_forms.csv`: candidate closure/model forms to fit next.
- `run_and_package_inventory.csv`: provenance and status for current packages
  and run families.
- `experimental_validation_next_steps.md`: what is needed to validate the 1D
  model against physical experiment data.

## Credibility Boundary

The strongest paper-facing material today is methods/provenance and diagnostic
mechanism evidence. The full predictive 1D model is still in development because
mesh independence is blocked, perturbation runs are false-steady, and pressure
gradients still need variable-density buoyancy decomposition before being fit as
mechanical losses.
"""
    (report_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    report_dir = ensure_dir(Path(args.report_dir))
    work_dir = ensure_dir(Path(args.work_dir))

    surface_rows = read_csv_rows(BAKEOFF_DIR / "surface_summary.csv")
    replay_rows = read_csv_rows(PRESSURE_PREDICTIVITY_DIR / "local_hydraulic_replay_summary.csv")
    correctness = read_json(CORRECTNESS_DIR / "summary.json") or read_json(CORRECTNESS_WORK / "summary.json")

    surface = find_surface(surface_rows, "baseline_full_surface") or (surface_rows[0] if surface_rows else {})
    probe = find_attempt(replay_rows, "major_plus_feature_probe_baseline")
    major = find_attempt(replay_rows, "major_only_baseline")
    endpoint = find_attempt(replay_rows, "major_plus_feature_endpoint_baseline")

    paper_rows = paper_readiness_rows(surface, probe, major, endpoint, correctness)
    figures = figure_inventory()
    models = model_form_rows(surface, replay_rows)
    coeffs = coefficient_rows(replay_rows)
    futures = future_model_rows()
    runs = run_inventory_rows()

    tables = {
        "paper_readiness_matrix.csv": paper_rows,
        "figure_inventory.csv": figures,
        "model_form_inventory.csv": models,
        "coefficient_inventory.csv": coeffs,
        "future_model_forms.csv": futures,
        "run_and_package_inventory.csv": runs,
    }
    for name, rows in tables.items():
        if rows:
            csv_dump(work_dir / name, list(rows[0].keys()), rows)
            csv_dump(report_dir / name, list(rows[0].keys()), rows)

    write_experimental_validation_note(report_dir)

    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-169",
        "report_dir": rel(report_dir),
        "work_dir": rel(work_dir),
        "paper_readiness_rows": len(paper_rows),
        "figure_rows": len(figures),
        "model_form_rows": len(models),
        "coefficient_rows": len(coeffs),
        "future_model_form_rows": len(futures),
        "run_inventory_rows": len(runs),
        "best_scenario": surface.get("best_primary_scenario", ""),
        "best_energy_error_pct": as_float(surface, "best_primary_mean_energy_error_pct_of_heater"),
        "best_mass_flow_error_pct": as_float(surface, "best_primary_mean_mass_flow_relative_error_pct_vs_cfd"),
        "probe_mdot_error_kg_s": as_float(probe, "mean_mdot_abs_error_kg_s"),
        "major_only_mdot_error_kg_s": as_float(major, "mean_mdot_abs_error_kg_s"),
        "endpoint_mdot_error_kg_s": as_float(endpoint, "mean_mdot_abs_error_kg_s"),
        "source_packages": [
            rel(BAKEOFF_DIR),
            rel(VALIDATION_DIR),
            rel(PRESSURE_PREDICTIVITY_DIR),
            rel(CLOSURE_RESULTS_DIR),
            rel(CORRECTNESS_DIR),
            rel(MODEL_FORM_DRAFT),
        ],
    }
    json_dump(work_dir / "summary.json", summary)
    json_dump(report_dir / "summary.json", summary)
    write_readme(report_dir, work_dir, summary)


if __name__ == "__main__":
    main()
