from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_passive_h2_salt14_diagnostic_freeze_and_blind_predictions as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2Salt14DiagnosticFreezeAndBlindPredictionsTests(unittest.TestCase):
    def test_salt1_prediction_attempt_is_blocked(self) -> None:
        rows = builder.salt1_prediction_attempt_rows()
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["case_key"] == "salt1_nominal" for row in rows))
        self.assertTrue(any(row["required_evidence"] == "case_row_passive_h2_operator" for row in rows))
        self.assertTrue(all(row["available"] == "false" for row in rows))

    def test_train_roster_preserves_salt1_4_contract(self) -> None:
        rows = builder.diagnostic_train_roster_rows()
        self.assertEqual(
            [row["case_key"] for row in rows],
            ["salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"],
        )
        self.assertEqual(sum(row["numeric_passive_h2_prediction_available"] == "true" for row in rows), 3)
        self.assertTrue(all(row["fit_ready_now"] == "false" for row in rows))

    def test_coefficient_lock_and_blind_predictions_fail_closed(self) -> None:
        lock = builder.coefficient_lock_rows()[0]
        self.assertEqual(lock["diagnostic_lock_created"], "false")
        self.assertEqual(lock["admitted_final_freeze_created"], "false")
        self.assertIn("salt1_nominal", lock["missing_prediction_cases"])
        blind = builder.blind_prediction_rows()
        self.assertEqual(len(blind), 21)
        self.assertTrue(all(row["prediction_available"] == "false" for row in blind))
        self.assertTrue(all(row["score_emitted"] == "false" for row in blind))

    def test_build_outputs_expected_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "passive_h2_salt14_freeze_and_blind_predictions_blocked_missing_salt1_no_lock_no_predictions",
            )
            self.assertEqual(summary["requested_train_rows"], 4)
            self.assertEqual(summary["train_numeric_prediction_rows_available"], 3)
            self.assertFalse(summary["diagnostic_lock_created"])
            self.assertEqual(summary["blind_numeric_prediction_rows_available"], 0)
            for filename in [
                "salt1_setup_prediction_attempt.csv",
                "diagnostic_train_roster.csv",
                "coefficient_lock_manifest.csv",
                "blind_prediction_artifact.csv",
                "split_leakage_audit.csv",
                "next_unblock_actions.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / filename).exists(), filename)
            leakage = read_rows(out / "split_leakage_audit.csv")
            self.assertTrue(all(row["used_for_fit"] == "false" for row in leakage))


if __name__ == "__main__":
    unittest.main()
