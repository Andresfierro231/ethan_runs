#!/usr/bin/env python3
"""Tests for M2 holdout scoring readiness."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_m2_holdout_scoring_readiness as mod


class M2HoldoutScoringReadinessTest(unittest.TestCase):
    def test_queue_does_not_score_or_admit_fit_rows(self) -> None:
        queue = mod.build_scoring_row_queue()

        self.assertGreaterEqual(len(queue), 8)
        self.assertTrue(all(row["fit_allowed"] == "no" for row in queue))
        self.assertTrue(all(row["model_selection_allowed"] == "no" for row in queue))
        self.assertTrue(all(row["score_now"] == "no" for row in queue))
        self.assertIn("PM10", {row["row_family"] for row in queue})
        self.assertIn("PM5", {row["row_family"] for row in queue})
        self.assertIn("val_salt2", {row["row_family"] for row in queue})

    def test_pm10_rows_are_ready_after_model_artifact_when_unblocked(self) -> None:
        with mock.patch.object(mod, "model_is_score_ready", return_value=True):
            queue = mod.build_scoring_row_queue()

        pm10_rows = [row for row in queue if row["row_family"] == "PM10"]
        self.assertEqual(len(pm10_rows), 4)
        self.assertTrue(all(row["readiness_status"] == "ready_after_model_artifact_score_ready" for row in pm10_rows))
        self.assertTrue(all(row["score_now"] == "no" for row in pm10_rows))

    def test_main_writes_readiness_package_without_predictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertEqual(summary["rows_scored_now"], 0)
            self.assertEqual(summary["fit_rows_added"], 0)
            self.assertFalse(summary["holdout_predictions_created"])
            with (base / "out/scoring_row_queue.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            with (base / "import.json").open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
