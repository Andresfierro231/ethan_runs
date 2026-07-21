#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_pressure_upcomer_isolated_relaunch_post_exit_rollup as mod


class PressureUpcomerIsolatedRelaunchPostExitRollupTest(unittest.TestCase):
    def test_missing_or_incomplete_rows_block_fit_release(self) -> None:
        status, reason = mod.classify_parsed_rows([{"metric_status": "incomplete", "admission_status": "blocked-missing-field", "quality_flags": "missing_plane_vtk"}])

        self.assertEqual(status, "blocked_missing_field")
        self.assertIn("missing", reason)

    def test_recirculation_is_diagnostic_only(self) -> None:
        row = {
            "metric_status": "parsed",
            "admission_status": "",
            "quality_flags": "",
            "reverse_area_fraction": "0.2",
            "reverse_mass_fraction": "0.0",
        }
        status, _ = mod.classify_parsed_rows([row])

        self.assertEqual(status, "diagnostic_only_recirculating")

    def test_main_writes_rollup_without_fit_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertEqual(summary["fit_rows_released_now"], 0)
            self.assertTrue((base / "out/fit_release_decision.csv").exists())


if __name__ == "__main__":
    unittest.main()
