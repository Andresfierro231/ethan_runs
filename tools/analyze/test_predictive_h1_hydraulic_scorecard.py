#!/usr/bin/env python3
"""Tests for the AGENT-310 H1 hydraulic scorecard."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_predictive_h1_hydraulic_scorecard as h1score


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class PredictiveH1HydraulicScorecardTests(unittest.TestCase):
    def test_scorecard_improves_mdot_without_thermal_fit(self) -> None:
        rows = h1score.build_scorecard()
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["thermal_fit_used"] == "false" for row in rows))
        self.assertTrue(all(row["movement_direction"] == "toward_cfd" for row in rows))
        f1 = [row for row in rows if row["base_variant_id"] == "F1_heater_only"]
        mean_reduction = sum(float(row["mdot_error_reduction_pct"]) for row in f1) / len(f1)
        self.assertGreater(mean_reduction, 50.0)

    def test_locked_split_boundaries_are_preserved(self) -> None:
        rows = h1score.build_scorecard()
        by_case = {row["case_id"]: row for row in rows if row["base_variant_id"] == "F1_heater_only"}
        self.assertEqual(by_case["salt_2"]["split_assignment"], "train")
        self.assertIn("training_residual", by_case["salt_2"]["split_score_boundary"])
        self.assertEqual(by_case["salt_3"]["split_assignment"], "validation")
        self.assertIn("no_refit", by_case["salt_3"]["split_score_boundary"])
        self.assertEqual(by_case["salt_4"]["split_assignment"], "holdout")
        self.assertIn("no_refit", by_case["salt_4"]["split_score_boundary"])

    def test_term_boundary_keeps_loss_families_separate(self) -> None:
        rows = h1score.build_term_boundary()
        by_term = {row["term_family"]: row for row in rows}
        required = {
            "straight_friction_pressure_gradient",
            "straight_section_named_loss",
            "component_K",
            "cluster_K",
            "branch_apparent_loss",
            "reset_development",
            "recirculation_diagnostics",
        }
        self.assertTrue(required.issubset(by_term))
        self.assertEqual(int(by_term["straight_friction_pressure_gradient"]["n_fit_target_or_fit_safe"]), 2)
        self.assertGreater(int(by_term["branch_apparent_loss"]["n_included_in_h1_proxy"]), 0)
        self.assertEqual(int(by_term["cluster_K"]["n_included_in_h1_proxy"]), 0)
        self.assertEqual(int(by_term["recirculation_diagnostics"]["n_fit_target_or_fit_safe"]), 0)

    def test_run_package_outputs_expected_files_and_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "scorecard"
            summary = h1score.run_package(out_dir)
            self.assertFalse(summary["thermal_fit_used"])
            self.assertFalse(summary["external_fluid_modified"])
            self.assertFalse(summary["publication_closure_allowed"])
            self.assertIn("diagnostic_proxy", summary["overall_decision"])
            self.assertTrue((out_dir / "README.md").exists())
            variant_rows = read_csv(out_dir / "h1_variant_decision_summary.csv")
            f1 = [row for row in variant_rows if row["base_variant_id"] == "F1_heater_only"][0]
            self.assertEqual(f1["movement_gate"], "pass_directional_screen")


if __name__ == "__main__":
    unittest.main()
