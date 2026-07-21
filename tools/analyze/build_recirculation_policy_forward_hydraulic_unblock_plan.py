#!/usr/bin/env python3
"""Build AGENT-419 recirculation policy and final unblock plan artifacts."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-419"
DATE = "2026-07-15"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan")
OUT = ROOT / OUT_REL

AGENT406 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair"
AGENT407 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger"
AGENT409 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess"
AGENT414 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh"
AGENT405 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


def recirculation_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "policy_variable": "reverse_area_fraction",
            "rule_band": "0 <= RAF < 0.01",
            "threshold_formula": "RAF = A(U_axial < 0) / A_total",
            "physical_interpretation": "no material reverse-flow area",
            "fit_use": "fit_candidate_if_all_source_mesh_sign_boundary_gates_pass",
            "validation_use": "validation_candidate",
            "diagnostic_use": "not_required_by_recirculation_policy",
            "invalid_single_stream_coefficients": "none_by_recirculation_policy",
            "required_companion_gates": "mesh_GCI; pressure_definition; sign_convention; heat_balance; setup_only_boundary_inputs",
            "current_evidence_overlap": "no AGENT-406 PM5 row; no AGENT-409 raw tap proxy",
        },
        {
            "policy_variable": "reverse_area_fraction",
            "rule_band": "0.01 <= RAF < 0.05",
            "threshold_formula": "RAF = A(U_axial < 0) / A_total",
            "physical_interpretation": "weak localized reverse pocket",
            "fit_use": "validation_only_by_default; fit only after explicit uncertainty override",
            "validation_use": "bounded_validation_candidate",
            "diagnostic_use": "onset_diagnostic",
            "invalid_single_stream_coefficients": "do_not_fit_true_Nu_f_D_K_without_override",
            "required_companion_gates": "repeatability; tap_orientation; no pressure recovery; mesh_GCI",
            "current_evidence_overlap": "no AGENT-406 PM5 row; no AGENT-409 raw tap proxy",
        },
        {
            "policy_variable": "reverse_area_fraction",
            "rule_band": "0.05 <= RAF < 0.20",
            "threshold_formula": "RAF = A(U_axial < 0) / A_total",
            "physical_interpretation": "transition/onset recirculation",
            "fit_use": "no_true_single_stream_fit",
            "validation_use": "section_effective_validation_only",
            "diagnostic_use": "recirculation_onset_and_section_effective_pressure_heat_transfer",
            "invalid_single_stream_coefficients": "Nu; f_D; K for fit labels",
            "required_companion_gates": "label_as_section_effective; do_not_mix_with_low_RAF_fit_rows",
            "current_evidence_overlap": "no AGENT-406 PM5 row; no AGENT-409 raw tap proxy",
        },
        {
            "policy_variable": "reverse_area_fraction",
            "rule_band": "RAF >= 0.20",
            "threshold_formula": "RAF = A(U_axial < 0) / A_total",
            "physical_interpretation": "material recirculation; no unique single upstream stream",
            "fit_use": "not_fit_admissible_for_true_Nu_f_D_or_component_K",
            "validation_use": "diagnostic_validation_only_for_section_effective_quantities",
            "diagnostic_use": "Nu_section_effective_upcomer_diagnostic; apparent_pressure_gradient; K_section_effective_recirculating_diagnostic",
            "invalid_single_stream_coefficients": "Nu; f_D; K",
            "required_companion_gates": "preserve_diagnostic_label; no promotion without new low-recirculation evidence",
            "current_evidence_overlap": "all AGENT-406 PM5 rows and all AGENT-409 raw tap proxies",
        },
        {
            "policy_variable": "reverse_mass_fraction",
            "rule_band": "0 <= RMF < 0.01",
            "threshold_formula": "RMF = abs(sum(rho U_axial dA for U_axial < 0)) / sum(abs(rho U_axial) dA)",
            "physical_interpretation": "mass transport is effectively single direction",
            "fit_use": "fit_candidate_if_other_gates_pass",
            "validation_use": "validation_candidate",
            "diagnostic_use": "not_required_by_recirculation_policy",
            "invalid_single_stream_coefficients": "none_by_recirculation_policy",
            "required_companion_gates": "same windows/source_paths as thermal and hydraulic extraction",
            "current_evidence_overlap": "no AGENT-406 PM5 row",
        },
        {
            "policy_variable": "reverse_mass_fraction",
            "rule_band": "0.01 <= RMF < 0.05",
            "threshold_formula": "RMF = abs(reverse_mass_flux) / total_absolute_mass_flux",
            "physical_interpretation": "weak reverse mass transport",
            "fit_use": "validation_only_by_default; fit only after explicit uncertainty override",
            "validation_use": "bounded_validation_candidate",
            "diagnostic_use": "onset_diagnostic",
            "invalid_single_stream_coefficients": "do_not_fit_true_Nu_f_D_K_without_override",
            "required_companion_gates": "repeatability; time-window stability; mesh_GCI",
            "current_evidence_overlap": "no AGENT-406 PM5 row",
        },
        {
            "policy_variable": "reverse_mass_fraction",
            "rule_band": "0.05 <= RMF < 0.20",
            "threshold_formula": "RMF = abs(reverse_mass_flux) / total_absolute_mass_flux",
            "physical_interpretation": "transition recirculation with material mass exchange",
            "fit_use": "no_true_single_stream_fit",
            "validation_use": "section_effective_validation_only",
            "diagnostic_use": "recirculation_onset_and_mixing_diagnostic",
            "invalid_single_stream_coefficients": "Nu; f_D; K for fit labels",
            "required_companion_gates": "label_as_section_effective",
            "current_evidence_overlap": "no AGENT-406 PM5 row",
        },
        {
            "policy_variable": "reverse_mass_fraction",
            "rule_band": "RMF >= 0.20",
            "threshold_formula": "RMF = abs(reverse_mass_flux) / total_absolute_mass_flux",
            "physical_interpretation": "material recirculating mass stream",
            "fit_use": "not_fit_admissible_for_true_Nu_f_D_or_component_K",
            "validation_use": "diagnostic_validation_only_for_section_effective_quantities",
            "diagnostic_use": "branch_mixing; upcomer_onset; section_effective_heat_pressure",
            "invalid_single_stream_coefficients": "Nu; f_D; K",
            "required_companion_gates": "no hidden absorption into internal_Nu_or_global_K",
            "current_evidence_overlap": "all AGENT-406 PM5 rows are near RMF=0.5",
        },
        {
            "policy_variable": "secondary_velocity_fraction",
            "rule_band": "SVF < 0.05",
            "threshold_formula": "SVF = ||U_secondary||_area_mean / ||U||_area_mean",
            "physical_interpretation": "quasi-1D secondary motion if reverse flow is also small",
            "fit_use": "fit_candidate_only_when_RAF_RMF_low",
            "validation_use": "validation_candidate",
            "diagnostic_use": "secondary_flow_monitor",
            "invalid_single_stream_coefficients": "none_if_RAF_RMF_and_other_gates_pass",
            "required_companion_gates": "RAF/RMF low; mesh_GCI; stable pressure/thermal signs",
            "current_evidence_overlap": "AGENT-406 mid-plane SVF is low, but RAF/RMF remain material",
        },
        {
            "policy_variable": "secondary_velocity_fraction",
            "rule_band": "0.05 <= SVF < 0.20",
            "threshold_formula": "SVF = ||U_secondary||_area_mean / ||U||_area_mean",
            "physical_interpretation": "secondary motion can bias 1D coefficient interpretation",
            "fit_use": "validation_only_or_diagnostic_if_recirculating",
            "validation_use": "bounded_validation_candidate",
            "diagnostic_use": "onset_mixing_diagnostic",
            "invalid_single_stream_coefficients": "true_fit_labels_invalid_when_combined_with_material_RAF_or_RMF",
            "required_companion_gates": "tap_orientation; plane_location_review",
            "current_evidence_overlap": "AGENT-406 inlet rows",
        },
        {
            "policy_variable": "secondary_velocity_fraction",
            "rule_band": "SVF >= 0.20",
            "threshold_formula": "SVF = ||U_secondary||_area_mean / ||U||_area_mean",
            "physical_interpretation": "multidimensional mixing-dominated section",
            "fit_use": "not_fit_admissible_for_true_single_stream_coefficients",
            "validation_use": "diagnostic_validation_only",
            "diagnostic_use": "section_effective_or_onset_diagnostic",
            "invalid_single_stream_coefficients": "Nu; f_D; K if reported as true 1D coefficients",
            "required_companion_gates": "use section-effective labels",
            "current_evidence_overlap": "AGENT-406 outlet rows",
        },
        {
            "policy_variable": "Richardson_number",
            "rule_band": "Ri < 0.1",
            "threshold_formula": "Ri = Gr / Re^2 using same property lane/window as extraction",
            "physical_interpretation": "forced-convection-dominant",
            "fit_use": "forced/mixed closure fit candidate if recirculation gates pass",
            "validation_use": "validation_candidate",
            "diagnostic_use": "regime_marker",
            "invalid_single_stream_coefficients": "none_by_Ri_alone",
            "required_companion_gates": "property lane fixed separately from friction/thermal fitting",
            "current_evidence_overlap": "no AGENT-406 PM5 row",
        },
        {
            "policy_variable": "Richardson_number",
            "rule_band": "0.1 <= Ri < 1",
            "threshold_formula": "Ri = Gr / Re^2",
            "physical_interpretation": "mixed convection transition",
            "fit_use": "mixed-convection-labeled validation/fit only if no material recirculation",
            "validation_use": "mixed_convection_validation",
            "diagnostic_use": "regime_marker",
            "invalid_single_stream_coefficients": "pure_forced_closure_label_invalid",
            "required_companion_gates": "include Ri/Gr/Ra metadata",
            "current_evidence_overlap": "no AGENT-406 PM5 row",
        },
        {
            "policy_variable": "Richardson_number",
            "rule_band": "Ri >= 1",
            "threshold_formula": "Ri = Gr / Re^2",
            "physical_interpretation": "buoyancy/mixed-convection strong",
            "fit_use": "no pure forced single-stream fit; mixed section-effective diagnostics unless RAF/RMF low and admitted",
            "validation_use": "mixed_convection_diagnostic_validation",
            "diagnostic_use": "upcomer_recirculation_and_buoyancy_onset",
            "invalid_single_stream_coefficients": "pure_forced_Nu_f_D_K_labels_invalid",
            "required_companion_gates": "do_not_absorb_boundary_or_buoyancy_residual_into_internal_Nu",
            "current_evidence_overlap": "all AGENT-406 PM5 rows",
        },
        {
            "policy_variable": "wall_bulk_delta_T",
            "rule_band": "abs(T_wall - T_bulk) < 0.5 K",
            "threshold_formula": "h_proxy = q_wall'' / (T_wall - T_bulk)",
            "physical_interpretation": "singular or noise-dominated heat-transfer denominator",
            "fit_use": "not_fit_admissible",
            "validation_use": "not_validation_admissible_for_Nu",
            "diagnostic_use": "thermal_sign_and_storage_review",
            "invalid_single_stream_coefficients": "Nu",
            "required_companion_gates": "wallHeatFlux; heat-balance residual; sign convention",
            "current_evidence_overlap": "no AGENT-406 PM5 row is small-deltaT, but sign issues remain",
        },
        {
            "policy_variable": "wall_bulk_delta_T",
            "rule_band": "h_proxy <= 0 under declared sign convention",
            "threshold_formula": "h_proxy = q_wall'' / (T_wall - T_bulk)",
            "physical_interpretation": "wall heat-flux and wall-bulk temperature signs are not interpretable as positive internal h",
            "fit_use": "not_fit_admissible_for_true_Nu",
            "validation_use": "diagnostic_sign_review_only",
            "diagnostic_use": "Nu_section_effective_upcomer_diagnostic_after_sign_metadata",
            "invalid_single_stream_coefficients": "Nu",
            "required_companion_gates": "same extraction window as thermal admission; radiation already included in CFD wallHeatFlux",
            "current_evidence_overlap": "AGENT-406 PM5 rows require section-effective/sign treatment",
        },
        {
            "policy_variable": "pressure_tap_location_orientation",
            "rule_band": "known upstream/downstream taps, static pressure definition, straight length known, no material recirculation",
            "threshold_formula": "Delta_p_component = p_upstream - p_downstream - Delta_p_straight",
            "physical_interpretation": "component K can be physically separated",
            "fit_use": "true_K_fit_candidate_if_mesh_GCI_and_dynamic_pressure_pass",
            "validation_use": "component_K_validation_candidate",
            "diagnostic_use": "pressure_residual_audit",
            "invalid_single_stream_coefficients": "none_if_all_gates_pass",
            "required_companion_gates": "tap geometry; static pressure; q_ref; straight/distributed loss subtraction; mesh_GCI",
            "current_evidence_overlap": "not yet satisfied by AGENT-409 raw two-tap rows",
        },
        {
            "policy_variable": "pressure_tap_location_orientation",
            "rule_band": "report-both-signs, reduced p_rgh proxy, or material recirculation at taps",
            "threshold_formula": "Delta_p_rgh_proxy = p_rgh(face_a) - p_rgh(face_b)",
            "physical_interpretation": "no universal single upstream stream or static component-loss definition",
            "fit_use": "not_fit_admissible_for_true_K",
            "validation_use": "diagnostic_validation_only",
            "diagnostic_use": "K_section_effective_recirculating_diagnostic; apparent pressure gradient",
            "invalid_single_stream_coefficients": "K; f_D when reported as true component/distributed coefficients",
            "required_companion_gates": "separate reduced-pressure diagnostic from final hydraulic attribution",
            "current_evidence_overlap": "all AGENT-409 raw two-tap rows",
        },
    ]


def coefficient_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "coefficient_label": "Nu",
            "definition": "true single-stream internal Nusselt number, Nu = h D_h / k",
            "required_inputs": "admitted wallHeatFlux, wall temperature, bulk temperature, D_h, k, property lane, heat-balance residual",
            "admission_rule": "RAF<0.01 and RMF<0.01 by default; positive interpretable h_proxy; no boundary/storage/radiation residual hidden in h",
            "allowed_use": "fit_or_validation_after_thermal_mesh_boundary_gates",
            "excluded_use": "material recirculation; sign-ambiguous h; missing heat-balance; fitting boundary residuals into internal Nu",
            "current_status": "zero fit-admissible rows; AGENT-406 rows not true Nu",
        },
        {
            "coefficient_label": "Nu_section_effective_upcomer_diagnostic",
            "definition": "section-effective heat-transfer diagnostic from local wall band and matched plane under recirculation",
            "required_inputs": "wallHeatFlux, wall T, bulk T, RAF/RMF/SVF/Ri metadata, extraction window/source path",
            "admission_rule": "allowed when fields exist but recirculation/sign gates prevent true Nu",
            "allowed_use": "diagnostic or bounded validation of regime/onset; paper diagnostic table with explicit label",
            "excluded_use": "single-stream closure fitting; universal Nu correlation; absorbing heater/cooler/passive/radiation residuals",
            "current_status": "available as diagnostic for AGENT-406 PM5 rows after sign metadata review",
        },
        {
            "coefficient_label": "f_D",
            "definition": "true Darcy friction factor for a single stream, f_D = (Delta_p/L) * 2 D_h / (rho V^2)",
            "required_inputs": "static pressure gradient, L, D_h, rho, V, monotone stream direction, straight/distributed section, mesh/GCI",
            "admission_rule": "RAF<0.01 and RMF<0.01; no pressure recovery ambiguity; pressure definition admitted",
            "allowed_use": "hydraulic closure fit or validation after mesh/GCI and sign gates",
            "excluded_use": "recirculating PM5/F6 rows; p_rgh proxy rows; nonmonotone/oscillatory GCI rows",
            "current_status": "not unlocked by AGENT-406/409; closure-QOI rows still blocked",
        },
        {
            "coefficient_label": "apparent_pressure_gradient_section_effective_diagnostic",
            "definition": "observed pressure-gradient or two-plane pressure change retained as a diagnostic, not a Darcy coefficient",
            "required_inputs": "pressure definition, tap labels, orientation note, RAF/RMF/SVF where available",
            "admission_rule": "allowed when pressure exists but true f_D/K gates fail",
            "allowed_use": "hydraulic residual triage; onset review; qualitative comparison",
            "excluded_use": "fit as true distributed friction; final component attribution without straight-loss separation",
            "current_status": "appropriate label for AGENT-409 raw two-tap pressure proxy",
        },
        {
            "coefficient_label": "K",
            "definition": "true localized component loss coefficient, K = Delta_p_local / q_ref",
            "required_inputs": "static p_upstream/p_downstream, q_ref, straight loss subtraction, tap geometry, no material reverse at taps, mesh/GCI",
            "admission_rule": "known upstream/downstream under monotone stream and Delta_p_local isolated from distributed/reset/development terms",
            "allowed_use": "component-K fit or validation after final hydraulic gate",
            "excluded_use": "AGENT-409 raw two-tap rows as currently staged; report-both-signs pressure proxy; recirculating sections",
            "current_status": "still blocked for final hydraulic attribution",
        },
        {
            "coefficient_label": "K_section_effective_recirculating_diagnostic",
            "definition": "section-effective pressure-loss diagnostic across a recirculating/two-tap section",
            "required_inputs": "two-tap pressure proxy or static pressure, tap labels, reverse-flow metrics, pressure-definition metadata",
            "admission_rule": "allowed when true K is invalid but pressure evidence is useful diagnostically",
            "allowed_use": "residual triage; PM5/F6 onset review; development/reset separation hypothesis",
            "excluded_use": "component-K fit; final residual closure; training a universal local loss coefficient",
            "current_status": "correct label for AGENT-409 raw two-tap rows",
        },
        {
            "coefficient_label": "invalid_coefficient_label",
            "definition": "any true Nu, f_D, or K label applied outside its admission envelope",
            "required_inputs": "recirculation, sign, pressure, and mesh metadata needed to identify invalidity",
            "admission_rule": "invalid when RAF>=0.20 or RMF>=0.20, SVF>=0.20 with material mixing, h_proxy<=0, p_rgh proxy lacks conversion, or straight loss is not separated",
            "allowed_use": "none; must relabel as diagnostic or reject",
            "excluded_use": "fit; validation; final forward-v1 evidence; final hydraulic residual evidence",
            "current_status": "guards against promoting current AGENT-406/409 diagnostic rows",
        },
    ]


def band_fraction(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < 0.01:
        return "single_stream_candidate"
    if value < 0.05:
        return "weak_reverse_validation_only"
    if value < 0.20:
        return "transition_section_effective"
    return "material_recirculation_diagnostic_only"


def band_secondary(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < 0.05:
        return "low_secondary_if_RAF_RMF_low"
    if value < 0.20:
        return "secondary_caution_validation_only"
    return "multidimensional_mixing_diagnostic_only"


def band_ri(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < 0.1:
        return "forced_dominant"
    if value < 1.0:
        return "mixed_transition"
    return "strong_mixed_convection"


def pm5_classification_rows(metrics: list[dict[str, str]], f6_rows: list[dict[str, str]], nu_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    f6_by_key = {(row["case_key"], row["plane_location"]): row for row in f6_rows}
    nu_by_key = {(row["case_key"], row["plane_location"]): row for row in nu_rows}
    rows: list[dict[str, Any]] = []
    for row in metrics:
        key = (row["case_key"], row["plane_location"])
        raf = safe_float(row.get("reverse_area_fraction"))
        rmf = safe_float(row.get("reverse_mass_fraction"))
        svf = safe_float(row.get("secondary_velocity_fraction"))
        ri = safe_float(row.get("Ri"))
        delta_t = safe_float(row.get("delta_T_wall_bulk_K"))
        q_wall = safe_float(row.get("wallHeatFlux_W_m2"))
        h_proxy = q_wall / delta_t if q_wall is not None and delta_t not in (None, 0.0) else None
        material_recirc = (raf is not None and raf >= 0.20) or (rmf is not None and rmf >= 0.20)
        strong_secondary = svf is not None and svf >= 0.20
        f6 = f6_by_key.get(key, {})
        nu = nu_by_key.get(key, {})
        rows.append(
            {
                "evidence_id": f"{row['case_key']}:{row['plane_location']}:{row.get('span', '')}",
                "evidence_type": "AGENT-406_PM5_matched_plane_wall_band",
                "case_key": row["case_key"],
                "split_role": row.get("case_role", ""),
                "location": row["plane_location"],
                "representative_time_s": row.get("representative_time_s", ""),
                "reverse_area_fraction": fmt(raf),
                "reverse_area_band": band_fraction(raf),
                "reverse_mass_fraction": fmt(rmf),
                "reverse_mass_band": band_fraction(rmf),
                "secondary_velocity_fraction": fmt(svf),
                "secondary_band": band_secondary(svf),
                "Ri": fmt(ri),
                "mixed_convection_band": band_ri(ri),
                "wall_bulk_delta_T_K": fmt(delta_t),
                "wallHeatFlux_W_m2": fmt(q_wall),
                "h_proxy_W_m2K": fmt(h_proxy),
                "pressure_tap_policy": "not_a_two_tap_component_K_row",
                "valid_labels": "Nu_section_effective_upcomer_diagnostic; apparent_pressure_or_onset_diagnostic",
                "invalid_single_stream_labels": "Nu; f_D; K" if material_recirc or strong_secondary else "none_by_recirculation_policy",
                "use_class": "diagnostic_only",
                "fit_admissible": "no",
                "validation_admissible": "diagnostic_validation_only",
                "current_gate_status": f"{f6.get('f6_review_status', '')}; {nu.get('internal_nu_review_status', '')}".strip("; "),
                "reason": "material reverse area/mass invalidates true single-stream labels; use section-effective diagnostic only",
                "source_path": rel(AGENT406 / "resampled_pm5_matched_plane_metrics.csv"),
            }
        )
    return rows


def raw_two_tap_classification_rows(raw_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        lower = safe_float(row.get("lower_reverse_area_fraction_proxy"))
        upper = safe_float(row.get("upper_reverse_area_fraction_proxy"))
        max_raf = max([value for value in [lower, upper] if value is not None], default=None)
        rows.append(
            {
                "evidence_id": f"{row['case_id']}:{row['tap_lower_label']}->{row['tap_upper_label']}",
                "evidence_type": "AGENT-409_raw_two_tap_test_section_complex",
                "case_key": row.get("case_key", ""),
                "split_role": "hydraulic_raw_tap_diagnostic",
                "location": "test_section_complex",
                "representative_time_s": row.get("representative_time_s", ""),
                "reverse_area_fraction": fmt(max_raf),
                "reverse_area_band": band_fraction(max_raf),
                "reverse_mass_fraction": "",
                "reverse_mass_band": "not_extracted_for_raw_two_tap",
                "secondary_velocity_fraction": "",
                "secondary_band": "not_extracted_for_raw_two_tap",
                "Ri": "",
                "mixed_convection_band": "not_extracted_for_raw_two_tap",
                "wall_bulk_delta_T_K": "",
                "wallHeatFlux_W_m2": "",
                "h_proxy_W_m2K": "",
                "pressure_tap_policy": "report_both_signs_reduced_p_rgh_proxy_no_universal_upstream_downstream",
                "valid_labels": "K_section_effective_recirculating_diagnostic; apparent_pressure_gradient_section_effective_diagnostic",
                "invalid_single_stream_labels": "K; f_D",
                "use_class": "diagnostic_only",
                "fit_admissible": "no",
                "validation_admissible": "diagnostic_validation_only",
                "current_gate_status": row.get("admission_status", ""),
                "reason": "coarse-only p_rgh proxy with material reverse-area proxies; no true component-K admission",
                "source_path": rel(AGENT409 / "raw_two_tap_test_section_complex.csv"),
            }
        )
    return rows


def final_forward_unblock_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "runtime_input_contract",
            "current_state": "partly_open_but_not_terminal",
            "missing_evidence": "final scorecard proving setup-only inputs for every forward-v1 lane",
            "artifact_or_calculation_needed": "runtime-input audit plus forward scorecard for selected setup-only HX/boundary variant",
            "executor": "forward-predictive/Fluid API agent",
            "admission_criterion": "zero CFD-duty runtime cheats: no realized CFD cooler duty, mdot, wallHeatFlux, validation temperatures, or validation pressures as model inputs",
            "failure_mode": "forward-v1 remains diagnostic replay or runtime-cheat candidate",
        },
        {
            "gate_id": "cooler_HX_setup_only_score",
            "current_state": "preferred_candidate_exists_not_final",
            "missing_evidence": "terminal Salt2 train / Salt3 validation / Salt4 holdout score using setup-only cooler/HX inputs",
            "artifact_or_calculation_needed": "setup_only_hx_boundary_scorecard.csv with fit scalar frozen after Salt2",
            "executor": "boundary/HX predictive model agent plus Fluid run agent",
            "admission_criterion": "validation and holdout errors meet documented tolerance without refit and without imposed cooler replay",
            "failure_mode": "promote only as diagnostic/predictive candidate; no final forward-v1",
        },
        {
            "gate_id": "heater_fraction_boundary",
            "current_state": "candidate_model_lane_defined_not_final",
            "missing_evidence": "realized heater fraction fitted from training only and checked against validation/holdout without absorbing cooler/wall/radiation residuals",
            "artifact_or_calculation_needed": "heater_fraction_scorecard.csv with residual ownership ledger",
            "executor": "boundary model agent",
            "admission_criterion": "heater fraction is setup/legal fitted parameter, not a CFD-duty replay term; residuals assigned to cooler, wall loss, storage, radiation metadata, or branch mixing",
            "failure_mode": "internal Nu or global K absorbs thermal boundary residuals",
        },
        {
            "gate_id": "recirculation_policy_gate",
            "current_state": "new_AGENT419_policy_explicit; current_AGENT406_409_rows_diagnostic_only",
            "missing_evidence": "low-recirculation admitted rows or explicit diagnostic-only forward lane",
            "artifact_or_calculation_needed": "current_evidence_recirculation_classification.csv plus any future low-RAF/RMF extraction",
            "executor": "hydraulic/internal-Nu extraction agents",
            "admission_criterion": "fit rows have RAF<0.01 and RMF<0.01 by default; recirculating rows use section-effective diagnostic labels only",
            "failure_mode": "single-stream Nu, f_D, or K labels silently fitted to recirculating PM5/tap evidence",
        },
        {
            "gate_id": "internal_Nu_thermal_admission",
            "current_state": "closed_zero_fit_admissible_rows",
            "missing_evidence": "matched wall/plane rows with positive interpretable h, low reverse/secondary flow, accepted heat-balance residual, mesh/GCI admitted triplet",
            "artifact_or_calculation_needed": "thermal_admission_internal_nu_refresh.csv using same windows/source paths as boundary metrics",
            "executor": "thermal/internal-Nu agent",
            "admission_criterion": "true Nu rows pass sign, recirculation, heat-balance, property-lane, and mesh/GCI gates",
            "failure_mode": "section-effective PM5 diagnostics are misused as true Nu",
        },
        {
            "gate_id": "hydraulic_F6_or_pressure_closure",
            "current_state": "blocked_for_fit; PM5 rows review_ready_diagnostic_only",
            "missing_evidence": "non-recirculating pressure/F6 rows or accepted section-effective diagnostic lane that does not train true f_D/K",
            "artifact_or_calculation_needed": "f6_pressure_scorecard.csv with RAF/RMF/SVF policy columns",
            "executor": "hydraulic postprocess agent",
            "admission_criterion": "pressure residual improvement on validation/holdout with no global K multiplier and no recirculating fit rows",
            "failure_mode": "hydraulic residual remains unassigned or fitted to invalid coefficients",
        },
        {
            "gate_id": "mesh_GCI_UQ",
            "current_state": "blocked_for_publication_and_final_fit",
            "missing_evidence": "mesh family triplets with monotone/convergent pressure and thermal closure QoIs",
            "artifact_or_calculation_needed": "closure_qoi_mesh_gci_admission.csv and uncertainty budget",
            "executor": "mesh/GCI agent",
            "admission_criterion": "admitted triplets or documented exclusion; uncertainty propagated into final forward-v1 score",
            "failure_mode": "coarse-only diagnostics cannot become final forward-v1 evidence",
        },
        {
            "gate_id": "final_scorecard_and_holdout_freeze",
            "current_state": "blocked_no_go_final_forward_v1_not_admitted",
            "missing_evidence": "single terminal scorecard combining setup-only thermal boundary, admitted hydraulic terms, sensor split, mesh/UQ, and recirculation labels",
            "artifact_or_calculation_needed": "final_forward_v1_scorecard_gate.csv and README",
            "executor": "lead closure/forward-v1 coordinator",
            "admission_criterion": "train/validation/holdout split preserved; no diagnostic rows promoted to fit; all coefficients named by policy",
            "failure_mode": "forward-v1 remains candidate package, not admissible final model",
        },
    ]


def final_hydraulic_unblock_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "raw_test_section_pressure_loss_admission",
            "current_state": "diagnostic_raw_two_tap_rows_landed_not_fit_admitted",
            "missing_evidence": "static pressure definition or admitted p_rgh conversion, upstream/downstream orientation, low-recirculation or diagnostic-only label, mesh/GCI",
            "artifact_or_calculation_needed": "raw_two_tap_admission_package.csv",
            "observed_term": "Delta_p_observed = p_upstream - p_downstream over admitted taps",
            "model_term": "not yet admitted",
            "admission_criterion": "pressure taps are geometrically documented and pressure variable is admissible for component loss",
            "failure_mode": "AGENT-409 rows remain K_section_effective_recirculating_diagnostic only",
        },
        {
            "gate_id": "straight_distributed_loss_separation",
            "current_state": "blocked",
            "missing_evidence": "centerline length, hydraulic diameter, density/velocity window, straight-section pressure gradient, mesh/GCI",
            "artifact_or_calculation_needed": "straight_loss_subtraction_ledger.csv",
            "observed_term": "Delta_p_two_tap",
            "model_term": "Delta_p_straight = f_D (L/D_h) q_ref",
            "admission_criterion": "straight/distributed contribution is independently admitted before component K is inferred",
            "failure_mode": "localized K absorbs distributed/reset/development pressure loss",
        },
        {
            "gate_id": "localized_K_vs_reset_development_K",
            "current_state": "diagnostic_separation_supported_not_fitted",
            "missing_evidence": "raw pressure evidence identifying which pressure charge belongs to local component versus reset/development after turns or expansions",
            "artifact_or_calculation_needed": "localized_vs_reset_development_k_scorecard.csv",
            "observed_term": "Delta_p_local_candidate = Delta_p_two_tap - Delta_p_straight",
            "model_term": "Delta_p_named = (K_localized + K_reset_development) q_ref",
            "admission_criterion": "K terms separately improve validation residuals and remain physically located",
            "failure_mode": "one fitted K becomes a catch-all for geometry, development, and recirculation",
        },
        {
            "gate_id": "PM5_F6_pressure_onset_review",
            "current_state": "unlocked_for_review_not_admitted; all PM5 rows diagnostic recirculating",
            "missing_evidence": "accepted F6/onset scorecard using recirculation policy and pressure residual target",
            "artifact_or_calculation_needed": "f6_review_protocol_result.csv",
            "observed_term": "pressure/onset indicators with RAF, RMF, SVF, Ri",
            "model_term": "bounded F6/Re/phi perturbation or section-effective onset diagnostic",
            "admission_criterion": "no PM5 row with material recirculation is used to fit true f_D or K",
            "failure_mode": "pressure-onset evidence remains diagnostic and cannot close final residual",
        },
        {
            "gate_id": "mesh_GCI_for_hydraulic_QoIs",
            "current_state": "blocked_non_monotone_or_missing_triplets",
            "missing_evidence": "mesh family pressure QoIs with monotone convergence or documented exclusion",
            "artifact_or_calculation_needed": "hydraulic_closure_qoi_mesh_gci.csv",
            "observed_term": "Delta_p and derived f_D/K over admitted mesh family",
            "model_term": "GCI uncertainty propagated to residual attribution",
            "admission_criterion": "publication-ready hydraulic QoI has GCI/UQ or is explicitly diagnostic",
            "failure_mode": "coarse-only rows remain prefinal diagnostics",
        },
        {
            "gate_id": "residual_decomposition_formula",
            "current_state": "formula_defined_inputs_missing",
            "missing_evidence": "all observed/model terms admitted on same window/source-path policy",
            "artifact_or_calculation_needed": "final_hydraulic_residual_decomposition.csv",
            "observed_term": "Delta_p_residual = Delta_p_observed - Delta_p_model",
            "model_term": "Delta_p_model = Delta_p_straight + Delta_p_localized_K + Delta_p_reset_development_K + Delta_p_recirculation_onset + Delta_p_buoyancy_density_gradient + Delta_p_acceleration_if_applicable",
            "admission_criterion": "each term is independently sourced, no double counting, uncertainty carried through",
            "failure_mode": "final hydraulic residual attribution remains blocked and qualitative",
        },
        {
            "gate_id": "final_hydraulic_attribution_freeze",
            "current_state": "blocked_not_final",
            "missing_evidence": "single frozen scorecard citing admitted pressure, K/f_D labels, PM5/F6 onset state, and mesh/UQ",
            "artifact_or_calculation_needed": "final_hydraulic_residual_attribution_v2.csv",
            "observed_term": "admitted Delta_p_observed from raw/static pressure gates",
            "model_term": "sum of admitted hydraulic model components only",
            "admission_criterion": "true coefficients and section-effective diagnostics are never mixed in one fit column",
            "failure_mode": "residual is still assigned to invalid or diagnostic-only evidence",
        },
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [
        AGENT409 / "README.md",
        AGENT409 / "raw_two_tap_test_section_complex.csv",
        AGENT409 / "closure_qoi_failed_gate_matrix.csv",
        AGENT409 / "internal_nu_reopen_status.csv",
        AGENT406 / "resampled_pm5_matched_plane_metrics.csv",
        AGENT406 / "summary.json",
        AGENT407 / "README.md",
        AGENT407 / "row_admission_ledger.csv",
        AGENT414 / "f6_pm5_row_readiness.csv",
        AGENT414 / "internal_nu_pm5_row_readiness.csv",
        AGENT405 / "final_hydraulic_residual_attribution.csv",
    ]
    return [
        {
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "use_in_agent419": "read_only_input",
        }
        for path in paths
    ]


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""# Recirculation Policy + Forward-v1 / Hydraulic Residual Unblock Plan

Date: {DATE}
Task: {TASK}

## Bottom Line

Final forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted`.
The current AGENT-406 PM5 rows and AGENT-409 raw two-tap rows do not unlock
true single-stream `Nu`, `f_D`, or `K`. They are useful, but only as
section-effective diagnostics because reverse area/mass fractions are material
and the pressure rows are reduced-pressure, report-both-signs proxies without a
final component-loss admission gate.

## Outputs

- `recirculation_policy_decision_table.csv` ({summary["recirculation_policy_rows"]} rows)
- `coefficient_label_admission_policy.csv` ({summary["coefficient_policy_rows"]} rows)
- `current_evidence_recirculation_classification.csv` ({summary["evidence_classification_rows"]} rows)
- `final_forward_v1_unblock_chain.csv` ({summary["forward_unblock_rows"]} rows)
- `final_hydraulic_residual_unblock_chain.csv` ({summary["hydraulic_unblock_rows"]} rows)
- `source_manifest.csv`
- `summary.json`

## Admission Rules

Reverse-flow fractions are now admission rules, not caveats:

- `RAF = A(U_axial < 0) / A_total`.
- `RMF = |sum(rho U_axial dA for U_axial < 0)| / sum(|rho U_axial| dA)`.
- `SVF = area-mean ||U_secondary|| / area-mean ||U||`.
- `Ri = Gr / Re^2`, using the same property lane and extraction window as the
  row being admitted.
- `h_proxy = q_wall'' / (T_wall - T_bulk)`.

Default fit admission for true single-stream `Nu`, `f_D`, or component `K`
requires `RAF < 0.01` and `RMF < 0.01`, plus the appropriate sign, pressure,
boundary, mesh/GCI, and source-path gates. Rows with `RAF >= 0.20` or
`RMF >= 0.20` are material recirculation rows and must be labeled
section-effective or diagnostic-only. Rows in the transition band
`0.05 <= RAF/RMF < 0.20` cannot fit true single-stream coefficients.

Thermal residuals must not be hidden in internal Nu. Heater fraction, cooler/HX
removal, passive wall/external convection, storage, branch mixing, and radiation
metadata remain separate residual owners. CFD `wallHeatFlux` from
`rcExternalTemperature` already includes radiative exchange; no separate `qr`
export is assumed here.

Hydraulic residual decomposition is:

`Delta_p_residual = Delta_p_observed - Delta_p_model`

with:

`Delta_p_model = Delta_p_straight + Delta_p_localized_K + Delta_p_reset_development_K + Delta_p_recirculation_onset + Delta_p_buoyancy_density_gradient + Delta_p_acceleration_if_applicable`

and:

`Delta_p_straight = f_D (L / D_h) q_ref`

`K_local = Delta_p_local / q_ref`

where `Delta_p_local` is only admissible after straight/distributed loss has
been subtracted and the taps have admitted pressure definition/orientation.

## Current Evidence Classification

AGENT-406 contributes {summary["pm5_rows"]} PM5 rows. All are diagnostic-only
under this policy. They have useful wall-band and matched-plane fields,
including `rho/Re/Pr/Ri/Gr/Ra`, but material reverse mass/area and sign/section
semantics prevent true single-stream `Nu`, `f_D`, or `K` fitting.

AGENT-409 contributes {summary["raw_two_tap_rows"]} raw two-tap rows. They are
diagnostic pressure evidence only: coarse, reduced `p_rgh` proxy rows with
report-both-signs orientation and material reverse-area proxies. The valid label
is `K_section_effective_recirculating_diagnostic` or apparent pressure-gradient
diagnostic, not true component `K`.

## Shortest Executable Path

1. Run the setup-only HX/cooler scorecard using the Fluid setup boundary hook:
   Salt2 fit, Salt3 validation, Salt4 holdout, with the fitted scalar frozen
   after training.
2. Produce a raw pressure admission package that converts or replaces the
   reduced `p_rgh` proxy with an admitted static pressure definition, fixes tap
   upstream/downstream orientation, subtracts straight loss, and carries mesh/GCI.
3. Refresh PM5/F6 pressure-onset review using this policy: current PM5 rows may
   support onset diagnostics, but they cannot train true `f_D` or `K`.
4. Keep internal-Nu closed to fitting until a row has wallHeatFlux, interpretable
   positive `h_proxy`, low RAF/RMF, accepted heat-balance residual, and mesh/GCI.
5. Freeze a final forward-v1 scorecard only after the thermal boundary model,
   hydraulic attribution, mesh/UQ, and sensor split all use the same
   validation/holdout discipline and coefficient-label policy.

## Guardrails

- Native CFD solver outputs were not mutated.
- External `../cfd-modeling-tools` was not edited.
- Staged/repaired/smoke outputs remain diagnostic until an explicit admission
  gate admits them.
- Current recirculating evidence does not unlock final forward-v1 or final
  hydraulic residual attribution.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def build() -> dict[str, Any]:
    metrics = read_csv(AGENT406 / "resampled_pm5_matched_plane_metrics.csv")
    raw_two_tap = read_csv(AGENT409 / "raw_two_tap_test_section_complex.csv")
    f6_rows = read_csv(AGENT414 / "f6_pm5_row_readiness.csv")
    nu_rows = read_csv(AGENT414 / "internal_nu_pm5_row_readiness.csv")
    closure_failed = read_csv(AGENT409 / "closure_qoi_failed_gate_matrix.csv")
    forward_ledger = read_csv(AGENT407 / "row_admission_ledger.csv")

    policy = recirculation_policy_rows()
    coeff_policy = coefficient_policy_rows()
    evidence = pm5_classification_rows(metrics, f6_rows, nu_rows) + raw_two_tap_classification_rows(raw_two_tap)
    forward = final_forward_unblock_rows()
    hydraulic = final_hydraulic_unblock_rows()

    counts = {
        "pm5_rows": len(metrics),
        "raw_two_tap_rows": len(raw_two_tap),
        "recirculation_policy_rows": write_csv(
            OUT / "recirculation_policy_decision_table.csv",
            policy,
            [
                "policy_variable",
                "rule_band",
                "threshold_formula",
                "physical_interpretation",
                "fit_use",
                "validation_use",
                "diagnostic_use",
                "invalid_single_stream_coefficients",
                "required_companion_gates",
                "current_evidence_overlap",
            ],
        ),
        "coefficient_policy_rows": write_csv(
            OUT / "coefficient_label_admission_policy.csv",
            coeff_policy,
            [
                "coefficient_label",
                "definition",
                "required_inputs",
                "admission_rule",
                "allowed_use",
                "excluded_use",
                "current_status",
            ],
        ),
        "evidence_classification_rows": write_csv(
            OUT / "current_evidence_recirculation_classification.csv",
            evidence,
            [
                "evidence_id",
                "evidence_type",
                "case_key",
                "split_role",
                "location",
                "representative_time_s",
                "reverse_area_fraction",
                "reverse_area_band",
                "reverse_mass_fraction",
                "reverse_mass_band",
                "secondary_velocity_fraction",
                "secondary_band",
                "Ri",
                "mixed_convection_band",
                "wall_bulk_delta_T_K",
                "wallHeatFlux_W_m2",
                "h_proxy_W_m2K",
                "pressure_tap_policy",
                "valid_labels",
                "invalid_single_stream_labels",
                "use_class",
                "fit_admissible",
                "validation_admissible",
                "current_gate_status",
                "reason",
                "source_path",
            ],
        ),
        "forward_unblock_rows": write_csv(
            OUT / "final_forward_v1_unblock_chain.csv",
            forward,
            [
                "gate_id",
                "current_state",
                "missing_evidence",
                "artifact_or_calculation_needed",
                "executor",
                "admission_criterion",
                "failure_mode",
            ],
        ),
        "hydraulic_unblock_rows": write_csv(
            OUT / "final_hydraulic_residual_unblock_chain.csv",
            hydraulic,
            [
                "gate_id",
                "current_state",
                "missing_evidence",
                "artifact_or_calculation_needed",
                "observed_term",
                "model_term",
                "admission_criterion",
                "failure_mode",
            ],
        ),
        "source_manifest_rows": write_csv(
            OUT / "source_manifest.csv",
            source_manifest_rows(),
            ["source_path", "exists", "use_in_agent419"],
        ),
    }
    use_classes = Counter(row["use_class"] for row in evidence)
    fit_classes = Counter(row["fit_admissible"] for row in evidence)
    closure_gate_counts = Counter(row.get("gate_status", "") for row in closure_failed)
    forward_classes = Counter(row.get("admission_class", "") for row in forward_ledger)
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_utc": utc_now(),
        "output_dir": rel(OUT),
        **counts,
        "evidence_use_class_counts": dict(use_classes),
        "evidence_fit_admissible_counts": dict(fit_classes),
        "closure_qoi_gate_status_counts": dict(closure_gate_counts),
        "forward_ledger_admission_class_counts": dict(forward_classes),
        "final_forward_v1_state": "blocked_no_go_final_forward_v1_not_admitted",
        "final_hydraulic_residual_state": "blocked_not_final",
        "next_executable_job": "run_setup_only_HX_cooler_scorecard_then_raw_pressure_admission_package",
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
