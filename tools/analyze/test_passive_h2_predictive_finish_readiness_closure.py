import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_predictive_finish_readiness_closure"
SCRIPT = ROOT / "tools/analyze/build_passive_h2_predictive_finish_readiness_closure.py"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2PredictiveFinishReadinessClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_is_fail_closed_without_release(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(
            summary["decision"],
            "passive_h2_predictive_finish_fail_closed_current_candidate_no_freeze_reduced_path_requires_new_predeclared_candidate",
        )
        self.assertFalse(summary["full_five_family_freeze_allowed"])
        self.assertFalse(summary["reduced_four_family_freeze_as_current_candidate_allowed"])
        self.assertTrue(summary["reduced_four_family_future_candidate_allowed"])
        self.assertEqual(summary["source_property_release_rows"], 0)
        self.assertEqual(summary["freeze_allowed_rows"], 0)
        self.assertEqual(summary["final_score_values"], 0)
        self.assertFalse(summary["protected_or_final_scoring"])

    def test_salt1_coverage_records_missing_junction(self) -> None:
        coverage = rows("salt1_family_coverage_gap.csv")
        self.assertEqual(len(coverage), 5)
        by_family = {row["source_family"]: row for row in coverage}
        self.assertEqual(by_family["junction"]["operator_row_present"], "false")
        self.assertEqual(by_family["junction"]["setup_basis_status"], "missing_case_family_coverage")
        for family in ("cooling_branch", "downcomer", "lower_leg", "upcomer"):
            self.assertEqual(by_family[family]["operator_row_present"], "true")

    def test_full_and_reduced_readiness_both_fail_closed(self) -> None:
        matrix = {row["candidate_option"]: row for row in rows("predictive_finish_readiness_matrix.csv")}
        full = matrix["full_five_family_current_candidate"]
        reduced = matrix["reduced_four_family_no_junction_candidate"]
        self.assertEqual(full["predictive_freeze_allowed_now"], "false")
        self.assertIn("salt1_family_coverage", full["hard_fail_gates"])
        self.assertIn("strict_source_envelope", full["hard_fail_gates"])
        self.assertEqual(reduced["salt1_family_coverage_ready"], "true")
        self.assertEqual(reduced["changes_current_candidate_definition"], "true")
        self.assertEqual(reduced["predictive_freeze_allowed_now"], "false")
        self.assertIn("posthoc_candidate_definition_change", reduced["hard_fail_gates"])

    def test_gap_ledger_requires_source_envelope_and_release_uq(self) -> None:
        gaps = rows("source_envelope_uq_gap_ledger.csv")
        self.assertEqual(len(gaps), 5)
        self.assertTrue(all(row["strict_source_envelope_status"] == "not_admitted" for row in gaps))
        self.assertTrue(all(row["same_qoi_release_uq_status"] == "missing_release_grade" for row in gaps))
        self.assertTrue(all(row["source_property_release_status"] == "fail_closed" for row in gaps))

    def test_reduced_policy_requires_new_predeclared_candidate(self) -> None:
        policy = rows("reduced_family_freeze_policy.csv")
        joined = " ".join(row["reason"] + " " + row["allowed_next_action"] for row in policy)
        self.assertIn("post-hoc", joined)
        self.assertIn("predeclare", joined)

    def test_guardrails_all_false(self) -> None:
        guardrails = rows("no_mutation_guardrails.csv")
        self.assertTrue(guardrails)
        self.assertTrue(all(row["value"] == "false" for row in guardrails))


if __name__ == "__main__":
    unittest.main()
