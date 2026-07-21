#!/usr/bin/env python3
"""Tests for build_predictive_input_contract.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_predictive_input_contract as contract  # noqa: E402


class PredictiveInputContractTests(unittest.TestCase):
    def test_forbidden_validation_and_wallflux_fields_are_not_forward_runtime(self) -> None:
        rows = contract.build_runtime_contract_rows()
        violations = contract.validate_contract(rows)
        self.assertEqual(violations, [])
        by_field = {row["field_name"]: row for row in rows}
        for field in (
            "cfd_mdot_kg_s",
            "cfd_Tmean_K",
            "TP_TW_measured_K",
            "heater_wallHeatFlux_W",
            "cooler_wallHeatFlux_W",
        ):
            self.assertEqual(by_field[field]["forward_v0_imposed_cooler_allowed"], "false")

    def test_imposed_cooler_allowed_only_in_forward_v0(self) -> None:
        row = {
            item["field_name"]: item for item in contract.build_runtime_contract_rows()
        }["imposed_cooler_duty_W"]
        self.assertEqual(row["forward_v0_imposed_cooler_allowed"], "true")
        self.assertEqual(row["predictive_hx_allowed"], "false")

    def test_boundary_ambient_is_hA_weighted_and_skips_cooler(self) -> None:
        rows = [
            {"case_id": "salt_2", "role": "heater", "h_W_m2K": "2", "area_m2": "3", "Ta_K": "310"},
            {"case_id": "salt_2", "role": "passive", "h_W_m2K": "4", "area_m2": "1", "Ta_K": "300"},
            {"case_id": "salt_2", "role": "cooler", "h_W_m2K": "100", "area_m2": "100", "Ta_K": "999"},
        ]
        result = contract.boundary_ambient_by_case(rows)
        self.assertAlmostEqual(result["salt_2"], (6 * 310 + 4 * 300) / 10)

    def test_case_runtime_inputs_do_not_use_validation_targets_as_inputs(self) -> None:
        target_rows = [
            {
                "case_id": "salt_2",
                "source_id": "source",
                "heater_imposed_duty_W": "265.7",
                "cooler_removed_duty_W": "-136.351",
                "cfd_mdot_kg_s": "0.01318",
            }
        ]
        validation_rows = [{"case_name": "Salt 2", "air_T_inlet_C": "26.04", "air_flow_Lpm": "37.0"}]
        patch_rows = [{"case_id": "salt_2", "role": "heater", "h_W_m2K": "2", "area_m2": "3", "Ta_K": "299"}]
        rows = contract.build_case_runtime_inputs(target_rows, validation_rows, patch_rows)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["runtime_input_status"], "allowed_forward_v0_imposed_cooler")
        self.assertNotIn("cfd_mdot_kg_s", rows[0])
        self.assertAlmostEqual(rows[0]["imposed_cooler_duty_W"], 136.351)
        self.assertAlmostEqual(rows[0]["mdot_search_lower_kg_s"], 0.005)

    def test_litrev_gates_are_required_before_forward_scoring(self) -> None:
        rows = contract.build_runtime_contract_rows()
        by_field = {row["field_name"]: row for row in rows}
        for gate_name, gate_path in contract.REQUIRED_LITREV_GATES.items():
            self.assertIn(gate_name, by_field)
            row = by_field[gate_name]
            self.assertEqual(row["litrev_gate"], gate_name)
            self.assertEqual(row["litrev_gate_source_path"], contract.rel(gate_path))
            self.assertEqual(row["litrev_gate_required_before_scoring"], "true")
            self.assertTrue(gate_path.exists())


if __name__ == "__main__":
    unittest.main()
