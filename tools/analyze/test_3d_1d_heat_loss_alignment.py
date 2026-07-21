#!/usr/bin/env python3
"""Tests for build_3d_1d_heat_loss_alignment.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_3d_1d_heat_loss_alignment as align


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class HeatLossAlignmentTests(unittest.TestCase):
    def test_split_signed_heat_uses_positive_into_fluid_convention(self) -> None:
        self.assertEqual(align.split_signed_heat(12.5), (12.5, 0.0))
        self.assertEqual(align.split_signed_heat(-7.25), (0.0, 7.25))
        self.assertEqual(align.sign_match(10.0, 2.0), "match")
        self.assertEqual(align.sign_match(-10.0, 2.0), "opposite_sign")

    def test_build_package_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = align.build_package(out)

            self.assertEqual(summary["task"], "AGENT-350")
            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["predictive_rows_admitted"], 0)
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["heavy_openfoam_run"])

            for name in {
                "README.md",
                "methodology_and_assumptions.md",
                "thesis_presentation_notes.md",
                "assumption_match_matrix.csv",
                "heat_loss_alignment_by_segment.csv",
                "heat_loss_alignment_by_role.csv",
                "case_heat_loss_summary.csv",
                "source_manifest.csv",
                "summary.json",
            }:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["study_mode"], "fixed_mdot_diagnostic_heat_path_alignment")

    def test_assumption_matrix_names_key_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            align.build_package(out)
            rows = read_csv(out / "assumption_match_matrix.csv")
            assumption_ids = {row["assumption_id"] for row in rows}

            self.assertIn("heater_setup_location_and_power", assumption_ids)
            self.assertIn("cooler_removal_location_and_duty", assumption_ids)
            self.assertIn("passive_wall_external_boundary", assumption_ids)
            self.assertIn("radiation_handling", assumption_ids)
            self.assertIn("wallheatflux_runtime_use", assumption_ids)
            self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})

    def test_radiation_off_rows_are_never_labeled_cfd_parity(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            align.build_package(out)
            rows = read_csv(out / "heat_loss_alignment_by_segment.csv")
            radiation_off = [row for row in rows if row["path_family"] == "radiation_off_sensitivity"]

            self.assertTrue(radiation_off)
            self.assertEqual(
                {row["evidence_class"] for row in radiation_off},
                {"radiation_off_sensitivity_not_cfd_parity"},
            )
            self.assertEqual(
                {row["admissibility_status"] for row in radiation_off},
                {"diagnostic_sensitivity_only"},
            )

    def test_segment_rows_have_source_paths_and_fixed_q_paths(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            align.build_package(out)
            rows = read_csv(out / "heat_loss_alignment_by_segment.csv")

            self.assertTrue(all(row["source_paths"] for row in rows))
            self.assertIn("B2_realized_wallflux_roles", {row["path_id"] for row in rows})
            self.assertIn("B3_imposed_setup_roles", {row["path_id"] for row in rows})
            b3 = [row for row in rows if row["path_id"] == "B3_imposed_setup_roles"]
            self.assertEqual(len(b3), 15)

    def test_source_manifest_has_hashes_for_inputs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            align.build_package(out)
            rows = read_csv(out / "source_manifest.csv")

            self.assertGreaterEqual(len(rows), 10)
            self.assertTrue(all(row["exists"] == "True" for row in rows))
            self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))


if __name__ == "__main__":
    unittest.main()
