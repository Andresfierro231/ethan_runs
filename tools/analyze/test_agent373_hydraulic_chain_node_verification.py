#!/usr/bin/env python3
"""Tests for AGENT-421 AGENT-373 hydraulic-chain verification."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_agent373_hydraulic_chain_node_verification as build


class Agent373HydraulicChainNodeVerificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build.build()
        cls.package = build.PACKAGE

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.package / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_contract(self) -> None:
        summary = json.loads((self.package / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-421")
        self.assertTrue(summary["agent373_stage_logic_rerun"])
        self.assertEqual(summary["raw_two_tap_rows"], 3)
        self.assertEqual(summary["raw_two_tap_fit_admitted_rows"], 0)
        self.assertEqual(summary["pm5_rows"], 12)
        self.assertEqual(summary["pm5_wallHeatFlux_rows"], 12)
        self.assertEqual(summary["f6_fit_admitted_rows"], 0)
        self.assertEqual(summary["final_hydraulic_residual_status"], "blocked_not_final")
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["registry_or_admission_mutated"])

    def test_admission_lanes_are_not_fit_promoted(self) -> None:
        rows = self.read_csv("hydraulic_admission_final_decisions.csv")
        by_item = {row["evidence_item"]: row for row in rows}
        self.assertEqual(by_item["raw_two_tap_test_section_complex"]["admission_lane"], "diagnostic_admitted_pressure_scale_only")
        self.assertEqual(by_item["raw_two_tap_test_section_complex"]["fit_admitted_rows"], "0")
        self.assertEqual(by_item["fluid_reset_k_diagnostic_sweep"]["admission_lane"], "diagnostic_admitted_component_separation_only")
        self.assertEqual(by_item["f6_ready_to_run_gate"]["fit_admitted_rows"], "0")
        self.assertEqual(by_item["pm5_matched_pressure_upcomer"]["diagnostic_admitted_rows"], "12")

    def test_chain_execution_outputs_landed(self) -> None:
        rows = self.read_csv("chain_execution_verification.csv")
        by_item = {row["item"]: row for row in rows}
        for item in ("test_section_complex_raw_two_tap", "f6_ready_to_run_gate", "fluid_reset_k_diagnostic_sweep"):
            self.assertEqual(by_item[item]["rerun_on_node_or_consumed"], "rerun_on_node")
            self.assertEqual(by_item[item]["output_exists"], "true")
        self.assertEqual(by_item["raw_two_tap_agent409_staged_copy"]["row_count"], "3")
        self.assertEqual(by_item["pm5_matched_pressure_upcomer"]["row_count"], "12")

    def test_final_residual_remains_blocked_for_right_reason(self) -> None:
        rows = self.read_csv("final_hydraulic_residual_attribution.csv")
        final = [row for row in rows if row["residual_component"] == "final_hydraulic_residual"]
        self.assertEqual(len(final), 1)
        self.assertEqual(final[0]["final_numeric_residual_status"], "blocked_not_final")
        self.assertIn("no fit-admitted raw pressure/F6 rows", final[0]["limitation"])


if __name__ == "__main__":
    unittest.main()
