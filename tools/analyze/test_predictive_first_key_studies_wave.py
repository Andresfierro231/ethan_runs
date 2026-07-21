#!/usr/bin/env python3
"""Tests for the predictive first-key-studies wave package."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_predictive_first_key_studies_wave as wave


class PredictiveFirstKeyStudiesWaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = wave.build()
        cls.status = cls.read_csv("first_key_study_wave_status.csv")
        cls.baseline = cls.read_csv("baseline_control_surface.csv")
        cls.external = cls.read_csv("external_bc_completion_matrix.csv")
        cls.split_heat = cls.read_csv("split_heat_completion_matrix.csv")
        cls.pressure = cls.read_csv("pressure_source_envelope_release_gate.csv")
        cls.gates = cls.read_csv("next_gate_queue.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (wave.OUT / name).open(newline="") as handle:
            return list(csv.DictReader(handle))

    def test_s0_to_s3_are_represented(self) -> None:
        self.assertEqual({row["study_id"] for row in self.status}, {"S0", "S1", "S2", "S3"})
        self.assertEqual(self.summary["wave_rows"], 4)

    def test_baseline_keeps_final_freeze_blocked(self) -> None:
        statuses = {row["final_freeze_status"] for row in self.baseline}
        self.assertIn("FINAL_FREEZE_TBD_absent", statuses)
        self.assertFalse(self.summary["final_freeze_exists"])

    def test_external_bc_marks_fluid_api_open(self) -> None:
        joined = " ".join(row["fluid_api_status"] for row in self.external)
        self.assertIn("TODO-FLUID-EXTERNAL-BC-DICT", joined)
        self.assertFalse(self.summary["fluid_edit"])

    def test_split_heat_keeps_qr_and_storage_unadmitted(self) -> None:
        for row in self.split_heat:
            self.assertEqual(row["qr_output_rows_admitted"], "0")
            self.assertEqual(row["solid_storage_runtime_rows_admitted"], "0")

    def test_pressure_gate_admits_no_component_k_or_f6(self) -> None:
        self.assertEqual(self.summary["component_k_admitted_rows"], 0)
        self.assertEqual(self.summary["f6_admitted_rows"], 0)
        for row in self.pressure:
            self.assertEqual(row["component_k_admitted_rows"], "0")
            self.assertEqual(row["f6_admitted_rows"], "0")

    def test_next_gate_queue_preserves_claim_boundaries(self) -> None:
        gates = {row["gate"]: row for row in self.gates}
        self.assertIn("TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE", gates)
        self.assertEqual(gates["TODO-HEATLOSS-PHASE-5-FROZEN-SCORECARD-AND-THESIS-HANDOFF"]["launch_now"], "no_trigger_gated")

    def test_no_runtime_or_split_leakage_failures(self) -> None:
        self.assertEqual(self.summary["runtime_or_split_leakage_failures"], 0)
        self.assertFalse(self.summary["model_scoring_or_admission"])


if __name__ == "__main__":
    unittest.main()
