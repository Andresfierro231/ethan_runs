#!/usr/bin/env python3
"""Tests for AGENT-423 thermal row admission ledger."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_thermal_row_admission_ledger as build


class ThermalRowAdmissionLedgerTest(unittest.TestCase):
    def run_build(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "ledger"
        build.main(["--out", str(out)])
        return out

    def read_rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="") as f:
            return list(csv.DictReader(f))

    def test_expected_family_counts_and_outputs(self) -> None:
        out = self.run_build()
        summary = json.loads((out / "summary.json").read_text())
        self.assertEqual(summary["row_count"], 40)
        self.assertEqual(summary["family_counts"]["final_predictive_hx_closure"], 14)
        self.assertEqual(summary["family_counts"]["fitted_internal_nu"], 3)
        self.assertEqual(summary["family_counts"]["realized_wallheatflux_replay"], 12)
        self.assertEqual(summary["family_counts"]["imposed_cooler_duty"], 8)
        self.assertEqual(summary["family_counts"]["diagnostic_test_section_negative_source"], 3)
        for filename in build.FAMILY_FILES.values():
            self.assertTrue((out / filename).exists(), filename)

    def test_no_runtime_leakage_rows_are_predictive_admitted(self) -> None:
        out = self.run_build()
        rows = self.read_rows(out / "thermal_row_admission_ledger.csv")
        leakage_rows = [
            r
            for r in rows
            if r["row_family"] in {"imposed_cooler_duty", "realized_wallheatflux_replay"}
        ]
        self.assertTrue(leakage_rows)
        for row in leakage_rows:
            self.assertNotIn("predictive_candidate", row["admission_class"])
            self.assertNotIn("final", row["forward_v1_use"])

    def test_internal_nu_remains_zero_fit(self) -> None:
        out = self.run_build()
        rows = self.read_rows(out / "fitted_internal_nu_rows.csv")
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["admission_class"], "blocked_empty_fit_set")
            self.assertIn("current_fit_admissible_rows=0", row["key_metric_3"])
            self.assertIn("no_internal_nu_fit", row["forward_v1_use"])

    def test_negative_source_rows_are_diagnostic_only(self) -> None:
        out = self.run_build()
        rows = self.read_rows(out / "diagnostic_test_section_negative_source_rows.csv")
        self.assertEqual({r["model_form"] for r in rows}, {"negative_source_compatibility"})
        self.assertEqual({r["admission_class"] for r in rows}, {"diagnostic_boundary_form_screen"})
        self.assertEqual({r["case_id"] for r in rows}, {"salt_2", "salt_3", "salt_4"})


if __name__ == "__main__":
    unittest.main()
