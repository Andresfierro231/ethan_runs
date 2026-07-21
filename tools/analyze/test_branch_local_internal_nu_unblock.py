#!/usr/bin/env python3
"""Tests for AGENT-459 branch-local Internal-Nu unblock package."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_branch_local_internal_nu_unblock as builder  # noqa: E402


class BranchLocalInternalNuUnblockTests(unittest.TestCase):
    def test_builder_outputs_expected_blocked_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-459")
            self.assertEqual(summary["blocker_decision"], "not_resolved")
            self.assertEqual(summary["fit_admissible_internal_nu_rows"], 0)
            self.assertEqual(summary["publication_ready_final_use_gci_rows"], 0)
            self.assertGreater(summary["targeted_queue_rows"], 0)

            required = [
                "README.md",
                "branch_local_thermal_admission.csv",
                "final_use_closure_qoi_gci.csv",
                "internal_nu_fit_admissible_rows.csv",
                "targeted_extraction_admission_queue.csv",
                "blocker_resolution_decision.csv",
                "source_manifest.csv",
                "summary.json",
            ]
            for filename in required:
                self.assertTrue((out / filename).exists(), filename)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["blocker_decision"], "not_resolved")

    def test_upcomer_rows_are_not_final_use_single_stream_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "final_use_closure_qoi_gci.csv").open(newline="", encoding="utf-8") as handle:
                final_rows = list(csv.DictReader(handle))
            self.assertTrue(final_rows)
            self.assertFalse(any(row["canonical_leg_id"] == "upcomer_left_vertical" for row in final_rows))

            with (out / "branch_local_thermal_admission.csv").open(newline="", encoding="utf-8") as handle:
                branch_rows = {row["canonical_leg_id"]: row for row in csv.DictReader(handle)}
            self.assertIn("upcomer_left_vertical", branch_rows)
            self.assertEqual(
                branch_rows["upcomer_left_vertical"]["branch_local_decision"],
                "hybrid_onset_diagnostic_not_single_stream",
            )


if __name__ == "__main__":
    unittest.main()
