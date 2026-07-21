#!/usr/bin/env python3
"""Tests for AGENT-525 two-tap component repair contract."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_two_tap_component_repair_contract as builder  # noqa: E402


class TwoTapComponentRepairContractTests(unittest.TestCase):
    def build_tmp(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name)
        builder.build_package(out)
        return out

    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_outputs_and_summary(self) -> None:
        out = self.build_tmp()
        for name in [
            "README.md",
            "component_repair_targets.csv",
            "repair_field_contract.csv",
            "future_extractor_schema.csv",
            "acceptance_gate_matrix.csv",
            "repair_contract_summary.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-525")
        self.assertEqual(summary["component_repair_target_rows"], 3)
        self.assertEqual(summary["ordinary_admitted_now"], 0)
        self.assertEqual(summary["field_contract_rows"], 7)
        self.assertEqual(summary["future_schema_rows"], 17)
        self.assertEqual(summary["acceptance_gate_rows"], 5)
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")

    def test_targets_are_current_corner_lower_right_rows_only(self) -> None:
        rows = self.rows(self.build_tmp() / "component_repair_targets.csv")
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["feature"] for row in rows}, {"corner_lower_right"})
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        for row in rows:
            self.assertEqual(row["readiness_status"], "extraction_required_component_or_cluster")
            self.assertEqual(row["ordinary_admission_now"], "no")
            self.assertIn("same_qoi_mesh_gci_missing", row["blocking_fields"])
            self.assertIn("final_pressure_basis", row["immediate_required_repair"])
            self.assertTrue(row["centerline_tap_length_m"])

    def test_field_contract_blocks_shortcuts(self) -> None:
        rows = self.rows(self.build_tmp() / "repair_field_contract.csv")
        fields = {row["field"]: row for row in rows}
        for expected in {
            "final_pressure_basis",
            "final_velocity_basis",
            "centerline_tap_length_m",
            "straight_loss_subtraction_pa",
            "component_isolation_label",
            "RAF_RMF_SVF",
            "same_qoi_mesh_time_UQ",
        }:
            self.assertIn(expected, fields)
            self.assertEqual(fields[expected]["reject_if_missing_or_ambiguous"], "yes")
        self.assertIn("double-counted", fields["final_pressure_basis"]["acceptance_rule"])
        self.assertIn("RAF < 0.01", fields["RAF_RMF_SVF"]["acceptance_rule"])

    def test_gates_and_schema_cover_future_extractor(self) -> None:
        out = self.build_tmp()
        gates = {row["gate"]: row for row in self.rows(out / "acceptance_gate_matrix.csv")}
        self.assertEqual(
            set(gates),
            {
                "pressure_and_velocity_basis",
                "straight_reference",
                "component_isolation",
                "recirculation_policy",
                "same_qoi_mesh_time_UQ",
            },
        )
        self.assertIn("clip negative K", gates["straight_reference"]["forbidden_shortcut"])
        self.assertIn("universal component K", gates["component_isolation"]["forbidden_shortcut"])
        schema_columns = {row["column"] for row in self.rows(out / "future_extractor_schema.csv")}
        for expected in {"K_local", "RAF", "RMF", "SVF", "mesh_time_uncertainty", "admission_status"}:
            self.assertIn(expected, schema_columns)


if __name__ == "__main__":
    unittest.main()
