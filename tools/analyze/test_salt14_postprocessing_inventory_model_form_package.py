#!/usr/bin/env python3
"""Tests for the Salt1-4 postProcessing inventory/model-form package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_salt14_postprocessing_inventory_model_form_package as pkg


class Salt14PostprocessingInventoryModelFormPackageTest(unittest.TestCase):
    def test_default_source_ids_include_registered_salt_rows(self) -> None:
        source_ids = pkg.default_source_ids()
        self.assertGreaterEqual(len(source_ids), 9)
        self.assertIn("viscosity_screening_salt_test_1_jin_coarse_mesh", source_ids)
        self.assertIn("viscosity_screening_salt_test_4_kirst_coarse_mesh", source_ids)

    def test_forbidden_runtime_quantities_are_diagnostic_only(self) -> None:
        for quantity in ("mdot_kg_s", "Q_wall_patch_W", "total_Q_postProc_W", "temperature_K"):
            self.assertEqual(pkg.admissibility_role(quantity), "diagnostic_only_forbidden_runtime_input")
        self.assertEqual(pkg.admissibility_role("avg_yplus"), "comparison_or_uq_support")
        self.assertEqual(pkg.admissibility_role("profile_Uy_m_s"), "comparison_or_uq_support")

    def test_window_stats_compute_drift_and_std(self) -> None:
        rows = [
            {
                "source_id": "demo",
                "case_id": "salt_test_1_jin",
                "case_family": "salt1",
                "function_object": "total_Q",
                "quantity": "total_Q_postProc_W",
                "patch_or_surface": "all_walls",
                "unit": "W",
                "admissibility_role": "diagnostic_only_forbidden_runtime_input",
                "time_s": "1.0",
                "value": "10.0",
            },
            {
                "source_id": "demo",
                "case_id": "salt_test_1_jin",
                "case_family": "salt1",
                "function_object": "total_Q",
                "quantity": "total_Q_postProc_W",
                "patch_or_surface": "all_walls",
                "unit": "W",
                "admissibility_role": "diagnostic_only_forbidden_runtime_input",
                "time_s": "2.0",
                "value": "12.0",
            },
        ]
        stats = pkg.build_window_stats(rows)
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]["n"], 2)
        self.assertEqual(stats[0]["drift_abs"], "2")
        self.assertEqual(stats[0]["drift_pct"], "20")

    def test_filtered_build_writes_required_schema_and_use_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "package"
            summary = pkg.build(
                ["viscosity_screening_salt_test_2_kirst_coarse_mesh"],
                out,
                profile_mode="none",
            )
            self.assertEqual(summary["source_count"], 1)
            self.assertGreater(summary["tidy_rows"], 0)
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["runtime_forbidden_inputs_released"])

            with (out / "salt14_postprocessing_tidy.csv").open(newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, pkg.TIDY_COLUMNS)
                rows = list(reader)
            self.assertTrue(rows)
            self.assertIn(
                "diagnostic_only_forbidden_runtime_input",
                {row["admissibility_role"] for row in rows},
            )

            with (out / "salt14_model_form_use_cases.csv").open(newline="") as handle:
                use_cases = list(csv.DictReader(handle))
            self.assertEqual({row["use_case_id"] for row in use_cases}, {
                "thermal_source_sink_diagnosis",
                "hydraulic_recirculation_support",
            })

            with (out / "salt14_inventory_manifest.csv").open(newline="") as handle:
                manifest = list(csv.DictReader(handle))
            self.assertEqual(manifest[0]["native_solver_output_mutated"], "false")
            self.assertEqual(manifest[0]["registry_or_admission_mutated"], "false")

            parsed_summary = json.loads((out / "summary.json").read_text())
            self.assertEqual(
                parsed_summary["decision"],
                "postprocessing_inventory_published_diagnostic_only_no_runtime_release",
            )


if __name__ == "__main__":
    unittest.main()
