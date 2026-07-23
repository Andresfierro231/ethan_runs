from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_passive_h2_candidate_source_property_gate_rerun as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2CandidateSourcePropertyGateRerunTests(unittest.TestCase):
    def test_gate_rows_preserve_support_but_block_release(self) -> None:
        gates = builder.gate_rows()
        by_gate = {row["gate"]: row for row in gates}
        self.assertEqual(by_gate["runtime_implementation"]["status"], "pass_support")
        self.assertEqual(by_gate["setup_subspan_support"]["status"], "pass_support")
        self.assertEqual(by_gate["salt2_same_qoi_setup_uq"]["status"], "pass_diagnostic")
        self.assertEqual(by_gate["release_grade_subspan"]["status"], "fail_closed")
        self.assertIn("salt34_runtime_rows=0", by_gate["protected_split_or_score"]["count_or_value"])
        self.assertEqual(by_gate["source_property_release"]["count_or_value"], "0")
        self.assertTrue(all(row["release_ready"] == "false" for row in gates))

    def test_decision_fail_closed(self) -> None:
        decision = builder.decision_rows()[0]
        self.assertEqual(
            decision["decision"],
            "passive_h2_candidate_source_property_gate_rerun_fail_closed_support_progress_no_release_no_freeze",
        )
        self.assertEqual(decision["source_property_release_allowed"], "false")
        self.assertEqual(decision["final_score_values"], "0")

    def test_build_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertTrue(summary["support_progress"])
            self.assertEqual(summary["salt2_setup_subspan_support_ready_rows"], 5)
            self.assertEqual(summary["diagnostic_ready_qoi_labels"], 6)
            self.assertEqual(summary["salt34_runtime_smoke_rows"], 0)
            self.assertEqual(summary["salt34_smoke_blocked_rows"], 2)
            self.assertEqual(summary["source_property_release_ready_rows"], 0)
            self.assertFalse(summary["candidate_freeze"])
            self.assertEqual(summary["final_score_values"], 0)
            self.assertEqual(len(rows(out / "candidate_gate_rerun_matrix.csv")), 10)


if __name__ == "__main__":
    unittest.main()
