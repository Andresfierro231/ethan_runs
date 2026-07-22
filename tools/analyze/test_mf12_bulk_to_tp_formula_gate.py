#!/usr/bin/env python3
"""Focused checks for MF12 bulk-to-TP formula gate outputs."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_mf12_bulk_to_tp_formula_gate.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate"


class TestMF12BulkToTPFormulaGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT_DIR / name).open(newline="") as f:
            return list(csv.DictReader(f))

    def test_summary_gate_is_fail_closed(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text())
        self.assertEqual(summary["decision"], "diagnostic_only_needs_source_basis")
        self.assertFalse(summary["ready_for_train_only_smoke"])
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["coefficient_admission"])
        self.assertFalse(summary["validation_holdout_external_scoring"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])

    def test_candidate_formulas_include_forbidden_empirical_fit(self) -> None:
        rows = self.read_csv("candidate_bulk_to_tp_formulas.csv")
        self.assertEqual(len(rows), 4)
        decisions = {row["decision"] for row in rows}
        self.assertIn("forbidden_as_empirical_projection_fit", decisions)
        self.assertIn("diagnostic_only_needs_source_basis", decisions)

    def test_release_matrix_blocks_admission(self) -> None:
        rows = self.read_csv("formula_release_gap_matrix.csv")
        self.assertGreaterEqual(len(rows), 5)
        self.assertTrue(all(row["release_allowed"] == "False" for row in rows))
        statuses = {row["status"] for row in rows}
        self.assertIn("fail_closed", statuses)

    def test_thesis_insert_preserves_claim_boundary(self) -> None:
        text = (OUT_DIR / "thesis_model_form_insert.md").read_text()
        self.assertIn("source-bounded projection term", text)
        self.assertIn("diagnostic-only", text)
        self.assertIn("does not release", text)


if __name__ == "__main__":
    unittest.main()
