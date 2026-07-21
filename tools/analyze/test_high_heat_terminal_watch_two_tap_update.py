#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_high_heat_terminal_watch_two_tap_update as mod


class HighHeatTerminalWatchTwoTapUpdateTest(unittest.TestCase):
    def test_running_jobs_keep_cand001_terminal_gated(self) -> None:
        watch = [{"scheduler_state": "R", "terminal_state": "false"}, {"scheduler_state": "R", "terminal_state": "false"}]
        cand = mod.build_two_tap_cand001_readiness_update(watch)[0]

        self.assertEqual(cand["readiness_status"], "terminal_gated_running")
        self.assertEqual(cand["launch_allowed_now"], "false")

    def test_terminal_jobs_require_review_before_release(self) -> None:
        watch = [{"scheduler_state": "COMPLETED", "terminal_state": "true"}, {"scheduler_state": "COMPLETED", "terminal_state": "true"}]
        cand = mod.build_two_tap_cand001_readiness_update(watch)[0]

        self.assertEqual(cand["readiness_status"], "terminal_review_required")

    def test_main_writes_terminal_watch(self) -> None:
        fake = {
            "3299610": {"job_id": "3299610", "job_name": "salt4_q3x_probe", "scheduler_state": "R", "elapsed": "1", "nodes": "1", "nodelist_or_reason": "node", "scheduler_source": "test"},
            "3299620": {"job_id": "3299620", "job_name": "salt4_heat_pack", "scheduler_state": "R", "elapsed": "1", "nodes": "1", "nodelist_or_reason": "node", "scheduler_source": "test"},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
                mock.patch.object(mod, "scheduler_rows", return_value=fake),
            ):
                summary = mod.main()

            self.assertEqual(summary["cand001_status"], "terminal_gated_running")
            self.assertFalse(summary["two_tap_launch_allowed_now"])
            self.assertTrue((base / "out/post_exit_harvest_gate.csv").exists())


if __name__ == "__main__":
    unittest.main()
