#!/usr/bin/env python3
"""Tests for the Salt1-4 nominal final training freeze package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_salt1_4_nominal_final_freeze as mod


class Salt14NominalFinalFreezeTest(unittest.TestCase):
    def test_final_freeze_manifest_contains_only_nominal_training_rows(self) -> None:
        rows = mod.build_final_freeze_manifest()
        by_case = {row["case_key"]: row for row in rows}

        self.assertEqual(
            set(by_case),
            {"salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"},
        )
        self.assertTrue(all(row["split_role"] == "final_training" for row in rows))
        self.assertTrue(all(row["fit_allowed"] == "yes" for row in rows))
        self.assertTrue(all(row["model_selection_allowed"] == "yes" for row in rows))
        self.assertTrue(all(row["schema_parity_status"] == "pass" for row in rows))
        self.assertEqual(
            by_case["salt1_nominal"]["schema_source_status"],
            "promoted_salt1_schema_parity_package",
        )
        self.assertTrue(
            all(row["prediction_model_freeze_status"] == "not_created_no_fitting_performed" for row in rows)
        )

    def test_holdout_exclusion_audit_keeps_blind_rows_out_of_fit(self) -> None:
        rows = mod.build_holdout_exclusion_audit()
        by_case = {row["case_key"]: row for row in rows}

        for case_key in (
            "salt2_lo5q",
            "salt2_hi5q",
            "val_salt2",
            "salt2_lo10q",
            "salt2_hi10q",
            "salt4_lo10q",
            "salt4_hi10q",
            "salt3_q_insulation_matrix",
        ):
            self.assertIn(case_key, by_case)
            self.assertEqual(by_case[case_key]["fit_allowed"], "no")
            self.assertEqual(by_case[case_key]["model_selection_allowed"], "no")
            self.assertEqual(by_case[case_key]["exclusion_gate"], "pass")
            self.assertEqual(by_case[case_key]["freeze_inclusion"], "excluded_from_final_training_freeze")

    def test_schema_and_runtime_audits_close_salt1_parity_without_target_leakage(self) -> None:
        schema_rows = mod.build_schema_parity_review()
        runtime_rows = mod.build_runtime_input_audit()

        salt1_lanes = {row["schema_lane"] for row in schema_rows if row["case_group"] == "salt1_nominal"}
        self.assertEqual(
            salt1_lanes,
            {
                "split_manifest",
                "bc_source_material",
                "heat_ledger",
                "pressure_streamwise",
                "pressure_branch",
                "sensor_targets",
                "runtime_input_audit",
            },
        )
        self.assertTrue(all(row["parity_status"] == "pass" for row in schema_rows))
        self.assertTrue(all(row["gate"] == "pass" for row in runtime_rows))
        forbidden = " ".join(row["forbidden_runtime_input"] for row in runtime_rows)
        self.assertIn("perturbation/external/new-CFD", forbidden)
        self.assertIn("PM5/PM10/val_salt2/new-CFD", forbidden)

    def test_main_writes_freeze_package_without_model_freeze(self) -> None:
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

            self.assertEqual(summary["nominal_rows_frozen"], 4)
            self.assertTrue(summary["freeze_gate_pass"])
            self.assertTrue(summary["salt1_schema_parity_closed"])
            self.assertFalse(summary["prediction_model_freeze_created"])
            self.assertFalse(summary["fitting_performed"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertTrue((out / "final_freeze_manifest.csv").exists())
            self.assertTrue((out / "candidate_freeze_gate.csv").exists())

            with (out / "final_freeze_manifest.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 4)
            with import_manifest.open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
