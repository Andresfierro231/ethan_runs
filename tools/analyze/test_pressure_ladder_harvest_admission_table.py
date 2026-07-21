import unittest

from tools.analyze.build_pressure_ladder_harvest_admission_table import (
    build_adjacent_pair_screen,
    build_branch_admission_table,
    recirculation_band,
    recirculation_gate_from_pairs,
)


class PressureLadderHarvestAdmissionTableTests(unittest.TestCase):
    def test_material_reverse_area_blocks_recirc_gate(self):
        self.assertEqual(recirculation_band(0.35), "material_recirc_mask_fail")
        self.assertEqual(
            recirculation_gate_from_pairs([{"pair_recirc_band": "material_recirc_mask_fail"}]),
            "blocked_material_recirculation_mask",
        )

    def test_low_reverse_area_can_pass_only_recirc_gate(self):
        self.assertEqual(recirculation_band(0.005), "low_recirc_mask_pass")
        self.assertEqual(
            recirculation_gate_from_pairs(
                [{"pair_recirc_band": "low_recirc_mask_pass"}, {"pair_recirc_band": "low_recirc_mask_pass"}]
            ),
            "passes_low_recirc_mask_pending_other_gates",
        )

    def test_mixed_pressure_ladder_orientation_remains_unresolved(self):
        adjacent = [
            {
                "case_key": "synthetic",
                "case_id": "salt_x",
                "split_role": "training",
                "harvest_package": "synthetic_package",
                "harvest_job_id": "1",
                "branch": "lower_leg",
                "delta_p_to_minus_from_Pa_float": 1.0,
                "delta_p_rgh_to_minus_from_Pa_float": 1.0,
                "max_reverse_area_fraction_proxy": 0.0,
                "pair_recirc_band": "low_recirc_mask_pass",
                "source_path": "synthetic.csv",
            },
            {
                "case_key": "synthetic",
                "case_id": "salt_x",
                "split_role": "training",
                "harvest_package": "synthetic_package",
                "harvest_job_id": "1",
                "branch": "lower_leg",
                "delta_p_to_minus_from_Pa_float": -1.0,
                "delta_p_rgh_to_minus_from_Pa_float": -1.0,
                "max_reverse_area_fraction_proxy": 0.0,
                "pair_recirc_band": "low_recirc_mask_pass",
                "source_path": "synthetic.csv",
            },
        ]
        rows = build_branch_admission_table(adjacent, [])
        self.assertEqual(rows[0]["orientation_status"], "orientation_unresolved_mixed_adjacent_p_rgh")
        self.assertEqual(rows[0]["true_f_D_or_K_fit_admitted"], "no")

    def test_upcomer_hybrid_branch_is_not_fit_admitted(self):
        adjacent = [
            {
                "case_key": "synthetic",
                "case_id": "salt_x",
                "split_role": "training",
                "harvest_package": "synthetic_package",
                "harvest_job_id": "1",
                "branch": "test_section_span",
                "delta_p_to_minus_from_Pa_float": 2.0,
                "delta_p_rgh_to_minus_from_Pa_float": 2.0,
                "max_reverse_area_fraction_proxy": 0.30,
                "pair_recirc_band": "material_recirc_mask_fail",
                "source_path": "synthetic.csv",
            }
        ]
        rows = build_branch_admission_table(adjacent, [])
        self.assertEqual(rows[0]["upcomer_hybrid_lane"], "yes")
        self.assertEqual(rows[0]["admission_status"], "not_admitted_recirc_mask")
        self.assertEqual(rows[0]["true_f_D_or_K_fit_admitted"], "no")

    def test_adjacent_pair_screen_preserves_no_fit_status(self):
        rows = build_adjacent_pair_screen(
            [
                {
                    "case_key": "synthetic",
                    "split_role": "training",
                    "harvest_package": "synthetic_package",
                    "branch": "lower_leg",
                    "from_station": "a",
                    "to_station": "b",
                    "delta_p_to_minus_from_Pa": "1",
                    "delta_p_rgh_to_minus_from_Pa": "-2",
                    "delta_p_rgh_to_minus_from_Pa_float": -2.0,
                    "from_reverse_area_fraction_proxy": "0.1",
                    "to_reverse_area_fraction_proxy": "0.2",
                    "max_reverse_area_fraction_proxy": 0.2,
                    "pair_recirc_band": "material_recirc_mask_fail",
                    "upcomer_hybrid_lane": "no",
                    "source_path": "synthetic.csv",
                }
            ]
        )
        self.assertEqual(rows[0]["delta_p_rgh_sign"], "negative")
        self.assertEqual(rows[0]["admission_status"], "diagnostic_pair_only_not_fit_admitted")


if __name__ == "__main__":
    unittest.main()
