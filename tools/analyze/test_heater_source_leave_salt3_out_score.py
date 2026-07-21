import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.analyze import build_heater_source_leave_salt3_out_score as heater


class HeaterSourceLeaveSalt3OutScoreTests(unittest.TestCase):
    def test_lambda_grid_is_exact_0_to_1_by_0p05(self):
        self.assertEqual(len(heater.LAMBDA_GRID), 21)
        self.assertEqual(heater.LAMBDA_GRID[0], 0.0)
        self.assertEqual(heater.LAMBDA_GRID[1], 0.05)
        self.assertEqual(heater.LAMBDA_GRID[-1], 1.0)

    def test_weights_are_positive_normalized_and_interpolated(self):
        middle = heater.heater_weights(0.5)
        self.assertAlmostEqual(sum(middle.values()), 1.0)
        self.assertTrue(all(value > 0.0 for value in middle.values()))
        self.assertAlmostEqual(middle["tw4_to_tw5"], 0.40)
        self.assertAlmostEqual(middle["tw5_to_tw6"], 0.325)
        self.assertAlmostEqual(middle["tw6_to_tp3"], 0.275)

    def test_case_split_contract_is_loso_and_blind_safe(self):
        rows = heater.case_split_contract_rows()
        by_case = {row["case_id"]: row for row in rows}
        for case_id in heater.TRAIN_CASES:
            self.assertEqual(by_case[case_id]["fit_allowed"], "yes")
            self.assertEqual(by_case[case_id]["model_selection_allowed"], "yes")
        self.assertEqual(by_case["salt_3"]["fit_allowed"], "no")
        self.assertEqual(by_case["salt_3"]["model_selection_allowed"], "no")
        for case_id in heater.BLIND_CASES:
            self.assertEqual(by_case[case_id]["fit_allowed"], "no")
            self.assertEqual(by_case[case_id]["model_selection_allowed"], "no")
            self.assertEqual(by_case[case_id]["fluid_adapter_status"], "blocked_no_fluid_case_adapter")

    def test_dry_training_contracts_are_salt124_triplets_only(self):
        rows = heater.scenario_contract_rows(None)
        self.assertEqual(len(rows), len(heater.LAMBDA_GRID) * len(heater.TRAIN_CASES))
        self.assertEqual({row["phase"] for row in rows}, {"loso_train_grid"})
        self.assertEqual({row["case_id"] for row in rows}, set(heater.TRAIN_CASES))
        self.assertNotIn("salt_3", {row["case_id"] for row in rows})
        for row in rows:
            self.assertEqual(row["fit_allowed_for_this_case"], "yes")
            self.assertIn("frozen_Salt2_HX_LUMPED_UA_NTU_alpha_UA", row["runtime_inputs"])

    def test_selected_contracts_score_salt3_without_model_selection(self):
        rows = heater.scenario_contract_rows(0.35)
        selected = [row for row in rows if row["phase"] == "selected_nominal_score"]
        self.assertEqual(len(selected), 4)
        self.assertEqual({row["case_id"] for row in selected}, set(heater.NOMINAL_CASES))
        salt3 = next(row for row in selected if row["case_id"] == "salt_3")
        self.assertEqual(salt3["fit_allowed_for_this_case"], "no")
        self.assertEqual(salt3["model_selection_allowed_for_this_case"], "no")

    def test_selection_requires_complete_salt124_triplet_and_excludes_salt3(self):
        rows = []
        for case_id, rmse in [("salt_1", 3.0), ("salt_2", 5.0), ("salt_4", 7.0)]:
            rows.append(
                {
                    "phase": "loso_train_grid",
                    "case_id": case_id,
                    "heater_lambda": "0.25",
                    "candidate_id": "candidate_a",
                    "coupled_run_status": "completed",
                    "root_status": "accepted",
                    "all_probe_rmse_K": str(rmse),
                    "tw_rmse_K": str(rmse + 1.0),
                    "mdot_error_pct": "4.0",
                }
            )
        rows.extend(
            [
                {
                    "phase": "loso_train_grid",
                    "case_id": "salt_1",
                    "heater_lambda": "0.30",
                    "candidate_id": "candidate_incomplete",
                    "coupled_run_status": "completed",
                    "root_status": "accepted",
                    "all_probe_rmse_K": "1.0",
                    "tw_rmse_K": "1.0",
                    "mdot_error_pct": "1.0",
                },
                {
                    "phase": "selected_nominal_score",
                    "case_id": "salt_3",
                    "heater_lambda": "0.95",
                    "candidate_id": "salt3_leak_if_selected",
                    "coupled_run_status": "completed",
                    "root_status": "accepted",
                    "all_probe_rmse_K": "0.1",
                    "tw_rmse_K": "0.1",
                    "mdot_error_pct": "0.1",
                },
            ]
        )
        selection = heater.select_lambda_from_training_rows(rows)
        self.assertEqual(selection["selection_status"], "selected_from_salt1_salt2_salt4_only")
        self.assertEqual(selection["heater_lambda"], "0.25")
        self.assertIn("0p25", selection["selected_candidate_id"])
        self.assertNotIn("salt3", selection["selected_candidate_id"])

    def test_diagnostic_selection_is_labeled_when_train_root_is_rejected(self):
        rows = []
        for case_id, root_status, rmse in [("salt_1", "accepted", 3.0), ("salt_2", "accepted", 4.0), ("salt_4", "rejected", 5.0)]:
            rows.append(
                {
                    "phase": "loso_train_grid",
                    "case_id": case_id,
                    "heater_lambda": "0.5",
                    "candidate_id": "candidate_diagnostic",
                    "coupled_run_status": "completed",
                    "root_status": root_status,
                    "all_probe_rmse_K": str(rmse),
                    "tw_rmse_K": str(rmse + 1.0),
                    "mdot_error_pct": "4.0",
                }
            )
        selection = heater.select_lambda_from_training_rows(rows)
        self.assertEqual(
            selection["selection_status"],
            "diagnostic_selected_from_salt1_salt2_salt4_finite_rows_with_root_rejections",
        )
        self.assertEqual(selection["heater_lambda"], "0.5")
        self.assertIn("diagnostic only", selection["root_status_policy"])

    def test_runtime_audit_names_forbidden_holdout_and_blind_inputs(self):
        audit = heater.runtime_input_audit_rows(heater.scenario_contract_rows(None), run_fluid=False, parallel_workers=8)
        text = " ".join(row["forbidden_runtime_input"] + " " + row["evidence"] for row in audit)
        self.assertIn("Salt3 fitting target", text)
        self.assertIn("Salt2 +/-5Q fitting target", text)
        self.assertIn("val_salt2 fitting target", text)
        self.assertIn("CFD mdot", text)
        self.assertIn("validation/holdout probe temperatures", text)

    def test_pb2_readiness_blocks_salt1_when_role_rows_missing(self):
        rows = heater.case_contract_readiness_rows()
        pb2_salt1 = next(row for row in rows if row["lane_id"] == heater.PB2_LANE and row["case_id"] == "salt_1")
        self.assertEqual(pb2_salt1["readiness"], "fail")
        self.assertIn("missing Salt1", pb2_salt1["blocking_reason"])

    def test_blind_rows_are_score_only_and_blocked_pending_adapter(self):
        rows = heater.blind_perturbation_external_scorecard_rows()
        self.assertEqual({row["case_id"] for row in rows}, set(heater.BLIND_CASES))
        for row in rows:
            self.assertEqual(row["fit_allowed"], "no")
            self.assertEqual(row["model_selection_allowed"], "no")
            self.assertEqual(row["score_status"], "blocked_pending_prediction_adapter")

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = heater.OUT
        original_log_dir = heater.LOG_DIR
        with tempfile.TemporaryDirectory() as tmp:
            heater.OUT = Path(tmp)
            heater.LOG_DIR = Path(tmp) / "logs"
            try:
                summary = heater.build(run_fluid=False, parallel_workers=4)
                self.assertEqual(summary["task"], heater.TASK)
                required = [
                    "case_split_contract.csv",
                    "case_contract_readiness.csv",
                    "candidate_definitions.csv",
                    "heater_source_lambda_grid.csv",
                    "scenario_contracts.csv",
                    "runtime_input_audit.csv",
                    "training_objective_by_lambda.csv",
                    "selected_heater_source_weights.csv",
                    "nominal_coupled_scorecard.csv",
                    "salt3_holdout_delta_vs_m3.csv",
                    "probe_error_localization.csv",
                    "blind_perturbation_external_scorecard.csv",
                    "candidate_admission_review.csv",
                    "background_run_contract.csv",
                    "ag529_heater_source_loso.sbatch",
                    "blocker_decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((heater.OUT / name).exists(), name)
                with (heater.OUT / "scenario_contracts.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), len(heater.LAMBDA_GRID) * len(heater.TRAIN_CASES))
            finally:
                heater.OUT = original_out
                heater.LOG_DIR = original_log_dir


if __name__ == "__main__":
    unittest.main()
