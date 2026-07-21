#!/usr/bin/env python3
"""Tests for the F6 non-recirculating pressure-anchor plan."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_f6_nonrecirculating_pressure_anchor_plan as mod


class F6NonrecirculatingPressureAnchorPlanTest(unittest.TestCase):
    def test_current_pm5_rows_are_recirculation_diagnostics(self) -> None:
        rows = mod.build_pressure_anchor_plan()
        current = [row for row in rows if row["evidence_family"] == "PM5_current"]

        self.assertEqual(len(current), 12)
        self.assertTrue(all(row["ordinary_f6_legitimate_now"] == "no" for row in current))
        self.assertTrue(all(row["recirculation_diagnostic_now"] == "yes" for row in current))
        self.assertTrue(all(row["ordinary_anchor_class"] == "current_recirculation_diagnostic" for row in current))
        self.assertTrue(any(float(row["RAF"]) > 0.01 for row in current))
        self.assertTrue(any(float(row["RMF"]) > 0.01 for row in current))

    def test_pending_pm10_and_high_heat_rows_remain_candidate_only(self) -> None:
        rows = mod.build_pressure_anchor_plan()
        pending = [row for row in rows if row["ordinary_anchor_class"] == "pending_ordinary_anchor_candidate"]

        self.assertGreaterEqual(len(pending), 8)
        self.assertTrue(all(row["ordinary_f6_legitimate_now"] == "no" for row in pending))
        self.assertTrue(all("terminal" in row["required_before_ordinary_f6"] for row in pending))
        self.assertTrue(all("RAF/RMF" in row["required_before_ordinary_f6"] for row in pending))

    def test_named_pressure_slots_separate_f6_from_component_k(self) -> None:
        rows = mod.build_named_pressure_anchor_slots()
        roles = {row["f6_anchor_role"] for row in rows}

        self.assertIn("ordinary_f6_pressure_slot_candidate", roles)
        self.assertIn("not_ordinary_f6_component_k_lane", roles)
        self.assertIn("recirculation_diagnostic_not_anchor", roles)
        self.assertTrue(all(row["ordinary_f6_legitimate_now"] == "no" for row in rows))

    def test_gate_contract_forbids_fit_without_low_reverse_and_uq(self) -> None:
        text = json.dumps(mod.build_ordinary_anchor_gate_contract())

        self.assertIn("RAF < 0.01", text)
        self.assertIn("RMF < 0.01", text)
        self.assertIn("same-window", text)
        self.assertIn("mesh/time", text)
        self.assertIn("single-stream f_D/F6 fitting", text)

    def test_runtime_audit_has_no_fit_and_no_agent511_collision(self) -> None:
        rows = mod.build_runtime_audit()
        checks = {row["check"]: row for row in rows}

        self.assertEqual(checks["no_fitting"]["status"], "pass")
        self.assertEqual(checks["no_AGENT_511_collision"]["status"], "pass")
        self.assertTrue(all(row["status"] == "pass" for row in rows))

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

                self.assertEqual(summary["pm5_current_rows"], 12)
                self.assertEqual(summary["current_ordinary_anchor_rows"], 0)
                self.assertEqual(summary["current_recirculation_diagnostic_rows"], 12)
                self.assertGreaterEqual(summary["pending_anchor_candidate_rows"], 8)
                self.assertFalse(summary["fitting_performed"])
                self.assertFalse(summary["scheduler_action"])
                for name in [
                    "f6_pressure_anchor_plan.csv",
                    "named_pressure_anchor_slots.csv",
                    "ordinary_anchor_gate_contract.csv",
                    "next_action_plan.csv",
                    "runtime_request_audit.csv",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]:
                    self.assertTrue((out / name).exists(), name)
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "f6_pressure_anchor_plan.csv").open(newline="") as f:
                    rows = list(csv.DictReader(f))
                self.assertTrue(all(row["ordinary_f6_legitimate_now"] == "no" for row in rows))

                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertEqual(manifest["task"], mod.TASK)
                self.assertFalse(manifest["fitting_performed"])
                self.assertFalse(manifest["external_fluid_edit"])


if __name__ == "__main__":
    unittest.main()
