import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_cooler_timeout_and_wall_circuit_study as study


class CoolerTimeoutAndWallCircuitStudyTests(unittest.TestCase):
    def test_case_aggregates_keep_active_and_passive_terms_separate(self):
        aggregates = study.case_aggregates()
        self.assertEqual(set(aggregates), {"salt_2", "salt_3", "salt_4"})
        for row in aggregates.values():
            self.assertGreater(row["passive_hA_W_K"], 0.0)
            self.assertGreater(row["passive_target_loss_W"], 0.0)
            self.assertGreater(row["heater_source_W_setup"], 0.0)
            self.assertGreater(row["cooler_sink_W_setup"], 0.0)

    def test_passive_total_power_scaled_candidate_is_promoted_not_admitted(self):
        scores = study.circuit_score_rows()
        summaries = {row["candidate_id"]: row for row in study.candidate_summary_rows(scores)}
        candidate = summaries["PB1_total_hA_heater_power_drive_p1"]
        self.assertEqual(candidate["target_scope"], "passive_total")
        self.assertEqual(candidate["validation_qoi_gate"], "pass")
        self.assertEqual(candidate["holdout_qoi_gate"], "pass")
        self.assertIn("promote_to_coupled", candidate["recommendation"])
        self.assertEqual(candidate["admission_decision"], "not_admitted_pending_coupled_score_and_local_temperature_review")

    def test_test_section_component_stays_not_admitted_when_percent_gate_fails(self):
        scores = study.circuit_score_rows()
        summaries = {row["candidate_id"]: row for row in study.candidate_summary_rows(scores)}
        candidate = summaries["TS6_test_section_hA_heater_power_drive_p2"]
        self.assertEqual(candidate["target_scope"], "test_section")
        self.assertEqual(candidate["validation_qoi_gate"], "fail")
        self.assertEqual(candidate["holdout_qoi_gate"], "fail")
        self.assertEqual(candidate["admission_decision"], "not_admitted_pending_coupled_score_and_local_temperature_review")

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = study.OUT
        with tempfile.TemporaryDirectory() as tmp:
            study.OUT = Path(tmp)
            try:
                summary = study.build()
                self.assertEqual(summary["task"], study.TASK)
                required = [
                    "fluid_timeout_diagnosis.csv",
                    "case_thermal_circuit_inputs.csv",
                    "thermal_circuit_methodology.csv",
                    "wall_circuit_candidate_scores.csv",
                    "wall_circuit_candidate_summary.csv",
                    "decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((study.OUT / name).exists(), name)
                with (study.OUT / "wall_circuit_candidate_summary.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertGreaterEqual(len(rows), 6)
            finally:
                study.OUT = original_out


if __name__ == "__main__":
    unittest.main()
