"""Tests for physical segment interface temperature sampling."""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sample_physical_segment_interface_temperatures as sampler


class PhysicalSegmentInterfaceSamplingTests(unittest.TestCase):
    def test_registry_covers_expected_physical_segments(self):
        rows = sampler.build_interface_registry(sampler.DEFAULT_RECON_ROOT)
        segments = {row["physical_segment"] for row in rows}
        self.assertLessEqual({"lower_leg", "cooling_branch", "downcomer", "upcomer", "junction"}, segments)
        self.assertEqual(len(rows), 15)
        junction = [row for row in rows if row["physical_segment"] == "junction"]
        self.assertTrue(junction)
        self.assertTrue(
            all(row["bracket_status"] == "not_bracketed_by_available_secmean_surfaces" for row in junction)
        )

    def test_interface_samples_include_physical_and_raw_rows(self):
        rows = sampler.build_interface_samples(sampler.DEFAULT_RECON_ROOT)
        self.assertTrue(rows)
        roles = {row["interface_role"] for row in rows}
        self.assertLessEqual({"raw_span_inlet", "raw_span_outlet", "physical_segment_inlet", "physical_segment_outlet"}, roles)
        self.assertTrue(any(row["quality_flags"] == "high_recirculation_forward_bulk_used" for row in rows))
        ok = [row for row in rows if row["status"] == "ok"]
        self.assertTrue(ok)
        self.assertTrue(all(row["temperature_selection_rule"] for row in ok))

    def test_build_package_writes_registry_and_samples(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            summary = sampler.build_package(output_dir=tmp_path)
            self.assertEqual(summary["counts"]["registry_rows"], 15)
            self.assertGreater(summary["counts"]["ok_sample_rows"], 0)
            samples = tmp_path / "interface_temperature_samples.csv"
            registry = tmp_path / "interface_registry.csv"
            self.assertTrue(samples.exists())
            self.assertTrue(registry.exists())
            with samples.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertGreaterEqual(rows[0].keys(), {"source_id", "physical_segment", "plane_file", "T_used_K"})

    def test_openfoam_plane_plan_brackets_required_control_volumes(self):
        rows = sampler.build_openfoam_plane_plan(
            "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "salt_2",
        )
        volumes = {row["control_volume"] for row in rows}
        self.assertIn("heater_interior", volumes)
        self.assertIn("cooler_reducer_interior", volumes)
        self.assertIn("lower_left_junction", volumes)
        self.assertIn("upper_right_junction", volumes)
        self.assertEqual(len(rows), 16)
        heater = [row for row in rows if row["control_volume"] == "heater_interior"]
        self.assertEqual({row["interface_role"] for row in heater}, {"cv_inlet_bracket", "cv_outlet_bracket"})

    def test_raw_plane_parser_keeps_mixing_and_forward_temperatures_separate(self):
        import tempfile

        data = np.array(
            [
                [0, 0, 0, 1.0, 0, 0, 10, 1900, 500],
                [0, 0, 0, 1.0, 0, 0, 10, 1900, 502],
                [0, 0, 0, 1.0, 0, 0, 10, 1900, 504],
                [0, 0, 0, 1.0, 0, 0, 10, 1900, 506],
                [0, 0, 0, 1.0, 0, 0, 10, 1900, 508],
                [0, 0, 0, 1.0, 0, 0, 10, 1900, 510],
                [0, 0, 0, -0.2, 0, 0, 10, 1900, 450],
                [0, 0, 0, -0.2, 0, 0, 10, 1900, 452],
            ],
            dtype=float,
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.xy"
            np.savetxt(path, data)
            parsed = sampler.parse_raw_plane_sample(path, (1.0, 0.0, 0.0))
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["dominant_flow_direction"], "positive_normal")
        self.assertNotEqual(parsed["T_mixing_cup_signed_K"], parsed["T_forward_dominant_bulk_K"])
        self.assertIn("signed_mixing_cup", parsed["temperature_selection_rule"])

    def test_raw_plane_parser_resolves_new_control_dict_column_order(self):
        import tempfile

        # New task controlDict writes fields as (U T rho p_rgh), which produces
        # columns x y z Ux Uy Uz T rho p_rgh.
        data = np.array(
            [
                [0, 0, 0, 0.5, 0, 0, 500, 1900, 12],
                [0, 0, 0, 0.5, 0, 0, 502, 1900, 12],
                [0, 0, 0, 0.5, 0, 0, 504, 1900, 12],
                [0, 0, 0, 0.5, 0, 0, 506, 1900, 12],
                [0, 0, 0, 0.5, 0, 0, 508, 1900, 12],
                [0, 0, 0, 0.5, 0, 0, 510, 1900, 12],
                [0, 0, 0, -0.1, 0, 0, 450, 1900, 12],
                [0, 0, 0, -0.1, 0, 0, 452, 1900, 12],
            ],
            dtype=float,
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.xy"
            np.savetxt(path, data)
            parsed = sampler.parse_raw_plane_sample(path, (1.0, 0.0, 0.0))
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["positive_flux_proxy"], "5700")
        self.assertEqual(parsed["negative_flux_proxy_abs"], "380")

    def test_openfoam_package_writer_emits_sbatch_and_scripts(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "package"
            tmp = Path(raw_tmp) / "tmp"
            summary = sampler.write_openfoam_package(out, tmp)
            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["plane_count_per_case"], 16)
            self.assertTrue((out / "scripts/submit_overnight_thermal_sampling.sbatch").exists())
            self.assertTrue((out / "scripts/run_thermal_openfoam_interface_sampling.sh").exists())


if __name__ == "__main__":
    unittest.main()
