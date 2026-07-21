#!/usr/bin/env python3
"""Tests for AGENT-505 F6 anchor-first refinement package."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_f6_anchor_first_refinement as builder  # noqa: E402


class F6AnchorFirstRefinementTests(unittest.TestCase):
    def test_builder_outputs_anchor_first_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out, live_scheduler=False)

            self.assertEqual(summary["task"], "AGENT-505")
            self.assertEqual(summary["pm5_rows"], 12)
            self.assertEqual(summary["pm5_ordinary_anchor_rows"], 0)
            self.assertEqual(summary["pm5_recirculation_diagnostic_rows"], 12)
            self.assertEqual(summary["blocked_pending_terminal_rows"], 8)
            self.assertEqual(summary["ordinary_f6_scoreable_rows"], 0)
            self.assertEqual(summary["hybrid_scoreable_rows"], 0)
            self.assertEqual(summary["production_closure"], "F3_shah_apparent")
            self.assertEqual(summary["promotion_allowed"], "no")
            self.assertEqual(summary["scheduler_action"], "none_recorded_status_only")

            for name in [
                "README.md",
                "terminal_status_refresh.csv",
                "anchor_gate_table.csv",
                "f6_lane_decision.csv",
                "pressure_residual_scorecard.csv",
                "recommended_next_cfd_runs.csv",
                "source_manifest.csv",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertFalse(written["live_scheduler_requested"])

    def test_pm5_rows_remain_diagnostic_not_ordinary_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "anchor_gate_table.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            pm5_rows = [row for row in rows if row["evidence_family"] == "PM5"]
            self.assertEqual(len(pm5_rows), 12)
            self.assertEqual({"recirculation_diagnostic"}, {row["lane"] for row in pm5_rows})
            self.assertEqual({"fail_material_reverse_flow"}, {row["reverse_flow_gate"] for row in pm5_rows})
            self.assertEqual({"no"}, {row["scoreable_now"] for row in pm5_rows})
            self.assertEqual({"no"}, {row["promotion_allowed"] for row in pm5_rows})
            self.assertTrue(all(float(row["RAF"]) >= 0.01 or float(row["RMF"]) >= 0.01 for row in pm5_rows))

    def test_terminal_rows_are_not_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "anchor_gate_table.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            blocked = [row for row in rows if row["lane"] == "blocked_pending_terminal"]
            self.assertEqual(len(blocked), 8)
            self.assertEqual({"no"}, {row["scoreable_now"] for row in blocked})
            self.assertEqual({"no"}, {row["promotion_allowed"] for row in blocked})
            self.assertEqual(
                {"not_evaluated_pending_terminal_harvest"},
                {row["reverse_flow_gate"] for row in blocked},
            )

    def test_lane_and_pressure_scorecards_keep_f3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "f6_lane_decision.csv").open(newline="", encoding="utf-8") as handle:
                lane_rows = list(csv.DictReader(handle))
            with (out / "pressure_residual_scorecard.csv").open(newline="", encoding="utf-8") as handle:
                pressure_rows = list(csv.DictReader(handle))

            self.assertEqual({"F3_shah_apparent"}, {row["production_baseline"] for row in lane_rows})
            self.assertEqual({"no"}, {row["promotion_allowed"] for row in lane_rows})
            self.assertIn("F3_shah_apparent", {row["model_or_evidence"] for row in pressure_rows})
            self.assertEqual(
                {"keep"},
                {row["decision"] for row in pressure_rows if row["model_or_evidence"] == "F3_shah_apparent"},
            )
            self.assertTrue(all(row["decision"] != "promote" for row in pressure_rows))

    def test_next_cfd_recommendations_include_sentinels_and_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "recommended_next_cfd_runs.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            case_keys = {row["case_key"] for row in rows}
            study_groups = {row["study_group"] for row in rows}
            self.assertIn("salt3_jin_q1500w_hiins_onset_anchor", case_keys)
            self.assertIn("salt3_jin_q0150w_loins_onset_anchor", case_keys)
            self.assertIn("small_q_x_insulation_matrix", study_groups)
            self.assertEqual(len(rows), 11)
            self.assertTrue(all("RAF/RMF" in row["required_outputs"] for row in rows))


if __name__ == "__main__":
    unittest.main()
