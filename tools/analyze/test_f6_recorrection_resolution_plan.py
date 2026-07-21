#!/usr/bin/env python3
"""Tests for AGENT-501 F6 re-correction resolution package."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_f6_recorrection_resolution_plan as builder  # noqa: E402


class F6RecorrectionResolutionPlanTests(unittest.TestCase):
    def test_builder_emits_expected_outputs_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-501")
            self.assertEqual(summary["pm5_rows"], 12)
            self.assertEqual(summary["ordinary_scoreable_rows"], 0)
            self.assertEqual(summary["ordinary_f6_candidate_rows"], 0)
            self.assertEqual(summary["recirculation_diagnostic_rows"], 12)
            self.assertEqual(summary["hybrid_scoreable_rows"], 0)
            self.assertEqual(summary["production_closure"], "F3_shah_apparent")
            self.assertEqual(summary["promotion_allowed"], "no")
            self.assertEqual(summary["native_output_mutation"], "none")
            self.assertEqual(summary["scheduler_action"], "none")

            for name in [
                "README.md",
                "f6_row_gate_matrix.csv",
                "f6_decision_tree.md",
                "f6_resolution_scorecard.csv",
                "f6_next_action_queue.csv",
                "recommended_further_studies.md",
                "source_manifest.csv",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["recommended_studies_count"], 6)

    def test_pm5_rows_are_diagnostic_not_ordinary_f6(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "f6_row_gate_matrix.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 12)
            self.assertEqual({"diagnostic_recirculation"}, {row["lane_classification"] for row in rows})
            self.assertEqual({"fail_material_reverse_flow"}, {row["ordinary_gate"] for row in rows})
            self.assertEqual({"no"}, {row["scoreable_now"] for row in rows})
            self.assertEqual({"no"}, {row["promotion_allowed"] for row in rows})
            self.assertTrue(all(float(row["RAF"]) >= 0.01 or float(row["RMF"]) >= 0.01 for row in rows))

    def test_scorecard_keeps_f3_and_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "f6_resolution_scorecard.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            by_item = {row["resolution_item"]: row for row in rows}
            self.assertEqual(by_item["production_baseline"]["decision"], "keep")
            self.assertEqual(by_item["production_baseline"]["production_baseline"], "F3_shah_apparent")
            self.assertEqual(by_item["ordinary_F6_single_stream"]["candidate_rows"], "0")
            self.assertEqual(by_item["ordinary_F6_single_stream"]["scoreable_rows"], "0")
            self.assertEqual(by_item["ordinary_F6_single_stream"]["promotion_allowed"], "no")
            self.assertEqual(by_item["recirculation_modeled_F6_onset"]["candidate_rows"], "12")
            self.assertEqual(by_item["recirculation_modeled_F6_onset"]["scoreable_rows"], "0")
            self.assertEqual(by_item["recirculation_modeled_F6_onset"]["promotion_allowed"], "no")

    def test_recommended_studies_include_required_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)
            text = (out / "recommended_further_studies.md").read_text(encoding="utf-8")

            for phrase in [
                "PM10",
                "high-heat",
                "Non-recirculating F6 anchor",
                "Q x insulation matrix",
                "Hybrid closure residual test",
                "Uncertainty sequence",
            ]:
                self.assertIn(phrase, text)

    def test_next_queue_names_terminal_and_study_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "f6_next_action_queue.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            action_ids = {row["action_id"] for row in rows}
            self.assertIn("pm10:terminal_harvest_and_pm5_style_postprocess", action_ids)
            self.assertIn("high_heat:terminal_harvest_nonrecirc_anchor", action_ids)
            self.assertIn("study:onset_bracketing_q_x_insulation_matrix", action_ids)
            self.assertIn("study:nonrecirculating_f6_anchor", action_ids)


if __name__ == "__main__":
    unittest.main()
