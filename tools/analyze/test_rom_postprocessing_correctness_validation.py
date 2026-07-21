#!/usr/bin/env python3
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_rom_postprocessing_correctness_validation import (  # noqa: E402
    build_observation_rows,
    geometry_taxonomy,
    inclination_from_horizontal,
    pressure_audit_class,
    pressure_taxonomy,
    rel_error,
    resistance_taxonomy_catalog,
    thermal_audit_class,
    thermal_taxonomy,
)


def test_inclination_from_horizontal_for_horizontal_and_vertical_vectors():
    assert inclination_from_horizontal(1.0, 0.0, 0.0) == pytest.approx(0.0)
    assert inclination_from_horizontal(0.0, 1.0, 0.0) == pytest.approx(90.0)
    assert inclination_from_horizontal(1.0, 1.0, 0.0) == pytest.approx(45.0)


def test_inclination_handles_bad_vector():
    assert math.isnan(inclination_from_horizontal(0.0, 0.0, 0.0))


def test_rel_error_guards_nonfinite_and_zero_reference():
    assert rel_error(10.0, 9.0) == pytest.approx(0.1)
    assert math.isnan(rel_error(0.0, 1.0))
    assert math.isnan(rel_error(math.nan, 1.0))


def test_pressure_audit_class_flags_negative_f_as_not_direct_friction():
    row = {
        "span": "lower_leg",
        "method": "section_mean_total_pressure_gradient",
        "n_stations_used": 3,
        "apparent_darcy_f": -0.7,
        "flags": "negative_f_pressure_recovery_or_noise",
    }
    audit_class, correction = pressure_audit_class(row)
    assert audit_class == "not_direct_friction"
    assert "buoyancy" in correction
    taxonomy = pressure_taxonomy(row, audit_class)
    assert taxonomy["resistance_class"] == "buoyancy_contaminated_apparent_resistance"
    assert taxonomy["closure_admissibility"] == "not_admissible_until_buoyancy_corrected"


def test_pressure_audit_class_marks_static_method_diagnostic():
    row = {
        "span": "left_lower_leg",
        "method": "section_mean_static_gradient",
        "n_stations_used": 3,
        "apparent_darcy_f": 2.0,
        "flags": "",
    }
    audit_class, correction = pressure_audit_class(row)
    assert audit_class == "diagnostic_static_or_secondary"
    assert "total" in correction
    taxonomy = pressure_taxonomy(row, audit_class)
    assert taxonomy["resistance_class"] == "reversible_acceleration_area_change_diagnostic"
    assert taxonomy["closure_admissibility"] == "diagnostic_only_not_fit"


def test_pressure_audit_class_marks_positive_upcomer_candidate():
    row = {
        "span": "left_lower_leg",
        "method": "section_mean_total_pressure_gradient",
        "n_stations_used": 3,
        "apparent_darcy_f": 2.0,
        "flags": "",
    }
    audit_class, correction = pressure_audit_class(row)
    assert audit_class == "direct_friction_candidate"
    assert "recirculation" in correction
    taxonomy = pressure_taxonomy(row, audit_class)
    assert taxonomy["resistance_class"] == "distributed_wall_friction_candidate"
    assert taxonomy["buoyancy_role"] == "mixed_convection_screen_required"


def test_geometry_taxonomy_marks_fitting_end_as_minor_loss_region():
    taxonomy = geometry_taxonomy({"is_fitting_end": True}, "fitting_end_exclude_from_straight_friction")
    assert taxonomy["resistance_class"] == "minor_loss_or_development_region"
    assert taxonomy["closure_admissibility"] == "exclude_from_straight_friction_fit"


def test_thermal_audit_class_detects_identity_mismatch_before_mesh_caveat():
    row = {
        "status": "computed",
        "uaprime_wmk": 10.0,
        "htc_times_perimeter_check_wmk": 9.0,
        "sign_consistent_heated_wall": True,
        "mesh_independence": "UNESTABLISHED",
    }
    assert thermal_audit_class(row) == "identity_mismatch_review_geometry_or_flux"
    taxonomy = thermal_taxonomy(row, "identity_mismatch_review_geometry_or_flux")
    assert taxonomy["thermal_resistance_class"] == "thermal_resistance_UAprime"
    assert taxonomy["rom_energy_role"] == "energy_conductance_per_length_primary_ROM_closure"


def test_thermal_audit_class_detects_sign_review():
    row = {
        "status": "computed",
        "uaprime_wmk": 10.0,
        "htc_times_perimeter_check_wmk": 10.0,
        "sign_consistent_heated_wall": False,
        "mesh_independence": "UNESTABLISHED",
    }
    assert thermal_audit_class(row) == "identity_ok_sign_convention_needs_review"
    taxonomy = thermal_taxonomy(row, "identity_ok_sign_convention_needs_review")
    assert taxonomy["rom_energy_role"] == "energy_conductance_per_length_sign_review_required"


def test_thermal_taxonomy_marks_blocked_row_unavailable():
    row = {"status": "thermally_blocked_segment_right_leg", "segment": "downcomer"}
    taxonomy = thermal_taxonomy(row, "not_computed_thermally_blocked_segment_right_leg")
    assert taxonomy["thermal_resistance_class"] == "thermal_resistance_unavailable"
    assert taxonomy["nu_admissibility"] == "not_admissible"


def test_resistance_taxonomy_catalog_contains_core_model_terms():
    classes = {row["resistance_class"] for row in resistance_taxonomy_catalog()}
    assert {
        "buoyancy_drive",
        "distributed_wall_friction_candidate",
        "minor_loss_or_development_region",
        "thermal_resistance_UAprime",
        "recirculation_cell_effective_resistance",
    }.issubset(classes)


def test_observation_rows_include_geometry_pressure_and_thermal():
    geometry_rows = [
        {
            "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "span": "lower_leg",
            "station": "lower_leg__s02",
            "quality_flag": "ok",
            "resistance_class": "geometry_support",
            "physics_role": "defines_area_diameter_tangent_for_closures",
            "development_state": "clean_interior_station",
            "buoyancy_role": "sets_streamwise_gravity_projection",
            "closure_admissibility": "usable_as_closure_geometry",
            "hydraulic_diameter_m": 0.022,
            "section_area_m2": 3.8e-4,
            "inclination_from_horizontal_deg": 21.5,
        }
    ]
    pressure_rows = [
        {
            "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "span": "left_lower_leg",
            "method": "section_mean_total_pressure_gradient",
            "audit_class": "direct_friction_candidate",
            "required_next_correction": "confirm_no_recirculation_for_station_subset",
            "resistance_class": "distributed_wall_friction_candidate",
            "physics_role": "clean_total_pressure_loss_candidate",
            "development_state": "requires_recirculation_screen",
            "buoyancy_role": "mixed_convection_screen_required",
            "closure_admissibility": "admissible_after_recirculation_and_GCI_checks",
            "apparent_darcy_f": 2.1,
        }
    ]
    thermal_rows = [
        {
            "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "segment": "lower_leg",
            "cfd_spans": "lower_leg",
            "audit_class": "computed_coarse_mesh_no_GCI",
            "thermal_resistance_class": "thermal_resistance_UAprime",
            "rom_energy_role": "energy_conductance_per_length_primary_ROM_closure",
            "nu_admissibility": "not_available",
            "status": "computed",
            "uaprime_wmk": 16.0,
            "htc_wm2k": 250.0,
            "Nu": math.nan,
        }
    ]
    rows = build_observation_rows(geometry_rows, pressure_rows, thermal_rows)
    quantities = {row["quantity"] for row in rows}
    assert {"hydraulic_diameter_m", "apparent_darcy_f", "uaprime_wmk"}.issubset(quantities)
    assert any(row["valid_for_fit"] for row in rows if row["quantity"] == "apparent_darcy_f")
    assert all("resistance_class" in row for row in rows)
    assert all("thermal_resistance_class" in row for row in rows)
