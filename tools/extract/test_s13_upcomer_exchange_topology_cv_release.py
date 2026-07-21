from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_topology_cv_release as builder


def write_label_list(path: Path, values: list[int]) -> None:
    path.write_text(f"{len(values)}\n(\n" + "\n".join(str(value) for value in values) + "\n)\n", encoding="utf-8")


class S13UpcomerExchangeTopologyCvReleaseTests(unittest.TestCase):
    def test_boundary_parser_extracts_patch_ranges(self) -> None:
        text = """
        2
        (
          pipeleg_right_01_lower
          {
            type wall;
            nFaces 10;
            startFace 100;
          }
          other_patch
          {
            type wall;
            nFaces 3;
            startFace 110;
          }
        )
        """
        patches = builder.parse_boundary_patches(text)
        self.assertEqual(patches[0].name, "pipeleg_right_01_lower")
        self.assertEqual(patches[0].start_face, 100)
        self.assertEqual(patches[0].end_face, 110)

    def test_release_decision_blocks_fragmented_component(self) -> None:
        payload = {
            "largest_face_component_fraction": 0.53,
            "selected_cells": {1, 2, 3},
        }
        stats = builder.TopologyStats(interface_face_count=5, interface_area_m2=1.0, wall_face_count=2, wall_area_m2=0.5)
        status, reason = builder.release_decision(payload, stats)
        self.assertEqual(status, "blocked_topology_cv_not_released")
        self.assertIn("largest_face_component_fraction_below", reason)

    def test_release_decision_passes_conservative_complete_case(self) -> None:
        payload = {
            "largest_face_component_fraction": 0.9,
            "selected_cells": {1, 2, 3},
        }
        stats = builder.TopologyStats(interface_face_count=5, interface_area_m2=1.0, wall_face_count=2, wall_area_m2=0.5)
        status, reason = builder.release_decision(payload, stats)
        self.assertEqual(status, "released_topology_cv")
        self.assertEqual(reason, "")

    def test_face_component_builder_relabels_from_owner_neighbour(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mesh = Path(tmp)
            write_label_list(mesh / "owner", [1, 2, 4])
            write_label_list(mesh / "neighbour", [2, 3, 5])
            masks = {
                "salt_2": {"all_cells": {1, 2, 3, 4, 5}},
                "salt_3": {"all_cells": {1, 2, 4}},
                "salt_4": {"all_cells": {6}},
            }
            result = builder.build_face_component_results(masks, mesh)
        self.assertEqual([len(cells) for cells in result["salt_2"].components], [3, 2])
        self.assertEqual([len(cells) for cells in result["salt_3"].components], [2, 1])
        self.assertEqual([len(cells) for cells in result["salt_4"].components], [1])

    def test_package_shell_writes_fail_closed_outputs_without_topology_stream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out, compute_topology=False)
            self.assertTrue((out / "topology_cv_case_summary.csv").exists())
            self.assertTrue((out / "face_connected_component_summary.csv").exists())
            self.assertTrue((out / "exchange_interface_topology_contract.csv").exists())
            self.assertEqual(payload["summary"]["released_topology_cv_rows"], 0)
            self.assertFalse(payload["summary"]["surface_extraction_allowed"])


if __name__ == "__main__":
    unittest.main()
