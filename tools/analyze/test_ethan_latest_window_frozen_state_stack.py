from __future__ import annotations

import math
import unittest

from tools.analyze.build_ethan_latest_window_frozen_state_stack import (
    TARGET_REPRESENTATIVE_COUNT,
    branch_drift_rollup,
    canonical_time_token,
    frozen_state_contract_rows,
    load_representative_times,
)


class EthanLatestWindowFrozenStateStackTests(unittest.TestCase):
    def test_canonical_time_token_matches_processor_labels(self) -> None:
        self.assertEqual(canonical_time_token("5378.0"), "5378")
        self.assertEqual(canonical_time_token("3617.6625"), "3617.6625")
        self.assertEqual(canonical_time_token("3398.45"), "3398.45")

    def test_frozen_state_contract_flags_short_window_but_keeps_case_candidate(self) -> None:
        rows = frozen_state_contract_rows(
            [
                {
                    "source_id": "src",
                    "case_label": "Salt 1 Jin",
                    "representative_time_count": TARGET_REPRESENTATIVE_COUNT - 2,
                    "late_window_time_start_s": 0.0,
                    "late_window_time_end_s": 10.0,
                    "latest_retained_time_s": 10.0,
                    "window_status": "window_shortfall",
                    "window_status_note": "short",
                    "package_root": "/tmp/pkg",
                    "runtime_root": "/tmp/run",
                    "profile_name": "demo",
                    "branch_rows": [
                        {"branch_name": "right_leg", "mean_bulk_temp_fluid_area_avg_k": "452.0"},
                        {"branch_name": "upcomer", "mean_bulk_temp_fluid_area_avg_k": "454.5"},
                        {"branch_name": "lower_leg", "mean_bulk_temp_fluid_area_avg_k": "447.0"},
                        {"branch_name": "upper_leg", "mean_bulk_temp_fluid_area_avg_k": "450.0"},
                    ],
                }
            ]
        )
        self.assertEqual(rows[0]["comparison_ready"], "comparison_candidate")
        self.assertEqual(rows[0]["window_status"], "window_shortfall")
        self.assertAlmostEqual(rows[0]["downcomer_to_upcomer_bulk_delta_k"], -2.5)
        self.assertAlmostEqual(rows[0]["heater_to_cooler_bulk_delta_k"], -3.0)

    def test_branch_drift_rollup_averages_only_finite_values(self) -> None:
        rows = branch_drift_rollup(
            [
                {
                    "branch_name": "left_lower_leg",
                    "bulk_latest_vs_mean_fraction": 0.1,
                    "wall_latest_vs_mean_fraction": 0.2,
                    "htc_latest_vs_mean_fraction": 0.3,
                },
                {
                    "branch_name": "left_lower_leg",
                    "bulk_latest_vs_mean_fraction": math.nan,
                    "wall_latest_vs_mean_fraction": 0.4,
                    "htc_latest_vs_mean_fraction": 0.5,
                },
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["mean_bulk_latest_vs_mean_fraction"], 0.1)
        self.assertAlmostEqual(rows[0]["mean_wall_latest_vs_mean_fraction"], 0.3)
        self.assertAlmostEqual(rows[0]["mean_htc_latest_vs_mean_fraction"], 0.4)
        self.assertAlmostEqual(rows[0]["max_htc_latest_vs_mean_fraction"], 0.5)


if __name__ == "__main__":
    unittest.main()
