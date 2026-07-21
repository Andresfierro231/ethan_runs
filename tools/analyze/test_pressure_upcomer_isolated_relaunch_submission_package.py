#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_pressure_upcomer_isolated_relaunch_submission_package as mod


class PressureUpcomerIsolatedRelaunchSubmissionPackageTest(unittest.TestCase):
    def test_exact_six_relaunch_cases_are_selected(self) -> None:
        matrix = mod.build_isolated_relaunch_case_matrix()

        self.assertEqual({row["case_key"] for row in matrix}, mod.EXPECTED_RELAUNCH_CASES)
        self.assertEqual(len(matrix), 6)
        self.assertTrue(all(row["fit_release_after_relaunch"] == "false" for row in matrix))

    def test_preflight_blocks_missing_inputs(self) -> None:
        matrix = [
            {
                "case_key": "missing",
                "source_id": "missing_source",
                "representative_time_s": "",
                "source_case_dir": "",
                "existing_recon_dir": "",
            }
        ]
        preflight = mod.build_preflight_gate(matrix)

        self.assertEqual(preflight[0]["preflight_status"], "blocked")
        self.assertIn("time_present", preflight[0]["failed_checks"])

    def test_main_writes_package_without_fit_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertEqual(summary["case_count"], 6)
            self.assertEqual(summary["fit_rows_released_now"], 0)
            self.assertTrue((base / "out/scripts/submit_pressure_upcomer_isolated_relaunch.sbatch").exists())


if __name__ == "__main__":
    unittest.main()
