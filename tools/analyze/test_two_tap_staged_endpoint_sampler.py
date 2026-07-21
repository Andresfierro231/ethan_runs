"""Focused tests for the two-tap staged endpoint sampler package."""

from __future__ import annotations

import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_two_tap_staged_endpoint_sampler as sampler


ROOT = sampler.ROOT
OUT = sampler.OUT


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TwoTapStagedEndpointSamplerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sampler.build_package()

    def test_exact_target_cases_times_and_labels(self) -> None:
        plan_rows = rows("case_sampling_plan.csv")
        self.assertEqual(len(plan_rows), 6)
        by_case = {}
        for row in plan_rows:
            by_case.setdefault(row["case_id"], set()).add((row["time_s"], row["station_label"], row["surface_label"]))
        self.assertEqual(set(by_case), {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({time for time, _, _ in by_case["salt_2"]}, {"7915"})
        self.assertEqual({time for time, _, _ in by_case["salt_3"]}, {"7618"})
        self.assertEqual({time for time, _, _ in by_case["salt_4"]}, {"10000"})
        for entries in by_case.values():
            labels = {station for _, station, _ in entries}
            self.assertEqual(labels, {"lower_leg__s04", "right_leg__s00"})
            surface_labels = {surface for _, _, surface in entries}
            self.assertIn("corner_lower_right__upstream_lower_leg__s04", surface_labels)
            self.assertIn("corner_lower_right__downstream_right_leg__s00", surface_labels)

    def test_preflight_records_empty_ncc_patch_blocker_and_cutting_plane_path(self) -> None:
        preflight = rows("sampler_preflight.csv")
        self.assertEqual(len(preflight), 3)
        for row in preflight:
            self.assertEqual(row["sampler_status"], "ready_for_cutting_plane_sampling")
            self.assertEqual(row["direct_patch_sampling_status"], "blocked_empty_ncc_patch_boundary")
            self.assertEqual(row["upstream_patch_boundary_nfaces"], "0")
            self.assertEqual(row["downstream_patch_boundary_nfaces"], "0")
            self.assertEqual(row["required_fields_missing"], "")

    def test_raw_outputs_are_missing_or_sampled_without_admission(self) -> None:
        raw = rows("raw_endpoint_pressure_velocity.csv")
        self.assertEqual(len(raw), 6)
        manifest = rows("raw_endpoint_surface_file_manifest.csv")
        if all(row["exists"] == "true" for row in manifest):
            self.assertTrue(all(row["sample_status"] == "sampled" for row in raw))
            self.assertTrue(all(row["p_pa"] != "" for row in raw))
            self.assertTrue(all(row["admission_status"] == "raw_sample_only_no_component_k_admission" for row in raw))
        else:
            self.assertTrue(all(row["sample_status"] == "missing_raw_surface_file" for row in raw))
            self.assertTrue(all(row["p_pa"] == "" for row in raw))
            self.assertTrue(all(row["admission_status"] == "missing_raw_sample_diagnostic_only" for row in raw))
        readiness = rows("sampler_readiness_or_failure.csv")
        self.assertTrue(
            all(
                row["decision"] in {"ready_to_submit_or_harvest_pending", "harvested_raw_endpoint_sample_not_admitted"}
                or row["decision"] == "raw_endpoint_sampled"
                for row in readiness
            )
        )

    def test_summary_guardrails(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], sampler.TASK)
        self.assertEqual(summary["target_cases"], 3)
        self.assertEqual(summary["endpoint_surfaces"], 6)
        self.assertEqual(summary["preflight_failures"], 0)
        self.assertIn(summary["raw_sampled_rows"], {0, 6})
        self.assertIn(summary["raw_missing_rows"], {0, 6})
        self.assertEqual(summary["raw_sampled_rows"] + summary["raw_missing_rows"], 6)
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["registry_or_admission_mutated"])
        self.assertFalse(summary["f6_fit_performed"])
        self.assertFalse(summary["component_k_admitted"])

    def test_scripts_are_shell_parseable(self) -> None:
        for row in rows("scripts_manifest.csv"):
            if row["script_id"] in {"runner", "sbatch"}:
                subprocess.run(["bash", "-n", str(ROOT / row["path"])], check=True)
        control_text = (OUT / "scripts/controlDicts/salt2_mainline.controlDict").read_text(encoding="utf-8")
        self.assertIn("fields          (U p p_rgh rho T);", control_text)
        self.assertIn("surfaceFormat   vtk;", control_text)

    def test_vtk_parser_area_weights_pressure_and_reverse_metrics(self) -> None:
        vtk_text = """# vtk DataFile Version 3.0
two_tap
ASCII
DATASET POLYDATA
POINTS 5 float
0 0 0  0 1 0  0 0 1  0 2 0  0 0 2
POLYGONS 2 8
3 0 1 2
3 0 3 4
CELL_DATA 2
VECTORS U float
1 0 0
-0.5 0 0
SCALARS p float 1
LOOKUP_TABLE default
10
20
SCALARS p_rgh float 1
LOOKUP_TABLE default
1
3
SCALARS rho float 1
LOOKUP_TABLE default
2
2
SCALARS T float 1
LOOKUP_TABLE default
300
320
"""
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.vtk"
            path.write_text(vtk_text, encoding="utf-8")
            parsed = sampler.parse_vtk_surface(path, (1.0, 0.0, 0.0))
        self.assertEqual(parsed["sample_status"], "sampled")
        self.assertEqual(parsed["face_count"], 2)
        self.assertAlmostEqual(parsed["area_m2"], 2.5)
        self.assertAlmostEqual(parsed["p_pa"], 18.0)
        self.assertAlmostEqual(parsed["p_rgh_pa"], 2.6)
        self.assertAlmostEqual(parsed["reverse_area_fraction"], 0.8)
        self.assertAlmostEqual(parsed["reverse_mass_fraction"], 2.0 / 3.0)

    def test_vtk_parser_reads_wrapped_polygons_and_field_attributes(self) -> None:
        vtk_text = """# vtk DataFile Version 2.0
sampleSurface
ASCII
DATASET POLYDATA
POINTS 5 float
0 0 0  0 1 0  0 0 1  0 2 0  0 0 2
POLYGONS 2 8
3 0 1
2 3 0
3 4
CELL_DATA 2
FIELD attributes 5
p 1 2 float
10 20
p_rgh 1 2 float
1 3
rho 1 2 float
2 2
T 1 2 float
300 320
U 3 2 float
1 0
0 -0.5 0 0
"""
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plane.vtk"
            path.write_text(vtk_text, encoding="utf-8")
            parsed = sampler.parse_vtk_surface(path, (1.0, 0.0, 0.0))
        self.assertEqual(parsed["sample_status"], "sampled")
        self.assertEqual(parsed["face_count"], 2)
        self.assertAlmostEqual(parsed["area_m2"], 2.5)
        self.assertAlmostEqual(parsed["p_pa"], 18.0)
        self.assertAlmostEqual(parsed["U_bulk_normal_m_s"], -0.2)


if __name__ == "__main__":
    unittest.main()
