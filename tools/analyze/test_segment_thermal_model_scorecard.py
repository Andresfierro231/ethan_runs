#!/usr/bin/env python3
"""Tests for the segment-local thermal model scorecard."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_segment_thermal_model_scorecard as mod


class SegmentThermalModelScorecardTest(unittest.TestCase):
    def test_scorecard_covers_regions_and_admission_statuses(self) -> None:
        rows = mod.build_segment_scorecard()
        by_region = {row["loop_region"]: row for row in rows}

        self.assertEqual(
            set(by_region),
            {
                "heater",
                "cooler_HX",
                "downcomer",
                "upcomer",
                "test_section",
                "junction_stub_connector",
                "lower_upper_legs",
            },
        )
        self.assertEqual(by_region["heater"]["admission_status"], "admitted_setup_source_term")
        self.assertEqual(by_region["cooler_HX"]["admission_status"], "admitted_setup_cooler_removal_candidate")
        self.assertEqual(by_region["test_section"]["admission_status"], "blocked_test_section_passive_loss")
        self.assertEqual(by_region["upcomer"]["admission_status"], "blocked_hybrid_cell_exchange_required")
        self.assertTrue(all(row["residual_internal_nu_fit_admitted_rows"] == 0 for row in rows))

    def test_slot_rows_do_not_admit_residual_internal_nu(self) -> None:
        slots = mod.build_slot_rows(mod.build_segment_scorecard())
        residual_rows = [row for row in slots if "internal_Nu" in row["thermal_slot"]]

        self.assertGreaterEqual(len(slots), 10)
        self.assertTrue(all(row["fit_allowed_now"] == "false" for row in residual_rows))
        self.assertTrue(
            all(row["admission_status"] == "not_admitted_residual_absorption_forbidden" for row in residual_rows)
        )
        self.assertTrue(any(row["admission_status"] == "admitted_setup_only" for row in slots))

    def test_evidence_rollup_preserves_setup_vs_diagnostic_split(self) -> None:
        rows = {row["evidence_source"]: row for row in mod.build_evidence_rollup(mod.build_segment_scorecard())}

        self.assertEqual(rows["predictive_boundary_submodel_admission"]["admitted_setup_rows"], 2)
        self.assertEqual(rows["test_section_heat_loss_model"]["admitted_setup_rows"], 0)
        self.assertEqual(rows["segment_scorecard_decisions"]["admitted_setup_rows"], 2)
        self.assertEqual(rows["segment_scorecard_decisions"]["status"], "complete_admission_status_split")

    def test_runtime_audit_forbids_thermal_leakage(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("realized wallHeatFlux", forbidden)
        self.assertIn("imposed CFD cooler duty", forbidden)
        self.assertIn("validation TP/TW temperatures", forbidden)
        self.assertIn("residual internal Nu fit", forbidden)
        self.assertIn("CFD mdot", forbidden)

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
                self.assertEqual(summary["segment_rows"], 7)
                self.assertEqual(summary["admitted_setup_model_rows"], 2)
                self.assertEqual(summary["residual_internal_nu_fit_admitted_rows"], 0)
                self.assertEqual(summary["runtime_audit_pass_rows"], 5)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "segment_thermal_model_scorecard.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "segment_thermal_model_scorecard.csv").open(newline="") as f:
                    scorecard = list(csv.DictReader(f))
                self.assertEqual(len(scorecard), 7)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
