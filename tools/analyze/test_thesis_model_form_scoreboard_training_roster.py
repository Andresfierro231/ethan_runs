from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_thesis_model_form_scoreboard_training_roster as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThesisModelFormScoreboardTrainingRosterTests(unittest.TestCase):
    def test_training_roster_contains_newer_model_form_families(self) -> None:
        rows = builder.training_roster_rows()
        ids = {row["model_form_id"] for row in rows}
        for expected in [
            "M0_setup_only_baseline",
            "M3_segment_only_fluid_walls",
            "MF12_signed_source_memory_bulk_to_TP",
            "MF15_wall_core_exchange_operator",
            "MF15_axial_mixing_operator",
            "M5_MF04_throughflow_recirculation_exchange_cell",
            "MF07_MF08_MF10_development_reset_signed_wallflux",
            "M6_final_frozen_candidate",
        ]:
            self.assertIn(expected, ids)
        self.assertGreaterEqual(len(rows), 12)

    def test_split_plan_keeps_train_holdout_external_separate(self) -> None:
        rows = builder.split_plan_rows()
        by_case = {row["case_or_family"]: row for row in rows}
        for case in ["salt_1_nominal", "salt_2_nominal", "salt_3_nominal", "salt_4_nominal"]:
            self.assertEqual(by_case[case]["split_role"], "train_nominal")
            self.assertTrue(by_case[case]["train_role_allowed"])
            self.assertFalse(by_case[case]["coefficient_fit_allowed_now"])
            self.assertTrue(by_case[case]["coefficient_fit_allowed_after_source_property_release"])
        for case in ["salt_2_minus5Q", "salt_2_plus5Q", "val_salt2"]:
            self.assertFalse(by_case[case]["train_role_allowed"])
            self.assertFalse(by_case[case]["coefficient_fit_allowed_now"])
            self.assertFalse(by_case[case]["model_selection_allowed_now"])
        self.assertIn("cannot_be_combined", by_case["legacy_salt3_salt4_transfer_packages"]["score_claim_allowed"])

    def test_build_outputs_no_protected_scoring_or_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "scoreboard_training_roster_complete_no_training_or_protected_scoring")
            self.assertEqual(summary["train_nominal_rows"], 4)
            self.assertEqual(summary["holdout_rows"], 2)
            self.assertEqual(summary["external_test_rows"], 1)
            self.assertEqual(summary["can_score_validation_now_rows"], 0)
            self.assertEqual(summary["source_property_release"], "false")
            for filename in [
                "model_form_training_roster.csv",
                "scoreboard_presence_audit.csv",
                "canonical_train_validation_holdout_plan.csv",
                "trainability_gate.csv",
                "next_training_sequence.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "summary.json",
                "README.md",
                "thesis_model_form_training_roster_insert.md",
            ]:
                self.assertTrue((out / filename).exists(), filename)

            gates = {row["gate"]: row for row in read_rows(out / "trainability_gate.csv")}
            self.assertEqual(gates["validation_holdout_scoring"]["status"], "locked")
            self.assertEqual(gates["runtime_source_property_release"]["status"], "fail_closed")


if __name__ == "__main__":
    unittest.main()
