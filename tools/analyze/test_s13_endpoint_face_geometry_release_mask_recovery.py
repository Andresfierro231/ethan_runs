from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_s13_endpoint_face_geometry_release_mask_recovery as builder


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13EndpointFaceGeometryReleaseMaskRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()

    def test_summary_is_fail_closed(self) -> None:
        summary = json.loads((builder.OUT_DIR / "summary.json").read_text())
        self.assertEqual(
            summary["decision"],
            "s13_endpoint_face_geometry_release_mask_recovery_fail_closed_no_exact_fields",
        )
        self.assertEqual(summary["endpoint_rows"], 6)
        self.assertEqual(summary["candidate_face_id_rows"], 288)
        self.assertEqual(summary["released_endpoint_masks"], 0)

    def test_recovery_matrix_blocks_every_endpoint(self) -> None:
        rows = read_csv(builder.OUT_DIR / "endpoint_face_geometry_recovery_matrix.csv")
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["release_mask_ready"] for row in rows}, {"False"})
        for row in rows:
            self.assertIn("area_m2", row["missing_release_fields"])
            self.assertIn("owner_cell", row["missing_release_fields"])
            self.assertIn("normal_convention", row["missing_release_fields"])
            self.assertIn("positive_mdot_convention", row["missing_release_fields"])

    def test_candidate_inventory_is_not_a_release_mask(self) -> None:
        rows = read_csv(builder.OUT_DIR / "candidate_face_id_inventory.csv")
        self.assertEqual(len(rows), 288)
        self.assertEqual({row["release_ready"] for row in rows}, {"False"})


if __name__ == "__main__":
    unittest.main()
