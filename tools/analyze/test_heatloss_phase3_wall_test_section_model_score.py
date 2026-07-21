#!/usr/bin/env python3
"""Tests for Phase 3 wall/test-section model-score gate artifacts."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_heatloss_phase3_wall_test_section_model_score as phase3


class HeatlossPhase3WallTestSectionModelScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = phase3.build()
        cls.candidates = cls.read_csv("wall_test_section_candidate_gate_scorecard.csv")
        cls.targets = cls.read_csv("heat_path_target_readiness.csv")
        cls.release = cls.read_csv("phase3_release_gate.csv")
        cls.runtime = cls.read_csv("runtime_thermal_input_audit.csv")
        cls.handoff = cls.read_csv("phase4_handoff_queue.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (phase3.OUT / name).open(newline="") as handle:
            return list(csv.DictReader(handle))

    def test_candidate_rows_cover_prior_wall_and_test_section_sources(self) -> None:
        self.assertEqual(self.summary["wall_candidate_rows"], 8)
        self.assertEqual(self.summary["test_section_candidate_rows"], 7)
        self.assertEqual(self.summary["candidate_gate_rows"], 15)
        families = {row["source_family"] for row in self.candidates}
        self.assertEqual(
            families,
            {"wall_thermal_circuit_study", "test_section_passive_loss_repair"},
        )

    def test_no_candidate_is_admitted(self) -> None:
        self.assertEqual(self.summary["admitted_candidate_rows"], 0)
        self.assertTrue(all(row["admission_decision"] == "not_admitted" for row in self.candidates))
        phase3_gate = next(row for row in self.release if row["gate_id"] == "phase3_admission_gate")
        self.assertEqual(phase3_gate["status"], "fail_no_candidate_admitted")

    def test_wall_rows_preserve_tw5_tw6_failure_evidence(self) -> None:
        wall_rows = [row for row in self.candidates if row["source_family"] == "wall_thermal_circuit_study"]
        self.assertTrue(wall_rows)
        self.assertTrue(any(row["validation_tw5_delta_vs_m3_K"] for row in wall_rows))
        self.assertTrue(any(row["validation_tw6_delta_vs_m3_K"] for row in wall_rows))
        self.assertTrue(any(row["holdout_tw5_delta_vs_m3_K"] for row in wall_rows))
        self.assertTrue(any(row["holdout_tw6_delta_vs_m3_K"] for row in wall_rows))

    def test_heat_targets_remain_diagnostic_not_direct_fit_targets(self) -> None:
        self.assertTrue(self.targets)
        self.assertTrue(
            all(
                row["phase3_target_status"] == "diagnostic_or_setup_only_not_direct_fit_target"
                for row in self.targets
            )
        )
        self.assertTrue(any(row["radiation_qr_presence_status"] == "absent_no_qr_output" for row in self.targets))
        self.assertTrue(any(row["storage_status"] == "absent_no_solid_storage_field" for row in self.targets))
        self.assertFalse(self.summary["qr_inferred"])
        self.assertFalse(self.summary["storage_inferred"])

    def test_runtime_audit_blocks_forbidden_inputs_and_execution(self) -> None:
        policies = " ".join(row["forbidden_runtime_inputs"] for row in self.runtime)
        for token in (
            "realized CFD wallHeatFlux",
            "CFD mdot",
            "imposed CFD cooler duty",
            "realized test-section heat",
            "validation temperatures",
        ):
            self.assertIn(token, policies)
        self.assertFalse(self.summary["fluid_or_openfoam_execution"])
        self.assertFalse(self.summary["native_solver_outputs_mutated"])
        self.assertFalse(self.summary["registry_or_admission_mutated"])
        self.assertFalse(self.summary["scheduler_action"])

    def test_phase4_handoff_is_explicit(self) -> None:
        self.assertGreaterEqual(self.summary["phase4_handoff_rows"], 1)
        self.assertTrue(
            all(
                row["next_task"] == "TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE"
                for row in self.handoff
            )
        )


if __name__ == "__main__":
    unittest.main()
