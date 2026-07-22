#!/usr/bin/env python3
"""Tests for the S13 seeded-CV surface/input manifest package."""

from __future__ import annotations

import csv
import unittest

from tools.extract import build_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv as manifest


class S13SeededSurfaceInputManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = manifest.build()
        cls.inventory = cls.read_csv("seeded_surface_input_inventory.csv")
        cls.seeded_manifest = cls.read_csv("seeded_surface_input_manifest.csv")
        cls.existence = cls.read_csv("input_file_existence_checks.csv")
        cls.matrix = cls.read_csv("case_preflight_matrix.csv")
        cls.downstream_gate = cls.read_csv("downstream_gate.csv")
        cls.decision = cls.read_csv("surface_input_decision.csv")
        cls.guardrails = cls.read_csv("no_mutation_guardrails.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (manifest.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_inventory_profiles_seeded_inputs(self) -> None:
        rows = {row["source_id"]: row for row in self.inventory}
        for source_id in (
            "seeded_release_decision",
            "seeded_recirc_cv_cells",
            "seeded_exchange_interface_faces",
            "seeded_trusted_wall_faces",
            "seeded_wall_core_band",
            "seeded_normal_convention",
            "seeded_source_sink_boundary_ledger",
            "surface_contract",
        ):
            self.assertEqual(rows[source_id]["exists"], "True")
            self.assertEqual(rows[source_id]["header_status"], "pass")
            self.assertEqual(rows[source_id]["missing_columns"], "")

        self.assertEqual(rows["seeded_recirc_cv_cells"]["row_count"], "116640")
        self.assertEqual(rows["seeded_exchange_interface_faces"]["row_count"], "116640")
        self.assertEqual(rows["seeded_trusted_wall_faces"]["row_count"], "116640")

    def test_three_cases_release_surface_extraction_inputs_only(self) -> None:
        self.assertEqual({row["case_id"] for row in self.matrix}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual(len(self.matrix), 3)
        self.assertTrue(all(row["surface_extraction_ready"] == "true" for row in self.matrix))
        self.assertTrue(all(row["seeded_surface_input_ready_for_extraction_task"] == "true" for row in self.matrix))
        self.assertTrue(all(row["sampler_manifest_ready"] == "false" for row in self.matrix))
        self.assertTrue(all(row["sampler_harvest_allowed"] == "false" for row in self.matrix))
        self.assertTrue(all(row["same_qoi_uq_ready"] == "false" for row in self.matrix))
        self.assertTrue(all(row["exchange_cell_admission_allowed"] == "false" for row in self.matrix))

    def test_seeded_manifest_and_split_files_exist(self) -> None:
        self.assertEqual(len(self.seeded_manifest), 3)
        self.assertEqual(len(self.existence), 24)
        self.assertTrue(all(row["ready_for_surface_extraction"] == "true" for row in self.seeded_manifest))
        self.assertTrue(all(row["surface_vtk_extraction_launched"] == "false" for row in self.seeded_manifest))
        self.assertTrue(all(row["sampler_ready"] == "false" for row in self.seeded_manifest))
        self.assertTrue(all(row["harvest_allowed"] == "false" for row in self.seeded_manifest))
        self.assertTrue(all(row["exists"] == "true" for row in self.existence))
        self.assertTrue(all(row["blocks_surface_extraction"] == "false" for row in self.existence))
        self.assertTrue(all(row["blocks_sampler_or_harvest"] == "true" for row in self.existence))
        for row in self.seeded_manifest:
            for input_name in (
                "recirc_cell_mask",
                "exchange_interface_faces_csv",
                "trusted_wall_faces_csv",
                "wall_core_band_csv",
                "classified_cap_faces_csv",
            ):
                self.assertTrue((manifest.ROOT / row[input_name]).exists())

    def test_blocking_reasons_keep_raw_sampling_and_energy_lanes_closed(self) -> None:
        for row in self.matrix:
            self.assertEqual(row["Q_wall_W_released"], "false")
            self.assertIn("raw_interface_wall_sampled_vtk_not_ready", row["blocking_reason"])
            self.assertIn("Q_wall_W_not_released", row["blocking_reason"])
            self.assertIn("same_window_sampler_outputs_not_generated", row["blocking_reason"])

    def test_decision_releases_no_sampler_or_admission(self) -> None:
        self.assertEqual(len(self.decision), 1)
        self.assertEqual(self.decision[0]["decision"], "release_surface_extraction_input_manifest_only")
        self.assertEqual(self.decision[0]["surface_extraction_ready"], "true")
        self.assertEqual(self.decision[0]["sampler_manifest_ready"], "false")
        self.assertEqual(self.decision[0]["sampler_harvest_allowed"], "false")
        self.assertEqual(self.decision[0]["same_qoi_uq_ready"], "false")
        self.assertEqual(self.decision[0]["exchange_cell_admission_allowed"], "false")
        self.assertEqual(len(self.downstream_gate), 3)
        self.assertTrue(all(row["surface_extraction_allowed_next_row"] == "true" for row in self.downstream_gate))
        self.assertTrue(all(row["production_harvest_allowed"] == "false" for row in self.downstream_gate))

    def test_summary_and_guardrails(self) -> None:
        self.assertEqual(self.summary["surface_extraction_ready_rows"], 3)
        self.assertEqual(self.summary["seeded_surface_manifest_rows"], 3)
        self.assertEqual(self.summary["input_file_existence_check_rows"], 24)
        self.assertEqual(self.summary["sampler_manifest_ready_rows"], 0)
        self.assertFalse(self.summary["sampler_harvest_allowed"])
        self.assertFalse(self.summary["same_qoi_uq_ready"])
        self.assertFalse(self.summary["exchange_cell_admission_allowed"])
        self.assertFalse(self.summary["s11_s12_s13_s15_s6_trigger"])
        self.assertFalse(self.summary["native_output_mutation"])
        self.assertFalse(self.summary["registry_or_admission_mutation"])
        self.assertFalse(self.summary["scheduler_action"])
        self.assertFalse(self.summary["solver_or_postprocessing_or_sampler_launched"])
        self.assertTrue(all(row["status"] == "false" for row in self.guardrails))


if __name__ == "__main__":
    unittest.main()
