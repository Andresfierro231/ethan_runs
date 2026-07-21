#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_two_tap_nonrecirc_source_family_refresh as mod


class TwoTapNonrecircSourceFamilyRefreshTest(unittest.TestCase):
    def test_cand001_is_preferred_but_terminal_gated(self) -> None:
        rows = mod.build_source_family_readiness()
        cand1 = next(row for row in rows if row["candidate_id"] == "CAND-001")

        self.assertIn("high-heat", cand1["source_family"].lower())
        self.assertEqual(cand1["launch_allowed_now"], "false")
        self.assertIn(cand1["readiness_status"], {"terminal_gated_running", "terminal_review_required"})

    def test_sampler_gate_locks_endpoint_and_no_make_positive(self) -> None:
        gate = mod.build_same_qoi_sampler_launch_gate([])[0]

        self.assertEqual(gate["endpoint_pair"], "lower_leg__s04->right_leg__s00")
        self.assertEqual(gate["launch_status"], "blocked")
        self.assertEqual(gate["no_make_positive_correction"], "true")

    def test_main_writes_refresh_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertFalse(summary["launch_allowed_now"])
            self.assertEqual(summary["preferred_candidate"], "CAND-001")
            self.assertTrue((base / "out/fallback_decision.csv").exists())


if __name__ == "__main__":
    unittest.main()
