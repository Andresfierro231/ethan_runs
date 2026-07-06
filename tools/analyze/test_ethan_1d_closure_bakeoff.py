from __future__ import annotations

import unittest

from tools.analyze.build_ethan_1d_closure_bakeoff import (
    build_heater_partition_rows,
    build_representative_validation_rows,
    case_family,
    choose_defended_scenario,
    scenario_setup_metadata,
    summarize_scenarios,
    truthy,
)


class Ethan1DClosureBakeoffTests(unittest.TestCase):
    def test_truthy_and_case_family_helpers(self) -> None:
        self.assertTrue(truthy("true"))
        self.assertTrue(truthy("Yes"))
        self.assertFalse(truthy("no"))
        self.assertEqual(case_family("Salt 2 Kirst"), "Salt 2")
        self.assertEqual(case_family("Salt 2"), "Salt 2")
        self.assertEqual(
            scenario_setup_metadata("ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_1")["branchwise_insulation_note"],
            "heated_incline=0.85x; left_lower_vertical=0.90x; test_section=0.95x; "
            "left_upper_vertical=0.90x; right_vertical=1.40x; "
            "cooled_incline_pre_hx=1.50x; cooled_incline_post_hx=1.50x",
        )

    def test_summarize_scenarios_uses_cfd_mass_flow_error(self) -> None:
        rows = summarize_scenarios(
            [
                {
                    "scenario": "a",
                    "accepted_for_validation": "True",
                    "validity_status": "valid",
                    "comparison_ready": "comparison_candidate",
                    "scenario_case_count": 2,
                    "scenario_primary_count": 2,
                    "scenario_primary_accepted_count": 2,
                    "scenario_all_accepted_count": 2,
                    "total_loss_error_pct_of_heater": 10.0,
                    "one_d_mass_flow_relative_error_pct_vs_cfd": 20.0,
                    "profile_descriptor_mode": "disabled",
                    "internal_htc_mode": "baseline",
                },
                {
                    "scenario": "a",
                    "accepted_for_validation": "True",
                    "validity_status": "valid",
                    "comparison_ready": "comparison_candidate",
                    "scenario_case_count": 2,
                    "scenario_primary_count": 2,
                    "scenario_primary_accepted_count": 2,
                    "scenario_all_accepted_count": 2,
                    "total_loss_error_pct_of_heater": 14.0,
                    "one_d_mass_flow_relative_error_pct_vs_cfd": 30.0,
                    "profile_descriptor_mode": "disabled",
                    "internal_htc_mode": "baseline",
                },
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["mean_primary_energy_error_pct_of_heater"], 12.0)
        self.assertAlmostEqual(rows[0]["mean_primary_mdot_error_pct_vs_cfd"], 25.0)

    def test_choose_defended_scenario_prefers_full_coverage_then_low_error(self) -> None:
        chosen = choose_defended_scenario(
            [
                {
                    "scenario": "partial",
                    "scenario_case_count": 3,
                    "scenario_all_accepted_count": 2,
                    "mean_primary_energy_error_pct_of_heater": 1.0,
                    "mean_primary_mdot_error_pct_vs_cfd": 1.0,
                },
                {
                    "scenario": "full_better",
                    "scenario_case_count": 3,
                    "scenario_all_accepted_count": 3,
                    "mean_primary_energy_error_pct_of_heater": 5.0,
                    "mean_primary_mdot_error_pct_vs_cfd": 7.0,
                },
                {
                    "scenario": "full_worse",
                    "scenario_case_count": 3,
                    "scenario_all_accepted_count": 3,
                    "mean_primary_energy_error_pct_of_heater": 6.0,
                    "mean_primary_mdot_error_pct_vs_cfd": 8.0,
                },
            ]
        )
        self.assertEqual(chosen["scenario"], "full_better")

    def test_representative_and_heater_rows_keep_cfd_basis(self) -> None:
        representative_rows = build_representative_validation_rows(
            defended_shadow_rows=[
                {
                    "comparison_ready": "comparison_candidate",
                    "frozen_case_label": "Salt 2 Kirst",
                    "frozen_source_id": "src",
                    "late_window_time_start_s": "10.0",
                    "late_window_time_end_s": "12.0",
                    "late_window_time_count": "3",
                    "primary_frozen_state_basis": "late_window_mean",
                    "sensitivity_snapshot_basis": "latest_retained_time",
                    "cfd_removed_w": "100.0",
                    "cfd_ambient_w": "50.0",
                    "cfd_total_loss_w": "150.0",
                    "cfd_heater_w": "200.0",
                    "cfd_test_section_w": "-5.0",
                    "cfd_junctions_w": "-10.0",
                    "cfd_mdot_kg_s": "0.01",
                    "downcomer_to_upcomer_bulk_delta_k": "-1.0",
                    "heater_to_cooler_bulk_delta_k": "-2.0",
                    "scenario": "ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_1",
                    "one_d_total_loss_w": "140.0",
                    "one_d_removed_w": "90.0",
                    "one_d_ambient_w": "50.0",
                    "one_d_mdot_kg_s": "0.011",
                }
            ],
            defended_case_rows=[
                {
                    "comparison_class": "comparison_candidate",
                    "frozen_case_label": "Salt 2 Kirst",
                    "energy_error_pct_of_heater": "5.0",
                    "tw_rmse_k": "6.0",
                    "tp_rmse_k": "7.0",
                    "mass_flow_relative_error_pct_vs_cfd": "10.0",
                },
            ]
        )
        self.assertEqual(representative_rows[0]["comparison_basis"], "CFD late_window_mean only")
        self.assertEqual(representative_rows[0]["one_d_scenario_variant"], "hybrid")
        self.assertEqual(representative_rows[0]["one_d_outer_closure_kind"], "per_parent_multiplier")
        self.assertAlmostEqual(representative_rows[0]["one_d_base_insulation_in"], 1.0)
        heater_rows = build_heater_partition_rows(representative_rows)
        self.assertAlmostEqual(heater_rows[0]["heater_power_config_w"], 265.7)
        self.assertAlmostEqual(heater_rows[0]["heater_section_gap_w"], 65.7)
        self.assertAlmostEqual(heater_rows[0]["heater_power_not_reaching_fluid_w"], 65.7)
        self.assertAlmostEqual(heater_rows[0]["heater_to_fluid_fraction_of_total_modeled_input"], 200.0 / 302.7)
        self.assertAlmostEqual(heater_rows[0]["ambient_fraction_of_total_loss"], 50.0 / 150.0)


if __name__ == "__main__":
    unittest.main()
