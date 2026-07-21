from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_h1_faithful_gap_and_f6_decision import build_package


class H1FaithfulGapAndF6DecisionTests(unittest.TestCase):
    def test_summary_retires_h1_proxy_and_selects_f6_candidate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h1-f6-decision-") as tmpdir:
            summary = build_package(Path(tmpdir))

            self.assertEqual(summary["h1_decision"], "retire_current_h1_as_proxy_only")
            self.assertEqual(summary["next_hydraulic_candidate"], "F6_phi_re")
            self.assertEqual(summary["f6_decision"], "next_bounded_candidate_after_admission_preconditions")
            self.assertFalse(summary["thermal_fit_used"])
            self.assertFalse(summary["global_friction_multiplier_exported"])
            self.assertFalse(summary["native_solver_outputs_mutated"])

    def test_gap_table_names_reset_and_localized_k_failures(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h1-f6-decision-") as tmpdir:
            out_dir = Path(tmpdir)
            build_package(out_dir)

            with (out_dir / "h1_faithful_implementation_gap_table.csv").open(encoding="utf-8", newline="") as handle:
                rows = {row["gap_id"]: row for row in csv.DictReader(handle)}

            self.assertEqual(rows["H1_LOCALIZED_FIXED_K_DIRECTION"]["current_status"], "failed_directional_screen")
            self.assertEqual(rows["H1_RESET_REDEVELOPMENT_NOT_IMPLEMENTED"]["gap_type"], "code_api")
            self.assertIn("reset/development", rows["H1_RESET_REDEVELOPMENT_NOT_IMPLEMENTED"]["faithful_requirement"])

    def test_f6_decision_has_validation_acceptance_and_rejection_rules(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h1-f6-decision-") as tmpdir:
            out_dir = Path(tmpdir)
            build_package(out_dir)

            with (out_dir / "f6_candidate_decision_table.csv").open(encoding="utf-8", newline="") as handle:
                rows = {row["candidate_id"]: row for row in csv.DictReader(handle)}

            f6 = rows["F6_phi_re"]
            self.assertEqual(f6["decision"], "next_bounded_candidate_after_admission_preconditions")
            self.assertIn("corrected-Q", f6["preconditions"])
            self.assertIn("pressure-loss", f6["primary_acceptance_metric"])
            self.assertIn("global multiplier", f6["rejection_rule"])


if __name__ == "__main__":
    unittest.main()
