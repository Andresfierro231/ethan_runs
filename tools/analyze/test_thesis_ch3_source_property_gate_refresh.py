import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_thesis_ch3_source_property_gate_refresh as builder


class ThesisCh3SourcePropertyGateRefreshTest(unittest.TestCase):
    def build_tmp(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        with mock.patch.object(builder, "OUT", tmp):
            summary = builder.build()
        self.summary = summary
        return tmp

    @staticmethod
    def rows(path: Path) -> list[dict[str, str]]:
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))

    def test_warning_rows_are_label_refreshed_but_not_released(self) -> None:
        out = self.build_tmp()
        rows = self.rows(out / "ch3_source_property_gate_resolution.csv")
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["labels_complete_after_refresh"] for row in rows}, {"true"})
        self.assertEqual({row["release_ready_after_refresh"] for row in rows}, {"false"})
        self.assertEqual({row["final_fit_allowed_after_refresh"] for row in rows}, {"false"})
        self.assertEqual({row["final_model_selection_allowed_after_refresh"] for row in rows}, {"false"})
        self.assertEqual({row["writer_use_now"] for row in rows}, {"database_provenance_and_diagnostic_context_only"})

    def test_expected_nominal_cases_are_resolved(self) -> None:
        out = self.build_tmp()
        rows = self.rows(out / "ch3_source_property_gate_resolution.csv")
        self.assertEqual(
            {row["case_key"] for row in rows},
            {"salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"},
        )
        by_case = {row["case_key"]: row for row in rows}
        self.assertIn("Salt1", by_case["salt1_nominal"]["next_unblock_task"])
        self.assertIn("strict-pass", by_case["salt2_jin_nominal"]["next_unblock_task"])

    def test_summary_and_claims_preserve_no_admission_guardrails(self) -> None:
        out = self.build_tmp()
        self.assertEqual(self.summary["decision"], "ch3_source_property_warning_resolved_by_demote_no_release")
        self.assertEqual(self.summary["warning_rows"], 4)
        self.assertEqual(self.summary["labels_complete_after_refresh_rows"], 4)
        self.assertEqual(self.summary["release_ready_rows"], 0)
        self.assertFalse(self.summary["source_property_release"])
        self.assertFalse(self.summary["candidate_freeze"])
        self.assertFalse(self.summary["protected_scoring"])
        claims = self.rows(out / "allowed_forbidden_claim_table.csv")
        forbidden = [row for row in claims if row["claim_type"] == "forbidden"]
        self.assertEqual(len(forbidden), 1)
        self.assertIn("candidate admission", forbidden[0]["claim"])


if __name__ == "__main__":
    unittest.main()
