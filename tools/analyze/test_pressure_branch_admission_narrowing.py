#!/usr/bin/env python3
"""Tests for branch-level pressure admission narrowing."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_pressure_branch_admission_narrowing as mod


class PressureBranchAdmissionNarrowingTest(unittest.TestCase):
    def test_branch_rows_keep_zero_fit_admissions(self) -> None:
        rows = mod.build_branch_admission_rows()
        by_branch = {row["branch_id"]: row for row in rows}

        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row["fit_admitted_pressure_rows"] == 0 for row in rows))
        self.assertEqual(by_branch["lower_upper_legs"]["least_risk_candidate"], "true")
        self.assertEqual(by_branch["junction_stub_connector"]["admission_status"], "diagnostic-only")
        self.assertEqual(by_branch["upcomer_left_vertical"]["admission_status"], "blocked")

    def test_gate_matrix_and_missing_queue_are_concrete(self) -> None:
        branches = mod.build_branch_admission_rows()
        gates = mod.build_gate_matrix(branches)
        missing = mod.build_missing_queue(branches)

        self.assertEqual(len(gates), 42)
        self.assertGreater(len(missing), 0)
        self.assertTrue(any(row["missing_gate"] == "mesh_gci" for row in missing))
        self.assertTrue(any(row["priority"] == "high" for row in missing))

    def test_runtime_audit_forbids_pressure_shortcuts(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("global friction multiplier", forbidden)
        self.assertIn("ordinary f_D/K fit on recirculating rows", forbidden)

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
                self.assertEqual(summary["branch_rows"], 7)
                self.assertEqual(summary["fit_admitted_pressure_rows"], 0)
                self.assertEqual(summary["least_risk_candidate_rows"], 1)
                self.assertEqual(summary["runtime_audit_pass_rows"], 4)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "branch_pressure_admission.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "branch_pressure_admission.csv").open(newline="") as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 7)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
