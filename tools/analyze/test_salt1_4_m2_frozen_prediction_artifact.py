#!/usr/bin/env python3
"""Tests for the Salt1-4 M2 frozen prediction artifact."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_salt1_4_m2_frozen_prediction_artifact as mod


class Salt14M2FrozenPredictionArtifactTest(unittest.TestCase):
    def test_model_freeze_records_admitted_terms_and_blocked_terms(self) -> None:
        freeze = mod.build_candidate_model_freeze()

        self.assertEqual(freeze["frozen_model_id"], mod.FROZEN_MODEL_ID)
        self.assertEqual(freeze["source_candidate_freeze_id"], mod.SOURCE_CANDIDATE_FREEZE_ID)
        self.assertEqual(freeze["holdout_rows_scored"], 0)
        self.assertEqual(freeze["blind_rows_used_for_fit"], 0)
        self.assertEqual({row["term_id"] for row in freeze["admitted_terms"]}, {"heater", "cooler_hx"})
        self.assertEqual(freeze["admitted_terms"][0]["fitted_scalar"], "0.9897032903")
        self.assertIn("two_tap_corner_k", {row["term_id"] for row in freeze["blocked_terms"]})

    def test_train_predictions_are_nominal_only_and_do_not_fabricate_salt1(self) -> None:
        rows = mod.build_train_row_predictions()
        by_case = {row["case_key"]: row for row in rows}

        self.assertEqual(set(by_case), {"salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"})
        self.assertEqual(len(rows), 4)
        self.assertEqual(by_case["salt1_nominal"]["admitted_boundary_prediction_status"], "missing_supported_scorecard_row")
        self.assertEqual(by_case["salt1_nominal"]["cooler_prediction_status"], "missing_supported_scorecard_row")
        for case_key in ("salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"):
            self.assertEqual(
                by_case[case_key]["admitted_boundary_prediction_status"],
                "admitted_boundary_prediction_available",
            )
            self.assertNotEqual(by_case[case_key]["cooler_predicted_qhx_W"], "")
        self.assertTrue(all(row["holdout_or_external_scoring"] == "not_performed" for row in rows))

    def test_runtime_audit_excludes_blind_rows_and_targets(self) -> None:
        rows = mod.build_freeze_runtime_audit()

        self.assertTrue(all(row["gate"] == "pass" for row in rows))
        families = {row["input_family"] for row in rows}
        self.assertIn("PM5", families)
        self.assertIn("PM10", families)
        self.assertIn("val_salt2", families)
        self.assertIn("new-CFD", families)
        self.assertIn("CFD mdot; realized CFD wallHeatFlux; pressure losses; validation temperatures", families)

    def test_main_writes_artifact(self) -> None:
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

            self.assertTrue(summary["frozen_prediction_artifact_created"])
            self.assertEqual(summary["train_rows"], 4)
            self.assertEqual(summary["rows_with_full_admitted_boundary_predictions"], 3)
            self.assertEqual(summary["rows_missing_supported_scorecard"], 1)
            self.assertEqual(summary["holdout_rows_scored"], 0)
            self.assertEqual(summary["blind_rows_used_for_fit"], 0)
            self.assertTrue((out / "candidate_model_freeze.json").exists())
            self.assertTrue((out / "train_row_predictions.csv").exists())
            with (out / "train_row_predictions.csv").open(newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 4)
            with import_manifest.open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
