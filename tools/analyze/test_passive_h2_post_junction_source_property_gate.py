import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_post_junction_source_property_gate"
SCRIPT = ROOT / "tools/analyze/build_passive_h2_post_junction_source_property_gate.py"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2PostJunctionGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_runtime_complete_but_release_closed(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], "passive_h2_post_junction_runtime_complete_source_property_release_fail_closed")
        self.assertEqual(summary["runtime_case_rows"], 4)
        self.assertEqual(summary["runtime_completed_case_rows"], 4)
        self.assertEqual(summary["accepted_root_case_rows"], 4)
        self.assertEqual(summary["runtime_nonzero_case_rows"], 4)
        self.assertTrue(summary["salt1_junction_runtime_gap_closed"])
        self.assertEqual(summary["source_property_release_ready_rows"], 0)
        self.assertEqual(summary["release_ready_qoi_labels"], 0)
        self.assertEqual(summary["freeze_ready_candidates"], 0)
        self.assertEqual(summary["final_score_values"], 0)

    def test_runtime_matrix_contains_four_cases_and_salt1_junction(self) -> None:
        runtime = rows("post_junction_runtime_evidence.csv")
        self.assertEqual({row["case_id"] for row in runtime}, {"salt_1", "salt_2", "salt_3", "salt_4"})
        salt1 = [row for row in runtime if row["case_id"] == "salt_1"][0]
        self.assertEqual(salt1["operator_rows_used"], "5")
        self.assertEqual(salt1["accepted_roots"], "true")
        self.assertEqual(salt1["forbidden_runtime_inputs_used"], "false")
        self.assertIn("junction", salt1["admissibility_role"])

    def test_release_gates_fail_closed_after_runtime_pass(self) -> None:
        gates = {row["gate"]: row for row in rows("post_junction_release_gate.csv")}
        self.assertEqual(gates["four_case_runtime_feasibility"]["status"], "pass_diagnostic")
        self.assertEqual(gates["salt1_junction_gap"]["status"], "closed_as_runtime_gap")
        self.assertEqual(gates["strict_source_envelope"]["status"], "fail_closed")
        self.assertEqual(gates["same_qoi_release_uq"]["status"], "fail_closed")
        self.assertEqual(gates["candidate_freeze"]["status"], "closed_not_run")
        self.assertTrue(all(row["release_ready"] == "false" for row in gates.values()))

    def test_claims_and_guardrails_do_not_release_or_score(self) -> None:
        claims = {row["claim"]: row for row in rows("claim_boundaries.csv")}
        self.assertEqual(claims["full five-family PASSIVE-H2 runtime coverage includes Salt1 junction"]["allowed"], "true")
        self.assertEqual(claims["Salt1 junction is source/property release-grade"]["allowed"], "false")
        guards = rows("no_mutation_guardrails.csv")
        self.assertTrue(guards)
        self.assertTrue(all(row["occurred"] == "false" for row in guards))


if __name__ == "__main__":
    unittest.main()
