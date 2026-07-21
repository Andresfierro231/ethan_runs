#!/usr/bin/env python3
"""Unit tests for the AGENT-406 PM5 wall-band/F6 verifier."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.analyze import build_pm5_wall_band_vtk_and_f6_unlock_repair as builder


class Pm5WallBandF6UnlockTests(unittest.TestCase):
    def test_requested_case_selection_covers_pm5_family(self) -> None:
        cases = builder.load_cases()

        self.assertEqual(set(cases), set(builder.REQUESTED_CASES))
        self.assertIn("salt2_lo5q", cases)
        self.assertIn("wallHeatFlux", builder.FIELD_SET)

    def test_empty_functions_include_repair(self) -> None:
        with TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "case"
            system_dir = case_dir / "system"
            system_dir.mkdir(parents=True)
            stale = system_dir / "functions"
            stale.write_text("old functions\n", encoding="utf-8")

            builder.ensure_empty_functions_include(case_dir)

            self.assertTrue(stale.exists())
            self.assertIn("Empty AGENT-406 scratch include", stale.read_text(encoding="utf-8"))
            self.assertTrue((system_dir / "functions.source_disabled_for_pm5_agent406").exists())

    def test_scorecard_separates_f6_from_internal_nu(self) -> None:
        rows = [
            {
                "case_key": "salt2_lo5q",
                "bulk_T_K": "600",
                "wall_T_K": "601",
                "Re": "100",
                "Pr": "20",
                "Ri": "1",
                "sampled_plane_file": "plane.vtk",
                "sampled_wall_file": "wall.vtk",
                "wallHeatFlux_available": "false",
                "wallHeatFlux_W_m2": "",
            }
        ]

        gates = {row["gate"]: row["status"] for row in builder.scorecard_rows(rows)}

        self.assertEqual(gates["pm5_full_plane_fields_for_f6"], "unlocked_for_bounded_review_not_admitted")
        self.assertEqual(gates["wall_band_vtk_wallHeatFlux_for_internal_nu"], "blocked")


if __name__ == "__main__":
    unittest.main()
