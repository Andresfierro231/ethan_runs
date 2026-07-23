from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_passive_h2_source_property_gate_rerun_with_salt34_smoke as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2SourcePropertyGateRerunWithSalt34SmokeTests(unittest.TestCase):
    def test_three_case_runtime_evidence_is_complete_but_diagnostic_only(self) -> None:
        runtime_rows = builder.three_case_runtime_evidence_rows()
        self.assertEqual({row["case_id"] for row in runtime_rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual(sum(row["runtime_completed"] == "true" for row in runtime_rows), 3)
        self.assertEqual(sum(row["accepted_roots"] == "true" for row in runtime_rows), 3)
        self.assertEqual(sum(row["radiation_on_nonzero"] == "true" for row in runtime_rows), 3)
        self.assertEqual({row["source_property_release"] for row in runtime_rows}, {"false"})
        self.assertEqual({row["protected_scoring"] for row in runtime_rows}, {"false"})
        self.assertEqual({row["candidate_freeze"] for row in runtime_rows}, {"false"})

    def test_release_gate_keeps_source_property_and_freeze_closed(self) -> None:
        gates = builder.source_property_release_gate_rows()
        by_gate = {row["gate"]: row for row in gates}
        self.assertEqual(by_gate["three_case_runtime_smoke"]["status"], "pass_diagnostic")
        self.assertEqual(by_gate["three_case_runtime_smoke"]["count_or_value"], "completed=3/3; nonzero=3/3")
        self.assertEqual(by_gate["release_grade_subspan"]["status"], "fail_closed")
        self.assertEqual(by_gate["release_grade_subspan"]["count_or_value"], "0/5")
        self.assertEqual(by_gate["row_specific_source_property"]["count_or_value"], "0")
        self.assertEqual(by_gate["same_qoi_runtime_uq"]["status"], "fail_closed")
        self.assertEqual(by_gate["split_safe_freeze"]["status"], "fail_closed")
        self.assertEqual(by_gate["final_score"]["count_or_value"], "0")
        self.assertEqual({row["release_ready"] for row in gates}, {"false"})

    def test_claim_boundaries_do_not_admit_score_or_source_release(self) -> None:
        claims = {row["claim"]: row for row in builder.claim_boundary_rows()}
        self.assertEqual(claims["PASSIVE-H2 executes on Salt2/Salt3/Salt4"]["allowed"], "true")
        self.assertEqual(claims["Salt3/Salt4 prove validation/holdout score improvement"]["allowed"], "false")
        self.assertEqual(claims["source/property release is open"]["allowed"], "false")
        self.assertEqual(claims["candidate is frozen for final model"]["allowed"], "false")

    def test_build_summary_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "passive_h2_with_salt34_smoke_runtime_evidence_complete_release_fail_closed",
            )
            self.assertTrue(summary["three_case_runtime_evidence_complete"])
            self.assertEqual(summary["runtime_completed_case_rows"], 3)
            self.assertEqual(summary["runtime_nonzero_case_rows"], 3)
            self.assertEqual(summary["source_property_release_ready_rows"], 0)
            self.assertEqual(summary["release_ready_qoi_labels"], 0)
            self.assertEqual(summary["salt2_release_ready_rows"], 0)
            self.assertEqual(summary["freeze_ready_candidates"], 0)
            self.assertEqual(summary["final_score_values"], 0)
            self.assertFalse(summary["source_property_release"])
            self.assertFalse(summary["candidate_freeze"])
            self.assertEqual(len(rows(out / "three_case_runtime_evidence.csv")), 3)
            self.assertEqual(len(rows(out / "source_property_release_gate.csv")), 6)


if __name__ == "__main__":
    unittest.main()
