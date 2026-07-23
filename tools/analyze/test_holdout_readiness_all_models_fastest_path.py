from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_holdout_readiness_all_models_fastest_path as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class HoldoutReadinessAllModelsFastestPathTests(unittest.TestCase):
    def test_case_family_readiness_preserves_blind_and_support_roles(self) -> None:
        rows = {row["case_key"]: row for row in builder.case_family_rows()}
        self.assertEqual(rows["salt2_lo5q"]["canonical_role"], "current_blind_holdout_testing")
        self.assertEqual(rows["salt2_hi5q"]["target_evidence_status"], "holdout_target_repaired_and_ready")
        self.assertFalse(rows["salt2_lo5q"]["score_ready_now"])
        self.assertFalse(rows["salt2_lo5q"]["fit_allowed"])
        self.assertFalse(rows["val_salt2"]["runtime_input_allowed"])
        self.assertEqual(rows["val_salt2"]["canonical_role"], "external_test")
        self.assertEqual(rows["salt1_lo10q"]["holdout_use_after_freeze"], "no_without_predeclared_split_policy_change")
        self.assertEqual(rows["salt4_hi5q"]["holdout_use_after_freeze"], "conditional_after_freeze_and_holdout_family_use_policy")

    def test_future_pm10_rows_are_future_only_with_no_score_now(self) -> None:
        rows = {row["case_key"]: row for row in builder.case_family_rows()}
        for case_key in ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"):
            row = rows[case_key]
            self.assertEqual(row["canonical_role"], "future_holdout_candidate")
            self.assertEqual(row["target_evidence_status"], "terminal_evidence_admitted_future_holdout_only")
            self.assertFalse(row["score_ready_now"])
            self.assertIn("total_Q", row["blockers"])

    def test_all_model_gate_matrix_has_no_holdout_score_ready_lane(self) -> None:
        rows = {row["model_lane"]: row for row in builder.all_model_gate_rows()}
        self.assertIn("PASSIVE-H2-CAND001", rows)
        self.assertIn("D4 physical successor", rows)
        self.assertIn("S13/upcomer exchange", rows)
        self.assertTrue(all(row["can_score_holdout_now"] is False for row in rows.values()))
        self.assertFalse(rows["PASSIVE-H2-CAND001"]["source_property_release_ready"])
        self.assertIn("strict source envelope", rows["PASSIVE-H2-CAND001"]["blocks"])
        self.assertIn("source-bounded", rows["D4 physical successor"]["blocks"])

    def test_sequence_orders_split_candidate_freeze_prediction_score(self) -> None:
        phases = [row["phase"] for row in builder.fastest_sequence_rows()]
        self.assertEqual(
            phases[:5],
            [
                "Freeze split and scoring law",
                "Candidate admission gate",
                "Train-only UQ and immutable freeze",
                "Blind prediction generation",
                "Score once",
            ],
        )

    def test_build_outputs_package_without_score_or_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["current_score_ready_case_rows"], 0)
            self.assertEqual(summary["model_lanes_score_ready_now"], 0)
            self.assertEqual(summary["current_first_targets_after_freeze_count"], 3)
            self.assertFalse(summary["candidate_freeze"])
            self.assertFalse(summary["source_property_or_qwall_release"])
            for filename in [
                "case_family_holdout_readiness.csv",
                "all_model_holdout_gate_matrix.csv",
                "fastest_safe_holdout_sequence.csv",
                "claim_boundaries.csv",
                "next_task_queue.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / filename).exists(), filename)
            case_rows = read_rows(out / "case_family_holdout_readiness.csv")
            self.assertTrue(all(row["score_ready_now"] == "False" for row in case_rows))


if __name__ == "__main__":
    unittest.main()
