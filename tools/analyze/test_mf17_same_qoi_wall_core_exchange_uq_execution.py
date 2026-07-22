#!/usr/bin/env python3
"""Checks for MF17 same-QOI wall/core exchange UQ execution."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_mf17_same_qoi_wall_core_exchange_uq_execution.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf17_same_qoi_wall_core_exchange_uq_execution"


class TestMF17SameQOIWallCoreExchangeUQ(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT_DIR / name).open(newline="") as f:
            return list(csv.DictReader(f))

    def test_summary_executes_temporal_uq_without_admission(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text())
        self.assertEqual(summary["decision"], "same_qoi_wall_core_exchange_temporal_uq_executed_no_admission")
        self.assertEqual(summary["qoi_label_count"], 4)
        self.assertEqual(summary["case_temporal_uq_rows"], 12)
        self.assertEqual(summary["same_qoi_temporal_uq_executed_qois"], 4)
        self.assertTrue(summary["mesh_gci_gate_input_ready"])
        self.assertFalse(summary["mesh_gci_uq_executed"])
        self.assertFalse(summary["production_harvest_allowed"])
        self.assertFalse(summary["admission_allowed"])
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["coefficient_admission"])

    def test_all_requested_qois_are_represented(self) -> None:
        rows = self.read_csv("qoi_temporal_uq_execution_summary.csv")
        self.assertEqual(
            {row["qoi_label"] for row in rows},
            {
                "Q_wall_W",
                "mdot_exchange_positive_outward_proxy_kg_s",
                "tau_recirc_proxy_s",
                "wall_core_bulk_temperature_contrast_K",
            },
        )
        self.assertTrue(all(row["same_qoi_temporal_uq_status"] == "executed" for row in rows))
        self.assertTrue(all(row["production_use_allowed_now"] == "False" for row in rows))
        self.assertTrue(all(row["admission_allowed_now"] == "False" for row in rows))

    def test_case_triplets_are_finite_and_executed(self) -> None:
        rows = self.read_csv("case_triplet_temporal_uq_rows.csv")
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(row["finite_triplet"] == "true" for row in rows))
        self.assertTrue(all(row["neighbor_window_uq_executed"] == "true" for row in rows))

    def test_mechanisms_do_not_admit_coefficients(self) -> None:
        rows = self.read_csv("d3_mechanism_uq_impact_table.csv")
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["same_qoi_temporal_uq_executed"] == "True" for row in rows))
        self.assertTrue(all(row["production_or_admission_allowed"] == "False" for row in rows))

    def test_production_boundary_blocks_release(self) -> None:
        rows = self.read_csv("production_admission_boundary.csv")
        self.assertTrue(all(row["release_allowed"] == "False" for row in rows))
        self.assertIn("mesh_gci_uq", {row["gate"] for row in rows})
        self.assertIn("source_property_release", {row["gate"] for row in rows})


if __name__ == "__main__":
    unittest.main()
