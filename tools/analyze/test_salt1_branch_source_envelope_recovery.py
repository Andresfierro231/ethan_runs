#!/usr/bin/env python3
"""Tests for the Salt1 branch source-envelope recovery package."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_salt1_branch_source_envelope_recovery as builder


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class Salt1BranchSourceEnvelopeRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = builder.build()

    def test_fail_closed_no_release_or_score(self) -> None:
        self.assertEqual(self.summary["decision"], "salt1_branch_source_envelope_recovery_fail_closed_diagnostic_only")
        self.assertFalse(self.summary["release_allowed"])
        self.assertFalse(self.summary["source_property_release"])
        self.assertFalse(self.summary["candidate_freeze"])
        self.assertEqual(self.summary["score_values_emitted"], 0)

    def test_expected_families_and_junction_blocker(self) -> None:
        rows = read_rows(builder.OUT / "salt1_branch_source_evidence_matrix.csv")
        self.assertEqual(len(rows), 5)
        by_family = {row["source_family"]: row for row in rows}
        self.assertIn("junction", by_family)
        self.assertEqual(by_family["junction"]["recovered_row_present"], "False")
        self.assertEqual(by_family["junction"]["strict_source_envelope_release_candidate"], "False")

    def test_forbidden_trace_blocks_recovered_rows(self) -> None:
        rows = read_rows(builder.OUT / "salt1_branch_source_evidence_matrix.csv")
        recovered = [row for row in rows if row["recovered_row_present"] == "True"]
        self.assertEqual(len(recovered), 4)
        self.assertTrue(all(row["diagnostic_operator_usable"] == "True" for row in recovered))
        self.assertTrue(all(row["forbidden_wallHeatFlux_or_postProcessing_trace"] == "True" for row in recovered))
        self.assertTrue(all(row["strict_source_envelope_release_candidate"] == "False" for row in recovered))

    def test_gate_matrix_overall_fail_closed(self) -> None:
        gates = {row["gate"]: row for row in read_rows(builder.OUT / "salt1_source_envelope_gate_matrix.csv")}
        self.assertEqual(gates["overall_salt1_branch_source_envelope"]["status"], "fail_closed_no_release")
        self.assertEqual(gates["validation_holdout_external_use"]["status"], "pass_closed")


if __name__ == "__main__":
    unittest.main()
