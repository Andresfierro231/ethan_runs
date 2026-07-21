from __future__ import annotations

import math
import unittest

from tools.analyze.build_ethan_salt_pressure_drop_predictivity import (
    case_family_from_label,
    local_replay_row,
    resistance_from_drop,
)


class EthanSaltPressureDropPredictivityTest(unittest.TestCase):
    def test_case_family_from_label_collapses_duplicate_salt_refs(self) -> None:
        self.assertEqual(case_family_from_label("Salt 2 Kirst"), "Salt 2")
        self.assertEqual(case_family_from_label("Salt 4 Jin"), "Salt 4")

    def test_resistance_from_drop_requires_positive_mdot(self) -> None:
        self.assertTrue(math.isnan(resistance_from_drop(5.0, 0.0)))
        self.assertAlmostEqual(resistance_from_drop(5.0, 0.25), 20.0)

    def test_local_replay_row_uses_major_only_override(self) -> None:
        summary_row = {
            "source_id": "case_a",
            "case_label": "Salt 1 Kirst",
            "case_family": "Salt 1",
            "best_available_total_dp_pa": 12.0,
            "cfd_mdot_kg_s": 0.3,
            "major_total_resistance_pa_s_kg": 20.0,
            "feature_endpoint_total_resistance_pa_s_kg": 10.0,
            "feature_probe_total_resistance_pa_s_kg": 6.0,
        }
        row = local_replay_row(summary_row, "major_only_baseline", "major_total_resistance_pa_s_kg", "note")
        self.assertAlmostEqual(row["predicted_mdot_kg_s"], 0.6)
        self.assertAlmostEqual(row["mdot_abs_error_kg_s"], 0.3)


if __name__ == "__main__":
    unittest.main()
