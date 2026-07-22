#!/usr/bin/env python3
"""Tests for seeded S13 geometry-only surface VTK generation."""

from __future__ import annotations

import csv
import unittest

from tools.extract import build_s13_upcomer_exchange_surface_vtk_from_seeded_cv as builder


class S13SeededSurfaceVtkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = builder.build()
        cls.manifest = cls.read_csv("released_surface_vtk_manifest.csv")
        cls.validation = cls.read_csv("surface_vtk_validation.csv")
        cls.downstream = cls.read_csv("downstream_gate.csv")
        cls.guardrails = cls.read_csv("no_mutation_guardrails.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (builder.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_releases_two_geometry_surfaces_per_case(self) -> None:
        self.assertEqual(len(self.manifest), 6)
        self.assertEqual({row["case_id"] for row in self.manifest}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual(
            {row["surface_kind"] for row in self.manifest},
            {"exchange_interface", "trusted_wall"},
        )
        self.assertTrue(all(row["geometry_only"] == "true" for row in self.manifest))
        self.assertTrue(all(row["sampled_fields_present"] == "false" for row in self.manifest))
        self.assertEqual(self.summary["validated_surface_vtk_rows"], 6)
        self.assertTrue(self.summary["geometry_only_surface_vtk_released"])

    def test_vtk_files_are_nonblank_and_count_matched(self) -> None:
        for row in self.validation:
            vtk_path = builder.ROOT / row["vtk_path"]
            self.assertTrue(vtk_path.is_file())
            self.assertGreater(vtk_path.stat().st_size, 1000)
            self.assertEqual(row["expected_face_count"], "38880")
            self.assertEqual(row["vtk_polygons"], "38880")
            self.assertEqual(row["count_check"], "true")
            self.assertEqual(row["area_check"], "true")
            self.assertGreater(int(row["vtk_points"]), 0)

    def test_vtk_contains_polydata_and_cell_data(self) -> None:
        sample = builder.ROOT / self.manifest[0]["vtk_path"]
        text = sample.read_text(encoding="utf-8", errors="replace")
        self.assertIn("DATASET POLYDATA", text)
        self.assertIn("POLYGONS 38880", text)
        self.assertIn("CELL_DATA 38880", text)
        self.assertIn("SCALARS face_id int 1", text)
        self.assertIn("SCALARS area_m2 float 1", text)

    def test_downstream_gates_remain_blocked(self) -> None:
        self.assertTrue(all(row["status"] == "blocked" for row in self.downstream))
        self.assertTrue(all(row["allowed_next"] == "false" for row in self.downstream))
        self.assertFalse(self.summary["sampler_or_harvest_allowed"])
        self.assertFalse(self.summary["same_qoi_uq_ready"])
        self.assertFalse(self.summary["exchange_cell_coefficient_admission"])
        self.assertFalse(self.summary["s11_s12_s13_s15_s6_trigger"])

    def test_guardrails_preserve_no_mutation(self) -> None:
        self.assertTrue(all(row["changed"] == "false" for row in self.guardrails))
        self.assertFalse(self.summary["native_output_mutation"])
        self.assertFalse(self.summary["registry_or_admission_mutation"])
        self.assertFalse(self.summary["scheduler_action"])
        self.assertFalse(self.summary["openfoam_solver_or_postprocessing_launch"])


if __name__ == "__main__":
    unittest.main()
