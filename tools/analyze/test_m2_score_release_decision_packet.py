#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_m2_score_release_decision_packet as mod


class M2ScoreReleaseDecisionPacketTest(unittest.TestCase):
    def test_default_decision_blocks_without_salt1_cooler_hx(self) -> None:
        decision = mod.build_default_blocked_decision()[0]

        self.assertEqual(decision["decision"], "blocked_missing_salt1_cooler_hx")
        self.assertEqual(decision["holdout_rows_scored_now"], 0)

    def test_exception_requirements_do_not_grant_exception(self) -> None:
        rows = mod.build_three_row_exception_requirements()

        self.assertTrue(any(row["status"] == "missing" for row in rows))
        self.assertTrue(all("required_before_release" in row for row in rows))

    def test_main_writes_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertFalse(summary["three_row_exception_granted"])
            self.assertEqual(summary["holdout_rows_scored_now"], 0)
            self.assertTrue((base / "out/holdout_rows_still_blocked.csv").exists())


if __name__ == "__main__":
    unittest.main()
