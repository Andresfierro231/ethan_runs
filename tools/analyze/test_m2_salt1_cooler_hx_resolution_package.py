#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_m2_salt1_cooler_hx_resolution_package as mod


class M2Salt1CoolerHxResolutionPackageTest(unittest.TestCase):
    def test_no_salt1_cooler_hx_value_is_fabricated(self) -> None:
        audit = mod.build_salt1_cooler_hx_source_audit()
        projection = mod.build_salt1_cooler_hx_projection_candidate(audit)

        self.assertEqual(projection[0]["projection_status"], "blocked_missing_supported_scorecard_row")
        self.assertEqual(projection[0]["candidate_value"], "")

    def test_holdout_scoring_remains_disabled_when_missing(self) -> None:
        audit = [{"salt1_cooler_hx_supported": "false", "source_path": "none"}]
        projection = mod.build_salt1_cooler_hx_projection_candidate(audit)
        decision = mod.build_m2_score_ready_decision(projection)[0]

        self.assertEqual(decision["decision"], "blocked_missing_salt1_cooler_hx")
        self.assertEqual(decision["holdout_score_release"], "false")
        self.assertEqual(decision["holdout_rows_scored_now"], 0)

    def test_supported_row_would_release_4row_decision(self) -> None:
        audit = [{"salt1_cooler_hx_supported": "true", "source_path": "supported.csv"}]
        projection = mod.build_salt1_cooler_hx_projection_candidate(audit)
        decision = mod.build_m2_score_ready_decision(projection)[0]

        self.assertEqual(decision["decision"], "score_ready_4row_supported")
        self.assertEqual(decision["holdout_score_release"], "true")

    def test_main_writes_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertEqual(summary["decision"], "blocked_missing_salt1_cooler_hx")
            self.assertEqual(summary["holdout_rows_scored_now"], 0)
            self.assertTrue((base / "out/optional_3row_exception_memo.csv").exists())


if __name__ == "__main__":
    unittest.main()
