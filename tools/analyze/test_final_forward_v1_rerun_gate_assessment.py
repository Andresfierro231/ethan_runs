#!/usr/bin/env python3
"""Tests for final forward-v1 rerun gate assessment."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_final_forward_v1_rerun_gate_assessment as mod


class FinalForwardV1RerunGateAssessmentTest(unittest.TestCase):
    def test_gate_deltas_do_not_trigger_rerun(self) -> None:
        rows = mod.build_gate_delta_rows()

        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["rerun_triggered"] == "false" for row in rows))
        self.assertTrue(any(row["gate"] == "pressure_closure" and row["new_admitted_rows"] == 0 for row in rows))
        self.assertTrue(any(row["gate"] == "test_section_passive_loss" and row["new_admitted_rows"] == 0 for row in rows))
        self.assertTrue(any(row["gate"] == "upcomer_hybrid" and row["new_admitted_rows"] == 0 for row in rows))

    def test_decision_is_no_rerun(self) -> None:
        rows = mod.build_decision_rows(mod.build_gate_delta_rows())

        self.assertEqual(rows[0]["decision"], "do_not_rerun_boundary_or_coupled_scorecards_now")
        self.assertEqual(rows[0]["boundary_layer_rerun"], "false")
        self.assertEqual(rows[0]["coupled_m3ts_rerun"], "false")

    def test_runtime_audit_forbids_side_effects(self) -> None:
        rows = mod.runtime_audit_rows()

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertTrue(any(row["forbidden_input"] == "OpenFOAM/Fluid solve" for row in rows))
        self.assertTrue(any(row["forbidden_input"] == "scheduler action" for row in rows))

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
                self.assertEqual(summary["rerun_triggered_gates"], 0)
                self.assertFalse(summary["boundary_layer_rerun"])
                self.assertFalse(summary["coupled_m3ts_rerun"])
                self.assertEqual(summary["runtime_audit_pass_rows"], 3)
                self.assertTrue(summary["all_sources_present"])
                self.assertTrue((out / "rerun_decision.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "rerun_decision.csv").open(newline="") as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(rows[0]["decision"], "do_not_rerun_boundary_or_coupled_scorecards_now")
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["native_solver_outputs_mutated"])
                self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
