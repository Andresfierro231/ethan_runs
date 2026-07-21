from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_topology_forensics_alt_cv as builder


class S13UpcomerExchangeTopologyForensicsAltCvTests(unittest.TestCase):
    def make_stats(
        self,
        component_id: int,
        cells: int,
        total: int = 100,
        wall_faces: int = 0,
        interface_faces: int = 2,
        escapes: int = 0,
    ) -> builder.ComponentStats:
        stats = builder.ComponentStats(
            case_id="salt_2",
            component_id=component_id,
            cells=set(range(component_id * 1000, component_id * 1000 + cells)),
            total_reverse_cells=total,
            source_mask_csv=Path("mask.csv"),
        )
        stats.right_leg_wall_face_count = wall_faces
        stats.right_leg_wall_area_m2 = 0.1 if wall_faces else 0.0
        stats.interface_face_count = interface_faces
        stats.interface_area_m2 = 0.2 if interface_faces else 0.0
        stats.boundary_escape_face_count = escapes
        return stats

    def test_release_status_blocks_missing_wall_contact(self) -> None:
        stats = self.make_stats(component_id=1, cells=90, wall_faces=0)
        status, reason = builder.release_status(stats)
        self.assertEqual(status, "blocked_alt_cv_not_released")
        self.assertIn("missing_positive_right_leg_wall_faces_or_area", reason)

    def test_release_status_requires_dominant_component(self) -> None:
        stats = self.make_stats(component_id=2, cells=40, wall_faces=3)
        status, reason = builder.release_status(stats)
        self.assertEqual(status, "blocked_alt_cv_not_released")
        self.assertIn("component_fraction_below", reason)

    def test_choose_alternate_prefers_wall_adjacent_when_no_release_exists(self) -> None:
        largest = self.make_stats(component_id=1, cells=80, wall_faces=0)
        wall_adjacent = self.make_stats(component_id=2, cells=10, wall_faces=5)
        chosen = builder.choose_alternate_component({1: largest, 2: wall_adjacent})
        self.assertEqual(chosen.component_id, 2)
        self.assertEqual(chosen.selection_basis, "largest_right_leg_wall_area_reverse_component_but_gate_blocked")

    def test_choose_alternate_prefers_releasable_component(self) -> None:
        releasable = self.make_stats(component_id=3, cells=80, wall_faces=4)
        blocked_wall = self.make_stats(component_id=2, cells=10, wall_faces=10)
        chosen = builder.choose_alternate_component({2: blocked_wall, 3: releasable})
        self.assertEqual(chosen.component_id, 3)
        self.assertEqual(chosen.selection_basis, "largest_component_passing_existing_release_gates")

    def test_package_shell_writes_outputs_without_topology_stream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out, compute_topology=False)
            self.assertTrue((out / "component_topology_forensics.csv").exists())
            self.assertTrue((out / "alternate_cv_case_summary.csv").exists())
            self.assertTrue((out / "downstream_release_gate.csv").exists())
            self.assertEqual(payload["summary"]["released_alt_cv_rows"], 0)
            self.assertFalse(payload["summary"]["surface_extraction_allowed"])


if __name__ == "__main__":
    unittest.main()
