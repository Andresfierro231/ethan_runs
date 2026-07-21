#!/usr/bin/env python3
"""Tests for Phase 4 upcomer exchange/internal-Nu gate artifacts."""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_heatloss_phase4_upcomer_exchange_and_internal_nu_gate as phase4


class HeatlossPhase4UpcomerExchangeInternalNuGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = phase4.build()
        cls.exchange = cls.read_csv("upcomer_exchange_cell_readiness.csv")
        cls.ordinary = cls.read_csv("ordinary_single_stream_nu_reopening_candidates.csv")
        cls.missing = cls.read_csv("missing_exchange_nu_evidence_queue.csv")
        cls.decisions = cls.read_csv("phase4_decision_gate.csv")
        cls.runtime = cls.read_csv("runtime_internal_nu_audit.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (phase4.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_exchange_rows_include_upcomer_and_test_section_diagnostics(self) -> None:
        features = {row["feature_or_span"] for row in self.exchange}
        self.assertIn("upcomer_inlet", features)
        self.assertIn("upcomer_mid", features)
        self.assertIn("upcomer_outlet", features)
        self.assertIn("test_section_span", features)
        self.assertGreater(self.summary["exchange_readiness_rows"], 0)

    def test_exchange_cell_not_calibration_ready(self) -> None:
        self.assertEqual(self.summary["exchange_cell_calibration_rows"], 0)
        self.assertTrue(
            all(row["exchange_cell_readiness"] != "ready_for_calibration" for row in self.exchange)
        )
        self.assertTrue(any(row["V_recirc_status"] == "missing" for row in self.exchange))
        self.assertTrue(any(row["mdot_exchange_status"] == "missing" for row in self.exchange))

    def test_ordinary_internal_nu_stays_closed(self) -> None:
        self.assertEqual(self.summary["ordinary_internal_nu_fit_rows"], 0)
        self.assertGreater(self.summary["ordinary_reopening_rows"], 0)
        self.assertTrue(
            all(row["ordinary_internal_Nu_fit_allowed"] == "false" for row in self.ordinary)
        )
        self.assertTrue(
            all(row["coefficient_admission_status"] == "no_coefficient_admission" for row in self.ordinary)
        )

    def test_missing_queue_contains_exchange_and_uncertainty_fields(self) -> None:
        statuses = {row["phase4_status"] for row in self.missing}
        self.assertIn("missing_V_recirc", statuses)
        self.assertIn("missing_mdot_exchange_and_tau_recirc", statuses)
        self.assertIn("blocked_missing_same_qoi_UQ", statuses)

    def test_decision_gate_blocks_phase5(self) -> None:
        decisions = {row["decision_id"]: row for row in self.decisions}
        self.assertEqual(decisions["phase5_release_gate"]["decision_status"], "not_triggered")
        self.assertEqual(self.summary["phase5_trigger"], "not_triggered")

    def test_runtime_guardrails_hold(self) -> None:
        policies = " ".join(row["policy"] for row in self.runtime)
        self.assertIn("forbidden", policies)
        self.assertFalse(self.summary["residual_absorbed_into_internal_nu"])
        self.assertFalse(self.summary["fitting_or_model_selection"])
        self.assertFalse(self.summary["admission_state_mutated"])
        self.assertFalse(self.summary["native_solver_outputs_mutated"])
        self.assertFalse(self.summary["scheduler_action"])


if __name__ == "__main__":
    unittest.main()
