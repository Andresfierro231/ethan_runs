#!/usr/bin/env python3
"""Tests for AGENT-503 val_salt2 pressure evidence/corner-K diagnosis."""

from __future__ import annotations

import unittest

from tools.analyze import build_val_salt2_pressure_evidence_corner_k_diagnosis as package


class ValSalt2PressureEvidenceCornerKDiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = package.build()
        cls.pressure = package.read_csv(package.OUT / "val_salt2_pressure_evidence_status.csv")
        cls.corner = package.read_csv(package.OUT / "corner_k_failure_modes.csv")
        cls.gates = package.read_csv(package.OUT / "corner_k_gate_matrix.csv")
        cls.policy = package.read_csv(package.OUT / "pressure_evidence_use_policy.csv")
        cls.queue = package.read_csv(package.OUT / "next_pressure_evidence_queue.csv")

    def test_val_salt2_branch_pressure_has_zero_fit_rows(self) -> None:
        self.assertEqual(len(self.pressure), 6)
        self.assertEqual(self.summary["val_salt2_branch_fit_admitted_rows"], 0)
        self.assertTrue(all(row["true_f_D_or_K_fit_admitted"] == "no" for row in self.pressure))
        self.assertTrue(all(row["fit_evidence_use"] == "diagnostic_pressure_map_only" for row in self.pressure))
        self.assertTrue(
            all(row["recirculation_mask_status"] == "blocked_material_recirculation_mask" for row in self.pressure)
        )

    def test_pressure_map_preserves_recirc_and_pressure_basis_flags(self) -> None:
        by_branch = {row["branch"]: row for row in self.pressure}
        self.assertEqual(by_branch["left_upper_leg"]["max_station_reverse_area_fraction_proxy"], "0.84")
        self.assertIn("pressure_definition_conflict", by_branch["lower_leg"]["blockers"])
        self.assertIn("pressure_definition_conflict", by_branch["test_section_span"]["blockers"])
        self.assertEqual(self.summary["val_salt2_pressure_definition_conflict_rows"], 2)

    def test_corner_k_has_zero_fit_rows_and_all_negative_centerline_k(self) -> None:
        self.assertEqual(len(self.corner), 12)
        self.assertEqual(self.summary["corner_fit_admitted_rows"], 0)
        self.assertEqual(self.summary["corner_centerline_negative_k_rows"], 12)
        self.assertTrue(all(row["fit_admitted"] == "no" for row in self.corner))
        self.assertTrue(all(row["centerline_local_K_negative"] == "yes" for row in self.corner))

    def test_centerline_straight_loss_over_subtracts_every_corner(self) -> None:
        ratios = [float(row["centerline_straight_to_feature_loss_ratio"]) for row in self.corner]
        self.assertTrue(all(ratio > 1.0 for ratio in ratios))
        self.assertTrue(all(row["primary_failure_mode"] == "straight_loss_reference_over_subtracts" for row in self.corner))
        self.assertTrue(all(float(row["centerline_subtraction_excess_pa"]) > 0.0 for row in self.corner))

    def test_gate_matrix_blocks_all_corner_fits(self) -> None:
        self.assertEqual(len(self.gates), 12)
        self.assertTrue(all(row["centerline_local_K_nonnegative_gate"] == "fail" for row in self.gates))
        self.assertTrue(all(row["recirculation_free_adjacent_branches_gate"] == "fail" for row in self.gates))
        self.assertTrue(all(row["same_qoi_mesh_gci_gate"] == "fail" for row in self.gates))
        self.assertTrue(all(row["component_isolated_gate"] == "fail" for row in self.gates))
        self.assertTrue(all(row["admission_decision"] == "blocked_keep_diagnostic" for row in self.gates))

    def test_policy_and_queue_are_explicit(self) -> None:
        policy = {row["evidence_object"]: row for row in self.policy}
        self.assertEqual(policy["val_salt2_streamwise_pressure_map"]["current_status"], "external_test_diagnostic_target")
        self.assertIn("training fit", policy["val_salt2_streamwise_pressure_map"]["forbidden_use"])
        self.assertEqual(policy["corner_K_local_centerline"]["current_status"], "invalid_for_fit_current_extraction")
        self.assertEqual([row["priority"] for row in self.queue], ["1", "2", "3", "4", "5"])
        self.assertEqual(self.queue[0]["action"], "resolve_pressure_basis")

    def test_machine_readable_answer_names_zero_fit_reason(self) -> None:
        answer = self.summary["plain_language_answer"]
        self.assertIn("0 fit-admitted", answer)
        self.assertIn("12/12 local centerline K values are negative", answer)
        self.assertEqual(self.summary["admission_change"], "none")


if __name__ == "__main__":
    unittest.main()
