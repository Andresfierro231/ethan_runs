#!/usr/bin/env python3
"""Tests for AGENT-464 F6/upcomer blocker status scorecard."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_f6_upcomer_blocker_status_scorecard as builder  # noqa: E402


class F6UpcomerBlockerStatusScorecardTests(unittest.TestCase):
    def test_builder_keeps_both_blockers_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-464")
            self.assertEqual(summary["f6_blocker_decision"], "keep_open")
            self.assertEqual(summary["upcomer_blocker_decision"], "keep_open")
            self.assertEqual(summary["f6_fit_admissible_rows"], 0)
            self.assertEqual(summary["upcomer_single_stream_fit_rows"], 0)
            self.assertGreater(summary["queue_rows"], 0)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["f6_blocker_decision"], "keep_open")

    def test_f6_rows_are_diagnostic_and_upcomer_points_observed_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "f6_status_scorecard.csv").open(newline="", encoding="utf-8") as handle:
                f6_rows = list(csv.DictReader(handle))
            self.assertTrue(f6_rows)
            self.assertEqual({"diagnostic_only_keep_f3_production"}, {row["f6_decision"] for row in f6_rows})

            with (out / "upcomer_onset_classification.csv").open(newline="", encoding="utf-8") as handle:
                upcomer_rows = list(csv.DictReader(handle))
            self.assertEqual({"observed_recirculation_only"}, {row["classification"] for row in upcomer_rows})


if __name__ == "__main__":
    unittest.main()
