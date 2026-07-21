#!/usr/bin/env python3
"""Tests for AGENT-496 external score/junction/corner progress package."""

from __future__ import annotations

import unittest

from tools.analyze import build_external_score_junction_corner_progress as progress


class ExternalScoreJunctionCornerProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = progress.build()
        cls.sensor_rows = progress.read_csv(progress.OUT / "val_salt2_sensor_numeric_join.csv")
        cls.external_rows = progress.read_csv(progress.OUT / "external_score_readiness.csv")
        cls.junction_rows = progress.read_csv(progress.OUT / "junction_stub_cross_case_audit.csv")
        cls.junction_trends = progress.read_csv(progress.OUT / "junction_stub_trend_summary.csv")
        cls.corner_rows = progress.read_csv(progress.OUT / "pressure_corner_k_unlock_contract.csv")
        cls.dependencies = progress.read_csv(progress.OUT / "active_dependency_handoff.csv")
        cls.runtime_rows = progress.read_csv(progress.OUT / "runtime_leakage_audit.csv")

    def test_val_salt2_sensor_numeric_targets_are_joined(self) -> None:
        self.assertEqual(len(self.sensor_rows), 17)
        self.assertTrue(all(row["numeric_join_status"] == "joined_numeric_target" for row in self.sensor_rows))
        self.assertTrue(all(row["runtime_input_allowed"] == "no" for row in self.sensor_rows))
        self.assertTrue(all(row["fit_allowed"] == "no" for row in self.sensor_rows))
        self.assertEqual(self.summary["numeric_sensor_targets_joined"], 17)
        by_sensor = {row["sensor"]: row for row in self.sensor_rows}
        self.assertEqual(by_sensor["TP2"]["scorecard_use"], "blocked_by_sensor_policy")
        self.assertEqual(by_sensor["TW10"]["scorecard_use"], "blocked_by_sensor_policy")
        self.assertEqual(by_sensor["TP1"]["scorecard_use"], "external_score_target_after_solve")

    def test_external_readiness_is_target_ready_not_fit_ready(self) -> None:
        lanes = {row["evidence_lane"] for row in self.external_rows}
        self.assertEqual(lanes, {"pressure_streamwise_map", "thermal_section_and_junction", "sensor_temperature"})
        self.assertTrue(all(row["fit_allowed"] == "no" for row in self.external_rows))
        self.assertTrue(all(row["runtime_input_allowed"] == "no" for row in self.external_rows))
        self.assertTrue(all(row["prediction_rows_available_here"] == "0" for row in self.external_rows))

    def test_junction_audit_combines_mainline_and_val_without_admission(self) -> None:
        self.assertEqual(len(self.junction_rows), 16)
        self.assertEqual(sum(row["case_key"] == "val_salt2" for row in self.junction_rows), 4)
        allowed_statuses = {
            "diagnostic_named_loss_not_coefficient_admitted",
            "external_test_target_only_not_coefficient_admitted",
        }
        self.assertTrue(all(row["admission_status"] in allowed_statuses for row in self.junction_rows))
        val_rows = [row for row in self.junction_rows if row["case_key"] == "val_salt2"]
        self.assertTrue(all(row["setup_metadata_status"] == "missing_area_temperature_drive_metadata_in_val_split" for row in val_rows))

    def test_junction_trends_include_upper_right_dominance(self) -> None:
        by_bucket = {row["physical_junction_bucket"]: row for row in self.junction_trends}
        self.assertEqual(set(by_bucket), {"lower_left", "lower_right", "upper_left", "upper_right"})
        self.assertEqual(by_bucket["upper_right"]["trend_interpretation"], "dominant_bucket_consistent")
        self.assertTrue(all(row["model_admission"] == "diagnostic_named_loss_only" for row in self.junction_trends))

    def test_corner_k_contract_keeps_all_rows_blocked(self) -> None:
        self.assertEqual(len(self.corner_rows), 12)
        self.assertTrue(all(row["current_fit_admitted"] == "no" for row in self.corner_rows))
        self.assertTrue(all(row["unlock_status"] == "blocked_keep_diagnostic" for row in self.corner_rows))
        self.assertTrue(all(row["straight_loss_subtraction_gate"] == "fail" for row in self.corner_rows))
        self.assertTrue(all("pressure_K_fit" in row["do_not_use_for"] for row in self.corner_rows))

    def test_active_dependency_handoff_defers_recirculation_lane(self) -> None:
        by_lane = {row["dependency_lane"]: row for row in self.dependencies}
        self.assertEqual(by_lane["upcomer_onset_recirculation_classifier"]["owning_task"], "AGENT-495")
        self.assertEqual(by_lane["upcomer_onset_recirculation_classifier"]["this_package_action"], "read_only_dependency_no_overlap")
        self.assertEqual(by_lane["PM10_terminal_admission"]["status"], "blocked_live_jobs")

    def test_runtime_audit_is_all_pass(self) -> None:
        self.assertGreaterEqual(len(self.runtime_rows), 6)
        self.assertTrue(all(row["status"].startswith("pass") for row in self.runtime_rows))


if __name__ == "__main__":
    unittest.main()
