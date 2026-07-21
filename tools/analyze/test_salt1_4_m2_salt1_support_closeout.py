#!/usr/bin/env python3
"""Tests for Salt1 M2 support closeout."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_salt1_4_m2_salt1_support_closeout as mod


class Salt14M2Salt1SupportCloseoutTest(unittest.TestCase):
    def test_salt1_cooler_gap_is_closed_without_fabrication(self) -> None:
        candidate = mod.build_salt1_boundary_projection_candidate()
        by_term = {row["term_id"]: row for row in candidate}

        self.assertEqual(by_term["heater"]["projection_status"], "supported")
        self.assertEqual(by_term["heater"]["candidate_value"], "0.9897032903")
        self.assertEqual(by_term["cooler_hx"]["projection_status"], "blocked_missing_supported_scorecard_row")
        self.assertEqual(by_term["cooler_hx"]["candidate_value"], "")
        self.assertEqual(by_term["cooler_hx"]["admission_use"], "do_not_update_no_fabricated_cooler_projection")

    def test_update_decision_leaves_current_artifact_unchanged(self) -> None:
        decision = mod.build_m2_artifact_update_decision()[0]

        self.assertEqual(decision["decision"], "no_update_salt1_cooler_hx_support_missing")
        self.assertEqual(decision["salt1_gap_status"], "closed_blocked_nonfabricated")
        self.assertEqual(decision["current_artifact_action"], "leave_current_artifact_unchanged")
        self.assertEqual(decision["holdout_scoring_unblocked"], "false")

    def test_main_writes_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertEqual(summary["salt1_gap_status"], "closed_blocked_nonfabricated")
            self.assertFalse(summary["follow_on_artifact_emitted"])
            self.assertTrue((base / "out/salt1_m2_support_audit.csv").exists())
            with (base / "out/m2_artifact_update_decision.csv").open(newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 1)
            with (base / "import.json").open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
