from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_source_bounded_cv_definition as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SourceBoundedCvDefinitionTests(unittest.TestCase):
    def test_split_reasons_deduplicates(self) -> None:
        self.assertEqual(builder.split_reasons("a;b", "b;c"), ["a", "b", "c"])

    def test_case_decision_blocks_current_evidence(self) -> None:
        decision = builder.case_decision("salt_2", builder.load_inputs())
        self.assertEqual(decision["release_status"], "blocked_source_bounded_cv_not_released")
        self.assertEqual(decision["s12_hiax1_unlocked"], "false")
        self.assertIn("missing_positive_right_leg_wall_faces_or_area", decision["blocking_reason"])

    def test_package_writes_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertFalse(payload["summary"]["s12_hiax1_unlocked"])
            for name in [
                "recirc_cv_cells.csv",
                "exchange_interface_faces.csv",
                "trusted_wall_faces.csv",
                "wall_core_band.csv",
                "normal_convention.csv",
                "source_sink_boundary_ledger.csv",
                "release_decision.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / name).exists(), name)

    def test_release_decision_has_three_blocked_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            builder.build_package(out)
            release_rows = rows(out / "release_decision.csv")
            self.assertEqual(len(release_rows), 3)
            self.assertTrue(all(row["release_status"].startswith("blocked") for row in release_rows))


if __name__ == "__main__":
    unittest.main()
