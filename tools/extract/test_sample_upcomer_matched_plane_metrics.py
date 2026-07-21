"""Tests for matched upcomer plane metric parsing and planning."""

from __future__ import annotations

import csv
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.extract import sample_upcomer_matched_plane_metrics as sampler


class UpcomerMatchedPlaneMetricsTests(unittest.TestCase):
    def test_secmean_parser_uses_supplied_geometric_normal(self):
        data = np.array(
            [
                [0, 0, 0, 1.0, 0.0, 0.0, 10.0, 1900.0],
                [0, 0, 0, 1.0, 0.0, 0.0, 10.0, 1900.0],
                [0, 0, 0, -0.5, 0.0, 0.0, 10.0, 1900.0],
                [0, 0, 0, 0.0, 1.0, 0.0, 10.0, 1900.0],
            ],
            dtype=float,
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.xy"
            np.savetxt(path, data)
            parsed = sampler.parse_secmean_plane(path, np.array([1.0, 0.0, 0.0]))
        self.assertAlmostEqual(float(parsed["reverse_area_fraction"]), 0.25)
        self.assertGreater(float(parsed["secondary_velocity_fraction"]), 0.0)
        self.assertEqual(parsed["source_column_rule"], "T_from_rho_linear_eos")

    def test_secmean_parser_resolves_raw_t_column(self):
        data = np.array(
            [
                [0, 0, 0, 1.0, 0.0, 0.0, 500.0, 1900.0, 10.0],
                [0, 0, 0, 1.0, 0.0, 0.0, 504.0, 1900.0, 10.0],
                [0, 0, 0, 1.0, 0.0, 0.0, 508.0, 1900.0, 10.0],
                [0, 0, 0, 1.0, 0.0, 0.0, 512.0, 1900.0, 10.0],
            ],
            dtype=float,
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.xy"
            np.savetxt(path, data)
            parsed = sampler.parse_secmean_plane(path, np.array([1.0, 0.0, 0.0]))
        self.assertEqual(parsed["source_column_rule"], "raw_T")
        self.assertAlmostEqual(float(parsed["bulk_T_K"]), 506.0)

    def test_convcell_parser_carries_nondimensional_medians(self):
        data = np.array(
            [
                [0, 0, 0, 1.0, 0, 0, 10.0, 2.0, 20.0, 100.0, 5.0],
                [0, 0, 0, -0.5, 0, 0, 12.0, 4.0, 30.0, 120.0, 7.0],
            ],
            dtype=float,
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.xy"
            np.savetxt(path, data)
            parsed = sampler.parse_convcell_plane(path, np.array([1.0, 0.0, 0.0]))
        self.assertAlmostEqual(float(parsed["reverse_area_fraction"]), 0.5)
        self.assertAlmostEqual(float(parsed["Ri"]), 3.0)
        self.assertAlmostEqual(float(parsed["Re"]), 110.0)

    def test_gz_zero_entry_is_not_numeric(self):
        self.assertTrue(math.isnan(sampler.gz_from_station(100.0, 5.0, 0.02, 0.0)))
        self.assertAlmostEqual(sampler.gz_from_station(100.0, 5.0, 0.02, 2.0), 5.0)

    def test_build_package_writes_required_outputs(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "pkg"
            summary = sampler.build_package(out)
            self.assertEqual(summary["admission_grade_rows"], 0)
            self.assertTrue((out / "upcomer_matched_plane_extraction_plan.csv").exists())
            self.assertTrue((out / "mesh_family_repeat_plan.csv").exists())
            self.assertTrue((out / "README.md").exists())
            with (out / "upcomer_matched_plane_extraction_plan.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertIn("wallHeatFlux_W_m2", rows[0])
            self.assertTrue(any(row["plane_location"] == "upcomer_mid" for row in rows))

    def test_vtk_plane_parser_area_weights_metrics(self):
        vtk_text = """# vtk DataFile Version 3.0
plane
ASCII
DATASET POLYDATA
POINTS 6 float
0 0 0  1 0 0  1 1 0  0 1 0  3 0 0  3 2 0
POLYGONS 2 8
3 0 1 2
3 0 4 5
CELL_DATA 2
VECTORS U float
1 0 0
-1 0 0
SCALARS rho float 1
LOOKUP_TABLE default
2
2
SCALARS T float 1
LOOKUP_TABLE default
300
330
SCALARS Re float 1
LOOKUP_TABLE default
10
20
SCALARS Pr float 1
LOOKUP_TABLE default
5
5
SCALARS Ri float 1
LOOKUP_TABLE default
0.1
0.2
SCALARS Gr float 1
LOOKUP_TABLE default
1
2
SCALARS Ra float 1
LOOKUP_TABLE default
3
4
"""
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.vtk"
            path.write_text(vtk_text, encoding="utf-8")
            parsed = sampler.parse_area_weighted_plane_vtk(path, np.array([1.0, 0.0, 0.0]))
        self.assertEqual(parsed["face_count"], 2)
        self.assertGreater(float(parsed["reverse_area_fraction"]), 0.5)
        self.assertAlmostEqual(float(parsed["reverse_mass_fraction"]), 3.0 / 3.5)
        self.assertAlmostEqual(float(parsed["Pr"]), 5.0)

    def test_vtk_field_attributes_parser(self):
        vtk_text = """# vtk DataFile Version 2.0
plane
ASCII
DATASET POLYDATA
POINTS 4 float
0 0 0  1 0 0  1 1 0  0 1 0
POLYGONS 1 5
4 0 1 2 3
CELL_DATA 1
FIELD attributes 5
T 1 1 float
300
rho 1 1 float
2
U 3 1 float
1 0 0
Re 1 1 float
10
Pr 1 1 float
5
"""
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.vtk"
            path.write_text(vtk_text, encoding="utf-8")
            parsed = sampler.parse_area_weighted_plane_vtk(path, np.array([1.0, 0.0, 0.0]))
        self.assertEqual(parsed["face_count"], 1)
        self.assertAlmostEqual(float(parsed["bulk_T_K"]), 300.0)
        self.assertAlmostEqual(float(parsed["Re"]), 10.0)

    def test_vtk_plane_parser_derives_temperature_from_rho_when_t_absent(self):
        vtk_text = """# vtk DataFile Version 2.0
plane
ASCII
DATASET POLYDATA
POINTS 4 float
0 0 0  1 0 0  1 1 0  0 1 0
POLYGONS 1 5
4 0 1 2 3
CELL_DATA 1
VECTORS U float
1 0 0
SCALARS rho float 1
LOOKUP_TABLE default
1918.75
"""
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.vtk"
            path.write_text(vtk_text, encoding="utf-8")
            parsed = sampler.parse_area_weighted_plane_vtk(path, np.array([1.0, 0.0, 0.0]))
        self.assertEqual(parsed["temperature_source"], "T_from_rho_linear_eos")
        self.assertAlmostEqual(float(parsed["bulk_T_K"]), 500.0)

    def test_wall_band_parser_filters_by_station_distance(self):
        vtk_text = """# vtk DataFile Version 3.0
wall
ASCII
DATASET POLYDATA
POINTS 6 float
0 0 0  0 1 0  0 0 1  2 0 0  2 1 0  2 0 1
POLYGONS 2 8
3 0 1 2
3 3 4 5
CELL_DATA 2
SCALARS T float 1
LOOKUP_TABLE default
400
900
SCALARS wallHeatFlux float 1
LOOKUP_TABLE default
-10
-90
"""
        plane = {"x": "0", "y": "0", "z": "0", "nx": "1", "ny": "0", "nz": "0", "bore_m": "1.0"}
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "wall.vtk"
            path.write_text(vtk_text, encoding="utf-8")
            parsed = sampler.parse_wall_band_vtk(path, plane)
        self.assertEqual(parsed["wall_face_count"], 1)
        self.assertAlmostEqual(float(parsed["wall_T_K"]), 400.0)
        self.assertAlmostEqual(float(parsed["wallHeatFlux_W_m2"]), -10.0)

    def test_wall_band_parser_derives_temperature_from_rho_when_t_absent(self):
        vtk_text = """# vtk DataFile Version 3.0
wall
ASCII
DATASET POLYDATA
POINTS 3 float
0 0 0  0 1 0  0 0 1
POLYGONS 1 4
3 0 1 2
CELL_DATA 1
SCALARS rho float 1
LOOKUP_TABLE default
1918.75
SCALARS wallHeatFlux float 1
LOOKUP_TABLE default
-25
"""
        plane = {"x": "0", "y": "0", "z": "0", "nx": "1", "ny": "0", "nz": "0", "bore_m": "1.0"}
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "wall.vtk"
            path.write_text(vtk_text, encoding="utf-8")
            parsed = sampler.parse_wall_band_vtk(path, plane)
        self.assertEqual(parsed["wall_temperature_source"], "T_from_rho_linear_eos")
        self.assertAlmostEqual(float(parsed["wall_T_K"]), 500.0)
        self.assertAlmostEqual(float(parsed["wallHeatFlux_W_m2"]), -25.0)

    def test_admission_classifier_blocks_recirculating_rows(self):
        row = {
            "reverse_area_fraction": "0.5",
            "reverse_mass_fraction": "0.5",
            "secondary_velocity_fraction": "0.01",
            "Ri": "0.1",
            "bulk_T_K": "300",
            "wall_T_K": "301",
            "wallHeatFlux_W_m2": "-10",
        }
        self.assertEqual(sampler.classify_metric_row(row), "diagnostic-only-recirculating")

    def test_admission_classifier_allows_recirculation_without_wall_fields(self):
        row = {
            "reverse_area_fraction": "0.5",
            "reverse_mass_fraction": "0.5",
            "secondary_velocity_fraction": "0.01",
            "Ri": "0.1",
            "bulk_T_K": "300",
            "wall_T_K": "",
            "wallHeatFlux_W_m2": "",
        }
        self.assertEqual(sampler.classify_metric_row(row), "diagnostic-only-recirculating")

    def test_build_openfoam_package_writes_compute_outputs(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "compute"
            tmp = Path(raw_tmp) / "tmp"
            summary = sampler.build_openfoam_package(out, tmp)
            self.assertEqual(summary["task"], sampler.COMPUTE_TASK_ID)
            self.assertTrue((out / "candidate_readiness_matrix.csv").exists())
            self.assertTrue((out / "method_trace.md").exists())
            self.assertTrue((out / "scripts" / "run_upcomer_matched_plane_compute.sh").exists())
            with (out / "matched_plane_metrics_admission.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertIn("admission_status", rows[0])

    def test_pm10_completed_rows_are_runnable_now(self):
        rows = sampler.build_candidate_readiness_rows()
        pm10 = {
            row["case_key"]: row
            for row in rows
            if row["case_key"] in {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"}
        }
        self.assertEqual(set(pm10), {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"})
        self.assertEqual({row["compute_readiness"] for row in pm10.values()}, {"runnable-now"})
        self.assertEqual(
            {row["blocking_reason"] for row in pm10.values()},
            {"completed_pm10_harvest_processor_frame_available"},
        )
        self.assertEqual({row["availability_status"] for row in pm10.values()}, {"available now"})
        self.assertEqual({row["run_state"] for row in pm10.values()}, {"completed"})
        self.assertEqual({row["admission_verdict"] for row in pm10.values()}, {"terminal-holdout-scoring"})
        self.assertEqual(pm10["salt2_lo10q"]["representative_time_s"], "12382")
        self.assertEqual(pm10["salt4_hi10q"]["representative_time_s"], "14017")
        self.assertTrue(all("2026-07-20_salt_pm10_terminal_admission_classification" in row["source_paths"] for row in pm10.values()))

    def test_pm5_rows_remain_dependency_gated(self):
        rows = sampler.build_candidate_readiness_rows()
        pm5 = {
            row["case_key"]: row
            for row in rows
            if row["case_key"] in {"salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q"}
        }
        self.assertEqual(set(pm5), {"salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q"})
        self.assertEqual({row["compute_readiness"] for row in pm5.values()}, {"dependency-gated"})
        self.assertEqual({row["dependency_job_id"] for row in pm5.values()}, {"3295437"})

    def test_openfoam_runner_absolutizes_source_case_before_symlink(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "compute"
            tmp = Path(raw_tmp) / "tmp"
            sampler.build_openfoam_package(out, tmp)
            runner = (out / "scripts" / "run_upcomer_matched_plane_compute.sh").read_text(encoding="utf-8")
        self.assertIn('[[ -n "$source_case" && "$source_case" != /* ]] && source_case="$ROOT/$source_case"', runner)
        self.assertIn('ln -s "$source_case/processors64" "$recon_dir/processors64"', runner)
        self.assertIn("reconstruct_fields='(U rho p_rgh Re Pr Ri Gr Ra wallHeatFlux)'", runner)
        self.assertIn("reconstruct_wallHeatFlux_${case_key}.log", runner)
        self.assertIn("Using reconstructed wallHeatFlux field", runner)

    def test_pm10_plan_rows_use_corrected_q_sampling_requirement(self):
        rows = [row for row in sampler.build_plan_rows() if row["case_key"] == "salt2_lo10q"]
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            {row["compute_requirement"] for row in rows},
            {"compute_node_required_reconstruct_corrected_q_processor_frame_for_admission_grade_sampling"},
        )
        self.assertEqual({row["representative_time_s"] for row in rows}, {"12382"})
        self.assertTrue(all("viscosity_screening_salt_test_2_jin_coarse_mesh" in row["mesh_stations_path"] for row in rows))

    def test_compute_package_preflight_checks_processor_frames(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "compute"
            tmp = Path(raw_tmp) / "tmp"
            sampler.build_openfoam_package(out, tmp)
            runner = out / "scripts" / "run_upcomer_matched_plane_compute.sh"
            text = runner.read_text(encoding="utf-8")
        self.assertIn("missing processor frame", text)
        self.assertIn("source_case/processors64/$time_s", text)
        self.assertIn("functions.upcomer_disabled", text)
        self.assertIn("-fileHandler collated -noFunctionObjects -newTimes", text)
        self.assertIn("reconstruction did not create", text)


if __name__ == "__main__":
    unittest.main()
