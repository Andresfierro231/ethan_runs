import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_candidate_gate_rerun_passive_role_filtered_policy"
SCRIPT = ROOT / "tools/analyze/build_passive_h2_candidate_gate_rerun_passive_role_filtered_policy.py"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2PassiveRoleFilteredPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_fails_closed_but_carries_scores(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(
            summary["decision"],
            "passive_h2_passive_role_filtered_setup_policy_supports_diagnostic_scores_release_fail_closed",
        )
        self.assertEqual(summary["case_family_rows"], 15)
        self.assertEqual(summary["runtime_setup_input_allowed_rows"], 15)
        self.assertEqual(summary["source_property_release_allowed_rows"], 0)
        self.assertEqual(summary["strict_source_envelope_pass_rows"], 0)
        self.assertEqual(summary["presentable_diagnostic_score_rows_carried_forward"], 11)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["protected_or_final_scoring"])

    def test_policy_matrix_distinguishes_setup_from_admission(self) -> None:
        rows = read_csv(OUT / "setup_vs_admission_policy_matrix.csv")
        by_item = {row["policy_item"]: row for row in rows}
        self.assertEqual(by_item["setup_dictionary_source_basis"]["setup_operator_allowed"], "true")
        self.assertEqual(by_item["setup_dictionary_source_basis"]["source_property_release_allowed"], "false")
        self.assertEqual(by_item["strict_literature_or_source_envelope"]["decision"], "fail_closed")
        self.assertIn("cannot substitute", by_item["strict_literature_or_source_envelope"]["rationale"])

    def test_case_family_rows_are_runtime_ready_not_release_ready(self) -> None:
        rows = read_csv(OUT / "candidate_case_family_policy_matrix.csv")
        self.assertEqual(len(rows), 15)
        self.assertTrue(all(row["runtime_setup_input_allowed"] == "true" for row in rows))
        self.assertTrue(all(row["source_property_release_allowed"] == "false" for row in rows))
        self.assertTrue(all(row["protected_or_final_score_allowed"] == "false" for row in rows))
        self.assertEqual({row["workaround_status"] for row in rows}, {"setup_runtime_contract_ready_no_release"})

    def test_legacy_named_gate_tables_are_regenerated(self) -> None:
        gate_rows = read_csv(OUT / "candidate_gate_rerun_matrix.csv")
        gates = {row["gate"]: row for row in gate_rows}
        self.assertEqual(gates["passive_role_filtered_subspan"]["status"], "pass_recovered")
        self.assertEqual(gates["strict_source_envelope"]["status"], "fail_closed")
        self.assertEqual(gates["final_score"]["count_or_value"], "0")

        source_rows = read_csv(OUT / "case_family_source_property_gate.csv")
        self.assertEqual(len(source_rows), 15)
        self.assertTrue(all(row["strict_source_envelope_pass"] == "false" for row in source_rows))
        self.assertTrue(all(row["source_property_release_allowed_now"] == "false" for row in source_rows))

        release = read_csv(OUT / "release_decision.csv")[0]
        self.assertEqual(release["source_property_release_allowed"], "false")
        self.assertEqual(release["score_allowed"], "false")

    def test_carried_scores_remain_diagnostic(self) -> None:
        rows = read_csv(OUT / "carried_forward_presentable_diagnostic_scores.csv")
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(row["admission_status"] == "diagnostic_presentable_not_admitted" for row in rows))
        score_ids = {row["score_id"] for row in rows}
        self.assertIn("D4_M3_segment_offsets_min2_train", score_ids)
        self.assertIn("PASSIVE-H2_runtime_salt_4", score_ids)
        self.assertIn("S13_Q_wall_W_medium_fine_mesh_spread", score_ids)

    def test_claims_have_allowed_and_forbidden_rows(self) -> None:
        rows = read_csv(OUT / "thesis_claim_language.csv")
        self.assertGreaterEqual(sum(row["allowed"] == "true" for row in rows), 3)
        self.assertGreaterEqual(sum(row["allowed"] == "false" for row in rows), 2)
        forbidden = " ".join(row["forbidden_wording"] for row in rows if row["allowed"] == "false")
        self.assertIn("source/property release", forbidden)
        self.assertIn("final score", forbidden)

    def test_svg_figures_exist_and_are_labeled_diagnostic(self) -> None:
        for name in [
            "temperature_residual_shape_rmse.svg",
            "passive_h2_runtime_closure_ratio.svg",
            "hx_fixed_mdot_duty_error.svg",
        ]:
            text = (OUT / "figures" / name).read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("Diagnostic evidence only", text)

    def test_no_mutation_guardrails_all_false(self) -> None:
        rows = read_csv(OUT / "no_mutation_guardrails.csv")
        self.assertTrue(rows)
        self.assertTrue(all(row["value"] == "false" for row in rows))


if __name__ == "__main__":
    unittest.main()
