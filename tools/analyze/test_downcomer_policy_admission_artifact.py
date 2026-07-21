#!/usr/bin/env python3
"""Tests for AGENT-469 downcomer policy/admission artifact."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_downcomer_policy_admission_artifact as builder  # noqa: E402


class DowncomerPolicyAdmissionArtifactTests(unittest.TestCase):
    def test_current_evidence_rejects_downcomer_internal_nu_fit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)
            self.assertEqual(summary["decision"], "not_admitted_downcomer_policy_failed")
            self.assertEqual(summary["ordinary_nu_fit_admitted"], 0)
            self.assertIn("fail", summary["sign_gate_counts"])
            self.assertIn("fail", summary["interface_recirc_gate_counts"])
            self.assertIn("fail", summary["gci_gate_counts"])

    def test_sign_enthalpy_rows_fail_on_opposed_direction_and_large_residual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)
            with (out / "downcomer_sign_enthalpy_gate.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertGreaterEqual(len(rows), 3)
            self.assertTrue(all(row["gate"] == "fail" for row in rows))
            self.assertTrue(any(row["direction_status"] == "opposed_direction" for row in rows))

    def test_core_station_can_pass_while_interface_recirculation_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)
            with (out / "downcomer_low_recirculation_gate.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertTrue(all(row["core_station_gate"] == "pass" for row in rows))
            self.assertTrue(all(row["interface_recirc_gate"] == "fail" for row in rows))
            self.assertTrue(any("interface_invalid" in row["interpretation"] for row in rows))

    def test_same_qoi_gci_gate_has_no_publication_ready_thermal_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)
            with (out / "downcomer_same_qoi_gci_gate.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            thermal = [row for row in rows if row["quantity"] in {"Nu", "HTC", "UA_prime", "thermal_segment_closure"}]
            self.assertTrue(thermal)
            self.assertTrue(all(row["gate"] == "fail" for row in thermal))


if __name__ == "__main__":
    unittest.main()
