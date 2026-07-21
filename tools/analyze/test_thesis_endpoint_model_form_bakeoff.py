#!/usr/bin/env python3
"""Tests for TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF outputs."""

from __future__ import annotations

import unittest

from tools.analyze import build_thesis_endpoint_model_form_bakeoff as bakeoff


class ThesisEndpointModelFormBakeoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = bakeoff.build()
        cls.contracts = bakeoff.read_csv(bakeoff.OUT / "model_form_contracts.csv")
        cls.scores = bakeoff.read_csv(bakeoff.OUT / "model_form_scores.csv")
        cls.costs = bakeoff.read_csv(bakeoff.OUT / "model_form_costs.csv")
        cls.failures = bakeoff.read_csv(bakeoff.OUT / "model_form_failure_modes.csv")
        cls.claims = bakeoff.read_csv(bakeoff.OUT / "thesis_claim_ledger.csv")
        cls.audit = bakeoff.read_csv(bakeoff.OUT / "runtime_leakage_audit.csv")

    def test_all_required_model_forms_are_present_once(self) -> None:
        expected = {"M0", "M1", "M2", "M3", "M4"}
        for rows in (self.contracts, self.scores, self.costs, self.failures, self.claims):
            self.assertEqual({row["model_form_id"] for row in rows}, expected)
            self.assertEqual(len(rows), 5)
        self.assertEqual(self.summary["model_forms"], 5)

    def test_locked_split_is_encoded_for_predictive_contracts(self) -> None:
        by_id = {row["model_form_id"]: row for row in self.contracts}
        for form_id in ("M0", "M2", "M3", "M4"):
            self.assertEqual(by_id[form_id]["train_rows"], bakeoff.TRAIN_ROWS)
            self.assertEqual(by_id[form_id]["score_rows"], bakeoff.CURRENT_SCORE_ROWS)
            self.assertEqual(by_id[form_id]["future_score_rows"], bakeoff.FUTURE_SCORE_ROWS)
        self.assertEqual(by_id["M1"]["train_rows"], "none_for_predictive_training")

    def test_diagnostic_and_predictive_labels_are_preserved(self) -> None:
        by_id = {row["model_form_id"]: row for row in self.contracts}
        self.assertEqual(by_id["M1"]["predictive_or_diagnostic"], "diagnostic_replay_only")
        self.assertIn("diagnostic", by_id["M4"]["predictive_or_diagnostic"])
        self.assertIn("admitted", by_id["M2"]["admission_status"])
        self.assertIn("blocked", by_id["M3"]["admission_status"])

    def test_scores_have_explicit_missing_or_diagnostic_statuses(self) -> None:
        by_id = {row["model_form_id"]: row for row in self.scores}
        self.assertEqual(by_id["M0"]["score_status"], "prediction_missing_not_run")
        self.assertEqual(by_id["M1"]["runtime_leakage_status"], "diagnostic_leakage_by_design")
        self.assertIn("prediction_missing", by_id["M2"]["score_status"])
        self.assertIn("final_prediction_missing", by_id["M3"]["score_status"])
        self.assertIn("prediction_missing", by_id["M4"]["score_status"])

    def test_numeric_evidence_is_carried_where_available(self) -> None:
        by_id = {row["model_form_id"]: row for row in self.scores}
        self.assertNotEqual(by_id["M1"]["mdot_error_pct"], "")
        self.assertNotEqual(by_id["M1"]["tp_sensor_error_K"], "")
        self.assertNotEqual(by_id["M2"]["branch_heat_residual_W"], "")
        self.assertNotEqual(by_id["M3"]["all_probe_error_K"], "")
        self.assertIn("corner_fit_admitted_rows=0", by_id["M4"]["pressure_residual_movement"])

    def test_failure_modes_link_to_current_blockers(self) -> None:
        by_id = {row["model_form_id"]: row for row in self.failures}
        self.assertIn("predictive-wall-test-section-submodels", by_id["M2"]["blocker_linkage"])
        self.assertIn("local_wall_temperature", by_id["M3"]["blocker_linkage"])
        self.assertIn("corner_K", by_id["M4"]["blocker_linkage"])

    def test_runtime_audit_passes(self) -> None:
        self.assertGreaterEqual(len(self.audit), 5)
        self.assertTrue(all(row["status"].startswith("pass") for row in self.audit))
        self.assertEqual(self.summary["runtime_audit_failures"], 0)


if __name__ == "__main__":
    unittest.main()
