import unittest

from tools.analyze.build_recirculation_policy_forward_hydraulic_unblock_plan import (
    band_fraction,
    band_ri,
    band_secondary,
    coefficient_policy_rows,
    final_forward_unblock_rows,
    final_hydraulic_unblock_rows,
    pm5_classification_rows,
    raw_two_tap_classification_rows,
    recirculation_policy_rows,
)


class RecirculationPolicyForwardHydraulicUnblockTests(unittest.TestCase):
    def test_fraction_bands_make_material_recirculation_explicit(self):
        self.assertEqual(band_fraction(0.0), "single_stream_candidate")
        self.assertEqual(band_fraction(0.03), "weak_reverse_validation_only")
        self.assertEqual(band_fraction(0.10), "transition_section_effective")
        self.assertEqual(band_fraction(0.20), "material_recirculation_diagnostic_only")
        self.assertEqual(band_secondary(0.25), "multidimensional_mixing_diagnostic_only")
        self.assertEqual(band_ri(16.0), "strong_mixed_convection")

    def test_policy_invalidates_true_coefficients_for_material_recirculation(self):
        material_rows = [
            row
            for row in recirculation_policy_rows()
            if row["policy_variable"] in {"reverse_area_fraction", "reverse_mass_fraction"}
            and ">= 0.20" in row["rule_band"]
        ]
        self.assertEqual(len(material_rows), 2)
        for row in material_rows:
            self.assertIn("Nu", row["invalid_single_stream_coefficients"])
            self.assertIn("f_D", row["invalid_single_stream_coefficients"])
            self.assertIn("K", row["invalid_single_stream_coefficients"])
            self.assertIn("not_fit_admissible", row["fit_use"])

    def test_coefficient_policy_contains_required_labels(self):
        labels = {row["coefficient_label"] for row in coefficient_policy_rows()}
        self.assertIn("Nu", labels)
        self.assertIn("Nu_section_effective_upcomer_diagnostic", labels)
        self.assertIn("f_D", labels)
        self.assertIn("apparent_pressure_gradient_section_effective_diagnostic", labels)
        self.assertIn("K", labels)
        self.assertIn("K_section_effective_recirculating_diagnostic", labels)
        self.assertIn("invalid_coefficient_label", labels)

    def test_pm5_material_rows_are_diagnostic_not_fit(self):
        metric = {
            "case_key": "salt2_lo5q",
            "case_role": "holdout",
            "plane_location": "upcomer_mid",
            "span": "test_section_span",
            "representative_time_s": "10275",
            "reverse_area_fraction": "0.369",
            "reverse_mass_fraction": "0.500",
            "secondary_velocity_fraction": "0.001",
            "Ri": "45.1",
            "delta_T_wall_bulk_K": "6.3",
            "wallHeatFlux_W_m2": "-390",
        }
        rows = pm5_classification_rows(
            [metric],
            [{"case_key": "salt2_lo5q", "plane_location": "upcomer_mid", "f6_review_status": "diagnostic_onset_only_recirculating_not_f6_fit"}],
            [{"case_key": "salt2_lo5q", "plane_location": "upcomer_mid", "internal_nu_review_status": "diagnostic_sign_review_required"}],
        )
        self.assertEqual(rows[0]["use_class"], "diagnostic_only")
        self.assertEqual(rows[0]["fit_admissible"], "no")
        self.assertIn("Nu", rows[0]["invalid_single_stream_labels"])
        self.assertIn("Nu_section_effective_upcomer_diagnostic", rows[0]["valid_labels"])

    def test_raw_two_tap_material_proxy_is_not_true_k(self):
        rows = raw_two_tap_classification_rows(
            [
                {
                    "case_id": "salt_2",
                    "case_key": "salt2_mainline",
                    "tap_lower_label": "left_lower_leg__s00",
                    "tap_upper_label": "left_upper_leg__s04",
                    "representative_time_s": "7915",
                    "lower_reverse_area_fraction_proxy": "0.62",
                    "upper_reverse_area_fraction_proxy": "0.84",
                    "admission_status": "diagnostic_agent409_staged_copy_openfoam_parsed_not_fit_admitted",
                }
            ]
        )
        self.assertEqual(rows[0]["fit_admissible"], "no")
        self.assertIn("K_section_effective_recirculating_diagnostic", rows[0]["valid_labels"])
        self.assertIn("K", rows[0]["invalid_single_stream_labels"])

    def test_unblock_chains_keep_final_states_blocked(self):
        forward_states = {row["current_state"] for row in final_forward_unblock_rows()}
        hydraulic_states = {row["current_state"] for row in final_hydraulic_unblock_rows()}
        self.assertIn("blocked_no_go_final_forward_v1_not_admitted", forward_states)
        self.assertIn("blocked_not_final", hydraulic_states)


if __name__ == "__main__":
    unittest.main()
