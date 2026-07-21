#!/usr/bin/env python3
"""Tests for AGENT-470 frozen M3+TS coupled score package."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_m3ts_frozen_candidate_coupled_score as builder  # noqa: E402


class M3TSFrozenCandidateCoupledScoreTests(unittest.TestCase):
    def test_default_without_fluid_keeps_blocker_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            builder.OUT = Path(tmp)
            summary = builder.build_package(run_fluid=False)
            self.assertEqual(summary["blocker_decision"], "keep_open")
            self.assertEqual(summary["admitted_candidates"], 0)
            self.assertEqual(summary["coupled_status_counts"], {"not_run_login_node_budget_guardrail": 9})

    def test_admission_requires_heat_and_coupled_score_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            builder.OUT = Path(tmp)
            builder.build_package(run_fluid=False)
            with (Path(tmp) / "m3ts_admission_review.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(row["admission_decision"] == "not_admitted" for row in rows))
            self.assertTrue(any("holdout_heat_loss_gate_failed" in row["blocking_reasons"] for row in rows))
            self.assertTrue(any("validation_coupled_score_not_improved" in row["blocking_reasons"] for row in rows))

    def test_delta_summary_excludes_train_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            builder.OUT = Path(tmp)
            builder.build_package(run_fluid=False)
            with (Path(tmp) / "m2_m3_delta_summary.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 6)
            self.assertFalse(any(row["split_role"] == "train" for row in rows))


if __name__ == "__main__":
    unittest.main()
