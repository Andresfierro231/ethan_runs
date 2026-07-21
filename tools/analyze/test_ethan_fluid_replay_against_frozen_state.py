from __future__ import annotations

import unittest

from tools.analyze.build_ethan_fluid_replay_against_frozen_state import (
    count_text_occurrences,
    hybrid_coverage_rows,
    scenario_condition,
    scenario_family,
)


class EthanFluidReplayAgainstFrozenStateTests(unittest.TestCase):
    def test_scenario_family(self) -> None:
        self.assertEqual(scenario_family("ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0"), "baseline")
        self.assertEqual(scenario_family("ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_0"), "hybrid")

    def test_scenario_condition(self) -> None:
        self.assertEqual(
            scenario_condition("ethan_cfd_informed_salt_hybrid_ins_2.0in_rad_1"),
            "ins_2.0in_rad_1",
        )

    def test_hybrid_coverage_rows_marks_partial_conditions(self) -> None:
        rows = [
            {"scenario": "ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0", "case_label": "Salt 1"},
            {"scenario": "ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0", "case_label": "Salt 2"},
            {"scenario": "ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_0", "case_label": "Salt 1"},
        ]
        coverage = hybrid_coverage_rows(rows)
        self.assertEqual(len(coverage), 1)
        self.assertEqual(coverage[0]["coverage_status"], "partial")
        self.assertEqual(coverage[0]["missing_hybrid_cases"], "Salt 2")

    def test_count_text_occurrences_counts_matches(self) -> None:
        self.assertEqual(count_text_occurrences("v1 alpha v1 beta", "v1"), 2)
        self.assertEqual(count_text_occurrences("no matches here", "v1"), 0)


if __name__ == "__main__":
    unittest.main()
