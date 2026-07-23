from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_holdout_split_freeze_case_family_policy as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class HoldoutSplitFreezeCaseFamilyPolicyTests(unittest.TestCase):
    def test_case_family_policy_locks_holdout_roles(self) -> None:
        rows = {row["case_key"]: row for row in builder.case_family_policy_rows()}
        self.assertEqual(rows["salt2_lo5q"]["frozen_split_role"], "primary_blind_holdout")
        self.assertEqual(rows["salt2_hi5q"]["score_allowed_after_model_freeze"], "primary_holdout_score_only")
        self.assertEqual(rows["val_salt2"]["frozen_split_role"], "external_test")
        self.assertEqual(rows["salt1_lo10q"]["score_allowed_after_model_freeze"], "no_without_new_predeclared_split_policy")
        self.assertFalse(rows["salt1_lo10q"]["fit_allowed_by_split_law"])
        self.assertEqual(rows["salt4_lo5q"]["frozen_split_role"], "conditional_postfreeze_holdout_family_sensitivity")
        self.assertEqual(rows["salt3_q_insulation_matrix"]["frozen_split_role"], "future_new_cfd_holdout_candidate")

    def test_no_case_is_score_or_fit_ready_now(self) -> None:
        rows = builder.case_family_policy_rows()
        self.assertTrue(all(row["score_allowed_now"] is False for row in rows))
        self.assertTrue(all(row["fit_or_selection_allowed_now"] is False for row in rows))
        self.assertTrue(all(row["runtime_input_allowed"] is False for row in rows))

    def test_score_order_starts_with_salt2_pm5_then_external(self) -> None:
        rows = builder.score_order_rows()
        self.assertEqual(rows[1]["score_block"], "primary_blind_holdout")
        self.assertEqual(rows[1]["case_keys"], "salt2_lo5q;salt2_hi5q")
        self.assertEqual(rows[2]["score_block"], "external_test")
        self.assertFalse(rows[2]["can_select_or_refit_after_viewing"])

    def test_model_lanes_cannot_consume_protected_rows_before_freeze(self) -> None:
        rows = builder.model_lane_consumption_rows()
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all(row["may_use_salt2_pm5_before_freeze"] is False for row in rows))
        self.assertTrue(all(row["may_use_val_salt2_before_freeze"] is False for row in rows))
        self.assertTrue(all(str(row["can_score_holdout_now"]) == "False" for row in rows))

    def test_build_outputs_policy_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "split_freeze_policy_locked_no_scoring_no_freeze")
            self.assertEqual(summary["score_allowed_now_rows"], 0)
            self.assertEqual(summary["fit_or_selection_allowed_now_rows"], 0)
            self.assertFalse(summary["salt1_pm10_holdout_allowed"])
            for filename in [
                "frozen_case_family_policy.csv",
                "score_release_law.csv",
                "holdout_score_order.csv",
                "model_lane_consumption_contract.csv",
                "blocker_unblock_ledger.csv",
                "publication_claim_boundaries.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / filename).exists(), filename)
            rows = read_rows(out / "frozen_case_family_policy.csv")
            self.assertTrue(all(row["score_allowed_now"] == "False" for row in rows))


if __name__ == "__main__":
    unittest.main()
