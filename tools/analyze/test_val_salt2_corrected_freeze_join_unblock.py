#!/usr/bin/env python3
"""Tests for AGENT-508 val_salt2 corrected-freeze join unblock package."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_val_salt2_corrected_freeze_join_unblock as package


class ValSalt2CorrectedFreezeJoinUnblockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = package.build()
        cls.audit = package.read_csv(package.OUT / "corrected_freeze_source_audit.csv")
        cls.joined = package.read_csv(package.OUT / "val_salt2_prediction_join.csv")
        cls.residuals = package.read_csv(package.OUT / "val_salt2_external_residual_scorecard.csv")
        cls.score_summary = package.read_csv(package.OUT / "val_salt2_score_summary.csv")
        cls.runtime = package.read_csv(package.OUT / "runtime_leakage_audit.csv")
        cls.figures = package.read_csv(package.OUT / "figure_manifest.csv")

    def test_default_state_reports_freeze_blocked_not_scored(self) -> None:
        self.assertEqual(len(self.joined), 61)
        self.assertEqual(self.summary["prediction_rows_joined"], 0)
        self.assertEqual(self.summary["policy_excluded_rows"], 2)
        self.assertGreater(self.summary["blocked_or_missing_rows"], 0)
        self.assertIn("freeze_blocked", self.summary["freeze_status"])
        self.assertTrue(all(row["score_status"] != "joined_scored" for row in self.residuals))

    def test_guardrails_remain_external_only(self) -> None:
        self.assertTrue(all(row["training_input_allowed"] == "no" for row in self.joined))
        self.assertTrue(all(row["fit_allowed"] == "no" for row in self.joined))
        self.assertTrue(all(row["model_selection_allowed"] == "no" for row in self.joined))
        self.assertTrue(all(row["runtime_input_allowed"] == "no" for row in self.joined))
        by_id = {row["target_id"]: row for row in self.residuals if row["target_id"] in {"TP2", "TW10"}}
        self.assertEqual(by_id["TP2"]["score_status"], "policy_excluded_not_scored")
        self.assertEqual(by_id["TW10"]["score_status"], "policy_excluded_not_scored")

    def test_blocked_legacy_candidates_are_not_joined_as_predictions(self) -> None:
        audit_status = ";".join(row["status"] for row in self.audit)
        self.assertIn("freeze_blocked", audit_status)
        self.assertTrue(all(row["prediction_join_status"] == "not_joined" for row in self.joined))
        self.assertTrue(all(row["score_status"] == "no_joined_predictions" for row in self.score_summary))

    def test_runtime_audit_and_figures_are_present(self) -> None:
        self.assertGreaterEqual(len(self.runtime), 7)
        self.assertTrue(all(row["status"].startswith("pass") for row in self.runtime))
        self.assertEqual(len(self.figures), 3)
        for row in self.figures:
            self.assertTrue((package.ROOT / row["path"]).exists(), row["path"])

    def test_mock_valid_frozen_predictions_join_and_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            prediction_csv = tmp_path / "mock_predictions.csv"
            output_dir = tmp_path / "out"
            targets = package.read_csv(package.TARGETS)
            fieldnames = [
                "case_key",
                "evidence_lane",
                "target_id",
                "prediction_model_id",
                "predicted_static_p_Pa",
                "predicted_p_rgh_Pa",
                "predicted_heat_W",
                "predicted_temperature_K",
            ]
            with prediction_csv.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for target in targets:
                    base = float(target["target_value"])
                    lane = target["evidence_lane"]
                    row = {
                        "case_key": target["case_key"],
                        "evidence_lane": lane,
                        "target_id": target["target_id"],
                        "prediction_model_id": "mock_corrected_freeze_v1",
                        "predicted_static_p_Pa": "",
                        "predicted_p_rgh_Pa": "",
                        "predicted_heat_W": "",
                        "predicted_temperature_K": "",
                    }
                    if lane == "pressure_streamwise_map":
                        row["predicted_static_p_Pa"] = str(base + 1.0)
                    elif lane == "thermal_section_and_junction":
                        row["predicted_heat_W"] = str(base + 2.0)
                    elif lane == "sensor_temperature":
                        row["predicted_temperature_K"] = str(base + 3.0)
                    writer.writerow(row)
            summary = package.build(output_dir=output_dir, prediction_csv=prediction_csv)
            residuals = package.read_csv(output_dir / "val_salt2_external_residual_scorecard.csv")
            score_summary = package.read_csv(output_dir / "val_salt2_score_summary.csv")
            self.assertEqual(summary["freeze_status"], "external_prediction_csv_provided")
            self.assertEqual(summary["prediction_rows_joined"], 59)
            self.assertEqual(summary["policy_excluded_rows"], 2)
            by_lane = {row["evidence_lane"]: row for row in score_summary}
            self.assertEqual(by_lane["pressure_streamwise_map"]["rmse"], "1")
            self.assertEqual(by_lane["thermal_section_and_junction"]["rmse"], "2")
            self.assertEqual(by_lane["sensor_temperature"]["rmse"], "3")
            tp2 = [row for row in residuals if row["target_id"] == "TP2"][0]
            self.assertEqual(tp2["score_status"], "policy_excluded_not_scored")


if __name__ == "__main__":
    unittest.main()
