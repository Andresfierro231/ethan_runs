#!/usr/bin/env python3
"""Tests for AGENT-500 val_salt2 external score/unlock package."""

from __future__ import annotations

import unittest

from tools.analyze import build_val_salt2_external_score_and_unlock_progress as package


class ValSalt2ExternalScoreAndUnlockProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = package.build()
        cls.targets = package.read_csv(package.OUT / "val_salt2_external_score_targets.csv")
        cls.join_contract = package.read_csv(package.OUT / "val_salt2_prediction_join_contract.csv")
        cls.residuals = package.read_csv(package.OUT / "val_salt2_external_residual_scorecard.csv")
        cls.junction = package.read_csv(package.OUT / "junction_heat_coefficient_readiness.csv")
        cls.corner = package.read_csv(package.OUT / "corner_k_unlock_gate.csv")
        cls.pm10 = package.read_csv(package.OUT / "pm10_holdout_admission_watch.csv")
        cls.runtime = package.read_csv(package.OUT / "runtime_leakage_audit.csv")
        cls.figures = package.read_csv(package.OUT / "figure_manifest.csv")

    def test_targets_are_external_only_with_expected_lanes(self) -> None:
        self.assertEqual(len(self.targets), 61)
        lanes = {row["evidence_lane"] for row in self.targets}
        self.assertEqual(lanes, {"pressure_streamwise_map", "thermal_section_and_junction", "sensor_temperature"})
        self.assertTrue(all(row["external_test_only"] == "yes" for row in self.targets))
        self.assertTrue(all(row["training_input_allowed"] == "no" for row in self.targets))
        self.assertTrue(all(row["fit_allowed"] == "no" for row in self.targets))
        self.assertTrue(all(row["model_selection_allowed"] == "no" for row in self.targets))
        self.assertTrue(all(row["runtime_input_allowed"] == "no" for row in self.targets))
        self.assertEqual(self.summary["pressure_target_rows"], 30)
        self.assertEqual(self.summary["sensor_target_rows"], 17)

    def test_sensor_policy_excludes_tp2_and_tw10(self) -> None:
        by_id = {row["target_id"]: row for row in self.targets if row["evidence_lane"] == "sensor_temperature"}
        self.assertEqual(by_id["TP2"]["score_allowed"], "no")
        self.assertEqual(by_id["TW10"]["score_allowed"], "no")
        self.assertEqual(by_id["TP1"]["score_allowed"], "yes")
        residual_by_id = {row["target_id"]: row for row in self.residuals}
        self.assertEqual(residual_by_id["TP2"]["score_status"], "policy_excluded_not_scored")
        self.assertEqual(residual_by_id["TW10"]["score_status"], "policy_excluded_not_scored")
        self.assertEqual(self.summary["policy_allowed_sensor_rows"], 15)

    def test_prediction_contract_marks_predictions_missing(self) -> None:
        self.assertEqual(len(self.join_contract), 3)
        self.assertTrue(all(row["join_status"] == "prediction_missing" for row in self.join_contract))
        self.assertTrue(all(row["prediction_rows_available"] == "0" for row in self.join_contract))
        self.assertEqual(self.summary["prediction_rows_joined"], 0)
        self.assertGreater(self.summary["prediction_missing_rows"], 0)

    def test_junction_coefficient_admission_is_blocked(self) -> None:
        self.assertEqual(len(self.junction), 16)
        self.assertEqual(self.summary["junction_coefficient_admitted_rows"], 0)
        self.assertTrue(all(row["fit_allowed"] == "no" for row in self.junction))
        val_rows = [row for row in self.junction if row["case_key"] == "val_salt2"]
        self.assertEqual(len(val_rows), 4)
        self.assertTrue(
            all(row["coefficient_admission_status"] == "blocked_missing_area_or_temperature_drive" for row in val_rows)
        )

    def test_corner_k_rows_remain_diagnostic(self) -> None:
        self.assertEqual(len(self.corner), 12)
        self.assertEqual(self.summary["corner_k_fit_admitted_rows"], 0)
        self.assertTrue(all(row["fit_admission_status"] == "blocked_keep_diagnostic" for row in self.corner))
        self.assertTrue(all(row["straight_loss_subtraction_gate"] == "fail" for row in self.corner))
        self.assertTrue(all("pressure_K_fit" in row["do_not_use_for"] for row in self.corner))

    def test_pm10_watch_is_monitor_only(self) -> None:
        self.assertEqual(len(self.pm10), 4)
        self.assertEqual(self.summary["pm10_terminal_admission_allowed_rows"], 0)
        self.assertTrue(all(row["terminal_admission_allowed_now"] == "no" for row in self.pm10))
        self.assertTrue(all(row["watch_status"] == "blocked_live_or_pending_jobs" for row in self.pm10))

    def test_runtime_audit_and_figures_are_complete(self) -> None:
        self.assertGreaterEqual(len(self.runtime), 7)
        self.assertTrue(all(row["status"].startswith("pass") for row in self.runtime))
        self.assertEqual(len(self.figures), 4)
        for row in self.figures:
            self.assertTrue((package.ROOT / row["path"]).exists(), row["path"])


if __name__ == "__main__":
    unittest.main()
