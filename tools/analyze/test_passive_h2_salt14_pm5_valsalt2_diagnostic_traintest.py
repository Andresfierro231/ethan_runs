from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2Salt14Pm5ValSalt2DiagnosticTrainTestTests(unittest.TestCase):
    def test_training_rows_are_salt1_4_and_fail_closed(self) -> None:
        rows = builder.training_availability_rows()
        self.assertEqual(
            [row["case_key"] for row in rows],
            ["salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"],
        )
        salt1 = rows[0]
        self.assertEqual(salt1["passive_h2_prediction_available"], "false")
        self.assertIn("missing_passive_h2_runtime_prediction", salt1["blocker_or_status"])
        self.assertTrue(all(row["fit_ready_now"] == "false" for row in rows))

    def test_blind_rows_are_score_only_and_not_ready(self) -> None:
        rows = builder.blind_test_availability_rows()
        self.assertEqual([row["case_key"] for row in rows], ["salt2_lo5q", "salt2_hi5q", "val_salt2"])
        self.assertTrue(all(row["fit_allowed"] == "no" for row in rows))
        self.assertTrue(all(row["model_selection_allowed"] == "no" for row in rows))
        self.assertTrue(all(row["passive_h2_frozen_prediction_available"] == "false" for row in rows))
        self.assertTrue(all(int(row["target_rows_available"]) > 0 for row in rows))

    def test_requested_score_shell_emits_no_scores(self) -> None:
        rows = builder.requested_score_shell_rows()
        self.assertEqual(len(rows), 18)
        self.assertTrue(all(row["score_emitted"] == "false" for row in rows))
        self.assertTrue(all(row["score_value"] == "" for row in rows))
        self.assertTrue(all(row["prediction_available"] == "false" for row in rows))

    def test_build_outputs_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "passive_h2_salt14_pm5_valsalt2_requested_traintest_blocked_no_fit_no_score",
            )
            self.assertEqual(summary["requested_train_rows"], 4)
            self.assertEqual(summary["requested_blind_test_rows"], 3)
            self.assertEqual(summary["score_values_emitted"], 0)
            self.assertFalse(summary["coefficient_fit_performed"])
            self.assertFalse(summary["protected_rows_used_for_fit_or_selection"])
            for filename in [
                "case_split_contract.csv",
                "training_availability.csv",
                "blind_test_availability.csv",
                "requested_score_shell.csv",
                "fit_and_score_decision.csv",
                "split_leakage_audit.csv",
                "next_action_queue.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / filename).exists(), filename)
            decision = read_rows(out / "fit_and_score_decision.csv")[0]
            self.assertEqual(decision["coefficient_fit_performed"], "false")
            self.assertEqual(decision["protected_rows_used_for_fit_or_selection"], "false")


if __name__ == "__main__":
    unittest.main()
