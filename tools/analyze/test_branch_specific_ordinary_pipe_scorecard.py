#!/usr/bin/env python3
"""Tests for the branch-specific ordinary pipe scorecard."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_branch_specific_ordinary_pipe_scorecard as mod


class BranchSpecificOrdinaryPipeScorecardTest(unittest.TestCase):
    def test_branch_mask_excludes_current_ordinary_aggregate_fits(self) -> None:
        rows = mod.build_branch_mask()
        by_branch = {row["branch_id"]: row for row in rows}

        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row["ordinary_pipe_fit_included"] == "false" for row in rows))
        self.assertEqual(by_branch["upcomer_left_vertical"]["handoff_target"], "TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL")
        self.assertEqual(by_branch["junction_stub_connector"]["admission_status"], "diagnostic_only_named_loss")
        self.assertEqual(by_branch["downcomer_right_vertical"]["admission_status"], "blocked_downcomer_policy")

    def test_model_contract_is_branch_specific_and_fit_forbidden(self) -> None:
        rows = mod.build_model_form_contract(mod.build_branch_mask())

        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row["fit_allowed_now"] == "false" for row in rows))
        self.assertTrue(any("HX" in row["allowed_model_form"] or "cooler" in row["allowed_model_form"] for row in rows))
        self.assertTrue(any("hybrid" in row["allowed_model_form"] for row in rows))

    def test_handoffs_cover_all_exclusions(self) -> None:
        mask = mod.build_branch_mask()
        handoffs = mod.build_handoff_rows(mask)

        self.assertEqual(len(handoffs), len(mask))
        self.assertTrue(any(row["handoff_target"] == "TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL" for row in handoffs))

    def test_runtime_audit_forbids_shortcuts(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("recirculating upcomer rows in ordinary-pipe aggregate", forbidden)
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("global Nu/f friction multiplier", forbidden)

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
                self.assertEqual(summary["ordinary_fit_included_branches"], 0)
                self.assertEqual(summary["ordinary_coefficient_fit_admitted_rows"], 0)
                self.assertEqual(summary["runtime_audit_pass_rows"], 4)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "ordinary_pipe_branch_mask.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "ordinary_pipe_branch_mask.csv").open(newline="") as f:
                    mask = list(csv.DictReader(f))
                self.assertEqual(len(mask), 7)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
