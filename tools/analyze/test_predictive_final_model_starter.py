#!/usr/bin/env python3
"""Tests for predictive final model starter artifacts."""

from __future__ import annotations

import unittest

from tools.analyze import build_predictive_final_model_starter as starter


class PredictiveFinalModelStarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = starter.build()
        cls.baseline = starter.read_csv(starter.OUT / "baseline_model_contract.csv")
        cls.runtime = starter.read_csv(starter.OUT / "runtime_and_split_gate_audit.csv")
        cls.residual = starter.read_csv(starter.OUT / "residual_lane_readiness.csv")
        cls.queue = starter.read_csv(starter.OUT / "next_study_queue.csv")
        cls.freeze = starter.read_csv(starter.OUT / "freeze_readiness_matrix.csv")
        cls.release = starter.read_csv(starter.OUT / "scorecard_release_guardrails.csv")

    def test_stage0_baseline_is_explicit_and_non_scoring(self) -> None:
        by_id = {row["contract_id"]: row for row in self.baseline}
        self.assertEqual(by_id["B0_current_scorecard_shell"]["model_freeze_id"], "FINAL_FREEZE_TBD")
        self.assertEqual(by_id["B0_current_scorecard_shell"]["prediction_status"], "shell_ready_no_final_scores")
        self.assertEqual(by_id["B0_current_scorecard_shell"]["fit_allowed_rows_after_source_property_gate"], "0")
        self.assertEqual(by_id["B2_missing_predictions_explicit"]["prediction_status"], "no_final_frozen_prediction_artifact")

    def test_runtime_and_split_gates_pass(self) -> None:
        self.assertGreaterEqual(len(self.runtime), 8)
        self.assertTrue(all(row["status"].startswith("pass") for row in self.runtime))
        self.assertEqual(self.summary["runtime_split_gate_failures"], 0)

    def test_residual_readiness_preserves_blockers(self) -> None:
        by_lane = {row["lane"]: row for row in self.residual}
        self.assertIn("f6-friction-re-correction", by_lane["straight_developing_loss"]["open_blocker_ids"])
        self.assertIn("predictive-wall-test-section-submodels", by_lane["test_section_source_loss"]["open_blocker_ids"])
        self.assertEqual(by_lane["heater_transfer"]["readiness_status"], "baseline_or_boundary_evidence_available")
        self.assertEqual(by_lane["cooler_hx_removal"]["readiness_status"], "baseline_or_boundary_evidence_available")

    def test_next_study_queue_is_ordered_and_non_launching(self) -> None:
        stages = [row["stage_name"] for row in self.queue]
        self.assertEqual(
            stages,
            [
                "baseline_current_model",
                "external_bc_dictionary",
                "pressure_source_envelope",
                "heat_loss_network",
                "recirculation_guard",
                "final_scorecard",
            ],
        )
        self.assertTrue(all(row["launch_now"] == "no" for row in self.queue))
        self.assertEqual(self.queue[0]["implementation_status"], "complete_stage0_with_this_runner")

    def test_freeze_readiness_still_blocks_final_freeze(self) -> None:
        by_gate = {row["gate_id"]: row for row in self.freeze}
        self.assertEqual(by_gate["baseline_contract_ready"]["current_state"], "pass")
        self.assertEqual(by_gate["source_property_fit_release"]["current_state"], "fail")
        self.assertEqual(by_gate["corrected_split_freeze_exists"]["current_state"], "fail")
        self.assertGreater(self.summary["freeze_blocking_gate_rows"], 0)

    def test_release_guardrails_never_enable_fit_or_selection(self) -> None:
        release_rows = [row for row in self.release if row["guardrail_id"].startswith("release_")]
        self.assertTrue(release_rows)
        self.assertTrue(all(row["fit_allowed"] == "no" for row in release_rows))
        self.assertTrue(all(row["model_selection_allowed"] == "no" for row in release_rows))

    def test_summary_records_no_mutating_scientific_actions(self) -> None:
        self.assertEqual(self.summary["new_admissions"], 0)
        self.assertEqual(self.summary["solver_or_scheduler_actions"], 0)
        self.assertFalse(self.summary["native_output_mutation"])
        self.assertFalse(self.summary["registry_mutation"])
        self.assertFalse(self.summary["fluid_source_mutation"])


if __name__ == "__main__":
    unittest.main()

