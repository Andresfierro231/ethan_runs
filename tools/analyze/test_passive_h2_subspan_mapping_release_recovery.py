from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_passive_h2_subspan_mapping_release_recovery as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2SubspanMappingReleaseRecoveryTests(unittest.TestCase):
    def test_salt2_has_support_but_no_release(self) -> None:
        gate = builder.salt2_release_rows()
        self.assertEqual(len(gate), 5)
        self.assertTrue(all(row["setup_subspan_support_ready"] == "true" for row in gate))
        self.assertTrue(any(row["area_match_support"] == "true" for row in gate))
        self.assertTrue(all(row["release_ready_now"] == "false" for row in gate))
        self.assertTrue(all(row["release_decision"] == "fail_closed_support_only" for row in gate))

    def test_all_case_setup_support_recovered(self) -> None:
        coverage = builder.all_case_coverage_rows()
        self.assertEqual(len(coverage), 15)
        self.assertTrue(all(row["setup_subspan_support_ready"] == "true" for row in coverage))
        self.assertTrue(all(row["release_grade_subspan_ready_now"] == "false" for row in coverage))

    def test_build_summary_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "passive_h2_subspan_mapping_support_recovered_release_fail_closed")
            self.assertEqual(summary["salt2_setup_subspan_support_ready_rows"], 5)
            self.assertEqual(summary["salt2_release_ready_rows"], 0)
            self.assertFalse(summary["source_property_release"])
            self.assertFalse(summary["candidate_freeze"])
            gate = rows(out / "salt2_subspan_release_gate.csv")
            self.assertEqual(len(gate), 5)


if __name__ == "__main__":
    unittest.main()
