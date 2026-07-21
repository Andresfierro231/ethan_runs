import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_predictive_boundary_submodel_admission import (
    COOLER_MODEL,
    HEATER_MODEL,
    HOLDOUT_W_TOL,
    PCT_TOL,
    VALIDATION_W_TOL,
    blocker_decision,
    gate_for_split,
    pass_fail,
    runtime_audit_rows,
    submodel_summary_rows,
)


class PredictiveBoundarySubmodelAdmissionTests(unittest.TestCase):
    def test_thresholds_are_inclusive(self):
        self.assertEqual(pass_fail(VALIDATION_W_TOL, VALIDATION_W_TOL), "pass")
        self.assertEqual(pass_fail(PCT_TOL, PCT_TOL), "pass")
        self.assertEqual(pass_fail(HOLDOUT_W_TOL + 0.001, HOLDOUT_W_TOL), "fail")
        self.assertEqual(pass_fail(None, HOLDOUT_W_TOL), "missing")

    def test_gate_requires_both_watts_and_percent_for_holdout(self):
        self.assertEqual(gate_for_split(9.0, 4.9, "holdout"), "pass")
        self.assertEqual(gate_for_split(9.0, 5.1, "holdout"), "fail")
        self.assertEqual(gate_for_split(10.1, 4.0, "holdout"), "fail")
        self.assertEqual(gate_for_split(0.0, 0.0, "train"), "fit_row_not_generalization_scored")

    def test_runtime_audit_has_no_failures(self):
        gates = {row["gate"] for row in runtime_audit_rows()}
        self.assertEqual(gates, {"pass"})

    def test_summary_supersedes_broad_blocker_when_only_wall_is_blocked(self):
        heater = [
            {
                "case_split": "validation",
                "abs_error_W": "0.49",
                "runtime_gate": "pass",
                "admission_decision": "admitted_predictive_boundary_submodel",
            },
            {
                "case_split": "holdout",
                "abs_error_W": "1.07",
                "runtime_gate": "pass",
                "admission_decision": "admitted_predictive_boundary_submodel",
            },
        ]
        cooler = [
            {
                "case_split": "validation",
                "abs_error_W": "2.869",
                "runtime_gate": "pass",
                "admission_decision": "admitted_predictive_boundary_submodel",
            },
            {
                "case_split": "holdout",
                "abs_error_W": "7.503",
                "runtime_gate": "pass",
                "admission_decision": "admitted_predictive_boundary_submodel",
            },
        ]
        wall = [
            {
                "model_form": "setup_only_distributed_loss_or_resistance_network",
                "runtime_gate": "pass_for_available_api_contract",
                "admission_decision": "not_admitted_narrow_blocker_required",
            }
        ]
        summary = submodel_summary_rows(heater, cooler, wall)
        decision = blocker_decision(summary)
        self.assertEqual(decision["decision"], "supersede_broad_blocker_with_narrow_wall_test_section_blocker")
        self.assertEqual(decision["new_or_remaining_blocker"], "predictive-wall-test-section-submodels")

    def test_summary_names_preferred_models(self):
        heater = [
            {
                "case_split": "validation",
                "abs_error_W": "0.49",
                "runtime_gate": "pass",
                "admission_decision": "admitted_predictive_boundary_submodel",
            },
            {
                "case_split": "holdout",
                "abs_error_W": "1.07",
                "runtime_gate": "pass",
                "admission_decision": "admitted_predictive_boundary_submodel",
            },
        ]
        cooler = [
            {
                "case_split": "validation",
                "abs_error_W": "2.869",
                "runtime_gate": "pass",
                "admission_decision": "admitted_predictive_boundary_submodel",
            },
            {
                "case_split": "holdout",
                "abs_error_W": "7.503",
                "runtime_gate": "pass",
                "admission_decision": "admitted_predictive_boundary_submodel",
            },
        ]
        wall = [
            {
                "model_form": "setup_only_distributed_loss_or_resistance_network",
                "runtime_gate": "pass_for_available_api_contract",
                "admission_decision": "not_admitted_narrow_blocker_required",
            }
        ]
        rows = submodel_summary_rows(heater, cooler, wall)
        models = {row["submodel"]: row["preferred_model"] for row in rows}
        self.assertEqual(models["heater"], HEATER_MODEL)
        self.assertEqual(models["cooler_hx"], COOLER_MODEL)


if __name__ == "__main__":
    unittest.main()
