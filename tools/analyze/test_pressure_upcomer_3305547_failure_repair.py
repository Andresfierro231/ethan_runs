#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_pressure_upcomer_3305547_failure_repair as mod


class PressureUpcomer3305547FailureRepairTest(unittest.TestCase):
    def test_partial_inventory_keeps_parsed_rows_diagnostic(self) -> None:
        inventory = mod.build_partial_parse_inventory()
        parsed = [row for row in inventory if row["exists"] == "yes"]

        self.assertTrue(parsed)
        self.assertTrue(all(row["parse_inventory_status"] in {"parsed_diagnostic_only", "parsed_blocked_or_incomplete"} for row in parsed))

    def test_salt2_lo10q_review_not_fit_admitted(self) -> None:
        rows = mod.build_salt2_lo10q_partial_admission_review()

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["admission_decision"] == "diagnostic_only_not_fit_admitted" for row in rows))

    def test_main_writes_failure_repair_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
                mock.patch.object(mod, "sacct_state", return_value={"job_id": mod.JOB_ID, "job_name": "upc_nominal", "scheduler_state": "FAILED", "elapsed": "00:02:17", "exit_code": "1:0", "nodes": "1", "nodelist": "c308-005", "scheduler_source": "test"}),
            ):
                summary = mod.main()

            self.assertEqual(summary["job_state"], "FAILED")
            self.assertEqual(summary["fit_admitted_rows"], 0)
            self.assertGreaterEqual(summary["relaunch_needed_cases"], 3)
            self.assertTrue((base / "out/remaining_case_relaunch_queue.csv").exists())


if __name__ == "__main__":
    unittest.main()
