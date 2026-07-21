#!/usr/bin/env python3
"""Tests for the boundary-layer development scorecard."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_boundary_layer_development_scorecard as mod


class BoundaryLayerDevelopmentScorecardTest(unittest.TestCase):
    def test_toggle_scorecard_has_segment_by_toggle_grid(self) -> None:
        rows = mod.build_toggle_scorecard()
        regions = {row["loop_region"] for row in rows}
        toggles = {row["toggle_id"] for row in rows}

        self.assertEqual(len(rows), 35)
        self.assertEqual(len(regions), 7)
        self.assertEqual(len(toggles), 5)
        self.assertTrue(all(row["ablation_executable_now"] == "false" for row in rows))
        self.assertTrue(all("no hidden global multiplier" in row["guardrail"] for row in rows))

    def test_metric_contract_covers_required_outputs(self) -> None:
        rows = {row["metric"]: row for row in mod.build_metric_contract()}

        self.assertEqual(set(rows), {"mdot", "TP_RMSE", "TW_RMSE", "Tmean", "loop_delta_T"})
        self.assertTrue(all(row["runtime_leakage_allowed"] == "false" for row in rows.values()))
        self.assertTrue(all(row["score_status"] == "blocked_not_run" for row in rows.values()))

    def test_prerequisite_gates_keep_ablation_blocked(self) -> None:
        rows = {row["gate"]: row for row in mod.build_prerequisite_gate_rows()}

        self.assertEqual(rows["segment_pressure_models"]["status"], "blocked")
        self.assertEqual(rows["upcomer_hybrid"]["status"], "diagnostic_only")
        self.assertEqual(rows["branch_specific_ordinary_pipe"]["admitted_rows"], 0)

    def test_runtime_audit_forbids_shortcuts(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("hidden global friction or thermal multiplier", forbidden)
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("validation TP/TW temperatures", forbidden)

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
                self.assertEqual(summary["toggle_rows"], 35)
                self.assertEqual(summary["executable_ablation_rows"], 0)
                self.assertEqual(summary["metric_contract_rows"], 5)
                self.assertEqual(summary["runtime_audit_pass_rows"], 4)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "development_toggle_scorecard.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "development_toggle_scorecard.csv").open(newline="") as f:
                    toggles = list(csv.DictReader(f))
                self.assertEqual(len(toggles), 35)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
