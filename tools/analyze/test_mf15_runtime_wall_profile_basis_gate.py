#!/usr/bin/env python3
"""Focused checks for MF15 runtime wall/profile basis gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_mf15_runtime_wall_profile_basis_gate.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf15_runtime_wall_profile_basis_gate"


class TestMF15RuntimeWallProfileBasisGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT_DIR / name).open(newline="") as f:
            return list(csv.DictReader(f))

    def test_summary_fails_closed(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text())
        self.assertEqual(summary["decision"], "runtime_wall_profile_basis_fail_closed_diagnostic_signal_only")
        self.assertEqual(summary["candidate_rows"], 3)
        self.assertEqual(summary["candidate_ready_rows"], 0)
        self.assertEqual(summary["wall_profile_correction_release_ready_rows"], 0)
        self.assertEqual(summary["same_qoi_triplet_ready_qois"], 4)
        self.assertFalse(summary["same_qoi_uq_executed"])
        self.assertFalse(summary["runtime_temperature_input_release"])
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["wall_profile_correction_release"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])

    def test_all_d3_candidate_families_are_represented(self) -> None:
        rows = self.read_csv("wall_profile_family_basis_gate.csv")
        self.assertEqual(
            {row["candidate_id"] for row in rows},
            {
                "D3-WALL-CORE-EXCHANGE-SHAPE",
                "D3-AXIAL-MIXING-SHAPE",
                "D3-SENSOR-PROJECTION-SHAPE",
            },
        )
        self.assertTrue(all(row["wall_profile_correction_release_ready"] == "False" for row in rows))
        self.assertTrue(any("source/property" in row["same_qoi_or_source_property_blockers"] for row in rows))

    def test_requirement_matrix_blocks_release(self) -> None:
        rows = self.read_csv("runtime_operator_requirement_matrix.csv")
        self.assertGreaterEqual(len(rows), 20)
        self.assertTrue(all(row["release_allowed"] == "False" for row in rows))
        statuses = {row["status"] for row in rows}
        self.assertIn("fail_closed", statuses)
        self.assertIn("triplet_ready_uq_not_executed", statuses)

    def test_case_metrics_are_read_only(self) -> None:
        rows = self.read_csv("wall_shape_case_metric_reuse_boundary.csv")
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["existing_metric_reused_read_only"] == "True" for row in rows))
        self.assertTrue(all(row["new_scoring_performed"] == "False" for row in rows))

    def test_next_queue_advances_to_source_property_release(self) -> None:
        rows = self.read_csv("next_study_queue.csv")
        self.assertEqual(rows[0]["next_study"], "source_property_label_release_candidate_after_exact_fields")
        self.assertEqual(rows[0]["current_status_after_mf15"], "next")


if __name__ == "__main__":
    unittest.main()
