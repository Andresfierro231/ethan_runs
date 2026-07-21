#!/usr/bin/env python3
"""Tests for the upcomer pipe-cell hybrid model package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_upcomer_pipe_cell_hybrid_model as mod


class UpcomerPipeCellHybridModelTest(unittest.TestCase):
    def test_candidate_contract_blocks_current_ordinary_pipe_lane(self) -> None:
        rows = {row["model_lane"]: row for row in mod.build_candidate_contract()}

        self.assertIn("ordinary_pipe", rows)
        self.assertIn("recirculating_upcomer_effective", rows)
        self.assertEqual(rows["ordinary_pipe"]["fit_allowed_now"], "false_for_current_upcomer")
        self.assertEqual(rows["recirculating_upcomer_effective"]["score_allowed_now"], "diagnostic_model_contract_ready")
        self.assertIn("single_stream_Nu", rows["recirculating_upcomer_effective"]["forbidden_labels"])

    def test_feature_scorecard_uses_recirculation_lane_without_fit(self) -> None:
        rows = mod.build_feature_scorecard()

        self.assertGreaterEqual(len(rows), 6)
        self.assertTrue(all(row["ordinary_fit_allowed"] == "false" for row in rows))
        self.assertTrue(all(row["hybrid_use_allowed"] == "diagnostic_only_not_calibrated" for row in rows))
        self.assertTrue(any(row["regime_class"] == "recirculating_upcomer_effective" for row in rows))
        self.assertTrue(all("single_stream_f_D" in row["blocked_labels"] for row in rows))

    def test_admission_decisions_keep_predictive_hybrid_blocked(self) -> None:
        rows = {row["decision_id"]: row for row in mod.build_admission_decisions()}

        self.assertEqual(rows["ordinary_upcomer_pipe_coefficients"]["admission_status"], "blocked")
        self.assertEqual(
            rows["hybrid_throughflow_pipe_plus_cell_contract"]["admission_status"],
            "diagnostic_only_contract_complete",
        )
        self.assertEqual(rows["hybrid_throughflow_pipe_plus_cell_contract"]["fit_allowed_now"], "false")
        self.assertIn("features and candidate form are defined", rows["hybrid_throughflow_pipe_plus_cell_contract"]["reason"])

    def test_runtime_audit_forbids_shortcuts(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("single-stream Nu/f_D/K labels on recirculating rows", forbidden)
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("realized wallHeatFlux", forbidden)
        self.assertIn("global friction or heat-transfer multiplier", forbidden)

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
                self.assertEqual(summary["ordinary_fit_admitted_rows"], 0)
                self.assertEqual(summary["hybrid_predictive_fit_admitted_rows"], 0)
                self.assertEqual(summary["runtime_audit_pass_rows"], 4)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "upcomer_admission_decision.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "recirculation_feature_scorecard.csv").open(newline="") as f:
                    features = list(csv.DictReader(f))
                self.assertGreaterEqual(len(features), 6)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
