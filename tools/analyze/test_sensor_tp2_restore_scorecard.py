#!/usr/bin/env python3
"""Tests for final TP2 restore / TW10 exclude scorecard."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_sensor_tp2_restore_scorecard as mod


class SensorTp2RestoreScorecardTest(unittest.TestCase):
    def test_policy_rows_restore_tp2_and_exclude_tw10(self) -> None:
        rows = {row["sensor"]: row for row in mod.policy_rows()}

        tp2 = rows["TP2"]
        self.assertEqual(tp2["source_segment_after_refresh"], mod.TP2_RESTORED_SEGMENT)
        self.assertEqual(tp2["aggregate_score_after_refresh"], "yes")
        self.assertEqual(tp2["finite_prediction_rows"], 3)
        self.assertEqual(tp2["total_rows"], 3)
        self.assertEqual(tp2["runtime_temperature_allowed"], "false")
        self.assertEqual(tp2["fit_allowed"], "false")
        self.assertEqual(tp2["score_gate_status"], "pass")

        tw10 = rows["TW10"]
        self.assertEqual(tw10["aggregate_score_after_refresh"], "no")
        self.assertEqual(tw10["runtime_temperature_allowed"], "false")
        self.assertEqual(tw10["fit_allowed"], "false")
        self.assertIn("active-HX shell-state", tw10["blocker_or_caveat"])

    def test_aggregate_before_after_counts_and_rmse_are_documented(self) -> None:
        rows = {row["aggregate_policy"]: row for row in mod.aggregate_rows()}
        current = rows["current_policy_excludes_tp2_tw10"]
        restored = rows["restored_policy_includes_tp2_excludes_tw10"]

        self.assertEqual(int(current["tp_count"]), 5)
        self.assertEqual(int(current["tw_count"]), 10)
        self.assertEqual(int(restored["tp_count"]), 6)
        self.assertEqual(int(restored["tw_count"]), 10)
        self.assertAlmostEqual(float(current["rmse_K"]), 163.588758922)
        self.assertAlmostEqual(float(restored["rmse_K"]), 163.760647979)
        self.assertIn("TP2", restored["included_sensors"])
        self.assertEqual(restored["excluded_sensors"], "TW10")

    def test_gate_rows_all_pass(self) -> None:
        gates = {row["gate"]: row["status"] for row in mod.gate_rows()}

        self.assertEqual(gates["TP2_source_segment_named"], "pass")
        self.assertEqual(gates["TP2_runtime_input_forbidden"], "pass")
        self.assertEqual(gates["TP2_finite_prediction_before_aggregate"], "pass")
        self.assertEqual(gates["TW10_excluded_until_active_hx_shell_state"], "pass")

    def test_main_writes_complete_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            out = base / "out"
            status = base / "status.md"
            journal = base / "journal.md"
            import_manifest = base / "import.json"
            with (
                mock.patch.object(mod, "OUT", out),
                mock.patch.object(mod, "STATUS", status),
                mock.patch.object(mod, "JOURNAL", journal),
                mock.patch.object(mod, "IMPORT", import_manifest),
            ):
                summary = mod.main()
                self.assertEqual(summary["sensor_rows"], 17)
                self.assertEqual(summary["tp2_source_segment"], mod.TP2_RESTORED_SEGMENT)
                self.assertEqual(summary["tp2_finite_rows"], 3)
                self.assertEqual(summary["current_tp_count"], 5)
                self.assertEqual(summary["restored_tp_count"], 6)
                self.assertEqual(summary["tw10_aggregate_after_refresh"], "no")
                self.assertTrue(summary["all_gates_pass"])
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "sensor_policy_scorecard.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "sensor_policy_scorecard.csv").open(newline="") as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 17)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
