#!/usr/bin/env python3
"""Tests for the S13 residual-complete open-CV contract builder."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_s13_residual_complete_open_cv_energy_balance_contract as builder


class S13ResidualCompleteOpenCVContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.build()
        cls.out_dir = builder.OUT_DIR

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.out_dir / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_fail_closed(self) -> None:
        summary = json.loads((self.out_dir / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(
            summary["decision"],
            "residual_complete_open_cv_contract_defined_fail_closed_no_residual_value_no_admission",
        )
        self.assertEqual(summary["case_budget_rows"], 3)
        self.assertEqual(summary["same_basis_residual_computable_rows"], 0)
        self.assertEqual(summary["residual_value_released_rows"], 0)
        self.assertFalse(summary["coefficient_admission"])
        self.assertFalse(summary["source_property_release"])

    def test_case_budget_releases_no_residual_values(self) -> None:
        rows = self.read_csv("case_budget_skeleton.csv")
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["residual_value_released"] == "false" for row in rows))
        self.assertTrue(all(row["can_compute_same_basis_residual_now"] == "false" for row in rows))

    def test_missing_gates_include_core_blockers(self) -> None:
        gates = {row["missing_input_or_gate"] for row in self.read_csv("missing_input_gate.csv")}
        self.assertIn("row_specific_cp_property_release", gates)
        self.assertIn("throughflow_enthalpy_endpoints", gates)
        self.assertIn("same_label_mesh_GCI_or_admitted_equivalence", gates)
        self.assertIn("source_property_Qwall_release", gates)

    def test_harvest_lanes_are_diagnostic_only(self) -> None:
        rows = self.read_csv("harvest_lane_requirements.csv")
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["admission_use_now"] == "false" for row in rows))

    def test_required_inputs_and_progression_name_next_harvest(self) -> None:
        inputs = {row["input_label"]: row for row in self.read_csv("required_input_matrix.csv")}
        self.assertEqual(inputs["H_throughflow_net_W"]["release_ready"], "false")
        self.assertIn("endpoint", inputs["H_throughflow_net_W"]["current_status"])
        gates = {row["gate"]: row for row in self.read_csv("progression_gate.csv")}
        self.assertEqual(gates["predictive_1d_next_step"]["status"], "open_next_harvest_only")

    def test_storage_policy_forbids_hidden_nu(self) -> None:
        rows = {row["term"]: row for row in self.read_csv("storage_and_named_loss_policy.csv")}
        self.assertEqual(rows["Q_storage_W"]["default_status"], "missing_not_zero")
        self.assertIn("internal Nu", rows["Q_other_named_losses_W"]["forbidden_use"])

    def test_source_manifest_has_existing_sources(self) -> None:
        rows = self.read_csv("source_manifest.csv")
        self.assertGreaterEqual(len(rows), 5)
        for row in rows:
            self.assertTrue((builder.ROOT / row["source_path"]).exists(), row["source_path"])


if __name__ == "__main__":
    unittest.main()
