from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_s14_recirc_cv_segmentation_preflight as builder


def write_fixture_vtk(path: Path) -> None:
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (2.4, 0.0, 0.0),
        (2.8, 0.0, 0.0),
        (2.4, 1.0, 0.0),
        (2.4, 0.0, 1.0),
        (2.7, 0.0, 0.0),
        (3.0, 0.0, 0.0),
        (2.7, 1.0, 0.0),
        (2.7, 0.0, 1.0),
    ]
    text = [
        "# vtk DataFile Version 2.0",
        "fixture",
        "ASCII",
        "DATASET UNSTRUCTURED_GRID",
        f"POINTS {len(points)} float",
        " ".join(str(coord) for point in points for coord in point),
        "CELLS 3 15",
        "4 0 1 2 3",
        "4 4 5 6 7",
        "4 8 9 10 11",
        "CELL_TYPES 3",
        "10 10 10",
        "CELL_DATA 3",
        "FIELD attributes 4",
        "cellID 1 3 int",
        "0 1 2",
        "T 1 3 float",
        "300 301 302",
        "rho 1 3 float",
        "1 1 1",
        "U 3 3 float",
        "0 1 0 0 1 0 0 -1 0",
    ]
    path.write_text("\n".join(text) + "\n", encoding="utf-8")


class RecircCvSegmentationPreflightTests(unittest.TestCase):
    def test_fixture_vtk_generates_reverse_flow_candidate_mask(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtk = root / "fixture.vtk"
            write_fixture_vtk(vtk)
            summary, components = builder.case_segmentation("fixture", vtk, root)
            mask = root / "masks/fixture_right_leg_reverse_flow_candidate_mask.csv"
            mask_exists = mask.exists()
        self.assertEqual(summary["observed_cells"], 3)
        self.assertEqual(summary["right_leg_roi_cells"], 2)
        self.assertEqual(summary["reverse_candidate_cells"], 1)
        self.assertEqual(summary["largest_component_cells"], 1)
        self.assertEqual(summary["release_status"], "candidate_mask_generated_not_released")
        self.assertEqual(len(components), 1)
        self.assertTrue(mask_exists)

    def test_interface_and_wall_rows_block_diagnostic_masks(self) -> None:
        summary_rows = [
            {
                "case_id": "salt_2",
                "release_status": "candidate_mask_generated_not_released",
            }
        ]
        interface = builder.interface_preflight_rows(summary_rows)
        wall = builder.wall_core_preflight_rows(summary_rows)
        self.assertEqual(interface[0]["exchange_interface_status"], "blocked")
        self.assertEqual(wall[0]["wall_core_status"], "blocked")
        self.assertEqual(wall[0]["q_wall_w_status"], "blocked")

    def test_s14_linkage_keeps_f3_comparison_unreleased(self) -> None:
        rows = builder.s14_linkage_rows()
        self.assertTrue(rows)
        right_leg = [row for row in rows if row["branch_or_feature"] == "right_leg"]
        self.assertTrue(right_leg)
        self.assertTrue(all(row["admitted_rows"] == "0" for row in rows))
        self.assertTrue(all(row["f3_shah_apparent_comparison_status"] == "not_evaluated_no_admitted_or_ordinary_candidate" for row in rows))


if __name__ == "__main__":
    unittest.main()
