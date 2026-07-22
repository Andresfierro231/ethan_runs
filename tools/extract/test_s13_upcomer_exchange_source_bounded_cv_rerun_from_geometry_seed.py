from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SeededSourceBoundedCvRerunTests(unittest.TestCase):
    def test_load_seed_cells(self) -> None:
        self.assertEqual(len(builder.load_seed_cells("salt_2")), 38880)

    def test_boundary_rows_have_wall_and_interface(self) -> None:
        seed_cells = builder.load_seed_cells("salt_2")
        payload = builder.boundary_rows("salt_2", seed_cells)
        self.assertGreater(len(payload["wall"]), 0)
        self.assertGreater(len(payload["interface"]), 0)
        self.assertEqual(len(payload["escapes"]), 0)

    def test_case_decision_releases_seeded_geometry_gate(self) -> None:
        seed_summary = builder.by_case(builder.read_csv(builder.GEOMETRY_SEED / "geometry_seed_case_summary.csv"))
        seed_cells = builder.load_seed_cells("salt_3")
        decision = builder.case_decision("salt_3", seed_summary["salt_3"], builder.boundary_rows("salt_3", seed_cells))
        self.assertEqual(decision["source_bounded_cv_release_status"], "released_seeded_source_bounded_cv")
        self.assertEqual(decision["surface_preflight_ready"], "true")
        self.assertEqual(decision["sampler_ready"], "false")

    def test_package_writes_required_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out, write_closeout=False)
            self.assertEqual(payload["summary"]["released_case_count"], 3)
            for name in [
                "seeded_recirc_cv_cells.csv",
                "seeded_exchange_interface_faces.csv",
                "seeded_trusted_wall_faces.csv",
                "seeded_wall_core_band.csv",
                "seeded_normal_convention.csv",
                "seeded_source_sink_boundary_ledger.csv",
                "seeded_release_decision.csv",
                "downstream_gate.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / name).exists(), name)
            decisions = rows(out / "seeded_release_decision.csv")
            self.assertEqual(len(decisions), 3)
            self.assertTrue(all(row["surface_preflight_ready"] == "true" for row in decisions))


if __name__ == "__main__":
    unittest.main()
