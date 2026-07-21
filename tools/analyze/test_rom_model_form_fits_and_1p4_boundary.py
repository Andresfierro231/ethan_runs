#!/usr/bin/env python3
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_rom_model_form_fits_and_1p4_boundary import (  # noqa: E402
    finite_float,
    minor_losses,
    pct_error,
    rmse,
    scenario_for,
    summarize_results,
)
from tamu_loop_model_v2.solver import ScenarioConfig  # noqa: E402


def base_scenario() -> ScenarioConfig:
    return ScenarioConfig(
        name="base",
        insulation_thickness_in=1.0,
        radiation_on=False,
        internal_htc_mode="profile",
        internal_htc_multiplier_by_parent_segment={"lower_leg": 2.0},
        profile_descriptor_mode="contract",
        outer_closure_mode="contract",
        outer_conv_multiplier_by_parent_segment={"lower_leg": 3.0},
        outer_rad_multiplier_by_parent_segment={"lower_leg": 4.0},
        outer_insulation_multiplier_by_parent_segment={"lower_leg": 5.0},
        use_three_d_source_profile=True,
        use_three_d_segment_losses=True,
        three_d_contract_case_id="salt2",
    )


def test_pct_error_and_rmse_guard_bad_references():
    assert pct_error(1.1, 1.0) == pytest.approx(10.0)
    assert pct_error(0.9, 1.0) == pytest.approx(-10.0)
    assert math.isnan(pct_error(1.0, 0.0))
    assert math.isnan(pct_error(math.nan, 1.0))
    assert rmse([3.0, 4.0, math.nan]) == pytest.approx(math.sqrt(12.5))
    assert math.isnan(rmse([math.nan]))


def test_finite_float_handles_blank_and_nonfinite_values():
    assert finite_float("1.25") == pytest.approx(1.25)
    assert finite_float("", default=-1.0) == pytest.approx(-1.0)
    assert finite_float("nan", default=-2.0) == pytest.approx(-2.0)


def test_scenario_for_builds_matched_boundary_and_disables_cfd_contracts():
    scenario = scenario_for(1.4, True, base=base_scenario())
    assert scenario.name == "local_matched_boundary_ins_1.4in_rad_1"
    assert scenario.insulation_thickness_in == pytest.approx(1.4)
    assert scenario.radiation_on is True
    assert scenario.internal_htc_mode == "baseline"
    assert scenario.profile_descriptor_mode == "disabled"
    assert scenario.outer_closure_mode == "baseline"
    assert scenario.use_three_d_source_profile is False
    assert scenario.use_three_d_segment_losses is False
    assert scenario.three_d_contract_case_id == ""
    assert scenario.outer_conv_multiplier_by_parent_segment == {}


def test_minor_losses_total_fixed_k_matches_current_model_definition():
    losses = minor_losses(major=2.0, k90=3.0, k20=0.5, include_diameter=False)
    assert losses.major_loss_multiplier == pytest.approx(2.0)
    assert losses.k_90deg == pytest.approx(3.0)
    assert losses.k_20deg == pytest.approx(0.5)
    assert losses.include_test_section_diameter_change is False
    assert losses.total_fixed_k() == pytest.approx(14.0)


def test_summarize_results_ranks_fit_salts_by_mean_absolute_mdot_error():
    rows = [
        {"model_form": "bad", "fit_family": "fit", "salt": 2, "signed_mdot_error_pct": 10.0, "energy_error_pct_of_heater": math.nan, "tp_rmse_k": 2.0, "tw_rmse_k": 3.0, "accepted_for_validation": True, "major_loss_multiplier": 1.0, "k90": 1.0, "k20": 0.1, "total_fixed_k": 4.4, "insulation_thickness_in": 1.4, "radiation_on": True},
        {"model_form": "bad", "fit_family": "fit", "salt": 3, "signed_mdot_error_pct": -8.0, "energy_error_pct_of_heater": math.nan, "tp_rmse_k": 4.0, "tw_rmse_k": 5.0, "accepted_for_validation": True, "major_loss_multiplier": 1.0, "k90": 1.0, "k20": 0.1, "total_fixed_k": 4.4, "insulation_thickness_in": 1.4, "radiation_on": True},
        {"model_form": "bad", "fit_family": "fit", "salt": 4, "signed_mdot_error_pct": 12.0, "energy_error_pct_of_heater": math.nan, "tp_rmse_k": 6.0, "tw_rmse_k": 7.0, "accepted_for_validation": True, "major_loss_multiplier": 1.0, "k90": 1.0, "k20": 0.1, "total_fixed_k": 4.4, "insulation_thickness_in": 1.4, "radiation_on": True},
        {"model_form": "good", "fit_family": "fit", "salt": 2, "signed_mdot_error_pct": 2.0, "energy_error_pct_of_heater": math.nan, "tp_rmse_k": 1.0, "tw_rmse_k": 2.0, "accepted_for_validation": True, "major_loss_multiplier": 1.5, "k90": 2.0, "k20": 0.0, "total_fixed_k": 8.0, "insulation_thickness_in": 1.4, "radiation_on": True},
        {"model_form": "good", "fit_family": "fit", "salt": 3, "signed_mdot_error_pct": -1.0, "energy_error_pct_of_heater": math.nan, "tp_rmse_k": 2.0, "tw_rmse_k": 3.0, "accepted_for_validation": True, "major_loss_multiplier": 1.5, "k90": 2.0, "k20": 0.0, "total_fixed_k": 8.0, "insulation_thickness_in": 1.4, "radiation_on": True},
        {"model_form": "good", "fit_family": "fit", "salt": 4, "signed_mdot_error_pct": 3.0, "energy_error_pct_of_heater": math.nan, "tp_rmse_k": 3.0, "tw_rmse_k": 4.0, "accepted_for_validation": True, "major_loss_multiplier": 1.5, "k90": 2.0, "k20": 0.0, "total_fixed_k": 8.0, "insulation_thickness_in": 1.4, "radiation_on": True},
        {"model_form": "ignored_salt1", "fit_family": "fit", "salt": 1, "signed_mdot_error_pct": 0.0, "energy_error_pct_of_heater": 0.0, "tp_rmse_k": 0.0, "tw_rmse_k": 0.0, "accepted_for_validation": True, "major_loss_multiplier": 1.0, "k90": 1.0, "k20": 0.1, "total_fixed_k": 4.4, "insulation_thickness_in": 1.4, "radiation_on": True},
    ]
    summary = summarize_results(rows)
    assert [row["model_form"] for row in summary] == ["good", "bad"]
    assert summary[0]["mdot_rank"] == 1
    assert summary[0]["mean_abs_mdot_error_pct"] == pytest.approx(2.0)
    assert summary[1]["mean_abs_mdot_error_pct"] == pytest.approx(10.0)
