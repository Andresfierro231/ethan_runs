#!/usr/bin/env python3
"""Focused checks for MF14 same-QOI TP projection UQ gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_mf14_same_qoi_tp_projection_uq_gate.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate"


class TestMF14SameQOITPProjectionUQGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT_DIR / name).open(newline="") as f:
            return list(csv.DictReader(f))

    def test_summary_fails_closed_without_runtime_temperature_release(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text())
        self.assertEqual(summary["decision"], "same_qoi_tp_projection_uq_fail_closed_no_runtime_temperature_release")
        self.assertEqual(summary["tp_rows"], 6)
        self.assertEqual(summary["same_qoi_label_rows"], 6)
        self.assertEqual(summary["quantitative_same_qoi_uq_ready_rows"], 0)
        self.assertEqual(summary["runtime_temperature_allowed_rows"], 0)
        self.assertEqual(summary["same_qoi_projection_release_ready_rows"], 0)
        self.assertFalse(summary["new_validation_holdout_external_scoring"])
        self.assertFalse(summary["runtime_temperature_input_release"])
        self.assertFalse(summary["bulk_to_tp_correction_release"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])

    def test_tp_rows_preserve_sensor_qoi_boundary(self) -> None:
        rows = self.read_csv("tp_same_qoi_projection_uq.csv")
        self.assertEqual({row["sensor"] for row in rows}, {"TP1", "TP2", "TP3", "TP4", "TP5", "TP6"})
        self.assertTrue(all(row["projection_operator"] == "bulk_fluid_projection" for row in rows))
        self.assertTrue(all(row["same_qoi_label_present"] == "True" for row in rows))
        self.assertTrue(all(row["same_qoi_projection_release_ready"] == "False" for row in rows))
        self.assertTrue(all("quantitative_same_qoi_projection_uq" in row["blocking_gap"] for row in rows))

    def test_release_gate_blocks_correction_release(self) -> None:
        rows = self.read_csv("projection_release_gate.csv")
        self.assertTrue(all(row["release_allowed"] == "False" for row in rows))
        gates = {row["gate"] for row in rows}
        self.assertIn("quantitative_same_qoi_uq_ready", gates)
        self.assertIn("runtime_temperature_release", gates)
        self.assertIn("bulk_to_tp_correction_release", gates)

    def test_d2_reuse_is_read_only_context(self) -> None:
        rows = self.read_csv("d2_reuse_boundary.csv")
        self.assertGreaterEqual(len(rows), 4)
        self.assertTrue(all(row["existing_metric_reused_read_only"] == "True" for row in rows))
        self.assertTrue(all(row["new_scoring_performed"] == "False" for row in rows))
        self.assertTrue(all(row["admission_allowed"] == "False" for row in rows))

    def test_next_queue_advances_to_wall_profile(self) -> None:
        rows = self.read_csv("next_study_queue.csv")
        self.assertEqual(rows[0]["next_study"], "runtime_wall_profile_basis_for_tp_projection")
        self.assertEqual(rows[0]["current_status_after_mf14"], "next")


if __name__ == "__main__":
    unittest.main()
