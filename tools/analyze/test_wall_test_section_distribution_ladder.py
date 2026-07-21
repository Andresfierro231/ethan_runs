import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.analyze import build_wall_test_section_distribution_ladder as ladder


class WallTestSectionDistributionLadderTests(unittest.TestCase):
    def test_local_candidate_definitions_are_exact_ladder(self):
        rows = ladder.local_candidate_definitions()
        ids = [row["wall_candidate_id"] for row in rows]
        self.assertEqual(ids, ladder.LOCAL_WALL_IDS)
        self.assertTrue(all(row["fit_case_id"] == "salt_2" for row in rows))
        self.assertTrue(all(row["fit_parameter_count"] == 1 for row in rows))

    def test_shape_candidates_are_positive_and_distinct(self):
        pb2 = ladder.shape_for_candidate("PB2_salt2_local_shape_passive_hA_p1")
        pb3 = ladder.shape_for_candidate("PB3_upcomer_test_section_attenuated_shape_p1")
        self.assertTrue(all(value > 0.0 for value in pb2.values()))
        self.assertTrue(all(value > 0.0 for value in pb3.values()))
        self.assertNotEqual(pb2[("upcomer", "test_section")], pb3[("upcomer", "test_section")])

    def test_runtime_audit_excludes_forbidden_validation_inputs(self):
        audit = ladder.runtime_input_audit_rows([], run_fluid=False)
        text = " ".join(row["forbidden_runtime_input"] + " " + row["evidence"] for row in audit)
        self.assertIn("realized wallHeatFlux", text)
        self.assertIn("validation/holdout wall-shell temperature", text)
        self.assertIn("validation/holdout probe temperatures", text)
        self.assertNotIn("Salt3_shape", text)
        self.assertNotIn("Salt4_shape", text)

    def test_static_gate_allows_only_nonphysical_free_candidates(self):
        audit = ladder.segment_heat_placement_audit_rows()
        gates = ladder.static_candidate_gate_rows(audit)
        self.assertEqual(len(gates), len(ladder.LOCAL_WALL_IDS) * 3)
        for row in gates:
            self.assertEqual(int(row["nonphysical_value_count"]), 0)
            if row["split_role"] != "train":
                self.assertEqual(row["static_gate"], "pass")

    def test_scenario_contracts_use_salt2_shape_only(self):
        audit = ladder.segment_heat_placement_audit_rows()
        gates = ladder.static_candidate_gate_rows(audit)
        rows = ladder.scenario_contract_rows(gates)
        self.assertEqual(len(rows), len(ladder.LOCAL_WALL_IDS) * len(ladder.COOLER_IDS) * 3)
        for row in rows:
            self.assertEqual(row["runtime_input_violations"], 0)
            self.assertIn("Salt2_wall_shape", row["runtime_inputs"])
            self.assertNotIn("wallHeatFlux", row["runtime_inputs"])
            self.assertNotIn("probe", row["runtime_inputs"])

    def test_coupled_delta_requires_mdot_all_probe_and_tw_to_pass(self):
        rows = [
            {
                "candidate_id": "candidate",
                "case_id": "salt_3",
                "split_role": "validation",
                "coupled_run_status": "completed",
                "mdot_error_pct": "0.1",
                "all_probe_rmse_K": "99.0",
                "tw_rmse_K": "99.0",
            }
        ]
        deltas = ladder.coupled_delta_rows(rows)
        self.assertEqual(deltas[0]["score_gate"], "fail")
        self.assertGreater(float(deltas[0]["all_probe_delta_vs_m3_K"]), 0.0)
        self.assertGreater(float(deltas[0]["tw_delta_vs_m3_K"]), 0.0)

    def test_default_coupled_rows_are_pending_background_run(self):
        audit = ladder.segment_heat_placement_audit_rows()
        gates = ladder.static_candidate_gate_rows(audit)
        contracts = ladder.scenario_contract_rows(gates)
        rows, probes = ladder.coupled_scorecard_rows(contracts, run_fluid=False, timeout_seconds=ladder.DEFAULT_TIMEOUT_SECONDS)
        self.assertEqual({row["coupled_run_status"] for row in rows}, {"not_run_submit_background_srun"})
        self.assertEqual({row["coupled_gate"] for row in rows}, {"pending_background_fluid_score"})
        self.assertEqual(probes, [])

    def test_probe_delta_rows_compare_to_m3_sensor_baseline(self):
        probes = [
            {
                "candidate_id": "candidate",
                "case_id": "salt_3",
                "split_role": "validation",
                "sensor": "TP3",
                "kind": "TP",
                "predicted_K": "450.0",
                "target_K": "447.213671156",
                "error_K": "2.786328844",
                "abs_error_K": "2.786328844",
                "prediction_source_segment": "left_lower_vertical",
                "validation_excluded": "no",
            }
        ]
        rows = ladder.probe_delta_rows(probes)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sensor"], "TP3")
        self.assertEqual(rows[0]["probe_gate"], "pass")

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = ladder.OUT
        with tempfile.TemporaryDirectory() as tmp:
            ladder.OUT = Path(tmp)
            try:
                summary = ladder.build(run_fluid=False)
                self.assertEqual(summary["task"], ladder.TASK)
                required = [
                    "segment_heat_placement_audit.csv",
                    "probe_shape_regression_audit.csv",
                    "local_candidate_definitions.csv",
                    "candidate_definitions.csv",
                    "static_candidate_gate.csv",
                    "scenario_contracts.csv",
                    "runtime_input_audit.csv",
                    "coupled_scorecard.csv",
                    "coupled_delta_vs_m3.csv",
                    "probe_error_localization.csv",
                    "probe_delta_vs_m3.csv",
                    "role_segment_error_summary.csv",
                    "candidate_admission_review.csv",
                    "background_run_contract.csv",
                    "blocker_decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((ladder.OUT / name).exists(), name)
                with (ladder.OUT / "scenario_contracts.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), len(ladder.LOCAL_WALL_IDS) * len(ladder.COOLER_IDS) * 3)
            finally:
                ladder.OUT = original_out


if __name__ == "__main__":
    unittest.main()
