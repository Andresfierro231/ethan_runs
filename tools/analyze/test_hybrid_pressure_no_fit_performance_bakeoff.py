#!/usr/bin/env python3
"""Tests for the hybrid pressure no-fit bakeoff builder."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_hybrid_pressure_no_fit_performance_bakeoff as builder
from tools.analyze import check_hybrid_pressure_no_fit_performance_bakeoff as checker


class HybridPressureNoFitBakeoffTests(unittest.TestCase):
    def test_performance_rows_preserve_no_admission(self) -> None:
        rows = builder.performance_rows(
            builder.read_csv(builder.THREE_LEVEL),
            builder.read_csv(builder.F3_STATUS),
            builder.read_csv(builder.S14_F3_TABLE),
        )
        self.assertEqual(4, len(rows))
        self.assertTrue(all(row["admission_status"] == "not_admitted" for row in rows))
        self.assertTrue(all(row["validation_rows_consumed"] == "0" for row in rows))
        self.assertTrue(any(row["method"] == "F3_shah_apparent_baseline_status" for row in rows))

    def test_baseline_rows_mark_f3_numeric_unavailable(self) -> None:
        rows = builder.baseline_rows(
            builder.read_csv(builder.F3_STATUS),
            builder.read_csv(builder.S10_F3_TABLE),
            builder.read_csv(builder.S14_F3_TABLE),
        )
        self.assertEqual(3, len(rows))
        self.assertTrue(all(row["numeric_comparison_available"] == "false" for row in rows))

    def test_decision_blocks_candidate_reviewability(self) -> None:
        rows = builder.decision_rows()
        self.assertTrue(any(row["decision"] == "no_thesis_evidence_only" for row in rows))

    def test_package_checker_passes_after_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            summary = builder.build(out_dir)
            self.assertEqual("thesis_evidence_only_not_candidate_reviewable", summary["candidate_reviewability"])
            self.assertEqual([], checker.check(out_dir))


if __name__ == "__main__":
    unittest.main()
