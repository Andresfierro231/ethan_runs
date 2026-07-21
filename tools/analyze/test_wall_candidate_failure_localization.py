#!/usr/bin/env python3
"""Tests for AGENT-515 wall-candidate failure localization."""

from __future__ import annotations

import unittest

from tools.analyze import build_wall_candidate_failure_localization as package


class WallCandidateFailureLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = package.build()
        cls.gates = package.read_csv(package.OUT / "wall_candidate_gate_failure_matrix.csv")
        cls.shape = package.read_csv(package.OUT / "temperature_shape_regression_summary.csv")
        cls.gaps = package.read_csv(package.OUT / "probe_localization_data_gap.csv")
        cls.segments = package.read_csv(package.OUT / "segment_heat_placement_failure_modes.csv")
        cls.family = package.read_csv(package.OUT / "candidate_family_decision.csv")
        cls.ladder = package.read_csv(package.OUT / "next_candidate_ladder.csv")
        cls.freeze = package.read_csv(package.OUT / "freeze_unblock_decision.csv")
        cls.runtime = package.read_csv(package.OUT / "runtime_leakage_audit.csv")

    def test_agent498_candidates_are_not_admitted(self) -> None:
        self.assertEqual(len({row["candidate_id"] for row in self.gates}), 4)
        self.assertEqual(len(self.gates), 8)
        self.assertTrue(all(row["runtime_gate"] == "pass" for row in self.gates))
        self.assertTrue(all(row["admission_decision"] == "not_admitted" for row in self.gates))
        self.assertTrue(all(row["coupled_gate_for_split"] == "fail" for row in self.gates))

    def test_mdot_improves_but_temperature_regresses(self) -> None:
        for row in self.gates:
            self.assertLess(float(row["mdot_delta_vs_m3_pct"]), 0.0)
            self.assertGreater(float(row["all_probe_delta_vs_m3_K"]), 0.0)
            self.assertGreater(float(row["tw_delta_vs_m3_K"]), 0.0)
            self.assertEqual(row["gate_interpretation"], "mdot_improves_temperature_regresses")
        self.assertEqual(self.summary["mdot_improves_temperature_regresses_rows"], 8)

    def test_temperature_shape_summary_covers_pb1_pb2_pb3(self) -> None:
        families = {row["candidate_family"] for row in self.shape}
        self.assertEqual(families, {"PB1_passive_total", "PB2_salt2_shape", "PB3_attenuated_shape"})
        heldout = [row for row in self.shape if row["split_role"] in {"validation", "holdout"}]
        self.assertTrue(heldout)
        self.assertTrue(any(row["tp_delta_vs_m3_K"] == "" for row in heldout if row["candidate_family"] != "PB1_passive_total"))

    def test_probe_localization_gap_is_explicit(self) -> None:
        self.assertEqual(len(self.gaps), 3)
        self.assertTrue(all(row["status"] == "available" for row in self.gaps))
        self.assertTrue(all(int(row["detail_rows"]) > 0 for row in self.gaps))
        self.assertEqual(self.summary["probe_localization_empty_files"], 0)

    def test_segment_heat_placement_failure_modes_capture_physics(self) -> None:
        self.assertEqual(len(self.segments), 36)
        modes = {row["failure_mode"] for row in self.segments}
        self.assertIn("test_section_loss_underpredicted", modes)
        self.assertIn("junction_loss_overpredicted", modes)
        salt4_ts = [
            row
            for row in self.segments
            if row["case_id"] == "salt_4" and row["one_d_segment"] == "upcomer" and row["role"] == "test_section"
        ]
        self.assertTrue(salt4_ts)
        self.assertTrue(all(float(row["heat_error_W"]) < 0.0 for row in salt4_ts))

    def test_family_decisions_and_freeze_remain_blocked(self) -> None:
        decisions = {row["candidate_family"]: row["admission_decision"] for row in self.family}
        self.assertEqual(decisions["PB1_passive_total"], "not_admitted_legacy_passive_total")
        self.assertEqual(decisions["PB2_salt2_shape"], "not_admitted_diagnostic_only")
        self.assertEqual(decisions["PB3_attenuated_shape"], "not_admitted_diagnostic_only")
        self.assertEqual(self.freeze[0]["current_status"], "blocked")
        self.assertEqual(self.freeze[0]["decision"], "do_not_build_corrected_freeze_yet")
        self.assertEqual(self.summary["admitted_wall_candidates"], 0)

    def test_next_ladder_and_runtime_guardrails(self) -> None:
        self.assertEqual([row["priority"] for row in self.ladder], ["1", "2", "3", "4", "5"])
        self.assertIn("do_not_duplicate", self.ladder[0]["status"])
        self.assertTrue(all(row["status"] == "pass" for row in self.runtime))
        self.assertEqual(self.summary["runtime_audit_failures"], 0)
        self.assertEqual(self.summary["scientific_admission_change"], "none")
        self.assertTrue((package.OUT / "wall_candidate_gate_deltas.svg").exists())
        self.assertTrue((package.OUT / "segment_heat_placement_errors.svg").exists())


if __name__ == "__main__":
    unittest.main()
