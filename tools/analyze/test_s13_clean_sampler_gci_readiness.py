#!/usr/bin/env python3
"""Tests for the S13 clean sampler/GCI readiness package."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13CleanSamplerGCIReadinessTests(unittest.TestCase):
    def test_summary_requires_clean_rerun(self) -> None:
        with (OUT / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(
            summary["decision"],
            "s13_clean_sampler_gci_readiness_latest_split_rerun_complete_gci_blocked_by_coarse_no_harvest",
        )
        self.assertEqual(summary["face_lane_rows"], 18)
        self.assertEqual(summary["failed_package_terminal_window_reduction_rows"], 0)
        self.assertEqual(summary["failed_package_exact_label_qoi_rows"], 0)
        self.assertEqual(summary["latest_split_terminal_window_reduction_rows"], 18)
        self.assertEqual(summary["latest_split_exact_label_qoi_rows"], 72)
        self.assertEqual(summary["gci_ready_rows"], 0)
        self.assertEqual(summary["production_harvest_allowed_rows"], 0)
        self.assertFalse(summary["scheduler_action"])
        self.assertFalse(summary["native_solver_outputs_mutated"])

    def test_face_inventory_covers_all_case_mesh_lanes(self) -> None:
        inventory = rows("face_lane_contract_inventory.csv")
        self.assertEqual(len(inventory), 18)
        keys = {(row["case_id"], row["mesh_level"], row["face_lane"]) for row in inventory}
        for case_id in {"salt_2", "salt_3", "salt_4"}:
            for mesh in {"medium", "fine"}:
                for lane in {"exchange_interface", "trusted_wall", "cap"}:
                    self.assertIn((case_id, mesh, lane), keys)
        for row in inventory:
            self.assertEqual(row["exists"], "true")
            self.assertGreater(int(row["row_count"]), 0)

    def test_exchange_and_wall_lanes_show_partial_header_repair(self) -> None:
        inventory = rows("face_lane_contract_inventory.csv")
        critical = [row for row in inventory if row["face_lane"] in {"exchange_interface", "trusted_wall"}]
        self.assertEqual(len(critical), 12)
        ready = [row for row in critical if row["release_grade_for_lane"] == "true"]
        incomplete = [row for row in critical if row["release_grade_for_lane"] == "false"]
        self.assertEqual(len(ready), 6)
        self.assertEqual(len(incomplete), 6)
        for row in ready:
            self.assertEqual(row["has_area_vectors"], "true")
            self.assertEqual(row["has_owner_basis"], "true")
            self.assertEqual(row["has_normal_convention"], "true")
        for row in incomplete:
            self.assertEqual(row["has_area_vectors"], "false")
            self.assertIn("area_vector_x_m2", row["missing_required_columns"])

    def test_gci_matrix_blocks_all_qois_until_clean_rerun(self) -> None:
        matrix = rows("gci_go_no_go_matrix.csv")
        self.assertEqual(len(matrix), 4)
        for row in matrix:
            self.assertEqual(row["terminal_window_rows_available"], "18")
            self.assertEqual(row["exact_label_qoi_rows_available"], "72")
            self.assertEqual(row["formal_gci_status"], "blocked_coarse_equivalence_not_admitted")
            self.assertEqual(row["production_harvest_allowed"], "false")
            self.assertEqual(row["admission_allowed"], "false")
            self.assertIn("coarse equivalence", row["next_action"])

    def test_failure_reconciliation_reports_historical_errors(self) -> None:
        reconciliation = rows("sampler_failure_reconciliation.csv")
        self.assertEqual(len(reconciliation), 4)
        observed = " ".join(row["observed"] for row in reconciliation)
        self.assertIn("sampling_error_rows=6", observed)
        self.assertIn("6 case-mesh errors", observed)
        self.assertIn("aggregated_exact_label_qoi_rows=72", observed)
        self.assertIn("exchange_interface_ready=3/6", observed)
        self.assertIn("trusted_wall_ready=3/6", observed)

    def test_next_run_contract_skips_duplicate_medium_fine_rerun(self) -> None:
        contract = rows("clean_next_run_contract.csv")
        self.assertEqual([row["step"] for row in contract], ["medium_fine_sampler_rerun", "strict_coarse_equivalence_resolution", "post_rerun_gci_gate"])
        self.assertEqual(contract[0]["scheduler_required"], "false")
        self.assertIn("already complete", contract[0]["success_criterion"])
        self.assertIn("do not duplicate medium/fine sampler", contract[0]["forbidden"])
        self.assertIn("coarse equivalence", contract[1]["success_criterion"])
        self.assertEqual(contract[2]["scheduler_required"], "false")

    def test_latest_sampler_success_gate_records_completed_split_rerun(self) -> None:
        gate = rows("latest_sampler_success_gate.csv")
        self.assertEqual(len(gate), 1)
        row = gate[0]
        self.assertEqual(row["successful_case_mesh_pairs"], "6")
        self.assertEqual(row["terminal_window_reduction_rows"], "18")
        self.assertEqual(row["exact_label_qoi_rows"], "72")
        self.assertEqual(row["sampling_error_rows_in_successful_outputs"], "0")
        self.assertEqual(row["next_blocker"], "coarse_equivalence_not_admitted")

    def test_guardrails_are_closed(self) -> None:
        for row in rows("no_mutation_guardrails.csv"):
            self.assertEqual(row["value"], "false")


if __name__ == "__main__":
    unittest.main()
