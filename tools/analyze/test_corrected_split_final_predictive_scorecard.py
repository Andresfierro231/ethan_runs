#!/usr/bin/env python3
"""Tests for AGENT-499 corrected-split final predictive scorecard."""

from __future__ import annotations

import unittest

from tools.analyze import build_corrected_split_final_predictive_scorecard as scorecard


class CorrectedSplitFinalPredictiveScorecardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = scorecard.build()
        cls.split_rows = scorecard.read_csv(scorecard.OUT / "split_legal_case_table.csv")
        cls.freeze_rows = scorecard.read_csv(scorecard.OUT / "candidate_freeze_manifest.csv")
        cls.coupled_rows = scorecard.read_csv(scorecard.OUT / "coupled_scorecard.csv")
        cls.blind_rows = scorecard.read_csv(scorecard.OUT / "blind_holdout_scorecard.csv")
        cls.gate_rows = scorecard.read_csv(scorecard.OUT / "admission_gate_review.csv")
        cls.future_rows = scorecard.read_csv(scorecard.OUT / "blocked_future_rows.csv")
        cls.runtime_rows = scorecard.read_csv(scorecard.OUT / "runtime_input_audit.csv")

    def test_final_training_set_is_salt1_4_nominal_only(self) -> None:
        training = {
            row["case_key"]
            for row in self.split_rows
            if row["corrected_scorecard_role"] == "final_training"
        }
        self.assertEqual(training, set(scorecard.FINAL_TRAINING_CASES))
        for row in self.split_rows:
            if row["case_key"] in scorecard.FINAL_TRAINING_CASES:
                self.assertEqual(row["final_fit_allowed"], "yes")
                self.assertEqual(row["final_model_selection_allowed"], "yes")
                self.assertEqual(row["blind_score_allowed_now"], "no")
        salt1 = {row["case_key"]: row for row in self.split_rows}["salt1_nominal"]
        self.assertEqual(salt1["current_readiness"], "ready_schema_promoted")

    def test_blind_holdout_and_external_rows_are_not_training_inputs(self) -> None:
        by_case = {row["case_key"]: row for row in self.split_rows}
        for case_key in ("salt2_lo5q", "salt2_hi5q", "val_salt2"):
            self.assertEqual(by_case[case_key]["final_fit_allowed"], "no")
            self.assertEqual(by_case[case_key]["final_model_selection_allowed"], "no")
            self.assertEqual(by_case[case_key]["blind_score_allowed_now"], "yes_after_final_freeze")
            self.assertIn("forbidden", by_case[case_key]["guardrail"])

    def test_existing_candidates_are_diagnostic_legacy_split_only(self) -> None:
        self.assertEqual(len(self.freeze_rows), 4)
        self.assertTrue(all(row["training_compliant"] == "no" for row in self.freeze_rows))
        self.assertTrue(
            all(row["corrected_split_freeze_status"] == "missing_not_frozen_on_salt1_4_nominal" for row in self.freeze_rows)
        )
        self.assertTrue(all(row["legacy_admission_status"] == "not_admitted" for row in self.freeze_rows))
        self.assertTrue(all("salt1_nominal" in row["missing_training_cases"] for row in self.freeze_rows))

    def test_coupled_scorecard_reclassifies_legacy_rows_and_marks_salt1_missing(self) -> None:
        legacy_rows = [
            row
            for row in self.coupled_rows
            if row["scorecard_use"] == "diagnostic_legacy_split_evidence_not_final_corrected_split"
        ]
        missing_salt1 = [
            row
            for row in self.coupled_rows
            if row["scorecard_use"] == "required_for_final_training_freeze_missing"
        ]
        self.assertEqual(len(legacy_rows), 12)
        self.assertEqual(len(missing_salt1), 4)
        self.assertTrue(all(row["corrected_split_training_compliant"] == "no" for row in self.coupled_rows))
        self.assertTrue(all(row["coupled_run_status"] == "missing_no_salt1_scenario_contract" for row in missing_salt1))

    def test_blind_rows_are_ready_but_blocked_until_final_freeze(self) -> None:
        self.assertEqual(len(self.blind_rows), 12)
        self.assertTrue(all(row["fit_allowed"] == "no" for row in self.blind_rows))
        self.assertTrue(all(row["model_selection_allowed"] == "no" for row in self.blind_rows))
        self.assertTrue(all(row["runtime_input_allowed"] == "no" for row in self.blind_rows))
        self.assertTrue(
            all(row["blind_score_status"] == "blocked_no_corrected_split_final_freeze" for row in self.blind_rows)
        )
        self.assertEqual({row["case_key"] for row in self.blind_rows}, {"salt2_lo5q", "salt2_hi5q", "val_salt2"})

    def test_future_rows_are_not_current_score_inputs(self) -> None:
        self.assertEqual({row["case_key"] for row in self.future_rows}, {
            "salt2_lo10q",
            "salt2_hi10q",
            "salt4_lo10q",
            "salt4_hi10q",
            "salt3_q_insulation_matrix",
        })
        self.assertTrue(all(row["score_allowed_now"] == "no" for row in self.future_rows))

    def test_admission_gates_reject_every_candidate(self) -> None:
        self.assertEqual(len(self.gate_rows), 4)
        self.assertTrue(all(row["corrected_split_freeze_gate"].startswith("fail") for row in self.gate_rows))
        self.assertTrue(all(row["legacy_coupled_gate"] == "fail" for row in self.gate_rows))
        self.assertTrue(all(row["pressure_model_gate"] == "fail_zero_fit_admitted" for row in self.gate_rows))
        self.assertTrue(all(row["final_candidate_admission"] == "not_admitted" for row in self.gate_rows))
        self.assertEqual(self.summary["final_admitted_candidates"], 0)

    def test_runtime_audit_passes(self) -> None:
        self.assertGreaterEqual(len(self.runtime_rows), 8)
        self.assertTrue(all(row["status"].startswith("pass") for row in self.runtime_rows))
        self.assertEqual(self.summary["runtime_audit_failures"], 0)


if __name__ == "__main__":
    unittest.main()
