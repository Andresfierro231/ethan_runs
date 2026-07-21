#!/usr/bin/env python3
"""Tests for AGENT-507 wall/passive/test-section admission closeout."""

from __future__ import annotations

import unittest

from tools.analyze import build_wall_passive_test_section_admission_closeout as package


class WallPassiveTestSectionAdmissionCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = package.build()
        cls.matrix = package.read_csv(package.OUT / "admission_decision_matrix.csv")
        cls.pb1 = package.read_csv(package.OUT / "pb1_coupled_score_summary.csv")
        cls.local = package.read_csv(package.OUT / "local_test_section_assessment.csv")
        cls.failures = package.read_csv(package.OUT / "failure_mode_evidence.csv")
        cls.next_steps = package.read_csv(package.OUT / "next_steps.csv")

    def test_pb1_was_taken_into_coupled_scoring(self) -> None:
        self.assertEqual(len(self.pb1), 4)
        self.assertEqual(self.summary["pb1_coupled_candidates"], 4)
        self.assertTrue(all(row["pb1_static_gate"] == "pass" for row in self.pb1))
        self.assertTrue(all(row["runtime_gate"] == "pass" for row in self.pb1))
        self.assertTrue(all(row["admission_decision"] == "not_admitted" for row in self.pb1))

    def test_mdot_improves_but_temperature_field_fails_for_pb1(self) -> None:
        for row in self.pb1:
            self.assertLess(float(row["validation_mdot_delta_vs_m3_pct"]), 0.0)
            self.assertLess(float(row["holdout_mdot_delta_vs_m3_pct"]), 0.0)
            self.assertGreater(float(row["validation_all_probe_delta_vs_m3_K"]), 0.0)
            self.assertGreater(float(row["holdout_all_probe_delta_vs_m3_K"]), 0.0)
            self.assertEqual(row["validation_coupled_gate"], "fail")
            self.assertEqual(row["holdout_coupled_gate"], "fail")

    def test_local_distribution_assessment_is_separate_and_not_admitted(self) -> None:
        local_matrix = [row for row in self.matrix if row["evidence_lane"] == "local_distribution_plus_cooler"]
        self.assertEqual(len(local_matrix), 4)
        self.assertEqual(self.summary["local_distribution_candidates"], 4)
        self.assertTrue(all(row["static_passive_or_distribution_gate"] == "pass" for row in local_matrix))
        self.assertTrue(all(row["admission_decision"] == "not_admitted" for row in local_matrix))
        self.assertTrue(all(float(row["validation_tw_delta_vs_m3_K"]) > 0.0 for row in local_matrix))
        self.assertTrue(all(float(row["holdout_tw_delta_vs_m3_K"]) > 0.0 for row in local_matrix))

    def test_direct_test_section_static_rows_fail_generalization(self) -> None:
        ts_rows = [
            row
            for row in self.local
            if row["assessment_lane"] == "direct_test_section_static_component"
            and row["split_role"] in {"validation", "holdout"}
        ]
        self.assertEqual(len(ts_rows), 4)
        self.assertTrue(all(row["gate"] == "fail" for row in ts_rows))
        self.assertTrue(all("underpredicts" in row["diagnosis"] for row in ts_rows))

    def test_decision_keeps_blocker_open_without_runtime_blame(self) -> None:
        self.assertEqual(self.summary["decision"], "keep_predictive_wall_test_section_submodels_open")
        self.assertEqual(self.summary["admitted_candidate_rows"], 0)
        self.assertEqual(self.summary["coupled_completed_rows_reviewed"], 24)
        self.assertEqual(self.summary["runtime_blocker"], "no")
        self.assertEqual(self.summary["admission_change"], "none")

    def test_failure_modes_and_next_steps_are_actionable(self) -> None:
        failure_ids = {row["failure_mode"] for row in self.failures}
        self.assertIn("passive_total_not_sufficient", failure_ids)
        self.assertIn("local_test_section_static_underprediction", failure_ids)
        self.assertIn("local_distribution_still_temperature_wrong", failure_ids)
        self.assertIn("runtime_not_current_blocker", failure_ids)
        self.assertEqual([row["priority"] for row in self.next_steps], ["1", "2", "3", "4"])
        self.assertIn("local wall-temperature", self.next_steps[0]["next_step"])


if __name__ == "__main__":
    unittest.main()
