"""Tests for durable Salt1 fixture and thesis story integration."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.analyze import build_salt1_durable_test_data_and_thesis_story as mod


class Salt1DurableTestDataAndThesisStoryTests(unittest.TestCase):
    def test_fixture_rows_keep_all_salt1_cases_admitted(self) -> None:
        rows = mod.build_salt1_fixture_rows()
        by_case = {row["case_key"]: row for row in rows}

        self.assertEqual(set(by_case), {"salt1_nominal", "salt1_lo10q", "salt1_hi10q"})
        self.assertTrue(all(row["admission_status"] == "admitted" for row in rows))
        self.assertTrue(all(row["suspicious_monitor_flag"] == "no" for row in rows))
        self.assertTrue(all(row["has_stopAt_writeNow"] == "no" for row in rows))
        self.assertTrue(all(row["foam_fatal_in_tail"] == "no" for row in rows))
        self.assertEqual(by_case["salt1_lo10q"]["q_ratio"], "0.90")
        self.assertEqual(by_case["salt1_hi10q"]["q_ratio"], "1.10")
        self.assertIn("primary_closure_evidence", by_case["salt1_nominal"]["recommended_use"])
        self.assertIn("operational", by_case["salt1_nominal"]["disallowed_future_claim"])

    def test_thesis_story_has_required_parallel_lanes(self) -> None:
        rows = mod.build_thesis_story_rows()
        lanes = {row["story_lane"]: row for row in rows}

        for lane in [
            "implemented_predictive_model",
            "admitted_primary_evidence",
            "diagnostic_evidence",
            "admission_gates",
            "unresolved_blockers",
        ]:
            self.assertIn(lane, lanes)

        self.assertEqual(lanes["admitted_primary_evidence"]["current_status"], "admitted")
        self.assertEqual(lanes["diagnostic_evidence"]["current_status"], "diagnostic_only")
        self.assertEqual(lanes["unresolved_blockers"]["current_status"], "partly_blocked")

    def test_main_writes_fixture_copy_and_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            base = Path(tmp)
            out = base / "out"
            fixture = base / "salt1_primary_closure_cases.csv"
            thesis = base / "thesis.md"
            journal = base / "journal.md"
            status = base / "status.md"
            manifest = base / "import.json"

            with (
                patch.object(mod, "OUT", out),
                patch.object(mod, "FIXTURE", fixture),
                patch.object(mod, "THESIS", thesis),
                patch.object(mod, "JOURNAL", journal),
                patch.object(mod, "STATUS", status),
                patch.object(mod, "IMPORT", manifest),
            ):
                summary = mod.main()

            self.assertTrue((out / "README.md").is_file())
            self.assertTrue((out / "salt1_primary_closure_cases.csv").is_file())
            self.assertTrue(fixture.is_file())
            self.assertTrue(thesis.is_file())
            self.assertTrue(journal.is_file())
            self.assertTrue(status.is_file())
            self.assertTrue(manifest.is_file())
            self.assertTrue(summary["all_salt1_rows_admitted"])

            with fixture.open(newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 3)
            self.assertEqual({row["admission_status"] for row in rows}, {"admitted"})

            loaded = json.loads((out / "summary.json").read_text())
            self.assertEqual(loaded["salt1_fixture_rows"], 3)
            self.assertIn("unresolved_blockers", loaded["story_lanes"])


if __name__ == "__main__":
    unittest.main()
