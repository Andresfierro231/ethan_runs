import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.analyze import build_wall_test_section_coupled_admission as adm


class WallTestSectionCoupledAdmissionTests(unittest.TestCase):
    def test_candidate_definitions_include_pb1_cooler_cross_product_and_ts_diagnostics(self):
        rows = adm.candidate_definitions()
        candidate_ids = {row["candidate_id"] for row in rows}
        self.assertIn("PB1_PLUS_HX_LUMPED_UA_NTU", candidate_ids)
        self.assertIn("PB1_PLUS_HX_SEGMENTED_UA_NTU_N16", candidate_ids)
        self.assertIn(adm.TS6_ID, candidate_ids)
        self.assertIn(adm.TS7_ID, candidate_ids)
        pb1_rows = [row for row in rows if row["candidate_id"].startswith("PB1_PLUS_")]
        self.assertEqual(len(pb1_rows), 4)
        self.assertTrue(all(row["wall_candidate_id"] == adm.PB1_ID for row in pb1_rows))

    def test_scenario_contracts_use_setup_only_pb1_inputs(self):
        rows = adm.scenario_contract_rows()
        self.assertEqual(len(rows), 12)
        for row in rows:
            self.assertEqual(row["runtime_input_violations"], 0)
            self.assertIn("setup_external_boundary_rows", row["runtime_inputs"])
            self.assertIn("PB1_Salt2_drive", row["runtime_inputs"])
            self.assertGreater(float(row["pb1_setup_multiplier"]), 0.0)
            self.assertNotIn("wallHeatFlux", row["runtime_inputs"])
            self.assertNotIn("validation", row["runtime_inputs"])

    def test_static_summary_keeps_pb1_and_local_ts_decisions_separate(self):
        summaries = {row["candidate_id"]: row for row in adm.static_component_summary_rows()}
        self.assertEqual(summaries[adm.PB1_ID]["validation_qoi_gate"], "pass")
        self.assertEqual(summaries[adm.PB1_ID]["holdout_qoi_gate"], "pass")
        self.assertIn("pending_coupled", summaries[adm.PB1_ID]["admission_decision"])
        self.assertEqual(summaries[adm.TS6_ID]["validation_qoi_gate"], "fail")
        self.assertEqual(summaries[adm.TS7_ID]["holdout_qoi_gate"], "fail")
        self.assertIn("not_admitted", summaries[adm.TS7_ID]["admission_decision"])

    def test_default_coupled_rows_are_pending_background_run(self):
        rows = adm.coupled_scorecard_rows(run_fluid=False, timeout_seconds=adm.DEFAULT_TIMEOUT_SECONDS)
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["coupled_run_status"] for row in rows}, {"not_run_submit_background_srun"})
        self.assertEqual({row["coupled_gate"] for row in rows}, {"pending_background_fluid_score"})

    def test_background_contract_uses_srun_and_timeout_273(self):
        row = adm.background_run_contract_rows(adm.DEFAULT_TIMEOUT_SECONDS)[0]
        self.assertEqual(row["timeout_seconds"], adm.DEFAULT_TIMEOUT_SECONDS)
        self.assertIn("srun -N1 -n1", row["command"])
        self.assertIn("--timeout-seconds 273", row["command"])
        self.assertIn("&", row["command"])

    def test_blocker_decision_stays_open_without_coupled_scores_and_with_ts_failures(self):
        coupled = adm.coupled_scorecard_rows(run_fluid=False, timeout_seconds=adm.DEFAULT_TIMEOUT_SECONDS)
        static = adm.static_component_summary_rows()
        runtime = adm.runtime_input_audit_rows(run_fluid=False)
        admission = adm.coupled_admission_rows(adm.coupled_delta_rows(coupled), static, runtime)
        decision = adm.blocker_decision_payload(coupled, static, admission, run_fluid=False)
        self.assertEqual(decision["blocker_decision"], "keep_open")
        self.assertEqual(decision["pb1_static_gate"], "pass")
        self.assertEqual(decision["local_test_section_gate"], "diagnostic_nonblocking_fail")
        self.assertEqual(decision["admitted_candidates"], [])

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = adm.OUT
        with tempfile.TemporaryDirectory() as tmp:
            adm.OUT = Path(tmp)
            try:
                summary = adm.build(run_fluid=False)
                self.assertEqual(summary["task"], adm.TASK)
                required = [
                    "candidate_definitions.csv",
                    "scenario_contracts.csv",
                    "static_component_scorecard.csv",
                    "static_component_summary.csv",
                    "coupled_scorecard.csv",
                    "coupled_delta_vs_m3.csv",
                    "coupled_admission_review.csv",
                    "runtime_input_audit.csv",
                    "background_run_contract.csv",
                    "blocker_decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((adm.OUT / name).exists(), name)
                with (adm.OUT / "scenario_contracts.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), 12)
            finally:
                adm.OUT = original_out


if __name__ == "__main__":
    unittest.main()
