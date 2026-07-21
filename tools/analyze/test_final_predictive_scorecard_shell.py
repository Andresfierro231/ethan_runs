#!/usr/bin/env python3
"""Tests for AGENT-509 final predictive scorecard shell."""

from __future__ import annotations

import unittest

from tools.analyze import build_final_predictive_scorecard_shell as shell


class FinalPredictiveScorecardShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = shell.build()
        cls.case_rows = shell.read_csv(shell.OUT / "case_partition_contract.csv")
        cls.freeze_rows = shell.read_csv(shell.OUT / "model_freeze_contract.csv")
        cls.metric_rows = shell.read_csv(shell.OUT / "metric_contract.csv")
        cls.prediction_rows = shell.read_csv(shell.OUT / "prediction_join_shell.csv")
        cls.release_rows = shell.read_csv(shell.OUT / "holdout_release_gates.csv")
        cls.gate_rows = shell.read_csv(shell.OUT / "admission_gate_shell.csv")
        cls.runtime_rows = shell.read_csv(shell.OUT / "runtime_input_audit.csv")
        cls.source_property_gate_rows = shell.read_csv(shell.OUT / "source_property_label_gate_audit.csv")

    def test_training_partition_is_salt1_4_nominal_only(self) -> None:
        train = {
            row["case_key"]
            for row in self.case_rows
            if row["final_scorecard_partition"] == "train_nominal"
        }
        self.assertEqual(train, set(shell.FINAL_TRAINING_CASES))
        for row in self.case_rows:
            if row["case_key"] in shell.FINAL_TRAINING_CASES:
                self.assertEqual(row["original_split_fit_allowed"], "yes")
                self.assertEqual(row["original_split_model_selection_allowed"], "yes")
                self.assertEqual(row["split_fit_allowed"], "no_source_property_policy_blocked")
                self.assertEqual(row["split_model_selection_allowed"], "no_source_property_policy_blocked")

    def test_source_property_policy_blocks_all_training_fit_rows(self) -> None:
        by_case = {row["case_key"]: row for row in self.case_rows}
        self.assertEqual(by_case["salt1_nominal"]["source_property_label_coverage"], "source_property_resolution_policy_applied")
        self.assertEqual(by_case["salt1_nominal"]["fit_allowed"], "no")
        self.assertEqual(by_case["salt1_nominal"]["model_selection_allowed"], "no")
        self.assertEqual(by_case["salt1_nominal"]["property_mode"], shell.PREFERRED_PROPERTY_MODE)
        self.assertNotIn("refresh_required", by_case["salt1_nominal"]["property_mode"])
        self.assertEqual(
            by_case["salt1_nominal"]["source_property_gate_status"],
            "blocked_pending_row_specific_source_envelope",
        )
        self.assertEqual(
            by_case["salt1_nominal"]["fit_use_status"],
            "final_no_fit_source_property_resolution_policy",
        )

        for case_key in ("salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"):
            self.assertEqual(by_case[case_key]["source_property_label_coverage"], "source_property_resolution_policy_applied")
            self.assertEqual(by_case[case_key]["source_property_gate_status"], "blocked_source_envelope_not_strict_pass")
            self.assertEqual(by_case[case_key]["property_mode"], shell.PREFERRED_PROPERTY_MODE)
            self.assertEqual(by_case[case_key]["fit_allowed"], "no")
            self.assertEqual(by_case[case_key]["model_selection_allowed"], "no")
            self.assertEqual(
                by_case[case_key]["source_use_category"],
                "demoted_no_fit_due_to_source_envelope_blockers",
            )

    def test_current_blind_rows_are_score_only_after_freeze(self) -> None:
        by_case = {row["case_key"]: row for row in self.case_rows}
        for case_key in ("salt2_lo5q", "salt2_hi5q", "val_salt2"):
            self.assertEqual(by_case[case_key]["fit_allowed"], "no")
            self.assertEqual(by_case[case_key]["model_selection_allowed"], "no")
            self.assertEqual(by_case[case_key]["shell_score_status"], "blocked_pending_corrected_final_freeze")
            self.assertIn("requires_corrected_salt1_4_final_freeze", by_case[case_key]["release_gate"])

    def test_future_rows_are_present_and_blocked(self) -> None:
        future = {
            row["case_key"]: row
            for row in self.case_rows
            if row["final_scorecard_partition"].startswith("future_")
        }
        self.assertEqual(set(future), set(shell.FUTURE_PM10_CASES + shell.FUTURE_NEW_CFD_CASES))
        for row in future.values():
            self.assertEqual(row["fit_allowed"], "no")
            self.assertEqual(row["model_selection_allowed"], "no")
            self.assertTrue(row["shell_score_status"].startswith("blocked_pending"))

    def test_model_freeze_contract_has_pending_freeze_and_rejects_legacy_candidates(self) -> None:
        by_freeze = {row["freeze_id"]: row for row in self.freeze_rows}
        self.assertEqual(by_freeze["FINAL_FREEZE_TBD"]["freeze_status"], "not_created")
        legacy = [row for row in self.freeze_rows if row["freeze_id"] != "FINAL_FREEZE_TBD"]
        self.assertEqual(len(legacy), 4)
        self.assertTrue(all(row["freeze_status"] == "diagnostic_legacy_candidate_not_final_freeze" for row in legacy))

    def test_metric_contract_contains_required_lanes(self) -> None:
        metric_ids = {row["metric_id"] for row in self.metric_rows}
        self.assertTrue(
            {
                "loop_mdot_abs_error_pct",
                "all_probe_temperature_rmse_K",
                "pressure_streamwise_rmse_Pa",
                "thermal_section_heat_abs_residual_W",
                "pm5_upcomer_recirculation_diagnostic",
            }.issubset(metric_ids)
        )
        self.assertTrue(all(row["fit_or_selection_from_blind_rows"] == "no" for row in self.metric_rows))

    def test_prediction_shell_blocks_blind_and_future_rows(self) -> None:
        self.assertGreater(len(self.prediction_rows), 0)
        for row in self.prediction_rows:
            self.assertEqual(row["fit_allowed"], "no")
            self.assertEqual(row["model_selection_allowed"], "no")
        blind_or_future = [
            row
            for row in self.prediction_rows
            if row["final_scorecard_partition"] != "train_nominal"
        ]
        self.assertTrue(all(row["join_status"].startswith("blocked_pending") for row in blind_or_future))

    def test_release_gates_cover_current_and_future_tests(self) -> None:
        self.assertEqual({row["case_key"] for row in self.release_rows}, {
            "salt2_lo5q",
            "salt2_hi5q",
            "val_salt2",
            "salt2_lo10q",
            "salt2_hi10q",
            "salt4_lo10q",
            "salt4_hi10q",
            "salt3_q_insulation_matrix",
        })
        self.assertTrue(all(row["fit_allowed_after_release"] == "no" for row in self.release_rows))
        self.assertTrue(all(row["model_selection_allowed_after_release"] == "no" for row in self.release_rows))

    def test_admission_gates_record_current_blockers(self) -> None:
        by_gate = {row["gate_id"]: row for row in self.gate_rows}
        self.assertEqual(by_gate["corrected_split_freeze_exists"]["current_state"], "fail")
        self.assertEqual(by_gate["blind_rows_excluded_from_fit"]["current_state"], "pass")
        self.assertIn("fail", by_gate["pm10_terminal_admission"]["current_state"])

    def test_runtime_audit_passes(self) -> None:
        self.assertGreaterEqual(len(self.runtime_rows), 5)
        self.assertTrue(all(row["status"].startswith("pass") for row in self.runtime_rows))
        self.assertEqual(self.summary["runtime_audit_failures"], 0)
        self.assertEqual(self.summary["score_status"], "shell_ready_no_final_scores")

    def test_prediction_shell_carries_required_source_property_labels(self) -> None:
        self.assertGreater(len(self.prediction_rows), 0)
        for row in self.prediction_rows:
            for column in shell.REQUIRED_SOURCE_PROPERTY_COLUMNS:
                self.assertIn(column, row)
                self.assertTrue(row[column].strip(), (column, row))
            self.assertIn("source_property_gate_status", row)
            self.assertTrue(row["section_or_segment"].startswith("scorecard_case_aggregate:"))

        salt1_rows = [row for row in self.prediction_rows if row["case_key"] == "salt1_nominal"]
        self.assertTrue(salt1_rows)
        self.assertTrue(
            all(row["source_property_gate_status"] == "blocked_pending_row_specific_source_envelope" for row in salt1_rows)
        )
        self.assertTrue(all(row["fit_allowed"] == "no" for row in salt1_rows))

    def test_source_property_label_gate_audit_passes(self) -> None:
        self.assertEqual(len(self.source_property_gate_rows), 2)
        self.assertTrue(all(row["audit_status"] == "pass" for row in self.source_property_gate_rows))
        self.assertTrue(all(row["missing_required_label_rows"] == "0" for row in self.source_property_gate_rows))
        self.assertTrue(
            all(row["fit_or_selection_allowed_despite_missing_labels"] == "0" for row in self.source_property_gate_rows)
        )
        self.assertEqual(self.summary["source_property_gate_failures"], 0)
        self.assertEqual(
            self.summary["source_property_label_policy"],
            "final_source_envelope_resolution_policy_required_before_fit_or_model_selection",
        )


if __name__ == "__main__":
    unittest.main()
