#!/usr/bin/env python3
"""Tests for the pressure alternate low-reverse anchor screen."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_pressure_alternate_low_reverse_anchor_screen as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PressureAlternateLowReverseAnchorScreenTest(unittest.TestCase):
    def test_build_outputs_no_existing_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "pressure_alternate_anchor_screen_complete_existing_replacement_not_found",
            )
            self.assertEqual(summary["existing_replacement_ready_rows"], 0)
            self.assertEqual(summary["component_K_or_F6_release_rows"], 0)
            self.assertEqual(summary["admissible_comparison_allowed_rows"], 0)
            self.assertEqual(summary["future_design_rows"], 11)
            self.assertEqual(summary["pm10_strong_recirculation_rows"], 4)
            self.assertFalse(summary["scheduler_query_or_action"])

            for name in [
                "alternate_anchor_screen.csv",
                "disqualification_matrix.csv",
                "no_launch_shortlist.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "README.md",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)
            json.loads((out / "summary.json").read_text(encoding="utf-8"))

    def test_screen_keeps_every_row_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            screen = rows(out / "alternate_anchor_screen.csv")
            self.assertTrue(screen)
            self.assertEqual({row["can_replace_CAND001_now"] for row in screen}, {"False"})
            self.assertEqual({row["component_K_or_F6_release_allowed"] for row in screen}, {"False"})
            self.assertTrue(
                all("component-K, F6, Shah" in row["claim_boundary"] for row in screen)
            )

    def test_disqualification_records_material_reverse_and_uq_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            disq = {row["blocker"]: row for row in rows(out / "disqualification_matrix.csv")}
            self.assertIn("material_reverse_flow", disq)
            self.assertIn("strong_material_reverse_flow", disq)
            self.assertIn("same_qoi_uq_missing", disq)
            self.assertEqual(disq["same_qoi_uq_missing"]["blocks_CAND001_replacement_now"], "True")


if __name__ == "__main__":
    unittest.main()
