from __future__ import annotations

import unittest

from tools.analyze.build_ethan_frozen_state_results_package import best_one_d_rows, normalized_delta


class EthanFrozenStateResultsPackageTests(unittest.TestCase):
    def test_normalized_delta(self) -> None:
        self.assertAlmostEqual(normalized_delta(11.0, 10.0), 0.1)

    def test_best_one_d_rows_prefers_smallest_temperature_error_then_flow_error(self) -> None:
        rows = [
            {
                "case_label": "Salt 2",
                "accepted_for_validation": "True",
                "validity_status": "valid",
                "air_outlet_temperature_error_k": -5.0,
                "mass_flow_relative_error_pct": 2.0,
            },
            {
                "case_label": "Salt 2",
                "accepted_for_validation": "True",
                "validity_status": "valid",
                "air_outlet_temperature_error_k": -3.0,
                "mass_flow_relative_error_pct": 10.0,
            },
        ]
        best = best_one_d_rows(rows)
        self.assertEqual(len(best), 1)
        self.assertEqual(best[0]["air_outlet_temperature_error_k"], -3.0)


if __name__ == "__main__":
    unittest.main()
