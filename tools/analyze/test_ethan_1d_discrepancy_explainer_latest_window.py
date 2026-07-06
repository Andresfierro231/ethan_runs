from __future__ import annotations

import unittest

from tools.analyze.build_ethan_1d_discrepancy_explainer_latest_window import (
    build_explanation_register,
    dominant_discrepancy_bucket,
)


class Ethan1DDiscrepancyExplainerLatestWindowTests(unittest.TestCase):
    def test_dominant_discrepancy_bucket_picks_largest_metric(self) -> None:
        self.assertEqual(
            dominant_discrepancy_bucket(
                energy_error_pct=12.0,
                mass_flow_error_pct=30.0,
                wall_rmse_k=20.0,
                centerline_rmse_k=10.0,
            ),
            "mass_flow",
        )
        self.assertEqual(
            dominant_discrepancy_bucket(
                energy_error_pct=4.0,
                mass_flow_error_pct=3.0,
                wall_rmse_k=80.0,
                centerline_rmse_k=20.0,
            ),
            "wall_temperature",
        )

    def test_explanation_register_marks_supported_and_possible_rows(self) -> None:
        rows = build_explanation_register(
            defended_rows=[
                {
                    "energy_error_pct_of_heater": 11.0,
                    "mass_flow_error_pct_vs_cfd": 22.0,
                }
            ],
            contrast_rows=[
                {
                    "upcomer_minus_downcomer_htc_w_m2_k": 15.0,
                }
            ],
            heat_gap_rows=[
                {
                    "removed_gap_w": -12.0,
                    "ambient_gap_w": 8.0,
                }
            ],
        )
        statuses = {row["explanation_id"]: row["status"] for row in rows}
        self.assertEqual(statuses["upcomer_requires_separate_model"], "supported")
        self.assertEqual(statuses["heat_partition_not_matched_case_by_case"], "supported")
        self.assertEqual(statuses["global_1p4in_setup_still_unpublished_in_readable_bundle"], "possible_not_tested")


if __name__ == "__main__":
    unittest.main()
