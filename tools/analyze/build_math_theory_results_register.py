#!/usr/bin/env python3
"""Build the cross-cutting math, theory, assumptions, and results register."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_math_theory_assumptions_results_register"
)

EQUATION_COLUMNS = [
    "equation_id",
    "lane",
    "equation_or_definition",
    "variables",
    "allowed_use",
    "blocked_use",
    "admission_dependency",
    "primary_source",
]
ASSUMPTION_COLUMNS = [
    "assumption_id",
    "lane",
    "assumption",
    "default_policy",
    "violation_if",
    "source_artifact",
]
RESULT_COLUMNS = [
    "field_name",
    "required",
    "units_or_allowed_values",
    "description",
    "why_required",
]
HOOK_COLUMNS = [
    "area",
    "current_status",
    "current_result",
    "next_required_evidence",
    "source_artifact",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def equation_register() -> list[dict[str, str]]:
    return [
        {
            "equation_id": "loop_pressure_root",
            "lane": "hydraulics",
            "equation_or_definition": "Find mdot such that dp_buoyancy(mdot,T) - dp_losses(mdot,T) - dp_residual = 0.",
            "variables": "mdot, density, branch temperatures, elevation, distributed losses, minor losses, reset/development terms",
            "allowed_use": "Predictive mdot solve after closure terms are declared from setup or trained rows.",
            "blocked_use": "Do not supply CFD mdot as a runtime input in predictive modes.",
            "admission_dependency": "Hydraulic gate and train/validation/holdout split.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md",
        },
        {
            "equation_id": "distributed_pressure_loss",
            "lane": "hydraulics",
            "equation_or_definition": "dp_dist = f_D * (L/D_h) * (rho * v_bulk^2 / 2).",
            "variables": "f_D, L, D_h, rho, v_bulk",
            "allowed_use": "Straight-section or branchwise pressure-loss attribution when tap/plane placement is fit-safe.",
            "blocked_use": "Do not hide component, cluster, reset, or recirculation loss in one global f_D.",
            "admission_dependency": "Pressure ledger fit-safety and coefficient-naming gate.",
            "primary_source": "operational_notes/maps/pressure-and-momentum-budget.md",
        },
        {
            "equation_id": "minor_or_component_loss",
            "lane": "hydraulics",
            "equation_or_definition": "dp_K = K_local * (rho * v_bulk^2 / 2).",
            "variables": "K_local, rho, v_bulk",
            "allowed_use": "Named fitting/component/cluster diagnostics or localized trained terms with declared provenance.",
            "blocked_use": "Do not promote branch-apparent or aggregate K as universal localized H1 closure.",
            "admission_dependency": "Named-loss/reset gate and localized Fluid support.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md",
        },
        {
            "equation_id": "bulk_velocity",
            "lane": "geometry_properties",
            "equation_or_definition": "v_bulk = mdot / (rho * A_flow).",
            "variables": "mdot, rho, A_flow",
            "allowed_use": "Convert solved or observed mass flow to section dynamic pressure and nondimensional groups.",
            "blocked_use": "Do not use CFD mdot-derived v_bulk as a predictive runtime anchor.",
            "admission_dependency": "Predictive input contract.",
            "primary_source": "work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/README.md",
        },
        {
            "equation_id": "reynolds_number",
            "lane": "properties",
            "equation_or_definition": "Re = rho * v_bulk * D_h / mu.",
            "variables": "rho, v_bulk, D_h, mu",
            "allowed_use": "Property-lane reporting, friction/heat-transfer source-envelope checks.",
            "blocked_use": "Do not mix property modes inside one fitted model score.",
            "admission_dependency": "Property mode declared before fitting or scoring.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md",
        },
        {
            "equation_id": "prandtl_number",
            "lane": "properties",
            "equation_or_definition": "Pr = cp * mu / k.",
            "variables": "cp, mu, k",
            "allowed_use": "Heat-transfer source-envelope and sensitivity reporting.",
            "blocked_use": "Do not interpret Nu residuals without declaring cp, mu, and k lane.",
            "admission_dependency": "Property mode gate.",
            "primary_source": "work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/property_sensitivity_summary.csv",
        },
        {
            "equation_id": "richardson_number",
            "lane": "mixed_convection",
            "equation_or_definition": "Ri = Gr / Re^2.",
            "variables": "Gr, Re",
            "allowed_use": "Regime and recirculation diagnostics.",
            "blocked_use": "Do not use failed F5 Ri multiplier as production closure.",
            "admission_dependency": "Upcomer onset and F6/Friction correction gates.",
            "primary_source": "operational_notes/maps/friction-closures.md",
        },
        {
            "equation_id": "segment_heat_balance",
            "lane": "thermal",
            "equation_or_definition": "mdot * cp * (T_out - T_in) = Q_heater - Q_cooler - Q_passive - Q_storage - Q_residual.",
            "variables": "mdot, cp, T_in, T_out, Q_heater, Q_cooler, Q_passive, Q_storage, Q_residual",
            "allowed_use": "Thermal residual attribution and admission review.",
            "blocked_use": "Do not fit internal Nu to absorb cooler, passive wall, heater efficiency, or storage residuals.",
            "admission_dependency": "Sign, enthalpy, heat-balance, and thermal mesh gates.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md",
        },
        {
            "equation_id": "internal_convection",
            "lane": "thermal",
            "equation_or_definition": "q_internal = h_i * A_i * (T_wall_i - T_bulk).",
            "variables": "h_i, A_i, T_wall_i, T_bulk",
            "allowed_use": "Internal HTC/Nu diagnostic or fit-admissible row only after thermal admission.",
            "blocked_use": "Do not use repaired smoke rows as fit targets before admission.",
            "admission_dependency": "Thermal admission/internal-Nu gate.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv",
        },
        {
            "equation_id": "nusselt_number",
            "lane": "thermal",
            "equation_or_definition": "Nu = h_i * D_h / k.",
            "variables": "h_i, D_h, k",
            "allowed_use": "Dimensionless reporting only for admitted or diagnostic rows with explicit property lane.",
            "blocked_use": "Do not call section-effective or recirculating rows universal Nu.",
            "admission_dependency": "Coefficient-naming and recirculation gates.",
            "primary_source": "work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/coefficient_naming_limits.csv",
        },
        {
            "equation_id": "ua_prime",
            "lane": "thermal",
            "equation_or_definition": "UA_prime = q_internal / (L_segment * deltaT_drive).",
            "variables": "q_internal, L_segment, deltaT_drive",
            "allowed_use": "Segment-effective thermal diagnostic or admitted closure row.",
            "blocked_use": "Do not compare across rows unless deltaT_drive definition and source policy match.",
            "admission_dependency": "Thermal sign, heat-balance, and mesh gates.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md",
        },
        {
            "equation_id": "external_convection",
            "lane": "boundary",
            "equation_or_definition": "q_ext = h_ext * A_ext * (T_surface_or_shell - Ta).",
            "variables": "h_ext, A_ext, T_surface_or_shell, Ta",
            "allowed_use": "Setup-only external boundary model when Fluid accepts first-class boundary dictionaries.",
            "blocked_use": "Do not tune hA per case to hide HX, heater, or internal-Nu residuals.",
            "admission_dependency": "Fluid external-boundary API and boundary model-form gate.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md",
        },
        {
            "equation_id": "radiation_boundary",
            "lane": "boundary",
            "equation_or_definition": "q_rad = emissivity * sigma * A * (T_surface^4 - Tsur^4).",
            "variables": "emissivity, sigma, A, T_surface, Tsur",
            "allowed_use": "First-class boundary model or sensitivity study with explicit no-double-counting policy.",
            "blocked_use": "Do not add a separate radiation term on top of CFD realized wallHeatFlux replay.",
            "admission_dependency": "Radiation semantics and Fluid API gate.",
            "primary_source": "operational_notes/maps/thermal-boundary-and-radiation.md",
        },
        {
            "equation_id": "hx_ua_or_epsilon_ntu",
            "lane": "boundary_hx",
            "equation_or_definition": "Q_HX = UA_HX * LMTD, or Q_HX = epsilon(mdot,UA,C_min,C_max) * C_min * (T_hot_in - T_cold_in).",
            "variables": "UA_HX, LMTD, epsilon, mdot, C_min, C_max, T_hot_in, T_cold_in",
            "allowed_use": "Predictive cooler model after one form is frozen under the declared split.",
            "blocked_use": "Do not call imposed CFD cooler duty predictive HX.",
            "admission_dependency": "HX fit with train/validation/holdout discipline.",
            "primary_source": "operational_notes/maps/forward-predictive-model.md",
        },
        {
            "equation_id": "gci_admission_formula",
            "lane": "mesh_uncertainty",
            "equation_or_definition": "GCI_fine = F_s * abs((phi_fine - phi_medium) / phi_fine) / (r^p - 1).",
            "variables": "F_s, phi_fine, phi_medium, r, observed order p",
            "allowed_use": "Publication uncertainty only for admitted monotone triplets with valid p and asymptotic checks.",
            "blocked_use": "Do not fabricate GCI for two-level, blocked, oscillatory, divergent, or sign-uncertain rows.",
            "admission_dependency": "Closure-QOI mesh gate.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md",
        },
        {
            "equation_id": "post_solve_score_residual",
            "lane": "scorecard",
            "equation_or_definition": "residual_y = y_model - y_reference, joined only after the forward solve.",
            "variables": "y_model, y_reference",
            "allowed_use": "Train/validation/holdout score tables and residual attribution.",
            "blocked_use": "Do not feed y_reference into runtime model state.",
            "admission_dependency": "Predictive input contract and validation split.",
            "primary_source": "work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/README.md",
        },
    ]


def assumption_register() -> list[dict[str, str]]:
    return [
        {
            "assumption_id": "predictive_runtime_hygiene",
            "lane": "forward_model",
            "assumption": "Predictive modes do not consume CFD mdot, realized CFD wallHeatFlux, CFD sensor references, or measured TP/TW temperatures at runtime.",
            "default_policy": "Targets join only after solve for scoring.",
            "violation_if": "Any target or diagnostic CFD evidence changes the solved mdot, heat state, or sensor state.",
            "source_artifact": "work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/README.md",
        },
        {
            "assumption_id": "split_discipline",
            "lane": "scorecard",
            "assumption": "salt_2 is train, salt_3 is validation, salt_4 is holdout for the current mainline Salt rows.",
            "default_policy": "Do not revise split after inspecting validation or holdout residuals.",
            "violation_if": "Validation or holdout rows are used to fit K, UA, eta, hA, Nu, or friction corrections without a prior dated split revision.",
            "source_artifact": "work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv",
        },
        {
            "assumption_id": "property_lane_first",
            "lane": "properties",
            "assumption": "Property mode is declared before interpreting Re, Pr, buoyancy head, pressure residual, or heat residual.",
            "default_policy": "Use replication mode for baseline; use alternate property sets only as declared sensitivity/reference lanes.",
            "violation_if": "A fitted result mixes property modes or omits the property lane.",
            "source_artifact": "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md",
        },
        {
            "assumption_id": "radiation_no_double_counting",
            "lane": "boundary",
            "assumption": "CFD rcExternalTemperature wallHeatFlux already includes emissivity/Tsur effects.",
            "default_policy": "Represent radiation separately only in first-class boundary modeling or sensitivity studies, not on top of realized CFD wallHeatFlux replay.",
            "violation_if": "A replay adds q_rad to a realized wallHeatFlux that already embeds radiation.",
            "source_artifact": "operational_notes/maps/thermal-boundary-and-radiation.md",
        },
        {
            "assumption_id": "h1_proxy_boundary",
            "lane": "hydraulics",
            "assumption": "Current H1 evidence is an aggregate fixed-K proxy, not faithful localized H1.",
            "default_policy": "Use H1 as diagnostic/proxy evidence until localized named-loss/reset support lands.",
            "violation_if": "A scorecard calls current H1 publication-ready localized closure.",
            "source_artifact": "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md",
        },
        {
            "assumption_id": "thermal_smoke_boundary",
            "lane": "thermal",
            "assumption": "Repaired thermal extraction smoke is diagnostic until sign, heat-balance, downcomer policy, and mesh gates admit rows.",
            "default_policy": "No thermal fit from smoke rows.",
            "violation_if": "A thermal UA/HTC/Nu row is used as fit target before admission.",
            "source_artifact": "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md",
        },
        {
            "assumption_id": "sensor_post_solve_only",
            "lane": "sensor",
            "assumption": "TP/TW sensor temperatures are validation targets only.",
            "default_policy": "Join provisional scoreable sensor rows after solve and exclude blocked labels explicitly.",
            "violation_if": "Sensor measurements anchor the runtime solve or a sensor-wise correction.",
            "source_artifact": "work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/README.md",
        },
    ]


def result_contract() -> list[dict[str, str]]:
    return [
        {"field_name": "task_id", "required": "yes", "units_or_allowed_values": "AGENT-* or TODO-*", "description": "Board task that produced the result.", "why_required": "Prevents orphaned evidence."},
        {"field_name": "case_id", "required": "yes", "units_or_allowed_values": "salt_2; salt_3; salt_4; explicit corrected-Q key; diagnostic key", "description": "Canonical row/case identifier.", "why_required": "Needed for split, admission, and provenance joins."},
        {"field_name": "split_role", "required": "yes", "units_or_allowed_values": "train; validation; holdout; diagnostic-only; blocked; not_in_split", "description": "Fit/score role for the row.", "why_required": "Prevents accidental refit on validation or holdout rows."},
        {"field_name": "model_mode", "required": "yes", "units_or_allowed_values": "diagnostic_fixed_mdot; forward_v0_imposed_cooler; h1_proxy; predictive_hx; final_forward_v1; other_explicit", "description": "Execution or interpretation mode.", "why_required": "Separates predictive modes from diagnostic replays."},
        {"field_name": "runtime_inputs", "required": "yes", "units_or_allowed_values": "semicolon-delimited field names", "description": "Fields consumed before solve.", "why_required": "Audits CFD target leakage."},
        {"field_name": "forbidden_runtime_inputs_used", "required": "yes", "units_or_allowed_values": "true; false", "description": "Whether CFD mdot, realized wallHeatFlux, or targets influenced runtime solve.", "why_required": "Hard predictive input gate."},
        {"field_name": "property_mode", "required": "yes", "units_or_allowed_values": "replication_reis_jadyn; declared sensitivity/reference lane", "description": "Property lane for rho/mu/cp/k.", "why_required": "Properties materially affect Re, Pr, Gz, buoyancy, and heat residuals."},
        {"field_name": "equation_ids", "required": "yes", "units_or_allowed_values": "IDs from equation_register.csv", "description": "Math forms used by the row.", "why_required": "Makes theory traceable."},
        {"field_name": "fitted_parameters", "required": "yes", "units_or_allowed_values": "names and values or none", "description": "Any K, UA, eta, hA, Nu, friction, or correction parameters.", "why_required": "Separates trained terms from setup inputs."},
        {"field_name": "fit_source_rows", "required": "yes", "units_or_allowed_values": "case IDs or none", "description": "Rows used to fit each parameter.", "why_required": "Enforces train/validation/holdout discipline."},
        {"field_name": "admission_status", "required": "yes", "units_or_allowed_values": "fit-admissible; validation-only; diagnostic-only; blocked; failed", "description": "Allowed use of the result.", "why_required": "Prevents overclaiming."},
        {"field_name": "mdot_error_kg_s", "required": "for scorecards", "units_or_allowed_values": "kg/s", "description": "Predicted minus reference mdot after solve.", "why_required": "Primary hydraulic score."},
        {"field_name": "temperature_error_K", "required": "for thermal/sensor scorecards", "units_or_allowed_values": "K", "description": "Predicted minus reference temperature after solve.", "why_required": "Primary thermal score."},
        {"field_name": "heat_residual_W", "required": "for thermal/boundary rows", "units_or_allowed_values": "W", "description": "Unclosed heat residual after declared source/sink terms.", "why_required": "Separates internal Nu from boundary/source errors."},
        {"field_name": "uncertainty_status", "required": "yes", "units_or_allowed_values": "publication-ready; diagnostic; missing-triplet; oscillatory; time-gated; not_applicable", "description": "Mesh/time/UQ readiness.", "why_required": "Thesis claims need uncertainty status."},
        {"field_name": "source_paths", "required": "yes", "units_or_allowed_values": "semicolon-delimited repo paths", "description": "Exact source artifacts.", "why_required": "Provenance and reproducibility."},
        {"field_name": "do_not_claim", "required": "yes", "units_or_allowed_values": "plain text", "description": "Explicit overclaim boundary.", "why_required": "Keeps presentation/thesis wording safe."},
    ]


def evidence_hooks() -> list[dict[str, str]]:
    return [
        {
            "area": "forward_v0_solve_case",
            "current_status": "admitted_confirmation",
            "current_result": "solve_case-vs-fast_scan comparison passed 6/6 rows; solve_case authoritative for forward-v0.",
            "next_required_evidence": "Use solve_case for any final forward mode after hydraulic/boundary implementation lands.",
            "source_artifact": "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json",
        },
        {
            "area": "h1_hydraulic_proxy",
            "current_status": "diagnostic_proxy",
            "current_result": "F1 mean mdot error dropped from 0.005478 to 0.002144 kg/s, a 60.29 percent reduction; all rows still overpredict.",
            "next_required_evidence": "Faithful localized named-loss/reset implementation and rerun.",
            "source_artifact": "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md",
        },
        {
            "area": "thermal_mesh_admission",
            "current_status": "blocked",
            "current_result": "25 QOI rows, 0 publication-ready GCI rows, 0 fit-admissible thermal rows.",
            "next_required_evidence": "Sign/enthalpy, heat-balance, lower-leg Nu, downcomer policy, and valid GCI checks.",
            "source_artifact": "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md",
        },
        {
            "area": "boundary_hx_wall_radiation",
            "current_status": "model_form_decided_api_pending",
            "current_result": "Boundary/HX/wall/radiation decision table separates admitted, sensitivity-only, reference-only, and rejected source roles.",
            "next_required_evidence": "Setup-only executable Fluid API and predictive HX model without imposed CFD cooler duty.",
            "source_artifact": "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md",
        },
        {
            "area": "sensor_map",
            "current_status": "partial_diagnostic",
            "current_result": "17 labels mapped, 15 provisionally diagnostic-scoreable, TP2 and TW10 blocked.",
            "next_required_evidence": "Survey-grade coordinates or explicit exclusion policy for final scorecard.",
            "source_artifact": "work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/README.md",
        },
        {
            "area": "corrected_salt_q",
            "current_status": "terminal_gate_pending",
            "current_result": "Live job 3293924 was still running at the latest admission check; no corrected-Q row admitted.",
            "next_required_evidence": "Terminal Slurm state and post-exit operating-point/admission review.",
            "source_artifact": ".agent/status/2026-07-14_AGENT-313.md",
        },
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - reports/thesis_dossier/master_thesis_bullet_outline.md
  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
tags: [thesis-source, methodology, equations, assumptions, results-contract, forward-model]
related:
  - reports/thesis_dossier/README.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-322
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Math, Theory, Assumptions, and Results Register

This package is the cross-cutting documentation contract for the CFD-to-1D
closure workflow. It records the equations that future packages should cite,
the assumptions that protect predictive-mode hygiene, and the fields required
when new results arrive.

## Purpose

The project should not progress by tuning one global coefficient. Each result
must state its governing balance, property lane, fitted parameters, split role,
admission status, and overclaim boundary. This package makes that requirement
machine-readable enough for future builders and human-readable enough for the
thesis methods chapter.

## Files

- `equation_register.csv`: `{summary['n_equations']}` equations/definitions and
  their allowed/blocked use.
- `assumption_register.csv`: `{summary['n_assumptions']}` assumptions and
  violation conditions.
- `result_intake_contract.csv`: `{summary['n_result_fields']}` required fields
  for future scorecards and gate packages.
- `current_evidence_hooks.csv`: current result hooks that future agents should
  update or cite as gates move.
- `summary.json`: machine-readable package metadata.

## Current Interpretation

- Forward-v0 solve_case execution is admitted as confirmation evidence.
- H1 is useful hydraulic directionality evidence, but remains proxy-only until
  localized named-loss/reset support lands.
- Thermal UA/HTC/Nu remains blocked for fitting: the current mesh gate reports
  zero fit-admissible thermal rows.
- HX/cooler and external-boundary work must become setup-only before final
  forward-v1 can be claimed.
- Sensor temperatures are validation targets only and join after solve.

## How To Use This Register

Every new gate-moving result should cite equation IDs from
`equation_register.csv`, fill the fields in `result_intake_contract.csv`, and
state which assumptions from `assumption_register.csv` it relies on. If a result
cannot satisfy the contract, it should be labeled diagnostic-only or blocked
rather than silently excluded.
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    equations = equation_register()
    assumptions = assumption_register()
    results = result_contract()
    hooks = evidence_hooks()

    write_csv(out_dir / "equation_register.csv", equations, EQUATION_COLUMNS)
    write_csv(out_dir / "assumption_register.csv", assumptions, ASSUMPTION_COLUMNS)
    write_csv(out_dir / "result_intake_contract.csv", results, RESULT_COLUMNS)
    write_csv(out_dir / "current_evidence_hooks.csv", hooks, HOOK_COLUMNS)
    summary = {
        "task_id": "AGENT-322",
        "generated_utc": utc_now(),
        "n_equations": len(equations),
        "n_assumptions": len(assumptions),
        "n_result_fields": len(results),
        "n_evidence_hooks": len(hooks),
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "outputs": [
            "README.md",
            "equation_register.csv",
            "assumption_register.csv",
            "result_intake_contract.csv",
            "current_evidence_hooks.csv",
            "summary.json",
        ],
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = build_package(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
