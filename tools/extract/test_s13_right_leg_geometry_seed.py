from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_right_leg_geometry_seed as builder


class S13RightLegGeometrySeedTests(unittest.TestCase):
    def test_cap_patch_classifier(self) -> None:
        self.assertTrue(builder.is_cap_patch("ncc_pipeleg_right_01_lower_start"))
        self.assertTrue(builder.is_cap_patch("couple3_on_ncc_pipeleg_right_03_upper_end"))
        self.assertFalse(builder.is_cap_patch("pipeleg_right_02_middle"))

    def test_bounds_expansion_and_contains(self) -> None:
        bounds = builder.Bounds(0.0, 1.0, 2.0, 3.0, -1.0, 1.0).expanded(0.25)
        self.assertTrue(bounds.contains((1.1, 1.9, -1.1)))
        self.assertFalse(bounds.contains((1.3, 1.9, -1.1)))

    def test_release_decision_requires_no_escape(self) -> None:
        seed = builder.CaseSeed(case_id="salt_x", bounds=builder.Bounds(0, 1, 0, 1, 0, 1))
        seed.seed_cells = {1, 2}
        seed.seed_volume_m3 = 1.0
        seed.trusted_wall_face_count = 1
        seed.trusted_wall_area_m2 = 1.0
        seed.internal_interface_face_count = 1
        seed.internal_interface_area_m2 = 1.0
        self.assertEqual(builder.release_decision(seed)[0], "released_geometry_seed_ready_for_source_bounded_rerun")
        seed.escape_face_count = 1
        self.assertEqual(builder.release_decision(seed)[0], "blocked_geometry_seed_not_ready")

    def test_reverse_flow_does_not_control_release(self) -> None:
        seed = builder.CaseSeed(case_id="salt_x", bounds=builder.Bounds(0, 1, 0, 1, 0, 1))
        seed.seed_cells = {1, 2}
        seed.reverse_candidate_cells = set()
        seed.reverse_flow_seed_cells = set()
        seed.seed_volume_m3 = 1.0
        seed.trusted_wall_face_count = 1
        seed.trusted_wall_area_m2 = 1.0
        seed.internal_interface_face_count = 1
        seed.internal_interface_area_m2 = 1.0
        self.assertEqual(builder.release_decision(seed)[0], "released_geometry_seed_ready_for_source_bounded_rerun")

    def test_write_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.write_readme(out, {"decision": "complete_test"})
            self.assertIn("Reverse-flow occupancy is diagnostic only", (out / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
