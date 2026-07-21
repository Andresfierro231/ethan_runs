#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_high_heat_status_refresh_2026_07_20 as mod


class HighHeatStatusRefresh20260720Test(unittest.TestCase):
    def test_diagnostic_policy_forbids_predictive_fit(self) -> None:
        rows = mod.build_diagnostic_use_policy(mod.load_cases())

        self.assertTrue(rows)
        self.assertTrue(all(row["predictive_fit_use"] == "forbidden" for row in rows))

    def test_walltime_risk_keeps_admission_false(self) -> None:
        live = [{"job_id": "3299610", "scheduler_state": "RUNNING", "latest_solver_time_s": 11000.0, "target_end_time_s": 22000.0}]
        rows = mod.build_walltime_risk(live)

        self.assertEqual(rows[0]["walltime_risk"], "high")
        self.assertEqual(rows[0]["admitted_evidence_now"], "false")

    def test_main_writes_status_refresh(self) -> None:
        fake_sched = {
            "3299610": {"job_id": "3299610", "job_name": "salt4_q3x_probe", "scheduler_state": "RUNNING", "elapsed": "3-00:00:00", "nodes": "1", "nodelist_or_reason": "node", "scheduler_source": "test"},
            "3299620": {"job_id": "3299620", "job_name": "salt4_heat_pack", "scheduler_state": "RUNNING", "elapsed": "3-00:00:00", "nodes": "1", "nodelist_or_reason": "node", "scheduler_source": "test"},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
                mock.patch.object(mod, "scheduler_rows", return_value=fake_sched),
            ):
                summary = mod.main()

            self.assertEqual(summary["running_job_count"], 2)
            self.assertEqual(summary["admitted_rows_now"], 0)
            self.assertTrue((base / "out/diagnostic_only_use_policy.csv").exists())


if __name__ == "__main__":
    unittest.main()
