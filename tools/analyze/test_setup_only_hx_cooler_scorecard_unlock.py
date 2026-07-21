import unittest

from tools.analyze.build_setup_only_hx_cooler_scorecard_unlock import (
    HOLDOUT_TOLERANCE_W,
    PREFERRED_CANDIDATE,
    VALIDATION_TOLERANCE_W,
    candidate_decision_rows,
    pass_fail,
    remaining_unlock_rows,
    runtime_legality_rows,
    scorecard_rows,
)


class SetupOnlyHxCoolerScorecardUnlockTests(unittest.TestCase):
    def test_pass_fail_thresholds_are_inclusive(self):
        self.assertEqual(pass_fail(VALIDATION_TOLERANCE_W, VALIDATION_TOLERANCE_W), "pass")
        self.assertEqual(pass_fail(HOLDOUT_TOLERANCE_W + 0.01, HOLDOUT_TOLERANCE_W), "fail")
        self.assertEqual(pass_fail(None, HOLDOUT_TOLERANCE_W), "missing")

    def test_preferred_candidate_advances_but_not_final(self):
        hx_rows = [
            {
                "candidate_id": PREFERRED_CANDIDATE,
                "case_id": "salt_2",
                "split_role": "train",
                "model_form": PREFERRED_CANDIDATE,
                "predicted_qhx_W": "136.35074",
                "target_qhx_W": "136.35074",
                "abs_error_W": "0",
                "runtime_input_violation_count": "0",
                "admission_class": "predictive_candidate",
                "forward_v1_use": "preferred_setup_legal_hx_candidate_pending_terminal_scorecard",
                "source_path": "source.csv",
            },
            {
                "candidate_id": PREFERRED_CANDIDATE,
                "case_id": "salt_3",
                "split_role": "validation",
                "model_form": PREFERRED_CANDIDATE,
                "predicted_qhx_W": "147.9005",
                "target_qhx_W": "150.7696",
                "abs_error_W": "2.8691",
                "runtime_input_violation_count": "0",
                "admission_class": "predictive_candidate",
                "forward_v1_use": "preferred_setup_legal_hx_candidate_pending_terminal_scorecard",
                "source_path": "source.csv",
            },
            {
                "candidate_id": PREFERRED_CANDIDATE,
                "case_id": "salt_4",
                "split_role": "holdout",
                "model_form": PREFERRED_CANDIDATE,
                "predicted_qhx_W": "161.7242",
                "target_qhx_W": "169.2268",
                "abs_error_W": "7.5026",
                "runtime_input_violation_count": "0",
                "admission_class": "predictive_candidate",
                "forward_v1_use": "preferred_setup_legal_hx_candidate_pending_terminal_scorecard",
                "source_path": "source.csv",
            },
        ]
        scores = scorecard_rows(hx_rows)
        decisions = candidate_decision_rows(
            [
                {
                    "candidate_id": PREFERRED_CANDIDATE,
                    "all_non_salt1_rmse_W": "4.6376",
                    "all_non_salt1_mae_W": "3.4572",
                    "decision": "preferred_current_candidate",
                    "source_path": "source.csv",
                }
            ],
            scores,
        )
        self.assertEqual(decisions[0]["validation_gate"], "pass")
        self.assertEqual(decisions[0]["holdout_gate"], "pass")
        self.assertEqual(decisions[0]["runtime_gate"], "pass")
        self.assertIn("advance_setup_only_hx_candidate", decisions[0]["agent438_decision"])
        self.assertIn("not_admitted_final_forward_v1", decisions[0]["final_forward_v1_admission"])

    def test_holdout_failure_prevents_secondary_selection(self):
        scores = scorecard_rows(
            [
                {
                    "candidate_id": "secondary",
                    "case_id": "salt_3",
                    "split_role": "validation",
                    "model_form": "secondary",
                    "target_qhx_W": "150",
                    "abs_error_W": "2",
                    "runtime_input_violation_count": "0",
                },
                {
                    "candidate_id": "secondary",
                    "case_id": "salt_4",
                    "split_role": "holdout",
                    "model_form": "secondary",
                    "target_qhx_W": "169",
                    "abs_error_W": "17.5",
                    "runtime_input_violation_count": "0",
                },
            ]
        )
        decisions = candidate_decision_rows([], scores)
        self.assertEqual(decisions[0]["validation_gate"], "pass")
        self.assertEqual(decisions[0]["holdout_gate"], "fail")
        self.assertEqual(decisions[0]["agent438_decision"], "candidate_not_selected_numeric_generalization_gate_failed")

    def test_runtime_legality_audit_has_no_failures(self):
        gates = {row["gate"] for row in runtime_legality_rows()}
        self.assertNotIn("fail", gates)

    def test_remaining_unlock_queue_keeps_final_blockers(self):
        rows = remaining_unlock_rows()
        blocking = {row["gate"] for row in rows if row["blocking_final_forward_v1"] == "yes"}
        self.assertIn("hydraulic_pressure_F6", blocking)
        self.assertIn("internal_Nu_thermal_sign_heat_balance", blocking)
        self.assertIn("mesh_GCI_UQ", blocking)


if __name__ == "__main__":
    unittest.main()
