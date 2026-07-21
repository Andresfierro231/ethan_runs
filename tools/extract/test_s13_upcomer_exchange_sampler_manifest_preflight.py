#!/usr/bin/env python3
"""Tests for the S13 upcomer exchange sampler manifest preflight package."""

from __future__ import annotations

import csv
import unittest

from tools.extract import build_s13_upcomer_exchange_sampler_manifest_preflight as preflight


class S13UpcomerExchangeSamplerManifestPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = preflight.build()
        cls.manifest = cls.read_csv("case_vtk_input_manifest.preflight.csv")
        cls.missing = cls.read_csv("missing_input_matrix.csv")
        cls.report = cls.read_csv("manifest_validation_report.csv")
        cls.gate = cls.read_csv("harvest_gate.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (preflight.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_manifest_has_one_row_per_salt_case(self) -> None:
        self.assertEqual({row["case_id"] for row in self.manifest}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual(len(self.manifest), 3)
        self.assertTrue(all(row["cell_vtk"].endswith(".vtk") for row in self.manifest))
        self.assertTrue(all(row["volume_csv"].endswith(".csv") for row in self.manifest))

    def test_manifest_is_fail_closed_on_surface_and_normals(self) -> None:
        self.assertTrue(all(row["interface_vtk"] == "MISSING_EXCHANGE_INTERFACE_VTK" for row in self.manifest))
        self.assertTrue(all(row["wall_vtk"] == "MISSING_WALL_VTK" for row in self.manifest))
        self.assertTrue(all(row["throughflow_nx"] == "" for row in self.manifest))
        self.assertTrue(all(row["interface_nx"] == "" for row in self.manifest))

    def test_missing_input_matrix_blocks_harvest(self) -> None:
        missing_by_name = {row["input_name"] for row in self.missing if row["present"] == "false"}
        self.assertIn("interface_vtk", missing_by_name)
        self.assertIn("wall_vtk", missing_by_name)
        self.assertIn("throughflow_normal", missing_by_name)
        self.assertIn("interface_normal", missing_by_name)
        self.assertTrue(all(row["harvest_allowed"] == "false" for row in self.gate))

    def test_scaffold_validator_fails_as_expected(self) -> None:
        self.assertEqual(len(self.report), 1)
        self.assertEqual(self.report[0]["validation_status"], "expected_fail_closed")
        self.assertNotEqual(self.report[0]["return_code"], "0")
        self.assertTrue(self.summary["scaffold_validator_expected_to_fail"])

    def test_summary_has_no_launch_or_admission(self) -> None:
        self.assertEqual(self.summary["manifest_rows"], 3)
        self.assertEqual(self.summary["ready_manifest_rows"], 0)
        self.assertFalse(self.summary["harvest_allowed"])
        self.assertFalse(self.summary["sampler_launch_allowed"])
        self.assertFalse(self.summary["scheduler_action"])
        self.assertFalse(self.summary["solver_or_postprocessing_or_sampler_launched"])


if __name__ == "__main__":
    unittest.main()
