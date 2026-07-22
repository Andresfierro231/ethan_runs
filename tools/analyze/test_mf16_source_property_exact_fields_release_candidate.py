#!/usr/bin/env python3
"""Checks for MF16 source/property exact-fields release candidate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_mf16_source_property_exact_fields_release_candidate.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate"


class TestMF16SourcePropertyExactFields(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT_DIR / name).open(newline="") as f:
            return list(csv.DictReader(f))

    def test_summary_fails_closed(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text())
        self.assertEqual(summary["decision"], "source_property_exact_fields_release_candidate_fail_closed_no_release")
        self.assertEqual(summary["nominal_rows"], 4)
        self.assertEqual(summary["labels_complete_rows"], 4)
        self.assertEqual(summary["nominal_release_ready_rows"], 0)
        self.assertEqual(summary["exact_field_release_ready_rows"], 0)
        self.assertEqual(summary["protected_rows_released"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["s11_s15_s6_opened"])

    def test_exact_fields_include_required_blockers(self) -> None:
        rows = self.read_csv("exact_field_release_matrix.csv")
        fields = {row["exact_field"] for row in rows}
        self.assertIn("q_setup_sign_and_magnitude", fields)
        self.assertIn("cp_property_basis", fields)
        self.assertIn("segment_source_placement_kernel", fields)
        self.assertIn("wall_profile_source_property_conservation", fields)
        self.assertIn("runtime_temperature_and_wall_state_use", fields)
        self.assertTrue(all(row["release_ready"] == "False" for row in rows))

    def test_row_level_matrix_preserves_no_fit_boundary(self) -> None:
        rows = self.read_csv("row_level_release_candidate_matrix.csv")
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["release_ready"] == "False" for row in rows))
        self.assertTrue(all(row["final_fit_allowed"] == "no" for row in rows))
        self.assertTrue(all(row["final_model_selection_allowed"] == "no" for row in rows))

    def test_release_gate_does_not_open_freeze(self) -> None:
        rows = self.read_csv("release_candidate_gate.csv")
        self.assertTrue(all(row["release_allowed"] == "False" for row in rows))
        self.assertTrue(all(row["candidate_freeze_allowed"] == "False" for row in rows))
        self.assertIn("nominal_train_source_envelope_strict_pass", {row["gate"] for row in rows})

    def test_next_queue_prioritizes_strict_source_envelope(self) -> None:
        rows = self.read_csv("next_study_queue.csv")
        self.assertEqual(rows[0]["next_study"], "strict_row_specific_source_envelope_recovery")
        self.assertEqual(rows[0]["status_after_mf16"], "next_serial")


if __name__ == "__main__":
    unittest.main()
