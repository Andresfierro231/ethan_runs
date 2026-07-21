from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_f6_hydraulic_screen import build_f6_hydraulic_screen


class F6HydraulicScreenTests(unittest.TestCase):
    def test_screen_keeps_f6_blocker_open_without_global_multiplier(self) -> None:
        with tempfile.TemporaryDirectory(prefix="f6-hydraulic-screen-") as tmpdir:
            summary = build_f6_hydraulic_screen(Path(tmpdir))

            self.assertTrue(summary["f6_code_available"])
            self.assertEqual(summary["f6_decision"], "screen_only_keep_blocker_open")
            self.assertEqual(summary["f6_blocker_status"], "open")
            self.assertFalse(summary["thermal_fit_used"])
            self.assertFalse(summary["global_friction_multiplier_exported"])
            self.assertGreater(summary["h1_mean_error_reduction_pct"], 50.0)

    def test_scorecard_separates_f6_from_h1_forward_screen(self) -> None:
        with tempfile.TemporaryDirectory(prefix="f6-hydraulic-screen-") as tmpdir:
            out_dir = Path(tmpdir)
            build_f6_hydraulic_screen(out_dir)

            with (out_dir / "f6_hydraulic_scorecard.csv").open(encoding="utf-8", newline="") as handle:
                rows = {row["candidate_id"]: row for row in csv.DictReader(handle)}

            self.assertEqual(rows["F6_phi_re"]["uses_global_friction_multiplier"], "false")
            self.assertEqual(rows["F6_phi_re"]["mdot_forward_score_available"], "false")
            self.assertEqual(rows["F6_phi_re"]["blocker_status_after_screen"], "open")
            self.assertEqual(
                rows["H1_localized_named_loss_and_reset_bundle"]["decision"],
                "unblocks_forward_v1_diagnostic_scorecard_only",
            )


if __name__ == "__main__":
    unittest.main()
