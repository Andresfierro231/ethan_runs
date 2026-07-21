#!/usr/bin/env python3
"""Tests for the two-tap corner_lower_right admission repair package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_two_tap_corner_lower_right_admission_repair as mod


class TwoTapCornerLowerRightAdmissionRepairTest(unittest.TestCase):
    def test_endpoint_reverse_flow_gate_fails_current_rows(self) -> None:
        rows = mod.build_endpoint_reverse_flow_gate()

        self.assertEqual({row["case_id"] for row in rows}, set(mod.CASE_ORDER))
        self.assertTrue(all(row["feature"] == "corner_lower_right" for row in rows))
        self.assertTrue(all(row["reverse_flow_gate"] == "fail_material_reverse_flow" for row in rows))
        self.assertTrue(all(float(row["aggregate_reverse_area_fraction"]) > 0.7 for row in rows))
        self.assertTrue(all(float(row["aggregate_reverse_mass_fraction"]) > 0.49 for row in rows))
        self.assertTrue(all(row["ordinary_component_k_candidate"] == "false" for row in rows))
        self.assertTrue(all(row["component_k_admitted"] == "false" for row in rows))

    def test_component_isolation_stays_apparent_cluster_only(self) -> None:
        rows = mod.build_component_isolation_ledger()

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["selected_component_isolation_label"] == "apparent_cluster_only" for row in rows))
        self.assertTrue(
            all(row["component_isolation_gate"] == "fail_no_admissible_straight_reference_for_ordinary_K" for row in rows)
        )
        self.assertTrue(all(row["component_k_admitted"] == "false" for row in rows))
        self.assertTrue(all(row["f6_fit_performed"] == "false" for row in rows))

    def test_same_qoi_uq_family_is_missing_no_gci(self) -> None:
        rows = mod.build_same_qoi_uq_family()

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["same_qoi_uncertainty_gate"] == "fail_missing_same_qoi_UQ" for row in rows))
        self.assertTrue(all(row["decision"] == "missing_no_GCI_diagnostic_only" for row in rows))
        self.assertTrue(all(row["component_k_admitted"] == "false" for row in rows))
        self.assertTrue(all(row["f6_fit_performed"] == "false" for row in rows))

    def test_split_decision_blocks_component_k_and_f6(self) -> None:
        endpoint = mod.build_endpoint_reverse_flow_gate()
        isolation = mod.build_component_isolation_ledger()
        uq = mod.build_same_qoi_uq_family()
        rows = mod.build_split_decision(endpoint, isolation, uq)

        self.assertEqual(len(rows), 3)
        self.assertTrue(
            all(row["admission_decision"] == "diagnostic_only_apparent_cluster_recirculation_blocked_missing_UQ" for row in rows)
        )
        self.assertTrue(all(row["selected_label"] == "apparent_cluster_only" for row in rows))
        self.assertTrue(all(row["split_use"] == "diagnostic_only_not_fit_or_model_selection" for row in rows))
        self.assertTrue(all(row["component_k_admitted"] == "false" for row in rows))
        self.assertTrue(all(row["f6_fit_performed"] == "false" for row in rows))
        for row in rows:
            self.assertIn("endpoint_reverse_flow_gate", row["failed_gates"])
            self.assertIn("component_isolation_gate", row["failed_gates"])
            self.assertIn("same_qoi_uncertainty_gate", row["failed_gates"])

    def test_main_writes_requested_four_tables(self) -> None:
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

            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["reverse_flow_pass_rows"], 0)
            self.assertEqual(summary["same_qoi_uq_pass_rows"], 0)
            self.assertEqual(summary["component_k_admitted_rows"], 0)
            self.assertFalse(summary["f6_fit_performed"])
            for filename in (
                "endpoint_reverse_flow_gate.csv",
                "component_isolation_ledger.csv",
                "same_qoi_uq_family.csv",
                "split_decision.csv",
            ):
                self.assertTrue((out / filename).exists())
                with (out / filename).open(newline="") as handle:
                    self.assertEqual(len(list(csv.DictReader(handle))), 3)
            with import_manifest.open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
