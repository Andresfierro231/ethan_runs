from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_passive_h2_final_form_admission_phase_gate as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2FinalFormAdmissionPhaseGateTests(unittest.TestCase):
    def test_runtime_support_does_not_equal_final_form(self) -> None:
        rows = builder.final_form_readiness_rows()
        by_gate = {row["gate"]: row for row in rows}
        self.assertEqual(by_gate["outer_insulation_radiation_runtime_implemented"]["status"], "pass")
        self.assertEqual(by_gate["runtime_input_legality"]["status"], "pass")
        self.assertEqual(by_gate["source_family_to_subspan_mapping"]["status"], "fail_closed")
        self.assertEqual(by_gate["same_qoi_setup_uq"]["status"], "fail_closed")
        self.assertEqual(by_gate["protected_score_or_final_form"]["status"], "closed_not_run")
        self.assertTrue(all(row["ready_for_final_form"] == "false" for row in rows))

    def test_subspan_rows_remain_unreleased(self) -> None:
        rows = builder.subspan_recovery_rows()
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["current_parent_mapping_ready"] == "True" for row in rows))
        self.assertTrue(all(row["current_subspan_mapping_ready"] == "False" for row in rows))
        self.assertTrue(all(row["release_now"] == "false" for row in rows))

    def test_same_qoi_uq_gap_blocks_freeze(self) -> None:
        rows = builder.same_qoi_uq_rows()
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["target_row_available"] == "True" for row in rows))
        self.assertTrue(all(row["target_minus_row_available"] == "False" for row in rows))
        self.assertTrue(all(row["target_plus_row_available"] == "False" for row in rows))
        self.assertTrue(all(row["same_qoi_uq_ready"] == "False" for row in rows))

    def test_build_summary_and_artifacts_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "passive_h2_final_form_admission_phase_fail_closed_runtime_supported_no_freeze_no_score",
            )
            self.assertTrue(summary["runtime_supported"])
            self.assertTrue(summary["runtime_roots_accepted"])
            self.assertEqual(summary["forbidden_runtime_inputs_true"], 0)
            self.assertEqual(summary["subspan_release_ready_rows"], 0)
            self.assertEqual(summary["same_qoi_uq_ready_rows"], 0)
            self.assertEqual(summary["source_property_release_ready_rows"], 0)
            self.assertFalse(summary["candidate_freeze"])
            self.assertFalse(summary["protected_scoring"])
            self.assertFalse(summary["final_form_allowed"])
            self.assertEqual(summary["final_score_values"], 0)
            decision = read_rows(out / "admission_phase_decision.csv")
            self.assertEqual(decision[0]["final_form_allowed"], "false")


if __name__ == "__main__":
    unittest.main()
