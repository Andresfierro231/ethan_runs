from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_cfd_postprocess_admission_workflow_triage import build_workflow_triage


class CFDPostprocessAdmissionWorkflowTriageTests(unittest.TestCase):
    def test_workflow_outputs_key_decisions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cfd-workflow-triage-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_workflow_triage(out_dir)

            self.assertEqual(summary["named_case_count"], 7)
            self.assertEqual(summary["harvest_rows"], 4)
            self.assertEqual(summary["harvest_closure_fit_admissible_rows"], 4)

            triage = self._rows_by_key(out_dir / "steady_candidate_admission_triage.csv", "case_key")
            self.assertEqual(triage["salt4_jin"]["current_admission_or_split_verdict"], "holdout")
            self.assertEqual(
                triage["salt4_jin"]["can_expand_training_now_after_correct_postprocessing"],
                "no",
            )
            self.assertIn("Salt1", triage["salt1_jin_lo10q_corrected"]["why_not_admitted_as_training_now"])
            self.assertIn("historical", triage["salt4_jin_hiq_hiins"]["why_not_admitted_as_training_now"])

            hiins = self._rows_by_key(out_dir / "hiins_loins_construction_review.csv", "case_key")
            self.assertIn("baseline insulation restored", hiins["salt3_jin_hiq_hiins"]["construction_status"])
            self.assertEqual(hiins["salt3_jin_hiq_hiins"]["insulation_delta_in"], "0.00")

            harvest = self._rows_by_key(out_dir / "corrected_q_harvest_3295437_processing_status.csv", "source_case_key")
            self.assertEqual(harvest["salt2_jin_lo5q_corrected"]["registry_aggregate_available"], "yes")
            self.assertIn("split-policy", harvest["salt4_jin_hi5q_corrected"]["next_workflow_action"])

            drift_doc = (out_dir / "drift_ratio_definition.md").read_text(encoding="utf-8")
            self.assertIn("drift_ratio = |a * W| / RMSE_about_trend", drift_doc)

            salt2 = self._rows_by_key(out_dir / "salt2_jin_vs_val_comparison.csv", "comparison_axis")
            self.assertIn("coarse", salt2["canonical_display_label"]["salt2_val"])
            self.assertIn("distinct historical", salt2["lineage"]["interpretation"])

    @staticmethod
    def _rows_by_key(path: Path, key: str) -> dict[str, dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return {row[key]: row for row in csv.DictReader(handle)}


if __name__ == "__main__":
    unittest.main()
