import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.analyze import build_heater_source_redistribution_coupled_score as heater


class HeaterSourceRedistributionCoupledScoreTests(unittest.TestCase):
    def test_lambda_grid_is_exact_0_to_1_by_0p05(self):
        self.assertEqual(len(heater.LAMBDA_GRID), 21)
        self.assertEqual(heater.LAMBDA_GRID[0], 0.0)
        self.assertEqual(heater.LAMBDA_GRID[-1], 1.0)
        self.assertEqual(heater.LAMBDA_GRID[1], 0.05)

    def test_weights_are_positive_normalized_and_interpolated(self):
        upstream = heater.heater_weights(0.0)
        middle = heater.heater_weights(0.5)
        downstream = heater.heater_weights(1.0)
        self.assertAlmostEqual(sum(upstream.values()), 1.0)
        self.assertAlmostEqual(sum(middle.values()), 1.0)
        self.assertAlmostEqual(sum(downstream.values()), 1.0)
        self.assertTrue(all(value > 0.0 for value in middle.values()))
        self.assertAlmostEqual(middle["tw4_to_tw5"], 0.40)
        self.assertAlmostEqual(middle["tw5_to_tw6"], 0.325)
        self.assertAlmostEqual(middle["tw6_to_tp3"], 0.275)

    def test_dry_contracts_are_salt2_fit_grid_only(self):
        rows = heater.scenario_contract_rows(None)
        self.assertEqual(len(rows), len(heater.LAMBDA_GRID))
        self.assertEqual({row["phase"] for row in rows}, {"salt2_fit_grid"})
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2"})
        self.assertEqual({row["heater_source_mode"] for row in rows}, {"tw4_to_tp3_three_span"})
        for row in rows:
            self.assertIn("Salt2_lambda", row["runtime_inputs"])
            self.assertNotIn("wallHeatFlux", row["runtime_inputs"])

    def test_selected_contracts_cover_three_cases_and_two_coolers(self):
        rows = heater.scenario_contract_rows(0.35)
        selected = [row for row in rows if row["phase"] == "selected_coupled_score"]
        self.assertEqual(len(selected), 6)
        self.assertEqual({row["case_id"] for row in selected}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["cooler_candidate_id"] for row in selected}, set(heater.COOLER_IDS))
        self.assertEqual({row["heater_lambda"] for row in selected}, {"0.35"})

    def test_selection_uses_salt2_grid_only_with_tie_breaks(self):
        rows = [
            {
                "phase": "salt2_fit_grid",
                "case_id": "salt_2",
                "heater_lambda": "0.25",
                "candidate_id": "a",
                "coupled_run_status": "completed",
                "root_status": "accepted",
                "all_probe_rmse_K": "10.0",
                "tw_rmse_K": "9.0",
                "mdot_error_pct": "5.0",
            },
            {
                "phase": "salt2_fit_grid",
                "case_id": "salt_2",
                "heater_lambda": "0.30",
                "candidate_id": "b",
                "coupled_run_status": "completed",
                "root_status": "accepted",
                "all_probe_rmse_K": "10.0",
                "tw_rmse_K": "8.0",
                "mdot_error_pct": "7.0",
            },
            {
                "phase": "salt2_fit_grid",
                "case_id": "salt_3",
                "heater_lambda": "0.95",
                "candidate_id": "leakage_if_selected",
                "coupled_run_status": "completed",
                "root_status": "accepted",
                "all_probe_rmse_K": "1.0",
                "tw_rmse_K": "1.0",
                "mdot_error_pct": "1.0",
            },
        ]
        selection = heater.select_lambda_from_coupled(rows)
        self.assertEqual(selection["selection_status"], "selected_from_salt2_only")
        self.assertEqual(selection["heater_lambda"], "0.3")
        self.assertEqual(selection["selected_candidate_id"], "b")

    def test_runtime_audit_names_forbidden_inputs(self):
        audit = heater.runtime_input_audit_rows(heater.scenario_contract_rows(None), run_fluid=False, selected_lambda=None)
        text = " ".join(row["forbidden_runtime_input"] + " " + row["evidence"] for row in audit)
        self.assertIn("realized wallHeatFlux", text)
        self.assertIn("CFD mdot", text)
        self.assertIn("validation/holdout probe temperatures", text)
        self.assertIn("Salt2", text)

    def test_admission_requires_validation_and_holdout_all_metrics(self):
        rows = [
            {
                "phase": "selected_coupled_score",
                "candidate_id": "candidate",
                "case_id": "salt_3",
                "split_role": "validation",
                "heater_lambda": "0.5",
                "cooler_candidate_id": "HX_LUMPED_UA_NTU",
                "coupled_run_status": "completed",
                "mdot_error_pct": "0.1",
                "tp_rmse_K": "99.0",
                "tw_rmse_K": "99.0",
                "all_probe_rmse_K": "99.0",
            }
        ]
        deltas = heater.coupled_delta_rows(rows)
        self.assertEqual(deltas[0]["score_gate"], "fail")
        self.assertGreater(float(deltas[0]["tp_delta_vs_m3_K"]), 0.0)
        self.assertGreater(float(deltas[0]["tw_delta_vs_m3_K"]), 0.0)

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = heater.OUT
        with tempfile.TemporaryDirectory() as tmp:
            heater.OUT = Path(tmp)
            try:
                summary = heater.build(run_fluid=False)
                self.assertEqual(summary["task"], heater.TASK)
                required = [
                    "heater_source_lambda_grid.csv",
                    "selected_heater_source_weights.csv",
                    "scenario_contracts.csv",
                    "runtime_input_audit.csv",
                    "coupled_scorecard.csv",
                    "coupled_delta_vs_m3.csv",
                    "probe_error_localization.csv",
                    "candidate_admission_review.csv",
                    "background_run_contract.csv",
                    "blocker_decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((heater.OUT / name).exists(), name)
                with (heater.OUT / "scenario_contracts.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), len(heater.LAMBDA_GRID))
            finally:
                heater.OUT = original_out


if __name__ == "__main__":
    unittest.main()
