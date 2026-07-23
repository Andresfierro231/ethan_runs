import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_r4_predeclared_source_envelope_uq_gate"
SCRIPT = ROOT / "tools/analyze/build_passive_h2_r4_predeclared_source_envelope_uq_gate.py"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2R4GateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_predeclares_but_does_not_freeze(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["candidate_id"], "PASSIVE-H2-R4-CAND001")
        self.assertEqual(summary["excluded_source_families"], ["junction"])
        self.assertEqual(summary["setup_runtime_ready_rows"], 16)
        self.assertEqual(summary["strict_source_envelope_ready_rows"], 0)
        self.assertEqual(summary["same_qoi_release_uq_ready_rows"], 0)
        self.assertEqual(summary["freeze_allowed_rows"], 0)
        self.assertFalse(summary["candidate_freeze"])

    def test_manifest_is_predeclared_before_scoring(self) -> None:
        manifest = rows("r4_candidate_predeclaration_manifest.csv")
        self.assertEqual(len(manifest), 1)
        row = manifest[0]
        self.assertEqual(row["candidate_id"], "PASSIVE-H2-R4-CAND001")
        self.assertEqual(row["predeclaration_time"], "before_any_R4_scoring_or_freeze")
        self.assertEqual(row["score_allowed_now"], "false")
        self.assertEqual(row["freeze_allowed_now"], "false")

    def test_family_matrix_has_only_four_families_across_four_cases(self) -> None:
        matrix = rows("r4_source_family_gate_matrix.csv")
        self.assertEqual(len(matrix), 16)
        self.assertEqual({row["source_family"] for row in matrix}, {"cooling_branch", "downcomer", "lower_leg", "upcomer"})
        self.assertEqual({row["case_id"] for row in matrix}, {"salt_1", "salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["setup_basis_ready"] == "true" for row in matrix))
        self.assertTrue(all(row["source_property_release_ready"] == "false" for row in matrix))

    def test_freeze_gate_fails_for_source_envelope_and_release_uq(self) -> None:
        gate = {row["gate"]: row for row in rows("r4_freeze_gate.csv")}
        self.assertEqual(gate["candidate_predeclared_before_r4_scoring"]["status"], "pass")
        self.assertEqual(gate["strict_source_envelope"]["status"], "fail_closed")
        self.assertEqual(gate["same_qoi_release_uq"]["status"], "fail_closed")
        self.assertEqual(gate["candidate_freeze"]["status"], "closed_not_run")

    def test_guardrails_all_false(self) -> None:
        guardrails = rows("no_mutation_guardrails.csv")
        self.assertTrue(guardrails)
        self.assertTrue(all(row["value"] == "false" for row in guardrails))


if __name__ == "__main__":
    unittest.main()
