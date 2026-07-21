from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_ethan_upcomer_recirculation_evidence import (
    CONTROL_BRANCH_NAME,
    FIGURE_STEM,
    UPCOMER_BRANCH_NAME,
    aggregate_reversal_groups,
    build_branch_profile_lookup,
    build_predictor_screen_rows,
    mean_profile_rows,
    render_svg_figure,
)


class EthanUpcomerRecirculationEvidenceTests(unittest.TestCase):
    def test_build_branch_profile_lookup_uses_component_and_bin(self) -> None:
        rows = [
            {
                "branch_name": UPCOMER_BRANCH_NAME,
                "component_span_name": "left_lower_leg",
                "span_name": "left_lower_leg",
                "bin_index": "3",
                "component_span_order_index": "0",
                "branch_profile_index": "3",
                "branch_s_fraction": "0.30",
                "branch_s_mid_m": "0.12",
                "branch_total_length_m": "0.95",
                "branch_s_start_m": "0.11",
                "branch_s_end_m": "0.13",
            },
            {
                "branch_name": UPCOMER_BRANCH_NAME,
                "component_span_name": "left_lower_leg",
                "span_name": "left_lower_leg",
                "bin_index": "3",
                "component_span_order_index": "0",
                "branch_profile_index": "3",
                "branch_s_fraction": "0.30",
                "branch_s_mid_m": "0.12",
                "branch_total_length_m": "0.95",
                "branch_s_start_m": "0.11",
                "branch_s_end_m": "0.13",
            },
        ]
        lookup = build_branch_profile_lookup(rows, UPCOMER_BRANCH_NAME)
        self.assertEqual(sorted(lookup.keys()), [("left_lower_leg", 3)])
        self.assertEqual(lookup[("left_lower_leg", 3)]["branch_profile_index"], 3)

    def test_aggregate_reversal_groups_computes_area_and_heat_fractions(self) -> None:
        lookup = {
            ("left_lower_leg", 0): {
                "component_span_name": "left_lower_leg",
                "component_span_order_index": 0,
                "branch_profile_index": 0,
                "branch_s_fraction": 0.0,
                "branch_s_mid_m": 0.0,
                "branch_total_length_m": 1.0,
                "branch_s_start_m": 0.0,
                "branch_s_end_m": 0.1,
            }
        }
        rows = [
            {
                "span_name": "left_lower_leg",
                "streamwise_bin_index": "0",
                "time_s": "1.0",
                "area_m2": "2.0",
                "mean_wall_shear_streamwise_pa": "-3.0",
                "total_wall_heat_w": "-4.0",
            },
            {
                "span_name": "left_lower_leg",
                "streamwise_bin_index": "0",
                "time_s": "1.0",
                "area_m2": "1.0",
                "mean_wall_shear_streamwise_pa": "1.0",
                "total_wall_heat_w": "2.0",
            },
        ]
        grouped = aggregate_reversal_groups(rows, lookup, {"left_lower_leg"}, UPCOMER_BRANCH_NAME)
        self.assertEqual(len(grouped), 1)
        self.assertAlmostEqual(grouped[0]["reverse_area_fraction"], 2.0 / 3.0)
        self.assertAlmostEqual(grouped[0]["reverse_abs_shear_fraction"], 6.0 / 7.0)
        self.assertAlmostEqual(grouped[0]["reverse_abs_heat_fraction"], 4.0 / 6.0)

    def test_build_predictor_screen_rows_marks_missing_predictors(self) -> None:
        case_rows = [
            {
                "case_label": "Salt 1 Jin",
                "upcomer_reverse_area_fraction": 0.60,
                "heater_power_W": 200.0,
                "temp_upcomer_bulk_k": 430.0,
            },
            {
                "case_label": "Salt 2 Jin",
                "upcomer_reverse_area_fraction": 0.62,
                "heater_power_W": 240.0,
                "temp_upcomer_bulk_k": 450.0,
            },
            {
                "case_label": "Salt 3 Jin",
                "upcomer_reverse_area_fraction": 0.66,
                "heater_power_W": 280.0,
                "temp_upcomer_bulk_k": 470.0,
            },
            {
                "case_label": "Salt 4 Jin",
                "upcomer_reverse_area_fraction": 0.68,
                "heater_power_W": 320.0,
                "temp_upcomer_bulk_k": 490.0,
            },
        ]
        predictor_rows = build_predictor_screen_rows(case_rows)
        heater_row = next(row for row in predictor_rows if row["predictor_key"] == "heater_power_W")
        reynolds_row = next(row for row in predictor_rows if row["predictor_key"] == "reynolds_bulk")
        self.assertEqual(heater_row["status"], "available")
        self.assertAlmostEqual(heater_row["spearman_rho"], 1.0)
        self.assertEqual(reynolds_row["status"], "not_available_in_reused_stack")

    def test_render_svg_figure_writes_expected_labels(self) -> None:
        per_case_profile_rows = {
            "viscosity_screening_salt_test_1_jin_coarse_mesh": mean_profile_rows(
                [
                    {
                        "branch_name": UPCOMER_BRANCH_NAME,
                        "time_s": 1.0,
                        "branch_profile_index": 0,
                        "branch_s_fraction": 0.0,
                        "branch_s_mid_m": 0.0,
                        "branch_total_length_m": 1.0,
                        "component_span_name": "left_lower_leg",
                        "component_span_order_index": 0,
                        "total_area_m2": 1.0,
                        "reverse_area_m2": 0.5,
                        "total_abs_shear_area_weight": 1.0,
                        "reverse_abs_shear_area_weight": 0.5,
                        "total_abs_heat_w": 1.0,
                        "reverse_abs_heat_w": 0.5,
                        "signed_shear_area_sum": -0.1,
                        "theta_bin_count": 4,
                        "reverse_area_fraction": 0.5,
                        "reverse_abs_shear_fraction": 0.5,
                        "reverse_abs_heat_fraction": 0.5,
                        "mean_signed_wall_shear_pa": -0.1,
                    },
                    {
                        "branch_name": UPCOMER_BRANCH_NAME,
                        "time_s": 1.0,
                        "branch_profile_index": 1,
                        "branch_s_fraction": 1.0,
                        "branch_s_mid_m": 1.0,
                        "branch_total_length_m": 1.0,
                        "component_span_name": "left_upper_leg",
                        "component_span_order_index": 2,
                        "total_area_m2": 1.0,
                        "reverse_area_m2": 0.75,
                        "total_abs_shear_area_weight": 1.0,
                        "reverse_abs_shear_area_weight": 0.75,
                        "total_abs_heat_w": 1.0,
                        "reverse_abs_heat_w": 0.75,
                        "signed_shear_area_sum": -0.2,
                        "theta_bin_count": 4,
                        "reverse_area_fraction": 0.75,
                        "reverse_abs_shear_fraction": 0.75,
                        "reverse_abs_heat_fraction": 0.75,
                        "mean_signed_wall_shear_pa": -0.2,
                    },
                ],
                "viscosity_screening_salt_test_1_jin_coarse_mesh",
                "Salt 1 Jin",
            )
        }
        per_case_profile_rows.update(
            {
                "viscosity_screening_salt_test_2_jin_coarse_mesh": per_case_profile_rows[
                    "viscosity_screening_salt_test_1_jin_coarse_mesh"
                ],
                "viscosity_screening_salt_test_3_jin_coarse_mesh": per_case_profile_rows[
                    "viscosity_screening_salt_test_1_jin_coarse_mesh"
                ],
                "viscosity_screening_salt_test_4_jin_coarse_mesh": per_case_profile_rows[
                    "viscosity_screening_salt_test_1_jin_coarse_mesh"
                ],
            }
        )
        case_summary_by_source = {
            source_id: {
                "case_label": f"Case {index + 1}",
                "upcomer_reverse_area_fraction": 0.5 + 0.1 * index,
            }
            for index, source_id in enumerate(per_case_profile_rows)
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "figures" / "svg" / f"{FIGURE_STEM}.svg"
            render_svg_figure(per_case_profile_rows, case_summary_by_source, path)
            text = path.read_text(encoding="utf-8")
        self.assertIn("Upcomer reverse-shear area fraction", text)
        self.assertIn("right-leg control stays at zero", text)
        self.assertIn("Case 1", text)


if __name__ == "__main__":
    unittest.main()
