#!/usr/bin/env python3
"""Tests for the coupled segment M3+TS scorecard."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import run_coupled_segment_m3ts_scorecard as mod


class CoupledSegmentM3TSScorecardTest(unittest.TestCase):
    def test_prerequisite_matrix_blocks_final_forward(self) -> None:
        rows = {row["gate"]: row for row in mod.build_prerequisite_matrix()}

        self.assertEqual(rows["segment_pressure_models"]["status"], "blocked")
        self.assertEqual(rows["segment_pressure_models"]["admitted_rows"], 0)
        self.assertEqual(rows["upcomer_hybrid"]["status"], "diagnostic_only")
        self.assertEqual(rows["previous_m3ts_candidates"]["admitted_rows"], 0)
        self.assertTrue(any(row["blocking"] == "true" for row in rows.values()))

    def test_candidate_scorecard_has_zero_admissions(self) -> None:
        rows = mod.build_candidate_scorecard()

        self.assertGreaterEqual(len(rows), 4)
        self.assertTrue(all(row["candidate_admitted"] == "false" for row in rows))
        self.assertTrue(any(row["candidate_id"] == "segment_setup_only_forward_v1" for row in rows))
        self.assertTrue(any("pressure_closure_zero_admitted" in row["blocking_reasons"] for row in rows))

    def test_admission_status_scorecard_has_required_categories(self) -> None:
        rows = {row["admission_status"]: row for row in mod.build_admission_status_scorecard()}

        self.assertEqual(set(rows), {"admitted", "validation-only", "diagnostic-only", "blocked"})
        self.assertEqual(rows["admitted"]["row_count"], 0)
        self.assertGreater(int(rows["validation-only"]["row_count"]), 0)
        self.assertGreater(int(rows["blocked"]["row_count"]), 0)

    def test_runtime_audit_forbids_shortcuts(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("validation TP/TW temperatures", forbidden)
        self.assertIn("realized wallHeatFlux", forbidden)
        self.assertIn("global friction/thermal multiplier", forbidden)

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
                self.assertEqual(summary["candidates_admitted"], 0)
                self.assertEqual(summary["admission_status_rows"], 4)
                self.assertEqual(summary["final_forward_v1_status"], "blocked")
                self.assertEqual(summary["runtime_audit_pass_rows"], 5)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "admission_status_scorecard.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "admission_status_scorecard.csv").open(newline="") as f:
                    admission = list(csv.DictReader(f))
                self.assertEqual(len(admission), 4)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
