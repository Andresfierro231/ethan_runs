#!/usr/bin/env python3
"""Tests for the Salt1-4 M2 predictive candidate freeze package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_salt1_4_m2_predictive_candidate_freeze as mod


class Salt14M2PredictiveCandidateFreezeTest(unittest.TestCase):
    def test_candidate_manifest_uses_only_final_nominal_training_rows(self) -> None:
        rows = mod.build_candidate_freeze_manifest()
        by_case = {row["case_key"]: row for row in rows}

        self.assertEqual(by_case.keys(), mod.FINAL_TRAINING_CASES)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["split_role"] == "final_training" for row in rows))
        self.assertTrue(all(row["candidate_fit_allowed"] == "yes" for row in rows))
        self.assertTrue(all(row["candidate_model_selection_allowed"] == "yes" for row in rows))
        self.assertTrue(all(row["model_family_id"] == "M2" for row in rows))

    def test_candidate_terms_admit_only_heater_and_cooler(self) -> None:
        rows = mod.build_candidate_model_terms()
        admitted = [row for row in rows if row["term_status"] == "admitted_predictive_boundary_term"]
        blocked = [row for row in rows if row["term_status"] == "blocked_or_diagnostic"]

        self.assertEqual({row["term_id"] for row in admitted}, {"heater", "cooler_hx"})
        self.assertTrue(all(row["candidate_fit_use"] == "included" for row in admitted))
        self.assertIn("wall_test_section_passive_boundary", {row["term_id"] for row in blocked})
        self.assertIn("pressure_lanes", {row["term_id"] for row in blocked})
        self.assertIn("upcomer_internal_nu", {row["term_id"] for row in blocked})
        self.assertIn("two_tap_corner_k", {row["term_id"] for row in blocked})
        self.assertTrue(all(row["candidate_fit_use"] == "excluded" for row in blocked))

    def test_runtime_and_holdout_audits_exclude_blind_rows(self) -> None:
        runtime_rows = mod.build_candidate_runtime_input_audit()
        holdout_rows = mod.build_holdout_exclusion_audit()
        by_case = {row["case_key"]: row for row in holdout_rows}

        self.assertTrue(all(row["gate"] == "pass" for row in runtime_rows))
        self.assertIn("PM5; PM10; val_salt2; new-CFD rows", {row["input_family"] for row in runtime_rows})
        for case_key in mod.FORBIDDEN_ROW_KEYS:
            self.assertIn(case_key, by_case)
            self.assertEqual(by_case[case_key]["candidate_fit_use"], "excluded_from_m2_candidate_fit")
            self.assertEqual(by_case[case_key]["candidate_model_selection_use"], "excluded_from_m2_candidate_selection")
            self.assertEqual(by_case[case_key]["exclusion_gate"], "pass")

    def test_main_writes_candidate_freeze_package(self) -> None:
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

            self.assertTrue(summary["candidate_freeze_created"])
            self.assertEqual(summary["training_rows"], 4)
            self.assertEqual(summary["admitted_predictive_terms"], 2)
            self.assertEqual(summary["holdout_rows_used_for_fit"], 0)
            self.assertFalse(summary["holdout_predictions_created"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertTrue((out / "candidate_freeze_manifest.csv").exists())
            self.assertTrue((out / "candidate_model_terms.csv").exists())
            self.assertTrue(status.exists())
            self.assertTrue(journal.exists())

            with (out / "candidate_freeze_manifest.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 4)
            with import_manifest.open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
