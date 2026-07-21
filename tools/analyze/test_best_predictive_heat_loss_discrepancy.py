#!/usr/bin/env python3
"""Tests for build_best_predictive_heat_loss_discrepancy.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_best_predictive_heat_loss_discrepancy as disc


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class BestPredictiveHeatLossDiscrepancyTests(unittest.TestCase):
    def test_best_model_is_f1_solve_case(self) -> None:
        rows = disc.best_model_results()
        self.assertEqual(set(rows), {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["variant_id"] for row in rows.values()}, {"F1_heater_only"})
        self.assertEqual({row["engine"] for row in rows.values()}, {"solve_case"})

    def test_discrepancy_rows_cover_five_legs_per_case(self) -> None:
        rows = disc.discrepancy_rows()
        self.assertEqual(len(rows), 15)
        for case_id in {"salt_2", "salt_3", "salt_4"}:
            legs = {row["leg"] for row in rows if row["case_id"] == case_id}
            self.assertEqual(legs, {"lower_leg", "upcomer", "cooling_branch", "downcomer", "junction"})

    def test_junction_is_under_loss_lane(self) -> None:
        rows = disc.discrepancy_rows()
        junction = [row for row in rows if row["leg"] == "junction"]
        self.assertEqual({row["heat_loss_bias"] for row in junction}, {"model_under_loses_heat"})
        self.assertTrue(all(float(row["model_minus_cfd_realized_loss_W"]) < 0.0 for row in junction))

    def test_build_package_outputs_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = disc.build_package(out)
            self.assertEqual(summary["task"], "AGENT-356")
            self.assertEqual(summary["best_model_variant"], "F1_heater_only")
            self.assertFalse(summary["predictive_hx_admitted"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["heavy_openfoam_run"])
            self.assertFalse(summary["external_fluid_modified"])

            for name in {
                "README.md",
                "methodology.md",
                "presentation_brief.md",
                "repeatability_and_refinement_guide.md",
                "thesis_reuse_index.md",
                "thesis_notes.md",
                "best_predictive_leg_heat_loss_discrepancy.csv",
                "best_predictive_case_heat_loss_summary.csv",
                "model_change_recommendations.csv",
                "source_manifest.csv",
                "summary.json",
            }:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["model_status"], "best_current_predictive_style_imposed_cooler_not_final_predictive_hx")

    def test_recommendations_name_required_model_changes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            disc.build_package(out)
            rows = {row["applies_to_leg"]: row for row in read_csv(out / "model_change_recommendations.csv")}
            self.assertIn("junction", rows)
            self.assertIn("junction/stub", rows["junction"]["model_area"])
            self.assertIn("external boundary", rows["downcomer"]["model_area"])
            self.assertIn("HX", rows["cooling_branch"]["required_change"])
            self.assertIn("realized CFD", rows["junction"]["guardrail"])

    def test_presentation_and_thesis_docs_are_findable_and_caveated(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            disc.build_package(out)
            brief = (out / "presentation_brief.md").read_text(encoding="utf-8")
            thesis = (out / "thesis_reuse_index.md").read_text(encoding="utf-8")
            readme = (out / "README.md").read_text(encoding="utf-8")

            self.assertIn("One-Sentence Takeaway", brief)
            self.assertIn("heat is lost in the wrong places", brief)
            self.assertIn("diagnostic that tells us exactly what to fix", brief)
            self.assertIn("Thesis Claim Status", thesis)
            self.assertIn("final predictive HX", thesis)
            self.assertIn("Open First", readme)
            self.assertIn("presentation_brief.md", readme)

    def test_repeatability_guide_preserves_refinement_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            disc.build_package(out)
            guide = (out / "repeatability_and_refinement_guide.md").read_text(encoding="utf-8")

            self.assertIn("python3.11 tools/analyze/build_best_predictive_heat_loss_discrepancy.py", guide)
            self.assertIn("Expected row counts", guide)
            self.assertIn("15 rows", guide)
            self.assertIn("Do not use realized CFD `wallHeatFlux`", guide)
            self.assertIn("junction under-loss should shrink", guide)


if __name__ == "__main__":
    unittest.main()
