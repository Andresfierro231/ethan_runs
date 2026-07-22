from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_right_leg_roi_patch_alignment_audit as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13RightLegRoiPatchAlignmentAuditTests(unittest.TestCase):
    def test_patch_classifier(self) -> None:
        self.assertTrue(builder.is_trusted_patch("pipeleg_right_02_middle"))
        self.assertFalse(builder.is_trusted_patch("ncc_pipeleg_right_03_upper_end"))
        self.assertTrue(builder.is_right_context_patch("junction_upper_right"))

    def test_package_reports_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertFalse(payload["summary"]["s12_unlocked"])
            self.assertEqual(payload["summary"]["decision"], "complete_fail_closed_geometry_seed_required")

    def test_dominant_components_have_no_trusted_contact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            builder.build_package(out)
            dominant = rows(out / "dominant_component_patch_overlap.csv")
            self.assertEqual(len(dominant), 3)
            self.assertTrue(all(row["trusted_right_leg_patch_contact_count"] == "0" for row in dominant))

    def test_seed_requirements_are_per_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            builder.build_package(out)
            seed = rows(out / "geometry_seed_requirements.csv")
            self.assertEqual({row["case_id"] for row in seed}, {"salt_2", "salt_3", "salt_4"})
            self.assertTrue(all(row["release_status"] == "blocked_geometry_seed_required" for row in seed))


if __name__ == "__main__":
    unittest.main()
