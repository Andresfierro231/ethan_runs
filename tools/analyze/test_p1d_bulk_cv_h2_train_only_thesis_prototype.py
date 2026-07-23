#!/usr/bin/env python3
"""Tests for the P1D bulk-CV-H2 train-only thesis prototype packet."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_p1d_bulk_cv_h2_train_only_thesis_prototype as builder  # noqa: E402


class P1DBulkCvH2TrainOnlyPrototypeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()
        cls.out = builder.OUT
        with (cls.out / "summary.json").open(encoding="utf-8") as handle:
            cls.summary = json.load(handle)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_is_working_prototype_but_not_admitted(self) -> None:
        self.assertEqual(
            self.summary["decision"],
            "p1d_bulk_cv_h2_train_only_prototype_runs_scorecard_blocked_no_freeze",
        )
        self.assertEqual(self.summary["train_context_case_rows"], 3)
        self.assertEqual(self.summary["nonzero_passive_h2_rows"], 3)
        self.assertEqual(self.summary["source_property_release_ready_rows"], 0)
        self.assertEqual(self.summary["same_basis_residual_computable_cases"], 0)
        for key in [
            "source_property_release",
            "Qwall_release",
            "validation_holdout_external_scoring",
            "protected_scoring",
            "fitting_or_model_selection",
            "coefficient_admission",
            "candidate_freeze",
            "final_score_claim",
            "hidden_multiplier",
            "residual_absorbed_into_internal_Nu",
        ]:
            self.assertIs(self.summary[key], False, key)

    def test_generated_kernel_runs_and_blocks_missing_residual_terms(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "p1d_bulk_cv_h2_candidate_model",
            self.out / "p1d_bulk_cv_h2_candidate_model.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules["p1d_bulk_cv_h2_candidate_model"] = module
        spec.loader.exec_module(module)

        blocked = module.run_prototype(
            module.PrototypeInputs(
                case_id="unit",
                heater_power_setpoint_W=1000.0,
                passive_h2_loss_W=40.0,
            )
        )
        self.assertFalse(blocked["residual_computable"])
        self.assertIn("throughflow_enthalpy_W", blocked["missing_residual_terms"])
        self.assertEqual(blocked["open_cv_residual_W"], None)

        complete = module.run_prototype(
            module.PrototypeInputs(
                case_id="unit",
                heater_power_setpoint_W=1000.0,
                passive_h2_loss_W=40.0,
                throughflow_enthalpy_W=900.0,
                storage_W=10.0,
                named_losses_W=5.0,
            )
        )
        self.assertTrue(complete["residual_computable"])
        self.assertAlmostEqual(complete["passive_fraction_of_heater"], 0.04)
        self.assertAlmostEqual(complete["open_cv_residual_W"], 45.0)

    def test_train_context_outputs_are_nonzero_and_not_scores(self) -> None:
        rows = self.read_csv("train_context_prototype_outputs.csv")
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        for row in rows:
            self.assertGreater(float(row["prototype_passive_h2_loss_W"]), 0.0)
            self.assertEqual(row["residual_computable_now"], "False")
            self.assertEqual(row["protected_scoring"], "False")
            self.assertEqual(row["candidate_freeze"], "False")

    def test_source_property_and_residual_gates_fail_closed(self) -> None:
        source_rows = self.read_csv("source_property_repair_status.csv")
        self.assertEqual(len(source_rows), 4)
        self.assertTrue(all(row["release_ready"] == "False" for row in source_rows))
        residual_rows = self.read_csv("residual_completion_gate.csv")
        self.assertGreaterEqual(len(residual_rows), 21)
        self.assertTrue(all(row["ready_now"] == "False" for row in residual_rows))

    def test_scorecard_shell_has_no_score_values(self) -> None:
        rows = self.read_csv("blocked_scorecard_shell.csv")
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["score_status"], "blocked_no_freeze")
            self.assertEqual(row["score_value"], "")
            self.assertEqual(row["protected_scoring"], "False")
            self.assertEqual(row["final_score_claim"], "False")


if __name__ == "__main__":
    unittest.main()
