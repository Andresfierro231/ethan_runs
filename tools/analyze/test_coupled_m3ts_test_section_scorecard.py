import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_coupled_m3ts_test_section_scorecard import (
    blocker_decision,
    coupled_rows,
    role_rows_for_case,
    runtime_audit_rows,
    scenario_contract_rows,
    setup_by_case,
    static_heat_loss_gate_rows,
)


class CoupledM3TSTestSectionScorecardTests(unittest.TestCase):
    def test_role_rows_include_ambient_wall_and_test_section_for_upcomer_parent(self):
        rows = role_rows_for_case(setup_by_case()["salt_2"])
        roles = {row["role"] for row in rows}
        self.assertEqual(roles, {"ambient_wall", "test_section"})
        self.assertTrue(all(row["parent_segment"] == "left_upper_vertical" for row in rows))
        self.assertTrue(all(row["hA_W_K"] is not None for row in rows))

    def test_scenario_contracts_emit_runtime_legal_json(self):
        rows = scenario_contract_rows()
        self.assertEqual(len(rows), 9)
        first = rows[0]
        payload = json.loads(first["scenario_json"])
        self.assertEqual(first["runtime_input_violations"], 0)
        self.assertIn("role_rows", payload)
        self.assertIn("parent_boundary_maps", payload)
        self.assertEqual(first["outer_closure_mode"], "external_boundary_table")

    def test_static_heat_loss_gate_keeps_prior_holdout_failure_visible(self):
        rows = static_heat_loss_gate_rows()
        holdout = [
            row
            for row in rows
            if row["candidate_id"] == "M3TS_R0_role_table_unscaled" and row["split_role"] == "holdout"
        ][0]
        self.assertEqual(holdout["heat_loss_gate"], "fail")
        self.assertGreater(float(holdout["abs_error_pct"]), 25.0)

    def test_default_coupled_rows_are_explicitly_not_run(self):
        rows = coupled_rows(run_fluid=False)
        self.assertEqual(len(rows), 9)
        self.assertEqual({row["coupled_gate"] for row in rows}, {"fail_no_completed_coupled_m3ts_score"})

    def test_runtime_audit_has_no_forbidden_input_failure(self):
        rows = runtime_audit_rows()
        self.assertTrue(any(row["gate"] == "pass" for row in rows))
        forbidden = ";".join(row["forbidden_runtime_input"] for row in rows)
        self.assertIn("realized wallHeatFlux", forbidden)

    def test_blocker_stays_open_without_completed_coupled_pass(self):
        decision = blocker_decision(coupled_rows(run_fluid=False), static_heat_loss_gate_rows())
        self.assertEqual(decision["blocker_id"], "predictive-wall-test-section-submodels")
        self.assertEqual(decision["decision"], "keep_open")


if __name__ == "__main__":
    unittest.main()
