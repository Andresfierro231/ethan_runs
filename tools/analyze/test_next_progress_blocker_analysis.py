#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_next_progress_blocker_analysis as mod


def fixture_state() -> dict[str, object]:
    return {
        "m2_score": {
            "decision": "blocked_missing_salt1_cooler_hx",
            "holdout_rows_blocked": 8,
            "holdout_rows_scored_now": 0,
        },
        "salt1_support": {
            "salt1_cooler_hx_projection_status": "blocked_missing_supported_scorecard_row",
        },
        "pressure_qos": {
            "submission_result": "not_attempted_retry_window_blocked",
            "active_submit_pressure_jobs": 3,
            "retry_now": False,
        },
        "pressure_rollup": {
            "admission_grade_candidate_rows": 0,
            "blocked_or_diagnostic_rows": 6,
        },
        "high_heat": {
            "cand001_status": "terminal_gated_running",
            "running_jobs": 2,
            "terminal_jobs": 0,
        },
        "holdout_blocked": [],
        "qos_window": [{"submit_command": "ssh login1 sbatch relaunch.sbatch"}],
        "two_tap": [{"launch_allowed_now": "false"}],
        "frontier": [],
    }


class NextProgressBlockerAnalysisTest(unittest.TestCase):
    def test_m2_blocker_preserved_without_salt1_cooler_hx(self) -> None:
        blockers = mod.build_active_blocker_ledger(fixture_state())
        m2 = next(row for row in blockers if row["blocker_id"] == "salt1_m2_cooler_hx_support")

        self.assertEqual(m2["current_state"], "blocked_missing_salt1_cooler_hx")
        self.assertIn("do not fabricate", m2["forbidden_shortcut"])

    def test_pressure_upcomer_ranked_scheduler_blocked(self) -> None:
        priorities = mod.build_progress_priority_matrix(fixture_state())
        pressure = next(row for row in priorities if row["lane"] == "pressure_upcomer_qos_retry")

        self.assertEqual(pressure["scheduler_dependency"], "QOS submit pressure")
        self.assertIn("preflight is clean", pressure["why_ranked_here"])

    def test_high_heat_does_not_allow_two_tap_launch_while_running(self) -> None:
        scheduler = mod.build_scheduler_wait_queue(fixture_state())
        high_heat = next(row for row in scheduler if row["queue_id"] == "high_heat_jobs_3299610_3299620")

        self.assertEqual(high_heat["scheduler_state"], "terminal_gated_running")
        self.assertEqual(high_heat["retry_now"], "false")

    def test_holdout_and_perturbation_rows_excluded_from_fit(self) -> None:
        guard = mod.build_holdout_fit_boundary_guard(fixture_state())
        blocked_families = {row["row_family"]: row for row in guard if row["row_family"] != "Salt1-4 nominal"}

        self.assertTrue(blocked_families)
        self.assertTrue(all(row["permitted_use_now"] == "not_for_fit_or_model_selection" for row in blocked_families.values()))
        self.assertTrue(all(row["fit_rows_added_now"] == 0 for row in guard))

    def test_main_writes_analysis_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertEqual(summary["best_next_move"], "m2_salt1_cooler_hx_resolution")
            self.assertEqual(summary["fit_rows_added_now"], 0)
            self.assertTrue((base / "out/active_blocker_ledger.csv").exists())
            self.assertTrue((base / "out/unlock_sequence.csv").exists())


if __name__ == "__main__":
    unittest.main()
