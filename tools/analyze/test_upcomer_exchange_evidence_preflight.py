#!/usr/bin/env python3
"""Tests for the upcomer exchange-evidence preflight package."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_upcomer_exchange_evidence_preflight as preflight


class UpcomerExchangeEvidencePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = preflight.build()
        cls.variables = cls.read_csv("exchange_variable_availability.csv")
        cls.sampler_queue = cls.read_csv("scoped_sampler_source_queue.csv")
        cls.qoi_rows = cls.read_csv("upcomer_exchange_qoi_rows.csv")
        cls.uq_rows = cls.read_csv("same_qoi_uq_status.csv")
        cls.decisions = cls.read_csv("phase4b_rescore_decision.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (preflight.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_blocks_sampler_phase4b_and_phase5(self) -> None:
        self.assertFalse(self.summary["sampler_allowed_now"])
        self.assertFalse(self.summary["phase4b_ready"])
        self.assertEqual(self.summary["phase5_trigger"], "not_triggered")
        self.assertEqual(self.summary["exchange_cell_admission"], "none")
        self.assertEqual(self.summary["ordinary_internal_nu_admission"], "none")

    def test_required_variables_are_represented(self) -> None:
        ids = {row["variable_id"] for row in self.variables}
        for variable in {
            "V_recirc",
            "mdot_exchange",
            "tau_recirc",
            "T_main_T_recirc",
            "wall_core_delta_T",
            "pressure_residual_basis",
            "same_QOI_UQ",
            "energy_residual",
        }:
            self.assertIn(variable, ids)

    def test_energy_residual_is_diagnostic_not_admitted(self) -> None:
        row = {row["variable_id"]: row for row in self.variables}["energy_residual"]
        self.assertEqual(row["current_status"], "available_existing_diagnostic")
        self.assertEqual(row["source_status"], "available_existing_diagnostic_only")
        self.assertEqual(row["admission_use_now"], "false")
        self.assertEqual(row["requires_new_sampler"], "no")

    def test_exchange_state_variables_stay_blocked(self) -> None:
        by_id = {row["variable_id"]: row for row in self.variables}
        for variable in ("V_recirc", "mdot_exchange", "tau_recirc", "same_QOI_UQ"):
            self.assertEqual(by_id[variable]["available_existing_rows"], "0")
            self.assertEqual(by_id[variable]["admission_use_now"], "false")
            self.assertEqual(by_id[variable]["requires_new_sampler"], "yes")

    def test_sampler_queue_allows_no_immediate_launch(self) -> None:
        self.assertGreater(len(self.sampler_queue), 0)
        self.assertTrue(all(row["sampler_allowed_now"] == "false" for row in self.sampler_queue))
        self.assertTrue(all(row["phase4b_candidate_source"] == "false" for row in self.sampler_queue))

    def test_qoi_rows_are_diagnostic_only(self) -> None:
        self.assertGreater(len(self.qoi_rows), 0)
        self.assertTrue(all(row["admission_use"] == "false" for row in self.qoi_rows))
        self.assertTrue(all(row["preflight_use"] == "diagnostic_only" for row in self.qoi_rows))

    def test_same_qoi_and_pressure_remain_blocked(self) -> None:
        rows = {row["qoi_gate"]: row for row in self.uq_rows}
        self.assertEqual(rows["same_qoi_UQ"]["current_status"], "blocked_missing_same_qoi_UQ")
        self.assertEqual(rows["pressure_basis"]["scorecard_use_now"], "false")
        self.assertEqual(rows["thermal_energy_residual"]["scorecard_use_now"], "diagnostic_only")

    def test_phase4b_decision_preserves_no_admission(self) -> None:
        rows = {row["decision_id"]: row for row in self.decisions}
        self.assertEqual(rows["scoped_sampler_launch"]["status"], "blocked_no_launch_from_preflight")
        self.assertEqual(rows["phase4b_rescore"]["status"], "blocked_waiting_evidence")
        self.assertEqual(rows["phase5_trigger"]["status"], "not_triggered")
        for row in self.decisions:
            self.assertEqual(row["admission_change"], "none")

    def test_no_side_effect_claims(self) -> None:
        for key in (
            "native_output_mutation",
            "registry_mutation",
            "scheduler_action",
            "fluid_edit",
            "external_repo_edit",
            "fitting_or_model_selection",
            "closure_admission_change",
            "blocker_register_change",
        ):
            self.assertFalse(self.summary[key])


if __name__ == "__main__":
    unittest.main()
