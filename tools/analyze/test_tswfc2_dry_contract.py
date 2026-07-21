#!/usr/bin/env python3
"""Tests for AGENT-541 TSWFC2 dry contract package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_tswfc2_dry_contract as builder


class TSWFC2DryContractTests(unittest.TestCase):
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
            "node_geometry_contract.csv",
            "node_heat_ledger_contract.csv",
            "runtime_input_audit_contract.csv",
            "score_gate_contract.csv",
            "distinction_from_tswfc1.csv",
            "next_step_handoff.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)

        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-541")
        self.assertEqual(summary["decision"], "dry_contract_only_no_solver")
        self.assertEqual(summary["model_family"], "TSWFC2_distributed_test_section_wall_fluid_nodes")
        self.assertEqual(summary["priority_status"], "secondary_after_umx1_api_result")
        self.assertEqual(summary["node_contract_rows"], 4)
        self.assertEqual(summary["heat_ledger_rows"], 4)
        self.assertEqual(summary["runtime_audit_rows"], 5)
        self.assertEqual(summary["score_gate_rows"], 3)
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")
        self.assertEqual(summary["external_fluid_edit"], "none")

    def test_node_contract_is_distributed_not_single_node(self) -> None:
        rows = self.rows(self.build_tmp() / "node_geometry_contract.csv")
        node_ids = {row["node_id"] for row in rows}
        self.assertGreaterEqual(len(node_ids), 4)
        self.assertIn("TSWFC2_N02_test_section_lower", node_ids)
        self.assertIn("TSWFC2_N03_test_section_upper", node_ids)
        self.assertTrue(all(row["fluid_state"] for row in rows))
        self.assertTrue(all(row["inner_wall_state"] for row in rows))
        self.assertTrue(all(row["outer_wall_state"] for row in rows))
        self.assertTrue(all(row["status_before_implementation"] == "required_missing" for row in rows))

    def test_runtime_audit_blocks_forbidden_inputs_and_requires_labels(self) -> None:
        rows = self.rows(self.build_tmp() / "runtime_input_audit_contract.csv")
        by_id = {row["gate_id"]: row for row in rows}
        self.assertIn("realized CFD heat, mdot, or validation temperatures", by_id["RA1_setup_only_inputs"]["reason"])
        self.assertIn("single-node bulk-to-ambient fallback failed", by_id["RA2_distributed_nodes_present"]["reason"])
        self.assertIn("Salt1/Salt2/Salt4 nominal", by_id["RA3_salt1_role_rows"]["required_status"])
        self.assertIn("property and source-validity labels", by_id["RA5_source_property_labels"]["required_status"])

    def test_score_gates_prevent_mdot_only_or_policy_admission(self) -> None:
        rows = self.rows(self.build_tmp() / "score_gate_contract.csv")
        by_id = {row["gate_id"]: row for row in rows}
        self.assertIn("mdot abs error; TP RMSE; TW RMSE; all-probe RMSE", by_id["SG1_train_nominal"]["metric"])
        self.assertIn("mdot-only improvement", by_id["SG1_train_nominal"]["hard_no_go"])
        self.assertIn("Salt3 or blind rows used for parameter choice", by_id["SG2_validation_holdout"]["hard_no_go"])
        self.assertIn("TW5/TW6 always scoreable", by_id["SG3_sensor_policy"]["metric"])
        self.assertIn("posthoc sensor exclusion", by_id["SG3_sensor_policy"]["hard_no_go"])

    def test_distinction_from_tswfc1_is_explicit(self) -> None:
        rows = self.rows(self.build_tmp() / "distinction_from_tswfc1.csv")
        by_dimension = {row["dimension"]: row for row in rows}
        self.assertIn("single test-section bulk-to-ambient series resistance", by_dimension["topology"]["tswfc1_observed_behavior"])
        self.assertIn("distributed axial nodes", by_dimension["topology"]["tswfc2_required_difference"])
        self.assertIn("per-node conservation ledger", by_dimension["energy ledger"]["tswfc2_required_difference"])
        self.assertIn("zero mdot-only admissions", by_dimension["selection objective"]["acceptance_signal"])

    def test_next_step_handoff_waits_for_umx1_and_new_fluid_row(self) -> None:
        rows = self.rows(self.build_tmp() / "next_step_handoff.csv")
        by_rank = {int(row["rank"]): row for row in rows}
        self.assertEqual(by_rank[1]["next_step_id"], "NS1_wait_for_or_read_umx1_api_result")
        self.assertIn("AGENT-540", by_rank[1]["blocked_by"])
        self.assertIn("do not edit Fluid", by_rank[1]["guardrails"])
        self.assertEqual(by_rank[2]["next_step_id"], "NS2_external_fluid_design_row_if_needed")
        self.assertIn("no score grid", by_rank[2]["guardrails"])

    def test_source_manifest_inputs_exist(self) -> None:
        rows = self.rows(self.build_tmp() / "source_manifest.csv")
        self.assertGreaterEqual(len(rows), 9)
        self.assertTrue(all(row["exists"] == "True" for row in rows))


if __name__ == "__main__":
    unittest.main()
