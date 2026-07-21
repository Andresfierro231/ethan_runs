#!/usr/bin/env python3
"""Tests for Phase 5 negative heat-loss freeze artifacts."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_heatloss_phase5_frozen_scorecard_and_thesis_handoff as phase5


class HeatlossPhase5FrozenScorecardHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = phase5.build()
        cls.decisions = cls.read_csv("negative_freeze_decision.csv")
        cls.metrics = cls.read_csv("metric_score_availability.csv")
        cls.paths = cls.read_csv("heat_path_residual_freeze.csv")
        cls.actions = cls.read_csv("blocker_delta_next_actions.csv")
        cls.guardrails = cls.read_csv("runtime_source_split_guardrail_audit.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (phase5.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_negative_freeze_has_no_final_scores_or_candidates(self) -> None:
        self.assertEqual(self.summary["freeze_status"], "negative_freeze_no_runtime_legal_heatloss_candidate")
        self.assertEqual(self.summary["final_score_values_computed"], 0)
        self.assertEqual(self.summary["frozen_heatloss_candidates"], 0)
        phase5_row = next(row for row in self.decisions if row["phase"] == "phase5_negative_freeze")
        self.assertEqual(phase5_row["score_or_fit_status"], "no_final_accuracy_score_run")

    def test_phase4_gates_remain_closed(self) -> None:
        self.assertEqual(self.summary["phase4_exchange_fit_ready_rows"], 0)
        self.assertEqual(self.summary["phase4_reopened_internal_Nu_rows"], 0)
        phase4_row = next(row for row in self.decisions if row["phase"] == "phase4_exchange_internal_nu_gate")
        self.assertIn("no_exchange_fit_or_internal_Nu_reopen", phase4_row["score_or_fit_status"])

    def test_metric_rows_include_required_qoi_families(self) -> None:
        metric_ids = {row["metric_id"] for row in self.metrics}
        for metric in (
            "loop_mdot_abs_error_pct",
            "all_probe_temperature_rmse_K",
            "tp_sensor_rmse_K",
            "tw_sensor_rmse_K",
            "thermal_section_heat_abs_residual_W",
            "branch_heat_residual_by_path",
            "loop_delta_T_heatloss",
        ):
            self.assertIn(metric, metric_ids)
        self.assertTrue(all(row["final_score_value_status"] == "not_computed_negative_freeze" for row in self.metrics))

    def test_heat_paths_keep_residual_explicit(self) -> None:
        self.assertTrue(self.paths)
        self.assertTrue(all(row["freeze_status"] == "not_admitted" for row in self.paths))
        self.assertTrue(all(row["residual_lane_status"] == "explicit_not_hidden_in_internal_Nu" for row in self.paths))
        self.assertFalse(self.summary["residual_hidden_in_internal_Nu"])

    def test_next_actions_are_shortest_evidence_path(self) -> None:
        blockers = {row["blocker"] for row in self.actions}
        self.assertIn("external_boundary_dictionary_not_runtime_ready", blockers)
        self.assertIn("upcomer_exchange_state_missing", blockers)
        self.assertIn("same_qoi_uncertainty_missing", blockers)
        self.assertIn("ordinary_internal_Nu_gates_closed", blockers)

    def test_guardrails_block_runtime_and_split_leakage(self) -> None:
        self.assertTrue(all(row["status"] == "pass" for row in self.guardrails))
        self.assertFalse(self.summary["fit_or_model_selection_performed"])
        self.assertFalse(self.summary["native_solver_outputs_mutated"])
        self.assertFalse(self.summary["registry_or_admission_mutated"])
        self.assertFalse(self.summary["scheduler_action"])
        self.assertFalse(self.summary["external_fluid_edit"])
        self.assertFalse(self.summary["thesis_files_edited"])


if __name__ == "__main__":
    unittest.main()
