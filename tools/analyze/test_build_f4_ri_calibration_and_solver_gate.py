#!/usr/bin/env python3
"""Admission-invariant tests for the AGENT-191 F4/Ri gate package."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products" / "2026-07-07_f4_ri_calibration_and_solver_gate"


def _rows(name: str) -> list[dict[str, str]]:
    with (OUT_DIR / name).open(newline="") as fh:
        return list(csv.DictReader(fh))


class TestF4RiCalibrationGate(unittest.TestCase):
    def test_calibration_rows_are_mainline_salt_2_3_4_only(self) -> None:
        rows = _rows("f4_ri_calibration_table.csv")
        self.assertEqual(len(rows), 18)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["closure_fit_admissible"] == "True" for row in rows))
        self.assertTrue(all(row["needs_special_gate_scrutiny"] == "False" for row in rows))

    def test_flagged_rows_are_not_fit_admissible(self) -> None:
        flagged = [
            row for row in _rows("admitted_evidence_freeze.csv")
            if row.get("needs_special_gate_scrutiny") == "True"
        ]
        self.assertGreaterEqual(len(flagged), 5)
        self.assertTrue(all(row["closure_fit_admissible"] == "False" for row in flagged))

    def test_upcomer_is_not_collapsed_for_fit(self) -> None:
        groups = {row["fit_group"] for row in _rows("f4_ri_calibration_table.csv")}
        self.assertIn("upcomer_lower", groups)
        self.assertIn("test_section", groups)
        self.assertIn("upcomer_upper", groups)
        self.assertNotIn("upcomer", groups)


if __name__ == "__main__":
    unittest.main()
