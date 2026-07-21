#!/usr/bin/env python3
"""Tests for the val_salt2 external-test ledger builder."""

from __future__ import annotations

import unittest

from tools.analyze import build_val_salt2_external_test_ledger as ledger


class ValSalt2ExternalLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ledger.build()
        cls.patch_rows = ledger.read_csv(ledger.OUT / "val_salt2_external_patch_heat_ledger.csv")
        cls.section_rows = ledger.read_csv(ledger.OUT / "val_salt2_external_section_heat_ledger.csv")
        cls.junction_rows = ledger.read_csv(ledger.OUT / "val_salt2_external_junction_split.csv")
        cls.target_rows = ledger.read_csv(ledger.OUT / "val_salt2_external_pressure_thermal_sensor_targets.csv")
        cls.audit_rows = ledger.read_csv(ledger.OUT / "val_salt2_external_runtime_input_audit.csv")
        cls.decisions = ledger.read_csv(ledger.OUT / "val_salt2_external_admission_decision.csv")

    def test_agent483_counts_are_carried_forward(self) -> None:
        self.assertEqual(len(self.patch_rows), 69)
        self.assertEqual(len(self.junction_rows), 4)
        self.assertGreaterEqual(len(self.section_rows), 1)
        self.assertEqual({row["case_key"] for row in self.patch_rows}, {"val_salt2"})

    def test_section_reconciliation_residual_is_small(self) -> None:
        residuals = [abs(ledger.fnum(row["latest_residual_patch_minus_ledger_w"])) for row in self.section_rows]
        self.assertLess(max(residuals), 1.0e-6)
        self.assertTrue(all(row["reconciliation_status"] == "pass" for row in self.section_rows))

    def test_junction_split_closes_to_known_loss(self) -> None:
        total = sum(ledger.fnum(row["realized_external_loss_positive_W"]) for row in self.junction_rows)
        self.assertAlmostEqual(total, 40.9260865692, places=9)
        self.assertTrue(all(row["target_family"] == "junction_stub_heat" for row in self.junction_rows))

    def test_targets_include_pressure_thermal_and_sensor_policy(self) -> None:
        target_types = {row["target_type"] for row in self.target_rows}
        self.assertIn("pressure_streamwise_map", target_types)
        self.assertIn("section_heat", target_types)
        self.assertIn("junction_stub_heat", target_types)
        self.assertIn("sensor_temperature_policy", target_types)
        sensor_rows = [row for row in self.target_rows if row["target_type"] == "sensor_temperature_policy"]
        self.assertEqual(len(sensor_rows), 17)
        self.assertTrue(all(row["case_specific_numeric_target_available_here"] == "no" for row in sensor_rows))

    def test_external_policy_blocks_fit_and_runtime_heat_inputs(self) -> None:
        policy_rows = self.patch_rows + self.section_rows + self.junction_rows
        self.assertTrue(all(row["external_test_only"] == "yes" for row in policy_rows))
        self.assertTrue(all(row["fit_allowed"] == "no" for row in policy_rows))
        self.assertTrue(all(row["model_selection_allowed"] == "no" for row in policy_rows))
        self.assertTrue(all(row["runtime_wallHeatFlux_allowed"] == "no" for row in policy_rows))

    def test_admission_decision_keeps_val_salt2_external_only(self) -> None:
        self.assertEqual(len(self.decisions), 1)
        decision = self.decisions[0]
        self.assertEqual(decision["admission_status"], "external_test_ledger_ready_training_forbidden")
        self.assertEqual(decision["external_test_only"], "yes")
        self.assertEqual(decision["training_input_allowed"], "no")
        self.assertEqual(decision["fit_allowed"], "no")
        self.assertEqual(decision["runtime_wallHeatFlux_allowed"], "no")

    def test_runtime_input_audit_is_all_pass(self) -> None:
        self.assertGreaterEqual(len(self.audit_rows), 5)
        self.assertTrue(all(row["status"].startswith("pass") for row in self.audit_rows))


if __name__ == "__main__":
    unittest.main()
