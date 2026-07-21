#!/usr/bin/env python3
"""Tests for the 1D radiation sensitivity/capability package."""

from __future__ import annotations

import csv
import math
import unittest

from tools.analyze import build_1d_radiation_sensitivity as radiation


class OneDRadiationSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = radiation.build()
        cls.analytic = cls.read_csv("radiation_analytic_tests.csv")
        cls.sensitivity = cls.read_csv("radiation_sensitivity_scenarios.csv")
        cls.ledger = cls.read_csv("radiation_energy_ledger.csv")
        cls.runtime = cls.read_csv("runtime_double_counting_audit.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (radiation.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_analytic_contract(self) -> None:
        self.assertEqual(self.summary["analytic_tests_failed"], 0)
        self.assertTrue(all(row["pass_fail"] == "pass" for row in self.analytic))
        self.assertAlmostEqual(radiation.radiation_heat_w(0.0, 1.0, 350.0, 300.0), 0.0)
        self.assertAlmostEqual(radiation.radiation_heat_w(0.95, 1.0, 300.0, 300.0), 0.0)
        self.assertGreater(radiation.radiation_heat_w(0.95, 1.0, 350.0, 300.0), 0.0)
        self.assertLess(radiation.radiation_heat_w(0.95, 1.0, 290.0, 300.0), 0.0)

    def test_predictive_boundary_rows_are_scenario_expanded(self) -> None:
        self.assertEqual(self.summary["predictive_boundary_rows"], 15)
        self.assertEqual(self.summary["sensitivity_rows"], 75)
        self.assertEqual(self.summary["energy_ledger_rows"], 15)
        self.assertEqual({row["case_id"] for row in self.sensitivity}, {"salt_2", "salt_3", "salt_4"})

    def test_zero_delta_scenario_sums_to_zero(self) -> None:
        zero_rows = [row for row in self.ledger if row["scenario_id"] == "surface_equals_surroundings"]
        self.assertEqual(len(zero_rows), 3)
        self.assertTrue(all(math.isclose(float(row["sum_q_radiation_W"]), 0.0, abs_tol=1e-9) for row in zero_rows))

    def test_positive_and_negative_sensitivities_exist(self) -> None:
        positive = [row for row in self.ledger if row["scenario_id"] == "surface_plus_25K"]
        negative = [row for row in self.ledger if row["scenario_id"] == "surface_minus_10K"]
        self.assertTrue(all(float(row["sum_q_radiation_W"]) > 0.0 for row in positive))
        self.assertTrue(all(float(row["sum_q_radiation_W"]) < 0.0 for row in negative))

    def test_runtime_policy_prevents_double_counting(self) -> None:
        modes = {row["mode"]: row for row in self.runtime}
        self.assertEqual(modes["predictive_setup"]["radiation_term_status"], "allowed_from_setup_emissivity_Tsur_area_and_solved_surface_state")
        self.assertEqual(modes["cfd_total_heat_replay"]["radiation_term_status"], "disabled_to_prevent_double_counting")
        self.assertIn("no_separate_exported_qr", modes["split_qr_extraction"]["radiation_term_status"])
        self.assertFalse(self.summary["fluid_or_external_edit"])
        self.assertFalse(self.summary["admission_state_mutated"])


if __name__ == "__main__":
    unittest.main()
