#!/usr/bin/env python3
"""Tests for the S13 throughflow endpoint-mask derivation package."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13ThroughflowEndpointMaskDerivationTests(unittest.TestCase):
    def test_summary_fails_closed_without_release(self) -> None:
        with (OUT / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(
            summary["decision"],
            "s13_throughflow_endpoint_masks_fail_closed_candidate_seed_cap_masks_only",
        )
        self.assertEqual(summary["case_rows"], 3)
        self.assertEqual(summary["released_endpoint_masks"], 0)
        self.assertEqual(summary["harvest_allowed_rows"], 0)
        self.assertEqual(summary["residual_value_release_rows"], 0)
        self.assertFalse(summary["native_output_mutated"])
        self.assertFalse(summary["scheduler_action"])

    def test_cap_inventory_has_three_available_case_rows(self) -> None:
        inventory = rows("classified_cap_face_inventory.csv")
        self.assertEqual(len(inventory), 3)
        for row in inventory:
            self.assertEqual(row["exists"], "true")
            self.assertEqual(int(row["row_count"]), 96)
            self.assertEqual(row["basic_face_ids_present"], "true")
            self.assertEqual(row["start_end_groups_present"], "true")
            self.assertEqual(row["release_columns_present"], "false")
            self.assertIn("area_vector_x_m2", row["missing_release_columns"])

    def test_endpoint_manifest_has_unreleased_inlet_outlet_rows(self) -> None:
        manifest = rows("endpoint_mask_manifest.csv")
        self.assertEqual(len(manifest), 6)
        labels = {row["endpoint_label"] for row in manifest}
        self.assertEqual(labels, {"open_cv_throughflow_inlet", "open_cv_throughflow_outlet"})
        for row in manifest:
            self.assertEqual(row["released"], "false")
            self.assertEqual(row["released_mask_path"], "")
            self.assertTrue(row["candidate_mask_path"])
            self.assertGreater(int(row["candidate_face_count"]), 0)
            self.assertIn("diagnostic candidate", row["basis"])

    def test_gate_blocks_harvest_and_residual_for_all_cases(self) -> None:
        gate = rows("endpoint_mask_derivation_gate.csv")
        self.assertEqual(len(gate), 3)
        for row in gate:
            self.assertEqual(row["cap_faces_available"], "true")
            self.assertEqual(row["candidate_endpoint_masks_written"], "2")
            self.assertEqual(row["released_endpoint_masks"], "0")
            self.assertEqual(row["normal_release_ready"], "false")
            self.assertEqual(row["area_release_ready"], "false")
            self.assertEqual(row["owner_cell_release_ready"], "false")
            self.assertEqual(row["throughflow_sign_convention_released"], "false")
            self.assertEqual(row["harvest_allowed"], "false")
            self.assertEqual(row["residual_value_release_allowed"], "false")
            self.assertIn("missing columns", row["blocking_reason"])

    def test_candidate_mask_files_exist_and_are_not_released(self) -> None:
        for row in rows("endpoint_mask_manifest.csv"):
            path = ROOT / row["candidate_mask_path"]
            self.assertTrue(path.exists(), row["candidate_mask_path"])
            with path.open(newline="", encoding="utf-8") as handle:
                candidate_rows = list(csv.DictReader(handle))
            self.assertEqual(len(candidate_rows), int(row["candidate_face_count"]))
            self.assertTrue(candidate_rows)
            for candidate in candidate_rows[:3]:
                self.assertEqual(candidate["candidate_only"], "true")
                self.assertEqual(candidate["release_ready"], "false")
                self.assertTrue(candidate["face_id"])

    def test_unblock_contract_names_exact_requirements(self) -> None:
        unblock = rows("next_unblock_contract.csv")
        self.assertGreaterEqual(len(unblock), 3)
        first = unblock[0]
        self.assertEqual(first["needed_artifact"], "released_open_cv_endpoint_face_masks")
        self.assertIn("area_vector", first["exact_requirement"])
        self.assertIn("owner_cell", first["exact_requirement"])
        self.assertIn("positive mdot convention", first["exact_requirement"])

    def test_source_manifest_has_no_mutation_or_scheduler_action(self) -> None:
        source = rows("source_manifest.csv")
        self.assertGreaterEqual(len(source), 5)
        for row in source:
            self.assertEqual(row["read_only"], "true")
            self.assertEqual(row["native_output_mutated"], "false")
            self.assertEqual(row["scheduler_action"], "false")


if __name__ == "__main__":
    unittest.main()
