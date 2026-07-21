#!/usr/bin/env python3
"""Tests for the segment-local pressure model scorecard."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_segment_pressure_model_scorecard as mod


class SegmentPressureModelScorecardTest(unittest.TestCase):
    def test_scorecard_covers_required_regions_with_no_fit_admission(self) -> None:
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
        self.assertTrue(all(row["true_fd_or_k_fit_admitted_rows"] == 0 for row in rows))
        self.assertTrue(all(row["scoreable_predictive_model_rows"] == 0 for row in rows))
        self.assertEqual(by_region["upcomer"]["admission_status"], "blocked_upcomer_hybrid_required")
        self.assertIn("recirculation_mask", by_region["upcomer"]["primary_blockers"])
        self.assertEqual(by_region["junction_stub_connector"]["admission_status"], "diagnostic_only_apparent_loss")

    def test_model_slots_are_fit_forbidden_and_diagnostic(self) -> None:
        rows = mod.build_model_slot_rows(mod.build_segment_scorecard())

        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all(row["fit_allowed_now"] == "false" for row in rows))
        self.assertTrue(all(row["score_allowed_now"] == "diagnostic" for row in rows))
        hybrid_rows = [row for row in rows if row["loop_region"] == "upcomer"]
        self.assertTrue(any("hybrid" in row["model_slot"] for row in hybrid_rows))
        self.assertTrue(
            any(row["admission_status"] == "diagnostic_or_blocked_until_hybrid_model" for row in hybrid_rows)
        )

    def test_evidence_rollup_preserves_zero_current_fit_admission(self) -> None:
        rows = {row["evidence_source"]: row for row in mod.build_evidence_rollup(mod.build_segment_scorecard())}

        self.assertEqual(rows["pressure_ladder_recirc_admission"]["fit_admitted_rows"], 0)
        self.assertEqual(rows["hydraulic_chain_final_decisions"]["fit_admitted_rows"], 0)
        self.assertEqual(rows["f6_re_correction_unblock"]["fit_admitted_rows"], 0)
        self.assertEqual(rows["segment_scorecard_decisions"]["status"], "complete_no_fit_admitted")

    def test_runtime_audit_forbids_pressure_shortcuts(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("global friction multiplier", forbidden)
        self.assertIn("true f_D/K fit from recirculating rows", forbidden)
        self.assertIn("unbracketed residual as physical K", forbidden)

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
                self.assertEqual(summary["fit_admitted_pressure_rows"], 0)
                self.assertEqual(summary["scoreable_predictive_model_rows"], 0)
                self.assertEqual(summary["runtime_audit_pass_rows"], 4)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "segment_pressure_model_scorecard.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "segment_pressure_model_scorecard.csv").open(newline="") as f:
                    scorecard = list(csv.DictReader(f))
                self.assertEqual(len(scorecard), 7)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
