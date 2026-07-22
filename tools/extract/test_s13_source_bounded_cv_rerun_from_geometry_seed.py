from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_source_bounded_cv_rerun_from_geometry_seed as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SourceBoundedCvRerunFromGeometrySeedTests(unittest.TestCase):
    def test_seed_case_releasable_requires_wall_interface_and_no_escape(self) -> None:
        row = {
            "seed_status": "released_geometry_seed_for_source_bounded_cv_rerun",
            "seed_cell_count": "10",
            "trusted_wall_face_count": "3",
            "trusted_wall_area_m2": "1.0",
            "internal_seed_core_interface_face_count": "4",
            "internal_seed_core_interface_area_m2": "2.0",
            "classified_cap_face_count": "2",
            "unclassified_escape_face_count": "0",
            "unclassified_escape_area_m2": "0",
            "source_bounded_cv_rerun_ready": "true",
        }
        self.assertEqual(builder.seed_case_releasable(row), (True, ""))
        row["unclassified_escape_face_count"] = "1"
        ready, reason = builder.seed_case_releasable(row)
        self.assertFalse(ready)
        self.assertIn("unclassified_boundary_escape_present", reason)

    def test_build_decision_rows_releases_current_seed_rows(self) -> None:
        seed_rows = builder.read_csv(builder.SEED / "geometry_seed_case_summary.csv")
        decisions = builder.build_decision_rows(seed_rows)
        self.assertEqual(len(decisions), 3)
        self.assertTrue(
            all(row["source_bounded_cv_release_status"] == "released_seed_source_bounded_cv_geometry" for row in decisions)
        )
        self.assertTrue(all(row["surface_extraction_ready"] == "true" for row in decisions))
        self.assertTrue(all(row["sampler_ready"] == "false" for row in decisions))

    def test_package_writes_expected_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["released_seed_cv_rows"], 3)
            self.assertEqual(payload["summary"]["surface_extraction_ready_rows"], 3)
            self.assertFalse(payload["summary"]["s12_hiax1_unlocked"])
            for name in [
                "seed_cv_release_decision.csv",
                "seed_cv_surface_contract.csv",
                "seed_cv_boundary_ledger.csv",
                "seed_cv_downstream_gate.csv",
                "s12_unlock_impact.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / name).exists(), name)

    def test_downstream_gate_keeps_sampler_and_s12_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            builder.build_package(out)
            gates = rows(out / "seed_cv_downstream_gate.csv")
            sampler_rows = [row for row in gates if row["downstream_lane"] == "sampler_manifest_refresh"]
            trigger_rows = [row for row in gates if row["downstream_lane"] == "S11_S12_S15_S6_trigger"]
            self.assertEqual(len(sampler_rows), 3)
            self.assertTrue(all(row["status"] == "blocked" for row in sampler_rows))
            self.assertTrue(all(row["status"] == "blocked" for row in trigger_rows))


if __name__ == "__main__":
    unittest.main()
