#!/usr/bin/env python3
"""Tests for PM10 same-window residual target builder."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_pm10_same_window_residual_targets as mod


def row(case_key: str, plane: str, p_rgh: str, q: str) -> dict[str, str]:
    return {
        "case_key": case_key,
        "plane_location": plane,
        "representative_time_s": "10",
        "sampled_plane_file": f"fixture/{case_key}/{plane}.vtk",
        "pressure_target_status": "pressure_plane_available",
        "area_m2": "1.0",
        "mean_p_rgh_pa": p_rgh,
        "mean_rho_kg_m3": "1000.0",
        "mean_speed_m_s": "1.0",
        "dynamic_pressure_pa": q,
        "source_paths": f"fixture/{case_key}/{plane}.vtk",
    }


class Pm10SameWindowResidualTargetsTests(unittest.TestCase):
    def test_target_rows_compute_partial_pressure_residual(self) -> None:
        rows: list[dict[str, str]] = []
        for case_key in mod.PM10_CASES:
            rows.extend(
                [
                    row(case_key, "upcomer_inlet", "10.0", "1.0"),
                    row(case_key, "upcomer_mid", "8.0", "1.5"),
                    row(case_key, "upcomer_outlet", "6.0", "3.0"),
                ]
            )

        targets = mod.target_rows(rows)

        self.assertEqual(len(targets), 4)
        self.assertEqual({target["target_status"] for target in targets}, {"residual_target_available"})
        self.assertEqual({target["pm10_pressure_partial_residual_pa"] for target in targets}, {"-6"})
        self.assertEqual({target["fit_allowed_now"] for target in targets}, {"no"})
        self.assertTrue(all("diagnostic_only" in target["pressure_residual_basis"] for target in targets))

    def test_missing_endpoint_blocks_target_without_admission(self) -> None:
        targets = mod.target_rows([row("salt2_lo10q", "upcomer_inlet", "10.0", "1.0")])
        salt2 = {target["case_key"]: target for target in targets}["salt2_lo10q"]

        self.assertEqual(salt2["target_status"], "blocked_missing_pressure_endpoint")
        self.assertIn("missing_inlet_or_outlet_plane", salt2["blockers"])
        self.assertEqual(salt2["runtime_input_allowed_now"], "no")

    def test_build_package_writes_reusable_outputs_from_mocked_planes(self) -> None:
        fixture_rows: list[dict[str, str]] = []
        for case_key in mod.PM10_CASES:
            fixture_rows.extend(
                [
                    row(case_key, "upcomer_inlet", "10.0", "1.0"),
                    row(case_key, "upcomer_outlet", "6.0", "3.0"),
                ]
            )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            with mock.patch.object(mod, "plane_pressure_rows", return_value=fixture_rows):
                summary = mod.build_package(Path(tmp) / "parsed", out)

            self.assertEqual(summary["residual_target_available_cases"], 4)
            with (out / "pm10_same_window_residual_targets.csv").open(newline="", encoding="utf-8") as handle:
                targets = list(csv.DictReader(handle))
            self.assertEqual(len(targets), 4)
            self.assertTrue((out / "README.md").exists())

    def test_current_default_build_finds_pm10_pressure_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = mod.build_package(output_dir=Path(tmp) / "out")

            self.assertEqual(summary["case_count"], 4)
            self.assertEqual(summary["plane_rows"], 12)
            self.assertEqual(summary["residual_target_available_cases"], 4)


if __name__ == "__main__":
    unittest.main()
