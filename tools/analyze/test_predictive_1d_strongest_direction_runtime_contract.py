#!/usr/bin/env python3
"""Tests for the predictive 1D strongest-direction runtime contract packet."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_predictive_1d_strongest_direction_runtime_contract as builder  # noqa: E402


class Predictive1DStrongestDirectionContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()
        cls.out = builder.OUT
        with (cls.out / "summary.json").open(encoding="utf-8") as handle:
            cls.summary = json.load(handle)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_keeps_all_admission_paths_closed(self) -> None:
        self.assertEqual(
            self.summary["decision"],
            "strongest_predictive_1d_runtime_contract_working_locally_no_release_no_freeze",
        )
        for key in [
            "native_solver_outputs_mutated",
            "registry_or_admission_mutated",
            "scheduler_action",
            "solver_postprocessing_sampler_harvest_uq_launched",
            "fluid_or_external_edit",
            "source_property_release",
            "wall_integral_release",
            "numeric_passive_loss_release",
            "validation_holdout_external_scoring",
            "fitting_or_model_selection",
            "coefficient_admission",
            "candidate_freeze",
            "final_score_claim",
            "hidden_multiplier",
            "residual_absorbed_into_internal_Nu",
        ]:
            self.assertIs(self.summary[key], False, key)

    def test_runtime_schema_has_legal_core_and_blocked_residual_lanes(self) -> None:
        rows = {row["field"]: row for row in self.read_csv("runtime_input_schema.csv")}
        self.assertEqual(rows["heater_power_setpoint_W"]["runtime_legal"], "True")
        self.assertEqual(rows["passive_segment_area_m2"]["runtime_legal"], "True")
        self.assertEqual(rows["throughflow_enthalpy_W"]["runtime_legal"], "False")
        self.assertIn("same-basis endpoints", rows["throughflow_enthalpy_W"]["contract"])
        self.assertNotIn("wallHeatFlux", "\n".join(row["field"] for row in rows.values()))

    def test_passive_targets_cover_salt_2_3_4_train_context_rows(self) -> None:
        rows = self.read_csv("train_context_passive_h2_targets.csv")
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        for row in rows:
            conv = float(row["diagnostic_convective_W"])
            rad = float(row["diagnostic_radiative_W"])
            total = float(row["diagnostic_total_W"])
            self.assertEqual(row["component_count"], "5")
            self.assertAlmostEqual(conv + rad, total, places=10)
            self.assertEqual(row["runtime_use"], "target_only_until_runtime_operator_moves_heat_ledger")

    def test_generated_reference_kernel_computes_and_refuses_incomplete_residual(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "predictive_1d_reference_kernel",
            self.out / "predictive_1d_reference_kernel.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules["predictive_1d_reference_kernel"] = module
        spec.loader.exec_module(module)

        segment = module.PassiveSegment(
            name="unit",
            area_m2=2.0,
            h_external_W_m2_K=3.0,
            emissivity=0.5,
            surface_temperature_K=350.0,
            ambient_temperature_K=300.0,
            surroundings_temperature_K=300.0,
        )
        row = module.passive_segment_loss_W(segment, radiation_on=True)
        expected_conv = 2.0 * 3.0 * 50.0
        expected_rad = 0.5 * module.SIGMA_W_M2_K4 * 2.0 * (350.0**4 - 300.0**4)
        self.assertTrue(math.isclose(row["convective_W"], expected_conv, rel_tol=1e-12))
        self.assertTrue(math.isclose(row["radiative_W"], expected_rad, rel_tol=1e-12))

        blocked = module.open_cv_residual_W(
            heater_power_setpoint_W=1000.0,
            passive_loss_W=50.0,
            throughflow_enthalpy_W=None,
            storage_W=0.0,
            named_losses_W=0.0,
        )
        self.assertIs(blocked["computable"], False)
        self.assertIn("throughflow_enthalpy_W", blocked["missing"])

        complete = module.open_cv_residual_W(
            heater_power_setpoint_W=1000.0,
            passive_loss_W=50.0,
            throughflow_enthalpy_W=900.0,
            storage_W=20.0,
            named_losses_W=10.0,
        )
        self.assertIs(complete["computable"], True)
        self.assertEqual(complete["residual_W"], 20.0)

    def test_next_execution_plan_is_ordered_and_separate_from_this_packet(self) -> None:
        rows = self.read_csv("execution_plan.csv")
        self.assertEqual([row["order"] for row in rows], ["1", "2", "3", "4"])
        self.assertEqual(rows[0]["row_to_claim"], "TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22")
        self.assertTrue(all(row["may_run_now_from_this_packet"] == "False" for row in rows))


if __name__ == "__main__":
    unittest.main()
