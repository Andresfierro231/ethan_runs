import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_predictive_test_section_heat_loss_model import (
    HOLDOUT_W_TOL,
    PCT_TOL,
    VALIDATION_W_TOL,
    blocker_decision,
    fit_training_scalars,
    load_test_section_setup_rows,
    pass_fail,
    qoi_gate,
    runtime_input_audit_rows,
    setup_candidate_summary_rows,
    setup_loss_candidate_rows,
)


class PredictiveTestSectionHeatLossModelTests(unittest.TestCase):
    def test_thresholds_are_inclusive(self):
        self.assertEqual(pass_fail(VALIDATION_W_TOL, VALIDATION_W_TOL), "pass")
        self.assertEqual(pass_fail(HOLDOUT_W_TOL, HOLDOUT_W_TOL), "pass")
        self.assertEqual(pass_fail(PCT_TOL, PCT_TOL), "pass")
        self.assertEqual(pass_fail(PCT_TOL + 0.001, PCT_TOL), "fail")
        self.assertEqual(pass_fail(None, PCT_TOL), "missing")

    def test_qoi_gate_requires_watts_and_percent_on_heldout_splits(self):
        self.assertEqual(qoi_gate(4.9, 24.9, "validation"), "pass")
        self.assertEqual(qoi_gate(4.9, 25.1, "validation"), "fail")
        self.assertEqual(qoi_gate(10.1, 10.0, "holdout"), "fail")
        self.assertEqual(qoi_gate(0.0, 0.0, "train"), "fit_row_not_generalization_scored")

    def test_salt2_fit_is_training_only_and_underpredicts_holdout(self):
        rows = load_test_section_setup_rows()
        scalars = fit_training_scalars(rows)
        self.assertGreater(scalars["salt2_fit_drive_delta_T_K"], 60.0)
        self.assertLess(scalars["salt2_fit_drive_delta_T_K"], 65.0)

        candidates = setup_loss_candidate_rows()
        ts1_holdout = next(
            row
            for row in candidates
            if row["candidate_id"] == "TS1_salt2_fit_hA_constant_drive_deltaT" and row["split_role"] == "holdout"
        )
        self.assertEqual(ts1_holdout["runtime_gate"], "pass_setup_only_inputs_after_salt2_training")
        self.assertEqual(ts1_holdout["qoi_gate"], "fail")
        self.assertGreater(float(ts1_holdout["abs_error_pct_of_target"]), PCT_TOL)

    def test_realized_loss_upper_bound_is_runtime_rejected(self):
        candidates = setup_loss_candidate_rows()
        upper_bound = [
            row for row in candidates if row["candidate_id"] == "TS4_realized_external_loss_upper_bound"
        ]
        self.assertTrue(all(float(row["abs_error_W"]) == 0.0 for row in upper_bound))
        self.assertTrue(all(row["runtime_gate"] == "fail_uses_realized_cfd_loss_at_runtime" for row in upper_bound))
        self.assertTrue(all(row["admission_decision"] == "not_admitted_not_a_setup_only_physical_candidate" for row in upper_bound))

    def test_runtime_audit_contains_required_failures_and_incomplete_gate(self):
        gates = {row["gate"] for row in runtime_input_audit_rows()}
        self.assertIn("fail_for_admission", gates)
        self.assertIn("incomplete_for_admission", gates)
        self.assertIn("pass", gates)

    def test_blocker_remains_open_when_no_candidate_admitted(self):
        summary = setup_candidate_summary_rows(setup_loss_candidate_rows())
        self.assertEqual({row["admission_decision"] for row in summary}, {"not_admitted"})
        decision = blocker_decision(summary)
        self.assertEqual(decision["blocker_id"], "predictive-wall-test-section-submodels")
        self.assertEqual(decision["decision"], "keep_open")
        self.assertEqual(decision["admitted_candidate_count"], 0)


if __name__ == "__main__":
    unittest.main()
