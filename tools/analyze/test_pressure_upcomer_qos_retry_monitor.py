#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_pressure_upcomer_qos_retry_monitor as mod


class PressureUpcomerQosRetryMonitorTest(unittest.TestCase):
    def test_qos_window_blocks_when_active_jobs_exist(self) -> None:
        active = mod.build_active_scheduler_pressure(
            [{"job_id": "1", "partition": "dev", "job_name": "x", "user": "u", "state": "R", "elapsed": "1", "nodes": "1", "nodelist_or_reason": "n"}]
        )
        qos = mod.build_qos_submit_window(active)[0]

        self.assertEqual(qos["retry_now"], "false")
        self.assertEqual(qos["active_submit_pressure_jobs"], 1)

    def test_successful_submit_attempt_records_job_id(self) -> None:
        qos = [{"retry_now": "true"}]
        fake = mock.Mock(returncode=0, stdout="Submitted batch job 12345\n", stderr="")
        with mock.patch.object(mod.subprocess, "run", return_value=fake):
            attempt = mod.attempt_submit_if_allowed(qos, do_submit=True)

        self.assertTrue(attempt["attempted"])
        self.assertEqual(attempt["result"], "submitted")
        self.assertEqual(attempt["job_id"], "12345")

    def test_main_writes_monitor_without_cancelling_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
                mock.patch.object(mod, "scheduler_rows", return_value=[]),
            ):
                summary = mod.main(do_submit=False)

            self.assertFalse(summary["submission_attempted"])
            self.assertEqual(summary["fit_rows_released_now"], 0)
            self.assertTrue((base / "out/qos_submit_window.csv").exists())


if __name__ == "__main__":
    unittest.main()
