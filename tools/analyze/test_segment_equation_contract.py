#!/usr/bin/env python3
"""Tests for the segment-resolved equation contract builder."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_segment_equation_contract as mod


class SegmentEquationContractTest(unittest.TestCase):
    def test_equations_expand_drive_loss_and_coupled_root(self) -> None:
        rows = {row["equation_id"]: row for row in mod.equation_forms()}

        self.assertIn("buoyancy_drive", rows)
        self.assertIn("pressure_loss", rows)
        self.assertIn("coupled_root", rows)
        self.assertIn("integral_loop rho", rows["buoyancy_drive"]["equation_text"])
        self.assertIn("sum_i", rows["pressure_loss"]["equation_text"])
        self.assertIn("T(s, mdot)", rows["coupled_root"]["equation_text"])

    def test_segment_rows_cover_required_regions_and_guardrails(self) -> None:
        rows = mod.segment_rows()
        by_region = {row["loop_region"]: row for row in rows}
        required = {
            "heater",
            "cooler_HX",
            "downcomer",
            "upcomer",
            "test_section",
            "junction_stub_connector",
            "lower_upper_legs",
        }

        self.assertEqual(set(by_region), required)
        self.assertIn("Q_test_section_loss_model", by_region["test_section"]["admission_model_forms"])
        self.assertIn("hybrid_throughflow_pipe_plus_recirculation_cell", by_region["upcomer"]["pressure_loss_slots"])
        self.assertIn("validation TP/TW temperatures", by_region["test_section"]["runtime_forbidden_inputs"])
        self.assertIn("imposed CFD cooler duty", by_region["cooler_HX"]["runtime_forbidden_inputs"])

    def test_runtime_audit_forbids_leakage_and_global_multiplier(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("realized CFD wallHeatFlux", forbidden)
        self.assertIn("imposed CFD cooler duty", forbidden)
        self.assertIn("validation TP/TW temperatures", forbidden)
        self.assertIn("hidden global friction or heat-loss multiplier", forbidden)
        self.assertIn("true Nu/f_D/K fits from recirculating rows", forbidden)

    def test_downstream_gates_start_pressure_thermal_not_coupled(self) -> None:
        rows = {row["downstream_task"]: row for row in mod.downstream_gate_rows()}

        self.assertEqual(rows["TODO-PREDICT-SEGMENT-PRESSURE-MODELS"]["may_start_after_this_package"], "yes")
        self.assertEqual(rows["TODO-PREDICT-SEGMENT-THERMAL-MODELS"]["may_start_after_this_package"], "yes")
        self.assertEqual(rows["TODO-PREDICT-COUPLED-SEGMENT-M3TS-SCORECARD"]["may_start_after_this_package"], "no")

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
                self.assertEqual(summary["runtime_forbidden_pass_rows"], 6)
                self.assertFalse(summary["coupled_m3ts_may_start"])
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "segment_equation_contract.csv").exists())
                self.assertTrue((out / "runtime_input_contract.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "segment_equation_contract.csv").open(newline="") as f:
                    segment_rows = list(csv.DictReader(f))
                self.assertEqual(len(segment_rows), 7)
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
