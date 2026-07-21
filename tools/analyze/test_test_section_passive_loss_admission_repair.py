#!/usr/bin/env python3
"""Tests for test-section passive-loss admission repair."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_test_section_passive_loss_admission_repair as mod


class TestSectionPassiveLossAdmissionRepairTest(unittest.TestCase):
    def test_candidate_classes_keep_zero_admissions(self) -> None:
        rows = mod.build_candidate_class_rows()
        by_class = {row["candidate_class"]: row for row in rows}

        self.assertGreaterEqual(len(rows), 7)
        self.assertTrue(all(row["admission_status"] == "blocked" for row in rows))
        self.assertEqual(by_class["TS4_realized_external_loss_upper_bound"]["runtime_gate"], "fail_uses_realized_cfd_loss_at_runtime")
        self.assertIn("TS5_setup_resistance_network_wall_external", by_class)
        self.assertIn("TS6_radiation_if_independently_admitted", by_class)

    def test_missing_requirements_are_specific(self) -> None:
        rows = {row["requirement_id"]: row for row in mod.build_missing_requirements()}

        self.assertEqual(
            set(rows),
            {
                "setup_only_resistance_network_candidate",
                "validation_holdout_heat_gate",
                "coupled_m3ts_score_for_candidate",
                "independent_radiation_semantics",
            },
        )
        self.assertTrue(all(row["status"] == "missing" for row in rows.values()))

    def test_runtime_audit_forbids_leakage(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("realized wallHeatFlux", forbidden)
        self.assertIn("validation TP/TW temperatures", forbidden)
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("imposed CFD cooler duty", forbidden)

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
                self.assertEqual(summary["admitted_candidate_rows"], 0)
                self.assertEqual(summary["missing_requirement_rows"], 4)
                self.assertEqual(summary["runtime_audit_pass_rows"], 4)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "test_section_candidate_class_admission.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "test_section_candidate_class_admission.csv").open(newline="") as f:
                    rows = list(csv.DictReader(f))
                self.assertGreaterEqual(len(rows), 7)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
