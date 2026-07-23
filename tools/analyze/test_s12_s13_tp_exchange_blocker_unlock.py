#!/usr/bin/env python3
"""Tests for the S12/S13 TP-exchange blocker unlock package."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_s13_tp_exchange_blocker_unlock"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S12S13TPExchangeBlockerUnlockTests(unittest.TestCase):
    def test_summary_is_fail_closed_with_join_progress(self) -> None:
        with (OUT / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(
            summary["decision"],
            "s12_s13_blocker_progress_diagnostic_join_complete_release_gates_closed",
        )
        self.assertEqual(summary["s12_tp_join_rows"], 3)
        self.assertEqual(summary["source_property_overlay_rows"], 3)
        self.assertEqual(summary["s13_blocker_rows"], 5)
        self.assertEqual(summary["source_property_release_ready_rows"], 0)
        self.assertEqual(summary["s13_production_ready_blockers"], 0)
        self.assertEqual(summary["residual_value_release_rows"], 0)
        self.assertEqual(summary["candidate_freeze_rows"], 0)
        self.assertFalse(summary["scheduler_action"])
        self.assertFalse(summary["native_solver_outputs_mutated"])

    def test_tp_join_quantifies_retained_window_for_each_case(self) -> None:
        joined = rows("s12_tp_retained_window_exchange_join.csv")
        self.assertEqual({row["case_id"] for row in joined}, {"salt_2", "salt_3", "salt_4"})
        for row in joined:
            self.assertEqual(row["claim_status"], "diagnostic_join_complete_no_release_no_freeze")
            self.assertGreater(float(row["Q_wall_W_target"]), 0.0)
            self.assertGreater(float(row["source_side_q_net_W"]), float(row["Q_wall_W_target"]))
            self.assertGreater(float(row["Q_wall_over_source_side_q"]), 0.0)
            self.assertLess(float(row["Q_wall_over_source_side_q"]), 1.0)
            self.assertEqual(row["source_property_release_ready"], "False")

    def test_source_property_overlay_blocks_release_and_freeze(self) -> None:
        overlay = rows("source_property_legality_overlay.csv")
        self.assertEqual(len(overlay), 3)
        for row in overlay:
            self.assertEqual(row["release_ready"], "False")
            self.assertEqual(row["protected_row_release"], "False")
            self.assertEqual(row["final_fit_allowed"], "no")
            self.assertEqual(row["final_model_selection_allowed"], "no")
            self.assertEqual(row["s12_s13_freeze_ready"], "false")
            self.assertEqual(row["combined_release_decision"], "fail_closed_no_source_property_release")

    def test_s13_disposition_names_gci_endpoint_and_source_blockers(self) -> None:
        disposition = rows("s13_blocker_disposition.csv")
        blockers = {row["blocker"]: row for row in disposition}
        self.assertIn("s13_same_label_mesh_gci", blockers)
        self.assertIn("s13_throughflow_endpoint_geometry", blockers)
        self.assertIn("s13_s12_source_property_cp", blockers)
        for row in disposition:
            self.assertEqual(row["release_ready"], "false")
            self.assertEqual(row["production_use_allowed"], "false")
        self.assertEqual(blockers["s13_throughflow_endpoint_geometry"]["evidence_count"], "0")

    def test_next_action_contract_separates_local_and_compute_work(self) -> None:
        actions = rows("next_action_contract.csv")
        self.assertEqual(len(actions), 5)
        self.assertEqual(actions[0]["status_after_this_packet"], "completed_diagnostic_join")
        self.assertIn("endpoint", actions[1]["action"].lower())
        self.assertIn("scheduler", actions[2]["local_or_compute"])
        self.assertIn("source/property", actions[3]["action"])
        self.assertEqual(actions[4]["status_after_this_packet"], "closed")

    def test_guardrails_remain_false(self) -> None:
        guardrails = rows("no_mutation_guardrails.csv")
        self.assertGreaterEqual(len(guardrails), 8)
        for row in guardrails:
            self.assertEqual(row["value"], "false")

    def test_source_manifest_paths_exist(self) -> None:
        for row in rows("source_manifest.csv"):
            self.assertEqual(row["exists"], "true")
            self.assertTrue((ROOT / row["source_path"]).exists(), row["source_path"])


if __name__ == "__main__":
    unittest.main()
