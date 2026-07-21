#!/usr/bin/env python3
"""Build a reusable ROM/post-processing correctness validation package.

This script consumes existing post-processing outputs only. It does not run
OpenFOAM and does not edit native solver outputs. The goal is to put the current
geometry, pressure/friction, and thermal closure quantities into normalized audit
tables that future ROM model-form bakeoffs can consume.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, finite_float
from tools.common import ensure_dir, iso_timestamp, json_dump, relative_to_workspace

DEFAULT_GEOMETRY_DIR = ROOT / "work_products" / "2026-07-01_claude_mesh_centerlines"
DEFAULT_SECTION_DIR = ROOT / "work_products" / "2026-07-01_claude_section_mean_pressure"
DEFAULT_FRICTION_JSON = ROOT / "work_products" / "2026-07-01_claude_segment_friction" / "segment_friction.json"
DEFAULT_THERMAL_DIR = ROOT / "work_products" / "2026-06-30_claude_thermal_htc"
DEFAULT_WORK_DIR = ROOT / "work_products" / "2026-07-01_rom_postprocessing_correctness_validation"
DEFAULT_REPORT_DIR = ROOT / "reports" / "2026-07" / "2026-07-01" / "2026-07-01_rom_postprocessing_correctness_validation"

HEATED_OR_COOLED_SPANS = {"lower_leg", "upper_leg", "right_leg", "test_section_span"}
UPCOMER_SPANS = {"left_lower_leg", "left_upper_leg", "test_section_span"}
TAXONOMY_FIELDS = [
    "resistance_class", "physics_role", "development_state", "buoyancy_role",
    "closure_admissibility",
]
THERMAL_TAXONOMY_FIELDS = [
    "thermal_resistance_class", "rom_energy_role", "nu_admissibility",
]

GEOMETRY_FIELDS = [
    "source_id", "span", "station", "x_m", "y_m", "z_m", "tx", "ty", "tz",
    "inclination_from_horizontal_deg", "bore_m", "section_area_m2",
    "wetted_perimeter_m", "hydraulic_diameter_m", "flow_alignment",
    "is_fitting_end", "geometry_source", "quality_flag", *TAXONOMY_FIELDS,
]

PRESSURE_FIELDS = [
    "source_id", "span", "method", "n_stations_used", "segment_arc_length_m",
    "dp_signed_ds_pa_per_m", "dp_loss_ds_pa_per_m", "hydraulic_diameter_m",
    "section_mean_rho_kg_m3", "u_bulk_m_s", "reynolds_number",
    "apparent_darcy_f", "excess_loss_factor_fapp_over_flam",
    "flow_alignment_min", "raw_flags", "audit_class", "required_next_correction",
    *TAXONOMY_FIELDS,
]

THERMAL_FIELDS = [
    "source_id", "segment", "cfd_spans", "status", "q_solver_wm2",
    "qprime_solver_wm", "T_wall_k", "T_bulk_k", "delta_T_k", "htc_wm2k",
    "uaprime_wmk", "R_prime_thermal_mkw", "wetted_perimeter_m",
    "htc_times_perimeter_check_wmk", "uaprime_identity_rel_error",
    "Nu", "nu_note", "mesh", "mesh_independence", "q_sign",
    "sign_consistent_heated_wall", "audit_class", *THERMAL_TAXONOMY_FIELDS,
]

OBS_FIELDS = [
    "source_id", "case_family", "mesh_level", "time_window", "span",
    "segment_1d", "station_or_segment", "quantity", "value", "units",
    "method", "quality_flag", "valid_for_fit", "valid_for_validation", "caveat",
    *TAXONOMY_FIELDS, *THERMAL_TAXONOMY_FIELDS,
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry-dir", default=str(DEFAULT_GEOMETRY_DIR))
    parser.add_argument("--section-dir", default=str(DEFAULT_SECTION_DIR))
    parser.add_argument("--friction-json", default=str(DEFAULT_FRICTION_JSON))
    parser.add_argument("--thermal-dir", default=str(DEFAULT_THERMAL_DIR))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK_DIR))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def case_family(source_id: str) -> str:
    for token in ("salt_test_", "salt"):
        idx = source_id.find(token)
        if idx >= 0:
            rest = source_id[idx + len(token):]
            digits = "".join(ch for ch in rest if ch.isdigit())
            if digits:
                return f"Salt {digits[0]}"
    return source_id


def inclination_from_horizontal(tx: float, ty: float, tz: float) -> float:
    norm = math.sqrt(tx * tx + ty * ty + tz * tz)
    if norm <= 0.0 or not math.isfinite(norm):
        return math.nan
    return math.degrees(math.asin(min(1.0, abs(ty) / norm)))


def rel_error(a: float, b: float) -> float:
    if not math.isfinite(a) or not math.isfinite(b) or abs(a) == 0.0:
        return math.nan
    return abs(a - b) / abs(a)


def geometry_quality(station: dict[str, Any], section_station: dict[str, Any] | None) -> str:
    flags: list[str] = []
    if bool(station.get("is_fitting_end")):
        flags.append("fitting_end_exclude_from_straight_friction")
    alignment = finite_float((section_station or {}).get("flow_alignment"))
    if math.isfinite(alignment) and alignment < 0.8:
        flags.append("low_flow_alignment")
    status = (section_station or {}).get("status")
    if status and status != "sampled":
        flags.append(f"section_status_{status}")
    return ";".join(flags) if flags else "ok"


def geometry_taxonomy(station: dict[str, Any], quality_flag: str) -> dict[str, str]:
    if bool(station.get("is_fitting_end")):
        return {
            "resistance_class": "minor_loss_or_development_region",
            "physics_role": "bend_fitting_geometry_context",
            "development_state": "fitting_endpoint_redeveloping_flow",
            "buoyancy_role": "geometry_projection_context",
            "closure_admissibility": "exclude_from_straight_friction_fit",
        }
    if quality_flag != "ok":
        return {
            "resistance_class": "geometry_qc_context",
            "physics_role": "section_geometry_with_quality_caveat",
            "development_state": "uncertain_section_quality",
            "buoyancy_role": "geometry_projection_context",
            "closure_admissibility": "validation_only_until_quality_resolved",
        }
    return {
        "resistance_class": "geometry_support",
        "physics_role": "defines_area_diameter_tangent_for_closures",
        "development_state": "clean_interior_station",
        "buoyancy_role": "sets_streamwise_gravity_projection",
        "closure_admissibility": "usable_as_closure_geometry",
    }


def pressure_audit_class(row: dict[str, Any]) -> tuple[str, str]:
    span = str(row.get("span", ""))
    method = str(row.get("method", ""))
    flags = str(row.get("flags", ""))
    f_app = finite_float(row.get("apparent_darcy_f"))
    n_stations = int(finite_float(row.get("n_stations_used"), 0.0))

    if n_stations < 2:
        return ("invalid", "need_at_least_two_clean_stations")
    if method != "section_mean_total_pressure_gradient":
        return ("diagnostic_static_or_secondary", "use_total_pressure_or_buoyancy_corrected_loss")
    if "negative_f" in flags or (math.isfinite(f_app) and f_app < 0.0):
        return ("not_direct_friction", "add_variable_density_buoyancy_correction_before_fit")
    if span in HEATED_OR_COOLED_SPANS:
        return ("apparent_resistance", "verify_buoyancy_correction_before_closure_grade")
    if span in UPCOMER_SPANS:
        return ("direct_friction_candidate", "confirm_no_recirculation_for_station_subset")
    return ("direct_friction_candidate", "carry_mesh_GCI_and_time_window_uncertainty")


def pressure_taxonomy(row: dict[str, Any], audit_class: str) -> dict[str, str]:
    span = str(row.get("span", ""))
    method = str(row.get("method", ""))
    flags = str(row.get("flags", row.get("raw_flags", "")))

    if audit_class == "invalid":
        return {
            "resistance_class": "unresolved_residual",
            "physics_role": "insufficient_station_support",
            "development_state": "not_classifiable",
            "buoyancy_role": "unknown",
            "closure_admissibility": "not_admissible",
        }
    if audit_class == "diagnostic_static_or_secondary" or method != "section_mean_total_pressure_gradient":
        return {
            "resistance_class": "reversible_acceleration_area_change_diagnostic",
            "physics_role": "static_pressure_component_not_mechanical_loss",
            "development_state": "diagnostic_only",
            "buoyancy_role": "not_separated",
            "closure_admissibility": "diagnostic_only_not_fit",
        }
    if "negative_f" in flags or audit_class == "not_direct_friction":
        return {
            "resistance_class": "buoyancy_contaminated_apparent_resistance",
            "physics_role": "local_buoyancy_source_or_pressure_recovery_exceeds_wall_loss",
            "development_state": "nonisothermal_or_buoyant_segment",
            "buoyancy_role": "local_pressure_gradient_source",
            "closure_admissibility": "not_admissible_until_buoyancy_corrected",
        }
    if audit_class == "apparent_resistance":
        return {
            "resistance_class": "distributed_wall_friction_plus_buoyancy_pending",
            "physics_role": "apparent_segment_loss_before_full_decomposition",
            "development_state": "nonisothermal_segment_pending_correction",
            "buoyancy_role": "possible_local_pressure_gradient_source",
            "closure_admissibility": "provisional_validation_only",
        }
    if span in UPCOMER_SPANS:
        return {
            "resistance_class": "distributed_wall_friction_candidate",
            "physics_role": "clean_total_pressure_loss_candidate",
            "development_state": "requires_recirculation_screen",
            "buoyancy_role": "mixed_convection_screen_required",
            "closure_admissibility": "admissible_after_recirculation_and_GCI_checks",
        }
    return {
        "resistance_class": "distributed_wall_friction_candidate",
        "physics_role": "clean_total_pressure_loss_candidate",
        "development_state": "interior_straight_segment",
        "buoyancy_role": "minor_or_screened",
        "closure_admissibility": "admissible_after_GCI_and_time_window_checks",
    }


def thermal_audit_class(row: dict[str, Any], identity_tol: float = 1e-6) -> str:
    status = str(row.get("status", ""))
    if status != "computed":
        return f"not_computed_{status}"
    identity = rel_error(
        finite_float(row.get("uaprime_wmk")),
        finite_float(row.get("htc_times_perimeter_check_wmk")),
    )
    sign_consistent = str(row.get("sign_consistent_heated_wall", "")).lower()
    sign_needs_review = sign_consistent == "false"
    if math.isfinite(identity) and identity > identity_tol:
        return "identity_mismatch_review_geometry_or_flux"
    if sign_needs_review:
        return "identity_ok_sign_convention_needs_review"
    if str(row.get("mesh_independence", "")).upper() == "UNESTABLISHED":
        return "computed_coarse_mesh_no_GCI"
    return "computed"


def thermal_taxonomy(row: dict[str, Any], audit_class: str) -> dict[str, str]:
    status = str(row.get("status", ""))
    segment = str(row.get("segment", ""))
    nu_note = str(row.get("nu_note", ""))
    nu_value = finite_float(row.get("Nu"))

    if status != "computed":
        return {
            "thermal_resistance_class": "thermal_resistance_unavailable",
            "rom_energy_role": "blocked_or_policy_excluded",
            "nu_admissibility": "not_admissible",
        }
    if segment == "upcomer":
        resistance_class = "recirculation_cell_effective_thermal_resistance"
    else:
        resistance_class = "thermal_resistance_UAprime"

    if "not_admitted" in nu_note:
        nu_admissibility = "not_directly_admitted"
    elif math.isfinite(nu_value):
        nu_admissibility = "direct_or_diagnostic_with_domain_guard"
    else:
        nu_admissibility = "not_available"

    role = "energy_conductance_per_length_primary_ROM_closure"
    if audit_class == "identity_ok_sign_convention_needs_review":
        role = "energy_conductance_per_length_sign_review_required"

    return {
        "thermal_resistance_class": resistance_class,
        "rom_energy_role": role,
        "nu_admissibility": nu_admissibility,
    }


def section_station_index(section_dir: Path) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted(section_dir.glob("section_mean_pressure_*.json")):
        payload = load_json(path)
        source_id = str(payload.get("source_id", path.stem))
        for station in payload.get("stations", []):
            index[(source_id, str(station.get("label", "")))] = station
    return index


def build_geometry_rows(geometry_dir: Path, section_dir: Path) -> list[dict[str, Any]]:
    section_index = section_station_index(section_dir)
    rows: list[dict[str, Any]] = []
    for path in sorted(geometry_dir.glob("*/mesh_stations.json")):
        payload = load_json(path)
        source_id = str(payload.get("source_id", path.parent.name))
        for station in payload.get("stations", []):
            label = str(station.get("label", ""))
            section_station = section_index.get((source_id, label))
            tx = finite_float(station.get("nx"))
            ty = finite_float(station.get("ny"))
            tz = finite_float(station.get("nz"))
            qflag = geometry_quality(station, section_station)
            taxonomy = geometry_taxonomy(station, qflag)
            rows.append(
                {
                    "source_id": source_id,
                    "span": station.get("span", ""),
                    "station": label,
                    "x_m": station.get("x", ""),
                    "y_m": station.get("y", ""),
                    "z_m": station.get("z", ""),
                    "tx": tx,
                    "ty": ty,
                    "tz": tz,
                    "inclination_from_horizontal_deg": inclination_from_horizontal(tx, ty, tz),
                    "bore_m": station.get("bore_m", ""),
                    "section_area_m2": (section_station or {}).get("section_area_m2", ""),
                    "wetted_perimeter_m": (section_station or {}).get("wetted_perimeter_m", ""),
                    "hydraulic_diameter_m": (section_station or {}).get("hydraulic_diameter_m", ""),
                    "flow_alignment": (section_station or {}).get("flow_alignment", ""),
                    "is_fitting_end": bool(station.get("is_fitting_end", False)),
                    "geometry_source": "mesh_centerline",
                    "quality_flag": qflag,
                    **taxonomy,
                }
            )
    return rows


def build_pressure_rows(friction_json: Path) -> list[dict[str, Any]]:
    payload = load_json(friction_json)
    rows: list[dict[str, Any]] = []
    for case in payload.get("cases", []):
        source_id = str(case.get("source_id", ""))
        for segment in case.get("segments", []):
            audit_class, correction = pressure_audit_class(segment)
            taxonomy = pressure_taxonomy(segment, audit_class)
            rows.append(
                {
                    "source_id": source_id,
                    "span": segment.get("span", ""),
                    "method": segment.get("method", ""),
                    "n_stations_used": segment.get("n_stations_used", ""),
                    "segment_arc_length_m": segment.get("segment_arc_length_m", ""),
                    "dp_signed_ds_pa_per_m": segment.get("dp_signed_ds_pa_per_m", ""),
                    "dp_loss_ds_pa_per_m": segment.get("dp_loss_ds_pa_per_m", ""),
                    "hydraulic_diameter_m": segment.get("hydraulic_diameter_m", ""),
                    "section_mean_rho_kg_m3": segment.get("section_mean_rho_kg_m3", ""),
                    "u_bulk_m_s": segment.get("u_bulk_m_s", ""),
                    "reynolds_number": segment.get("reynolds_number", ""),
                    "apparent_darcy_f": segment.get("apparent_darcy_f", ""),
                    "excess_loss_factor_fapp_over_flam": segment.get("excess_loss_factor_fapp_over_flam", ""),
                    "flow_alignment_min": segment.get("flow_alignment_min", ""),
                    "raw_flags": segment.get("flags", ""),
                    "audit_class": audit_class,
                    "required_next_correction": correction,
                    **taxonomy,
                }
            )
    return rows


def build_thermal_rows(thermal_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(thermal_dir.glob("segment_htc_uaprime_*.json")):
        payload = load_json(path)
        source_id = str(payload.get("source_id", path.stem))
        for segment in payload.get("segments", []):
            audit_class = thermal_audit_class(segment)
            taxonomy = thermal_taxonomy(segment, audit_class)
            identity = rel_error(
                finite_float(segment.get("uaprime_wmk")),
                finite_float(segment.get("htc_times_perimeter_check_wmk")),
            )
            rows.append(
                {
                    "source_id": source_id,
                    "segment": segment.get("segment", ""),
                    "cfd_spans": segment.get("cfd_spans", ""),
                    "status": segment.get("status", ""),
                    "q_solver_wm2": segment.get("q_w_wm2", ""),
                    "qprime_solver_wm": segment.get("qprime_wall_wm", ""),
                    "T_wall_k": segment.get("T_wall_k", ""),
                    "T_bulk_k": segment.get("T_bulk_k", ""),
                    "delta_T_k": segment.get("delta_T_k", ""),
                    "htc_wm2k": segment.get("htc_wm2k", ""),
                    "uaprime_wmk": segment.get("uaprime_wmk", ""),
                    "R_prime_thermal_mkw": segment.get("R_prime_thermal_mkw", ""),
                    "wetted_perimeter_m": segment.get("wetted_perimeter_m", ""),
                    "htc_times_perimeter_check_wmk": segment.get("htc_times_perimeter_check_wmk", ""),
                    "uaprime_identity_rel_error": identity,
                    "Nu": segment.get("Nu", ""),
                    "nu_note": segment.get("nu_note", ""),
                    "mesh": segment.get("mesh", ""),
                    "mesh_independence": segment.get("mesh_independence", ""),
                    "q_sign": segment.get("q_sign", ""),
                    "sign_consistent_heated_wall": segment.get("sign_consistent_heated_wall", ""),
                    "audit_class": audit_class,
                    **taxonomy,
                }
            )
    return rows


def observation_row(
    *,
    source_id: str,
    span: str,
    segment_1d: str,
    station_or_segment: str,
    quantity: str,
    value: Any,
    units: str,
    method: str,
    quality_flag: str,
    valid_for_fit: bool,
    valid_for_validation: bool,
    caveat: str,
    resistance_class: str = "",
    physics_role: str = "",
    development_state: str = "",
    buoyancy_role: str = "",
    closure_admissibility: str = "",
    thermal_resistance_class: str = "",
    rom_energy_role: str = "",
    nu_admissibility: str = "",
    time_window: str = "",
    mesh_level: str = "coarse",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "case_family": case_family(source_id),
        "mesh_level": mesh_level,
        "time_window": time_window,
        "span": span,
        "segment_1d": segment_1d,
        "station_or_segment": station_or_segment,
        "quantity": quantity,
        "value": value,
        "units": units,
        "method": method,
        "quality_flag": quality_flag,
        "valid_for_fit": valid_for_fit,
        "valid_for_validation": valid_for_validation,
        "caveat": caveat,
        "resistance_class": resistance_class,
        "physics_role": physics_role,
        "development_state": development_state,
        "buoyancy_role": buoyancy_role,
        "closure_admissibility": closure_admissibility,
        "thermal_resistance_class": thermal_resistance_class,
        "rom_energy_role": rom_energy_role,
        "nu_admissibility": nu_admissibility,
    }


def build_observation_rows(
    geometry_rows: list[dict[str, Any]],
    pressure_rows: list[dict[str, Any]],
    thermal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in geometry_rows:
        source_id = str(row["source_id"])
        span = str(row["span"])
        station = str(row["station"])
        qflag = str(row["quality_flag"])
        for quantity, units in (
            ("hydraulic_diameter_m", "m"),
            ("section_area_m2", "m2"),
            ("inclination_from_horizontal_deg", "deg"),
        ):
            rows.append(
                observation_row(
                    source_id=source_id,
                    span=span,
                    segment_1d=span,
                    station_or_segment=station,
                    quantity=quantity,
                    value=row.get(quantity, ""),
                    units=units,
                    method="mesh_centerline_section_geometry",
                    quality_flag=qflag,
                    valid_for_fit=qflag == "ok",
                    valid_for_validation=True,
                    caveat="fitting_end_stations_excluded_from_straight_friction" if qflag != "ok" else "",
                    resistance_class=str(row.get("resistance_class", "")),
                    physics_role=str(row.get("physics_role", "")),
                    development_state=str(row.get("development_state", "")),
                    buoyancy_role=str(row.get("buoyancy_role", "")),
                    closure_admissibility=str(row.get("closure_admissibility", "")),
                )
            )
    for row in pressure_rows:
        valid_fit = row["audit_class"] == "direct_friction_candidate"
        rows.append(
            observation_row(
                source_id=str(row["source_id"]),
                span=str(row["span"]),
                segment_1d=str(row["span"]),
                station_or_segment=str(row["span"]),
                quantity="apparent_darcy_f",
                value=row.get("apparent_darcy_f", ""),
                units="1",
                method=str(row["method"]),
                quality_flag=str(row["audit_class"]),
                valid_for_fit=valid_fit,
                valid_for_validation=True,
                caveat=str(row["required_next_correction"]),
                resistance_class=str(row.get("resistance_class", "")),
                physics_role=str(row.get("physics_role", "")),
                development_state=str(row.get("development_state", "")),
                buoyancy_role=str(row.get("buoyancy_role", "")),
                closure_admissibility=str(row.get("closure_admissibility", "")),
            )
        )
    for row in thermal_rows:
        valid_fit = str(row["audit_class"]) == "computed_coarse_mesh_no_GCI"
        for quantity, units in (
            ("uaprime_wmk", "W/m/K"),
            ("htc_wm2k", "W/m2/K"),
            ("Nu", "1"),
        ):
            rows.append(
                observation_row(
                    source_id=str(row["source_id"]),
                    span=str(row["cfd_spans"]),
                    segment_1d=str(row["segment"]),
                    station_or_segment=str(row["segment"]),
                    quantity=quantity,
                    value=row.get(quantity, ""),
                    units=units,
                    method="enthalpy_flux_bulk_T_wallHeatFlux",
                    quality_flag=str(row["audit_class"]),
                    valid_for_fit=valid_fit and quantity != "Nu",
                    valid_for_validation=str(row["status"]) == "computed",
                    caveat="coarse_mesh_no_GCI;Nu_direct_only_where_admitted",
                    thermal_resistance_class=str(row.get("thermal_resistance_class", "")),
                    rom_energy_role=str(row.get("rom_energy_role", "")),
                    nu_admissibility=str(row.get("nu_admissibility", "")),
                )
            )
    return rows


def model_form_specs() -> list[dict[str, Any]]:
    return [
        {
            "model_id": "darcy_laminar_multiplier_by_span",
            "target_quantity": "apparent_darcy_f",
            "functional_form": "f_D = C_span * 64/Re",
            "features_used": ["Re", "span"],
            "domain_guards": ["clean_through_flow", "buoyancy_corrected_loss_required"],
        },
        {
            "model_id": "darcy_power_law_by_span",
            "target_quantity": "apparent_darcy_f",
            "functional_form": "f_D = a_span * Re**b_span",
            "features_used": ["Re", "span"],
            "domain_guards": ["minimum_three_physical_cases", "no_recirculation"],
        },
        {
            "model_id": "segment_constant_uaprime",
            "target_quantity": "uaprime_wmk",
            "functional_form": "UA'_segment = constant",
            "features_used": ["segment"],
            "domain_guards": ["computed_T_bulk", "coarse_mesh_flag_until_GCI"],
        },
        {
            "model_id": "segment_uaprime_power_law",
            "target_quantity": "uaprime_wmk",
            "functional_form": "UA' = a_segment * Re**b_segment",
            "features_used": ["Re", "segment"],
            "domain_guards": ["independent_Re_span_required", "mesh_GCI_required_for_publication"],
        },
        {
            "model_id": "upcomer_recirculation_onset",
            "target_quantity": "backflow_area_fraction",
            "functional_form": "bf = bf_max / (1 + (Ri_crit/Ri_streamwise)**k)",
            "features_used": ["Ri_streamwise", "station_region"],
            "domain_guards": ["cell_off_points_required", "median_Ri_not_mean_Ri"],
        },
        {
            "model_id": "bend_minor_loss_constant_K",
            "target_quantity": "minor_loss_K",
            "functional_form": "K_feature = constant",
            "features_used": ["feature_class"],
            "domain_guards": ["two_tap_total_pressure_loss", "straight_friction_removed"],
        },
    ]


def resistance_taxonomy_catalog() -> list[dict[str, str]]:
    return [
        {
            "resistance_class": "buoyancy_drive",
            "governing_role": "loop-scale density/elevation head that drives natural circulation",
            "expected_sign": "drives flow in the solved circulation direction",
            "rom_role": "left-hand-side pressure drive",
            "admissible_closure_form": "computed from rho(T), gravity projection, and elevation",
            "required_evidence": "temperature/density field and geometry orientation",
        },
        {
            "resistance_class": "distributed_wall_friction_candidate",
            "governing_role": "irreversible straight-span wall loss",
            "expected_sign": "positive mechanical loss",
            "rom_role": "Darcy-Weisbach distributed pressure loss",
            "admissible_closure_form": "f_D(Re, geometry, branch) after buoyancy/development checks",
            "required_evidence": "clean section alignment, no recirculation, corrected total-pressure loss, GCI",
        },
        {
            "resistance_class": "minor_loss_or_development_region",
            "governing_role": "bend, fitting, reducer, junction, entrance, or redevelopment loss",
            "expected_sign": "positive loss after reversible pressure exchange is removed",
            "rom_role": "minor-loss K or separate development correction",
            "admissible_closure_form": "K_feature or development-length correction",
            "required_evidence": "two-tap total-pressure loss and adjacent straight-friction subtraction",
        },
        {
            "resistance_class": "reversible_acceleration_area_change_diagnostic",
            "governing_role": "static pressure exchange from area or velocity change",
            "expected_sign": "can be positive or negative and is not an irreversible loss",
            "rom_role": "diagnostic term to separate from K/friction",
            "admissible_closure_form": "not fit as resistance",
            "required_evidence": "section mean total pressure and area/velocity change",
        },
        {
            "resistance_class": "buoyancy_contaminated_apparent_resistance",
            "governing_role": "raw apparent pressure slope where buoyancy source exceeds or masks wall loss",
            "expected_sign": "can be negative",
            "rom_role": "blocked apparent quantity until decomposed",
            "admissible_closure_form": "not admissible until variable-density buoyancy term is removed",
            "required_evidence": "mechanical-loss decomposition using p, p_rgh, rho, gravity projection",
        },
        {
            "resistance_class": "recirculation_cell_effective_resistance",
            "governing_role": "mixed-convection cell or reverse-flow structure modifying effective transport",
            "expected_sign": "not reducible to one Darcy f without a cell model",
            "rom_role": "branch-specific effective resistance or regime switch",
            "admissible_closure_form": "onset law in Ri/Ra plus effective transport model",
            "required_evidence": "backflow metric, median/characteristic Ri, onset/off-domain points",
        },
        {
            "resistance_class": "thermal_resistance_UAprime",
            "governing_role": "wall-to-bulk conductance per unit length",
            "expected_sign": "positive conductance under physics-positive heat-flow convention",
            "rom_role": "1D energy-equation closure",
            "admissible_closure_form": "UA'(segment), R'=1/UA', or guarded Nu relation",
            "required_evidence": "signed heat-flux audit, enthalpy-flux T_bulk, UA'=hP check, GCI",
        },
        {
            "resistance_class": "unresolved_residual",
            "governing_role": "remaining mismatch after modeled terms",
            "expected_sign": "case-dependent",
            "rom_role": "calibration residual and uncertainty ledger",
            "admissible_closure_form": "reported residual, not promoted to physics law",
            "required_evidence": "full term balance and error table",
        },
    ]


def value_counts(rows: list[dict[str, Any]], column: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(column, "") or "(blank)")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def write_readme(
    report_dir: Path,
    *,
    geometry_rows: list[dict[str, Any]],
    pressure_rows: list[dict[str, Any]],
    thermal_rows: list[dict[str, Any]],
    observation_rows: list[dict[str, Any]],
    work_dir: Path,
) -> None:
    pressure_classes: dict[str, int] = {}
    for row in pressure_rows:
        pressure_classes[str(row["audit_class"])] = pressure_classes.get(str(row["audit_class"]), 0) + 1
    thermal_classes: dict[str, int] = {}
    for row in thermal_rows:
        thermal_classes[str(row["audit_class"])] = thermal_classes.get(str(row["audit_class"]), 0) + 1
    resistance_classes = value_counts(pressure_rows, "resistance_class")
    thermal_resistance_classes = value_counts(thermal_rows, "thermal_resistance_class")

    readme = f"""# ROM Post-Processing Correctness Validation

Date: `2026-07-01`  
Task: `AGENT-165`  
Status: generated audit package from existing work products; no OpenFOAM run

## Purpose

This package implements the first reusable audit layer requested for the ROM and
post-processing work. It normalizes the existing mesh-geometry, pressure/friction,
and thermal closure outputs into tables that future agents can use for model-form
bakeoffs and correctness checks.

## Generated Tables

- `geometry_reference.csv`: mesh-derived station/tangent/bore plus section area,
  wetted perimeter, hydraulic diameter, fitting-end flag, and flow-alignment flag.
- `pressure_friction_audit.csv`: per-segment pressure/friction rows with an audit
  class stating whether the row is direct-friction candidate, apparent resistance,
  or not direct friction until variable-density buoyancy correction is added.
- `thermal_sign_identity_audit.csv`: per-segment thermal rows with the `UA' = hP`
  identity error and sign-convention audit class.
- `closure_observations.csv`: normalized long-form observation table for future
  ROM model-form bakeoffs.
- `model_form_specs_seed.json`: initial candidate model-form specs to score later.
- `resistance_taxonomy_catalog.json`: reusable definitions for hydraulic,
  buoyancy, development, recirculation, and thermal resistance classes.

The audit tables also carry the physical mental-model columns:
`resistance_class`, `physics_role`, `development_state`, `buoyancy_role`, and
`closure_admissibility`. Thermal rows carry `thermal_resistance_class`,
`rom_energy_role`, and `nu_admissibility`.

Work-product root: `{relative_to_workspace(work_dir)}`

## Counts

- Geometry rows: `{len(geometry_rows)}`
- Pressure/friction rows: `{len(pressure_rows)}`
- Thermal rows: `{len(thermal_rows)}`
- Closure-observation rows: `{len(observation_rows)}`

Pressure audit classes:

{chr(10).join(f"- `{key}`: {value}" for key, value in sorted(pressure_classes.items()))}

Thermal audit classes:

{chr(10).join(f"- `{key}`: {value}" for key, value in sorted(thermal_classes.items()))}

Pressure resistance classes:

{chr(10).join(f"- `{key}`: {value}" for key, value in sorted(resistance_classes.items()))}

Thermal resistance classes:

{chr(10).join(f"- `{key}`: {value}" for key, value in sorted(thermal_resistance_classes.items()))}

## Loop Resistance Mental Model

For the 1D ROM, the loop pressure balance should be interpreted as:

```text
buoyancy drive =
  distributed wall friction
+ minor losses from bends/reducers/junctions
+ flow-development or redevelopment losses
+ reversible acceleration / area-change pressure exchange
+ recirculation-cell effective resistance
+ unresolved residual and uncertainty
```

This package does not yet solve every term. Instead, it classifies each extracted
quantity by physical role so later closure fits do not mix different terms. In
particular, `p_rgh` gradients in heated or cooled non-isothermal legs can contain
local buoyancy-source terms, so those rows are marked as buoyancy-contaminated
apparent resistance until the mechanical-loss decomposition is implemented.

The energy-side analogue is:

```text
q' = UA' * (T_wall - T_bulk)
R'_thermal = 1 / UA'
Nu = h * D_h / k(T_bulk)
```

`UA'` is treated as the primary ROM thermal conductance per length. `Nu` remains
direct or diagnostic unless the row's domain and data support a real correlation.

## Interpretation

The current mesh-corrected pressure/friction table is intentionally conservative:
negative apparent friction or heated/cooled non-isothermal spans are not promoted
to closure-grade friction. They are marked for the next pressure decomposition
step: add the variable-density buoyancy correction before fitting distributed
Darcy losses.

The thermal table confirms the existing `UA' = h * wetted_perimeter` consistency
route and exposes rows whose solver-sign convention still needs explicit
paper-facing interpretation. The values remain coarse-mesh until GCI results
exist.

## Next Implementation Step

Add the actual buoyancy-corrected mechanical-loss calculation to the pressure
pipeline once AGENT-162's extractor ownership is clear. This package gives that
next step a stable output contract and acceptance surface.
"""
    (report_dir / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    args = parse_args()
    geometry_dir = Path(args.geometry_dir)
    section_dir = Path(args.section_dir)
    friction_json = Path(args.friction_json)
    thermal_dir = Path(args.thermal_dir)
    work_dir = ensure_dir(Path(args.work_dir))
    report_dir = ensure_dir(Path(args.report_dir))

    geometry_rows = build_geometry_rows(geometry_dir, section_dir)
    pressure_rows = build_pressure_rows(friction_json)
    thermal_rows = build_thermal_rows(thermal_dir)
    observation_rows = build_observation_rows(geometry_rows, pressure_rows, thermal_rows)
    specs = model_form_specs()
    taxonomy = resistance_taxonomy_catalog()

    csv_dump_rows(work_dir / "geometry_reference.csv", geometry_rows, GEOMETRY_FIELDS)
    csv_dump_rows(work_dir / "pressure_friction_audit.csv", pressure_rows, PRESSURE_FIELDS)
    csv_dump_rows(work_dir / "thermal_sign_identity_audit.csv", thermal_rows, THERMAL_FIELDS)
    csv_dump_rows(work_dir / "closure_observations.csv", observation_rows, OBS_FIELDS)
    json_dump(work_dir / "model_form_specs_seed.json", specs)
    json_dump(work_dir / "resistance_taxonomy_catalog.json", taxonomy)

    summary = {
        "generated_at": iso_timestamp(),
        "task": "AGENT-165",
        "no_openfoam_run": True,
        "inputs": {
            "geometry_dir": relative_to_workspace(geometry_dir),
            "section_dir": relative_to_workspace(section_dir),
            "friction_json": relative_to_workspace(friction_json),
            "thermal_dir": relative_to_workspace(thermal_dir),
        },
        "outputs": {
            "geometry_reference_csv": relative_to_workspace(work_dir / "geometry_reference.csv"),
            "pressure_friction_audit_csv": relative_to_workspace(work_dir / "pressure_friction_audit.csv"),
            "thermal_sign_identity_audit_csv": relative_to_workspace(work_dir / "thermal_sign_identity_audit.csv"),
            "closure_observations_csv": relative_to_workspace(work_dir / "closure_observations.csv"),
            "model_form_specs_seed_json": relative_to_workspace(work_dir / "model_form_specs_seed.json"),
            "resistance_taxonomy_catalog_json": relative_to_workspace(work_dir / "resistance_taxonomy_catalog.json"),
            "report_readme": relative_to_workspace(report_dir / "README.md"),
        },
        "counts": {
            "geometry_rows": len(geometry_rows),
            "pressure_rows": len(pressure_rows),
            "thermal_rows": len(thermal_rows),
            "closure_observation_rows": len(observation_rows),
            "model_form_specs": len(specs),
            "resistance_taxonomy_classes": len(taxonomy),
        },
        "taxonomy_counts": {
            "pressure_resistance_class": value_counts(pressure_rows, "resistance_class"),
            "pressure_closure_admissibility": value_counts(pressure_rows, "closure_admissibility"),
            "thermal_resistance_class": value_counts(thermal_rows, "thermal_resistance_class"),
            "thermal_nu_admissibility": value_counts(thermal_rows, "nu_admissibility"),
            "observation_resistance_class": value_counts(observation_rows, "resistance_class"),
            "observation_thermal_resistance_class": value_counts(observation_rows, "thermal_resistance_class"),
        },
        "limitations": [
            "Pressure rows are not buoyancy-corrected yet.",
            "Thermal rows are coarse-mesh and need GCI before publication-grade coefficients.",
            "This package is an audit layer, not a closure-bundle refresh.",
        ],
    }
    json_dump(work_dir / "summary.json", summary)
    json_dump(report_dir / "summary.json", summary)
    write_readme(
        report_dir,
        geometry_rows=geometry_rows,
        pressure_rows=pressure_rows,
        thermal_rows=thermal_rows,
        observation_rows=observation_rows,
        work_dir=work_dir,
    )

    print(f"Wrote {relative_to_workspace(work_dir / 'summary.json')}")
    print(f"Wrote {relative_to_workspace(report_dir / 'README.md')}")


if __name__ == "__main__":
    main()
