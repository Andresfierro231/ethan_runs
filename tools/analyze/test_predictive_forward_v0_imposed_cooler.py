#!/usr/bin/env python3
"""Tests for run_predictive_forward_v0_imposed_cooler.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import run_predictive_forward_v0_imposed_cooler as runner  # noqa: E402


class PredictiveForwardV0Tests(unittest.TestCase):
    def test_run_plan_has_two_forward_variants_without_fixed_mdot_policy(self) -> None:
        rows = runner.run_plan_rows(
            [
                {
                    "case_id": "salt_2",
                    "fluid_case_name": "Salt 2",
                    "source_id": "source",
                    "imposed_cooler_duty_W": "136.351",
                    "boundary_ambient_Ta_K": "299.19",
                }
            ]
        )
        self.assertEqual({row["variant_id"] for row in rows}, {"F0_current_fluid_sources", "F1_heater_only"})
        self.assertTrue(all("solve mdot" in row["hydraulic_policy"] for row in rows))
        self.assertTrue(all("CFD mdot" in row["hydraulic_policy"] for row in rows))
        self.assertTrue(all("litrev_gate_policy" in row for row in rows))
        self.assertTrue(all("source envelope" in row["litrev_gate_policy"] for row in rows))

    def test_heater_only_variant_prescribes_only_heated_incline(self) -> None:
        class Case:
            heater_power_W = 265.7
            test_section_power_W = 37.0

        self.assertIsNone(runner.prescribed_sources_for(Case(), "F0_current_fluid_sources"))
        self.assertEqual(runner.prescribed_sources_for(Case(), "F1_heater_only"), {"heated_incline": 265.7})

    def test_model_loop_delta_proxy_uses_segment_temperature_span(self) -> None:
        class State:
            def __init__(self, value: float) -> None:
                self.T_avg_K = value

        class Result:
            segment_states = [State(450.0), State(455.5), State(449.5)]

        self.assertAlmostEqual(runner.model_loop_delta_proxy(Result()), 6.0)

    def test_cfd_sensor_reference_loader_maps_salt_labels(self) -> None:
        refs = runner.load_cfd_sensor_reference()
        self.assertIn(("salt_2", "TP1"), refs)
        self.assertEqual(refs[("salt_2", "TP1")]["kind"], "TP")

    def test_result_columns_do_not_duplicate_engine(self) -> None:
        self.assertEqual(runner.RESULT_COLUMNS.count("engine"), 1)

    def test_litrev_gate_reference_audit_requires_all_gates(self) -> None:
        runtime_contract = {
            row["field_name"]: row
            for row in runner.input_contract.build_runtime_contract_rows()
        }
        audits = runner.litrev_gate_reference_rows(runtime_contract)
        self.assertEqual(len(audits), len(runner.input_contract.REQUIRED_LITREV_GATES))
        self.assertTrue(all(row["scoring_admission_status"] == "pass" for row in audits))

        missing = dict(runtime_contract)
        missing.pop("source_envelope_gate")
        failed = runner.litrev_gate_reference_rows(missing)
        self.assertTrue(any(row["gate_name"] == "source_envelope_gate" and row["scoring_admission_status"] == "fail" for row in failed))
        with self.assertRaises(ValueError):
            runner.enforce_litrev_gate_references(failed)


if __name__ == "__main__":
    unittest.main()
