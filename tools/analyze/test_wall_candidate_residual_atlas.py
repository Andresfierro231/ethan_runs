#!/usr/bin/env python3
"""Tests for AGENT-520 wall-candidate residual atlas."""

from __future__ import annotations

import unittest

from tools.analyze import build_wall_candidate_residual_atlas as atlas


class WallCandidateResidualAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = atlas.build()
        cls.gates = atlas.read_csv(atlas.OUT / "candidate_gate_matrix.csv")
        cls.probes = atlas.read_csv(atlas.OUT / "probe_residual_atlas.csv")
        cls.roles = atlas.read_csv(atlas.OUT / "role_segment_residual_rank.csv")
        cls.failures = atlas.read_csv(atlas.OUT / "thermal_failure_mode_decision.csv")
        cls.freeze = atlas.read_csv(atlas.OUT / "freeze_gate_status.csv")
        cls.next_decisions = atlas.read_csv(atlas.OUT / "next_candidate_decision.csv")
        cls.runtime = atlas.read_csv(atlas.OUT / "runtime_leakage_audit.csv")

    def test_completed_pb_and_wtd_rows_are_in_gate_matrix(self) -> None:
        completed = [row for row in self.gates if row["evidence_state"] == "completed"]
        self.assertGreaterEqual(len(completed), 14)
        families = {row["candidate_family"] for row in completed}
        self.assertIn("PB2_salt2_shape", families)
        self.assertIn("PB3_attenuated_shape", families)
        self.assertIn("WTD1_pipe_outer_wall_drive", families)
        self.assertIn("WTD2_outer_surface_drive", families)
        self.assertTrue(all(row["admission_decision"] == "not_admitted" for row in completed))

    def test_wtd1_repeats_mdot_temperature_tradeoff(self) -> None:
        wtd1 = [
            row for row in self.gates
            if row["candidate_family"] == "WTD1_pipe_outer_wall_drive"
            and row["split_role"] in {"validation", "holdout"}
        ]
        self.assertEqual(len(wtd1), 4)
        self.assertTrue(all(float(row["mdot_delta_vs_m3_pct"]) < 0.0 for row in wtd1))
        self.assertTrue(all(float(row["tw_delta_vs_m3_K"]) > 0.0 for row in wtd1))
        self.assertTrue(all(float(row["all_probe_delta_vs_m3_K"]) > 0.0 for row in wtd1))

    def test_agent511_is_not_treated_as_failure_evidence_when_pending(self) -> None:
        hs_rows = [row for row in self.failures if row["candidate_family"] == "HS1_heater_source_redistribution"]
        self.assertEqual(len(hs_rows), 1)
        if self.summary["agent511_completed_rows"] == 0:
            self.assertEqual(hs_rows[0]["failure_mode"], "pending_heater_source_scoring")
            self.assertEqual(self.next_decisions[0]["decision"], "complete_heater_source_redistribution_scoring_first")
            pending_gates = [row for row in self.gates if row["candidate_family"] == "HS1_heater_source_redistribution"]
            self.assertTrue(pending_gates)
            self.assertTrue(all(row["evidence_state"] != "completed" for row in pending_gates))

    def test_probe_and_role_residuals_are_available_from_agent513(self) -> None:
        self.assertGreaterEqual(len(self.probes), 100)
        self.assertGreaterEqual(len(self.roles), 50)
        self.assertTrue(any(row["source_package"] == "AGENT-513_wall_temperature_drive" for row in self.probes))
        self.assertTrue(any(float(row["abs_error_delta_vs_m3_K"]) > 0.0 for row in self.probes if row["abs_error_delta_vs_m3_K"]))
        self.assertTrue((atlas.OUT / "probe_residual_regression_rank.svg").exists())

    def test_freeze_remains_blocked_and_runtime_guardrails_pass(self) -> None:
        self.assertEqual(self.freeze[0]["current_status"], "blocked")
        self.assertEqual(self.freeze[0]["decision"], "do_not_build_corrected_freeze_yet")
        self.assertEqual(self.summary["freeze_status"], "blocked")
        self.assertEqual(self.summary["scientific_admission_change"], "none")
        self.assertEqual(self.summary["scheduler_action"], "none")
        self.assertTrue(all(row["status"] == "pass" for row in self.runtime))


if __name__ == "__main__":
    unittest.main()
