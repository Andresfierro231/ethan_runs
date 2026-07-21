#!/usr/bin/env python3
"""Tests for the frozen upcomer hybrid candidate score package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_upcomer_hybrid_frozen_candidate_score as mod


class UpcomerHybridFrozenCandidateScoreTest(unittest.TestCase):
    def test_candidate_definition_forbids_ordinary_labels(self) -> None:
        rows = mod.build_candidate_definition()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["candidate_id"], "UH1_throughflow_pipe_plus_recirc_cell")
        self.assertEqual(rows[0]["admission_status"], "blocked")
        self.assertIn("single_stream_Nu", rows[0]["forbidden_labels"])
        self.assertIn("dp_throughflow_pipe", rows[0]["pressure_form"])

    def test_score_gates_are_blocked_until_anchors_and_scores(self) -> None:
        rows = mod.build_score_gate_rows()

        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["status"] == "blocked" for row in rows))
        self.assertTrue(any(row["score_gate"] == "onset_anchor_coverage" for row in rows))
        self.assertTrue(any(row["score_gate"] == "train_validation_holdout_tp_tw" for row in rows))

    def test_admission_decision_has_zero_admitted_rows(self) -> None:
        rows = mod.build_admission_decision()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["admission_status"], "blocked")
        self.assertEqual(rows[0]["hybrid_fit_admitted_rows"], 0)
        self.assertEqual(rows[0]["launched_anchor_rows"], 0)

    def test_runtime_audit_forbids_leakage(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("single-stream Nu/f_D/K labels", forbidden)
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("realized wallHeatFlux", forbidden)

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
                self.assertEqual(summary["candidate_rows"], 1)
                self.assertEqual(summary["candidate_admitted_rows"], 0)
                self.assertEqual(summary["blocked_score_gates"], 6)
                self.assertEqual(summary["runtime_audit_pass_rows"], 4)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "frozen_candidate_definition.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "hybrid_admission_decision.csv").open(newline="") as f:
                    decisions = list(csv.DictReader(f))
                self.assertEqual(decisions[0]["admission_status"], "blocked")
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
