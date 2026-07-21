#!/usr/bin/env python3
"""Tests for the S13 upcomer exchange surface VTK disposition package."""

from __future__ import annotations

import csv
import unittest

from tools.extract import build_s13_upcomer_exchange_surface_vtk_disposition as disposition


class S13UpcomerExchangeSurfaceVtkDispositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = disposition.build()
        cls.inputs = cls.read_csv("surface_input_disposition.csv")
        cls.released = cls.read_csv("released_surface_manifest.csv")
        cls.blocked = cls.read_csv("blocked_surface_manifest.csv")
        cls.normals = cls.read_csv("normal_vector_provenance.csv")
        cls.fragment = cls.read_csv("downstream_manifest_fragment.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (disposition.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_cell_vtk_is_ready_for_three_cases(self) -> None:
        ready = [row for row in self.inputs if row["input_lane"] == "cell_vtk" and row["release_status"] == "ready"]
        self.assertEqual({row["case_id"] for row in ready}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["surface_vtk_path"].endswith(".vtk") for row in ready))

    def test_no_surface_rows_are_released(self) -> None:
        self.assertEqual(self.released, [])
        self.assertFalse(self.summary["surface_vtk_extraction_allowed"])
        self.assertFalse(self.summary["harvest_allowed"])

    def test_blocked_manifest_covers_all_non_cell_lanes(self) -> None:
        self.assertEqual(len(self.blocked), 12)
        lanes = {row["blocked_lane"] for row in self.blocked}
        self.assertEqual(lanes, {"exchange_interface_vtk", "wall_core_vtk", "Q_wall_W", "exchange_cell_harvest"})

    def test_normals_are_not_numerically_released(self) -> None:
        self.assertEqual(len(self.normals), 3)
        self.assertTrue(all(row["current_normal_vector"] == "" for row in self.normals))
        self.assertTrue(all(row["normal_vector_status"] == "blocked_no_trusted_exchange_interface" for row in self.normals))

    def test_downstream_fragment_is_fail_closed_but_keeps_cell_vtks(self) -> None:
        self.assertEqual(len(self.fragment), 3)
        self.assertTrue(all(row["cell_vtk"].endswith(".vtk") for row in self.fragment))
        self.assertTrue(all(row["interface_vtk"] == "MISSING_EXCHANGE_INTERFACE_VTK" for row in self.fragment))
        self.assertTrue(all(row["wall_vtk"] == "MISSING_WALL_VTK" for row in self.fragment))


if __name__ == "__main__":
    unittest.main()
